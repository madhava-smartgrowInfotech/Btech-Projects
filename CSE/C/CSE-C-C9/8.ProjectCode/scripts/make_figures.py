"""
Result charts for the project documents, drawn from artifacts/*.json (matplotlib, 150 dpi).

    python scripts/make_figures.py        # -> docs/figures/*.png

Every value is read from the artifacts written by scripts/train.py and scripts/report_metrics.py.
"""
import json
import os
import shutil

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "artifacts")
OUT = os.path.join(ROOT, "docs", "figures")
os.makedirs(OUT, exist_ok=True)

NAVY, BLUE, GREEN, ORANGE, PURPLE, GOLD, SLATE = "#1B2A41", "#2A78D6", "#1BAF7A", "#EB6834", "#6B52D6", "#E8A317", "#475569"
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#9AA8BD", "axes.titleweight": "bold", "axes.titlesize": 11, "font.size": 9})

J = lambda n: json.load(open(os.path.join(ART, n), encoding="utf-8"))
cmp_ = J("model_comparison.json")["models"]
rm = J("report_metrics.json")
val = J("validation_report.json")
shap = J("shap_global.json")
fc = J("forecast.json")
LABEL = {"logistic_regression": "Logistic\nRegression", "random_forest": "Random\nForest", "gradient_boosting": "Gradient\nBoosting", "xgboost": "XGBoost"}
ORDER = ["logistic_regression", "random_forest", "gradient_boosting", "xgboost"]
COL = {"logistic_regression": SLATE, "random_forest": GREEN, "gradient_boosting": GOLD, "xgboost": BLUE}


def save(fig, name):
    p = os.path.join(OUT, name)
    fig.savefig(p, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", p)


def model_comparison():
    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    metrics = [("accuracy", "Accuracy"), ("precision", "Precision"), ("recall", "Recall"), ("f1", "F1"), ("roc_auc", "ROC-AUC")]
    w = 0.19
    x = np.arange(len(metrics))
    for i, m in enumerate(ORDER):
        vals = [cmp_[m][k] for k, _ in metrics]
        b = ax.bar(x + (i - 1.5) * w, vals, w, label=LABEL[m].replace("\n", " "), color=COL[m])
        for r, v in zip(b, vals):
            ax.text(r.get_x() + r.get_width() / 2, v + 0.008, f"{v:.3f}", ha="center", fontsize=5.8, rotation=90)
    ax.set_xticks(x)
    ax.set_xticklabels([n for _, n in metrics])
    ax.set_ylim(0.5, 1.03)
    ax.set_ylabel("Score on 9,769 held-out test rows")
    ax.set_title("Four classifiers on the same stratified test split")
    ax.legend(ncol=4, fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.09), frameon=False)
    ax.grid(axis="y", alpha=0.25)
    save(fig, "model_comparison.png")


def cv_folds():
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    for i, m in enumerate(ORDER):
        v = val["cv_roc_auc"][m]
        ax.scatter([i] * len(v), v, color=COL[m], s=28, zorder=3)
        ax.hlines(np.mean(v), i - 0.25, i + 0.25, color=COL[m], lw=2)
        ax.text(i, max(v) + 0.0012, f"mean {np.mean(v):.4f}", ha="center", fontsize=7.5, color=COL[m])
    ax.set_xticks(range(4))
    ax.set_xticklabels([LABEL[m] for m in ORDER])
    ax.set_ylabel("ROC-AUC per fold")
    ax.set_ylim(0.903, 0.936)
    ax.set_title("Five-fold stratified cross-validation (training split)")
    ax.grid(axis="y", alpha=0.25)
    save(fig, "cv_folds.png")


