"""HTTP and WebSocket routers."""

from fastapi import APIRouter

from app.api import categories, health, items, members, transfer, trips, ws

api_router = APIRouter(prefix="/api")
for module in (health, members, trips, categories, items, transfer):
    api_router.include_router(module.router)

ws_router = ws.router

__all__ = ["api_router", "ws_router"]
