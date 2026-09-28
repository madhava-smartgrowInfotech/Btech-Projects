from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import create_token, current_user, verify_password
from ..db import User, get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginIn(BaseModel):
    email: str
    password: str


def user_out(u: User):
    return {"id": u.id, "email": u.email, "name": u.name, "role": u.role}


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return {"token": create_token(user), "user": user_out(user)}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return user_out(user)
