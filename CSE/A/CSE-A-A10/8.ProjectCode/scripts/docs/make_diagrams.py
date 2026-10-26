"""FlowSense design diagrams 01-06 (matplotlib, 150 dpi) -> docs/diagrams/.  Diagrams 07-12 live in diagrams_more.py.

    python -m scripts.docs.make_diagrams            # from 8.ProjectCode; writes all twelve
Every diagram mirrors the code: smart_traffic/{sim,predictor,vision}.py and backend/{main,service,auth,config}.py.
"""
from __future__ import annotations

import math
from pathlib import Path

from .dgm_lib import *  # noqa: F401,F403

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------ 01 architecture
def architecture():
    fig, ax = canvas(9.6, 7.0, 100, 73)
    panel(ax, 1, 59, 98, 13, "TIER 1 - PRESENTATION (browser)", fc=PALE_BLUE, fs=9)
    box(ax, 22, 63.2, 38, 6.4, "React 19 + Vite console  :5310\nLanding · Login · Live · Benchmark ·\nVision · Prediction · Violations · About", BLUE, fs=7.2)
    box(ax, 55, 63.2, 22, 6.4, "axios client (src/api.js)\nBearer token kept\nin the browser", BLUE, fs=7.2)
    box(ax, 83, 63.2, 27, 6.4, "Legacy Streamlit app.py\n(same engine,\nseparate process)", GREY, fs=7.2)
    panel(ax, 1, 31, 98, 26, "TIER 2 - FastAPI application :8310 (backend/main.py, 20 routes, errors as {message, hint})", fc=PALE_PURPLE, fs=8.5)
    groups = [
        (13.2, "PUBLIC - no token (4)", "GET  /api/health\nPOST /api/auth/login\nGET  /api/auth/demo\nGET  /api/public/pulse"),
        (37.6, "SESSION, META, LIVE (6)", "GET  /api/auth/me\nGET  /api/meta\nGET  /api/live\nPUT  /api/live/config\nPOST /api/live/step\nPOST /api/live/ambulance"),
        (62.4, "LIVE + ANALYSIS (4)", "POST /api/live/reset\nPOST /api/benchmark\nPOST /api/benchmark/sweep\nGET  /api/violations"),
        (86.8, "VISION + PREDICTION (6)", "GET  /api/vision/synthetic\nGET  /api/vision/sample\nPOST /api/vision/analyze\nGET  /api/prediction\nGET  /api/prediction/live\nPOST /api/prediction/simulate"),
    ]
    for cx, t, body in groups:
        box(ax, cx, 44.2, 23.6, 17, "", PURPLE, alpha=0.12, ec=PURPLE, lw=1.1)
        ax.text(cx, 51.2, t, ha="center", va="center", fontsize=6.8, fontweight="bold", color=NAVY, zorder=4)
        ax.text(cx - 11.2, 44.0, body, ha="left", va="center", fontsize=6.0, color=INK, zorder=4, family="DejaVu Sans Mono", linespacing=1.32)
    ax.text(50, 33.0, "auth.py: HS256 token (stdlib hmac), 12 h life  ·  config.py: ports and demo account from .env  ·  Depends(current_user) guards 16 of the 20 routes",
            ha="center", fontsize=6.6, color=NAVY, zorder=4)
    panel(ax, 1, 10.5, 98, 19, "TIER 3 - service layer and traffic engine (pure Python, one process)", fc=PALE_TEAL, fs=8.5)
    box(ax, 17, 19.5, 29, 10.5, "backend/service.py\nLive (shared simulation) · Preview\nPredictor (background training)\nbenchmark · sweep · vision_* · violations", TEAL, fs=6.9)
    box(ax, 50, 19.5, 30, 10.5, "smart_traffic/sim.py\nSim: queues, signals, 4 controllers,\nemergencies, violation events,\nsummary(), feature_matrix()", TEAL, fs=6.9)
    box(ax, 83, 19.5, 29, 10.5, "predictor.py: QueuePredictor (GB)\nvision.py: YOLOv8n, light-bar rule,\nPCU density, scene renderer", TEAL, fs=6.9)
    arrow(ax, (31.6, 19.5), (34.8, 19.5), color=NAVY, lw=1.8)
    arrow(ax, (65.2, 19.5), (68.4, 19.5), color=NAVY, lw=1.8)
    panel(ax, 1, 0.5, 98, 8.5, "TIER 4 - state and files (NO database)", fc=LIGHT, fs=8.5)
    box(ax, 25, 3.3, 45, 4.2, "In memory: live sim, preview sim, benchmark cache,\nlast-benchmark violations, trained forecaster", GREY, fs=6.6)
    box(ax, 73, 3.3, 46, 4.2, "Files: yolov8n.pt · Ultralytics sample bus.jpg ·\n.env (ports, demo account) · docs/screenshots", GREY, fs=6.6)
    for x in (22, 55, 83):
        arrow(ax, (x, 59.8), (x, 57.2), color=NAVY, lw=1.6)
    arrow(ax, (50, 31), (50, 29.6), color=NAVY, lw=1.6)
    arrow(ax, (25, 10.5), (25, 9.0), color=GREY, lw=1.5)
    arrow(ax, (73, 10.5), (73, 9.0), color=GREY, lw=1.5)
    ax.text(60, 58.4, "HTTP + JSON  /api  (Vite proxy)", fontsize=6.5, color=NAVY, ha="left")
    save(fig, OUT / "01_system_architecture.png")


