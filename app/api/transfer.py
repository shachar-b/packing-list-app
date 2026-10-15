"""JSON export / import endpoints."""

from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.api.deps import DB, Bus, ClientId
from app.repositories import trips as trips_repo
from app.schemas import ExportDocument, ImportResult
from app.services.transfer import export_document, import_document

router = APIRouter(tags=["import-export"])


def _download(doc: ExportDocument, filename: str) -> JSONResponse:
    return JSONResponse(
        doc.model_dump(mode="json"),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export", response_model=ExportDocument)
async def export_all(db: DB) -> JSONResponse:
    """Full backup: every trip and template plus all family members."""
    return _download(export_document(db), "packing-backup.json")


@router.get("/trips/{trip_id}/export", response_model=ExportDocument)
async def export_trip(trip_id: int, db: DB) -> JSONResponse:
    trips_repo.ensure_exists(db, trip_id)
    return _download(export_document(db, [trip_id]), f"packing-trip-{trip_id}.json")


@router.post("/import", response_model=ImportResult, status_code=status.HTTP_201_CREATED)
async def import_(body: ExportDocument, db: DB, bus: Bus, origin: ClientId) -> dict:
    """Additive restore: creates new trips; never modifies existing ones."""
    with db.transaction():
        trip_ids, new_members = import_document(db, body)
        summaries = [trips_repo.get_summary(db, t) for t in trip_ids]
    for member in new_members:
        await bus.publish("member.created", member, origin=origin)
    for summary in summaries:
        await bus.publish("trip.created", summary, trip_id=summary["id"], origin=origin)
    return {"trips": summaries, "members_created": len(new_members)}
