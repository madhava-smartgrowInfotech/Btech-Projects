"""Creates .env from .env.example with a freshly generated JWT secret (never overwrites)."""
from __future__ import annotations

import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    env = ROOT / ".env"
    if env.exists():
        print("[ok] .env already exists - leaving it unchanged")
        return 0
    template = (ROOT / ".env.example").read_text(encoding="utf-8")
    content = template.replace(
        "JWT_SECRET=change-me-run-setup-bat-to-generate-one", f"JWT_SECRET={secrets.token_urlsafe(48)}"
    )
    env.write_text(content, encoding="utf-8", newline="\n")
    print("[ok] created .env with a new random JWT secret")
    return 0


if __name__ == "__main__":
    sys.exit(main())
