"""Evaluation tooling for the SeatWise seating engine.

Run the modules from the product root, for example ``python -m ml.benchmark``.
The backend package is added to the import path so the benchmark exercises
exactly the engine the product uses.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
