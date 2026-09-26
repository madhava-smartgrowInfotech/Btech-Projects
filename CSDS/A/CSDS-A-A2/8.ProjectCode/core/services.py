"""
Service layer: everything the UI needs, with no Streamlit dependency so it can
also be exercised from scripts and unit tests.
"""
from __future__ import annotations

import fnmatch
import secrets
from dataclasses import dataclass
from datetime import datetime

import numpy as np
from sqlalchemy import select

import config
from core import auth, face_match, geofence, liveness
from core.timeutil import utcnow
from core.db import get_session
from core.models import AttendanceRecord, AttendanceSession, DeviceBinding, User, VerificationAttempt


class ServiceError(Exception):
    pass


# --------------------------------------------------------------------------- #
# Users
# --------------------------------------------------------------------------- #
def register_user(role: str, username: str, full_name: str, password: str,
                  roll_number: str | None = None, face_image=None) -> User:
    if role not in {"faculty", "student"}:
        raise ServiceError("Invalid role.")
    username = username.strip().lower()
    if not username or not full_name.strip() or len(password) < 6:
        raise ServiceError("Username, full name and a password of at least 6 characters are required.")
    if role == "student":
        roll_number = (roll_number or "").strip().upper()
        if not roll_number:
            raise ServiceError("Roll number is required for students.")
    else:
        roll_number = None

    embedding = None
    if face_image is not None:
        embedding = face_match.to_bytes(face_match.embed(face_image))

    with get_session() as db:
        if db.scalar(select(User).where(User.username == username)):
            raise ServiceError("That username is already registered.")
        if roll_number and db.scalar(select(User).where(User.roll_number == roll_number)):
            raise ServiceError("That roll number is already registered.")
        user = User(role=role, username=username, full_name=full_name.strip(),
                    roll_number=roll_number, password_hash=auth.hash_password(password),
                    face_embedding=embedding)
        db.add(user)
        db.flush()
        db.refresh(user)
        return user


def authenticate(username: str, password: str, device_hash: str) -> tuple[User, str]:
    username = username.strip().lower()
    with get_session() as db:
        user = db.scalar(select(User).where(User.username == username))
        if user is None and username:
            user = db.scalar(select(User).where(User.roll_number == username.upper()))
        if user is None or not auth.verify_password(password, user.password_hash):
            raise ServiceError("Incorrect username / roll number or password.")
        return user, auth.issue_token(user, device_hash)


def get_user(user_id: int) -> User | None:
    with get_session() as db:
        return db.get(User, user_id)


def enroll_face(user_id: int, image_bgr: np.ndarray) -> float:
    """Store (or replace) the student's reference face. Returns nothing meaningful except success."""
    emb = face_match.embed(image_bgr)
    with get_session() as db:
        user = db.get(User, user_id)
        if user is None:
            raise ServiceError("User not found.")
        user.face_embedding = face_match.to_bytes(emb)
    return 1.0


def list_students() -> list[User]:
    with get_session() as db:
        return list(db.scalars(select(User).where(User.role == "student").order_by(User.roll_number)))


def reset_devices(user_id: int) -> int:
    with get_session() as db:
        rows = list(db.scalars(select(DeviceBinding).where(DeviceBinding.user_id == user_id)))
        for r in rows:
            db.delete(r)
        return len(rows)


# --------------------------------------------------------------------------- #
# Sessions
# --------------------------------------------------------------------------- #
def create_session(faculty_id: int, course_code: str, course_name: str, section: str,
                   starts_at: datetime, ends_at: datetime, latitude: float, longitude: float,
                   radius_m: float, allowed_rolls: str = "*") -> AttendanceSession:
    if ends_at <= starts_at:
        raise ServiceError("Session end must be after start.")
    if radius_m <= 0:
        raise ServiceError("Radius must be positive.")
    allowed = ",".join(p.strip().upper() for p in allowed_rolls.split(",") if p.strip()) or "*"
    with get_session() as db:
        s = AttendanceSession(
            token=secrets.token_urlsafe(24), faculty_id=faculty_id,
            course_code=course_code.strip().upper(), course_name=course_name.strip(),
            section=section.strip(), starts_at=starts_at, ends_at=ends_at,
            latitude=latitude, longitude=longitude, radius_m=radius_m, allowed_rolls=allowed,
        )
        db.add(s)
        db.flush()
        db.refresh(s)
        return s


