from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.db import get_db, utcnow
from ..core.logging import log_event
from ..core.security import create_access_token, get_current_user, hash_password, verify_password
from ..models import User
from ..schemas.auth import LoginIn, ProfileUpdate, RegisterIn, TokenOut, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])
log = logging.getLogger("signalscout.auth")


def _token_response(user: User) -> TokenOut:
    return TokenOut(access_token=create_access_token(user), expires_in=settings.jwt_expire_hours * 3600,
                    user=UserOut.model_validate(user))


def _authenticate(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(func.lower(User.email) == email.lower()).first()
    if not user or not verify_password(password, user.password_hash):
        log_event(log, "login failed", logging.WARNING, email=email)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Email or password is incorrect")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="This account has been disabled by an administrator")
    user.last_login_at = utcnow()
    db.commit()
    log_event(log, "login", user_id=user.id, role=user.role)
    return user


@router.post("/register", response_model=TokenOut, status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)) -> TokenOut:
    if db.query(User).filter(func.lower(User.email) == body.email.lower()).first():
        raise HTTPException(status.HTTP_409_CONFLICT, detail="An account with this email already exists")
    user = User(email=body.email.lower(), name=body.name, role="user", password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    log_event(log, "registered", user_id=user.id)
    return _token_response(user)


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    return _token_response(_authenticate(db, body.email, body.password))


@router.post("/token", response_model=TokenOut, include_in_schema=True, summary="Login (form) - used by the /docs Authorize button")
def login_form(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> TokenOut:
    return _token_response(_authenticate(db, form.username, form.password))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.patch("/me", response_model=UserOut)
def update_me(body: ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
    if body.name is not None:
        user.name = " ".join(body.name.split())
    if body.notify_email is not None:
        user.notify_email = body.notify_email
    if body.new_password:
        if user.is_demo:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Demo account passwords cannot be changed")
        if not body.current_password or not verify_password(body.current_password, user.password_hash):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
        user.password_hash = hash_password(body.new_password)
    db.commit()
    db.refresh(user)
    return user
