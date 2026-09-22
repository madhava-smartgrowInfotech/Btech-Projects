"""Background loop that closes Delayed Protection holds when their time is up."""
from __future__ import annotations

import asyncio

from app.core.db import session_scope
from app.core.logging import get_logger
from app.models import CollectRequest, utcnow

log = get_logger("upi_guardian.scheduler")


def tick() -> int:
    from sqlalchemy import select

    from app.services.holds import process_due_holds

    with session_scope() as db:
        closed = process_due_holds(db)
        now = utcnow()
        for req in db.scalars(
            select(CollectRequest).where(CollectRequest.status == "pending", CollectRequest.expires_at <= now)
        ):
            req.status = "expired"
    return closed


async def run_forever(interval_seconds: int) -> None:
    while True:
        try:
            await asyncio.to_thread(tick)
        except Exception:
            log.exception("scheduler tick failed")
        await asyncio.sleep(max(1, interval_seconds))
