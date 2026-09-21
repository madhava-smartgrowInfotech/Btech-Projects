"""Create .env from .env.example (first run) and fill in a random JWT_SECRET if it is empty."""

from __future__ import annotations

import re
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    env, example = ROOT / ".env", ROOT / ".env.example"
    created = False
    if not env.exists():
        env.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
        created = True
    text = env.read_text(encoding="utf-8")
    if re.search(r"(?m)^JWT_SECRET=\s*$", text):
        text = re.sub(r"(?m)^JWT_SECRET=\s*$", f"JWT_SECRET={secrets.token_urlsafe(48)}", text, count=1)
        env.write_text(text, encoding="utf-8")
    key_set = bool(re.search(r"(?m)^GEMINI_API_KEY=\S+", text))
    print(f"[OK]   .env {'created' if created else 'found'}")
    if not key_set:
        print("[!]    GEMINI_API_KEY is empty. Get a free key at https://aistudio.google.com/apikey and paste it into .env")
    return 0


if __name__ == "__main__":
    sys.exit(main())
