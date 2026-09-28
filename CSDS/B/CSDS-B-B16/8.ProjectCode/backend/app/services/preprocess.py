"""Fundus preprocessing: green channel -> CLAHE -> resize -> normalise, plus a quality check."""
import cv2
import numpy as np

DISPLAY_SIZE = 512
MODEL_SIZE = 256  # wavelet input; 2-level Haar gives 128 and 64 px sub-bands

# Quality thresholds (calibrated on the training set, see ml/train_retina.py)
BLUR_MIN = 150.0       # variance of Laplacian on the CLAHE green channel inside the field of view (training 1st pct ~310)
BRIGHT_MIN = 20.0      # mean green intensity inside the field of view
BRIGHT_MAX = 180.0
CLIP_MAX = 0.25        # max share of over/under-exposed pixels


def decode_image(data: bytes) -> np.ndarray:
    arr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("The file is not a readable image (use JPG or PNG).")
    return img


def crop_to_fov(img: np.ndarray) -> np.ndarray:
    """Crop the black border around the circular field of view and pad to a square."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ys, xs = np.where(gray > 15)
    if len(xs) > 100:
        img = img[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = img.shape[:2]
    s = max(h, w)
    out = np.zeros((s, s, 3), np.uint8)
    out[(s - h) // 2:(s - h) // 2 + h, (s - w) // 2:(s - w) // 2 + w] = img
    return out


def fov_mask(img: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mask = (gray > 15).astype(np.uint8)
    return cv2.erode(mask, np.ones((7, 7), np.uint8)).astype(bool)


def clahe(gray: np.ndarray) -> np.ndarray:
    return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)


def quality_check(green: np.ndarray, enhanced: np.ndarray, mask: np.ndarray) -> dict:
    if mask.sum() < 0.2 * mask.size:
        mask = np.ones_like(mask, bool)
    blur = float(cv2.Laplacian(enhanced, cv2.CV_64F)[mask].var())
    vals = green[mask]
    bright = float(vals.mean())
    clipped = float(((vals < 8) | (vals > 247)).mean())
    issues = []
    if blur < BLUR_MIN:
        issues.append("Image looks blurred or out of focus.")
    if bright < BRIGHT_MIN:
        issues.append("Image is too dark (under-exposed).")
    if bright > BRIGHT_MAX:
        issues.append("Image is too bright (over-exposed).")
    if clipped > CLIP_MAX:
        issues.append("Large areas are over- or under-exposed.")
    return {
        "passed": not issues,
        "sharpness": round(blur, 1),
        "brightness": round(bright, 1),
        "clipped_fraction": round(clipped, 3),
        "issues": issues,
        "thresholds": {"sharpness_min": BLUR_MIN, "brightness_range": [BRIGHT_MIN, BRIGHT_MAX], "clipped_max": CLIP_MAX},
    }


def preprocess(img: np.ndarray) -> dict:
    """Returns the display steps, the normalised model input and the quality report."""
    sq = crop_to_fov(img)
    disp = cv2.resize(sq, (DISPLAY_SIZE, DISPLAY_SIZE), interpolation=cv2.INTER_AREA)
    mask = fov_mask(disp)
    green = disp[:, :, 1]
    enhanced = clahe(green)
    enhanced[~mask] = 0
    small = cv2.resize(enhanced, (MODEL_SIZE, MODEL_SIZE), interpolation=cv2.INTER_AREA)
    norm = small.astype(np.float32) / 255.0
    norm = (norm - norm.mean()) / (norm.std() + 1e-6)
    norm_view = cv2.normalize(norm, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    return {
        "original": disp,
        "green": green,
        "clahe": enhanced,
        "resized": norm_view,
        "input": norm,
        "mask": mask,
        "quality": quality_check(green, enhanced, mask),
    }


def model_input_from_bgr(img: np.ndarray) -> np.ndarray:
    return preprocess(img)["input"]
