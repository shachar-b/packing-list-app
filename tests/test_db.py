"""Database layer: migrations, PRAGMAs, transactions and cascades."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.db import Database


def test_migrations_create_schema(db: Database) -> None:
    tables = {r[0] for r in db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"trips", "categories", "items", "family_members", "item_assignees", "schema_migrations"} <= tables
    assert db.schema_version() == 2


def test_migrations_are_idempotent(db: Database) -> None:
    assert db.migrate() == []
    assert db.schema_version() == 2


def test_new_migration_is_applied_once(db: Database, tmp_path: Path) -> None:
    mig_dir = tmp_path / "migs"
    mig_dir.mkdir()
    (mig_dir / "0001_initial.sql").write_text("SELECT 1;", encoding="utf-8")
    (mig_dir / "0002_trip_departure_date.sql").write_text("SELECT 1;", encoding="utf-8")
    (mig_dir / "0003_add_flag.sql").write_text("ALTER TABLE trips ADD COLUMN archived INTEGER DEFAULT 0;")
    (mig_dir / "README.txt").write_text("ignored")
    assert db.migrate(mig_dir) == [3]
    assert db.migrate(mig_dir) == []
    cols = {r["name"] for r in db.fetchall("PRAGMA table_info(trips)")}
    assert "archived" in cols


def test_failed_migration_rolls_back(db: Database, tmp_path: Path) -> None:
    mig_dir = tmp_path / "migs"
    mig_dir.mkdir()
    (mig_dir / "0003_broken.sql").write_text("CREATE TABLE ok_table (id INTEGER); THIS IS NOT SQL;")
    with pytest.raises(sqlite3.Error):
        db.migrate(mig_dir)
    assert db.fetchone("SELECT name FROM sqlite_master WHERE name='ok_table'") is None
    assert db.schema_version() == 2


def test_pragmas(db: Database) -> None:
    assert db.fetchone("PRAGMA foreign_keys")[0] == 1
    assert db.fetchone("PRAGMA journal_mode")[0].lower() == "wal"


def test_transaction_rolls_back_on_error(db: Database) -> None:
    with pytest.raises(RuntimeError):
        with db.transaction():
            db.execute("INSERT INTO trips (name) VALUES ('x')")
            raise RuntimeError("boom")
    assert db.fetchone("SELECT COUNT(*) FROM trips")[0] == 0


def test_nested_transaction_joins_outer(db: Database) -> None:
    with pytest.raises(RuntimeError):
        with db.transaction():
            db.execute("INSERT INTO trips (name) VALUES ('outer')")
            with db.transaction():
                db.execute("INSERT INTO trips (name) VALUES ('inner')")
            raise RuntimeError("boom")
    assert db.fetchone("SELECT COUNT(*) FROM trips")[0] == 0


def test_delete_trip_cascades(db: Database) -> None:
    with db.transaction():
        trip = db.execute("INSERT INTO trips (name) VALUES ('t')").lastrowid
        cat = db.execute("INSERT INTO categories (trip_id, name) VALUES (?, 'c')", (trip,)).lastrowid
        item = db.execute("INSERT INTO items (category_id, name) VALUES (?, 'i')", (cat,)).lastrowid
        member = db.execute("INSERT INTO family_members (name) VALUES ('m')").lastrowid
        db.execute("INSERT INTO item_assignees VALUES (?, ?)", (item, member))
        db.execute("DELETE FROM trips WHERE id = ?", (trip,))
    for table in ("categories", "items", "item_assignees"):
        assert db.fetchone(f"SELECT COUNT(*) FROM {table}")[0] == 0
    assert db.fetchone("SELECT COUNT(*) FROM family_members")[0] == 1


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO trips (name) VALUES ('   ')",
        "INSERT INTO items (category_id, name) VALUES (999, 'orphan')",
        "INSERT INTO trips (name, is_template) VALUES ('x', 5)",
    ],
)
def test_schema_constraints(db: Database, sql: str) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(sql)


def test_meta_roundtrip(db: Database) -> None:
    assert db.get_meta("k") is None
    db.set_meta("k", "v1")
    db.set_meta("k", "v2")
    assert db.get_meta("k") == "v2"
