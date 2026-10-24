"""Demo sign-in: one operator account from .env and a small HS256 token (stdlib only)."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

from fastapi import Header, HTTPException

from . import config


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _sign(msg: str) -> str:
    return _b64(hmac.new(config.JWT_SECRET.encode(), msg.encode(), hashlib.sha256).digest())


def make_token(email: str, name: str) -> str:
    head = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    body = _b64(json.dumps({"sub": email, "name": name, "exp": int(time.time()) + config.TOKEN_HOURS * 3600}).encode())
    return f"{head}.{body}.{_sign(head + '.' + body)}"


def read_token(token: str) -> dict | None:
    try:
        head, body, sig = token.split(".")
        if not hmac.compare_digest(sig, _sign(head + "." + body)):
            return None
        data = json.loads(_unb64(body))
        return data if data.get("exp", 0) > time.time() else None
    except Exception:
        return None


def check_credentials(email: str, password: str) -> bool:
    ok_user = hmac.compare_digest(email.strip().lower().encode(), config.DEMO_EMAIL.lower().encode())
    ok_pass = hmac.compare_digest(password.encode(), config.DEMO_PASSWORD.encode())
    return ok_user and ok_pass


def current_user(authorization: str | None = Header(default=None)) -> dict:
    if authorization and authorization.lower().startswith("bearer "):
        data = read_token(authorization[7:].strip())
        if data:
            return data
    raise HTTPException(401, detail={"message": "Sign in required.", "hint": "Your session may have expired - sign in again."})
