"""PeerScope model training: TF-IDF (word 1-2 + char 3-5) + LogisticRegression, stratified split, fixed seed."""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data" / "processed_dataset.csv"
MODELS = BASE / "models"

RANDOM_SEED = 42


class CombinedVectorizer:
    """Picklable wrapper combining word + char TF-IDF vectorizers (re-export)."""

    def __init__(self, w, c):
        from app.services.textvec import CombinedVectorizer as _C

        self._impl = _C(w, c)
        self.w, self.c = w, c

    def transform(self, texts):
        return self._impl.transform(texts)


def main() -> None:
    if not DATA.exists():
        raise SystemExit(f"Dataset not found at {DATA}. Run scripts/prepare_dataset.py first.")
    df = pd.read_csv(DATA).dropna(subset=["title", "text", "label"])
    df = df[(df["title"].str.len() > 3) & (df["text"].str.len() > 20)]
    if len(df) < 100:
        raise SystemExit("Not enough samples to train.")
    blob = (df["title"].fillna("") + " " + df["text"].fillna(""))
    le = LabelEncoder()
    y = le.fit_transform(df["label"].astype(str))
    print("Classes:", list(le.classes_), "counts:", dict(Counter(df['label'])))
    strat = y if len(set(y)) > 1 and min(Counter(y).values()) >= 2 else None
    Xtr, Xte, ytr, yte = train_test_split(blob, y, test_size=0.2, random_state=RANDOM_SEED, stratify=strat)
    wvec = TfidfVectorizer(max_features=8000, ngram_range=(1, 2), lowercase=True, stop_words="english")
    cvec = TfidfVectorizer(max_features=4000, ngram_range=(3, 5), analyzer="char_wb", lowercase=True)
    Xtr_f = hstack([wvec.fit_transform(Xtr), cvec.fit_transform(Xtr)])
    Xte_f = hstack([wvec.transform(Xte), cvec.transform(Xte)])
    clf = LogisticRegression(max_iter=1000, class_weight="balanced", C=1.0, random_state=RANDOM_SEED)
    clf.fit(Xtr_f, ytr)
    pred = clf.predict(Xte_f)
    acc = accuracy_score(yte, pred)
    prec = precision_score(yte, pred, average="macro", zero_division=0)
    rec = recall_score(yte, pred, average="macro", zero_division=0)
    f1 = f1_score(yte, pred, average="macro", zero_division=0)
    roc = None
    try:
        if len(set(yte)) > 2:
            from sklearn.preprocessing import label_binarize

            Yb = label_binarize(yte, classes=list(range(len(le.classes_))))
            P = clf.predict_proba(Xte_f)
            from sklearn.metrics import roc_auc_score as _roc

            roc = float(_roc(Yb, P, average="macro", multi_class="ovr"))
        elif len(set(yte)) == 2:
            P = clf.predict_proba(Xte_f)[:, 1]
            roc = float(roc_auc_score(yte, P))
    except Exception as exc:
        print("ROC-AUC unavailable:", exc)
    cm = confusion_matrix(yte, pred).tolist()
    MODELS.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, MODELS / "decision_model.joblib")

    joblib.dump(CombinedVectorizer(wvec, cvec), MODELS / "tfidf_vectorizer.joblib")
    # Also persist canonical importable wrapper so joblib unpickling resolves
    # via app.services.textvec regardless of training entrypoint.
    from app.services.textvec import CombinedVectorizer as Canonical

    joblib.dump(Canonical(wvec, cvec), MODELS / "tfidf_vectorizer.joblib")

    metrics = {
        "status": "ok", "model_type": "LogisticRegression(class_weight=balanced)",
        "features": "TF-IDF word(1-2, 8k) + char_wb(3-5, 4k) over title+text",
        "accuracy": round(float(acc), 4), "precision_macro": round(float(prec), 4),
        "recall_macro": round(float(rec), 4), "f1_macro": round(float(f1), 4),
        "roc_auc": (round(float(roc), 4) if roc is not None else None),
        "confusion_matrix": cm, "labels": list(le.classes_),
        "test_samples": int(len(yte)),
        "class_distribution": {str(k): int(v) for k, v in Counter(df['label']).items()},
        "dataset_source": str(df.get("source", ["unknown"])[0] if "source" in df.columns else "unknown"),
        "synthetic_fallback": bool((df.get("source") == "synthetic-fallback").any() if "source" in df.columns else True),
        "dataset_rows": int(len(df)), "random_seed": RANDOM_SEED,
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }
    (MODELS / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
