from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import api_error, get_current_user
from app.core.logging import get_logger
from app.core.security import create_access_token, hash_secret, verify_secret
from app.models import User
from app.schemas.auth import LoginIn, MeOut, PinChangeIn, RegisterIn, TokenOut
from app.services.accounts import create_account, me_payload

router = APIRouter(prefix="/auth", tags=["auth"])
log = get_logger("upi_guardian.auth")


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, db: Session = Depends(get_db)) -> dict:
    clauses = [User.phone == body.phone]
    if body.email:
        clauses.append(User.email == body.email.lower())
    if db.scalar(select(User.id).where(or_(*clauses))) is not None:
        raise api_error(status.HTTP_409_CONFLICT, "account_exists", "An account with this mobile number or email already exists.")
    user = create_account(
        db,
        full_name=body.full_name,
        phone=body.phone,
        email=body.email,
        password=body.password,
        pin=body.pin,
        language=body.language,
    )
    db.commit()
    db.refresh(user)
    log.info("user registered", extra={"user_id": user.id})
    return {"access_token": create_access_token(user.id, user.role), "user": me_payload(user)}


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)) -> dict:
    ident = body.identifier.strip().lower()
    user = db.scalar(select(User).where(or_(User.phone == ident, User.email == ident)))
    if user is None or not verify_secret(body.password, user.password_hash):
        raise api_error(status.HTTP_401_UNAUTHORIZED, "bad_credentials", "Mobile number / email or password is incorrect.")
    return {"access_token": create_access_token(user.id, user.role), "user": me_payload(user)}


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(get_current_user)) -> dict:
    return me_payload(user)


@router.post("/pin", status_code=status.HTTP_204_NO_CONTENT)
def change_pin(body: PinChangeIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> None:
    if not verify_secret(body.current_pin, user.pin_hash):
        raise api_error(status.HTTP_400_BAD_REQUEST, "wrong_pin", "Current PIN is incorrect.")
    user.pin_hash = hash_secret(body.new_pin)
    db.commit()