def session_link(session: AttendanceSession) -> str:
    return f"{config.BASE_URL}/?session={session.token}"


def get_session_by_token(token: str) -> AttendanceSession | None:
    with get_session() as db:
        s = db.scalar(select(AttendanceSession).where(AttendanceSession.token == token))
        return s


def get_session_by_id(session_id: int) -> AttendanceSession | None:
    with get_session() as db:
        s = db.get(AttendanceSession, session_id)
        return s


def list_sessions(faculty_id: int) -> list[AttendanceSession]:
    with get_session() as db:
        rows = list(db.scalars(select(AttendanceSession)
                               .where(AttendanceSession.faculty_id == faculty_id)
                               .order_by(AttendanceSession.starts_at.desc())))
        return rows


def close_session(session_id: int) -> None:
    with get_session() as db:
        s = db.get(AttendanceSession, session_id)
        if s:
            s.is_closed = True


def records_for(session_id: int) -> list[AttendanceRecord]:
    with get_session() as db:
        return list(db.scalars(select(AttendanceRecord)
                               .where(AttendanceRecord.session_id == session_id)
                               .order_by(AttendanceRecord.marked_at)))


def attempts_for(session_id: int) -> list[VerificationAttempt]:
    with get_session() as db:
        return list(db.scalars(select(VerificationAttempt)
                               .where(VerificationAttempt.session_id == session_id)
                               .order_by(VerificationAttempt.created_at)))


def roll_allowed(patterns: str, roll: str) -> bool:
    roll = roll.upper()
    return any(fnmatch.fnmatchcase(roll, p.strip().upper()) for p in patterns.split(",") if p.strip())


def expected_rolls(patterns: str) -> list[str] | None:
    """If the allowed list is explicit (no wildcards) return it, else None."""
    pats = [p.strip().upper() for p in patterns.split(",") if p.strip()]
    if any(any(ch in p for ch in "*?[") for p in pats):
        return None
    return sorted(set(pats))


# --------------------------------------------------------------------------- #
# Verification pipeline pieces
# --------------------------------------------------------------------------- #
def log_attempt(session_id: int, roll: str, stage: str, passed: bool, reason: str, device_hash: str) -> None:
    with get_session() as db:
        db.add(VerificationAttempt(session_id=session_id, roll_number=roll, stage=stage,
                                   passed=passed, reason=reason[:1000], device_hash=device_hash))


@dataclass
class Eligibility:
    ok: bool
    reason: str


def check_eligibility(session: AttendanceSession, user: User, device_hash: str,
                      device_label: str = "", now: datetime | None = None) -> Eligibility:
    """Session window, roll-number restriction, duplicate record, device binding."""
    now = now or utcnow()
    status = session.status(now)
    if status != "live":
        msgs = {"upcoming": "This session has not started yet.",
                "expired": "This session has expired.",
                "closed": "This session was closed by the faculty."}
        return Eligibility(False, msgs[status])
    if user.role != "student" or not user.roll_number:
        return Eligibility(False, "Only student accounts can mark attendance.")
    if not roll_allowed(session.allowed_rolls, user.roll_number):
        return Eligibility(False, f"Roll number {user.roll_number} is not allowed in this session.")

    with get_session() as db:
        already = db.scalar(select(AttendanceRecord).where(
            AttendanceRecord.session_id == session.id, AttendanceRecord.student_id == user.id))
        if already:
            return Eligibility(False, "Attendance already marked for this session.")

        # One device may mark only one roll number per session.
        other = db.scalar(select(AttendanceRecord).where(
            AttendanceRecord.session_id == session.id, AttendanceRecord.device_hash == device_hash,
            AttendanceRecord.student_id != user.id))
        if other:
            return Eligibility(False, f"This device already marked attendance for {other.roll_number} in this session.")

        # Device binding: a student may use at most MAX_DEVICES_PER_STUDENT devices.
        bindings = list(db.scalars(select(DeviceBinding).where(DeviceBinding.user_id == user.id)))
        known = next((b for b in bindings if b.device_hash == device_hash), None)
        if known:
            known.last_seen = now
        elif len(bindings) >= config.MAX_DEVICES_PER_STUDENT:
            return Eligibility(False, "This device is not registered to your account. "
                                      "Use your usual device or ask faculty to reset your devices.")
        else:
            db.add(DeviceBinding(user_id=user.id, device_hash=device_hash, device_label=device_label))
    return Eligibility(True, "Eligible.")


