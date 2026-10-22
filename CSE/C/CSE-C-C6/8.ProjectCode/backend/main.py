"""Thin FastAPI layer over the existing Fake News Detection library (src/).

Every endpoint calls the same functions the Streamlit app (app.py) calls; no model or
pipeline logic lives here. Run:  python -m uvicorn backend.main:app --port 8406
"""
import io
import os
import sys
import tempfile
import threading
import time
import uuid
from contextlib import asynccontextmanager

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from src.dataset import build_demo_dataset, load_csv  # noqa: E402
from src.pipeline import FakeNewsMSVMPipeline  # noqa: E402
from src.preprocessing import ID2LABEL, LABELS, clean_text  # noqa: E402

MODEL_PATH = os.environ.get("FAKENEWS_MODEL", os.path.join(BASE, "models", "msvm_model.pkl"))
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_BATCH_ROWS = 20000
TEXT_COLUMN_HINTS = ("text", "news", "content", "statement", "article")

# Cue vocabularies, identical to the ones the Streamlit "Detect" tab highlights.
SENSATIONAL = {"shocking", "secret", "unbelievable", "miracle", "hoax", "conspiracy", "exposed",
               "urgent", "breaking", "viral", "click", "banned", "hidden"}
CREDIBILITY = {"official", "confirmed", "verified", "evidence", "report", "data", "expert", "audit"}

PIPELINE_STEPS = [
    {"title": "Clean + features", "text": "Text cleaning, TF-IDF (1-2 grams) and 25 stylometric signals."},
    {"title": "PCA", "text": "Standardise, then PCA keeps 95% of the variance."},
    {"title": "Firefly", "text": "The Firefly algorithm selects PCA components and tunes C and gamma."},
    {"title": "MSVM", "text": "RBF multi-class SVM (one-vs-rest, balanced weights) outputs REAL, PARTIALLY TRUE or FAKE."},
]

@asynccontextmanager
async def lifespan(_: FastAPI):
    get_pipe()  # load (or train) the model once at startup
    yield


app = FastAPI(title="Fake News Detection API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5406", "http://127.0.0.1:5406"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_handler(_: Request, exc: RequestValidationError):
    parts = []
    for err in exc.errors():
        where = ".".join(str(p) for p in err.get("loc", []) if p not in ("body", "query"))
        parts.append(f"{where}: {err.get('msg')}" if where else str(err.get("msg")))
    return JSONResponse(status_code=422, content={"detail": "; ".join(parts) or "Invalid request"})


# ---------------------------------------------------------------- model state
_lock = threading.RLock()
_pipe = None


def _load_model():
    """Load the saved model; train a small demo model when none exists (same as app.py)."""
    if os.path.exists(MODEL_PATH):
        return FakeNewsMSVMPipeline.load(MODEL_PATH)
    pipe = FakeNewsMSVMPipeline(max_tfidf=4000, n_fireflies=8, n_generations=8)
    texts, y = build_demo_dataset(n_per_class=250)
    pipe.fit(texts, y, verbose=False)
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    pipe.save(MODEL_PATH)
    return pipe


def get_pipe():
    global _pipe
    with _lock:
        if _pipe is None:
            _pipe = _load_model()
        return _pipe


# ------------------------------------------------------------------- helpers
def _cues(text: str):
    toks = clean_text(text).split()

    def pick(vocab):
        seen = []
        for w in toks:
            if w in vocab and w not in seen:
                seen.append(w)
        return seen[:10]

    return {"sensational": pick(SENSATIONAL), "credibility": pick(CREDIBILITY)}


async def _read_csv_upload(file: UploadFile) -> pd.DataFrame:
    name = file.filename or "upload.csv"
    if not name.lower().endswith(".csv"):
        raise HTTPException(400, f"'{name}' is not a .csv file. Export your data as CSV and try again.")
    raw = await file.read()
    if not raw.strip():
        raise HTTPException(400, f"'{name}' is empty.")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"'{name}' is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.")
    try:
        df = pd.read_csv(io.BytesIO(raw))
    except Exception as exc:  # malformed CSV
        raise HTTPException(400, f"Could not read '{name}' as CSV: {exc}") from exc
    if df.shape[1] == 0 or len(df) == 0:
        raise HTTPException(400, f"'{name}' has no rows to read.")
    return df


