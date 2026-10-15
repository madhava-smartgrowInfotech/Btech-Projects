"""Shared FastAPI dependencies: DB session, signed bearer tokens, role checks."""
import base64
import hashlib
import hmac
import json
import os
import time

from fastapi import Depends, Header, HTTPException

from database.database import get_session
from database.models import User, StudentProfile, MentorProfile

SECRET = os.getenv("APP_SECRET", "skillverse-dev-secret-change-me").encode()
TOKEN_TTL = 60 * 60 * 24 * 7  # one week


def iso(dt):
    return dt.isoformat() if dt else None


def make_token(user_id: int) -> str:
    body = base64.urlsafe_b64encode(json.dumps({"uid": user_id, "exp": int(time.time()) + TOKEN_TTL}).encode()).decode()
    sig = hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def read_token(token: str):
    try:
        body, sig = token.split(".", 1)
        good = hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, good):
            return None
        data = json.loads(base64.urlsafe_b64decode(body.encode()))
        return data["uid"] if data["exp"] > time.time() else None
    except Exception:
        return None


def get_db():
    """One SQLAlchemy session per request: commit on success, roll back on error."""
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def current_user(authorization: str = Header(default=""), db=Depends(get_db)) -> User:
    token = authorization[7:] if authorization.lower().startswith("bearer ") else ""
    uid = read_token(token) if token else None
    user = db.get(User, uid) if uid else None
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Your session has ended. Please sign in again.")
    return user


def require(*roles):
    def check(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail=f"This area is for {' / '.join(roles)} accounts.")
        return user
    return check


def student_of(db, user: User) -> StudentProfile:
    sp = db.query(StudentProfile).filter_by(user_id=user.id).first()
    if not sp:
        raise HTTPException(status_code=404, detail="Student profile not found.")
    return sp


def mentor_of(db, user: User) -> MentorProfile:
    mp = db.query(MentorProfile).filter_by(user_id=user.id).first()
    if not mp:
        raise HTTPException(status_code=404, detail="Mentor profile not found.")
    return mp


def user_dict(user: User) -> dict:
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role,
            "is_verified": bool(user.is_verified)}
