"""SentinelFlow design diagrams (matplotlib, 150 dpi) -> docs/diagrams/.

    python -m scripts.docs.make_diagrams            # from 8.ProjectCode; writes all ten
Every diagram mirrors the code: app.py, monitoring/*, ml/*, security/*, database/db.py and frontend/src/*.
"""
from __future__ import annotations

from pathlib import Path

from .dgm_lib import *  # noqa: F401,F403

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------ 01 architecture
def architecture():
    fig, ax = canvas(9.6, 7.6, 100, 79)
    ax.text(40, 77, "SentinelFlow: browser, Flask API, pipeline modules, local files - one process, no authentication on the API", ha="center", fontsize=8, color=ORANGE, fontweight="bold")
    panel(ax, 1, 62, 72, 13.5, "TIER 1 - BROWSER (React 19 + Vite, port 5415; legacy Jinja dashboard on 8415)", fc=PALE_BLUE, fs=8.4)
    box(ax, 19.5, 67.6, 32, 7, "Pages: Landing, Login (browser-side demo gate)\nOverview, Detections, Analytics, Network health,\nMitigation, Model, Settings", BLUE, fs=6.9)
    box(ax, 55, 67.6, 32, 7, "src/api.js (axios) + lib/live.jsx polling\n/api/status every 2 s, detections, health;\nVite dev proxy forwards /api and /static/results", BLUE, fs=6.9)
    panel(ax, 1, 41, 72, 19, "TIER 2 - Flask application (app.py, port 8415, threaded)", fc=PALE_PURPLE, fs=8.4)
    box(ax, 19.5, 49.2, 32, 11.5, "12 JSON endpoints under /api\nstatus health interfaces detections\ndetections/latest mitigations settings(GET,POST)\nmonitor/start|stop  demo/start|stop  model/metrics", PURPLE, fs=6.6)
    box(ax, 55, 49.2, 32, 11.5, "process_window(): the shared inference\npipeline for live AND simulated windows\nstate: baseline deque(12), persistence counter,\nhealth sampler thread (every 5 s)", PURPLE, fs=6.6)
    panel(ax, 1, 14, 72, 25, "TIER 3 - pipeline modules", fc=PALE_TEAL, fs=8.4)
    mods = [(10.5, 31, "monitoring/\ninterface_manager\npacket_capture\n(MonitorEngine)"), (28.5, 31, "monitoring/\nsimulator\n(TrafficSimulator)\ntraffic_aggregator"), (46.5, 31, "ml/\nfeatures, model_loader\ntrain_model\nevaluate_model"), (64, 31, "security/\ndetector\ndistributed_analysis\nseverity, mitigation")]
    for x, y, t in mods:
        box(ax, x, y, 16.5, 9.5, t, TEAL, fs=6.5)
    box(ax, 19.5, 20, 34, 6.5, "Scapy sniff() -> packets -> 10-feature windows", NAVY, fs=6.7)
    box(ax, 55.5, 20, 34, 6.5, "Random Forest -> distributed risk -> severity -> action", NAVY, fs=6.7)
    panel(ax, 1, 1, 72, 11.5, "TIER 4 - local files and SQLite", fc=LIGHT, fs=8.4)
    box(ax, 15, 5.6, 25, 6.2, "data/sentinelflow.db (SQLite)\ndetections, mitigations,\nhealth_samples, settings", GREY, fs=6.4)
    box(ax, 42, 5.6, 24, 6.2, "models/\nsentinelflow_rf.joblib\nfeature_list, metadata", GREY, fs=6.4)
    box(ax, 63, 5.6, 17, 6.2, "results/\nmetrics.json, PNGs", GREY, fs=6.4)
    panel(ax, 76, 14, 23, 61, "OUTSIDE THE PROCESS", fc=PALE_ORANGE, ec=ORANGE, fs=8.4, tc=ORANGE)
    box(ax, 87.5, 65, 19, 9, "Network interface\n(Scapy + Npcap);\nneeds Administrator", ORANGE, fs=6.6)
    box(ax, 87.5, 53, 19, 9, "psutil\nCPU, memory,\nnet counters", ORANGE, fs=6.6)
    box(ax, 87.5, 41, 19, 9, "CICIDS2017 CSV\n(offline training,\nnot at runtime)", ORANGE, fs=6.6)
    box(ax, 87.5, 29, 19, 9, "OS firewall\n(never touched;\nstub returns applied: false)", ORANGE, fs=6.4)
    box(ax, 87.5, 18.5, 19, 7.5, "Administrator\n(analyst)", NAVY, fs=6.6)
    arrow(ax, (40, 62), (40, 60.5), "HTTP + JSON", color=NAVY, lw=1.6, lo=(8, 0), fs=6.8)
    arrow(ax, (40, 41), (40, 39.5), "import / call", color=NAVY, lw=1.6, lo=(8, 0), fs=6.8)
    arrow(ax, (40, 14), (40, 12.7), "read / write", color=NAVY, lw=1.6, lo=(8, 0), fs=6.8)
    arrow(ax, (73, 50), (77.5, 53), "", color=ORANGE, lw=1.4)
    arrow(ax, (73, 27), (77.5, 62), "", color=ORANGE, lw=1.4)
    save(fig, OUT / "01_system_architecture.png")


