"""AgriVision API - a thin FastAPI layer over the existing Flask product in ../agrivision.

It imports the original modules (config, disease_db, inference, and app.init_db) and reads/writes the same
SQLite file and tables. The detection, knowledge base and database logic are NOT reimplemented here; this
file only adds a JSON login (bearer token) and exposes what the Flask templates computed server-side.

Run:  python -m uvicorn backend.main:app --port 8416   (from the project root, see run.bat)
"""
from __future__ import annotations

import base64
import csv
import hashlib
import hmac
import io
import json
import os
import re
import sqlite3
import sys
import time
import uuid
from datetime import datetime
from typing import Any, Iterator

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEGACY = os.path.join(ROOT, "agrivision")
if LEGACY not in sys.path:
    sys.path.insert(0, LEGACY)

# Optional overrides for tests: keep the user's real database untouched.
if os.environ.get("AGRIVISION_DB"):
    import config as _cfg  # noqa: E402

    _cfg.DB_PATH = os.environ["AGRIVISION_DB"]
if os.environ.get("AGRIVISION_UPLOADS"):
    import config as _cfg2  # noqa: E402

    _cfg2.UPLOAD_DIR = os.environ["AGRIVISION_UPLOADS"]

import config  # noqa: E402  (agrivision/config.py)
import inference  # noqa: E402  (agrivision/inference.py)
from app import init_db  # noqa: E402  (creates tables + seeds demo@agrivision.ai, exactly like Flask)
from disease_db import CLASSES, display_name, get_disease_info  # noqa: E402
from inference import predict  # noqa: E402

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Request, UploadFile  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import FileResponse, JSONResponse, Response  # noqa: E402
from werkzeug.security import check_password_hash, generate_password_hash  # noqa: E402

os.makedirs(config.UPLOAD_DIR, exist_ok=True)
init_db()

TOKEN_TTL = 60 * 60 * 24 * 7
SECRET = (os.environ.get("AGRIVISION_SECRET") or config.SECRET_KEY).encode()
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CROP_OPTIONS = ["tomato", "potato", "corn", "maize", "grape", "apple", "pepper", "orange", "peach", "strawberry",
                "squash", "cherry", "blueberry", "soybean", "raspberry", "rice", "wheat", "general"]

app = FastAPI(title="AgriVision API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


# ---------------------------------------------------------------- errors
def err(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"error": code, "message": message})


@app.exception_handler(HTTPException)
async def http_error(_req: Request, exc: HTTPException):
    d = exc.detail
    body = d if isinstance(d, dict) else {"error": "ERROR", "message": str(d)}
    # "detail" is what the web client shows; "error"/"message" keep the Flask API's shape
    return JSONResponse(status_code=exc.status_code, content={**body, "detail": body.get("message", "")})


# ---------------------------------------------------------------- db + auth
def get_db() -> Iterator[sqlite3.Connection]:
    con = sqlite3.connect(config.DB_PATH, check_same_thread=False)  # FastAPI runs deps and handlers on different threads
    con.row_factory = sqlite3.Row
    try:
        yield con
    finally:
        con.close()


