"""Real-data experiments for the PCA + Firefly + MSVM pipeline on LIAR2.

Run with the project .venv (scikit-learn 1.9):
    .venv\\Scripts\\python scripts\\run_experiments.py --seed 42

Uses the product's own FakeNewsMSVMPipeline (src/), trained on a stratified subsample of the LIAR2
training split, and scores on the official validation and test splits. Writes
experiments/liar2/seed_<seed>.json (+ predictions for seed 42) and models/liar2_msvm_model.pkl (seed 42).
LIAR2 labels: 0 pants-on-fire, 1 false, 2 barely-true, 3 half-true, 4 mostly-true, 5 true -> the
project's 3-class map (true/mostly-true = REAL, half-true = PARTIALLY TRUE, the rest = FAKE).
"""
import argparse
import json
import os
import sys
import time
import warnings

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import ComplementNB
from sklearn.svm import LinearSVC, SVC

warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src.firefly import FireflyOptimizer  # noqa: E402
from src.pipeline import FakeNewsMSVMPipeline  # noqa: E402
from src.preprocessing import LABELS  # noqa: E402

DATA = os.path.join(ROOT, "data", "liar2")
OUT = os.path.join(ROOT, "experiments", "liar2")


def to3(lbl):
    lbl = np.asarray(lbl)
    return np.where(np.isin(lbl, [4, 5]), 0, np.where(lbl == 3, 1, 2))


def load(split):
    df = pd.read_csv(os.path.join(DATA, split + ".csv"))
    return df["statement"].fillna("").astype(str).tolist(), to3(df["label"].values), df


def score(y, pred):
    rep = classification_report(y, pred, target_names=LABELS, output_dict=True, zero_division=0)
    return {"accuracy": float(accuracy_score(y, pred)), "f1_macro": float(f1_score(y, pred, average="macro")),
            "f1_weighted": float(f1_score(y, pred, average="weighted")),
            "per_class": {k: {m: float(rep[k][m]) for m in ("precision", "recall", "f1-score", "support")} for k in LABELS},
            "confusion_matrix": confusion_matrix(y, pred, labels=[0, 1, 2]).tolist()}


