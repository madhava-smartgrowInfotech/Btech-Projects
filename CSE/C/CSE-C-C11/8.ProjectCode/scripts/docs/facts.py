"""
Single source of truth for the documentation build of FINJARVIS (CSE-C-C11).

Batch details come from 1.C11_BATCH_DETAILS.docx / Students.txt. Every measured number is read at build time from
experiments/metrics.json and experiments/api_latency.json (written by scripts/run_experiments.py and scripts/measure_api.py);
docs/REPORT_FACTS.md is the human-readable copy and must agree with this module.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))          # 8.ProjectCode
BATCH = os.path.dirname(CODE)                           # CSE-C-C11
DOCS = os.path.join(CODE, "docs")
DIAG = os.path.join(DOCS, "diagrams")
FIGS = os.path.join(DOCS, "figures")
SHOTS = os.path.join(DOCS, "screenshots")
EXP = os.path.join(CODE, "experiments")

REPORT = False   # set True by build_docs.doc17 so content modules can emit the compact report variant
PRODUCT = "FINJARVIS"
TITLE = "AI Based Personal Finance Manager"
SUBTITLE = "a web platform that categorises spending, forecasts the next month, scores financial health and answers questions from the user's own data"
FULL_TITLE = TITLE
TAGLINE = ("FINJARVIS: a FastAPI and React web application in which a user records or imports transactions, a TF-IDF and logistic-regression model labels them, "
           "a linear-trend model forecasts next month's spending, six weighted components give a 0-100 financial health score, and a rule-routed assistant answers questions from the user's own records")
BATCH_NO = "C11"
SECTION = "CSE-C"
DEPT = "Department of Computer Science and Engineering"
COLLEGE = "TKR College of Engineering & Technology (An Autonomous Institution)"
COLLEGE_SHORT = "TKR College of Engineering & Technology"
ADDRESS = "Medbowli, Meerpet, Balapur, Hyderabad, Telangana - 500 097"
YEAR = "[ACADEMIC YEAR]"
PLACE = "[PLACE]"
DATE = "[DATE]"
STUDENTS = [
    ("Mekala Kalyan", "23K91A05F0"),
    ("Rajanala Sai Hemanth", "23K91A05K3"),
    ("Middala Surya Teja Reddy", "23K91A05F2"),
    ("Manga Akash", "23K91A05E5"),
]
STUDENTS_UPPER = [(n.upper(), r) for n, r in STUDENTS]
GUIDE = "N Padmavathi"
GUIDE_DESIGNATION = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"

# The batch's registered base paper (3.BASE PAPER.docx, 5.LITERATURE SURVEY.docx).
BASE_PAPER = ("R. Kharat, S. Solapurkar, A. Tikkas, M. Uttarwar and A. Yadav, \"A smart AI-based personal finance assistant: A multi-model approach for expense "
              "categorization, budgeting, forecasting and anomaly detection,\" International Journal for Research in Applied Science and Engineering Technology (IJRASET), "
              "vol. 13, no. XI, pp. 167-180, Nov. 2025, doi: 10.22214/ijraset.2025.75019.")
BASE_SHORT = "Kharat et al. (IJRASET, 2025)"
API_PORT, WEB_PORT = 8411, 5411
DEMO_USER, DEMO_PASS = "demo", "Demo@1234"


def _load(name):
    path = os.path.join(EXP, name)
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


M = _load("metrics.json")
LAT = _load("api_latency.json")
CLS = M["classifier"]
FC = M["forecast"]
HL = M["health"]
AS = M["assistant"]
IMP = M["import"]

PYTEST_TOTAL, PYTEST_PASSED = 38, 38
PYTEST_FILES = {"test_auth.py": 9, "test_budget.py": 6, "test_financial_health.py": 6, "test_ml.py": 9, "test_transactions.py": 8}
SMOKE_TOTAL, SMOKE_PASSED = 49, 49
N_ROUTES = 33
N_TABLES = 6
N_PAGES = 13


def lat(name, key="median_ms"):
    """Latency of an endpoint whose key starts with `name` (see experiments/api_latency.json)."""
    for k, v in LAT.items():
        if isinstance(v, dict) and k.startswith(name) and key in v:
            return v[key]
    raise KeyError(name)


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def f1(x):
    return f"{x:.1f}"


def f2(x):
    return f"{x:.2f}"


def f3(x):
    return f"{x:.3f}"


def inr(x):
    return f"INR {x:,.0f}"


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
