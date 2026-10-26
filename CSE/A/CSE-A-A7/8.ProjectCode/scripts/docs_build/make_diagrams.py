"""Draw the ATHENA design diagrams (first half) into docs/diagrams/ (PNG, 150 dpi, matplotlib only).

Every box and arrow mirrors the code: backend/app/main.py + routes/api.py (routes), services/extract.py, features.py, triage.py, pdf.py,
db.py (tables), ml/train.py (model) and frontend/src (screens).
    python scripts/docs_build/make_diagrams.py        (also runs diagrams_dfd.py and diagrams_more.py)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dgm_lib import *  # noqa: E402,F401,F403

OUT = Path(__file__).resolve().parents[2] / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)


def system_architecture():
    fig, ax = canvas(10, 8.4, 100, 84)
    panel(ax, 2, 64, 96, 18, "Presentation tier - React 19 + Vite single-page app (port 5307)", PALE_BLUE, BLUE)
    box(ax, 17, 70, 28, 10.5, "Pages (lazy-loaded)\nLanding - Login - New patient\nResult - Queue - Performance", BLUE, fs=7.6)
    box(ax, 47, 70, 28, 10.5, "lib/api.js + auth.jsx\nfetch wrapper, bearer token\nin local storage, route guard", BLUE, fs=7.6)
    box(ax, 77, 70, 28, 10.5, "Neo Brutal Grid UI kit\nRecharts - Framer Motion - GSAP\ndark mode, drawer navigation", BLUE, fs=7.6)

    panel(ax, 2, 41, 96, 21, "Application tier - FastAPI + Uvicorn (backend/app/main.py, port 8307, router prefix /api)", PALE_TEAL, TEAL)
    box(ax, 14.5, 47.5, 21, 12.5, "Auth\nPOST /auth/login\nGET /auth/me\nbcrypt + JWT (12 h)", TEAL, fs=7.2)
    box(ax, 38, 47.5, 21, 12.5, "Reports\nPOST /reports/extract\nGET /samples\nGET /samples/{file}", TEAL, fs=7.2)
    box(ax, 62, 47.5, 23, 12.5, "Patients\nPOST, GET /patients\nGET /patients/{id}\nPOST .../override\nGET .../summary.pdf", TEAL, fs=7.0)
    box(ax, 85.5, 47.5, 21, 12.5, "Status\nGET /health\nGET /public/stats\nGET /metrics", TEAL, fs=7.2)

    panel(ax, 2, 19, 96, 20, "Service modules (backend/app/services)", PALE_ORANGE, ORANGE)
    box(ax, 15, 26, 22, 12, "extract.py\npypdf, RapidOCR (ONNX),\nclinical lexicon, labs", ORANGE, fs=7.2)
    box(ax, 38.5, 26, 21, 12, "features.py\nfused record:\n8 vitals + 28 flags", ORANGE, fs=7.4)
    box(ax, 62.5, 26, 24, 12, "triage.py\nXGBoost + isotonic\ncalibration + SHAP", ORANGE, fs=7.4)
    box(ax, 85.5, 26, 19, 12, "pdf.py\nReportLab\ntriage summary", ORANGE, fs=7.4)

    panel(ax, 2, 1.5, 96, 15.5, "Data tier - one SQLite file and files on disk", LIGHT, "#B7C3D3")
    store(ax, 14, 8, 21, 9, "data/app.db\nusers, patients,\noverrides", fs=7.0)
    store(ax, 37, 8, 21, 9, "models/\ntriage_model.joblib", fs=7.0)
    store(ax, 59.5, 8, 21, 9, "data/sample_reports/\n12 files + expected.json", fs=7.0)
    store(ax, 84, 8, 22, 9, "experiments/\nmetrics.json, eval/, extra/", fs=7.0)

    arrow(ax, (50, 64), (50, 62), "HTTP + JSON, multipart upload (Vite /api proxy)", lo=(21, 0), fs=7.2, color=NAVY)
    arrow(ax, (50, 41), (50, 39), "function calls", lo=(8, 0), fs=7.2, color=NAVY)
    arrow(ax, (50, 19), (50, 17), "SQLAlchemy ORM, joblib, JSON", lo=(14, 0), fs=7.2, color=NAVY)
    save(fig, OUT / "01_system_architecture.png")


def high_level_workflow():
    fig, ax = canvas(10, 7.4, 100, 74)
    ax.text(50, 71, "From a scanned report and eight vitals to a priority the clinician can accept or change", ha="center", fontsize=9.6, color=NAVY, fontweight="bold")
    ax.text(3, 65, "Intake (nurse)", fontsize=8.4, color=BLUE, fontweight="bold")
    row1 = [("1  Upload report", "PDF, PNG or JPG,\nup to 15 MB", BLUE), ("2  Read pages", "PDF text layer, or\nOCR when a page\nhas no text", BLUE),
            ("3  Parse", "22-term lexicon, negation,\n6 lab values with\nreference ranges, pages", BLUE), ("4  Enter vitals", "age, heart rate, BP,\nSpO2, temperature,\nresp. rate, arrival", BLUE)]
    xs = [14, 38, 62, 86]
    for x, (t, d, c) in zip(xs, row1):
        box(ax, x, 55, 21, 13, f"{t}\n{d}", c, fs=7.3)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 10.8, 55), (b - 10.8, 55), color=NAVY)
    ax.text(3, 41.6, "Assessment (system)", fontsize=8.4, color=TEAL, fontweight="bold")
    row2 = [("5  Fuse", "28 report flags + 8\nvitals = 36 inputs", TEAL), ("6  Calibrated XGBoost", "priority 1-5, risk\nlevel, confidence", TEAL),
            ("7  SHAP reasons", "strongest drivers\nfirst, with values", TEAL), ("8  Clinician decides", "accept, or change\nwith a reason", ORANGE)]
    for x, (t, d, c) in zip(xs, row2):
        box(ax, x, 33, 21, 13, f"{t}\n{d}", c, fs=7.3)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(ax, (a + 10.8, 33), (b - 10.8, 33), color=NAVY)
    # connector from step 4 down to step 5
    ax.plot([86, 86], [48.4, 45.4], color=NAVY, lw=1.5, zorder=4)
    ax.plot([86, 22], [45.4, 45.4], color=NAVY, lw=1.5, zorder=4)
    arrow(ax, (22, 45.4), (22, 39.6), color=NAVY)
    ax.text(3, 21, "Outputs", fontsize=8.4, color=ORANGE, fontweight="bold")
    outs = [("Live queue", "ordered by priority,\nthen arrival", NAVY), ("Override log", "who, old and new\npriority, reason", NAVY),
            ("Summary PDF", "priority, vitals,\nfindings, reasons", NAVY), ("Performance page", "offline metrics and\nlive counts", NAVY)]
    for x, (t, d, c) in zip(xs, outs):
        box(ax, x, 11.5, 21, 12, f"{t}\n{d}", c, fs=7.3)
    ax.plot([86, 86], [26.4, 22.8], color=GREY, lw=1.5, zorder=4)
    ax.plot([14, 86], [22.8, 22.8], color=GREY, lw=1.5, zorder=4)
    ax.text(50, 24.2, "decision stored with the patient; every output reads it", ha="center", fontsize=7.2, color=INK)
    for x in xs:
        arrow(ax, (x, 22.8), (x, 17.6), color=GREY)
    save(fig, OUT / "02_high_level_workflow.png")


def flowchart_triage():
    fig, ax = canvas(7.6, 11.0, 100, 144)
    ax.set_ylim(-5, 139)
    cx = 40
    box(ax, cx, 134, 46, 6, "Start: vitals (8) + report flags (28)", NAVY, fs=8.2)
    box(ax, cx, 122, 62, 8, "fuse(): 36 values in model column order\narrival mode coded walk-in 0, transfer 1, ambulance 2", BLUE, fs=7.6)
    box(ax, cx, 108, 62, 8, "calibrated.predict_proba(row)\n5 probabilities, one per priority", BLUE, fs=7.6)
    box(ax, cx, 94, 62, 8, "cls = argmax;  priority = cls + 1\nconfidence = probability of cls", BLUE, fs=7.6)
    box(ax, cx, 80, 62, 8, "risk_level: P1-P2 High, P3 Moderate, P4-P5 Low", BLUE, fs=7.6)
    box(ax, cx, 66, 62, 8, "TreeExplainer on the same trees:\ncontribution of each input toward class cls", TEAL, fs=7.6)
    box(ax, cx, 53, 62, 6.5, "sort inputs by absolute contribution, largest first", TEAL, fs=7.6)
    diamond(ax, cx, 38, 58, 13, "next input is a report flag,\nabsent, and |impact| < 0.15 ?", fs=7.4)
    box(ax, cx, 22.5, 50, 7, "keep: feature, label, value, impact,\ndirection (raises / lowers urgency)", TEAL, fs=7.4)
    diamond(ax, cx, 9.5, 44, 10, "8 items kept\nor list ended?", fs=7.4)
    box(ax, cx, -2, 76, 5.5, "Return priority, name, risk, confidence, probabilities, shap, fused, seconds", NAVY, fs=6.8)
    for y1, y2 in [(131, 126), (118, 112), (104, 98), (90, 84), (76, 70), (62, 56.3)]:
        arrow(ax, (cx, y1), (cx, y2), color=NAVY)
    arrow(ax, (cx, 49.7), (cx, 44.6), color=NAVY)
    arrow(ax, (cx, 31.4), (cx, 26.2), "no: keep", lo=(6, 0), fs=7.2, color=NAVY)
    arrow(ax, (cx, 19), (cx, 14.6), color=NAVY)
    arrow(ax, (cx, 4.4), (cx, 0.9), "yes", lo=(3, 0), fs=7.2, color=NAVY)
    # yes branch: hide the item, take the next input
    ax.plot([cx + 29, 90, 90, cx], [38, 38, 47.5, 47.5], color=ORANGE, lw=1.5, zorder=4)
    ax.text(88.5, 42.5, "yes: hide\nthe item,\nnext input", fontsize=7.0, color=INK, ha="right", va="center")
    # no branch of the last diamond: next input
    ax.plot([cx - 22, 6, 6, cx], [9.5, 9.5, 47.5, 47.5], color=GREY, lw=1.5, zorder=4)
    ax.text(7.5, 28, "no: next\ninput", fontsize=7.0, color=INK, va="center")
    save(fig, OUT / "10_flowchart_triage.png")


def flowchart_reading():
    fig, ax = canvas(9.4, 11.8, 100, 125)
    ax.set_ylim(-6, 119)
    box(ax, 50, 115, 52, 6, "Start: uploaded bytes + file name (limit 15 MB)", NAVY, fs=7.8)
    diamond(ax, 50, 104, 46, 10, "PDF?  (.pdf name or\n%PDF header)", fs=7.4)
    box(ax, 22, 90, 36, 7, "pypdf: read each page\ntext layer", BLUE, fs=7.3)
    diamond(ax, 22, 77, 40, 11, "text under 20 chars\nand page has an image?", fs=7.0)
    box(ax, 22, 63, 36, 6.5, "OCR the first embedded image", TEAL, fs=7.3)
    box(ax, 78, 90, 36, 7, "open with Pillow\n(failure: error 422)", BLUE, fs=7.3)
    box(ax, 78, 77, 36, 11, "upscale x1.6 when the long side\nis under 2000 px; RapidOCR;\nsort boxes by line, then x", TEAL, fs=7.0)
    box(ax, 50, 49, 62, 7, "pages = [(page number, text, method)]; no text at all: error 422", BLUE, fs=7.4)
    box(ax, 50, 39, 62, 7, "unwrap lines (45+ chars, no closing . ; :), split into sentences", BLUE, fs=7.4)
    box(ax, 50, 29, 62, 7, "per sentence: lab regex + clinical lexicon (22 flags)", TEAL, fs=7.4)
    diamond(ax, 20, 15, 34, 12, "negation word within\n45 chars before match?", fs=6.6)
    diamond(ax, 80, 15, 34, 12, "lab value beyond\nreference range?", fs=6.6)
    box(ax, 20, 1, 30, 6, "drop the flag", GREY, fs=7.4)
    box(ax, 80, 1, 30, 6, "set the lab flag", ORANGE, fs=7.4)
    box(ax, 50, 20, 18, 7, "keep the item with\npage and sentence", TEAL, fs=6.6)
    box(ax, 50, 8, 18, 6, "normal: nothing set", GREY, fs=6.6)
    arrow(ax, (50, 112), (50, 109), color=NAVY)
    ax.plot([27, 22], [104, 104], color=NAVY, lw=1.5, zorder=4); arrow(ax, (22, 104), (22, 93.6), "yes", lo=(3, 0), fs=7.2, color=NAVY)
    ax.plot([73, 78], [104, 104], color=NAVY, lw=1.5, zorder=4); arrow(ax, (78, 104), (78, 93.6), "no", lo=(3, 0), fs=7.2, color=NAVY)
    arrow(ax, (22, 86.5), (22, 82.5), color=NAVY)
    arrow(ax, (22, 71.5), (22, 66.3), "yes", lo=(3, 0), fs=7.2, color=NAVY)
    arrow(ax, (78, 86.5), (78, 82.5), color=NAVY)
    ax.plot([2, 2, 14], [77, 55, 55], color=GREY, lw=1.5, zorder=4)
    ax.text(3.8, 72, "no: keep text", fontsize=7, color=INK, va="center", rotation=90)
    ax.plot([22, 22, 34], [59.8, 55, 55], color=NAVY, lw=1.5, zorder=4)
    ax.plot([14, 34], [55, 55], color=GREY, lw=1.5, zorder=3)
    arrow(ax, (34, 55), (34, 52.5), color=NAVY)
    ax.plot([78, 78, 66], [71.5, 55, 55], color=NAVY, lw=1.5, zorder=4)
    arrow(ax, (66, 55), (66, 52.5), color=NAVY)
    arrow(ax, (50, 45.5), (50, 42.5), color=NAVY)
    arrow(ax, (50, 35.5), (50, 32.5), color=NAVY)
    arrow(ax, (20, 25.5), (20, 21.2), "lexicon hit", lo=(8, 0), fs=7, color=NAVY)
    arrow(ax, (80, 25.5), (80, 21.2), "lab value", lo=(-7, 0), fs=7, color=NAVY)
    arrow(ax, (20, 9), (20, 4.2), "yes", lo=(3, 0), fs=7.2, color=NAVY)
    arrow(ax, (80, 9), (80, 4.2), "yes", lo=(3, 0), fs=7.2, color=NAVY)
    arrow(ax, (37, 15), (41, 19), "no", lo=(-0.5, 2.2), fs=7.2, color=NAVY)
    arrow(ax, (63, 15), (59, 9.5), "no", lo=(1.5, -2.2), fs=7.2, color=NAVY)
    ax.text(50, -5, "Output: symptoms, findings, history, labs, flags (28), pages, text, seconds", ha="center", fontsize=7.4, color=NAVY, fontweight="bold")
    save(fig, OUT / "11_flowchart_report_reading.png")


def model_architecture():
    fig, ax = canvas(10.4, 6.2, 100, 59.6)
    ax.text(50, 57, "Calibrated gradient-boosted triage model with per-patient SHAP (ml/train.py, services/triage.py)", ha="center", fontsize=9.4, color=NAVY, fontweight="bold")
    box(ax, 9, 42, 15, 7.5, "8 vitals", BLUE, fs=8)
    box(ax, 9, 31, 15, 7.5, "28 report flags", BLUE, fs=8)
    box(ax, 29, 36.5, 14, 13, "Fused record\n36 inputs\n(column order\nfixed)", NAVY, fs=7.6)
    box(ax, 50.5, 36.5, 22, 22, "XGBoost\nmulti:softprob\n220 trees, depth 4\nlearning rate 0.1\nsubsample 0.9\ncolsample 0.9\nfit on 3,840 rows\n5 raw probabilities", TEAL, fs=7.3)
    box(ax, 75, 36.5, 17, 17, "Isotonic\ncalibration\nfit on 960 rows\n(frozen base\nmodel)", ORANGE, fs=7.4)
    box(ax, 92.5, 36.5, 12, 11, "5 calibrated\nprobabilities", NAVY, fs=6.8)
    arrow(ax, (16.5, 42), (22, 38.5), color=NAVY)
    arrow(ax, (16.5, 31), (22, 34.5), color=NAVY)
    arrow(ax, (36, 36.5), (39.5, 36.5), color=NAVY)
    arrow(ax, (62, 36.5), (66.5, 36.5), color=NAVY)
    arrow(ax, (83.5, 36.5), (86.5, 36.5), color=NAVY)
    box(ax, 64, 13, 24, 9, "argmax -> priority 1 to 5\nconfidence = its probability", BLUE, fs=7.4)
    box(ax, 90, 13, 18, 9, "Risk level\nP1-2 High, P3 Moderate,\nP4-5 Low", BLUE, fs=6.8)
    ax.plot([92.5, 92.5, 64], [31, 24.5, 24.5], color=NAVY, lw=1.5, zorder=4)
    arrow(ax, (64, 24.5), (64, 17.7), color=NAVY)
    arrow(ax, (76, 13), (81, 13), color=NAVY)
    box(ax, 27, 13, 40, 12, "SHAP TreeExplainer on the same trees\ncontribution of every input toward the chosen\npriority, sorted by size; top 8 shown", TEAL, fs=7.2)
    arrow(ax, (42, 25.5), (42, 19.2), "same trees", lo=(5, 0), fs=6.8, color=TEAL, ls="--")
    ax.text(5, 4, "Training: 6,000 synthetic rows -> 3,840 fit / 960 calibration / 1,200 held-out test (seed 7307). Evaluation on the 1,200 test rows.", fontsize=7.4, color=INK)
    save(fig, OUT / "12_model_architecture.png")


def sequence_diagram():
    fig, ax = canvas(10, 8.6, 100, 86)
    names = ["Browser\n(React)", "FastAPI\nrouter", "extract\nservice", "triage\nservice", "SQLite\n(app.db)"]
    xs = [10, 30, 50, 70, 90]
    for x, n in zip(xs, names):
        box(ax, x, 81, 15, 7, n, NAVY, fs=7.8)
        ax.plot([x, x], [77.2, 2], color="#9AA7B8", lw=1.1, ls="--", zorder=1)

    def msg(y, a, b, text, ret=False, dy=1.0):
        arrow(ax, (xs[a], y), (xs[b], y), color=ORANGE if ret else NAVY, ls="--" if ret else "-", lw=1.4)
        ax.text((xs[a] + xs[b]) / 2, y + dy + 0.7, text, ha="center", va="bottom", fontsize=6.9, color=INK, zorder=6,
                bbox=dict(fc="white", ec="none", pad=0.5, alpha=0.9))

    def selfmsg(y, i, text):
        ax.plot([xs[i], xs[i] + 6, xs[i] + 6], [y, y, y - 2.6], color=NAVY, lw=1.3, zorder=4)
        arrow(ax, (xs[i] + 6, y - 2.6), (xs[i], y - 2.6), color=NAVY, lw=1.3)
        ax.text(xs[i] + 7, y - 1.3, text, ha="left", va="center", fontsize=6.7, color=INK)

    ax.text(2, 75.2, "1  Sign in", fontsize=8, color=TEAL, fontweight="bold")
    msg(71.5, 0, 1, "POST /api/auth/login {email, password}")
    selfmsg(66.2, 1, "bcrypt check, sign JWT (12 h)")
    msg(61.5, 1, 0, "access_token + user", ret=True)
    ax.text(2, 59.5, "2  Read the report", fontsize=8, color=TEAL, fontweight="bold")
    msg(54.5, 0, 1, "POST /api/reports/extract  (file)")
    msg(49.5, 1, 2, "extract_report(bytes, name)")
    selfmsg(46.5, 2, "pages -> lexicon, negation, labs")
    msg(41.3, 2, 1, "flags, items with pages, labs", ret=True)
    msg(37.3, 1, 0, "structured report JSON", ret=True)
    ax.text(2, 35.3, "3  Assess and store", fontsize=8, color=TEAL, fontweight="bold")
    msg(30.2, 0, 1, "POST /api/patients {vitals, report}")
    msg(26.2, 1, 3, "predict(vitals, flags)")
    msg(22.2, 3, 1, "priority, risk, confidence, shap", ret=True)
    msg(18.2, 1, 4, "INSERT patient")
    msg(14.4, 1, 0, "patient JSON (priority 1-5, reasons)", ret=True)
    ax.text(2, 12.6, "4  Clinician decision", fontsize=8, color=TEAL, fontweight="bold")
    msg(7.8, 0, 1, "POST /api/patients/{id}/override {priority, reason}")
    msg(4.0, 1, 4, "INSERT override, UPDATE priority + risk (change needs a reason)")
    msg(0.8, 1, 0, "updated patient; queue reorders", ret=True)
    save(fig, OUT / "07_sequence_flow.png")


def main():
    system_architecture()
    high_level_workflow()
    flowchart_triage()
    flowchart_reading()
    model_architecture()
    sequence_diagram()
    import diagrams_dfd
    import diagrams_more
    diagrams_dfd.main()
    diagrams_more.main()


if __name__ == "__main__":
    main()
