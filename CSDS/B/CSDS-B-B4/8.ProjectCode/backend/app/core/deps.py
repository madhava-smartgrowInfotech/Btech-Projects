"""FastAPI dependencies: database session, current user, admin guard."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decode_access_token
from app.models import User

_bearer = HTTPBearer(auto_error=False)


def api_error(status_code: int, code: str, message: str) -> HTTPException:
    """Errors carry a stable code (translated in the UI) and an English message."""
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def user_from_token(token: str, db: Session) -> User | None:
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except Exception:
        return None
    return db.get(User, user_id)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise api_error(status.HTTP_401_UNAUTHORIZED, "auth_required", "Please sign in to continue.")
    user = user_from_token(creds.credentials, db)
    if user is None:
        raise api_error(status.HTTP_401_UNAUTHORIZED, "auth_invalid", "Your session has expired. Please sign in again.")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise api_error(status.HTTP_403_FORBIDDEN, "admin_only", "This area is for fraud-risk team members only.")
    return user
