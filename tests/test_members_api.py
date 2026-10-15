"""Family member endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import Api


def test_member_crud(client: TestClient, api: Api) -> None:
    dad = api.member("אבא", color="#10b981", emoji="👨")
    mom = api.member("אמא")
    assert dad == {"id": dad["id"], "name": "אבא", "color": "#10b981", "emoji": "👨", "position": 0}
    assert mom["position"] == 1 and mom["color"] == "#6366f1"

    resp = client.patch(f"/api/members/{mom['id']}", json={"name": "  אמא שלי  ", "emoji": None})
    assert resp.status_code == 200
    assert resp.json()["name"] == "אמא שלי"

    assert [m["name"] for m in client.get("/api/members").json()] == ["אבא", "אמא שלי"]

    assert client.delete(f"/api/members/{dad['id']}").status_code == 204
    assert client.delete(f"/api/members/{dad['id']}").status_code == 404
    assert [m["id"] for m in client.get("/api/members").json()] == [mom["id"]]


def test_member_duplicate_name_conflict(client: TestClient, api: Api) -> None:
    api.member("Dad")
    resp = client.post("/api/members", json={"name": "dad"})
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "conflict"


def test_member_rename_to_existing_conflict(client: TestClient, api: Api) -> None:
    api.member("אבא")
    mom = api.member("אמא")
    assert client.patch(f"/api/members/{mom['id']}", json={"name": "אבא"}).status_code == 409


def test_member_validation(client: TestClient) -> None:
    assert client.post("/api/members", json={"name": ""}).status_code == 422
    assert client.post("/api/members", json={"name": "x", "color": "red"}).status_code == 422
    assert client.post("/api/members", json={"name": "x" * 41}).status_code == 422
    assert client.post("/api/members", json={"name": "x", "unknown": 1}).status_code == 422


def test_member_null_name_rejected(client: TestClient, api: Api) -> None:
    m = api.member()
    assert client.patch(f"/api/members/{m['id']}", json={"name": None}).status_code == 422


def test_deleting_member_removes_assignments(client: TestClient, api: Api, populated: dict) -> None:
    client.delete(f"/api/members/{populated['dad']['id']}")
    trip = api.get_trip(populated["trip"]["id"])
    all_assignees = [a for c in trip["categories"] for i in c["items"] for a in i["assignee_ids"]]
    assert populated["dad"]["id"] not in all_assignees
    assert populated["kids"]["id"] in all_assignees
