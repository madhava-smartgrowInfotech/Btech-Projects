"""Structured logging: one line per event, key=value fields, console and rotating file."""
from __future__ import annotations

import logging
import logging.handlers
from datetime import datetime, timezone

from app.core.config import LOGS_DIR

_RESERVED = set(vars(logging.makeLogRecord({}))) | {"message", "asctime", "taskName", "color_message"}


class KeyValueFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        stamp = datetime.fromtimestamp(record.created, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-4] + "Z"
        parts = [f"ts={stamp}", f"level={record.levelname}", f"logger={record.name}", f'msg="{record.getMessage()}"']
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                text = str(value)
                parts.append(f'{key}="{text}"' if " " in text else f"{key}={text}")
        line = " ".join(parts)
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        return line


def configure_logging(level: str = "INFO") -> None:
    LOGS_DIR.mkdir(exist_ok=True)
    formatter = KeyValueFormatter()
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    file_handler = logging.handlers.RotatingFileHandler(
        LOGS_DIR / "seatwise.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers[:] = [console, file_handler]
    root.setLevel(level)
    for noisy in ("uvicorn.access", "passlib", "multipart"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    for name in ("uvicorn", "uvicorn.error"):
        logging.getLogger(name).handlers[:] = []
        logging.getLogger(name).propagate = True
