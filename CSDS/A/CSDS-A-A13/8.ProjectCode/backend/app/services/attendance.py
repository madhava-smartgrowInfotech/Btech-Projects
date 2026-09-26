"""Hall attendance: marking, scanning seat slips, and locking a hall's register."""
from __future__ import annotations

import re
from collections import Counter
from urllib.parse import unquote, urlparse

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.errors import AppError, NotFound
from app.models import AttendanceMark, Candidate, Hall, HallSubmission, InvigilatorAssignment, Plan, SeatAssignment, User
from app.models._common import utcnow
from app.models.attendance import ABSENT, PRESENT
from app.models.plan import PLAN_PUBLISHED
from app.services import audit


def _load(db: Session, plan_id: int, hall_id: int, user: User) -> tuple[Plan, Hall]:
    plan = db.get(Plan, plan_id)
    hall = db.get(Hall, hall_id)
    if plan is None:
        raise NotFound("Plan")
    if hall is None or hall.id not in plan.hall_ids:
        raise NotFound("Hall in this plan")
    if plan.status != PLAN_PUBLISHED:
        raise AppError("Attendance is taken on the published plan only.", 409)
    if not user.is_admin:
        assigned = db.scalar(select(InvigilatorAssignment.id).where(
            InvigilatorAssignment.plan_id == plan.id, InvigilatorAssignment.hall_id == hall.id,
            InvigilatorAssignment.user_id == user.id))
        if assigned is None:
            raise AppError("You are not assigned to this hall.", 403)
    return plan, hall


def _submission(db: Session, plan: Plan, hall: Hall) -> HallSubmission | None:
    return db.scalar(select(HallSubmission).where(HallSubmission.plan_id == plan.id, HallSubmission.hall_id == hall.id))


def _ensure_open(db: Session, plan: Plan, hall: Hall) -> None:
    if _submission(db, plan, hall) is not None:
        raise AppError("Attendance for this hall has been submitted. An administrator can reopen it.", 409)


def counts(db: Session, plan: Plan, hall: Hall) -> dict:
    seated = db.scalars(select(SeatAssignment.candidate_id).where(SeatAssignment.plan_id == plan.id,
                                                                  SeatAssignment.hall_id == hall.id)).all()
    marks = Counter(db.scalars(select(AttendanceMark.status).where(AttendanceMark.plan_id == plan.id,
                                                                   AttendanceMark.hall_id == hall.id)))
    sub = _submission(db, plan, hall)
    return {"total": len(seated), "present": marks[PRESENT], "absent": marks[ABSENT],
            "unmarked": len(seated) - marks[PRESENT] - marks[ABSENT],
            "submitted_at": sub.submitted_at.isoformat() if sub else None}


def _set(db: Session, plan: Plan, hall: Hall, candidate_id: int, status: str | None, user: User, method: str) -> None:
    mark = db.scalar(select(AttendanceMark).where(AttendanceMark.plan_id == plan.id,
                                                  AttendanceMark.candidate_id == candidate_id))
    if status is None:
        if mark is not None:
            db.delete(mark)
        return
    if mark is None:
        db.add(AttendanceMark(plan_id=plan.id, candidate_id=candidate_id, hall_id=hall.id, status=status,
                              method=method, marked_by=user.id))
    else:
        mark.status, mark.method, mark.marked_by, mark.marked_at = status, method, user.id, utcnow()


def mark(db: Session, plan_id: int, hall_id: int, candidate_id: int, status: str | None, user: User) -> dict:
    plan, hall = _load(db, plan_id, hall_id, user)
    _ensure_open(db, plan, hall)
    seat = db.scalar(select(SeatAssignment).where(SeatAssignment.plan_id == plan.id,
                                                  SeatAssignment.candidate_id == candidate_id))
    if seat is None or seat.hall_id != hall.id:
        raise AppError("This candidate is not seated in this hall.", 400)
    _set(db, plan, hall, candidate_id, status, user, "tap")
    db.commit()
    return counts(db, plan, hall)


_URL_ROLL = re.compile(r"/lookup/([^/?#]+)")


def parse_code(code: str) -> str:
    """A scanned slip holds the lookup URL; a typed code is the roll number itself."""
    text = code.strip()
    if "://" in text:
        match = _URL_ROLL.search(urlparse(text).path)
        if match:
            return unquote(match.group(1)).strip().upper()
    return text.upper()


