"""Quality-grading experiments: the shipped Random Forest, seeds, baselines, ablations, label-noise ceiling.

    venv\\Scripts\\python scripts/exp_quality.py        -> experiments/quality/metrics.json
"""
from __future__ import annotations

import time

import numpy as np
import pandas as pd

from exp_common import save

from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from app.ml.quality.feature_extraction import FEATURE_NAMES
from app.ml.quality.generate_dataset import GRADES, PROFILES, generate


def rf(seed=42):
    return RandomForestClassifier(n_estimators=250, max_depth=9, min_samples_leaf=4, random_state=seed, n_jobs=-1)


def generate_with_clean(n_per_grade=1500, seed=42):
    """Replicates generate() but keeps the clean (pre-noise) label next to the noisy one."""
    rng = np.random.default_rng(seed)
    rows = []
    for grade in GRADES:
        for _ in range(n_per_grade):
            row = {}
            for feat in FEATURE_NAMES:
                mean, std = PROFILES[grade][feat]
                row[feat] = float(np.clip(rng.normal(mean, std), 0.0, 1.0))
            row["grade_clean"] = grade
            row["grade"] = grade
            rows.append(row)
    df = pd.DataFrame(rows)
    noise_idx = rng.choice(len(df), size=int(len(df) * 0.06), replace=False)
    neighbor = {"A": "B", "B": "C", "C": "B", "Reject": "C"}
    df.loc[noise_idx, "grade"] = df.loc[noise_idx, "grade"].map(neighbor)
    return df.sample(frac=1.0, random_state=seed).reset_index(drop=True)


