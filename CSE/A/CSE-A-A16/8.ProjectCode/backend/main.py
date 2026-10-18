"""SignSpeak API: a thin FastAPI layer over the existing sign_language_app modules.

No recognition / training logic lives here - every endpoint calls the same functions the desktop
GUI calls (preprocessing, dataset, train, recognizer, tts). Run with:
    python -m uvicorn backend.main:app --port 8316
"""

from __future__ import annotations

import tensorflow  # noqa: F401  - must load before scikit-learn on Windows (DLL init order)

import base64
import json
import re
import threading
import time
import uuid
from collections import OrderedDict
from typing import Optional

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from sign_language_app import config, tts
from sign_language_app.dataset import class_counts, load_labels
from sign_language_app.preprocessing import crop_roi, get_roi_box, segment_hand
from sign_language_app.recognizer import SignRecognizer

from . import content
from .train_job import CONFUSION_PATH, TrainJob

app = FastAPI(title="SignSpeak API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------
_base = SignRecognizer()                      # owns the loaded Keras model
_model_lock = threading.Lock()               # Keras predict/load are not re-entrant
_sessions: "OrderedDict[str, SignRecognizer]" = OrderedDict()   # per-tab smoothing history
_MAX_SESSIONS = 20


def _reload_model() -> bool:
    with _model_lock:
        ok = _base.load()
        for rec in _sessions.values():
            rec.model, rec.labels = _base.model, _base.labels
    return ok


job = TrainJob(on_finished=_reload_model)


@app.on_event("startup")
def _startup() -> None:
    if config.MODEL_PATH.exists():
        threading.Thread(target=_reload_model, daemon=True).start()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _check_class(cls: str) -> str:
    if cls not in config.CLASSES:
        raise HTTPException(404, f"Unknown class '{cls}'. Use one of: {', '.join(config.CLASSES)}")
    return cls


async def _read_frame(upload: UploadFile) -> np.ndarray:
    data = await upload.read()
    if not data:
        raise HTTPException(400, "The frame was empty. Make sure the camera is running.")
    frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(400, "The frame could not be decoded as an image (send JPEG or PNG).")
    if frame.shape[1] != config.FRAME_WIDTH or frame.shape[0] != config.FRAME_HEIGHT:
        frame = cv2.resize(frame, (config.FRAME_WIDTH, config.FRAME_HEIGHT), interpolation=cv2.INTER_AREA)
    return frame


def _roi(frame: np.ndarray) -> np.ndarray:
    h, w = frame.shape[:2]
    return crop_roi(frame, get_roi_box(w, h))


def _png_data_url(img: np.ndarray, size: int = 128) -> str:
    small = cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".png", small)
    return "data:image/png;base64," + base64.b64encode(buf.tobytes()).decode("ascii")


# ---------------------------------------------------------------------------
# Meta
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "product": "SignSpeak",
        "model_loaded": _base.is_loaded,
        "model_file": config.MODEL_PATH.exists(),
        "training_state": job.snapshot()["state"],
    }


@app.get("/api/config")
def get_config():
    x1, y1, x2, y2 = get_roi_box(config.FRAME_WIDTH, config.FRAME_HEIGHT)
    return {
        "classes": config.CLASSES,
        "letter_classes": config.LETTER_CLASSES,
        "control_classes": config.CONTROL_CLASSES,
        "frame": {"width": config.FRAME_WIDTH, "height": config.FRAME_HEIGHT},
        "roi": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
        "img_size": config.IMG_SIZE,
        "segmentation_mode": config.SEGMENTATION_MODE,
        "thresholds": {
            "confidence": config.CONFIDENCE_THRESHOLD,
            "history_len": config.PREDICTION_HISTORY_LEN,
            "stable_frames": config.STABLE_FRAMES_TO_COMMIT,
        },
        "capture_delay_ms": config.CAPTURE_DELAY_MS,
        "training_defaults": {
            "epochs": config.DEFAULT_EPOCHS,
            "batch_size": config.DEFAULT_BATCH_SIZE,
            "learning_rate": config.DEFAULT_LEARNING_RATE,
            "validation_split": config.VALIDATION_SPLIT,
            "test_split": config.TEST_SPLIT,
        },
    }


