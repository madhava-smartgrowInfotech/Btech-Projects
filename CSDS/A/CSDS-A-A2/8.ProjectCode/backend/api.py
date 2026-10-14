"""
Attendance Magic — thin HTTP API for the React frontend.

    venv\\Scripts\\python -m uvicorn backend.api:app --port 8102

Every endpoint calls the existing `core/` functions (the same ones the Streamlit UI in `ui/`
calls). No verification logic lives here: this module only translates HTTP <-> service calls and
keeps the per-student check-in wizard state that Streamlit kept in `st.session_state`.
"""
from __future__ import annotations

import io
import json
import sys
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Request, UploadFile  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import Response  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402
from sqlalchemy import func, select  # noqa: E402

import config  # noqa: E402
from core import auth, device, export, face_match, geofence, liveness, services, timeutil  # noqa: E402
from core.db import get_session, init_db  # noqa: E402
from core.models import AttendanceRecord, AttendanceSession, DeviceBinding, User, VerificationAttempt  # noqa: E402

try:  # same constants the Streamlit wizard uses
    from ui.student import MAX_LIVENESS_RETRIES, STEPS
except Exception:  # pragma: no cover - streamlit missing
    MAX_LIVENESS_RETRIES = 3
    STEPS = ["Sign in", "Eligibility", "Location", "Live challenge", "Face match", "Done"]

app = FastAPI(title=f"{config.APP_NAME} API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

_models: dict[str, str] = {}
_models_lock = threading.Lock()


def _warm_models() -> dict[str, str]:
    """Load MediaPipe + InsightFace once per process (mirrors app._warm_models)."""
    with _models_lock:
        if not _models:
            det = liveness.get_detector()
            face_match.get_embedder()
            _models.update(landmarks=det.backend, recognition=f"insightface/{config.INSIGHTFACE_MODEL}")
    return dict(_models)


@app.on_event("startup")
def _startup() -> None:
    init_db()
    threading.Thread(target=_warm_models, daemon=True).start()


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() + "Z" if dt else None


def _headers(request: Request) -> dict:
    return dict(request.headers)


def device_hash(request: Request) -> str:
    """Same fingerprint as the Streamlit app, seeded with the browser's persistent id."""
    return device.fingerprint(_headers(request), extra=request.headers.get("x-device-id", ""))


def user_out(u: User, devices: int | None = None) -> dict:
    out = {
        "id": u.id, "role": u.role, "username": u.username, "full_name": u.full_name,
        "roll_number": u.roll_number, "enrolled": u.face_embedding is not None,
        "created_at": _iso(u.created_at), "registered": timeutil.fmt(u.created_at),
    }
    if devices is not None:
        out["devices"] = devices
    return out


def session_out(s: AttendanceSession, private: bool = True) -> dict:
    out = {
        "id": s.id, "token": s.token, "course_code": s.course_code, "course_name": s.course_name,
        "section": s.section, "status": s.status(),
        "starts_at": _iso(s.starts_at), "ends_at": _iso(s.ends_at),
        "starts_local": timeutil.fmt(s.starts_at), "ends_local": timeutil.fmt(s.ends_at),
        "latitude": s.latitude, "longitude": s.longitude, "radius_m": s.radius_m,
        "faculty_name": s.faculty.full_name if s.faculty else "",
    }
    if private:
        out.update(allowed_rolls=s.allowed_rolls, is_closed=s.is_closed,
                   streamlit_link=services.session_link(s), created_at=_iso(s.created_at))
    return out


def attempt_out(a: VerificationAttempt) -> dict:
    return {"id": a.id, "time": timeutil.fmt(a.created_at, True), "created_at": _iso(a.created_at),
            "roll_number": a.roll_number, "stage": a.stage, "passed": a.passed, "reason": a.reason,
            "device": a.device_hash[:10]}


def _read_image(data: bytes):
    try:
        return liveness.decode_image(data)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


# --------------------------------------------------------------------------- #
# Auth dependencies (JWT verified on every request against the device, as Streamlit does per rerun)
# --------------------------------------------------------------------------- #
def current_claims(request: Request) -> auth.TokenClaims:
    header = request.headers.get("authorization", "")
    token = header[7:].strip() if header.lower().startswith("bearer ") else ""
    if not token:
        raise HTTPException(401, "Please sign in.")
    try:
        return auth.verify_token(token, device_hash(request))
    except auth.TokenError as exc:
        raise HTTPException(401, str(exc)) from exc


def faculty_claims(claims: auth.TokenClaims = Depends(current_claims)) -> auth.TokenClaims:
    if claims.role != "faculty":
        raise HTTPException(403, "You are signed in as a student. Sign out to use the faculty portal.")
    return claims


def student_claims(claims: auth.TokenClaims = Depends(current_claims)) -> auth.TokenClaims:
    if claims.role != "student":
        raise HTTPException(403, "Faculty accounts cannot mark attendance. Sign out and use a student account.")
    return claims


def _own_session(session_id: int, claims: auth.TokenClaims) -> AttendanceSession:
    s = services.get_session_by_id(session_id)
    if s is None or s.faculty_id != claims.user_id:
        raise HTTPException(404, "Session not found.")
    return s


# --------------------------------------------------------------------------- #
# Meta
# --------------------------------------------------------------------------- #
@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "app": config.APP_NAME, "tagline": config.APP_TAGLINE,
            "db": config.DATABASE_URL.split("://")[0], "models_ready": bool(_models)}


