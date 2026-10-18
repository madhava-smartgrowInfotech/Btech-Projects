"""
backend/main.py
---------------
Thin FastAPI layer over the existing Flask project. It does NOT rewrite any
logic: the model loader, preprocessing, Grad-CAM and SQLite functions are the
same ones app.py uses. Run from the project root:

    uvicorn backend.main:api --port 8312

Additions on top of the Flask feature set (all additive):
    * demo login (signed cookie session)
    * GET /api/stats          read-only aggregates for the dashboard
    * DELETE /api/predictions/{id}
"""

import base64
import hashlib
import hmac
import json
import os
import threading
import time
import uuid
from collections import Counter
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

import cv2
import numpy as np
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

load_dotenv()

import app as flask_app  # noqa: E402  (existing Flask module: model loader + folders)
from database import db  # noqa: E402
from model.gradcam import make_gradcam_heatmap, overlay_heatmap  # noqa: E402
from model.preprocess import load_and_preprocess_image, preprocess_for_display  # noqa: E402

FRONTEND_PORT = os.getenv("FRONTEND_PORT", "5312")
DEMO_EMAIL = os.getenv("DEMO_EMAIL", "demo@pneumodetect.ai")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "Pneumo@123")
DEMO_NAME = "Dr. Demo Radiologist"
DEMO_ROLE = "Radiologist (demo)"
SESSION_SECRET = os.getenv("SESSION_SECRET", "pneumodetect-dev-session-secret").encode()
SESSION_TTL = 12 * 3600
COOKIE = "pneumo_session"
MAX_BYTES = flask_app.app.config["MAX_CONTENT_LENGTH"]

_predict_lock = threading.Lock()  # one TensorFlow inference at a time


# --------------------------------------------------------------- lifecycle
@asynccontextmanager
async def lifespan(_app):
    db.init_db()
    threading.Thread(target=flask_app.get_model, daemon=True).start()  # warm the model
    yield


api = FastAPI(title="Pneumonia Detection API", version="1.0", lifespan=lifespan)
api.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://localhost:{FRONTEND_PORT}", f"http://127.0.0.1:{FRONTEND_PORT}"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------- auth
def _sign(payload: str) -> str:
    return hmac.new(SESSION_SECRET, payload.encode(), hashlib.sha256).hexdigest()


def make_token(email: str) -> str:
    body = base64.urlsafe_b64encode(json.dumps({"e": email, "x": int(time.time()) + SESSION_TTL}).encode()).decode()
    return f"{body}.{_sign(body)}"


def read_token(token):
    if not token or "." not in token:
        return None
    body, sig = token.rsplit(".", 1)
    if not hmac.compare_digest(sig, _sign(body)):
        return None
    try:
        data = json.loads(base64.urlsafe_b64decode(body.encode()))
    except Exception:
        return None
    return data if data.get("x", 0) > time.time() else None


def current_user(request: Request):
    data = read_token(request.cookies.get(COOKIE))
    if not data:
        raise HTTPException(401, "Please sign in to continue.")
    return {"email": data["e"], "name": DEMO_NAME, "role": DEMO_ROLE}


class Login(BaseModel):
    email: str
    password: str


@api.post("/api/auth/login")
def login(body: Login, response: Response):
    ok = hmac.compare_digest(body.email.strip().lower(), DEMO_EMAIL.lower()) and hmac.compare_digest(
        body.password, DEMO_PASSWORD
    )
    if not ok:
        raise HTTPException(401, "Wrong email or password.")
    response.set_cookie(COOKIE, make_token(DEMO_EMAIL), max_age=SESSION_TTL, httponly=True, samesite="lax")
    return {"email": DEMO_EMAIL, "name": DEMO_NAME, "role": DEMO_ROLE}


@api.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE)
    return {"ok": True}


@api.get("/api/auth/me")
def me(request: Request):
    """Public on purpose: returns the signed-in user, or null (200) so the SPA can probe without a 401."""
    data = read_token(request.cookies.get(COOKIE))
    return {"email": data["e"], "name": DEMO_NAME, "role": DEMO_ROLE} if data else None


# ---------------------------------------------------------------- helpers
def serialize(row) -> dict:
    return {
        "id": row["id"],
        "filename": row["filename"],
        "original_url": "/api/files/" + row["original_path"],
        "heatmap_url": "/api/files/" + row["heatmap_path"],
        "prediction": row["prediction"],
        "confidence": row["confidence"],
        "probabilities": {
            "Normal": row["prob_normal"] or 0.0,
            "Bacterial Pneumonia": row["prob_bacterial"] or 0.0,
            "Viral Pneumonia": row["prob_viral"] or 0.0,
        },
        "created_at": row["created_at"] + "Z",
        "demo_mode": flask_app._demo_mode,
    }


def bad(status: int, msg: str):
    raise HTTPException(status, msg)


# ------------------------------------------------------------------ routes
@api.get("/api/health")
def health():
    ready = flask_app._model is not None
    return {
        "status": "ok",
        "model_ready": ready,
        "demo_mode": flask_app._demo_mode if ready else None,
        "classes": list(flask_app._class_names),
        "max_upload_mb": MAX_BYTES // (1024 * 1024),
        "allowed_types": sorted(flask_app.ALLOWED_EXT),
    }