def _guess_column(columns):
    for c in columns:
        if str(c).lower() in TEXT_COLUMN_HINTS:
            return str(c)
    return str(columns[0])


def _public_stats(stats: dict) -> dict:
    return {k: v for k, v in stats.items() if k not in ("y_test", "y_pred")}


# ----------------------------------------------------------------- endpoints
@app.get("/api/health")
def health():
    try:
        shown = os.path.relpath(MODEL_PATH, BASE)
    except ValueError:  # model on another drive
        shown = MODEL_PATH
    return {"status": "ok", "model_loaded": _pipe is not None, "model_path": shown}


@app.get("/api/model")
def model_info():
    pipe = get_pipe()
    return {"labels": LABELS, "stats": _public_stats(pipe.stats_), "pipeline": PIPELINE_STEPS}


@app.get("/api/samples")
def samples():
    """One real document per class from the built-in demo corpus (build_demo_dataset)."""
    texts, y = build_demo_dataset(n_per_class=300)
    out = []
    for cls in range(len(LABELS)):
        idx = [i for i, lab in enumerate(y) if int(lab) == cls][:2]
        out.extend({"label": ID2LABEL[cls], "text": texts[i]} for i in idx)
    return {"samples": out}


class PredictBody(BaseModel):
    title: str = ""
    text: str = ""


@app.post("/api/predict")
def predict(body: PredictBody):
    full = (body.title + " " + body.text).strip()
    if len(full.split()) < 5:
        raise HTTPException(422, "Please enter at least a few words of news text (5 or more).")
    pipe = get_pipe()
    t0 = time.time()
    ids, proba = pipe.predict([full])
    latency_ms = (time.time() - t0) * 1000
    label_id = int(ids[0])
    result = {
        "label": ID2LABEL[label_id],
        "label_id": label_id,
        "latency_ms": round(latency_ms, 1),
        "cues": _cues(full),
        "word_count": len(full.split()),
        "confidence": None,
        "probabilities": None,
    }
    if proba is not None:
        probs = proba[0]
        result["probabilities"] = {ID2LABEL[i]: float(p) for i, p in enumerate(probs)}
        result["confidence"] = float(np.max(probs))
    return result


@app.post("/api/batch/preview")
async def batch_preview(file: UploadFile = File(...)):
    df = await _read_csv_upload(file)
    head = df.head(10).astype(object).where(df.head(10).notna(), "")
    return {
        "filename": file.filename,
        "n_rows": int(len(df)),
        "columns": [str(c) for c in df.columns],
        "guessed_column": _guess_column(list(df.columns)),
        "preview": [{str(k): str(v) for k, v in row.items()} for row in head.to_dict("records")],
    }


@app.post("/api/batch/run")
async def batch_run(file: UploadFile = File(...), column: str = Form(...)):
    df = await _read_csv_upload(file)
    if column not in [str(c) for c in df.columns]:
        raise HTTPException(400, f"Column '{column}' is not in this file. Available: {', '.join(map(str, df.columns))}.")
    if len(df) > MAX_BATCH_ROWS:
        raise HTTPException(413, f"This file has {len(df)} rows; the limit is {MAX_BATCH_ROWS} per batch.")
    pipe = get_pipe()
    col = next(c for c in df.columns if str(c) == column)
    texts = df[col].fillna("").astype(str).tolist()
    t0 = time.time()
    ids, proba = pipe.predict(texts)
    df["predicted"] = [ID2LABEL[int(i)] for i in ids]
    if proba is not None:
        df["confidence"] = proba.max(axis=1).round(3)
    dist = df["predicted"].value_counts()
    rows = [
        {
            "row": i + 1,
            "text": texts[i],
            "predicted": df["predicted"].iat[i],
            "confidence": float(df["confidence"].iat[i]) if "confidence" in df.columns else None,
        }
        for i in range(len(df))
    ]
    return {
        "filename": file.filename,
        "column": column,
        "n_rows": int(len(df)),
        "seconds": round(time.time() - t0, 2),
        "rows": rows,
        "distribution": {label: int(dist.get(label, 0)) for label in LABELS},
        "csv": df.to_csv(index=False),
    }


