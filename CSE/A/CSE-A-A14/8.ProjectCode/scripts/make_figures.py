"""Result figures and the extra analyses for the documentation.

Re-trains the models with the project's own src/ functions on the app-default split (80/20, seed 42,
class weights), so every curve is real. Reads metrics.json for the numbers already measured.

    python scripts/make_figures.py

Writes docs/figures/*.png and experiments/churn_synthetic/extra_analysis.json
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
os.environ.setdefault("LOKY_MAX_CPU_COUNT", str(os.cpu_count() or 1))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import brier_score_loss  # noqa: E402

from data_loader import detect_column_types, normalize_target, profile_dataset  # noqa: E402
from preprocessing import build_preprocessor, clean_missing_and_duplicates, get_feature_names, train_test_split_data  # noqa: E402
from train_models import train_selected_models  # noqa: E402
from utils import assign_risk_series, make_tenure_group  # noqa: E402

FIG = os.path.join(ROOT, "docs", "figures")
EXP = os.path.join(ROOT, "experiments", "churn_synthetic")
os.makedirs(FIG, exist_ok=True)
M = json.load(open(os.path.join(EXP, "metrics.json"), encoding="utf8"))

NAVY, BLUE, ORANGE, GREEN, PURPLE, GREY = "#1B2A41", "#2A78D6", "#EB6834", "#1BAF7A", "#6B52D6", "#94A3B8"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#475569", "axes.titleweight": "bold", "axes.titlesize": 11, "savefig.dpi": 150})


def save(fig, name, dpi=150):
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, name), dpi=dpi, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


# ------------------------------------------------------------------ data and the app-default split
df = pd.read_csv(os.path.join(ROOT, "data", "customer_churn.csv"))
prof = profile_dataset(df)
target, idc = prof.target_col, prof.id_col
df, _ = clean_missing_and_duplicates(df)
num, cat = detect_column_types(df, target, idc)
feats = num + cat
y = normalize_target(df, target)
X_train, X_test, y_train, y_test = train_test_split_data(df[feats], y, test_size=0.2)
pre = build_preprocessor(num, cat)
Xtr, Xte = pre.fit_transform(X_train), pre.transform(X_test)
models, res = train_selected_models(Xtr, y_train.values, Xte, y_test.values,
                                    ["Logistic Regression", "Decision Tree", "Random Forest", "Gradient Boosting", "Hist Gradient Boosting"], "class_weight")
SHORT = {"Logistic Regression": "LR", "Decision Tree": "DT", "Random Forest": "RF", "Gradient Boosting": "GB", "Hist Gradient Boosting": "HGB"}
COL = {"Logistic Regression": BLUE, "Decision Tree": ORANGE, "Random Forest": GREEN, "Gradient Boosting": PURPLE, "Hist Gradient Boosting": GREY}
CW = M["app_default_split"]["class_weight"]["models"]
# the re-trained models must reproduce the stored numbers exactly
for n in CW:
    assert abs(res[n]["f1_score"] - CW[n]["f1_score"]) < 5e-4, (n, res[n]["f1_score"], CW[n]["f1_score"])

# ------------------------------------------------------------------ 1. class balance
fig, ax = plt.subplots(figsize=(4.6, 3.4))
counts = [int((y == 0).sum()), int((y == 1).sum())]
b = ax.bar(["Retained", "Churned"], counts, color=[BLUE, ORANGE], width=0.55)
for r, c in zip(b, counts):
    ax.text(r.get_x() + r.get_width() / 2, c + 12, f"{c}  ({100 * c / len(y):.1f}%)", ha="center", fontsize=10, color=NAVY)
ax.set_ylabel("Customers")
ax.set_ylim(0, max(counts) * 1.18)
ax.set_title("Class balance of the 1,000-customer dataset")
save(fig, "class_balance.png")

# ------------------------------------------------------------------ 2. churn rate by contract, tenure group, internet service, payment method
d = df.copy()
d["_y"] = y.values
d["Tenure group"] = make_tenure_group(d["tenure"])
fig, axs = plt.subplots(2, 2, figsize=(9.2, 6.2))
for ax, col, ttl in ((axs[0, 0], "Contract", "Contract type"), (axs[0, 1], "Tenure group", "Tenure group"),
                     (axs[1, 0], "InternetService", "Internet service"), (axs[1, 1], "PaymentMethod", "Payment method")):
    g = d.groupby(col)["_y"].agg(["mean", "size"]).sort_values("mean", ascending=False)
    bars = ax.barh([str(i) for i in g.index][::-1], (g["mean"] * 100).values[::-1], color=ORANGE)
    for r, (m_, n_) in zip(bars, list(zip(g["mean"], g["size"]))[::-1]):
        ax.text(r.get_width() + 0.8, r.get_y() + r.get_height() / 2, f"{m_ * 100:.1f}%  (n={n_})", va="center", fontsize=8.5, color=NAVY)
    ax.axvline(100 * y.mean(), color=NAVY, ls="--", lw=1)
    ax.set_xlim(0, max(g["mean"] * 100) * 1.45)
    ax.set_title(f"Churn rate by {ttl.lower()}")
    ax.set_xlabel("Churn rate (%); dashed line = overall 26.4%")
save(fig, "churn_by_segment.png")
seg = {col: {str(k): round(float(v), 4) for k, v in d.groupby(col)["_y"].mean().items()} for col in ("Contract", "Tenure group", "InternetService", "PaymentMethod")}

# ------------------------------------------------------------------ 3. numeric distributions by class
fig, axs = plt.subplots(1, 3, figsize=(10.4, 3.3))
for ax, col in zip(axs, ("tenure", "MonthlyCharges", "TotalCharges")):
    ax.hist(d.loc[d._y == 0, col], bins=24, alpha=0.65, color=BLUE, label="Retained")
    ax.hist(d.loc[d._y == 1, col], bins=24, alpha=0.65, color=ORANGE, label="Churned")
    ax.set_title(col)
    ax.set_xlabel(col)
    ax.set_ylabel("Customers")
axs[0].legend(frameon=False)
save(fig, "numeric_distributions.png")

# ------------------------------------------------------------------ 4. model comparison (5 models x 5 metrics)
keys = ["accuracy", "precision", "recall", "f1_score", "roc_auc"]
lab = ["Accuracy", "Precision", "Recall", "F1", "ROC-AUC"]
fig, ax = plt.subplots(figsize=(9.2, 4.2))
w = 0.16
for i, n in enumerate(SHORT):
    vals = [CW[n][k] for k in keys]
    bars = ax.bar(np.arange(5) + (i - 2) * w, vals, w, color=COL[n], label=n)
    for r, v in zip(bars, vals):
        ax.text(r.get_x() + r.get_width() / 2, v + 0.01, f"{v:.2f}", ha="center", fontsize=7, rotation=90, color=NAVY)
ax.set_xticks(np.arange(5))
ax.set_xticklabels(lab)
ax.set_ylim(0, 1.0)
ax.set_ylabel("Score on the 200-row test split")
ax.legend(ncol=5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.13), fontsize=8.5)
save(fig, "model_comparison.png")

# paper-size version (3 required models; half-width, readable)
fig, ax = plt.subplots(figsize=(3.45, 2.55))
w = 0.26
for i, n in enumerate(("Logistic Regression", "Decision Tree", "Random Forest")):
    vals = [CW[n][k] for k in keys]
    bars = ax.bar(np.arange(5) + (i - 1) * w, vals, w, color=COL[n], label=SHORT[n])
    for r, v in zip(bars, vals):
        ax.text(r.get_x() + r.get_width() / 2, v + 0.012, f"{v:.2f}".lstrip("0"), ha="center", fontsize=5.5, rotation=90, color=NAVY)
ax.set_xticks(np.arange(5))
ax.set_xticklabels(["Acc.", "Prec.", "Rec.", "F1", "AUC"], fontsize=7)
ax.tick_params(axis="y", labelsize=7)
ax.set_ylim(0, 0.95)
ax.legend(ncol=3, frameon=False, fontsize=7, loc="upper center", bbox_to_anchor=(0.5, 1.12))
save(fig, "paper_model_comparison.png", dpi=300)

# ------------------------------------------------------------------ 5. confusion matrices (LR, DT, RF)
fig, axs = plt.subplots(1, 3, figsize=(9.6, 3.3))
for ax, n in zip(axs, ("Logistic Regression", "Decision Tree", "Random Forest")):
    cm = np.array(CW[n]["confusion_matrix"])
    ax.imshow(cm, cmap="Blues")
    for (i, j), v in np.ndenumerate(cm):
        ax.text(j, i, str(v), ha="center", va="center", fontsize=14, color="white" if v > cm.max() / 2 else NAVY, fontweight="bold")
    ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
    ax.set_xticklabels(["Retained", "Churn"]); ax.set_yticklabels(["Retained", "Churn"])
    ax.set_xlabel("Predicted"); ax.set_ylabel("Actual")
    ax.set_title(n)
    ax.spines[:].set_visible(False)
save(fig, "confusion_matrices.png")

# ------------------------------------------------------------------ 6. ROC and PR curves (3 required models)
fig, axs = plt.subplots(1, 2, figsize=(9.2, 3.9))
for n in ("Logistic Regression", "Decision Tree", "Random Forest"):
    fpr, tpr = res[n]["roc_curve"]
    axs[0].plot(fpr, tpr, color=COL[n], lw=2, label=f"{SHORT[n]} (AUC {res[n]['roc_auc']:.3f})")
    p_, r_ = res[n]["pr_curve"]
    axs[1].plot(r_, p_, color=COL[n], lw=2, label=SHORT[n])
axs[0].plot([0, 1], [0, 1], "--", color=GREY)
axs[0].set_xlabel("False positive rate"); axs[0].set_ylabel("True positive rate"); axs[0].set_title("ROC curves"); axs[0].legend(frameon=False, loc="lower right")
axs[1].axhline(y_test.mean(), ls="--", color=GREY)
axs[1].text(0.02, y_test.mean() + 0.015, f"no-skill = {y_test.mean():.3f}", color="#475569", fontsize=8.5)
axs[1].set_xlabel("Recall"); axs[1].set_ylabel("Precision"); axs[1].set_title("Precision-recall curves"); axs[1].legend(frameon=False)
save(fig, "roc_pr_curves.png")

# ------------------------------------------------------------------ 7. stability: single split vs 5-fold CV vs 5 splits (F1, ROC-AUC)
fig, axs = plt.subplots(1, 2, figsize=(9.2, 3.8))
three = ("Logistic Regression", "Decision Tree", "Random Forest")
for ax, key, ttl in ((axs[0], "f1_score", "F1-score"), (axs[1], "roc_auc", "ROC-AUC")):
    w = 0.26
    for i, (src, nm, col) in enumerate((("single", "Single split (seed 42)", GREY), ("cv", "5-fold CV", BLUE), ("spl", "5 random splits", ORANGE))):
        means, sds = [], []
        for n in three:
            if src == "single":
                means.append(CW[n][key]); sds.append(0)
            else:
                d_ = (M["cross_validation_5fold_class_weight"] if src == "cv" else M["repeated_random_splits_5_seeds_class_weight"])[n][key]
                means.append(d_["mean"]); sds.append(d_["std"])
        ax.bar(np.arange(3) + (i - 1) * w, means, w, yerr=sds, capsize=3, color=col, label=nm, ecolor=NAVY)
        for x_, m_ in zip(np.arange(3) + (i - 1) * w, means):
            ax.text(x_, 0.02, f"{m_:.2f}", ha="center", fontsize=8, color="white", fontweight="bold")
    ax.set_xticks(range(3)); ax.set_xticklabels([SHORT[n] for n in three]); ax.set_ylim(0, 0.85); ax.set_title(ttl + " (error bar = 1 sd)")
axs[0].legend(frameon=False, fontsize=8, loc="upper right")
save(fig, "stability.png")

# ------------------------------------------------------------------ 8. imbalance strategy
fig, axs = plt.subplots(1, 2, figsize=(9.2, 3.8))
S = {"none": "No handling", "class_weight": "Class weights", "smote": "SMOTE"}
for ax, n in zip(axs, ("Logistic Regression", "Random Forest")):
    w = 0.26
    for i, (k, c) in enumerate((("accuracy", GREY), ("recall", ORANGE), ("f1_score", BLUE))):
        vals = [M["app_default_split"][s]["models"][n][k] for s in S]
        bars = ax.bar(np.arange(3) + (i - 1) * w, vals, w, color=c, label={"accuracy": "Accuracy", "recall": "Recall", "f1_score": "F1"}[k])
        for r, v in zip(bars, vals):
            ax.text(r.get_x() + r.get_width() / 2, v + 0.01, f"{v:.2f}", ha="center", fontsize=8, color=NAVY)
    ax.set_xticks(range(3)); ax.set_xticklabels(list(S.values())); ax.set_ylim(0, 0.95); ax.set_title(n)
axs[0].legend(frameon=False, fontsize=8.5, loc="upper left", ncol=3)
save(fig, "imbalance_strategy.png")

# ------------------------------------------------------------------ 9. drivers: LR coefficients and permutation importance
imp = M["importance"]["model_importance"]
perm = M["importance"]["permutation_importance"]
fig, axs = plt.subplots(1, 2, figsize=(10.2, 4.0))
axs[0].barh([i["feature"] for i in imp][::-1], [i["importance"] for i in imp][::-1], color=BLUE)
axs[0].set_title("LR: absolute coefficient (top 10)", fontsize=10); axs[0].set_xlabel("Absolute standardised coefficient")
perm8 = perm[:8]
axs[1].barh([i["feature"] for i in perm8][::-1], [i["importance"] for i in perm8][::-1], color=GREEN)
axs[1].set_title("Permutation importance", fontsize=10); axs[1].set_xlabel("Mean drop in accuracy")
save(fig, "feature_importance.png")

# ------------------------------------------------------------------ 10. risk band distribution of the 1,000 customers
rb = M["risk_bands_default_thresholds"]
fig, ax = plt.subplots(figsize=(5.6, 3.5))
names = ["Low Risk", "Medium Risk", "High Risk", "Critical Risk"]
vals = [rb["counts"][n] for n in names]
bars = ax.bar(["Low\n<30%", "Medium\n30-60%", "High\n60-80%", "Critical\n>=80%"], vals, color=[GREEN, "#E8A317", ORANGE, "#C0392B"], width=0.6)
for r, v in zip(bars, vals):
    ax.text(r.get_x() + r.get_width() / 2, v + 8, f"{v} ({100 * v / rb['total']:.1f}%)", ha="center", fontsize=9, color=NAVY)
ax.set_ylim(0, max(vals) * 1.18); ax.set_ylabel("Customers"); ax.set_title("Risk bands at the default 30 / 60 / 80 thresholds")
save(fig, "risk_bands.png")

# ------------------------------------------------------------------ 11. extra analyses on the LR test predictions
lr = res["Logistic Regression"]
proba, yt = lr["y_proba"], y_test.values
extra = {"model": "Logistic Regression", "split": "80/20 stratified, seed 42, class weights", "test_rows": int(len(yt)), "test_churners": int(yt.sum())}

# (a) decision-threshold sweep
ths = np.round(np.arange(0.20, 0.81, 0.05), 2)
sweep = []
for t in ths:
    p = (proba >= t).astype(int)
    tp = int(((p == 1) & (yt == 1)).sum()); fp = int(((p == 1) & (yt == 0)).sum()); fn = int(((p == 0) & (yt == 1)).sum())
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    sweep.append({"threshold": float(t), "flagged": int(p.sum()), "precision": round(prec, 4), "recall": round(rec, 4), "f1": round(f1, 4)})
extra["threshold_sweep"] = sweep
fig, ax = plt.subplots(figsize=(5.2, 3.6))
ax.plot(ths, [s["precision"] for s in sweep], color=BLUE, lw=2, marker="o", ms=3, label="Precision")
ax.plot(ths, [s["recall"] for s in sweep], color=ORANGE, lw=2, marker="o", ms=3, label="Recall")
ax.plot(ths, [s["f1"] for s in sweep], color=GREEN, lw=2, marker="o", ms=3, label="F1")
ax.axvline(0.5, ls="--", color=GREY); ax.text(0.505, 0.03, "app batch cut-off 0.50", fontsize=8, color="#475569")
ax.set_xlabel("Decision threshold on predicted churn probability"); ax.set_ylabel("Score"); ax.set_ylim(0, 1.0); ax.legend(frameon=False, loc="center left")
ax.set_title("Threshold trade-off (Logistic Regression, test split)")
save(fig, "threshold_sweep.png")

# (b) reliability / Brier
bins = np.linspace(0, 1, 6)
idx = np.clip(np.digitize(proba, bins) - 1, 0, 4)
rel = []
for b_ in range(5):
    m_ = idx == b_
    if m_.sum():
        rel.append({"bin": f"{bins[b_]:.1f}-{bins[b_ + 1]:.1f}", "n": int(m_.sum()), "mean_predicted": round(float(proba[m_].mean()), 4), "observed_churn": round(float(yt[m_].mean()), 4)})
extra["reliability"] = rel
extra["brier_score"] = round(float(brier_score_loss(yt, proba)), 4)
extra["brier_no_skill_constant_base_rate"] = round(float(yt.mean() * (1 - yt.mean())), 4)
extra["mean_predicted_probability"] = round(float(proba.mean()), 4)
extra["observed_churn_rate_test"] = round(float(yt.mean()), 4)
fig, ax = plt.subplots(figsize=(4.6, 3.6))
ax.plot([0, 1], [0, 1], "--", color=GREY, label="perfectly calibrated")
ax.plot([r["mean_predicted"] for r in rel], [r["observed_churn"] for r in rel], "o-", color=BLUE, lw=2, label="Logistic Regression")
for r in rel:
    ax.text(r["mean_predicted"] + 0.015, r["observed_churn"] - 0.04, f"n={r['n']}", fontsize=7.5, color="#475569")
ax.set_xlabel("Mean predicted probability"); ax.set_ylabel("Observed churn rate"); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.legend(frameon=False)
ax.set_title("Reliability of the predicted probabilities")
save(fig, "calibration.png")

# (c) targeting value: churners captured by contacting the top-k% scored customers
order = np.argsort(-proba)
lift = []
for frac in (0.1, 0.2, 0.3, 0.4, 0.5):
    k = int(round(frac * len(yt)))
    cap = int(yt[order[:k]].sum())
    lift.append({"top_fraction": frac, "contacted": k, "churners_captured": cap, "capture_rate": round(cap / yt.sum(), 4), "precision": round(cap / k, 4),
                 "lift": round((cap / k) / yt.mean(), 3)})
extra["targeting_lift"] = lift
fig, ax = plt.subplots(figsize=(5.2, 3.6))
fr = [0] + [l["top_fraction"] for l in lift]
ax.plot([0] + [f * 100 for f in fr[1:]], [0] + [l["capture_rate"] * 100 for l in lift], "o-", color=BLUE, lw=2, label="Ranked by model")
ax.plot([0, 50], [0, 50], "--", color=GREY, label="Random contact")
ax.set_xlabel("Share of customers contacted (highest risk first), %"); ax.set_ylabel("Churners captured, %")
ax.legend(frameon=False); ax.set_title("Retention targeting value (test split)")
save(fig, "targeting_lift.png")

# (d) RF/DT/LR agreement is already in metrics; store the segment churn table
extra["churn_rate_by_segment"] = seg
json.dump(extra, open(os.path.join(EXP, "extra_analysis.json"), "w", encoding="utf8"), indent=2)
print("wrote extra_analysis.json")
