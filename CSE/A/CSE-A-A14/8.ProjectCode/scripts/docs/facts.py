"""
Single source of truth for the documentation build (CSE-A-A14, ChurnIQ).

Batch details are copied from 1.A14_BATCH_DETAILS.docx / Students.txt; every number is read from
experiments/churn_synthetic/*.json at build time (see docs/REPORT_FACTS.md for the human-readable copy).
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))          # 8.ProjectCode
BATCH = os.path.dirname(CODE)                           # CSE-A-A14
DOCS = os.path.join(CODE, "docs")
DIAG = os.path.join(DOCS, "diagrams")
FIGS = os.path.join(DOCS, "figures")
SHOTS = os.path.join(DOCS, "screenshots")
EXP = os.path.join(CODE, "experiments", "churn_synthetic")

TITLE = "Customer Churn Prediction in Telecom Industry"
SUBTITLE = "Machine Learning Based Customer Retention System"
FULL_TITLE = f"{TITLE} ({SUBTITLE})"
PRODUCT = "ChurnIQ"
BATCH_NO = "A14"
SECTION = "CSE-A"
DEPT = "Department of Computer Science and Engineering"
COLLEGE = "TKR College of Engineering and Technology (Autonomous)"
CITY = "Hyderabad, Telangana"
YEAR = "[ACADEMIC YEAR]"
STUDENTS = [
    ("ANANTULA SAI NIKHILA SRAVANI", "23K91A0512"),
    ("AVULA ANUDEEP", "23K91A0518"),
    ("B SANDEEP", "24K915A0503"),
    ("DARAGANI VINOD KUMAR", "23K91A0558"),
]
GUIDE = "B. SRIKANTH"
GUIDE_DESIGNATION = "Assistant Professor, Department of CSE"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"
BASE_PAPER = ("S.-V. Oprea and A. Bara, \"Explaining Customer Churn Through Unified Perturbation-Based XAI Soft Computing,\" "
              "IEEE Access, vol. 14, pp. 24460-24478, 2026, doi: 10.1109/ACCESS.2026.3663648.")
KEYWORDS = ("customer churn prediction, machine learning, telecom analytics, customer retention, logistic regression, "
            "decision tree, random forest, exploratory data analysis, explainable AI")


def _load(name):
    p = os.path.join(EXP, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


M = _load("metrics.json")
M15 = _load("metrics_sklearn1.5.0.json")
API = _load("api_latency.json")
EXTRA = _load("extra_analysis.json")
MODEL_ORDER = ["Logistic Regression", "Decision Tree", "Random Forest", "Gradient Boosting", "Hist Gradient Boosting"]
SHORT = {"Logistic Regression": "LR", "Decision Tree": "DT", "Random Forest": "RF", "Gradient Boosting": "GB", "Hist Gradient Boosting": "HGB"}
CW = M["app_default_split"]["class_weight"]["models"]
SMOTE = M["app_default_split"]["smote"]["models"]
NONE = M["app_default_split"]["none"]["models"]
CV = M["cross_validation_5fold_class_weight"]
SPL = M["repeated_random_splits_5_seeds_class_weight"]
DS = M["dataset"]
SP = M["split"]
RISK = M["risk_bands_default_thresholds"]
LAT = M["inference_latency_ms"]
LR = CW["Logistic Regression"]
RF = CW["Random Forest"]
DT = CW["Decision Tree"]

TESTS = {"pytest": 44, "smoke": 63}
N_ROUTES = 31
N_PAGES = 13


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


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
