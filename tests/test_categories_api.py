"""Category endpoints including bulk pack/unpack."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import Api


def test_category_crud(client: TestClient, api: Api) -> None:
    trip = api.trip()
    a = api.category(trip["id"], "אלקטרוניקה", icon="🔌")
    b = api.category(trip["id"], "ביגוד")
    assert a["icon"] == "🔌" and a["sort_order"] == 0 and a["items"] == []
    assert b["icon"] == "📦" and b["sort_order"] == 1

    resp = client.patch(f"/api/categories/{a['id']}", json={"name": "גאדג׳טים", "icon": "📱"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "גאדג׳טים" and resp.json()["icon"] == "📱"

    assert client.delete(f"/api/categories/{b['id']}").status_code == 204
    assert [c["id"] for c in api.get_trip(trip["id"])["categories"]] == [a["id"]]


def test_category_reorder(client: TestClient, api: Api) -> None:
    trip = api.trip()
    a = api.category(trip["id"], "א")
    b = api.category(trip["id"], "ב")
    client.patch(f"/api/categories/{a['id']}", json={"sort_order": 5})
    assert [c["id"] for c in api.get_trip(trip["id"])["categories"]] == [b["id"], a["id"]]


def test_category_on_missing_trip(client: TestClient) -> None:
    resp = client.post("/api/trips/42/categories", json={"name": "x"})
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


def test_category_validation(client: TestClient, api: Api) -> None:
    trip = api.trip()
    assert client.post(f"/api/trips/{trip['id']}/categories", json={"name": ""}).status_code == 422
    assert client.post(f"/api/trips/{trip['id']}/categories", json={"name": "a", "icon": "x" * 17}).status_code == 422
    cat = api.category(trip["id"])
    assert client.patch(f"/api/categories/{cat['id']}", json={"icon": None}).status_code == 422


def test_delete_category_cascades_items(client: TestClient, api: Api, populated: dict) -> None:
    client.delete(f"/api/categories/{populated['clothes']['id']}")
    assert client.patch(f"/api/items/{populated['shirts']['id']}", json={"packed": True}).status_code == 404
    assert api.get_trip(populated["trip"]["id"])["total_items"] == 1


def test_pack_all_and_unpack_all(client: TestClient, api: Api, populated: dict) -> None:
    cid = populated["clothes"]["id"]
    resp = client.post(f"/api/categories/{cid}/pack-all", json={})
    assert resp.status_code == 200
    assert all(i["packed"] for i in resp.json()["items"])
    # Other categories untouched.
    trip = api.get_trip(populated["trip"]["id"])
    assert trip["categories"][0]["items"][0]["packed"] is False
    assert trip["packed_items"] == 2

    resp = client.post(f"/api/categories/{cid}/pack-all", json={"packed": False})
    assert not any(i["packed"] for i in resp.json()["items"])


def test_pack_all_missing_category(client: TestClient) -> None:
    assert client.post("/api/categories/77/pack-all", json={}).status_code == 404
    assert client.patch("/api/categories/77", json={"name": "x"}).status_code == 404
    assert client.delete("/api/categories/77").status_code == 404
