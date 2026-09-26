from fastapi import APIRouter
from sqlalchemy import func, or_, select

from app.core.deps import DB, AdminUser, CurrentUser
from app.core.errors import NotFound
from app.models import Candidate, Course, Department, ExamSession, Hall, Plan, Registration, SeatAssignment, SessionPaper
from app.models.plan import PLAN_PUBLISHED
from app.schemas.data import (
    CandidateDetail, CandidateOut, CandidatePage, CandidateSeat, CourseOut, DataSummary, DepartmentOut, HallOut,
    HallUpdate, SessionOut,
)
from app.services import audit
from app.services.engine.graph import paper_ceiling
from app.services.halls import engine_hall
from app.services.sessions import course_candidate_counts, session_out
from app.services.settings_service import get_rules

router = APIRouter(tags=["data"])


@router.get("/data/summary", response_model=DataSummary, summary="Counts of everything imported")
def summary(db: DB, _: CurrentUser) -> DataSummary:
    count = lambda q: db.scalar(q) or 0  # noqa: E731
    halls = db.scalars(select(Hall)).all()
    return DataSummary(
        departments=count(select(func.count()).select_from(Department)),
        courses=count(select(func.count()).select_from(Course)),
        candidates=count(select(func.count()).select_from(Candidate)),
        accessible_candidates=count(select(func.count()).select_from(Candidate).where(Candidate.needs_accessible_seat.is_(True))),
        registrations=count(select(func.count()).select_from(Registration)),
        halls=len(halls),
        active_halls=sum(h.is_active for h in halls),
        seats=sum(h.capacity for h in halls if h.is_active),
        sessions=count(select(func.count()).select_from(ExamSession)),
        papers=count(select(func.count()).select_from(SessionPaper)),
    )


@router.get("/departments", response_model=list[DepartmentOut], summary="Departments")
def departments(db: DB, _: AdminUser) -> list[DepartmentOut]:
    courses = dict(db.execute(select(Course.department_id, func.count()).group_by(Course.department_id)).all())
    cands = dict(db.execute(select(Candidate.department_id, func.count()).group_by(Candidate.department_id)).all())
    return [DepartmentOut(id=d.id, code=d.code, name=d.name, courses=courses.get(d.id, 0), candidates=cands.get(d.id, 0))
            for d in db.scalars(select(Department).order_by(Department.code))]


@router.get("/courses", response_model=list[CourseOut], summary="Courses with candidate counts and their sitting")
def courses(db: DB, _: AdminUser, q: str | None = None) -> list[CourseOut]:
    counts = course_candidate_counts(db)
    papers = {p.course_id: p for p in db.scalars(select(SessionPaper))}
    sessions = {s.id: s for s in db.scalars(select(ExamSession))}
    stmt = select(Course).order_by(Course.code)
    if q:
        stmt = stmt.where(or_(Course.code.ilike(f"%{q}%"), Course.name.ilike(f"%{q}%")))
    out = []
    for c in db.scalars(stmt):
        paper = papers.get(c.id)
        session = sessions.get(paper.session_id) if paper else None
        out.append(CourseOut(id=c.id, code=c.code, name=c.name, department_code=c.department.code,
                             department_name=c.department.name, candidates=counts.get(c.id, 0),
                             session_id=session.id if session else None, session_label=session.label if session else None,
                             paper_group=paper.paper_group if paper else None))
    return out


def _candidate_out(c: Candidate) -> dict:
    return dict(id=c.id, roll_no=c.roll_no, full_name=c.full_name, department_code=c.department.code,
                department_name=c.department.name, email=c.email, date_of_birth=c.date_of_birth,
                needs_accessible_seat=c.needs_accessible_seat,
                courses=sorted(r.course.code for r in c.registrations))


