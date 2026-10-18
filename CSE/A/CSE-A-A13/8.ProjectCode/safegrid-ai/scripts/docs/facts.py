"""
Single source of truth for the documentation build.

Batch details come from the batch documents; every number comes from docs/results/experiment_3seeds_24steps.json
(produced by running this repository) or from the measurements recorded in docs/REPORT_FACTS.md. Nothing is copied from a paper.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CODE = os.path.dirname(os.path.dirname(HERE))          # 8.ProjectCode/safegrid-ai
BATCH = os.path.dirname(os.path.dirname(CODE))          # CSE-A-A13
DOCS = os.path.join(CODE, "docs")
DIAG = os.path.join(DOCS, "diagrams")
FIGS = os.path.join(DOCS, "figures")
SHOTS = os.path.join(DOCS, "screenshots")
RESULTS = os.path.join(DOCS, "results", "experiment_3seeds_24steps.json")

TITLE = "SafeGrid-AI: An Explainable Multi-Agent System for Dynamic Power Routing"
SHORT = "SafeGrid-AI"
BATCH_NO = "A13"
SECTION = "CSE-A"
DEPT = "Department of Computer Science and Engineering"
COLLEGE = "TKR College of Engineering and Technology (Autonomous)"
CITY = "[CITY]"
YEAR = "[ACADEMIC YEAR]"
STUDENTS = [
    ("DISHA KAUSHAL", "23K91A0563"),
    ("BOLLAM RAKESH", "23K91A0542"),
    ("CHINNOLLA RAVINDHAR", "23K91A0554"),
    ("AFFAN MOHAMMED RAMY", "23K91A0505"),
]
GUIDE = "CHANDRASHEKAR"
GUIDE_DESIGNATION = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"
BASE_PAPER = ("S. E. Eyimaya and N. Altin, \"Design of multi-agent-based energy management system for DC microgrids,\" "
              "IEEE Access, vol. 14, pp. 39120-39133, 2026, doi: 10.1109/ACCESS.2026.3672618.")

SCENARIOS = ["normal", "high_solar", "peak_demand", "battery_stress", "line_congestion", "voltage_violation", "unsafe_ai_action"]
SCEN_STEPS = {"normal": 32, "high_solar": 24, "peak_demand": 24, "battery_stress": 16, "line_congestion": 16, "voltage_violation": 16, "unsafe_ai_action": 12}
ARMS = ["baseline_rule", "agents_unshielded", "safegrid_shielded"]
ARM_LABEL = {"baseline_rule": "Rule baseline", "agents_unshielded": "Agents, no shield", "safegrid_shielded": "SafeGrid-AI"}

R = json.load(open(RESULTS, encoding="utf-8"))
OVERALL = R["overall"]
BYSC = R["by_scenario"]


def mean(arm, key):
    return OVERALL[arm][key]["mean"]


def sc_mean(sc, arm, key):
    return BYSC[sc][arm][key]["mean"]


def total(key, arm="safegrid_shielded"):
    """Sum over the 21 runs of an arm (mean x runs)."""
    return sum(r["summary"][key] for r in R["runs"] if r["arm"] == arm)


# ---- headline numbers, derived from the run records
N_RUNS = len(R["runs"])
PROPOSALS = round(total("proposals"))
APPROVED = round(total("approved"))
PROJECTED = round(total("projected"))
REJECTED = round(total("rejected"))
SAFETY_EVENTS = 354
CONFLICTS = 241
UNSHIELDED_CAUSED = round(total("violations_caused_by_actions", "agents_unshielded"))
UNSHIELDED_CAUSED_STEPS = round(total("violation_steps_caused_by_actions", "agents_unshielded"))
BASELINE_CAUSED = round(total("violations_caused_by_actions", "baseline_rule"))
BASELINE_CAUSED_STEPS = round(total("violation_steps_caused_by_actions", "baseline_rule"))
SHIELDED_CAUSED = round(total("violations_caused_by_actions"))
RAW_WOULD = round(total("violations_without_shield"))
RAW_WOULD_STEPS = round(total("violation_steps_without_shield"))
SHIELDED_STEPS = sum(r["summary"].get("steps", 24) for r in R["runs"] if r["arm"] == "safegrid_shielded")

API_LAT = [  # call, n, median ms, p95 ms  (live uvicorn, scenario unsafe_ai_action, seed 42; REPORT_FACTS section 5)
    ("GET /api/health", 50, 1.7, 15.4),
    ("GET /api/grid/state", 50, 2.5, 25.5),
    ("GET /api/scenarios", 50, 2.7, 23.2),
    ("GET /api/agents", 30, 2.7, 16.2),
    ("POST /api/agents/{id}/decision (agent proposal, dry run)", 30, 62.8, 84.5),
    ("POST dry run, unsafe 1000 kW export (rejected)", 30, 36.6, 80.5),
    ("POST dry run, 9 kW charge (projected by bisection)", 30, 230.0, 262.6),
    ("POST /api/simulation/step", 12, 440.7, 522.2),
]
TESTS = dict(total=55, passed=52, failed=2, hung=1, seconds=55, safety=22, agents=12, simulation=11, grid=6, api=4)
MACHINE = "Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB RAM, Windows 11 Pro, no GPU used"
LOC = dict(backend=3117, tests=624, frontend=6989)


def pct(x, d=1):
    return f"{x * 100:.{d}f}%"


def f1(x):
    return f"{x:.1f}"


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