# --------------------------------------------------------- 02 high-level workflow
def workflow():
    fig, ax = canvas(9.8, 6.4, 100, 65.3)
    ax.text(50, 63.3, "Offline training once, then a repeating 10-second monitoring cycle", ha="center", fontsize=8.4, color=NAVY, fontweight="bold")
    panel(ax, 1, 38, 98, 22, "STAGE 1 - OFFLINE (python ml/train_model.py)", fc=PALE_BLUE, fs=8.6)
    xs = [10, 29, 48, 67, 86]
    items = [("1 LOAD", "CICIDS2017 CSVs in\ndata/raw, else\nsynthetic fallback"), ("2 CLEAN + MAP", "normalise names,\ndrop inf/NaN, forward->sent\nbackward->received"),
             ("3 AUGMENT", "6000 aggregated windows\nfrom the simulator\n(window-scale rows)"), ("4 TRAIN", "stratified 80/20,\nRandomForest 200 trees\nseed 42"),
             ("5 PERSIST", "joblib model, feature\nlist, metadata,\nmetrics, plots")]
    for x, (t, b) in zip(xs, items):
        box(ax, x, 48.5, 17, 12.5, f"{t}\n\n{b}", BLUE if x < 60 else NAVY, fs=6.4)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 8.5, 48.5), (b - 8.5, 48.5), color=NAVY, lw=1.5)
    ax.text(50, 36.0, "the persisted model and feature list are loaded once and reused for every window", ha="center", fontsize=7, color=GREY, style="italic")
    panel(ax, 1, 1, 98, 32, "STAGE 2 - ONLINE: one pass per window (live capture or Simulation Mode)", fc=PALE_TEAL, fs=8.6)
    xs2 = [10, 29, 48, 67, 86]
    it2 = [("A CAPTURE", "Scapy sniff() for the\nwindow, or simulator\npackets (no I/O)"), ("B AGGREGATE", "packets -> 10 features\n+ context: sources,\ndestinations, protocols"),
           ("C CLASSIFY", "Random Forest:\nBenign / Attack +\nconfidence"), ("D RISK + SEVERITY", "distributed risk (0..1)\nthen score ->\nLow/Medium/High/Critical"), ("E ACT + STORE", "quarantine / recommend /\nmonitor; row in SQLite;\ndashboard refresh")]
    for x, (t, b) in zip(xs2, it2):
        box(ax, x, 19, 17, 13.5, f"{t}\n\n{b}", TEAL if x < 60 else PURPLE, fs=6.4)
    for a, b in zip(xs2[:-1], xs2[1:]):
        arrow(ax, (a + 8.5, 19), (b - 8.5, 19), color=NAVY, lw=1.5)
    ax.text(50, 5.5, "quarantines lapse after 40 s (80 s for Critical) and are marked 'recovered'; the next window starts immediately", ha="center", fontsize=7, color=GREY, style="italic")
    save(fig, OUT / "02_high_level_workflow.png")


