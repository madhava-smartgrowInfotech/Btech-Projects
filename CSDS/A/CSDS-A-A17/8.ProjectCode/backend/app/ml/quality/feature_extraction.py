"""Real computer-vision feature extraction for crop quality grading.

Every feature here is computed from actual pixel data of the image the
farmer uploads (color, texture, edges, blemishes, relative size) -- there
is nothing simulated in this module. The trained classifier consumes
exactly this feature vector, both during offline training (on synthetic
labeled features, see generate_dataset.py) and at real inference time.
"""

from __future__ import annotations

import io

import cv2
import numpy as np
from PIL import Image
from skimage.feature import graycomatrix, graycoprops

FEATURE_NAMES = [
    "mean_hue",
    "mean_saturation",
    "mean_value",
    "saturation_std",
    "color_uniformity",
    "texture_contrast",
    "texture_homogeneity",
    "texture_energy",
    "edge_density",
    "blemish_ratio",
    "size_score",
]

TARGET_SIZE = 256


def _load_image(image_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img.thumbnail((TARGET_SIZE, TARGET_SIZE))
    canvas = Image.new("RGB", (TARGET_SIZE, TARGET_SIZE), (255, 255, 255))
    offset = ((TARGET_SIZE - img.width) // 2, (TARGET_SIZE - img.height) // 2)
    canvas.paste(img, offset)
    return cv2.cvtColor(np.array(canvas), cv2.COLOR_RGB2BGR)


def _foreground_mask(bgr: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]
    # background heuristic: low-saturation, bright/near-uniform surface
    _, mask = cv2.threshold(sat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    bright_bg = (val > 235) & (sat < 25)
    mask[bright_bg] = 0
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    coverage = mask.mean() / 255.0
    if coverage < 0.03 or coverage > 0.98:
        mask = np.full(bgr.shape[:2], 255, dtype=np.uint8)
    return mask


def extract_features(image_bytes: bytes) -> dict[str, float]:
    bgr = _load_image(image_bytes)
    mask = _foreground_mask(bgr)
    mask_bool = mask > 0
    mask_area_ratio = float(mask_bool.mean())

    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
    h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]

    hue_rad = h[mask_bool] * (np.pi / 90.0)  # opencv hue is 0-179
    mean_hue = float(((np.arctan2(np.sin(hue_rad).mean(), np.cos(hue_rad).mean())) % (2 * np.pi)) / (2 * np.pi))
    mean_saturation = float(s[mask_bool].mean() / 255.0)
    mean_value = float(v[mask_bool].mean() / 255.0)
    saturation_std = float(s[mask_bool].std() / 255.0)
    color_uniformity = float(np.clip(1.0 - saturation_std * 2.2, 0.0, 1.0))

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gray_masked = gray.copy()
    gray_masked[~mask_bool] = 0
    glcm = graycomatrix(
        (gray_masked // 16).astype(np.uint8),
        distances=[2],
        angles=[0, np.pi / 4, np.pi / 2, 3 * np.pi / 4],
        levels=16,
        symmetric=True,
        normed=True,
    )
    texture_contrast = float(np.clip(graycoprops(glcm, "contrast").mean() / 40.0, 0.0, 1.0))
    texture_homogeneity = float(graycoprops(glcm, "homogeneity").mean())
    texture_energy = float(graycoprops(glcm, "energy").mean())

    edges = cv2.Canny(gray, 60, 150)
    edge_density = float((edges[mask_bool] > 0).mean()) if mask_bool.any() else 0.0

    value_pixels = v[mask_bool]
    if value_pixels.size:
        thresh = value_pixels.mean() - 1.15 * value_pixels.std()
        blemish_pixels = ((v < thresh) & mask_bool).sum()
        blemish_ratio = float(blemish_pixels / value_pixels.size)
    else:
        blemish_ratio = 0.0

    size_score = float(np.clip(mask_area_ratio / 0.55, 0.0, 1.0))

    return {
        "mean_hue": mean_hue,
        "mean_saturation": mean_saturation,
        "mean_value": mean_value,
        "saturation_std": saturation_std,
        "color_uniformity": color_uniformity,
        "texture_contrast": texture_contrast,
        "texture_homogeneity": texture_homogeneity,
        "texture_energy": texture_energy,
        "edge_density": edge_density,
        "blemish_ratio": min(blemish_ratio, 1.0),
        "size_score": size_score,
    }


def features_to_vector(features: dict[str, float]) -> np.ndarray:
    return np.array([[features[name] for name in FEATURE_NAMES]], dtype=np.float64)
