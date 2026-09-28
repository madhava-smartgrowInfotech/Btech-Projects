from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import DEMO_PASSWORD, JWT_EXPIRE_MINUTES, JWT_SECRET
from .db import SessionLocal, User, get_db

bearer = HTTPBearer(auto_error=False)

DEMO_USERS = [
    ("supervisor@callsense.local", "QA Supervisor", "supervisor"),
    ("agent@callsense.local", "Alex", "agent"),
    ("sam@callsense.local", "Sam", "agent"),
    ("jordan@callsense.local", "Jordan", "agent"),
]


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def verify_password(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())


def create_token(user: User) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user.id), "role": user.role, "exp": exp}, JWT_SECRET, algorithm="HS256")


def _user_from_token(token, db: Session) -> User:
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired, please sign in again")
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user


def current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    return _user_from_token(creds.credentials if creds else None, db)


def user_from_header_or_query(creds: HTTPAuthorizationCredentials | None = Depends(bearer),
                              token: str | None = Query(None), db: Session = Depends(get_db)) -> User:
    """Audio elements cannot send headers, so the audio endpoint also accepts ?token=."""
    return _user_from_token(creds.credentials if creds else token, db)


def require_supervisor(user: User = Depends(current_user)) -> User:
    if user.role != "supervisor":
        raise HTTPException(403, "Supervisor access required")
    return user


def user_dict(u: User) -> dict:
    return {"id": u.id, "email": u.email, "name": u.name, "role": u.role}


def seed_users():
    with SessionLocal() as db:
        for email, name, role in DEMO_USERS:
            if not db.query(User).filter_by(email=email).first():
                db.add(User(email=email, name=name, role=role, password_hash=hash_password(DEMO_PASSWORD)))
        db.commit()
