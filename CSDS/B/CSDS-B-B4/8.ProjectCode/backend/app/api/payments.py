from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import api_error, get_current_user
from app.models import RiskAssessment, Transaction, User
from app.services import payments as svc
from app.services.views import payment_view

router = APIRouter(prefix="/payments", tags=["payments"])


class AssessIn(BaseModel):
    upi_id: str = Field(min_length=3, max_length=80)
    amount: float = Field(gt=0, le=100000)
    note: str | None = Field(default=None, max_length=140)
    channel: Literal["send", "qr"] = "send"
    qr_payload: str | None = Field(default=None, max_length=1000)
    device: Literal["mobile", "desktop", "tablet"] = "mobile"
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)


class IntentIn(BaseModel):
    purpose: str = Field(min_length=2, max_length=20)
    asked_by_someone: bool = False
    verified_by_call: bool | None = None
    advance_to_online_seller: bool | None = None


class ConfirmIn(BaseModel):
    pin: str = Field(pattern=r"^\d{4}$")


@router.post("/assess")
def assess(body: AssessIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Scores a payment before confirmation and returns the risk panel (a draft payment)."""
    payee = svc.find_wallet(db, body.upi_id)
    geo = (body.lat, body.lon) if body.lat is not None and body.lon is not None else None
    txn, _, _ = svc.create_assessed_payment(
        db, user, payee, round(body.amount, 2), note=(body.note or "").strip() or None, channel=body.channel, device=body.device, geo=geo, qr_payload=body.qr_payload
    )
    db.commit()
    db.refresh(txn)
    return payment_view(txn, user)


@router.post("/{txn_id}/intent")
def intent(txn_id: int, body: IntentIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    txn = svc.get_own_transaction(db, user, txn_id)
    result = svc.submit_intent(db, txn, body.model_dump())
    db.refresh(txn)
    return {"result": result, "payment": payment_view(txn, user)}


@router.post("/{txn_id}/confirm")
def confirm(txn_id: int, body: ConfirmIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    txn = svc.get_own_transaction(db, user, txn_id)
    txn = svc.confirm(db, user, txn, body.pin)
    return payment_view(txn, user)


@router.post("/{txn_id}/cancel")
def cancel(txn_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    txn = svc.get_own_transaction(db, user, txn_id)
    txn = svc.cancel(db, user, txn)
    return payment_view(txn, user)


@router.get("")
def history(
    direction: Literal["all", "sent", "received"] = "all",
    level: Literal["all", "low", "medium", "high"] = "all",
    status_filter: str | None = Query(None, alias="status"),
    q: str | None = Query(None, max_length=60),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    w = user.wallet
    stmt = select(Transaction).where(Transaction.status != "draft")
    if direction == "sent":
        stmt = stmt.where(Transaction.payer_wallet_id == w.id)
    elif direction == "received":
        stmt = stmt.where(Transaction.payee_wallet_id == w.id, Transaction.status == "completed")
    else:
        stmt = stmt.where(or_(Transaction.payer_wallet_id == w.id, (Transaction.payee_wallet_id == w.id) & (Transaction.status == "completed")))
    if level != "all":
        stmt = stmt.join(RiskAssessment).where(RiskAssessment.final_level == level, Transaction.payer_wallet_id == w.id)
    if status_filter:
        stmt = stmt.where(Transaction.status == status_filter)
    rows = db.scalars(stmt.order_by(Transaction.created_at.desc()).offset(offset).limit(limit + 1)).all()
    items = [payment_view(t, user, detail=False) for t in rows[:limit]]
    if q:
        needle = q.lower()
        items = [i for i in items if needle in i["counterparty"]["name"].lower() or needle in i["counterparty"]["upi_id"] or needle in (i["note"] or "").lower()]
    return {"items": items, "has_more": len(rows) > limit, "offset": offset}


@router.get("/{txn_id}")
def detail(txn_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    txn = db.get(Transaction, txn_id)
    if txn is None or user.wallet.id not in (txn.payer_wallet_id, txn.payee_wallet_id) or (txn.payee_wallet_id == user.wallet.id and txn.status == "draft"):
        raise api_error(status.HTTP_404_NOT_FOUND, "payment_not_found", "Payment not found.")
    return payment_view(txn, user)
