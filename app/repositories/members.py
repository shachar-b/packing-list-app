"""Family member persistence."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from typing import Any

from app.db import Database
from app.errors import ConflictError, DomainValidationError, NotFoundError

_COLUMNS = "id, name, color, emoji, position"


def _to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def list_members(db: Database) -> list[dict[str, Any]]:
    return [_to_dict(r) for r in db.fetchall(f"SELECT {_COLUMNS} FROM family_members ORDER BY position, id")]


def get_member(db: Database, member_id: int) -> dict[str, Any]:
    row = db.fetchone(f"SELECT {_COLUMNS} FROM family_members WHERE id = ?", (member_id,))
    if row is None:
        raise NotFoundError(f"Family member {member_id} not found")
    return _to_dict(row)


def find_by_name(db: Database, name: str) -> dict[str, Any] | None:
    row = db.fetchone(f"SELECT {_COLUMNS} FROM family_members WHERE name = ?", (name.strip(),))
    return _to_dict(row) if row else None


def create_member(db: Database, name: str, color: str = "#6366f1", emoji: str | None = None) -> dict[str, Any]:
    try:
        cur = db.execute(
            "INSERT INTO family_members (name, color, emoji, position)"
            " VALUES (?, ?, ?, (SELECT COALESCE(MAX(position), -1) + 1 FROM family_members))",
            (name, color, emoji),
        )
    except sqlite3.IntegrityError as exc:
        raise ConflictError(f"A family member named '{name}' already exists") from exc
    return get_member(db, int(cur.lastrowid))


def update_member(db: Database, member_id: int, changes: dict[str, Any]) -> dict[str, Any]:
    get_member(db, member_id)
    allowed = {k: v for k, v in changes.items() if k in {"name", "color", "emoji", "position"}}
    if allowed:
        assignments = ", ".join(f"{k} = ?" for k in allowed)
        try:
            db.execute(f"UPDATE family_members SET {assignments} WHERE id = ?", (*allowed.values(), member_id))
        except sqlite3.IntegrityError as exc:
            raise ConflictError(f"A family member named '{allowed.get('name')}' already exists") from exc
    return get_member(db, member_id)


def delete_member(db: Database, member_id: int) -> None:
    get_member(db, member_id)
    db.execute("DELETE FROM family_members WHERE id = ?", (member_id,))


def ensure_exist(db: Database, member_ids: Iterable[int]) -> list[int]:
    """Validate and de-duplicate member ids (order preserved)."""
    unique = list(dict.fromkeys(member_ids))
    if not unique:
        return []
    placeholders = ",".join("?" * len(unique))
    found = {r[0] for r in db.fetchall(f"SELECT id FROM family_members WHERE id IN ({placeholders})", unique)}
    missing = [i for i in unique if i not in found]
    if missing:
        raise DomainValidationError("Unknown family member id(s)", details={"missing": missing})
    return unique
