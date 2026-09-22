from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import api_error, get_current_user
from app.models import ScamReport, SmsCheck, User
from app.services.sms_service import analyze_and_store, check_payload

router = APIRouter(prefix="/sms", tags=["sms check"])


class CheckIn(BaseModel):
    text: str = Field(min_length=3, max_length=2000)


@router.post("/check")
def check(body: CheckIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    c = analyze_and_store(db, user, body.text)
    db.commit()
    return check_payload(db, c)


@router.get("/history")
def history(limit: int = Query(20, ge=1, le=100), user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    rows = db.scalars(select(SmsCheck).where(SmsCheck.user_id == user.id).order_by(SmsCheck.created_at.desc()).limit(limit)).all()
    return {"items": [check_payload(db, c) for c in rows]}


@router.post("/{check_id}/report")
def report(check_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Reports every UPI ID found in a scam message to the community."""
    c = db.get(SmsCheck, check_id)
    if c is None or c.user_id != user.id:
        raise api_error(status.HTTP_404_NOT_FOUND, "sms_not_found", "Message not found.")
    reported = []
    for upi in c.entities.get("upi_ids", []):
        if upi == user.wallet.upi_id:
            continue
        exists = db.scalar(select(ScamReport).where(ScamReport.reporter_user_id == user.id, ScamReport.upi_id == upi))
        if not exists:
            db.add(ScamReport(reporter_user_id=user.id, upi_id=upi, category=c.scam_type or "other", source="sms", note=c.text[:280]))
        reported.append(upi)
    db.commit()
    return {"reported": reported}
