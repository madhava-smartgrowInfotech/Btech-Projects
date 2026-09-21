from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class ImportIssue(BaseModel):
    kind: str
    row: int | None
    column: str | None
    message: str
    level: str


class ImportKindReport(BaseModel):
    rows_total: int
    rows_valid: int
    new: int
    updated: int
    errors: int
    warnings: int


class ImportReport(BaseModel):
    mode: str
    kinds: dict[str, ImportKindReport]
    errors: int
    warnings: int
    issues: list[ImportIssue]
    issues_truncated: bool = False
    preview: dict[str, list[dict]] = {}


class ImportBatchOut(BaseModel):
    id: int
    kind: str
    filename: str
    status: str
    rows_total: int
    rows_valid: int
    created_at: datetime
    committed_at: datetime | None
    created_by: str | None
    report: ImportReport | None = None


class DataSummary(BaseModel):
    departments: int
    courses: int
    candidates: int
    accessible_candidates: int
    registrations: int
    halls: int
    active_halls: int
    seats: int
    sessions: int
    papers: int


class DepartmentOut(BaseModel):
    id: int
    code: str
    name: str
    courses: int
    candidates: int


class CourseOut(BaseModel):
    id: int
    code: str
    name: str
    department_code: str
    department_name: str
    candidates: int
    session_id: int | None
    session_label: str | None
    paper_group: str | None


class CandidateOut(BaseModel):
    id: int
    roll_no: str
    full_name: str
    department_code: str
    department_name: str
    email: str | None
    date_of_birth: date | None
    needs_accessible_seat: bool
    courses: list[str]


class CandidatePage(BaseModel):
    items: list[CandidateOut]
    total: int
    page: int
    page_size: int


class CandidateSeat(BaseModel):
    plan_id: int
    plan_status: str
    session_id: int
    session_label: str
    date: date
    start_time: str
    end_time: str
    course_code: str
    course_name: str
    hall_code: str
    hall_name: str
    seat_label: str


class CandidateDetail(CandidateOut):
    seats: list[CandidateSeat]


class HallOut(BaseModel):
    id: int
    code: str
    name: str
    building: str
    floor: str
    rows: int
    cols: int
    capacity: int
    blocked_seats: list[str]
    accessible_seats: list[str]
    aisles_after_cols: list[int]
    is_active: bool
    paper_ceiling: int


class HallUpdate(BaseModel):
    is_active: bool


class SessionPaperOut(BaseModel):
    course_id: int
    course_code: str
    course_name: str
    department_code: str
    paper_group: str | None
    candidates: int


class SessionPlanSummary(BaseModel):
    count: int
    latest_id: int | None
    latest_status: str | None
    published_id: int | None


class SessionOut(BaseModel):
    id: int
    code: str
    label: str
    date: date
    start_time: str
    end_time: str
    papers: list[SessionPaperOut]
    candidates: int
    accessible_candidates: int
    plans: SessionPlanSummary
