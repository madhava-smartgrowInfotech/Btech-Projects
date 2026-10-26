"""FlowSense result figures f01-f13 (matplotlib, 150 dpi) -> docs/figures/.   Run from 8.ProjectCode:

    python -m scripts.docs.make_figures [f01 f05 ...]

Every plotted number is read from experiments/**/metrics.json through scripts/docs/facts.py.  f06, f11 and f13 re-run the shipped code
(forecaster fit, seed-40 simulation, YOLOv8n on the real images in data/external).  Selection rule for f13 is stated in its docstring.
"""
from __future__ import annotations

import sys
from pathlib import Path

try:  # on Windows torch must load before scikit-learn / OpenCV
    import torch  # noqa: F401
except Exception:
    pass

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from . import facts as F

OUT = Path(F.FIGS)
OUT.mkdir(parents=True, exist_ok=True)
CODE = Path(F.CODE)
sys.path.insert(0, str(CODE))

COL = {"fixed": "#5B6B7F", "adaptive": "#2B6CB0", "emergency": "#D9772F", "advanced": "#14907F"}
INK, GREY, NAVY, PURPLE, RED = "#14213D", "#5B6B7F", "#1F3A5F", "#6B5BD2", "#C0392B"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#8895A7", "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
                     "axes.titleweight": "bold", "axes.titlesize": 10, "figure.facecolor": "white"})


def save(fig, name):
    fig.savefig(OUT / name, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", name)


def bar_labels(ax, bars, fmt="{:.1f}", dy=0.0, fs=7.5, color=INK):
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + dy, fmt.format(h), ha="center", va="bottom", fontsize=fs, color=color)


# ------------------------------------------------------------------ f01
def f01():
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    w = 0.19
    for gi, grid in enumerate(("2x2", "3x3")):
        for ci, c in enumerate(F.CTRL_KEYS):
            m, s = F.gm(grid, c, "Avg delay / vehicle (s)")
            x = gi + (ci - 1.5) * w
            b = ax.bar(x, m, w * 0.92, yerr=s, capsize=3, color=COL[c], label=F.CTRL_SHORT[c] if gi == 0 else None, error_kw=dict(lw=1, ecolor=INK))
            ax.text(x, m + s + 1.2, f"{m:.1f}", ha="center", fontsize=7.5)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["2 x 2 junctions", "3 x 3 junctions"])
    ax.set_ylabel("Average delay per vehicle (s)")
    ax.set_title("Average delay by controller (mean ± std over 5 seeds, demand x1.2, 1800 s)")
    ax.legend(frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.1), fontsize=8)
    ax.set_ylim(0, max(F.gm(g, "fixed", "Avg delay / vehicle (s)")[0] + F.gm(g, "fixed", "Avg delay / vehicle (s)")[1] for g in ("2x2", "3x3")) * 1.18)
    save(fig, "f01_delay_by_controller.png")


# ------------------------------------------------------------------ f02
def f02():
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    w = 0.19
    groups = ["2x2, 1 ambulance\nper ~150 s (5 seeds)", "3x3, 1 ambulance\nper ~150 s (5 seeds)", "2x2, emergency-heavy\n1 per ~60 s, 3600 s"]
    for gi in range(3):
        for ci, c in enumerate(F.CTRL_KEYS):
            if gi < 2:
                m, s = F.gm(("2x2", "3x3")[gi], c, "Emergency delay (s)")
            else:
                m, s = F.EM["results"][c]["mean"], 0.0
            x = gi + (ci - 1.5) * w
            ax.bar(x, m, w * 0.92, yerr=s if s else None, capsize=3, color=COL[c], label=F.CTRL_SHORT[c] if gi == 0 else None, error_kw=dict(lw=1, ecolor=INK))
            ax.text(x, m + s + 0.8, f"{m:.1f}", ha="center", fontsize=7.5)
    ax.set_xticks(range(3))
    ax.set_xticklabels(groups, fontsize=8)
    ax.set_ylabel("Mean ambulance delay (s)")
    ax.set_title("Ambulance delay by controller (waiting time at stop lines)")
    ax.legend(frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.17), fontsize=8)
    ax.set_ylim(0, 50)
    save(fig, "f02_emergency_delay.png")