def make_token(uid: str) -> str:
    payload = base64.urlsafe_b64encode(json.dumps({"uid": uid, "exp": int(time.time()) + TOKEN_TTL}).encode()).decode()
    sig = hmac.new(SECRET, payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def read_token(token: str) -> str | None:
    try:
        payload, sig = token.split(".", 1)
        good = hmac.new(SECRET, payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, good):
            return None
        data = json.loads(base64.urlsafe_b64decode(payload.encode()))
        return data["uid"] if data["exp"] > time.time() else None
    except Exception:
        return None


def user_out(row: sqlite3.Row | dict) -> dict:
    u = dict(row)
    try:
        crops = json.loads(u.get("crops") or "[]")
    except ValueError:
        crops = []
    return {"id": u["id"], "email": u["email"], "phone": u.get("phone") or "", "full_name": u.get("full_name") or "",
            "role": u.get("role") or "farmer", "region": u.get("region") or "", "language": u.get("language") or "en",
            "crops": crops, "created_at": u.get("created_at") or ""}


def current_user(request: Request, con: sqlite3.Connection = Depends(get_db)) -> dict:
    auth = request.headers.get("authorization", "")
    uid = read_token(auth[7:]) if auth.lower().startswith("bearer ") else None
    row = con.execute("SELECT * FROM users WHERE id=? AND is_active=1", (uid,)).fetchone() if uid else None
    if not row:
        raise err(401, "AUTHENTICATION_REQUIRED", "Please sign in to continue.")
    return dict(row)


# ---------------------------------------------------------------- serializers
def card(cls: str) -> dict:
    return get_disease_info(cls)


def result_out(r: sqlite3.Row, detail: bool = False) -> dict:
    info = get_disease_info(r["predicted"])
    out: dict[str, Any] = {
        "result_id": r["id"],
        "predicted": info["class"],
        "predicted_disease": info["name"],
        "crop": info["crop"],
        "healthy": info["healthy"],
        "confidence": r["confidence"],
        "detection_date": r["created_at"],
        "crop_type": r["crop_hint"],
        "severity": r["severity"],
        "urgent": info["urgent"],
        "latency_ms": r["latency_ms"],
        "image_url": "/api/v1/uploads/" + os.path.basename(r["image_path"] or ""),
        "bookmarked": bool(r["bookmarked"]),
    }
    if detail:
        top3 = json.loads(r["top3"] or "[]")
        out["created_at"] = r["created_at"]
        out["image_size"] = r["image_size"]
        out["disease_details"] = info
        out["top_3_predictions"] = [
            {"class": c, "disease": display_name(c), "confidence": p, "severity": get_disease_info(c)["severity"],
             "healthy": get_disease_info(c)["healthy"]} for c, p in top3]
        out["engine"] = inference.MODEL_KIND if inference.MODEL is not None else "heuristic"
    return out


def owned(con: sqlite3.Connection, rid: str, uid: str) -> sqlite3.Row:
    r = con.execute("SELECT * FROM results WHERE id=? AND user_id=?", (rid, uid)).fetchone()
    if not r:
        raise err(404, "NOT_FOUND", "That result was not found. It may have been deleted.")
    return r


def engine_name() -> str:
    return inference.MODEL_KIND if inference.MODEL is not None else "heuristic"


# ---------------------------------------------------------------- health + public
@app.get("/api/health")
def health(con: sqlite3.Connection = Depends(get_db)):
    con.execute("SELECT 1").fetchone()
    return {"status": "ok", "classes": len(CLASSES), "engine": engine_name(),
            "trained_model": inference.MODEL is not None, "db": "ok"}


@app.get("/api/v1/diseases")
def diseases():
    return [card(c) for c in CLASSES]


@app.get("/api/v1/diseases/{name:path}")
def disease_one(name: str):
    cls = next((c for c in CLASSES if display_name(c) == name or c == name), None)
    if not cls:
        raise err(404, "NOT_FOUND", "Disease not found.")
    return card(cls)


@app.get("/api/v1/uploads/{name}")
def upload_file(name: str):
    safe = os.path.basename(name)  # file names are random uuid hex, so the URL is the capability
    path = os.path.join(config.UPLOAD_DIR, safe)
    if not os.path.isfile(path):
        raise err(404, "NOT_FOUND", "Image not found.")
    return FileResponse(path, headers={"Cache-Control": "private, max-age=86400"})


# ---------------------------------------------------------------- auth + profile
def create_user(con: sqlite3.Connection, d: dict) -> str:
    email = str(d.get("email", "")).strip().lower()
    password = str(d.get("password", ""))
    if not EMAIL_RE.match(email):
        raise err(400, "INVALID_REQUEST", "Enter a valid email address.")
    if len(password) < 6:
        raise err(400, "INVALID_REQUEST", "Password must be at least 6 characters.")
    uid = str(uuid.uuid4())
    crops = d.get("crops") or [d.get("crop") or "tomato"]
    try:
        con.execute(
            "INSERT INTO users(id,email,phone,full_name,password_hash,role,region,language,crops,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (uid, email, d.get("phone", ""), d.get("full_name", ""), generate_password_hash(password),
             d.get("role", "farmer"), d.get("region", ""), d.get("language", "en"), json.dumps(crops),
             datetime.utcnow().isoformat()))
        con.commit()
    except sqlite3.IntegrityError:
        raise err(409, "EMAIL_EXISTS", "That email is already registered. Try signing in.")
    return uid


@app.post("/api/v1/auth/register", status_code=201)
async def register(request: Request, con: sqlite3.Connection = Depends(get_db)):
    try:
        d = await request.json()
    except Exception:
        d = {}
    if not isinstance(d, dict) or not d.get("email") or not d.get("password"):
        raise err(400, "INVALID_REQUEST", "Email and password are required.")
    uid = create_user(con, d)
    row = con.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    return {"user_id": uid, "email": row["email"], "message": "Account created.", "token": make_token(uid),
            "user": user_out(row)}


@app.post("/api/v1/auth/login")
async def login(request: Request, con: sqlite3.Connection = Depends(get_db)):
    try:
        d = await request.json()
    except Exception:
        d = {}
    email = str((d or {}).get("email", "")).strip().lower()
    row = con.execute("SELECT * FROM users WHERE email=? AND is_active=1", (email,)).fetchone()
    if not row or not check_password_hash(row["password_hash"], str((d or {}).get("password", ""))):
        raise err(401, "INVALID_CREDENTIALS", "Invalid email or password.")
    return {"token": make_token(row["id"]), "user": user_out(row)}


