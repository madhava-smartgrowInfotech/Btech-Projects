"""Result figures for the documentation set. Reads experiments/metrics.json, experiments/latency.json and data/*.csv only.
Run from 8.ProjectCode:  python scripts/docs_build/make_figures.py
(the only typed numbers are the base paper's Table 1, used in f13)."""
import json
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "docs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
M = json.loads((ROOT / "experiments" / "metrics.json").read_text())
L = json.loads((ROOT / "experiments" / "latency.json").read_text())

NAVY, BLUE, TEAL, ORANGE, PURPLE, GREY, INK = "#1F3A5F", "#2B6CB0", "#14907F", "#D9772F", "#6B5BD2", "#5B6B7F", "#14213D"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": GREY, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
                     "axes.titleweight": "bold", "axes.titlesize": 11})
SM = M["saved_models"]
NAMES = {"classical": "PCD", "sa": "SAS", "qa": "QS", "ensemble": "Ensemble"}
COL = {"classical": BLUE, "sa": ORANGE, "qa": PURPLE, "ensemble": TEAL}
BCOL = {"Logistic Regression": "#7A8CA3", "Random Forest": "#4C9A6A", "XGBoost": "#B8893A"}


def save(fig, name):
    fig.savefig(OUT / name, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("saved", name)


def pct(ax):
    ax.set_ylim(0, 1.05)
    ax.set_yticks(np.arange(0, 1.01, 0.2))
    ax.set_yticklabels([f"{int(t * 100)}%" for t in ax.get_yticks()])
    ax.grid(axis="y", color="#E3E8EF", lw=0.8)
    ax.set_axisbelow(True)


def labels(ax, bars, fmt="{:.1f}", scale=100, size=7.5):
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + 0.012, fmt.format(h * scale), ha="center", va="bottom", fontsize=size, color=INK)


# ---------------------------------------------------------------- f01
df = pd.read_csv(ROOT / "data" / "creditcard_synthetic.csv")
fig, axs = plt.subplots(1, 4, figsize=(15, 3.8), gridspec_kw={"width_ratios": [0.8, 1.3, 1.2, 1.0]})
cnt = df["Class"].value_counts().sort_index()
axs[0].bar(["Legitimate", "Fraud"], [cnt[0], cnt[1]], color=[BLUE, ORANGE])
for i, v in enumerate([cnt[0], cnt[1]]):
    axs[0].text(i, v, f"{v:,}", ha="center", va="bottom", fontsize=9)
axs[0].set_title("Class balance")
axs[0].set_ylim(0, cnt.max() * 1.15)
bins = np.linspace(0, 1200, 41)
axs[1].hist(df[df.Class == 0].Amount.clip(upper=1200), bins=bins, alpha=0.75, color=BLUE, label="Legitimate")
axs[1].hist(df[df.Class == 1].Amount.clip(upper=1200), bins=bins, alpha=0.75, color=ORANGE, label="Fraud")
axs[1].set_title("Transaction amount")
axs[1].set_xlabel("Amount (values above 1,200 shown at 1,200)")
axs[1].legend(frameon=False)
for ax, col, title in ((axs[2], "Merchant_Category", "Fraud rate by merchant"), (axs[3], "Transaction_Type", "Fraud rate by channel")):
    r = df.groupby(col)["Class"].mean().sort_values()
    ax.barh(r.index, r.values, color=TEAL)
    for i, v in enumerate(r.values):
        ax.text(v + 0.01, i, f"{v * 100:.0f}%", va="center", fontsize=8)
    ax.set_xlim(0, 1)
    ax.set_title(title)
fig.tight_layout()
save(fig, "f01_dataset_overview.png")

# ---------------------------------------------------------------- f02
fig, ax = plt.subplots(figsize=(8.5, 4.2))
metrics = ["accuracy", "precision", "recall", "f1"]
w = 0.2
for j, k in enumerate(["classical", "sa", "qa", "ensemble"]):
    bars = ax.bar(np.arange(4) + (j - 1.5) * w, [SM[k][m] for m in metrics], w, color=COL[k], label=NAMES[k])
    labels(ax, bars)
ax.set_xticks(range(4))
ax.set_xticklabels(["Accuracy", "Precision", "Recall", "F1"])
pct(ax)
ax.legend(ncol=4, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.13))
ax.set_title("Shipped models on the held-out split (threshold 0.5)", pad=26)
save(fig, "f02_model_metrics.png")

