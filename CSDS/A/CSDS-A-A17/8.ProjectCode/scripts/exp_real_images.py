"""Real-photo check of the grading pipeline on the Fresh and Rotten Fruits dataset (Sultana et al., 2022; CC BY 4.0).

The shipped classifier was trained on synthetic feature vectors. This script runs the REAL feature extractor on real fruit photographs
and asks what the shipped model does with them, and whether the 11 features carry signal when trained on real labels.

    venv\\Scripts\\python scripts/exp_real_images.py     -> experiments/real_images/metrics.json (+ C:/cs17/data/real_features.csv)
"""
from __future__ import annotations

import io
import sys
import time

import numpy as np
import pandas as pd

from exp_common import DATA, save

import pyarrow.parquet as pq
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import GroupKFold, StratifiedKFold, cross_val_predict, cross_val_score

from app.ml.quality.feature_extraction import FEATURE_NAMES, extract_features
from app.ml.quality.infer import load_artifact

FEATS = DATA / "real_features.csv"
LIMIT_PER_CELL = int(sys.argv[1]) if len(sys.argv) > 1 else 10_000  # cap per (fruit, label)


def extract_all():
    art = load_artifact()
    model = art["model"]
    classes = list(model.classes_)
    rows = []
    counts: dict = {}
    t0 = time.time()
    for shard in sorted(DATA.glob("raw_*.parquet")):
        pf = pq.ParquetFile(shard)
        for batch in pf.iter_batches(batch_size=32):
            d = batch.to_pydict()
            for img, lab, fruit in zip(d["image"], d["label"], d["fruit_type"]):
                key = (fruit, lab)
                if counts.get(key, 0) >= LIMIT_PER_CELL:
                    continue
                counts[key] = counts.get(key, 0) + 1
                f = extract_features(img["bytes"])
                vec = np.array([[f[n] for n in FEATURE_NAMES]])
                p = model.predict_proba(vec)[0]
                row = {"fruit": fruit, "label": "fresh" if lab == 0 else "rotten", **f, "pred": classes[int(np.argmax(p))]}
                row.update({f"p_{c}": float(x) for c, x in zip(classes, p)})
                rows.append(row)
            if len(rows) % 320 < 32:
                print(len(rows), "images", round(time.time() - t0), "s", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(FEATS, index=False)
    return df


def main():
    t0 = time.time()
    df = pd.read_csv(FEATS) if FEATS.exists() and "--reuse" in sys.argv else extract_all()
    classes = ["A", "B", "C", "Reject"]
    out = {"dataset": {
        "name": "Fresh and Rotten Fruits Dataset for Machine-Based Evaluation of Fruit Quality", "authors": "Sultana, Jahan, Uddin (2022), Data in Brief 44:108552, Mendeley Data doi:10.17632/bdd69gyhv8.1",
        "licence": "CC BY 4.0", "obtained_from": "Hugging Face mirror Project-AgML/fresh_rotten_fruit_classification (raw config)",
        "images_used": int(len(df)), "fresh": int((df.label == "fresh").sum()), "rotten": int((df.label == "rotten").sum()),
        "fruits": sorted(df.fruit.unique().tolist()), "per_fruit_counts": df.groupby(["fruit", "label"]).size().unstack(fill_value=0).to_dict(orient="index"),
        "caveat": "fresh/rotten is a binary freshness label, not the A/B/C/Reject grade; mapping fresh->{A,B} and rotten->{C,Reject} is an assumption of this check",
    }}

    # ---- what the shipped (synthetic-trained) model says
    dist = {lab: {c: float((df[df.label == lab].pred == c).mean()) for c in classes} for lab in ("fresh", "rotten")}
    df["accept"] = df.pred.isin(["A", "B"]).astype(int)
    df["fresh_bin"] = (df.label == "fresh").astype(int)
    df["score"] = df["p_A"] + df["p_B"]
    df["score_ab_minus_cr"] = (df["p_A"] + df["p_B"]) - (df["p_C"] + df["p_Reject"])
    acc_map = accuracy_score(df.fresh_bin, df.accept)
    out["shipped_model_on_real_photos"] = {
        "predicted_grade_share_by_label": dist,
        "mapped_binary_accuracy": acc_map,
        "mapped_binary_f1_fresh": f1_score(df.fresh_bin, df.accept),
        "auc_fresh_vs_rotten_using_pA_plus_pB": float(roc_auc_score(df.fresh_bin, df.score)),
        "share_predicted_A_overall": float((df.pred == "A").mean()),
        "share_predicted_Reject_overall": float((df.pred == "Reject").mean()),
        "mean_top_probability": float(df[[f"p_{c}" for c in classes]].max(axis=1).mean()),
    }
    per_fruit = {}
    for fruit, g in df.groupby("fruit"):
        per_fruit[fruit] = {"n": int(len(g)), "mapped_accuracy": float(accuracy_score(g.fresh_bin, g.accept)),
                            "auc": float(roc_auc_score(g.fresh_bin, g.score)) if g.fresh_bin.nunique() == 2 else None,
                            "accepted_share_fresh": float(g[g.fresh_bin == 1].accept.mean()), "accepted_share_rotten": float(g[g.fresh_bin == 0].accept.mean())}
    out["shipped_model_per_fruit"] = per_fruit

    # ---- do the 11 features carry signal when trained on REAL labels?  (5-fold CV, stratified; also grouped by fruit)
    X = df[FEATURE_NAMES].values
    y = df.fresh_bin.values
    rf = RandomForestClassifier(n_estimators=250, max_depth=9, min_samples_leaf=4, random_state=42, n_jobs=-1)
    skf = StratifiedKFold(5, shuffle=True, random_state=42)
    cv_acc = cross_val_score(rf, X, y, cv=skf, scoring="accuracy")
    cv_auc = cross_val_score(rf, X, y, cv=skf, scoring="roc_auc")
    groups = df.fruit.values
    gcv = GroupKFold(n_splits=min(4, len(set(groups))))
    g_acc = cross_val_score(rf, X, y, cv=gcv, groups=groups, scoring="accuracy")
    g_auc = cross_val_score(rf, X, y, cv=gcv, groups=groups, scoring="roc_auc")
    rf.fit(X, y)
    out["features_trained_on_real_labels"] = {
        "five_fold_cv_accuracy_mean": float(cv_acc.mean()), "five_fold_cv_accuracy_std": float(cv_acc.std(ddof=1)),
        "five_fold_cv_auc_mean": float(cv_auc.mean()),
        "leave_fruits_out_accuracy_mean": float(g_acc.mean()), "leave_fruits_out_auc_mean": float(g_auc.mean()), "leave_fruits_out_folds": int(len(g_acc)),
        "importance": sorted([{"feature": f, "importance": float(v)} for f, v in zip(FEATURE_NAMES, rf.feature_importances_)], key=lambda r: -r["importance"]),
        "majority_baseline": float(max(y.mean(), 1 - y.mean())),
    }

    # ---- feature means: real fresh / rotten vs the synthetic grade profiles (domain gap)
    from app.ml.quality.generate_dataset import PROFILES
    gap = {}
    for f in FEATURE_NAMES:
        gap[f] = {"real_fresh": float(df[df.label == "fresh"][f].mean()), "real_rotten": float(df[df.label == "rotten"][f].mean()),
                  "synthetic_A": PROFILES["A"][f][0], "synthetic_B": PROFILES["B"][f][0], "synthetic_C": PROFILES["C"][f][0], "synthetic_Reject": PROFILES["Reject"][f][0],
                  "real_fresh_std": float(df[df.label == "fresh"][f].std()), "real_rotten_std": float(df[df.label == "rotten"][f].std())}
    out["feature_means_real_vs_synthetic"] = gap
    # how many real images fall outside the synthetic grade envelope for at least one feature (> 3 sd of every grade)
    outside = 0
    for _, r in df.iterrows():
        ok = False
        for g in classes:
            if all(abs(r[f] - PROFILES[g][f][0]) <= 3 * PROFILES[g][f][1] for f in FEATURE_NAMES):
                ok = True
                break
        outside += 0 if ok else 1
    out["share_real_images_outside_every_synthetic_profile_3sd"] = outside / len(df)
    out["runtime_seconds"] = round(time.time() - t0, 1)
    save("real_images", out)
    print(out["shipped_model_on_real_photos"])
    print(out["features_trained_on_real_labels"]["five_fold_cv_accuracy_mean"])


if __name__ == "__main__":
    main()