# --------------------------------------------------------- 02 high-level workflow
def workflow():
    fig, ax = canvas(9.6, 6.2, 100, 64.5)
    ax.text(50, 62.5, "Two lanes: the simulated control loop (closed) and the vision layer (demo; not wired into the controllers)", ha="center", fontsize=7.6, color=NAVY, fontweight="bold")
    panel(ax, 1, 31, 98, 29, "LANE A - control loop, repeated every simulated second", fc=PALE_BLUE, fs=8.5)
    xs = [9.4, 25.9, 42.4, 58.9, 75.4, 91.4]
    boxes = [
        ("1 SENSE", "Poisson arrivals\nfill approach\nqueues (PCU)", BLUE),
        ("2 FORECAST", "11 features -> GB,\nqueue at +30 s,\nrefresh every 10 s", PURPLE),
        ("3 DECIDE", "pressure score,\ninbound platoon,\nambulance target", NAVY),
        ("4 ACT", "keep or switch phase;\n3 s clearance then\nNS / EW green", TEAL),
        ("5 COORDINATE", "released vehicles ride\na 12 s link to the\nnext junction", ORANGE),
        ("6 REPORT", "KPIs, benchmark,\nviolation log,\nmap", GREY),
    ]
    for x, (t, body, c) in zip(xs, boxes):
        box(ax, x, 46.2, 14.0, 17.5, f"{t}\n\n{body}", c, fs=6.3)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 7.1, 46.2), (b - 7.1, 46.2), color=NAVY, lw=1.6)
    arrow(ax, (75.4, 35.8), (9.4, 35.8), color=GREY, ls="--", lw=1.2)
    ax.text(42, 33.2, "feedback: the new queues, phases and in-flight vehicles are the next second's input", ha="center", fontsize=6.5, color=GREY, style="italic")
    panel(ax, 1, 1, 98, 27, "LANE B - vision layer for one camera frame (API /api/vision/*)", fc=PALE_TEAL, fs=8.5)
    xb = [11, 29.5, 48, 66.5, 86]
    bb = [("FRAME", "upload, bundled\nphoto, or synthetic\noverhead scene", GREY),
          ("DETECT", "YOLOv8n (COCO):\ncar, bike, bus, truck;\nor contour detector", BLUE),
          ("LIGHT-BAR", "HSV red + blue blobs\ntouching -> relabel\nthe box ambulance", PURPLE),
          ("DENSITY", "PCU / 14 -> LOW,\nMEDIUM, HIGH, JAMMED;\ngreen-time hint", TEAL),
          ("ANNOTATE", "boxes, counts, level\nreturned as JSON\nand JPEG", NAVY)]
    for x, (t, body, c) in zip(xb, bb):
        box(ax, x, 12.5, 16.2, 15.5, f"{t}\n\n{body}", c, fs=6.3)
    for a, b in zip(xb[:-1], xb[1:]):
        arrow(ax, (a + 8.4, 12.5), (b - 8.4, 12.5), color=NAVY, lw=1.6)
    save(fig, OUT / "02_high_level_workflow.png")


