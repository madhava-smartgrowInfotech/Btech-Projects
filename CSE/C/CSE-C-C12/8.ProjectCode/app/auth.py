import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from app.config import settings

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False

def create_token(user_id: int, email: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "email": email, "exp": exp}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def decode_token(token: str):
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except Exception:
        return None
