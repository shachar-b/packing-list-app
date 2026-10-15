"""Item endpoints: creation, granular partial updates, assignees and moves."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.conftest import Api


def test_create_item_defaults(api: Api) -> None:
    trip = api.trip()
    cat = api.category(trip["id"])
    item = api.item(cat["id"], "  מברשת שיניים  ")
    assert item["name"] == "מברשת שיניים"
    assert item["packed"] is False and item["quantity"] == 1
    assert item["note"] is None and item["assignee_ids"] == []
    assert item["category_id"] == cat["id"]
    second = api.item(cat["id"], "משחה")
    assert second["sort_order"] == item["sort_order"] + 1


def test_create_item_full(api: Api, populated: dict) -> None:
    item = populated["passport"]
    assert item["quantity"] == 4 and item["note"] == "לבדוק תוקף"
    assert item["assignee_ids"] == [populated["dad"]["id"]]


def test_assignee_ids_deduplicated(api: Api, populated: dict) -> None:
    d = populated["dad"]["id"]
    item = api.item(populated["docs"]["id"], "x", assignee_ids=[d, d])
    assert item["assignee_ids"] == [d]


def test_unknown_assignee_rejected(client: TestClient, populated: dict) -> None:
    resp = client.post(f"/api/categories/{populated['docs']['id']}/items", json={"name": "x", "assignee_ids": [999]})
    assert resp.status_code == 422
    assert resp.json()["error"]["details"] == {"missing": [999]}
    resp = client.patch(f"/api/items/{populated['hat']['id']}", json={"assignee_ids": [999]})
    assert resp.status_code == 422


def test_create_item_missing_category(client: TestClient) -> None:
    assert client.post("/api/categories/5/items", json={"name": "x"}).status_code == 404


@pytest.mark.parametrize(
    "payload",
    [
        {"name": ""},
        {"name": "x", "quantity": 0},
        {"name": "x", "quantity": 1000},
        {"name": "x", "quantity": "lots"},
        {"name": "x", "note": "n" * 501},
        {"name": "x", "packed": "maybe"},
        {"name": "x", "extra": True},
        {"quantity": 2},
    ],
)
def test_create_item_validation(client: TestClient, populated: dict, payload: dict) -> None:
    resp = client.post(f"/api/categories/{populated['docs']['id']}/items", json=payload)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"


def test_patch_only_touches_sent_fields(api: Api, populated: dict) -> None:
    """Two devices editing different fields of the same item must not clobber each other."""
    item_id = populated["passport"]["id"]
    # Device A checks the item off…
    api.patch_item(item_id, packed=True)
    # …while device B (holding a stale copy) edits only the note.
    after = api.patch_item(item_id, note="בתיק של אבא")
    assert after["packed"] is True
    assert after["note"] == "בתיק של אבא"
    assert after["quantity"] == 4
    assert after["assignee_ids"] == [populated["dad"]["id"]]


def test_packed_is_idempotent_set_not_toggle(api: Api, populated: dict) -> None:
    item_id = populated["passport"]["id"]
    api.patch_item(item_id, packed=True)
    assert api.patch_item(item_id, packed=True)["packed"] is True


def test_patch_assignees_and_clear_note(api: Api, populated: dict) -> None:
    item_id = populated["passport"]["id"]
    kids = populated["kids"]["id"]
    updated = api.patch_item(item_id, assignee_ids=[kids], note=None, quantity=2)
    assert updated["assignee_ids"] == [kids] and updated["note"] is None and updated["quantity"] == 2
    assert api.patch_item(item_id, assignee_ids=[])["assignee_ids"] == []
    assert api.patch_item(item_id, note="")["note"] is None


def test_patch_updates_timestamp(api: Api, populated: dict) -> None:
    before = populated["passport"]["updated_at"]
    after = api.patch_item(populated["passport"]["id"], packed=True)["updated_at"]
    assert after >= before


@pytest.mark.parametrize("field", ["name", "quantity", "packed", "assignee_ids", "category_id"])
def test_patch_rejects_null_for_required_fields(api: Api, populated: dict, field: str) -> None:
    api.patch_item(populated["passport"]["id"], expected=422, **{field: None})


def test_move_item_between_categories(api: Api, populated: dict) -> None:
    moved = api.patch_item(populated["passport"]["id"], category_id=populated["clothes"]["id"])
    assert moved["category_id"] == populated["clothes"]["id"]
    trip = api.get_trip(populated["trip"]["id"])
    assert trip["categories"][0]["items"] == []
    assert [i["name"] for i in trip["categories"][1]["items"]][-1] == "דרכונים"


def test_move_item_to_other_trip_rejected(api: Api, populated: dict) -> None:
    other = api.category(api.trip("אחר")["id"])
    api.patch_item(populated["passport"]["id"], expected=422, category_id=other["id"])
    api.patch_item(populated["passport"]["id"], expected=422, category_id=9999)


def test_delete_item(client: TestClient, api: Api, populated: dict) -> None:
    assert client.delete(f"/api/items/{populated['hat']['id']}").status_code == 204
    assert client.delete(f"/api/items/{populated['hat']['id']}").status_code == 404
    assert api.get_trip(populated["trip"]["id"])["total_items"] == 2


def test_patch_missing_item(api: Api) -> None:
    api.patch_item(4242, expected=404, packed=True)
