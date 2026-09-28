from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import JWT_SECRET
from .db import User, get_db

bearer = HTTPBearer(auto_error=False)
ROLES = ("candidate", "recruiter", "career", "expert")


def hash_password(pw):
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt(rounds=10)).decode()


def check_password(pw, h):
    try:
        return bcrypt.checkpw(pw.encode(), h.encode())
    except ValueError:
        return False


def make_token(user):
    exp = datetime.now(timezone.utc) + timedelta(days=7)
    return jwt.encode({"sub": str(user.id), "role": user.role, "exp": exp}, JWT_SECRET, algorithm="HS256")


def current_user(cred: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not cred:
        raise HTTPException(401, "Not signed in")
    try:
        data = jwt.decode(cred.credentials, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Session expired - please sign in again")
    user = db.get(User, int(data["sub"]))
    if not user:
        raise HTTPException(401, "Account not found")
    return user


def require(*roles):
    def dep(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, f"This action needs one of: {', '.join(roles)}")
        return user
    return dep


def public_user(u: User):
    return {"id": u.id, "name": u.name, "email": u.email, "role": u.role, "level": u.level,
            "rating": u.rating, "job_ready": u.job_ready, "target_role": u.target_role, "is_sample": u.is_sample}
