"""Small stateless demo login: a signed, expiring bearer token (stdlib only)."""
import base64
import hashlib
import hmac
import json
import time

from fastapi import Header, HTTPException

from . import config


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _sign(body: str) -> str:
    return _b64(hmac.new(config.AUTH_SECRET.encode(), body.encode(), hashlib.sha256).digest())


def check_credentials(email: str, password: str) -> bool:
    ok_email = hmac.compare_digest(email.strip().lower().encode(), config.DEMO_EMAIL.lower().encode())
    ok_pw = hmac.compare_digest(password.encode(), config.DEMO_PASSWORD.encode())
    return ok_email and ok_pw


def make_token(email: str) -> str:
    body = _b64(json.dumps({"sub": email, "exp": int(time.time()) + config.TOKEN_TTL_SECONDS}).encode())
    return f"{body}.{_sign(body)}"


def read_token(token: str) -> dict | None:
    try:
        body, sig = token.split(".", 1)
        if not hmac.compare_digest(sig, _sign(body)):
            return None
        data = json.loads(_unb64(body))
        return data if data.get("exp", 0) > time.time() else None
    except Exception:
        return None


def require_user(authorization: str | None = Header(default=None)) -> dict:
    """FastAPI dependency: 401 unless a valid bearer token is supplied."""
    scheme, _, token = (authorization or "").partition(" ")
    data = read_token(token) if scheme.lower() == "bearer" else None
    if not data:
        raise HTTPException(status_code=401, detail="Your session has expired. Please sign in again.")
    return data
