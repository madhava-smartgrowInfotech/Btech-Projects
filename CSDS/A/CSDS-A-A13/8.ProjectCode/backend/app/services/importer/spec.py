"""Import file layouts: one definition used by the importer, the templates and the docs."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Column:
    name: str
    required: bool
    description: str
    example: str
    aliases: tuple[str, ...] = ()


KINDS = ("courses", "candidates", "halls", "timetable")

TITLES = {
    "courses": "Courses",
    "candidates": "Candidates",
    "halls": "Halls",
    "timetable": "Timetable",
}

SPECS: dict[str, list[Column]] = {
    "courses": [
        Column("course_code", True, "Unique code of the course (letters, digits and - only).", "ACF-201",
               ("code", "course", "subject_code", "paper_code")),
        Column("course_name", True, "Full name of the course.", "Financial Reporting", ("name", "course_title", "subject")),
        Column("department_code", True, "Short code of the department that runs the course.", "ACF",
               ("department", "dept", "dept_code")),
        Column("department_name", False, "Full name of the department (needed the first time a department appears).",
               "Accounting & Finance", ("dept_name",)),
    ],
    "candidates": [
        Column("roll_no", True, "Unique candidate ID / roll number. Candidates use it to look up their seat.",
               "ACF24017", ("roll_number", "roll", "candidate_id", "id")),
        Column("full_name", True, "Name as printed on seating lists.", "Maya Fernandes", ("name", "candidate_name")),
        Column("department_code", True, "Department code (must exist in the courses file).", "ACF",
               ("department", "dept", "dept_code")),
        Column("course_codes", True, "Courses the candidate sits, separated by semicolons.",
               "ACF-201;ACF-202;ACF-203", ("courses", "subjects", "papers")),
        Column("needs_accessible_seat", False, "yes if the candidate needs an accessible seat, otherwise no or empty.",
               "no", ("accessible", "accessible_seat", "needs_accessible")),
        Column("email", False, "Contact email.", "maya.fernandes@example.com", ("e_mail", "mail")),
        Column("date_of_birth", False, "Date of birth as YYYY-MM-DD.", "2004-05-17", ("dob", "birth_date")),
    ],
    "halls": [
        Column("hall_code", True, "Unique short code of the hall.", "MB-101", ("code", "hall", "room_code", "room")),
        Column("hall_name", True, "Display name.", "Main Building 101", ("name", "room_name")),
        Column("building", False, "Building or block.", "Main Building", ("block",)),
        Column("floor", False, "Floor.", "1", ("level",)),
        Column("rows", True, "Number of seat rows (front to back), 1-26.", "8", ("row_count",)),
        Column("columns", True, "Seats per row (left to right), 1-30.", "8", ("cols", "column_count", "seats_per_row")),
        Column("blocked_seats", False, "Seats that cannot be used, separated by semicolons (row letter + column).",
               "D4;D5", ("blocked", "unusable_seats")),
        Column("accessible_seats", False, "Accessible seats, separated by semicolons. Empty = the default from Settings.",
               "A1;A2", ("accessible",)),
        Column("aisles_after_columns", False, "Column numbers followed by an aisle, separated by semicolons.",
               "4", ("aisles", "aisle_after")),
    ],
    "timetable": [
        Column("session_date", True, "Date of the sitting as YYYY-MM-DD.", "2026-10-12", ("date", "exam_date")),
        Column("start_time", True, "Start time as HH:MM (24-hour).", "09:30", ("start", "from")),
        Column("end_time", True, "End time as HH:MM (24-hour).", "12:30", ("end", "to")),
        Column("course_code", True, "Course examined in this sitting.", "ACF-201", ("course", "paper", "subject_code")),
        Column("paper_group", False, "Courses that share one question paper get the same paper group.", "DB-COMMON",
               ("common_paper", "group")),
    ],
}


def normalise_header(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(text).strip().lower()).strip("_")


def header_map(kind: str) -> dict[str, str]:
    """Every accepted spelling of a header -> the canonical column name."""
    mapping: dict[str, str] = {}
    for column in SPECS[kind]:
        mapping[column.name] = column.name
        for alias in column.aliases:
            mapping[normalise_header(alias)] = column.name
    return mapping
