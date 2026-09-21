"""Claim Copilot verdict accuracy on hand-written scenarios (confusion matrix over the four verdicts)."""

from __future__ import annotations

import statistics
from datetime import date
from typing import Any

from ml import common  # noqa: F401
from ml.metrics import classification_report, latency_stats

LABELS = ["covered", "partly_covered", "not_covered", "needs_info"]


def _months_ago(months: int, today: date) -> date:
    year, month = today.year, today.month - months
    while month <= 0:
        month += 12
        year -= 1
    return date(year, month, min(today.day, 28))


def run(doc_ids: dict[str, int], scenarios: list[dict[str, Any]], log=print, run=None) -> tuple[dict, list[dict]]:  # noqa: ANN001,A002
    from sqlalchemy import select

    from app.core.db import SessionLocal
    from app.models import PolicyCard
    from app.services.claim_copilot import run_claim_copilot

    done = {p["id"]: p for p in (run.load_predictions("claims.jsonl") if run else [])}
    today = date.today()
    rows: list[dict] = []
    for sc in scenarios:
        if sc["id"] in done:
            rows.append(done[sc["id"]])
            continue
        doc_id = doc_ids[sc["policy"]]
        with SessionLocal() as db:
            card = db.scalar(select(PolicyCard).where(PolicyCard.document_id == doc_id))
        inputs = dict(sc["inputs"])
        months = inputs.pop("policy_start_date_months_ago", None)
        inputs["policy_start_date"] = _months_ago(months, today) if months is not None else None
        inputs.setdefault("room_type", "not_sure")
        try:
            result = run_claim_copilot(doc_id, card.data if card else None, sc["treatment"], inputs, "en", None,
                                       cache=True)
        except Exception as exc:  # noqa: BLE001
            log(f"claim {sc['id']}: ERROR {exc}")
            rows.append({"id": sc["id"], "error": str(exc)[:300]})
            continue
        row = {
            "id": sc["id"],
            "policy": sc["policy"],
            "treatment": sc["treatment"],
            "expected": sc["expected_verdict"],
            "predicted": result["verdict"],
            "model_verdict": result["model_verdict"],
            "summary": result["verdict_summary_en"],
            "faithfulness": result["faithfulness"].get("score"),
            "documents": len(result["documents"]),
            "steps": len(result["steps"]),
            "total_ms": result["timings"]["total_ms"],
            "model": result.get("model"),
        }
        rows.append(row)
        if run:
            run.append_prediction(row, "claims.jsonl")
        log(f"claim {sc['id']}: expected={row['expected']} predicted={row['predicted']} ms={row['total_ms']}")
    ok = [r for r in rows if "error" not in r]
    report = classification_report([r["expected"] for r in ok], [r["predicted"] for r in ok], LABELS) if ok else {}
    faith = [r["faithfulness"] for r in ok if r["faithfulness"] is not None]
    report.update({
        "n": len(ok),
        "errors": len(rows) - len(ok),
        "faithfulness_mean": round(statistics.fmean(faith), 1) if faith else None,
        "avg_documents": round(statistics.fmean(r["documents"] for r in ok), 1) if ok else None,
        "avg_steps": round(statistics.fmean(r["steps"] for r in ok), 1) if ok else None,
        "latency_ms": latency_stats([r["total_ms"] for r in ok]),
    })
    return report, rows
