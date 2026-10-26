"""
Single source of truth for the documentation build of ATHENA (CSE-A-A7).

Batch details come from 1.A7_BATCH_DETAILS.docx / Students.txt. Every performance number is read at build time from the JSON files written by
the experiment scripts (experiments/metrics.json, experiments/eval/metrics.json, experiments/extra/*.json) - nothing is typed in by hand
except what the code, the batch files or the base paper state. docs/REPORT_FACTS.md is the human-readable copy of the same numbers.

THE TRIAGE MODEL IS TRAINED AND EVALUATED ON SEEDED SYNTHETIC DATA. Every results sentence must say so.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))          # 8.ProjectCode
BATCH = os.path.dirname(CODE)                           # CSE-A-A7
DOCS = os.path.join(CODE, "docs")
DIAG = os.path.join(DOCS, "diagrams")
FIGS = os.path.join(DOCS, "figures")
SHOTS = os.path.join(DOCS, "screenshots")
EXP = os.path.join(CODE, "experiments")

REPORT = False   # set True by build_docs.doc17 so content modules can emit the compact report variant
PRODUCT = "ATHENA"
TITLE = "ATHENA - Autonomous Triage and Healthcare Electronic Neural Assistant"
SUBTITLE = "Fusing scanned reports and vitals into an explainable emergency triage priority"
FULL_TITLE = TITLE
TAGLINE = "ATHENA: a scanned report and eight vitals in, a calibrated priority from 1 to 5 and the reasons behind it out"
BATCH_NO = "A7"
SECTION = "CSE-A"
DEPT = "Department of Computer Science and Engineering"
COLLEGE = "TKR College of Engineering & Technology (An Autonomous Institution)"
COLLEGE_SHORT = "TKR College of Engineering & Technology"
ADDRESS = "Medbowli, Meerpet, Balapur, Hyderabad, Telangana - 500 097"
YEAR = "[ACADEMIC YEAR]"
PLACE = "[PLACE]"
DATE = "[DATE]"
STUDENTS = [
    ("Badaveni Srinath", "23K91A0523"),
    ("Basani Avinash", "23K91A0532"),
    ("Degala Praneeth", "23K91A0561"),
    ("Bontha Saisree", "23K91A0545"),
]
STUDENTS_UPPER = [(n.upper(), r) for n, r in STUDENTS]
GUIDE = "K. Shalini"
GUIDE_DESIGNATION = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"

BASE_PAPER = ("M. Mlodawski, S. Deniziak, M. Plaza, A. Kwiatkowska, D. Jaszczyk, A. Gajda and K. Twardowski, \"Multidimensional analysis of the "
              "diagnostic performance of machine learning models in disease classification: implications for clinical decision support systems,\" "
              "IEEE Access, vol. 14, pp. 92149-92177, 2026, doi: 10.1109/ACCESS.2026.3703248.")
BASE_SHORT = "Mlodawski et al. (IEEE Access, 2026)"
API_PORT, WEB_PORT = 8307, 5307
DEMO_USER, DEMO_PASS = "clinician@athena.health", "Athena@123"

MACHINE = "Intel Core i5-12500 (12 threads), 15.7 GB RAM, Windows 11 Pro, no GPU, Python 3.11.9, Node 24.19.0"


def _load(*p):
    path = os.path.join(*p)
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


SHIPPED = _load(EXP, "metrics.json")               # as shipped: ml/train.py
EVAL = _load(EXP, "eval", "metrics.json")          # ml/eval.py: reading + end to end timing
X = _load(EXP, "extra", "metrics.json")            # scripts/run_experiments.py
STRESS = _load(EXP, "extra", "extract_stress.json")
LAT = _load(EXP, "extra", "api_latency.json")

# ---- shipped model, 1,200 held-out synthetic cases
ACC, W1, MF1 = SHIPPED["accuracy"], SHIPPED["within_one_priority"], SHIPPED["macro_f1"]
REC = [SHIPPED["per_class_recall"][str(i)] for i in range(1, 6)]
SUP = [SHIPPED["support"][str(i)] for i in range(1, 6)]
CM = SHIPPED["confusion_matrix"]
N_TRAIN, N_CAL, N_TEST = SHIPPED["n_train"], SHIPPED["n_calibration"], SHIPPED["n_test"]
MEAN_CONF = SHIPPED["mean_confidence"]
QWK = X["shipped"]["calibrated"]["qwk"]
TOP2 = X["shipped"]["calibrated"]["top2"]
ACC_UNCAL = X["shipped"]["uncalibrated"]["accuracy"]
MF1_UNCAL = X["shipped"]["uncalibrated"]["macro_f1"]
MODEL_SEC = SHIPPED["model_seconds_per_patient"]
TRAIN_SEC = SHIPPED["train_seconds"]
READ = EVAL["report_reading"]
E2E = EVAL["end_to_end_seconds_per_patient"]

# ---- dataset
ROWS, N_FEATURES, N_VITALS, N_FLAGS = 6000, 36, 8, 28
SEED = 7307
PRIO_SHARE = [X["dataset"]["priority_share"][str(i)] for i in range(1, 6)]
ARCH_SHARE = X["dataset"]["archetype_share"]
CEILING = X["noise_ceiling"]["oracle_accuracy_knowing_clean_severity"]

# ---- extra experiments
COMP = X["model_comparison"]
CV5 = X["cv5_accuracy"]
ABL = X["ablation"]
CAL = X["calibration"]
THR = X["confidence_threshold"]
SAFE = X["safety"]
ROB = X["robustness_dropped_flags"]
SEEDS = X["seed_stability"]
SHAP_TOP = X["shap_global"]

# ---- tests (measured in the documentation run)
PYTEST_TOTAL, PYTEST_PASSED, PYTEST_XFAIL, PYTEST_FAILED, PYTEST_SECONDS = 47, 46, 1, 0, 15
SMOKE_TOTAL, SMOKE_PASSED = 17, 17

# ---- base paper numbers as printed in IEEE Access 14:92149 (Mlodawski et al.)
BASE_PAPER_RESULTS = {
    "cases": 1655, "internal": 616, "pediatrics": 1039, "algorithms": 19, "classes": 87, "classes_ped": 32, "classes_int": 55,
    "parameters": 479, "best_int": ("Gradient Boosting", 0.8474), "best_ped": ("Multi-Layer Perceptron", 0.8720),
    "top3_mean_int": 0.7743, "top3_mean_ped": 0.8199, "top3_best_int": 0.9172, "top3_best_ped": 0.9471,
    "ext_cases": 120, "ext_top1_int": 0.7333, "ext_top1_ped": 0.7833, "ext_top3_int": 0.8667, "ext_top3_ped": 0.9000,
    "threshold": 0.85, "trials": 100,
}


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def f2(x):
    return f"{x:.2f}"


def f3(x):
    return f"{x:.3f}"


def f4(x):
    return f"{x:.4f}"


def ms(x, d=1):
    return f"{x:.{d}f} ms"


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


def lat(name, key="median_ms"):
    """Median (or p95_ms) HTTP latency in ms from experiments/extra/api_latency.json."""
    return LAT[name][key]


def thr_row(t):
    for r in THR:
        if abs(r["threshold"] - t) < 1e-9:
            return r
    raise KeyError(t)


def rob_row(p):
    for r in ROB:
        if abs(r["drop_rate"] - p) < 1e-9:
            return r
    raise KeyError(p)
