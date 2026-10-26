"""Clause-classification experiments on the cached Gemini embeddings (no API calls).

    venv\\Scripts\\python.exe scripts\\exp_embed_cache.py        (once; needs the API key)
    venv\\Scripts\\python.exe scripts\\exp_classification.py

1. Runs the unmodified ml/eval.py with the embedding call replaced by the cached vectors, so
   experiments/eval/metrics.json holds exactly what the shipped evaluation code computes.
2. Extra checks the shipped evaluation does not make: contract-disjoint scoring, exact-duplicate leakage,
   accuracy by confidence, tie-break trigger rate, baselines (TF-IDF + logistic regression, kNN, logistic
   regression on the embeddings), per-category scores and the confusion matrix.
Writes experiments/classification/metrics.json and confusion.csv.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
OUT = ROOT / "experiments" / "classification"

from app.services import gemini_client  # noqa: E402

TRAIN = json.loads((ROOT / "data/sample/cuad_train_examples.json").read_text(encoding="utf-8"))
CATS = TRAIN["categories"]
TRAIN_ITEMS = [(c, t) for c in CATS for t in TRAIN["examples"][c]]
EVAL = json.loads((ROOT / "data/sample/cuad_eval_set.json").read_text(encoding="utf-8"))
Z = np.load(OUT / "embeddings.npz")
XT, XE = Z["train"], Z["eval"]
assert len(XT) == len(TRAIN_ITEMS) and len(XE) == len(EVAL), (len(XT), len(XE))
YT = np.array([CATS.index(c) for c, _ in TRAIN_ITEMS])
YE = np.array([CATS.index(x["label"]) for x in EVAL])


def unit(a):
    return a / np.linalg.norm(a, axis=-1, keepdims=True)


def sims_to(Xq, C):
    return unit(Xq) @ unit(C).T


def centroids(X, y, exclude=None):
    return np.vstack([X[(y == k) & (exclude if exclude is not None else True)].mean(axis=0) for k in range(len(CATS))])


def run_shipped_eval():
    """ml/eval.py exactly as shipped, with embed_text answered from the cache."""
    lookup = {x["text"]: XE[i] for i, x in enumerate(EVAL)}
    gemini_client.embed_text = lambda text, task_type="RETRIEVAL_DOCUMENT": lookup[text].tolist()
    spec = importlib.util.spec_from_file_location("clauseguard_eval", ROOT / "ml" / "eval.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.main()
    return json.loads((ROOT / "experiments/eval/metrics.json").read_text(encoding="utf-8"))["cuad_classification"]


def doc_map():
    """text -> set of CUAD contracts the span comes from (same normalisation as scripts/build_cuad_samples.py)."""
    m = defaultdict(set)
    for doc in json.loads((ROOT / "data/cuad/CUADv1.json").read_text(encoding="utf-8"))["data"]:
        for para in doc["paragraphs"]:
            for qa in para["qas"]:
                for ans in qa.get("answers", []):
                    m[" ".join(ans["text"].strip().replace("\n", " ").split())].add(doc["title"])
    return m


def acc(pred, y):
    return round(float((pred == y).mean()), 3)


def main():
    shipped = run_shipped_eval()
    res = {"shipped_eval": shipped}

    S = sims_to(XE, centroids(XT, YT))
    order = np.argsort(-S, axis=1)
    top1, top2 = S[np.arange(len(S)), order[:, 0]], S[np.arange(len(S)), order[:, 1]]
    pred = order[:, 0]
    res["centroid"] = {"top1": acc(pred, YE), "top3": round(float(np.mean([YE[i] in order[i, :3] for i in range(len(YE))])), 3), "top5": round(float(np.mean([YE[i] in order[i, :5] for i in range(len(YE))])), 3)}

    # --- leakage: exact duplicate texts across train and eval
    train_texts = {t for _, t in TRAIN_ITEMS}
    dup = np.array([x["text"] in train_texts for x in EVAL])
    res["exact_duplicates_eval_in_train"] = int(dup.sum())
    res["centroid"]["top1_without_duplicates"] = acc(pred[~dup], YE[~dup])

    # --- contract-disjoint: rebuild centroids without any train example from the same contract as the eval span
    dm = doc_map()
    tr_docs = [dm.get(t, set()) for _, t in TRAIN_ITEMS]
    ev_docs = [dm.get(x["text"], set()) for x in EVAL]
    cd_pred, n_same = [], 0
    for i in range(len(EVAL)):
        mask = np.array([not (tr_docs[j] & ev_docs[i]) for j in range(len(TRAIN_ITEMS))])
        n_same += int((~mask).sum() > 0)
        s = sims_to(XE[i:i + 1], centroids(XT, YT, exclude=mask))[0]
        cd_pred.append(int(np.argmax(s)))
    cd_pred = np.array(cd_pred)
    res["contract_disjoint"] = {"eval_items_whose_contract_also_in_train": n_same, "top1": acc(cd_pred, YE)}

    # --- accuracy by confidence band, tie-break trigger (gap<0.03 and top1<0.60) and Unclassified (<0.35) rates
    bands = [(0, 0.55), (0.55, 0.60), (0.60, 0.65), (0.65, 0.70), (0.70, 1.01)]
    res["by_confidence"] = [{"band": f"{lo:.2f}-{min(hi, 1):.2f}", "n": int(((top1 >= lo) & (top1 < hi)).sum()),
                             "top1": acc(pred[(top1 >= lo) & (top1 < hi)], YE[(top1 >= lo) & (top1 < hi)]) if ((top1 >= lo) & (top1 < hi)).any() else None}
                            for lo, hi in bands]
    tie = (top1 - top2 < 0.03) & (top1 < 0.60)
    res["tie_break"] = {"trigger_rate": round(float(tie.mean()), 3), "n_triggered": int(tie.sum()),
                        "embedding_top1_on_triggered": acc(pred[tie], YE[tie]) if tie.any() else None,
                        "top3_on_triggered": round(float(np.mean([YE[i] in order[i, :3] for i in np.where(tie)[0]])), 3) if tie.any() else None,
                        "unclassified_rate_below_0.35": round(float((top1 < 0.35).mean()), 3),
                        "confidence_min_median_max": [round(float(top1.min()), 3), round(float(np.median(top1)), 3), round(float(top1.max()), 3)]}

    # --- baselines on the same split
    tf = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=2, stop_words="english")
    Tt = tf.fit_transform([t for _, t in TRAIN_ITEMS])
    Te = tf.transform([x["text"] for x in EVAL])
    lr_tf = LogisticRegression(max_iter=2000, C=10).fit(Tt, YT)
    lr_emb = LogisticRegression(max_iter=3000, C=10).fit(unit(XT), YT)
    knn = {}
    SS = sims_to(XE, XT)
    for k in (1, 5):
        idx = np.argsort(-SS, axis=1)[:, :k]
        knn[k] = np.array([Counter(YT[row]).most_common(1)[0][0] for row in idx])
    cent_tfidf = np.vstack([np.asarray(Tt[YT == k].mean(axis=0)) for k in range(len(CATS))])
    tf_cent_pred = np.argmax(np.asarray(Te @ cent_tfidf.T), axis=1)
    res["baselines_top1"] = {
        "chance (20 categories)": 0.05,
        "TF-IDF nearest centroid": acc(tf_cent_pred, YE),
        "TF-IDF + logistic regression": acc(lr_tf.predict(Te), YE),
        "Gemini embedding 1-NN": acc(knn[1], YE),
        "Gemini embedding 5-NN": acc(knn[5], YE),
        "Gemini embedding + logistic regression": acc(lr_emb.predict(unit(XE)), YE),
        "Gemini embedding nearest centroid (shipped)": res["centroid"]["top1"],
    }

    # --- per-category and confusion
    per = {}
    for k, c in enumerate(CATS):
        m = YE == k
        per[c] = {"n": int(m.sum()), "recall": acc(pred[m], YE[m]), "precision": round(float((YE[pred == k] == k).mean()), 3) if (pred == k).any() else 0.0}
    res["per_category"] = per
    conf = np.zeros((len(CATS), len(CATS)), dtype=int)
    for y, p in zip(YE, pred):
        conf[y, p] += 1
    with open(OUT / "confusion.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["true\\pred"] + CATS)
        for k, c in enumerate(CATS):
            w.writerow([c] + conf[k].tolist())
    pairs = sorted(((int(conf[a, b]), CATS[a], CATS[b]) for a in range(len(CATS)) for b in range(len(CATS)) if a != b and conf[a, b]), reverse=True)[:10]
    res["top_confusions"] = [{"count": n, "true": a, "predicted": b} for n, a, b in pairs]
    (OUT / "metrics.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k not in ("per_category", "shipped_eval")}, indent=1))


if __name__ == "__main__":
    main()
