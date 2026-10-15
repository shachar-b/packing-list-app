"""Category endpoints, including bulk pack/unpack and nested item creation."""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.api.deps import DB, Bus, ClientId
from app.repositories import categories as repo
from app.repositories import items as items_repo
from app.repositories import trips as trips_repo
from app.schemas import Category, CategoryUpdate, Item, ItemCreate, PackAllRequest

router = APIRouter(prefix="/categories", tags=["categories"])


@router.patch("/{category_id}", response_model=Category)
async def update_category(category_id: int, body: CategoryUpdate, db: DB, bus: Bus, origin: ClientId) -> dict:
    with db.transaction():
        category = repo.update_category(db, category_id, body.changes())
        trips_repo.touch(db, category["trip_id"])
    await bus.publish("category.updated", category, trip_id=category["trip_id"], origin=origin)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: int, db: DB, bus: Bus, origin: ClientId) -> Response:
    with db.transaction():
        trip_id = repo.trip_id_for_category(db, category_id)
        repo.delete_category(db, category_id)
        trips_repo.touch(db, trip_id)
    await bus.publish("category.deleted", {"id": category_id}, trip_id=trip_id, origin=origin)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{category_id}/pack-all", response_model=Category)
async def pack_all(category_id: int, body: PackAllRequest, db: DB, bus: Bus, origin: ClientId) -> dict:
    """Mark every item in the category packed (or unpacked with ``{"packed": false}``)."""
    with db.transaction():
        trip_id = repo.trip_id_for_category(db, category_id)
        items_repo.set_packed_for_category(db, category_id, body.packed)
        trips_repo.touch(db, trip_id)
        category = repo.get_category(db, category_id)
    await bus.publish("category.updated", category, trip_id=trip_id, origin=origin)
    return category


@router.post("/{category_id}/items", response_model=Item, status_code=status.HTTP_201_CREATED)
async def create_item(category_id: int, body: ItemCreate, db: DB, bus: Bus, origin: ClientId) -> dict:
    with db.transaction():
        trip_id = repo.trip_id_for_category(db, category_id)
        item = items_repo.create_item(db, category_id, **body.model_dump())
        trips_repo.touch(db, trip_id)
    await bus.publish("item.created", item, trip_id=trip_id, origin=origin)
    return item
