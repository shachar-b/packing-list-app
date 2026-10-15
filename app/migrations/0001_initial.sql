-- 0001_initial: core schema for trips, categories, items and family members.

CREATE TABLE family_members (
    id          INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL COLLATE NOCASE UNIQUE CHECK (length(trim(name)) > 0),
    color       TEXT    NOT NULL DEFAULT '#6366f1',
    emoji       TEXT,
    position    INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE trips (
    id          INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL CHECK (length(trim(name)) > 0),
    emoji       TEXT,
    is_template INTEGER NOT NULL DEFAULT 0 CHECK (is_template IN (0, 1)),
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE categories (
    id          INTEGER PRIMARY KEY,
    trip_id     INTEGER NOT NULL REFERENCES trips (id) ON DELETE CASCADE,
    name        TEXT    NOT NULL CHECK (length(trim(name)) > 0),
    icon        TEXT    NOT NULL DEFAULT '📦',
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
CREATE INDEX ix_categories_trip ON categories (trip_id, sort_order);

CREATE TABLE items (
    id          INTEGER PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES categories (id) ON DELETE CASCADE,
    name        TEXT    NOT NULL CHECK (length(trim(name)) > 0),
    packed      INTEGER NOT NULL DEFAULT 0 CHECK (packed IN (0, 1)),
    quantity    INTEGER NOT NULL DEFAULT 1 CHECK (quantity BETWEEN 1 AND 999),
    note        TEXT,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
CREATE INDEX ix_items_category ON items (category_id, sort_order);

CREATE TABLE item_assignees (
    item_id     INTEGER NOT NULL REFERENCES items (id) ON DELETE CASCADE,
    member_id   INTEGER NOT NULL REFERENCES family_members (id) ON DELETE CASCADE,
    PRIMARY KEY (item_id, member_id)
) WITHOUT ROWID;
CREATE INDEX ix_item_assignees_member ON item_assignees (member_id);

CREATE TABLE app_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
) WITHOUT ROWID;
