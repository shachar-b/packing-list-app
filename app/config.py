"""Runtime configuration, read from ``PACKING_*`` environment variables.

Kept dependency-free (no pydantic-settings) to minimise footprint on the LXC.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FRONTEND_DIR = PROJECT_ROOT / "frontend"


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    db_path: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "packing.db")
    frontend_dir: Path = DEFAULT_FRONTEND_DIR
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    log_format: str = "text"  # "text" | "json"
    seed_on_first_boot: bool = True
    serve_frontend: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        defaults = cls()
        return cls(
            db_path=Path(os.environ.get("PACKING_DB_PATH", str(defaults.db_path))),
            frontend_dir=Path(os.environ.get("PACKING_FRONTEND_DIR", str(defaults.frontend_dir))),
            host=os.environ.get("PACKING_HOST", defaults.host),
            port=int(os.environ.get("PACKING_PORT", str(defaults.port))),
            log_level=os.environ.get("PACKING_LOG_LEVEL", defaults.log_level).upper(),
            log_format=os.environ.get("PACKING_LOG_FORMAT", defaults.log_format).lower(),
            seed_on_first_boot=_env_bool("PACKING_SEED", defaults.seed_on_first_boot),
            serve_frontend=_env_bool("PACKING_SERVE_FRONTEND", defaults.serve_frontend),
        )
