"""Password hashing helpers. Uses bcrypt via passlib's CryptContext."""
from __future__ import annotations

from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password. Never store plaintext passwords anywhere."""
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Check a plaintext password against a stored bcrypt hash."""
    try:
        return _pwd_context.verify(plain_password, password_hash)
    except Exception:
        # Malformed hash or other verification error -> treat as invalid, never raise to caller
        return False
