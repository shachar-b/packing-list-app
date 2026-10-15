"""WebSocket real-time broadcasts."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.realtime import Broadcaster
from tests.conftest import Api


def _connect(client: TestClient, client_id: str = "tab-1") -> Any:
    ws = client.websocket_connect(f"/ws?client_id={client_id}")
    session = ws.__enter__()
    hello = session.receive_json()
    assert hello["type"] == "hello"
    return ws, session


@pytest.fixture
def two_devices(client: TestClient):
    a_ctx, phone_a = _connect(client, "phone-a")
    b_ctx, phone_b = _connect(client, "phone-b")
    yield phone_a, phone_b
    b_ctx.__exit__(None, None, None)
    a_ctx.__exit__(None, None, None)


def test_ping_pong(client: TestClient) -> None:
    with client.websocket_connect("/ws") as ws:
        assert ws.receive_json()["type"] == "hello"
        ws.send_text("not json")  # ignored, must not kill the socket
        ws.send_json({"type": "ping", "ts": 123})
        assert ws.receive_json() == {"type": "pong", "ts": 123}


def test_item_update_broadcast_to_all_devices(client: TestClient, populated: dict, two_devices) -> None:
    phone_a, phone_b = two_devices
    item_id = populated["passport"]["id"]
    resp = client.patch(f"/api/items/{item_id}", json={"packed": True}, headers={"X-Client-Id": "phone-a"})
    assert resp.status_code == 200
    for phone in (phone_a, phone_b):
        event = phone.receive_json()
        assert event["type"] == "item.updated"
        assert event["trip_id"] == populated["trip"]["id"]
        assert event["origin"] == "phone-a"
        assert event["data"]["id"] == item_id and event["data"]["packed"] is True


def test_event_sequence_for_crud(client: TestClient, api: Api, two_devices) -> None:
    phone_a, _ = two_devices
    trip = api.trip("סנכרון")
    assert phone_a.receive_json()["type"] == "trip.created"
    cat = api.category(trip["id"])
    ev = phone_a.receive_json()
    assert ev["type"] == "category.created" and ev["data"]["id"] == cat["id"]
    item = api.item(cat["id"])
    ev = phone_a.receive_json()
    assert ev["type"] == "item.created" and ev["data"]["category_id"] == cat["id"]
    client.delete(f"/api/items/{item['id']}")
    ev = phone_a.receive_json()
    assert ev == {
        "type": "item.deleted",
        "trip_id": trip["id"],
        "origin": None,
        "data": {"id": item["id"], "category_id": cat["id"]},
    }
    client.post(f"/api/categories/{cat['id']}/pack-all", json={})
    assert phone_a.receive_json()["type"] == "category.updated"
    client.delete(f"/api/categories/{cat['id']}")
    assert phone_a.receive_json()["type"] == "category.deleted"
    client.post(f"/api/trips/{trip['id']}/reset")
    ev = phone_a.receive_json()
    assert ev["type"] == "trip.snapshot" and "categories" in ev["data"]
    client.patch(f"/api/trips/{trip['id']}", json={"name": "חדש"})
    assert phone_a.receive_json()["type"] == "trip.updated"
    client.delete(f"/api/trips/{trip['id']}")
    assert phone_a.receive_json() == {"type": "trip.deleted", "trip_id": trip["id"], "origin": None, "data": {"id": trip["id"]}}


def test_member_events(client: TestClient, api: Api, two_devices) -> None:
    _, phone_b = two_devices
    m = api.member("סבתא")
    assert phone_b.receive_json()["type"] == "member.created"
    client.patch(f"/api/members/{m['id']}", json={"emoji": "👵"})
    assert phone_b.receive_json()["data"]["emoji"] == "👵"
    client.delete(f"/api/members/{m['id']}")
    assert phone_b.receive_json() == {"type": "member.deleted", "trip_id": None, "origin": None, "data": {"id": m["id"]}}


def test_import_broadcasts(client: TestClient, two_devices) -> None:
    phone_a, _ = two_devices
    client.post("/api/import", json={"members": [{"name": "דוד"}], "trips": [{"name": "מיובא"}]})
    assert phone_a.receive_json()["type"] == "member.created"
    assert phone_a.receive_json()["type"] == "trip.created"


def test_failed_request_does_not_broadcast(client: TestClient, populated: dict, two_devices) -> None:
    phone_a, _ = two_devices
    client.patch(f"/api/items/{populated['passport']['id']}", json={"quantity": 0})
    client.patch(f"/api/items/{populated['passport']['id']}", json={"note": "ok"})
    # The first event received must be from the *successful* request.
    assert phone_a.receive_json()["data"]["note"] == "ok"


def test_connection_count_in_health(client: TestClient) -> None:
    assert client.get("/api/health").json()["connections"] == 0
    with client.websocket_connect("/ws") as ws:
        ws.receive_json()
        assert client.get("/api/health").json()["connections"] == 1


class _DeadSocket:
    async def send_json(self, _: Any) -> None:
        raise RuntimeError("connection reset")


class _LiveSocket:
    def __init__(self) -> None:
        self.sent: list[Any] = []

    async def send_json(self, payload: Any) -> None:
        self.sent.append(payload)


@pytest.mark.anyio
async def test_broadcaster_drops_dead_sockets() -> None:
    bus = Broadcaster()
    dead, live = _DeadSocket(), _LiveSocket()
    bus._clients[dead] = "dead"  # type: ignore[index]
    bus._clients[live] = "live"  # type: ignore[index]
    await bus.publish("trip.updated", {"id": 1}, trip_id=1)
    assert bus.connection_count == 1
    assert live.sent[0]["type"] == "trip.updated"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