# ------------------------------------------------------------------ 03-05 DFDs
def dfd0():
    fig, ax = canvas(9.2, 4.7, 100, 51)
    ax.text(2, 48.8, "Level 0 data flow diagram (context)", fontsize=9, fontweight="bold", color=NAVY)
    box(ax, 12, 36, 18, 9, "Administrator", NAVY, fs=8.5)
    box(ax, 12, 10, 18, 9, "Network\ninterface /\nTraffic simulator", ORANGE, fs=8)
    box(ax, 88, 36, 18, 9, "psutil\n(host counters)", ORANGE, fs=8)
    box(ax, 88, 10, 18, 9, "CICIDS2017 CSV\n(offline)", ORANGE, fs=8)
    circle(ax, 50, 26, 13.5, "0\nSentinelFlow\nDetection &\nMitigation\nSystem", BLUE, fs=8.4)
    store(ax, 50, 4.5, 30, 6, "D1  SQLite + model files", fs=8)
    arrow(ax, (21, 38), (38, 31), "start / stop, settings,\nview requests", lo=(0, 4.2), fs=7)
    arrow(ax, (38.5, 23), (21, 33.5), "status, detections,\nmitigations, metrics", lo=(0, -4.5), fs=7, color=TEAL)
    arrow(ax, (21, 10), (38, 19.5), "packets (windows)", lo=(-1, -3), fs=7)
    arrow(ax, (79, 36), (62, 30), "CPU, memory,\nbytes, packets", lo=(1, 4.2), fs=7)
    arrow(ax, (79, 10), (62, 19.5), "labelled flow rows", lo=(2, -3), fs=7)
    arrow(ax, (46, 12.5), (46, 7.6), "", color=NAVY)
    arrow(ax, (54, 7.6), (54, 12.5), "", color=NAVY)
    save(fig, OUT / "03_dfd_level0.png")


def dfd1():
    fig, ax = canvas(9.8, 6.4, 100, 65.3)
    ax.text(2, 63, "Level 1 data flow diagram", fontsize=9, fontweight="bold", color=NAVY)
    box(ax, 8, 54, 13, 8, "Administrator", NAVY, fs=7.6)
    box(ax, 92, 54, 11, 7, "psutil", ORANGE, fs=7.6)
    box(ax, 8, 16, 13, 9, "Network /\nSimulator", ORANGE, fs=7.6)
    box(ax, 93, 3.5, 12, 6, "CICIDS2017\nCSV", ORANGE, fs=6.8)
    circle(ax, 32, 54, 7.4, "5.0\nAPI &\ndashboard", BLUE, fs=7)
    circle(ax, 64, 54, 7.0, "6.0\nHealth\nsampler", BLUE, fs=7)
    circle(ax, 30, 16, 7.4, "1.0\nCapture &\naggregate", TEAL, fs=6.8)
    circle(ax, 50, 16, 7.4, "2.0\nClassify\n(RF)", TEAL, fs=6.8)
    circle(ax, 70, 16, 7.4, "3.0\nRisk &\nseverity", TEAL, fs=6.8)
    circle(ax, 64, 38, 7.4, "4.0\nMitigate", TEAL, fs=7)
    circle(ax, 91, 18, 7.0, "7.0\nTrain\nmodel", PURPLE, fs=6.8)
    store(ax, 32, 38, 20, 5.6, "D1 detections", fs=7.4)
    store(ax, 91, 36, 16, 5.6, "D2 mitigations", fs=7.0)
    store(ax, 90, 46.5, 17, 5.6, "D4 health_samples", fs=6.8)
    store(ax, 72, 3.5, 18, 5.4, "D3 model files", fs=7.2)
    arrow(ax, (14.5, 55.5), (24.6, 55.5), "requests", lo=(0, 1.8), fs=6.4)
    arrow(ax, (24.6, 52.5), (14.5, 52.5), "responses", lo=(0, -1.8), fs=6.4, color=TEAL)
    arrow(ax, (14.5, 16), (22.6, 16), "packets", lo=(0, 1.8), fs=6.4)
    arrow(ax, (37.4, 16), (42.6, 16), "features", lo=(0, 2.4), fs=6.0)
    arrow(ax, (57.4, 16), (62.6, 16), "label", lo=(0, 2.4), fs=6.0)
    arrow(ax, (68, 23.4), (65.5, 30.6), "severity,\nrisk", lo=(6, 0), fs=6.0)
    arrow(ax, (57.0, 40.5), (38.5, 51.4), "actions", lo=(-2, 2.4), fs=6.2)
    arrow(ax, (70, 23.4), (40, 35.5), "detection record", lo=(-3, 0.8), fs=6.0, rad=0.0)
    arrow(ax, (32, 41.0), (32, 46.6), "queries", lo=(4, 0), fs=6.2, ls="--")
    arrow(ax, (71, 38), (83, 36.3), "quarantine rows", lo=(0, 2.2), fs=5.8)
    arrow(ax, (86.5, 54), (71, 54), "counters", lo=(0, 1.8), fs=6.2)
    arrow(ax, (70.0, 51.0), (82, 47.5), "samples", lo=(0, 2.0), fs=6.0)
    arrow(ax, (93, 6.5), (92, 11.0), "", color=NAVY)
    arrow(ax, (86.0, 14.0), (81, 6.5), "model, metrics", lo=(-1, -3.0), fs=6.0)
    arrow(ax, (63, 5.0), (52.5, 9.2), "load once", lo=(-3, -1.5), fs=6.0, ls="--")
    save(fig, OUT / "04_dfd_level1.png")