@app.get("/api/v1/auth/me")
def me(user: dict = Depends(current_user)):
    return user_out(user)


@app.put("/api/v1/profile")
async def update_profile(request: Request, user: dict = Depends(current_user), con: sqlite3.Connection = Depends(get_db)):
    d = await request.json()
    language = d.get("language", user["language"])
    if language not in ("en", "hi", "mr"):
        raise err(400, "INVALID_REQUEST", "Language must be en, hi or mr.")
    crops = d.get("crops") or ["tomato"]  # same default as Flask's profile form
    con.execute("UPDATE users SET full_name=?, region=?, language=?, crops=? WHERE id=?",
                (d.get("full_name", user["full_name"]), d.get("region", user["region"]), language,
                 json.dumps(crops), user["id"]))
    con.commit()
    return user_out(con.execute("SELECT * FROM users WHERE id=?", (user["id"],)).fetchone())


# ---------------------------------------------------------------- dashboard + analytics
@app.get("/api/v1/dashboard")
def dashboard(user: dict = Depends(current_user), con: sqlite3.Connection = Depends(get_db)):
    uid = user["id"]
    rows = con.execute("SELECT * FROM results WHERE user_id=? ORDER BY created_at DESC LIMIT 6", (uid,)).fetchall()
    total = con.execute("SELECT COUNT(*) c FROM results WHERE user_id=?", (uid,)).fetchone()["c"]
    healthy = con.execute("SELECT COUNT(*) c FROM results WHERE user_id=? AND severity='none'", (uid,)).fetchone()["c"]
    urgent = con.execute("SELECT COUNT(*) c FROM results WHERE user_id=? AND severity='high'", (uid,)).fetchone()["c"]
    return {"user": user_out(user), "total": total, "healthy": healthy, "urgent": urgent,
            "disease_rate": round((total - healthy) / total * 100, 1) if total else 0,
            "recent": [result_out(r) for r in rows], "engine": engine_name()}


@app.get("/api/v1/analytics/dashboard")
def analytics(user: dict = Depends(current_user), con: sqlite3.Connection = Depends(get_db)):
    rows = con.execute("SELECT predicted, severity, created_at FROM results WHERE user_id=? ORDER BY created_at",
                       (user["id"],)).fetchall()
    dist: dict[str, int] = {}
    sev = {"high": 0, "medium": 0, "low": 0, "none": 0}
    timeline: dict[str, int] = {}
    for r in rows:
        k = display_name(r["predicted"])
        dist[k] = dist.get(k, 0) + 1
        sev[r["severity"]] = sev.get(r["severity"], 0) + 1
        day = (r["created_at"] or "")[:10]
        timeline[day] = timeline.get(day, 0) + 1
    return {"total_detections": len(rows), "disease_distribution": dist, "severity": sev,
            "timeline": [{"date": d, "count": n} for d, n in timeline.items()]}


# ---------------------------------------------------------------- detection
@app.post("/api/v1/detect/upload")
async def detect(image: UploadFile = File(None), crop_type: str = Form("general"),
                 user: dict = Depends(current_user), con: sqlite3.Connection = Depends(get_db)):
    if image is None or not image.filename:
        raise err(400, "NO_IMAGE", "Choose a leaf image first.")
    ext = image.filename.rsplit(".", 1)[-1].lower()
    if ext not in config.ALLOWED_EXT:
        raise err(400, "INVALID_IMAGE_FORMAT", "Image must be JPG, PNG, JPEG or WEBP (max 10 MB).")
    data = await image.read()
    if len(data) > config.MAX_CONTENT_LENGTH:
        raise err(413, "IMAGE_TOO_LARGE", "That image is over 10 MB. Use a smaller photo.")
    if not data:
        raise err(400, "NO_IMAGE", "The file is empty.")
    try:
        out = predict(data, crop_type)
    except Exception:
        raise err(400, "UNREADABLE_IMAGE", "That file could not be read as an image. Try another photo.")
    info = get_disease_info(out["predicted"])
    name = f"{uuid.uuid4().hex}.{ext if ext != 'webp' else 'png'}"  # same naming rule as Flask's /detect
    with open(os.path.join(config.UPLOAD_DIR, name), "wb") as fh:
        fh.write(data)
    rid = str(uuid.uuid4())
    con.execute("INSERT INTO results VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (rid, user["id"], f"static/uploads/{name}", len(data), out["predicted"], out["confidence"],
                 json.dumps(out["top3"]), info["severity"], crop_type, out["latency_ms"],
                 datetime.utcnow().isoformat(), 0))
    con.commit()
    return {"result_id": rid, "predicted_disease": info["name"], "confidence": out["confidence"],
            "top_3_predictions": [{"disease": display_name(c), "confidence": p} for c, p in out["top3"]],
            "severity": info["severity"], "processing_time_ms": out["latency_ms"],
            "recommendations": {"treatments": info["treatments"], "prevention": info["prevention"],
                                "urgent_action": info["urgent"]},
            "engine": out.get("engine", engine_name())}


