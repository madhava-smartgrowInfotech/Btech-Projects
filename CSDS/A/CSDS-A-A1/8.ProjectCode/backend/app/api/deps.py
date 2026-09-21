"""Shared FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import NotFound, Unauthorized
from app.core.security import decode_access_token
from app.models import Policy, User

_bearer = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise Unauthorized("Please sign in to continue.")
    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise Unauthorized("Your session has expired. Please sign in again.", code="token_invalid")
    user = db.get(User, user_id)
    if user is None:
        raise Unauthorized("This account no longer exists.", code="token_invalid")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_owned_policy(db: Session, user: User, policy_id: int) -> Policy:
    policy = db.get(Policy, policy_id)
    if policy is None or policy.owner_id != user.id:
        raise NotFound("Policy not found.")
    return policy
