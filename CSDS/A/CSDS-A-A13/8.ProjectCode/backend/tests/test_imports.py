"""F1 - data import and validation."""
from __future__ import annotations

import pytest

from tests.helpers import SAMPLE, csv_bytes, import_sample, reset, upload


@pytest.fixture(scope="module", autouse=True)
def fresh_workspace(client, admin_headers):
    reset(client, admin_headers)
    yield


def messages(response) -> list[str]:
    return [i["message"] for i in response.json()["report"]["issues"] if i["level"] == "error"]


def test_templates_and_samples_download(client, admin_headers):
    for kind in ("courses", "candidates", "halls", "timetable", "workbook"):
        xlsx = client.get(f"/api/imports/templates/{kind}", headers=admin_headers)
        assert xlsx.status_code == 200 and xlsx.content[:2] == b"PK"
        sample = client.get(f"/api/imports/samples/{kind}", headers=admin_headers)
        assert sample.status_code == 200 and len(sample.content) > 100
    csv = client.get("/api/imports/templates/halls?format=csv", headers=admin_headers)
    assert csv.text.lstrip("﻿").startswith("hall_code,hall_name")


def test_candidates_need_known_courses(client, admin_headers):
    response = upload(client, admin_headers, "candidates", "candidates.csv",
                      (SAMPLE / "candidates.csv").read_bytes())
    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert any("Department ACF is unknown" in m for m in messages(response))


def test_sample_workbook_imports_cleanly(client, admin_headers):
    result = import_sample(client, admin_headers)
    kinds = result["report"]["kinds"]
    assert kinds["candidates"]["new"] == 908
    assert kinds["halls"]["new"] == 14
    summary = client.get("/api/data/summary", headers=admin_headers).json()
    assert summary["candidates"] == 908 and summary["sessions"] == 6 and summary["courses"] == 49
    sessions = client.get("/api/sessions", headers=admin_headers).json()
    assert all(s["candidates"] > 300 for s in sessions)
    db_paper = [p for s in sessions for p in s["papers"] if p["paper_group"] == "DB-COMMON"]
    assert len(db_paper) == 2 and len({p["course_code"] for p in db_paper}) == 2
    halls = client.get("/api/halls", headers=admin_headers).json()
    defaulted = next(h for h in halls if h["code"] == "MB-101")
    assert defaulted["accessible_seats"] == ["A1", "A2"]      # the default of 2 per hall was applied


def test_reimport_updates_instead_of_duplicating(client, admin_headers):
    response = upload(client, admin_headers, "halls", "halls.csv", (SAMPLE / "halls.csv").read_bytes())
    report = response.json()["report"]
    assert report["errors"] == 0 and report["kinds"]["halls"]["updated"] == 14
    committed = client.post(f"/api/imports/{response.json()['id']}/commit", headers=admin_headers)
    assert committed.status_code == 200
    assert client.post(f"/api/imports/{response.json()['id']}/commit", headers=admin_headers).status_code == 409


def test_row_level_errors_are_reported_with_row_numbers(client, admin_headers):
    content = csv_bytes(
        "roll_no,full_name,department_code,course_codes,needs_accessible_seat,email,date_of_birth",
        "ZZ001,Test One,ACF,ACF-201;NOPE-1,no,bad-email,2004-02-30",
        "ZZ001,Test Two,ACF,ACF-201,maybe,,",
        ",No Roll,ACF,ACF-201,no,,",
    )
    response = upload(client, admin_headers, "candidates", "bad.csv", content)
    issues = response.json()["report"]["issues"]
    text = " | ".join(i["message"] for i in issues)
    assert "ZZ001 appears more than once" in text
    assert "Unknown course code(s): NOPE-1" in text
    assert "not a valid email" in text
    assert "not a date" in text
    assert "must be yes or no" in text
    assert "Roll number is empty" in text
    assert any(i["row"] == 4 for i in issues)


def test_hall_layout_errors(client, admin_headers):
    content = csv_bytes(
        "hall_code,hall_name,building,floor,rows,columns,blocked_seats,accessible_seats,aisles_after_columns",
        "T-1,Test,,,4,4,Z9;A1,A1,7",
        "T-2,Test,,,40,4,,,",
    )
    text = " | ".join(messages(upload(client, admin_headers, "halls", "halls.csv", content)))
    assert "outside the 4 x 4 layout" in text
    assert "both blocked and accessible" in text
    assert "Aisle position '7'" in text
    assert "Rows must be between 1 and 26" in text


def test_timetable_clash_and_split_paper_group(client, admin_headers):
    content = csv_bytes(
        "session_date,start_time,end_time,course_code,paper_group",
        "2026-11-02,09:30,12:30,ACF-201,",
        "2026-11-02,09:30,12:30,ACF-202,",          # the same ACF cohort sits both -> clash
        "2026-11-02,14:00,17:00,SWE-202,DB-COMMON",
        "2026-11-03,09:30,12:30,DAN-202,DB-COMMON",  # one paper, two sittings
        "2026-11-03,12:00,11:00,ACF-101,",
    )
    text = " | ".join(messages(upload(client, admin_headers, "timetable", "tt.csv", content)))
    assert "ACF-201 and ACF-202 are both in the sitting" in text
    assert "Paper group DB-COMMON is spread over 2 sittings" in text
    assert "end time must be after" in text


def test_unreadable_files_are_rejected(client, admin_headers):
    response = upload(client, admin_headers, "halls", "notes.txt", b"hello")
    assert response.status_code == 400
    assert ".csv or .xlsx" in response.json()["detail"]
    response = upload(client, admin_headers, "courses", "courses.csv", b"code_only\nX\n")
    assert any("Required column 'course_name' is missing" in m for m in messages(response))


def test_invigilators_cannot_import(client, invigilator_headers):
    response = upload(client, invigilator_headers, "halls", "halls.csv", (SAMPLE / "halls.csv").read_bytes())
    assert response.status_code == 403
