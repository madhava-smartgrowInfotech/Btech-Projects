"""Image preprocessing pipeline.

Implements, in order, exactly the steps described in the project abstract:

    1. Region-of-interest extraction (hand crop)
    2. Grayscale conversion
    3. Noise reduction (Gaussian blur)
    4. Segmentation (binary threshold / skin-color mask)
    5. Normalization (resize + scale to [0, 1])

The same pipeline is used at data-collection preview time, training time and
real-time inference time so the CNN always sees consistently processed
input.
"""

from __future__ import annotations

import cv2
import numpy as np

from . import config


def get_roi_box(frame_w: int, frame_h: int, box_size: int = config.ROI_BOX_SIZE):
    """Return (x1, y1, x2, y2) for a centered-right square ROI box.

    Placed toward the right side of the frame, which is comfortable for a
    right-handed user facing the webcam; large enough to fit a full hand.
    """
    x2 = frame_w - 40
    x1 = max(0, x2 - box_size)
    y1 = 90
    y2 = min(frame_h, y1 + box_size)
    return x1, y1, x2, y2


def crop_roi(frame: np.ndarray, box) -> np.ndarray:
    x1, y1, x2, y2 = box
    return frame[y1:y2, x1:x2].copy()


def reduce_noise(gray: np.ndarray) -> np.ndarray:
    """Gaussian blur to suppress sensor / background noise."""
    return cv2.GaussianBlur(gray, (7, 7), 0)


def segment_threshold(blurred_gray: np.ndarray) -> np.ndarray:
    """Otsu binary threshold -> isolates the hand silhouette from background."""
    _, mask = cv2.threshold(
        blurred_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    # Ensure the hand (foreground) is the brighter region; if the mask is
    # mostly white it likely inverted against a bright background, so flip it.
    if np.mean(mask) > 127:
        mask = cv2.bitwise_not(mask)
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    return mask


def segment_skin(roi_bgr: np.ndarray) -> np.ndarray:
    """YCrCb skin-color mask; more robust against cluttered backgrounds."""
    ycrcb = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2YCrCb)
    lower = np.array([0, 133, 77], dtype=np.uint8)
    upper = np.array([255, 173, 127], dtype=np.uint8)
    mask = cv2.inRange(ycrcb, lower, upper)
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.GaussianBlur(mask, (5, 5), 0)
    return mask


def segment_hand(roi_bgr: np.ndarray, mode: str | None = None) -> np.ndarray:
    """Full grayscale -> blur -> segmentation pipeline. Returns a uint8 mask."""
    mode = mode or config.SEGMENTATION_MODE
    gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
    blurred = reduce_noise(gray)

    if mode == "skin":
        return segment_skin(roi_bgr)
    return segment_threshold(blurred)


def normalize_for_model(mask: np.ndarray, size: int = config.IMG_SIZE) -> np.ndarray:
    """Resize + scale to [0, 1], shaped (size, size, 1) float32."""
    resized = cv2.resize(mask, (size, size), interpolation=cv2.INTER_AREA)
    normalized = resized.astype("float32") / 255.0
    return np.expand_dims(normalized, axis=-1)


def preprocess_roi(roi_bgr: np.ndarray, mode: str | None = None):
    """Convenience: full pipeline from a raw color ROI crop to model input.

    Returns (model_input, display_mask) where model_input is ready to feed
    into the CNN (with an added batch dimension by the caller) and
    display_mask is a uint8 image suitable for on-screen preview.
    """
    mask = segment_hand(roi_bgr, mode=mode)
    model_input = normalize_for_model(mask)
    return model_input, mask
