"""Shared FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, Request

from app.db import Database
from app.realtime import Broadcaster


def get_db(request: Request) -> Database:
    return request.app.state.db


def get_broadcaster(request: Request) -> Broadcaster:
    return request.app.state.broadcaster


def get_client_id(x_client_id: Annotated[str | None, Header(max_length=64)] = None) -> str | None:
    """Opaque per-tab id so clients can ignore echoes of their own changes."""
    return x_client_id


DB = Annotated[Database, Depends(get_db)]
Bus = Annotated[Broadcaster, Depends(get_broadcaster)]
ClientId = Annotated[str | None, Depends(get_client_id)]
