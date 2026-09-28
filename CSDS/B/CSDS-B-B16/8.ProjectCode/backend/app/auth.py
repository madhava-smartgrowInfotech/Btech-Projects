from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import DEMO_PASSWORD, JWT_EXPIRE_MINUTES, JWT_SECRET
from .db import SessionLocal, User, get_db

bearer = HTTPBearer(auto_error=False)


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def verify_password(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())


def create_token(user: User) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user.id), "role": user.role, "exp": exp}, JWT_SECRET, algorithm="HS256")


def current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in")
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired, please sign in again")
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user


def user_dict(u: User) -> dict:
    return {"id": u.id, "email": u.email, "name": u.name, "role": u.role}


def seed_users():
    demo = [
        ("clinician@retinaguard.local", "Demo Clinician", "clinician"),
        ("technician@retinaguard.local", "Demo Technician", "technician"),
    ]
    with SessionLocal() as db:
        for email, name, role in demo:
            if not db.query(User).filter_by(email=email).first():
                db.add(User(email=email, name=name, role=role, password_hash=hash_password(DEMO_PASSWORD)))
        db.commit()
