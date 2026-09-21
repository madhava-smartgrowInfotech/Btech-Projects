from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import delete

from app.core.deps import DB, AdminUser, CurrentUser
from app.core.errors import AppError
from app.models import (
    AttendanceMark, Candidate, Course, Department, ExamSession, Hall, HallSubmission, ImportBatch,
    InvigilatorAssignment, Plan, Registration, SeatAssignment, SessionPaper,
)
from app.schemas.settings import RulesIn, RulesOut
from app.services import audit
from app.services.settings_service import get_rules, save_rules

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/rules", response_model=RulesOut, summary="Default seating rules")
def read_rules(db: DB, _: CurrentUser) -> RulesOut:
    return RulesOut(**get_rules(db).model_dump())


@router.put("/rules", response_model=RulesOut, summary="Change the default seating rules")
def update_rules(body: RulesIn, db: DB, admin: AdminUser) -> RulesOut:
    before = get_rules(db).model_dump()
    save_rules(db, body)
    changed = {k: [before[k], v] for k, v in body.model_dump().items() if before.get(k) != v}
    if changed:
        audit.record(db, "settings.rules", f"{admin.full_name} changed default rules: "
                     + ", ".join(f"{k} {a} -> {b}" for k, (a, b) in changed.items()), actor=admin, details=changed)
    db.commit()
    return RulesOut(**body.model_dump())


class ResetIn(BaseModel):
    confirm: str


@router.post("/reset-workspace", summary="Delete all exam data (accounts and settings are kept)")
def reset_workspace(body: ResetIn, db: DB, admin: AdminUser) -> dict:
    if body.confirm != "RESET":
        raise AppError('Type RESET to confirm.', 400)
    counts = {}
    for model in (AttendanceMark, HallSubmission, InvigilatorAssignment, SeatAssignment, Plan, SessionPaper,
                  ExamSession, Registration, Candidate, Course, Department, Hall, ImportBatch):
        counts[model.__tablename__] = db.execute(delete(model)).rowcount
    audit.record(db, "workspace.reset", f"{admin.full_name} cleared all exam data", actor=admin, details=counts)
    db.commit()
    return {"deleted": counts}