# ------------------------------------------------------------------ f03
def f03():
    fig, ax = plt.subplots(figsize=(6.8, 3.9))
    lv = F.SW["levels"]
    for c in F.CTRL_KEYS:
        m = np.array([r["delay_mean"] for r in F.SW["series"][c]])
        s = np.array([r["delay_std"] for r in F.SW["series"][c]])
        ax.plot(lv, m, "-o", color=COL[c], label=F.CTRL_SHORT[c], lw=1.8, ms=4)
        ax.fill_between(lv, m - s, m + s, color=COL[c], alpha=0.12)
    ax.set_xlabel("Demand multiplier")
    ax.set_ylabel("Average delay per vehicle (s)")
    ax.set_title("Delay versus demand (2x2, 3 seeds, 1200 s; band = ± 1 std)")
    ax.set_xticks(lv)
    ax.legend(frameon=False, fontsize=8)
    a = F.SW["series"]
    ax.annotate("advanced is worse than\nadaptive at x0.6", xy=(lv[0], a["advanced"][0]["delay_mean"]), xytext=(lv[0] + 0.1, a["advanced"][0]["delay_mean"] + 38),
                fontsize=7.5, color=GREY, arrowprops=dict(arrowstyle="->", color=GREY, lw=0.9))
    save(fig, "f03_demand_sweep.png")


# ------------------------------------------------------------------ f04
def f04():
    names = list(F.AB["results"])
    fig, axs = plt.subplots(1, 2, figsize=(8.2, 3.7), gridspec_kw=dict(wspace=0.08), sharey=True)
    cols = ["#14907F"] + ["#8A9BB0"] * (len(names) - 1)
    for ax, key, title in ((axs[0], "Avg delay / vehicle (s)", "Average delay per vehicle (s)"), (axs[1], "Emergency delay (s)", "Ambulance delay (s)")):
        m = [F.AB["results"][n][key]["mean"] for n in names]
        s = [F.AB["results"][n][key]["std"] for n in names]
        y = np.arange(len(names))[::-1]
        ax.barh(y, m, xerr=s, color=cols, height=0.62, capsize=3, error_kw=dict(lw=1, ecolor=INK))
        for yi, mi, si in zip(y, m, s):
            ax.text(mi + si + 0.5, yi, f"{mi:.1f}", va="center", fontsize=8)
        ax.set_title(title)
        ax.set_xlim(0, max(np.array(m) + np.array(s)) * 1.18)
    axs[0].set_yticks(np.arange(len(names))[::-1])
    axs[0].set_yticklabels(names)
    fig.suptitle("Ablation of the advanced controller (2x2, 5 seeds, demand x1.2, 1800 s)", fontsize=10, fontweight="bold", y=1.02)
    save(fig, "f04_ablation.png")


