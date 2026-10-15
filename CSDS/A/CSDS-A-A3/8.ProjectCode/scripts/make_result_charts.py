"""Draw the result charts (PNG, 150 dpi) into docs/charts/ from the measured files.

    python scripts/make_result_charts.py

Reads models/metrics.json, docs/experiments/measured.json and docs/experiments/test_results.json (all written by
the measurement scripts) plus data/urls_sample.csv. Nothing is typed in by hand.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "charts"
OUT.mkdir(parents=True, exist_ok=True)
M = json.loads((ROOT / "models" / "metrics.json").read_text())
R = json.loads((ROOT / "docs" / "experiments" / "measured.json").read_text())
T = json.loads((ROOT / "docs" / "experiments" / "test_results.json").read_text())
V2 = json.loads((ROOT / "docs" / "experiments" / "demo_retrain_metrics_v2.json").read_text())

INK, GREEN, INDIGO, AMBER, ROSE, GREY = "#1b2238", "#0f7a5a", "#3f3fbf", "#d99a1e", "#c9372c", "#8a93a8"
NAMES = {"xgboost": "XGBoost", "random_forest": "Random Forest", "logistic_regression": "Logistic Regression"}
COL = {"xgboost": GREEN, "random_forest": INDIGO, "logistic_regression": AMBER}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": "#444", "axes.spines.top": False,
                     "axes.spines.right": False, "axes.titleweight": "bold", "axes.titlesize": 10})


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=150, facecolor="white")
    plt.close(fig)
    print("saved", name)


def comparison():
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    keys = ["accuracy", "precision", "recall", "f1", "roc_auc"]
    labels = ["Accuracy", "Precision", "Recall", "F1", "ROC-AUC"]
    w = 0.26
    for i, n in enumerate(["xgboost", "random_forest", "logistic_regression"]):
        vals = [M["models"][n][k] * 100 for k in keys]
        b = ax.bar(np.arange(5) + (i - 1) * w, vals, w, label=NAMES[n], color=COL[n])
        for r, v in zip(b, vals):
            ax.text(r.get_x() + r.get_width() / 2, v + 0.6, f"{v:.1f}", ha="center", fontsize=6.8)
    ax.set_xticks(range(5))
    ax.set_xticklabels(labels)
    ax.set_ylim(60, 108)
    ax.set_ylabel("percent (held-out 8,000 URLs)")
    ax.set_title("Model comparison on the held-out test set")
    ax.legend(loc="upper center", frameon=False, ncol=3, fontsize=8)
    save(fig, "model_comparison.png")


def confusion():
    fig, axs = plt.subplots(1, 3, figsize=(8.4, 2.9))
    for ax, n in zip(axs, ["xgboost", "random_forest", "logistic_regression"]):
        cm = M["models"][n]["confusion_matrix"]
        a = np.array([[cm["tn"], cm["fp"]], [cm["fn"], cm["tp"]]])
        ax.imshow(a, cmap="Greens", vmin=0, vmax=4200)
        for (i, j), v in np.ndenumerate(a):
            ax.text(j, i, f"{v:,}", ha="center", va="center", fontsize=11, fontweight="bold", color="white" if v > 2500 else INK)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["pred. legit", "pred. phishing"], fontsize=7.5)
        ax.set_yticks([0, 1])
        ax.set_yticklabels(["actual legit", "actual phishing"], fontsize=7.5, rotation=90, va="center")
        ax.set_title(NAMES[n], fontsize=9)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.tick_params(length=0)
    save(fig, "confusion_matrices.png")


def roc():
    fig, ax = plt.subplots(figsize=(4.6, 4.0))
    for n in ["xgboost", "random_forest", "logistic_regression"]:
        r = R["roc"][n]
        ax.plot(r["fpr"], r["tpr"], color=COL[n], lw=1.8, label=f"{NAMES[n]} (AUC {r['auc']:.3f})")
    ax.plot([0, 1], [0, 1], color=GREY, ls="--", lw=1)
    ax.set_xlabel("false-positive rate")
    ax.set_ylabel("true-positive rate (recall)")
    ax.set_title("ROC curves, 8,000 test URLs")
    ax.legend(loc="lower right", frameon=False, fontsize=8)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    save(fig, "roc_curves.png")


def thresholds():
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    t = [d["threshold"] for d in R["thresholds"]]
    for k, c, lab in (("precision", INDIGO, "Precision"), ("recall", ROSE, "Recall"), ("f1", GREEN, "F1")):
        ax.plot(t, [d[k] * 100 for d in R["thresholds"]], marker="o", ms=4, color=c, lw=1.8, label=lab)
    ax.axvline(0.35, color=AMBER, ls="--", lw=1)
    ax.axvline(0.60, color=ROSE, ls="--", lw=1)
    ax.text(0.352, 76, "suspicious\n>= 0.35", fontsize=7, color=AMBER)
    ax.text(0.602, 76, "phishing\n>= 0.60", fontsize=7, color=ROSE)
    ax.set_xlabel("probability threshold")
    ax.set_ylabel("percent")
    ax.set_title("XGBoost: precision, recall and F1 against the threshold")
    ax.legend(frameon=False, loc="lower center", ncol=3, fontsize=8)
    ax.set_ylim(72, 101)
    save(fig, "threshold_sweep.png")


def importance():
    fig, ax = plt.subplots(figsize=(6.0, 3.8))
    top = M["models"]["xgboost"]["top_features"][:10][::-1]
    ax.barh([d["feature"] for d in top], [d["importance"] for d in top], color=GREEN)
    for i, d in enumerate(top):
        ax.text(d["importance"] + 0.003, i, f"{d['importance']:.3f}", va="center", fontsize=7.5)
    ax.set_xlabel("importance (share of total)")
    ax.set_title("XGBoost: ten most important features")
    ax.set_xlim(0, 0.24)
    save(fig, "feature_importance.png")


def learning():
    fig, ax = plt.subplots(figsize=(6.0, 3.5))
    x = [d["train_rows"] for d in R["learning"]]
    ax.plot(x, [d["f1"] * 100 for d in R["learning"]], marker="o", color=GREEN, lw=2, label="F1")
    ax.plot(x, [d["accuracy"] * 100 for d in R["learning"]], marker="s", ms=4, color=INDIGO, lw=1.4, label="Accuracy")
    ax.set_xlabel("training URLs used")
    ax.set_ylabel("percent on the fixed test set")
    ax.set_title("XGBoost learning curve (10% to 100% of the training data)")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.set_ylim(88, 94.5)
    save(fig, "learning_curve.png")


def ablation():
    fig, ax = plt.subplots(figsize=(6.6, 3.8))
    items = list(R["ablation"].items())
    names = [f"{k} ({v['n_features']})" for k, v in items][::-1]
    vals = [v["f1"] * 100 for _, v in items][::-1]
    cols = [GREEN if k == "all 47" else (AMBER if k.startswith("without") else INDIGO) for k, _ in items][::-1]
    ax.barh(names, vals, color=cols)
    for i, v in enumerate(vals):
        ax.text(v + 0.4, i, f"{v:.1f}", va="center", fontsize=7.5)
    ax.set_xlim(50, 100)
    ax.set_xlabel("F1 (%) on the 8,000 test URLs, threshold 0.5")
    ax.set_title("Feature ablation: XGBoost with fewer features")
    save(fig, "feature_ablation.png")


def cv():
    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    for i, n in enumerate(["xgboost", "random_forest", "logistic_regression"]):
        folds = [f * 100 for f in R["cv5"][n]["fold_f1"]]
        ax.scatter([i] * 5, folds, color=COL[n], s=26, zorder=3)
        m = R["cv5"][n]["f1"]["mean"] * 100
        ax.hlines(m, i - 0.28, i + 0.28, color=INK, lw=1.6, zorder=4)
        ax.text(i, m + 1.1 if n != "logistic_regression" else m + 1.2, f"{m:.2f}", ha="center", fontsize=8, fontweight="bold")
    ax.set_xticks(range(3))
    ax.set_xticklabels([NAMES[n] for n in ["xgboost", "random_forest", "logistic_regression"]])
    ax.set_ylabel("F1 (%) per fold")
    ax.set_title("5-fold stratified cross-validation (40,000 URLs)")
    ax.set_ylim(78, 96)
    save(fig, "cross_validation.png")


def latency():
    L = R["latency"]
    fig, ax = plt.subplots(figsize=(6.2, 3.2))
    names = ["feature extraction\n(per URL)", "extraction + model\n(single URL)", "/api/check\nmean", "/api/check\np95"]
    vals = [L["feature_extraction_ms_per_url"], L["single_url_score_ms"], L["api_check_ms_mean"], L["api_check_ms_p95"]]
    b = ax.bar(names, vals, color=[INDIGO, INDIGO, GREEN, GREEN])
    for r, v in zip(b, vals):
        ax.text(r.get_x() + r.get_width() / 2, v + 0.2, f"{v:.2f} ms", ha="center", fontsize=8)
    ax.set_ylabel("milliseconds")
    ax.set_title("Measured response times (local machine)")
    save(fig, "latency.png")


def crowd():
    fig, ax = plt.subplots(figsize=(6.0, 3.4))
    ks = [d["confirmed_urls"] for d in R["crowd"]]
    x = np.arange(len(ks))
    ax.bar(x - 0.19, [d["f1_before"] * 100 for d in R["crowd"]], 0.38, color=GREY, label="before (saved model)")
    ax.bar(x + 0.19, [d["f1_after"] * 100 for d in R["crowd"]], 0.38, color=GREEN, label="after adding confirmed URLs x3")
    for i, d in enumerate(R["crowd"]):
        ax.text(i - 0.19, d["f1_before"] * 100 + 0.1, f"{d['f1_before'] * 100:.2f}", ha="center", fontsize=7)
        ax.text(i + 0.19, d["f1_after"] * 100 + 0.1, f"{d['f1_after'] * 100:.2f}", ha="center", fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{k:,} confirmed" for k in ks])
    ax.set_ylim(90, 95)
    ax.set_ylabel("F1 (%) on the remaining unseen URLs")
    ax.set_title("Effect of retraining with confirmed URLs (mean of 3 draws)")
    ax.legend(frameon=False, fontsize=7.5, loc="upper left")
    save(fig, "crowd_experiment.png")


def bands():
    fig, ax = plt.subplots(figsize=(6.0, 3.0))
    b = R["verdict_bands"]
    labels = ["phishing URLs (4,000)", "legitimate URLs (4,000)"]
    for i, (key, lab) in enumerate((("phishing_urls", labels[0]), ("legitimate_urls", labels[1]))):
        left = 0
        for v, c, nm in (("phishing", ROSE, "verdict phishing"), ("suspicious", AMBER, "suspicious"), ("safe", GREEN, "safe")):
            n = b[key][v]
            ax.barh(i, n, left=left, color=c, label=nm if i == 0 else None)
            if n > 150:
                ax.text(left + n / 2, i, f"{n:,}", ha="center", va="center", color="white", fontsize=8, fontweight="bold")
            left += n
    ax.set_yticks([0, 1])
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel("URLs in the test set")
    ax.set_title("Deployed verdicts on the 8,000 test URLs")
    ax.legend(frameon=False, ncol=3, fontsize=7.5, loc="lower center", bbox_to_anchor=(0.5, -0.5))
    save(fig, "verdict_bands.png")


def tests():
    fig, ax = plt.subplots(figsize=(6.0, 3.0))
    cats = list(T["by_category"].items())
    ax.barh([c for c, _ in cats][::-1], [v["total"] for _, v in cats][::-1], color=INDIGO, alpha=0.25, label="checks")
    ax.barh([c for c, _ in cats][::-1], [v["passed"] for _, v in cats][::-1], color=GREEN, label="passed")
    for i, (c, v) in enumerate(cats[::-1]):
        ax.text(v["total"] + 0.3, i, f"{v['passed']}/{v['total']}", va="center", fontsize=8)
    ax.set_xlabel("automated checks (scripts/extra_tests.py)")
    ax.set_title(f"Extra test suite: {T['passed']} of {T['total']} checks passed")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    save(fig, "tests_by_category.png")


def dataset():
    df = pd.read_csv(ROOT / "data" / "urls_sample.csv")
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.0), gridspec_kw={"width_ratios": [1, 2]})
    cnt = df.label.value_counts().sort_index()
    axs[0].bar(["legitimate", "phishing"], [cnt[0], cnt[1]], color=[GREEN, ROSE])
    for i, v in enumerate([cnt[0], cnt[1]]):
        axs[0].text(i, v + 300, f"{v:,}", ha="center", fontsize=8)
    axs[0].set_ylim(0, 24000)
    axs[0].set_title("Class balance")
    bins = np.arange(0, 205, 5)
    for lab, c, nm in ((0, GREEN, "legitimate"), (1, ROSE, "phishing")):
        axs[1].hist(df[df.label == lab].url.str.len().clip(upper=200), bins=bins, color=c, alpha=0.55, label=nm)
    axs[1].set_xlabel("URL length in characters (values above 200 shown at 200)")
    axs[1].set_ylabel("URLs")
    axs[1].set_title("URL length distribution")
    axs[1].legend(frameon=False, fontsize=8)
    save(fig, "dataset_overview.png")


def retrain_versions():
    fig, ax = plt.subplots(figsize=(6.2, 3.3))
    names = ["XGBoost", "Random Forest", "Logistic Regression"]
    keys = ["xgboost", "random_forest", "logistic_regression"]
    v1 = [M["models"][k]["f1"] * 100 for k in keys]
    v2 = [V2["models"][k]["f1"] * 100 for k in keys]
    x = np.arange(3)
    ax.bar(x - 0.19, v1, 0.38, color=GREY, label=f"version 1 ({M['test_rows']:,} test URLs)")
    ax.bar(x + 0.19, v2, 0.38, color=GREEN, label=f"version 2 ({V2['test_rows']:,} test URLs)")
    for i in range(3):
        ax.text(i - 0.19, v1[i] + 0.8, f"{v1[i]:.2f}", ha="center", fontsize=7.5)
        ax.text(i + 0.19, v2[i] + 0.8, f"{v2[i]:.2f}", ha="center", fontsize=7.5)
    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.set_ylim(70, 100)
    ax.set_ylabel("F1 (%)")
    ax.set_title("Model F1 before and after the retraining demo (different test sets)")
    ax.legend(frameon=False, fontsize=7.5, loc="lower left")
    save(fig, "retrain_versions.png")


if __name__ == "__main__":
    for f in (comparison, confusion, roc, thresholds, importance, learning, ablation, cv, latency, crowd, bands, tests, dataset, retrain_versions):
        f()
