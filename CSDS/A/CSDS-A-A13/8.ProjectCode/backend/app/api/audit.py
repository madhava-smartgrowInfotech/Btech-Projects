from fastapi import APIRouter
from sqlalchemy import select

from app.core.deps import DB, AdminUser
from app.models import AuditEvent, User
from app.schemas.plans import AuditOut

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditOut], summary="Audit trail (newest first)")
def audit_trail(db: DB, _: AdminUser, plan_id: int | None = None, action: str | None = None,
                limit: int = 200) -> list[AuditOut]:
    stmt = select(AuditEvent).order_by(AuditEvent.id.desc()).limit(min(max(limit, 1), 1000))
    if plan_id is not None:
        stmt = stmt.where(AuditEvent.plan_id == plan_id)
    if action:
        stmt = stmt.where(AuditEvent.action.startswith(action))
    names = {u.id: u.full_name for u in db.scalars(select(User))}
    return [AuditOut(id=e.id, at=e.at, action=e.action, summary=e.summary, actor=names.get(e.actor_id),
                     plan_id=e.plan_id, details=e.details or {}) for e in db.scalars(stmt)]
