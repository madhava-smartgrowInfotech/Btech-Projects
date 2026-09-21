"""F6 plan comparison endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, status
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, get_owned_policy
from app.core.config import get_settings
from app.core.errors import AppError, NotFound
from app.models import Comparison, Policy, PolicyCard, RiskFlag

router = APIRouter(prefix="/comparisons", tags=["compare"])


class ComparisonIn(BaseModel):
    policy_a_id: int
    policy_b_id: int
    language: str | None = None


class ComparisonOut(BaseModel):
    id: int
    policy_a_id: int
    policy_b_id: int
    policy_a_name: str
    policy_b_name: str
    language: str
    result: dict[str, Any]
    model: str | None
    total_ms: int | None
    created_at: datetime


def _out(db, c: Comparison) -> ComparisonOut:  # noqa: ANN001
    a, b = db.get(Policy, c.policy_a_id), db.get(Policy, c.policy_b_id)
    return ComparisonOut(id=c.id, policy_a_id=c.policy_a_id, policy_b_id=c.policy_b_id,
                         policy_a_name=a.display_name if a else "", policy_b_name=b.display_name if b else "",
                         language=c.language, result=c.result, model=c.model, total_ms=c.total_ms,
                         created_at=c.created_at)


def _card_and_risks(db, policy: Policy) -> tuple[dict, list[dict]]:  # noqa: ANN001
    card = db.scalar(select(PolicyCard).where(PolicyCard.document_id == policy.document_id))
    if card is None:
        raise AppError(f"“{policy.display_name}” does not have a Policy Card yet.", code="card_missing")
    risks = [{"title": r.title, "severity": r.severity, "category": r.category, "clause_ordinal": r.clause_ordinal}
             for r in db.scalars(select(RiskFlag).where(RiskFlag.document_id == policy.document_id)).all()]
    order = {"high": 0, "medium": 1, "low": 2}
    risks.sort(key=lambda r: order.get(r["severity"], 3))
    return card.data, risks


@router.post("", response_model=ComparisonOut, status_code=status.HTTP_201_CREATED)
def create_comparison(body: ComparisonIn, user: CurrentUser, db: DbSession) -> ComparisonOut:
    from app.services.comparator import compare

    if body.policy_a_id == body.policy_b_id:
        raise AppError("Choose two different policies to compare.", code="same_policy")
    a = get_owned_policy(db, user, body.policy_a_id)
    b = get_owned_policy(db, user, body.policy_b_id)
    card_a, risks_a = _card_and_risks(db, a)
    card_b, risks_b = _card_and_risks(db, b)
    language = body.language or user.language or "en"
    if language not in get_settings().supported_languages:
        language = "en"
    result = compare(card_a, risks_a, card_b, risks_b, language, user.id)
    comp = Comparison(user_id=user.id, policy_a_id=a.id, policy_b_id=b.id, language=language, result=result,
                      model=result.get("model"), total_ms=result["timings"]["total_ms"])
    db.add(comp)
    db.commit()
    db.refresh(comp)
    return _out(db, comp)


@router.get("", response_model=list[ComparisonOut])
def list_comparisons(user: CurrentUser, db: DbSession) -> list[ComparisonOut]:
    rows = db.scalars(select(Comparison).where(Comparison.user_id == user.id).order_by(Comparison.created_at.desc()))
    return [_out(db, c) for c in rows.all()]


@router.get("/{comparison_id}", response_model=ComparisonOut)
def get_comparison(comparison_id: int, user: CurrentUser, db: DbSession) -> ComparisonOut:
    comp = db.get(Comparison, comparison_id)
    if comp is None or comp.user_id != user.id:
        raise NotFound("Comparison not found.")
    return _out(db, comp)


@router.delete("/{comparison_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comparison(comparison_id: int, user: CurrentUser, db: DbSession) -> None:
    comp = db.get(Comparison, comparison_id)
    if comp is None or comp.user_id != user.id:
        raise NotFound("Comparison not found.")
    db.delete(comp)
    db.commit()