# --------------------------------------------------------------- 03 DFD level 0
def _edge_pt(c, hw, hh, u):
    """Point where the ray from rectangle centre c in direction u leaves the rectangle."""
    t = min(hw / abs(u[0]) if u[0] else 1e9, hh / abs(u[1]) if u[1] else 1e9)
    return (c[0] + u[0] * t, c[1] + u[1] * t)


def dfd0():
    fig, ax = canvas(9.2, 6.0, 100, 65)
    cc, r = (50, 32.5), 12.5
    circle(ax, cc[0], cc[1], r, "FlowSense\nplatform\n(API + engine)", NAVY, fs=9)
    ents = {
        "op": ((13, 54), "OPERATOR\n(control-room user)", "login, network config,\nstep / ambulance / benchmark", "live KPIs, map, queues,\nforecasts, violation log"),
        "img": ((87, 54), "IMAGE SOURCE\n(camera frame, upload)", "JPG / PNG frame\n(<= 12 MB), confidence", "detections, PCU density,\nlight-bar flag"),
        "dev": ((13, 11), "EVALUATOR /\nDEVELOPER", "run_experiments, tests,\n.env settings", "metrics.json, test results,\nscreenshots"),
        "dem": ((87, 11), "SIMULATED DEMAND\n(seeded Poisson)", "vehicle arrivals,\nambulance events", None),
    }
    hw, hh = 9.6, 4.6
    for key, (c, name, to_lab, from_lab) in ents.items():
        box(ax, c[0], c[1], 2 * hw, 2 * hh, name, PALE_ORANGE, tc=INK, ec=ORANGE, fs=7.2, bold=True)
        v = (cc[0] - c[0], cc[1] - c[1])
        d = math.hypot(*v)
        u = (v[0] / d, v[1] / d)
        n = (-u[1], u[0])
        off = 2.4 if from_lab else 0.0
        e1 = _edge_pt(c, hw, hh, u)
        p_out = (e1[0] + n[0] * off, e1[1] + n[1] * off)
        q_out = (cc[0] - u[0] * r + n[0] * off * 0.6, cc[1] - u[1] * r + n[1] * off * 0.6)
        arrow(ax, p_out, q_out, None, color=NAVY, lw=1.5)
        mx, my = (p_out[0] + q_out[0]) / 2 + n[0] * 5.8, (p_out[1] + q_out[1]) / 2 + n[1] * 5.8
        ax.text(mx, my, to_lab, ha="center", va="center", fontsize=6.3, color=INK, zorder=5, bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))
        if from_lab:
            p_in = (e1[0] - n[0] * off, e1[1] - n[1] * off)
            q_in = (cc[0] - u[0] * r - n[0] * off * 0.6, cc[1] - u[1] * r - n[1] * off * 0.6)
            arrow(ax, q_in, p_in, None, color=TEAL, lw=1.5)
            mx, my = (p_in[0] + q_in[0]) / 2 - n[0] * 5.8, (p_in[1] + q_in[1]) / 2 - n[1] * 5.8
            ax.text(mx, my, from_lab, ha="center", va="center", fontsize=6.3, color=INK, zorder=5, bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))
    ax.text(50, 2.2, "Level 0: the whole product is one process. Demand is generated inside the platform (seeded); it is drawn as an external entity because a deployment would replace it with real cameras.",
            ha="center", fontsize=5.9, color=GREY, style="italic")
    save(fig, OUT / "03_dfd_level0.png")


