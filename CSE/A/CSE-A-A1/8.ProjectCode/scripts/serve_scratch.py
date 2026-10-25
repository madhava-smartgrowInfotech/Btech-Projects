"""
Runs the FastAPI backend against a throw-away database and upload folder, so measurements and screenshots never
touch instance/app.db.

    venv\Scripts\python.exe scripts\serve_scratch.py --data C:\path\to\scratch --port 8301
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ap = argparse.ArgumentParser()
ap.add_argument("--data", required=True)
ap.add_argument("--port", type=int, default=8301)
args = ap.parse_args()

from config import Config  # noqa: E402

os.makedirs(args.data, exist_ok=True)
Config.DATABASE = os.path.join(args.data, "scratch.db")
Config.UPLOAD_FOLDER = os.path.join(args.data, "uploads")

import uvicorn  # noqa: E402
from backend.main import app  # noqa: E402

uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")
