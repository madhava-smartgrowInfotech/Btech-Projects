"""Environment-driven settings. Reads .env, falling back to .env.example so a fresh checkout runs."""
import os
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]


def _load() -> dict:
    vals = {}
    for name in (".env.example", ".env"):
        p = ROOT / name
        if p.exists():
            vals.update({k: v for k, v in dotenv_values(p).items() if v is not None})
    vals.update({k: v for k, v in os.environ.items() if k in vals or k in ("DATABASE_URL", "JWT_SECRET")})
    return vals


_env = _load()

BACKEND_PORT = int(_env.get("BACKEND_PORT", 8309))
FRONTEND_PORT = int(_env.get("FRONTEND_PORT", 5309))
JWT_SECRET = _env.get("JWT_SECRET", "")
if not JWT_SECRET or JWT_SECRET.startswith("generate-a-random"):
    JWT_SECRET = "botgraph-local-dev-secret-0123456789abcdef"
JWT_HOURS = int(_env.get("JWT_HOURS", 12))
_db = _env.get("DATABASE_URL", "sqlite:///./data/app.db")
if _db.startswith("sqlite:///./"):
    _db = "sqlite:///" + (ROOT / _db[len("sqlite:///./"):]).as_posix()
DATABASE_URL = _db
