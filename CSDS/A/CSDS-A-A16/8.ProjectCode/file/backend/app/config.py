import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("MOSAIC_SECRET_KEY", "dev-secret-change-in-production-please")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

DATABASE_URL = f"sqlite:///{BASE_DIR / 'mosaic.db'}"

CHECKPOINT_DIR = BASE_DIR / "checkpoints"
CLASSIFIER_CHECKPOINT = CHECKPOINT_DIR / "classifier_final.pt"

MEDIA_DIR = BASE_DIR / "media" / "thumbs"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
