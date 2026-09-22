from __future__ import annotations

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.db import SessionLocal, get_db
from app.core.deps import get_current_user, user_from_token
from app.models import CollectRequest, Hold, Notification, User, utcnow
from app.services import notifier

router = APIRouter(tags=["notifications"])


class ReadIn(BaseModel):
    ids: list[int] | None = None  # None marks everything as read


@router.get("/notifications")
def list_notifications(
    limit: int = Query(30, ge=1, le=100), user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    rows = db.scalars(
        select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(limit)
    ).all()
    unread = db.scalar(select(func.count(Notification.id)).where(Notification.user_id == user.id, Notification.read_at.is_(None)))
    return {
        "unread": unread or 0,
        "items": [
            {"id": n.id, "kind": n.kind, "payload": n.payload, "read": n.read_at is not None, "created_at": n.created_at}
            for n in rows
        ],
    }


@router.post("/notifications/read", status_code=204)
def mark_read(body: ReadIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    stmt = update(Notification).where(Notification.user_id == user.id, Notification.read_at.is_(None))
    if body.ids:
        stmt = stmt.where(Notification.id.in_(body.ids))
    db.execute(stmt.values(read_at=utcnow()))
    db.commit()


@router.get("/notifications/summary")
def badges(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Counts for the navigation badges."""
    collect = db.scalar(
        select(func.count(CollectRequest.id)).where(
            CollectRequest.payer_wallet_id == user.wallet.id, CollectRequest.status == "pending"
        )
    )
    approvals = db.scalar(
        select(func.count(Hold.id)).where(
            Hold.approver_user_id == user.id, Hold.status == "active", Hold.approval_status == "pending"
        )
    )
    unread = db.scalar(select(func.count(Notification.id)).where(Notification.user_id == user.id, Notification.read_at.is_(None)))
    return {"collect": collect or 0, "approvals": approvals or 0, "unread": unread or 0}


@router.websocket("/ws")
async def live_updates(ws: WebSocket, token: str = Query(...)) -> None:
    with SessionLocal() as db:
        user = user_from_token(token, db)
        user_id = user.id if user else None
    if user_id is None:
        await ws.close(code=4401)
        return
    await notifier.connect(user_id, ws)
    try:
        await ws.send_json({"type": "hello"})
        while True:
            msg = await ws.receive_text()
            if msg == "ping":
                await ws.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        notifier.disconnect(user_id, ws)
