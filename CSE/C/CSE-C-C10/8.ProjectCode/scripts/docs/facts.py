"""
Single source of truth for the documentation build of VenturePulse (CSE-C-C10).

Batch details are copied from 1.C10_BATCH_DETAILS.docx / Students.txt. Every measured number is read at build time from
evaluation/real_results.json (scripts/run_experiments.py, real 922-row table), evaluation/extra_results.json (scripts/extra_experiments.py),
evaluation/evaluation_results.json (the shipped app on its synthetic fallback), evaluation/latency.json (scripts/measure_latency.py) and
docs/metrics/*.json (tests). docs/REPORT_FACTS.md is the human-readable version; documents must agree with it.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))          # 8.ProjectCode
BATCH = os.path.dirname(CODE)                           # CSE-C-C10
DOCS = os.path.join(CODE, "docs")
DIAG = os.path.join(DOCS, "diagrams")
FIGS = os.path.join(DOCS, "figures")
SHOTS = os.path.join(DOCS, "screenshots")
EVAL = os.path.join(CODE, "evaluation")
MODELS = os.path.join(CODE, "models")

PRODUCT = "VenturePulse"
TITLE = "An Efficient Novel Approach for Predicting Startup Company Success Rates Using Advanced Machine Learning Paradigms"
BATCH_NO = "C10"
SECTION = "CSE-C"
DEPT = "Department of Computer Science and Engineering"
COLLEGE = "[COLLEGE NAME]"
COLLEGE_SHORT = "[COLLEGE NAME]"
ADDRESS = "[COLLEGE ADDRESS]"
YEAR = "[ACADEMIC YEAR]"
PLACE = "[PLACE]"
DATE = "[DATE]"
STUDENTS = [
    ("Orchu Shirisha", "23K91A05H6"),
    ("Mudavath Raghavendar", "23K91A05G1"),
    ("Majgi Vaishnavi", "23K91A05E0"),
    ("Polishetty Poojitha", "23K91A05J4"),
]
GUIDE = "P Prasanna"
GUIDE_DESIGNATION = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"

BASE_PAPER = ("M. Panjwani, P. Shrivastava, P. Hande, G. Meshram, N. Verma and D. Gotmare, \"Startup success prediction using machine learning and ensemble techniques,\" "
              "IJRASET, vol. 14, no. IV, Apr. 2026, doi: 10.22214/ijraset.2026.80226.")
KEYWORDS = ["Startup Success Prediction", "Machine Learning", "Predictive Analytics", "Business Analytics", "Classification Algorithms", "Random Forest",
            "Decision Tree", "Logistic Regression", "Feature Engineering", "Artificial Intelligence"]
CLASSES = ["SUCCESS", "FAILURE"]


def _load(path):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


R = _load(os.path.join(EVAL, "real_results.json"))            # real-data experiments (922 rows)
X = _load(os.path.join(EVAL, "extra_results.json"))           # leakage ablation, retrieval-only, per industry
S = _load(os.path.join(EVAL, "evaluation_results.json"))      # shipped app, synthetic fallback, fused features
LAT = _load(os.path.join(EVAL, "latency.json"))
TESTS = _load(os.path.join(DOCS, "metrics", "tests.json"))
EDGE = _load(os.path.join(DOCS, "metrics", "edge_tests.json"))
META = _load(os.path.join(MODELS, "metadata.json"))

N_SMOKE, N_UNIT, N_EDGE = TESTS["smoke"], TESTS["unit_app"], TESTS["edge_api"]
N_TESTS = N_SMOKE + N_UNIT + N_EDGE

REAL_ROWS = R["dataset"]["rows"]                 # 922
REAL_SUCCESS = R["dataset"]["success"]           # 596
REAL_FAILURE = R["dataset"]["failure"]           # 326
SYN_ROWS = META["n_train"]                       # 1400
SYN_SUCCESS = META["class_counts"]["SUCCESS"]    # 595
SYN_FAILURE = META["class_counts"]["FAILURE"]    # 805

# code size (lines), measured with wc -l on 2026-10-26
LOC = {"backend": 1351, "templates": 143, "frontend": 3045, "tests": 78, "experiment_scripts": 612}

HARDWARE = "Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB RAM, Windows 11 Pro, CPU only (no GPU)"
SOFTWARE = ("Python 3.11.9, scikit-learn 1.5.2, pandas 2.2.3, XGBoost 2.1.3, sentence-transformers 3.3.1, torch 2.5.1 (CPU), FastAPI 0.115.6, uvicorn 0.34.0; "
            "frontend React 18, Vite 6, Tailwind CSS 4, Recharts")

MODEL_ORDER_REAL = ["Logistic Regression", "Decision Tree", "Random Forest", "XGBoost", "HistGradientBoosting"]
MODEL_ORDER_APP = ["Logistic Regression", "Decision Tree", "Random Forest", "XGBoost"]


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def f2(x):
    return f"{x:.2f}"


def f3(x):
    return f"{x:.3f}"


def pm(blk, key="balanced_accuracy", d=3):
    """'0.746 +/- 0.031' from an aggregated block such as F.R['models']['XGBoost']."""
    return f"{blk[key]['mean']:.{d}f} ± {blk[key]['std']:.{d}f}"


def real(model, key="balanced_accuracy", d=3):
    return pm(R["models"][model], key, d)


def syn_app(model, key="balanced_accuracy", d=3):
    return pm(S["models"][model], key, d)


def syn_struct(model, key="balanced_accuracy", d=3):
    return pm(R["synthetic_structured_only"][model], key, d)


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
