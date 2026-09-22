"""Background loops started with the API: zone housekeeping and the notification retry queue."""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

from sqlalchemy.orm import Session

from ..core.db import SessionLocal
from . import notifier, zone_engine

log = logging.getLogger("signalscout.background")


def _run(fn: Callable[[Session], object]) -> None:
    with SessionLocal() as db:
        try:
            fn(db)
        except Exception:
            db.rollback()
            log.exception("background task failed", extra={"fields": {"task": fn.__name__}})


async def _loop(fn: Callable[[Session], object], every_s: float, first_delay_s: float) -> None:
    await asyncio.sleep(first_delay_s)
    while True:
        await asyncio.to_thread(_run, fn)
        await asyncio.sleep(every_s)


def start() -> list[asyncio.Task]:
    return [
        asyncio.create_task(_loop(zone_engine.sweep, 30, 10), name="zone-sweep"),
        asyncio.create_task(_loop(notifier.send_pending, 15, 5), name="notifications"),
    ]
