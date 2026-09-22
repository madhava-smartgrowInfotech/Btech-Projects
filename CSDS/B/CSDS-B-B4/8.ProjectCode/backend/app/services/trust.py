"""F3 - payee trust score from the sandbox ledger: account age, received-payment pattern, community reports."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ml.features import TrustInputs, report_weight, trust_band, trust_score
from app.models import CollectRequest, ScamReport, Transaction, User, Wallet, utcnow

SETTLED = ("completed",)


@dataclass
class TrustResult:
    score: int
    band: str
    components: list[dict]
    inputs: TrustInputs
    report_count: int

    def as_dict(self) -> dict:
        return {
            "score": self.score,
            "band": self.band,
            "components": self.components,
            "account_age_days": int(self.inputs.account_age_days),
            "report_count": self.report_count,
            "report_score": round(self.inputs.report_score, 3),
            "distinct_payers_24h": self.inputs.distinct_payers_24h,
            "distinct_payers_7d": self.inputs.distinct_payers_7d,
            "new_payer_share_7d": round(self.inputs.new_payer_share_7d, 3),
            "distinct_payers_90d": self.inputs.distinct_payers_90d,
            "collect_targets_7d": self.inputs.collect_targets_7d,
            "is_merchant": self.inputs.is_merchant,
        }


def report_score(db: Session, upi_id: str, now: datetime) -> tuple[float, int]:
    rows = db.execute(
        select(ScamReport.created_at, User.created_at)
        .join(User, User.id == ScamReport.reporter_user_id)
        .where(ScamReport.upi_id == upi_id, ScamReport.created_at <= now)
    ).all()
    score = sum(report_weight((r_created - u_created).total_seconds() / 86400, (now - r_created).total_seconds() / 86400) for r_created, u_created in rows)
    return float(score), len(rows)


def compute_trust(db: Session, wallet: Wallet, now: datetime | None = None) -> TrustResult:
    now = now or utcnow()
    since90 = now - timedelta(days=90)
    inbound = db.execute(
        select(Transaction.created_at, Transaction.payer_wallet_id)
        .where(Transaction.payee_wallet_id == wallet.id, Transaction.status.in_(SETTLED), Transaction.created_at >= since90, Transaction.created_at <= now)
        .order_by(Transaction.created_at)
    ).all()
    # First-ever payment time of each payer to this payee (for the "new payer" share).
    firsts = dict(
        db.execute(
            select(Transaction.payer_wallet_id, func.min(Transaction.created_at))
            .where(Transaction.payee_wallet_id == wallet.id, Transaction.status.in_(SETTLED))
            .group_by(Transaction.payer_wallet_id)
        ).all()
    )
    d24 = {p for t, p in inbound if t >= now - timedelta(days=1)}
    w7 = [(t, p) for t, p in inbound if t >= now - timedelta(days=7)]
    d7 = {p for _, p in w7}
    new_share = (sum(1 for t, p in w7 if firsts.get(p) == t) / len(w7)) if w7 else 0.0
    collect_targets = db.scalar(
        select(func.count(func.distinct(CollectRequest.payer_wallet_id))).where(
            CollectRequest.requester_wallet_id == wallet.id, CollectRequest.created_at >= now - timedelta(days=7)
        )
    ) or 0
    reports, n_reports = report_score(db, wallet.upi_id, now)
    inputs = TrustInputs(
        account_age_days=max(0.0, (now - wallet.created_at).total_seconds() / 86400),
        report_score=reports,
        distinct_payers_24h=len(d24),
        distinct_payers_7d=len(d7),
        new_payer_share_7d=new_share,
        inbound_count_90d=len(inbound),
        distinct_payers_90d=len({p for _, p in inbound}),
        collect_targets_7d=int(collect_targets),
        is_merchant=wallet.is_merchant,
    )
    score, components = trust_score(inputs)
    return TrustResult(score=score, band=trust_band(score), components=components, inputs=inputs, report_count=n_reports)
