"""Turns database rows into API payloads (one place, so every screen sees the same shape)."""
from __future__ import annotations

from app.i18n.messages import LANGS, advice, scam_type_name
from app.models import CollectRequest, Transaction, User, Wallet
from app.services import intent as intent_svc


def party(wallet: Wallet) -> dict:
    return {
        "upi_id": wallet.upi_id,
        "name": wallet.display_name,
        "is_merchant": wallet.is_merchant,
        "category": wallet.merchant_category,
        "is_sample": wallet.user.is_sample if wallet.user else False,
    }


def warning_for(scam_type: str | None) -> dict | None:
    if not scam_type:
        return None
    return {
        "scam_type": scam_type,
        "name": {lang: scam_type_name(scam_type, lang) if scam_type != "general" else "" for lang in LANGS},
        "advice": {lang: advice(scam_type, lang) for lang in LANGS},
    }


def assessment_view(txn: Transaction) -> dict | None:
    a = txn.assessment
    if a is None:
        return None
    shap = (a.contributions or {}).get("shap", {})
    top = sorted(shap.items(), key=lambda kv: -abs(kv[1]))[:12]
    reasons = [r for r in a.reasons if r.get("kind") != "reassurance"]
    reassurance = [r for r in a.reasons if r.get("kind") == "reassurance"]
    guard = a.guard or {}
    return {
        "score": a.risk_score,
        "level": a.level,
        "final_level": a.final_level,
        "action": a.action,
        "probability": (a.contributions or {}).get("probability"),
        "behaviour_score": a.behaviour_score,
        "behaviour_top_feature": (a.contributions or {}).get("behaviour_top_feature"),
        "payee_trust": a.payee_trust,
        "trust": guard.get("trust"),
        "reasons": reasons,
        "reassurance": reassurance,
        "contributions": [{"feature": f, "value": round(v, 4)} for f, v in top],
        "base_value": (a.contributions or {}).get("base_value"),
        "features": a.features,
        "guard": {k: v for k, v in guard.items() if k != "trust"},
        "local_time": guard.get("local_time"),
        "sandbox_clock": guard.get("sandbox_clock", False),
        "model_version": a.model_version,
        "created_at": a.created_at,
    }


def payment_view(txn: Transaction, viewer: User, detail: bool = True) -> dict:
    outgoing = txn.payer_wallet_id == viewer.wallet.id
    counterparty = txn.payee_wallet if outgoing else txn.payer_wallet
    out = {
        "id": txn.id,
        "reference": txn.reference,
        "direction": "sent" if outgoing else "received",
        "counterparty": party(counterparty),
        "amount": txn.amount_paise / 100,
        "note": txn.note,
        "channel": txn.channel,
        "status": txn.status,
        "status_reason": txn.status_reason,
        "created_at": txn.created_at,
        "completed_at": txn.completed_at,
        "level": txn.assessment.final_level if txn.assessment else None,
        "score": txn.assessment.risk_score if txn.assessment else None,
    }
    if not outgoing:
        return out  # receivers never see the payer's risk details
    if detail:
        out["assessment"] = assessment_view(txn)
        it = txn.intent
        out["intent"] = (
            {
                "purpose": it.purpose,
                "answers": it.answers,
                "matched_scam_type": it.matched_scam_type,
                "escalated": it.escalated,
                "warning": warning_for(it.matched_scam_type or ("general" if it.escalated else None)),
            }
            if it
            else None
        )
        h = txn.hold
        out["hold"] = (
            {
                "id": h.id,
                "status": h.status,
                "hold_minutes": h.hold_minutes,
                "hold_until": h.hold_until,
                "needs_approval": h.needs_approval,
                "approval_status": h.approval_status,
                "approver_user_id": h.approver_user_id,
                "decided_at": h.decided_at,
            }
            if h
            else None
        )
        if txn.status == "draft" and txn.assessment and txn.assessment.level != "low":
            out["questions"] = intent_svc.questions_for({"features": txn.assessment.features})
    return out


def collect_view(req: CollectRequest, viewer: User) -> dict:
    incoming = req.payer_wallet_id == viewer.wallet.id
    other = req.requester_wallet if incoming else req.payer_wallet
    return {
        "id": req.id,
        "direction": "incoming" if incoming else "outgoing",
        "counterparty": party(other),
        "amount": req.amount_paise / 100,
        "note": req.note,
        "status": req.status,
        "guard": req.guard if incoming else None,
        "expires_at": req.expires_at,
        "created_at": req.created_at,
    }
