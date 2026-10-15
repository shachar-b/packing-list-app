"""First-boot seed data."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.db import Database
from app.main import create_app
from app.services.seed import seed_if_needed
from tests.conftest import make_settings

REQUIRED_CATEGORIES = {"מסמכים וכסף", "ביגוד והנעלה", "טואלטיקה ופארם", "אלקטרוניקה", "ילדים וציוד לטיולי יום"}


def test_seed_creates_hebrew_templates(seeded_client: TestClient) -> None:
    trips = seeded_client.get("/api/trips").json()
    templates = [t for t in trips if t["is_template"]]
    regular = [t for t in trips if not t["is_template"]]
    assert len(templates) >= 2 and len(regular) == 1
    assert all(t["total_items"] > 0 and t["packed_items"] == 0 for t in trips)

    abroad = next(t for t in templates if "חו״ל" in t["name"])
    detail = seeded_client.get(f"/api/trips/{abroad['id']}").json()
    assert {c["name"] for c in detail["categories"]} == REQUIRED_CATEGORIES
    assert all(c["icon"] for c in detail["categories"])


def test_seed_creates_family_members(seeded_client: TestClient) -> None:
    names = [m["name"] for m in seeded_client.get("/api/members").json()]
    assert names == ["כל המשפחה", "הורים", "אבא", "אמא", "ילדים"]


def test_seed_items_have_assignees(seeded_client: TestClient) -> None:
    trip = next(t for t in seeded_client.get("/api/trips").json() if not t["is_template"])
    detail = seeded_client.get(f"/api/trips/{trip['id']}").json()
    assert any(i["assignee_ids"] for c in detail["categories"] for i in c["items"])


def test_seed_runs_only_once(tmp_path: Path) -> None:
    settings = make_settings(tmp_path, seed=True)
    with TestClient(create_app(settings)) as c:
        first = c.get("/api/trips").json()
        # The family deletes every trip; a restart must not resurrect the seed.
        for t in first:
            c.delete(f"/api/trips/{t['id']}")
    with TestClient(create_app(settings)) as c:
        assert c.get("/api/trips").json() == []


def test_seed_skipped_when_data_exists(db: Database) -> None:
    db.execute("INSERT INTO trips (name) VALUES ('existing')")
    assert seed_if_needed(db) is False
    assert db.fetchone("SELECT COUNT(*) FROM trips")[0] == 1
    assert seed_if_needed(db) is False


def test_seed_disabled(client: TestClient) -> None:
    assert client.get("/api/trips").json() == []
    assert client.get("/api/members").json() == []
