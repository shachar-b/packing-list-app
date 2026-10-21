"""Trip persistence and aggregate (summary / detail) queries."""

from __future__ import annotations

from typing import Any

from app.db import Database
from app.errors import NotFoundError
from app.repositories import NOW_SQL, categories

_SUMMARY_SQL = """
SELECT t.id, t.name, t.emoji, t.is_template, t.departure_date, t.created_at, t.updated_at,
       COUNT(i.id)                     AS total_items,
       COALESCE(SUM(i.packed), 0)      AS packed_items
FROM trips t
LEFT JOIN categories c ON c.trip_id = t.id
LEFT JOIN items i      ON i.category_id = c.id
{where}
GROUP BY t.id
ORDER BY t.is_template, t.updated_at DESC, t.id DESC
"""


def _summary(row: Any) -> dict[str, Any]:
    d = dict(row)
    d["is_template"] = bool(d["is_template"])
    return d


def list_summaries(db: Database) -> list[dict[str, Any]]:
    return [_summary(r) for r in db.fetchall(_SUMMARY_SQL.format(where=""))]


def get_summary(db: Database, trip_id: int) -> dict[str, Any]:
    row = db.fetchone(_SUMMARY_SQL.format(where="WHERE t.id = ?"), (trip_id,))
    if row is None:
        raise NotFoundError(f"Trip {trip_id} not found")
    return _summary(row)


def get_detail(db: Database, trip_id: int) -> dict[str, Any]:
    detail = get_summary(db, trip_id)
    detail["categories"] = categories.categories_for_trip(db, trip_id)
    return detail


def ensure_exists(db: Database, trip_id: int) -> None:
    if db.fetchone("SELECT 1 FROM trips WHERE id = ?", (trip_id,)) is None:
        raise NotFoundError(f"Trip {trip_id} not found")


def create_trip(
    db: Database,
    *,
    name: str,
    emoji: str | None = None,
    is_template: bool = False,
    departure_date: str | None = None,
) -> int:
    final_date = None if is_template else (departure_date or None)
    cur = db.execute(
        "INSERT INTO trips (name, emoji, is_template, departure_date) VALUES (?, ?, ?, ?)",
        (name, emoji or None, int(is_template), final_date),
    )
    return int(cur.lastrowid)


def update_trip(db: Database, trip_id: int, changes: dict[str, Any]) -> None:
    current = get_summary(db, trip_id)
    allowed: dict[str, Any] = {}
    if "name" in changes:
        allowed["name"] = changes["name"]
    if "emoji" in changes:
        allowed["emoji"] = changes["emoji"] or None
    if "is_template" in changes:
        allowed["is_template"] = int(changes["is_template"])
    if "departure_date" in changes:
        allowed["departure_date"] = changes["departure_date"] or None

    # Templates never carry a departure date
    resulting_is_template = bool(allowed.get("is_template", current["is_template"]))
    if resulting_is_template and ("is_template" in allowed or "departure_date" in allowed):
        allowed["departure_date"] = None

    if allowed:
        assignments = ", ".join(f"{k} = ?" for k in allowed)
        db.execute(
            f"UPDATE trips SET {assignments}, updated_at = {NOW_SQL} WHERE id = ?", (*allowed.values(), trip_id)
        )


def touch(db: Database, trip_id: int) -> None:
    """Bump ``updated_at`` so recently edited trips sort first."""
    db.execute(f"UPDATE trips SET updated_at = {NOW_SQL} WHERE id = ?", (trip_id,))


def delete_trip(db: Database, trip_id: int) -> None:
    cur = db.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
    if cur.rowcount == 0:
        raise NotFoundError(f"Trip {trip_id} not found")
