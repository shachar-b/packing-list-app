"""Data-access layer. Functions here contain SQL only — no HTTP or broadcasting.

All mutating functions expect to be called inside ``db.transaction()``.
"""

NOW_SQL = "strftime('%Y-%m-%dT%H:%M:%fZ','now')"
