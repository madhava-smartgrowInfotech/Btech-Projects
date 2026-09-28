"""Train the symptom -> condition model used for triage.

Input: multi-hot vector over the symptom vocabulary. Patients rarely report every symptom,
so training rows are augmented with random symptom subsets (seeded). Evaluation uses
held-out symptom combinations with only 3 reported symptoms.
Saves models/triage_model.joblib and experiments/triage_metrics.json.
"""
import json
import random

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, top_k_accuracy_score

from common import EXPERIMENTS, MODELS, load_severity_weights, load_symptom_rows

SEED = 42
AUG_PER_ROW = 20


def vectorize(sym_lists, vocab_idx):
    X = np.zeros((len(sym_lists), len(vocab_idx)), dtype=np.float32)
    for i, syms in enumerate(sym_lists):
        for s in syms:
            if s in vocab_idx:
                X[i, vocab_idx[s]] = 1
    return X


def augment(rows, rng, per_row, min_k=2):
    out = []
    for disease, syms in rows:
        out.append((disease, syms))
        for _ in range(per_row):
            k = rng.randint(min(min_k, len(syms)), len(syms))
            out.append((disease, rng.sample(syms, k)))
    return out


def main():
    rng = random.Random(SEED)
    weights = load_severity_weights()
    rows = load_symptom_rows()
    vocab = sorted(set(weights) | {s for _, syms in rows for s in syms})
    vocab_idx = {s: i for i, s in enumerate(vocab)}
    diseases = sorted({d for d, _ in rows})

    # de-duplicate symptom sets, then split unique combinations 80/20
    uniq = sorted({(d, tuple(s)) for d, s in rows})
    rng.shuffle(uniq)
    cut = int(len(uniq) * 0.8)
    train = [(d, list(s)) for d, s in uniq[:cut]]
    test = [(d, list(s)) for d, s in uniq[cut:]]

    train_aug = augment(train, rng, AUG_PER_ROW)
    Xtr = vectorize([s for _, s in train_aug], vocab_idx)
    ytr = [d for d, _ in train_aug]
    model = LogisticRegression(max_iter=2000, C=2.0)
    model.fit(Xtr, ytr)

    # evaluation: full symptom sets and partial (3 reported symptoms)
    def evaluate(cases):
        X = vectorize([s for _, s in cases], vocab_idx)
        y = [d for d, _ in cases]
        proba = model.predict_proba(X)
        pred = model.classes_[proba.argmax(1)]
        return {
            "n": len(cases),
            "top1_accuracy": round(accuracy_score(y, pred), 4),
            "top3_accuracy": round(top_k_accuracy_score(y, proba, k=3, labels=model.classes_), 4),
            "macro_f1": round(f1_score(y, pred, average="macro"), 4),
        }

    partial = [(d, rng.sample(s, min(3, len(s)))) for d, s in test for _ in range(5)]
    metrics = {
        "model": "LogisticRegression (multinomial) on multi-hot symptoms",
        "n_symptoms": len(vocab), "n_conditions": len(diseases),
        "unique_train_combinations": len(train), "unique_test_combinations": len(test),
        "augmented_train_rows": len(train_aug),
        "test_full_symptoms": evaluate(test),
        "test_3_symptoms": evaluate(partial),
    }
    # refit on all unique combinations for the served model
    all_aug = augment([(d, list(s)) for d, s in uniq], rng, AUG_PER_ROW)
    model.fit(vectorize([s for _, s in all_aug], vocab_idx), [d for d, _ in all_aug])

    MODELS.mkdir(exist_ok=True)
    EXPERIMENTS.mkdir(exist_ok=True)
    joblib.dump({"model": model, "vocab": vocab}, MODELS / "triage_model.joblib")
    (EXPERIMENTS / "triage_metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
