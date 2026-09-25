"""Trains the fusion XGBoost classifier on [JEPA embedding + morphological
traits + environmental tabular data] -> germination outcome, and writes
evaluation metrics + artifacts.

Run after train_encoder.py: `python ml/train_classifier.py`
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import joblib
import numpy as np
import pandas as pd
import torch
import xgboost as xgb
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from app.core.classifier import build_feature_names, build_feature_vector
from app.core.config import (
    CLASSIFIER_PATH,
    DATASET_CSV,
    DATASET_DIR,
    EMBEDDING_DIM,
    ENCODER_WEIGHTS_PATH,
    FEATURE_NAMES_PATH,
    IMAGE_SIZE,
    METRICS_PATH,
    SCALER_PATH,
    SEED_TYPE_ENCODER_PATH,
)
from app.core.encoder import JepaEncoder
from app.core.feature_extraction import extract_morph_features, preprocess_for_encoder


def embed_images(paths, model, device, batch_size=64) -> np.ndarray:
    embeddings = []
    batch = []
    for p in paths:
        img_bgr = cv2.imread(str(p))
        batch.append(preprocess_for_encoder(img_bgr, IMAGE_SIZE))
        if len(batch) == batch_size:
            t = torch.from_numpy(np.stack(batch)).float().to(device)
            embeddings.append(model.embed(t).cpu().numpy())
            batch = []
    if batch:
        t = torch.from_numpy(np.stack(batch)).float().to(device)
        embeddings.append(model.embed(t).cpu().numpy())
    return np.concatenate(embeddings, axis=0)


def main():
    df = pd.read_csv(DATASET_CSV)
    images_dir = DATASET_DIR / "images"
    paths = [images_dir / fname for fname in df["image"]]

    device = "cuda" if torch.cuda.is_available() else "cpu"
    encoder = JepaEncoder(embed_dim=EMBEDDING_DIM).to(device)
    encoder.load_state_dict(torch.load(ENCODER_WEIGHTS_PATH, map_location=device))
    encoder.eval()

    print("Computing image embeddings...")
    embeddings = embed_images(paths, encoder, device)

    print("Extracting morphological features...")
    morph_vectors = []
    for p in paths:
        img_bgr = cv2.imread(str(p))
        feats = extract_morph_features(img_bgr)
        morph_vectors.append(feats.as_vector())
    morph_vectors = np.stack(morph_vectors)

    print("Assembling feature matrix...")
    X = np.stack([
        build_feature_vector(
            embeddings[i], morph_vectors[i],
            df.loc[i, "soil_moisture"], df.loc[i, "temperature"], df.loc[i, "humidity"],
            df.loc[i, "rainfall"], df.loc[i, "soil_ph"], df.loc[i, "seed_type"],
        )
        for i in range(len(df))
    ])
    y = df["germinated"].values
    feature_names = build_feature_names()

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    dtrain = xgb.DMatrix(X_train_s, label=y_train, feature_names=feature_names)
    dtest = xgb.DMatrix(X_test_s, label=y_test, feature_names=feature_names)

    params = {
        "objective": "binary:logistic",
        "eval_metric": "logloss",
        "max_depth": 5,
        "eta": 0.08,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "min_child_weight": 3,
        "seed": 42,
    }
    print("Training XGBoost classifier...")
    booster = xgb.train(
        params, dtrain, num_boost_round=250,
        evals=[(dtrain, "train"), (dtest, "test")],
        early_stopping_rounds=20, verbose_eval=25,
    )

    y_prob = booster.predict(dtest)
    y_pred = (y_prob >= 0.5).astype(int)

    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred)), 4),
        "recall": round(float(recall_score(y_test, y_pred)), 4),
        "f1_score": round(float(f1_score(y_test, y_pred)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_prob)), 4),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "positive_rate": round(float(y.mean()), 4),
    }
    print("Test metrics:", json.dumps(metrics, indent=2))

    booster.save_model(str(CLASSIFIER_PATH))
    joblib.dump(scaler, SCALER_PATH)
    with open(FEATURE_NAMES_PATH, "w") as f:
        json.dump(feature_names, f)
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    # Global feature importance for the model-info endpoint.
    importance = booster.get_score(importance_type="gain")
    top_importance = sorted(importance.items(), key=lambda kv: kv[1], reverse=True)[:15]
    with open(Path(FEATURE_NAMES_PATH).parent / "feature_importance.json", "w") as f:
        json.dump(top_importance, f, indent=2)

    print(f"Saved classifier -> {CLASSIFIER_PATH}")
    print(f"Saved scaler -> {SCALER_PATH}")
    print(f"Saved metrics -> {METRICS_PATH}")


if __name__ == "__main__":
    main()
