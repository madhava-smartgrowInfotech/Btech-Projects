"""Validation of uploaded rows against each other and against the data already in SeatWise."""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Candidate, Course, Department, ExamSession, Hall, Plan, Registration, SeatAssignment, SessionPaper
from app.services.engine.graph import parse_seat_label, seat_label
from app.services.importer.parse import Table
from app.services.importer.spec import KINDS

CODE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-_./]{0,29}$")
DEPT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-_]{0,19}$")
ROLL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-_/]{0,29}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_LISTED_ISSUES = 500
YES = {"yes", "y", "true", "1", "x"}
NO = {"no", "n", "false", "0", ""}


@dataclass
class Issue:
    kind: str
    row: int | None
    column: str | None
    message: str
    level: str = "error"


@dataclass
class KindResult:
    kind: str
    rows_total: int = 0
    valid: list[dict] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    new: int = 0
    updated: int = 0

    @property
    def errors(self) -> int:
        return sum(i.level == "error" for i in self.issues)

    @property
    def warnings(self) -> int:
        return sum(i.level == "warning" for i in self.issues)


@dataclass
class Context:
    departments: dict[str, str]
    courses: dict[str, str]                 # course code -> department code
    halls: dict[str, dict]                  # hall code -> layout
    candidates: set[str]
    registrations: dict[str, set[str]]      # roll -> course codes
    course_session: dict[str, tuple[str, str]]   # course -> (date, start)
    course_group: dict[str, str | None]
    halls_in_plans: set[str]
    plan_count: int
    default_accessible: int
    hall_capacity: int = 0


def load_context(db: Session, default_accessible: int) -> Context:
    departments = {d.code: d.name for d in db.scalars(select(Department))}
    courses = {c.code: c.department.code for c in db.scalars(select(Course))}
    halls = {h.code: {"rows": h.rows, "cols": h.cols, "blocked": sorted(h.blocked_seats or []),
                      "accessible": sorted(h.accessible_seats or []), "aisles": sorted(h.aisles_after_cols or []),
                      "active": h.is_active, "capacity": h.capacity}
             for h in db.scalars(select(Hall))}
    candidates = set(db.scalars(select(Candidate.roll_no)))
    registrations: dict[str, set[str]] = defaultdict(set)
    for roll, code in db.execute(select(Candidate.roll_no, Course.code).join(Registration, Registration.candidate_id == Candidate.id)
                                 .join(Course, Course.id == Registration.course_id)):
        registrations[roll].add(code)
    course_session, course_group = {}, {}
    for code, d, start, group in db.execute(
            select(Course.code, ExamSession.date, ExamSession.start_time, SessionPaper.paper_group)
            .join(SessionPaper, SessionPaper.course_id == Course.id)
            .join(ExamSession, ExamSession.id == SessionPaper.session_id)):
        course_session[code] = (d.isoformat(), start.strftime("%H:%M"))
        course_group[code] = group
    halls_in_plans = set(db.scalars(select(Hall.code).join(SeatAssignment, SeatAssignment.hall_id == Hall.id).distinct()))
    plan_count = len(db.scalars(select(Plan.id)).all())
    return Context(departments, courses, halls, candidates, dict(registrations), course_session, course_group,
                   halls_in_plans, plan_count, default_accessible)


# ------------------------------------------------------------------ value parsers

