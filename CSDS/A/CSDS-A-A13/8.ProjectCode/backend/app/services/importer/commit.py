"""Validate uploads into an import batch, then apply a batch to the database."""
from __future__ import annotations

from datetime import date, time

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.errors import AppError, NotFound
from app.models import (
    Candidate, Course, Department, ExamSession, Hall, ImportBatch, Plan, Registration, SessionPaper, User,
)
from app.models._common import utcnow
from app.services import audit
from app.services.importer.parse import Table, read_upload
from app.services.importer.spec import TITLES
from app.services.importer.validate import load_context, report, validate_tables
from app.services.settings_service import get_rules

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def session_label(day: date, start: time) -> str:
    part = "Morning" if start.hour < 12 else "Afternoon" if start.hour < 17 else "Evening"
    return f"{WEEKDAYS[day.weekday()]} {day.day} {MONTHS[day.month - 1]} {day.year} · {part}"


def _tables_to_payload(tables: dict[str, Table]) -> dict:
    return {kind: {"rows": t.rows, "row_numbers": t.row_numbers, "unknown": t.unknown_columns,
                   "missing": t.missing_columns} for kind, t in tables.items()}


def _payload_to_tables(payload: dict) -> dict[str, Table]:
    return {kind: Table(kind, p["rows"], p["row_numbers"], p["unknown"], p["missing"]) for kind, p in payload.items()}


def _validate(db: Session, tables: dict[str, Table], mode: str):
    ctx = load_context(db, get_rules(db).accessible_per_hall)
    results = validate_tables(tables, ctx, mode)
    return results, report(results)


def create_batch(db: Session, kind: str, filename: str, data: bytes, mode: str, user: User) -> ImportBatch:
    tables = read_upload(kind, filename, data)
    results, rep = _validate(db, tables, mode)
    preview = {k: tables[k].rows[:15] for k in tables}
    batch = ImportBatch(
        kind=kind, filename=filename[:200], status="validated" if rep["errors"] == 0 else "failed",
        rows_total=sum(r.rows_total for r in results.values()),
        rows_valid=sum(len(r.valid) for r in results.values()),
        report={**rep, "mode": mode, "preview": preview},
        payload={"mode": mode, "tables": _tables_to_payload(tables)},
        created_by=user.id,
    )
    db.add(batch)
    db.commit()
    return batch


def commit_batch(db: Session, batch_id: int, user: User) -> ImportBatch:
    batch = db.get(ImportBatch, batch_id)
    if batch is None:
        raise NotFound("Import")
    if batch.status == "committed":
        raise AppError("This import has already been applied.", 409)
    mode = batch.payload["mode"]
    tables = _payload_to_tables(batch.payload["tables"])
    results, rep = _validate(db, tables, mode)   # the data may have changed since the upload was checked
    if rep["errors"]:
        batch.status = "failed"
        batch.report = {**rep, "mode": mode, "preview": batch.report.get("preview", {})}
        db.commit()
        raise AppError("The data changed since this file was checked and it no longer passes validation. "
                       "Upload it again to see the problems.", 409)

    counts = {}
    for kind in ("courses", "halls", "candidates", "timetable"):
        if kind in results:
            counts[kind] = APPLY[kind](db, results[kind].valid, mode)
    batch.status = "committed"
    batch.committed_at = utcnow()
    summary = ", ".join(f"{TITLES[k].lower()}: {v['new']} new, {v['updated']} updated" for k, v in counts.items())
    audit.record(db, "import.committed", f"{user.full_name} imported {batch.filename} ({summary})", actor=user,
                 details={"batch_id": batch.id, "mode": mode, "counts": counts})
    db.commit()
    return batch


# ------------------------------------------------------------------ appliers

def _apply_courses(db: Session, rows: list[dict], mode: str) -> dict:
    if mode == "replace":
        db.execute(delete(SessionPaper))
        db.execute(delete(Registration))
        db.execute(delete(Course))
    departments = {d.code: d for d in db.scalars(select(Department))}
    courses = {c.code: c for c in db.scalars(select(Course))}
    new = updated = 0
    for row in rows:
        dept = departments.get(row["department_code"])
        if dept is None:
            dept = Department(code=row["department_code"], name=row["department_name"] or row["department_code"])
            db.add(dept)
            db.flush()
            departments[dept.code] = dept
        elif row["department_name"] and dept.name != row["department_name"]:
            dept.name = row["department_name"]
        course = courses.get(row["code"])
        if course is None:
            db.add(Course(code=row["code"], name=row["name"], department_id=dept.id))
            new += 1
        else:
            course.name, course.department_id = row["name"], dept.id
            updated += 1
    db.flush()
    if mode == "replace":
        used = set(db.scalars(select(Course.department_id))) | set(db.scalars(select(Candidate.department_id)))
        db.execute(delete(Department).where(Department.id.not_in(used)))
    return {"new": new, "updated": updated}


