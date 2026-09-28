"""Train the resume role classifier on the Kaggle Resume Dataset (CPU, a few seconds).

TF-IDF (word 1-2 grams) + Logistic Regression over 24 job categories, stratified 80/20 split, seed 42.
Outputs:
  models/resume_clf.joblib            the fitted pipeline
  models/role_skills.json             top skills per category (used for "missing skills")
  experiments/resume_classifier/metrics.json
Run:  python ml/train_resume.py
"""
import csv
import json
import sys
import time
from collections import Counter
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score, top_k_accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.skills import extract_skills  # noqa: E402

SEED = 42
csv.field_size_limit(10**8)


def load():
    texts, labels = [], []
    with open(ROOT / "data" / "resume" / "Resume.csv", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["Resume_str"].strip():
                texts.append(r["Resume_str"])
                labels.append(r["Category"])
    return texts, labels


def role_skills(texts, labels, top=12):
    doc_skills = [set(extract_skills(t)) for t in texts]
    overall = Counter(s for d in doc_skills for s in d)
    n = len(texts)
    out = {}
    for cat in sorted(set(labels)):
        idx = [i for i, l in enumerate(labels) if l == cat]
        c = Counter(s for i in idx for s in doc_skills[i])
        scored = []
        for s, k in c.items():
            f_cat = k / len(idx)
            lift = f_cat / (overall[s] / n)
            if f_cat >= 0.12:
                scored.append((f_cat * lift, s, round(f_cat, 3)))
        scored.sort(reverse=True)
        out[cat] = [{"skill": s, "share": f} for _, s, f in scored[:top]]
    return out


def main():
    t0 = time.time()
    texts, labels = load()
    X_tr, X_te, y_tr, y_te = train_test_split(texts, labels, test_size=0.2, stratify=labels, random_state=SEED)
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=60000, sublinear_tf=True,
                                  stop_words="english")),
        ("clf", LogisticRegression(C=10, max_iter=2000, random_state=SEED)),
    ])
    pipe.fit(X_tr, y_tr)
    pred = pipe.predict(X_te)
    proba = pipe.predict_proba(X_te)
    metrics = {
        "model": "TF-IDF (1-2 gram) + LogisticRegression",
        "dataset": "Kaggle Resume Dataset (snehaanbhawal/resume-dataset)",
        "n_train": len(X_tr), "n_test": len(X_te), "n_classes": len(set(labels)), "seed": SEED,
        "accuracy": round(accuracy_score(y_te, pred), 4),
        "macro_f1": round(f1_score(y_te, pred, average="macro"), 4),
        "weighted_f1": round(f1_score(y_te, pred, average="weighted"), 4),
        "top3_accuracy": round(top_k_accuracy_score(y_te, proba, k=3, labels=pipe.classes_), 4),
        "per_class": {k: {m: round(v, 3) for m, v in d.items()} for k, d in
                      classification_report(y_te, pred, output_dict=True, zero_division=0).items()
                      if k in pipe.classes_},
        "train_seconds": round(time.time() - t0, 1),
    }
    # refit on all data for the served model
    pipe.fit(texts, labels)
    (ROOT / "models").mkdir(exist_ok=True)
    joblib.dump(pipe, ROOT / "models" / "resume_clf.joblib", compress=3)
    (ROOT / "models" / "role_skills.json").write_text(json.dumps(role_skills(texts, labels), indent=1))
    exp = ROOT / "experiments" / "resume_classifier"
    exp.mkdir(parents=True, exist_ok=True)
    (exp / "metrics.json").write_text(json.dumps(metrics, indent=1))
    print({k: v for k, v in metrics.items() if k != "per_class"})


if __name__ == "__main__":
    main()
