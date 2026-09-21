"""Append-only audit trail."""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models import AuditEvent, User

log = logging.getLogger("app.audit")


def record(db: Session, action: str, summary: str, *, actor: User | None = None, plan_id: int | None = None,
           details: dict | None = None) -> AuditEvent:
    """Add an audit event to the session; the caller commits it with the change it describes."""
    event = AuditEvent(action=action, summary=summary[:300], actor_id=actor.id if actor else None,
                       plan_id=plan_id, details=details or {})
    db.add(event)
    log.info(summary, extra={"action": action, "plan_id": plan_id, "actor": actor.email if actor else "system"})
    return event
