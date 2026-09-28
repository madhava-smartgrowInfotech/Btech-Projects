from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import create_token, current_user, hash_password, verify_password
from ..db import User, get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterIn(BaseModel):
    name: str
    email: str
    password: str


class LoginIn(BaseModel):
    email: str
    password: str


def user_out(u):
    return {"id": u.id, "name": u.name, "email": u.email}


@router.post("/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    if "@" not in email or len(body.password) < 6 or not body.name.strip():
        raise HTTPException(400, "Enter a name, a valid email and a password of at least 6 characters")
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(400, "An account with this email already exists")
    u = User(name=body.name.strip(), email=email, password_hash=hash_password(body.password))
    db.add(u)
    db.commit()
    return {"token": create_token(u), "user": user_out(u)}


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    u = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    if not u or not verify_password(body.password, u.password_hash):
        raise HTTPException(401, "Wrong email or password")
    return {"token": create_token(u), "user": user_out(u)}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return user_out(user)
