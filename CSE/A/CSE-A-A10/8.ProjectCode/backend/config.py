"""Settings read from the project-level .env (with safe defaults so a fresh checkout still runs)."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_env() -> None:
    f = ROOT / ".env"
    if not f.exists():
        return
    for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env()

BACKEND_PORT = int(os.environ.get("BACKEND_PORT", "8310"))
FRONTEND_PORT = int(os.environ.get("FRONTEND_PORT", "5310"))
# A placeholder in .env.example must not be used as a real signing key.
_secret = os.environ.get("JWT_SECRET", "")
JWT_SECRET = _secret if len(_secret) >= 32 and not _secret.startswith("generate-") else "flowsense-local-development-signing-key"
DEMO_EMAIL = os.environ.get("DEMO_EMAIL", "operator@flowsense.app")
DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "Flow@1234")
DEMO_NAME = os.environ.get("DEMO_NAME", "Control Room Operator")
TOKEN_HOURS = 12
