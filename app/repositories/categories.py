"""Category persistence."""

from __future__ import annotations

from typing import Any

from app.db import Database
from app.errors import NotFoundError
from app.repositories import NOW_SQL, items

_COLUMNS = "id, trip_id, name, icon, sort_order"


def get_category(db: Database, category_id: int, *, with_items: bool = True) -> dict[str, Any]:
    row = db.fetchone(f"SELECT {_COLUMNS} FROM categories WHERE id = ?", (category_id,))
    if row is None:
        raise NotFoundError(f"Category {category_id} not found")
    category = dict(row)
    category["items"] = items.items_for_categories(db, [category_id]).get(category_id, []) if with_items else []
    return category


def categories_for_trip(db: Database, trip_id: int) -> list[dict[str, Any]]:
    rows = db.fetchall(f"SELECT {_COLUMNS} FROM categories WHERE trip_id = ? ORDER BY sort_order, id", (trip_id,))
    cats = [dict(r) for r in rows]
    by_cat = items.items_for_categories(db, [c["id"] for c in cats])
    for c in cats:
        c["items"] = by_cat.get(c["id"], [])
    return cats


def create_category(
    db: Database, trip_id: int, *, name: str, icon: str = "📦", sort_order: int | None = None
) -> dict[str, Any]:
    if sort_order is None:
        cur = db.execute(
            "INSERT INTO categories (trip_id, name, icon, sort_order)"
            " VALUES (?, ?, ?, (SELECT COALESCE(MAX(sort_order), -1) + 1 FROM categories WHERE trip_id = ?))",
            (trip_id, name, icon, trip_id),
        )
    else:
        cur = db.execute(
            "INSERT INTO categories (trip_id, name, icon, sort_order) VALUES (?, ?, ?, ?)",
            (trip_id, name, icon, sort_order),
        )
    return get_category(db, int(cur.lastrowid))


def update_category(db: Database, category_id: int, changes: dict[str, Any]) -> dict[str, Any]:
    get_category(db, category_id, with_items=False)
    allowed = {k: v for k, v in changes.items() if k in {"name", "icon", "sort_order"}}
    if allowed:
        assignments = ", ".join(f"{k} = ?" for k in allowed)
        db.execute(
            f"UPDATE categories SET {assignments}, updated_at = {NOW_SQL} WHERE id = ?",
            (*allowed.values(), category_id),
        )
    return get_category(db, category_id)


def delete_category(db: Database, category_id: int) -> None:
    cur = db.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    if cur.rowcount == 0:
        raise NotFoundError(f"Category {category_id} not found")


def trip_id_for_category(db: Database, category_id: int) -> int:
    row = db.fetchone("SELECT trip_id FROM categories WHERE id = ?", (category_id,))
    if row is None:
        raise NotFoundError(f"Category {category_id} not found")
    return int(row[0])
