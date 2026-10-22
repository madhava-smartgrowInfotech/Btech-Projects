"""Audit endpoints: history + chain verification."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.database import get_db
from backend.app.db.models import AuditLog, FileRecord, User
from backend.app.services import audit_service
from backend.app.services.permission_service import get_effective_role

router = APIRouter(prefix="/api/audit", tags=["audit"])


def _out(db: Session, e: AuditLog) -> dict:
    u = db.query(User).filter(User.id == e.user_id).first() if e.user_id else None
    return {
        "id": e.id, "timestamp_utc": e.timestamp_utc, "user_id": e.user_id,
        "user_email": u.email if u else None, "file_id": e.file_id, "action": e.action,
        "success": e.success, "ip_address": e.ip_address, "details": e.details,
        "previous_hash": e.previous_hash, "current_hash": e.current_hash,
    }


@router.get("")
def list_audit(limit: int = Query(default=100, le=500), action: str | None = None,
               db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    # Any authenticated user sees the global security-event history (no secrets stored in logs).
    q = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(limit)
    events = q.all()
    if action:
        events = [e for e in events if e.action == action]
    return [_out(db, e) for e in events]


@router.get("/file/{file_id}")
def file_audit(file_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    from fastapi import HTTPException
    f = db.query(FileRecord).filter(FileRecord.id == file_id).first()
    if f is None:
        # Show deletion/orphan events referencing the id anyway
        events = db.query(AuditLog).filter(AuditLog.file_id == file_id).order_by(AuditLog.id.desc()).all()
        return [_out(db, e) for e in events]
    role = get_effective_role(db, f, current.id)
    if role != "owner":
        raise HTTPException(status_code=403, detail="Only the owner can view file audit history")
    events = db.query(AuditLog).filter(AuditLog.file_id == file_id).order_by(AuditLog.id.desc()).all()
    return [_out(db, e) for e in events]


@router.get("/verify")
def verify(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    valid, checked, failure_at = audit_service.verify_chain(db)
    audit_service.record_event(
        db, action="integrity_verification" if valid else "failed_integrity_verification",
        success=valid, user_id=current.id,
        details=f"audit chain verification: {'valid' if valid else 'FAILURE'} ({checked} entries checked)",
        ip_address=None,
    )
    return {"valid": valid, "checked": checked, "failure_at": failure_at,
            "message": "Audit chain valid" if valid else f"Audit chain integrity failure at entry {failure_at}"}
