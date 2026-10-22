"""
Single source of truth for the documentation build of PeerScope (CSE-C-C8).

Batch details come from 1.C8_BATCH_DETAILS.docx / Students.txt. Every performance number is read at build time from
docs/metrics/metrics.json (written by scripts/measure_metrics.py), docs/metrics/latency.json (scripts/measure_latency.py)
and the test runs recorded in docs/REPORT_FACTS.md. Nothing is typed in by hand except what the code or the batch files state.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))          # 8.ProjectCode
BATCH = os.path.dirname(CODE)                           # CSE-C-C8
DOCS = os.path.join(CODE, "docs")
DIAG = os.path.join(DOCS, "diagrams")
FIGS = os.path.join(DOCS, "figures")
SHOTS = os.path.join(DOCS, "screenshots")
METRICS_DIR = os.path.join(DOCS, "metrics")
MODELS = os.path.join(CODE, "models")

REPORT = False   # set True by build_docs.doc17 so content modules can emit the compact report variant
PRODUCT = "PeerScope"
TITLE = "Paper Evaluation Using Artificial Intelligence"
SUBTITLE = "Hybrid AI Framework for Research Paper Evaluation and Reviewer Recommendation"
FULL_TITLE = f"{TITLE} ({SUBTITLE})"
TAGLINE = "PeerScope: a local web application that turns a research-paper PDF into a preliminary assessment and an auditable reviewer ranking"
BATCH_NO = "C8"
SECTION = "CSE-C"
DEPT = "Department of Computer Science and Engineering"
COLLEGE = "TKR College of Engineering & Technology (An Autonomous Institution)"
COLLEGE_SHORT = "TKR College of Engineering & Technology"
ADDRESS = "Medbowli, Meerpet, Balapur, Hyderabad, Telangana - 500 097"
YEAR = "[ACADEMIC YEAR]"
PLACE = "[PLACE]"
DATE = "[DATE]"
STUDENTS = [
    ("Mula Sreebindu", "23K91A05G3"),
    ("Puramshetty Vishnu Vardhan", "23K91A05K2"),
    ("K Sampoorna", "24K95A0512"),
    ("Korsa Shivashankar", "24K95A0515"),
]
GUIDE = "M Anupama"
GUIDE_DESIGNATION = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"

BASE_PAPER = ("F. Bagheri, D. Buscaldi and D. Reforgiato Recupero, \"LLM-assisted reviewer assignment via auditable expertise matching,\" "
              "IEEE Access, vol. 14, pp. 127834-127863, 2026, doi: 10.1109/ACCESS.2026.3724622.")
BASE_SHORT = "Bagheri et al. (IEEE Access, 2026)"


def _load(path):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


M = _load(os.path.join(METRICS_DIR, "metrics.json"))
LATENCY = _load(os.path.join(METRICS_DIR, "latency.json")) or {}
SAVED = _load(os.path.join(MODELS, "metrics.json"))

ENV = M["environment"]
DM = M["decision_model"]
SHIPPED = DM["shipped"]
PER_CLASS = DM["per_class"]
BASELINES = DM["baselines"]
SEEDS = DM["seed_study"]
THR = DM["threshold_analysis"]
GEN = DM["generator_structure"]
MATCH = M["matching"]
MINILM = MATCH["sentence_transformer_minilm"]
TFIDF = MATCH["tfidf_fallback"]
REAL = M["real_pdfs"]
LIT = M["literature"]
LOC = M["loc"]

# measured by the test runs (docs/REPORT_FACTS.md section 5); filled by scripts/docs/test_counts.json if present
_T = _load(os.path.join(METRICS_DIR, "tests.json")) or {}
PYTEST_TOTAL = _T.get("pytest_total", 7)
PYTEST_PASSED = _T.get("pytest_passed")
PYTEST_SECONDS = _T.get("pytest_seconds")
SMOKE_TOTAL = _T.get("smoke_total")
SMOKE_PASSED = _T.get("smoke_passed")

MATCH_WEIGHTS = {"expertise_similarity": 0.55, "keyword_score": 0.20, "method_score": 0.15, "availability_score": 0.10, "conflict_penalty": 0.60}
STRENGTH_BANDS = {"Strong": 65, "Good": 45, "Possible": 25}
UPLOAD_LIMIT_MB = 20
API_PORT, WEB_PORT = 8408, 5408
REVIEWER_POOL = 6


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


def thr_row(t):
    for r in THR:
        if abs(r["threshold"] - t) < 1e-9:
            return r
    raise KeyError(t)


def lat_demo_text():
    """Human-readable end-to-end time of one analysis (demo paper, local LLM on) from docs/metrics/latency.json."""
    st = (LATENCY.get("pipeline_stages") or {}).get("demo")
    if not st:
        return "[latency pending]"
    m = st["_total_ms"] / 60000.0
    return f"about {m:.0f} minutes" if m >= 1.5 else f"about {st['_total_ms'] / 1000:.0f} seconds"
