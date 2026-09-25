"""Self-learning feedback loop and the weight time series behind it."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import WeightHistory
from ..recommender.feedback_engine import apply_feedback
from ..recommender.orchestrator import orchestrator
from ..schemas import FeedbackIn, FeedbackOut, WeightHistoryOut

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackOut)
def submit_feedback(payload: FeedbackIn, db: Session = Depends(get_db)):
    result = apply_feedback(
        db,
        orchestrator,
        rec_id=payload.rec_id,
        action=payload.action,
        session_id=payload.session_id,
        user_id=payload.user_id,
    )
    return FeedbackOut(
        ok=True,
        updated_weights=result["weights"],
        learning_step=result["step"],
        applied=result["applied"],
        reward=result["reward"],
        agent_credit=result.get("gains") or None,
        delta=result.get("delta"),
    )


@router.get("/weights-history", response_model=list[WeightHistoryOut])
def weights_history(limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)):
    rows = (
        db.execute(select(WeightHistory).order_by(WeightHistory.id.desc()).limit(limit))
        .scalars()
        .all()
    )
    rows.reverse()  # oldest first, so the chart reads left to right
    return [
        WeightHistoryOut(
            step=r.step,
            timestamp=r.created_at,
            weights=r.weights,
            trigger_action=r.trigger_action,
        )
        for r in rows
    ]