def confusion():
    fig, axes = plt.subplots(1, 4, figsize=(10, 2.9))
    for ax, m in zip(axes, ORDER):
        c = rm["models"][m]
        cm = np.array([[c["tn"], c["fp"]], [c["fn"], c["tp"]]])
        ax.imshow(cm, cmap="Blues", vmin=0, vmax=7500)
        for i in range(2):
            for j in range(2):
                ax.text(j, i, f"{cm[i, j]:,}", ha="center", va="center", fontsize=10, color="white" if cm[i, j] > 3750 else NAVY, fontweight="bold")
        ax.set_xticks([0, 1]); ax.set_xticklabels(["<=50K", ">50K"], fontsize=8)
        ax.set_yticks([0, 1]); ax.set_yticklabels(["<=50K", ">50K"], fontsize=8)
        ax.set_xlabel("Predicted", fontsize=8)
        if m == ORDER[0]:
            ax.set_ylabel("Actual", fontsize=8)
        ax.set_title(LABEL[m].replace("\n", " "), fontsize=9)
        for s in ax.spines.values():
            s.set_visible(False)
    fig.subplots_adjust(wspace=0.5)
    fig.suptitle("Confusion matrices on the 9,769-row test split (threshold 0.5)", fontsize=10, fontweight="bold", y=1.04)
    save(fig, "confusion_matrices.png")


def threshold():
    sw = rm["threshold_sweep_xgboost"]
    t = [r["threshold"] for r in sw]
    fig, ax = plt.subplots(figsize=(6.6, 3.5))
    for k, c, lab in (("precision", BLUE, "Precision"), ("recall", ORANGE, "Recall"), ("f1", GREEN, "F1"), ("accuracy", SLATE, "Accuracy")):
        ax.plot(t, [r[k] for r in sw], marker="o", ms=4, color=c, label=lab, lw=1.8)
    ax.axvline(0.5, color="#9AA8BD", ls="--", lw=1)
    ax.text(0.505, 0.43, "default 0.5", fontsize=7.5, color=SLATE)
    ax.set_xlabel("Decision threshold on P(income > 50K)")
    ax.set_ylabel("Score (XGBoost, test split)")
    ax.set_title("Threshold analysis: precision and recall trade off")
    ax.legend(ncol=4, fontsize=8, frameon=False, loc="lower center", bbox_to_anchor=(0.5, -0.32))
    ax.grid(alpha=0.25)
    save(fig, "threshold_sweep.png")


def calibration():
    cal = [c for c in rm["calibration"] if c["n"]]
    fig, ax = plt.subplots(figsize=(4.6, 4.2))
    ax.plot([0, 1], [0, 1], "--", color="#9AA8BD", label="perfect calibration")
    ax.plot([c["mean_pred"] for c in cal], [c["observed"] for c in cal], marker="o", color=BLUE, lw=1.8, label="XGBoost (10 bins)")
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Observed share with income > 50K")
    ax.set_title("Reliability diagram, test split")
    ax.legend(fontsize=8, frameon=False)
    ax.grid(alpha=0.25)
    save(fig, "calibration.png")


def shap_top():
    f = shap["features"][:12][::-1]
    fig, ax = plt.subplots(figsize=(6.6, 3.9))
    ax.barh([x["label"] for x in f], [x["mean_abs_shap"] for x in f], color=BLUE)
    for i, x in enumerate(f):
        ax.text(x["mean_abs_shap"] + 0.012, i, f"{x['mean_abs_shap']:.3f}", va="center", fontsize=7.5)
    ax.set_xlabel("Mean |SHAP value| (XGBoost, 500-row sample, log-odds scale)")
    ax.set_title("Global feature importance")
    ax.set_xlim(0, 1.15)
    save(fig, "shap_top.png")


def bands():
    cnt = rm["profile_band_counts_test"]
    act = rm["profile_band_actual_positive_rate"]
    names = ["Emerging", "Developing", "Established"]
    cols = [ORANGE, GOLD, GREEN]
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.4, 3.2))
    a.bar(names, [cnt[n] for n in names], color=cols)
    for i, n in enumerate(names):
        a.text(i, cnt[n] + 80, f"{cnt[n]:,}", ha="center", fontsize=8)
    a.set_title("Test rows per profile band")
    a.set_ylabel("Rows")
    b.bar(names, [act[n] * 100 for n in names], color=cols)
    for i, n in enumerate(names):
        b.text(i, act[n] * 100 + 1.5, f"{act[n] * 100:.1f}%", ha="center", fontsize=8)
    b.set_ylim(0, 100)
    b.set_title("Share who actually earn > 50K")
    b.set_ylabel("Percent")
    save(fig, "profile_bands.png")


