"""
utils.py
--------
Small, reusable helper functions shared across the application:
path handling, file validation, timestamps, and safe directory
creation. Keeping these in one place avoids duplicating logic
across app.py, train.py, evaluate.py and predict.py.
"""

import os
from datetime import datetime
from pathlib import Path

# Project root = the folder this file's parent (src/) lives in.
# Using relative/derived paths avoids hard-coding absolute
# Windows/Mac/Linux paths, so the project runs on any machine.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODELS_DIR = PROJECT_ROOT / "models"
RESULTS_DIR = PROJECT_ROOT / "results"
REPORTS_DIR = PROJECT_ROOT / "reports"
DATA_DIR = PROJECT_ROOT / "data"

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def ensure_dirs(*dirs) -> None:
    """Create any of the given directories if they don't already exist."""
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)


def is_valid_image_file(filename: str) -> bool:
    """Check a filename's extension against allowed image types."""
    if not filename:
        return False
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS


def timestamp_now() -> str:
    """Return a human-readable timestamp for reports/history rows."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def safe_filename(name: str) -> str:
    """Strip path separators from a user-provided filename for safe saving."""
    return os.path.basename(name).replace("..", "")


# Make sure the folders the app writes to always exist, even on
# a completely fresh clone of the repository.
ensure_dirs(MODELS_DIR, RESULTS_DIR, REPORTS_DIR)