# ------------------------------------------------------------------ f05
def f05():
    P = F.PR
    models = list(P["random_split_5x"])
    fig, axs = plt.subplots(1, 2, figsize=(8.6, 3.8), gridspec_kw=dict(width_ratios=[1.15, 1], wspace=0.28))
    ax = axs[0]
    x = np.arange(len(models))
    w = 0.36
    a = [P["random_split_5x"][m]["mae_mean"] for m in models]
    ae = [P["random_split_5x"][m]["mae_std"] for m in models]
    b = [P["leave_one_simulation_out"][m]["mae_mean"] for m in models]
    be = [P["leave_one_simulation_out"][m]["mae_std"] for m in models]
    b1 = ax.bar(x - w / 2, a, w, yerr=ae, capsize=3, color="#2B6CB0", label="random 75/25 split (mean of 5 splits)", error_kw=dict(lw=1))
    b2 = ax.bar(x + w / 2, b, w, color="#D9772F", label="leave-one-simulation-out (mean of 6 folds)")
    for xi, m in zip(x, models):
        folds = P["leave_one_simulation_out"][m]["mae_per_fold"]
        ax.scatter(np.full(len(folds), xi + w / 2), folds, s=11, color="#14213D", zorder=4, label="one held-out run" if xi == 0 else None)
    bar_labels(ax, b1, "{:.2f}", 0.15, 7)
    for r, v in zip(b2, b):
        ax.text(r.get_x() + r.get_width() / 2 + 0.07, v + 0.15, f"{v:.2f}", ha="left", fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels([m.replace(" (used)", "\n(used)").replace("Gradient Boosting", "Gradient\nBoosting").replace("Random Forest", "Random\nForest").replace("Ridge regression", "Ridge") for m in models], fontsize=8)
    ax.set_ylabel("MAE of the 30 s queue forecast (vehicles)")
    ax.set_title("Validation protocol changes the answer")
    ax.legend(frameon=False, fontsize=7.2, loc="upper left")
    ax.set_ylim(0, max(max(P["leave_one_simulation_out"][m]["mae_per_fold"]) for m in models) * 1.45)
    ax = axs[1]
    g = P["leave_one_simulation_out"]["Gradient Boosting (used)"]["mae_per_fold"]
    p = P["leave_one_simulation_out"]["Persistence"]["mae_per_fold"]
    x = np.arange(1, 7)
    ax.bar(x - 0.19, p, 0.38, color="#5B6B7F", label="Persistence")
    ax.bar(x + 0.19, g, 0.38, color="#6B5BD2", label="Gradient boosting")
    ax.set_xticks(x)
    ax.set_xlabel("Held-out simulation run")
    ax.set_ylabel("MAE (vehicles)")
    ax.set_title("Per held-out run: 5 of 6 won, 1 lost")
    k = int(np.argmax(g))
    ax.annotate("only heavily congested run:\nqueues beyond the\ntraining range", xy=(k + 1 + 0.19, g[k] * 0.82), xytext=(0.6, g[k] * 0.52), fontsize=7.2, color=RED,
                arrowprops=dict(arrowstyle="->", color=RED, lw=0.9))
    ax.legend(frameon=False, fontsize=7.5, loc="upper left")
    ax.set_ylim(0, g[k] * 1.12)
    save(fig, "f05_forecaster_validation.png")


# ------------------------------------------------------------------ f06
def f06():
    from smart_traffic.predictor import QueuePredictor

    p = QueuePredictor().fit()
    yte, ypr = p.test
    imp = F.PR["shipped_fit"]["importance"]
    gb = F.PR["shipped_fit"]["metrics"]["Gradient Boosting (used)"]
    fig, axs = plt.subplots(1, 2, figsize=(8.6, 3.9), gridspec_kw=dict(width_ratios=[1.0, 1.0], wspace=0.62))
    ax = axs[0]
    hb = ax.hexbin(yte, ypr, gridsize=40, bins="log", cmap="viridis", mincnt=1, extent=(0, 40, 0, 40))
    ax.plot([0, 40], [0, 40], color=RED, lw=1.2, ls="--", label="perfect forecast")
    ax.set_xlim(0, 40)
    ax.set_ylim(0, 40)
    ax.set_xlabel("Actual queue at t + 30 s (vehicles)")
    ax.set_ylabel("Forecast (vehicles)")
    ax.set_title("Held-out 25 % of the training runs")
    ax.text(1.5, 36, f"MAE {gb['mae']:.2f}   R2 {gb['r2']:.3f}\n(clipped to 40; n = {len(yte):,})", fontsize=8, va="top", color=INK, bbox=dict(fc="white", ec="none", alpha=0.85))
    ax.legend(frameon=False, fontsize=7.5, loc="lower right")
    fig.colorbar(hb, ax=ax, label="samples (log)", shrink=0.8, pad=0.02)
    ax = axs[1]
    items = sorted(imp.items(), key=lambda kv: kv[1])
    ax.barh([k for k, _ in items], [v for _, v in items], color="#6B5BD2")
    for i, (_, v) in enumerate(items):
        ax.text(v + 0.01, i, f"{v:.3f}", va="center", fontsize=7.5)
    ax.set_xlim(0, max(imp.values()) * 1.18)
    ax.set_title("Gradient-boosting feature importance")
    save(fig, "f06_forecast_scatter_importance.png")


# ------------------------------------------------------------------ f07
def f07():
    R = F.VS["results"]
    labels = {"clean": "clean", "gaussian_noise_sigma10": "noise\nσ = 10", "gaussian_noise_sigma25": "noise\nσ = 25", "brightness_x0.6": "brightness\nx 0.6", "gaussian_blur_7x7": "blur\n7 x 7"}
    keys = list(labels)
    fig, ax = plt.subplots(figsize=(7.4, 3.9))
    x = np.arange(len(keys))
    w = 0.26
    v1 = [R[k]["recall"] for k in keys]
    v2 = [R[k]["class_accuracy_of_matched"] for k in keys]
    v3 = [R[k]["ambulance_recall"] for k in keys]
    for off, v, c, lab in ((-w, v1, "#2B6CB0", "vehicle recall (IoU >= 0.3)"), (0, v2, "#14907F", "class accuracy of matched boxes"), (w, v3, "#D9772F", "ambulance recall (light-bar rule)")):
        b = ax.bar(x + off, v, w * 0.92, color=c, label=lab)
        bar_labels(ax, b, "{:.2f}", 0.01, 7)
    for xi in (1, 2):
        ax.text(xi, 0.08, "no detections\nat all", ha="center", fontsize=7.5, color=RED)
    ax.set_xticks(x)
    ax.set_xticklabels([labels[k] for k in keys])
    ax.set_ylim(0, 1.22)
    ax.set_ylabel("Score")
    ax.set_title(f"Classical detector on {R['clean']['scenes']} synthetic scenes: clean vs perturbed")
    ax.legend(frameon=False, fontsize=7.5, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.17))
    save(fig, "f07_vision_synthetic_robustness.png")


