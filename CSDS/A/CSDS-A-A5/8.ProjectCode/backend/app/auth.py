"""Password hashing (bcrypt) and JWT bearer tokens."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import JWT_EXPIRE_MINUTES, JWT_SECRET
from .db import User, get_db

bearer = HTTPBearer(auto_error=False)


def hash_password(pw):
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def verify_password(pw, hashed):
    return bcrypt.checkpw(pw.encode(), hashed.encode())


def make_token(user):
    exp = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user.id), "exp": exp}, JWT_SECRET, algorithm="HS256")


def current_user(creds: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not creds:
        raise HTTPException(401, "Not signed in")
    try:
        uid = int(jwt.decode(creds.credentials, JWT_SECRET, algorithms=["HS256"])["sub"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Session expired - please sign in again")
    user = db.get(User, uid)
    if not user:
        raise HTTPException(401, "User not found")
    return user
