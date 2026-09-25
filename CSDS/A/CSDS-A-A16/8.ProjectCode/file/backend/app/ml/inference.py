import io

import cv2
import numpy as np
import torch
from PIL import Image

from app.config import CLASSIFIER_CHECKPOINT
from app.ml.classifier_model import EmotionCNN, IMG_SIZE
from app.ml.face import detect_largest_face
from app.ml.taxonomy import (
    ALL_LABELS,
    BASIC_EMOTIONS,
    COMPOUND_EMOTIONS,
    NUM_LABELS,
    display_label,
)

_model: EmotionCNN | None = None
_device = torch.device("cpu")


def model_is_loaded() -> bool:
    return _model is not None


def load_model() -> EmotionCNN:
    global _model
    if _model is None:
        if not CLASSIFIER_CHECKPOINT.exists():
            raise FileNotFoundError(f"Classifier checkpoint not found at {CLASSIFIER_CHECKPOINT}")
        model = EmotionCNN(out_dim=NUM_LABELS)
        state = torch.load(CLASSIFIER_CHECKPOINT, map_location=_device)
        model.load_state_dict(state)
        model.eval()
        _model = model
    return _model


def _preprocess(face_gray: np.ndarray) -> torch.Tensor:
    face = cv2.resize(face_gray, (IMG_SIZE, IMG_SIZE))
    face = face.astype(np.float32) / 255.0
    face = (face - 0.5) / 0.5
    tensor = torch.from_numpy(face).unsqueeze(0).unsqueeze(0)  # 1x1xHxW
    return tensor


def analyze_image_bytes(image_bytes: bytes, threshold: float = 0.0):
    """Returns (face_detected, basic_scores, compound_scores, dominant, face_crop_bgr)."""
    pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    rgb = np.array(pil_img)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    face_gray = detect_largest_face(bgr)
    if face_gray is None:
        return False, [], [], None, None

    model = load_model()
    tensor = _preprocess(face_gray)
    with torch.no_grad():
        logits = model(tensor)
        probs = torch.sigmoid(logits).squeeze(0).numpy()

    scores = {label: float(probs[i]) for i, label in enumerate(ALL_LABELS)}

    basic_scores = sorted(
        [{"key": k, "label": display_label(k), "confidence": scores[k]} for k in BASIC_EMOTIONS],
        key=lambda x: x["confidence"],
        reverse=True,
    )
    compound_scores = sorted(
        [{"key": k, "label": display_label(k), "confidence": scores[k]} for k in COMPOUND_EMOTIONS],
        key=lambda x: x["confidence"],
        reverse=True,
    )

    best_key = max(scores, key=scores.get)
    kind = "basic" if best_key in BASIC_EMOTIONS else "compound"
    dominant = {"key": best_key, "label": display_label(best_key), "confidence": scores[best_key], "kind": kind}

    return True, basic_scores, compound_scores, dominant, face_gray
