"""Shared test setup: make the repo importable and load TensorFlow before scikit-learn (Windows DLL order)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tensorflow  # noqa: E402,F401
