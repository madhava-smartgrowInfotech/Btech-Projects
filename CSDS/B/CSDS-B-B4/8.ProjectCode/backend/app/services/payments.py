"""Payment flow: assess (risk panel) -> intent check -> confirm with PIN -> pay now or hold -> cancel."""
from __future__ import annotations

from datetime import datetime

from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import api_error
from app.core.logging import get_logger
from app.core.security import verify_secret
from app.models import CollectRequest, FailedAttempt, IntentCheck, RiskAssessment, Transaction, User, Wallet, utcnow
from app.services import holds, intent, ledger
from app.services.guard import collect_guard, qr_guard
from app.services.notifier import notify
from app.services.risk import PaymentContext, assess_payment

log = get_logger("upi_guardian.payments")
MAX_AMOUNT = 100000.0  # sandbox per-payment limit, like the common UPI limit


def find_wallet(db: Session, upi_id: str) -> Wallet:
    wallet = db.scalar(select(Wallet).where(Wallet.upi_id == upi_id.strip().lower()))
    if wallet is None:
        raise api_error(status.HTTP_404_NOT_FOUND, "payee_not_found", "No sandbox wallet has this UPI ID.")
    return wallet


def _validate(user: User, payee: Wallet, amount: float) -> None:
    if payee.id == user.wallet.id:
        raise api_error(status.HTTP_400_BAD_REQUEST, "self_payment", "You cannot pay your own UPI ID.")
    if amount <= 0 or amount > MAX_AMOUNT:
        raise api_error(status.HTTP_400_BAD_REQUEST, "amount_invalid", "Enter an amount between ₹1 and ₹1,00,000.")


def create_assessed_payment(
    db: Session,
    user: User,
    payee: Wallet,
    amount: float,
    *,
    note: str | None = None,
    channel: str = "send",
    device: str = "mobile",
    geo: tuple[float, float] | None = None,
    qr_payload: str | None = None,
    collect: CollectRequest | None = None,
    now: datetime | None = None,
) -> tuple[Transaction, RiskAssessment, dict]:
    _validate(user, payee, amount)
    now = now or utcnow()
    guard: dict = {}
    note_score, qr_score = 0.0, 0.0
    if channel == "collect":
        guard = collect_guard(collect.note if collect else note, amount)
        note_score = guard["note_score"]
    elif channel == "qr" and qr_payload:
        guard = {"type": "qr", **qr_guard(db, qr_payload)}
        qr_score = guard.get("qr_flag", 0.0)
    result = assess_payment(
        db,
        PaymentContext(payer=user, payee_wallet=payee, amount=amount, channel=channel, note=note, note_score=note_score, qr_flag=qr_score, device=device, geo=geo, now=now),
    )
    txn = Transaction(
        reference=ledger.new_reference(db),
        payer_wallet_id=user.wallet.id,
        payee_wallet_id=payee.id,
        amount_paise=int(round(amount * 100)),
        note=(note or (collect.note if collect else None) or None),
        channel=channel,
        status="draft",
        device_type=device,
        geo_lat=geo[0] if geo else None,
        geo_lon=geo[1] if geo else None,
        local_time_used=result["local_time"] if result["sandbox_clock"] else None,
        collect_request_id=collect.id if collect else None,
        qr_payload=qr_payload,
        created_at=now,
    )
    db.add(txn)
    db.flush()
    assessment = RiskAssessment(
        transaction_id=txn.id,
        model_version=result["model_version"],
        behaviour_score=result["behaviour_score"],
        risk_score=result["score"],
        level=result["level"],
        final_level=result["level"],
        action=result["action"],
        payee_trust=result["trust"]["score"],
        features=result["features"],
        contributions={"shap": result["contributions"], "base_value": result["base_value"], "probability": result["probability"], "behaviour_top_feature": result["behaviour_top_feature"]},
        reasons=result["reasons"] + [dict(r, kind="reassurance") for r in result["reassurance"]],
        guard=guard | {"trust": result["trust"], "linked_sms_id": result["linked_sms_id"], "sandbox_clock": result["sandbox_clock"], "local_time": result["local_time"]},
        created_at=now,
    )
    db.add(assessment)
    db.flush()
    log.info("payment assessed", extra={"transaction_id": txn.id, "score": result["score"], "level": result["level"], "channel": channel})
    return txn, assessment, result


