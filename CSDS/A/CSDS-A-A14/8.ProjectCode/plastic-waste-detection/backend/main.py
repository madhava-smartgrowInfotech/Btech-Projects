"""
backend/main.py
---------------
Thin FastAPI layer over the existing plastic-waste-detection functions.

Nothing here re-implements detection logic: it imports and calls
src.model / src.preprocessing / src.detection / src.database exactly as the
Streamlit pages do, and only adds HTTP plumbing (upload, JSON, plot files).

Run from the project root:
    python -m uvicorn backend.main:app --port 8114
"""

import base64
import io
import json
import os
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image, UnidentifiedImageError

from src.database import add_record, clear_history, get_history
from src.detection import detections_to_rows, run_detection
from src.preprocessing import preprocess_image
from src.utils import RESULTS_DIR, ensure_dirs, is_valid_image_file, safe_filename, timestamp_now

FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "5114"))
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8114"))
MAX_UPLOAD_BYTES = 25 * 1024 * 1024

# Same names and order as pages/3_Evaluation.py
PLOT_FILES = {
    "confusion_matrix.png": "Confusion Matrix",
    "confusion_matrix_normalized.png": "Normalized Confusion Matrix",
    "P_curve.png": "Precision Curve",
    "R_curve.png": "Recall Curve",
    "PR_curve.png": "Precision-Recall Curve",
    "F1_curve.png": "F1 Curve",
    "results.png": "Training Results (loss/mAP over epochs)",
}

app = FastAPI(title="PlastiScan API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://localhost:{FRONTEND_PORT}", f"http://127.0.0.1:{FRONTEND_PORT}"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Model state - loaded once in the background so /api/health answers instantly
# ---------------------------------------------------------------------------
_state = {"status": "idle", "model": None, "device": None, "used_fallback": None, "message": None, "error": None}
_load_lock = threading.Lock()
_infer_lock = threading.Lock()  # one inference at a time - YOLO predict is not thread-safe


def _device_guess() -> str:
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:  # noqa: BLE001
        return "cpu"


def _load():
    with _load_lock:
        if _state["status"] == "ready":
            return
        _state.update(status="loading", error=None)
        try:
            from src.model import load_model

            model, device, used_fallback, message = load_model()
            _state.update(status="ready", model=model, device=device, used_fallback=used_fallback, message=message)
        except Exception as exc:  # noqa: BLE001 - surfaced to the UI as a clean message
            _state.update(status="error", error=str(exc))


def _model_info() -> dict:
    return {
        "status": _state["status"],
        "ready": _state["status"] == "ready",
        "used_fallback": _state["used_fallback"],
        "message": _state["message"],
        "error": _state["error"],
    }


@app.on_event("startup")
def _warm_up() -> None:
    ensure_dirs(RESULTS_DIR)
    threading.Thread(target=_load, daemon=True).start()


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "device": _state["device"] or _device_guess(),
        "model": _model_info(),
    }


@app.post("/api/model/reload")
def reload_model():
    """Retry loading the model after a failure (e.g. the weights download was interrupted)."""
    if _state["status"] != "loading":
        _state["status"] = "idle"
        threading.Thread(target=_load, daemon=True).start()
    return _model_info()


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------
@app.post("/api/detect")
async def detect(
    file: UploadFile = File(...),
    conf: float = Form(0.5),
    preprocess: bool = Form(True),
):
    name = safe_filename(file.filename or "")
    if not is_valid_image_file(name):
        raise HTTPException(400, "Invalid file format. Please upload a .jpg, .jpeg or .png image.")
    if not 0.1 <= conf <= 0.9:
        raise HTTPException(422, "Confidence threshold must be between 0.1 and 0.9.")

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "Image is larger than 25 MB. Please upload a smaller file.")
    try:
        pil_image = Image.open(io.BytesIO(data)).convert("RGB")
        image_bgr = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(422, "Could not read this image - it may be corrupted. Please try another file.")

    if _state["status"] != "ready":
        _load()
    if _state["status"] != "ready":
        raise HTTPException(503, f"Model failed to load: {_state['error']}")

    with _infer_lock:
        processed = preprocess_image(image_bgr) if preprocess else image_bgr
        annotated_bgr, detections = run_detection(_state["model"], processed, conf_threshold=conf)

    count = len(detections)
    avg_conf = (sum(d.confidence for d in detections) / count) if count else 0.0
    stamp = timestamp_now()

    ok, buf = cv2.imencode(".jpg", annotated_bgr)
    if not ok:
        raise HTTPException(500, "Could not encode the annotated image.")

    saved_as = None
    logged = False
    if count:  # identical to pages/1_Detection.py: only runs with detections are saved and logged
        saved_as = f"detected_{Path(name).stem}.jpg"
        cv2.imwrite(str(RESULTS_DIR / saved_as), annotated_bgr)
        add_record(name, count, avg_conf, stamp)
        logged = True

    h, w = annotated_bgr.shape[:2]
    return {
        "filename": name,
        "timestamp": stamp,
        "conf_threshold": conf,
        "preprocessed": preprocess,
        "detection_count": count,
        "average_confidence_percent": round(avg_conf * 100, 2),
        "detections": [
            {
                "index": i,
                "class_name": d.class_name,
                "confidence": d.confidence,
                "confidence_percent": round(d.confidence * 100, 1),
                "bbox": [d.x1, d.y1, d.x2, d.y2],
            }
            for i, d in enumerate(detections, start=1)
        ],
        "rows": detections_to_rows(detections),
        "annotated_image": "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode("ascii"),
        "image_size": {"width": w, "height": h},
        "logged": logged,
        "saved_as": saved_as,
        "device": _state["device"],
        "model": _model_info(),
    }


# ---------------------------------------------------------------------------
# History / dashboard
# ---------------------------------------------------------------------------
@app.get("/api/history")
def history():
    return get_history()


@app.delete("/api/history")
def delete_history():
    clear_history()
    return {"cleared": True}


# ---------------------------------------------------------------------------
# Evaluation (read-only view of what evaluate.py wrote to results/)
# ---------------------------------------------------------------------------
@app.get("/api/evaluation")
def evaluation():
    summary_path = RESULTS_DIR / "eval_summary.json"
    if not summary_path.exists():
        return {"available": False, "metrics": None, "plots": []}
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        metrics = {k: float(summary[k]) for k in ("precision", "recall", "map50", "map50_95")}
    except (ValueError, KeyError, TypeError):
        raise HTTPException(500, "results/eval_summary.json is unreadable. Re-run `python evaluate.py`.")
    plots = [
        {"key": fn, "label": label, "url": f"/api/evaluation/plots/{fn}"}
        for fn, label in PLOT_FILES.items()
        if (RESULTS_DIR / fn).exists()
    ]
    return {"available": True, "metrics": metrics, "plots": plots}


@app.get("/api/evaluation/plots/{name}")
def evaluation_plot(name: str):
    if name not in PLOT_FILES or not (RESULTS_DIR / name).exists():
        raise HTTPException(404, "Plot not found.")
    return FileResponse(RESULTS_DIR / name, media_type="image/png")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="127.0.0.1", port=BACKEND_PORT)
