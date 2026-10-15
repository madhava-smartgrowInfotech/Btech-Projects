from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import current_user, make_token, verify_password
from ..db import SessionLocal, User, audit

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginIn(BaseModel):
    email: str
    password: str


def user_out(u: User):
    return {"id": u.id, "email": u.email, "name": u.name, "role": u.role}


@router.post("/login")
def login(body: LoginIn):
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == body.email.strip().lower()).first()
        if not user or not verify_password(body.password, user.password_hash):
            audit(db, None, "login_failed", body.email[:80])
            raise HTTPException(401, "Wrong email or password")
        audit(db, user, "login")
        return {"token": make_token(user), "user": user_out(user)}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return user_out(user)
