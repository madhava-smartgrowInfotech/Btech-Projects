from __future__ import annotations

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

from app.core.config import DATA_DIR
from app.ml.quality.feature_extraction import FEATURE_NAMES
from app.ml.quality.generate_dataset import generate


def train() -> dict:
    dataset_path = DATA_DIR / "quality_dataset.csv"
    if dataset_path.exists():
        df = pd.read_csv(dataset_path)
    else:
        df = generate()
        df.to_csv(dataset_path, index=False)

    X = df[FEATURE_NAMES].values
    y = df["grade"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = RandomForestClassifier(
        n_estimators=250,
        max_depth=9,
        min_samples_leaf=4,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    acc = accuracy_score(y_test, preds)
    report = classification_report(y_test, preds, output_dict=True)

    artifact = {
        "model": model,
        "feature_names": FEATURE_NAMES,
        "classes": list(model.classes_),
        "test_accuracy": acc,
        "report": report,
    }
    out_path = DATA_DIR / "quality_model.joblib"
    joblib.dump(artifact, out_path)
    print(f"quality model test accuracy: {acc:.3f}")
    print(f"saved to {out_path}")
    return artifact


if __name__ == "__main__":
    train()