def dfd2():
    fig, ax = canvas(9.8, 6.4, 100, 65.3)
    ax.text(2, 63.3, "Level 2 data flow diagram: process 3.0 (risk and severity) and 4.0 (mitigation) expanded", fontsize=8.8, fontweight="bold", color=NAVY)
    box(ax, 9, 46, 15, 10, "From 1.0 / 2.0\nfeatures, context,\nlabel, confidence", NAVY, fs=6.5)
    circle(ax, 31, 54, 6.8, "3.1\nSource +\ndestination\ndiversity", TEAL, fs=6)
    circle(ax, 31, 38, 6.8, "3.2\nRate pressure\n+ baseline\ndeviation", TEAL, fs=6)
    circle(ax, 54, 46, 7.4, "3.3\nWeighted\nrisk score\n0.30/0.30/\n0.25/0.15", TEAL, fs=5.6)
    circle(ax, 77, 46, 7.4, "3.4\nSeverity\nscore + factors\n+ persistence", TEAL, fs=5.8)
    circle(ax, 88, 24, 7.2, "4.1\nChoose\naction by\nseverity", PURPLE, fs=6)
    circle(ax, 62, 14, 7.0, "4.2\nProtect\nlocal / loopback\naddresses", PURPLE, fs=5.7)
    circle(ax, 36, 14, 7.0, "4.3\nQuarantine\n40 s / 80 s,\nexpire", PURPLE, fs=5.8)
    store(ax, 13, 5, 22, 5.6, "D2 mitigations", fs=7.2)
    store(ax, 31, 24, 24, 5.6, "D5 baseline (12 windows)", fs=6.4)
    box(ax, 92, 52, 14, 8, "To 5.0 API\nrecord + actions", NAVY, fs=6.3)
    arrow(ax, (16.5, 49), (24.5, 53), "", color=NAVY)
    arrow(ax, (16.5, 43), (24.5, 39), "", color=NAVY)
    arrow(ax, (37.8, 53), (47, 49.5), "src/dst\ncomponents", lo=(1, 3.8), fs=5.8)
    arrow(ax, (37.8, 39), (47, 43), "rate, baseline\ncomponents", lo=(3, -3.8), fs=5.8)
    arrow(ax, (61.4, 46), (69.6, 46), "risk 0..1", lo=(0, 2.2), fs=5.8)
    arrow(ax, (29, 26.8), (29, 31.2), "mean rate", lo=(-5.5, 0), fs=5.6)
    arrow(ax, (33, 31.2), (33, 26.8), "new rate", lo=(5.0, 0), fs=5.6)
    arrow(ax, (82, 40.5), (87, 31.0), "severity", lo=(5, 1), fs=5.8)
    arrow(ax, (94, 31.2), (94, 47.8), "actions", lo=(-4.5, 0), fs=5.8)
    arrow(ax, (81, 21), (68.6, 16), "targets", lo=(0, 2.6), fs=5.8)
    arrow(ax, (55, 14), (43, 14), "allowed IPs", lo=(0, 2.4), fs=5.8)
    arrow(ax, (30, 10.6), (22, 6.3), "history", lo=(-1, 2.4), fs=5.8)
    arrow(ax, (84.4, 48.5), (85.4, 50.5), "", color=NAVY)
    save(fig, OUT / "05_dfd_level2.png")


