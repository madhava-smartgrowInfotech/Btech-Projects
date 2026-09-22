"""F5 - Smart Payment Intent Verification.

For Medium and High risk payments the user is asked what the payment is for. Answers that
match a known scam script ("I'm receiving a refund", "KYC update", "someone on a call asked me")
escalate the payment and show the warning for that exact scam. An answer can never lower the risk.
"""
from __future__ import annotations

from app.i18n.messages import LANGS, advice, scam_type_name
from app.services.policy import raise_level

PURPOSES = ["family_friend", "shopping", "bill", "refund", "prize", "kyc", "job", "loan", "investment", "other"]

# Purposes that only ever come from a scam script: nobody pays to receive a refund or a prize.
SCAM_PURPOSES = {
    "refund": "refund_scam",
    "prize": "lottery_prize",
    "kyc": "kyc_fraud",
    "job": "job_task",
    "loan": "loan_fee",
    "investment": "investment",
}

QUESTIONS = {
    "purpose": {"type": "choice", "options": PURPOSES},
    "asked_by_someone": {"type": "yes_no", "when": "always"},
    "verified_by_call": {"type": "yes_no", "when": {"purpose": ["family_friend"], "new_payee": True}},
    "advance_to_online_seller": {"type": "yes_no", "when": {"purpose": ["shopping"], "new_payee": True}},
}


def questions_for(assessment: dict) -> list[dict]:
    new_payee = assessment["features"].get("is_new_payee", 0) >= 1
    out = [{"id": "purpose", **QUESTIONS["purpose"]}, {"id": "asked_by_someone", "type": "yes_no"}]
    if new_payee:
        out.append({"id": "verified_by_call", "type": "yes_no", "only_for_purpose": ["family_friend"]})
        out.append({"id": "advance_to_online_seller", "type": "yes_no", "only_for_purpose": ["shopping"]})
    return out


def evaluate(level: str, channel: str, features: dict, answers: dict) -> dict:
    purpose = answers.get("purpose", "other")
    if purpose not in PURPOSES:
        purpose = "other"
    asked = bool(answers.get("asked_by_someone"))
    new_payee = features.get("is_new_payee", 0) >= 1
    scam_type: str | None = None
    signals: list[str] = []

    if purpose in SCAM_PURPOSES:
        scam_type = SCAM_PURPOSES[purpose]
        if channel == "collect" and purpose in ("refund", "prize"):
            scam_type = "collect_request"
        if channel == "qr" and purpose in ("refund", "prize"):
            scam_type = "qr_scam"
        signals.append("scam_purpose")
    if purpose == "family_friend" and new_payee and answers.get("verified_by_call") is False:
        scam_type = scam_type or "impersonation"
        signals.append("unverified_new_number")
    if purpose == "shopping" and new_payee and answers.get("advance_to_online_seller"):
        signals.append("advance_to_unknown_seller")
    if purpose == "bill" and asked:
        scam_type = scam_type or "bill_disconnection"
    if asked:
        signals.append("pressured_by_someone")
    if channel == "collect" and purpose in ("family_friend", "shopping", "bill", "other") and features.get("collect_note_score", 0) >= 0.5:
        scam_type = scam_type or "collect_request"
        signals.append("collect_note_promises_money")

    final = level
    if "scam_purpose" in signals:
        final = "high"
    elif signals:
        final = raise_level(level)

    warning_type = scam_type or ("general" if signals else None)
    return {
        "purpose": purpose,
        "signals": signals,
        "scam_type": scam_type,
        "escalated": final != level,
        "final_level": final,
        "recommend_cancel": "scam_purpose" in signals or "unverified_new_number" in signals,
        "warning": None
        if warning_type is None
        else {
            "scam_type": warning_type,
            "name": {lang: scam_type_name(warning_type, lang) if warning_type != "general" else "" for lang in LANGS},
            "advice": {lang: advice(warning_type, lang) for lang in LANGS},
        },
    }
