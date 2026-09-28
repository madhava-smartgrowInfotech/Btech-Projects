"""Create .env from .env.example with a random JWT secret (no-op if .env already exists)."""
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
env = ROOT / ".env"
if env.exists():
    print(".env already exists - left unchanged")
else:
    text = (ROOT / ".env.example").read_text().replace("JWT_SECRET=\n", f"JWT_SECRET={secrets.token_hex(32)}\n", 1)
    env.write_text(text)
    print("Created .env")
