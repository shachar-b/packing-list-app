"""Shared pytest fixtures.

Every test gets an isolated SQLite file under ``tmp_path``. The TestClient is
always used as a context manager so that the lifespan runs and REST calls and
WebSocket sessions share one event loop (required for broadcast tests).
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import DEFAULT_FRONTEND_DIR, Settings
from app.db import Database
from app.main import create_app


def make_settings(tmp_path: Path, *, seed: bool = False) -> Settings:
    return Settings(db_path=tmp_path / "test.db", frontend_dir=DEFAULT_FRONTEND_DIR, seed_on_first_boot=seed)


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    with TestClient(create_app(make_settings(tmp_path))) as c:
        yield c


@pytest.fixture
def seeded_client(tmp_path: Path) -> Iterator[TestClient]:
    with TestClient(create_app(make_settings(tmp_path, seed=True))) as c:
        yield c


@pytest.fixture
def db(tmp_path: Path) -> Iterator[Database]:
    database = Database(tmp_path / "unit.db")
    database.migrate()
    yield database
    database.close()


# ----------------------------------------------------------------- API helpers
class Api:
    """Thin helper that asserts status codes so tests read as scenarios."""

    def __init__(self, client: TestClient) -> None:
        self.c = client

    def _ok(self, resp: Any, expected: int) -> Any:
        assert resp.status_code == expected, resp.text
        return resp.json() if resp.content else None

    def member(self, name: str = "אבא", **kw: Any) -> dict:
        return self._ok(self.c.post("/api/members", json={"name": name, **kw}), 201)

    def trip(self, name: str = "טיול", **kw: Any) -> dict:
        return self._ok(self.c.post("/api/trips", json={"name": name, **kw}), 201)

    def category(self, trip_id: int, name: str = "ביגוד", **kw: Any) -> dict:
        return self._ok(self.c.post(f"/api/trips/{trip_id}/categories", json={"name": name, **kw}), 201)

    def item(self, category_id: int, name: str = "חולצה", **kw: Any) -> dict:
        return self._ok(self.c.post(f"/api/categories/{category_id}/items", json={"name": name, **kw}), 201)

    def get_trip(self, trip_id: int) -> dict:
        return self._ok(self.c.get(f"/api/trips/{trip_id}"), 200)

    def patch_item(self, item_id: int, expected: int = 200, **changes: Any) -> dict:
        return self._ok(self.c.patch(f"/api/items/{item_id}", json=changes), expected)


@pytest.fixture
def api(client: TestClient) -> Api:
    return Api(client)


@pytest.fixture
def populated(api: Api) -> dict[str, Any]:
    """A trip with two categories, three items and two family members."""
    dad = api.member("אבא", color="#10b981", emoji="👨")
    kids = api.member("ילדים")
    trip = api.trip("חופשה ביוון", emoji="🇬🇷")
    docs = api.category(trip["id"], "מסמכים", icon="📄")
    clothes = api.category(trip["id"], "ביגוד", icon="👕")
    passport = api.item(docs["id"], "דרכונים", quantity=4, note="לבדוק תוקף", assignee_ids=[dad["id"]])
    shirts = api.item(clothes["id"], "חולצות", quantity=7, assignee_ids=[dad["id"], kids["id"]])
    hat = api.item(clothes["id"], "כובע", packed=True)
    return {
        "trip": trip,
        "docs": docs,
        "clothes": clothes,
        "passport": passport,
        "shirts": shirts,
        "hat": hat,
        "dad": dad,
        "kids": kids,
    }
