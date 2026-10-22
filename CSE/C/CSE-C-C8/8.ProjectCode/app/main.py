"""PeerScope FastAPI application: API + polished frontend."""
from __future__ import annotations

import csv
import io
import json
import logging
import tempfile
from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import BASE_DIR, MAX_UPLOAD_BYTES
from app.database import get_db, init_db
from app.services import ml_predict as ml_svc
from app.services import pipeline as pipe
from app.services import seed as seed_svc
from app.services import export_service as exp_svc
from app.services import llm_service, embeddings

log = logging.getLogger("peerscope")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="PeerScope", version="1.0.0",
              description="AI-assisted research-paper evaluation and reviewer recommendation for decision support.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

init_db()
try:
    _db = next(get_db())
    seed_svc.seed_if_empty(_db)
    _db.close()
except Exception as exc:  # startup must never crash on seeding
    log.warning("Reviewer seeding skipped: %s", exc)

STATIC_DIR = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/api/health", response_model=schemas.HealthOut)
def health(db: Session = Depends(get_db)):
    n = db.query(models.Reviewer).count()
    return {"status": "ok", "product": "PeerScope",
            "llm_status": ("loaded" if llm_service.llm_status().get("available") else "lazy-not-loaded"),
            "embedding_status": embeddings.embedding_status().get("model", "tfidf-fallback"),
            "model_loaded": ml_svc.artifacts_exist(), "reviewer_count": n}


@app.get("/api/model/metrics")
def model_metrics():
    return ml_svc.load_metrics()


def _r_to_dict(r: models.Reviewer) -> dict:
    return {c: getattr(r, c) for c in ("id", "display_name", "affiliation", "expertise_description",
                                       "research_topics", "methods", "keywords", "publication_titles",
                                       "current_load", "maximum_load", "is_active", "conflict_terms")}


@app.get("/api/reviewers")
def list_reviewers(db: Session = Depends(get_db)):
    return [_r_to_dict(r) for r in db.query(models.Reviewer).order_by(models.Reviewer.id).all()]


@app.post("/api/reviewers", status_code=201)
def create_reviewer(payload: schemas.ReviewerIn, db: Session = Depends(get_db)):
    r = models.Reviewer(**payload.model_dump())
    db.add(r)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(400, f"Could not save reviewer: {exc}")
    db.refresh(r)
    return _r_to_dict(r)


@app.put("/api/reviewers/{rid}")
def update_reviewer(rid: int, payload: schemas.ReviewerIn, db: Session = Depends(get_db)):
    r = db.query(models.Reviewer).filter(models.Reviewer.id == rid).first()
    if not r:
        raise HTTPException(404, "Reviewer not found")
    for k, v in payload.model_dump().items():
        setattr(r, k, v)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(400, f"Could not update reviewer: {exc}")
    db.refresh(r)
    return _r_to_dict(r)


@app.delete("/api/reviewers/{rid}")
def delete_reviewer(rid: int, db: Session = Depends(get_db)):
    r = db.query(models.Reviewer).filter(models.Reviewer.id == rid).first()
    if not r:
        raise HTTPException(404, "Reviewer not found")
    db.delete(r)
    db.commit()
    return {"deleted": rid}


