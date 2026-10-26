"""
Single source of truth for the documentation build of VeriVision AI (CSE-C-C14).

Batch details come from 1.C14_BATCH_DETAILS.docx / Students.txt. Every performance number is read at build time from
experiments/cifake/metrics.json (written by scripts/run_cifake_experiments.py), docs/metrics/latency.json
(scripts/measure_latency.py) and docs/metrics/tests.json (the recorded pytest / smoke-test runs). Nothing is typed in by hand
except what the code or the batch files state.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))          # 8.ProjectCode
BATCH = os.path.dirname(CODE)                           # CSE-C-C14
DOCS = os.path.join(CODE, "docs")
DIAG = os.path.join(DOCS, "diagrams")
FIGS = os.path.join(DOCS, "figures")
SHOTS = os.path.join(DOCS, "screenshots")
METRICS_DIR = os.path.join(DOCS, "metrics")
EXP = os.path.join(CODE, "experiments", "cifake")

REPORT = False   # set True by build_docs.doc17 so content modules can emit the compact report variant
PRODUCT = "VeriVision AI"
TITLE = "Detecting AI Generated Images with CNN and Interpretation Using Explainable AI"
SUBTITLE = "A Heterogeneous CNN Ensemble with Grad-CAM Explanations"
FULL_TITLE = TITLE
TAGLINE = "VeriVision AI: a local web application that estimates whether an image is real or AI-generated with four CNN routes and explains the decision with Grad-CAM"
BATCH_NO = "C14"
SECTION = "CSE-C"
DEPT = "Department of Computer Science and Engineering"
COLLEGE = "[COLLEGE NAME]"
COLLEGE_SHORT = "[COLLEGE NAME]"
ADDRESS = "[COLLEGE ADDRESS]"
YEAR = "[ACADEMIC YEAR]"
PLACE = "[PLACE]"
DATE = "[DATE]"
STUDENTS = [
    ("Ponugoti Viduranandan", "23K91A05J5"),
    ("Naina Baherji", "23K91A05G9"),
    ("Likki Pranathi", "23K91A05D2"),
    ("Motasani Sathish", "23K91A05G0"),
]
GUIDE = "M Thanmayee"
GUIDE_DESIGNATION = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"

BASE_PAPER = ("N. Larue, V. Struc, P. Peer and N.-S. Vu, \"Learning the manifold of authenticity: hybrid-curvature representation learning for generalizable deepfake detection,\" "
              "IEEE Access, vol. 14, pp. 101988-102001, 2026, doi: 10.1109/ACCESS.2026.3702429.")
BASE_SHORT = "Larue et al. (IEEE Access, 2026)"
BASE_NAME = "CTrue"
API_PORT, WEB_PORT = 8414, 5414
DEMO_EMAIL, DEMO_PASSWORD = "demo@verivision.ai", "Demo@1234"
UPLOAD_LIMIT_MB = 10


def _load(path):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


M = _load(os.path.join(EXP, "metrics.json")) or {}
LATENCY = _load(os.path.join(METRICS_DIR, "latency.json")) or {}
_T = _load(os.path.join(METRICS_DIR, "tests.json")) or {}
DEMO = _load(os.path.join(METRICS_DIR, "demo_data_metrics.json")) or {}      # metrics of the shipped synthetic-data models (kept for the record)
DATA = _load(os.path.join(METRICS_DIR, "data_counts.json")) or {}

BRANCHES = ["a1", "a2", "b", "c"]
BRANCH_NAME = {"a1": "EfficientNet-B0 A1", "a2": "EfficientNet-B0 A2", "b": "ResNet50 B", "c": "MobileNetV3-Large C"}
BRANCH_SHORT = {"a1": "A1", "a2": "A2", "b": "B", "c": "C"}
BRANCH_RES = {"a1": 224, "a2": 224, "b": 320, "c": 224}

CLEAN = M.get("clean", {})
ENS = CLEAN.get("ensemble", {})
BR = CLEAN.get("branches", {})
VARIANTS = CLEAN.get("ensemble_variants", {})
SWEEP = M.get("threshold_sweep", [])
ROB = M.get("robustness", {})
XD = M.get("xdomain", {})
HIST = M.get("histories", {})
CI = M.get("bootstrap_ci_accuracy", {})
ECE = M.get("ece_ensemble")
ERR = M.get("error_analysis", {})
N_TEST = M.get("n_test")
AGREE = M.get("branch_vs_ensemble_agreement", {})
UNANIMOUS = M.get("unanimous_rate")

PYTEST_TOTAL = _T.get("pytest_total", 19)
PYTEST_PASSED = _T.get("pytest_passed")
PYTEST_SECONDS = _T.get("pytest_seconds")
SMOKE_TOTAL = _T.get("smoke_total")
SMOKE_PASSED = _T.get("smoke_passed")

WEIGHTS = {"a1": 0.35, "a2": 0.15, "b": 0.25, "c": 0.25}
GATE_TAU_B, GATE_TAU_C, GATE_CORR = 2.5, 2.5, 0.75
CONF_HIGH, CONF_MOD = 0.85, 0.60


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


def lat(key, default="[latency pending]"):
    """Human-readable latency from docs/metrics/latency.json."""
    v = LATENCY.get(key)
    if v is None:
        return default
    return f"{v:.1f} s"
