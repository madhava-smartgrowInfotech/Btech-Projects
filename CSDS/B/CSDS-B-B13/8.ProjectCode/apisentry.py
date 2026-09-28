"""APISentry CLI entrypoint. Run: python apisentry.py scan --spec <file> --fail-on high"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from app.cli import app  # noqa: E402

if __name__ == "__main__":
    app()
