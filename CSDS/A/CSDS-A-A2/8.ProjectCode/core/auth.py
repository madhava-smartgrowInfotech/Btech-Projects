"""Password hashing (PBKDF2-HMAC-SHA256) and JWT issue / verification."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt

import config


# --------------------------------------------------------------------------- #
# Passwords
# --------------------------------------------------------------------------- #
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, config.PBKDF2_ITERATIONS)
    return "pbkdf2$%d$%s$%s" % (
        config.PBKDF2_ITERATIONS,
        base64.b64encode(salt).decode(),
        base64.b64encode(digest).decode(),
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iterations, salt_b64, digest_b64 = stored.split("$")
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
    except (ValueError, TypeError):
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations))
    return hmac.compare_digest(digest, expected)


# --------------------------------------------------------------------------- #
# JWT
# --------------------------------------------------------------------------- #
@dataclass
class TokenClaims:
    user_id: int
    role: str
    username: str
    full_name: str
    roll_number: str | None
    device_hash: str
    expires_at: datetime


def issue_token(user, device_hash: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "username": user.username,
        "name": user.full_name,
        "roll": user.roll_number,
        "dev": device_hash,
        "iat": now,
        "exp": now + timedelta(minutes=config.JWT_EXPIRY_MINUTES),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


class TokenError(Exception):
    pass


def verify_token(token: str, device_hash: str | None = None) -> TokenClaims:
    """Decode a JWT; optionally make sure it is presented from the same device it was issued to."""
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("Your login has expired. Please sign in again.") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError("Invalid authentication token.") from exc

    if device_hash is not None and payload.get("dev") != device_hash:
        raise TokenError("This login token was issued to a different device.")

    return TokenClaims(
        user_id=int(payload["sub"]),
        role=payload["role"],
        username=payload["username"],
        full_name=payload["name"],
        roll_number=payload.get("roll"),
        device_hash=payload["dev"],
        expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
    )
