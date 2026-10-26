"""
Single source of truth for the documentation build of CipherVeil (CSE-A-A15).

Batch details come from 1.A15_BATCH_DETAILS.docx / Students.txt. Every performance number is read at build time from
experiments/eval/metrics.json (ml/eval.py), experiments/extra/metrics.json (scripts/run_experiments.py) and
experiments/extra/api_latency.json (scripts/measure_api.py). docs/REPORT_FACTS.md is the human-readable copy of the same numbers.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))          # 8.ProjectCode
BATCH = os.path.dirname(CODE)                           # CSE-A-A15
DOCS = os.path.join(CODE, "docs")
DIAG = os.path.join(DOCS, "diagrams")
FIGS = os.path.join(DOCS, "figures")
SHOTS = os.path.join(DOCS, "screenshots")
EXP = os.path.join(CODE, "experiments")
for _d in (DIAG, FIGS):
    os.makedirs(_d, exist_ok=True)

REPORT = False   # set True by build_docs.doc17 so content modules can emit the compact report variant
PRODUCT = "CipherVeil"
TITLE = "Data Protection Using Hybrid Encryption and Steganography"
SUBTITLE = "AES-256-GCM for the data, RSA-OAEP for the key, LSB steganography in a PNG for concealment"
FULL_TITLE = TITLE
TAGLINE = ("CipherVeil: a file is encrypted with a fresh AES-256-GCM key, the key is wrapped with the receiver's RSA public key, "
           "and the resulting bundle is hidden in the least significant bits of an ordinary-looking PNG")
BATCH_NO = "A15"
SECTION = "CSE-A"
DEPT = "Department of Computer Science and Engineering"
COLLEGE = "TKR College of Engineering & Technology (An Autonomous Institution)"
COLLEGE_SHORT = "TKR College of Engineering & Technology"
ADDRESS = "Medbowli, Meerpet, Balapur, Hyderabad, Telangana - 500 097"
YEAR = "[ACADEMIC YEAR]"
PLACE = "[PLACE]"
DATE = "[DATE]"
STUDENTS = [
    ("Allam Rakesh", "23K91A0509"),
    ("Bolleddu Shanker", "23K91A0543"),
    ("Agaram Sri Sarvagna", "23K91A0506"),
    ("B Akshay", "24K915A0504"),
]
STUDENTS_UPPER = [(n.upper(), r) for n, r in STUDENTS]
GUIDE = "Rajalakshmi"
GUIDE_DESIGNATION = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"

BASE_PAPER = ("S. Ahmad and S. Rass, \"ProSt: Provably secure homomorphic steganography,\" IEEE Access, vol. 14, pp. 14393-14409, 2026, "
              "doi: 10.1109/ACCESS.2026.3656995.")
BASE_SHORT = "Ahmad and Rass (IEEE Access, 2026)"
API_PORT, WEB_PORT = 8315, 5315
DEMO_USER, DEMO_PASSWORD = "demo", "Demo@12345"

# measured by the test runs (docs/REPORT_FACTS.md section 8)
PYTEST_TOTAL = PYTEST_PASSED = 39
PYTEST_CRYPTO, PYTEST_LSB, PYTEST_METRICS, PYTEST_API = 13, 9, 7, 10
SMOKE_TOTAL = SMOKE_PASSED = 21


def _load(*parts):
    path = os.path.join(EXP, *parts)
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


EV = _load("eval", "metrics.json")            # ml/eval.py
EX = _load("extra", "metrics.json")           # scripts/run_experiments.py
API = _load("extra", "api_latency.json")      # scripts/measure_api.py
S = EV["summary"]                              # headline numbers of the core evaluation


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def f1(x):
    return f"{x:.1f}"


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
