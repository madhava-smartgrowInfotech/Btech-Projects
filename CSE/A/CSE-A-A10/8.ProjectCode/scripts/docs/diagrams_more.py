"""FlowSense diagrams 05 and 07-12: DFD level 2, sequence, use case, ER, control flowchart, vision flowchart, forecaster architecture."""
from __future__ import annotations

import json
from pathlib import Path

from matplotlib.patches import Ellipse, Rectangle

from .dgm_lib import *  # noqa: F401,F403

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"
EXP = Path(__file__).resolve().parents[2] / "experiments"


def _pred():
    return json.loads((EXP / "predictor" / "metrics.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------- 05 DFD level 2
def dfd2():
    fig, ax = canvas(10, 7.6, 100, 76)
    pr = lambda cx, cy, n, t, c=TEAL: circle(ax, cx, cy, 6.3, f"{n}\n{t}", c, fs=6.0)
    pr(18, 38, "3.2", "Refresh\nforecast", PURPLE)
    pr(50, 60, "3.1", "Scan\nupstream")
    pr(80, 60, "3.3", "Find ambulance\ntarget", ORANGE)
    pr(50, 38, "3.4", "Score\npressure", BLUE)
    pr(50, 15, "3.5", "Decide\nphase", NAVY)
    pr(84, 15, "3.6", "Switch &\ndischarge", GREY)
    st = lambda cx, cy, t, w: store(ax, cx, cy, w, 6.0, t, fs=6.2)
    st(18, 54, "D2  trained forecaster", 22)
    st(84, 42, "D1  queues, transit, phase, timer", 24)
    st(84, 3.6, "D4  violation / emergency logs", 24)
    A = dict(color=NAVY, fs=5.9)
    arrow(ax, (18, 51), (18, 44.4), "predict", lo=(4.2, 0), **A)
    arrow(ax, (24.4, 38), (43.6, 38), "forecast excess", lo=(0, 2.0), **A)
    arrow(ax, (56.4, 60), (73.6, 60), "ambulances inbound\n(<= 15 s)", lo=(0, 3.2), **A)
    arrow(ax, (82, 45), (82, 53.8), "queued\nambulances", lo=(6.8, 0), **A)
    arrow(ax, (72.5, 45), (55, 55.5), "transit queue", lo=(3.5, 3.0), **A)
    arrow(ax, (50, 53.7), (50, 44.4), "inbound PCU\n(<= 8 s)", lo=(-6.8, 0), **A)
    arrow(ax, (72, 39.5), (56.4, 38.5), "queue PCU,\nhead wait", lo=(0, 3.2), **A)
    arrow(ax, (50, 31.7), (50, 21.4), "current / other\npressure", lo=(-8.2, 0), **A)
    arrow(ax, (77, 54.8), (54.8, 19.6), "ambulance\ntarget phase", lo=(1.0, -8.0), **A)
    arrow(ax, (56.4, 15), (77.6, 15), "switch / hold", lo=(0, 2.1), **A)
    arrow(ax, (84, 21.4), (84, 39), "update queues,\nphase, transit", lo=(-7.4, 0), **A)
    arrow(ax, (84, 8.7), (84, 6.7), "events", lo=(5.0, 0), **A)
    ax.text(3, 15, "3.0 Control signals expanded:\none junction, one second.\n\n3.2 runs every 10 s (advanced\ncontroller only, t >= 30).\n\nEvery junction is processed\nin turn each second.", fontsize=6.1, color=GREY, va="center", style="italic")
    save(fig, OUT / "05_dfd_level2.png")


# --------------------------------------------------------------- 07 sequence
def sequence():
    fig, ax = canvas(10, 8.9, 100, 89)
    names = ["Operator", "React console", "FastAPI\n(main.py)", "Live\n(service.py)", "Sim\n(sim.py)", "QueuePredictor"]
    xs = [7, 22, 38, 55, 72, 90]
    cols = [ORANGE, BLUE, NAVY, TEAL, TEAL, PURPLE]
    for x, n, c in zip(xs, names, cols):
        box(ax, x, 85.5, 13.8, 5.4, n, c, fs=6.4, bold=True)
        ax.plot([x, x], [82.7, 2], color="#9AA7B8", lw=1.0, ls=(0, (4, 3)), zorder=1)

    def msg(i, j, y, text, dashed=False, color=NAVY):
        x1, x2 = xs[i], xs[j]
        ax.annotate("", xy=(x2, y), xytext=(x1, y), arrowprops=dict(arrowstyle="-|>", color=color, lw=1.2, ls="--" if dashed else "-"))
        ax.text((x1 + x2) / 2, y + 1.15, text, ha="center", fontsize=5.7, color=INK, bbox=dict(fc="white", ec="none", pad=0.3))

    def selfmsg(i, y, text, w=14):
        x = xs[i]
        ax.plot([x, x + 5, x + 5], [y, y, y - 2.6], color=NAVY, lw=1.2)
        ax.annotate("", xy=(x, y - 2.6), xytext=(x + 5, y - 2.6), arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=1.2))
        ax.text(x + 6, y - 1.3, text, fontsize=5.6, ha="left", va="center", color=INK)

    def activation(i, y1, y2):
        ax.add_patch(Rectangle((xs[i] - 0.8, y2), 1.6, y1 - y2, fc=PALE_BLUE, ec=NAVY, lw=0.8, zorder=2))

    ax.text(2, 80.2, "A. Skip 5 minutes on the Live page", fontsize=6.8, fontweight="bold", color=NAVY)
    msg(0, 1, 77.5, "click 'Skip 5 min'")
    msg(1, 2, 73.8, "POST /api/live/step  {seconds: 300}  + Bearer token")
    selfmsg(2, 71.6, "current_user(): read_token (HS256 signature, expiry)")
    activation(3, 67.5, 38)
    msg(2, 3, 67.0, "step(300)  under S.LOCK")
    selfmsg(3, 65.0, "_attach(): predictor = PRED.model if use_ml")
    msg(3, 4, 59.8, "sim.run(300)")
    activation(4, 59.8, 37.5)
    ax.add_patch(Rectangle((58.0, 39.6), 40.0, 17.6, fc="none", ec=GREY, lw=1.1, ls="--", zorder=1))
    ax.text(59.0, 55.9, "loop 300 times (one simulated second each)", fontsize=5.6, color=GREY, style="italic", va="center")
    selfmsg(4, 54.0, "_arrivals, _transit_arrivals, _signals")
    msg(4, 5, 48.8, "predict(features)  every 10 s (advanced)")
    msg(5, 4, 45.6, "forecast n x 4, clip 0..40", dashed=True, color=PURPLE)
    selfmsg(4, 43.0, "_discharge, _record (queues, delays)")
    msg(4, 3, 36.2, "run finished", dashed=True)
    msg(3, 2, 33.8, "snapshot(): KPIs, map, queue series, junctions", dashed=True)
    msg(2, 1, 30.8, "200 JSON", dashed=True)
    msg(1, 0, 27.8, "map, KPI tiles and chart re-render", dashed=True)
    ax.text(2, 23.0, "B. Send an ambulance, then step", fontsize=6.8, fontweight="bold", color=NAVY)
    msg(1, 2, 20.0, "POST /api/live/ambulance")
    msg(2, 3, 16.6, "ambulance()")
    msg(3, 4, 13.2, "_new_vehicle(emg=True) -> entry queue")
    msg(3, 1, 9.8, "snapshot + banner 'signals pre-empting'", dashed=True)
    selfmsg(4, 7.2, "next step: _decide -> pre-empt")
    save(fig, OUT / "07_sequence_flow.png")


# --------------------------------------------------------------- 08 use case
def use_case():
    fig, ax = canvas(10, 7.4, 100, 74)
    ax.add_patch(Rectangle((24, 2), 56, 70, fc="#FAFBFD", ec=NAVY, lw=1.5, zorder=0))
    ax.text(52, 69.3, "FlowSense (system boundary)", ha="center", fontsize=8, fontweight="bold", color=NAVY)

    def actor(x, y, name):
        ax.add_patch(Ellipse((x, y + 5.2), 3.6, 3.6, fc=WHITE, ec=NAVY, lw=1.4, zorder=3))
        ax.plot([x, x], [y + 3.4, y - 1.8], color=NAVY, lw=1.4, zorder=3)
        ax.plot([x - 3, x + 3], [y + 1.8, y + 1.8], color=NAVY, lw=1.4, zorder=3)
        ax.plot([x, x - 2.8], [y - 1.8, y - 5.5], color=NAVY, lw=1.4, zorder=3)
        ax.plot([x, x + 2.8], [y - 1.8, y - 5.5], color=NAVY, lw=1.4, zorder=3)
        ax.text(x, y - 8.5, name, ha="center", fontsize=6.6, fontweight="bold", color=INK)
        return (x, y + 1.8)

    uc = {}
    items = [
        ("signin", 48, 62, "Sign in (demo account)", PALE_PURPLE, PURPLE),
        ("config", 52, 54, "Configure network:\ngrid, controller, demand, ML toggle", PALE_BLUE, BLUE),
        ("live", 52, 46, "Run live / skip 5 min", PALE_BLUE, BLUE),
        ("amb", 52, 38.5, "Send an ambulance", PALE_ORANGE, ORANGE),
        ("bench", 52, 31, "Run controller benchmark\nand demand sweep", PALE_BLUE, BLUE),
        ("vision", 52, 23, "Analyse an image\n(synthetic, sample, upload)", PALE_TEAL, TEAL),
        ("pred", 52, 15.5, "View queue forecast", PALE_BLUE, BLUE),
        ("viol", 52, 8, "Review violation log", PALE_BLUE, BLUE),
        ("pulse", 70, 64, "Watch live preview\n(landing page)", PALE_TEAL, TEAL),
        ("exp", 70, 28, "Run experiments,\ntests, screenshots", LIGHT, GREY),
    ]
    for k, x, y, t, fc, ec in items:
        w = 25 if x in (52, 48) else 17
        ax.add_patch(Ellipse((x, y), w, 6.2 if "\n" in t else 5.2, fc=fc, ec=ec, lw=1.3, zorder=2))
        ax.text(x, y, t, ha="center", va="center", fontsize=6.0, color=INK, zorder=3, linespacing=1.15)
        uc[k] = (x, y, w)
    op = actor(10, 40, "OPERATOR")
    vis = actor(90, 60, "VISITOR")
    dev = actor(90, 22, "EVALUATOR /\nDEVELOPER")

    def link(a, k, side="l", color=NAVY):
        x, y, w = uc[k]
        tx = x - w / 2 * 0.98 if side == "l" else x + w / 2 * 0.98
        ax.plot([a[0], tx], [a[1], y], color=color, lw=1.0, zorder=1)

    for k in ("signin", "config", "live", "amb", "bench", "vision", "pred", "viol"):
        link(op, k)
    link(vis, "pulse", "r", GREY)
    link(dev, "exp", "r", GREY)
    # include / extend
    def dash(k1, k2, label):
        x1, y1, w1 = uc[k1]
        x2, y2, w2 = uc[k2]
        ax.annotate("", xy=(x2, y2 - 2.9), xytext=(x1, y1 + 2.9), arrowprops=dict(arrowstyle="-|>", color=GREY, lw=1.0, ls="--"))
        ax.text(x1 + 1.2, (y1 + y2) / 2, label, fontsize=5.4, color=GREY, ha="left")
    dash("config", "signin", "<<include>>")
    dash("live", "config", "<<include>>")
    dash("amb", "live", "<<extend>>")
    ax.text(50, 0.1, "Every operator use case needs a valid token (Sign in). 'Visitor' sees only the public preview; 'Evaluator' runs the scripts in scripts/ and tests/, which import the same engine.",
            ha="center", fontsize=5.6, color=GREY, style="italic")
    save(fig, OUT / "08_use_case.png")


# --------------------------------------------------------------- 09 logical ER
def er():
    fig, ax = canvas(10, 8.2, 100, 82)
    ax.text(50, 79.5, "Logical entities - FlowSense keeps NO database: everything below lives in process memory (or in files)", ha="center", fontsize=7.4, color=NAVY, fontweight="bold")
    fs = 5.8
    X = (2, 36, 70)
    R = {}
    R["net"] = uml_class(ax, X[0], 75, 27, "NETWORK  (Sim)", ["rows, cols, controller", "demand, seed, start_hour", "t, spawned, preemptions"], [], hdr=NAVY, stereotype="1 per simulation", fs=fs)
    R["jun"] = uml_class(ax, X[1], 75, 27, "JUNCTION", ["j (0..n-1), phase 0 | 1", "timer, clear, nxt", "preempt_active"], [], hdr=BLUE, stereotype="n = rows x cols", fs=fs)
    R["app"] = uml_class(ax, X[2], 75, 28, "APPROACH", ["name N | E | S | W", "queue: deque[Vehicle]", "pred (forecast), credit", "is_entry"], [], hdr=BLUE, stereotype="4 per junction", fs=fs)
    R["fc"] = uml_class(ax, X[0], 50, 27, "FORECASTER", ["GradientBoosting (160 trees)", "metrics, importance", "n_samples, fit_seconds"], [], hdr=PURPLE, stereotype="trained at API start", fs=fs)
    R["emg"] = uml_class(ax, X[1], 50, 27, "EMERGENCY_RUN", ["id, delay, travel"], [], hdr=ORANGE, stereotype="one per ambulance served", fs=fs)
    R["veh"] = uml_class(ax, X[2], 50, 28, "VEHICLE", ["id, vtype, t0, wait", "emg, red_runner", "hop, plate, u[10]"], [], hdr=TEAL, stereotype="queued or in transit", fs=fs)
    R["bc"] = uml_class(ax, X[0], 26, 27, "BENCHMARK_CACHE", ["key (grid, secs, demand,", "  seeds, hour, use_ml)", "value: summaries, queues,", "  violation counts"], [], hdr=GREY, stereotype="dict in service.py", fs=fs)
    R["tok"] = uml_class(ax, X[1], 26, 27, "SESSION_TOKEN", ["sub (email), name", "exp (12 h)", "HS256 signature"], [], hdr=GREY, stereotype="stateless, kept by the browser", fs=fs)
    R["vio"] = uml_class(ax, X[2], 26, 28, "VIOLATION", ["t, junction, approach", "kind: red-light | wrong-way", "plate, vehicle", "confidence 0.86-0.99"], [], hdr=ORANGE, stereotype="simulated event", fs=fs)

    def h(a, b, lab, off=8.0):
        ra, rb = R[a], R[b]
        y = ra[1] + ra[3] - off
        xa, xb = (ra[0] + ra[2], rb[0]) if ra[0] < rb[0] else (ra[0], rb[0] + rb[2])
        ax.plot([xa, xb], [y, y], color=NAVY, lw=1.6, zorder=1)
        ax.text((xa + xb) / 2, y + 1.3, lab, fontsize=5.7, color=GREY, ha="center", bbox=dict(fc="white", ec="none", pad=0.3), zorder=5)

    def v(a, b, lab):
        ra, rb = R[a], R[b]
        x = ra[0] + ra[2] / 2
        ax.plot([x, x], [ra[1], rb[1] + rb[3]], color=NAVY, lw=1.6, zorder=1)
        ax.text(x + 1.2, (ra[1] + rb[1] + rb[3]) / 2, lab, fontsize=5.7, color=GREY, ha="left", va="center", bbox=dict(fc="white", ec="none", pad=0.3), zorder=5)

    h("net", "jun", "1 : n")
    h("jun", "app", "1 : 4")
    v("app", "veh", "1 : 0..*  (queue)")
    v("net", "fc", "uses 0..1")
    v("fc", "bc", "used by")
    v("veh", "vio", "0..1")
    h("veh", "emg", "0..1", off=6.0)
    ax.text(50, 3.0, "No foreign keys: relations are Python references inside one process. NETWORK 1-n JUNCTION 1-4 APPROACH 1-n VEHICLE; a VEHICLE may raise one VIOLATION or finish as an EMERGENCY_RUN.\nA SNAPSHOT (the JSON the API returns) is built from NETWORK state on every request; all of it is lost when the server restarts.",
            ha="center", fontsize=5.6, color=GREY, style="italic")
    save(fig, OUT / "09_er_diagram.png")


# --------------------------------------------------------------- 10 control flowchart
def flow_ctrl():
    fig, ax = canvas(10, 9.6, 100, 96)
    X, R = 32, 76
    A = dict(color=NAVY, fs=6.3)
    box(ax, X, 93, 40, 4.2, "Every simulated second, for each junction j\n(advanced controller)", NAVY, fs=6.4, bold=True)
    ys = dict(d1=85, t=77.5, d2=69.5, p=58.5, d3=47.5, d4=39, d5=30.5, d6=22, hold=11)
    diamond(ax, X, ys["d1"], 36, 7.2, "clearance[j] > 0 ?", fs=6.6)
    box(ax, R, ys["d1"], 38, 6.6, "clearance -= 1; at 0 the next phase starts\n(this second is spent clearing)", GREY, fs=6.0)
    box(ax, X, ys["t"], 26, 4.2, "timer[j] += 1", BLUE, fs=6.6)
    diamond(ax, X, ys["d2"], 40, 7.8, "ambulance queued here or\ninbound within 15 s ?", fs=6.3)
    box(ax, R, ys["d2"], 38, 9.4, "target = phase of the nearest ambulance\nif target != phase and timer >= 2:\nSWITCH to target (count a pre-emption)\nelse HOLD", ORANGE, fs=5.9)
    box(ax, X, ys["p"], 46, 10.4, "pressure(phase) = sum over its approaches of\nPCU queue + 0.7 * max(forecast - queue, 0)\n+ inbound PCU (<= 8 s) + head wait / 12\n(x 0.3 if the straight-ahead queue >= 26)\ncur = pressure(phase), oth = pressure(other)", PURPLE, fs=5.8)
    diamond(ax, X, ys["d3"], 30, 7.0, "timer < 13 ?", fs=6.6)
    box(ax, R, ys["d3"], 30, 4.4, "HOLD  (minimum green)", TEAL, fs=6.2)
    diamond(ax, X, ys["d4"], 30, 7.0, "timer >= 60 ?", fs=6.6)
    box(ax, R, ys["d4"], 38, 5.2, "SWITCH if oth > 0, else HOLD\n(maximum green)", ORANGE, fs=5.9)
    diamond(ax, X, ys["d5"], 38, 7.0, "cur <= 0.01 and oth > 0 ?", fs=6.3)
    box(ax, R, ys["d5"], 38, 4.4, "SWITCH  (empty phase, other waiting)", ORANGE, fs=5.9)
    diamond(ax, X, ys["d6"], 34, 7.0, "oth > 2 * cur + 4 ?", fs=6.6)
    box(ax, R, ys["d6"], 38, 4.4, "SWITCH  (other side clearly worse)", ORANGE, fs=5.9)
    box(ax, X, ys["hold"], 26, 4.4, "HOLD the current phase", TEAL, fs=6.4, bold=True)
    box(ax, 50, 3.0, 88, 4.6, "SWITCH = start a 3 s yellow/all-red clearance, then the new phase turns green; after a 2 s start-up the approaches discharge at 0.5 vehicle/s each.", LIGHT, tc=INK, ec="#B7C3D3", fs=5.9)
    # spine arrows
    arrow(ax, (X, 90.9), (X, 88.6), **A)
    arrow(ax, (X, 81.4), (X, 79.6), "no", lo=(2.2, 0), **A)
    arrow(ax, (X, 75.4), (X, 73.4), **A)
    arrow(ax, (X, 65.6), (X, 63.7), "no", lo=(2.2, 0), **A)
    arrow(ax, (X, 53.3), (X, 51.0), **A)
    for a, b in (("d3", "d4"), ("d4", "d5"), ("d5", "d6")):
        arrow(ax, (X, ys[a] - 3.5), (X, ys[b] + 3.5), "no", lo=(2.2, 0), **A)
    arrow(ax, (X, ys["d6"] - 3.5), (X, ys["hold"] + 2.2), "no", lo=(2.2, 0), **A)
    # yes arrows
    for k, w in (("d1", 18), ("d2", 20), ("d3", 15), ("d4", 15), ("d5", 19), ("d6", 17)):
        arrow(ax, (X + w, ys[k]), (R - (19 if k in ("d1", "d2", "d4", "d5", "d6") else 15), ys[k]), "yes", lo=(0, 1.6), **A)
    save(fig, OUT / "10_flowchart_control.png")


# --------------------------------------------------------------- 11 vision flowchart
def flow_vision():
    fig, ax = canvas(10, 8.6, 100, 86)
    A = dict(color=NAVY, fs=6.3)
    box(ax, 50, 82.5, 36, 4.6, "Frame (BGR image) arrives at /api/vision/*", NAVY, fs=6.6, bold=True)
    diamond(ax, 50, 74, 30, 7.6, "source ?", fs=6.8)
    box(ax, 20, 62, 36, 14.5, "SYNTHETIC SCENE - detect_classical\nroad, lane paint and grass masked out;\nclose 5x5 / open 3x3; connected components\n>= 350 px; class by area and long side\n(bike < 900 px, car < 95, truck < 130, else bus)", BLUE, fs=5.8)
    box(ax, 80, 62, 36, 14.5, "REAL PHOTO - detect_yolo\nYOLOv8n (COCO), conf >= 0.3, classes\ncar, motorcycle (= bike), bus, truck;\nboxes with confidence and class", BLUE, fs=5.8)
    box(ax, 50, 45.5, 66, 11.2, "detect_lightbars  (same rule on both paths)\nred mask: H 0-8 or 172-180; blue mask: H 100-130; S >= 120, V >= 190; open 3x3\ndilate by 5 % of the short side, keep red AND blue (they must touch); connected components\nkeep a cluster with >= 12 red and >= 12 blue pixels; score = balance of the two colours", PURPLE, fs=5.9)
    diamond(ax, 50, 29.5, 48, 9.6, "light-bar centre on the vehicle\nbox (x +- 5 px, 0.3 h above to\n0.6 h below its top), score > 0.25 ?", fs=5.5)
    box(ax, 87, 29.5, 20, 7.0, "relabel the box\n'ambulance'", ORANGE, fs=6.2)
    box(ax, 50, 14.6, 78, 10.4, "density_report:  PCU = sum of class weights (car 1, bike 0.5, bus 3, truck 2, ambulance 1);  ratio = PCU / 14\nLOW < 0.35 · MEDIUM < 0.7 · HIGH < 1.0 · JAMMED otherwise\ngreen-time hint = 12 s if an ambulance is present, else clamp(12 + 3.2 x PCU, 15, 60) s", TEAL, fs=5.9)
    box(ax, 50, 4.2, 66, 5.4, "annotate boxes, return JSON: detections, counts, PCU, level, green hint, light-bar clusters", NAVY, fs=6.1, bold=True)
    arrow(ax, (50, 80.1), (50, 77.8), **A)
    arrow(ax, (35, 74), (20, 69.3), "synthetic", lo=(-4.5, 1.8), **A)
    arrow(ax, (65, 74), (80, 69.3), "photo / upload", lo=(5.5, 1.8), **A)
    arrow(ax, (20, 54.7), (36, 51.1), **A)
    arrow(ax, (80, 54.7), (64, 51.1), **A)
    arrow(ax, (50, 39.9), (50, 34.3), **A)
    arrow(ax, (74, 29.5), (77, 29.5), "yes", lo=(0, 2.4), **A)
    arrow(ax, (87, 26.0), (87, 19.8), **A)
    arrow(ax, (50, 24.7), (50, 19.8), "no: keep the class", lo=(8.5, 0), **A)
    arrow(ax, (50, 9.4), (50, 6.9), **A)
    save(fig, OUT / "11_flowchart_vision.png")


# --------------------------------------------------------------- 12 forecaster architecture
def model():
    p = _pred()
    n, nf, h = p["n_samples"], p["n_features"], p["horizon_s"]
    fig, ax = canvas(10, 6.4, 100, 64)
    A = dict(color=NAVY, fs=6.0)
    ax.text(50, 62, "Queue forecaster: what the gradient-boosting model sees, predicts, and where its output is used", ha="center", fontsize=7.4, color=NAVY, fontweight="bold")
    box(ax, 11, 46, 19, 14, "Simulator state\nat second t\n(per junction and\napproach, n x 4 rows)", NAVY, fs=6.4)
    box(ax, 36, 46, 25, 20, "Feature vector, %d values\nqueue · pcu_queue\nqueue_lag10 · queue_lag30\ninflow_30s · inbound_15s\nis_green · green_time\nis_entry · sin_day · cos_day" % nf, BLUE, fs=6.0)
    box(ax, 66, 54, 24, 6.4, "Gradient Boosting (USED)\n160 trees, depth 4, lr 0.08,\nsubsample 0.9", PURPLE, fs=5.8)
    box(ax, 66, 45.5, 24, 6.0, "Random Forest (baseline)\n80 trees, depth 10", GREY, fs=5.8)
    box(ax, 66, 37.5, 24, 5.4, "Persistence (baseline)\nforecast = queue now", GREY, fs=5.8)
    box(ax, 91, 46, 14, 20, "y_hat\nqueue\nat t + %d s\nclip to\n0..40" % h, TEAL, fs=6.2, bold=True)
    arrow(ax, (20.5, 46), (23.5, 46), **A)
    arrow(ax, (48.5, 50), (54, 54), **A)
    arrow(ax, (48.5, 46), (54, 45.5), **A)
    arrow(ax, (48.5, 42), (54, 38.5), **A)
    arrow(ax, (78, 54), (84, 50.5), **A)
    ax.text(2, 30.5, "Training and evaluation (QueuePredictor.fit)", fontsize=7.0, fontweight="bold", color=NAVY)
    box(ax, 27, 21, 50, 14.2, "build_dataset: 6 simulated runs of 1800 s under the 'adaptive' controller,\nalternating 2x2 / 3x3 grids, demand 0.7 / 1.0 / 1.3 / 1.6, start hours 7, 8, 12, 17;\nsnapshot every 10 s from t = 40; label = queue at t + 30 s\n-> %s rows x %d features" % (format(n, ","), nf), LIGHT, tc=INK, ec="#B7C3D3", fs=5.9)
    box(ax, 27, 5.6, 50, 6.8, "random 75 / 25 split (random_state 1); metrics: MAE and R2 for the three models;\nfeature importances kept for the Prediction page", LIGHT, tc=INK, ec="#B7C3D3", fs=5.9)
    arrow(ax, (27, 13.9), (27, 9.0), **A)
    ax.text(58, 30.5, "Use inside the 'advanced' controller", fontsize=7.0, fontweight="bold", color=NAVY)
    box(ax, 78, 21, 40, 14.2, "refreshed every 10 s once t >= 30;\n_pressure adds  0.7 * max(y_hat - queue, 0)  to each\napproach's score, so a queue that is about to grow\ntilts the next green toward it", ORANGE, fs=5.9)
    box(ax, 78, 5.6, 40, 6.8, "off when the 'ML forecast' toggle is off;\nthe other three controllers never read it", LIGHT, tc=INK, ec="#B7C3D3", fs=5.9)
    arrow(ax, (91, 36), (88, 28.2), **A)
    save(fig, OUT / "12_model_architecture.png")


def main():
    dfd2()
    sequence()
    use_case()
    er()
    flow_ctrl()
    flow_vision()
    model()


if __name__ == "__main__":
    main()
