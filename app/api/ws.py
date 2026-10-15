"""Real-time sync WebSocket endpoint.

Server → client: :class:`app.schemas.Event` JSON objects (plus ``hello``/``pong``).
Client → server: ``{"type": "ping"}`` keep-alive. Anything else is ignored.
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app import __version__

log = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, client_id: str | None = Query(default=None, max_length=64)) -> None:
    bus = ws.app.state.broadcaster
    await bus.connect(ws, client_id)
    try:
        await ws.send_json({"type": "hello", "version": __version__})
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except ValueError:
                continue
            if isinstance(msg, dict) and msg.get("type") == "ping":
                await ws.send_json({"type": "pong", "ts": msg.get("ts")})
    except WebSocketDisconnect:
        pass
    except Exception:  # noqa: BLE001
        log.warning("WebSocket error", exc_info=True)
    finally:
        bus.disconnect(ws)
