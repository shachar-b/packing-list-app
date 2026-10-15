"""Application factory."""

from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app import __version__
from app.api import api_router, ws_router
from app.config import Settings
from app.db import Database
from app.errors import install_error_handlers
from app.realtime import Broadcaster
from app.services.seed import seed_if_needed

log = logging.getLogger("app")


class RequestLogMiddleware:
    """Pure-ASGI access log + response headers (cheaper than BaseHTTPMiddleware)."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        start = time.perf_counter()
        path: str = scope["path"]
        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = list(message.get("headers", []))
                message["headers"] = headers
                headers.append((b"x-content-type-options", b"nosniff"))
                headers.append((b"referrer-policy", b"same-origin"))
                if path.startswith("/api/"):
                    headers.append((b"cache-control", b"no-store"))
                else:
                    # Static assets: always revalidate (ETag → 304) so deploys apply instantly.
                    headers.append((b"cache-control", b"no-cache"))
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            if path.startswith("/api/"):
                log.info(
                    "request",
                    extra={
                        "method": scope["method"],
                        "path": path,
                        "status": status_code,
                        "duration_ms": round((time.perf_counter() - start) * 1000, 2),
                    },
                )


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        db = Database(settings.db_path)
        db.migrate()
        if settings.seed_on_first_boot:
            seed_if_needed(db)
        app.state.db = db
        app.state.broadcaster = Broadcaster()
        log.info("Started", extra={"version": __version__, "db": str(settings.db_path)})
        try:
            yield
        finally:
            db.close()
            log.info("Stopped")

    app = FastAPI(
        title="Family Packing List",
        version=__version__,
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    app.state.settings = settings
    install_error_handlers(app)
    app.add_middleware(RequestLogMiddleware)
    app.include_router(api_router)
    app.include_router(ws_router)

    if settings.serve_frontend and settings.frontend_dir.is_dir():
        app.mount("/", StaticFiles(directory=settings.frontend_dir, html=True), name="frontend")
    return app


app = create_app()
