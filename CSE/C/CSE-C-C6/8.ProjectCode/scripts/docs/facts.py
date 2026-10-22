"""
Single source of truth for the documentation build of the Fake News Detection System (CSE-C-C6, product name TruthGlow).

Batch details are copied from 1.C6_BATCH_DETAILS.docx / Students.txt. Every measured number is read at build time from
experiments/liar2/metrics.json (written by scripts/docs_build/make_figures.py from the seed_*.json runs of scripts/run_experiments.py),
experiments/liar2/latency.json (scripts/measure_api.py), models/metrics.json (the shipped synthetic-demo model) and docs/metrics/tests.json.
docs/REPORT_FACTS.md is the human-readable version of the same numbers; documents must agree with it.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))          # 8.ProjectCode
BATCH = os.path.dirname(CODE)                           # CSE-C-C6
DOCS = os.path.join(CODE, "docs")
DIAG = os.path.join(DOCS, "diagrams")
FIGS = os.path.join(DOCS, "figures")
SHOTS = os.path.join(DOCS, "screenshots")
EXP = os.path.join(CODE, "experiments", "liar2")
MODELS = os.path.join(CODE, "models")

PRODUCT = "TruthGlow"
TITLE = "Fake News Detection System Using Feature Based Optimised MSVM Classification"
BATCH_NO = "C6"
SECTION = "CSE-C"
DEPT = "Department of Computer Science and Engineering"
COLLEGE = "[COLLEGE NAME]"
COLLEGE_SHORT = "[COLLEGE NAME]"
ADDRESS = "[COLLEGE ADDRESS]"
YEAR = "[ACADEMIC YEAR]"
PLACE = "[PLACE]"
DATE = "[DATE]"
STUDENTS = [
    ("Neela Mojes", "23K91A05H1"),
    ("Noor Saniya", "23K91A05H4"),
    ("Malkajgiri Akshitha", "23K91A05E2"),
    ("Maravajhala Radha Sri Aashritha", "23K91A05E7"),
]
GUIDE = "K Rajasekhar Rao"
GUIDE_DESIGNATION = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"

BASE_PAPER = ("M. Saad, S. Abdelrazek and I. R. Abdelmaksoud, \"An algorithmic system for Arabic fake news detection using neural networks and transformer "
              "embeddings with class weighting,\" Scientific Reports, vol. 16, Art. no. 12226, 2026, doi: 10.1038/s41598-026-45653-4.")
KEYWORDS = ["Fake News Detection", "Multi-Class Support Vector Machine (MSVM)", "Principal Component Analysis (PCA)", "Firefly Algorithm",
            "Metaheuristic Feature Optimization", "Misinformation Filtering"]
CLASSES = ["REAL", "PARTIALLY TRUE", "FAKE"]


def _load(path):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


A = _load(os.path.join(EXP, "metrics.json"))                  # aggregated LIAR2 results (mean/std over seeds)
DEMO = _load(os.path.join(MODELS, "metrics.json"))            # shipped synthetic-demo model
LAT = _load(os.path.join(EXP, "latency.json"))                # list: [liar2 model, demo model]
TESTS = _load(os.path.join(DOCS, "metrics", "tests.json"))
EA = A["error_analysis"]                                      # error analysis, seed 42, test split
LV = EA["label_vs_proba"]                                     # verdict vs probability disagreement
SEED42 = _load(os.path.join(EXP, "seed_42.json"))             # one full run (per-class, confusion matrix, Firefly history)
SEEDS = A["seeds"]
NTEST, NVALID, NTRAIN_FULL, NTRAIN = A["n_test"], A["n_valid"], A["n_train_full"], A["n_train_subsample"]

N_SMOKE, N_UNIT_LIB, N_UNIT_API = TESTS["smoke"], TESTS["unit_lib"], TESTS["unit_api"]
N_TESTS = N_SMOKE + N_UNIT_LIB + N_UNIT_API

# code size (lines), measured with wc -l
LOC = {"src": 488, "backend": 339, "streamlit_cli": 320, "frontend": 4865, "frontend_pages": 1303}

HARDWARE = "Intel Core i5-12500 (6 cores, 12 threads, 3.0 GHz), 15.7 GB RAM, Windows 11 Pro, no GPU used"
SOFTWARE = "Python 3.11.9, scikit-learn 1.9.1, NumPy 2.4.6, SciPy 1.17.1, pandas 3.0.6, FastAPI 0.159.1, uvicorn 0.54.0, Node 24.19.0, React 18.3, Vite 8, TypeScript 5.9, Tailwind CSS 4"


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def f2(x):
    return f"{x:.2f}"


def f3(x):
    return f"{x:.3f}"


def f4(x):
    return f"{x:.4f}"


def pm(blk, key="f1_macro", d=3):
    """'0.429 +/- 0.010' from an aggregated block such as A['proposed_test']."""
    return f"{blk[key]['mean']:.{d}f} ± {blk[key]['std']:.{d}f}"


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
