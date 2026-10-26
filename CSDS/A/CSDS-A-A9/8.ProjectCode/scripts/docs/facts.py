"""Single source of truth for every number used in the ForgetSafe documents.

Loads experiments/*/metrics.json (written by scripts/run_experiments.py).  Document builders
import `F` from here instead of typing numbers, so the chapters, decks and paper cannot drift.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BATCH = ROOT.parent
EXP = ROOT / "experiments"
SHOTS = ROOT / "docs" / "screenshots"
DIAG = ROOT / "docs" / "diagrams"
CHARTS = ROOT / "docs" / "charts"


def load(name: str) -> dict:
    return json.loads((EXP / name / "metrics.json").read_text(encoding="utf-8"))


class _F:
    pass


F = _F()
F.baseline = load("baseline")
F.seeds = load("seeds")
F.sweep = load("noise_sweep")
F.gold = load("gold_retrain")
F.nofree = load("noise_free_leakage")
F.seq = load("sequential")
F.audit = load("audit_tamper")
F.dp = load("dp_accounting")
F.scaling = load("scaling")
F.api = load("api")
F.env = load("environment")

# ---- project identity (from Students.txt / 1.A9_BATCH_DETAILS.docx)
F.title = "Privacy-Preserving Machine Unlearning in Federated LLMs: A Certified Right-to-Be-Forgotten Framework"
F.product = "ForgetSafe"
F.batch = "CSDS-A / Batch A9"
F.students = [
    ("G. Shashank", "23K91A6761"),
    ("B. Sathish", "23K91A6719"),
    ("G. Rakesh", "23K91A6759"),
    ("B. Akhil", "23K91A6721"),
]
F.students_upper = [("G.SHASHANK", "23K91A6761"), ("B.SATHISH", "23K91A6719"), ("G.RAKESH", "23K91A6759"), ("B.AKHIL", "23K91A6721")]
F.guide = "[GUIDE NAME]"
F.dept = "Department of Computer Science and Engineering (Data Science)"
F.college = "[COLLEGE NAME]"

# ---- machine used for every measurement
F.hw = "Intel Core i5-12500 (6 cores / 12 threads), 15.7 GB RAM, Windows 11 Pro, no GPU used"
F.sw = f"Python {F.env['python']} (standard library only), Node.js 24.19 / npm 11.17 for the React UI"


def pct(x: float, d: int = 1) -> str:
    return f"{100 * x:.{d}f}%"
