"""Result charts (PNG, 150 dpi) from experiments/*/metrics.json into docs/charts/.

    venv\\Scripts\\python scripts/make_charts.py        (needs the backend copy for the scatter and the IoT trace)
"""
from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from exp_common import EXPERIMENTS, PROJECT  # noqa: E402

OUT = PROJECT / "docs" / "charts"
OUT.mkdir(parents=True, exist_ok=True)
G, G2, AMB, RED, BLUE, GREY = "#1b6b3a", "#7fb98f", "#e0a030", "#c8453c", "#2f6fb0", "#9aa5ba"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "axes.titlesize": 10, "axes.titleweight": "bold"})


def load(n):
    return json.loads((EXPERIMENTS / n / "metrics.json").read_text(encoding="utf-8"))


def save(fig, name):
    fig.savefig(OUT / name, dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


Q, P, R, D, I, A = load("quality"), load("price"), load("real_images"), load("delivery"), load("iot"), load("api_latency")

# 1 confusion matrix --------------------------------------------------------------------------------
cm = np.array(Q["shipped_rf"]["confusion_matrix"])
lab = Q["shipped_rf"]["labels"]
fig, ax = plt.subplots(figsize=(4.6, 3.9))
ax.imshow(cm, cmap="Greens")
ax.set_xticks(range(4), lab)
ax.set_yticks(range(4), lab)
ax.set_xlabel("Predicted grade")
ax.set_ylabel("True grade")
for i in range(4):
    for j in range(4):
        ax.text(j, i, cm[i, j], ha="center", va="center", color="white" if cm[i, j] > 150 else "black", fontsize=10)
ax.set_title("Quality model: confusion matrix (1,200 synthetic test rows)")
for s in ax.spines.values():
    s.set_visible(False)
save(fig, "01_quality_confusion_matrix.png")

# 2 feature importance ------------------------------------------------------------------------------
imp = Q["feature_importance"]["impurity"]
perm = {r["feature"]: r["mean"] for r in Q["feature_importance"]["permutation_accuracy_drop"]}
names = [r["feature"] for r in imp][::-1]
fig, ax = plt.subplots(figsize=(6.2, 3.9))
y = np.arange(len(names))
ax.barh(y + 0.2, [next(r["importance"] for r in imp if r["feature"] == n) for n in names], 0.38, color=G, label="impurity importance")
ax.barh(y - 0.2, [perm[n] for n in names], 0.38, color=AMB, label="permutation (accuracy drop)")
ax.set_yticks(y, [n.replace("_", " ") for n in names])
ax.set_title("Quality model: which features carry the grade")
ax.legend(frameon=False, loc="lower right")
save(fig, "02_quality_feature_importance.png")

# 3 baselines + seeds -------------------------------------------------------------------------------
b = Q["baselines"]
order = ["majority_class", "decision_tree_depth9", "hist_gradient_boosting", "random_forest_shipped", "knn_k15", "logistic_regression"]
labs = ["majority\nclass", "decision\ntree", "hist. grad.\nboosting", "random forest\n(shipped)", "k-NN\n(k=15)", "logistic\nregression"]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.2, 3.5), gridspec_kw={"width_ratios": [1.6, 1]})
vals = [b[k]["accuracy"] for k in order]
a1.bar(range(6), vals, color=[GREY, G2, G2, G, G2, G2])
for i, v in enumerate(vals):
    a1.text(i, v + 0.01, f"{v:.3f}", ha="center", fontsize=8)
a1.set_xticks(range(6), labs, fontsize=7.5)
a1.set_ylim(0, 1.05)
a1.set_ylabel("Test accuracy")
a1.set_title("Baselines on the same split")
s = Q["seed_study"]["runs"]
a2.bar([str(r["seed"]) for r in s], [r["accuracy"] for r in s], color=G)
a2.set_ylim(0.9, 0.94)
a2.axhline(Q["seed_study"]["accuracy_mean"], color=RED, lw=1, ls="--")
a2.set_xlabel("Split / forest seed")
a2.set_title(f"Five seeds: {Q['seed_study']['accuracy_mean']:.3f} ± {Q['seed_study']['accuracy_std']:.3f}")
save(fig, "03_quality_baselines_seeds.png")

# 4 ablation ----------------------------------------------------------------------------------------
ab, on = Q["ablation_drop_group"], Q["ablation_only_group"]
groups = list(ab)
short = ["colour", "texture", "edge density", "blemish", "size"]
fig, ax = plt.subplots(figsize=(6.2, 3.3))
x = np.arange(5)
ax.bar(x - 0.2, [on[g]["accuracy"] for g in groups], 0.38, color=AMB, label="only this group")
ax.bar(x + 0.2, [ab[g]["accuracy"] for g in groups], 0.38, color=G, label="all except this group")
ax.axhline(Q["shipped_rf"]["test_accuracy"], color=RED, ls="--", lw=1)
ax.text(4.45, Q["shipped_rf"]["test_accuracy"] + 0.012, "all 11 features: 0.923", color=RED, ha="right", fontsize=8)
ax.set_xticks(x, short)
ax.set_ylim(0.4, 1.0)
ax.set_ylabel("Test accuracy")
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)
ax.set_title("Quality model: feature-group ablation")
save(fig, "04_quality_ablation.png")

