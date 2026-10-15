"""Liveness / readiness endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.api.deps import DB, Bus
from app.schemas import Health

router = APIRouter(tags=["health"])


@router.get("/health", response_model=Health)
async def health(db: DB, bus: Bus) -> Health:
    db.fetchone("SELECT 1")
    return Health(status="ok", version=__version__, schema_version=db.schema_version(), connections=bus.connection_count)