def get_own_transaction(db: Session, user: User, txn_id: int) -> Transaction:
    txn = db.get(Transaction, txn_id)
    if txn is None or txn.payer_wallet_id != user.wallet.id:
        raise api_error(status.HTTP_404_NOT_FOUND, "payment_not_found", "Payment not found.")
    return txn


def submit_intent(db: Session, txn: Transaction, answers: dict) -> dict:
    if txn.status != "draft":
        raise api_error(status.HTTP_409_CONFLICT, "payment_closed", "This payment has already been processed.")
    a = txn.assessment
    result = intent.evaluate(a.level, txn.channel, a.features, answers)
    if txn.intent:
        txn.intent.purpose = result["purpose"]
        txn.intent.answers = answers
        txn.intent.matched_scam_type = result["scam_type"]
        txn.intent.escalated = result["escalated"]
    else:
        db.add(IntentCheck(transaction_id=txn.id, purpose=result["purpose"], answers=answers, matched_scam_type=result["scam_type"], escalated=result["escalated"]))
    a.final_level = result["final_level"]
    if a.action != "block":
        a.action = {"low": "pay", "medium": "verify", "high": "hold"}[result["final_level"]]
    db.commit()
    return result


def _check_pin(db: Session, user: User, pin: str) -> None:
    if not verify_secret(pin, user.pin_hash):
        db.add(FailedAttempt(user_id=user.id, reason="wrong_pin"))
        db.commit()
        raise api_error(status.HTTP_400_BAD_REQUEST, "wrong_pin", "Incorrect UPI PIN.")


def confirm(db: Session, user: User, txn: Transaction, pin: str) -> Transaction:
    if txn.status != "draft":
        raise api_error(status.HTTP_409_CONFLICT, "payment_closed", "This payment has already been processed.")
    a = txn.assessment
    if a.action == "block":
        raise api_error(status.HTTP_403_FORBIDDEN, "payment_blocked", "This payment was blocked because the receiver is a reported scam account.")
    if a.level in ("medium", "high") and txn.intent is None:
        raise api_error(status.HTTP_409_CONFLICT, "intent_required", "Please answer the safety check before paying.")
    _check_pin(db, user, pin)
    if a.final_level == "high":
        holds.create_hold(db, txn, user)
    else:
        ledger.pay_now(db, txn)
        notify(db, txn.payee_wallet.user_id, "payment_received", {"transaction_id": txn.id, "amount": txn.amount_paise / 100, "payer_name": user.full_name})
    if txn.collect_request_id:
        req = db.get(CollectRequest, txn.collect_request_id)
        if req:
            req.status = "held" if txn.status == "held" else "approved"
    db.commit()
    db.refresh(txn)
    return txn


def cancel(db: Session, user: User, txn: Transaction) -> Transaction:
    if txn.status == "draft":
        txn.status = "cancelled"
        txn.status_reason = "cancelled_after_warning" if txn.assessment and txn.assessment.final_level != "low" else "cancelled_by_user"
        txn.completed_at = utcnow()
        if txn.collect_request_id:
            req = db.get(CollectRequest, txn.collect_request_id)
            if req and req.status == "pending":
                req.status = "declined"
    elif txn.status == "held" and txn.hold:
        holds.cancel_hold(db, txn.hold, user)
        if txn.collect_request_id:
            req = db.get(CollectRequest, txn.collect_request_id)
            if req:
                req.status = "cancelled"
    else:
        raise api_error(status.HTTP_409_CONFLICT, "payment_closed", "This payment can no longer be cancelled.")
    db.commit()
    db.refresh(txn)
    return txn