# --------------------------------------------------------------- 04 DFD level 1
def dfd1():
    fig, ax = canvas(10, 7.4, 100, 74)
    ent = lambda cx, cy, t, w=15: box(ax, cx, cy, w, 6.4, t, PALE_ORANGE, tc=INK, ec=ORANGE, fs=7.0, bold=True)
    ent(8.5, 61, "OPERATOR", 15)
    ent(8.5, 46, "DEVELOPER", 15)
    ent(93, 61, "IMAGE\nSOURCE", 12)
    ent(93, 31, "OPERATOR\n(display)", 12)
    pr = lambda cx, cy, n, t, c=BLUE: circle(ax, cx, cy, 6.6, f"{n}\n{t}", c, fs=6.2)
    pr(30, 61, "1.0", "Authenticate\n& validate")
    pr(55, 61, "2.0", "Simulate\ntraffic", NAVY)
    pr(77, 61, "5.0", "Analyse\nvision frame", ORANGE)
    pr(30, 32, "4.0", "Forecast\nqueues", PURPLE)
    pr(55, 32, "3.0", "Control\nsignals", TEAL)
    pr(79, 32, "7.0", "Report KPIs,\nmap, log", GREY)
    pr(52, 10, "6.0", "Benchmark\ncontrollers", BLUE)
    st = lambda cx, cy, t, w: store(ax, cx, cy, w, 6.2, t, fs=6.2)
    st(42.5, 47, "D1  live / preview sim state\n(queues, phases, transit)", 25)
    st(77, 47.5, "D5  yolov8n.pt weights", 17)
    st(30, 18.5, "D2  trained forecaster", 22)
    st(66, 19.5, "D4  violation and\nemergency logs (in Sim)", 19)
    st(18, 10, "D3  benchmark cache +\nlast-benchmark violations", 25)
    A = dict(color=NAVY, fs=5.9)
    arrow(ax, (16.2, 62.6), (23.4, 62.6), "credentials,\ncommands", lo=(0, 3.4), **A)
    arrow(ax, (23.4, 59.4), (16.2, 59.4), "token, errors", lo=(0, -2.1), **A)
    arrow(ax, (16.2, 48), (25.6, 56.4), ".env settings", lo=(3.6, -3.2), **A)
    arrow(ax, (36.6, 61), (48.4, 61), "validated\ncommands", lo=(0, 3.4), **A)
    arrow(ax, (52, 54.4), (49, 50.1), "write state", lo=(-6.6, 0.5), **A)
    arrow(ax, (50, 43.9), (52.6, 38.4), "queues", lo=(5.2, 0.5), **A)
    arrow(ax, (36.5, 43.9), (31.6, 38.4), "queues, lags,\ninflow", lo=(-5.8, 1.2), **A)
    arrow(ax, (36.6, 32), (48.4, 32), "forecast\n(+30 s)", lo=(0, 3.4), **A)
    ax.annotate("", xy=(30, 22.1), xytext=(30, 25.4), arrowprops=dict(arrowstyle="<|-|>", color=NAVY, lw=1.3))
    ax.text(31.4, 23.7, "fit / predict", fontsize=5.9, ha="left", va="center", bbox=dict(fc="white", ec="none", pad=0.4))
    arrow(ax, (59.5, 26.6), (62.8, 22.6), "events", lo=(-3.8, -0.4), **A)
    arrow(ax, (72.4, 22.6), (76.2, 26.6), "log rows", lo=(4.3, -0.6), **A)
    arrow(ax, (54.4, 48.8), (73.6, 36.4), "state, KPIs", lo=(-1.5, 3.6), **A)
    arrow(ax, (87, 61), (83.6, 61), "frame,\nconf", lo=(0, 3.4), **A)
    arrow(ax, (77, 54.4), (77, 50.7), "load", lo=(4.5, 0), **A)
    arrow(ax, (82.5, 55.4), (91.2, 36.6), "detections, density,\nlight-bar flag", lo=(7.5, 1.5), **A)
    arrow(ax, (85.6, 32), (87.0, 32), "KPIs, map,\nviolation log", lo=(0, -5.5), **A)
    arrow(ax, (45.4, 10), (30.6, 10), "summaries", lo=(0, 2.1), **A)
    arrow(ax, (41.2, 16.2), (47.6, 14.6), "model", lo=(-1.0, 2.0), **A)
    ax.text(50, 0.9, "1.0 also validates the benchmark and vision requests it hands to 6.0 and 5.0; 6.0 builds its own simulations (it does not touch D1).",
            ha="center", fontsize=5.9, color=GREY, style="italic")
    save(fig, OUT / "04_dfd_level1.png")


