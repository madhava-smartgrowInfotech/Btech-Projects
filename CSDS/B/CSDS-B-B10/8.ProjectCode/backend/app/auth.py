import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .db import SessionLocal, User, get_db

SECRET = os.getenv("JWT_SECRET", "")
if not SECRET or SECRET.startswith("change-me"):
    raise RuntimeError("Set JWT_SECRET in .env (see .env.example)")
EXPIRE_MIN = int(os.getenv("JWT_EXPIRE_MINUTES", "720"))

router = APIRouter(prefix="/api/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)


class RegisterIn(BaseModel):
    name: str
    email: str
    password: str


class LoginIn(BaseModel):
    email: str
    password: str


def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def make_token(user: User) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MIN)
    return jwt.encode({"sub": str(user.id), "exp": exp}, SECRET, algorithm="HS256")


def user_from_token(token: str, db: Session) -> User:
    try:
        uid = int(jwt.decode(token, SECRET, algorithms=["HS256"])["sub"])
    except Exception:
        raise HTTPException(401, "Session expired - please sign in again")
    user = db.get(User, uid)
    if not user:
        raise HTTPException(401, "Account not found")
    return user


def current_user(cred: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not cred:
        raise HTTPException(401, "Not signed in")
    return user_from_token(cred.credentials, db)


def _out(user: User):
    return {"token": make_token(user), "user": {"id": user.id, "name": user.name, "email": user.email}}


@router.post("/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    if "@" not in email or len(body.password) < 6 or not body.name.strip():
        raise HTTPException(400, "Enter a name, a valid email and a password of at least 6 characters")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(400, "An account with this email already exists")
    user = User(email=email, name=body.name.strip(), password_hash=hash_pw(body.password))
    db.add(user)
    db.commit()
    return _out(user)


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.strip().lower()).first()
    if not user or not bcrypt.checkpw(body.password.encode(), user.password_hash.encode()):
        raise HTTPException(401, "Wrong email or password")
    return _out(user)


@router.get("/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "name": user.name, "email": user.email}


def seed_demo_user():
    email = os.getenv("DEMO_EMAIL", "demo@skycipher.app").lower()
    pw = os.getenv("DEMO_PASSWORD", "SkyCipher@2026")
    with SessionLocal() as db:
        if not db.query(User).filter(User.email == email).first():
            db.add(User(email=email, name="Demo Operator", password_hash=hash_pw(pw)))
            db.commit()
