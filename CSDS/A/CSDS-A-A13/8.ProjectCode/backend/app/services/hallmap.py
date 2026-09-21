"""Seat map of one hall in a plan, as shown in the product and printed on charts."""
from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError, NotFound
from app.models import AttendanceMark, Hall, HallSubmission, InvigilatorAssignment, Plan, SeatAssignment, User
from app.models.plan import PLAN_ARCHIVED, PLAN_PUBLISHED
from app.services.swap import paper_keys


def can_view_hall(db: Session, plan: Plan, hall: Hall, user: User) -> bool:
    if user.is_admin:
        return True
    if plan.status != PLAN_PUBLISHED:
        return False
    return db.scalar(select(InvigilatorAssignment.id).where(
        InvigilatorAssignment.plan_id == plan.id, InvigilatorAssignment.hall_id == hall.id,
        InvigilatorAssignment.user_id == user.id)) is not None


def hall_map(db: Session, plan_id: int, hall_id: int, user: User) -> dict:
    plan = db.get(Plan, plan_id)
    hall = db.get(Hall, hall_id)
    if plan is None:
        raise NotFound("Plan")
    if hall is None or hall.id not in plan.hall_ids:
        raise NotFound("Hall in this plan")
    if not can_view_hall(db, plan, hall, user):
        raise AppError("You are not assigned to this hall.", 403)

    papers_of = paper_keys(db, plan)
    seats = db.scalars(select(SeatAssignment).where(SeatAssignment.plan_id == plan.id,
                                                    SeatAssignment.hall_id == hall.id)).all()
    marks = {m.candidate_id: m for m in db.scalars(select(AttendanceMark).where(
        AttendanceMark.plan_id == plan.id, AttendanceMark.hall_id == hall.id))}

    by_paper: dict[str, dict] = defaultdict(lambda: {"courses": set(), "count": 0})
    for s in seats:
        key = papers_of.get(s.course_id, s.course.code)
        by_paper[key]["courses"].add(s.course.code)
        by_paper[key]["count"] += 1
    legend = [{"paper": key, "courses": sorted(v["courses"]), "count": v["count"], "colour": i}
              for i, (key, v) in enumerate(sorted(by_paper.items()))]
    colour = {p["paper"]: p["colour"] for p in legend}

    seat_rows = []
    for s in sorted(seats, key=lambda a: (a.row, a.col)):
        paper = papers_of.get(s.course_id, s.course.code)
        mark = marks.get(s.candidate_id)
        seat_rows.append({
            "label": s.seat_label, "row": s.row, "col": s.col,
            "candidate": {"id": s.candidate.id, "roll_no": s.candidate.roll_no, "full_name": s.candidate.full_name,
                          "department": s.candidate.department.code},
            "course_code": s.course.code, "course_name": s.course.name, "paper": paper, "colour": colour[paper],
            "needs_accessible": s.candidate.needs_accessible_seat,
            "attendance": mark.status if mark else None,
        })

    staff = [{"id": a.user.id, "full_name": a.user.full_name} for a in db.scalars(select(InvigilatorAssignment).where(
        InvigilatorAssignment.plan_id == plan.id, InvigilatorAssignment.hall_id == hall.id))]
    submitted = db.scalar(select(HallSubmission).where(HallSubmission.plan_id == plan.id,
                                                       HallSubmission.hall_id == hall.id))
    card = next((h for h in plan.scorecard.get("per_hall", []) if h["hall"] == hall.code), None)
    used_halls = {h["hall"]: h["placed"] for h in plan.scorecard.get("per_hall", [])}
    others = [{"hall_id": h.id, "code": h.code, "name": h.name, "placed": used_halls[h.code]}
              for h in db.scalars(select(Hall).where(Hall.id.in_(plan.hall_ids)).order_by(Hall.code))
              if h.code in used_halls]
    if not user.is_admin:
        others = [o for o in others if can_view_hall(db, plan, db.get(Hall, o["hall_id"]), user)]

    return {
        "plan": {"id": plan.id, "version": plan.version, "status": plan.status, "seed": plan.seed,
                 "adjacency": plan.rules.get("adjacency", 8), "roll_gap": plan.rules.get("roll_gap", 0),
                 "session": {"id": plan.session.id, "label": plan.session.label, "date": plan.session.date.isoformat(),
                             "start_time": plan.session.start_time.strftime("%H:%M"),
                             "end_time": plan.session.end_time.strftime("%H:%M")}},
        "hall": {"id": hall.id, "code": hall.code, "name": hall.name, "building": hall.building, "floor": hall.floor,
                 "rows": hall.rows, "cols": hall.cols, "blocked": hall.blocked_seats or [],
                 "accessible": hall.accessible_seats or [], "aisles": hall.aisles_after_cols or [],
                 "capacity": hall.capacity},
        "legend": legend,
        "seats": seat_rows,
        "violations": [v for v in plan.scorecard.get("violations", []) if v["hall"] == hall.code],
        "stats": card or {},
        "invigilators": staff,
        "attendance": {"present": sum(1 for m in marks.values() if m.status == "present"),
                       "absent": sum(1 for m in marks.values() if m.status == "absent"),
                       "submitted_at": submitted.submitted_at.isoformat() if submitted else None},
        "can_edit": user.is_admin and plan.status != PLAN_ARCHIVED,
        "halls": others,
    }