# ------------------------------------------------------------------ 06 class diagram
def classes():
    fig, ax = canvas(9.8, 10.0, 100, 102)
    ax.text(1.5, 100.2, "UML class diagram (classes and module-level interfaces actually present in the code)", fontsize=8.6, fontweight="bold", color=NAVY)
    uml_class(ax, 1.5, 97, 30, "MonitorEngine", ["on_window", "running: bool", "interface: str", "window_seconds: int", "last_error: str", "windows_completed: int"],
              ["start_live(interface, window)", "stop()", "_live_loop()"], fs=6.3)
    uml_class(ax, 35, 97, 30, "TrafficSimulator", ["on_window", "running: bool", "window_seconds: int", "attack_probability = 0.35", "windows_completed: int"],
              ["start(window_seconds)", "stop()", "_loop()", "_make_window(is_attack)"], fs=6.3)
    uml_class(ax, 68.5, 97, 30, "Database", ["path: str", "_lock: Lock"],
              ["add_detection(record)", "get_detections(limit)", "count_by_prediction()", "count_by_severity()", "add_mitigation(...)", "mark_mitigation_recovered()", "get_mitigations(limit)", "add_health() / get_health_history()", "get_setting() / set_setting()"], fs=6.1)
    uml_class(ax, 1.5, 64, 30, "MitigationManager", ["db: Database", "quarantine_seconds: int", "active: dict[ip -> record]", "_lock: Lock"],
              ["decide(severity, context, reason)", "quarantine(ip, reason, duration)", "expire_due()", "get_active()", "set_duration(seconds)", "apply_os_firewall_block(ip)"], fs=6.1, hdr=PURPLE)
    uml_class(ax, 35, 64, 30, "Flask app (app.py)", ["db: Database", "mitigation: MitigationManager", "monitor: MonitorEngine", "simulator: TrafficSimulator", "baseline_rates: deque(12)", "consecutive_suspicious: int"],
              ["process_window(features, context,", "    source, interface)", "_health_sampler()", "api_* route handlers (12)"], fs=6.0, hdr=BLUE, stereotype="module")
    uml_class(ax, 68.5, 64, 30, "model_loader", ["_MODEL: RandomForestClassifier", "_FEATURES: list[str]", "_METADATA: dict"],
              ["is_trained()", "load_model()", "get_metadata()", "predict_traffic(features)"], fs=6.2, hdr=TEAL, stereotype="module")
    uml_class(ax, 1.5, 30, 30, "distributed_analysis", [],
              ["compute_distributed_risk(features,", "    context, baseline) -> dict"], fs=6.2, hdr=TEAL, stereotype="module")
    uml_class(ax, 35, 30, 30, "severity / detector", [],
              ["assess_severity(prediction, conf,", "    features, distributed, persistence)", "detect(features) -> dict"], fs=6.2, hdr=TEAL, stereotype="module")
    uml_class(ax, 68.5, 30, 30, "features / traffic_aggregator", ["FEATURE_COLUMNS: 10 names"],
              ["validate_feature_dict(features)", "empty_feature_dict()", "aggregate_packets(packets,", "    window_seconds, local_ips)"], fs=6.0, hdr=TEAL, stereotype="module")
    # composition / use relations from the Flask module
    arrow(ax, (31.5, 50), (35, 50), "uses", lo=(0, 1.4), fs=6)
    arrow(ax, (65, 50), (68.5, 50), "uses", lo=(0, 1.4), fs=6)
    arrow(ax, (42, 64), (22, 71.5), "owns", lo=(-1, 0), fs=6, color=NAVY)
    arrow(ax, (50, 64), (50, 71.5), "owns", lo=(3.5, 0), fs=6, color=NAVY)
    arrow(ax, (58, 64), (78, 68.5), "owns", lo=(2, 2.2), fs=6, color=NAVY)
    arrow(ax, (42, 38.5), (22, 28.5), "calls", lo=(-1, 1.8), fs=6)
    arrow(ax, (50, 38.5), (50, 28.5), "calls", lo=(3.5, 0), fs=6)
    ax.text(50, 3.2, "MonitorEngine and TrafficSimulator hand each finished window to Flask app.process_window (on_window callback) and both call traffic_aggregator;", ha="center", fontsize=6.2, color=GREY, style="italic")
    ax.text(50, 0.8, "MitigationManager writes through Database. Class boxes show the attributes and methods that exist in the source files.", ha="center", fontsize=6.2, color=GREY, style="italic")
    save(fig, OUT / "06_uml_class.png")


