"""PeerScope model evaluation: reload artifacts and recompute test metrics."""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

BASE = Path(__file__).resolve().parent.parent


def main() -> None:
    vec = joblib.load(BASE / "models" / "tfidf_vectorizer.joblib")
    clf = joblib.load(BASE / "models" / "decision_model.joblib")
    df = pd.read_csv(BASE / "data" / "processed_dataset.csv").dropna()
    blob = df["title"].fillna("") + " " + df["text"].fillna("")
    y = df["label"].astype(str)
    _, Xte, _, yte = train_test_split(blob, y, test_size=0.2, random_state=42, stratify=y)
    pred = clf.predict(vec.transform(list(Xte)))
    out = {"accuracy": accuracy_score(yte, pred),
           "precision_macro": precision_score(yte, pred, average="macro", zero_division=0),
           "recall_macro": recall_score(yte, pred, average="macro", zero_division=0),
           "f1_macro": f1_score(yte, pred, average="macro", zero_division=0),
           "confusion_matrix": confusion_matrix(yte, pred).tolist()}
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
