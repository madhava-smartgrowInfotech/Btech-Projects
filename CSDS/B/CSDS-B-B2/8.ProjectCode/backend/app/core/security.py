"""Passwords (bcrypt), login tokens (JWT), role checks and device API keys."""
from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

import jwt
from fastapi import Depends, Header, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..models import Device, User
from .config import settings
from .db import get_db, utcnow

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)
ALGORITHM = "HS256"
ROLE_RANK = {"user": 0, "engineer": 1, "admin": 2}


def hash_password(password: str) -> str:
    return _pwd.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _pwd.verify(password, hashed)
    except ValueError:
        return False


def create_access_token(user: User) -> str:
    now = utcnow()
    payload = {"sub": str(user.id), "role": user.role, "iat": now, "exp": now + timedelta(hours=settings.jwt_expire_hours)}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def _unauthorized(detail: str = "Please sign in again") -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, detail=detail, headers={"WWW-Authenticate": "Bearer"})


def user_from_token(token: str | None, db: Session) -> User:
    if not token:
        raise _unauthorized("Sign in to continue")
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Your session has expired - please sign in again")
    except jwt.PyJWTError:
        raise _unauthorized()
    user = db.get(User, int(payload.get("sub", 0)))
    if not user or not user.is_active:
        raise _unauthorized("This account is not active")
    return user


def get_current_user(token: str | None = Depends(_oauth2), db: Session = Depends(get_db)) -> User:
    return user_from_token(token, db)


def get_current_user_sse(access_token: str | None = Query(None), token: str | None = Depends(_oauth2),
                         db: Session = Depends(get_db)) -> User:
    """EventSource cannot send headers, so live streams also accept ?access_token=."""
    return user_from_token(token or access_token, db)


def require_role(min_role: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if ROLE_RANK.get(user.role, -1) < ROLE_RANK[min_role]:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail=f"This needs the {min_role} role")
        return user
    return checker


def has_role(user: User, min_role: str) -> bool:
    return ROLE_RANK.get(user.role, -1) >= ROLE_RANK[min_role]


# ---------------------------------------------------------------- device keys
def new_device_key() -> tuple[str, str, str]:
    """Returns (plain key shown once, sha256 hash stored, display prefix)."""
    key = "ssk_" + secrets.token_urlsafe(32)
    return key, hash_device_key(key), key[:10]


def hash_device_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def get_current_device(x_device_key: str | None = Header(None, alias="X-Device-Key"), db: Session = Depends(get_db)) -> Device:
    if not x_device_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Missing X-Device-Key header")
    device = db.query(Device).filter(Device.api_key_hash == hash_device_key(x_device_key)).first()
    if not device or not device.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Unknown or disabled device key")
    return device
