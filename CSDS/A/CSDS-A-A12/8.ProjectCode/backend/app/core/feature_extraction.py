"""Morphological trait extraction from seed images using classical CV.

Mirrors the base-paper approach of deriving RGB + shape traits (area,
perimeter, aspect ratio, circularity, colour statistics) from a segmented
seed contour, rather than relying purely on end-to-end deep features.
"""
from dataclasses import dataclass, asdict

import cv2
import numpy as np


@dataclass
class MorphFeatures:
    area: float
    perimeter: float
    aspect_ratio: float
    circularity: float
    mean_color_rgb: list
    color_std: float
    segmented: bool

    def as_dict(self):
        return asdict(self)

    def as_vector(self) -> np.ndarray:
        """Flat numeric feature vector for model fusion (colour channels split out)."""
        r, g, b = self.mean_color_rgb
        return np.array(
            [self.area, self.perimeter, self.aspect_ratio, self.circularity, r, g, b, self.color_std],
            dtype=np.float32,
        )


VECTOR_LENGTH = 8

# Fallback values used when a seed contour cannot be reliably segmented
# (e.g. cluttered background, low contrast). Chosen as roughly the median
# of a well-formed millet grain so a failed segmentation degrades
# gracefully instead of producing an outlier that dominates the fusion model.
_FALLBACK = MorphFeatures(
    area=850.0,
    perimeter=110.0,
    aspect_ratio=1.6,
    circularity=0.72,
    mean_color_rgb=[150.0, 120.0, 70.0],
    color_std=28.0,
    segmented=False,
)


def _largest_contour(mask: np.ndarray):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    return max(contours, key=cv2.contourArea)


def extract_morph_features(image_bgr: np.ndarray) -> MorphFeatures:
    """Segment the dominant seed blob and compute morphological + colour traits.

    Accepts any BGR image (as read by cv2.imread / cv2.imdecode). Falls back
    to representative defaults if no usable contour is found so the pipeline
    never crashes on an arbitrary upload.
    """
    try:
        img = image_bgr
        if img is None or img.size == 0:
            return _FALLBACK

        h, w = img.shape[:2]
        if max(h, w) > 800:
            scale = 800 / max(h, w)
            img = cv2.resize(img, (int(w * scale), int(h * scale)))

        blurred = cv2.GaussianBlur(img, (5, 5), 0)
        gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)

        # Otsu thresholding, tried both polarities since the seed may be
        # darker or lighter than its background.
        _, thresh_dark = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        _, thresh_light = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        candidates = []
        for mask in (thresh_dark, thresh_light):
            kernel = np.ones((3, 3), np.uint8)
            clean = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
            clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, kernel, iterations=2)
            c = _largest_contour(clean)
            if c is not None:
                candidates.append((cv2.contourArea(c), c, clean))

        if not candidates:
            return _FALLBACK

        img_area = h * w
        # Prefer the contour that plausibly represents a single foreground
        # object (not the whole frame, not noise specks).
        valid = [c for c in candidates if 0.005 * img_area < c[0] < 0.85 * img_area]
        area, contour, mask = max(valid, key=lambda c: c[0]) if valid else max(candidates, key=lambda c: c[0])

        perimeter = cv2.arcLength(contour, True)
        rect = cv2.minAreaRect(contour)
        (rw, rh) = rect[1]
        if rw <= 0 or rh <= 0:
            return _FALLBACK
        aspect_ratio = max(rw, rh) / max(min(rw, rh), 1e-6)
        circularity = float(4 * np.pi * area / (perimeter**2)) if perimeter > 0 else 0.0
        circularity = max(0.0, min(circularity, 1.0))

        obj_mask = np.zeros(gray.shape, dtype=np.uint8)
        cv2.drawContours(obj_mask, [contour], -1, 255, thickness=cv2.FILLED)
        pixels = img[obj_mask == 255]
        if pixels.size == 0:
            mean_rgb = [150.0, 120.0, 70.0]
            color_std = 28.0
        else:
            mean_bgr = pixels.mean(axis=0)
            mean_rgb = [float(mean_bgr[2]), float(mean_bgr[1]), float(mean_bgr[0])]
            color_std = float(pixels.std())

        return MorphFeatures(
            area=float(area),
            perimeter=float(perimeter),
            aspect_ratio=float(aspect_ratio),
            circularity=circularity,
            mean_color_rgb=[round(v, 2) for v in mean_rgb],
            color_std=round(color_std, 2),
            segmented=True,
        )
    except Exception:
        return _FALLBACK


def preprocess_for_encoder(image_bgr: np.ndarray, size: int) -> np.ndarray:
    """Resize/normalize an image into a (3, size, size) float32 tensor in [0, 1]."""
    if image_bgr is None or image_bgr.size == 0:
        image_bgr = np.zeros((size, size, 3), dtype=np.uint8)
    resized = cv2.resize(image_bgr, (size, size), interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    chw = np.transpose(rgb, (2, 0, 1))
    return chw