@app.get("/api/config")
def public_config() -> dict:
    """Read-only view of the settings the UI needs to render the same rules as Streamlit."""
    return {
        "app_name": config.APP_NAME, "tagline": config.APP_TAGLINE,
        "allow_manual_location": config.ALLOW_MANUAL_LOCATION,
        "default_radius_m": config.DEFAULT_GEOFENCE_RADIUS_M,
        "geofence_tolerance_m": config.GEOFENCE_TOLERANCE_M,
        "max_gps_accuracy_m": config.MAX_GPS_ACCURACY_M,
        "identity_threshold": config.IDENTITY_THRESHOLD,
        "duplicate_threshold": config.DUPLICATE_THRESHOLD,
        "frame_consistency_threshold": config.FRAME_CONSISTENCY_THRESHOLD,
        "require_enrollment": config.REQUIRE_ENROLLMENT,
        "jwt_expiry_minutes": config.JWT_EXPIRY_MINUTES,
        "max_devices_per_student": config.MAX_DEVICES_PER_STUDENT,
        "camera_mirrored": config.CAMERA_MIRRORED,
        "timezone": config.TIMEZONE,
        "now_local": timeutil.now_local().strftime("%Y-%m-%dT%H:%M"),
        "max_liveness_retries": MAX_LIVENESS_RETRIES,
        "steps": STEPS,
        "liveness": {"yaw_delta": config.LIVENESS_YAW_DELTA, "pitch_delta": config.LIVENESS_PITCH_DELTA,
                     "roll_deg": config.LIVENESS_ROLL_DEG, "mouth_open_mar": config.LIVENESS_MOUTH_OPEN_MAR,
                     "eyes_closed_ear": config.LIVENESS_EYES_CLOSED_EAR},
        "challenges": [{"code": k, "text": v[0], "emoji": v[1]} for k, v in liveness.CHALLENGES.items()],
    }


@app.get("/api/models")
def models() -> dict:
    return {**_warm_models(), "db": config.DATABASE_URL.split("://")[0]}


