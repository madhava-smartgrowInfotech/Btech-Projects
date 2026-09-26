"""
Central configuration for Attendance Magic.

Every setting can be overridden with an environment variable so the same code
runs on a laptop (SQLite, manual GPS allowed for testing) and on a server
(PostgreSQL / Supabase, strict GPS).
"""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


# --------------------------------------------------------------------------- #
# Application
# --------------------------------------------------------------------------- #
APP_NAME = "Attendance Magic"
APP_TAGLINE = "Smart Geo-Fenced Attendance with Live Challenge Verification"
# Public URL of the deployed app. Used to build the unique session links.
BASE_URL = os.getenv("AM_BASE_URL", "http://localhost:8501").rstrip("/")

# --------------------------------------------------------------------------- #
# Database  (SQLite by default; set DATABASE_URL for PostgreSQL / Supabase)
# e.g.  postgresql+psycopg2://postgres:PASSWORD@db.xxxx.supabase.co:5432/postgres
# --------------------------------------------------------------------------- #
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'attendance_magic.db'}")

# --------------------------------------------------------------------------- #
# Authentication (JWT)
# --------------------------------------------------------------------------- #
JWT_SECRET = os.getenv("AM_JWT_SECRET", "change-me-in-production-please")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = _env_int("AM_JWT_EXPIRY_MINUTES", 120)
PBKDF2_ITERATIONS = 200_000

# --------------------------------------------------------------------------- #
# Device identification
# --------------------------------------------------------------------------- #
# How many distinct devices a student may use. 1 = strict (default).
MAX_DEVICES_PER_STUDENT = _env_int("AM_MAX_DEVICES_PER_STUDENT", 1)

# --------------------------------------------------------------------------- #
# Geo-fence
# --------------------------------------------------------------------------- #
DEFAULT_GEOFENCE_RADIUS_M = _env_float("AM_DEFAULT_RADIUS_M", 60.0)
# Extra tolerance added to the radius to absorb GPS inaccuracy (metres).
GEOFENCE_TOLERANCE_M = _env_float("AM_GEOFENCE_TOLERANCE_M", 15.0)
# If the browser reports an accuracy worse than this, reject the reading.
MAX_GPS_ACCURACY_M = _env_float("AM_MAX_GPS_ACCURACY_M", 150.0)
# For development / demo on machines without GPS, let the user type coordinates.
ALLOW_MANUAL_LOCATION = _env_bool("AM_ALLOW_MANUAL_LOCATION", True)

# --------------------------------------------------------------------------- #
# Liveness challenge (MediaPipe Face Mesh)
# --------------------------------------------------------------------------- #
# Streamlit's camera widget returns a mirrored (selfie-style) image.
CAMERA_MIRRORED = _env_bool("AM_CAMERA_MIRRORED", True)
LIVENESS_YAW_DELTA = _env_float("AM_LIVENESS_YAW_DELTA", 0.12)      # head turn
LIVENESS_PITCH_DELTA = _env_float("AM_LIVENESS_PITCH_DELTA", 0.08)  # look up/down
LIVENESS_ROLL_DEG = _env_float("AM_LIVENESS_ROLL_DEG", 12.0)        # head tilt
LIVENESS_MOUTH_OPEN_MAR = _env_float("AM_LIVENESS_MAR", 0.35)       # mouth open
LIVENESS_EYES_CLOSED_EAR = _env_float("AM_LIVENESS_EAR", 0.18)      # eyes closed
NEUTRAL_MAX_YAW = 0.10
NEUTRAL_MAX_MAR = 0.25

# --------------------------------------------------------------------------- #
# Face matching (InsightFace ArcFace embeddings, cosine similarity)
# --------------------------------------------------------------------------- #
INSIGHTFACE_MODEL = os.getenv("AM_INSIGHTFACE_MODEL", "buffalo_l")
# Same-person similarity between the enrolled face and the live capture.
IDENTITY_THRESHOLD = _env_float("AM_IDENTITY_THRESHOLD", 0.40)
# Similarity above which two captures in one session count as the same face.
DUPLICATE_THRESHOLD = _env_float("AM_DUPLICATE_THRESHOLD", 0.45)
# Neutral frame and challenge frame must be the same person.
FRAME_CONSISTENCY_THRESHOLD = _env_float("AM_FRAME_CONSISTENCY_THRESHOLD", 0.45)
# Students must enrol a reference face before they can check in.
REQUIRE_ENROLLMENT = _env_bool("AM_REQUIRE_ENROLLMENT", True)

# --------------------------------------------------------------------------- #
# Misc
# --------------------------------------------------------------------------- #
TIMEZONE = os.getenv("AM_TIMEZONE", "Asia/Kolkata")  # display timezone (DB stores UTC)
