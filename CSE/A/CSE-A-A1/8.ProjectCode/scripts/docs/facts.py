"""
Single source of truth for the documentation build of the Adaptive Learning Intelligence Platform (CSE-A-A1).

Batch details come from 1.A1_BATCH_DETAILS.docx / Students.txt. Every performance number is read at build time from
experiments/results.json, experiments/api_latency.json, experiments/quiz_audit.json and experiments/pytest_report.xml -
the same files that docs/REPORT_FACTS.md summarises. Nothing is typed in by hand except what the code or the batch files state.
"""

import json
import os
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))          # 8.ProjectCode
BATCH = os.path.dirname(CODE)                           # CSE-A-A1
DOCS = os.path.join(CODE, "docs")
DIAG = os.path.join(DOCS, "diagrams")
FIGS = os.path.join(DOCS, "figures")
SHOTS = os.path.join(DOCS, "screenshots")
EXP_DIR = os.path.join(CODE, "experiments")
TEMPLATES = r"D:\abstracts\Templates"

PRODUCT = "Adaptive Learning Intelligence Platform"
SHORT = "ALIP"
TITLE = "Adaptive Learning Intelligence Platform Using Educational Document Analysis and Personalized Learning Analytics"
BATCH_NO = "A1"
SECTION = "CSE-A"
DEPT = "Department of Computer Science and Engineering"
COLLEGE = "TKR College of Engineering & Technology (An Autonomous Institution)"
COLLEGE_SHORT = "TKR College of Engineering & Technology"
ADDRESS = "[COLLEGE ADDRESS]"
YEAR = "[ACADEMIC YEAR]"
PLACE = "[PLACE]"
DATE = "[DATE]"
STUDENTS = [
    ("A Dhanush", "23K91A0501"),
    ("Ale Vijayalaxmi", "23K91A0508"),
    ("Burri Mallikarjun", "23K91A0549"),
    ("Atragada Nagatrimurthulu", "23K91A0517"),
]
GUIDE = "Raghavendra"
GUIDE_DESIGNATION = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"

BASE_PAPER = ("D. Zhang, H. Yu, J. Huo and M. Su, \"SAC-RAG: Semantic Adaptive Context Compression for Retrieval-Augmented Generation,\" "
              "IEEE Access, vol. 14, pp. 117406-117418, 2026, doi: 10.1109/ACCESS.2026.3718025.")


def _load(path):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


RESULTS = _load(os.path.join(EXP_DIR, "results.json"))
API = _load(os.path.join(EXP_DIR, "api_latency.json"))
AUDIT = _load(os.path.join(EXP_DIR, "quiz_audit.json"))
DENSE = _load(os.path.join(EXP_DIR, "dense_meta.json"))

CORPUS = RESULTS["corpus"]                 # documents, chunks, words, questions ...
RET = RESULTS["retrieval"]                 # name -> {hit{1..10}, mrr10, by_type{fact,definition,reasoning}, first_rank}
RET_CI = RESULTS["retrieval_ci_shipped"]
CHUNKS = RESULTS["chunk_sizes"]            # "180/30" -> {...}
CMP = RESULTS["compression"]               # "1","2","4","6","8", by_type_k4, k4_given_retrieval_hit
ABS = RESULTS["abstention"]
DOCAN = RESULTS["document_analysis"]
QUIZ = RESULTS["quiz"]
SCALE = RESULTS["scaling"]                 # list by index size
SHIPPED = "tfidf_shipped (1-2gram)"

# pytest result
_t = ET.parse(os.path.join(EXP_DIR, "pytest_report.xml")).getroot()
_ts = _t.find("testsuite") if _t.tag != "testsuite" else _t
TESTS = {"tests": int(_ts.get("tests")), "failures": int(_ts.get("failures")), "errors": int(_ts.get("errors")),
         "skipped": int(_ts.get("skipped")), "seconds": float(_ts.get("time"))}
TEST_FILES = {"test_api.py": 45, "test_text_extraction.py": 15, "test_security.py": 11, "test_rag_engine.py": 9, "test_quiz_generator.py": 4}
SMOKE_TOTAL = 24

RET_LABELS = {
    "tfidf_shipped (1-2gram)": "TF-IDF 1-2 gram (shipped)", "tfidf_unigram": "TF-IDF unigram", "bm25": "BM25",
    "tfidf_lsa200": "TF-IDF + LSA (200)", "hybrid_bm25_lsa": "BM25 + LSA", "dense_bge_small": "Dense BGE-small",
    "hybrid_bm25_dense": "BM25 + dense BGE-small",
}

ENV = {"cpu": "Intel Core i5-12500 (6 cores, 12 threads)", "ram": "15.7 GB", "os": "Windows 11 Pro", "gpu": "none (CPU only)",
       "python": "3.11.9", "sklearn": "1.5.1", "numpy": "1.26.4", "fastapi": "0.115.0", "uvicorn": "0.30.6", "flask": "3.0.3",
       "pypdf": "4.3.1", "python-docx": "1.1.2", "node": "24.19.0", "react": "19", "vite": "8.3", "tailwind": "4"}

# code size (lines), measured
LOC = {"application (9 Python files)": 1252, "tests (6 files)": 631, "scripts (measurement, figures, screenshots)": 2160,
       "frontend (53 TS/TSX files)": 4867, "original Flask templates (10 files)": 439}

SCREENS = [
    ("01_landing-light.png", "Landing page (light theme)"), ("02_landing-dark.png", "Landing page (dark theme)"),
    ("03_login.png", "Login"), ("04_register.png", "Registration"),
    ("05_upload-ready.png", "Upload: file and subject chosen"), ("06_upload-done.png", "Upload: document processed, topics detected"),
    ("07_dashboard.png", "Dashboard"), ("08_documents.png", "Documents (knowledge repository)"),
    ("09_ask.png", "Ask your notes: answer with sources"), ("10_quiz-picker.png", "Quiz: choose a document"),
    ("11_quiz-taking.png", "Quiz in progress"), ("12_quiz-result.png", "Quiz result and review"),
    ("13_roadmap.png", "Study roadmap"), ("14_dashboard-dark.png", "Dashboard (dark theme)"),
    ("15_mobile-dashboard.png", "Dashboard on a 360 px phone"), ("16_mobile-ask.png", "Ask page on a 360 px phone"),
    ("17_tablet-roadmap.png", "Roadmap on a 768 px tablet"), ("18_mobile-roadmap-dark.png", "Roadmap on a phone, dark theme"),
]


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def f2(x):
    return f"{x:.2f}"


def f3(x):
    return f"{x:.3f}"


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


def hit(name, k):
    return RET[name]["hit"][str(k)]


def ret_row(name, ks=(1, 3, 4, 10)):
    r = RET[name]
    return [RET_LABELS[name]] + [f"{r['hit'][str(k)]:.3f}" for k in ks] + [f"{r['mrr10']:.3f}"]
