"""Login (analyst / moderator), JWT tokens and the demo accounts."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import SessionLocal, User, get_db
from .settings import JWT_HOURS, JWT_SECRET

DEMO_PASSWORD = "Demo@1234"
DEMO_USERS = [
    ("analyst@botgraph.app", "Demo Analyst", "analyst"),
    ("moderator@botgraph.app", "Demo Moderator", "moderator"),
]

bearer = HTTPBearer(auto_error=False)


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode()[:72], bcrypt.gensalt()).decode()


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode()[:72], hashed.encode())
    except ValueError:
        return False


def make_token(user: User) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=JWT_HOURS)
    return jwt.encode({"sub": str(user.id), "role": user.role, "exp": exp}, JWT_SECRET, algorithm="HS256")


def user_out(u: User) -> dict:
    return {"id": u.id, "email": u.email, "name": u.name, "role": u.role}


def seed_demo_users() -> None:
    with SessionLocal() as db:
        for email, name, role in DEMO_USERS:
            if not db.scalar(select(User).where(User.email == email)):
                db.add(User(email=email, name=name, role=role, password_hash=hash_password(DEMO_PASSWORD)))
        db.commit()


def current_user(cred: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    err = HTTPException(status.HTTP_401_UNAUTHORIZED, "Please sign in to continue.")
    if not cred:
        raise err
    try:
        data = jwt.decode(cred.credentials, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Your session has expired. Please sign in again.")
    user = db.get(User, int(data["sub"]))
    if not user:
        raise err
    return user


def require_moderator(user: User = Depends(current_user)) -> User:
    if user.role != "moderator":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only moderators can record decisions or retrain the model.")
    return user