def scan(db: Session, plan_id: int, hall_id: int, code: str, user: User) -> dict:
    plan, hall = _load(db, plan_id, hall_id, user)
    _ensure_open(db, plan, hall)
    roll = parse_code(code)
    if not roll:
        raise AppError("The code is empty.", 400)
    candidate = db.scalar(select(Candidate).where(Candidate.roll_no == roll))
    seat = db.scalar(select(SeatAssignment).where(SeatAssignment.plan_id == plan.id,
                                                  SeatAssignment.candidate_id == candidate.id)) if candidate else None
    if seat is None:
        raise AppError(f"{roll} is not seated in this sitting.", 404)
    if seat.hall_id != hall.id:
        other = db.get(Hall, seat.hall_id)
        raise AppError(f"{candidate.full_name} ({roll}) sits in {other.code} ({other.name}), seat {seat.seat_label} - "
                       "please send them there.", 409)
    existing = db.scalar(select(AttendanceMark).where(AttendanceMark.plan_id == plan.id,
                                                      AttendanceMark.candidate_id == candidate.id))
    already = existing is not None and existing.status == PRESENT
    _set(db, plan, hall, candidate.id, PRESENT, user, "scan")
    db.commit()
    return {"candidate": {"id": candidate.id, "roll_no": candidate.roll_no, "full_name": candidate.full_name},
            "seat": seat.seat_label, "already_present": already, "counts": counts(db, plan, hall)}


def mark_remaining_absent(db: Session, plan_id: int, hall_id: int, user: User) -> dict:
    plan, hall = _load(db, plan_id, hall_id, user)
    _ensure_open(db, plan, hall)
    marked = set(db.scalars(select(AttendanceMark.candidate_id).where(AttendanceMark.plan_id == plan.id,
                                                                      AttendanceMark.hall_id == hall.id)))
    seated = db.scalars(select(SeatAssignment.candidate_id).where(SeatAssignment.plan_id == plan.id,
                                                                  SeatAssignment.hall_id == hall.id)).all()
    n = 0
    for cid in seated:
        if cid not in marked:
            _set(db, plan, hall, cid, ABSENT, user, "bulk")
            n += 1
    db.commit()
    return {"marked_absent": n, **counts(db, plan, hall)}


def submit(db: Session, plan_id: int, hall_id: int, user: User) -> dict:
    plan, hall = _load(db, plan_id, hall_id, user)
    _ensure_open(db, plan, hall)
    c = counts(db, plan, hall)
    if c["unmarked"]:
        raise AppError(f"{c['unmarked']} candidates are not marked yet. Mark them, or mark the remaining ones absent.", 409)
    db.add(HallSubmission(plan_id=plan.id, hall_id=hall.id, submitted_by=user.id))
    audit.record(db, "attendance.submitted",
                 f"{user.full_name} submitted attendance for {hall.code}, {plan.session.label}: "
                 f"{c['present']} present, {c['absent']} absent", actor=user, plan_id=plan.id,
                 details={"hall": hall.code, **c})
    db.commit()
    return counts(db, plan, hall)


def reopen(db: Session, plan_id: int, hall_id: int, user: User) -> dict:
    if not user.is_admin:
        raise AppError("Only administrators can reopen a submitted register.", 403)
    plan, hall = _load(db, plan_id, hall_id, user)
    db.execute(delete(HallSubmission).where(HallSubmission.plan_id == plan.id, HallSubmission.hall_id == hall.id))
    audit.record(db, "attendance.reopened", f"{user.full_name} reopened attendance for {hall.code}, {plan.session.label}",
                 actor=user, plan_id=plan.id, details={"hall": hall.code})
    db.commit()
    return counts(db, plan, hall)


def assignments(db: Session, user: User) -> list[dict]:
    plans = db.scalars(select(Plan).where(Plan.status == PLAN_PUBLISHED)).all()
    out = []
    for plan in plans:
        per_hall = {h["hall"]: h["placed"] for h in plan.scorecard.get("per_hall", [])}
        halls = db.scalars(select(Hall).where(Hall.id.in_(plan.hall_ids))).all()
        staff: dict[int, list[str]] = {}
        mine: set[int] = set()
        for a in db.scalars(select(InvigilatorAssignment).where(InvigilatorAssignment.plan_id == plan.id)):
            staff.setdefault(a.hall_id, []).append(a.user.full_name)
            if a.user_id == user.id:
                mine.add(a.hall_id)
        for hall in halls:
            if hall.code not in per_hall or (not user.is_admin and hall.id not in mine):
                continue
            s = plan.session
            out.append({
                "plan_id": plan.id, "plan_version": plan.version,
                "session": {"id": s.id, "label": s.label, "date": s.date.isoformat(),
                            "start_time": s.start_time.strftime("%H:%M"), "end_time": s.end_time.strftime("%H:%M")},
                "hall": {"id": hall.id, "code": hall.code, "name": hall.name, "building": hall.building,
                         "floor": hall.floor},
                "invigilators": staff.get(hall.id, []), "mine": hall.id in mine,
                **counts(db, plan, hall),
            })
    out.sort(key=lambda a: (a["session"]["date"], a["session"]["start_time"], a["hall"]["code"]))
    return out
