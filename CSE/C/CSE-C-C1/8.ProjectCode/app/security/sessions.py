import secrets
import time
from typing import Optional

SESSION_COOKIE = "aegis_session"
CSRF_COOKIE = "aegis_csrf"

# In-memory session store (server-side)
_sessions: dict[str, dict] = {}

def create_session(user_id: int, username: str, role: str) -> str:
    token = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(24)
    _sessions[token] = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "csrf": csrf,
        "created": time.time(),
    }
    return token

def get_session(token: str) -> Optional[dict]:
    return _sessions.get(token)

def destroy_session(token: str):
    _sessions.pop(token, None)

def get_csrf_for_session(token: str) -> Optional[str]:
    s = _sessions.get(token)
    return s["csrf"] if s else None
