"""F2 - real-time risk engine: scores a payment before the user confirms it.

behaviour + history + payee trust + SMS signals + collect/QR guard
    -> M1 behaviour model -> M3 payment risk model -> 0-100 score -> policy -> SHAP reasons
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import api_error
from app.ml.features import M1_FEATURES, RISK_FEATURES, m1_row, merchant_risk_from_trust, risk_row
from app.ml.registry import registry
from app.models import IST, FailedAttempt, SavedPayee, SmsCheck, Transaction, User, Wallet, utcnow
from app.services import policy as policy_svc
from app.services.explain import build_reasons
from app.services.trust import compute_trust

MOVED = ("completed", "held")


@dataclass
class PaymentContext:
    payer: User
    payee_wallet: Wallet
    amount: float
    channel: str = "send"  # send | qr | collect
    note: str | None = None
    note_score: float = 0.0
    qr_flag: float = 0.0
    device: str = "mobile"
    geo: tuple[float, float] | None = None
    now: datetime | None = None


def local_clock(user: User, now: datetime) -> tuple[float, str, bool]:
    """Hour of day used for scoring: the sandbox clock if the user set one, otherwise India time."""
    clock = user.settings.sandbox_clock if user.settings else None
    if clock:
        h, m = (int(x) for x in clock.split(":"))
        return h + m / 60, clock, True
    t = now.astimezone(IST)
    return t.hour + t.minute / 60, f"{t:%H:%M}", False


def _haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def score_from_probability(p: float, anchors: dict) -> int:
    t_med, t_high = anchors["t_medium"], anchors["t_high"]
    ms, hs = anchors.get("medium_score", 35), anchors.get("high_score", 70)
    if p < t_med:
        s = ms * p / t_med
    elif p < t_high:
        s = ms + (hs - ms) * (p - t_med) / (t_high - t_med)
    else:
        s = hs + (100 - hs) * (p - t_high) / (1 - t_high)
    return int(max(0, min(100, round(s))))


def _sms_signals(db: Session, user: User, payee: Wallet, amount: float, now: datetime) -> tuple[float, bool, int | None]:
    """Scam SMS checked in the last 48 h that mention this payee (UPI ID or phone) or the same amount."""
    checks = db.scalars(
        select(SmsCheck).where(SmsCheck.user_id == user.id, SmsCheck.created_at >= now - timedelta(hours=48)).order_by(SmsCheck.created_at.desc())
    ).all()
    linked_prob, linked_id, recent = 0.0, None, False
    payee_phone = payee.user.phone if payee.user else None
    for c in checks:
        if c.verdict == "scam" and c.created_at >= now - timedelta(hours=24):
            recent = True
        if c.verdict == "safe":
            continue
        ent = c.entities or {}
        mentions = payee.upi_id in ent.get("upi_ids", []) or (payee_phone and payee_phone in ent.get("phones", []))
        same_amount = any(abs(a - amount) < 0.5 for a in ent.get("amounts", []))
        if (mentions or same_amount) and c.probability > linked_prob:
            linked_prob, linked_id = c.probability, c.id
    return linked_prob, recent, linked_id


def assess_payment(db: Session, ctx: PaymentContext) -> dict:
    if not (registry.available("behaviour") and registry.available("risk")):
        raise api_error(status.HTTP_503_SERVICE_UNAVAILABLE, "models_missing", "Risk models are not trained yet. Run ml/train_all.py.")
    now = ctx.now or utcnow()
    payer, payee = ctx.payer, ctx.payee_wallet
    wallet = payer.wallet
    hour, local_time, simulated = local_clock(payer, now)

    # ---- payer behaviour and history ---------------------------------------------
    rows = db.execute(
        select(Transaction.amount_paise, Transaction.created_at, Transaction.status, Transaction.geo_lat, Transaction.geo_lon)
        .where(Transaction.payer_wallet_id == wallet.id, Transaction.status.in_(MOVED), Transaction.created_at >= now - timedelta(days=90), Transaction.created_at <= now)
        .order_by(Transaction.created_at)
    ).all()
    completed = [r for r in rows if r.status == "completed"]
    past_amounts = [r.amount_paise / 100 for r in completed]
    past_hours = [(r.created_at.astimezone(IST).hour + r.created_at.astimezone(IST).minute / 60) for r in completed]
    c1 = sum(1 for r in rows if r.created_at >= now - timedelta(hours=1))
    c24 = sum(1 for r in rows if r.created_at >= now - timedelta(hours=24))
    failed = db.scalar(select(func.count(FailedAttempt.id)).where(FailedAttempt.user_id == payer.id, FailedAttempt.created_at >= now - timedelta(hours=24))) or 0
    age_days = max(0.0, (now - payer.created_at).total_seconds() / 86400)
    months = max(1.0, min(90.0, max(age_days, 1.0)) / 30.0)
    avg_monthly = sum(past_amounts) / months if past_amounts else 0.0
    geo_km = None
    last_geo = next((r for r in reversed(rows) if r.geo_lat is not None and r.geo_lon is not None), None)
    if ctx.geo and last_geo:
        geo_km = _haversine_km(ctx.geo, (last_geo.geo_lat, last_geo.geo_lon))

    times_paid = db.scalar(
        select(func.count(Transaction.id)).where(Transaction.payer_wallet_id == wallet.id, Transaction.payee_wallet_id == payee.id, Transaction.status == "completed")
    ) or 0
    saved = db.scalar(select(SavedPayee.id).where(SavedPayee.user_id == payer.id, SavedPayee.payee_wallet_id == payee.id)) is not None

    # ---- payee trust and SMS signals ---------------------------------------------
    trust = compute_trust(db, payee, now)
    sms_prob, sms_recent, sms_id = _sms_signals(db, payer, payee, ctx.amount, now)

    # ---- M1 behaviour model --------------------------------------------------------
    m1 = m1_row(
        amount=ctx.amount,
        avg_monthly_spend=avg_monthly,
        account_age_days=age_days,
        txn_count_1h=c1,
        txn_count_24h=c24,
        failed_txn_count_24h=int(failed),
        geo_distance_km=geo_km,
        merchant_risk_score=merchant_risk_from_trust(trust.score),
        hour=hour,
        device=ctx.device,
    )
    x1 = pd.DataFrame([m1])[M1_FEATURES]
    behaviour = float(registry.get("behaviour")["model"].predict_proba(x1)[0, 1])
    sv1 = registry.explainers["behaviour"].shap_values(x1)[0]
    m1_top = M1_FEATURES[int(np.argmax(sv1))] if np.max(sv1) > 0 else None

    # ---- M3 payment risk model -------------------------------------------------------
    features = risk_row(
        behaviour_score=behaviour,
        amount=ctx.amount,
        past_amounts=past_amounts,
        is_new_payee=times_paid == 0,
        payee_times_paid=times_paid,
        is_saved_contact=saved,
        hour=hour,
        past_hours=past_hours,
        hour_prior=registry.hour_prior(int(hour)),
        txn_count_1h=c1,
        txn_count_24h=c24,
        failed_24h=int(failed),
        payee_account_age_days=trust.inputs.account_age_days,
        payee_reports=trust.inputs.report_score,
        payee_distinct_payers_24h=trust.inputs.distinct_payers_24h,
        payee_new_payer_share_7d=trust.inputs.new_payer_share_7d,
        payee_collects_7d=trust.inputs.collect_targets_7d,
        payee_is_merchant=payee.is_merchant,
        sms_scam_prob=sms_prob,
        sms_recent_scam=sms_recent,
        channel=ctx.channel,
        collect_note_score=ctx.note_score if ctx.channel == "collect" else 0.0,
        qr_flag=ctx.qr_flag if ctx.channel == "qr" else 0.0,
        payer_account_age_days=age_days,
    )
    bundle = registry.get("risk")
    x3 = pd.DataFrame([features])[RISK_FEATURES]
    probability = float(bundle["model"].predict_proba(x3)[0, 1])
    sv3 = registry.explainers["risk"].shap_values(x3)[0]
    contributions = {f: float(v) for f, v in zip(RISK_FEATURES, sv3)}
    score = score_from_probability(probability, bundle["score_anchors"])

    pol = policy_svc.get_policy(db)
    level = policy_svc.level_for(score, pol)
    action = policy_svc.action_for(level)
    blocked = level == "high" and trust.inputs.report_score >= pol["block_report_score"]
    if blocked:
        action = "block"

    risk_reasons, safe_reasons = build_reasons(
        features,
        contributions,
        {
            "payee_name": payee.display_name,
            "amount": ctx.amount,
            "local_time": local_time,
            "has_history": len(past_amounts) >= 3,
            "report_count": trust.report_count,
            "m1_top": m1_top,
        },
    )
    return {
        "model_version": f"{registry.get('behaviour')['version']}+{bundle['version']}",
        "probability": round(probability, 6),
        "score": score,
        "level": level,
        "action": action,
        "blocked": blocked,
        "behaviour_score": round(behaviour, 5),
        "behaviour_top_feature": m1_top,
        "trust": trust.as_dict(),
        "features": {k: round(float(v), 5) for k, v in features.items()},
        "contributions": {k: round(v, 5) for k, v in contributions.items()},
        "base_value": round(float(bundle["base_value"]), 5),
        "reasons": risk_reasons,
        "reassurance": safe_reasons,
        "local_time": local_time,
        "sandbox_clock": simulated,
        "linked_sms_id": sms_id,
        "policy": pol,
        "evaluated_at": now.isoformat(),
    }