@app.get("/api/reviewers/export/csv")
def export_reviewers(db: Session = Depends(get_db)):
    rows = list_reviewers(db)
    buf = io.StringIO()
    if rows:
        w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return Response(content=buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=peerscope_reviewers.csv"})


@app.post("/api/reviewers/import")
async def import_reviewers(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        raw = (await file.read()).decode("utf-8", errors="replace")
    except Exception:
        raise HTTPException(400, "Could not read CSV file")
    try:
        reader = csv.DictReader(io.StringIO(raw))
        added = 0
        for row in reader:
            name = (row.get("display_name") or "").strip()
            if not name:
                continue
            db.add(models.Reviewer(
                display_name=name[:200], affiliation=(row.get("affiliation") or "")[:300],
                expertise_description=row.get("expertise_description") or "",
                research_topics=row.get("research_topics") or "", methods=row.get("methods") or "",
                keywords=row.get("keywords") or "", publication_titles=row.get("publication_titles") or "",
                current_load=int(row.get("current_load") or 0), maximum_load=int(row.get("maximum_load") or 5),
                is_active=str(row.get("is_active", "true")).lower() not in ("0", "false", "no"),
                conflict_terms=row.get("conflict_terms") or ""))
            added += 1
        db.commit()
        return {"imported": added}
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(400, f"Malformed reviewer CSV: {exc}")


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...), active_only: str = Form("true"),
                  min_score: str = Form("0"), topic: str = Form(""), method: str = Form(""),
                  db: Session = Depends(get_db)):
    fname = file.filename or "upload.pdf"
    if not fname.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted (.pdf).")
    if file.content_type and "pdf" not in file.content_type.lower() and "octet" not in file.content_type.lower():
        raise HTTPException(400, f"Unexpected file type: {file.content_type}. Please upload a PDF.")
    data = await file.read()
    if not data:
        raise HTTPException(400, "Uploaded file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"File too large ({len(data)/1048576:.1f} MB). Limit is {MAX_UPLOAD_BYTES/1048576:.0f} MB.")
    if not data.startswith(b"%PDF"):
        raise HTTPException(400, "File does not look like a valid PDF (missing PDF header).")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    try:
        tmp.write(data)
        tmp.close()
        reviewers = db.query(models.Reviewer).order_by(models.Reviewer.id).all()
        if not reviewers:
            raise HTTPException(400, "Reviewer directory is empty. Add reviewers first.")
        try:
            result = pipe.run_analysis(tmp.name, fname, reviewers,
                                       {"active_only": active_only.lower() == "true",
                                        "min_score": float(min_score or 0), "topic": topic, "method": method})
        except ValueError as exc:
            raise HTTPException(400, str(exc))
        except Exception as exc:
            log.exception("analysis failed")
            raise HTTPException(500, "Paper analysis failed. Try another PDF.")
        if (result.get("features", {}) or {}).get("word_count", 0) < 50:
            result["warning"] = "Very little extractable text was found in this PDF; results are limited."
        rec = models.Analysis(filename=fname, overall_assessment=result.get("overall_assessment", "")[:120],
                              concern_count=int(result.get("concern_count", 0)),
                              recommendation_count=int(result.get("recommendation_count", 0)),
                              top_reviewer=(result.get("top_reviewer", "") or "")[:200],
                              status="completed", result_json=json.dumps(result, ensure_ascii=False))
        db.add(rec)
        db.commit()
        db.refresh(rec)
        result["analysis_id"] = rec.id
        return result
    finally:
        try:
            Path(tmp.name).unlink(missing_ok=True)
        except Exception:
            pass


@app.get("/api/analyses")
def list_analyses(db: Session = Depends(get_db)):
    out = []
    for a in db.query(models.Analysis).order_by(models.Analysis.id.desc()).all():
        out.append({"id": a.id, "filename": a.filename,
                    "created_at": a.created_at.isoformat() if isinstance(a.created_at, datetime) else str(a.created_at),
                    "overall_assessment": a.overall_assessment, "concern_count": a.concern_count,
                    "recommendation_count": a.recommendation_count, "top_reviewer": a.top_reviewer, "status": a.status})
    return out


@app.get("/api/analyses/{aid}")
def get_analysis(aid: int, db: Session = Depends(get_db)):
    a = db.query(models.Analysis).filter(models.Analysis.id == aid).first()
    if not a:
        raise HTTPException(404, "Analysis not found")
    try:
        return json.loads(a.result_json or "{}")
    except Exception:
        raise HTTPException(500, "Stored analysis is corrupted")


@app.get("/api/analyses/{aid}/export")
def export_analysis(aid: int, format: str = "json", db: Session = Depends(get_db)):
    a = db.query(models.Analysis).filter(models.Analysis.id == aid).first()
    if not a:
        raise HTTPException(404, "Analysis not found")
    result = json.loads(a.result_json or "{}")
    if format == "pdf":
        pdf = exp_svc.analysis_to_pdf(result)
        return Response(content=pdf, media_type="application/pdf",
                        headers={"Content-Disposition": f"attachment; filename=peerscope_analysis_{aid}.pdf"})
    return JSONResponse(content=result,
                        headers={"Content-Disposition": f"attachment; filename=peerscope_analysis_{aid}.json"})


@app.exception_handler(Exception)
async def _unhandled(request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    log.exception("unhandled error")
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})
