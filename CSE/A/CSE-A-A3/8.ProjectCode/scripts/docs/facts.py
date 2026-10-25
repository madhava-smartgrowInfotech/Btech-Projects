"""
Single source of truth for the documentation build (CSE-A-A3, Multi-Disease Prediction Using Machine Learning).

Batch details come from 1.A3_BATCH_DETAILS.docx / Students.txt.  Every number is read at build time from
  models/training_report.json            (what train_models.py wrote and the app serves)
  docs/experiments/results.json          (scripts/run_experiments.py: AUC, confusion, CV, seeds, thresholds, ...)
  docs/experiments/real_data_results.json(scripts/real_data_check.py: real public benchmark data, supplementary)
  docs/experiments/api_tests.json        (scripts/api_tests.py: 41 API checks and latency)
docs/REPORT_FACTS.md is the human-readable copy; nothing in the documents may disagree with it.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))          # 8.ProjectCode
BATCH = os.path.dirname(CODE)                           # CSE-A-A3
DOCS = os.path.join(CODE, "docs")
DIAG = os.path.join(DOCS, "diagrams")
FIGS = os.path.join(DOCS, "figures")
SHOTS = os.path.join(DOCS, "screenshots")
EXP = os.path.join(DOCS, "experiments")

TITLE = "Multi-Disease Prediction Using Machine Learning"
SUBTITLE = "An Intelligent Health Assistant for Diabetes, Heart, Liver and Kidney Risk"
FULL_TITLE = TITLE
PRODUCT = "Intelligent Health Assistant"
BATCH_NO = "A3"
SECTION = "CSE-A"
DEPT = "Department of Computer Science and Engineering"
COLLEGE = "TKR College of Engineering and Technology (Autonomous)"
CITY = "Hyderabad, Telangana"
YEAR = "[ACADEMIC YEAR]"
STUDENTS = [
    ("AJMEERA HARINI", "23K91A0507"),
    ("BANDI LIKITHA", "23K91A0526"),
    ("CHINTHAKINDI SWATHI", "23K91A0555"),
    ("BADROJU SRI HANSIKA", "23K91A0524"),
]
GUIDE = "B. SRUTHI"
GUIDE_DESIGNATION = "Faculty Project Guide, Department of CSE"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"
BASE_PAPER = ("M. Z. Alam, R. Rahman, H. M. Sozib, H. Ahmed, A. Hossain, A. A. Sabeena, A. F. Tasnim, F. Ahmed, M. I. Sarkar and "
              "T. I. Erdei, \"Enhancing Thyroid Disease Diagnosis With Machine Learning and Counterfactual Explainable AI,\" "
              "IEEE Access, vol. 14, pp. 80346-80370, 2026, doi: 10.1109/ACCESS.2026.3663497.")
KEYWORDS = ("multi-disease prediction, healthcare analytics, machine learning, random forest, support vector machine, decision tree, "
            "logistic regression, early diagnosis, medical risk assessment")

DISEASES = ["diabetes", "heart", "liver", "kidney"]
NAME = {"diabetes": "Diabetes", "heart": "Heart disease", "liver": "Liver disease", "kidney": "Kidney disease"}
TARGET = {"diabetes": "Outcome", "heart": "target", "liver": "Dataset", "kidney": "classification"}
MODEL_ORDER = ["Logistic Regression", "Decision Tree", "Random Forest", "SVM"]
SHORT = {"Logistic Regression": "LR", "Decision Tree": "DT", "Random Forest": "RF", "SVM": "SVM"}
CSV_FEATURES = {"diabetes": 8, "heart": 13, "liver": 10, "kidney": 12}
LABEL_NOISE = 0.08   # generate_data.add_noise_labels(noise=0.08)
N_ROWS = 2000        # generate_data.N
SPLIT = "80/20 stratified, random_state 42 (1,600 train / 400 test per disease)"


def _load(path):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


REPORT = _load(os.path.join(CODE, "models", "training_report.json"))   # what the app serves
X = _load(os.path.join(EXP, "results.json"))                           # extended measurements
REAL = _load(os.path.join(EXP, "real_data_results.json"))              # supplementary, real public data
API = _load(os.path.join(EXP, "api_tests.json"))                       # API checks + latency

BEST = {d: REPORT[d]["best_model"] for d in DISEASES}
HO = {d: REPORT[d]["all_results"] for d in DISEASES}                   # accuracy/precision/recall/f1 (4 d.p.)
SMOKE_CHECKS = 27
API_CHECKS = (API["passed"], API["total"]) if API else (0, 0)
N_ENDPOINTS = 7
N_PAGES = 7   # landing, overview, predict (x4 via route param), models, datasets, about, not-found  (route components)


def pct(x, d=1):
    """Percent with round-half-up (0.8825 -> 88.3%), so prose and tables agree."""
    from decimal import ROUND_HALF_UP, Decimal

    q = (Decimal(repr(round(x, 8))) * 100).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)
    return f"{q}%"


def f3(x):
    return f"{x:.3f}"


def f4(x):
    return f"{x:.4f}"


def diag(name):
    return os.path.join(DIAG, name)


def fig(name):
    return os.path.join(FIGS, name)


def shot(name):
    return os.path.join(SHOTS, name)
