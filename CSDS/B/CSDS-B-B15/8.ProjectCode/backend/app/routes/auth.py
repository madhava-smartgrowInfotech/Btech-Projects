from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import check_password, current_user, hash_password, make_token, user_dict
from ..db import User, get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginIn(BaseModel):
    email: str
    password: str


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=160)
    password: str = Field(min_length=6, max_length=100)
    age: int | None = Field(default=None, ge=0, le=120)
    gender: str | None = Field(default=None, pattern="^[MF]$")
    phone: str | None = None


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    if not user or not check_password(body.password, user.password_hash):
        raise HTTPException(401, "Wrong email or password")
    return {"token": make_token(user), "user": user_dict(user)}


@router.post("/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    if "@" not in email:
        raise HTTPException(422, "Enter a valid email")
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "An account with this email already exists")
    user = User(name=body.name.strip(), email=email, password_hash=hash_password(body.password), role="patient",
                age=body.age, gender=body.gender, phone=body.phone)
    db.add(user)
    db.commit()
    return {"token": make_token(user), "user": user_dict(user)}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return user_dict(user)