# ------------------------------------------------------------------ f08
def f08():
    A = F.VR["ambulance_classification"]
    fig, axs = plt.subplots(1, 2, figsize=(7.8, 3.6), gridspec_kw=dict(wspace=0.45))
    for ax, key, title in ((axs[0], "lightbar_cluster_any", "Any red+blue light-bar cluster"), (axs[1], "ambulance_flag_yolo_plus_lightbar", "YOLOv8n box carrying a light bar")):
        v = A[key]
        m = np.array([[v["tp"], v["fn"]], [v["fp"], v["tn"]]])
        ax.imshow(m, cmap="Blues", vmin=0, vmax=m.max() * 1.15)
        for i in range(2):
            for j in range(2):
                ax.text(j, i, f"{m[i, j]}", ha="center", va="center", fontsize=14, fontweight="bold", color="white" if m[i, j] > m.max() / 2 else INK)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["flagged", "not flagged"])
        ax.set_yticks([0, 1])
        ax.set_yticklabels(["ambulance\nphoto", "other\nphoto"])
        ax.set_title(title, fontsize=9)
        ax.set_xlabel(f"precision {v['precision']:.2f}  recall {v['recall']:.3f}  false-alarm {v['false_alarm_rate']:.3f}", fontsize=8)
        for sp in ax.spines.values():
            sp.set_visible(False)
    fig.suptitle(f"Light-bar rule on {A['images']} real photos ({A['ambulance_images']} ambulance, {A['no_ambulance_images']} other), no tuning", fontsize=10, fontweight="bold", y=1.03)
    save(fig, "f08_ambulance_real_confusion.png")


# ------------------------------------------------------------------ f09
def f09():
    B = F.BASE_PAPER_RESULTS
    c2, c3 = F.C2["results"], F.C3["results"]

    def red(a, b):
        return 100 * (1 - a / b)

    cats = ["Ambulance waiting\nvs fixed-time", "Ambulance waiting\nvs adaptive / GA-SGD", "Network delay or waiting\nvs fixed-time", "Network delay or waiting\nvs adaptive / GA-SGD"]
    base = [red(B["amb_wait_s"]["proposed"], B["amb_wait_s"]["fixed"]), red(B["amb_wait_s"]["proposed"], B["amb_wait_s"]["ga_sgd"]),
            red(B["total_wait_s"]["proposed"], B["total_wait_s"]["fixed"]), red(B["total_wait_s"]["proposed"], B["total_wait_s"]["ga_sgd"])]

    def fs(res):
        m = {k: res[k]["metrics"] for k in F.CTRL_KEYS}
        return [red(m["advanced"]["Emergency delay (s)"]["mean"], m["fixed"]["Emergency delay (s)"]["mean"]),
                red(m["advanced"]["Emergency delay (s)"]["mean"], m["adaptive"]["Emergency delay (s)"]["mean"]),
                red(m["advanced"]["Avg delay / vehicle (s)"]["mean"], m["fixed"]["Avg delay / vehicle (s)"]["mean"]),
                red(m["advanced"]["Avg delay / vehicle (s)"]["mean"], m["adaptive"]["Avg delay / vehicle (s)"]["mean"])]
    f2, f3 = fs(c2), fs(c3)
    fig, ax = plt.subplots(figsize=(8.0, 4.2))
    x = np.arange(4)
    w = 0.26
    for off, v, c, lab in ((-w, base, "#8A9BB0", "Base paper (SUMO roundabout, one scenario)"), (0, f2, "#14907F", "FlowSense, 2x2 simulator (5 seeds)"), (w, f3, "#2B6CB0", "FlowSense, 3x3 simulator (5 seeds)")):
        b = ax.bar(x + off, v, w * 0.92, color=c, label=lab)
        bar_labels(ax, b, "{:.1f}%", 1.0, 7.5)
    ax.set_xticks(x)
    ax.set_xticklabels(cats, fontsize=8)
    ax.set_ylabel("Reduction (%)")
    ax.set_ylim(0, 105)
    ax.set_title("Relative reductions reported by the base paper and measured for FlowSense")
    ax.legend(frameon=False, fontsize=7.5, loc="upper right")
    ax.text(0.5, -0.30, "DIFFERENT TESTBEDS: SUMO roundabout vs the in-house simulator; waiting time vs simulated delay; GA-SGD vs queue-actuated adaptive.\nIndicative only - absolute values are not comparable.",
            transform=ax.transAxes, ha="center", fontsize=7.5, color=RED, style="italic")
    save(fig, "f09_base_paper_comparison.png")


