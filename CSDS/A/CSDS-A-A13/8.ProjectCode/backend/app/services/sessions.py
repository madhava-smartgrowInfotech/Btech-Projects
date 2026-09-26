"""Timetable sittings: who sits them and how they are summarised."""
from __future__ import annotations

from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Candidate, Course, ExamSession, Plan, Registration, SessionPaper
from app.models.plan import PLAN_ARCHIVED, PLAN_PUBLISHED
from app.schemas.data import SessionOut, SessionPaperOut, SessionPlanSummary


def session_entries(db: Session, session_id: int) -> list[tuple[Candidate, Course, str | None]]:
    """(candidate, course, paper group) for everyone sitting a paper in this session."""
    rows = db.execute(
        select(Candidate, Course, SessionPaper.paper_group)
        .join(Registration, Registration.candidate_id == Candidate.id)
        .join(Course, Course.id == Registration.course_id)
        .join(SessionPaper, SessionPaper.course_id == Course.id)
        .where(SessionPaper.session_id == session_id)
        .order_by(Candidate.roll_no)
    ).all()
    return [(cand, course, group) for cand, course, group in rows]


def course_candidate_counts(db: Session) -> Counter:
    return Counter(dict(db.execute(select(Registration.course_id, func.count()).group_by(Registration.course_id)).all()))


def session_out(db: Session, session: ExamSession, counts: Counter | None = None) -> SessionOut:
    counts = counts if counts is not None else course_candidate_counts(db)
    papers = sorted(session.papers, key=lambda p: p.course.code)
    accessible = db.scalar(
        select(func.count(func.distinct(Candidate.id)))
        .join(Registration, Registration.candidate_id == Candidate.id)
        .join(SessionPaper, SessionPaper.course_id == Registration.course_id)
        .where(SessionPaper.session_id == session.id, Candidate.needs_accessible_seat.is_(True))) or 0
    plans = db.scalars(select(Plan).where(Plan.session_id == session.id).order_by(Plan.version.desc())).all()
    live = [p for p in plans if p.status != PLAN_ARCHIVED]
    published = next((p for p in plans if p.status == PLAN_PUBLISHED), None)
    return SessionOut(
        id=session.id, code=session.code, label=session.label, date=session.date,
        start_time=session.start_time.strftime("%H:%M"), end_time=session.end_time.strftime("%H:%M"),
        papers=[SessionPaperOut(course_id=p.course_id, course_code=p.course.code, course_name=p.course.name,
                                department_code=p.course.department.code, paper_group=p.paper_group,
                                candidates=counts.get(p.course_id, 0)) for p in papers],
        candidates=sum(counts.get(p.course_id, 0) for p in papers),
        accessible_candidates=accessible,
        plans=SessionPlanSummary(count=len(live), latest_id=live[0].id if live else None,
                                 latest_status=live[0].status if live else None,
                                 published_id=published.id if published else None),
    )