# ------------------------------------------------------------- UML class diagram
def uml():
    fig, ax = canvas(10, 7.4, 100, 74)
    fs = 5.6

    def bus(y):
        arrow(ax, (28, y), (30, y), color=NAVY, lw=1.3)

    uml_class(ax, 1, 72, 25, "FastAPI app", ["title='FlowSense API'", "version='1.0.0'"],
              ["login(Login)", "live() live_config() live_step()", "live_ambulance() live_reset()", "benchmark(Bench) sweep()", "vision_*() prediction*()", "violations() health()"], hdr=NAVY, stereotype="main.py", fs=fs)
    uml_class(ax, 1, 43, 25, "auth / config", ["JWT_SECRET, TOKEN_HOURS=12", "DEMO_EMAIL, DEMO_PASSWORD"],
              ["make_token(email, name)", "read_token(token)", "check_credentials()", "current_user(header)"], hdr=GREY, stereotype="modules", fs=fs)
    uml_class(ax, 1, 23, 25, "Benchmark cache", ["_BENCH_CACHE: dict", "LAST_BENCH: dict"], ["benchmark(grid, secs, dem,", "          seeds, hour, use_ml)", "sweep(grid, use_ml)"], hdr=GREY, stereotype="service.py", fs=fs)
    uml_class(ax, 30, 72, 27, "Live", ["grid: '2x2' | '3x3'", "use_ml: bool", "sim: Sim"],
              ["configure(grid, controller,", "   demand, emergencies, use_ml)", "reset()  step(seconds)", "ambulance() -> entry", "snapshot() -> dict"], hdr=TEAL, stereotype="service.py", fs=fs)
    uml_class(ax, 30, 45, 27, "Preview", ["sim: Sim  (seed 21)", "seq: int, last: float"], ["pulse() -> dict   # landing"], hdr=TEAL, stereotype="service.py", fs=fs)
    uml_class(ax, 30, 31, 27, "Predictor", ["model: QueuePredictor", "error: str | None", "fit_seconds: float"], ["train()  # background thread", "ready -> bool"], hdr=TEAL, stereotype="service.py", fs=fs)
    uml_class(ax, 61, 72, 38, "Sim", ["rows, cols, controller, demand, seed, t", "q[j][a]: deque[Vehicle]; phase[j]; timer[j]; clear[j]", "transit: {arrive_t -> [(veh, j, a, dep, src)]}", "pred: ndarray (n x 4); predictor", "viol_log, emg_log, done_delays, qhist"],
              ["step()  run(seconds)  summary()", "_arrivals()  _transit_arrivals()  _signals()", "_decide(j)  _pressure(j, phase, adv)", "_emergency_target(j)  _scan_upstream()", "_discharge()  _release()  _record()", "feature_matrix() -> (n*4, 11)"], hdr=NAVY, fs=fs)
    uml_class(ax, 81, 37, 18, "Vehicle", ["id, vtype, t0, wait", "emg, red_runner", "u[10], hop, plate"], [], hdr=BLUE, fs=fs)
    uml_class(ax, 61, 37, 19, "QueuePredictor", ["model: GradientBoosting", "metrics, importance", "test, n_samples"], ["fit(X, y)", "predict(X)  # clip 0..40"], hdr=PURPLE, fs=fs)
    uml_class(ax, 61, 20, 38, "vision  (module)", ["COCO_VEHICLES, PCU, BOX_COLORS"],
              ["detect_yolo(bgr, conf)  detect_classical(bgr)", "detect_lightbars(bgr)  lightbar_masks(bgr)", "density_report(dets)  annotate(bgr, dets)", "render_scene(n, emergency, phase, seed)"], hdr=ORANGE, stereotype="smart_traffic/vision.py", fs=fs)
    # app -> services bus
    ax.plot([28, 28], [9, 67], color=NAVY, lw=1.3, zorder=1)
    ax.plot([26, 28], [67, 67], color=NAVY, lw=1.3, zorder=1)
    for y in (67, 41, 25):
        bus(y)
    ax.annotate("", xy=(26, 12), xytext=(28, 12), arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=1.3))
    ax.text(20.5, 46.3, "Depends(current_user)", fontsize=5.4, color=GREY, ha="center")
    ax.annotate("", xy=(13.5, 43.1), xytext=(13.5, 47.6), arrowprops=dict(arrowstyle="-|>", color=GREY, lw=1.1))
    # Live / Preview -> Sim
    ax.annotate("", xy=(61, 67), xytext=(57, 67), arrowprops=dict(arrowstyle="-|>", color=TEAL, lw=1.6))
    ax.text(59, 68.4, "owns 1", fontsize=5.4, color=GREY, ha="center")
    ax.annotate("", xy=(61, 47.5), xytext=(57, 43), arrowprops=dict(arrowstyle="-|>", color=TEAL, lw=1.4))
    ax.text(57.6, 46.8, "owns 1", fontsize=5.4, color=GREY, ha="center", rotation=0)
    # Sim -> Vehicle / QueuePredictor
    ax.annotate("", xy=(89.5, 37), xytext=(89.5, 42.0), arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=1.3))
    ax.text(87.8, 39.5, "queues hold 0..*", fontsize=5.4, color=GREY, ha="right", bbox=dict(fc="white", ec="none", pad=0.3))
    ax.annotate("", xy=(70, 37), xytext=(70, 42.0), arrowprops=dict(arrowstyle="-|>", color=PURPLE, lw=1.3, ls="--"))
    ax.text(71.3, 39.5, "uses (optional)", fontsize=5.4, color=GREY, ha="left", bbox=dict(fc="white", ec="none", pad=0.3))
    # Predictor -> QueuePredictor (horizontal under Vehicle)
    ax.annotate("", xy=(61, 27.0), xytext=(57, 27.0), arrowprops=dict(arrowstyle="-|>", color=PURPLE, lw=1.4))
    ax.text(59, 28.3, "holds", fontsize=5.4, color=GREY, ha="center")
    # vision usage note
    ax.text(30, 6.4, "service.py vision_*() functions call the vision module; Predictor.train() runs\nin a daemon thread started by the FastAPI startup hook.", fontsize=5.6, color=GREY, ha="left", style="italic")
    ax.text(50, 1.0, "Solid arrows: composition or use. Dashed: optional use (only the 'advanced' controller reads the forecaster). Vehicles are created by Sim._new_vehicle().",
            ha="center", fontsize=5.8, color=GREY, style="italic")
    save(fig, OUT / "06_uml_class.png")


def main():
    architecture()
    workflow()
    dfd0()
    dfd1()
    uml()
    try:
        from . import diagrams_more
    except ImportError:
        return
    diagrams_more.main()


if __name__ == "__main__":
    main()
