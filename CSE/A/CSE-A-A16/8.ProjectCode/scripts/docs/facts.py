"""
Single source of truth for the documentation build of SignSpeak (CSE-A-A16).

Batch details are copied from 1.A16_BATCH_DETAILS.docx / Students.txt. Every performance number is read at build
time from docs/metrics/metrics.json (written by scripts/measure_metrics.py), models/*.json and the test runs recorded in
docs/REPORT_FACTS.md. Nothing is typed in by hand except what the code or the batch files state.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))          # 8.ProjectCode
BATCH = os.path.dirname(CODE)                           # CSE-A-A16
DOCS = os.path.join(CODE, "docs")
DIAG = os.path.join(DOCS, "diagrams")
FIGS = os.path.join(DOCS, "figures")
SHOTS = os.path.join(DOCS, "screenshots")
METRICS_DIR = os.path.join(DOCS, "metrics")
MODELS = os.path.join(CODE, "models")

PRODUCT = "SignSpeak"
TITLE = "Sign Language Recognition System Based on Convolutional Neural Networks (CNNs)"
BATCH_NO = "A16"
SECTION = "CSE-A"
DEPT = "Department of Computer Science and Engineering"
COLLEGE = "TKR College of Engineering & Technology (An Autonomous Institution)"
COLLEGE_SHORT = "TKR College of Engineering & Technology"
ADDRESS = "Medbowli, Meerpet, Balapur, Hyderabad, Telangana - 500 097"
YEAR = "[ACADEMIC YEAR]"
PLACE = "[PLACE]"
DATE = "[DATE]"
STUDENTS = [
    ("AJAY", "24K95A0502"),
    ("A NAVADEEP REDDDY", "23K91A0514"),
    ("B MANIDEEP", "23K91A0540"),
    ("B MAHESHWARI", "23K91A0536"),
]
GUIDE = "V. PALLAVI"
GUIDE_DESIGNATION = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"

BASE_PAPER = ("D. T. D. Vo, V. D. Nguyen, T. H. M. Nguyen and M. H. Vo, \"MAG-KD: Mask-Guided Adaptive Gating Knowledge Distillation for "
              "Skeleton-Based Sign Language Recognition on Edge Devices,\" IEEE Access, vol. 14, pp. 54761-54775, 2026, doi: 10.1109/ACCESS.2026.3681176.")

LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
CLASSES = LETTERS + ["space", "del", "nothing"]


def _load(path):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


M = _load(os.path.join(METRICS_DIR, "metrics.json"))
CONFUSIONS = _load(os.path.join(METRICS_DIR, "top_confusions.json"))
FAILS = _load(os.path.join(METRICS_DIR, "failure_cases.json"))
HISTORY = _load(os.path.join(MODELS, "training_history.json"))
CM = _load(os.path.join(MODELS, "confusion_matrix.json"))

ENV = M["environment"]
MODEL = M["model"]
DS = M["dataset"]
T = M["test_split"]
THR = M["threshold_analysis"]
UNSEEN = M["unseen_archive"]
OFFICIAL = M["official_test_28"]
ROB = M["robustness"]["accuracy"]
LAT = M["latency"]
TRAIN_SPEED = M["training_speed"]
RUN = M["saved_training_run"]

# measured by the test runs (docs/REPORT_FACTS.md section 5)
PYTEST_TOTAL, PYTEST_API, PYTEST_PRE, PYTEST_REC, PYTEST_DS = 52, 27, 10, 7, 8
SMOKE_TOTAL = 26

# code size (lines), measured with wc -l
LOC = {"sign_language_app": 1648, "backend": 530, "frontend": 5268, "tests": 398}


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def f2(x):
    return f"{x:.2f}"


def f3(x):
    return f"{x:.3f}"


def f4(x):
    return f"{x:.4f}"


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


def thr_row(t):
    for r in THR:
        if abs(r["threshold"] - t) < 1e-9:
            return r
    raise KeyError(t)


def sorted_f1():
    return sorted(T["per_class_f1"].items(), key=lambda kv: kv[1])
