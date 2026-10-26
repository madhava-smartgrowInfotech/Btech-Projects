"""
Draws every design diagram used in the project documents (matplotlib only, 150 dpi).

    python scripts/make_diagrams.py            # -> docs/diagrams/*.png

Each diagram mirrors what the code does:
  backend/main.py (FastAPI routes), backend/session.py (RiderSession), app.py (Tk desktop app),
  core.py (RiskEngine, Calibration, Settings), vision.py (MediaPipe landmarks + quality gates),
  storage.py (SQLite events, settings.json), research.py (offline evaluation).
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyBboxPatch, Polygon, Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "diagrams")
os.makedirs(OUT, exist_ok=True)

NAVY, INK, SLATE = "#1B2A41", "#0F172A", "#475569"
ORANGE, BLUE, GREEN, PURPLE, GOLD = "#EB6834", "#2A78D6", "#1BAF7A", "#6B52D6", "#E8A317"
PAPER, LINE = "#F6F8FB", "#9AA8BD"
plt.rcParams["font.family"] = "DejaVu Sans"


def canvas(w, h, title=None, ty=99):
    """Work in a 100 x (ty+2) coordinate space; the figure is cropped to its content when saved."""
    top = ty + 2
    fig, ax = plt.subplots(figsize=(w, w * top / 100))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, top)
    ax.axis("off")
    ax.set_aspect("equal")
    if title:
        ax.text(1, ty, title, fontsize=13, fontweight="bold", color=NAVY, va="top")
    return fig, ax


def box(ax, x, y, w, h, text, fc=PAPER, ec=LINE, tc=INK, fs=9.5, bold=False, lw=1.3, rounding=1.2, ls="-"):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={rounding}", fc=fc, ec=ec, lw=lw, ls=ls)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc,
            fontweight="bold" if bold else "normal", linespacing=1.25)
    return (x, y, w, h)


def arrow(ax, p, q, label=None, color=SLATE, lw=1.4, ls="-", fs=8, off=(0, 1.2), rad=0.0, head="-|>", lab_ha="center", lp=None):
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle=head, color=color, lw=lw, ls=ls,
                                                    connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0))
    if label:
        lx, ly = lp if lp else ((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1])
        ax.text(lx, ly, label, fontsize=fs, color=color,
                ha=lab_ha, va="center", bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))


def line(ax, pts, color=SLATE, lw=1.4, ls="-"):
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color=color, lw=lw, ls=ls, solid_capstyle="butt")


def poly_arrow(ax, pts, label=None, lp=None, color=SLATE, lw=1.4, ls="-", fs=8, lab_ha="center"):
    """Polyline with an arrow head on the last segment."""
    if len(pts) > 2:
        line(ax, pts[:-1], color, lw, ls)
    arrow(ax, pts[-2], pts[-1], None, color=color, lw=lw, ls=ls)
    if label:
        ax.text(lp[0], lp[1], label, fontsize=fs, color=color, ha=lab_ha, va="center",
                bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", path)


def mid(b, side):
    x, y, w, h = b
    return {"l": (x, y + h / 2), "r": (x + w, y + h / 2), "t": (x + w / 2, y + h), "b": (x + w / 2, y)}[side]


# ---------------------------------------------------------------- 01 architecture
def architecture():
    fig, ax = canvas(11, 7.6, "System architecture", ty=78)
    for x, w, label in ((1, 22, "Client tier"), (26, 26, "Application tier"), (55, 23, "Shared Python modules"), (81, 18, "Data tier")):
        ax.add_patch(Rectangle((x, 6), w, 66, fc="#FBFCFE", ec="#D5DCE6", lw=1))
        ax.text(x + w / 2, 69.6, label, ha="center", fontsize=9.5, color=SLATE, fontweight="bold")
    spa = box(ax, 3, 44, 18, 20, "React SPA\n(Vite, TypeScript)\nport 5306\n\nbrowser webcam via\ngetUserMedia;\nJPEG frames 640x480", fc="#E8F0FC", ec=BLUE, fs=8)
    tk = box(ax, 3, 12, 18, 20, "Tkinter desktop app\napp.py\n(Application)\n\nCameraWorker thread\ncv2.VideoCapture\n(DirectShow)", fc="#FFF1EA", ec=ORANGE, fs=8)
    api = box(ax, 28, 48, 22, 16, "FastAPI service\nbackend/main.py\nport 8306\nHMAC-signed demo login,\nvalidated inputs", fc="#E6F6EF", ec=GREEN, fs=8)
    ses = box(ax, 28, 25, 22, 16, "backend/session.py\nRiderSession\n(one per browser tab)\nsource, calibration,\nmonitoring state", fc="#E6F6EF", ec=GREEN, fs=8)
    vis = box(ax, 57, 50, 19, 14, "vision.py  Vision\nMediaPipe Face Landmarker\n+ 7 pixel quality gates\nEAR, head roll", fc=PAPER, ec=NAVY, fs=7.8)
    core = box(ax, 57, 33, 19, 13, "core.py\nRiskEngine, Calibration,\nSettings, simulate()\nrule decisions", fc=PAPER, ec=NAVY, fs=7.8)
    sto = box(ax, 57, 20, 19, 9, "storage.py  Store\nSQLite + JSON", fc=PAPER, ec=NAVY, fs=7.8)
    res = box(ax, 57, 8, 19, 9, "research.py (offline)\nnearest-centroid eval", fc="#F1EEFC", ec=PURPLE, fs=7.8)
    mdl = box(ax, 83, 50, 15, 14, "models/\nface_landmarker\n.task\n(downloaded once)", fc="#FFF8E5", ec=GOLD, fs=7.8)
    ev = box(ax, 83, 33, 15, 12, "data/\nevents.sqlite3\ntable events", fc="#FFF8E5", ec=GOLD, fs=7.8)
    st = box(ax, 83, 20, 15, 9, "data/\nsettings.json", fc="#FFF8E5", ec=GOLD, fs=7.8)
    rr = box(ax, 83, 8, 15, 9, "research_results/\nreport.json, .npz,\nmatrix PNG", fc="#FFF8E5", ec=GOLD, fs=7.2)
    arrow(ax, mid(spa, "r"), mid(api, "l"), "REST + JPEG\nover HTTP", color=BLUE, off=(0, 3.2), fs=7.4)
    arrow(ax, (39, 48), (39, 41), "frame(), tick()", off=(0, 0), lp=(45.5, 44.5), fs=7.4)
    arrow(ax, mid(ses, "r"), (57, 55), None, color=GREEN)
    arrow(ax, (50, 31), (57, 39.5), None, color=GREEN)
    arrow(ax, (50, 28), (57, 24.5), None, color=GREEN)
    poly_arrow(ax, [(21, 22), (54, 22), (57, 36)], "imports the same modules\n(no HTTP)", lp=(36, 18.6), color=ORANGE, ls="--", fs=7.4)
    arrow(ax, mid(vis, "r"), mid(mdl, "l"), "load once", off=(0, 2.0), fs=7.4, ls="--")
    arrow(ax, (76, 26), (83, 38), "events", off=(1.0, 0), lp=(79.4, 33.6), fs=7.2)
    arrow(ax, (76, 24), (83, 24.5), "settings", off=(0, 1.8), fs=7.2)
    arrow(ax, (76, 12.5), (83, 12.5), "report", off=(0, 1.8), fs=7.2)
    ax.text(50, 1.6, "The REST API and the Tk app share core.py, vision.py and storage.py, so both front ends write to the same SQLite file.\n"
                     "Video frames exist only in RAM; only numeric events are stored. research.py never changes the live rules.",
            ha="center", fontsize=7.8, color=SLATE, style="italic")
    save(fig, "01_system_architecture.png")


# ---------------------------------------------------------------- 02 workflow
def workflow():
    fig, ax = canvas(11, 5.2, "High-level workflow of a monitoring session", ty=54)
    steps = [
        ("1  Sign in", "demo account,\nHMAC token (12 h)", NAVY),
        ("2  Choose source", "webcam, or Simulation\n(4 scripted scenarios)", BLUE),
        ("3  Calibrate", "camera only: 8-15 s, eyes\nopen; threshold =\n0.72 x median EAR", ORANGE),
        ("4  Monitor", "frame -> Observation ->\nquality gates -> RiskEngine", PURPLE),
        ("5  Verdict", "Normal / Possible\nimpairment or drowsiness /\nUnable to assess", GREEN),
        ("6  Log", "numeric event row on state\nchange, every 5 s, or alert", GOLD),
        ("7  Review", "history table, EAR chart,\nCSV export", NAVY),
        ("8  Tune / research", "thresholds; offline evaluation\n(never alters live rules)", BLUE),
    ]
    bw, gap = 21.2, 4.0
    for i, (t, s, c) in enumerate(steps):
        row_y = 24 if i < 4 else 4
        xx = 1.5 + (i % 4) * (bw + gap)
        box(ax, xx, row_y, bw, 15, "", fc="white", ec=c, lw=2)
        ax.add_patch(Rectangle((xx, row_y + 10.4), bw, 4.6, fc=c, ec=c))
        ax.text(xx + bw / 2, row_y + 12.7, t, ha="center", va="center", color="white", fontsize=9.6, fontweight="bold")
        ax.text(xx + bw / 2, row_y + 5.0, s, ha="center", va="center", color=INK, fontsize=8.0, linespacing=1.3)
        if i % 4 != 3:
            arrow(ax, (xx + bw, row_y + 6), (xx + bw + gap, row_y + 6))
    x4 = 1.5 + 3 * (bw + gap) + bw / 2
    x5 = 1.5 + bw / 2
    poly_arrow(ax, [(x4, 24), (x4, 21.5), (x5, 21.5), (x5, 19)])
    ax.text(50, 47.4, "A frame that fails a quality gate (no face, poor light, blur, motion, covered eyes) gives\n"
                      "'Unable to assess' and clears the evidence: the system never guesses.",
            ha="center", fontsize=8.2, color=SLATE, style="italic", linespacing=1.4)
    ax.text(50, 41.4, "Step 3 is optional: without it the default EAR threshold 0.21 is used.\n"
                      "Simulation needs no webcam and cannot write a calibration.",
            ha="center", fontsize=8.2, color=SLATE, style="italic", linespacing=1.4)
    save(fig, "02_high_level_workflow.png")


# ---------------------------------------------------------------- DFD helpers
def process(ax, cx, cy, r, text, num, fs=8):
    ax.add_patch(Circle((cx, cy), r, fc="#E8F0FC", ec=BLUE, lw=1.6))
    ax.text(cx, cy + r * 0.52, num, ha="center", va="center", fontsize=8.5, fontweight="bold", color=BLUE)
    ax.text(cx, cy - r * 0.14, text, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.2)
    return (cx, cy, r)


def entity(ax, x, y, w, h, text):
    ax.add_patch(Rectangle((x, y), w, h, fc="#FFF1EA", ec=ORANGE, lw=1.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9, color=INK, fontweight="bold", linespacing=1.2)
    return (x, y, w, h)


def store(ax, x, y, w, h, text, tag):
    ax.add_patch(Rectangle((x, y), w, h, fc="#FFF8E5", ec="none"))
    ax.plot([x, x + w], [y + h, y + h], color=GOLD, lw=1.8)
    ax.plot([x, x + w], [y, y], color=GOLD, lw=1.8)
    ax.plot([x, x], [y, y + h], color=GOLD, lw=1.8)
    ax.text(x + 1.3, y + h / 2, tag, ha="left", va="center", fontsize=8.5, fontweight="bold", color=GOLD)
    ax.text(x + w / 2 + 2.5, y + h / 2, text, ha="center", va="center", fontsize=8.2, color=INK, linespacing=1.2)
    return (x, y, w, h)


def pt(c, ang_deg):
    """Point on the circle (cx, cy, r) at an angle in degrees."""
    import math
    cx, cy, r = c
    return (cx + r * math.cos(math.radians(ang_deg)), cy + r * math.sin(math.radians(ang_deg)))


def tag(ax, x, y, text, fs=7.4, color=SLATE, ha="center"):
    ax.text(x, y, text, fontsize=fs, color=color, ha=ha, va="center", linespacing=1.2,
            bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))


# ---------------------------------------------------------------- 03 DFD 0
def dfd0():
    fig, ax = canvas(10.5, 5.6, "Data flow diagram, level 0 (context diagram)", ty=58)
    entity(ax, 1, 33, 17, 14, "Rider /\nDemonstrator")
    entity(ax, 1, 6, 17, 10, "Webcam")
    entity(ax, 82, 22, 17, 14, "Reviewer /\nResearcher")
    c = process(ax, 50, 30, 15, "Smart Rider\nImpairment Warning\nSystem", "0", fs=9.5)
    arrow(ax, (18, 44), pt(c, 152), None)
    tag(ax, 27.5, 47.4, "credentials, source choice,\nthresholds, calibrate / start", 7.6)
    arrow(ax, pt(c, 190), (18, 36), None)
    tag(ax, 27.5, 24.6, "verdict, reason, warning,\nmeasurements, history", 7.6)
    arrow(ax, (18, 11), pt(c, 228), None)
    tag(ax, 28, 9.8, "video frames\n(kept in RAM only)", 7.6)
    arrow(ax, (82, 33), pt(c, 25), None)
    tag(ax, 76, 40.4, "labelled, consented\nmeasurement CSV,\nheld-out subject IDs", 7.6)
    arrow(ax, pt(c, 337), (82, 25), None)
    tag(ax, 74, 15.6, "event history, CSV export,\nevaluation report", 7.6)
    ax.text(50, 2.5, "A camera cannot confirm alcohol use: the verdict is a possible-impairment or drowsiness indicator, not an alcohol result.",
            ha="center", fontsize=8, color=SLATE, style="italic")
    save(fig, "03_dfd_level0.png")


# ---------------------------------------------------------------- 04 DFD 1
def dfd1():
    fig, ax = canvas(11, 8.4, "Data flow diagram, level 1", ty=94)
    entity(ax, 50, 85, 24, 8, "Rider / Demonstrator")
    entity(ax, 1, 8, 14, 8, "Webcam")
    entity(ax, 83, 1, 16, 8, "Reviewer /\nResearcher")
    r = 7.6
    p1 = process(ax, 14, 70, r, "Authenticate", "1", 7.8)
    p6 = process(ax, 86, 68, r, "Settings, calibration\nand session control", "6", 6.4)
    p2 = process(ax, 13, 44, r, "Capture and\nvalidate frame", "2", 7.0)
    p3 = process(ax, 36, 44, r, "Extract\nobservation", "3", 7.4)
    p4 = process(ax, 62, 44, r, "Assess risk\n(rule engine)", "4", 7.4)
    p5 = process(ax, 87, 44, r, "Log and\nexport events", "5", 7.2)
    p7 = process(ax, 58, 18, r, "Offline research\nevaluation", "7", 7.0)
    store(ax, 66, 54, 14, 5, "settings.json", "D2")
    store(ax, 78, 21, 21, 6, "events.sqlite3", "D1")
    store(ax, 40, 1, 30, 5, "research_results/", "D3")
    # rider <-> authenticate / settings
    arrow(ax, (50, 87), pt(p1, 40), None)
    tag(ax, 38.5, 78.2, "email, password", 7.2)
    arrow(ax, pt(p1, 75), (50, 91), None)
    tag(ax, 31, 87.4, "signed demo token", 7.2)
    arrow(ax, (74, 89), pt(p6, 118), None)
    tag(ax, 84, 86.6, "thresholds, source,\ncalibrate, start / stop", 7.0)
    # frame pipeline
    arrow(ax, (8, 16), pt(p2, 255), None)
    tag(ax, 8, 28, "video frame", 7.2)
    arrow(ax, pt(p2, 0), pt(p3, 180), None)
    tag(ax, 24.5, 47.6, "valid frame", 7.0)
    arrow(ax, pt(p3, 0), pt(p4, 180), None)
    tag(ax, 49, 49.6, "Observation\n(EAR, roll,\nquality)", 6.6)
    arrow(ax, pt(p4, 0), pt(p5, 180), None)
    tag(ax, 74.5, 47.4, "Decision", 7.2)
    # verdict back to rider
    arrow(ax, (62, 51.7), (62, 85), None)
    tag(ax, 62, 66, "verdict, reason,\nwarning, measurements", 7.0)
    # history to rider (right-hand channel)
    poly_arrow(ax, [(94.2, 46), (98, 46), (98, 89), (74, 89)], None)
    tag(ax, 96, 80.5, "history,\nCSV export", 7.0)
    # calibration observations to process 6
    arrow(ax, pt(p3, 55), pt(p6, 188), None)
    tag(ax, 52, 60.8, "calibration\nobservations", 7.0)
    # settings store
    arrow(ax, pt(p6, 250), (80, 58.5), None)
    tag(ax, 88.8, 58.4, "validated\nsettings", 6.8)
    arrow(ax, (70, 54), pt(p4, 62), None)
    tag(ax, 73.5, 51.2, "thresholds", 7.0)
    # events store
    arrow(ax, (84, 36.4), (84, 27), None)
    arrow(ax, (89, 27), (89, 36.4), None)
    tag(ax, 80.2, 31.8, "event\nrow", 6.8)
    tag(ax, 92.6, 31.8, "rows", 6.8)
    # research
    arrow(ax, (83, 6), pt(p7, 345), None)
    tag(ax, 77.5, 13.4, "labelled consented\nCSV, held-out IDs", 6.8)
    arrow(ax, pt(p7, 298), (83, 3), None)
    tag(ax, 74, 4.2, "evaluation report", 6.8)
    arrow(ax, pt(p7, 265), (57.5, 6), None)
    tag(ax, 47, 10.6, "report.json,\nmodel, matrix", 6.8)
    save(fig, "04_dfd_level1.png")


# ---------------------------------------------------------------- 05 DFD 2
def dfd2():
    fig, ax = canvas(11, 8.4, "Data flow diagram, level 2: processes 3 and 4 in detail", ty=98)
    r = 6.9
    entity(ax, 1, 60, 14, 14, "Frame\n(BGR,\n640x480)")
    box(ax, 12, 82, 32, 7, "Decision: Unable to assess (reason = quality)\nreset(): evidence cleared", fc="#FFF1EA", ec=ORANGE, fs=7.4)
    p31 = process(ax, 29, 67, r, "Quality\ngates", "3.1", 7.4)
    p32 = process(ax, 52, 67, r, "EAR and\nhead roll", "3.2", 7.4)
    p33 = process(ax, 75, 67, r, "3-sample\nmedian", "3.3", 7.4)
    p41 = process(ax, 22, 40, r, "Closure timer\nand blinks", "4.1", 6.8)
    p42 = process(ax, 47, 40, r, "10 s closed\nfraction", "4.2", 7.0)
    p43 = process(ax, 72, 40, r, "Head tilt with\nlow EAR", "4.3", 6.8)
    p44 = process(ax, 36, 14, r, "Persistence\nchecks", "4.4", 7.2)
    p45 = process(ax, 62, 14, r, "Alert\ncooldown", "4.5", 7.2)
    entity(ax, 83, 8, 16, 12, "Decision\n(state, reason,\nmeasurements,\nalert)")
    store(ax, 84, 38, 15, 5, "settings", "D2")
    arrow(ax, (15, 67), pt(p31, 180), None)
    arrow(ax, pt(p31, 0), pt(p32, 180), None)
    tag(ax, 40.5, 70.4, "frame passes", 7.0)
    arrow(ax, pt(p32, 0), pt(p33, 180), None)
    tag(ax, 63.5, 70.4, "EAR, roll", 7.0)
    arrow(ax, pt(p31, 100), (29, 82), None)
    tag(ax, 24, 78.4, "fails a gate", 7.0)
    tag(ax, 41, 58.2, "7 gates: light, blur,\nmotion, face count, eye\nsize, eye patch, geometry", 6.4)
    # bus from 3.3 to 4.x
    line(ax, [(75, 60.1), (75, 54), (22, 54)])
    arrow(ax, (22, 54), pt(p41, 90), None)
    arrow(ax, (47, 54), pt(p42, 90), None)
    arrow(ax, (72, 54), pt(p43, 90), None)
    tag(ax, 60, 55.6, "smoothed EAR, roll, time t", 7.0)
    # to 4.4
    arrow(ax, pt(p41, 300), pt(p44, 140), None)
    tag(ax, 24, 25.4, "closure s", 7.0)
    arrow(ax, pt(p42, 255), pt(p44, 60), None)
    tag(ax, 43.4, 28.4, "fraction", 7.0)
    poly_arrow(ax, [pt(p43, 270), (72, 26), (52, 26), (40.5, 20.6)], None)
    tag(ax, 61.5, 26, "tilt + closed", 7.0)
    arrow(ax, pt(p44, 0), pt(p45, 180), None)
    tag(ax, 49, 17.4, "state:\nWARNING", 7.0)
    arrow(ax, pt(p45, 0), (83, 14), None)
    tag(ax, 74, 17.4, "alert flag", 7.0)
    # settings feed
    arrow(ax, (84, 40.5), pt(p43, 0), None)
    tag(ax, 91.5, 46.4, "thresholds", 7.0)
    ax.text(50, 1.2, "D2 supplies every limit (EAR threshold, closure s, persistence s, closed fraction, tilt degrees, cooldown s). "
                     "A failed gate resets 4.1-4.5 but keeps the cooldown clock.",
            ha="center", fontsize=7.4, color=SLATE, style="italic")
    save(fig, "05_dfd_level2.png")


# ---------------------------------------------------------------- 06 UML class
def uml_class(ax, x, y, w, name, attrs, methods, stereo=None, color=BLUE, fs=7.4):
    lh = 2.2
    h = 4.6 + lh * (len(attrs) + len(methods)) + (1.2 if attrs and methods else 0) + 0.8
    ax.add_patch(Rectangle((x, y - h), w, h, fc="white", ec=color, lw=1.6))
    ax.add_patch(Rectangle((x, y - 4.6), w, 4.6, fc=color, ec=color))
    if stereo:
        ax.text(x + w / 2, y - 1.1, f"<<{stereo}>>", ha="center", va="center", color="white", fontsize=6.6)
        ax.text(x + w / 2, y - 3.1, name, ha="center", va="center", color="white", fontsize=8.4, fontweight="bold")
    else:
        ax.text(x + w / 2, y - 2.3, name, ha="center", va="center", color="white", fontsize=8.4, fontweight="bold")
    cy = y - 4.6 - 1.2
    for a in attrs:
        ax.text(x + 0.8, cy, a, fontsize=fs, va="center", color=INK, family="monospace")
        cy -= lh
    if attrs and methods:
        ax.plot([x, x + w], [cy + 0.3, cy + 0.3], color=color, lw=0.8)
        cy -= 0.9
    for m in methods:
        ax.text(x + 0.8, cy, m, fontsize=fs, va="center", color=INK, family="monospace")
        cy -= lh
    return (x, y - h, w, h)


def class_diagram():
    fig, ax = canvas(11.5, 10, "UML class diagram (core, vision, storage, web session)", ty=104)
    W = 20.5
    X = [1, 26.5, 52, 77.5]
    uml_class(ax, X[0], 96, W, "Application", [
        "store: Store", "settings: Settings", "engine: RiskEngine", "worker: CameraWorker", "calibration: Calibration"],
        ["start_camera()", "calibrate()", "consume(o, frame)", "tick()", "history() / export_csv()", "thresholds() / research()"],
        stereo="app.py, Tkinter", color=ORANGE)
    uml_class(ax, X[0], 58, W, "CameraWorker", ["index: int", "stop_event: Event", "results: Queue(2)"],
              ["run()", "publish(item)", "stop()"], stereo="Thread, vision.py", color=ORANGE)
    uml_class(ax, X[0], 32, W, "Vision", ["detector: FaceLandmarker", "previous: ndarray", "last_ms: int"],
              ["process(frame, now)", "  -> Observation", "close()"], stereo="vision.py", color=PURPLE)
    uml_class(ax, X[1], 96, W, "RiderSession", [
        "id: str", "settings: Settings", "engine: RiskEngine", "vision: Vision", "calibration: Calibration",
        "source / scenario", "monitoring: bool"],
        ["set_source()", "set_monitoring()", "set_calibration()", "frame(jpeg) -> jpeg", "tick()", "consume(o)", "snapshot()", "apply_settings()"],
        stereo="backend/session.py", color=GREEN)
    uml_class(ax, X[1], 52, W, "SessionError", ["status: int"], ["(user-facing failure,", " carries HTTP status)"],
              stereo="Exception", color=SLATE)
    uml_class(ax, X[1], 34, W, "Observation", ["t: float", "ear: float", "roll: float", "quality: str", "brightness, sharpness"],
              [], stereo="dataclass", color=BLUE)
    uml_class(ax, X[2], 96, W, "RiskEngine", [
        "settings: Settings", "samples, ears, blinks", "closed_since: float", "risk_since: float", "good_since: float", "last_alert: float"],
        ["reset()", "update(o) -> Decision"], stereo="core.py", color=BLUE)
    uml_class(ax, X[2], 66, W, "Decision", ["state: str", "reason: str", "quality: str", "ear, closure: float", "blink_rate: float",
                                            "closed_fraction: float", "roll: float", "alert: bool"], [], stereo="dataclass", color=BLUE)
    uml_class(ax, X[2], 38, W, "Calibration", ["start: float", "values: list[float]", "attempts: int"],
              ["add(o) -> threshold |", "   None | ValueError"], stereo="core.py", color=BLUE)
    uml_class(ax, X[3], 96, W, "Store", ["directory: Path", "db: sqlite3.Connection"],
              ["add(source, decision)", "recent(limit)", "export(path)", "load_settings()", "save_settings(s)", "close()"],
              stereo="storage.py", color=GOLD)
    uml_class(ax, X[3], 66, W, "Settings", [
        "ear_threshold = 0.21", "closure_seconds = 1.5", "persistence_seconds = 1.0", "closed_fraction = 0.55",
        "tilt_degrees = 25", "cooldown_seconds = 15", "calibrated: bool"], ["validate() -> Settings"], stereo="dataclass", color=BLUE)

    def link(p, q, label=None, lp=None, dashed=False, color=SLATE):
        arrow(ax, p, q, None, color=color, ls="--" if dashed else "-", lw=1.2)
        if label:
            tag(ax, lp[0], lp[1], label, 6.6, color)

    link((X[0] + W / 2, 65.2), (X[0] + W / 2, 58), "owns 0..1", (X[0] + W / 2 + 6, 61.6), color=ORANGE)
    link((X[0] + W / 2, 38.2), (X[0] + W / 2, 32), "creates", (X[0] + W / 2 + 4.5, 35.1), color=ORANGE)
    poly_arrow(ax, [(X[0] + 4, 96), (X[0] + 4, 99.4), (X[2] + W / 2, 99.4), (X[2] + W / 2, 96)], "owns 1", (36.5, 99.4),
               color=ORANGE, lw=1.2, fs=6.6)
    link((X[1], 56), (X[0] + W, 26), "0..1", (X[0] + W + 2.8, 44.5), color=GREEN)
    link((X[1] + W, 90), (X[2], 90), "owns 1", (X[1] + W + 2.7, 91.8), color=GREEN)
    link((X[1] + W, 64), (X[2], 36), "0..1", (X[1] + W + 2.2, 52.0), color=GREEN)
    link((X[1] + W / 2, 56.4), (X[1] + W / 2, 52), "raises", (X[1] + W / 2 + 4.5, 54.2), dashed=True, color=SLATE)
    link((X[0] + W, 24), (X[1], 28), "creates", (X[0] + W + 2.8, 21.2), dashed=True, color=PURPLE)
    link((X[2], 30), (X[1] + W, 28), "reads", (X[1] + W + 2.8, 31.4), dashed=True)
    link((X[2] + W / 2, 71.8), (X[2] + W / 2, 66), "returns", (X[2] + W / 2 + 4.2, 69.0), dashed=True)
    link((X[2] + W, 80), (X[3], 62), "uses", (X[2] + W + 2.8, 72.4))
    link((X[3] + W / 2, 71.8), (X[3] + W / 2, 66), "load / save", (X[3] + W / 2 + 5.8, 69.0), color=GOLD)
    ax.text(1, 6, "Solid arrow: holds / uses.  Dashed arrow: creates, returns, reads or raises.  Application (Tk) and RiderSession (web) are two front ends over the same core.py,\n"
                  "vision.py and storage.py: both also hold a Store and a Settings object and write Decision rows through Store.add(). Store opens a fresh SQLite connection\n"
                  "per web call because sqlite connections are bound to the thread that created them.",
            fontsize=7.2, color=SLATE, style="italic", linespacing=1.4)
    save(fig, "06_uml_class_diagram.png")


def sequence():
    fig, ax = canvas(11, 9.6, "Sequence diagram: one camera frame (POST /api/session/{id}/frame)", ty=100)
    names = [("Browser", "React SPA", BLUE), ("FastAPI", "backend/main.py", GREEN), ("RiderSession", "backend/session.py", GREEN),
             ("Vision", "vision.py", PURPLE), ("RiskEngine", "core.py", NAVY), ("Store", "storage.py, SQLite", GOLD)]
    xs = [9, 26, 43, 60, 76, 91]
    top, bottom = 92, 4
    for x, (a, b, c) in zip(xs, names):
        box(ax, x - 7.2, top, 14.4, 6, f"{a}\n{b}", fc="white", ec=c, fs=7.8, bold=False, lw=1.8)
        ax.plot([x, x], [top, bottom], color=c, lw=1.0, ls=(0, (5, 4)))

    def msg(i, j, y, text, dashed=False, color=SLATE, above=True):
        x1, x2 = xs[i], xs[j]
        arrow(ax, (x1, y), (x2, y), None, color=color, ls="--" if dashed else "-", lw=1.3)
        cx = (x1 + x2) / 2
        ax.text(cx, y + 1.5, text, ha="center", va="bottom", fontsize=7.2, color=INK, linespacing=1.15,
                bbox=dict(fc="white", ec="none", pad=0.5, alpha=0.9))

    def selfcall(i, y, text, w=7.5, color=SLATE):
        x = xs[i]
        line(ax, [(x, y), (x + w, y), (x + w, y - 2.6)], color=color, lw=1.3)
        arrow(ax, (x + w, y - 2.6), (x, y - 2.6), None, color=color, lw=1.3)
        ax.text(x + w + 0.8, y - 1.3, text, ha="left", va="center", fontsize=7.0, color=INK, linespacing=1.15,
                bbox=dict(fc="white", ec="none", pad=0.5, alpha=0.9))

    y = 86.0
    msg(0, 1, y, "POST /api/session/{id}/frame\nJPEG file + Bearer token", color=BLUE); y -= 6.4
    selfcall(1, y, "current_user(): verify HMAC token", color=GREEN); y -= 5.6
    msg(1, 2, y, "frame(data)", color=GREEN); y -= 4.8
    selfcall(2, y, "cv2.imdecode, resize 640x480", color=GREEN); y -= 5.6
    msg(2, 3, y, "process(image, now)"); y -= 4.4
    selfcall(3, y, "7 quality gates;\nFaceLandmarker; EAR, roll", color=PURPLE); y -= 6.2
    msg(3, 2, y, "Observation(t, ear, roll, quality)", dashed=True, color=PURPLE); y -= 5.2
    selfcall(2, y, "consume(o): calibration step\nor monitoring branch", color=GREEN); y -= 6.2
    msg(2, 4, y, "update(o)  [if monitoring]", color=NAVY); y -= 4.6
    selfcall(4, y, "median, timers, rules,\npersistence, cooldown", color=NAVY); y -= 6.4
    msg(4, 2, y, "Decision(state, reason, ..., alert)", dashed=True, color=NAVY); y -= 5.0
    msg(2, 5, y, "add(source, decision)\n[state changed, 5 s elapsed, or alert]", color=GOLD); y -= 6.0
    msg(2, 1, y, "annotated JPEG bytes  (+ snapshot())", dashed=True, color=GREEN); y -= 5.0
    msg(1, 0, y, "200 JSON: state, reason, metrics, preview (data URI)", dashed=True, color=BLUE); y -= 5.4
    ax.text(50, 1.2, "Errors: no token -> 401; no active camera source -> 409; undecodable image -> 422 (SessionError), and nothing is logged.\n"
                     "Frames are decoded in RAM and never written to disk.",
            ha="center", fontsize=7.6, color=SLATE, style="italic", linespacing=1.4)
    save(fig, "07_sequence_diagram.png")


def use_case():
    fig, ax = canvas(11, 7.6, "Use-case diagram", ty=78)
    ax.add_patch(Rectangle((22, 4.5), 56, 70.5, fc="#FBFCFE", ec="#D5DCE6", lw=1.4))
    ax.text(50, 72.4, "Smart Rider Impairment Warning System", ha="center", fontsize=10, fontweight="bold", color=NAVY)
    left = [("Sign in with demo account", 66), ("Run a simulation scenario", 60), ("Start webcam", 54), ("Calibrate EAR threshold\n(camera only)", 48),
            ("Start / stop monitoring", 42), ("See verdict, reason and\nmeasurements", 36), ("Edit thresholds", 30), ("Optional alert sound\n(extends monitoring)", 24)]
    right = [("Run offline evaluation\n(CSV + held-out subjects)", 58), ("View research report\nand confusion matrix", 50)]
    for t, yy in left:
        ax.add_patch(Ellipse((38, yy), 27, 5.0, fc="#E8F0FC", ec=BLUE, lw=1.3))
        ax.text(38, yy, t, ha="center", va="center", fontsize=7.4, color=INK, linespacing=1.1)
    for t, yy in right:
        ax.add_patch(Ellipse((65, yy), 27, 5.6, fc="#EFEBFC", ec=PURPLE, lw=1.3))
        ax.text(65, yy, t, ha="center", va="center", fontsize=7.4, color=INK, linespacing=1.1)
    # shared use cases grouped in one package so both actors connect to the group, not to every case
    ax.add_patch(FancyBboxPatch((26, 7), 48, 13.5, boxstyle="round,pad=0,rounding_size=1.2", fc="#F6FBF8", ec=GREEN, lw=1.5, ls=(0, (5, 3))))
    ax.text(50, 18.2, "Shared by both roles (after sign-in)", ha="center", fontsize=8, fontweight="bold", color=GREEN)
    for t, xx in (("View event history\nand EAR chart", 36), ("Export history\nas CSV", 50), ("Read How it works\n(formulas, limits)", 64)):
        ax.add_patch(Ellipse((xx, 12), 13.4, 6.4, fc="#E6F6EF", ec=GREEN, lw=1.3))
        ax.text(xx, 12, t, ha="center", va="center", fontsize=6.6, color=INK, linespacing=1.1)

    def actor(x, y, label, color):
        ax.add_patch(Circle((x, y + 8), 2.2, fc="white", ec=color, lw=1.8))
        ax.plot([x, x], [y + 5.8, y + 1.2], color=color, lw=1.8)
        ax.plot([x - 3, x + 3], [y + 4.2, y + 4.2], color=color, lw=1.8)
        ax.plot([x, x - 2.5], [y + 1.2, y - 2.6], color=color, lw=1.8)
        ax.plot([x, x + 2.5], [y + 1.2, y - 2.6], color=color, lw=1.8)
        ax.text(x, y - 5.4, label, ha="center", fontsize=8.4, fontweight="bold", color=INK, linespacing=1.15)
    actor(9, 40, "Rider /\nDemonstrator", ORANGE)
    actor(91, 40, "Reviewer /\nResearcher", PURPLE)
    for t, yy in left:
        ax.plot([12.5, 24.5], [43, yy], color=LINE, lw=0.9)
    ax.plot([12.5, 26], [43, 15], color=GREEN, lw=1.1)
    for t, yy in right:
        ax.plot([87.5, 78.5], [43, yy], color=LINE, lw=0.9)
    ax.plot([87.5, 74], [43, 15], color=GREEN, lw=1.1)
    ax.text(50, 1.2, "All cases except 'Sign in' need a signed-in session.  Calibration needs a live camera; the optional sound extends monitoring when a warning fires.\n"
                     "A warning is advice to stop somewhere safe; the system never controls ignition, brakes or vehicle power.",
            ha="center", fontsize=7.0, color=SLATE, style="italic", linespacing=1.4)
    save(fig, "08_use_case_diagram.png")


def entity_box(ax, x, y, w, title, rows, color, dashed=False, fs=7.4, sub=None):
    lh = 2.15
    h = 5.2 + lh * len(rows) + 0.8
    ls = (0, (4, 3)) if dashed else "-"
    ax.add_patch(Rectangle((x, y - h), w, h, fc="white", ec=color, lw=1.7, ls=ls))
    ax.add_patch(Rectangle((x, y - 5.2), w, 5.2, fc=color, ec=color, alpha=0.95))
    ax.text(x + w / 2, y - 2.6 if not sub else y - 1.8, title, ha="center", va="center", color="white", fontsize=8.6, fontweight="bold")
    if sub:
        ax.text(x + w / 2, y - 4.1, sub, ha="center", va="center", color="white", fontsize=6.6)
    cy = y - 5.2 - 1.4
    for r_ in rows:
        ax.text(x + 0.9, cy, r_, fontsize=fs, va="center", color=INK, family="monospace")
        cy -= lh
    return (x, y - h, w, h)


def er():
    fig, ax = canvas(11, 8.6, "Entity-relationship diagram (persisted data and in-memory session)", ty=88)
    events = entity_box(ax, 1, 86, 25, "events", [
        "id           INTEGER PK", "timestamp    TEXT (UTC ISO)", "source       TEXT", "state        TEXT", "quality      TEXT",
        "reason       TEXT", "ear          REAL", "closure      REAL", "blink_rate   REAL", "closed_fract. REAL", "roll         REAL", "alert        INTEGER"],
        GOLD, sub="SQLite table  data/events.sqlite3")
    settings = entity_box(ax, 1, 50, 25, "settings", [
        "ear_threshold       0.08-0.40", "closure_seconds     0.5-5", "persistence_seconds 0.5-5", "closed_fraction     0.3-0.9",
        "tilt_degrees        10-45", "cooldown_seconds    5-120", "calibrated         bool"], GOLD, sub="JSON document  data/settings.json")
    sess = entity_box(ax, 37, 86, 30, "RiderSession", [
        "id          hex(12)", "source      none|camera|simulation", "scenario    one of 4 scripted", "monitoring  bool", "calibration Calibration | None",
        "state, reason, alert text", "settings    Settings (shared)", "vision, engine  objects"], GREEN, dashed=True,
        sub="in memory only, one per browser tab")
    meas = entity_box(ax, 72, 86, 27, "measurement CSV", [
        "subject_id", "session_id", "timestamp_s", "ear", "roll_deg", "quality", "label: normal|", "       possible_impairment", "consent: yes"],
        PURPLE, sub="user-supplied (research.py FIELDS)")
    win = entity_box(ax, 72, 56, 27, "window_features.csv", [
        "subject_id, session_id", "window_index (5 s)", "ear_mean, ear_std, ear_min", "closed_fraction", "absolute_roll_mean,", "roll_std",
        "label, split (train|test)"], PURPLE, sub="derived by extract_windows()")
    rep = entity_box(ax, 72, 27, 27, "research_results/", [
        "report.json (metrics,", "  subjects, exclusions,", "  dataset sha256)", "centroid_model.npz", "confusion_matrix.png"],
        PURPLE, sub="written by evaluate()")
    # relationships
    arrow(ax, (37, 78), (26, 78), None, color=GREEN, lw=1.4)
    tag(ax, 31.5, 80.6, "writes", 7.0, GREEN)
    tag(ax, 31.5, 75.4, "1 session : N events", 6.6, GREEN)
    arrow(ax, (42, 62.5), (26, 46), None, color=GREEN, lw=1.4)
    tag(ax, 33.5, 58.2, "loads / saves", 7.0, GREEN)
    tag(ax, 33.5, 54.8, "1 : 1", 6.6, GREEN)
    arrow(ax, (85.5, 60.6), (85.5, 56), None, color=PURPLE, lw=1.4)
    tag(ax, 92.0, 58.3, "1 CSV : N windows", 6.4, PURPLE)
    arrow(ax, (85.5, 36.5), (85.5, 31), None, color=PURPLE, lw=1.4) if False else None
    arrow(ax, (85.5, 34.9), (85.5, 27.0), None, color=PURPLE, lw=1.4)
    tag(ax, 92.0, 31.0, "1 run : 1 report", 6.4, PURPLE)
    ax.text(37, 30, "Legend", fontsize=8.4, fontweight="bold", color=NAVY)
    ax.add_patch(Rectangle((37, 24.4), 4, 2.6, fc="white", ec=GOLD, lw=1.7))
    ax.text(42.5, 25.7, "persisted by the live app (SQLite / JSON)", fontsize=7.4, va="center", color=INK)
    ax.add_patch(Rectangle((37, 20), 4, 2.6, fc="white", ec=GREEN, lw=1.7, ls=(0, (4, 3))))
    ax.text(42.5, 21.3, "in memory only, lost when the session closes", fontsize=7.4, va="center", color=INK)
    ax.add_patch(Rectangle((37, 15.6), 4, 2.6, fc="white", ec=PURPLE, lw=1.7))
    ax.text(42.5, 16.9, "files of the offline research tools", fontsize=7.4, va="center", color=INK)
    ax.text(1, 6, "events.source is 'LIVE CAMERA' or 'SIMULATION: <scenario>', so simulated rows can never be mistaken for live ones. No image or video is stored anywhere.\n"
                  "The measurement CSV is the dataset format for research.py; the web app can also generate a synthetic demo CSV (flagged 'Synthetic data').",
            fontsize=7.2, color=SLATE, style="italic", linespacing=1.4)
    save(fig, "09_er_diagram.png")


# ---------------------------------------------------------------- 10 flowchart
def diamond(ax, cx, cy, w, h, text, fc="#FFF8E5", ec=GOLD, fs=8):
    ax.add_patch(Polygon([(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)], closed=True, fc=fc, ec=ec, lw=1.5))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.1)


def flowchart():
    nodes = [
        ("term", "Start: Observation o = (t, EAR, roll, quality)", 4.4),
        ("dec", "quality not Good, or time gap\n(t - last_t not in (0, 0.5] s),\nor value not finite / EAR out of range?", 11),
        ("proc", "median of last 3 EAR -> smoothed EAR\nclosed = smoothed EAR < ear_threshold (0.21)", 6),
        ("proc", "closure timer: starts when closed, stops on reopening;\nan interval of 0.08-0.8 s counts as a blink", 6),
        ("proc", "keep the last 10 s of (t, closed): span and time-weighted\nclosed fraction; blink rate over 60 s", 6),
        ("proc", "rule tests (all evaluated, reasons collected):\nA closure >= 1.5 s   B span >= 8 s and fraction >= 0.55\nC |roll| >= 25 deg and closed", 8.4),
        ("proc", "any reason?  yes: start evidence timer if not running\n(risk_since = t);  no: clear it", 6),
        ("proc", "state = UNKNOWN while span < 2 s (warm-up), else NORMAL", 4.6),
        ("dec", "reasons present, span >= 2 s and\nt - risk_since >= persistence (1.0 s)?", 9),
        ("dec", "state is WARNING and\nt - last_alert >= cooldown (15 s)?", 8.4),
        ("term", "Return Decision(state, reason, measurements, alert)", 4.4),
    ]
    DG = 1.6                                   # extra height of a diamond over its text height
    def top(n, cy): return cy + (n[2] + (DG if n[0] == "dec" else 0)) / 2
    def bot(n, cy): return cy - (n[2] + (DG if n[0] == "dec" else 0)) / 2
    gaps = [7.4 if n[0] == "dec" else 4.2 for n in nodes[:-1]]
    total = sum(n[2] + (DG if n[0] == "dec" else 0) for n in nodes) + sum(gaps)
    ty = int(total + 12)
    fig, ax = canvas(10.2, 10.0, "Flowchart of the core algorithm: RiskEngine.update(o)", ty=ty)
    cx = 33
    y = ty - 8
    cys = []
    for i, n in enumerate(nodes):
        h = n[2] + (DG if n[0] == "dec" else 0)
        cy = y - h / 2
        cys.append(cy)
        if n[0] == "term":
            box(ax, cx - 23, cy - h / 2, 46, h, n[1], fc=NAVY, ec=NAVY, tc="white", fs=7.8, bold=True, rounding=2.2)
        elif n[0] == "proc":
            box(ax, cx - 22, cy - h / 2, 44, h, n[1], fc="#F4F8FE", ec=BLUE, fs=7.6)
        else:
            diamond(ax, cx, cy, 46, h, n[1], fs=7.4)
        y -= h + (gaps[i] if i < len(gaps) else 0)
    for i in range(len(nodes) - 1):
        arrow(ax, (cx, bot(nodes[i], cys[i])), (cx, top(nodes[i + 1], cys[i + 1])), None, lw=1.3)
    # exit 1: invalid frame
    c1 = cys[1]
    box(ax, 62, c1 - 7.5, 37, 15, "reset(): clear samples, blinks and\ntimers (the alert cool-down clock\nis kept)\nreturn UNKNOWN  'Unable to assess'\nreason = quality, or 'Unstable timing\nor invalid measurement'", fc="#FFF1EA", ec=ORANGE, fs=7.2)
    arrow(ax, (cx + 23, c1), (62, c1), None, color=ORANGE, lw=1.3)
    tag(ax, 57.6, c1 + 2.0, "yes", 7.6, ORANGE)
    tag(ax, cx - 3.2, bot(nodes[1], c1) - 2.6, "no", 7.6, GREEN)
    # decision 9: WARNING branch re-joins the main line
    c9 = cys[8]
    box(ax, 62, c9 - 3.4, 37, 6.8, "state = WARNING\nreason = the collected reasons", fc="#FDECEC", ec="#B42318", fs=7.4)
    arrow(ax, (cx + 23, c9), (62, c9), None, color="#B42318", lw=1.3)
    tag(ax, 57.6, c9 + 2.0, "yes", 7.6, "#B42318")
    tag(ax, cx - 3.2, bot(nodes[8], c9) - 2.2, "no", 7.6, SLATE)
    ym = bot(nodes[8], c9) - 5.2
    poly_arrow(ax, [(80.5, c9 - 3.4), (80.5, ym), (cx + 0.2, ym)], None, color="#B42318", lw=1.3)
    # decision 10: alert branch re-joins the main line
    c10 = cys[9]
    box(ax, 62, c10 - 3.8, 37, 7.6, "alert = True; last_alert = t\n(on-screen warning, optional bell,\nevent row marked alert)", fc="#FFF8E5", ec=GOLD, fs=7.2)
    arrow(ax, (cx + 23, c10), (62, c10), None, color=GOLD, lw=1.3)
    tag(ax, 57.6, c10 + 2.0, "yes", 7.6, GOLD)
    tag(ax, cx - 3.2, bot(nodes[9], c10) - 2.2, "no", 7.6, SLATE)
    ym2 = bot(nodes[9], c10) - 5.2
    poly_arrow(ax, [(80.5, c10 - 3.8), (80.5, ym2), (cx + 0.2, ym2)], None, color=GOLD, lw=1.3)
    save(fig, "10_core_algorithm_flowchart.png")


def main():
    for fn in (architecture, workflow, dfd0, dfd1, dfd2, class_diagram, sequence, use_case, er, flowchart):
        fn()


if __name__ == "__main__":
    main()
