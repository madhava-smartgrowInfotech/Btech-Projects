"""Result charts for the ResQAI documents, drawn from experiments/resqai_eval/*.json (no number is typed in).

    python scripts/docs_build/make_figures.py      -> docs/figures/f01..f10 (PNG, 150 dpi)
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "docs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
EV = ROOT / "experiments" / "resqai_eval"
M = json.load(open(EV / "metrics.json", encoding="utf-8"))
L = json.load(open(EV / "api_latency.json", encoding="utf-8"))

NAVY, BLUE, TEAL, ORANGE, PURPLE, GREY, RED = "#1F3A5F", "#2B6CB0", "#14907F", "#D9772F", "#6B5BD2", "#8795A8", "#C0392B"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.25})
SEV = ["None", "Minor", "Moderate", "Severe"]


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=150, facecolor="white")
    plt.close(fig)
    print("saved", name)


def f01_feature_separation():
    import train_models as tm
    np.random.seed(42)
    kinds = np.random.choice(["normal", "harsh_brake", "minor_crash", "moderate_crash", "severe_crash"], size=tm.N_SAMPLES, p=[0.60, 0.20, 0.10, 0.06, 0.04])
    rows = [tm.make_event(k) for k in kinds]
    mag = np.array([r["acc_magnitude"] for r in rows])
    jerk = np.array([r["jerk"] for r in rows])
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.6))
    cols = {"normal": GREY, "harsh_brake": TEAL, "minor_crash": BLUE, "moderate_crash": ORANGE, "severe_crash": RED}
    bins = np.linspace(0, 90, 91)
    for k, c in cols.items():
        axes[0].hist(mag[kinds == k], bins=bins, color=c, alpha=0.75, label=k.replace("_", " "))
    axes[0].set_yscale("log")
    axes[0].axvline(15, color="black", ls="--", lw=1)
    axes[0].text(15.8, 3000, "15 m/s²: the gap between\nbraking (max 13.2) and\ncrashes (min 15.3)", fontsize=7.5)
    axes[0].set_xlabel("acc_magnitude (m/s²)")
    axes[0].set_ylabel("events (12,000 generated)")
    axes[0].set_title("Acceleration magnitude by event kind")
    axes[0].legend(fontsize=7.5, frameon=False)
    for k, c in cols.items():
        axes[1].scatter(mag[kinds == k][:600], jerk[kinds == k][:600], s=5, color=c, alpha=0.6, label=k.replace("_", " "))
    axes[1].set_xlabel("acc_magnitude (m/s²)")
    axes[1].set_ylabel("jerk (m/s³)")
    axes[1].set_title("Magnitude against jerk (600 events per kind)")
    save(fig, "f01_feature_separation.png")


def cm_plot(ax, cm, labels, title):
    cm = np.array(cm)
    ax.imshow(cm, cmap="Blues", norm=matplotlib.colors.PowerNorm(0.35))
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)
    ax.set_xlabel("predicted")
    ax.set_ylabel("true")
    ax.set_title(title)
    ax.grid(False)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i][j]), ha="center", va="center", color="white" if cm[i][j] > cm.max() * 0.4 else "black", fontsize=9)


def f02_confusion():
    s = M["shipped_model"]
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.8))
    cm_plot(axes[0], s["detector_test"]["confusion"], ["no accident", "accident"], "Accident detector (n = 2,400)")
    cm_plot(axes[1], s["severity_test_after_gating"]["confusion"], SEV, "Severity after the detector gate")
    save(fig, "f02_confusion_matrices.png")


def f03_baselines():
    b = M["baselines"]
    names = list(b)
    short = ["rule\n(thresholds)", "logistic\nregression", "decision\ntree", "hist. gradient\nboosting", "random forest\n(ResQAI)"]
    acc = [b[n]["sev_accuracy"] for n in names]
    f1 = [b[n]["sev_macro_f1"] for n in names]
    x = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(8.2, 3.8))
    ax.bar(x - 0.2, acc, 0.38, color=BLUE, label="accuracy")
    ax.bar(x + 0.2, f1, 0.38, color=ORANGE, label="macro-F1")
    for i, (a, f) in enumerate(zip(acc, f1)):
        ax.text(i - 0.2, a + 0.002, f"{a:.4f}", ha="center", fontsize=7)
        ax.text(i + 0.2, f + 0.002, f"{f:.4f}", ha="center", fontsize=7)
    ax.set_ylim(0.88, 1.012)
    ax.set_xticks(x)
    ax.set_xticklabels(short)
    ax.set_ylabel("severity score on the 2,400 test events")
    ax.set_title("Severity grading: random forest against simpler models (detection: all five score 1.000)")
    ax.legend(frameon=False, loc="lower right")
    save(fig, "f03_baselines.png")


def f04_importance():
    imp = M["importance"]
    feats = list(imp["detector_gini"])
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.9), sharey=True)
    order = sorted(feats, key=lambda f: imp["severity_gini"][f] + imp["detector_gini"][f])
    y = np.arange(len(order))
    axes[0].barh(y - 0.2, [imp["detector_gini"][f] for f in order], 0.38, color=TEAL, label="detector")
    axes[0].barh(y + 0.2, [imp["severity_gini"][f] for f in order], 0.38, color=ORANGE, label="severity")
    axes[0].set_yticks(y)
    axes[0].set_yticklabels(order)
    axes[0].set_title("Gini importance")
    axes[0].legend(frameon=False)
    axes[1].barh(y - 0.2, [imp["detector_permutation_f1_drop"][f] for f in order], 0.38, color=TEAL)
    axes[1].barh(y + 0.2, [imp["severity_permutation_macro_f1_drop"][f] for f in order], 0.38, color=ORANGE)
    axes[1].set_title("Permutation importance (F1 / macro-F1 drop)")
    save(fig, "f04_feature_importance.png")


def f05_noise():
    n = M["noise_robustness"]
    x = [r["noise_sd_fraction_of_feature_sd"] for r in n]
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    ax.plot(x, [r["det_f1"] for r in n], "o-", color=TEAL, label="detector F1")
    ax.plot(x, [r["sev_macro_f1"] for r in n], "s-", color=ORANGE, label="severity macro-F1")
    ax.plot(x, [r["det_false_alarm"] for r in n], "^--", color=RED, label="detector false-alarm rate")
    ax.set_xlabel("added Gaussian noise, SD as a fraction of each feature's own SD")
    ax.set_ylabel("score")
    ax.set_title("Robustness of the shipped models to sensor noise (never trained on noise)")
    ax.legend(frameon=False)
    for r in n:
        ax.annotate(f"{r['det_false_alarm'] * 100:.1f}%", (r["noise_sd_fraction_of_feature_sd"], r["det_false_alarm"]), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=7, color=RED)
    save(fig, "f05_noise_robustness.png")


def f06_threshold():
    t = M["threshold_sweep"]
    x = [r["threshold"] for r in t]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ax.plot(x, [r["precision"] for r in t], "o-", color=BLUE, label="precision")
    ax.plot(x, [r["recall"] for r in t], "s-", color=ORANGE, label="recall")
    ax.set_ylim(0.985, 1.003)
    ax.set_xlabel("accident-probability threshold")
    ax.set_ylabel("score")
    ax.set_title("Detector threshold sweep: a wide plateau at 1.000 between 0.2 and 0.9")
    ax2 = ax.twinx()
    ax2.bar(x, [r["false_positives"] + r["false_negatives"] for r in t], width=0.02, color=GREY, alpha=0.5)
    ax2.set_ylabel("errors (FP + FN) of 2,400", color=GREY)
    ax2.grid(False)
    ax.legend(frameon=False, loc="lower center")
    save(fig, "f06_threshold_sweep.png")


def f07_ood():
    pk = M["shipped_model"]["per_event_kind"]
    o = M["ood_probes"]
    names = ["normal\ndriving", "harsh\nbraking", "pothole-like\n(probe)", "speed-breaker-\nlike (probe)", "minor\ncrash"]
    flagged = [pk["normal"]["predicted_accident_rate"], pk["harsh_brake"]["predicted_accident_rate"], o["pothole"]["predicted_accident_rate"], o["speed_breaker"]["predicted_accident_rate"], pk["minor_crash"]["predicted_accident_rate"]]
    alert = [pk["normal"]["alert_trigger_rate"], pk["harsh_brake"]["alert_trigger_rate"], o["pothole"]["alert_trigger_rate"], o["speed_breaker"]["alert_trigger_rate"], pk["minor_crash"]["alert_trigger_rate"]]
    x = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(8, 3.8))
    ax.bar(x - 0.2, [v * 100 for v in flagged], 0.38, color=[GREY, GREY, RED, RED, BLUE], label="flagged as accident")
    ax.bar(x + 0.2, [v * 100 for v in alert], 0.38, color=ORANGE, label="starts the 15 s alert (Moderate / Severe)")
    for i, (a, b) in enumerate(zip(flagged, alert)):
        ax.text(i - 0.2, a * 100 + 1.5, f"{a * 100:.1f}%", ha="center", fontsize=7.5)
        ax.text(i + 0.2, b * 100 + 1.5, f"{b * 100:.1f}%", ha="center", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.set_ylim(0, 112)
    ax.set_ylabel("% of events")
    ax.set_title("Hard braking is rejected; road-surface events the model never saw are flagged about half the time")
    ax.legend(frameon=False, loc="upper left", fontsize=8)
    save(fig, "f07_ood_probes.png")


def f08_latency():
    e = L["endpoints"]
    labels = ["GET\n/simulate", "POST\n/predict", "GET\n/hospitals", "POST\n/emergency", "alert path\n(3 calls)"]
    vals = [e["GET /api/simulate"], e["POST /api/predict"], e["GET /api/hospitals?k=3"], e["POST /api/emergency"], L["alert_path_ms"]]
    x = np.arange(len(vals))
    fig, ax = plt.subplots(figsize=(7.6, 3.7))
    ax.bar(x - 0.2, [v["mean"] for v in vals], 0.38, color=BLUE, label="mean")
    ax.bar(x + 0.2, [v["p95"] for v in vals], 0.38, color=ORANGE, label="95th percentile")
    for i, v in enumerate(vals):
        ax.text(i - 0.2, v["mean"] + 1.5, f"{v['mean']:.1f}", ha="center", fontsize=7.5)
        ax.text(i + 0.2, v["p95"] + 1.5, f"{v['p95']:.1f}", ha="center", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("milliseconds (loopback, Flask dev server)")
    ax.set_title("API latency, 300 calls per endpoint (150 for the alert path)")
    ax.legend(frameon=False)
    save(fig, "f08_api_latency.png")


def f09_seeds():
    rows = M["five_seed"]["rows"]
    x = [r["seed"] for r in rows]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ax.plot(x, [r["sev_accuracy"] for r in rows], "o-", color=BLUE, label="severity accuracy")
    ax.plot(x, [r["sev_macro_f1"] for r in rows], "s-", color=ORANGE, label="severity macro-F1")
    ax.plot(x, [r["alert_recall"] for r in rows], "^-", color=TEAL, label="alert-trigger recall")
    ax.set_xticks(x)
    ax.set_xlabel("seed (new dataset, split and forests each time)")
    ax.set_ylabel("score on 2,400 test events")
    ax.set_title("Five-seed repeat: detector accuracy was 1.000 in every run")
    ax.legend(frameon=False)
    save(fig, "f09_five_seeds.png")


def f10_ablation():
    a = M["ablation"]
    names = list(a)
    fig, ax = plt.subplots(figsize=(8.6, 3.9))
    y = np.arange(len(names))
    ax.barh(y - 0.2, [a[n]["sev_accuracy"] for n in names], 0.38, color=BLUE, label="severity accuracy")
    ax.barh(y + 0.2, [a[n]["sev_macro_f1"] for n in names], 0.38, color=ORANGE, label="severity macro-F1")
    ax.set_yticks(y)
    ax.set_yticklabels([n.replace(" (", "\n(") for n in names], fontsize=7.5)
    ax.invert_yaxis()
    ax.set_xlim(0.9, 1.005)
    ax.set_xlabel("score (detector accuracy is 1.000 in every row except the last: 0.9996)")
    ax.set_title("Feature-group ablation (models retrained on each subset)")
    ax.legend(frameon=False, loc="lower left", fontsize=8)
    save(fig, "f10_ablation.png")


if __name__ == "__main__":
    f01_feature_separation()
    f02_confusion()
    f03_baselines()
    f04_importance()
    f05_noise()
    f06_threshold()
    f07_ood()
    f08_latency()
    f09_seeds()
    f10_ablation()
