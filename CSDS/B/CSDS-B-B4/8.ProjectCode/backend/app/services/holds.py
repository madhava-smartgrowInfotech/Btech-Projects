"""Delayed Protection Mode (F6): cooling-off holds with optional trusted-contact approval."""
from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import api_error
from app.core.logging import get_logger
from app.models import Hold, Transaction, TrustedContact, User, utcnow
from app.services import ledger
from app.services.notifier import notify

log = get_logger("upi_guardian.holds")


def approver_for(db: Session, user: User) -> TrustedContact | None:
    return db.scalar(
        select(TrustedContact)
        .where(TrustedContact.user_id == user.id, TrustedContact.can_approve.is_(True))
        .order_by(TrustedContact.created_at)
    )


def _txn_summary(txn: Transaction) -> dict:
    return {
        "transaction_id": txn.id,
        "reference": txn.reference,
        "amount": txn.amount_paise / 100,
        "payee_upi_id": txn.payee_wallet.upi_id,
        "payee_name": txn.payee_wallet.display_name,
        "payer_name": txn.payer_wallet.display_name,
    }


def create_hold(db: Session, txn: Transaction, user: User) -> Hold:
    minutes = max(1, int(user.settings.hold_minutes))
    approver = approver_for(db, user) if user.settings.trusted_approval_required else None
    ledger.reserve_for_hold(db, txn)
    hold = Hold(
        transaction_id=txn.id,
        hold_minutes=minutes,
        hold_until=utcnow() + timedelta(minutes=minutes),
        needs_approval=approver is not None,
        approval_status="pending" if approver else "none",
        approver_user_id=approver.contact_user_id if approver else None,
    )
    db.add(hold)
    db.flush()
    summary = _txn_summary(txn) | {"hold_id": hold.id, "hold_until": hold.hold_until.isoformat()}
    notify(db, user.id, "hold_started", summary)
    if approver:
        notify(db, approver.contact_user_id, "approval_requested", summary | {"requested_by": user.full_name})
    log.info("payment held", extra={"transaction_id": txn.id, "minutes": minutes, "needs_approval": hold.needs_approval})
    return hold


def _require_active(hold: Hold) -> None:
    if hold.status != "active":
        raise api_error(status.HTTP_409_CONFLICT, "hold_closed", "This payment is no longer on hold.")


def cancel_hold(db: Session, hold: Hold, user: User) -> Hold:
    txn = hold.transaction
    if txn.payer_wallet.user_id != user.id:
        raise api_error(status.HTTP_404_NOT_FOUND, "hold_not_found", "Hold not found.")
    _require_active(hold)
    ledger.refund_payer(db, txn, "cancelled", "cancelled_during_hold")
    hold.status = "cancelled"
    hold.decided_at = utcnow()
    notify(db, user.id, "hold_cancelled", _txn_summary(txn))
    if hold.approver_user_id:
        notify(db, hold.approver_user_id, "approval_closed", _txn_summary(txn) | {"outcome": "cancelled"})
    return hold


def decide_approval(db: Session, hold: Hold, approver: User, approve: bool) -> Hold:
    if hold.approver_user_id != approver.id:
        raise api_error(status.HTTP_404_NOT_FOUND, "approval_not_found", "Approval request not found.")
    _require_active(hold)
    txn = hold.transaction
    hold.decided_at = utcnow()
    owner_id = txn.payer_wallet.user_id
    if approve:
        hold.approval_status = "approved"
        hold.status = "released"
        ledger.credit_payee(db, txn)
        txn.status_reason = "approved_by_trusted_contact"
        notify(db, owner_id, "hold_approved", _txn_summary(txn) | {"approver": approver.full_name})
    else:
        hold.approval_status = "rejected"
        hold.status = "rejected"
        ledger.refund_payer(db, txn, "rejected", "rejected_by_trusted_contact")
        notify(db, owner_id, "hold_rejected", _txn_summary(txn) | {"approver": approver.full_name})
    return hold


def process_due_holds(db: Session, now: datetime | None = None) -> int:
    """Release (or expire, when approval never came) every hold whose cooling-off time is over."""
    now = now or utcnow()
    due = db.scalars(select(Hold).where(Hold.status == "active", Hold.hold_until <= now)).all()
    for hold in due:
        txn = hold.transaction
        owner_id = txn.payer_wallet.user_id
        if hold.needs_approval and hold.approval_status != "approved":
            hold.status = "expired"
            hold.decided_at = now
            ledger.refund_payer(db, txn, "cancelled", "not_approved_in_time")
            notify(db, owner_id, "hold_expired", _txn_summary(txn))
            if hold.approver_user_id:
                notify(db, hold.approver_user_id, "approval_closed", _txn_summary(txn) | {"outcome": "expired"})
        else:
            hold.status = "released"
            hold.decided_at = now
            ledger.credit_payee(db, txn, now)
            txn.status_reason = "released_after_hold"
            notify(db, owner_id, "hold_released", _txn_summary(txn))
        log.info("hold closed", extra={"hold_id": hold.id, "status": hold.status})
    return len(due)
