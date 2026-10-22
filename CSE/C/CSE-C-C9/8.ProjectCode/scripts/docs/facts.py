"""
Single source of truth for the documentation build (FinSight AI, batch CSE-C-C9).

Batch details are copied from 1.C9_BATCH_DETAILS.docx / Students.txt; every performance number is read at
build time from artifacts/*.json (written by scripts/train.py and scripts/report_metrics.py) or from
artifacts/measured.json (test and latency runs). See docs/REPORT_FACTS.md for the human-readable version.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))          # 8.ProjectCode
BATCH = os.path.dirname(CODE)                           # CSE-C-C9
DOCS = os.path.join(CODE, "docs")
DIAG = os.path.join(DOCS, "diagrams")
FIGS = os.path.join(DOCS, "figures")
SHOTS = os.path.join(DOCS, "screenshots")
ART = os.path.join(CODE, "artifacts")

TITLE = "AI-Based Financial Identification Based On Demography and Financial Forecasting"
PRODUCT = "FinSight AI"
BATCH_NO = "C9"
SECTION = "CSE-C"
DEPT = "Department of Computer Science and Engineering"
COLLEGE = "TKR College of Engineering and Technology (Autonomous)"
CITY = "Hyderabad, Telangana"
YEAR = "[ACADEMIC YEAR]"
STUDENTS = [
    ("MOHD AHMED", "23K91A05F7"),
    ("MANNE UPENDER", "23K91A05E6"),
    ("PADALA RAJESH", "23K91A05H7"),
    ("MADAGOUNI HARSHAVARDHAN GOUD", "23K91A05D5"),
]
GUIDE = "B SRIKANTH"
GUIDE_DESIGNATION = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"
BASE_PAPER = ("Y. Kim and E. J. Sun, \"An Explainable Machine Learning Framework for Organizational Financial Distress "
              "Detection: Evidence From Korean Hospital Panel Data,\" IEEE Access, vol. 14, pp. 100337-100350, 2026, "
              "doi: 10.1109/ACCESS.2026.3709346.")

MODELS = ["logistic_regression", "random_forest", "gradient_boosting", "xgboost"]
MODEL_LABEL = {"logistic_regression": "Logistic Regression", "random_forest": "Random Forest",
               "gradient_boosting": "Gradient Boosting", "xgboost": "XGBoost"}


def _load(path):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


METRICS = _load(os.path.join(ART, "metrics.json"))                    # best model, test
COMPARE = _load(os.path.join(ART, "model_comparison.json"))["models"]  # all four, test + CV
VALID = _load(os.path.join(ART, "validation_report.json"))
STATS = _load(os.path.join(ART, "stats_report.json"))
SHAP = _load(os.path.join(ART, "shap_global.json"))
FORECAST = _load(os.path.join(ART, "forecast.json"))
TRAIN = _load(os.path.join(ART, "training_summary.json"))
RM = _load(os.path.join(ART, "report_metrics.json"))                  # confusion matrices, sweep, calibration, back-test
MEAS = _load(os.path.join(ART, "measured.json"))                      # pytest, smoke test, API latency, environment

BEST = METRICS["best_model"]
CM = RM["models"]                                                      # per-model tn/fp/fn/tp + pr_auc + brier
N_ROWS, N_TRAIN, N_TEST = RM["rows"], RM["train"], RM["test"]
TEST_POS = VALID["class_balance_test"][">50K"]
TEST_NEG = VALID["class_balance_test"]["<=50K"]


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
