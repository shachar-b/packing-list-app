"""Trip endpoints, including cloning, bulk reset and category creation."""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.api.deps import DB, Bus, ClientId
from app.repositories import categories as categories_repo
from app.repositories import items as items_repo
from app.repositories import trips as repo
from app.schemas import Category, CategoryCreate, CloneRequest, TripCreate, TripDetail, TripSummary, TripUpdate
from app.services.cloning import clone_trip

router = APIRouter(prefix="/trips", tags=["trips"])


def _summary_of(detail: dict) -> dict:
    return {k: v for k, v in detail.items() if k != "categories"}


@router.get("", response_model=list[TripSummary])
async def list_trips(db: DB) -> list[dict]:
    return repo.list_summaries(db)


@router.post("", response_model=TripDetail, status_code=status.HTTP_201_CREATED)
async def create_trip(body: TripCreate, db: DB, bus: Bus, origin: ClientId) -> dict:
    with db.transaction():
        if body.source_trip_id is not None:
            trip_id = clone_trip(
                db,
                body.source_trip_id,
                name=body.name,
                emoji=body.emoji,
                is_template=body.is_template,
                departure_date=body.departure_date,
            )
        else:
            trip_id = repo.create_trip(
                db,
                name=body.name,
                emoji=body.emoji,
                is_template=body.is_template,
                departure_date=body.departure_date,
            )
        detail = repo.get_detail(db, trip_id)
    await bus.publish("trip.created", _summary_of(detail), trip_id=trip_id, origin=origin)
    return detail


@router.get("/{trip_id}", response_model=TripDetail)
async def get_trip(trip_id: int, db: DB) -> dict:
    return repo.get_detail(db, trip_id)


@router.patch("/{trip_id}", response_model=TripSummary)
async def update_trip(trip_id: int, body: TripUpdate, db: DB, bus: Bus, origin: ClientId) -> dict:
    with db.transaction():
        repo.update_trip(db, trip_id, body.changes())
        summary = repo.get_summary(db, trip_id)
    await bus.publish("trip.updated", summary, trip_id=trip_id, origin=origin)
    return summary


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip(trip_id: int, db: DB, bus: Bus, origin: ClientId) -> Response:
    with db.transaction():
        repo.delete_trip(db, trip_id)
    await bus.publish("trip.deleted", {"id": trip_id}, trip_id=trip_id, origin=origin)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{trip_id}/clone", response_model=TripDetail, status_code=status.HTTP_201_CREATED)
async def clone(trip_id: int, body: CloneRequest, db: DB, bus: Bus, origin: ClientId) -> dict:
    with db.transaction():
        new_id = clone_trip(
            db,
            trip_id,
            name=body.name,
            emoji=body.emoji,
            is_template=body.is_template,
            departure_date=body.departure_date,
        )
        detail = repo.get_detail(db, new_id)
    await bus.publish("trip.created", _summary_of(detail), trip_id=new_id, origin=origin)
    return detail


@router.post("/{trip_id}/reset", response_model=TripDetail)
async def reset(trip_id: int, db: DB, bus: Bus, origin: ClientId) -> dict:
    """Uncheck every item in the trip."""
    with db.transaction():
        repo.ensure_exists(db, trip_id)
        items_repo.set_packed_for_trip(db, trip_id, False)
        repo.touch(db, trip_id)
        detail = repo.get_detail(db, trip_id)
    await bus.publish("trip.snapshot", detail, trip_id=trip_id, origin=origin)
    return detail


@router.post("/{trip_id}/categories", response_model=Category, status_code=status.HTTP_201_CREATED)
async def create_category(trip_id: int, body: CategoryCreate, db: DB, bus: Bus, origin: ClientId) -> dict:
    with db.transaction():
        repo.ensure_exists(db, trip_id)
        category = categories_repo.create_category(db, trip_id, name=body.name, icon=body.icon)
        repo.touch(db, trip_id)
    await bus.publish("category.created", category, trip_id=trip_id, origin=origin)
    return category