@app.get("/api/stats")
def stats() -> dict:
    """Read-only totals for the landing page stats strip."""
    with get_session() as db:
        count = lambda q: int(db.scalar(q) or 0)  # noqa: E731
        sessions = list(db.scalars(select(AttendanceSession)))
        return {
            "sessions": len(sessions),
            "live_sessions": sum(1 for s in sessions if s.status() == "live"),
            "records": count(select(func.count(AttendanceRecord.id))),
            "attempts": count(select(func.count(VerificationAttempt.id))),
            "blocked": count(select(func.count(VerificationAttempt.id)).where(VerificationAttempt.passed.is_(False))),
            "students": count(select(func.count(User.id)).where(User.role == "student")),
            "enrolled": count(select(func.count(User.id)).where(User.role == "student",
                                                                User.face_embedding.is_not(None))),
            "faculty": count(select(func.count(User.id)).where(User.role == "faculty")),
        }


@app.get("/api/qr")
def qr(text: str = Query(..., min_length=1, max_length=2048)) -> Response:
    import qrcode

    img = qrcode.make(text, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(buf.getvalue(), media_type="image/png")


# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #
class LoginIn(BaseModel):
    username: str = ""
    password: str = ""
    role: str | None = None


@app.post("/api/auth/login")
def login(body: LoginIn, request: Request) -> dict:
    try:
        user, token = services.authenticate(body.username, body.password, device_hash(request))
    except services.ServiceError as exc:
        raise HTTPException(401, str(exc)) from exc
    if body.role and user.role != body.role:
        raise HTTPException(403, f"This account is a {user.role} account. Please use the {user.role} portal.")
    claims = auth.verify_token(token)
    return {"token": token, "user": user_out(user), "expires_at": claims.expires_at.isoformat(),
            "expires_local": claims.expires_at.astimezone(timeutil.LOCAL_TZ).strftime("%H:%M"),
            "jwt_expiry_minutes": config.JWT_EXPIRY_MINUTES}


@app.post("/api/auth/register")
def register(
    role: str = Form(...), full_name: str = Form(""), password: str = Form(""),
    username: str = Form(""), roll_number: str = Form(""), face: UploadFile | None = File(None),
) -> dict:
    """Mirrors ui.common.register_form: students need a neutral reference face when enrolment is required."""
    try:
        face_img = None
        roll = roll_number or None
        if role == "student":
            if config.REQUIRE_ENROLLMENT and face is None:
                raise HTTPException(400, "A reference face photo is required for student registration.")
            if face is not None:
                face_img = _read_image(face.file.read())
                if err := liveness.check_neutral(liveness.analyze(face_img)):
                    raise HTTPException(400, err)
            username = (username or roll or "").strip()
        user = services.register_user(role, username, full_name, password, roll, face_img)
    except HTTPException:
        raise
    except (services.ServiceError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:  # face errors
        raise HTTPException(400, f"Face enrolment failed: {exc}") from exc
    return {"user": user_out(user), "message": f"Account created for {user.full_name}. You can sign in now."}


@app.get("/api/auth/me")
def me(request: Request, claims: auth.TokenClaims = Depends(current_claims)) -> dict:
    user = services.get_user(claims.user_id)
    if user is None:
        raise HTTPException(401, "Account no longer exists.")
    return {"user": user_out(user), "device": device_hash(request)[:10],
            "device_label": device.label(_headers(request)),
            "expires_local": claims.expires_at.astimezone(timeutil.LOCAL_TZ).strftime("%H:%M")}


@app.post("/api/auth/logout")
def logout(request: Request, claims: auth.TokenClaims = Depends(current_claims)) -> dict:
    """Streamlit's logout also drops the check-in wizard state."""
    dev = device_hash(request)
    with _ck_lock:
        for key in [k for k in _checkins if k[0] == claims.user_id and k[2] == dev]:
            _checkins.pop(key, None)
    return {"ok": True}


# --------------------------------------------------------------------------- #
# Faculty: sessions
# --------------------------------------------------------------------------- #
class SessionIn(BaseModel):
    course_code: str = ""
    course_name: str = ""
    section: str = ""
    start_local: str  # "YYYY-MM-DDTHH:MM" in config.TIMEZONE
    duration_min: int = Field(15, ge=1, le=600)
    latitude: float
    longitude: float
    radius_m: float
    allowed_rolls: str = "*"


def _session_summary(s: AttendanceSession) -> dict:
    records = services.records_for(s.id)
    attempts = services.attempts_for(s.id)
    expected = services.expected_rolls(s.allowed_rolls)
    return {**session_out(s), "present": len(records), "expected": len(expected) if expected else None,
            "attempts": len(attempts), "blocked": sum(1 for a in attempts if not a.passed)}


@app.get("/api/sessions")
def sessions(claims: auth.TokenClaims = Depends(faculty_claims)) -> list[dict]:
    return [_session_summary(s) for s in services.list_sessions(claims.user_id)]


@app.post("/api/sessions")
def create_session(body: SessionIn, claims: auth.TokenClaims = Depends(faculty_claims)) -> dict:
    try:
        starts_local = datetime.fromisoformat(body.start_local)
    except ValueError as exc:
        raise HTTPException(400, "Start date/time is not valid.") from exc
    starts_utc = timeutil.to_utc(starts_local.replace(tzinfo=None, second=0, microsecond=0))
    try:
        s = services.create_session(
            claims.user_id, body.course_code, body.course_name, body.section, starts_utc,
            starts_utc + timedelta(minutes=int(body.duration_min)), body.latitude, body.longitude,
            float(body.radius_m), body.allowed_rolls,
        )
    except services.ServiceError as exc:
        raise HTTPException(400, str(exc)) from exc
    return _session_summary(services.get_session_by_id(s.id))


@app.get("/api/sessions/{session_id}")
def session_detail(session_id: int, claims: auth.TokenClaims = Depends(faculty_claims)) -> dict:
    s = _own_session(session_id, claims)
    records = services.records_for(s.id)
    attempts = services.attempts_for(s.id)
    expected = services.expected_rolls(s.allowed_rolls)
    df = export.records_dataframe(s, records, expected)
    rows = json.loads(df.to_json(orient="records")) if not df.empty else []
    return {
        "session": session_out(s),
        "metrics": {"status": s.status(), "present": len(records),
                    "expected": len(expected) if expected else None,
                    "blocked": sum(1 for a in attempts if not a.passed), "attempts": len(attempts)},
        "rows": rows,
        "records": [{"roll_number": r.roll_number, "student_name": r.student_name, "latitude": r.latitude,
                     "longitude": r.longitude, "distance_m": r.distance_m, "marked": timeutil.fmt(r.marked_at, True),
                     "challenge": r.challenge, "liveness_score": r.liveness_score,
                     "identity_similarity": r.identity_similarity} for r in records],
        "attempts": [attempt_out(a) for a in reversed(attempts)],
    }


@app.post("/api/sessions/{session_id}/close")
def close_session(session_id: int, claims: auth.TokenClaims = Depends(faculty_claims)) -> dict:
    s = _own_session(session_id, claims)
    services.close_session(s.id)
    return session_out(services.get_session_by_id(s.id))


@app.get("/api/sessions/{session_id}/export")
def export_session(session_id: int, claims: auth.TokenClaims = Depends(faculty_claims)) -> Response:
    s = _own_session(session_id, claims)
    records, attempts = services.records_for(s.id), services.attempts_for(s.id)
    data = export.to_excel_bytes(s, records, attempts, services.expected_rolls(s.allowed_rolls))
    name = f"attendance_{s.course_code}_{timeutil.to_local(s.starts_at):%Y%m%d_%H%M}.xlsx"
    return Response(data, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="{name}"'})


@app.get("/api/dashboard")
def dashboard(claims: auth.TokenClaims = Depends(faculty_claims)) -> dict:
    """Read-only aggregate over the faculty's own sessions."""
    rows, stages, recent = [], {}, []
    for s in services.list_sessions(claims.user_id):
        records, attempts = services.records_for(s.id), services.attempts_for(s.id)
        rows.append({"id": s.id, "course_code": s.course_code, "section": s.section, "status": s.status(),
                     "starts_local": timeutil.fmt(s.starts_at), "present": len(records),
                     "attempts": len(attempts), "blocked": sum(1 for a in attempts if not a.passed)})
        for a in attempts:
            st = stages.setdefault(a.stage, {"stage": a.stage, "passed": 0, "blocked": 0})
            st["passed" if a.passed else "blocked"] += 1
            recent.append((a.created_at, {**attempt_out(a), "course_code": s.course_code, "session_id": s.id}))
    recent.sort(key=lambda t: t[0], reverse=True)
    order = ["eligibility", "location", "liveness", "face", "success"]
    return {
        "totals": {"sessions": len(rows), "live": sum(1 for r in rows if r["status"] == "live"),
                   "present": sum(r["present"] for r in rows), "attempts": sum(r["attempts"] for r in rows),
                   "blocked": sum(r["blocked"] for r in rows)},
        "sessions": rows,
        "stages": sorted(stages.values(), key=lambda d: order.index(d["stage"]) if d["stage"] in order else 99),
        "recent_attempts": [r for _, r in recent[:10]],
    }


# --------------------------------------------------------------------------- #
# Faculty: students
# --------------------------------------------------------------------------- #
@app.get("/api/students")
def students(claims: auth.TokenClaims = Depends(faculty_claims)) -> list[dict]:
    with get_session() as db:
        counts = dict(db.execute(select(DeviceBinding.user_id, func.count(DeviceBinding.id))
                                 .group_by(DeviceBinding.user_id)).all())
    return [user_out(u, counts.get(u.id, 0)) for u in services.list_students()]


@app.post("/api/students/{user_id}/reset-devices")
def reset_devices(user_id: int, claims: auth.TokenClaims = Depends(faculty_claims)) -> dict:
    n = services.reset_devices(user_id)
    user = services.get_user(user_id)
    return {"removed": n, "message": f"Removed {n} device binding(s) for {user.roll_number if user else user_id}."}


@app.post("/api/students/{user_id}/enroll")
def enroll(user_id: int, face: UploadFile = File(...), claims: auth.TokenClaims = Depends(faculty_claims)) -> dict:
    img = _read_image(face.file.read())
    try:
        if err := liveness.check_neutral(liveness.analyze(img)):
            raise HTTPException(400, err)
        services.enroll_face(user_id, img)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(400, f"Enrolment failed: {exc}") from exc
    return {"ok": True, "message": "Reference face updated."}


# --------------------------------------------------------------------------- #
# Student check-in (the 6-step wizard of ui/student.py)
# --------------------------------------------------------------------------- #
_checkins: dict[tuple[int, int, str], dict[str, Any]] = {}
_ck_lock = threading.Lock()


def _session_by_token(token: str) -> AttendanceSession:
    s = services.get_session_by_token(token)
    if s is None:
        raise HTTPException(404, "Invalid session link.")
    return s


def _ck(user_id: int, session_id: int, dev: str) -> dict[str, Any]:
    key = (user_id, session_id, dev)
    with _ck_lock:
        ck = _checkins.get(key)
        if ck is None:
            ck = {"step": 1, "challenge": liveness.random_challenge(), "liveness_tries": 0}
            _checkins[key] = ck
        return ck


def _ck_out(ck: dict[str, Any]) -> dict:
    text, emoji = liveness.describe(ck["challenge"])
    out = {"step": ck["step"], "challenge": ck["challenge"], "challenge_text": text, "challenge_emoji": emoji,
           "tries_left": MAX_LIVENESS_RETRIES - ck["liveness_tries"], "locked": ck["step"] == 99}
    if "distance" in ck:
        out["distance_m"] = ck["distance"]
    if "liveness_score" in ck:
        out["liveness_score"] = ck["liveness_score"]
    if "result" in ck:
        out["result"] = ck["result"]
    return out


def _require_step(ck: dict, step: int) -> None:
    if ck["step"] != step:
        raise HTTPException(409, "Complete the previous step first.")


@app.get("/api/public/sessions/{token}")
def public_session(token: str) -> dict:
    return session_out(_session_by_token(token), private=False)


@app.get("/api/checkin/{token}/state")
def checkin_state(token: str, request: Request, claims: auth.TokenClaims = Depends(student_claims)) -> dict:
    s = _session_by_token(token)
    return _ck_out(_ck(claims.user_id, s.id, device_hash(request)))


@app.post("/api/checkin/{token}/start")
def checkin_start(token: str, request: Request, claims: auth.TokenClaims = Depends(student_claims)) -> dict:
    s, dev = _session_by_token(token), device_hash(request)
    user = services.get_user(claims.user_id)
    ck = _ck(user.id, s.id, dev)
    if ck["step"] != 1:
        return {"ok": True, "reason": "Eligible.", "state": _ck_out(ck)}
    elig = services.check_eligibility(s, user, dev, device.label(_headers(request)))
    services.log_attempt(s.id, user.roll_number, "eligibility", elig.ok, elig.reason, dev)
    if elig.ok:
        ck["step"] = 2
    return {"ok": elig.ok, "reason": elig.reason, "state": _ck_out(ck)}


class LocationIn(BaseModel):
    lat: float
    lon: float
    accuracy: float | None = None


@app.post("/api/checkin/{token}/location")
def checkin_location(token: str, body: LocationIn, request: Request,
                     claims: auth.TokenClaims = Depends(student_claims)) -> dict:
    s, dev = _session_by_token(token), device_hash(request)
    user = services.get_user(claims.user_id)
    ck = _ck(user.id, s.id, dev)
    _require_step(ck, 2)
    geo = geofence.check_geofence(body.lat, body.lon, s.latitude, s.longitude, s.radius_m, body.accuracy)
    services.log_attempt(s.id, user.roll_number, "location", geo.inside, geo.reason, dev)
    if geo.inside:
        ck.update(step=3, loc=body.model_dump(), distance=geo.distance_m)
    return {"inside": geo.inside, "distance_m": geo.distance_m, "allowed_m": geo.allowed_m,
            "reason": geo.reason, "state": _ck_out(ck)}


@app.post("/api/checkin/{token}/neutral")
def checkin_neutral(token: str, request: Request, image: UploadFile = File(...),
                    claims: auth.TokenClaims = Depends(student_claims)) -> dict:
    s = _session_by_token(token)
    _require_step(_ck(claims.user_id, s.id, device_hash(request)), 3)
    err = liveness.check_neutral(liveness.analyze(_read_image(image.file.read())))
    return {"ok": err is None, "message": err or "Good neutral frame."}


@app.post("/api/checkin/{token}/liveness")
def checkin_liveness(token: str, request: Request, neutral: UploadFile = File(...),
                     challenge: UploadFile = File(...), claims: auth.TokenClaims = Depends(student_claims)) -> dict:
    s, dev = _session_by_token(token), device_hash(request)
    user = services.get_user(claims.user_id)
    ck = _ck(user.id, s.id, dev)
    _require_step(ck, 3)
    n_bytes, c_bytes = neutral.file.read(), challenge.file.read()
    n_img, c_img = _read_image(n_bytes), _read_image(c_bytes)
    asked = ck["challenge"]
    res = liveness.verify_challenge(asked, liveness.analyze(n_img), liveness.analyze(c_img))
    services.log_attempt(s.id, user.roll_number, "liveness", res.passed, f"{asked}: {res.reason}", dev)
    message = None
    if res.passed:
        ck.update(step=4, neutral_bytes=n_bytes, challenge_bytes=c_bytes,
                  liveness_score=res.score, liveness_reason=res.reason)
    else:
        ck["liveness_tries"] += 1
        if ck["liveness_tries"] >= MAX_LIVENESS_RETRIES:
            ck["step"] = 99
            message = "Too many failed attempts. Start over, or contact faculty."
        else:
            ck["challenge"] = liveness.random_challenge()  # new random challenge each retry
            message = (f"New challenge issued ({MAX_LIVENESS_RETRIES - ck['liveness_tries']} tries left). "
                       "Take both photos again.")
    return {"passed": res.passed, "score": res.score, "reason": res.reason, "challenge": asked,
            "message": message, "state": _ck_out(ck)}


@app.post("/api/checkin/{token}/face")
def checkin_face(token: str, request: Request, claims: auth.TokenClaims = Depends(student_claims)) -> dict:
    s, dev = _session_by_token(token), device_hash(request)
    user = services.get_user(claims.user_id)
    ck = _ck(user.id, s.id, dev)
    _require_step(ck, 4)
    try:
        n_img = liveness.decode_image(ck["neutral_bytes"])
        c_img = liveness.decode_image(ck["challenge_bytes"])
        emb_n, emb_c = face_match.embed(n_img), face_match.embed(c_img)
    except (face_match.FaceError, ValueError) as exc:
        services.log_attempt(s.id, user.roll_number, "face", False, str(exc), dev)
        return {"passed": False, "reason": str(exc), "retake": True, "state": _ck_out(ck)}
    enrolled = face_match.from_bytes(user.face_embedding) if user.face_embedding else None
    match = face_match.verify_faces(emb_n, enrolled, services.session_embeddings(s.id, user.id), emb_c)
    services.log_attempt(s.id, user.roll_number, "face", match.passed, match.reason, dev)
    if not match.passed:
        return {"passed": False, "reason": match.reason, "retake": False, "state": _ck_out(ck)}
    # Re-check eligibility right before writing (session may have expired meanwhile).
    elig = services.check_eligibility(s, user, dev)
    if not elig.ok:
        return {"passed": False, "reason": elig.reason, "retake": False, "state": _ck_out(ck)}
    rec = services.record_attendance(
        s, user, lat=ck["loc"]["lat"], lon=ck["loc"]["lon"], accuracy=ck["loc"].get("accuracy"),
        distance=ck["distance"], device_hash=dev, challenge=ck["challenge"],
        liveness_score=ck["liveness_score"], identity_sim=match.identity_similarity,
        dup_sim=match.max_duplicate_similarity, embedding=emb_n,
    )
    text, emoji = liveness.describe(ck["challenge"])
    ck.update(step=5, record_id=rec.id, result={
        "roll_number": user.roll_number, "full_name": user.full_name, "distance_m": ck["distance"],
        "liveness_score": ck["liveness_score"], "challenge": ck["challenge"], "challenge_text": text,
        "challenge_emoji": emoji, "identity_similarity": match.identity_similarity,
        "max_duplicate_similarity": match.max_duplicate_similarity,
        "recorded_at": timeutil.fmt(rec.marked_at, True), "device": dev[:10],
        "identity_threshold": config.IDENTITY_THRESHOLD, "duplicate_threshold": config.DUPLICATE_THRESHOLD,
    })
    for k in ("neutral_bytes", "challenge_bytes"):
        ck.pop(k, None)
    return {"passed": True, "reason": "Attendance recorded.", "state": _ck_out(ck)}


@app.post("/api/checkin/{token}/retake")
def checkin_retake(token: str, request: Request, claims: auth.TokenClaims = Depends(student_claims)) -> dict:
    """'Retake photos' after a face-detection error sends the wizard back to the challenge step."""
    s = _session_by_token(token)
    ck = _ck(claims.user_id, s.id, device_hash(request))
    _require_step(ck, 4)
    ck["step"] = 3
    return {"state": _ck_out(ck)}


@app.post("/api/checkin/{token}/reset")
def checkin_reset(token: str, request: Request, claims: auth.TokenClaims = Depends(student_claims)) -> dict:
    """'Start over' — drops the wizard state, exactly like popping st.session_state['checkin']."""
    s, dev = _session_by_token(token), device_hash(request)
    with _ck_lock:
        _checkins.pop((claims.user_id, s.id, dev), None)
    return {"state": _ck_out(_ck(claims.user_id, s.id, dev))}
