"""
Single source of truth for the documentation build of the Smart Campus Placement System (CSE-C-C5).

Batch details come from 1.C5_BATCH_DETAILS.docx / Students.txt. Every performance number is read at build time from
models/metrics.json, docs/experiments/experiments.json (scripts/run_experiments.py) and docs/experiments/tests.json
(scripts/edge_tests.py) - the same files that docs/REPORT_FACTS.md summarises. Nothing is typed in by hand except
what the code or the batch files state.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))          # 8.ProjectCode
BATCH = os.path.dirname(CODE)                           # CSE-C-C5
DOCS = os.path.join(CODE, "docs")
DIAG = os.path.join(DOCS, "diagrams")
FIGS = os.path.join(DOCS, "figures")
SHOTS = os.path.join(DOCS, "screenshots")
EXP_DIR = os.path.join(DOCS, "experiments")
MODELS = os.path.join(CODE, "models")
STATIC = os.path.join(CODE, "static")
TEMPLATES = r"D:\abstracts\Templates"

PRODUCT = "Smart Campus Placement System"
SHORT = "SCPS"
TITLE = "Smart Campus Placement System"
BATCH_NO = "C5"
SECTION = "CSE-C"
DEPT = "Department of Computer Science and Engineering"
COLLEGE = "TKR College of Engineering & Technology (An Autonomous Institution)"
COLLEGE_SHORT = "TKR College of Engineering & Technology"
ADDRESS = "[COLLEGE ADDRESS]"
YEAR = "[ACADEMIC YEAR]"
PLACE = "[PLACE]"
DATE = "[DATE]"
STUDENTS = [
    ("Mopidevi Bhagyasri", "23K91A05F9"),
    ("Pamulaparthi Harsha Vardan Reddy", "23K91A05J0"),
    ("Mohammad Faruk Baba", "23K91A05F3"),
    ("Prahalladh Terati", "23K91A05J8"),
]
GUIDE = "S Usha Devi"
GUIDE_DESIGNATION = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"

# Declared base paper (batch document 3) and the technique source the code is built on (README)
BASE_PAPER = ("M. Prasanna Kumari, B. Punith, M. Srinath, P. Koushik and Y. Gourav, \"Student placement prediction system using machine learning,\" "
              "Int. J. Eng. Technol. Manage. Sci. (IJETMS), vol. 10, no. 3, pp. 47-51, May-Jun. 2026, doi: 10.46647/ijetms.2026.v10i03.008.")
TECH_PAPER = ("M. Heidari Fard and E. Tabrizi, \"A hybrid machine learning approach for graduate admission prediction and combined "
              "university-program recommendation,\" arXiv:2603.29881 [cs.IR], Feb. 2026.")


def _load(path):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


METRICS = _load(os.path.join(MODELS, "metrics.json"))          # shipped model metrics (seed 42, 450 test rows)
EXP = _load(os.path.join(EXP_DIR, "experiments.json"))         # extra measurements
TESTS = _load(os.path.join(EXP_DIR, "tests.json"))             # 46 checks + latency

R = EXP["seed42"]["results"]            # every model, shipped artefacts, seed 42
DS = EXP["dataset"]
CONF = EXP["confusion"]
RES = EXP["residual"]
BAND = EXP["band_sweep"]
THR = EXP["threshold_sweep"]
CAL = EXP["calibration"]
SHAP = EXP["shap_top"]
MS = EXP["multi_seed"]["summary"]
MS_ACC = EXP["multi_seed"]["per_seed_accuracy"]
SEEDS = EXP["multi_seed"]["seeds"]
REC = EXP["recommender"]
LAT_PREDICT = EXP["latency_predict_for_ms"]
PERF = TESTS["performance_127_0_0_1"]
TEST_SUMMARY = TESTS["summary"]
TEST_CHECKS = TESTS["checks"]
SMOKE_TOTAL = 15

CV9 = METRICS["cv_xgb_9fold"]
BRIER = METRICS["brier_platt"]
RESIDUAL_RATE = METRICS["residual_rate"]
TEST_N = METRICS["test_size"]
TRAIN_N, VAL_N = 2100, 450

MODEL_LABELS = {
    "logreg": "Logistic Regression", "tree": "Decision Tree", "rf": "Random Forest", "svm": "SVM (RBF)", "knn": "kNN (k = 9)",
    "xgb": "XGBoost", "xgb_calibrated": "XGBoost + Platt", "hybrid_xgb_knn": "Hybrid XGB + kNN (paper rule)",
    "hybrid_xgb_svm": "Hybrid XGB + SVM (paper rule)", "hybrid_knn_labelfree": "Hybrid kNN, label-free (borderline only)",
    "hybrid_knn_serving": "Hybrid kNN, serving rule",
}

ENV = {"cpu": "Intel Core i5-12500 (6 cores, 12 threads)", "ram": "15.7 GB", "os": "Windows 11 Pro", "gpu": "none (CPU only)",
       "python": "3.14.7", "sklearn": "1.9.0", "xgboost": "3.4.1", "pandas": "3.0.5", "numpy": "2.5.3", "shap": "0.52.0",
       "fastapi": "0.159.1", "uvicorn": "0.54.0", "pydantic": "2.14.1", "flask": "3.1.3", "node": "24.19.0",
       "react": "19.3", "vite": "8.3", "tailwind": "4.3", "three": "0.186"}

# code size (lines), measured with wc -l
LOC = {"src": 508, "backend": 221, "app.py": 140, "frontend pages": 953, "scripts (this work)": 1560}

SCREENS = [
    ("01_landing_dark.png", "Landing page (dark theme)"), ("01_landing_light.png", "Landing page (light theme)"),
    ("02_predict.png", "Placement eligibility result"), ("03_recommend.png", "Company-role recommendations"),
    ("04_dashboard.png", "Officer dashboard overview"), ("05_dashboard_shap.png", "Officer dashboard: SHAP importance"),
    ("06_recruiter.png", "Recruiter shortlist"), ("07_companies.png", "Companies board"),
    ("08_command_palette.png", "Command palette"), ("09_activity_log.png", "Activity log"),
]


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


def static(name):
    return os.path.join(STATIC, name)


def shot_w(path, base=5.6, max_h_in=6.4):
    """Picture width in inches that keeps the height under max_h_in."""
    from PIL import Image

    with Image.open(path) as im:
        w, h = im.size
    return min(base, max_h_in * w / h)


def ms(name, metric="accuracy"):
    """'mean +- sd' string for the five-seed study."""
    v = MS[name][metric]
    return f"{v['mean']:.4f} \u00b1 {v['sd']:.4f}"


def model_row(name):
    r = R[name]
    return [MODEL_LABELS[name], f"{r['accuracy']:.4f}", f"{r['roc_auc']:.4f}", f"{r['f1']:.4f}", f"{r['precision']:.4f}", f"{r['recall']:.4f}"]


def perf_row(label, key):
    r = PERF[key]
    return [label, str(r["n"]), f"{r['mean_ms']:.1f}", f"{r['p50_ms']:.1f}", f"{r['p95_ms']:.1f}", f"{r['max_ms']:.1f}"]
