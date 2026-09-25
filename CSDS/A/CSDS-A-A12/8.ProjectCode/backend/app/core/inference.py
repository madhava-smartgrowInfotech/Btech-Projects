"""Loads all trained artifacts once and exposes a single `run_prediction` call
that turns (image bytes, crop/environmental inputs) into a full prediction +
explanation payload.
"""
import base64
import io
import json

import cv2
import numpy as np
import torch
from PIL import Image

from app.core.classifier import GerminationClassifier, build_feature_vector
from app.core.config import (
    CLASSIFIER_PATH,
    EMBEDDING_DIM,
    ENCODER_VERSION,
    ENCODER_WEIGHTS_PATH,
    FEATURE_NAMES_PATH,
    IMAGE_SIZE,
    MODEL_VERSION,
    SCALER_PATH,
)
from app.core.encoder import JepaEncoder
from app.core.explain import generate_explanation
from app.core.feature_extraction import extract_morph_features, preprocess_for_encoder

_device = "cpu"
_encoder: JepaEncoder | None = None
_classifier: GerminationClassifier | None = None


def _artifacts_ready() -> bool:
    return CLASSIFIER_PATH.exists() and SCALER_PATH.exists() and ENCODER_WEIGHTS_PATH.exists() and FEATURE_NAMES_PATH.exists()


def load_models():
    global _encoder, _classifier
    if not _artifacts_ready():
        raise RuntimeError(
            "Model artifacts not found. Run `python ml/build_pipeline.py` from the backend/ directory first."
        )
    encoder = JepaEncoder(embed_dim=EMBEDDING_DIM).to(_device)
    encoder.load_state_dict(torch.load(ENCODER_WEIGHTS_PATH, map_location=_device))
    encoder.eval()
    _encoder = encoder
    _classifier = GerminationClassifier.load(CLASSIFIER_PATH, SCALER_PATH, FEATURE_NAMES_PATH)


def models_loaded() -> bool:
    return _encoder is not None and _classifier is not None


def _decode_image(image_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img


def _make_thumbnail_data_url(image_bytes: bytes, size: int = 96) -> str | None:
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img.thumbnail((size, size))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70)
        encoded = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/jpeg;base64,{encoded}"
    except Exception:
        return None


def run_prediction(image_bytes: bytes, soil_moisture: float, temperature: float, humidity: float,
                    rainfall: float, soil_ph: float, seed_type: str) -> dict:
    if not models_loaded():
        load_models()

    img_bgr = _decode_image(image_bytes)
    morph = extract_morph_features(img_bgr)

    chw = preprocess_for_encoder(img_bgr, IMAGE_SIZE)
    tensor = torch.from_numpy(chw).unsqueeze(0).float().to(_device)
    embedding = _encoder.embed(tensor).cpu().numpy()[0]

    feature_vector = build_feature_vector(
        embedding, morph.as_vector(), soil_moisture, temperature, humidity, rainfall, soil_ph, seed_type,
    )

    probability_germinate = _classifier.predict_proba(feature_vector)
    contribs = _classifier.predict_contribs(feature_vector)

    prediction = "germinate" if probability_germinate >= 0.5 else "no_germinate"
    confidence = probability_germinate if probability_germinate >= 0.5 else 1 - probability_germinate

    if confidence >= 0.75:
        risk_level = "low" if prediction == "germinate" else "high"
    elif confidence >= 0.6:
        risk_level = "medium"
    else:
        risk_level = "medium" if prediction == "germinate" else "high"

    inputs = {
        "soil_moisture": soil_moisture, "temperature": temperature, "humidity": humidity,
        "rainfall": rainfall, "soil_ph": soil_ph, "seed_type": seed_type,
    }
    explanation = generate_explanation(
        _classifier.feature_names, contribs, probability_germinate, inputs, morph.as_dict(),
    )

    top_idx = np.argsort(-np.abs(embedding))[:6]
    embedding_summary = {
        "encoder": ENCODER_VERSION,
        "embedding_dim": int(EMBEDDING_DIM),
        "top_activations": [round(float(embedding[i]), 4) for i in top_idx],
    }

    thumbnail = _make_thumbnail_data_url(image_bytes)

    return {
        "prediction": prediction,
        "confidence": round(float(confidence), 4),
        "probability_germinate": round(float(probability_germinate), 4),
        "risk_level": risk_level,
        "morphological_features": morph.as_dict(),
        "embedding_summary": embedding_summary,
        "explanation": explanation,
        "seed_type": seed_type,
        "soil_moisture": soil_moisture,
        "temperature": temperature,
        "humidity": humidity,
        "rainfall": rainfall,
        "soil_ph": soil_ph,
        "thumbnail_data_url": thumbnail,
        "model_version": MODEL_VERSION,
    }


def get_model_metrics() -> dict:
    from app.core.config import METRICS_PATH
    if not METRICS_PATH.exists():
        return {}
    with open(METRICS_PATH) as f:
        return json.load(f)


def get_global_feature_importance() -> list[dict]:
    from app.core.config import ARTIFACTS_DIR
    path = ARTIFACTS_DIR / "feature_importance.json"
    if not path.exists():
        return []
    with open(path) as f:
        pairs = json.load(f)
    return [{"feature": name, "importance": round(val, 4)} for name, val in pairs]
