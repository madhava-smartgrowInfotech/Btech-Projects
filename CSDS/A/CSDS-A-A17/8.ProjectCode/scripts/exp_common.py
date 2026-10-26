"""Shared setup for the experiment scripts.

The experiments import the product code (backend/app/...) unchanged. Drive D: of the build machine was full,
so the backend is run from a copy on drive C: (see docs/REPORT_FACTS.md, "How the numbers were produced");
set CS_BACKEND to point at it. The default is the copy used for the documentation run.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

BACKEND = Path(os.environ.get("CS_BACKEND", r"C:\cs17\app\backend"))
PROJECT = Path(__file__).resolve().parent.parent
EXPERIMENTS = PROJECT / "experiments"
DATA = Path(os.environ.get("CS_DATA", r"C:\cs17\data"))

sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)


def save(name: str, payload: dict) -> Path:
    out = EXPERIMENTS / name / "metrics.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, default=float), encoding="utf-8")
    print("wrote", out)
    return out
