from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import create_token, current_user, user_dict, verify_password
from ..db import User, get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginIn(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=body.email.strip().lower()).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Wrong email or password")
    return {"token": create_token(user), "user": user_dict(user)}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return user_dict(user)
