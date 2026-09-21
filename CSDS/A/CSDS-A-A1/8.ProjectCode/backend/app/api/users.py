from __future__ import annotations

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.core.config import LANGUAGE_NAMES, get_settings
from app.core.errors import AppError
from app.core.security import hash_password, verify_password
from app.models import User
from app.schemas.auth import PasswordChange, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.patch("/me", response_model=UserOut)
def update_me(body: UserUpdate, user: CurrentUser, db: DbSession) -> User:
    if body.full_name is not None:
        user.full_name = body.full_name.strip()
    if body.language is not None:
        if body.language not in get_settings().supported_languages:
            raise AppError("This language is not available.", code="language_unsupported")
        user.language = body.language
    if body.theme is not None:
        user.theme = body.theme
    db.commit()
    db.refresh(user)
    return user


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(body: PasswordChange, user: CurrentUser, db: DbSession) -> None:
    if not verify_password(body.current_password, user.password_hash):
        raise AppError("Your current password is incorrect.", code="bad_password")
    user.password_hash = hash_password(body.new_password)
    db.commit()


@router.get("/languages")
def languages() -> list[dict[str, str]]:
    return [{"code": code, "name": LANGUAGE_NAMES[code]} for code in get_settings().supported_languages]
