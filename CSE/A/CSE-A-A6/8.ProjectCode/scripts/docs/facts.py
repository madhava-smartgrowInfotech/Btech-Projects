"""
Single source of truth for the documentation build.

Nothing here is typed in by hand except batch details (copied from the batch documents) and
facts read from the code. All performance numbers are read from experiments/*/metrics.json,
experiments/api_latency.json and experiments/test_run.json at build time.
"""

import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))          # 8.ProjectCode
BATCH = os.path.dirname(CODE)                           # CSE-A-A6
DOCS = os.path.join(CODE, "docs")
DIAG = os.path.join(DOCS, "diagrams")
FIGS = os.path.join(DOCS, "figures")
SHOTS = os.path.join(DOCS, "screenshots")
EXP = os.path.join(CODE, "experiments")

TITLE = "Smart Alcohol Intoxication Detection and Prevention System Using AI"
PRODUCT = "Smart Rider Impairment Warning System for Two-Wheelers"
BATCH_NO = "A6"
SECTION = "CSE-A"
DEPT = "Department of Computer Science and Engineering"
COLLEGE = "TKR College of Engineering and Technology (Autonomous)"
CITY = "Hyderabad, Telangana"
YEAR = "[ACADEMIC YEAR]"
STUDENTS = [
    ("B PRANITHA", "23K91A0522"),
    ("BANTU KAVYA", "23K91A0531"),
    ("DASARI VIVEKA SARVESHWARI", "23K91A0560"),
    ("BEKKAM VAMSHI", "23K91A0534"),
]
GUIDE = "N. PADMAVATHI"
GUIDE_DESIGNATION = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"
BASE_PAPER = ("C.-L. Feng and T.-H. S. Li, \"Robust Driver State Assessment on an Embedded Platform Using a Fuzzy Belief "
              "Rule-Based Fusion of Eye Aspect Ratio and Voice Commands,\" IEEE Access, vol. 14, pp. 36158-36175, 2026, "
              "doi: 10.1109/ACCESS.2026.3670924.")

STATES = ["Normal", "Possible impairment or drowsiness", "Unable to assess"]


def _load(path):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


def exp(*parts):
    return _load(os.path.join(EXP, *parts))


_M = exp("cew_ear", "metrics.json") or {}
CEW = _M.get("cew")                       # shipped pipeline with quality gates (2,423 images)
GEO = _M.get("cew_geometry_only")         # same landmarks and EAR, no gates
ROB = _M.get("robustness")                # degraded-condition gating (open-eye faces)
RULES = exp("rule_engine", "metrics.json")   # scripted-stream behaviour of the rule engine
API_LAT = exp("api_latency", "metrics.json")
TESTS = exp("tests", "test_run.json")
HW = {"cpu": "12th Gen Intel Core i5-12500 (6 cores, 12 threads)", "ram": "15.7 GB", "gpu": "Intel UHD Graphics 770 (not used)",
      "os": "Windows 11 Pro", "python": "3.14.7", "mediapipe": "1.0.1"}


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def f2(x):
    return f"{x:.2f}"


def f3(x):
    return f"{x:.3f}"


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


def shot_w(path, base=4.1, max_h_in=3.4):
    """Picture width in inches that keeps the height under max_h_in."""
    from PIL import Image

    with Image.open(path) as im:
        w, h = im.size
    return min(base, 4.1, max_h_in * w / h)


def diag(name):
    return os.path.join(DIAG, name)


def fig(name):
    return os.path.join(FIGS, name)
