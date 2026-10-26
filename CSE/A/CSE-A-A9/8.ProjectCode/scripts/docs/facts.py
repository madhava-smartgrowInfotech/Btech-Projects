"""
Single source of truth for the documentation build of BotGraph (CSE-A-A9).

Batch details come from 1.A9_BATCH_DETAILS.docx / Students.txt. Performance numbers are read at build time from the JSON files written by the
experiment scripts (experiments/metrics.json, scalability.json, eval/metrics.json, extra/metrics.json) - nothing is typed in by hand except what the
code or the batch files state. docs/REPORT_FACTS.md is the human-readable copy; docs/NARRATIVE.md fixes the story.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))          # 8.ProjectCode
BATCH = os.path.dirname(CODE)                           # CSE-A-A9
DOCS = os.path.join(CODE, "docs")
DIAG = os.path.join(DOCS, "diagrams")
FIGS = os.path.join(DOCS, "figures")
SHOTS = os.path.join(DOCS, "screenshots")
EXP = os.path.join(CODE, "experiments")

REPORT = False   # set True by build_docs.doc17 so content modules can emit the compact report variant
PRODUCT = "BotGraph"
TITLE = "Graph Neural Network Analysis for Scalable Fake Profile Detection and Botnets"
SUBTITLE = "GCN, GAT and GraphSAGE on a social graph, with Louvain botnet clusters and a moderator review loop"
FULL_TITLE = TITLE
TAGLINE = "BotGraph: fake accounts and coordinated botnets found from the shape of the social graph"
BATCH_NO = "A9"
SECTION = "CSE-A"
DEPT = "Department of Computer Science and Engineering"
COLLEGE = "TKR College of Engineering & Technology (An Autonomous Institution)"
COLLEGE_SHORT = "TKR College of Engineering & Technology"
ADDRESS = "Medbowli, Meerpet, Balapur, Hyderabad, Telangana - 500 097"
YEAR = "[ACADEMIC YEAR]"
PLACE = "[PLACE]"
DATE = "[DATE]"
STUDENTS = [
    ("Bijja Naga Lakshmi", "23K91A0538"),
    ("Divvela Srivatshav", "23K91A0564"),
    ("Adumulla Durga", "23K91A0504"),
    ("Burugula Koushik", "23K91A0550"),
]
STUDENTS_UPPER = [(n.upper(), r) for n, r in STUDENTS]
GUIDE = "Neelima"
GUIDE_DESIGNATION = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"

BASE_PAPER = ("A. Saha, N. K. Sarkar and S. Pratihar, \"PruferNET: An augmented graph neural network for influential node detection in social networks,\" "
              "IEEE Access, vol. 14, pp. 79940-79959, 2026, doi: 10.1109/ACCESS.2026.3695637.")
BASE_SHORT = "Saha et al. (IEEE Access, 2026)"
API_PORT, WEB_PORT = 8309, 5309


def _load(*p):
    path = os.path.join(*p)
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


M = _load(EXP, "metrics.json")                 # three-seed comparison, served model, cluster recovery
SC = _load(EXP, "scalability.json")            # scalability sweep
EV = _load(EXP, "eval", "metrics.json")
EXTRA = _load(EXP, "extra", "metrics.json")    # threshold sweep, error analysis, feature-group ablation (scripts/run_extra_experiments.py)
GMETA = _load(CODE, "data", "processed", "graph_meta.json")
MODELS = M["models"]
BEST = M["meta"]["best"]                       # 'sage'
REC = M["cluster_recovery"]
SPLITS = M["meta"]["splits"]

ORDER = ["baseline", "gcn", "gat", "sage"]
LABEL = {"baseline": "Feature-only baseline (MLP)", "gcn": "GCN", "gat": "GAT", "sage": "GraphSAGE"}

# graph facts (docs/REPORT_FACTS.md section 3)
NODES, EDGES = 4533, 94456
REAL_NODES, INJ_NODES = 3963, 570
REAL_EDGES, INJ_EDGES = 88156, 6300
FAKE, FAKE_SHARE = 570, 0.126
TEST_N, TEST_FAKE = 908, 114
N_FEATURES = 23
BOTNET_SIZES = [62, 50, 52, 60, 48, 56, 58, 34]
LONE_SPAMMERS = 150
CAMO_BOTS, SUSPICIOUS_GENUINE = 198, 231
FLAGGED = 548

# tests and measurements (docs/REPORT_FACTS.md sections 7-9)
SMOKE_TOTAL, SMOKE_PASSED = 36, 36
LATENCY = {  # median / p95 ms, 20 requests each, 127.0.0.1, warm server
    "GET /api/health": (11.1, 20.1), "GET /api/overview": (12.6, 26.9), "GET /api/graph/summary": (8.3, 22.8),
    "GET /api/accounts (25 rows)": (8.9, 23.1), "GET /api/accounts/{id}": (10.6, 27.5),
    "GET /api/accounts/{id}/neighbourhood": (13.8, 28.4), "GET /api/clusters": (15.0, 23.2),
    "GET /api/queue": (6.7, 22.4), "GET /api/models": (16.0, 24.3), "GET /api/models/scalability": (3.0, 27.7),
}
LOGIN_MS = 233
STARTUP_S = 5.1
HARDWARE = "12th Gen Intel Core i5-12500 (6 cores, 12 threads), 16 GB RAM, Windows 11 Pro, CPU only"

# PruferNET as printed in the base paper (different task and data - never compared like for like)
BASE_PAPER_RESULTS = {
    "task": "3-class node classification by depth in a minimum spanning tree (Very Shallow / Shallow / Deep)",
    "data": "SNAP Facebook, 4,039 nodes and 88,234 edges; Email-Eu-core, 986 nodes and 16,064 edges",
    "with_prufer_acc": 0.9963, "without_prufer_acc": 0.9654, "split": "60/20/20",
    "model": "GraphSAGE, 64 hidden units, dropout 0.5, AdamW lr 0.003, 300 epochs", "hardware": "T4 GPU, 16 GB RAM",
}


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def f2(x):
    return f"{x:.2f}"


def f3(x):
    return f"{x:.3f}"


def f4(x):
    return f"{x:.4f}"


def ms(x, d=1):
    return f"{x:.{d}f} ms"


def mean(model, key):
    return MODELS[model][key]["mean"]


def std(model, key):
    return MODELS[model][key]["std"]


def mstd(model, key, d=3):
    s = MODELS[model][key]
    return f"{s['mean']:.{d}f} ± {s['std']:.{d}f}"


def lift(model):
    """F1 gain over the feature-only baseline, in F1 points."""
    return (mean(model, "f1") - mean("baseline", "f1")) * 100


def conf(model):
    c = MODELS[model]["confusion"]      # seed 0 only
    return c["tn"], c["fp"], c["fn"], c["tp"]


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


def scal_row(scale):
    for r in SC["rows"]:
        if r["scale"] == scale:
            return r
    raise KeyError(scale)
