"""File endpoints: upload / list / metadata / download / update / delete / verify."""

import base64
import binascii
import re
import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, File as FastAPIFile, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.api.deps import get_client_ip, get_current_user
from backend.app.core.config import get_settings
from backend.app.db.database import get_db
from backend.app.db.models import FilePermission, FileRecord, User
from backend.app.services import audit_service
from backend.app.services.permission_service import (
    can_delete, can_read, can_write, get_effective_role,
)

router = APIRouter(prefix="/api/files", tags=["files"])

SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def _storage_dir() -> Path:
    d = get_settings().storage_path
    d.mkdir(parents=True, exist_ok=True)
    return d


def _validate_b64(value: str, label: str, max_len: int = 200000) -> str:
    if not value or len(value) > max_len:
        raise HTTPException(status_code=400, detail=f"Invalid {label}")
    try:
        raw = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail=f"Invalid {label}: must be base64")
    if len(raw) == 0:
        raise HTTPException(status_code=400, detail=f"Invalid {label}: empty")
    return value


def _file_out(db: Session, f: FileRecord, viewer_id: int) -> dict:
    role = get_effective_role(db, f, viewer_id) or "none"
    owner = db.query(User).filter(User.id == f.owner_id).first()
    return {
        "id": f.id, "original_filename": f.original_filename, "mime_type": f.mime_type,
        "encrypted_size": f.encrypted_size, "original_size": f.original_size,
        "owner_id": f.owner_id, "owner_name": owner.name if owner else None,
        "owner_email": owner.email if owner else None, "effective_role": role,
        "plaintext_sha256": f.plaintext_sha256, "created_at": f.created_at, "updated_at": f.updated_at,
    }


