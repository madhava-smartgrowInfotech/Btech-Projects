"""Hash-chained audit log service."""

import hashlib
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.db.models import AuditLog

GENESIS = "GENESIS"


def _hash_event(previous_hash: str, timestamp: datetime, user_id, file_id, action: str, success: bool, details: str) -> str:
    body = f"{previous_hash}|{timestamp.isoformat()}|{user_id}|{file_id}|{action}|{success}|{details}"
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def record_event(
    db: Session,
    *,
    action: str,
    success: bool = True,
    user_id: int | None = None,
    file_id: int | None = None,
    details: str = "",
    ip_address: str | None = None,
) -> AuditLog:
    last = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    previous_hash = last.current_hash if last else GENESIS
    now = datetime.now(timezone.utc)
    current_hash = _hash_event(previous_hash, now, user_id, file_id, action, success, details)
    entry = AuditLog(
        timestamp_utc=now,
        user_id=user_id,
        file_id=file_id,
        action=action,
        success=success,
        ip_address=ip_address,
        details=details[:2000],
        previous_hash=previous_hash,
        current_hash=current_hash,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def verify_chain(db: Session) -> tuple[bool, int, int | None]:
    """Recompute the chain. Returns (valid, checked_count, failure_id)."""
    entries = db.query(AuditLog).order_by(AuditLog.id.asc()).all()
    expected_prev = GENESIS
    for entry in entries:
        ts = entry.timestamp_utc
        if ts is not None and ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        recomputed = _hash_event(
            entry.previous_hash, ts, entry.user_id, entry.file_id,
            entry.action, entry.success, entry.details or "",
        )
        if entry.previous_hash != expected_prev or recomputed != entry.current_hash:
            return False, len(entries), entry.id
        expected_prev = entry.current_hash
    return True, len(entries), None
