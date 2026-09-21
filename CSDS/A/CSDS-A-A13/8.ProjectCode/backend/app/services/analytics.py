"""Figures for the dashboard and analytics pages."""
from __future__ import annotations

from collections import Counter, defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AttendanceMark, Candidate, ExamSession, Hall, Plan, SeatAssignment
from app.models.plan import PLAN_ARCHIVED, PLAN_PUBLISHED
from app.services.sessions import course_candidate_counts


def _attendance(db: Session, plan_id: int, total: int) -> dict:
    marks = Counter(dict(db.execute(select(AttendanceMark.status, func.count()).where(AttendanceMark.plan_id == plan_id)
                                    .group_by(AttendanceMark.status)).all()))
    present, absent = marks.get("present", 0), marks.get("absent", 0)
    return {"total": total, "present": present, "absent": absent, "unmarked": max(0, total - present - absent)}


def _plan_brief(plan: Plan) -> dict:
    card, base = plan.scorecard or {}, plan.baseline or {}
    return {"id": plan.id, "version": plan.version, "status": plan.status, "solve_ms": plan.solve_ms,
            "halls_used": card.get("halls_used", 0), "utilisation": card.get("utilisation", 0.0),
            "candidates": card.get("placed", 0), "same_paper_pairs": card.get("same_paper_pairs", 0),
            "same_department_pairs": card.get("same_department_pairs", 0), "hard_ok": card.get("hard_ok", False),
            "conflicts_avoided": max(0, (base.get("same_paper_pairs") or 0) - card.get("same_paper_pairs", 0)),
            "swaps": plan.swaps}


def overview(db: Session) -> dict:
    counts = course_candidate_counts(db)
    sessions = db.scalars(select(ExamSession).order_by(ExamSession.date, ExamSession.start_time)).all()
    plans = db.scalars(select(Plan).order_by(Plan.created_at)).all()
    published = {p.session_id: p for p in plans if p.status == PLAN_PUBLISHED}

    rows = []
    for s in sessions:
        plan = published.get(s.id)
        candidates = sum(counts.get(p.course_id, 0) for p in s.papers)
        rows.append({
            "id": s.id, "label": s.label, "date": s.date.isoformat(), "start_time": s.start_time.strftime("%H:%M"),
            "candidates": candidates, "papers": len(s.papers),
            "published_plan": _plan_brief(plan) if plan else None,
            "plans": sum(1 for p in plans if p.session_id == s.id and p.status != PLAN_ARCHIVED),
            "attendance": _attendance(db, plan.id, plan.scorecard.get("placed", 0)) if plan else None,
        })

    live = [p for p in plans if p.status != PLAN_ARCHIVED]
    solve = [{"plan_id": p.id, "label": f"{p.session.label} v{p.version}", "session_id": p.session_id,
              "version": p.version, "candidates": (p.scorecard or {}).get("placed", 0), "solve_ms": p.solve_ms,
              "created_at": p.created_at.isoformat(), "status": p.status} for p in plans]

    hall_use: dict[str, list[float]] = defaultdict(list)
    for p in published.values():
        for h in p.scorecard.get("per_hall", []):
            hall_use[h["hall"]].append(h["utilisation"])
    halls = {h.code: h for h in db.scalars(select(Hall))}
    hall_usage = sorted(({"hall": code, "name": halls[code].name if code in halls else code, "sittings": len(v),
                          "utilisation": round(sum(v) / len(v), 4)} for code, v in hall_use.items()),
                        key=lambda r: (-r["sittings"], -r["utilisation"]))

    attendance = Counter()
    for r in rows:
        if r["attendance"]:
            attendance.update({k: r["attendance"][k] for k in ("total", "present", "absent", "unmarked")})
    marked = attendance["present"] + attendance["absent"]
    pub = [published[s.id] for s in sessions if s.id in published]
    return {
        "counts": {
            "candidates": db.scalar(select(func.count()).select_from(Candidate)) or 0,
            "halls": len(halls), "sessions": len(sessions), "plans": len(live),
            "published": len(published), "seated": sum(p.scorecard.get("placed", 0) for p in pub),
        },
        "totals": {
            "conflicts_avoided": sum(_plan_brief(p)["conflicts_avoided"] for p in pub),
            "same_paper_pairs": sum(p.scorecard.get("same_paper_pairs", 0) for p in pub),
            "avg_solve_ms": round(sum(p.solve_ms for p in live) / len(live)) if live else None,
            "max_solve_ms": max((p.solve_ms for p in live), default=None),
            "hard_ok_rate": (sum(1 for p in live if p.scorecard.get("hard_ok")) / len(live)) if live else None,
            "manual_moves": sum(p.swaps for p in live),
        },
        "attendance": {**{k: attendance[k] for k in ("total", "present", "absent", "unmarked")},
                       "rate": round(attendance["present"] / marked, 4) if marked else None},
        "sessions": rows,
        "solve_times": solve,
        "hall_usage": hall_usage,
    }


def plan_analytics(db: Session, plan: Plan) -> dict:
    card, base = plan.scorecard or {}, plan.baseline or {}
    per_hall = card.get("per_hall", [])
    departments = sorted({d for h in per_hall for d in h.get("departments", {})})
    attendance_by_hall = defaultdict(Counter)
    for hall_id, status in db.execute(select(AttendanceMark.hall_id, AttendanceMark.status)
                                      .where(AttendanceMark.plan_id == plan.id)).all():
        attendance_by_hall[hall_id][status] += 1
    hall_ids = {h.code: h.id for h in db.scalars(select(Hall).where(Hall.id.in_(plan.hall_ids)))}
    placed = dict(db.execute(select(SeatAssignment.hall_id, func.count()).where(SeatAssignment.plan_id == plan.id)
                             .group_by(SeatAssignment.hall_id)).all())
    pairs = card.get("neighbour_pairs", 0)
    return {
        "plan": _plan_brief(plan),
        "session": {"id": plan.session.id, "label": plan.session.label},
        "halls": [{"hall": h["hall"], "seats": h["seats"], "placed": h["placed"], "utilisation": h["utilisation"],
                   "papers": len(h["papers"]), "departments": h["departments"],
                   "same_department_pairs": h["same_department_pairs"], "neighbour_pairs": h["neighbour_pairs"]}
                  for h in per_hall],
        "department_codes": departments,
        "comparison": [
            {"measure": "Same paper", "seatwise": card.get("same_paper_pairs", 0), "baseline": base.get("same_paper_pairs")},
            {"measure": "Roll gap", "seatwise": card.get("roll_gap_violations", 0), "baseline": base.get("roll_gap_violations")},
            {"measure": "Accessible", "seatwise": card.get("accessible_violations", 0), "baseline": base.get("accessible_violations")},
            {"measure": "Same dept.", "seatwise": card.get("same_department_pairs", 0), "baseline": base.get("same_department_pairs")},
        ],
        "neighbour_pairs": {"total": pairs, "same_paper": card.get("same_paper_pairs", 0),
                            "same_department": card.get("same_department_pairs", 0),
                            "mixed": max(0, pairs - card.get("same_paper_pairs", 0) - card.get("same_department_pairs", 0))},
        "attendance": [{"hall": code, "total": placed.get(hid, 0), "present": attendance_by_hall[hid]["present"],
                        "absent": attendance_by_hall[hid]["absent"]}
                       for code, hid in sorted(hall_ids.items()) if placed.get(hid)],
    }
