"""
Single source of truth for the documentation build (LabLens, batch CSE-A-A8).

Nothing here is typed in by hand except batch details (copied from the batch documents).
All performance numbers are read at build time from experiments/lablens/*.json, produced by
scripts/run_experiments.py, scripts/measure_api.py and the pytest / smoke runs (test_run.json).
The evaluation corpus is GENERATED (120 synthetic lab-report PDFs with known ground truth): there is
no manually labelled real-report set, no Tesseract on the test machine, and no LLM key.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))          # 8.ProjectCode
BATCH = os.path.dirname(CODE)                           # CSE-A-A8
DOCS = os.path.join(CODE, "docs")
DIAG = os.path.join(DOCS, "diagrams")
FIGS = os.path.join(DOCS, "figures")
SHOTS = os.path.join(DOCS, "screenshots")
EXP = os.path.join(CODE, "experiments", "lablens")

TITLE = "AI-Powered Medical Lab Report Analysis and Health Insights Platform"
PRODUCT = "LabLens"
BATCH_NO = "A8"
SECTION = "CSE-A"
DEPT = "Department of Computer Science and Engineering"
COLLEGE = "TKR College of Engineering and Technology (Autonomous)"
CITY = "Hyderabad, Telangana"
YEAR = "2026-2027"
STUDENTS = [
    ("BANOTH SWAPNA", "23K91A0528"),
    ("BEKKAM VARSHITHA", "23K91A0535"),
    ("A NAVADEEP REDDY", "23K91A0502"),
    ("BUDIGAM MANOJ", "23K91A0546"),
]
GUIDE = "L.G REDDY"
GUIDE_DESIGNATION = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"
BASE_PAPER = ("A. Karhade, I. Verma, V. Gadaokar and J. Mahajan, \"RAG-Based Blood Test Report Analysis to Reverse Metabolic Syndrome,\" "
              "Communications on Applied Nonlinear Analysis, vol. 32, no. 10s, pp. 2771-2779, 2025, doi: 10.52783/cana.v32.5718.")

STATUSES = ["LOW", "NORMAL", "HIGH", "UNKNOWN"]


def _load(path):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


METRICS = _load(os.path.join(EXP, "metrics.json"))
API_LAT = _load(os.path.join(EXP, "api_latency.json"))
TESTS = _load(os.path.join(EXP, "test_run.json"))
EXTRACTION = METRICS["extraction"]
NAMES = METRICS["name_normalisation"]
CLASSIF = METRICS["classification"]
INSIGHT = METRICS["insight_coverage"]
LATENCY = METRICS["latency"]


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def f2(x):
    return f"{x:.2f}"


def f3(x):
    return f"{x:.3f}"


def shot(name):
    return os.path.join(SHOTS, name)


def shot_view(name, max_h=1500):
    """Screenshot path for documents: very tall full-page captures are cropped to the first `max_h` pixels."""
    from PIL import Image

    p = os.path.join(SHOTS, name)
    with Image.open(p) as im:
        w, h = im.size
        if h <= max_h * 1.35:
            return p
        os.makedirs(os.path.join(FIGS, "_crops"), exist_ok=True)
        out = os.path.join(FIGS, "_crops", name)
        im.convert("RGB").crop((0, 0, w, max_h)).save(out)
        return out


def shot_w(path, base=5.6, max_h_in=6.4):
    """Picture width in inches that keeps the height under max_h_in."""
    from PIL import Image

    with Image.open(path) as im:
        w, h = im.size
    return min(base, max_h_in * w / h)


def diag(name):
    return os.path.join(DIAG, name)


def fig(name):
    return os.path.join(FIGS, name)