@router.get("/candidates", response_model=CandidatePage, summary="Search candidates")
def candidates(db: DB, _: CurrentUser, q: str | None = None, department: str | None = None,
               accessible: bool | None = None, page: int = 1, page_size: int = 25) -> CandidatePage:
    page, page_size = max(page, 1), min(max(page_size, 1), 200)
    stmt = select(Candidate)
    if q:
        stmt = stmt.where(or_(Candidate.roll_no.ilike(f"%{q}%"), Candidate.full_name.ilike(f"%{q}%")))
    if department:
        stmt = stmt.join(Department, Department.id == Candidate.department_id).where(Department.code == department.upper())
    if accessible is not None:
        stmt = stmt.where(Candidate.needs_accessible_seat.is_(accessible))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(Candidate.roll_no).offset((page - 1) * page_size).limit(page_size)).all()
    return CandidatePage(items=[CandidateOut(**_candidate_out(c)) for c in rows], total=total, page=page,
                         page_size=page_size)


@router.get("/candidates/{candidate_id}", response_model=CandidateDetail, summary="A candidate and their seats")
def candidate(candidate_id: int, db: DB, _: CurrentUser) -> CandidateDetail:
    cand = db.get(Candidate, candidate_id)
    if cand is None:
        raise NotFound("Candidate")
    seats = []
    rows = db.execute(select(SeatAssignment, Plan).join(Plan, Plan.id == SeatAssignment.plan_id)
                      .where(SeatAssignment.candidate_id == cand.id, Plan.status == PLAN_PUBLISHED)).all()
    halls = {h.id: h for h in db.scalars(select(Hall))}
    for seat, plan in rows:
        session = plan.session
        hall = halls[seat.hall_id]
        seats.append(CandidateSeat(plan_id=plan.id, plan_status=plan.status, session_id=session.id,
                                   session_label=session.label, date=session.date,
                                   start_time=session.start_time.strftime("%H:%M"),
                                   end_time=session.end_time.strftime("%H:%M"), course_code=seat.course.code,
                                   course_name=seat.course.name, hall_code=hall.code, hall_name=hall.name,
                                   seat_label=seat.seat_label))
    seats.sort(key=lambda s: (s.date, s.start_time))
    return CandidateDetail(**_candidate_out(cand), seats=seats)


def _hall_out(h: Hall, adjacency: int) -> HallOut:
    return HallOut(id=h.id, code=h.code, name=h.name, building=h.building, floor=h.floor, rows=h.rows, cols=h.cols,
                   capacity=h.capacity, blocked_seats=h.blocked_seats or [], accessible_seats=h.accessible_seats or [],
                   aisles_after_cols=h.aisles_after_cols or [], is_active=h.is_active,
                   paper_ceiling=paper_ceiling(engine_hall(h), adjacency))


@router.get("/halls", response_model=list[HallOut], summary="Halls and their seat layouts")
def halls(db: DB, _: CurrentUser) -> list[HallOut]:
    adjacency = get_rules(db).adjacency
    return [_hall_out(h, adjacency) for h in db.scalars(select(Hall).order_by(Hall.code))]


@router.patch("/halls/{hall_id}", response_model=HallOut, summary="Make a hall available or unavailable for new plans")
def update_hall(hall_id: int, body: HallUpdate, db: DB, admin: AdminUser) -> HallOut:
    hall = db.get(Hall, hall_id)
    if hall is None:
        raise NotFound("Hall")
    if hall.is_active != body.is_active:
        hall.is_active = body.is_active
        audit.record(db, "hall.updated", f"{admin.full_name} marked {hall.code} as "
                     f"{'available' if body.is_active else 'unavailable'}", actor=admin)
        db.commit()
    return _hall_out(hall, get_rules(db).adjacency)


@router.get("/sessions", response_model=list[SessionOut], summary="Timetable sittings with their papers and plans")
def sessions(db: DB, _: CurrentUser) -> list[SessionOut]:
    counts = course_candidate_counts(db)
    items = db.scalars(select(ExamSession).order_by(ExamSession.date, ExamSession.start_time)).all()
    return [session_out(db, s, counts) for s in items]


@router.get("/sessions/{session_id}", response_model=SessionOut, summary="One sitting")
def session_detail(session_id: int, db: DB, _: CurrentUser) -> SessionOut:
    session = db.get(ExamSession, session_id)
    if session is None:
        raise NotFound("Sitting")
    return session_out(db, session)
