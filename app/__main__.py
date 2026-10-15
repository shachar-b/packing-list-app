"""Entry point: ``python -m app`` (used by the systemd unit)."""

from __future__ import annotations

import uvicorn

from app.config import Settings
from app.logging_config import configure_logging


def main() -> None:
    settings = Settings.from_env()
    configure_logging(settings.log_level, settings.log_format)
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        workers=1,  # single writer by design — see app/db.py
        log_config=None,
        access_log=False,
        proxy_headers=True,
        forwarded_allow_ips="*",
        ws_ping_interval=20,
        ws_ping_timeout=20,
    )


if __name__ == "__main__":
    main()
