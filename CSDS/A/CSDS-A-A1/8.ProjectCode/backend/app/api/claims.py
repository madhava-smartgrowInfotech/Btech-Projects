"""F5 Claim Copilot endpoints."""

from __future__ import annotations

from fastapi import APIRouter, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, get_owned_policy
from app.core.config import get_settings
from app.core.errors import AppError, NotFound
from app.models import ClaimCase, Policy, PolicyCard
from app.schemas.claim import ChecklistUpdate, ClaimCaseOut, ClaimIn

router = APIRouter(prefix="/claims", tags=["claim copilot"])


def _out(db, case: ClaimCase) -> ClaimCaseOut:  # noqa: ANN001
    policy = db.get(Policy, case.policy_id)
    return ClaimCaseOut(id=case.id, policy_id=case.policy_id, policy_name=policy.display_name if policy else "",
                        treatment=case.treatment, inputs=case.inputs, result=case.result, verdict=case.verdict,
                        checklist_state=case.checklist_state or {}, language=case.language,
                        faithfulness=case.faithfulness, total_ms=case.total_ms, model=case.model,
                        created_at=case.created_at)


def _owned(db, user, case_id: int) -> ClaimCase:  # noqa: ANN001
    case = db.get(ClaimCase, case_id)
    if case is None or case.user_id != user.id:
        raise NotFound("Claim check not found.")
    return case


@router.post("", response_model=ClaimCaseOut, status_code=status.HTTP_201_CREATED)
def create_claim_check(body: ClaimIn, user: CurrentUser, db: DbSession) -> ClaimCaseOut:
    from app.services.claim_copilot import run_claim_copilot

    policy = get_owned_policy(db, user, body.policy_id)
    if policy.document.status not in ("ready", "extracting"):
        raise AppError("This policy is still being processed. Please wait until it is ready.", code="busy",
                       status_code=409)
    language = body.language or user.language or "en"
    if language not in get_settings().supported_languages:
        language = "en"
    card = db.scalar(select(PolicyCard).where(PolicyCard.document_id == policy.document_id))
    inputs = body.model_dump(exclude={"policy_id", "language", "treatment"})
    result = run_claim_copilot(policy.document_id, card.data if card else None, body.treatment.strip(), inputs,
                               language, user.id)
    stored_inputs = {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in inputs.items()}
    case = ClaimCase(user_id=user.id, policy_id=policy.id, treatment=body.treatment.strip()[:300],
                     inputs=stored_inputs, result=result, verdict=result["verdict"], checklist_state={},
                     language=language, faithfulness=result["faithfulness"].get("score"),
                     total_ms=result["timings"]["total_ms"], model=result.get("model"))
    db.add(case)
    db.commit()
    db.refresh(case)
    return _out(db, case)


@router.get("", response_model=list[ClaimCaseOut])
def list_claim_checks(user: CurrentUser, db: DbSession) -> list[ClaimCaseOut]:
    cases = db.scalars(select(ClaimCase).where(ClaimCase.user_id == user.id).order_by(ClaimCase.created_at.desc()))
    return [_out(db, c) for c in cases.all()]


@router.get("/{case_id}", response_model=ClaimCaseOut)
def get_claim_check(case_id: int, user: CurrentUser, db: DbSession) -> ClaimCaseOut:
    return _out(db, _owned(db, user, case_id))


@router.patch("/{case_id}/checklist", response_model=ClaimCaseOut)
def update_checklist(case_id: int, body: ChecklistUpdate, user: CurrentUser, db: DbSession) -> ClaimCaseOut:
    case = _owned(db, user, case_id)
    valid = {d["id"] for d in case.result.get("documents", [])}
    if body.item_id not in valid:
        raise AppError("Unknown checklist item.", code="bad_item")
    state = dict(case.checklist_state or {})
    state[body.item_id] = body.done
    case.checklist_state = state
    db.commit()
    return _out(db, case)


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_claim_check(case_id: int, user: CurrentUser, db: DbSession) -> None:
    case = _owned(db, user, case_id)
    db.delete(case)
    db.commit()
