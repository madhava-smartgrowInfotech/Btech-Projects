"""Complaint lifecycle: Detected -> Registered -> Acknowledged -> In progress -> Resolved -> Verified (or reopened)."""
from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..core.db import utcnow
from ..core.logging import log_event
from ..models import Complaint, ComplaintEvent, User
from . import events, notifier
from .llm import rewrite_summary

log = logging.getLogger("signalscout.complaints")

# to_status -> (allowed from statuses, minimum role for a person; "system" transitions are always allowed)
TRANSITIONS: dict[str, tuple[tuple[str, ...], str]] = {
    "registered": (("detected", "resolved"), "engineer"),        # register now / reopen
    "acknowledged": (("registered",), "engineer"),
    "in_progress": (("registered", "acknowledged"), "engineer"),
    "resolved": (("acknowledged", "in_progress"), "engineer"),
    "verified": (("resolved",), "engineer"),
    "dismissed": (("detected", "registered", "acknowledged"), "engineer"),
}
TIMESTAMP_FIELD = {"registered": "registered_at", "acknowledged": "acknowledged_at", "in_progress": "in_progress_at",
                   "resolved": "resolved_at", "verified": "verified_at", "dismissed": "dismissed_at"}
STATUS_LABEL = {"detected": "Detected", "registered": "Registered", "acknowledged": "Acknowledged", "in_progress": "In progress",
                "resolved": "Resolved", "verified": "Verified", "dismissed": "Dismissed"}


def next_ref(db: Session, c: Complaint) -> str:
    return f"SS-{(c.detected_at or utcnow()).year}-{c.id:06d}"


def add_event(db: Session, c: Complaint, kind: str, note: str | None = None, actor: User | None = None,
              from_status: str | None = None, to_status: str | None = None) -> ComplaintEvent:
    e = ComplaintEvent(complaint_id=c.id, kind=kind, note=note, from_status=from_status, to_status=to_status,
                       actor_user_id=actor.id if actor else None, actor_label=actor.name if actor else "System")
    db.add(e)
    return e


def publish(c: Complaint, event: str) -> None:
    events.publish("complaint", {"id": c.id, "ref_code": c.ref_code, "status": c.status, "event": event, "operator": c.operator,
                                 "severity": c.severity, "source": c.source, "lat": c.lat, "lon": c.lon})


def register(db: Session, c: Complaint, note: str, actor: User | None = None, reopen: bool = False, at=None) -> None:
    """Freeze the evidence, issue the reference, write the summary and notify."""
    prev = c.status
    c.status = "registered"
    c.registered_at = c.registered_at or at or utcnow()   # "at": reading time that met the rule (replays, late syncs)
    if reopen:
        c.reopen_count += 1
        c.resolved_at = None
    c.summary = rewrite_summary(c.summary or "", c.evidence or {}) if not reopen else c.summary
    add_event(db, c, "status", note, actor, prev, "registered")
    notifier.queue_for_complaint(db, c, "reopened" if reopen else "registered")
    db.commit()
    publish(c, "reopened" if reopen else "registered")
    log_event(log, "complaint reopened" if reopen else "complaint registered", ref=c.ref_code, operator=c.operator, source=c.source)


def transition(db: Session, c: Complaint, to: str, actor: User | None, note: str | None = None) -> Complaint:
    if to not in TRANSITIONS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"Unknown status: {to}")
    allowed_from, _ = TRANSITIONS[to]
    if c.status not in allowed_from:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            detail=f"A complaint that is {STATUS_LABEL[c.status]} cannot move to {STATUS_LABEL[to]}")
    if to == "registered":
        register(db, c, note or ("Reopened by an engineer" if c.status == "resolved" else "Registered by an engineer"), actor,
                 reopen=c.status == "resolved")
        return c
    prev = c.status
    c.status = to
    setattr(c, TIMESTAMP_FIELD[to], utcnow())
    if to == "resolved":
        c.verification = {"state": "waiting", "since": utcnow().isoformat() + "Z", "readings": 0}
    if to == "verified" and actor:
        c.verification = {**(c.verification or {}), "state": "confirmed_by_engineer"}
    add_event(db, c, "status", note, actor, prev, to)
    notifier.queue_for_complaint(db, c, to)
    db.commit()
    publish(c, to)
    log_event(log, "complaint status", ref=c.ref_code, to=to, by=actor.id if actor else "system")
    return c
