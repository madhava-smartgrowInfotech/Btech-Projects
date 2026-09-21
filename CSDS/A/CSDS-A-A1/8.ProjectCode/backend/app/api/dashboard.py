"""Dashboard: KPIs and chart series computed from the signed-in user's own activity."""

from __future__ import annotations

import statistics
from datetime import timedelta
from typing import Any

from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.core.db import utcnow
from app.models import ClaimCase, Comparison, Conversation, LlmCall, Message, Policy, RiskFlag

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(user: CurrentUser, db: DbSession) -> dict[str, Any]:
    policies = db.scalars(select(Policy).where(Policy.owner_id == user.id)).all()
    doc_ids = [p.document_id for p in policies]
    answers = db.execute(
        select(Message.id, Message.faithfulness, Message.total_ms, Message.created_at, Message.status)
        .join(Conversation, Conversation.id == Message.conversation_id)
        .where(Conversation.user_id == user.id, Message.role == "assistant")
        .order_by(Message.created_at)
    ).all()
    claims = db.scalars(select(ClaimCase).where(ClaimCase.user_id == user.id)).all()
    comparisons = db.scalar(select(func.count()).select_from(Comparison).where(Comparison.user_id == user.id)) or 0
    risks = db.execute(select(RiskFlag.document_id, RiskFlag.severity, func.count())
                       .where(RiskFlag.document_id.in_(doc_ids or [-1]))
                       .group_by(RiskFlag.document_id, RiskFlag.severity)).all()
    calls = db.execute(select(func.count(), func.coalesce(func.sum(LlmCall.input_tokens), 0),
                              func.coalesce(func.sum(LlmCall.output_tokens), 0))
                       .where(LlmCall.user_id == user.id, LlmCall.ok.is_(True))).one()

    faith = [a.faithfulness for a in answers if a.faithfulness is not None]
    times = [a.total_ms for a in answers if a.total_ms]
    per_doc: dict[int, dict[str, int]] = {}
    for doc_id, severity, count in risks:
        per_doc.setdefault(doc_id, {"high": 0, "medium": 0, "low": 0})[severity] = int(count)

    today = utcnow().date()
    days = [today - timedelta(days=i) for i in range(13, -1, -1)]
    by_day = {d: 0 for d in days}
    for a in answers:
        d = a.created_at.date()
        if d in by_day:
            by_day[d] += 1
    claims_by_day = {d: 0 for d in days}
    for c in claims:
        d = c.created_at.date()
        if d in claims_by_day:
            claims_by_day[d] += 1

    bins = [("0-49", 0, 50), ("50-79", 50, 80), ("80-100", 80, 101)]
    verdict_counts: dict[str, int] = {}
    for c in claims:
        verdict_counts[c.verdict] = verdict_counts.get(c.verdict, 0) + 1

    recent: list[dict[str, Any]] = []
    for p in policies:
        recent.append({"type": "policy", "title": f"Added {p.display_name}", "at": p.created_at,
                       "link": f"/app/policies/{p.id}"})
    for c in claims:
        recent.append({"type": "claim", "title": f"Claim check: {c.treatment}", "at": c.created_at,
                       "link": f"/app/claims/{c.id}", "verdict": c.verdict})
    convs = db.scalars(select(Conversation).where(Conversation.user_id == user.id)).all()
    for conv in convs:
        recent.append({"type": "chat", "title": conv.title, "at": conv.updated_at, "link": f"/app/chat/{conv.id}"})
    recent.sort(key=lambda r: r["at"], reverse=True)

    names = {p.document_id: p.display_name for p in policies}
    return {
        "kpis": {
            "policies": len(policies),
            "ready_policies": sum(1 for p in policies if p.document.status == "ready"),
            "questions": len(answers),
            "avg_faithfulness": round(statistics.fmean(faith), 1) if faith else None,
            "median_response_ms": round(statistics.median(times)) if times else None,
            "claim_checks": len(claims),
            "comparisons": comparisons,
            "high_risks": sum(v["high"] for v in per_doc.values()),
            "ai_calls": int(calls[0] or 0),
            "ai_tokens": int((calls[1] or 0) + (calls[2] or 0)),
        },
        "activity_by_day": [{"date": d.isoformat(), "questions": by_day[d], "claim_checks": claims_by_day[d]}
                            for d in days],
        "faithfulness_bins": [{"bin": label, "count": sum(1 for f in faith if lo <= f < hi)}
                              for label, lo, hi in bins],
        "verdicts": [{"verdict": k, "count": v} for k, v in sorted(verdict_counts.items())],
        "risks_by_policy": [{"policy": names.get(doc_id, f"Policy {doc_id}"), **counts}
                            for doc_id, counts in per_doc.items()],
        "response_times": [{"n": i + 1, "ms": a.total_ms, "faithfulness": a.faithfulness}
                           for i, a in enumerate(answers[-20:]) if a.total_ms],
        "recent": recent[:8],
    }
