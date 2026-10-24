"""
backend/main.py
---------------
Thin FastAPI layer over the existing LabLens Python modules.

Nothing here re-implements pipeline logic: uploads go through `process_uploaded_report`,
reads go through the helpers in `database.py`. The Streamlit app (`app.py`) keeps working
against the same SQLite file.

Run (from the project root):
    python -m uvicorn backend.main:app --port 8308
"""

import base64
import hashlib
import hmac
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  # the product modules live in the project root

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, UploadFile  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel  # noqa: E402

import database as db  # noqa: E402
from ai_insights import MEDICAL_DISCLAIMER  # noqa: E402
from ner_processor import KNOWN_TEST_NAMES  # noqa: E402
from ocr_processor import SUPPORTED_EXTENSIONS  # noqa: E402
from report_processor import process_uploaded_report  # noqa: E402

BACKEND_PORT = int(os.environ.get("BACKEND_PORT", 8308))
FRONTEND_PORT = int(os.environ.get("FRONTEND_PORT", 5308))
MAX_UPLOAD_MB = 15  # same limit ocr_processor.validate_file enforces

# Demo account. The product had no login; this gate exists so the new UI has a sign-in screen.
DEMO_EMAIL = os.environ.get("DEMO_EMAIL", "demo@lablens.com")
DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "Demo@1234")
SECRET = os.environ.get("JWT_SECRET", "change-me-on-first-run").encode()
TOKEN_TTL = 60 * 60 * 12

