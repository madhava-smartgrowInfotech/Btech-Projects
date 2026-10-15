from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from cryptography.fernet import Fernet
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import FERNET_KEY, JWT_SECRET
from .db import SessionLocal, User

fernet = Fernet(FERNET_KEY.encode())
bearer = HTTPBearer(auto_error=False)


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def verify_password(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())


def encrypt_text(text: str) -> str:
    return fernet.encrypt(text.encode()).decode() if text else ""


def decrypt_text(token: str) -> str:
    return fernet.decrypt(token.encode()).decode() if token else ""


def make_token(user: User) -> str:
    payload = {"sub": str(user.id), "role": user.role, "exp": datetime.now(timezone.utc) + timedelta(hours=12)}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer)) -> User:
    if creds is None:
        raise HTTPException(401, "Not signed in")
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Session expired - please sign in again")
    with SessionLocal() as db:
        user = db.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(401, "Unknown user")
    return user


def require_role(*roles):
    def dep(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, f"This action needs the {' or '.join(roles)} role")
        return user

    return dep
