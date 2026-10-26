"""
Single source of truth for the documentation build of AgriVision (CSE-C-C16).

Batch details come from 1.C16_BATCH_DETAILS.docx / Students.txt. Every measured number is read at build time from
experiments/plantdoc/metrics.json (scripts/run_experiments.py), experiments/plantdoc/latency.json (scripts/measure_api.py) and
docs/metrics/edge_tests.json (scripts/edge_tests.py). docs/REPORT_FACTS.md is the human-readable version of the same numbers;
documents must agree with it. Build strings from F, never type a measured number by hand.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))          # 8.ProjectCode
BATCH = os.path.dirname(CODE)                           # CSE-C-C16
DOCS = os.path.join(CODE, "docs")
DIAG = os.path.join(DOCS, "diagrams")
FIGS = os.path.join(DOCS, "figures")
SHOTS = os.path.join(DOCS, "screenshots")
EXP = os.path.join(CODE, "experiments", "plantdoc")

PRODUCT = "AgriVision"
TITLE = "AI Powered Crop Disease Detection and Recommendation System for Sustainable Development"
BATCH_NO = "C16"
SECTION = "CSE-C"
DEPT = "Department of Computer Science and Engineering"
COLLEGE = "[COLLEGE NAME]"
COLLEGE_SHORT = "[COLLEGE NAME]"
ADDRESS = "[COLLEGE ADDRESS]"
YEAR = "[ACADEMIC YEAR]"
PLACE = "[PLACE]"
DATE = "[DATE]"
STUDENTS = [
    ("Pishke Vishal", "23K91A05J2"),
    ("Kyatham Nithisha", "23K91A05D1"),
    ("Mekala Tharun Kuruma", "23K91A05F1"),
    ("Nakka Sreenith", "23K91A05H0"),
]
GUIDE = "V Krishna Teja"
GUIDE_DESIGNATION = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"

BASE_PAPER = ("N. Pakka, T. Wilkerson, L. Chen and N.-F. Tzeng, \"Foliagen: Framework for crop foliage image generation from individual leaf images,\" "
              "IEEE Access, 2026, doi: 10.1109/ACCESS.2026.3727421.")
KEYWORDS = ["Crop Disease Detection", "Agricultural AI", "Computer Vision", "Leaf Disease Classification", "Fertilizer Recommendation",
            "Yield Prediction", "Sustainable Agriculture", "Multilingual Farming Support"]


def _load(path):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


M = _load(os.path.join(EXP, "metrics.json"))
LAT = _load(os.path.join(EXP, "latency.json"))
EDGE = _load(os.path.join(DOCS, "metrics", "edge_tests.json"))
DS = M["dataset"]
H = M["heuristic"]                  # shipped engine, 5 hash seeds
HC, HG = H["test_crop_hint"], H["test_general"]
H0 = H["shipped_hashseed0"]["test_crop_hint"]
C = M["cnn"]                        # shipped compact CNN, held-out validation, 3 seeds
CS = M["cnn_shipped_protocol"]      # shipped protocol (test folder as validation), seed 42
CT = M["cnn_tuned"]                 # no LR decay, seed 42
MB = M["mobilenet"]                 # MobileNetV2 transfer, 3 seeds
BL = M["baseline"]                  # random forest / logistic regression on hand-made features
NTRAIN, NTEST = DS["n_train"], DS["n_test"]
HCONF = _load(os.path.join(EXP, "heuristic_confidence.json"))   # confidence vs correctness of the heuristic (160 answerable test photos)

N_SMOKE = 39
N_UI = 55
N_EDGE, N_EDGE_PASS, N_EDGE_DEFECT = EDGE["total"], EDGE["PASS"], EDGE["DEFECT"]
N_UNIT = EDGE["by_group"]["unit"]["PASS"] + EDGE["by_group"]["unit"]["DEFECT"]
N_API = EDGE["by_group"]["api"]["PASS"] + EDGE["by_group"]["api"]["DEFECT"]

LOC = {"agrivision": 905, "backend": 437, "frontend": 5647, "scripts": 1448}

HARDWARE = "Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB RAM, Windows 11 Pro, CPU only (no GPU)"
SOFTWARE = ("Python 3.11.9, TensorFlow 2.21.0 (Keras 3), scikit-learn 1.5.0, OpenCV 4.11, Pillow 12.3, FastAPI, Flask 3.1, reportlab 4.1, "
            "Node 24.19, React 18.3, Vite 8, TypeScript 5.9, Tailwind CSS 4")


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def f2(x):
    return f"{x:.2f}"


def f3(x):
    return f"{x:.3f}"


def pm(blk, key="accuracy", d=1, as_pct=True):
    """'12.0 +/- 0.5 %' from an aggregated block with {key: {mean, std}}."""
    s = 100 if as_pct else 1
    v = blk[key]
    return f"{v['mean'] * s:.{d}f} ± {v['std'] * s:.{d}f}" + ("%" if as_pct else "")


def mean_pct(blk, key="accuracy", d=1):
    return f"{blk[key]['mean'] * 100:.{d}f}%"


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


def src(rel, start=None, end=None):
    """Lines start..end (1-based, inclusive) of a source file of 8.ProjectCode, for code listings."""
    lines = open(os.path.join(CODE, rel), encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    return "\n".join(lines[(start or 1) - 1:end or len(lines)]).rstrip("\n")
