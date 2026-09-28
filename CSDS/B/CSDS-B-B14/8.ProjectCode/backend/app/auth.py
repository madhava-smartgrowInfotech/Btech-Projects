from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import JWT_EXPIRE_MINUTES, JWT_SECRET
from .db import User, get_db

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is not set - copy .env.example to .env")

bearer = HTTPBearer(auto_error=False)


def hash_password(pw):
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def verify_password(pw, h):
    return bcrypt.checkpw(pw.encode(), h.encode())


def create_token(user):
    exp = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    return jwt.encode({"sub": user.email, "role": user.role, "exp": exp}, JWT_SECRET, algorithm="HS256")


def current_user(cred: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)):
    if not cred:
        raise HTTPException(401, "Not signed in")
    try:
        payload = jwt.decode(cred.credentials, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Session expired - sign in again")
    user = db.scalar(select(User).where(User.email == payload["sub"]))
    if not user:
        raise HTTPException(401, "Unknown user")
    return user


def require_role(*roles):
    def dep(user: User = Depends(current_user)):
        if user.role not in roles:
            raise HTTPException(403, f"This action needs the {' or '.join(roles)} role")
        return user

    return dep
