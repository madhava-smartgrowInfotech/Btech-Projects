from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..db import get_db

router = APIRouter(prefix="/api/track", tags=["track"])


@router.get("/{share_token}")
def get_tracking_info(share_token: str, db: Session = Depends(get_db)):
    """Public, read-only endpoint for guardians - no login required, just the
    unguessable per-session share token that was sent in the alert."""
    session = db.query(models.EmergencySession).filter(
        models.EmergencySession.share_token == share_token
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Tracking link not found or expired")

    owner = session.user
    return {
        "status": session.status,
        "trigger": session.trigger,
        "started_at": session.started_at,
        "ended_at": session.ended_at,
        "last_lat": session.last_lat,
        "last_lng": session.last_lng,
        "last_update_at": session.last_update_at,
        "user_name": owner.name,
        "path": [{"lat": p.lat, "lng": p.lng, "ts": p.ts} for p in session.pings],
    }
