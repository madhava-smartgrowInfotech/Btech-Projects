from fastapi import APIRouter
from sqlalchemy import func, select

from app.core.deps import DB, AdminUser
from app.core.errors import AppError, NotFound
from app.core.security import hash_password
from app.models import User
from app.models.user import ROLE_ADMIN, STATUS_ACTIVE
from app.schemas.auth import UserCreateIn, UserOut, UserUpdateIn
from app.services import audit

router = APIRouter(prefix="/users", tags=["team"])


@router.get("", response_model=list[UserOut], summary="All accounts")
def list_users(db: DB, _: AdminUser) -> list[UserOut]:
    users = db.scalars(select(User).order_by(User.status.desc(), User.role, User.full_name)).all()
    return [UserOut.model_validate(u) for u in users]


@router.post("", response_model=UserOut, status_code=201, summary="Create an active account")
def create_user(body: UserCreateIn, db: DB, admin: AdminUser) -> UserOut:
    if db.scalar(select(User).where(User.email == body.email)):
        raise AppError("An account with this email already exists.", 409)
    user = User(email=body.email, full_name=body.full_name, role=body.role, status=STATUS_ACTIVE,
                password_hash=hash_password(body.password))
    db.add(user)
    db.flush()
    audit.record(db, "user.created", f"{admin.full_name} added {user.full_name} as {user.role}", actor=admin)
    db.commit()
    return UserOut.model_validate(user)


@router.patch("/{user_id}", response_model=UserOut, summary="Approve, disable, change role or reset password")
def update_user(user_id: int, body: UserUpdateIn, db: DB, admin: AdminUser) -> UserOut:
    user = db.get(User, user_id)
    if user is None:
        raise NotFound("Account")
    losing_admin = user.role == ROLE_ADMIN and (
        (body.role and body.role != ROLE_ADMIN) or (body.status and body.status != STATUS_ACTIVE))
    if losing_admin:
        active_admins = db.scalar(select(func.count()).select_from(User).where(
            User.role == ROLE_ADMIN, User.status == STATUS_ACTIVE))
        if active_admins <= 1:
            raise AppError("At least one active administrator is required.", 409)
    changes = []
    if body.full_name:
        user.full_name = " ".join(body.full_name.split())
        changes.append("name")
    if body.role and body.role != user.role:
        user.role = body.role
        changes.append(f"role={body.role}")
    if body.status and body.status != user.status:
        changes.append(f"status={body.status}")
        user.status = body.status
    if body.password:
        user.password_hash = hash_password(body.password)
        changes.append("password reset")
    if changes:
        audit.record(db, "user.updated", f"{admin.full_name} updated {user.full_name}: {', '.join(changes)}", actor=admin)
    db.commit()
    return UserOut.model_validate(user)
