"""
Automated tests for the LabLens pipeline and API.

Run from the project root:  python -m pytest tests -q
Database tests point SQLAlchemy at a temporary SQLite file, so data/medical_lab.db is never touched.
"""

import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pymupdf  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

import ai_insights as ai  # noqa: E402
import database as db  # noqa: E402
import ner_processor as ner  # noqa: E402
import ocr_processor as ocr  # noqa: E402
import result_analyzer as ra  # noqa: E402
from models import Base  # noqa: E402


def make_pdf(lines):
    doc = pymupdf.open()
    page = doc.new_page()
    y = 60
    for line in lines:
        page.insert_text((56, y), line, fontsize=10)
        y += 16
    data = doc.tobytes()
    doc.close()
    return data


SAMPLE_LINES = [
    "Patient Name: Test Patient",
    "Date: 12/04/2026",
    "Test Name Result Unit Reference Range",
    "Hemoglobin 10.8 g/dL 12 - 16",
    "Glucose 92 mg/dL 70 - 99",
    "LDL Cholesterol 152 mg/dL <100",
    "HDL Cholesterol 45 mg/dL >40",
]


@pytest.fixture()
def scratch_db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    old = (db.engine, db.SessionLocal)
    db.engine = engine
    db.SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    yield db
    db.engine, db.SessionLocal = old
    engine.dispose()


# ----------------------------------------------------------------------------- classification
@pytest.mark.parametrize(
    "value,low,high,expected",
    [
        (5, 5, 10, "NORMAL"), (10, 5, 10, "NORMAL"), (4.99, 5, 10, "LOW"), (10.01, 5, 10, "HIGH"),
        (120, None, 100, "HIGH"), (80, None, 100, "NORMAL"), (30, 40, None, "LOW"), (45, 40, None, "NORMAL"),
        (7, None, None, "UNKNOWN"), (None, 5, 10, "UNKNOWN"),
    ],
)
def test_classify_result(value, low, high, expected):
    assert ra.classify_result(value, low, high) == expected


def test_summarize_statuses():
    rows = ra.analyze_results([
        {"test_name": "A", "result_value": 1, "reference_low": 2, "reference_high": 3},
        {"test_name": "B", "result_value": 2.5, "reference_low": 2, "reference_high": 3},
        {"test_name": "C", "result_value": 9, "reference_low": 2, "reference_high": 3},
    ])
    assert ra.summarize_statuses(rows) == {"NORMAL": 1, "LOW": 1, "HIGH": 1, "UNKNOWN": 0}


# ----------------------------------------------------------------------------- field extraction
def test_extract_two_sided_range():
    rows = ner.extract_structured_tests("Hemoglobin 10.8 g/dL 12 - 16")
    assert len(rows) == 1
    r = rows[0]
    assert (r["test_name"], r["result_value"], r["unit"], r["reference_low"], r["reference_high"]) == ("Hemoglobin", 10.8, "g/dL", 12.0, 16.0)
    assert r["confidence_score"] == 0.9


def test_extract_one_sided_ranges():
    rows = ner.extract_structured_tests("LDL Cholesterol 152 mg/dL <100\nHDL Cholesterol 45 mg/dL >40")
    assert rows[0]["reference_low"] is None and rows[0]["reference_high"] == 100.0
    assert rows[1]["reference_low"] == 40.0 and rows[1]["reference_high"] is None


def test_header_lines_are_skipped():
    assert ner.extract_structured_tests("Patient Name: Test Patient\nTest Name\nResult\nReference") == []


def test_duplicate_rows_are_dropped():
    rows = ner.extract_structured_tests("Glucose 92 mg/dL 70 - 99\nGlucose 92 mg/dL 70 - 99")
    assert len(rows) == 1


def test_extract_test_date():
    assert ner.extract_test_date("Date: 12/04/2026") == datetime(2026, 4, 12)
    assert ner.extract_test_date("no date here") is None


def test_patient_name_label():
    assert ner.extract_patient_name("Patient Name: Rahul Sharma\nAge: 34") == "Rahul Sharma"


def test_name_normalisation_fixes_ocr_noise():
    assert ner.normalize_test_name("Haemogl0bin") == "Hemoglobin"
    assert ner.normalize_test_name("WBC Count") == "WBC Count"


def test_unseen_name_is_kept_title_cased():
    assert ner.normalize_test_name("LIPASE") == "Lipase"


# ----------------------------------------------------------------------------- OCR / input handling
def test_pdf_text_layer_extraction():
    text = ocr.extract_text("r.pdf", make_pdf(SAMPLE_LINES))
    assert "Hemoglobin 10.8 g/dL" in text


def test_unsupported_extension_rejected():
    with pytest.raises(ocr.OCRError):
        ocr.extract_text("notes.txt", b"hello")


def test_empty_file_rejected():
    with pytest.raises(ocr.OCRError):
        ocr.validate_file("r.pdf", b"")


def test_oversize_file_rejected():
    with pytest.raises(ocr.OCRError):
        ocr.validate_file("r.pdf", b"0" * (16 * 1024 * 1024))


def test_corrupt_pdf_rejected():
    with pytest.raises(ocr.OCRError):
        ocr.extract_text("r.pdf", b"%PDF-not-really")