# 5 real photos: predicted grade share ---------------------------------------------------------------
sh = R["shipped_model_on_real_photos"]["predicted_grade_share_by_label"]
fig, ax = plt.subplots(figsize=(5.4, 3.3))
bottom = np.zeros(2)
for g, c in zip(["A", "B", "C", "Reject"], [G, BLUE, AMB, RED]):
    v = np.array([sh["fresh"][g], sh["rotten"][g]]) * 100
    ax.bar(["fresh (1,600)", "rotten (1,600)"], v, bottom=bottom, color=c, label=f"grade {g}")
    bottom += v
ax.set_ylabel("Share of photos (%)")
ax.set_title("Shipped model on 3,200 real fruit photos")
ax.legend(frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.12))
save(fig, "05_real_photos_grade_share.png")

# 6 real photos: AUC per fruit ----------------------------------------------------------------------
pf = R["shipped_model_per_fruit"]
fr = sorted(pf, key=lambda k: pf[k]["auc"])
fig, ax = plt.subplots(figsize=(5.8, 3.3))
ax.barh(fr, [pf[k]["auc"] for k in fr], color=[RED if pf[k]["auc"] < 0.5 else G for k in fr])
ax.axvline(0.5, color="black", lw=1, ls="--")
for i, k in enumerate(fr):
    ax.text(pf[k]["auc"] + 0.01, i, f"{pf[k]['auc']:.2f}", va="center", fontsize=8)
ax.set_xlim(0, 1)
ax.set_xlabel("AUC, P(A)+P(B) separating fresh from rotten (0.5 = chance)")
ax.set_title(f"Shipped model per fruit (all fruits pooled: {R['shipped_model_on_real_photos']['auc_fresh_vs_rotten_using_pA_plus_pB']:.2f})")
save(fig, "06_real_photos_auc_per_fruit.png")

# 7 real vs synthetic feature means ------------------------------------------------------------------
fm = R["feature_means_real_vs_synthetic"]
feats = ["mean_hue", "mean_saturation", "color_uniformity", "texture_contrast", "blemish_ratio", "size_score"]
fig, axs = plt.subplots(1, 6, figsize=(10.2, 2.9))
for ax, f in zip(axs, feats):
    v = [fm[f]["synthetic_A"], fm[f]["synthetic_B"], fm[f]["synthetic_C"], fm[f]["synthetic_Reject"], fm[f]["real_fresh"], fm[f]["real_rotten"]]
    ax.bar(range(6), v, color=[G, G, G, G, BLUE, BLUE], alpha=1)
    for k in (0, 1, 2, 3):
        ax.patches[k].set_alpha(0.35 + 0.2 * (3 - k) / 3)
    ax.set_xticks(range(6), ["A", "B", "C", "Rej", "fresh", "rotten"], fontsize=6.5, rotation=45)
    ax.set_title(f.replace("_", " "), fontsize=8)
fig.suptitle("Feature means: synthetic grade profiles (green) against 3,200 real photos (blue)", fontsize=10, fontweight="bold", y=1.04)
fig.tight_layout()
save(fig, "07_real_vs_synthetic_features.png")

# 8 real-label retrain -------------------------------------------------------------------------------
f = R["features_trained_on_real_labels"]
fig, ax = plt.subplots(figsize=(5.6, 3.2))
labs = ["shipped model\n(synthetic-trained)", "same features,\nreal labels\n(5-fold CV)", "real labels,\nunseen fruit\n(leave-fruits-out)"]
vals = [R["shipped_model_on_real_photos"]["mapped_binary_accuracy"], f["five_fold_cv_accuracy_mean"], f["leave_fruits_out_accuracy_mean"]]
ax.bar(labs, vals, color=[RED, G, AMB])
ax.axhline(0.5, color="black", ls="--", lw=1)
for i, v in enumerate(vals):
    ax.text(i, v + 0.015, f"{v:.3f}", ha="center", fontsize=9)
ax.set_ylim(0, 1.05)
ax.set_ylabel("Fresh vs rotten accuracy")
ax.set_title("What the 11 features can do with real labels")
save(fig, "08_real_label_retrain.png")

# 9 price: scatter + baselines + importance ------------------------------------------------------------
import sys  # noqa: E402

from sklearn.ensemble import GradientBoostingRegressor  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402

from app.ml.price.features import FEATURE_COLUMNS  # noqa: E402
from app.ml.price.generate_dataset import generate  # noqa: E402

df = generate()
X, y = df[FEATURE_COLUMNS].values, df["price"].values
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.15, random_state=42)
pred = GradientBoostingRegressor(n_estimators=300, max_depth=4, learning_rate=0.06, random_state=42).fit(Xtr, ytr).predict(Xte)
fig, ax = plt.subplots(figsize=(4.8, 4.2))
ax.scatter(yte, pred, s=3, alpha=0.35, color=G)
m = max(yte.max(), pred.max())
ax.plot([0, m], [0, m], color=RED, lw=1)
ax.set_xlabel("Observed price (INR / quintal, synthetic)")
ax.set_ylabel("Predicted price")
ax.set_title(f"Price model: observed vs predicted (R² {P['shipped_gbr']['r2']:.4f})")
save(fig, "09_price_scatter.png")