# ------------------------------------------------------------------ 07 sequence
def sequence():
    fig, ax = canvas(9.2, 8.0, 100, 87)
    ax.text(2, 85.3, "Sequence diagram: one monitoring window in Simulation Mode, from Start to a stored detection", fontsize=8.4, fontweight="bold", color=NAVY)
    names = ["Administrator", "React UI", "Flask app", "Simulator /\nMonitorEngine", "Aggregator", "Random Forest", "Risk + Severity", "Mitigation\nManager", "SQLite"]
    xs = [6, 16.5, 28, 40, 51.5, 62.5, 73.5, 84, 94.5]
    for x, n in zip(xs, names):
        box(ax, x, 80, 9.6, 5.5, n, NAVY, fs=6.0)
        ax.plot([x, x], [77, 3], color="#9AA7B8", lw=0.9, ls="--", zorder=1)
    msgs = [
        (0, 1, 74.5, "click Start simulation", False), (1, 2, 71.5, "POST /api/demo/start {window_seconds}", False), (2, 3, 68.5, "simulator.start() (thread)", False),
        (2, 1, 66, "200 {ok, mode: simulation}", True), (3, 3, 63.0, "build packet list for window", False), (3, 4, 59.8, "aggregate_packets(packets, window, local_ips)", False),
        (4, 3, 57.4, "features (10) + context", True), (3, 2, 54.8, "on_window = process_window(...)", False), (2, 5, 52.0, "detect(features): validate, predict, predict_proba", False),
        (5, 2, 49.5, "Attack / Benign, confidence", True), (2, 6, 46.7, "distributed risk(baseline) -> severity(persistence)", False), (6, 2, 44.3, "risk, severity, factors", True),
        (2, 7, 41.5, "decide(severity, context)", False), (7, 8, 38.7, "add_mitigation(ip, reason, duration)", False), (7, 2, 36.1, "actions list", True),
        (2, 8, 33.3, "add_detection(record + detail JSON)", False), (8, 2, 30.8, "row id", True), (1, 2, 27.8, "poll GET /api/status, /api/detections (2 s)", False),
        (2, 1, 25.2, "latest detection, counters, active quarantines", True), (1, 0, 22.4, "cards, table, countdowns update", True),
    ]
    for a, b, y, t, ret in msgs:
        x1, x2 = xs[a], xs[b]
        if a == b:
            ax.add_patch(Rectangle((x1, y - 1.1), 2.6, 2.4, fc=PALE_BLUE, ec=BLUE, lw=1, zorder=3))
            ax.text(x1 + 3.4, y, t, fontsize=6.2, va="center", color=INK)
            continue
        arrow(ax, (x1, y), (x2, y), None, color=GREY if ret else NAVY, lw=1.2, ls="--" if ret else "-")
        ax.text((x1 + x2) / 2, y + 1.15, t, fontsize=6.2, ha="center", va="bottom", color=INK, bbox=dict(fc="white", ec="none", pad=0.4, alpha=0.9), zorder=6)
    panel(ax, 2, 4, 96, 14.5, "ALTERNATIVE FLOWS", fc=PALE_ORANGE, ec=ORANGE, fs=7.6, tc=ORANGE)
    ax.text(4, 13.6, "- Medium severity: Mitigation Manager returns rate_limit_recommended (no quarantine); Low: monitor.", fontsize=6.3, va="center")
    ax.text(4, 10.9, "- Live mode: Scapy sniff() fails (no Npcap / no permission) -> callback with error -> status shows capture_error; no stored row.", fontsize=6.3, va="center")
    ax.text(4, 8.2, "- Feature validation error (NaN, negative, missing) -> process_window returns {error}; second Start while running -> HTTP 409.", fontsize=6.3, va="center")
    ax.text(4, 5.5, "- Quarantine expiry: next get_active()/decide() calls expire_due(), status becomes recovered in SQLite.", fontsize=6.3, va="center")
    save(fig, OUT / "07_sequence_main_flow.png")