@app.get("/api/about")
def about():
    return {
        "title": "Sign Language Recognition System (CNN-based)",
        "batch": "CSE-A | Batch 16",
        "abstract": content.ABSTRACT_TEXT,
        "pipeline": content.PIPELINE_STEPS,
        "base_paper": content.BASE_PAPER,
        "adoption_note": content.ADOPTION_NOTE,
    }


# ---------------------------------------------------------------------------
# Dataset / collection
# ---------------------------------------------------------------------------
@app.get("/api/dataset")
def dataset():
    counts = class_counts()
    trainable = [c for c, n in counts.items() if n > 0]
    return {
        "counts": counts,
        "total": sum(counts.values()),
        "trainable_classes": trainable,
        "ready_to_train": len(trainable) >= 2,
    }


@app.get("/api/dataset/{cls}/images")
def dataset_images(cls: str, limit: int = 24):
    _check_class(cls)
    folder = config.DATA_DIR / cls
    files = []
    if folder.exists():
        files = sorted(
            [p for p in folder.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg")],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
    limit = max(1, min(limit, 200))
    return {
        "class": cls,
        "total": len(files),
        "images": [{"name": p.name, "url": f"/api/dataset/{cls}/images/{p.name}"} for p in files[:limit]],
    }


@app.get("/api/dataset/{cls}/images/{name}")
def dataset_image(cls: str, name: str):
    _check_class(cls)
    if not re.fullmatch(r"[\w\-. ]+\.(png|jpe?g)", name, re.I):
        raise HTTPException(400, "Invalid image name.")
    path = config.DATA_DIR / cls / name
    if not path.is_file():
        raise HTTPException(404, "Image not found.")
    return FileResponse(path)


@app.post("/api/preview")
async def preview(frame: UploadFile = File(...)):
    img = await _read_frame(frame)
    return {"mask": _png_data_url(segment_hand(_roi(img)))}


_collect_lock = threading.Lock()


@app.post("/api/collect/{cls}")
async def collect(cls: str, frame: UploadFile = File(...)):
    _check_class(cls)
    img = await _read_frame(frame)
    roi = _roi(img)
    resized = cv2.resize(roi, (config.RAW_SAVE_SIZE, config.RAW_SAVE_SIZE), interpolation=cv2.INTER_AREA)
    folder = config.DATA_DIR / cls
    with _collect_lock:
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{cls}_{int(time.time() * 1000)}.png"
        n = 0
        while path.exists():      # two frames inside the same millisecond
            n += 1
            path = folder / f"{cls}_{int(time.time() * 1000)}_{n}.png"
        cv2.imwrite(str(path), resized)
    return {
        "class": cls,
        "saved": path.name,
        "count": class_counts().get(cls, 0),
        "mask": _png_data_url(segment_hand(roi), 96),
    }


# ---------------------------------------------------------------------------
# Recognition
# ---------------------------------------------------------------------------
@app.post("/api/recognize/session")
def recognize_session():
    sid = uuid.uuid4().hex[:12]
    rec = SignRecognizer()
    rec.model, rec.labels = _base.model, _base.labels
    _sessions[sid] = rec
    while len(_sessions) > _MAX_SESSIONS:
        _sessions.popitem(last=False)
    return {"session_id": sid, "model_loaded": _base.is_loaded}


@app.post("/api/recognize/reload")
def recognize_reload():
    if not config.MODEL_PATH.exists():
        raise HTTPException(404, "No trained model found. Train one first.")
    ok = _reload_model()
    return {"model_loaded": ok, "labels": _base.labels}


@app.post("/api/recognize/frame")
async def recognize_frame(frame: UploadFile = File(...), session_id: str = Form(...)):
    if not _base.is_loaded:
        raise HTTPException(409, "No trained model is loaded. Train one in the Train tab first.")
    rec = _sessions.get(session_id)
    if rec is None:
        raise HTTPException(404, "Unknown session. Restart the camera to start a new one.")
    img = await _read_frame(frame)
    roi = _roi(img)
    with _model_lock:
        result = rec.predict_frame(roi)
    return {
        "label": result["label"],
        "confidence": result["confidence"],
        "stable_label": result["stable_label"],
        "committed": result["committed"],
        "mask": _png_data_url(result["mask"]),
    }


class SpeakBody(BaseModel):
    text: str


@app.post("/api/tts/speak")
def speak(body: SpeakBody):
    text = body.text.strip()
    if not text:
        raise HTTPException(400, "There is no text to speak yet.")
    if len(text) > 2000:
        raise HTTPException(400, "The sentence is too long to speak (2000 characters max).")
    tts.speak_async(text)
    return {"spoken": True, "chars": len(text)}


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------
class TrainBody(BaseModel):
    epochs: int = config.DEFAULT_EPOCHS
    batch_size: int = config.DEFAULT_BATCH_SIZE
    learning_rate: float = config.DEFAULT_LEARNING_RATE


@app.post("/api/train/start")
def train_start(body: TrainBody):
    if not 1 <= body.epochs <= 500:
        raise HTTPException(400, "Epochs must be between 1 and 500.")
    if not 1 <= body.batch_size <= 1024:
        raise HTTPException(400, "Batch size must be between 1 and 1024.")
    if not 1e-6 <= body.learning_rate <= 1:
        raise HTTPException(400, "Learning rate must be between 0.000001 and 1.")
    counts = class_counts()
    if sum(1 for n in counts.values() if n > 0) < 2:
        raise HTTPException(409, "Collect images for at least 2 classes before training.")
    if not job.start(body.epochs, body.batch_size, body.learning_rate):
        raise HTTPException(409, "Training is already running.")
    return job.snapshot()


@app.post("/api/train/stop")
def train_stop():
    job.request_stop()
    return job.snapshot()


@app.get("/api/train/status")
def train_status():
    return job.snapshot()


# ---------------------------------------------------------------------------
# Trained-model report
# ---------------------------------------------------------------------------
_ROW = re.compile(r"^\s*(.+?)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)\s*$")


def _parse_report(text: str) -> tuple[Optional[float], Optional[float], list[dict]]:
    acc = loss = None
    rows: list[dict] = []
    for line in text.splitlines():
        if line.startswith("Test accuracy:"):
            acc = float(line.split(":")[1])
        elif line.startswith("Test loss:"):
            loss = float(line.split(":")[1])
        else:
            m = _ROW.match(line)
            if m:
                rows.append({
                    "label": m.group(1), "precision": float(m.group(2)), "recall": float(m.group(3)),
                    "f1": float(m.group(4)), "support": int(m.group(5)),
                })
    return acc, loss, rows


@app.get("/api/model")
def model_info():
    if not config.REPORT_PATH.exists() and not config.MODEL_PATH.exists():
        return {"trained": False}      # 200, not 404: "no model yet" is a normal state
    report = config.REPORT_PATH.read_text(encoding="utf-8") if config.REPORT_PATH.exists() else ""
    acc, loss, rows = _parse_report(report)
    history = None
    if config.HISTORY_PATH.exists():
        history = json.loads(config.HISTORY_PATH.read_text(encoding="utf-8"))
    confusion = None
    if CONFUSION_PATH.exists():
        confusion = json.loads(CONFUSION_PATH.read_text(encoding="utf-8"))
    return {
        "trained": config.MODEL_PATH.exists(),
        "loaded": _base.is_loaded,
        "labels": load_labels(),
        "test_accuracy": acc,
        "test_loss": loss,
        "report": report,
        "report_rows": rows,
        "history": history,
        "confusion_matrix": confusion,
        "trained_at": config.MODEL_PATH.stat().st_mtime if config.MODEL_PATH.exists() else None,
    }