def parse_date(text: str) -> date | None:
    text = text.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y/%m/%d", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def parse_time(text: str) -> time | None:
    text = text.strip().upper().replace(".", ":")
    for fmt in ("%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M%p", "%I %p"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    return None


def split_list(text: str | None) -> list[str]:
    if not text:
        return []
    return [part.strip() for part in re.split(r"[;,|]", text) if part.strip()]


# ------------------------------------------------------------------ per kind

class _Checker:
    def __init__(self, kind: str, table: Table):
        self.result = KindResult(kind=kind, rows_total=len(table.rows))
        self.table = table
        self.row_ok = True
        self.row_number: int | None = None

    def error(self, message: str, column: str | None = None, row: int | None = -1) -> None:
        self._add(message, column, row, "error")

    def warn(self, message: str, column: str | None = None, row: int | None = -1) -> None:
        self._add(message, column, row, "warning")

    def _add(self, message: str, column: str | None, row: int | None, level: str) -> None:
        if level == "error" and row == -1:
            self.row_ok = False
        self.result.issues.append(Issue(self.result.kind, self.row_number if row == -1 else row, column, message, level))

    def rows(self):
        for row, number in zip(self.table.rows, self.table.row_numbers):
            self.row_number, self.row_ok = number, True
            yield row
        self.row_number = None

    def header_checks(self) -> bool:
        for column in self.table.missing_columns:
            self.error(f"Required column '{column}' is missing.", column, row=None)
        for column in self.table.unknown_columns:
            self.warn(f"Column '{column}' is not used by SeatWise and was ignored.", None, row=None)
        if not self.table.rows:
            self.error("The file has no data rows.", row=None)
        return not self.table.missing_columns and bool(self.table.rows)


def _duplicates(checker: _Checker, key: str, label: str) -> set[str]:
    counts = Counter((r.get(key) or "").upper() for r in checker.table.rows if r.get(key))
    dupes = {k for k, n in counts.items() if n > 1}
    for k in sorted(dupes)[:50]:
        checker.error(f"{label} {k} appears more than once in the file.", key, row=None)
    return dupes


def validate_courses(table: Table, ctx: Context, mode: str) -> KindResult:
    c = _Checker("courses", table)
    if not c.header_checks():
        return c.result
    dupes = _duplicates(c, "course_code", "Course")
    names_in_file: dict[str, str] = {}
    for row in table.rows:
        if row.get("department_code") and row.get("department_name"):
            names_in_file.setdefault(row["department_code"].upper(), row["department_name"])
    batch_courses: dict[str, str] = {}
    for row in c.rows():
        code = (row["course_code"] or "").upper()
        dept = (row["department_code"] or "").upper()
        if not code:
            c.error("Course code is empty.", "course_code")
        elif not CODE_RE.match(code):
            c.error(f"Course code '{row['course_code']}' may only contain letters, digits, - _ . and /.", "course_code")
        if not row["course_name"]:
            c.error("Course name is empty.", "course_name")
        elif len(row["course_name"]) > 160:
            c.error("Course name is longer than 160 characters.", "course_name")
        if not dept:
            c.error("Department code is empty.", "department_code")
        elif not DEPT_RE.match(dept):
            c.error(f"Department code '{row['department_code']}' may only contain letters, digits, - and _.",
                    "department_code")
        elif dept not in ctx.departments and dept not in names_in_file:
            c.error(f"Department {dept} is new: fill in its department_name.", "department_name")
        name = row["department_name"]
        if name and dept in names_in_file and names_in_file[dept] != name:
            c.warn(f"Department {dept} has more than one name in this file; '{names_in_file[dept]}' is used.",
                   "department_name")
        if c.row_ok and code not in dupes:
            c.result.valid.append({"code": code, "name": row["course_name"].strip(), "department_code": dept,
                                   "department_name": names_in_file.get(dept) or ctx.departments.get(dept)})
            batch_courses[code] = dept
            if code in ctx.courses:
                c.result.updated += 1
            else:
                c.result.new += 1
    if mode == "replace":
        ctx.courses = {}
    ctx.courses = {**ctx.courses, **batch_courses}
    for row in c.result.valid:
        ctx.departments.setdefault(row["department_code"], row["department_name"] or row["department_code"])
    return c.result


def validate_halls(table: Table, ctx: Context, mode: str) -> KindResult:
    c = _Checker("halls", table)
    if not c.header_checks():
        return c.result
    dupes = _duplicates(c, "hall_code", "Hall")
    batch: dict[str, dict] = {}
    for row in c.rows():
        code = (row["hall_code"] or "").upper()
        if not code:
            c.error("Hall code is empty.", "hall_code")
        elif not CODE_RE.match(code):
            c.error(f"Hall code '{row['hall_code']}' may only contain letters, digits, - _ . and /.", "hall_code")
        if not row["hall_name"]:
            c.error("Hall name is empty.", "hall_name")
        rows_n = cols_n = None
        try:
            rows_n = int(float(row["rows"] or ""))
            if not 1 <= rows_n <= 26:
                c.error("Rows must be between 1 and 26.", "rows")
                rows_n = None
        except ValueError:
            c.error(f"Rows '{row['rows']}' is not a whole number.", "rows")
        try:
            cols_n = int(float(row["columns"] or ""))
            if not 1 <= cols_n <= 30:
                c.error("Columns must be between 1 and 30.", "columns")
                cols_n = None
        except ValueError:
            c.error(f"Columns '{row['columns']}' is not a whole number.", "columns")

        def seats(column: str) -> list[str]:
            out = []
            for label in split_list(row[column]):
                seat = parse_seat_label(label)
                if seat is None:
                    c.error(f"'{label}' is not a seat label (use row letter + column number, e.g. C4).", column)
                elif rows_n and cols_n and not (seat[0] < rows_n and seat[1] < cols_n):
                    c.error(f"Seat {label.upper()} is outside the {rows_n} x {cols_n} layout.", column)
                else:
                    out.append(seat_label(*seat))
            return sorted(set(out))

        blocked = seats("blocked_seats")
        accessible = seats("accessible_seats")
        clash = sorted(set(blocked) & set(accessible))
        if clash:
            c.error(f"Seats {', '.join(clash)} are both blocked and accessible.", "accessible_seats")
        aisles = []
        for part in split_list(row["aisles_after_columns"]):
            if not part.isdigit() or (cols_n and not 1 <= int(part) < cols_n):
                c.error(f"Aisle position '{part}' must be a column number between 1 and {max((cols_n or 2) - 1, 1)}.",
                        "aisles_after_columns")
            else:
                aisles.append(int(part))
        defaulted = False
        if not accessible and rows_n and cols_n and ctx.default_accessible:
            front = [seat_label(0, col) for col in range(cols_n) if seat_label(0, col) not in blocked]
            accessible = front[:ctx.default_accessible]
            defaulted = True
        if rows_n and cols_n and rows_n * cols_n - len(blocked) <= 0:
            c.error("Every seat in this hall is blocked.", "blocked_seats")
        if not c.row_ok or code in dupes:
            continue
        layout = {"rows": rows_n, "cols": cols_n, "blocked": blocked, "accessible": sorted(accessible),
                  "aisles": sorted(set(aisles))}
        existing = ctx.halls.get(code)
        if existing and code in ctx.halls_in_plans and any(existing[k] != layout[k] for k in layout):
            c.error(f"Hall {code} is used by existing seating plans, so its layout cannot change. "
                    "Delete those plans first or give the new layout a new hall code.", "rows")
            continue
        if defaulted:
            c.warn(f"No accessible seats given: {', '.join(accessible)} (front row, nearest the door) were used.",
                   "accessible_seats")
        c.result.valid.append({"code": code, "name": row["hall_name"].strip(), "building": row["building"] or "",
                               "floor": row["floor"] or "", **layout})
        batch[code] = {**layout, "active": True, "capacity": rows_n * cols_n - len(blocked)}
        if existing:
            c.result.updated += 1
        else:
            c.result.new += 1
    if mode == "replace":
        if ctx.plan_count:
            c.error(f"Replacing all halls would break {ctx.plan_count} existing plan(s). Use 'Add and update' instead, "
                    "or delete the plans first.", row=None)
        ctx.halls = {}
    ctx.halls = {**ctx.halls, **batch}
    return c.result


def validate_candidates(table: Table, ctx: Context, mode: str) -> KindResult:
    c = _Checker("candidates", table)
    if not c.header_checks():
        return c.result
    dupes = _duplicates(c, "roll_no", "Roll number")
    batch: dict[str, set[str]] = {}
    for row in c.rows():
        roll = (row["roll_no"] or "").upper()
        dept = (row["department_code"] or "").upper()
        if not roll:
            c.error("Roll number is empty.", "roll_no")
        elif not ROLL_RE.match(roll):
            c.error(f"Roll number '{row['roll_no']}' may only contain letters, digits, - _ and /.", "roll_no")
        if not row["full_name"]:
            c.error("Name is empty.", "full_name")
        elif len(row["full_name"]) > 120:
            c.error("Name is longer than 120 characters.", "full_name")
        if not dept:
            c.error("Department code is empty.", "department_code")
        elif dept not in ctx.departments:
            c.error(f"Department {dept} is unknown. Import it with the courses first.", "department_code")
        courses = [code.upper() for code in split_list(row["course_codes"])]
        if not courses:
            c.error("No course codes given.", "course_codes")
        unknown = [code for code in courses if code not in ctx.courses]
        if unknown:
            c.error(f"Unknown course code(s): {', '.join(unknown)}. Import them with the courses first.", "course_codes")
        if len(set(courses)) < len(courses):
            c.warn("A course is listed twice; it is counted once.", "course_codes")
        flag = (row["needs_accessible_seat"] or "").strip().lower()
        if flag not in YES | NO:
            c.error(f"needs_accessible_seat must be yes or no, not '{row['needs_accessible_seat']}'.",
                    "needs_accessible_seat")
        email = row["email"]
        if email and not EMAIL_RE.match(email):
            c.error(f"'{email}' is not a valid email address.", "email")
        dob = None
        if row["date_of_birth"]:
            dob = parse_date(row["date_of_birth"])
            if dob is None:
                c.error(f"Date of birth '{row['date_of_birth']}' is not a date (use YYYY-MM-DD).", "date_of_birth")
        if not c.row_ok or roll in dupes:
            continue
        c.result.valid.append({"roll_no": roll, "full_name": " ".join(row["full_name"].split()), "department_code": dept,
                               "courses": sorted(set(courses)), "accessible": flag in YES,
                               "email": email.lower() if email else None,
                               "date_of_birth": dob.isoformat() if dob else None})
        batch[roll] = set(courses)
        if roll in ctx.candidates:
            c.result.updated += 1
        else:
            c.result.new += 1
    if mode == "replace":
        if ctx.plan_count:
            c.error(f"Replacing all candidates would break {ctx.plan_count} existing plan(s). "
                    "Use 'Add and update' instead, or delete the plans first.", row=None)
        ctx.registrations = {}
    ctx.registrations = {**ctx.registrations, **batch}
    ctx.candidates |= set(batch)
    return c.result


def validate_timetable(table: Table, ctx: Context, mode: str) -> KindResult:
    c = _Checker("timetable", table)
    if not c.header_checks():
        return c.result
    dupes = _duplicates(c, "course_code", "Course")
    batch_session: dict[str, tuple[str, str]] = {}
    batch_group: dict[str, str | None] = {}
    session_end: dict[tuple[str, str], str] = {}
    for row in c.rows():
        course = (row["course_code"] or "").upper()
        day = parse_date(row["session_date"] or "") if row["session_date"] else None
        start = parse_time(row["start_time"] or "") if row["start_time"] else None
        end = parse_time(row["end_time"] or "") if row["end_time"] else None
        if day is None:
            c.error(f"Date '{row['session_date'] or ''}' is not a date (use YYYY-MM-DD).", "session_date")
        if start is None:
            c.error(f"Start time '{row['start_time'] or ''}' is not a time (use HH:MM).", "start_time")
        if end is None:
            c.error(f"End time '{row['end_time'] or ''}' is not a time (use HH:MM).", "end_time")
        if start and end and end <= start:
            c.error("The end time must be after the start time.", "end_time")
        if not course:
            c.error("Course code is empty.", "course_code")
        elif course not in ctx.courses:
            c.error(f"Course {course} is unknown. Import it with the courses first.", "course_code")
        group = (row["paper_group"] or "").upper() or None
        if group and not CODE_RE.match(group):
            c.error(f"Paper group '{row['paper_group']}' may only contain letters, digits, - _ . and /.", "paper_group")
        if not c.row_ok or course in dupes:
            continue
        key = (day.isoformat(), start.strftime("%H:%M"))
        end_text = end.strftime("%H:%M")
        if key in session_end and session_end[key] != end_text:
            c.error(f"The sitting on {key[0]} at {key[1]} already ends at {session_end[key]} in another row.", "end_time")
            continue
        session_end[key] = end_text
        batch_session[course] = key
        batch_group[course] = group
        c.result.valid.append({"course_code": course, "date": key[0], "start": key[1], "end": end_text,
                               "paper_group": group})
        if course in ctx.course_session:
            c.result.updated += 1
        else:
            c.result.new += 1

    # A paper group is one question paper: all its courses must be in the same sitting.
    by_group: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for course, group in batch_group.items():
        if group:
            by_group[group].add(batch_session[course])
    for group, keys in sorted(by_group.items()):
        if len(keys) > 1:
            c.error(f"Paper group {group} is spread over {len(keys)} sittings; courses sharing a paper must be "
                    "examined in the same sitting.", "paper_group", row=None)

    # Sittings that overlap in time on the same day.
    starts = sorted(session_end)
    for i, (d1, s1) in enumerate(starts):
        for d2, s2 in starts[i + 1:]:
            if d1 == d2 and s2 < session_end[(d1, s1)]:
                c.warn(f"Sittings on {d1} at {s1} and {s2} overlap in time.", "start_time", row=None)

    if mode == "replace":
        if ctx.plan_count:
            c.error(f"Replacing the timetable would break {ctx.plan_count} existing plan(s). "
                    "Use 'Add and update' instead, or delete the plans first.", row=None)
        ctx.course_session, ctx.course_group = {}, {}
    elif ctx.plan_count and any(ctx.course_session.get(k) not in (None, v) for k, v in batch_session.items()):
        c.warn("Some courses move to a different sitting. Regenerate the plans of the sittings involved.", row=None)
    ctx.course_session = {**ctx.course_session, **batch_session}
    ctx.course_group = {**ctx.course_group, **batch_group}
    return c.result


def cross_checks(results: dict[str, KindResult], ctx: Context) -> None:
    """Subject-combination clashes and sitting capacity, once candidates and the timetable are both known."""
    target = results.get("timetable") or results.get("candidates")
    if target is None or not ctx.registrations or not ctx.course_session:
        return
    clashes: dict[tuple[tuple[str, str], tuple[str, ...]], list[str]] = defaultdict(list)
    for roll, courses in ctx.registrations.items():
        per_session: dict[tuple[str, str], list[str]] = defaultdict(list)
        for code in courses:
            if code in ctx.course_session:
                per_session[ctx.course_session[code]].append(code)
        for key, codes in per_session.items():
            if len(codes) > 1:
                clashes[(key, tuple(sorted(codes)))].append(roll)
    for (key, codes), rolls in sorted(clashes.items())[:50]:
        sample = ", ".join(sorted(rolls)[:5]) + (f" and {len(rolls) - 5} more" if len(rolls) > 5 else "")
        target.issues.append(Issue(target.kind, None, "course_codes" if target.kind == "candidates" else "course_code",
                                   f"{' and '.join(codes)} are both in the sitting on {key[0]} at {key[1]}, "
                                   f"but {len(rolls)} candidate(s) take both ({sample}). Move one course to another sitting."))
    capacity = sum(h.get("capacity", 0) for h in ctx.halls.values() if h.get("active", True))
    if capacity:
        load: Counter = Counter()
        for courses in ctx.registrations.values():
            for code in courses:
                if code in ctx.course_session:
                    load[ctx.course_session[code]] += 1
        for key, n in sorted(load.items()):
            if n > capacity:
                target.issues.append(Issue(target.kind, None, None,
                                           f"The sitting on {key[0]} at {key[1]} has {n} candidates but all active "
                                           f"halls together seat {capacity}.", "warning"))


VALIDATORS = {
    "courses": validate_courses,
    "halls": validate_halls,
    "candidates": validate_candidates,
    "timetable": validate_timetable,
}
ORDER = ["courses", "halls", "candidates", "timetable"]


def validate_tables(tables: dict[str, Table], ctx: Context, mode: str) -> dict[str, KindResult]:
    results = {}
    for kind in ORDER:
        if kind in tables:
            results[kind] = VALIDATORS[kind](tables[kind], ctx, mode)
    cross_checks(results, ctx)
    return results


def report(results: dict[str, KindResult]) -> dict:
    issues = [asdict(i) for r in results.values() for i in r.issues]
    errors = sum(r.errors for r in results.values())
    return {
        "kinds": {k: {"rows_total": r.rows_total, "rows_valid": len(r.valid), "new": r.new, "updated": r.updated,
                      "errors": r.errors, "warnings": r.warnings} for k, r in results.items()},
        "errors": errors,
        "warnings": sum(r.warnings for r in results.values()),
        "issues": sorted(issues, key=lambda i: (i["level"] != "error", KINDS.index(i["kind"]), i["row"] or 0))[:MAX_LISTED_ISSUES],
        "issues_truncated": len(issues) > MAX_LISTED_ISSUES,
    }