# ------------------------------------------------------------------ retraining
_jobs: dict = {}


def _retrain_worker(job_id, texts, y, fireflies, generations, max_tfidf):
    job = _jobs[job_id]
    try:
        new_pipe = FakeNewsMSVMPipeline(max_tfidf=max_tfidf, n_fireflies=fireflies, n_generations=generations)
        new_pipe.fit(texts, y, verbose=False)
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        tmp = MODEL_PATH + ".tmp"
        new_pipe.save(tmp)
        os.replace(tmp, MODEL_PATH)
        global _pipe
        with _lock:
            _pipe = new_pipe
        s = new_pipe.stats_
        job["result"] = {
            "accuracy": s["accuracy"], "f1_macro": s["f1_macro"], "n_docs": s["n_docs"],
            "n_selected": s["n_selected"], "n_pca": s["n_pca"], "train_time_s": s["train_time_s"],
        }
        job["status"] = "done"
    except Exception as exc:
        job["error"] = f"Training failed: {exc}"
        job["status"] = "error"
    finally:
        job["finished"] = time.time()


@app.post("/api/retrain", status_code=202)
async def retrain(
    file: UploadFile | None = File(None),
    fireflies: int = Form(10),
    generations: int = Form(12),
    max_tfidf: int = Form(4000),
):
    if not 4 <= fireflies <= 20:
        raise HTTPException(422, "fireflies must be between 4 and 20.")
    if not 3 <= generations <= 30:
        raise HTTPException(422, "generations must be between 3 and 30.")
    if not 1000 <= max_tfidf <= 8000:
        raise HTTPException(422, "max_tfidf must be between 1000 and 8000.")
    if any(j["status"] == "running" for j in _jobs.values()):
        raise HTTPException(409, "A retraining job is already running. Wait for it to finish.")

    source = "built-in demo corpus (300 per class)"
    if file is not None and file.filename:
        await _read_csv_upload(file)  # validates extension, size and readability
        await file.seek(0)
        raw = await file.read()
        fd, tmp = tempfile.mkstemp(suffix=".csv")
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(raw)
            try:
                texts, y = load_csv(tmp)
            except Exception as exc:
                raise HTTPException(400, f"Could not use '{file.filename}' for training: {exc}") from exc
        finally:
            os.unlink(tmp)
        if len(texts) < 30:
            raise HTTPException(400, f"Need at least 30 labelled rows to train; this file has {len(texts)}.")
        source = f"{file.filename} ({len(texts)} rows)"
    else:
        texts, y = build_demo_dataset(n_per_class=300)

    job_id = uuid.uuid4().hex[:12]
    _jobs[job_id] = {"status": "running", "started": time.time(), "source": source,
                     "settings": {"fireflies": fireflies, "generations": generations, "max_tfidf": max_tfidf}}
    threading.Thread(target=_retrain_worker, args=(job_id, texts, y, fireflies, generations, max_tfidf),
                     daemon=True).start()
    return {"job_id": job_id}


@app.get("/api/retrain/{job_id}")
def retrain_status(job_id: str):
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(404, "Unknown retraining job (the server may have restarted).")
    end = job.get("finished") or time.time()
    out = {"status": job["status"], "elapsed_s": round(end - job["started"], 1),
           "source": job["source"], "settings": job["settings"]}
    if "result" in job:
        out["result"] = job["result"]
    if "error" in job:
        out["error"] = job["error"]
    return out


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("BACKEND_PORT", "8406"))
    uvicorn.run(app, host="127.0.0.1", port=port)
