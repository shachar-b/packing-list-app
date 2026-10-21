"""JSON export / import (manual backup & restore).

Import is *additive*: it always creates new trips and never overwrites existing
data. Family members are matched by name (case-insensitive); unknown names are
created.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone

from app.db import Database
from app.repositories import categories as categories_repo
from app.repositories import items as items_repo
from app.repositories import members as members_repo
from app.repositories import trips as trips_repo
from app.schemas import (
    ExportCategory,
    ExportDocument,
    ExportItem,
    ExportMember,
    ExportTrip,
)


def export_document(db: Database, trip_ids: Sequence[int] | None = None) -> ExportDocument:
    all_members = members_repo.list_members(db)
    names = {m["id"]: m["name"] for m in all_members}
    is_full_backup = trip_ids is None
    if trip_ids is None:
        trip_ids = [t["id"] for t in trips_repo.list_summaries(db)]

    exported: list[ExportTrip] = []
    used_members: set[int] = set()
    for trip_id in trip_ids:
        detail = trips_repo.get_detail(db, trip_id)
        cats: list[ExportCategory] = []
        for c in detail["categories"]:
            exported_items = []
            for i in c["items"]:
                used_members.update(i["assignee_ids"])
                exported_items.append(
                    ExportItem(
                        name=i["name"],
                        quantity=i["quantity"],
                        note=i["note"],
                        packed=i["packed"],
                        assignees=[names[m] for m in i["assignee_ids"] if m in names],
                    )
                )
            cats.append(ExportCategory(name=c["name"], icon=c["icon"], items=exported_items))
        exported.append(
            ExportTrip(
                name=detail["name"],
                emoji=detail["emoji"],
                is_template=detail["is_template"],
                departure_date=detail.get("departure_date"),
                categories=cats,
            )
        )

    member_list = [
        ExportMember(name=m["name"], color=m["color"], emoji=m["emoji"])
        for m in all_members
        if is_full_backup or m["id"] in used_members
    ]
    return ExportDocument(
        exported_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        members=member_list,
        trips=exported,
    )


def import_document(db: Database, doc: ExportDocument) -> tuple[list[int], list[dict]]:
    """Create trips from ``doc``. Must run inside a transaction.

    Returns ``(new_trip_ids, created_members)``.
    """
    created: list[dict] = []
    by_name: dict[str, int] = {m["name"].casefold(): m["id"] for m in members_repo.list_members(db)}

    def resolve(name: str, color: str = "#6366f1", emoji: str | None = None) -> int:
        key = name.strip().casefold()
        if key not in by_name:
            member = members_repo.create_member(db, name.strip(), color, emoji)
            by_name[key] = member["id"]
            created.append(member)
        return by_name[key]

    for m in doc.members:
        resolve(m.name, m.color, m.emoji)

    new_ids: list[int] = []
    for t in doc.trips:
        trip_id = trips_repo.create_trip(
            db,
            name=t.name,
            emoji=t.emoji,
            is_template=t.is_template,
            departure_date=t.departure_date,
        )
        for c in t.categories:
            cat_id = categories_repo.create_category(db, trip_id, name=c.name, icon=c.icon)["id"]
            for i in c.items:
                items_repo.create_item(
                    db,
                    cat_id,
                    name=i.name,
                    quantity=i.quantity,
                    note=i.note,
                    packed=i.packed,
                    assignee_ids=[resolve(n) for n in i.assignees],
                )
        new_ids.append(trip_id)
    return new_ids, created
