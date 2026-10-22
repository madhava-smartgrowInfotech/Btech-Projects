"""
Single source of truth for the documentation build of SymptoTrackAI (CSE-C-C12).

Batch details come from 1.C12_BATCH_DETAILS.docx / Students.txt. Every performance number is read at build time from
docs/metrics/metrics.json (scripts/measure_metrics.py), docs/metrics/latency_*.json (scripts/measure_latency.py) and
docs/metrics/tests.json (the pytest and smoke-test runs). Nothing is typed in by hand except what the code or the batch files state.

The product is built and shown on screen as "CareLens AI" (the name in the code); SymptoTrackAI is the project title.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))          # 8.ProjectCode
BATCH = os.path.dirname(CODE)                           # CSE-C-C12
DOCS = os.path.join(CODE, "docs")
DIAG = os.path.join(DOCS, "diagrams")
FIGS = os.path.join(DOCS, "figures")
SHOTS = os.path.join(DOCS, "screenshots")
METRICS_DIR = os.path.join(DOCS, "metrics")

REPORT = False   # set True by build_docs.doc17 so content modules can emit the compact report variant
PRODUCT = "SymptoTrackAI"
APP_NAME = "CareLens AI"
TITLE = "SymptoTrackAI"
SUBTITLE = "Hybrid RAG Based Symptom Tracking and Health Monitoring System"
FULL_TITLE = f"{TITLE}: {SUBTITLE}"
TAGLINE = "SymptoTrackAI: a local web application that retrieves grounded medical information for symptoms described in everyday language, with safety escalation and a private consultation history"
BATCH_NO = "C12"
SECTION = "CSE-C"
DEPT = "Department of Computer Science and Engineering"
COLLEGE = "TKR College of Engineering & Technology (An Autonomous Institution)"
COLLEGE_SHORT = "TKR College of Engineering & Technology"
ADDRESS = "Medbowli, Meerpet, Balapur, Hyderabad, Telangana - 500 097"
YEAR = "[ACADEMIC YEAR]"
PLACE = "[PLACE]"
DATE = "[DATE]"
STUDENTS = [
    ("Mariyada Karthika Reddy", "23K91A05E9"),
    ("Nacharam Akshaya", "23K91A05G6"),
    ("Madoori Prabath Teja", "23K91A05D6"),
    ("Pulimadhi Keerthan", "23K91A05K1"),
]
GUIDE = "Dr. Ch. B. Naga Lakshmi"
GUIDE_DESIGNATION = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"

BASE_PAPER = ("U. S. Madhury and M. Ramesh, \"A hybrid retrieval-augmented generation framework for intelligent symptom monitoring and disease guidance,\" "
              "*Int. J. Eng. Res. Sci. Technol.*, vol. 22, no. 3, pp. 702-707, 2026, doi: 10.62643/ijerst.2026.v22.n3.4170.")
BASE_SHORT = "Madhury and Ramesh (IJERST, 2026)"
API_PORT, WEB_PORT = 8412, 5412
DEMO_LOGIN = ("demo@carelens.ai", "Demo@1234")


def _load(path):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


M = _load(os.path.join(METRICS_DIR, "metrics.json"))
LAT_FB = _load(os.path.join(METRICS_DIR, "latency_fallback.json")) or {}
LAT_T5 = _load(os.path.join(METRICS_DIR, "latency_flan-t5.json")) or {}
SHIPPED_EVAL = _load(os.path.join(CODE, "results", "metrics.json")) or {}   # the file the About page serves (scripts/evaluate.py, Sept 2026)
_T = _load(os.path.join(METRICS_DIR, "tests.json")) or {}
PYTEST_TOTAL, PYTEST_PASSED, PYTEST_SECONDS = _T.get("pytest_total"), _T.get("pytest_passed"), _T.get("pytest_seconds")
SMOKE_TOTAL, SMOKE_PASSED = _T.get("smoke_total"), _T.get("smoke_passed")

ENV = M["environment"]
KB = M["kb"]
RET = M["retrieval"]
REL = M["relevance"]
GEN = M["generation"]
SAF = M["safety"]
LAT = M["latency"]

SETS = ["S1_shipped_protocol_30", "S1_leave_one_out_30", "S2_verbatim_leave_one_out_176", "S3_two_symptoms_leave_one_out_176", "S4_lay_language_60"]
CFG_ORDER = ["bm25", "dense", "hybrid", "hybrid_rerank", "hybrid_rerank_nohyde", "dense_tfidf", "hybrid_tfidf"]
SHIP = RET["hybrid_rerank"]               # the shipped configuration
FUSION_WEIGHTS = (0.65, 0.35)
CANDIDATE_K, TOP_K = 15, 5


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def f2(x):
    return f"{x:.2f}"


def f3(x):
    return f"{x:.3f}"


def f4(x):
    return f"{x:.4f}"


def ret(cfg, s, key="top1"):
    return RET[cfg][s][key]


def ci(cfg, s):
    lo, hi = RET[cfg][s]["top1_ci"]
    return f"{lo * 100:.1f}-{hi * 100:.1f}%"


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