# ------------------------------------------------------------------ f10
def f10():
    rows = F.API["results"]
    names = [r["endpoint"].split(":")[0] if ":" in r["endpoint"] and not r["endpoint"].startswith("POST") else r["endpoint"].replace("POST /api/", "") for r in rows]
    names = [n.replace("(4 ctrl x 3 seeds x 1800 s, first call)", "(first call)").replace("benchmark/sweep (5 demand levels x 4 ctrl)", "benchmark sweep") for n in names]
    mean = np.array([r["mean_ms"] for r in rows])
    p95 = np.array([r.get("p95_ms", np.nan) for r in rows])
    fig, ax = plt.subplots(figsize=(7.6, 5.0))
    y = np.arange(len(rows))[::-1]
    ax.barh(y, mean, color="#2B6CB0", height=0.62, label="mean")
    ok = ~np.isnan(p95)
    ax.scatter(p95[ok], y[ok], color="#D9772F", zorder=3, s=22, label="p95")
    for yi, m in zip(y, mean):
        ax.text(mean.max() * 3.8, yi, f"{m:.1f} ms" if m < 1000 else f"{m / 1000:.2f} s", va="center", ha="right", fontsize=7.5)
    ax.set_xscale("log")
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=7.8)
    ax.set_xlabel("Response time on 127.0.0.1 (ms, log scale)")
    ax.set_title("FlowSense API response times (CPU-only i5-12500)")
    ax.legend(frameon=False, fontsize=8, loc="upper right", bbox_to_anchor=(0.86, 1.0))
    ax.set_xlim(1, mean.max() * 4)
    save(fig, "f10_api_latency.png")


# ------------------------------------------------------------------ f11
def f11():
    from smart_traffic.predictor import QueuePredictor
    from smart_traffic.sim import Sim

    pred = QueuePredictor().fit()
    fig, ax = plt.subplots(figsize=(7.6, 3.8))
    for c in F.CTRL_KEYS:
        s = Sim(2, 2, c, 1.2, seed=40, predictor=pred if c == "advanced" else None).run(1800)
        q = np.array(s.qtot)
        k = 20
        sm = np.convolve(q, np.ones(k) / k, mode="valid")
        ax.plot(np.arange(len(sm)) + k // 2, sm, color=COL[c], lw=1.6, label=f"{F.CTRL_SHORT[c]}  (mean {q.mean():.0f})")
    ax.set_xlabel("Simulated seconds from 08:00")
    ax.set_ylabel("Vehicles queued in the network")
    ax.set_title("Network queue over time (2x2, seed 40, demand x1.2; 20 s moving average)")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    save(fig, "f11_queue_timeseries.png")


# ------------------------------------------------------------------ f12
def f12():
    M = F.VR["mixed_traffic"]
    cl = list(M["per_class"])
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    x = np.arange(len(cl))
    w = 0.26
    for off, key, c in ((-w, "precision", "#2B6CB0"), (0, "recall", "#14907F"), (w, "f1", "#D9772F")):
        b = ax.bar(x + off, [M["per_class"][k][key] for k in cl], w * 0.92, color=c, label=key)
        bar_labels(ax, b, "{:.2f}", 0.01, 7.5)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{k}\n(n = {M['per_class'][k]['n_gt']})" for k in cl], fontsize=8)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Score (IoU >= 0.5)")
    ax.set_title(f"YOLOv8n (COCO) on {M['images']} real mixed-traffic dashcam frames, conf {M['conf']}")
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="upper right")
    save(fig, "f12_real_vision_per_class.png")


