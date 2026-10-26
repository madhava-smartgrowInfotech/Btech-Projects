"""
Single source of truth for the documentation build of AegisBallot (CSE-C-C1).

Batch details come from 1.C1_BATCH_DETAILS.docx / Students.txt. Every measured number is read at build time from
experiments/voting/metrics.json (scripts/run_experiments.py), experiments/voting/benchmark_1000_voters.json (the product's own
`python -m app.benchmarks.run_benchmark --voters 1000`), benchmark_results/*.json (earlier idle-PC runs) and docs/metrics/tests.json.
docs/REPORT_FACTS.md is generated from the same files (scripts/docs/make_report_facts.py) and states every limitation in prose.
"""

import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))          # 8.ProjectCode
BATCH = os.path.dirname(CODE)                           # CSE-C-C1
DOCS = os.path.join(CODE, "docs")
DIAG = os.path.join(DOCS, "diagrams")
FIGS = os.path.join(DOCS, "figures")
SHOTS = os.path.join(DOCS, "screenshots")
METRICS_DIR = os.path.join(DOCS, "metrics")
EXP = os.path.join(CODE, "experiments", "voting")

REPORT = False   # set True by build_docs.doc17 so content modules can emit the compact report variant
PRODUCT = "AegisBallot"
TITLE = "Secure Voting System with Aadhaar Verification through Blockchain"
SUBTITLE = "A Local Permissioned-Ledger E-Voting Platform with Verhoeff-Checked Aadhaar Identity, Encrypted Ballots and Auditor Tools"
FULL_TITLE = "SECURE VOTING SYSTEM WITH AADHAR VERIFICATION THROUGH BLOCKCHAIN"
TAGLINE = ("AegisBallot: a local web application in which a voter proves identity with a Verhoeff-checked, hashed Aadhaar number, receives a single-use token, "
           "casts an AES-256-GCM encrypted ballot that is committed to a three-validator, Ed25519-signed hash-chained ledger, and keeps a receipt that an auditor can check")
BATCH_NO = "C1"
SECTION = "CSE-C"
DEPT = "Department of Computer Science and Engineering"
COLLEGE = "TKR College of Engineering & Technology (An Autonomous Institution)"
COLLEGE_SHORT = "TKR College of Engineering & Technology"
ADDRESS = "Medbowli, Meerpet, Balapur, Hyderabad, Telangana - 500 097"
YEAR = "[ACADEMIC YEAR]"
PLACE = "[PLACE]"
DATE = "[DATE]"
STUDENTS = [
    ("Mohammed Anwar-Ul-Haq", "23K91A05F6"),
    ("Mohammad Mosin", "23K91A05F4"),
    ("Manda Akshitha", "23K91A05E4"),
    ("Kothlapur Ganesh", "24K95A0516"),
]
GUIDE = "B Shruthi"
GUIDE_DESIGNATION = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"

BASE_PAPER = ("A. Shaikh, N. Adhikari, A. Nazir, A. S. Shah, S. Baig and H. Al Shihi, \"Blockchain-enhanced electoral integrity: a robust model for secure digital voting systems in Oman,\" "
              "F1000Research, vol. 14, art. 223, 2025, doi: 10.12688/f1000research.160087.3.")
BASE_TITLE = "Blockchain-enhanced electoral integrity: a robust model for secure digital voting systems in Oman"
BASE_SHORT = "Shaikh et al. (F1000Research, 2025)"
BASE_NAME = "the Oman model"
API_PORT, WEB_PORT = 8401, 5401
DEMO_LOGINS = [("admin", "Admin@123", "ADMIN"), ("auditor", "Audit@123", "AUDITOR"), ("voter1 ... voter20", "Voter@01pass ... Voter@20pass", "VOTER")]


def _load(path):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


M = _load(os.path.join(EXP, "metrics.json")) or {}
B = _load(os.path.join(EXP, "benchmark_1000_voters.json")) or {}
T = _load(os.path.join(METRICS_DIR, "tests.json")) or {}

# earlier benchmark files committed with the product (idle PC, 2026-09-08): list of dicts with voters_count, sync, async_batches
IDLE_RUNS = [d for d in (_load(f) for f in sorted(glob.glob(os.path.join(CODE, "benchmark_results", "benchmark_*.json")))) if d]

ENV = M.get("environment", {})
MICRO = M.get("micro_timings", {})
GROWTH = M.get("growth", {})
STAGE = M.get("vote_stage_breakdown_ms_mean", {})
VALIDATE_BY_HEIGHT = GROWTH.get("validate_chain_by_height", {})
TAMPER = M.get("tamper_study", {})
TAMPER_CASES = TAMPER.get("cases", [])
HTTP = M.get("http", {})
LAT = HTTP.get("latency", {})
MATRIX = HTTP.get("matrix", [])

BENCH_SYNC = B.get("sync", {})
BENCH_BATCH = B.get("async_batches", {})
N_VOTERS_BENCH = B.get("voters_count", 1000)

PYTEST_TOTAL = T.get("pytest_total")
PYTEST_PASSED = T.get("pytest_passed")
PYTEST_SECONDS = T.get("pytest_seconds")
PYTEST_NAMES = T.get("pytest_names", [])
MATRIX_TOTAL = HTTP.get("matrix_summary", {}).get("total")
MATRIX_PASSED = HTTP.get("matrix_summary", {}).get("passed")

N_TAMPER = len(TAMPER_CASES)
N_TAMPER_PRODUCT = sum(1 for c in TAMPER_CASES if c["validate_chain_detects"])
N_TAMPER_STRICT = sum(1 for c in TAMPER_CASES if c["strict_audit_detects"])

# approximate per-transaction times read by eye from Figures 6 and 9 of the base paper (not tabulated there)
BASE_REG_MS_APPROX = 2000
BASE_VOTE_MS_APPROX = 3000      # asynchronous batch of 10 (Figure 9); about 4000 ms for single synchronous transactions (Figure 6)
BASE_VOTE_SYNC_MS_APPROX = 4000

# design constants of the product (read from the code)
N_TABLES = 13
N_VALIDATORS, QUORUM = 3, 2
TOKEN_MINUTES = 10
LOGIN_LIMIT = (10, 60)       # requests, seconds
VERIFY_LIMIT = (15, 60)


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def f1(x):
    return f"{x:.1f}"


def f2(x):
    return f"{x:.2f}"


def f3(x):
    return f"{x:.3f}"


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
