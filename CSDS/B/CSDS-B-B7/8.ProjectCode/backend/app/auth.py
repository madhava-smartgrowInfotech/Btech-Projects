"""JWT login and role checks."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import JWT_EXPIRE_HOURS, JWT_SECRET
from .db import User, get_db

bearer = HTTPBearer(auto_error=False)


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(user: User) -> str:
    payload = {"sub": str(user.id), "role": user.role,
               "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not creds:
        raise HTTPException(401, "Not signed in")
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Session expired - please sign in again")
    user = db.scalar(select(User).where(User.id == int(payload["sub"])))
    if not user:
        raise HTTPException(401, "User not found")
    return user


def require_admin(user: User = Depends(current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(403, "Only administrators can do this")
    return user
