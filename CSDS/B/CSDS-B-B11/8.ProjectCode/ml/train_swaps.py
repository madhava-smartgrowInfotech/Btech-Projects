"""Train the K-Means swap model on dish nutrient profiles.

Features (per dish, portion-independent): protein/carb/fat energy shares, fibre and sugar per 100 kcal,
log sodium per 100 kcal and log energy density. k is chosen by silhouette score over a small grid.

Outputs  models/swap_kmeans.joblib   {scaler, kmeans, features, k}
         experiments/metrics.json    training metrics + swap-quality check
Runs on CPU in a few seconds; seeded for repeatability.
"""
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "4")

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.foods import FEATURES, PLAN_ROLES, feature_frame  # noqa: E402

SEED = 42
K_GRID = list(range(6, 31, 2))


def main():
    t0 = time.time()
    df = pd.read_csv(ROOT / "data" / "processed" / "foods.csv")
    X = feature_frame(df)[FEATURES].values
    scaler = StandardScaler().fit(X)
    Xs = scaler.transform(X)

    grid = []
    for k in K_GRID:
        km = KMeans(n_clusters=k, n_init=10, random_state=SEED).fit(Xs)
        grid.append({"k": k, "inertia": round(float(km.inertia_), 2),
                     "silhouette": round(float(silhouette_score(Xs, km.labels_)), 4)})
    # prefer the best silhouette among k >= 10 so clusters stay small enough to give specific swaps
    best = max((g for g in grid if g["k"] >= 10), key=lambda g: g["silhouette"])
    k = best["k"]
    km = KMeans(n_clusters=k, n_init=20, random_state=SEED).fit(Xs)
    labels = km.labels_

    # swap-quality check: for every plan dish, nearest same-role same-cluster neighbour
    df["cluster"] = labels
    feats = feature_frame(df)
    kcal_err, macro_dist, found = [], [], 0
    plan = df[df["role"].isin(PLAN_ROLES)]
    for i, r in plan.iterrows():
        cands = plan[(plan["role"] == r["role"]) & (plan["cluster"] == r["cluster"]) & (plan.index != i)]
        if cands.empty:
            continue
        found += 1
        d = np.linalg.norm(Xs[cands.index] - Xs[i], axis=1)
        j = cands.index[int(np.argmin(d))]
        shares_a = feats.loc[i, ["p_share", "c_share", "f_share"]].values
        shares_b = feats.loc[j, ["p_share", "c_share", "f_share"]].values
        macro_dist.append(float(np.abs(shares_a - shares_b).sum() / 2))  # 0 = identical macro split
        # portion is rescaled to match calories, so remaining error comes only from rounding to 5 g
        grams = r["serving_g"]
        target = r["kcal"] * grams / 100
        g2 = min(max(target / max(df.loc[j, "kcal"], 1) * 100, 0.5 * df.loc[j, "serving_g"]), 2 * df.loc[j, "serving_g"])
        g2 = 5 * round(g2 / 5)
        kcal_err.append(abs(df.loc[j, "kcal"] * g2 / 100 - target) / max(target, 1))

    metrics = {
        "model": "KMeans",
        "features": FEATURES,
        "n_dishes": int(len(df)),
        "k_grid": grid,
        "chosen_k": k,
        "silhouette": round(float(silhouette_score(Xs, labels)), 4),
        "davies_bouldin": round(float(davies_bouldin_score(Xs, labels)), 4),
        "calinski_harabasz": round(float(calinski_harabasz_score(Xs, labels)), 2),
        "cluster_sizes": {int(c): int(n) for c, n in zip(*np.unique(labels, return_counts=True))},
        "swap_check": {
            "plan_dishes": int(len(plan)),
            "with_same_cluster_swap_pct": round(100 * found / len(plan), 1),
            "mean_macro_split_difference_pct": round(100 * float(np.mean(macro_dist)), 2),
            "mean_kcal_error_after_portioning_pct": round(100 * float(np.mean(kcal_err)), 2),
        },
        "train_seconds": round(time.time() - t0, 2),
        "seed": SEED,
    }
    (ROOT / "models").mkdir(exist_ok=True)
    (ROOT / "experiments").mkdir(exist_ok=True)
    joblib.dump({"scaler": scaler, "kmeans": km, "features": FEATURES, "k": k}, ROOT / "models" / "swap_kmeans.joblib")
    (ROOT / "experiments" / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps({key: metrics[key] for key in ["chosen_k", "silhouette", "davies_bouldin", "swap_check", "train_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
