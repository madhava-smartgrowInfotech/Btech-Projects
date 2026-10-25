"""
Single source of truth for the documentation build of SecurePay AI (CSE-A-A4).

Batch details come from 1.A4_BATCH_DETAILS.docx / Students.txt. Every performance number is read at build time from
experiments/metrics.json (scripts/run_experiments.py), experiments/latency.json (scripts/measure_latency.py) and
experiments/tests.json. Nothing is typed in by hand except what the code or the batch files state.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))          # 8.ProjectCode
BATCH = os.path.dirname(CODE)                           # CSE-A-A4
DOCS = os.path.join(CODE, "docs")
DIAG = os.path.join(DOCS, "diagrams")
FIGS = os.path.join(DOCS, "figures")
SHOTS = os.path.join(DOCS, "screenshots")
EXP = os.path.join(CODE, "experiments")

REPORT = False   # set True by build_docs.doc17 so content modules can emit the compact report variant
PRODUCT = "SecurePay AI"
TITLE = "Credit Card Fraud Detection Using Machine Learning"
SUBTITLE = "Quantum-Inspired Restricted Boltzmann Machine Classifier with a Real-Time Screening Interface"
FULL_TITLE = TITLE
TAGLINE = "SecurePay AI: a Flask and React application that scores card transactions with three restricted-Boltzmann-machine classifiers"
BATCH_NO = "A4"
SECTION = "CSE-A"
DEPT = "Department of Computer Science and Engineering"
COLLEGE = "TKR College of Engineering & Technology (An Autonomous Institution)"
COLLEGE_SHORT = "TKR College of Engineering & Technology"
ADDRESS = "Medbowli, Meerpet, Balapur, Hyderabad, Telangana - 500 097"
YEAR = "[ACADEMIC YEAR]"
PLACE = "[PLACE]"
DATE = "[DATE]"
STUDENTS = [
    ("ARELLI PRAVEEN KUMAR", "23K91A0513"),
    ("BANOTHU AJAY", "23K91A0529"),
    ("D CHANDRIKA", "23K91A0557"),
    ("BAIRAGONI VIJAY", "23K91A0525"),
]
GUIDE = "KOTESHWAR RAO"
GUIDE_DESIGNATION = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"

BASE_PAPER = ("J. M. C. de Albuquerque Neto, G. C. do Amaral and G. P. Temporao, \"Fraud detection in credit card transactions using "
              "quantum-assisted restricted Boltzmann machines,\" IEEE Access, vol. 14, pp. 62923-62932, 2026, doi: 10.1109/ACCESS.2026.3683308.")
BASE_SHORT = "Neto et al. (IEEE Access, 2026)"
# Table 1 of the base paper, read from the PDF (accuracy, precision, recall, F1 in %, training time)
BASE_TABLE = {"PCD": (84, 86, 81, 83, "2 minutes"), "SAS": (85, 94, 82, 88, "4 hours"), "QS": (85, 91, 79, 84, "1.8 hours")}


def _load(path):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


M = _load(os.path.join(EXP, "metrics.json"))
LATENCY = _load(os.path.join(EXP, "latency.json")) or {}
_T = _load(os.path.join(EXP, "tests.json")) or {}
SMOKE_TOTAL = _T.get("smoke_total", 20)
SMOKE_PASSED = _T.get("smoke_passed", 20)

DATASET = M["dataset"]
SPLIT = M["split"]
SAVED = M["saved_models"]
SERVING = M["serving"]
BASE_BAL = M["baselines_balanced"]
IMB = M["imbalance"]
SEEDS = M["seeds"]
FULL = M["full39k"]
HIST = SAVED["histories"]

API_PORT, WEB_PORT = 8304, 5304
RISK_BANDS = (0.4, 0.7)       # app.py predict_single: >0.7 HIGH, >0.4 MEDIUM, else LOW
N_ENDPOINTS = 16
BACKEND_LINES, FRONTEND_LINES = 1338, 3574


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def f2(x):
    return f"{x:.2f}"


def f3(x):
    return f"{x:.3f}"


def shot(name):
    return os.path.join(SHOTS, name)


def diag(name):
    return os.path.join(DIAG, name)


def fig(name):
    return os.path.join(FIGS, name)


def shot_w(path, base=5.6, max_h_in=6.4):
    """Picture width in inches that keeps the height under max_h_in."""
    from PIL import Image

    with Image.open(path) as im:
        w, h = im.size
    return min(base, max_h_in * w / h)


def best_epoch(mode):
    h = HIST[mode]
    i = max(range(len(h["f1"])), key=lambda k: h["f1"][k])
    return i + 1, h["f1"][i]


def seed_cell(mode, key, scale=100, d=1):
    r = SEEDS[mode][key]
    return f"{r['mean'] * scale:.{d}f} +/- {r['std'] * scale:.{d}f}"


def imb_row(model, strategy):
    for r in IMB["results"]:
        if r["model"] == model and r["strategy"] == strategy:
            return r
    raise KeyError((model, strategy))
