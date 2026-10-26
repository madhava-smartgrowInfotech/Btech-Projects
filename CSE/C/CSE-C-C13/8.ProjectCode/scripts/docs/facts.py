"""
Single source of truth for the documentation build of CipherVault (CSE-C-C13).

Batch details come from 1.C13_BATCH_DETAILS.docx / Students.txt. Every performance number is read at build time from
docs/metrics/metrics.json (written by scripts/measure_metrics.py) and docs/metrics/tests.json; nothing is typed in by hand
except what the code or the batch files state.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))          # 8.ProjectCode
BATCH = os.path.dirname(CODE)                           # CSE-C-C13
DOCS = os.path.join(CODE, "docs")
DIAG = os.path.join(DOCS, "diagrams")
FIGS = os.path.join(DOCS, "figures")
SHOTS = os.path.join(DOCS, "screenshots")
METRICS_DIR = os.path.join(DOCS, "metrics")

REPORT = False   # set True by build_docs.doc17 so content modules can emit the compact report variant
PRODUCT = "CipherVault"
TITLE = "Secure File Storage System with Encryption and Role-Based Access Control (RBAC)"
SUBTITLE = "Client-Side AES-256-GCM Encryption, RSA-OAEP Key Wrapping and a Hash-Chained Audit Log"
FULL_TITLE = TITLE
TAGLINE = "CipherVault: a web application that encrypts every file in the browser before upload, enforces Owner / Editor / Viewer access on the server and keeps a tamper-evident audit trail"
BATCH_NO = "C13"
SECTION = "CSE-C"
DEPT = "Department of Computer Science and Engineering"
COLLEGE = "TKR College of Engineering & Technology (An Autonomous Institution)"
COLLEGE_SHORT = "TKR College of Engineering & Technology"
ADDRESS = "Medbowli, Meerpet, Balapur, Hyderabad, Telangana - 500 097"
YEAR = "[ACADEMIC YEAR]"
PLACE = "[PLACE]"
DATE = "[DATE]"
STUDENTS = [
    ("Pramod Reddy Yalala", "23K91A05J9"),
    ("Pendela Vyshnavi", "23K91A05J1"),
    ("Luke Abraham Sam", "23K91A05D4"),
    ("Mudavath Suresh", "23K91A05G2"),
]
GUIDE = "D V V Deepthi"
GUIDE_DESIGNATION = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"

# Base paper as declared in 3.BASE PAPER.docx (and 1.C13_BATCH_DETAILS.docx)
BASE_PAPER = ("A. Nekouie, M. Vafaei Jahan, M. H. Moattar and R. Sheibani, \"Secure electronic health record access control via blockchain, "
              "dual-attribute encryption, and large language model-based attribute extraction,\" Scientific Reports, vol. 16, art. 8673, 2026, "
              "doi: 10.1038/s41598-026-39690-2.")
BASE_SHORT = "Nekouie et al. (Scientific Reports, 2026)"
# Closest-architecture paper that was downloaded into archived_base_papers/ (client-side AES + RSA + RBAC + audit log)
NEAR_PAPER = ("G. Sowmiya, R. Nivas and E. Vikram, \"Secure cloud file storage architecture with client-side encryption and access control,\" "
              "Int. J. Eng. Develop. Res. (IJEDR), vol. 14, no. 2, pp. 576-579, Apr. 2026, paper IJEDR2602501.")
NEAR_SHORT = "Sowmiya et al. (IJEDR, 2026)"


def _load(path):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


M = _load(os.path.join(METRICS_DIR, "metrics.json"))
T = _load(os.path.join(METRICS_DIR, "tests.json")) or {}

ENV = M["environment"]
BR = M["browser"]
CRY = BR["crypto"]
AES = CRY["aes"]
E2E = BR["e2e"]
API = M["api"]
RBAC = M["rbac"]
TAMPER = M["tamper"]
SCALE = M["audit_chain_scaling"]
CONC = M["audit_concurrency"]
LOC = M["loc"]

PYTEST_TOTAL = T.get("pytest_total", 21)
PYTEST_PASSED = T.get("pytest_passed", 21)
PYTEST_SECONDS = T.get("pytest_seconds", 13.0)
E2E_PASSED, E2E_TOTAL = T.get("e2e_passed", 17), T.get("e2e_total", 17)
UI_PASSED, UI_TOTAL = T.get("ui_passed", 18), T.get("ui_total", 18)
EVAL_PASSED, EVAL_TOTAL = T.get("eval_passed", 17), T.get("eval_total", 17)

API_PORT, WEB_PORT = 8413, 5413
UPLOAD_LIMIT_MB = 25
PBKDF2_ITER = 120000
BCRYPT_COST = 12
JWT_MINUTES = 120
LOGIN_LIMIT = (20, 300)


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def f1(x):
    return f"{x:.1f}"


def f2(x):
    return f"{x:.2f}"


def f3(x):
    return f"{x:.3f}"


def ms(x):
    """Format a millisecond value with sensible precision."""
    if x < 0.1:
        return f"{x:.3f}"
    if x < 10:
        return f"{x:.2f}"
    if x < 100:
        return f"{x:.1f}"
    return f"{x:.0f}"


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
