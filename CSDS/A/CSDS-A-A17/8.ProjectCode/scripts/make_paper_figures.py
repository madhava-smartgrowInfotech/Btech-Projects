"""Figures for the IEEE paper, sized for one 3.4 in column: architecture, main flow, a results chart and two cropped screens.

    python scripts/make_paper_figures.py      -> docs/paper/*.png      (system python with matplotlib + Pillow)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, ROSE_L, Canvas, anchor  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "paper"
SHOTS = ROOT / "docs" / "screenshots"
EXP = ROOT / "experiments"
FS = 5.6


def architecture(path):
    c = Canvas(3.45, 2.7)
    c.box(1, 23.0, 32.5, 3.4, "Browser: React 19 + Vite web app (port 5190)", fc=BLUE_L, fs=FS, bold=True, r=1)
    c.box(1, 18.2, 32.5, 3.4, "FastAPI REST + WebSocket (port 8000): JWT, role guards", fc=INDIGO_L, ec=INDIGO, fs=FS, bold=True, r=1)
    c.arrow((17, 23.0), (17, 21.6), both=True, lw=0.8)
    svc = ["CV features\n(11) + RF\ngrader\n+ SHAP", "GBR price\n+ 2 bands\n+ SHAP", "Delivery\nscore\n(5 terms)", "Order\nstate\nmachine", "Sensor\nsimulator\n(WebSocket)"]
    bw = 6.0
    for i, t in enumerate(svc):
        x = 1 + i * (bw + 0.625)
        c.box(x, 9.8, bw, 6.6, t, fc="white", fs=4.7, r=0.8)
        c.arrow((x + bw / 2, 18.2), (x + bw / 2, 16.4), lw=0.7)
    c.box(1, 2.4, 10.0, 4.6, "SQLite, 9 tables\n(users, listings, orders...)", fc=AMBER_L, fs=4.8, r=0.8)
    c.box(12.2, 2.4, 10.0, 4.6, "Uploaded photos\n(app/data/uploads)", fc=AMBER_L, fs=4.8, r=0.8)
    c.box(23.4, 2.4, 10.1, 4.6, "Model files (.joblib)\nRF, GBR x3", fc=GREEN_L, fs=4.8, r=0.8)
    for x in (6.0, 17.2, 28.4):
        c.arrow((x, 9.8), (x, 7.0), both=True, lw=0.7)
    c.text(17.2, 0.8, "No external service: all models and the sensor stream run locally", fs=4.6, italic=True)
    c.save(path)


def flow(path):
    c = Canvas(3.45, 3.2)
    bw, h = 15.0, 3.0
    L, R = 1.5, 18.0
    left = [("1 Upload crop photo\n(JPEG/PNG/WEBP, <= 8 MB)", BLUE_L), ("2 Foreground mask +\n11 CV features", INDIGO_L), ("3 Random Forest grade\nA/B/C/Reject + SHAP", INDIGO_L),
            ("4 GBR price, band,\n31-day forecast", GREEN_L), ("5 Score buyers\n(5 weighted terms)", GREEN_L)]
    right = [("6 Publish listing\n(farmer sets price)", AMBER_L), ("7 Buyer orders;\nfarmer confirms", AMBER_L), ("8 Distributor starts\ntransit", ROSE_L),
             ("9 Live sensor stream\n+ alert banner", ROSE_L), ("10 Delivered;\nadmin KPIs", BLUE_L)]
    ys = [27.0, 21.6, 16.2, 10.8, 5.4]
    lb = [c.box(L, y, bw, h + 0.6, t, fc=f, fs=4.7, r=0.8) for (t, f), y in zip(left, ys)]
    rb = [c.box(R, y, bw, h + 0.6, t, fc=f, fs=4.7, r=0.8) for (t, f), y in zip(right, ys)]
    for a, b in zip(lb[:-1], lb[1:]):
        c.arrow(anchor(a, "b"), anchor(b, "t"), lw=0.7)
    for a, b in zip(rb[:-1], rb[1:]):
        c.arrow(anchor(a, "b"), anchor(b, "t"), lw=0.7)
    c.path([(L + bw, ys[-1] + 1.8), (16.7, ys[-1] + 1.8), (16.7, 28.8), (R, 28.8)], lw=0.7)
    c.text(17.2, 1.8, "steps 1-5 farmer; 6-7 farmer and buyer; 8-10 distributor and admin", fs=4.4, italic=True)
    c.save(path)


def results_chart(path):
    q = json.loads((EXP / "quality" / "metrics.json").read_text(encoding="utf-8"))
    r = json.loads((EXP / "real_images" / "metrics.json").read_text(encoding="utf-8"))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(3.45, 1.95), gridspec_kw={"width_ratios": [1, 1.15]})
    plt.rcParams.update({"font.family": "DejaVu Sans"})
    sh = r["shipped_model_on_real_photos"]["predicted_grade_share_by_label"]
    bottom = [0, 0]
    for g, col in zip(["A", "B", "C", "Reject"], ["#1b6b3a", "#2f6fb0", "#e0a030", "#c8453c"]):
        v = [sh["fresh"][g] * 100, sh["rotten"][g] * 100]
        a1.bar(["fresh", "rotten"], v, bottom=bottom, color=col, label=g, width=0.6)
        bottom = [bottom[0] + v[0], bottom[1] + v[1]]
    a1.set_ylabel("photos predicted (%)", fontsize=5.5)
    a1.set_title("(a) shipped grader, 3,200\nreal fruit photos", fontsize=5.8)
    a1.legend(fontsize=4.6, frameon=False, ncol=2, loc="lower center", bbox_to_anchor=(0.5, -0.42))
    a1.tick_params(labelsize=5.5)
    f = r["features_trained_on_real_labels"]
    labels = ["synthetic\ntest set", "real photos,\nshipped", "real labels,\n5-fold CV", "unseen\nfruits"]
    vals = [q["shipped_rf"]["test_accuracy"], r["shipped_model_on_real_photos"]["mapped_binary_accuracy"], f["five_fold_cv_accuracy_mean"], f["leave_fruits_out_accuracy_mean"]]
    a2.bar(range(4), vals, color=["#9aa5ba", "#c8453c", "#1b6b3a", "#e0a030"], width=0.65)
    for i, v in enumerate(vals):
        a2.text(i, v + 0.02, f"{v:.2f}", ha="center", fontsize=5.2)
    a2.axhline(0.5, color="black", lw=0.6, ls="--")
    a2.set_xticks(range(4), labels, fontsize=4.6)
    a2.set_ylim(0, 1.1)
    a2.tick_params(axis="y", labelsize=5.5)
    a2.set_title("(b) accuracy (dashed: chance)", fontsize=5.8)
    for a in (a1, a2):
        a.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(pad=0.4)
    fig.savefig(path, dpi=300, facecolor="white", bbox_inches="tight")
    plt.close(fig)


def price_iot_chart(path):
    p = json.loads((EXP / "price" / "metrics.json").read_text(encoding="utf-8"))
    i = json.loads((EXP / "iot" / "metrics.json").read_text(encoding="utf-8"))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(3.45, 1.85))
    k = ["crop_mean", "crop_x_grade_mean", "linear_regression", "random_forest_200", "gradient_boosting_shipped"]
    vals = [p["baselines"][x]["mae"] for x in k]
    a1.bar(range(5), vals, color=["#9aa5ba", "#9aa5ba", "#9aa5ba", "#7fb98f", "#1b6b3a"], width=0.65)
    for n, v in enumerate(vals):
        a1.text(n, v + 20, f"{v:.0f}", ha="center", fontsize=5)
    a1.axhline(p["noise_floor"]["generating_function_vs_observed"]["mae"], color="#c8453c", lw=0.7, ls="--")
    a1.set_xticks(range(5), ["crop\nmean", "crop\nx grade", "linear", "RF", "GBR"], fontsize=5)
    a1.set_ylabel("test MAE (INR/quintal)", fontsize=5.5)
    a1.set_title("(a) price baselines;\ndashed: noise floor", fontsize=5.8)
    a1.tick_params(axis="y", labelsize=5.5)
    fs = i["share_flagged_at_step"]
    st = [int(x) for x in fs]
    a2.plot(st, [fs[str(x)] * 100 for x in st], marker="o", ms=2.5, lw=1, color="#c8453c")
    a2.set_xlabel("step (1.4 s)", fontsize=5.5)
    a2.set_ylabel("shipments in alarm (%)", fontsize=5.5)
    a2.set_title("(b) simulator alarm\n(50 shipments)", fontsize=5.8)
    a2.tick_params(labelsize=5.5)
    for a in (a1, a2):
        a.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(pad=0.4)
    fig.savefig(path, dpi=300, facecolor="white", bbox_inches="tight")
    plt.close(fig)


def crop(src, box, dst, width=1100):
    im = Image.open(src).convert("RGB").crop(box)
    ratio = width / im.size[0]
    im.resize((width, int(im.size[1] * ratio)), Image.LANCZOS).save(dst, optimize=True)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    architecture(OUT / "fig1_architecture.png")
    flow(OUT / "fig2_flow.png")
    results_chart(OUT / "fig3_results.png")
    price_iot_chart(OUT / "fig6_price_iot.png")
    crop(SHOTS / "07_grading_result.png", (300, 118, 1395, 528), OUT / "fig4_grade.png")
    crop(SHOTS / "08_price_forecast.png", (300, 556, 1395, 900), OUT / "fig5_price.png")
    print("saved", OUT)