# ----------------------------------------------------------------------------- insights
def test_rule_based_insight_has_disclaimer_and_no_diagnosis():
    ins = ai.generate_insight("Hemoglobin", "LOW")
    assert "does not provide medical diagnosis" in ins.disclaimer
    assert "generally" in ins.possible_causes.lower()
    assert "doctor" in ins.recommendations.lower()


def test_unknown_test_gets_generic_text():
    ins = ai.generate_insight("Lipase", "HIGH")
    assert "non-specific" in ins.possible_causes


def test_llm_failure_falls_back(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    ins = ai.generate_insight("Glucose", "HIGH", use_llm=True)
    assert ins.explanation.startswith("Glucose measures")


# ----------------------------------------------------------------------------- pipeline + database
def test_full_pipeline_persists_results(scratch_db):
    from report_processor import process_uploaded_report

    res = process_uploaded_report("r.pdf", make_pdf(SAMPLE_LINES))
    assert res.status == "Completed"
    assert res.stages_completed[:4] == ["Text extraction", "Test-value extraction", "Result classification", "Database storage"]
    rows = db.get_results_for_report(res.report_id)
    assert len(rows) == 4
    status = {r.test_name: r.status for r in rows}
    assert status["Hemoglobin"] == "LOW" and status["Glucose"] == "NORMAL" and status["LDL Cholesterol"] == "HIGH"
    low = [r for r in rows if r.status in ("LOW", "HIGH")]
    assert all(db.get_insight_for_test_result(r.id) is not None for r in low)


def test_pipeline_marks_unreadable_report_failed(scratch_db):
    from report_processor import process_uploaded_report

    res = process_uploaded_report("blank.pdf", make_pdf(["Nothing useful on this page at all, just words."]))
    assert res.status == "Failed"
    assert db.get_report_by_id(res.report_id).processing_status == "Failed"


def test_delete_report_cascades(scratch_db):
    from report_processor import process_uploaded_report

    res = process_uploaded_report("r.pdf", make_pdf(SAMPLE_LINES))
    db.delete_report(res.report_id)
    assert db.get_report_by_id(res.report_id) is None
    assert db.get_results_for_report(res.report_id) == []


def test_dashboard_stats_and_critical_heuristic(scratch_db):
    from report_processor import process_uploaded_report

    process_uploaded_report("r.pdf", make_pdf(SAMPLE_LINES + ["Creatinine 2.4 mg/dL 0.6 - 1.3"]))
    stats = db.get_dashboard_stats()
    assert stats["total_reports"] == 1 and stats["total_tests"] == 5
    # creatinine 2.4 > 1.3 x 1.5 and LDL 152 > 100 x 1.5 are both "critical"; Hemoglobin 10.8 is not < 0.5 x 12
    assert stats["critical"] == 2


# ----------------------------------------------------------------------------- API
@pytest.fixture()
def client(scratch_db):
    from fastapi.testclient import TestClient
    import backend.main as main

    c = TestClient(main.app)
    token = c.post("/api/auth/login", json={"email": main.DEMO_EMAIL, "password": main.DEMO_PASSWORD}).json()["token"]
    c.headers.update({"Authorization": f"Bearer {token}"})
    return c


def test_api_requires_login(scratch_db):
    from fastapi.testclient import TestClient
    import backend.main as main

    c = TestClient(main.app)
    assert c.get("/api/reports").status_code == 401
    assert c.post("/api/auth/login", json={"email": "demo@lablens.com", "password": "wrong"}).status_code == 401
    assert c.get("/api/health").json() == {"status": "ok"}


def test_api_tampered_token_rejected(client):
    client.headers["Authorization"] = client.headers["Authorization"][:-3] + "abc"
    assert client.get("/api/reports").status_code == 401


def test_api_upload_detail_trend_compare_insights(client):
    def upload(lines):
        return client.post("/api/reports", files={"file": ("r.pdf", make_pdf(lines), "application/pdf")}).json()

    a = upload(SAMPLE_LINES)
    b = upload([l.replace("10.8", "13.1") for l in SAMPLE_LINES])
    assert a["status"] == "Completed" and len(a["results"]) == 4
    detail = client.get(f"/api/reports/{a['report_id']}").json()
    assert detail["report"]["abnormal_count"] == 2
    trend = client.get("/api/trends", params={"test": "Hemoglobin"}).json()
    assert [p["value"] for p in trend["points"]] == [10.8, 13.1] and trend["direction"] == "increasing"
    cmp_ = client.get("/api/compare", params={"a": a["report_id"], "b": b["report_id"]}).json()
    assert {r["test"]: r["change"] for r in cmp_["rows"]}["Hemoglobin"] == 2.3
    assert client.get("/api/compare", params={"a": 1, "b": 1}).status_code == 400
    assert len(client.get("/api/insights").json()) == 3  # Hgb low + LDL high from #1, LDL high from #2


def test_api_rejects_bad_upload_and_missing_report(client):
    bad = client.post("/api/reports", files={"file": ("x.txt", b"hello", "text/plain")}).json()
    assert bad["status"] == "Failed" and "Unsupported file format" in bad["error"]
    assert client.get("/api/reports/9999").status_code == 404
    assert client.delete("/api/reports/9999").status_code == 404


def test_api_demo_seed_only_into_empty_library(client):
    first = client.post("/api/demo/seed")
    assert first.status_code == 200 and len(first.json()["created"]) == 5
    assert client.post("/api/demo/seed").status_code == 409