def _apply_halls(db: Session, rows: list[dict], mode: str) -> dict:
    if mode == "replace":
        db.execute(delete(Hall))
    halls = {h.code: h for h in db.scalars(select(Hall))}
    new = updated = 0
    for row in rows:
        values = dict(name=row["name"], building=row["building"], floor=row["floor"], rows=row["rows"],
                      cols=row["cols"], blocked_seats=row["blocked"], accessible_seats=row["accessible"],
                      aisles_after_cols=row["aisles"], is_active=True)
        hall = halls.get(row["code"])
        if hall is None:
            db.add(Hall(code=row["code"], **values))
            new += 1
        else:
            for key, value in values.items():
                setattr(hall, key, value)
            updated += 1
    db.flush()
    return {"new": new, "updated": updated}


def _apply_candidates(db: Session, rows: list[dict], mode: str) -> dict:
    if mode == "replace":
        db.execute(delete(Registration))
        db.execute(delete(Candidate))
    departments = {d.code: d.id for d in db.scalars(select(Department))}
    courses = {c.code: c.id for c in db.scalars(select(Course))}
    candidates = {c.roll_no: c for c in db.scalars(select(Candidate))}
    new = updated = 0
    for row in rows:
        values = dict(full_name=row["full_name"], department_id=departments[row["department_code"]], email=row["email"],
                      date_of_birth=date.fromisoformat(row["date_of_birth"]) if row["date_of_birth"] else None,
                      needs_accessible_seat=row["accessible"])
        cand = candidates.get(row["roll_no"])
        if cand is None:
            cand = Candidate(roll_no=row["roll_no"], **values)
            db.add(cand)
            new += 1
        else:
            for key, value in values.items():
                setattr(cand, key, value)
            updated += 1
        cand.registrations = [Registration(course_id=courses[code]) for code in row["courses"]]
    db.flush()
    return {"new": new, "updated": updated}


def _apply_timetable(db: Session, rows: list[dict], mode: str) -> dict:
    if mode == "replace":
        db.execute(delete(SessionPaper))
        db.execute(delete(ExamSession).where(ExamSession.id.not_in(select(Plan.session_id))))
    courses = {c.code: c.id for c in db.scalars(select(Course))}
    sessions = {(s.date, s.start_time): s for s in db.scalars(select(ExamSession))}
    papers = {p.course_id: p for p in db.scalars(select(SessionPaper))}
    new = updated = 0
    for row in rows:
        day, start = date.fromisoformat(row["date"]), time.fromisoformat(row["start"])
        end = time.fromisoformat(row["end"])
        session = sessions.get((day, start))
        if session is None:
            session = ExamSession(code=f"S{day:%Y%m%d}-{start:%H%M}", date=day, start_time=start, end_time=end,
                                  label=session_label(day, start))
            db.add(session)
            db.flush()
            sessions[(day, start)] = session
        else:
            session.end_time = end
        course_id = courses[row["course_code"]]
        paper = papers.get(course_id)
        if paper is None:
            paper = SessionPaper(session_id=session.id, course_id=course_id, paper_group=row["paper_group"])
            db.add(paper)
            papers[course_id] = paper
            new += 1
        else:
            paper.session_id, paper.paper_group = session.id, row["paper_group"]
            updated += 1
    db.flush()
    # Remove sittings left without papers (unless a plan still refers to them).
    empty = select(ExamSession.id).where(~ExamSession.id.in_(select(SessionPaper.session_id)),
                                         ~ExamSession.id.in_(select(Plan.session_id)))
    db.execute(delete(ExamSession).where(ExamSession.id.in_(empty)))
    return {"new": new, "updated": updated}


APPLY = {
    "courses": _apply_courses,
    "halls": _apply_halls,
    "candidates": _apply_candidates,
    "timetable": _apply_timetable,
}
