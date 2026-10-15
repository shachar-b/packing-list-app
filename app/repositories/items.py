"""Item persistence, including the many-to-many assignee link table."""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from collections.abc import Sequence
from typing import Any

from app.db import Database
from app.errors import DomainValidationError, NotFoundError
from app.repositories import NOW_SQL, members

_COLUMNS = "i.id, i.category_id, i.name, i.packed, i.quantity, i.note, i.sort_order, i.updated_at"


def _assignees_for(db: Database, item_ids: Sequence[int]) -> dict[int, list[int]]:
    result: dict[int, list[int]] = defaultdict(list)
    if not item_ids:
        return result
    # Chunk to stay well below SQLITE_MAX_VARIABLE_NUMBER on old builds.
    for start in range(0, len(item_ids), 500):
        chunk = item_ids[start : start + 500]
        placeholders = ",".join("?" * len(chunk))
        rows = db.fetchall(
            "SELECT a.item_id, a.member_id FROM item_assignees a"
            " JOIN family_members m ON m.id = a.member_id"
            f" WHERE a.item_id IN ({placeholders}) ORDER BY m.position, m.id",
            chunk,
        )
        for r in rows:
            result[r["item_id"]].append(r["member_id"])
    return result


def rows_to_items(db: Database, rows: Sequence[sqlite3.Row]) -> list[dict[str, Any]]:
    assignees = _assignees_for(db, [r["id"] for r in rows])
    return [
        {**dict(r), "packed": bool(r["packed"]), "assignee_ids": assignees.get(r["id"], [])}
        for r in rows
    ]


def get_item(db: Database, item_id: int) -> dict[str, Any]:
    row = db.fetchone(f"SELECT {_COLUMNS} FROM items i WHERE i.id = ?", (item_id,))
    if row is None:
        raise NotFoundError(f"Item {item_id} not found")
    return rows_to_items(db, [row])[0]


def items_for_categories(db: Database, category_ids: Sequence[int]) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    if not category_ids:
        return grouped
    placeholders = ",".join("?" * len(category_ids))
    rows = db.fetchall(
        f"SELECT {_COLUMNS} FROM items i WHERE i.category_id IN ({placeholders}) ORDER BY i.sort_order, i.id",
        list(category_ids),
    )
    for item in rows_to_items(db, rows):
        grouped[item["category_id"]].append(item)
    return grouped


def trip_id_for_item(db: Database, item_id: int) -> int:
    row = db.fetchone(
        "SELECT c.trip_id FROM items i JOIN categories c ON c.id = i.category_id WHERE i.id = ?", (item_id,)
    )
    if row is None:
        raise NotFoundError(f"Item {item_id} not found")
    return int(row[0])


def _set_assignees(db: Database, item_id: int, member_ids: Sequence[int]) -> None:
    db.execute("DELETE FROM item_assignees WHERE item_id = ?", (item_id,))
    db.executemany(
        "INSERT INTO item_assignees (item_id, member_id) VALUES (?, ?)", [(item_id, m) for m in member_ids]
    )


def _next_sort_order(db: Database, category_id: int) -> int:
    row = db.fetchone("SELECT COALESCE(MAX(sort_order), -1) + 1 FROM items WHERE category_id = ?", (category_id,))
    return int(row[0])


def create_item(
    db: Database,
    category_id: int,
    *,
    name: str,
    quantity: int = 1,
    note: str | None = None,
    packed: bool = False,
    assignee_ids: Sequence[int] = (),
    sort_order: int | None = None,
) -> dict[str, Any]:
    member_ids = members.ensure_exist(db, assignee_ids)
    final_order = sort_order if sort_order is not None else _next_sort_order(db, category_id)
    cur = db.execute(
        "INSERT INTO items (category_id, name, quantity, note, packed, sort_order) VALUES (?, ?, ?, ?, ?, ?)",
        (category_id, name, quantity, note or None, int(packed), final_order),
    )
    item_id = int(cur.lastrowid)
    _set_assignees(db, item_id, member_ids)
    return get_item(db, item_id)


def update_item(db: Database, item_id: int, changes: dict[str, Any]) -> dict[str, Any]:
    current = get_item(db, item_id)
    columns: dict[str, Any] = {}
    for key in ("name", "quantity", "sort_order"):
        if key in changes:
            columns[key] = changes[key]
    if "note" in changes:
        columns["note"] = changes["note"] or None
    if "packed" in changes:
        columns["packed"] = int(changes["packed"])
    if "category_id" in changes and changes["category_id"] != current["category_id"]:
        target = changes["category_id"]
        same_trip = db.fetchone(
            "SELECT 1 FROM categories src JOIN categories dst ON dst.trip_id = src.trip_id"
            " WHERE src.id = ? AND dst.id = ?",
            (current["category_id"], target),
        )
        if same_trip is None:
            raise DomainValidationError("Target category must exist in the same trip")
        columns["category_id"] = target
        columns.setdefault("sort_order", _next_sort_order(db, target))

    if "assignee_ids" in changes:
        _set_assignees(db, item_id, members.ensure_exist(db, changes["assignee_ids"]))

    if columns or "assignee_ids" in changes:
        assignments = ", ".join(f"{k} = ?" for k in columns)
        sep = ", " if assignments else ""
        db.execute(
            f"UPDATE items SET {assignments}{sep}updated_at = {NOW_SQL} WHERE id = ?",
            (*columns.values(), item_id),
        )
    return get_item(db, item_id)


def delete_item(db: Database, item_id: int) -> None:
    cur = db.execute("DELETE FROM items WHERE id = ?", (item_id,))
    if cur.rowcount == 0:
        raise NotFoundError(f"Item {item_id} not found")


def set_packed_for_category(db: Database, category_id: int, packed: bool) -> int:
    cur = db.execute(
        f"UPDATE items SET packed = ?, updated_at = {NOW_SQL} WHERE category_id = ? AND packed != ?",
        (int(packed), category_id, int(packed)),
    )
    return cur.rowcount


def set_packed_for_trip(db: Database, trip_id: int, packed: bool) -> int:
    cur = db.execute(
        f"UPDATE items SET packed = ?, updated_at = {NOW_SQL}"
        " WHERE packed != ? AND category_id IN (SELECT id FROM categories WHERE trip_id = ?)",
        (int(packed), int(packed), trip_id),
    )
    return cur.rowcount
