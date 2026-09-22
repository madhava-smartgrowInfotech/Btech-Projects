from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import api_error, get_current_user
from app.models import Hold, Transaction, User
from app.services import holds as svc
from app.services.views import assessment_view, party, payment_view

router = APIRouter(tags=["delayed protection"])


def _approval_view(h: Hold) -> dict:
    txn = h.transaction
    return {
        "hold_id": h.id,
        "status": h.status,
        "approval_status": h.approval_status,
        "hold_until": h.hold_until,
        "decided_at": h.decided_at,
        "created_at": h.created_at,
        "amount": txn.amount_paise / 100,
        "note": txn.note,
        "channel": txn.channel,
        "requested_by": {"name": txn.payer_wallet.display_name, "upi_id": txn.payer_wallet.upi_id},
        "payee": party(txn.payee_wallet),
        "assessment": assessment_view(txn),
        "intent": {"purpose": txn.intent.purpose, "matched_scam_type": txn.intent.matched_scam_type} if txn.intent else None,
    }


@router.get("/holds")
def my_holds(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    rows = db.scalars(
        select(Hold).join(Transaction).where(Transaction.payer_wallet_id == user.wallet.id).order_by(Hold.created_at.desc()).limit(30)
    ).all()
    return {"items": [payment_view(h.transaction, user) for h in rows]}


@router.post("/holds/{hold_id}/cancel")
def cancel_hold(hold_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    hold = db.get(Hold, hold_id)
    if hold is None:
        raise api_error(status.HTTP_404_NOT_FOUND, "hold_not_found", "Hold not found.")
    svc.cancel_hold(db, hold, user)
    db.commit()
    return payment_view(hold.transaction, user)


@router.get("/approvals")
def approvals(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    rows = db.scalars(select(Hold).where(Hold.approver_user_id == user.id).order_by(Hold.created_at.desc()).limit(30)).all()
    return {"items": [_approval_view(h) for h in rows]}


def _decide(hold_id: int, approve: bool, user: User, db: Session) -> dict:
    hold = db.get(Hold, hold_id)
    if hold is None:
        raise api_error(status.HTTP_404_NOT_FOUND, "approval_not_found", "Approval request not found.")
    svc.decide_approval(db, hold, user, approve)
    db.commit()
    return _approval_view(hold)


@router.post("/approvals/{hold_id}/approve")
def approve(hold_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return _decide(hold_id, True, user, db)


@router.post("/approvals/{hold_id}/reject")
def reject(hold_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return _decide(hold_id, False, user, db)
