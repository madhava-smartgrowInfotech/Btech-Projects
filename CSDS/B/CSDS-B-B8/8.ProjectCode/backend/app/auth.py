from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from .config import JWT_SECRET
from .db import User, get_db


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def verify_password(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())


def make_token(user: User) -> str:
    payload = {"sub": str(user.id), "exp": datetime.now(timezone.utc) + timedelta(days=7)}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def current_user(request: Request, token: str | None = Query(None), db: Session = Depends(get_db)) -> User:
    header = request.headers.get("Authorization", "")
    raw = header[7:] if header.startswith("Bearer ") else token  # ?token= is used by <img> tags
    if not raw:
        raise HTTPException(401, "Not signed in")
    try:
        uid = int(jwt.decode(raw, JWT_SECRET, algorithms=["HS256"])["sub"])
    except Exception:
        raise HTTPException(401, "Session expired - please sign in again")
    user = db.get(User, uid)
    if not user:
        raise HTTPException(401, "User not found")
    return user
