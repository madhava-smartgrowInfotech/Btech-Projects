"""Auth endpoints: register / login / me / keys."""

from fastapi import APIRouter, Depends, Request, status
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import check_rate_limit, get_client_ip, get_current_user
from backend.app.core.config import get_settings
from backend.app.core.security import create_access_token, hash_password, verify_password
from backend.app.db.database import get_db
from backend.app.db.models import User
from backend.app.schemas.schemas import (
    LoginRequest, RegisterRequest, TokenResponse, UpdateKeysRequest, UserOut,
)
from backend.app.services import audit_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id, name=user.name, email=user.email, role=user.role,
        public_key=user.public_key, has_private_key=bool(user.encrypted_private_key),
        is_active=user.is_active, created_at=user.created_at,
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        audit_service.record_event(db, action="register", success=False, details=f"duplicate email: {email}",
                                   ip_address=get_client_ip(request))
        raise HTTPException(status_code=400, detail="An account with this email already exists")
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    user = User(
        name=payload.name.strip()[:120],
        email=email,
        password_hash=hash_password(payload.password),
        role="user",
        public_key=payload.public_key,
        encrypted_private_key=payload.encrypted_private_key,
        private_key_salt=payload.private_key_salt,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    audit_service.record_event(db, action="register", success=True, user_id=user.id,
                               details=f"user registered: {email}", ip_address=get_client_ip(request))
    return _user_out(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    settings = get_settings()
    email = payload.email.strip().lower()
    ip = get_client_ip(request)
    check_rate_limit(f"login:{ip}:{email}", settings.LOGIN_MAX_ATTEMPTS, settings.LOGIN_WINDOW_SECONDS)
    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        audit_service.record_event(db, action="login_failure", success=False,
                                   user_id=user.id if user else None,
                                   details=f"failed login for: {email}", ip_address=ip)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(str(user.id))
    audit_service.record_event(db, action="login_success", success=True, user_id=user.id,
                               details=f"login: {email}", ip_address=ip)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)):
    return _user_out(current)


@router.put("/keys", response_model=UserOut)
def update_keys(payload: UpdateKeysRequest, request: Request,
                db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    current.public_key = payload.public_key
    current.encrypted_private_key = payload.encrypted_private_key
    current.private_key_salt = payload.private_key_salt
    db.commit()
    db.refresh(current)
    audit_service.record_event(db, action="keys_updated", success=True, user_id=current.id,
                               details="user key material updated", ip_address=get_client_ip(request))
    return _user_out(current)


@router.get("/key-bundle")
def key_bundle(current: User = Depends(get_current_user)):
    if not current.encrypted_private_key:
        raise HTTPException(status_code=404, detail="No encrypted private key stored")
    return {"bundle": current.encrypted_private_key}


@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    audit_service.record_event(db, action="logout", success=True, user_id=current.id,
                               details=f"logout: {current.email}", ip_address=get_client_ip(request))
    return {"message": "Logged out"}
