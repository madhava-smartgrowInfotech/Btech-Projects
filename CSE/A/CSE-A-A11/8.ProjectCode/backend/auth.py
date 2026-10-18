"""Small account layer: SQLite users, bcrypt password hashes, signed JWT bearer tokens.

The product itself had no login. This is additive and lives next to the data folder, so the Streamlit app and
the `autosecai` package are untouched. A demo account is created on first start so the UI can be walked end to end.
"""
from __future__ import annotations

import hashlib
import os
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "app.db"
# hashed so the HMAC key is always >= 32 bytes, whatever length JWT_SECRET has in .env
SECRET = hashlib.sha256((os.environ.get("JWT_SECRET") or "change-me-on-first-run").encode()).hexdigest()
TOKEN_HOURS = 12

DEMO_EMAIL = "demo@autosecai.dev"
DEMO_PASSWORD = "Demo@1234"
DEMO_NAME = "Demo Reviewer"

EMAIL_RX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
bearer = HTTPBearer(auto_error=False)


def _conn() -> sqlite3.Connection:
    DB.parent.mkdir(exist_ok=True)
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
        password_hash BLOB NOT NULL, created TEXT NOT NULL)""")
    return c


def _hash(password: str) -> bytes:
    return bcrypt.hashpw(password.encode()[:72], bcrypt.gensalt(rounds=10))


def _public(row: sqlite3.Row) -> dict:
    return dict(id=row["id"], email=row["email"], name=row["name"], created=row["created"],
                is_demo=row["email"] == DEMO_EMAIL)


def seed_demo() -> None:
    with _conn() as c:
        if not c.execute("SELECT 1 FROM users WHERE email=?", (DEMO_EMAIL,)).fetchone():
            c.execute("INSERT INTO users(email,name,password_hash,created) VALUES (?,?,?,?)",
                      (DEMO_EMAIL, DEMO_NAME, _hash(DEMO_PASSWORD), datetime.now(timezone.utc).isoformat(timespec="seconds")))


def register(name: str, email: str, password: str) -> dict:
    name, email = name.strip(), email.strip().lower()
    if len(name) < 2:
        raise HTTPException(422, "Enter your name (at least 2 characters).")
    if not EMAIL_RX.match(email):
        raise HTTPException(422, "Enter a valid email address.")
    if len(password) < 8:
        raise HTTPException(422, "Password must be at least 8 characters.")
    with _conn() as c:
        if c.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone():
            raise HTTPException(409, "An account with that email already exists. Sign in instead.")
        cur = c.execute("INSERT INTO users(email,name,password_hash,created) VALUES (?,?,?,?)",
                        (email, name, _hash(password), datetime.now(timezone.utc).isoformat(timespec="seconds")))
        row = c.execute("SELECT * FROM users WHERE id=?", (cur.lastrowid,)).fetchone()
    return _public(row)


def authenticate(email: str, password: str) -> dict:
    with _conn() as c:
        row = c.execute("SELECT * FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
    if not row or not bcrypt.checkpw(password.encode()[:72], row["password_hash"]):
        raise HTTPException(401, "Email or password is incorrect.")
    return _public(row)


def make_token(user: dict) -> str:
    now = int(time.time())
    return jwt.encode({"sub": str(user["id"]), "iat": now, "exp": now + TOKEN_HOURS * 3600}, SECRET, algorithm="HS256")


def current_user(cred: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    if cred is None:
        raise HTTPException(401, "Sign in to continue.")
    try:
        data = jwt.decode(cred.credentials, SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Your session has expired. Sign in again.")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Your session is not valid. Sign in again.")
    with _conn() as c:
        row = c.execute("SELECT * FROM users WHERE id=?", (int(data["sub"]),)).fetchone()
    if not row:
        raise HTTPException(401, "This account no longer exists. Sign in again.")
    return _public(row)
