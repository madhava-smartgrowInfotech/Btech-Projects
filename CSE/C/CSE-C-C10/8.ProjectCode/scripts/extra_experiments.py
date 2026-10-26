"""Extra real-data studies for the documentation run (leakage ablation, retrieval-only classifier, per-industry errors).

    .venv\\Scripts\\python.exe scripts\\extra_experiments.py

Reuses the loader of scripts/run_experiments.py (922 real rows, structured features only). Writes evaluation/extra_results.json.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from sklearn.compose import ColumnTransformer  # noqa: E402
from sklearn.model_selection import StratifiedShuffleSplit  # noqa: E402
from sklearn.metrics.pairwise import cosine_similarity  # noqa: E402

from app.config import BINARY_FEATURES, CATEGORICAL_FEATURES, N_SPLITS, NUMERIC_FEATURES, RANDOM_STATE, TEST_SIZE  # noqa: E402
from app.ml.embeddings import l2norm  # noqa: E402
from app.ml.preprocessing import build_preprocessor  # noqa: E402
from run_experiments import agg, load_real, model_zoo, proba_of, score  # noqa: E402

OUT = ROOT / "evaluation" / "extra_results.json"
POSTHOC = ["relationships", "milestones", "age_first_milestone_year", "age_last_milestone_year"]  # recorded around/after the outcome


def build_pre(drop):
    import app.config as cfg
    import app.ml.preprocessing as pp
    num = [c for c in NUMERIC_FEATURES if c not in drop]
    pp.NUMERIC_FEATURES = num
    pre = build_preprocessor()
    pp.NUMERIC_FEATURES = NUMERIC_FEATURES
    return pre


def run_models(df, drop, names):
    y = df["label"].to_numpy()
    sss = StratifiedShuffleSplit(n_splits=N_SPLITS, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    rows = {n: [] for n in names}
    for tr, te in sss.split(df, y):
        pre = build_pre(drop)
        Xtr = pre.fit_transform(df.iloc[tr])
        Xte = pre.transform(df.iloc[te])
        zoo = model_zoo()
        for n in names:
            m = zoo[n]
            m.fit(Xtr, y[tr])
            p = proba_of(m, Xte)
            rows[n].append(score(y[te], (p >= 0.5).astype(int), p))
    return {n: agg(r) for n, r in rows.items()}


def retrieval_only(df, ks=(10, 20, 30, 50)):
    """Balanced top-k cosine retrieval on the structured representation only (no text exists in the real table)."""
    y = df["label"].to_numpy()
    sss = StratifiedShuffleSplit(n_splits=N_SPLITS, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    res = {k: [] for k in ks}
    for tr, te in sss.split(df, y):
        pre = build_preprocessor()
        Xtr = pre.fit_transform(df.iloc[tr])
        Xte = pre.transform(df.iloc[te])
        Xtr = Xtr.toarray() if hasattr(Xtr, "toarray") else np.asarray(Xtr)
        Xte = Xte.toarray() if hasattr(Xte, "toarray") else np.asarray(Xte)
        Xtr, Xte = l2norm(Xtr.astype(np.float32)), l2norm(Xte.astype(np.float32))
        S = cosine_similarity(Xte, Xtr)
        ytr = y[tr]
        for k in ks:
            probs = []
            for i in range(len(te)):
                order = np.argsort(-S[i])
                qs, qf = k // 2, k - k // 2
                pick, cs, cf = [], 0, 0
                for j in order:
                    if ytr[j] == 1 and cs < qs:
                        pick.append(j); cs += 1
                    elif ytr[j] == 0 and cf < qf:
                        pick.append(j); cf += 1
                    if len(pick) >= k:
                        break
                sims = S[i, pick]
                probs.append(float((sims * ytr[pick]).sum() / max(sims.sum(), 1e-9)))
            p = np.array(probs)
            # balanced retrieval has a 50 % success prior; the decision threshold is therefore 0.5
            res[k].append(score(y[te], (p >= 0.5).astype(int), p))
    return {str(k): agg(r) for k, r in res.items()}


def per_industry(df):
    y = df["label"].to_numpy()
    sss = StratifiedShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    tr, te = next(sss.split(df, y))
    pre = build_preprocessor()
    Xtr, Xte = pre.fit_transform(df.iloc[tr]), pre.transform(df.iloc[te])
    m = model_zoo()["Random Forest"]
    m.fit(Xtr, y[tr])
    pred = m.predict(Xte)
    out = {}
    ind = df.iloc[te]["industry_type"].to_numpy()
    for g in sorted(set(ind)):
        mask = ind == g
        if mask.sum() >= 5:
            out[g] = {"n": int(mask.sum()), "accuracy": float((pred[mask] == y[te][mask]).mean()),
                      "success_share": float(y[te][mask].mean())}
    return out


def main():
    t0 = time.time()
    df = load_real()
    res = {"posthoc_features_dropped": POSTHOC}
    res["with_all_features"] = run_models(df, [], ["Logistic Regression", "Random Forest", "XGBoost"])
    res["without_posthoc_features"] = run_models(df, POSTHOC, ["Logistic Regression", "Random Forest", "XGBoost"])
    res["retrieval_only_structured"] = retrieval_only(df)
    res["per_industry_rf_seed42_split"] = per_industry(df)
    res["runtime_seconds"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(res, indent=2), encoding="utf-8")
    print("wrote", OUT, res["runtime_seconds"], "s")
    for k in ("with_all_features", "without_posthoc_features"):
        for n, v in res[k].items():
            print(k, n, round(v["balanced_accuracy"]["mean"], 3), round(v["roc_auc"]["mean"], 3))
    for k, v in res["retrieval_only_structured"].items():
        print("retrieval k", k, round(v["balanced_accuracy"]["mean"], 3), round(v["roc_auc"]["mean"], 3))


if __name__ == "__main__":
    main()
