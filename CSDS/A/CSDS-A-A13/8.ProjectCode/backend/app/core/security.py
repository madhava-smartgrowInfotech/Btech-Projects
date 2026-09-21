"""Password hashing and login tokens."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _pwd.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _pwd.verify(password, password_hash)
    except ValueError:
        return False


def create_access_token(user_id: int, role: str) -> tuple[str, datetime]:
    settings = get_settings()
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    token = jwt.encode({"sub": str(user_id), "role": role, "exp": expires}, settings.jwt_secret, algorithm=ALGORITHM)
    return token, expires


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, get_settings().jwt_secret, algorithms=[ALGORITHM])
