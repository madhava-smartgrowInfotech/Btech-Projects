"""F10 - fraud analytics for the fraud-risk team."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_admin
from app.models import IST, Hold, IntentCheck, RiskAssessment, ScamReport, SmsCheck, Transaction, User, Wallet, utcnow
from app.services import policy as policy_svc
from app.services.trust import compute_trust
from app.services.views import party

router = APIRouter(prefix="/admin", tags=["fraud analytics"])
STOPPED = ("cancelled", "rejected", "blocked")


def _stopped(t: Transaction) -> bool:
    return t.status in STOPPED and t.assessment is not None and t.assessment.final_level != "low"


@router.get("/overview")
def overview(days: int = Query(30, ge=1, le=365), _: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    since = utcnow() - timedelta(days=days)
    txns = db.scalars(select(Transaction).join(RiskAssessment).where(Transaction.created_at >= since)).all()
    levels = Counter(t.assessment.final_level for t in txns)
    stopped = [t for t in txns if _stopped(t)]
    released = [t for t in txns if t.hold and t.hold.status == "released"]
    held_now = db.scalar(select(func.count(Hold.id)).where(Hold.status == "active")) or 0
    sms = db.scalars(select(SmsCheck).where(SmsCheck.created_at >= since)).all()
    escalated = db.scalar(select(func.count(IntentCheck.id)).where(IntentCheck.created_at >= since, IntentCheck.matched_scam_type.is_not(None))) or 0
    intents = db.scalar(select(func.count(IntentCheck.id)).where(IntentCheck.created_at >= since)) or 0
    return {
        "days": days,
        "payments_scored": len(txns),
        "levels": {k: levels.get(k, 0) for k in ("low", "medium", "high")},
        "held_now": held_now,
        "holds_total": sum(1 for t in txns if t.hold),
        "holds_released": len(released),
        "payments_stopped": len(stopped),
        "blocked": sum(1 for t in txns if t.status == "blocked"),
        "money_protected": round(sum(t.amount_paise for t in stopped) / 100, 2),
        "average_score": round(sum(t.assessment.risk_score for t in txns) / len(txns), 1) if txns else 0,
        "intent_checks": intents,
        "intent_escalations": escalated,
        "sms_checks": len(sms),
        "sms_scams": sum(1 for s in sms if s.verdict == "scam"),
        "reports": db.scalar(select(func.count(ScamReport.id)).where(ScamReport.created_at >= since)) or 0,
        "users": db.scalar(select(func.count(User.id))) or 0,
    }


@router.get("/trends")
def trends(days: int = Query(30, ge=7, le=180), _: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    now = utcnow()
    since = now - timedelta(days=days)
    buckets: dict[str, dict] = {}
    for i in range(days - 1, -1, -1):
        key = (now - timedelta(days=i)).astimezone(IST).strftime("%Y-%m-%d")
        buckets[key] = {"date": key, "scored": 0, "medium": 0, "high": 0, "stopped": 0, "held": 0, "sms_scams": 0}
    for t in db.scalars(select(Transaction).join(RiskAssessment).where(Transaction.created_at >= since)).all():
        b = buckets.get(t.created_at.astimezone(IST).strftime("%Y-%m-%d"))
        if not b:
            continue
        b["scored"] += 1
        if t.assessment.final_level in ("medium", "high"):
            b[t.assessment.final_level] += 1
        if t.hold:
            b["held"] += 1
        if _stopped(t):
            b["stopped"] += 1
    for s in db.scalars(select(SmsCheck).where(SmsCheck.created_at >= since, SmsCheck.verdict == "scam")).all():
        b = buckets.get(s.created_at.astimezone(IST).strftime("%Y-%m-%d"))
        if b:
            b["sms_scams"] += 1
    return {"items": list(buckets.values())}


@router.get("/scam-types")
def scam_types(days: int = Query(30, ge=1, le=365), _: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    since = utcnow() - timedelta(days=days)
    sms = Counter(t for (t,) in db.execute(select(SmsCheck.scam_type).where(SmsCheck.created_at >= since, SmsCheck.scam_type.is_not(None))).all())
    intents = Counter(t for (t,) in db.execute(select(IntentCheck.matched_scam_type).where(IntentCheck.created_at >= since, IntentCheck.matched_scam_type.is_not(None))).all())
    reports = Counter(t for (t,) in db.execute(select(ScamReport.category).where(ScamReport.created_at >= since)).all())
    keys = sorted(set(sms) | set(intents) | set(reports), key=lambda k: -(sms[k] + intents[k] + reports[k]))
    return {"items": [{"scam_type": k, "sms": sms[k], "intent": intents[k], "reports": reports[k], "total": sms[k] + intents[k] + reports[k]} for k in keys]}


@router.get("/risk-distribution")
def distribution(days: int = Query(30, ge=1, le=365), _: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    since = utcnow() - timedelta(days=days)
    rows = db.execute(select(RiskAssessment.risk_score, Transaction.created_at).join(Transaction).where(Transaction.created_at >= since)).all()
    hist = [{"bucket": f"{b}-{b + 9}", "count": 0} for b in range(0, 100, 10)]
    by_hour: dict[int, list[int]] = defaultdict(list)
    for score, created in rows:
        hist[min(9, score // 10)]["count"] += 1
        by_hour[created.astimezone(IST).hour].append(score)
    hours = [{"hour": h, "payments": len(by_hour[h]), "high": sum(1 for s in by_hour[h] if s >= 70)} for h in range(24)]
    return {"histogram": hist, "by_hour": hours}


@router.get("/flagged")
def flagged(limit: int = Query(20, ge=1, le=200), _: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    rows = db.scalars(
        select(Transaction).join(RiskAssessment).where(RiskAssessment.final_level != "low", Transaction.status != "draft").order_by(Transaction.created_at.desc()).limit(limit)
    ).all()
    return {
        "items": [
            {
                "id": t.id,
                "reference": t.reference,
                "created_at": t.created_at,
                "payer": party(t.payer_wallet),
                "payee": party(t.payee_wallet),
                "amount": t.amount_paise / 100,
                "channel": t.channel,
                "status": t.status,
                "status_reason": t.status_reason,
                "score": t.assessment.risk_score,
                "level": t.assessment.final_level,
                "hold_status": t.hold.status if t.hold else None,
                "scam_type": t.intent.matched_scam_type if t.intent else None,
                "top_reasons": [r["text"] for r in t.assessment.reasons if r.get("kind") != "reassurance"][:3],
            }
            for t in rows
        ]
    }


@router.get("/reports")
def reported(_: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    rows = db.execute(select(ScamReport.upi_id, func.count(ScamReport.id), func.max(ScamReport.created_at)).group_by(ScamReport.upi_id).order_by(func.count(ScamReport.id).desc()).limit(20)).all()
    items = []
    for upi, n, last in rows:
        w = db.scalar(select(Wallet).where(Wallet.upi_id == upi))
        cats = Counter(c for (c,) in db.execute(select(ScamReport.category).where(ScamReport.upi_id == upi)).all())
        items.append(
            {
                "upi_id": upi,
                "name": w.display_name if w else None,
                "reports": n,
                "last_report": last,
                "top_category": cats.most_common(1)[0][0] if cats else None,
                "trust": compute_trust(db, w).score if w else None,
                "in_sandbox": w is not None,
            }
        )
    return {"items": items}


class PolicyIn(BaseModel):
    medium: int = Field(ge=5, le=90)
    high: int = Field(ge=10, le=99)
    block_report_score: float = Field(ge=0.5, le=20)

    @model_validator(mode="after")
    def _order(self):
        if self.high <= self.medium:
            raise ValueError("high must be greater than medium")
        return self


@router.get("/policy")
def get_policy(_: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    return policy_svc.get_policy(db) | {"defaults": policy_svc.default_policy()}


@router.put("/policy")
def put_policy(body: PolicyIn, _: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    return policy_svc.set_policy(db, body.medium, body.high, body.block_report_score) | {"defaults": policy_svc.default_policy()}