# ------------------------------------------------------------------ f13
def f13():
    """Four real photos (CC BY 4.0 datasets).  Selection rules, fixed in advance and not tuned by eye:
    traffic 'decent' = the frame with the highest recall among frames with >= 8 ground-truth vehicles;
    traffic 'miss'   = the frame with the lowest recall among those frames;
    ambulance 'hit'  = the first ambulance photo (file order) that the shipped rule flags;
    ambulance 'miss' = the first ambulance photo (file order) that the rule does not flag."""
    import cv2

    from smart_traffic import vision as V

    ext = CODE / "data" / "external"
    PM = {"bike": 1, "car": 3, "bus": 3, "truck": 3, "ambulance": 3}

    def iou(a, b):
        ix, iy = max(0, min(a[2], b[2]) - max(a[0], b[0])), max(0, min(a[3], b[3]) - max(a[1], b[1]))
        i = ix * iy
        u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i
        return i / u if u > 0 else 0

    cands = []
    for p in sorted((ext / "mixed_traffic" / "images").rglob("*.jpg")):
        img = cv2.imread(str(p))
        h, w = img.shape[:2]
        lab = ext / "mixed_traffic" / "labels" / p.parent.name / (p.stem + ".txt")
        gts = []
        for ln in lab.read_text().splitlines() if lab.exists() else []:
            c, x, y, bw, bh = ln.split()
            if int(c) == 0:
                continue
            x, y, bw, bh = float(x) * w, float(y) * h, float(bw) * w, float(bh) * h
            gts.append((int(c), (x - bw / 2, y - bh / 2, x + bw / 2, y + bh / 2)))
        if len(gts) < 8:
            continue
        dets, bars = V.detect_yolo(img, 0.3)
        used, tp = set(), 0
        for d in sorted(dets, key=lambda d: -d["conf"]):
            best, bi = 0, -1
            for i, (gc, gb) in enumerate(gts):
                if i in used:
                    continue
                o = iou(d["box"], gb)
                if o > best:
                    best, bi = o, i
            if best >= 0.5:
                used.add(bi)
                tp += 1
        cands.append((tp / len(gts), p, img, gts, dets, bars, tp))
    good = max(cands, key=lambda t: t[0])
    bad = min(cands, key=lambda t: t[0])

    def amb(first_flagged):
        for p in sorted((ext / "ambulance_cls" / "ambulance").iterdir()):
            img = cv2.imread(str(p))
            if img is None:
                continue
            dets, bars = V.detect_yolo(img, 0.3)
            flagged = len(bars) > 0
            if flagged == first_flagged:
                return p, img, dets, bars

    hit, miss = amb(True), amb(False)
    fig, axs = plt.subplots(2, 2, figsize=(8.2, 6.6), gridspec_kw=dict(hspace=0.16, wspace=0.04))

    def panel(ax, img, dets, bars, gts, title):
        out = V.annotate(img, dets, bars)
        for _, g in gts or []:
            cv2.rectangle(out, (int(g[0]), int(g[1])), (int(g[2]), int(g[3])), (255, 255, 255), 1, cv2.LINE_AA)
        ax.imshow(cv2.cvtColor(out, cv2.COLOR_BGR2RGB))
        ax.set_title(title, fontsize=8)
        ax.axis("off")

    panel(axs[0, 0], good[2], good[4], good[5], good[3], f"Traffic frame, best recall: {good[6]} of {len(good[3])} vehicles found\n(white = ground truth; coloured = YOLOv8n)")
    panel(axs[0, 1], bad[2], bad[4], bad[5], bad[3], f"Traffic frame, worst recall: {bad[6]} of {len(bad[3])} vehicles found")
    panel(axs[1, 0], hit[1], hit[2], hit[3], None, f"Ambulance photo flagged ({len(hit[3])} clusters), but they sit on\nlivery stripes, not roof lights (all 4 flagged photos)")
    panel(axs[1, 1], miss[1], miss[2], miss[3], None, "Ambulance photo, light bar not found\n(first unflagged photo in file order)")
    save(fig, "f13_real_examples.png")


ALL = dict(f01=f01, f02=f02, f03=f03, f04=f04, f05=f05, f06=f06, f07=f07, f08=f08, f09=f09, f10=f10, f11=f11, f12=f12, f13=f13)

if __name__ == "__main__":
    for k in (sys.argv[1:] or list(ALL)):
        ALL[k]()
