"""Template cloning logic (service + endpoints)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.db import Database
from app.repositories import trips as trips_repo
from app.services.cloning import clone_trip
from tests.conftest import Api


def _shape(trip: dict) -> list:
    return [
        (c["name"], c["icon"], [(i["name"], i["quantity"], i["note"], i["assignee_ids"]) for i in c["items"]])
        for c in trip["categories"]
    ]


def test_clone_endpoint_copies_structure_and_resets_packed(client: TestClient, api: Api, populated: dict) -> None:
    src_id = populated["trip"]["id"]
    api.patch_item(populated["passport"]["id"], packed=True)
    resp = client.post(f"/api/trips/{src_id}/clone", json={"name": "חופשה ביוון 2027"})
    assert resp.status_code == 201
    clone = resp.json()

    source = api.get_trip(src_id)
    assert clone["id"] != src_id
    assert clone["name"] == "חופשה ביוון 2027"
    assert clone["emoji"] == source["emoji"]  # inherited when not given
    assert clone["is_template"] is False
    assert _shape(clone) == _shape(source)
    assert clone["packed_items"] == 0 and clone["total_items"] == source["total_items"]
    assert all(not i["packed"] for c in clone["categories"] for i in c["items"])

    # New rows, not shared references.
    src_ids = {i["id"] for c in source["categories"] for i in c["items"]}
    clone_ids = {i["id"] for c in clone["categories"] for i in c["items"]}
    assert src_ids.isdisjoint(clone_ids)


def test_source_untouched_by_edits_to_clone(client: TestClient, api: Api, populated: dict) -> None:
    clone = client.post(f"/api/trips/{populated['trip']['id']}/clone", json={"name": "copy"}).json()
    cloned_item = clone["categories"][0]["items"][0]
    api.patch_item(cloned_item["id"], name="שונה", packed=True)
    source = api.get_trip(populated["trip"]["id"])
    assert source["categories"][0]["items"][0]["name"] == "דרכונים"


def test_create_trip_from_template(client: TestClient, api: Api, populated: dict) -> None:
    client.patch(f"/api/trips/{populated['trip']['id']}", json={"is_template": True})
    trip = api.trip("טיול חדש", emoji="🏖️", source_trip_id=populated["trip"]["id"])
    assert trip["emoji"] == "🏖️"
    assert trip["is_template"] is False
    assert trip["total_items"] == 3 and trip["packed_items"] == 0


def test_clone_as_template(client: TestClient, populated: dict) -> None:
    resp = client.post(
        f"/api/trips/{populated['trip']['id']}/clone", json={"name": "תבנית חדשה", "is_template": True}
    )
    assert resp.json()["is_template"] is True


def test_clone_unknown_source(client: TestClient) -> None:
    assert client.post("/api/trips/999/clone", json={"name": "x"}).status_code == 404
    assert client.post("/api/trips", json={"name": "x", "source_trip_id": 999}).status_code == 404
    # The failed clone must not leave a half-created trip behind.
    assert client.get("/api/trips").json() == []


def test_clone_service_keep_packed(db: Database) -> None:
    with db.transaction():
        src = trips_repo.create_trip(db, name="src")
        cat = db.execute("INSERT INTO categories (trip_id, name) VALUES (?, 'c')", (src,)).lastrowid
        db.execute("INSERT INTO items (category_id, name, packed) VALUES (?, 'i', 1)", (cat,))
        kept = clone_trip(db, src, name="kept", keep_packed=True)
        reset = clone_trip(db, src, name="reset")
    assert trips_repo.get_summary(db, kept)["packed_items"] == 1
    assert trips_repo.get_summary(db, reset)["packed_items"] == 0


def test_clone_empty_trip(client: TestClient, api: Api) -> None:
    src = api.trip("ריק")
    clone = client.post(f"/api/trips/{src['id']}/clone", json={"name": "עדיין ריק"}).json()
    assert clone["categories"] == []
