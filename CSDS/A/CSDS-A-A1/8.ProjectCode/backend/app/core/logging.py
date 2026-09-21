"""Structured logging: ``key=value`` lines to the console and ``logs/backend.log``."""

from __future__ import annotations

import logging
import logging.handlers
from typing import Any

from app.core.config import get_settings

_CONFIGURED = False


class KeyValueFormatter(logging.Formatter):
    """Formats ``logger.info("event", extra={"fields": {...}})`` as ``event key=value ...``."""

    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        fields: dict[str, Any] | None = getattr(record, "fields", None)
        if fields:
            parts = []
            for key, value in fields.items():
                text = str(value)
                if " " in text or not text:
                    text = '"' + text.replace('"', "'") + '"'
                parts.append(f"{key}={text}")
            base = f"{base} {' '.join(parts)}"
        return base


def configure_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    settings = get_settings()
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    fmt = KeyValueFormatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S")

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    file_handler = logging.handlers.RotatingFileHandler(
        settings.logs_dir / "backend.log", maxBytes=5_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)

    root = logging.getLogger("policylens")
    root.setLevel(settings.log_level)
    root.handlers = [console, file_handler]
    root.propagate = False

    for noisy in ("httpx", "httpcore", "chromadb", "sentence_transformers", "urllib3", "google_genai"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"policylens.{name}")


def log_event(logger: logging.Logger, event: str, level: int = logging.INFO, **fields: Any) -> None:
    logger.log(level, event, extra={"fields": fields})
