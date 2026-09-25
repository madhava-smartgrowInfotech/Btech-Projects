"""Fusion classifier: JEPA image embeddings + morphological traits + crop/environmental
tabular data -> germination probability, via gradient-boosted trees (XGBoost).

Feature layout (fixed order, must match training):
  [0:EMBEDDING_DIM)                       -> encoder embedding
  [EMBEDDING_DIM:+8)                      -> morphological features (area, perimeter,
                                              aspect_ratio, circularity, r, g, b, color_std)
  [+5)                                    -> soil_moisture, temperature, humidity, rainfall, soil_ph
  [+len(SEED_TYPES))                      -> one-hot seed type
"""
import json

import joblib
import numpy as np
import xgboost as xgb

from app.core.config import EMBEDDING_DIM, SEED_TYPES
from app.core.feature_extraction import VECTOR_LENGTH as MORPH_LEN

TABULAR_ENV_NAMES = ["soil_moisture", "temperature", "humidity", "rainfall", "soil_ph"]
MORPH_NAMES = ["seed_area", "seed_perimeter", "seed_aspect_ratio", "seed_circularity",
               "seed_red", "seed_green", "seed_blue", "seed_color_std"]


def build_feature_names() -> list[str]:
    embed_names = [f"embedding_{i}" for i in range(EMBEDDING_DIM)]
    seed_type_names = [f"seed_type_{s.replace(' ', '_')}" for s in SEED_TYPES]
    return embed_names + MORPH_NAMES + TABULAR_ENV_NAMES + seed_type_names


def build_feature_vector(
    embedding: np.ndarray,
    morph_vector: np.ndarray,
    soil_moisture: float,
    temperature: float,
    humidity: float,
    rainfall: float,
    soil_ph: float,
    seed_type: str,
) -> np.ndarray:
    assert embedding.shape[0] == EMBEDDING_DIM
    assert morph_vector.shape[0] == MORPH_LEN

    env = np.array([soil_moisture, temperature, humidity, rainfall, soil_ph], dtype=np.float32)

    one_hot = np.zeros(len(SEED_TYPES), dtype=np.float32)
    if seed_type in SEED_TYPES:
        one_hot[SEED_TYPES.index(seed_type)] = 1.0

    return np.concatenate([embedding.astype(np.float32), morph_vector.astype(np.float32), env, one_hot])


class GerminationClassifier:
    def __init__(self, booster: xgb.Booster, scaler, feature_names: list[str]):
        self.booster = booster
        self.scaler = scaler
        self.feature_names = feature_names

    @classmethod
    def load(cls, classifier_path, scaler_path, feature_names_path):
        booster = xgb.Booster()
        booster.load_model(str(classifier_path))
        scaler = joblib.load(scaler_path)
        with open(feature_names_path) as f:
            feature_names = json.load(f)
        return cls(booster, scaler, feature_names)

    def _scale(self, x: np.ndarray) -> np.ndarray:
        return self.scaler.transform(x.reshape(1, -1))

    def predict_proba(self, feature_vector: np.ndarray) -> float:
        scaled = self._scale(feature_vector)
        dmat = xgb.DMatrix(scaled, feature_names=self.feature_names)
        prob = float(self.booster.predict(dmat)[0])
        return prob

    def predict_contribs(self, feature_vector: np.ndarray) -> np.ndarray:
        """Per-feature SHAP-style additive contributions (xgboost pred_contribs)."""
        scaled = self._scale(feature_vector)
        dmat = xgb.DMatrix(scaled, feature_names=self.feature_names)
        contribs = self.booster.predict(dmat, pred_contribs=True)[0]
        return contribs  # last entry is the bias term
