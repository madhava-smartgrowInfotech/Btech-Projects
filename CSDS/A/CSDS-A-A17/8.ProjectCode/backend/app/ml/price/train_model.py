from __future__ import annotations

import joblib
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from app.core.config import DATA_DIR
from app.ml.price.features import FEATURE_COLUMNS
from app.ml.price.generate_dataset import generate


def train() -> dict:
    dataset_path = DATA_DIR / "price_dataset.csv"
    if dataset_path.exists():
        df = pd.read_csv(dataset_path)
    else:
        df = generate()
        df.to_csv(dataset_path, index=False)

    X = df[FEATURE_COLUMNS].values
    y = df["price"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)

    point_model = GradientBoostingRegressor(n_estimators=300, max_depth=4, learning_rate=0.06, random_state=42)
    point_model.fit(X_train, y_train)

    low_model = GradientBoostingRegressor(
        n_estimators=250, max_depth=3, learning_rate=0.06, loss="quantile", alpha=0.15, random_state=42
    )
    low_model.fit(X_train, y_train)

    high_model = GradientBoostingRegressor(
        n_estimators=250, max_depth=3, learning_rate=0.06, loss="quantile", alpha=0.85, random_state=42
    )
    high_model.fit(X_train, y_train)

    preds = point_model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)

    artifact = {
        "point_model": point_model,
        "low_model": low_model,
        "high_model": high_model,
        "feature_columns": FEATURE_COLUMNS,
        "test_mae": mae,
        "test_r2": r2,
    }
    out_path = DATA_DIR / "price_model.joblib"
    joblib.dump(artifact, out_path)
    print(f"price model MAE: {mae:.2f}  R2: {r2:.3f}")
    print(f"saved to {out_path}")
    return artifact


if __name__ == "__main__":
    train()