bl = P["baselines"]
k = ["crop_mean", "crop_x_grade_mean", "linear_regression", "random_forest_200", "gradient_boosting_shipped"]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.4, 3.3))
a1.bar(range(5), [bl[x]["mae"] for x in k], color=[GREY, GREY, GREY, G2, G])
a1.axhline(P["noise_floor"]["generating_function_vs_observed"]["mae"], color=RED, ls="--", lw=1)
a1.text(4.4, P["noise_floor"]["generating_function_vs_observed"]["mae"] + 25, "noise floor 106", color=RED, ha="right", fontsize=8)
for i, x in enumerate(k):
    a1.text(i, bl[x]["mae"] + 20, f"{bl[x]['mae']:.0f}", ha="center", fontsize=8)
a1.set_xticks(range(5), ["crop\nmean", "crop x\ngrade", "linear\nregr.", "random\nforest", "GBR\n(shipped)"], fontsize=7.5)
a1.set_ylabel("Test MAE (INR / quintal)")
a1.set_title("Price baselines")
fi = P["feature_importance_grouped"][:8][::-1]
a2.barh([r["feature"] for r in fi], [r["importance"] for r in fi], color=G)
a2.set_title("Price model: grouped importance")
fig.tight_layout()
save(fig, "10_price_baselines_importance.png")

# 10 served forecast: best sell day ---------------------------------------------------------------------
h = P["served_forecast"]["best_sell_day_hist"]
fig, ax = plt.subplots(figsize=(5.8, 3.1))
ax.bar([int(a) for a in h], list(h.values()), color=G)
ax.set_xlabel("Recommended best day to sell (0 = today)")
ax.set_ylabel("Crop x region x grade combinations (of 256)")
ax.set_title("Best-sell-day recommendations")
save(fig, "11_best_sell_day_hist.png")

# 11 IoT -----------------------------------------------------------------------------------------------
from app.ml.iot.simulate import ShipmentSensorState  # noqa: E402

fs = I["share_flagged_at_step"]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.2, 3.3))
st = [int(k) for k in fs]
a1.plot(st, [fs[str(k)] * 100 for k in st], marker="o", color=RED)
a1.set_xlabel("Step (1.4 s each)")
a1.set_ylabel("Shipments in alarm (%)")
a1.set_title("Simulator: share of 50 shipments in alarm")
s = ShipmentSensorState(3 * 97 + 13)
rows = [s.step() for _ in range(240)]
t = np.arange(240) * 1.4 / 60
a2.plot(t, [r["temperature_c"] for r in rows], color=BLUE, label="temperature (C)")
a2.axhspan(0.5, 9.5, color=G2, alpha=0.25)
a2.plot(t, [r["humidity_pct"] / 10 for r in rows], color=G, label="humidity (% / 10)")
a2.plot(t, [r["shock_g"] for r in rows], color=AMB, lw=0.8, label="shock (g)")
a2.set_xlabel("Minutes since the stream opened")
a2.set_title("Shipment #1 (order #3, seed 304): drift out of the 0.5-9.5 C band")
a2.legend(frameon=False, fontsize=7, loc="upper left")
fig.tight_layout()
save(fig, "12_iot_alarm_behaviour.png")

# 12 delivery -------------------------------------------------------------------------------------------
w = D["weights"]
tv = D["term_variation_across_buyers"]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.0, 3.0))
a1.bar([k.replace("_", "\n") for k in w], list(w.values()), color=G)
a1.set_title("Scoring weights (sum 1.00)")
a2.bar([k.replace("_", "\n") for k in tv], list(tv.values()), color=AMB)
a2.set_title("What actually separates buyers\n(SD of weighted term)")
fig.tight_layout()
save(fig, "13_delivery_weights.png")

# 13 latency --------------------------------------------------------------------------------------------
ks = ["health", "marketplace_listings", "admin_overview", "price_predict", "delivery_recommend", "admin_model_insights", "upload_and_grade", "login"]
lbl = ["health", "marketplace\nlistings", "admin\noverview", "price\npredict", "delivery\nrecommend", "model\ninsights", "upload +\ngrade", "login\n(bcrypt)"]
fig, ax = plt.subplots(figsize=(8.0, 3.2))
x = np.arange(len(ks))
ax.bar(x - 0.2, [A[k]["median_ms"] for k in ks], 0.38, color=G, label="median")
ax.bar(x + 0.2, [A[k]["p95_ms"] for k in ks], 0.38, color=AMB, label="95th percentile")
ax.set_xticks(x, lbl, fontsize=7.5)
ax.set_ylabel("Milliseconds")
ax.set_title("API response times (live server, 127.0.0.1)")
ax.legend(frameon=False)
save(fig, "14_api_latency.png")
