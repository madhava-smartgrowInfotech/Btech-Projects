import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"
EXPERIMENTS_DIR = ROOT / "experiments"
SNAPSHOT_DIR = DATA_DIR / "snapshots"
CLIPS_DIR = DATA_DIR / "own_clips"

BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8208"))
JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/app.db")
if DATABASE_URL.startswith("sqlite:///") and not DATABASE_URL.startswith("sqlite:////"):
    rel = DATABASE_URL[len("sqlite:///"):]
    if not Path(rel).is_absolute():
        DATABASE_URL = f"sqlite:///{(ROOT / rel).as_posix()}"

CAMERA_SOURCE = os.getenv("CAMERA_SOURCE", "0")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").replace(" ", "").strip()

POSE_MODEL = MODELS_DIR / "yolo11n-pose.pt"
ACTIVITY_MODEL = MODELS_DIR / "activity_rf.joblib"

ACTIVITIES = ["walking", "standing", "sitting", "lying", "drinking", "picking_up"]
CLIP_LABELS = ACTIVITIES + ["fall"]

DEMO_EMAIL = "demo@carewatch.app"
DEMO_PASSWORD = "CareWatch123"

for d in (DATA_DIR, SNAPSHOT_DIR, CLIPS_DIR):
    d.mkdir(parents=True, exist_ok=True)