def forecast_plot():
    hist = fc["history"]
    f = fc["forecast"]
    hx = list(range(len(hist)))
    fig, ax = plt.subplots(figsize=(7.6, 3.5))
    ax.plot(hx, [h["value"] for h in hist], color=NAVY, lw=1.3, label="History (synthetic index)")
    fx = list(range(len(hist), len(hist) + len(f)))
    ax.plot(fx, [x["value"] for x in f], color=GREEN, lw=1.8, label="12-month forecast")
    ax.fill_between(fx, [x["lower"] for x in f], [x["upper"] for x in f], color=GREEN, alpha=0.2, label="95% band")
    ticks = list(range(0, len(hist) + len(f), 12))
    labels = [(hist + f)[i]["date"][:4] for i in ticks]
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Household Financial Conditions Index")
    ax.set_title("Holt-Winters forecast of the (synthetic) index")
    ax.legend(fontsize=8, frameon=False, loc="upper left")
    ax.grid(alpha=0.25)
    save(fig, "forecast_plot.png")


def base_compare():
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    labs = ["Logistic\nRegression", "Random\nForest", "Gradient\nBoosting", "XGBoost"]
    base = [0.776, 0.831, 0.840, 0.842]
    ours = [cmp_[m]["roc_auc"] for m in ORDER]
    x = np.arange(4)
    b1 = ax.bar(x - 0.2, base, 0.38, color=SLATE, label="Base paper: 165 hospitals, hospital-level Group K-Fold")
    b2 = ax.bar(x + 0.2, ours, 0.38, color=BLUE, label="This project: 48,842 individuals, stratified test split")
    for bars in (b1, b2):
        for r in bars:
            ax.text(r.get_x() + r.get_width() / 2, r.get_height() + 0.006, f"{r.get_height():.3f}", ha="center", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels(labs)
    ax.set_ylim(0.6, 1.0)
    ax.set_ylabel("ROC-AUC")
    ax.set_title("ROC-AUC of the same four model families on different data")
    ax.legend(fontsize=7.5, frameon=False, loc="upper left")
    ax.grid(axis="y", alpha=0.25)
    save(fig, "base_paper_comparison.png")


def latency():
    m = json.load(open(os.path.join(ART, "measured.json")))["api_latency_ms_127_0_0_1"]
    keys = [k for k in m if k.startswith(("GET", "POST"))]
    fig, ax = plt.subplots(figsize=(7.2, 3.3))
    y = np.arange(len(keys))
    med = [m[k]["median"] for k in keys]
    p95 = [m[k]["p95"] for k in keys]
    ax.barh(y + 0.19, med, 0.36, color=BLUE, label="median")
    ax.barh(y - 0.19, p95, 0.36, color=ORANGE, label="95th percentile")
    for i in range(len(keys)):
        ax.text(med[i] + 2, i + 0.19, f"{med[i]:.1f}", va="center", fontsize=7.5)
        ax.text(p95[i] + 2, i - 0.19, f"{p95[i]:.1f}", va="center", fontsize=7.5)
    ax.set_yticks(y)
    ax.set_yticklabels(keys, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Milliseconds (40 calls each, 127.0.0.1, CPU only)")
    ax.set_title("API response time")
    ax.legend(fontsize=8, frameon=False, loc="lower right")
    save(fig, "api_latency.png")


def main():
    for fn in (model_comparison, cv_folds, confusion, threshold, calibration, shap_top, bands, forecast_plot, base_compare, latency):
        fn()
    for n in ("roc_curve.png", "shap_beeswarm.png", "confusion_matrix.png", "shap_bar.png"):
        src = os.path.join(ART, n)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(OUT, "artifact_" + n))


if __name__ == "__main__":
    main()
