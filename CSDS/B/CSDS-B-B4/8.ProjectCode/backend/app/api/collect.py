from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import api_error, get_current_user
from app.models import CollectRequest, User, utcnow
from app.services import payments as pay_svc
from app.services.guard import collect_guard
from app.services.notifier import notify
from app.services.trust import compute_trust
from app.services.views import collect_view, payment_view

router = APIRouter(prefix="/collect", tags=["collect"])


class CollectIn(BaseModel):
    upi_id: str = Field(min_length=3, max_length=80, description="UPI ID of the person who should pay you")
    amount: float = Field(gt=0, le=100000)
    note: str | None = Field(default=None, max_length=140)


def _own_incoming(db: Session, user: User, req_id: int) -> CollectRequest:
    req = db.get(CollectRequest, req_id)
    if req is None or req.payer_wallet_id != user.wallet.id:
        raise api_error(status.HTTP_404_NOT_FOUND, "request_not_found", "Request not found.")
    return req


def _refresh_guard(db: Session, req: CollectRequest) -> None:
    guard = collect_guard(req.note, req.amount_paise / 100)
    guard["requester_trust"] = compute_trust(db, req.requester_wallet).as_dict()
    req.guard = guard


@router.post("", status_code=status.HTTP_201_CREATED)
def create(body: CollectIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    payer = pay_svc.find_wallet(db, body.upi_id)
    if payer.id == user.wallet.id:
        raise api_error(status.HTTP_400_BAD_REQUEST, "self_payment", "You cannot request money from yourself.")
    req = CollectRequest(
        requester_wallet_id=user.wallet.id,
        payer_wallet_id=payer.id,
        amount_paise=int(round(body.amount * 100)),
        note=(body.note or "").strip() or None,
        expires_at=utcnow() + timedelta(days=2),
    )
    db.add(req)
    db.flush()
    _refresh_guard(db, req)
    notify(db, payer.user_id, "collect_received", {"request_id": req.id, "amount": body.amount, "requested_by": user.full_name})
    db.commit()
    return collect_view(req, user)


@router.get("/incoming")
def incoming(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    rows = db.scalars(select(CollectRequest).where(CollectRequest.payer_wallet_id == user.wallet.id).order_by(CollectRequest.created_at.desc()).limit(50)).all()
    changed = False
    for r in rows:
        if r.status == "pending" and not r.guard:
            _refresh_guard(db, r)
            changed = True
    if changed:
        db.commit()
    return {"items": [collect_view(r, user) for r in rows]}


@router.get("/outgoing")
def outgoing(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    rows = db.scalars(select(CollectRequest).where(CollectRequest.requester_wallet_id == user.wallet.id).order_by(CollectRequest.created_at.desc()).limit(50)).all()
    return {"items": [collect_view(r, user) for r in rows]}


@router.post("/{req_id}/assess")
def assess(req_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Approving starts a normal (risk-checked) payment with channel 'collect'."""
    req = _own_incoming(db, user, req_id)
    if req.status != "pending":
        raise api_error(status.HTTP_409_CONFLICT, "request_closed", "This request is no longer waiting.")
    txn, _, _ = pay_svc.create_assessed_payment(db, user, req.requester_wallet, req.amount_paise / 100, channel="collect", collect=req)
    db.commit()
    db.refresh(txn)
    return payment_view(txn, user)


@router.post("/{req_id}/decline")
def decline(req_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    req = _own_incoming(db, user, req_id)
    if req.status != "pending":
        raise api_error(status.HTTP_409_CONFLICT, "request_closed", "This request is no longer waiting.")
    req.status = "declined"
    db.commit()
    return collect_view(req, user)
