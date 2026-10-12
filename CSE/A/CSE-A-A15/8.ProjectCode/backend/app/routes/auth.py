from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import check_pw, current_user, hash_pw, make_token
from ..db import User, get_db, log_op

router = APIRouter(prefix="/api/auth", tags=["auth"])


class Creds(BaseModel):
    username: str = Field(min_length=3, max_length=40, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=72)


@router.post("/register")
def register(body: Creds, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.username == body.username)):
        raise HTTPException(409, "That username is taken")
    user = User(username=body.username, pw_hash=hash_pw(body.password))
    db.add(user)
    db.commit()
    log_op(db, user.id, "register", True, {})
    return {"token": make_token(user), "username": user.username}


@router.post("/login")
def login(body: Creds, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == body.username))
    if not user or not check_pw(body.password, user.pw_hash):
        raise HTTPException(401, "Wrong username or password")
    log_op(db, user.id, "login", True, {})
    return {"token": make_token(user), "username": user.username}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "username": user.username}
