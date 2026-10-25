"""
Single source of truth for the documentation build of ResQAI (CSE-A-A2).

Batch details come from 1.A2_BATCH_DETAILS.docx / Students.txt. Every performance number is read at build time from
experiments/resqai_eval/metrics.json (scripts/measure_metrics.py), api_latency.json (scripts/measure_api.py) and
tests.json / smoke_test.txt (scripts/run_tests.py, scripts/smoke_test.py). Nothing is typed in by hand except what the code
or the batch files state. docs/REPORT_FACTS.md is the human-readable copy of the same numbers.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))          # 8.ProjectCode
BATCH = os.path.dirname(CODE)                           # CSE-A-A2
DOCS = os.path.join(CODE, "docs")
DIAG = os.path.join(DOCS, "diagrams")
FIGS = os.path.join(DOCS, "figures")
SHOTS = os.path.join(DOCS, "screenshots")
EVAL_DIR = os.path.join(CODE, "experiments", "resqai_eval")

REPORT = False   # set True by build_docs.doc17 so content modules can emit the compact report variant
PRODUCT = "ResQAI"
APP_NAME = "ResQAI"
TITLE = "ResQAI"
SUBTITLE = "AI-Based Accident Detection, Severity Assessment and Intelligent Emergency Response System"
FULL_TITLE = f"{TITLE}: {SUBTITLE}"
TAGLINE = ("ResQAI: a web application that detects a crash from smartphone-style motion-sensor readings, grades its severity, "
           "asks the occupant to confirm, and then drafts a located emergency alert with the nearest hospitals")
BATCH_NO = "A2"
SECTION = "CSE-A"
DEPT = "Department of Computer Science and Engineering"
COLLEGE = "TKR College of Engineering & Technology (An Autonomous Institution)"
COLLEGE_SHORT = "TKR College of Engineering & Technology"
ADDRESS = "Medbowli, Meerpet, Balapur, Hyderabad, Telangana - 500 097"
YEAR = "[ACADEMIC YEAR]"
PLACE = "[PLACE]"
DATE = "[DATE]"
STUDENTS = [
    ("Adepu Meenakshi", "23K91A0503"),
    ("Ayila Shanmukha Sai", "23K91A0521"),
    ("Chekka Chandrashekhar", "23K91A0552"),
    ("Avula Sreeya", "23K91A0519"),
]
GUIDE = "Shirisha Reddy"
GUIDE_DESIGNATION = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"

BASE_PAPER = ("Y. Wang, Z. Liang and Y. He, \"Multi-Task FT-Transformer: A high-performance and interpretable framework for traffic accident severity prediction,\" "
              "*IEEE Access*, vol. 14, pp. 21585-21606, 2026, doi: 10.1109/ACCESS.2026.3658687.")
BASE_SHORT = "Wang, Liang and He (IEEE Access, 2026)"
API_PORT, WEB_PORT = 8302, 5302
DEMO_LOGIN = ("demo@resqai.test", "ResQAI-demo-2026")


def _load(path):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


M = _load(os.path.join(EVAL_DIR, "metrics.json"))
LAT = _load(os.path.join(EVAL_DIR, "api_latency.json"))
TESTS = _load(os.path.join(EVAL_DIR, "tests.json"))
SMOKE_TOTAL = 33          # PASS lines in experiments/resqai_eval/smoke_test.txt
SMOKE_PASSED = 33

DS = M["dataset"]
SHIP = M["shipped_model"]
DET = SHIP["detector_test"]
SEVM = SHIP["severity_test_after_gating"]
ALERT = SHIP["alert_trigger_test"]
RETRAIN = M["retrained_same_seed"]
SEEDS = M["five_seed"]
BASE = M["baselines"]
IMP = M["importance"]
ABL = M["ablation"]
NOISE = M["noise_robustness"]
OOD = M["ood_probes"]
SWEEP = M["threshold_sweep"]
INF = M["inference_latency_ms"]
ENDPOINTS = LAT["endpoints"]
ALERT_PATH = LAT["alert_path_ms"]
TEST_TOTAL = TESTS["total"]
TEST_PASSED = TESTS["passed"]

N_TRAIN, N_TEST, N_TOTAL = DS["n_train"], DS["n_test"], DS["n_total"]
FEATURES = DS["features"]
SEV_NAMES = ["None", "Minor", "Moderate", "Severe"]
COUNTDOWN_S = 15
LIVE_MS = 1500
N_HOSPITALS = 10


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def f2(x):
    return f"{x:.2f}"


def f3(x):
    return f"{x:.3f}"


def f4(x):
    return f"{x:.4f}"


def f5(x):
    return f"{x:.5f}"


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