def _require_file(db: Session, file_id: int) -> FileRecord:
    f = db.query(FileRecord).filter(FileRecord.id == file_id).first()
    if f is None:
        raise HTTPException(status_code=404, detail="File not found")
    return f


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload(
    request: Request,
    ciphertext: UploadFile = FastAPIFile(...),
    original_filename: str = Form(...),
    mime_type: str = Form(default="application/octet-stream"),
    original_size: int = Form(...),
    iv: str = Form(...),
    wrapped_fek: str = Form(...),
    plaintext_sha256: str = Form(...),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    settings = get_settings()
    data = await ciphertext.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty upload")
    if len(data) > settings.max_upload_bytes + 1024:  # ciphertext slightly larger than plaintext
        raise HTTPException(status_code=413, detail=f"File too large (max {settings.MAX_UPLOAD_MB} MB)")
    if not original_filename or len(original_filename) > 512:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if original_size < 0 or original_size > settings.max_upload_bytes:
        raise HTTPException(status_code=400, detail="Invalid original size")
    _validate_b64(iv, "IV", max_len=64)
    try:
        iv_raw = base64.b64decode(iv)
        if len(iv_raw) != 12:
            raise HTTPException(status_code=400, detail="IV must decode to 12 bytes")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid IV")
    _validate_b64(wrapped_fek, "wrapped FEK", max_len=5000)
    if not SHA256_RE.match(plaintext_sha256 or ""):
        raise HTTPException(status_code=400, detail="Invalid SHA-256 digest")

    stored = secrets.token_hex(16)
    dest = _storage_dir() / stored
    try:
        dest.write_bytes(data)
    except OSError:
        raise HTTPException(status_code=500, detail="Storage failure")
    rec = FileRecord(
        owner_id=current.id,
        original_filename=original_filename[:512],
        stored_filename=stored,
        mime_type=(mime_type or "application/octet-stream")[:255],
        encrypted_size=len(data),
        original_size=original_size,
        iv=iv,
        owner_wrapped_fek=wrapped_fek,
        plaintext_sha256=plaintext_sha256.lower(),
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    audit_service.record_event(db, action="upload", success=True, user_id=current.id, file_id=rec.id,
                               details=f"upload: {original_filename} ({original_size} bytes)",
                               ip_address=get_client_ip(request))
    return _file_out(db, rec, current.id)


@router.get("")
def list_files(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    owned = db.query(FileRecord).filter(FileRecord.owner_id == current.id).order_by(FileRecord.created_at.desc()).all()
    return [_file_out(db, f, current.id) for f in owned]


@router.get("/shared")
def list_shared(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    perms = db.query(FilePermission).filter(FilePermission.user_id == current.id).all()
    out = []
    for p in perms:
        f = db.query(FileRecord).filter(FileRecord.id == p.file_id).first()
        if f:
            out.append(_file_out(db, f, current.id))
    return out


@router.get("/{file_id}")
def get_metadata(file_id: int, request: Request, db: Session = Depends(get_db),
                 current: User = Depends(get_current_user)):
    f = _require_file(db, file_id)
    role = get_effective_role(db, f, current.id)
    if not can_read(role):
        audit_service.record_event(db, action="unauthorized_access", success=False, user_id=current.id,
                                   file_id=file_id, details="metadata access denied",
                                   ip_address=get_client_ip(request))
        raise HTTPException(status_code=403, detail="Access denied")
    info = _file_out(db, f, current.id)
    # Attach the wrapped FEK appropriate for this caller + IV so the browser can decrypt.
    if role == "owner":
        wrapped = f.owner_wrapped_fek
    else:
        perm = db.query(FilePermission).filter(
            FilePermission.file_id == f.id, FilePermission.user_id == current.id).first()
        wrapped = perm.wrapped_fek if perm else None
    info.update({"iv": f.iv, "wrapped_fek": wrapped})
    return info


@router.get("/{file_id}/download")
def download(file_id: int, request: Request, db: Session = Depends(get_db),
             current: User = Depends(get_current_user)):
    f = _require_file(db, file_id)
    role = get_effective_role(db, f, current.id)
    if not can_read(role):
        audit_service.record_event(db, action="unauthorized_access", success=False, user_id=current.id,
                                   file_id=file_id, details="download denied",
                                   ip_address=get_client_ip(request))
        raise HTTPException(status_code=403, detail="Access denied")
    path = _storage_dir() / f.stored_filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Stored object missing")
    if role == "owner":
        wrapped = f.owner_wrapped_fek
    else:
        perm = db.query(FilePermission).filter(
            FilePermission.file_id == f.id, FilePermission.user_id == current.id).first()
        wrapped = perm.wrapped_fek if perm else None
    audit_service.record_event(db, action="download", success=True, user_id=current.id, file_id=file_id,
                               details=f"ciphertext download by {current.email}",
                               ip_address=get_client_ip(request))
    return FileResponse(
        path=str(path),
        media_type="application/octet-stream",
        headers={
            "X-CipherVault-IV": f.iv,
            "X-CipherVault-Wrapped-FEK": wrapped or "",
            "X-CipherVault-SHA256": f.plaintext_sha256,
            "X-CipherVault-Filename": f.original_filename,
            "X-CipherVault-MIME": f.mime_type,
            "Access-Control-Expose-Headers": "X-CipherVault-IV, X-CipherVault-Wrapped-FEK, X-CipherVault-SHA256, X-CipherVault-Filename, X-CipherVault-MIME",
        },
    )


@router.delete("/{file_id}")
def delete_file(file_id: int, request: Request, db: Session = Depends(get_db),
                current: User = Depends(get_current_user)):
    f = _require_file(db, file_id)
    role = get_effective_role(db, f, current.id)
    if not can_delete(role):
        audit_service.record_event(db, action="unauthorized_access", success=False, user_id=current.id,
                                   file_id=file_id, details="delete denied (owner only)",
                                   ip_address=get_client_ip(request))
        raise HTTPException(status_code=403, detail="Only the owner can delete this file")
    path = _storage_dir() / f.stored_filename
    try:
        if path.exists():
            path.unlink()
    except OSError:
        raise HTTPException(status_code=500, detail="Storage failure during delete")
    audit_service.record_event(db, action="delete", success=True, user_id=current.id, file_id=None,
                               details=f"deleted file id={file_id} name={f.original_filename}",
                               ip_address=get_client_ip(request))
    db.delete(f)
    db.commit()
    return {"message": "File deleted"}


@router.put("/{file_id}", status_code=status.HTTP_200_OK)
async def update_file(
    file_id: int,
    request: Request,
    ciphertext: UploadFile = FastAPIFile(...),
    iv: str = Form(...),
    wrapped_fek: str | None = Form(default=None),
    plaintext_sha256: str = Form(...),
    original_size: int = Form(...),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    settings = get_settings()
    f = _require_file(db, file_id)
    role = get_effective_role(db, f, current.id)
    if not can_write(role):
        audit_service.record_event(db, action="unauthorized_access", success=False, user_id=current.id,
                                   file_id=file_id, details="update denied",
                                   ip_address=get_client_ip(request))
        raise HTTPException(status_code=403, detail="Access denied: update requires Owner or Editor")
    data = await ciphertext.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty upload")
    if len(data) > settings.max_upload_bytes + 1024:
        raise HTTPException(status_code=413, detail="File too large")
    _validate_b64(iv, "IV", max_len=64)
    try:
        if len(base64.b64decode(iv)) != 12:
            raise HTTPException(status_code=400, detail="IV must decode to 12 bytes")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid IV")
    if not SHA256_RE.match(plaintext_sha256 or ""):
        raise HTTPException(status_code=400, detail="Invalid SHA-256 digest")
    dest = _storage_dir() / f.stored_filename
    try:
        dest.write_bytes(data)
    except OSError:
        raise HTTPException(status_code=500, detail="Storage failure")
    f.iv = iv
    f.plaintext_sha256 = plaintext_sha256.lower()
    f.encrypted_size = len(data)
    f.original_size = original_size
    # If owner rotates the FEK, keep owner copy in sync. Editors keep their own wrapped copies;
    # owner should re-share afterwards for new content (documented in UI/docs).
    if role == "owner" and wrapped_fek:
        _validate_b64(wrapped_fek, "wrapped FEK", max_len=5000)
        f.owner_wrapped_fek = wrapped_fek
    db.commit()
    db.refresh(f)
    audit_service.record_event(db, action="file_update", success=True, user_id=current.id, file_id=file_id,
                               details=f"file updated by {current.email} (role={role})",
                               ip_address=get_client_ip(request))
    return _file_out(db, f, current.id)