def main():
    t0 = time.time()
    shipped = generate()
    full = generate_with_clean()
    same = bool(np.allclose(shipped[FEATURE_NAMES].values, full[FEATURE_NAMES].values) and (shipped["grade"].values == full["grade"].values).all())
    print("replica identical to shipped generator:", same)

    X = full[FEATURE_NAMES].values
    y = full["grade"].values
    yc = full["grade_clean"].values
    idx = np.arange(len(full))
    tr, te = train_test_split(idx, test_size=0.2, random_state=42, stratify=y)
    Xtr, Xte, ytr, yte = X[tr], X[te], y[tr], y[te]

    out: dict = {
        "dataset": {
            "rows": int(len(full)), "per_grade": 1500, "classes": GRADES, "n_features": len(FEATURE_NAMES), "features": FEATURE_NAMES,
            "label_noise_fraction": 0.06, "noisy_labels_actual": int((full["grade"] != full["grade_clean"]).sum()),
            "split": "80/20 stratified, random_state=42", "train_rows": int(len(tr)), "test_rows": int(len(te)),
            "source": "synthetic: per-grade normal distributions in the CV feature space (generate_dataset.py), 6% labels moved to a neighbouring grade",
            "replica_identical_to_generate": same,
        }
    }

    # ---- shipped model (identical hyper-parameters and split to train_model.py)
    model = rf(42).fit(Xtr, ytr)
    pred = model.predict(Xte)
    acc = accuracy_score(yte, pred)
    rep = classification_report(yte, pred, output_dict=True)
    labels = list(model.classes_)
    cm = confusion_matrix(yte, pred, labels=labels)
    proba = model.predict_proba(Xte)
    conf = proba.max(1)
    correct = pred == yte
    out["shipped_rf"] = {
        "hyperparameters": {"n_estimators": 250, "max_depth": 9, "min_samples_leaf": 4, "random_state": 42},
        "test_accuracy": acc, "macro_f1": f1_score(yte, pred, average="macro"), "weighted_f1": f1_score(yte, pred, average="weighted"),
        "per_class": {k: rep[k] for k in labels}, "labels": labels, "confusion_matrix": cm.tolist(),
        "mean_confidence_correct": float(conf[correct].mean()), "mean_confidence_wrong": float(conf[~correct].mean()),
        "train_accuracy": accuracy_score(ytr, model.predict(Xtr)),
        "accuracy_vs_clean_labels_on_same_test_rows": accuracy_score(yc[te], pred),
        "test_rows_with_noisy_label": int((yte != yc[te]).sum()),
        "max_possible_accuracy_if_noise_unlearnable": float((yte == yc[te]).mean()),
        "adjacent_error_share": None,
    }
    order = {g: i for i, g in enumerate(GRADES)}
    wrong = [(a, b) for a, b in zip(yte, pred) if a != b]
    out["shipped_rf"]["adjacent_error_share"] = float(np.mean([abs(order[a] - order[b]) == 1 for a, b in wrong])) if wrong else None
    out["shipped_rf"]["errors"] = len(wrong)

    # ---- feature importance (impurity + permutation)
    imp = sorted(zip(FEATURE_NAMES, model.feature_importances_), key=lambda x: -x[1])
    perm = permutation_importance(model, Xte, yte, n_repeats=10, random_state=0, n_jobs=1)
    pi = sorted(zip(FEATURE_NAMES, perm.importances_mean, perm.importances_std), key=lambda x: -x[1])
    out["feature_importance"] = {
        "impurity": [{"feature": f, "importance": float(v)} for f, v in imp],
        "permutation_accuracy_drop": [{"feature": f, "mean": float(m), "std": float(s)} for f, m, s in pi],
    }

    # ---- seeds: different split + forest seed
    seeds = []
    for s in range(5):
        a, b = train_test_split(idx, test_size=0.2, random_state=s, stratify=y)
        m = rf(s).fit(X[a], y[a])
        p = m.predict(X[b])
        seeds.append({"seed": s, "accuracy": accuracy_score(y[b], p), "macro_f1": f1_score(y[b], p, average="macro")})
    accs = np.array([r["accuracy"] for r in seeds])
    f1s = np.array([r["macro_f1"] for r in seeds])
    out["seed_study"] = {"runs": seeds, "accuracy_mean": float(accs.mean()), "accuracy_std": float(accs.std(ddof=1)), "accuracy_min": float(accs.min()),
                         "accuracy_max": float(accs.max()), "macro_f1_mean": float(f1s.mean()), "macro_f1_std": float(f1s.std(ddof=1))}

    # ---- baselines on the shipped split
    base = {}
    models = {
        "majority_class": DummyClassifier(strategy="most_frequent"),
        "logistic_regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)),
        "decision_tree_depth9": DecisionTreeClassifier(max_depth=9, min_samples_leaf=4, random_state=42),
        "knn_k15": make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=15)),
        "hist_gradient_boosting": HistGradientBoostingClassifier(random_state=42),
        "random_forest_shipped": rf(42),
    }
    for name, m in models.items():
        m.fit(Xtr, ytr)
        p = m.predict(Xte)
        base[name] = {"accuracy": accuracy_score(yte, p), "macro_f1": f1_score(yte, p, average="macro")}
    out["baselines"] = base

    # ---- label-noise: train on clean labels, test on clean labels (separability of the profiles)
    mc = rf(42).fit(X[tr], yc[tr])
    pc = mc.predict(X[te])
    out["clean_label_reference"] = {"accuracy_trained_and_tested_on_clean_labels": accuracy_score(yc[te], pc),
                                   "macro_f1": f1_score(yc[te], pc, average="macro"),
                                   "note": "same features, labels before the 6% neighbour-grade noise was applied"}

    # ---- ablation: drop one feature group at a time
    groups = {
        "colour (hue, saturation, value, saturation_std, uniformity)": ["mean_hue", "mean_saturation", "mean_value", "saturation_std", "color_uniformity"],
        "texture (GLCM contrast, homogeneity, energy)": ["texture_contrast", "texture_homogeneity", "texture_energy"],
        "edge_density": ["edge_density"],
        "blemish_ratio": ["blemish_ratio"],
        "size_score": ["size_score"],
    }
    abl = {}
    for g, cols in groups.items():
        keep = [i for i, f in enumerate(FEATURE_NAMES) if f not in cols]
        m = rf(42).fit(Xtr[:, keep], ytr)
        p = m.predict(Xte[:, keep])
        abl[g] = {"removed": cols, "accuracy": accuracy_score(yte, p), "macro_f1": f1_score(yte, p, average="macro")}
    only = {}
    for g, cols in groups.items():
        keep = [i for i, f in enumerate(FEATURE_NAMES) if f in cols]
        m = rf(42).fit(Xtr[:, keep], ytr)
        p = m.predict(Xte[:, keep])
        only[g] = {"accuracy": accuracy_score(yte, p)}
    out["ablation_drop_group"] = abl
    out["ablation_only_group"] = only

    # ---- shipped artefact (if trained) agrees with this replica
    try:
        from app.ml.quality.train_model import train
        art = train()
        out["train_model_py"] = {"test_accuracy": float(art["test_accuracy"]), "matches_replica": abs(art["test_accuracy"] - acc) < 1e-9}
    except Exception as e:  # pragma: no cover
        out["train_model_py"] = {"error": str(e)}

    out["runtime_seconds"] = round(time.time() - t0, 1)
    save("quality", out)
    print("accuracy", acc, "seeds", out["seed_study"]["accuracy_mean"], out["seed_study"]["accuracy_std"])


if __name__ == "__main__":
    main()
