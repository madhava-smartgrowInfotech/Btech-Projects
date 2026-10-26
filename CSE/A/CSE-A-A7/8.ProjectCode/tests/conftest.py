"""Test setup: point the app at a scratch SQLite file before it is imported."""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
_tmp = Path(tempfile.mkdtemp(prefix="athena_test_"))
os.environ["DATABASE_URL"] = "sqlite:///" + str(_tmp / "test.db").replace("\\", "/")
