"""Train the text models used by the call pipeline (CPU, well under a minute).

- Intent: Bitext customer-support utterances -> 27 intents (and their 11 topic categories).
- Sentiment: Twitter US Airline Sentiment (customer-service messages) -> negative / neutral / positive.
- Keywords: a TF-IDF vocabulary over customer-support text, used to pull keywords out of transcripts.
Outputs: models/intent.joblib, models/sentiment.joblib, models/keywords.joblib, experiments/metrics.json
Usage: python ml/train.py
"""
import json
import re
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
MODELS = ROOT / "models"
EXP = ROOT / "experiments"
SEED = 42


def clean(text):
    text = str(text)
    text = re.sub(r"\{\{[^}]*\}\}", " ", text)          # Bitext placeholders like {{Order Number}}
    text = re.sub(r"https?://\S+|@\w+|#", " ", text)     # tweet handles, links, hashtags
    return re.sub(r"\s+", " ", text).strip().lower()


def features():
    return FeatureUnion([
        ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=3, sublinear_tf=True, max_features=60000)),
    ])


def fit_eval(name, X, y, C, class_weight=None):
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=SEED, stratify=y)
    t0 = time.time()
    model = Pipeline([("features", features()),
                      ("clf", LogisticRegression(C=C, max_iter=2000, class_weight=class_weight))])
    model.fit(Xtr, ytr)
    pred = model.predict(Xte)
    labels = list(model.classes_)
    rep = classification_report(yte, pred, labels=labels, output_dict=True, zero_division=0)
    metrics = {
        "train_size": len(Xtr), "test_size": len(Xte), "classes": labels,
        "accuracy": round(accuracy_score(yte, pred), 4),
        "macro_f1": round(f1_score(yte, pred, average="macro"), 4),
        "weighted_f1": round(f1_score(yte, pred, average="weighted"), 4),
        "per_class_f1": {c: round(rep[c]["f1-score"], 4) for c in labels},
        "confusion_matrix": confusion_matrix(yte, pred, labels=labels).tolist(),
        "train_seconds": round(time.time() - t0, 1),
    }
    print(f"{name}: accuracy {metrics['accuracy']}  macro-F1 {metrics['macro_f1']}  ({metrics['train_seconds']}s)")
    return model, metrics


def main():
    MODELS.mkdir(exist_ok=True)
    EXP.mkdir(exist_ok=True)

    bitext = pd.read_csv(next((DATA / "bitext").glob("*.csv")))
    bitext["text"] = bitext["instruction"].map(clean)
    bitext = bitext[bitext["text"].str.len() > 2]
    intent_model, intent_metrics = fit_eval("Intent", bitext["text"].tolist(), bitext["intent"].tolist(), C=10)
    categories = bitext.groupby("intent")["category"].first().to_dict()
    joblib.dump({"model": intent_model, "categories": categories}, MODELS / "intent.joblib", compress=3)

    tweets = pd.read_csv(DATA / "airline" / "Tweets.csv")
    tweets["text"] = tweets["text"].map(clean)
    tweets = tweets[tweets["text"].str.len() > 2]
    sent_model, sent_metrics = fit_eval("Sentiment", tweets["text"].tolist(),
                                        tweets["airline_sentiment"].tolist(), C=3, class_weight="balanced")
    joblib.dump({"model": sent_model}, MODELS / "sentiment.joblib", compress=3)

    calls = pd.read_csv(DATA / "call_center" / "call_recordings.csv")
    corpus = pd.concat([bitext["text"], bitext["response"].map(clean), tweets["text"],
                        calls["Transcript"].map(clean)]).tolist()
    kw = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=3, max_df=0.2, sublinear_tf=True,
                         token_pattern=r"(?u)\b[a-z][a-z]{2,}\b")
    kw.fit(corpus)
    joblib.dump(kw, MODELS / "keywords.joblib", compress=3)
    print(f"Keyword vocabulary: {len(kw.vocabulary_)} terms")

    metrics = {
        "intent": {"dataset": "Bitext customer support (27 intents)", "model": "TF-IDF word+char + logistic regression",
                   **intent_metrics},
        "sentiment": {"dataset": "Twitter US Airline Sentiment (3 classes)",
                      "model": "TF-IDF word+char + logistic regression (balanced)", **sent_metrics},
        "keywords": {"vocabulary_size": len(kw.vocabulary_)},
        "seed": SEED,
    }
    (EXP / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print("Saved models/ and experiments/metrics.json")


if __name__ == "__main__":
    np.random.seed(SEED)
    main()
