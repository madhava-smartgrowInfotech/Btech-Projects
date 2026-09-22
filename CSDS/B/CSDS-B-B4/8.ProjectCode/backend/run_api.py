"""Starts the UPI Guardian API on the port from .env (default 8204)."""
from __future__ import annotations

import socket
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import uvicorn  # noqa: E402

from app.core.config import get_settings  # noqa: E402


def port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def main() -> int:
    settings = get_settings()
    if not port_free(settings.api_host, settings.api_port):
        print(
            f"[x] Port {settings.api_port} is already in use. UPI Guardian may already be running "
            f"(use stop.bat), or another program is using it."
        )
        return 1
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
        access_log=False,
        app_dir=str(Path(__file__).resolve().parent),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
