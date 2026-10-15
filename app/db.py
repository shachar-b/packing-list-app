"""SQLite access layer: connection setup, explicit transactions and migrations.

Concurrency model
-----------------
The app runs as a single uvicorn worker. All request handlers are ``async`` and
perform their (sub-millisecond) SQLite work synchronously on the event-loop
thread inside short ``BEGIN IMMEDIATE`` transactions, so writes are naturally
serialised. A re-entrant lock guards the connection defensively in case any
code path ever touches it from a worker thread.
"""

from __future__ import annotations

import logging
import re
import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"
_MIGRATION_RE = re.compile(r"^(\d{4})_([\w-]+)\.sql$")


class Database:
    def __init__(self, path: Path | str) -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        # isolation_level=None → autocommit; transactions are explicit below.
        self._conn = sqlite3.connect(self.path, isolation_level=None, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self._depth = 0
        self._configure()

    # -- setup ---------------------------------------------------------------
    def _configure(self) -> None:
        c = self._conn
        c.execute("PRAGMA foreign_keys = ON")
        c.execute("PRAGMA busy_timeout = 5000")
        if self.path != ":memory:":
            c.execute("PRAGMA journal_mode = WAL")
            c.execute("PRAGMA synchronous = NORMAL")

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # -- queries -------------------------------------------------------------
    def execute(self, sql: str, params: Any = ()) -> sqlite3.Cursor:
        with self._lock:
            return self._conn.execute(sql, params)

    def executemany(self, sql: str, seq: Any) -> sqlite3.Cursor:
        with self._lock:
            return self._conn.executemany(sql, seq)

    def fetchone(self, sql: str, params: Any = ()) -> sqlite3.Row | None:
        with self._lock:
            return self._conn.execute(sql, params).fetchone()

    def fetchall(self, sql: str, params: Any = ()) -> list[sqlite3.Row]:
        with self._lock:
            return self._conn.execute(sql, params).fetchall()

    @contextmanager
    def transaction(self) -> Iterator["Database"]:
        """Explicit write transaction; nested calls join the outer transaction."""
        with self._lock:
            if self._depth:
                self._depth += 1
                try:
                    yield self
                finally:
                    self._depth -= 1
                return
            self._conn.execute("BEGIN IMMEDIATE")
            self._depth = 1
            try:
                yield self
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise
            else:
                self._conn.execute("COMMIT")
            finally:
                self._depth = 0

    # -- migrations ----------------------------------------------------------
    def migrate(self, migrations_dir: Path = MIGRATIONS_DIR) -> list[int]:
        """Apply pending ``NNNN_name.sql`` files in order. Returns applied versions."""
        with self._lock:
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations ("
                " version INTEGER PRIMARY KEY, name TEXT NOT NULL,"
                " applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')))"
            )
            done = {r[0] for r in self._conn.execute("SELECT version FROM schema_migrations")}
            applied: list[int] = []
            for file in sorted(migrations_dir.glob("*.sql")):
                m = _MIGRATION_RE.match(file.name)
                if not m:
                    log.warning("Ignoring unrecognised migration file", extra={"file": file.name})
                    continue
                version, name = int(m.group(1)), m.group(2)
                if version in done:
                    continue
                sql = file.read_text(encoding="utf-8")
                # executescript() can't be parameterised; name is validated by the regex.
                try:
                    self._conn.executescript(
                        f"BEGIN IMMEDIATE;\n{sql}\n"
                        f"INSERT INTO schema_migrations (version, name) VALUES ({version}, '{name}');\n"
                        "COMMIT;"
                    )
                except Exception:
                    if self._conn.in_transaction:
                        self._conn.execute("ROLLBACK")
                    log.exception("Migration failed", extra={"version": version})
                    raise
                log.info("Applied migration", extra={"version": version, "migration": name})
                applied.append(version)
            return applied

    def schema_version(self) -> int:
        row = self.fetchone("SELECT COALESCE(MAX(version), 0) FROM schema_migrations")
        return int(row[0]) if row else 0

    # -- meta ----------------------------------------------------------------
    def get_meta(self, key: str) -> str | None:
        row = self.fetchone("SELECT value FROM app_meta WHERE key = ?", (key,))
        return row["value"] if row else None

    def set_meta(self, key: str, value: str) -> None:
        self.execute(
            "INSERT INTO app_meta (key, value) VALUES (?, ?)"
            " ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