# ---------------------------------------------------------------- f03
fig, axs = plt.subplots(1, 4, figsize=(13, 3.5))
for ax, k in zip(axs, ["classical", "sa", "qa", "ensemble"]):
    r = SM[k]
    cm = np.array([[r["tn"], r["fp"]], [r["fn"], r["tp"]]])
    ax.imshow(cm, cmap="Blues", vmin=0, vmax=cm.max() * 1.1)
    for (i, j), v in np.ndenumerate(cm):
        ax.text(j, i, f"{v:,}", ha="center", va="center", fontsize=13, fontweight="bold", color="white" if v > cm.max() * 0.55 else INK)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["Pred legit", "Pred fraud"], fontsize=8)
    ax.set_yticks([0, 1]); ax.set_yticklabels(["Legit", "Fraud"], fontsize=8)
    ax.set_title(NAMES[k])
    for s in ax.spines.values():
        s.set_visible(False)
fig.tight_layout()
save(fig, "f03_confusion_matrices.png")

# ---------------------------------------------------------------- f04
fig, ax = plt.subplots(figsize=(6.2, 5.2))
for k in ["classical", "sa", "qa"]:
    ax.plot(SM[k]["roc"]["fpr"], SM[k]["roc"]["tpr"], color=COL[k], lw=2, label=f"{NAMES[k]} (AUC {SM[k]['roc_auc']:.3f})")
ax.plot(SM["ensemble"]["roc"]["fpr"], SM["ensemble"]["roc"]["tpr"], color=COL["ensemble"], lw=2, ls=":", label=f"Ensemble (AUC {SM['ensemble']['roc_auc']:.3f})")
for k, r in M["baselines_balanced"].items():
    ax.plot(r["roc"]["fpr"], r["roc"]["tpr"], color=BCOL[k], lw=1.4, ls="--", label=f"{k} (AUC {r['roc_auc']:.3f})")
ax.plot([0, 1], [0, 1], color="#C5CEDA", lw=1)
ax.set_xlabel("False positive rate"); ax.set_ylabel("True positive rate")
ax.set_title("ROC curves on the held-out split")
ax.legend(frameon=False, fontsize=8, loc="lower right")
ax.grid(color="#E3E8EF", lw=0.8)
save(fig, "f04_roc_curves.png")

# ---------------------------------------------------------------- f05
fig, axs = plt.subplots(1, 2, figsize=(11, 4))
for k in ["classical", "sa", "qa"]:
    h = SM["histories"][k]
    ep = np.arange(1, len(h["f1"]) + 1)
    axs[0].plot(ep, h["f1"], color=COL[k], lw=2, marker="o", ms=3, label=NAMES[k])
    axs[1].plot(ep, h["loss"], color=COL[k], lw=2, marker="o", ms=3, label=NAMES[k])
axs[0].set_title("F1 on the test split after each epoch"); axs[0].set_ylim(-0.02, 1.02)
axs[1].set_title("Reconstruction loss per epoch")
for ax in axs:
    ax.set_xlabel("Epoch"); ax.legend(frameon=False); ax.grid(color="#E3E8EF", lw=0.8)
fig.tight_layout()
save(fig, "f05_training_curves.png")

# ---------------------------------------------------------------- f06
fig, axs = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
for ax, key, title in ((axs[0], "ensemble_threshold_sweep", "Ensemble"), (axs[1], "classical_threshold_sweep", "PCD alone")):
    sw = SM[key]
    t = [r["threshold"] for r in sw]
    ax.plot(t, [r["precision"] for r in sw], color=BLUE, lw=2, label="Precision")
    ax.plot(t, [r["recall"] for r in sw], color=ORANGE, lw=2, label="Recall")
    if "f1" in sw[0]:
        ax.plot(t, [r["f1"] for r in sw], color=TEAL, lw=2, label="F1")
    else:
        ax.plot(t, [r["accuracy"] for r in sw], color=TEAL, lw=2, label="Accuracy")
    for v, c in ((0.4, GREY), (0.5, NAVY), (0.7, GREY)):
        ax.axvline(v, color=c, ls="--", lw=1)
    ax.text(0.405, 1.02, "0.4", fontsize=8, color=GREY); ax.text(0.505, 1.02, "0.5 verdict", fontsize=8, color=NAVY); ax.text(0.705, 1.02, "0.7", fontsize=8, color=GREY)
    ax.set_title(f"{title}: metrics by decision threshold", pad=14)
    ax.set_xlabel("Threshold"); ax.set_ylim(-0.02, 1.08); ax.legend(frameon=False, loc="lower left", fontsize=8); ax.grid(color="#E3E8EF", lw=0.8)
fig.tight_layout()
save(fig, "f06_threshold_sweep.png")