# ------------------------------------------------------------------ 08 use case
def usecase():
    fig, ax = canvas(8.4, 6.8, 100, 81)
    ax.text(2, 78.5, "Use-case diagram", fontsize=9, fontweight="bold", color=NAVY)
    ax.add_patch(Rectangle((24, 3), 52, 72, fc="#FBFCFE", ec=NAVY, lw=1.4, zorder=0))
    ax.text(50, 73, "SentinelFlow", ha="center", fontsize=8.6, fontweight="bold", color=NAVY)
    cases = ["Sign in (demo gate)", "Start live capture", "Start Simulation Mode", "Stop session", "View threat overview", "Browse and filter detections",
             "Inspect threat detail (factors)", "View analytics", "View network health", "View active quarantines and history", "Change window / quarantine settings", "View model metrics", "Retrain model (command line)"]
    ys = [67 - i * 4.7 for i in range(len(cases))]
    for t, y in zip(cases, ys):
        ellipse(ax, 50, y, 34, 3.8, t, fs=6.6)
    box(ax, 10, 38, 14, 10, "Administrator\n/ analyst", NAVY, fs=7.6)
    for y in ys[:-1]:
        arrow(ax, (17, 38), (33, y), "", color=GREY, lw=0.7, style="-")
    box(ax, 90, 62, 15, 8, "Network\ninterface", ORANGE, fs=7.2)
    box(ax, 90, 46, 15, 8, "Traffic\nsimulator", ORANGE, fs=7.2)
    box(ax, 90, 28, 15, 8, "Developer\n(training)", PURPLE, fs=7.2)
    arrow(ax, (82.5, 62), (67, ys[1]), "", color=ORANGE, lw=0.9, style="-")
    arrow(ax, (82.5, 46), (67, ys[2]), "", color=ORANGE, lw=0.9, style="-")
    arrow(ax, (82.5, 28), (67, ys[12]), "", color=PURPLE, lw=0.9, style="-")
    ax.text(50, 1, "Mitigation (quarantine / recommend) and detection run automatically on every window; they are not user-triggered use cases", ha="center", fontsize=6.2, color=GREY, style="italic")
    save(fig, OUT / "08_use_case.png")


# ------------------------------------------------------------------ 09 ER diagram
def er():
    fig, ax = canvas(9.6, 6.6, 100, 69)
    ax.text(2, 66.5, "Entity-relationship diagram of data/sentinelflow.db (SQLite, 4 tables)", fontsize=8.8, fontweight="bold", color=NAVY)

    def table(x, y, w, name, cols, color=NAVY):
        lh = 2.55
        h = 3.8 + lh * len(cols) + 0.6
        ax.add_patch(Rectangle((x, y - h), w, h, fc=WHITE, ec=NAVY, lw=1.3, zorder=2))
        ax.add_patch(Rectangle((x, y - 3.8), w, 3.8, fc=color, ec=NAVY, lw=1.3, zorder=3))
        ax.text(x + w / 2, y - 1.9, name, ha="center", va="center", color=WHITE, fontsize=8.2, fontweight="bold", zorder=4)
        for i, c in enumerate(cols):
            ax.text(x + 0.9, y - 3.8 - 1.6 - i * lh, c, fontsize=6.2, va="center", family="DejaVu Sans Mono", zorder=4)
        return h

    table(1, 62, 33, "detections", ["PK id INTEGER", "timestamp REAL", "interface TEXT", "source TEXT", "prediction TEXT", "confidence REAL", "severity TEXT", "packet_rate REAL", "byte_rate REAL", "source_count INTEGER", "destination_count INTEGER", "distributed_risk REAL", "mitigation_status TEXT", "detail_json TEXT"], BLUE)
    table(42, 62, 27, "mitigations", ["PK id INTEGER", "timestamp REAL", "ip TEXT", "reason TEXT", "duration INTEGER", "status TEXT (active|recovered)"], PURPLE)
    table(74, 62, 25, "health_samples", ["PK id INTEGER", "timestamp REAL", "cpu_percent REAL", "memory_percent REAL", "bytes_sent INTEGER", "bytes_recv INTEGER", "packets_sent INTEGER", "packets_recv INTEGER"], TEAL)
    table(42, 38, 27, "settings", ["PK key TEXT", "value TEXT"], GREY)
    box(ax, 62, 10, 70, 12, "", PALE_ORANGE, ec=ORANGE, tc=INK)
    ax.text(62, 14, "No foreign keys are declared.", ha="center", fontsize=6.8, fontweight="bold", color=ORANGE)
    ax.text(62, 9.8, "A mitigation row is tied to the detection that caused it only logically: its reason text names the window source and severity,\nand its timestamp falls inside the same window. Health samples and settings stand alone.", ha="center", va="center", fontsize=6.2, linespacing=1.4)
    arrow(ax, (34, 52), (42, 52), "caused by (logical)", lo=(0, 1.6), fs=6.0, ls="--", color=ORANGE)
    save(fig, OUT / "09_er_diagram.png")


