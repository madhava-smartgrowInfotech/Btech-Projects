import os
import base64
import secrets
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'aegisballot.db'}")

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production-32chars!!")
SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-session-secret-change-me-please!!")

SECRETS_FILE = DATA_DIR / "secrets.json"

def get_or_create_election_key() -> bytes:
    # election encryption key AES-256
    env_key = os.getenv("ELECTION_ENCRYPTION_KEY")
    if env_key:
        try:
            return base64.b64decode(env_key)
        except Exception:
            pass
    if SECRETS_FILE.exists():
        try:
            data = json.loads(SECRETS_FILE.read_text())
            if "election_key" in data:
                return base64.b64decode(data["election_key"])
        except Exception:
            pass
    key = secrets.token_bytes(32)
    encoded = base64.b64encode(key).decode()
    try:
        existing = {}
        if SECRETS_FILE.exists():
            existing = json.loads(SECRETS_FILE.read_text())
        existing["election_key"] = encoded
        SECRETS_FILE.write_text(json.dumps(existing, indent=2))
    except Exception:
        pass
    return key

ELECTION_KEY = get_or_create_election_key()

APP_NAME = "AegisBallot"
APP_VERSION = "1.0.0"