# ---------------------------------------------------------------- f07
fig, axs = plt.subplots(1, 2, figsize=(9.5, 4))
for ax, key, title in ((axs[0], "f1", "F1 (final epoch)"), (axs[1], "recall", "Recall (final epoch)")):
    mean = [M["seeds"][k][key]["mean"] for k in ("classical", "sa", "qa")]
    std = [M["seeds"][k][key]["std"] for k in ("classical", "sa", "qa")]
    bars = ax.bar(["PCD", "SAS", "QS"], mean, yerr=std, capsize=5, color=[BLUE, ORANGE, PURPLE])
    for b, m_, s_ in zip(bars, mean, std):
        ax.text(b.get_x() + b.get_width() / 2, 0.03, f"{m_ * 100:.1f}\n±{s_ * 100:.1f}", ha="center", va="bottom", color="white", fontsize=8.5, fontweight="bold")
    ax.set_title(f"{title}, mean ± sd over {len(M['seeds']['sa']['runs'])} seeds")
    pct(ax)
fig.tight_layout()
save(fig, "f07_seed_study.png")

# ---------------------------------------------------------------- f08
fig, axs = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
bal = [("SAS", SM["sa"]["f1"], ORANGE), ("QS", SM["qa"]["f1"], PURPLE), ("Ensemble", SM["ensemble"]["f1"], TEAL)]
bal += [(k.replace("Logistic Regression", "Logistic\nRegression").replace("Random Forest", "Random\nForest"), r["f1"], BCOL[k]) for k, r in M["baselines_balanced"].items()]
full = M["full39k"]
fl = [("PCD", full["classical"]["f1"], BLUE), ("SAS", full["sa"]["f1"], ORANGE), ("QS", full["qa"]["f1"], PURPLE)]
fl += [(k.replace("Logistic Regression", "Logistic\nRegression").replace("Random Forest", "Random\nForest"), full[k]["f1"], BCOL[k]) for k in ("Logistic Regression", "Random Forest", "XGBoost")]
for ax, data, title in ((axs[0], bal, f"Held-out split of the 8,000-row sample (n = {M['split']['test'][0]:,})"), (axs[1], fl, f"Whole 39,000-row file (test n = {full['test'][0]:,})")):
    bars = ax.bar([d[0] for d in data], [d[1] for d in data], color=[d[2] for d in data])
    labels(ax, bars, size=8)
    ax.set_title(title, fontsize=10)
    pct(ax)
    ax.tick_params(axis="x", labelsize=8)
axs[0].set_ylabel("F1")
fig.tight_layout()
save(fig, "f08_baseline_comparison.png")

# ---------------------------------------------------------------- f09
im = M["imbalance"]
rows = [(f"{r['model']}\n{r['strategy']}", r["precision"]["mean"], r["recall"]["mean"]) for r in im["results"]]
rb = im["rule_based"]
rows.append(("Rule\n(3 of 4 signals)", rb["precision"]["mean"], rb["recall"]["mean"]))
fig, ax = plt.subplots(figsize=(14, 4.8))
x = np.arange(len(rows))
b1 = ax.bar(x - 0.2, [r[1] for r in rows], 0.4, color=BLUE, label="Precision")
b2 = ax.bar(x + 0.2, [r[2] for r in rows], 0.4, color=ORANGE, label="Recall")
labels(ax, b1, fmt="{:.2f}", scale=1, size=6.5); labels(ax, b2, fmt="{:.2f}", scale=1, size=6.5)
ax.set_xticks(x); ax.set_xticklabels([r[0] for r in rows], fontsize=7, rotation=45, ha="right")
pct(ax)
ax.set_ylim(0, 1.15)
ax.legend(frameon=False, ncol=2, loc="upper left")
ax.set_title(f"1% fraud variant: mean over 5 seeds, {im['test_fraud_per_seed']} fraud in {im['test_rows_per_seed']:,} test rows, threshold 0.5")
fig.tight_layout()
save(fig, "f09_imbalance_study.png")

# ---------------------------------------------------------------- f10
sv = M["serving"]
fig, axs = plt.subplots(1, 3, figsize=(12, 3.9))
for ax, key, title in ((axs[0], "accuracy", "Accuracy"), (axs[1], "recall", "Recall")):
    for j, (lab, c) in enumerate((("as_served_no_scaling", ORANGE), ("with_scaling", TEAL))):
        vals = [sv[lab][k][key] for k in ("classical", "sa", "qa", "ensemble")]
        bars = ax.bar(np.arange(4) + (j - 0.5) * 0.38, vals, 0.38, color=c, label="Batch route as served (no scaling)" if j == 0 else "With scaling")
        labels(ax, bars, size=7)
    ax.set_xticks(range(4)); ax.set_xticklabels(["PCD", "SAS", "QS", "Ens."]); ax.set_title(title); pct(ax)
