from fastapi import APIRouter
from sqlalchemy import select

from app.core.config import get_settings
from app.core.deps import DB, CurrentUser
from app.core.errors import AppError
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.models._common import utcnow
from app.models.user import ROLE_INVIGILATOR, STATUS_ACTIVE, STATUS_PENDING
from app.schemas.auth import LoginIn, RegisterIn, TokenOut, UserOut
from app.services import audit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut, summary="Sign in and receive an access token")
def login(body: LoginIn, db: DB) -> TokenOut:
    user = db.scalar(select(User).where(User.email == body.email))
    if user is None or not verify_password(body.password, user.password_hash):
        raise AppError("Email or password is incorrect.", 401)
    if user.status == STATUS_PENDING:
        raise AppError("Your account is waiting for an administrator to approve it.", 403)
    if user.status != STATUS_ACTIVE:
        raise AppError("This account has been disabled. Contact your administrator.", 403)
    user.last_login_at = utcnow()
    db.commit()
    token, expires = create_access_token(user.id, user.role)
    return TokenOut(access_token=token, expires_at=expires, user=UserOut.model_validate(user))


@router.post("/register", response_model=UserOut, status_code=201,
             summary="Request an invigilator account (an administrator approves it)")
def register(body: RegisterIn, db: DB) -> UserOut:
    if db.scalar(select(User).where(User.email == body.email)):
        raise AppError("An account with this email already exists.", 409)
    user = User(email=body.email, full_name=body.full_name, role=ROLE_INVIGILATOR, status=STATUS_PENDING,
                password_hash=hash_password(body.password))
    db.add(user)
    db.flush()
    audit.record(db, "user.registered", f"{user.full_name} requested an invigilator account", details={"email": user.email})
    db.commit()
    return UserOut.model_validate(user)


@router.get("/me", response_model=UserOut, summary="The signed-in user")
def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)


@router.get("/demo", summary="Demo accounts offered on the sign-in page (only when demo accounts are enabled)")
def demo_accounts(db: DB) -> dict:
    settings = get_settings()
    if not settings.seed_demo_users:
        return {"enabled": False, "password": None, "accounts": []}
    emails = [settings.demo_admin_email, settings.demo_invigilator_email]
    users = {u.email: u for u in db.scalars(select(User).where(User.email.in_(emails), User.status == STATUS_ACTIVE))}
    accounts = [{"role": users[e].role, "email": e, "name": users[e].full_name} for e in emails if e in users]
    password = settings.demo_password if not settings.is_production else None
    if password and not any(verify_password(password, users[e].password_hash) for e in emails if e in users):
        password = None  # the demo password was changed, so do not advertise it
    return {"enabled": bool(accounts), "password": password, "accounts": accounts}