db.init_db()
app = FastAPI(title="LabLens API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://localhost:{FRONTEND_PORT}", f"http://127.0.0.1:{FRONTEND_PORT}"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- auth

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def make_token(email: str) -> str:
    body = _b64(json.dumps({"sub": email, "exp": int(time.time()) + TOKEN_TTL}).encode())
    sig = _b64(hmac.new(SECRET, body.encode(), hashlib.sha256).digest())
    return f"{body}.{sig}"


def read_token(token: str):
    try:
        body, sig = token.split(".")
        good = _b64(hmac.new(SECRET, body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, good):
            return None
        payload = json.loads(_unb64(body))
        return payload if payload.get("exp", 0) > time.time() else None
    except Exception:
        return None


def require_user(authorization: str = Header(default="")):
    token = authorization[7:] if authorization.lower().startswith("bearer ") else ""
    payload = read_token(token) if token else None
    if not payload:
        raise HTTPException(401, "Please sign in to continue.")
    return payload["sub"]


class LoginBody(BaseModel):
    email: str
    password: str


@app.post("/api/auth/login")
def login(body: LoginBody):
    ok_email = hmac.compare_digest(body.email.strip().lower(), DEMO_EMAIL.lower())
    ok_pass = hmac.compare_digest(body.password, DEMO_PASSWORD)
    if not (ok_email and ok_pass):
        raise HTTPException(401, "Email or password is incorrect.")
    return {"token": make_token(DEMO_EMAIL), "user": {"email": DEMO_EMAIL, "name": "Demo User"}}


@app.get("/api/auth/me")
def me(user: str = Depends(require_user)):
    return {"email": user, "name": "Demo User"}


# --------------------------------------------------------------------------- serializers

def iso(dt):
    """Report timestamps are stored as naive UTC; mark them so the browser converts correctly."""
    return dt.isoformat() + "Z" if dt else None


def ref_display(low, high):
    if low is not None and high is not None:
        return f"{low} - {high}"
    if high is not None:
        return f"< {high}"
    if low is not None:
        return f"> {low}"
    return "N/A"


def insight_dict(insight):
    if insight is None:
        return None
    return {
        "explanation": insight.explanation,
        "possible_causes": insight.possible_causes,
        "recommendations": insight.recommendations,
    }


def result_dict(r, with_insight=False):
    d = {
        "id": r.id,
        "report_id": r.report_id,
        "test_name": r.test_name,
        "result_value": r.result_value,
        "unit": r.unit,
        "reference_low": r.reference_low,
        "reference_high": r.reference_high,
        "reference_range": ref_display(r.reference_low, r.reference_high),
        "status": r.status,
        "test_date": r.test_date.date().isoformat() if r.test_date else None,
        "confidence_score": r.confidence_score,
    }
    if with_insight:
        d["insight"] = insight_dict(db.get_insight_for_test_result(r.id)) if r.status in ("LOW", "HIGH") else None
    return d


def report_dict(r, counts=None):
    d = {
        "id": r.id,
        "file_name": r.file_name,
        "file_type": (r.file_type or "").lower(),
        "upload_date": iso(r.upload_date),
        "processing_status": r.processing_status,
        "error_message": r.error_message,
    }
    if counts is not None:
        total, abnormal = counts.get(r.id, (0, 0))
        d["test_count"] = total
        d["abnormal_count"] = abnormal
    return d


def counts_by_report():
    counts = {}
    for t in db.get_all_test_results():
        total, abnormal = counts.get(t.report_id, (0, 0))
        counts[t.report_id] = (total + 1, abnormal + (1 if t.status in ("LOW", "HIGH") else 0))
    return counts


# --------------------------------------------------------------------------- routes

@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/config")
def config():
    return {
        "disclaimer": MEDICAL_DISCLAIMER,
        "supported_extensions": sorted(SUPPORTED_EXTENSIONS),
        "known_tests": KNOWN_TEST_NAMES,
        "max_size_mb": MAX_UPLOAD_MB,
        # ai_insights._call_llm_for_insight reads exactly this variable
        "llm_available": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "demo_email": DEMO_EMAIL,
        "demo_password": DEMO_PASSWORD,
    }


@app.get("/api/dashboard")
def dashboard(_: str = Depends(require_user)):
    reports = db.get_all_reports()[:10]
    counts = counts_by_report()
    return {"stats": db.get_dashboard_stats(), "recent": [report_dict(r, counts) for r in reports]}


@app.get("/api/reports")
def list_reports(_: str = Depends(require_user)):
    counts = counts_by_report()
    return [report_dict(r, counts) for r in db.get_all_reports()]


@app.post("/api/reports")
def upload_report(file: UploadFile = File(...), use_llm: bool = Form(False), _: str = Depends(require_user)):
    data = file.file.read()
    result = process_uploaded_report(file.filename or "upload", data, use_llm_insights=use_llm)
    out = {
        "status": result.status,
        "report_id": result.report_id,
        "stages_completed": result.stages_completed,
        "error": result.error,
        "raw_text": result.raw_text[:5000],
        "results": [],
    }
    if result.status == "Completed" and result.report_id is not None:
        out["results"] = [result_dict(r, with_insight=True) for r in db.get_results_for_report(result.report_id)]
    return out


@app.get("/api/reports/{report_id}")
def report_detail(report_id: int, _: str = Depends(require_user)):
    report = db.get_report_by_id(report_id)
    if report is None:
        raise HTTPException(404, f"Report #{report_id} was not found. It may have been deleted.")
    results = db.get_results_for_report(report_id)
    counts = {report_id: (len(results), sum(1 for r in results if r.status in ("LOW", "HIGH")))}
    return {
        "report": report_dict(report, counts),
        "raw_text": (report.raw_text or "")[:5000],
        "results": [result_dict(r, with_insight=True) for r in results],
    }


@app.delete("/api/reports/{report_id}")
def delete_report(report_id: int, _: str = Depends(require_user)):
    if db.get_report_by_id(report_id) is None:
        raise HTTPException(404, f"Report #{report_id} was not found.")
    db.delete_report(report_id)
    return {"deleted": report_id}


@app.get("/api/tests")
def test_names(_: str = Depends(require_user)):
    return db.get_distinct_test_names()


@app.get("/api/trends")
def trends(test: str = Query(...), _: str = Depends(require_user)):
    rows = db.get_results_by_test_name(test)
    points = [
        {
            "report_id": report.id,
            "file_name": report.file_name,
            "date": iso(report.upload_date),
            "value": tr.result_value,
            "reference_low": tr.reference_low,
            "reference_high": tr.reference_high,
            "unit": tr.unit,
            "status": tr.status,
        }
        for tr, report in rows
    ]
    direction = None
    values = [p["value"] for p in points if p["value"] is not None]
    if len(values) >= 2:
        direction = "increasing" if values[-1] > values[0] else "decreasing" if values[-1] < values[0] else "stable"
    return {"test": test, "points": points, "direction": direction}


@app.get("/api/compare")
def compare(a: int, b: int, _: str = Depends(require_user)):
    if a == b:
        raise HTTPException(400, "Please select two different reports.")
    ra, rb = db.get_report_by_id(a), db.get_report_by_id(b)
    if ra is None or rb is None:
        raise HTTPException(404, "One of the selected reports was not found.")
    res_a = {t.test_name: t for t in db.get_results_for_report(a)}
    res_b = {t.test_name: t for t in db.get_results_for_report(b)}
    rows = []
    for name in sorted(set(res_a) & set(res_b)):
        va, vb = res_a[name].result_value, res_b[name].result_value
        rows.append({
            "test": name,
            "a": va,
            "b": vb,
            "unit": res_a[name].unit,
            "status_a": res_a[name].status,
            "status_b": res_b[name].status,
            "change": round(vb - va, 2) if va is not None and vb is not None else None,
        })
    return {"report_a": report_dict(ra), "report_b": report_dict(rb), "rows": rows}


@app.get("/api/insights")
def insights(_: str = Depends(require_user)):
    names = {r.id: r for r in db.get_all_reports()}
    out = []
    for r in db.get_all_test_results():
        if r.status not in ("LOW", "HIGH"):
            continue
        d = result_dict(r, with_insight=True)
        report = names.get(r.report_id)
        d["file_name"] = report.file_name if report else None
        d["upload_date"] = iso(report.upload_date) if report else None
        out.append(d)
    out.sort(key=lambda d: d["upload_date"] or "", reverse=True)
    return out


@app.post("/api/demo/seed")
def seed_demo(_: str = Depends(require_user)):
    """Load five synthetic sample reports through the real pipeline (only into an empty database)."""
    if db.get_all_reports():
        raise HTTPException(409, "Sample reports are only loaded into an empty library.")
    from backend.demo_data import seed_demo_reports

    return {"created": seed_demo_reports()}


# --------------------------------------------------------------------------- built frontend (optional)

DIST = ROOT / "frontend" / "dist"
if DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(404, "Not found")
        candidate = DIST / path
        if path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(DIST / "index.html")
