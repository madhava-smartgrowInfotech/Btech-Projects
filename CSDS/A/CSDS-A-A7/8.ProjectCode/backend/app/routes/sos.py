from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import auth, config, models, schemas
from ..db import get_db
from ..services import telegram, email as email_service
from ..ws_manager import manager

router = APIRouter(prefix="/api/sos", tags=["sos"])


def _tracking_url(share_token: str, request_origin: str | None) -> str:
    base = request_origin or f"http://localhost:{config.FRONTEND_PORT}"
    return f"{base.rstrip('/')}/track/{share_token}"


@router.post("/start")
async def start_sos(
    body: schemas.SosStartIn,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    session = models.EmergencySession(
        user_id=current_user.id,
        trigger=body.trigger,
        last_lat=body.lat,
        last_lng=body.lng,
        last_update_at=datetime.now(timezone.utc),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    ping = models.LocationPing(session_id=session.id, lat=body.lat, lng=body.lng)
    db.add(ping)
    db.commit()

    origin = request.headers.get("origin")
    if not origin:
        referer = request.headers.get("referer")
        if referer:
            origin = "/".join(referer.split("/")[:3])
    tracking_url = _tracking_url(session.share_token, origin)
    guardians = db.query(models.Guardian).filter(models.Guardian.owner_id == current_user.id).all()

    alert_text = (
        f"SHEGUARD ALERT: {current_user.name} may need help "
        f"({body.trigger} trigger). Live location: {tracking_url}"
    )
    delivery = []
    for g in guardians:
        sent_tg = await telegram.send_telegram_message(g.telegram_chat_id, alert_text) if g.telegram_chat_id else False
        sent_email = email_service.send_email(g.email, "SHEGUARD emergency alert", alert_text) if g.email else False
        delivery.append({"guardian": g.name, "telegram": sent_tg, "email": sent_email})

    return {
        "session_id": session.id,
        "share_token": session.share_token,
        "tracking_url": tracking_url,
        "started_at": session.started_at,
        "delivery": delivery,
    }


@router.post("/{session_id}/location")
async def push_location(
    session_id: int,
    body: schemas.LocationUpdateIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    session = db.get(models.EmergencySession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "active":
        raise HTTPException(status_code=400, detail="Session is not active")

    session.last_lat = body.lat
    session.last_lng = body.lng
    session.last_update_at = datetime.now(timezone.utc)
    db.add(models.LocationPing(session_id=session.id, lat=body.lat, lng=body.lng))
    db.commit()

    await manager.broadcast(session.share_token, {
        "type": "location",
        "lat": body.lat,
        "lng": body.lng,
        "ts": session.last_update_at.isoformat(),
    })
    return {"ok": True}


@router.post("/{session_id}/cancel")
async def cancel_sos(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    session = db.get(models.EmergencySession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = "cancelled"
    session.ended_at = datetime.now(timezone.utc)
    db.commit()

    await manager.broadcast(session.share_token, {"type": "cancelled"})
    return {"ok": True}


@router.get("/{session_id}")
def get_sos(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    session = db.get(models.EmergencySession, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "id": session.id,
        "status": session.status,
        "share_token": session.share_token,
        "trigger": session.trigger,
        "started_at": session.started_at,
        "ended_at": session.ended_at,
        "last_lat": session.last_lat,
        "last_lng": session.last_lng,
        "evidence_count": len(session.evidence),
    }