# ------------------------------------------------------------------ 10 flowchart of the core algorithm
def flowchart():
    fig, ax = canvas(8.4, 9.8, 100, 117)
    ax.text(2, 114.5, "Flowchart: process_window() - the core algorithm", fontsize=8.8, fontweight="bold", color=NAVY)
    cx = 42
    steps = [
        (109, "box", "Window ready: features, context, source, interface", NAVY),
        (101, "dia", "context.error?", None), (92.5, "box", "detector.detect(features): validate -> RF predict -> confidence", BLUE),
        (84, "dia", "model missing or\nfeature invalid?", None), (75, "box", "distributed risk = 0.30 src + 0.30 dst + 0.25 rate + 0.15 baseline", TEAL),
        (67, "box", "append packet rate to rolling baseline (12)", TEAL), (58.5, "dia", "Attack or risk >= 0.7?", None),
        (49.5, "box", "persistence += 1 (otherwise reset to 0)", TEAL), (41, "box", "severity score: label, confidence, rate, risk, spread, persistence", TEAL),
        (32, "dia", "severity?", None),
    ]
    for y, kind, t, col in steps:
        if kind == "box":
            box(ax, cx, y, 50, 6.2, t, col, fs=6.4)
        else:
            diamond(ax, cx, y, 40, 8, t, fs=6.5)
    ys = [s[0] for s in steps]
    kinds = [s[1] for s in steps]
    for i in range(len(steps) - 1):
        top = ys[i] - (3.1 if kinds[i] == "box" else 4)
        bot = ys[i + 1] + (3.1 if kinds[i + 1] == "box" else 4)
        arrow(ax, (cx, top), (cx, bot), "", color=NAVY, lw=1.1)
    for y, lab in ((97, "no"), (80, "no")):
        ax.text(cx + 1.5, y, lab, fontsize=6.2)
    ax.text(cx + 1.5, 54.3, "(either way)", fontsize=6.0, color=GREY)
    box(ax, 87, 101, 22, 6, "return {error}", ORANGE, fs=6.6)
    arrow(ax, (62, 101), (76, 101), "yes", lo=(0, 1.4), fs=6.2, color=ORANGE)
    box(ax, 87, 84, 22, 6, "return {error}", ORANGE, fs=6.6)
    arrow(ax, (62, 84), (76, 84), "yes", lo=(0, 1.4), fs=6.2, color=ORANGE)
    box(ax, 12, 17.5, 22, 9, "Low:\nmonitor", TEAL, fs=6.6)
    box(ax, 42, 17.5, 24, 9, "Medium:\nrecommend rate limit", ORANGE, fs=6.4)
    box(ax, 80, 17.5, 28, 11, "High / Critical:\nquarantine top 3 non-protected\nsources (Critical: double time);\nif none: rate-limit advice", PURPLE, fs=6.0)
    arrow(ax, (31, 29), (14, 22.2), "Low", lo=(-3, 1.2), fs=6.2)
    arrow(ax, (42, 28), (42, 22.2), "Medium", lo=(4.5, 0), fs=6.2)
    arrow(ax, (58, 29.5), (76, 23.2), "High / Critical", lo=(4, 2.6), fs=6.2)
    box(ax, 42, 4.5, 56, 6.2, "store detection row (SQLite) + keep latest in memory; return record with actions", NAVY, fs=6.3)
    arrow(ax, (12, 13), (24, 7.6), "", color=NAVY, lw=1.1)
    arrow(ax, (42, 13), (42, 7.7), "", color=NAVY, lw=1.1)
    arrow(ax, (80, 11.5), (66, 7.0), "", color=NAVY, lw=1.1)
    save(fig, OUT / "10_flowchart_core_algorithm.png")


if __name__ == "__main__":
    architecture(); workflow(); dfd0(); dfd1(); dfd2(); classes(); sequence(); usecase(); er(); flowchart()