# ---------------------------------------------------------------- history + exports
@app.get("/api/v1/history")
def history(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), q: str = "", crop: str = "",
            disease: str = "", user: dict = Depends(current_user), con: sqlite3.Connection = Depends(get_db)):
    rows = con.execute("SELECT * FROM results WHERE user_id=? ORDER BY created_at DESC", (user["id"],)).fetchall()
    all_crops = sorted({get_disease_info(r["predicted"])["crop"] for r in rows})
    items = []
    for r in rows:  # same filter rules as Flask's /history
        info = get_disease_info(r["predicted"])
        if q and q.lower() not in (info["name"] + info["crop"]).lower():
            continue
        if crop and crop.lower() not in info["crop"].lower() and crop.lower() not in (r["crop_hint"] or "").lower():
            continue
        if disease == "healthy" and not info["healthy"]:
            continue
        if disease == "diseased" and info["healthy"]:
            continue
        items.append(r)
    return {"total_count": len(items), "all_count": len(rows), "crops": all_crops,
            "results": [result_out(r) for r in items[offset:offset + limit]]}


@app.get("/api/v1/history/export")
def export_all(user: dict = Depends(current_user), con: sqlite3.Connection = Depends(get_db)):
    rows = con.execute("SELECT * FROM results WHERE user_id=? ORDER BY created_at DESC", (user["id"],)).fetchall()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["result_id", "date", "crop_hint", "predicted", "confidence", "severity"])
    for r in rows:
        w.writerow([r["id"], r["created_at"], r["crop_hint"], display_name(r["predicted"]), r["confidence"], r["severity"]])
    return Response(buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="agrivision-history.csv"'})


@app.get("/api/v1/history/{rid}")
def history_one(rid: str, user: dict = Depends(current_user), con: sqlite3.Connection = Depends(get_db)):
    return result_out(owned(con, rid, user["id"]), detail=True)


@app.delete("/api/v1/history/{rid}")
def history_delete(rid: str, user: dict = Depends(current_user), con: sqlite3.Connection = Depends(get_db)):
    r = owned(con, rid, user["id"])
    try:
        os.remove(os.path.join(config.UPLOAD_DIR, os.path.basename(r["image_path"] or "")))
    except OSError:
        pass
    con.execute("DELETE FROM results WHERE id=?", (rid,))
    con.commit()
    return {"deleted": rid}


def pdf_bytes(rows: list[dict], info: dict | None = None) -> bytes:
    from reportlab.lib.pagesizes import A4  # same content/layout as Flask's export_pdf
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    _w, h = A4
    y = h - 60
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, y, "AgriVision - Disease Report")
    y -= 24
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Generated {datetime.utcnow():%Y-%m-%d %H:%M UTC}")
    y -= 30
    for r in rows:
        inf = info or get_disease_info(r["predicted"])
        for line in [f"Result: {r['id']}", f"Date: {r['created_at']}", f"Disease: {inf['name']}",
                     f"Confidence: {r['confidence'] * 100:.2f}%   Severity: {inf['severity']}",
                     f"Symptoms: {inf['symptoms'][:220]}",
                     f"Treatment: {inf['treatments'][0]['detail'][:220]}",
                     f"Prevention: {inf['prevention'][:220]}"]:
            c.setFont("Helvetica", 10)
            c.drawString(50, y, line.encode("latin-1", "replace").decode("latin-1")[:110])
            y -= 16
            if y < 60:
                c.showPage()
                y = h - 60
        y -= 12
    c.save()
    return buf.getvalue()


@app.get("/api/v1/history/{rid}/export")
def export_one(rid: str, format: str = "csv", user: dict = Depends(current_user),
               con: sqlite3.Connection = Depends(get_db)):
    r = owned(con, rid, user["id"])
    if format == "pdf":
        return Response(pdf_bytes([dict(r)], get_disease_info(r["predicted"])), media_type="application/pdf",
                        headers={"Content-Disposition": f'attachment; filename="agrivision-{rid[:8]}.pdf"'})
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["result_id", "date", "crop_hint", "predicted", "confidence", "severity", "latency_ms"])
    w.writerow([r["id"], r["created_at"], r["crop_hint"], display_name(r["predicted"]), r["confidence"],
                r["severity"], r["latency_ms"]])
    return Response(buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="agrivision-{rid[:8]}.csv"'})
