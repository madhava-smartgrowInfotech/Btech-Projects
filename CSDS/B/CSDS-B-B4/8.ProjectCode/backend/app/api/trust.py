from __future__ import annotations

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import api_error, get_current_user
from app.models import ScamReport, User
from app.services.payments import find_wallet
from app.services.trust import compute_trust
from app.services.views import party

router = APIRouter(tags=["trust"])

REPORT_CATEGORIES = [
    "kyc_fraud", "refund_scam", "collect_request", "lottery_prize", "job_task", "bill_disconnection", "wrong_transfer",
    "courier_customs", "loan_fee", "otp_pin_request", "impersonation", "investment", "qr_scam", "other",
]


class ReportIn(BaseModel):
    upi_id: str = Field(min_length=3, max_length=80)
    category: str = Field(default="other")
    note: str | None = Field(default=None, max_length=280)
    source: str = Field(default="manual", pattern=r"^(manual|sms|payment|collect)$")


@router.get("/trust/{upi_id}")
def trust(upi_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    w = find_wallet(db, upi_id)
    mine = db.scalar(select(ScamReport.id).where(ScamReport.reporter_user_id == user.id, ScamReport.upi_id == w.upi_id)) is not None
    return party(w) | {"trust": compute_trust(db, w).as_dict(), "reported_by_you": mine}


@router.post("/reports", status_code=status.HTTP_201_CREATED)
def report(body: ReportIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    upi = body.upi_id.strip().lower()
    if upi == user.wallet.upi_id:
        raise api_error(status.HTTP_400_BAD_REQUEST, "self_report", "You cannot report your own UPI ID.")
    category = body.category if body.category in REPORT_CATEGORIES else "other"
    existing = db.scalar(select(ScamReport).where(ScamReport.reporter_user_id == user.id, ScamReport.upi_id == upi))
    if existing:
        existing.category, existing.note = category, body.note
    else:
        db.add(ScamReport(reporter_user_id=user.id, upi_id=upi, category=category, note=body.note, source=body.source))
    db.commit()
    return {"upi_id": upi, "category": category, "status": "reported"}