def session_embeddings(session_id: int, exclude_student_id: int) -> list[tuple[str, np.ndarray]]:
    with get_session() as db:
        rows = db.scalars(select(AttendanceRecord).where(
            AttendanceRecord.session_id == session_id, AttendanceRecord.student_id != exclude_student_id))
        return [(r.roll_number, face_match.from_bytes(r.face_embedding)) for r in rows]


def record_attendance(session: AttendanceSession, user: User, *, lat: float, lon: float,
                      accuracy: float | None, distance: float, device_hash: str, challenge: str,
                      liveness_score: float, identity_sim: float | None, dup_sim: float | None,
                      embedding: np.ndarray) -> AttendanceRecord:
    with get_session() as db:
        rec = AttendanceRecord(
            session_id=session.id, student_id=user.id, roll_number=user.roll_number,
            student_name=user.full_name, latitude=lat, longitude=lon, gps_accuracy_m=accuracy,
            distance_m=distance, device_hash=device_hash, challenge=challenge,
            liveness_score=liveness_score, identity_similarity=identity_sim,
            max_duplicate_similarity=dup_sim, face_embedding=face_match.to_bytes(embedding),
        )
        db.add(rec)
        db.flush()
        db.refresh(rec)
    log_attempt(session.id, user.roll_number, "success", True, "Attendance recorded.", device_hash)
    return rec


# --------------------------------------------------------------------------- #
# Headless end-to-end pipeline (used by the demo script and tests)
# --------------------------------------------------------------------------- #
@dataclass
class PipelineResult:
    success: bool
    stage: str
    reason: str
    record: AttendanceRecord | None = None


def run_pipeline(session: AttendanceSession, user: User, device_hash: str, lat: float, lon: float,
                 accuracy: float | None, challenge: str, neutral_bgr: np.ndarray,
                 challenge_bgr: np.ndarray, now: datetime | None = None) -> PipelineResult:
    """Run every check in order exactly as the UI does, logging each stage."""
    roll = user.roll_number or user.username

    elig = check_eligibility(session, user, device_hash, now=now)
    log_attempt(session.id, roll, "eligibility", elig.ok, elig.reason, device_hash)
    if not elig.ok:
        return PipelineResult(False, "eligibility", elig.reason)

    geo = geofence.check_geofence(lat, lon, session.latitude, session.longitude, session.radius_m, accuracy)
    log_attempt(session.id, roll, "location", geo.inside, geo.reason, device_hash)
    if not geo.inside:
        return PipelineResult(False, "location", geo.reason)

    live = liveness.verify_challenge(challenge, liveness.analyze(neutral_bgr), liveness.analyze(challenge_bgr))
    log_attempt(session.id, roll, "liveness", live.passed, live.reason, device_hash)
    if not live.passed:
        return PipelineResult(False, "liveness", live.reason)

    try:
        emb_neutral = face_match.embed(neutral_bgr)
        emb_chal = face_match.embed(challenge_bgr)
    except face_match.FaceError as exc:
        log_attempt(session.id, roll, "face", False, str(exc), device_hash)
        return PipelineResult(False, "face", str(exc))

    enrolled = face_match.from_bytes(user.face_embedding) if user.face_embedding else None
    match = face_match.verify_faces(emb_neutral, enrolled, session_embeddings(session.id, user.id), emb_chal)
    log_attempt(session.id, roll, "face", match.passed, match.reason, device_hash)
    if not match.passed:
        return PipelineResult(False, "face", match.reason)

    rec = record_attendance(session, user, lat=lat, lon=lon, accuracy=accuracy, distance=geo.distance_m,
                            device_hash=device_hash, challenge=challenge, liveness_score=live.score,
                            identity_sim=match.identity_similarity, dup_sim=match.max_duplicate_similarity,
                            embedding=emb_neutral)
    return PipelineResult(True, "success", "Attendance recorded.", rec)
