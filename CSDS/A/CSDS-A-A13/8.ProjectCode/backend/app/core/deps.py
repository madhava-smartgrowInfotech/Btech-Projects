"""Request dependencies: database session and the signed-in user."""
from __future__ import annotations

from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import AppError
from app.core.security import decode_access_token
from app.models import User
from app.models.user import STATUS_ACTIVE

_bearer = HTTPBearer(auto_error=False, description="Paste the access_token from POST /api/auth/login")

DB = Annotated[Session, Depends(get_db)]


def get_current_user(db: DB, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]) -> User:
    if credentials is None:
        raise AppError("Please sign in to continue.", 401)
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise AppError("Your session has expired. Please sign in again.", 401)
    except jwt.InvalidTokenError:
        raise AppError("Your sign-in is not valid. Please sign in again.", 401)
    user = db.get(User, int(payload.get("sub", 0)))
    if user is None or user.status != STATUS_ACTIVE:
        raise AppError("This account is not active.", 401)
    return user


def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if not user.is_admin:
        raise AppError("Only administrators can do this.", 403)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_admin)]
