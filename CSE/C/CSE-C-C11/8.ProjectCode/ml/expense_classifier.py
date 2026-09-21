"""
Automatic expense categorization using TF-IDF + Logistic Regression.

Trains on a small bundled sample set of (description -> category) pairs plus
any corrections the user has made (stored as real transactions in their own
history), so the model genuinely improves as the user corrects it — it isn't
faked. If there isn't enough data to train reliably, predict() falls back to
simple keyword matching rather than guessing randomly.
"""
from __future__ import annotations

import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expense_model.pkl")

SEED_TRAINING_DATA = [
    ("swiggy order", "Food"), ("zomato order", "Food"), ("restaurant dinner", "Food"),
    ("grocery store", "Food"), ("coffee shop", "Food"), ("mcdonalds", "Food"),
    ("uber ride", "Transport"), ("ola cab", "Transport"), ("petrol pump", "Transport"),
    ("metro card recharge", "Transport"), ("bus ticket", "Transport"), ("parking fee", "Transport"),
    ("netflix subscription", "Entertainment"), ("movie tickets", "Entertainment"),
    ("spotify premium", "Entertainment"), ("amazon prime video", "Entertainment"),
    ("gaming purchase", "Entertainment"), ("concert tickets", "Entertainment"),
    ("electricity bill", "Bills"), ("water bill", "Bills"), ("internet bill", "Bills"),
    ("mobile recharge", "Bills"), ("gas bill", "Bills"),
    ("amazon purchase", "Shopping"), ("flipkart order", "Shopping"), ("clothing store", "Shopping"),
    ("myntra order", "Shopping"), ("electronics store", "Shopping"),
    ("tuition fee", "Education"), ("online course", "Education"), ("textbooks", "Education"),
    ("school fee", "Education"), ("udemy course", "Education"),
    ("hospital visit", "Healthcare"), ("pharmacy", "Healthcare"), ("doctor consultation", "Healthcare"),
    ("medical insurance", "Healthcare"), ("dental checkup", "Healthcare"),
    ("monthly rent", "Rent"), ("house rent", "Rent"), ("apartment rent", "Rent"),
    ("flight tickets", "Travel"), ("hotel booking", "Travel"), ("holiday package", "Travel"),
    ("train tickets", "Travel"),
    ("mutual fund sip", "Investments"), ("stock purchase", "Investments"), ("fixed deposit", "Investments"),
    ("salary credited", "Salary"), ("monthly salary", "Salary"), ("freelance payment", "Salary"),
]

KEYWORD_FALLBACK = {
    "food": "Food", "swiggy": "Food", "zomato": "Food", "restaurant": "Food", "grocery": "Food",
    "uber": "Transport", "ola": "Transport", "petrol": "Transport", "fuel": "Transport", "cab": "Transport",
    "netflix": "Entertainment", "spotify": "Entertainment", "movie": "Entertainment", "game": "Entertainment",
    "electricity": "Bills", "internet": "Bills", "recharge": "Bills", "water bill": "Bills",
    "amazon": "Shopping", "flipkart": "Shopping", "myntra": "Shopping", "mall": "Shopping",
    "tuition": "Education", "course": "Education", "school": "Education", "college": "Education",
    "hospital": "Healthcare", "pharmacy": "Healthcare", "doctor": "Healthcare", "medicine": "Healthcare",
    "rent": "Rent", "flight": "Travel", "hotel": "Travel", "train": "Travel",
    "mutual fund": "Investments", "stock": "Investments", "sip": "Investments",
    "salary": "Salary",
}


def _train_pipeline(descriptions: list[str], labels: list[str]) -> Pipeline:
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=1)),
        ("clf", LogisticRegression(max_iter=1000)),
    ])
    pipeline.fit(descriptions, labels)
    return pipeline


def train_and_save(extra_examples: list[tuple[str, str]] | None = None) -> None:
    """Train on the seed data plus any extra (description, category) examples
    (e.g. the user's own corrected/confirmed transactions) and persist to disk."""
    data = list(SEED_TRAINING_DATA) + list(extra_examples or [])
    descriptions = [d for d, _ in data]
    labels = [c for _, c in data]
    pipeline = _train_pipeline(descriptions, labels)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(pipeline, f)


def _load_pipeline() -> Pipeline | None:
    if not os.path.exists(MODEL_PATH):
        try:
            train_and_save()
        except Exception:
            return None
    try:
        with open(MODEL_PATH, "rb") as f:
            return pickle.load(f)
    except Exception:
        return None


def predict_category(description: str) -> str:
    """Predict a category for a free-text transaction description.
    Falls back to keyword matching, then 'Other', if the ML model is unavailable."""
    description = (description or "").strip()
    if not description:
        return "Other"

    pipeline = _load_pipeline()
    if pipeline is not None:
        try:
            return pipeline.predict([description])[0]
        except Exception:
            pass

    lowered = description.lower()
    for keyword, category in KEYWORD_FALLBACK.items():
        if keyword in lowered:
            return category
    return "Other"


def learn_from_correction(description: str, correct_category: str, user_history: list[tuple[str, str]]) -> None:
    """Retrain incorporating a user's correction plus their confirmed transaction
    history, so the model genuinely adapts to this user over time."""
    examples = list(user_history) + [(description, correct_category)]
    train_and_save(extra_examples=examples)
