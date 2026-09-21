"""Everything an export needs about a plan, gathered once."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AttendanceMark, Hall, InvigilatorAssignment, Plan, SeatAssignment, User
from app.services.swap import paper_keys

# Light-mode categorical palette (same order as the product's seat maps).
PAPER_HEX = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
OTHER_HEX = "#898781"


def paper_hex(index: int) -> str:
    return PAPER_HEX[index] if index < len(PAPER_HEX) else OTHER_HEX


@dataclass
class SeatRow:
    label: str
    row: int
    col: int
    candidate_id: int
    roll_no: str
    full_name: str
    department: str
    course_code: str
    course_name: str
    paper: str
    colour: int
    needs_accessible: bool
    attendance: str | None = None
    marked_at: datetime | None = None
    marked_by: str | None = None


@dataclass
class HallExport:
    hall: Hall
    seats: list[SeatRow]
    legend: list[dict]
    invigilators: list[str]
    papers: Counter = field(default_factory=Counter)


@dataclass
class PlanExport:
    plan: Plan
    halls: list[HallExport]

    @property
    def title(self) -> str:
        s = self.plan.session
        return f"{s.label} · {s.start_time:%H:%M}-{s.end_time:%H:%M}"

    @property
    def stamp(self) -> str:
        return (f"Plan v{self.plan.version} ({self.plan.status}) · seed {self.plan.seed} · "
                f"seating {self.plan.assignment_hash[:12]}")


def load_plan_export(db: Session, plan: Plan, hall_id: int | None = None) -> PlanExport:
    papers_of = paper_keys(db, plan)
    stmt = select(SeatAssignment).where(SeatAssignment.plan_id == plan.id)
    if hall_id is not None:
        stmt = stmt.where(SeatAssignment.hall_id == hall_id)
    seats = db.scalars(stmt).all()
    marks = {m.candidate_id: m for m in db.scalars(select(AttendanceMark).where(AttendanceMark.plan_id == plan.id))}
    names = {u.id: u.full_name for u in db.scalars(select(User))}
    staff: dict[int, list[str]] = {}
    for a in db.scalars(select(InvigilatorAssignment).where(InvigilatorAssignment.plan_id == plan.id)):
        staff.setdefault(a.hall_id, []).append(a.user.full_name)

    by_hall: dict[int, list[SeatAssignment]] = {}
    for s in seats:
        by_hall.setdefault(s.hall_id, []).append(s)
    halls = {h.id: h for h in db.scalars(select(Hall).where(Hall.id.in_(list(by_hall))))}

    out = []
    for hid in sorted(by_hall, key=lambda i: halls[i].code):
        rows = by_hall[hid]
        paper_list = sorted({papers_of.get(s.course_id, s.course.code) for s in rows})
        colour = {p: i for i, p in enumerate(paper_list)}
        seat_rows = []
        counts: Counter = Counter()
        for s in sorted(rows, key=lambda a: (a.row, a.col)):
            paper = papers_of.get(s.course_id, s.course.code)
            counts[paper] += 1
            mark = marks.get(s.candidate_id)
            seat_rows.append(SeatRow(
                label=s.seat_label, row=s.row, col=s.col, candidate_id=s.candidate_id, roll_no=s.candidate.roll_no,
                full_name=s.candidate.full_name, department=s.candidate.department.code, course_code=s.course.code,
                course_name=s.course.name, paper=paper, colour=colour[paper],
                needs_accessible=s.candidate.needs_accessible_seat,
                attendance=mark.status if mark else None, marked_at=mark.marked_at if mark else None,
                marked_by=names.get(mark.marked_by) if mark and mark.marked_by else None))
        courses_by_paper: dict[str, set[str]] = {}
        for r in seat_rows:
            courses_by_paper.setdefault(r.paper, set()).add(f"{r.course_code} {r.course_name}")
        legend = [{"paper": p, "colour": colour[p], "count": counts[p], "courses": sorted(courses_by_paper[p])}
                  for p in paper_list]
        out.append(HallExport(hall=halls[hid], seats=seat_rows, legend=legend, invigilators=staff.get(hid, []),
                              papers=counts))
    return PlanExport(plan=plan, halls=out)
