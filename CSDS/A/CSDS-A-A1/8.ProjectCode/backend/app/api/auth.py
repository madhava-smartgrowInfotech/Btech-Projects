from __future__ import annotations

from fastapi import APIRouter, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.core.errors import Conflict, Unauthorized
from app.core.logging import get_logger, log_event
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas.auth import LoginIn, RegisterIn, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])
log = get_logger("auth")


def _token_for(user: User) -> TokenOut:
    token, expires = create_access_token(user.id)
    return TokenOut(access_token=token, expires_at=expires, user=UserOut.model_validate(user))


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, db: DbSession) -> TokenOut:
    email = body.email.lower()
    if db.scalar(select(User).where(func.lower(User.email) == email)):
        raise Conflict("An account with this email already exists. Try signing in instead.", code="email_taken")
    user = User(email=email, full_name=body.full_name, password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    log_event(log, "user_registered", user_id=user.id)
    return _token_for(user)


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: DbSession) -> TokenOut:
    user = db.scalar(select(User).where(func.lower(User.email) == body.email.lower()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise Unauthorized("Email or password is incorrect.", code="bad_credentials")
    log_event(log, "user_login", user_id=user.id)
    return _token_for(user)


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> User:
    return user