h_, l_ = axs[0].get_legend_handles_labels()
fig.legend(h_, l_, frameon=False, ncol=2, loc="lower center", bbox_to_anchor=(0.5, -0.08))
for j, (lab, c) in enumerate((("as_served_no_scaling", ORANGE), ("with_scaling", TEAL))):
    vals = [sv[lab][k]["fp"] for k in ("classical", "sa", "qa", "ensemble")]
    bars = axs[2].bar(np.arange(4) + (j - 0.5) * 0.38, vals, 0.38, color=c)
    for b in bars:
        axs[2].text(b.get_x() + b.get_width() / 2, b.get_height(), f"{int(b.get_height())}", ha="center", va="bottom", fontsize=7)
axs[2].set_xticks(range(4)); axs[2].set_xticklabels(["PCD", "SAS", "QS", "Ens."])
axs[2].set_title(f"False positives (of {sv['fresh_rows'] // 2:,} legitimate)")
fig.suptitle(f"Fresh {sv['fresh_rows']:,}-row batch: the batch route skips the scaler", fontweight="bold", y=1.02)
fig.tight_layout()
save(fig, "f10_serving_defect.png")

# ---------------------------------------------------------------- f11
imp = M["baselines_balanced"]["Random Forest"]["top_importances"]
fig, ax = plt.subplots(figsize=(7, 4.2))
names = [a for a, _ in imp][::-1]
vals = [b for _, b in imp][::-1]
ax.barh(names, vals, color=TEAL)
for i, v in enumerate(vals):
    ax.text(v + 0.004, i, f"{v:.3f}", va="center", fontsize=8)
ax.set_title("Random-forest importance of the ten strongest features")
ax.set_xlabel("Mean decrease in impurity")
save(fig, "f11_feature_importance.png")

# ---------------------------------------------------------------- f12
eps = [(k, v) for k, v in L.items() if isinstance(v, dict) and "median_ms" in v]
fig, ax = plt.subplots(figsize=(8.5, 4.6))
y = np.arange(len(eps))[::-1]
ax.barh(y + 0.2, [v["median_ms"] for _, v in eps], 0.4, color=BLUE, label="Median")
ax.barh(y - 0.2, [v["p95_ms"] for _, v in eps], 0.4, color=ORANGE, label="95th percentile")
for yy, (_, v) in zip(y, eps):
    ax.text(v["median_ms"] + 0.5, yy + 0.2, f"{v['median_ms']:.1f}", va="center", fontsize=7.5)
    ax.text(v["p95_ms"] + 0.5, yy - 0.2, f"{v['p95_ms']:.1f}", va="center", fontsize=7.5)
ax.set_yticks(y); ax.set_yticklabels([k.replace("_", " ") for k, _ in eps], fontsize=8)
ax.set_xlabel("Milliseconds (Flask development server, 127.0.0.1)")
ax.set_title("API response time")
ax.legend(frameon=False, loc="lower right")
fig.tight_layout()
save(fig, "f12_latency.png")

# ---------------------------------------------------------------- f13  (base paper Table 1 typed from the paper)
paper = {"PCD": (84, 86, 81, 83), "SAS": (85, 94, 82, 88), "QS": (85, 91, 79, 84)}
ours = {"PCD": "classical", "SAS": "sa", "QS": "qa"}
fig, axs = plt.subplots(1, 3, figsize=(13, 4.3), sharey=True)
for ax, (nm, vals) in zip(axs, paper.items()):
    mine = [SM[ours[nm]][m] * 100 for m in metrics]
    x = np.arange(4)
    b1 = ax.bar(x - 0.2, vals, 0.4, color=GREY, label="Base paper (real data)")
    b2 = ax.bar(x + 0.2, mine, 0.4, color=COL[ours[nm]], label="This project (synthetic data)")
    for b in list(b1) + list(b2):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1, f"{b.get_height():.0f}", ha="center", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(["Acc.", "Prec.", "Rec.", "F1"])
    ax.set_title(nm); ax.set_ylim(0, 115); ax.grid(axis="y", color="#E3E8EF"); ax.set_axisbelow(True)
axs[0].set_ylabel("Percent")
h_, l_ = axs[0].get_legend_handles_labels()
fig.legend(h_, l_, frameon=False, ncol=2, loc="lower center", bbox_to_anchor=(0.5, -0.07))
fig.suptitle("Base paper Table 1 vs this project. Different data: real Stone vs synthetic; not directly comparable", fontweight="bold", y=1.02)
fig.tight_layout()
save(fig, "f13_paper_comparison.png")