class CountingFirefly(FireflyOptimizer):
    n_evals = 0

    def _fitness(self, vec, X, y):
        self.n_evals += 1
        return super()._fitness(vec, X, y)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n-train", type=int, default=3000)
    ap.add_argument("--fireflies", type=int, default=10)
    ap.add_argument("--generations", type=int, default=12)
    ap.add_argument("--max-tfidf", type=int, default=4000)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    tr_t, tr_y, _ = load("train")
    va_t, va_y, _ = load("valid")
    te_t, te_y, te_df = load("test")
    sub, _ = train_test_split(np.arange(len(tr_t)), train_size=a.n_train, stratify=tr_y, random_state=a.seed)
    s_t = [tr_t[i] for i in sub]
    s_y = tr_y[sub]
    res = {"seed": a.seed, "n_train_subsample": int(len(sub)), "n_train_full": len(tr_t), "n_valid": len(va_t),
           "n_test": len(te_t), "train_class_counts": np.bincount(s_y, minlength=3).tolist(),
           "test_class_counts": np.bincount(te_y, minlength=3).tolist(),
           "settings": {"fireflies": a.fireflies, "generations": a.generations, "max_tfidf": a.max_tfidf}}

    # ---- proposed pipeline (product code path)
    pipe = FakeNewsMSVMPipeline(max_tfidf=a.max_tfidf, n_fireflies=a.fireflies, n_generations=a.generations,
                                random_state=a.seed)
    opt_cls = CountingFirefly

    import src.pipeline as sp
    sp.FireflyOptimizer = opt_cls
    t0 = time.time()
    pipe.fit(s_t, s_y, verbose=False)
    res["train_time_s"] = time.time() - t0
    st = pipe.stats_
    res["n_firefly_evals"] = int(pipe.optimizer.n_evals)
    res["pipeline"] = {k: st[k] for k in ("n_tfidf", "n_total_features", "n_pca", "pca_variance", "n_selected", "best_C",
                                          "best_gamma", "firefly_history", "accuracy", "f1_macro", "baseline_accuracy",
                                          "baseline_f1", "baseline_time_s")}
    res["internal_holdout"] = {"accuracy": st["accuracy"], "f1_macro": st["f1_macro"]}
    t1 = time.time()
    ids_te, proba_te = pipe.predict(te_t)
    res["predict_time_test_s"] = time.time() - t1
    ids_va, _ = pipe.predict(va_t)
    res["proposed"] = {"valid": score(va_y, ids_va), "test": score(te_y, ids_te)}

    # ---- baseline: PCA + default RBF SVC on the same PCA space and the same train split
    X_all = pipe.transform(s_t)
    Xtr, _, ytr, _ = train_test_split(X_all, s_y, test_size=0.2, stratify=s_y, random_state=a.seed)
    Xte = pipe.transform(te_t)
    Xva = pipe.transform(va_t)
    base = SVC(class_weight="balanced", decision_function_shape="ovr", random_state=a.seed).fit(Xtr, ytr)
    res["pca_svc_default"] = {"valid": score(va_y, base.predict(Xva)), "test": score(te_y, base.predict(Xte))}

    # ---- PCA + SVC, Firefly mask only (default C/gamma): isolates feature selection
    mask = pipe.optimizer.best_mask_
    m_only = SVC(class_weight="balanced", random_state=a.seed).fit(Xtr[:, mask], ytr)
    res["pca_svc_mask_only"] = {"test": score(te_y, m_only.predict(Xte[:, mask]))}

    # ---- equal-budget random search with the same fitness function
    rs = FireflyOptimizer(n_fireflies=a.fireflies, n_generations=a.generations, random_state=a.seed)
    rng = np.random.default_rng(a.seed + 1)
    nf = Xtr.shape[1]
    best, best_vec = -1, None
    t2 = time.time()
    for _ in range(res["n_firefly_evals"]):
        v = rng.uniform(-1, 1, size=nf + 2)
        v[nf] = rng.uniform(-1, 3)
        v[nf + 1] = rng.uniform(-4, 1)
        f = rs._fitness(v, Xtr, ytr)
        if f > best:
            best, best_vec = f, v.copy()
    m_r, C_r, g_r = rs._decode(best_vec, nf)
    rsvc = SVC(C=C_r, gamma=g_r, class_weight="balanced", random_state=a.seed).fit(Xtr[:, m_r], ytr)
    res["random_search"] = {"fitness": float(best), "n_selected": int(m_r.sum()), "C": float(C_r), "gamma": float(g_r),
                            "search_time_s": time.time() - t2, "test": score(te_y, rsvc.predict(Xte[:, m_r]))}
    res["firefly_fitness_best"] = float(pipe.optimizer.best_score_)

    # ---- reference classifiers on raw TF-IDF (subsample and full training split)
    def refs(texts, y, tag):
        vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=2, max_df=0.9, max_features=20000)
        A = vec.fit_transform(texts)
        Bt = vec.transform(te_t)
        out = {}
        for name, clf in (("LinearSVC", LinearSVC(class_weight="balanced", random_state=a.seed)),
                          ("LogisticRegression", LogisticRegression(class_weight="balanced", max_iter=2000)),
                          ("ComplementNB", ComplementNB())):
            t = time.time()
            clf.fit(A, y)
            out[name] = {"test": score(te_y, clf.predict(Bt)), "train_time_s": time.time() - t}
        res["ref_" + tag] = out

    refs(s_t, s_y, "subsample")
    refs(tr_t, tr_y, "full")
    maj = np.full(len(te_y), np.bincount(tr_y).argmax())
    res["majority"] = score(te_y, maj)

    # ---- shipped synthetic-demo model on real LIAR2 statements (seed-independent, run once)
    if a.seed == 42:
        demo_path = os.path.join(ROOT, "models", "msvm_model.pkl")
        demo = FakeNewsMSVMPipeline.load(demo_path)
        d_ids, _ = demo.predict(te_t)
        res["demo_model_on_liar2_test"] = score(te_y, d_ids)
        res["demo_model_prediction_counts"] = np.bincount(d_ids, minlength=3).tolist()
        pipe.save(os.path.join(ROOT, "models", "liar2_msvm_model.pkl"))
        pd.DataFrame({"statement": te_t, "true": [LABELS[i] for i in te_y], "pred": [LABELS[int(i)] for i in ids_te],
                      "p_real": proba_te[:, 0].round(4), "p_partial": proba_te[:, 1].round(4),
                      "p_fake": proba_te[:, 2].round(4), "orig_label": te_df["label"].values}
                     ).to_csv(os.path.join(OUT, "test_predictions_seed42.csv"), index=False)

    with open(os.path.join(OUT, f"seed_{a.seed}.json"), "w") as f:
        json.dump(res, f, indent=2)
    p = res["proposed"]["test"]
    print(f"seed {a.seed}: test acc={p['accuracy']:.4f} f1m={p['f1_macro']:.4f} "
          f"pcaSVC f1m={res['pca_svc_default']['test']['f1_macro']:.4f} "
          f"rand f1m={res['random_search']['test']['f1_macro']:.4f} train={res['train_time_s']:.0f}s")


if __name__ == "__main__":
    main()
