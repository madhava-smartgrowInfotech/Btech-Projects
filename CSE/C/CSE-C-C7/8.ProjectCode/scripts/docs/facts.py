"""
Single source of truth for the documentation build.

Nothing here is typed in by hand except the batch details (copied from the batch documents).
All performance numbers are read at build time from
  artifacts/metrics/model_metrics.json      (the shipped training run, seed 42)
  experiments/*.json                         (scripts/run_experiments.py, measure_api.py, collect_env.py)
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))          # 8.ProjectCode
BATCH = os.path.dirname(CODE)                           # CSE-C-C7
DOCS = os.path.join(CODE, "docs")
DIAG = os.path.join(DOCS, "diagrams")
FIGS = os.path.join(DOCS, "figures")
SHOTS = os.path.join(DOCS, "screenshots")
EXP = os.path.join(CODE, "experiments")

TITLE = "Personalized E-learning Course Recommendation System"
PRODUCT = "LearnPathIQ"
BATCH_NO = "C7"
SECTION = "CSE-C"
DEPT = "Department of Computer Science and Engineering"
COLLEGE = "[COLLEGE NAME]"
CITY = "[CITY]"
YEAR = "[ACADEMIC YEAR]"
STUDENTS = [
    ("PITTALA AKHILA", "23K91A05J3"),
    ("MUNDALA SANDHYA", "23K91A05G5"),
    ("MULA THANUJ REDDY", "23K91A05G4"),
    ("MAJJIGAPU JAGADESHWAR REDDY", "23K91A05E1"),
]
GUIDE = "K GAYATHRI"
GUIDE_DESIGNATION = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"
BASE_PAPER = ("C. P. Isiwu, L. C. Nnadi, and Y. Watanobe, \"From prediction to prescription: A Causal-AI for personalized learning path "
              "optimization in MOOCs,\" IEEE Access, vol. 14, pp. 29105-29118, 2026, doi: 10.1109/ACCESS.2026.3666619.")


def _load(path):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


METRICS = _load(os.path.join(CODE, "artifacts", "metrics", "model_metrics.json"))
SEEDS = _load(os.path.join(EXP, "seed_study.json"))
CEIL = _load(os.path.join(EXP, "ceiling.json"))
PROFILE = _load(os.path.join(EXP, "data_profile.json"))
REC = _load(os.path.join(EXP, "recsys_eval.json"))
FB = _load(os.path.join(EXP, "feedback_loop.json"))
ACT = _load(os.path.join(EXP, "action_scores.json"))
API_LAT = _load(os.path.join(EXP, "api_latency.json"))
TESTS = _load(os.path.join(EXP, "test_run.json"))
ENV = _load(os.path.join(EXP, "environment.json"))
CATALOG = _load(os.path.join(CODE, "data", "catalog", "courses.json"))

MODEL_LABEL = {"logistic_regression": "Logistic Regression", "random_forest": "Random Forest", "xgboost": "XGBoost"}
ACTIONS = ["quiz", "content", "forum", "homepage", "continue_course"]


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


def shot_view(name, max_h=1500):
    """Screenshot path for documents: very tall full-page captures are cropped to the first `max_h` pixels."""
    from PIL import Image

    p = os.path.join(SHOTS, name)
    with Image.open(p) as im:
        w, h = im.size
        if h <= max_h * 1.35:
            return p
        os.makedirs(os.path.join(FIGS, "_crops"), exist_ok=True)
        out = os.path.join(FIGS, "_crops", name)
        im.convert("RGB").crop((0, 0, w, max_h)).save(out)
        return out


def shot_w(path, base=5.6, max_h_in=6.4):
    """Picture width in inches that keeps the height under max_h_in."""
    from PIL import Image

    with Image.open(path) as im:
        w, h = im.size
    return min(base, max_h_in * w / h)


def diag(name):
    return os.path.join(DIAG, name)


def fig(name):
    return os.path.join(FIGS, name)
