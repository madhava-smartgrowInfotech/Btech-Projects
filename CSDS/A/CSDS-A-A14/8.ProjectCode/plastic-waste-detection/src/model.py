"""
model.py
--------
Model-loading module. Loads the YOLO weights exactly once
(cached by Streamlit across reruns), auto-selects GPU/CPU, and
fails gracefully with a clear message if weights are missing.

NOTE ON BASE PAPER vs THIS IMPLEMENTATION:
The base paper uses YOLOv7 for floating-water-garbage detection.
This project uses the Ultralytics YOLO implementation (YOLOv8)
instead. Both are single-stage, anchor-free-capable YOLO
detectors trained the same conceptual way (transfer learning
from a COCO-pretrained backbone onto a custom plastic-waste
dataset). YOLOv8 was chosen here because the Ultralytics library
provides a stable, actively maintained Python API for training,
validation and inference (used throughout train.py / evaluate.py
/ predict.py / app.py), which is significantly easier for a
B.Tech project to install, train and demo reliably than the
original YOLOv7 research codebase. The detection concept,
architecture family, and evaluation metrics (Precision, Recall,
mAP) are consistent with the base paper.
"""

from pathlib import Path

import torch
from ultralytics import YOLO

from src.utils import MODELS_DIR

DEFAULT_MODEL_PATH = MODELS_DIR / "best.pt"
# Fallback used only when no trained plastic-waste weights are
# present, so the app can still be demoed end-to-end. This
# fallback is a general COCO-pretrained model and will NOT
# accurately detect "plastic" as a class — it is clearly labelled
# as a demo fallback everywhere it is used.
FALLBACK_MODEL_NAME = "yolov8n.pt"


def get_device() -> str:
    """Return 'cuda' if a GPU is available, otherwise 'cpu'."""
    return "cuda" if torch.cuda.is_available() else "cpu"


def load_model(model_path: str | Path = DEFAULT_MODEL_PATH):
    """
    Load a YOLO model from disk.

    Returns a tuple: (model, device, used_fallback: bool, message: str)

    - If trained weights exist at model_path, they are loaded.
    - If not, falls back to a COCO-pretrained yolov8n.pt so the
      UI remains usable for a demo, but used_fallback=True is
      returned so calling code can warn the user clearly. This
      is REQUIRED USER INPUT: place your trained models/best.pt
      (produced by train.py) to get real plastic-waste detection.
    - If loading fails entirely (corrupted file, missing
      dependency, etc.) a RuntimeError is raised with a clear
      message instead of letting a raw traceback reach the user.
    """
    device = get_device()
    model_path = Path(model_path)

    try:
        if model_path.exists():
            model = YOLO(str(model_path))
            model.to(device)
            return model, device, False, f"Loaded trained model from {model_path.name}."

        # No trained weights found -> fall back to a pretrained
        # general-purpose model purely so the pipeline runs.
        model = YOLO(FALLBACK_MODEL_NAME)
        model.to(device)
        msg = (
            "No trained plastic-waste model found at "
            f"'{model_path}'. REQUIRED USER INPUT: run train.py to "
            "produce models/best.pt, or place your own trained "
            "weights there. Using a general COCO-pretrained model "
            "as a placeholder — it will NOT reliably detect plastic."
        )
        return model, device, True, msg

    except Exception as exc:  # noqa: BLE001 - surface as a clean message
        raise RuntimeError(
            f"Failed to load YOLO model ({exc}). Check that the weights "
            "file is a valid .pt file and that 'ultralytics' and 'torch' "
            "are installed correctly."
        ) from exc
