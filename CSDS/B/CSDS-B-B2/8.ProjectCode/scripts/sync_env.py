"""Create .env from .env.example, or add any keys that are new in .env.example to an existing .env.

Existing values are never changed. A placeholder JWT_SECRET is replaced with a random one.
Used by setup.bat; safe to run any time: python scripts/sync_env.py
"""
from __future__ import annotations

import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE, ENV = ROOT / ".env.example", ROOT / ".env"
PLACEHOLDER = "replace-with-a-long-random-string"


def keys_of(text: str) -> set[str]:
    return {line.split("=", 1)[0].strip() for line in text.splitlines()
            if line.strip() and not line.lstrip().startswith("#") and "=" in line}


def main() -> None:
    example = EXAMPLE.read_text(encoding="utf-8")
    if not ENV.exists():
        ENV.write_text(example.replace(PLACEHOLDER, secrets.token_urlsafe(48)), encoding="utf-8")
        print(".env created from .env.example")
        return
    current = ENV.read_text(encoding="utf-8")
    if f"JWT_SECRET={PLACEHOLDER}" in current:
        current = current.replace(f"JWT_SECRET={PLACEHOLDER}", "JWT_SECRET=" + secrets.token_urlsafe(48))
    missing = [line for line in example.splitlines()
               if line.strip() and not line.lstrip().startswith("#") and "=" in line
               and line.split("=", 1)[0].strip() not in keys_of(current)]
    if missing:
        current = current.rstrip("\n") + "\n\n# Added by scripts/sync_env.py (new settings)\n" + "\n".join(missing) + "\n"
        print(f".env: added {len(missing)} new setting(s): " + ", ".join(m.split('=', 1)[0] for m in missing))
    else:
        print(".env is up to date")
    ENV.write_text(current, encoding="utf-8")


if __name__ == "__main__":
    main()
