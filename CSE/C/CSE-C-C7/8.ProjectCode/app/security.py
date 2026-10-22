from passlib.context import CryptContext
import secrets

pwd_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto", pbkdf2_sha256__rounds=29000)

def hash_password(pw: str) -> str:
    # bcrypt max 72 bytes
    b = pw.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    return pwd_ctx.hash(b)

def verify_password(pw: str, h: str) -> bool:
    try:
        b = pw.encode("utf-8")[:72].decode("utf-8", errors="ignore")
        return pwd_ctx.verify(b, h)
    except Exception:
        return False

def new_token() -> str:
    return secrets.token_urlsafe(32)
