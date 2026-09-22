"""In-app notifications: stored in the database and pushed live over WebSocket."""
from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from typing import Any

from fastapi import WebSocket
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.logging import get_logger
from app.models import Notification

log = get_logger("upi_guardian.notify")

_loop: asyncio.AbstractEventLoop | None = None
_sockets: dict[int, set[WebSocket]] = defaultdict(set)


def bind_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _loop
    _loop = loop


async def connect(user_id: int, ws: WebSocket) -> None:
    await ws.accept()
    _sockets[user_id].add(ws)


def disconnect(user_id: int, ws: WebSocket) -> None:
    _sockets[user_id].discard(ws)


async def _send(user_id: int, message: dict[str, Any]) -> None:
    dead = []
    for ws in list(_sockets.get(user_id, ())):
        try:
            await ws.send_text(json.dumps(message, default=str))
        except Exception:
            dead.append(ws)
    for ws in dead:
        disconnect(user_id, ws)


def push(user_id: int, message: dict[str, Any]) -> None:
    """Thread-safe live push (request handlers run in a worker thread)."""
    if _loop is None or not _sockets.get(user_id):
        return
    try:
        running = asyncio.get_running_loop()
    except RuntimeError:
        running = None
    if running is _loop:
        _loop.create_task(_send(user_id, message))
    else:
        asyncio.run_coroutine_threadsafe(_send(user_id, message), _loop)


def notify(db: Session, user_id: int, kind: str, payload: dict[str, Any]) -> Notification:
    """Store a notification and push it live once the surrounding transaction commits."""
    note = Notification(user_id=user_id, kind=kind, payload=payload)
    db.add(note)
    db.flush()
    message = {"type": "notification", "id": note.id, "kind": kind, "payload": payload}
    pending = db.info.setdefault("pending_pushes", [])
    pending.append((user_id, message))
    return note


def flush_pushes(db: Session) -> None:
    for user_id, message in db.info.pop("pending_pushes", []):
        push(user_id, message)


@event.listens_for(SessionLocal, "after_commit")
def _after_commit(session: Session) -> None:
    flush_pushes(session)


@event.listens_for(SessionLocal, "after_soft_rollback")
def _after_rollback(session: Session, _previous) -> None:
    session.info.pop("pending_pushes", None)
