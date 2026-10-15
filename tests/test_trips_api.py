"""Trip endpoints: CRUD, summaries, reset, templates and cloning."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import Api


def test_empty_database_has_no_trips(client: TestClient) -> None:
    assert client.get("/api/trips").json() == []


def test_trip_crud(client: TestClient, api: Api) -> None:
    trip = api.trip("קמפינג", emoji="⛺")
    assert trip["name"] == "קמפינג" and trip["emoji"] == "⛺"
    assert trip["is_template"] is False and trip["categories"] == []
    assert trip["total_items"] == 0 and trip["packed_items"] == 0

    resp = client.patch(f"/api/trips/{trip['id']}", json={"name": "קמפינג בגליל", "is_template": True})
    assert resp.status_code == 200
    assert resp.json()["name"] == "קמפינג בגליל" and resp.json()["is_template"] is True
    assert "categories" not in resp.json()

    assert client.delete(f"/api/trips/{trip['id']}").status_code == 204
    assert client.get(f"/api/trips/{trip['id']}").status_code == 404


def test_trip_summary_counts(client: TestClient, populated: dict) -> None:
    [summary] = client.get("/api/trips").json()
    assert summary["total_items"] == 3
    assert summary["packed_items"] == 1


def test_templates_sorted_after_trips(client: TestClient, api: Api) -> None:
    api.trip("תבנית", is_template=True)
    api.trip("טיול")
    names = [t["name"] for t in client.get("/api/trips").json()]
    assert names == ["טיול", "תבנית"]


def test_trip_detail_structure(api: Api, populated: dict) -> None:
    trip = api.get_trip(populated["trip"]["id"])
    assert [c["name"] for c in trip["categories"]] == ["מסמכים", "ביגוד"]
    clothes = trip["categories"][1]
    assert [i["name"] for i in clothes["items"]] == ["חולצות", "כובע"]
    shirts = clothes["items"][0]
    assert shirts["quantity"] == 7
    assert shirts["assignee_ids"] == [populated["dad"]["id"], populated["kids"]["id"]]


def test_reset_unchecks_everything(client: TestClient, api: Api, populated: dict) -> None:
    api.patch_item(populated["passport"]["id"], packed=True)
    resp = client.post(f"/api/trips/{populated['trip']['id']}/reset")
    assert resp.status_code == 200
    body = resp.json()
    assert body["packed_items"] == 0
    assert all(not i["packed"] for c in body["categories"] for i in c["items"])


def test_reset_unknown_trip(client: TestClient) -> None:
    assert client.post("/api/trips/999/reset").status_code == 404


def test_patch_trip_validation(client: TestClient, api: Api) -> None:
    trip = api.trip()
    assert client.patch(f"/api/trips/{trip['id']}", json={"name": None}).status_code == 422
    assert client.patch(f"/api/trips/{trip['id']}", json={"name": "  "}).status_code == 422
    assert client.patch(f"/api/trips/{trip['id']}", json={"colour": "x"}).status_code == 422
    assert client.patch("/api/trips/999", json={"name": "x"}).status_code == 404


def test_patch_trip_clear_emoji(client: TestClient, api: Api) -> None:
    trip = api.trip(emoji="🌴")
    assert client.patch(f"/api/trips/{trip['id']}", json={"emoji": None}).json()["emoji"] is None


def test_empty_patch_is_noop(client: TestClient, api: Api) -> None:
    trip = api.trip("x")
    resp = client.patch(f"/api/trips/{trip['id']}", json={})
    assert resp.status_code == 200 and resp.json()["name"] == "x"


def test_delete_unknown_trip(client: TestClient) -> None:
    assert client.delete("/api/trips/12345").status_code == 404
