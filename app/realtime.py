"""WebSocket connection manager and event broadcaster."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import WebSocket

from app.schemas import Event

log = logging.getLogger(__name__)

SEND_TIMEOUT_S = 5.0


class Broadcaster:
    def __init__(self) -> None:
        self._clients: dict[WebSocket, str | None] = {}

    @property
    def connection_count(self) -> int:
        return len(self._clients)

    async def connect(self, ws: WebSocket, client_id: str | None) -> None:
        await ws.accept()
        self._clients[ws] = client_id
        log.info("WebSocket connected", extra={"client_id": client_id, "connections": len(self._clients)})

    def disconnect(self, ws: WebSocket) -> None:
        client_id = self._clients.pop(ws, None)
        log.info("WebSocket disconnected", extra={"client_id": client_id, "connections": len(self._clients)})

    async def _send(self, ws: WebSocket, payload: dict[str, Any]) -> bool:
        try:
            await asyncio.wait_for(ws.send_json(payload), timeout=SEND_TIMEOUT_S)
            return True
        except Exception:  # noqa: BLE001 — any failure means the socket is unusable
            return False

    async def publish(
        self,
        type_: str,
        data: dict[str, Any],
        *,
        trip_id: int | None = None,
        origin: str | None = None,
    ) -> None:
        """Send an event to every connected client. Dead sockets are dropped."""
        payload = Event(type=type_, trip_id=trip_id, origin=origin, data=data).model_dump(mode="json")
        clients = list(self._clients)
        if not clients:
            return
        results = await asyncio.gather(*(self._send(ws, payload) for ws in clients))
        for ws, ok in zip(clients, results):
            if not ok:
                self.disconnect(ws)
        log.debug("Broadcast", extra={"event": type_, "trip_id": trip_id, "recipients": len(clients)})