@api.post("/api/predict", status_code=201)
def predict(xray_image: UploadFile = File(None), user=Depends(current_user)):
    # same validation order as the Flask /predict route
    if xray_image is None:
        bad(400, "No file part in the request.")
    if not xray_image.filename:
        bad(400, "Please choose an X-ray image to upload.")
    if not flask_app.allowed_file(xray_image.filename):
        bad(400, "Unsupported file type. Please upload a JPG or PNG image.")
    data = xray_image.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        bad(413, f"File is too large. The limit is {MAX_BYTES // (1024 * 1024)} MB.")

    model = flask_app.get_model()
    ext = xray_image.filename.rsplit(".", 1)[1].lower()
    unique_id = uuid.uuid4().hex[:12]
    saved_name = f"{unique_id}.{ext}"
    saved_path = os.path.join(flask_app.UPLOAD_FOLDER, saved_name)
    with open(saved_path, "wb") as f:
        f.write(data)

    try:
        preprocessed = load_and_preprocess_image(saved_path)
        display_img = preprocess_for_display(saved_path)
    except ValueError:
        os.remove(saved_path)
        bad(400, "That file could not be read as an image. Try another X-ray.")
    batch = np.expand_dims(preprocessed, axis=0)

    with _predict_lock:
        probs = model.predict(batch, verbose=0)[0]
        pred_idx = int(np.argmax(probs))
        heatmap, _ = make_gradcam_heatmap(batch, model, flask_app._last_conv_layer, pred_index=pred_idx)

    names = flask_app._class_names
    prob_map = {n: float(p) for n, p in zip(names, probs)}
    overlay = overlay_heatmap(display_img, heatmap, alpha=0.4)
    heatmap_name = f"{unique_id}_heatmap.png"
    cv2.imwrite(os.path.join(flask_app.HEATMAP_FOLDER, heatmap_name), cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))

    pred_id = db.insert_prediction(
        filename=xray_image.filename,
        original_path=f"uploads/{saved_name}",
        heatmap_path=f"heatmaps/{heatmap_name}",
        prediction=names[pred_idx],
        confidence=float(probs[pred_idx]),
        prob_normal=prob_map.get("Normal", 0.0),
        prob_bacterial=prob_map.get("Bacterial Pneumonia", 0.0),
        prob_viral=prob_map.get("Viral Pneumonia", 0.0),
    )
    return serialize(db.get_prediction(pred_id))


@api.get("/api/predictions")
def list_predictions(limit: int = 200, user=Depends(current_user)):
    return [serialize(r) for r in db.get_all_predictions(limit=max(1, min(limit, 1000)))]


@api.get("/api/predictions/{pred_id}")
def get_prediction(pred_id: int, user=Depends(current_user)):
    row = db.get_prediction(pred_id)
    if row is None:
        bad(404, "Prediction not found.")
    return serialize(row)


@api.delete("/api/predictions/{pred_id}")
def delete_prediction(pred_id: int, user=Depends(current_user)):
    row = db.get_prediction(pred_id)
    if row is None:
        bad(404, "Prediction not found.")
    for rel in (row["original_path"], row["heatmap_path"]):
        path = os.path.join(flask_app.app.root_path, "static", rel)
        if os.path.isfile(path):
            os.remove(path)
    conn = db.get_connection()
    conn.execute("DELETE FROM predictions WHERE id = ?", (pred_id,))
    conn.commit()
    conn.close()
    return {"deleted": pred_id}


@api.get("/api/stats")
def stats(user=Depends(current_user)):
    rows = db.get_all_predictions(limit=100000)
    counts = Counter(r["prediction"] for r in rows)
    today = datetime.utcnow().date()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    per_day = Counter(r["created_at"][:10] for r in rows)
    total = len(rows)
    return {
        "total": total,
        "by_class": {n: counts.get(n, 0) for n in flask_app._class_names},
        "pneumonia_total": counts.get("Bacterial Pneumonia", 0) + counts.get("Viral Pneumonia", 0),
        "avg_confidence": (sum(r["confidence"] for r in rows) / total) if total else None,
        "daily": [{"date": d.isoformat(), "count": per_day.get(d.isoformat(), 0)} for d in days],
        "last_scan_at": (rows[0]["created_at"] + "Z") if rows else None,
        "demo_mode": flask_app._demo_mode,
    }


@api.get("/api/files/{kind}/{name}")
def files(kind: str, name: str, user=Depends(current_user)):
    folder = {"uploads": flask_app.UPLOAD_FOLDER, "heatmaps": flask_app.HEATMAP_FOLDER}.get(kind)
    if folder is None or name != os.path.basename(name):
        bad(404, "File not found.")
    path = os.path.join(folder, name)
    if not os.path.isfile(path):
        bad(404, "File not found.")
    return FileResponse(path, headers={"Cache-Control": "private, max-age=3600"})
