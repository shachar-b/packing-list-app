"""Trip cloning: copy a trip/template's categories, items and assignees."""

from __future__ import annotations

from app.db import Database
from app.repositories import trips


def clone_trip(
    db: Database,
    source_trip_id: int,
    *,
    name: str,
    emoji: str | None = None,
    is_template: bool = False,
    departure_date: str | None = None,
    keep_packed: bool = False,
) -> int:
    """Create a new trip from ``source_trip_id``. Packed flags are reset unless ``keep_packed``.

    Must be called inside a transaction. Returns the new trip id.
    """
    source = db.fetchone("SELECT emoji FROM trips WHERE id = ?", (source_trip_id,))
    if source is None:
        trips.ensure_exists(db, source_trip_id)  # raises NotFoundError
    new_trip_id = trips.create_trip(
        db,
        name=name,
        emoji=emoji if emoji is not None else source["emoji"],
        is_template=is_template,
        departure_date=departure_date,
    )

    categories = db.fetchall(
        "SELECT id, name, icon, sort_order FROM categories WHERE trip_id = ? ORDER BY sort_order, id",
        (source_trip_id,),
    )
    for cat in categories:
        new_cat_id = db.execute(
            "INSERT INTO categories (trip_id, name, icon, sort_order) VALUES (?, ?, ?, ?)",
            (new_trip_id, cat["name"], cat["icon"], cat["sort_order"]),
        ).lastrowid
        items = db.fetchall(
            "SELECT id, name, packed, quantity, note, sort_order FROM items WHERE category_id = ? ORDER BY sort_order, id",
            (cat["id"],),
        )
        for item in items:
            new_item_id = db.execute(
                "INSERT INTO items (category_id, name, packed, quantity, note, sort_order) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    new_cat_id,
                    item["name"],
                    item["packed"] if keep_packed else 0,
                    item["quantity"],
                    item["note"],
                    item["sort_order"],
                ),
            ).lastrowid
            db.execute(
                "INSERT INTO item_assignees (item_id, member_id)"
                " SELECT ?, member_id FROM item_assignees WHERE item_id = ?",
                (new_item_id, item["id"]),
            )
    return new_trip_id
