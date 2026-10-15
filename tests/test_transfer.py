"""JSON export / import (backup & restore)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import Api


def test_export_single_trip(client: TestClient, populated: dict) -> None:
    resp = client.get(f"/api/trips/{populated['trip']['id']}/export")
    assert resp.status_code == 200
    assert "attachment" in resp.headers["content-disposition"]
    doc = resp.json()
    assert doc["format"] == "family-packing-list" and doc["version"] == 1
    assert doc["exported_at"]
    [trip] = doc["trips"]
    assert trip["name"] == "חופשה ביוון"
    assert [c["name"] for c in trip["categories"]] == ["מסמכים", "ביגוד"]
    passport = trip["categories"][0]["items"][0]
    assert passport == {"name": "דרכונים", "quantity": 4, "note": "לבדוק תוקף", "packed": False, "assignees": ["אבא"]}
    assert {m["name"] for m in doc["members"]} == {"אבא", "ילדים"}


def test_export_single_trip_only_includes_used_members(client: TestClient, api: Api, populated: dict) -> None:
    api.member("סבתא")
    doc = client.get(f"/api/trips/{populated['trip']['id']}/export").json()
    assert "סבתא" not in {m["name"] for m in doc["members"]}
    full = client.get("/api/export").json()
    assert "סבתא" in {m["name"] for m in full["members"]}


def test_export_missing_trip(client: TestClient) -> None:
    assert client.get("/api/trips/9/export").status_code == 404


def test_roundtrip_into_fresh_database(client: TestClient, populated: dict, tmp_path) -> None:
    from tests.conftest import make_settings
    from app.main import create_app

    backup = client.get("/api/export").json()
    fresh_dir = tmp_path / "fresh"
    fresh_dir.mkdir()
    with TestClient(create_app(make_settings(fresh_dir))) as other:
        resp = other.post("/api/import", json=backup)
        assert resp.status_code == 201, resp.text
        result = resp.json()
        assert result["members_created"] == 2
        [summary] = result["trips"]
        assert summary["total_items"] == 3 and summary["packed_items"] == 1
        re_export = other.get("/api/export").json()
    assert re_export["trips"] == backup["trips"]
    assert re_export["members"] == backup["members"]


def test_import_is_additive_and_matches_members_by_name(client: TestClient, populated: dict) -> None:
    doc = client.get(f"/api/trips/{populated['trip']['id']}/export").json()
    doc["trips"][0]["categories"][0]["items"][0]["assignees"].append("סבא")
    result = client.post("/api/import", json=doc).json()
    assert result["members_created"] == 1  # only "סבא" is new
    assert len(client.get("/api/trips").json()) == 2
    assert len(client.get("/api/members").json()) == 3


def test_import_validation(client: TestClient) -> None:
    assert client.post("/api/import", json={"trips": []}).status_code == 422
    assert client.post("/api/import", json={"format": "other", "trips": [{"name": "x"}]}).status_code == 422
    assert client.post("/api/import", json={"version": 2, "trips": [{"name": "x"}]}).status_code == 422
    bad_item = {"trips": [{"name": "x", "categories": [{"name": "c", "items": [{"name": "i", "quantity": -1}]}]}]}
    assert client.post("/api/import", json=bad_item).status_code == 422
    # Nothing partially imported.
    assert client.get("/api/trips").json() == []


def test_import_minimal_document(client: TestClient) -> None:
    resp = client.post("/api/import", json={"trips": [{"name": "מינימלי"}]})
    assert resp.status_code == 201
    assert resp.json()["trips"][0]["name"] == "מינימלי"
