"""
preprocessing.py
-----------------
Image preprocessing pipeline tailored for underwater / ocean
surface imagery before it is fed to the YOLO detector.

Ocean images have specific challenges that ordinary photos
don't: colour cast from water absorbing red wavelengths,
low contrast/haze, uneven lighting (glare, shadows under
waves) and sensor noise from compression or low-light capture.
Each step below targets one of those problems.

IMPORTANT: YOLO models (via Ultralytics) already do their own
resizing/letterboxing and normalisation internally at inference
time. So this pipeline is deliberately light-touch — it improves
visual quality (denoising, contrast, colour balance) rather than
duplicating what the model already handles, since over-processing
an image before detection can *remove* the texture/edge
information the model relies on and hurt accuracy.
"""

import cv2
import numpy as np


def resize_image(image: np.ndarray, max_dim: int = 1280) -> np.ndarray:
    """
    Resize while keeping aspect ratio, capping the longest side.

    Why: extremely large phone/drone photos slow inference and
    provide no extra benefit since YOLO internally resizes to its
    own input size anyway. Capping the longest side keeps things
    fast without visibly degrading quality.
    """
    h, w = image.shape[:2]
    longest = max(h, w)
    if longest <= max_dim:
        return image
    scale = max_dim / longest
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)


def denoise_image(image: np.ndarray) -> np.ndarray:
    """
    Mild denoising using a fast Non-Local Means filter.

    Why: underwater/low-light shots often have sensor grain that
    can look like small floating debris to a detector, causing
    false positives. A light denoise reduces this without
    blurring away real object edges (strength kept low on purpose).
    """
    return cv2.fastNlMeansDenoisingColored(image, None, h=5, hColor=5,
                                            templateWindowSize=7,
                                            searchWindowSize=21)


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    """
    CLAHE (Contrast Limited Adaptive Histogram Equalisation) on
    the luminance channel.

    Why: ocean photos are frequently hazy/low-contrast (overcast
    sky, water turbidity, sun glare). CLAHE boosts local contrast
    so plastic objects stand out more from water/foam/sand
    backgrounds, without over-amplifying noise the way global
    histogram equalisation would.
    """
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_eq = clahe.apply(l)
    merged = cv2.merge((l_eq, a, b))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)


def correct_color_cast(image: np.ndarray) -> np.ndarray:
    """
    Simple grey-world white balance correction.

    Why: water absorbs red wavelengths first, so underwater and
    even surface ocean images often skew blue/green. This shifts
    channel averages back toward neutral grey, making plastic
    (which is often brightly, unnaturally coloured) easier for
    both the model and a human reviewer to distinguish from the
    natural blue/green background.
    """
    result = image.astype(np.float32)
    avg_b, avg_g, avg_r = [np.mean(result[:, :, i]) for i in range(3)]
    avg_gray = (avg_b + avg_g + avg_r) / 3.0
    # Avoid division by zero on a flat/blank image
    for i, avg_c in enumerate([avg_b, avg_g, avg_r]):
        if avg_c > 1e-6:
            result[:, :, i] *= (avg_gray / avg_c)
    return np.clip(result, 0, 255).astype(np.uint8)


def preprocess_image(image: np.ndarray, apply_denoise: bool = True,
                      apply_contrast: bool = True,
                      apply_color_correction: bool = True,
                      max_dim: int = 1280) -> np.ndarray:
    """
    Full preprocessing pipeline. Returns a BGR uint8 image ready
    to hand to the detector.

    Steps are individually toggleable so a user/demo can compare
    "raw" vs "preprocessed" detection quality — useful for the
    project viva to show *why* each step exists.
    """
    processed = resize_image(image, max_dim=max_dim)

    if apply_color_correction:
        processed = correct_color_cast(processed)

    if apply_denoise:
        processed = denoise_image(processed)

    if apply_contrast:
        processed = enhance_contrast(processed)

    return processed
