"""Sharing endpoints: share / list / change role / revoke (owner only)."""

import base64
import binascii

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.api.deps import get_client_ip, get_current_user
from backend.app.db.database import get_db
from backend.app.db.models import FilePermission, FileRecord, User
from backend.app.schemas.schemas import ChangeRoleRequest, ShareRequest
from backend.app.services import audit_service
from backend.app.services.permission_service import can_share, get_effective_role

router = APIRouter(prefix="/api/files", tags=["sharing"])


def _require_owned_file(db: Session, file_id: int, current: User) -> FileRecord:
    f = db.query(FileRecord).filter(FileRecord.id == file_id).first()
    if f is None:
        raise HTTPException(status_code=404, detail="File not found")
    if not can_share(get_effective_role(db, f, current.id)):
        raise HTTPException(status_code=403, detail="Only the owner can manage access")
    return f


@router.post("/{file_id}/share")
def share_file(file_id: int, payload: ShareRequest, request: Request,
               db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    f = _require_owned_file(db, file_id, current)
    target = None
    if payload.user_id is not None:
        target = db.query(User).filter(User.id == payload.user_id, User.is_active.is_(True)).first()
    elif payload.email is not None:
        target = db.query(User).filter(User.email == payload.email.strip().lower()).first()
    if target is None:
        raise HTTPException(status_code=404, detail="Share target user not found")
    if target.id == f.owner_id:
        raise HTTPException(status_code=400, detail="User is already the owner")
    if payload.role not in ("viewer", "editor"):
        raise HTTPException(status_code=400, detail="Invalid role")
    try:
        raw = base64.b64decode(payload.wrapped_fek, validate=True)
        if len(raw) != 256:  # RSA-2048 OAEP output is 256 bytes
            raise HTTPException(status_code=400, detail="wrapped_fek must be a 256-byte RSA-OAEP value (base64)")
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="wrapped_fek must be base64")
    existing = db.query(FilePermission).filter(
        FilePermission.file_id == file_id, FilePermission.user_id == target.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="User already has access; use change-role instead")
    perm = FilePermission(file_id=file_id, user_id=target.id, role=payload.role, wrapped_fek=payload.wrapped_fek)
    db.add(perm)
    db.commit()
    audit_service.record_event(db, action="share", success=True, user_id=current.id, file_id=file_id,
                               details=f"shared with {target.email} as {payload.role}",
                               ip_address=get_client_ip(request))
    return {"message": "Shared", "user_id": target.id, "role": payload.role}


@router.get("/{file_id}/permissions")
def list_permissions(file_id: int, request: Request,
                     db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    f = db.query(FileRecord).filter(FileRecord.id == file_id).first()
    if f is None:
        raise HTTPException(status_code=404, detail="File not found")
    role = get_effective_role(db, f, current.id)
    if role is None:
        audit_service.record_event(db, action="unauthorized_access", success=False, user_id=current.id,
                                   file_id=file_id, details="permission list denied",
                                   ip_address=get_client_ip(request))
        raise HTTPException(status_code=403, detail="Access denied")
    perms = db.query(FilePermission).filter(FilePermission.file_id == file_id).all()
    owner = db.query(User).filter(User.id == f.owner_id).first()
    out = [{
        "user_id": owner.id if owner else f.owner_id,
        "user_name": owner.name if owner else None,
        "user_email": owner.email if owner else None,
        "role": "owner",
        "created_at": None,
    }] if owner or True else []
    for p in perms:
        u = db.query(User).filter(User.id == p.user_id).first()
        out.append({"user_id": p.user_id, "user_name": u.name if u else None,
                    "user_email": u.email if u else None, "role": p.role, "created_at": p.created_at})
    return out


@router.put("/{file_id}/permissions/{user_id}")
def change_role(file_id: int, user_id: int, payload: ChangeRoleRequest, request: Request,
                db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    _require_owned_file(db, file_id, current)
    perm = db.query(FilePermission).filter(
        FilePermission.file_id == file_id, FilePermission.user_id == user_id).first()
    if perm is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    perm.role = payload.role
    db.commit()
    audit_service.record_event(db, action="permission_change", success=True, user_id=current.id, file_id=file_id,
                               details=f"role of user {user_id} changed to {payload.role}",
                               ip_address=get_client_ip(request))
    return {"message": "Role updated", "user_id": user_id, "role": payload.role}


@router.delete("/{file_id}/permissions/{user_id}")
def revoke(file_id: int, user_id: int, request: Request,
           db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    _require_owned_file(db, file_id, current)
    perm = db.query(FilePermission).filter(
        FilePermission.file_id == file_id, FilePermission.user_id == user_id).first()
    if perm is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    db.delete(perm)
    db.commit()
    audit_service.record_event(db, action="access_revocation", success=True, user_id=current.id, file_id=file_id,
                               details=f"revoked access of user {user_id}",
                               ip_address=get_client_ip(request))
    return {"message": "Access revoked"}
