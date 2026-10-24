"""
demo_data.py
------------
Synthetic sample lab reports for demos, screenshots and tests.

Each report is rendered to a real PDF (with a text layer) and pushed through the
unchanged `process_uploaded_report` pipeline, so the data in the app is produced by the
same OCR -> extraction -> classification -> insight code as a genuine upload.
Only the upload date is back-dated afterwards so trends span several months.

All people, values and dates here are invented.
"""

from datetime import datetime

import pymupdf

import database as db
from models import Report
from report_processor import process_uploaded_report

# name, unit, low, high, values across the five sample reports (oldest -> newest)
# low/high of None means a one-sided limit: ("<", 100) / (">", 40)
TESTS = [
    ("Hemoglobin", "g/dL", 12.0, 16.0, [10.8, 11.2, 11.9, 12.6, 13.1]),
    ("WBC Count", "10^3/uL", 4.0, 11.0, [6.8, 7.4, 11.8, 7.1, 6.9]),
    ("Platelet Count", "10^3/uL", 150, 400, [265, 280, 271, 410, 300]),
    ("Glucose", "mg/dL", 70, 99, [104, 112, 98, 95, 92]),
    ("HbA1c", "%", 4.0, 5.6, [6.1, 5.9, 5.8, 5.6, 5.4]),
    ("Total Cholesterol", "mg/dL", 125, 200, [232, 221, 214, 198, 190]),
    ("LDL Cholesterol", "mg/dL", "<", 100, [152, 141, 128, 118, 96]),
    ("HDL Cholesterol", "mg/dL", ">", 40, [36, 38, 41, 43, 45]),
    ("Triglycerides", "mg/dL", "<", 150, [188, 172, 160, 146, 138]),
    ("Creatinine", "mg/dL", 0.6, 1.3, [0.9, 1.0, 0.9, 1.0, 1.0]),
    ("Sodium", "mEq/L", 135, 145, [138, 139, 137, 141, 140]),
    ("Potassium", "mEq/L", 3.5, 5.1, [4.2, 4.4, 5.4, 4.3, 4.1]),
    ("TSH", "mIU/L", 0.4, 4.0, [5.8, 5.1, 4.4, 3.6, 3.2]),
    ("Vitamin D", "ng/mL", 30, 100, [14, 19, 24, 31, 38]),
]

REPORTS = [
    ("Health_Checkup_Apr2026.pdf", datetime(2026, 4, 12, 9, 30)),
    ("Health_Checkup_Jun2026.pdf", datetime(2026, 6, 8, 10, 15)),
    ("Health_Checkup_Aug2026.pdf", datetime(2026, 8, 2, 8, 45)),
    ("Health_Checkup_Sep2026.pdf", datetime(2026, 9, 15, 11, 0)),
    ("Health_Checkup_Oct2026.pdf", datetime(2026, 10, 18, 9, 5)),
]


def _fmt(v):
    return f"{v:g}"


def _range(low, high):
    if low == "<":
        return f"<{_fmt(high)}"
    if low == ">":
        return f">{_fmt(high)}"
    return f"{_fmt(low)} - {_fmt(high)}"


def render_pdf(index: int, when: datetime) -> bytes:
    """Draw one synthetic lab report as a PDF with an embedded text layer."""
    doc = pymupdf.open()
    page = doc.new_page()
    y = 64
    header = [
        ("LabLens Demo Diagnostics - Sample Report", 15),
        ("Patient Name: Demo Patient", 10),
        (f"Date: {when.strftime('%d/%m/%Y')}", 10),
        ("Test Name Result Unit Reference Range", 10),
    ]
    for text, size in header:
        page.insert_text((56, y), text, fontsize=size)
        y += size + 8
    y += 6
    for name, unit, low, high, values in TESTS:
        line = f"{name} {_fmt(values[index])} {unit} {_range(low, high)}"
        page.insert_text((56, y), line, fontsize=10.5)
        y += 19
    page.insert_text((56, y + 12), "Synthetic data for demonstration only.", fontsize=8)
    data = doc.tobytes()
    doc.close()
    return data


def seed_demo_reports(use_llm: bool = False) -> list:
    """Create the five sample reports. Returns [{report_id, file_name, status}]."""
    created = []
    for index, (file_name, when) in enumerate(REPORTS):
        result = process_uploaded_report(file_name, render_pdf(index, when), use_llm_insights=use_llm)
        if result.report_id is not None:
            with db.get_session() as session:
                report = session.query(Report).filter(Report.id == result.report_id).first()
                if report is not None:
                    report.upload_date = when
        created.append({"report_id": result.report_id, "file_name": file_name, "status": result.status})
    return created
