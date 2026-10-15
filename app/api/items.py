"""Item endpoints. PATCH applies only the fields present in the request body."""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.api.deps import DB, Bus, ClientId
from app.repositories import items as repo
from app.repositories import trips as trips_repo
from app.schemas import Item, ItemUpdate

router = APIRouter(prefix="/items", tags=["items"])


@router.patch("/{item_id}", response_model=Item)
async def update_item(item_id: int, body: ItemUpdate, db: DB, bus: Bus, origin: ClientId) -> dict:
    with db.transaction():
        trip_id = repo.trip_id_for_item(db, item_id)
        item = repo.update_item(db, item_id, body.changes())
        trips_repo.touch(db, trip_id)
    await bus.publish("item.updated", item, trip_id=trip_id, origin=origin)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int, db: DB, bus: Bus, origin: ClientId) -> Response:
    with db.transaction():
        trip_id = repo.trip_id_for_item(db, item_id)
        category_id = repo.get_item(db, item_id)["category_id"]
        repo.delete_item(db, item_id)
        trips_repo.touch(db, trip_id)
    await bus.publish("item.deleted", {"id": item_id, "category_id": category_id}, trip_id=trip_id, origin=origin)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
