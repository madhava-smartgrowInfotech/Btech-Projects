"""Image loading, preprocessing and overlay helpers shared by the API and the training scripts."""
import io

import cv2
import numpy as np
from PIL import Image

CLS_SIZE = 224  # classifier input
SEG_SIZE = 256  # U-Net input
VIEW_SIZE = 512  # images shown in the UI
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


class ImageError(ValueError):
    pass


def load_image(data: bytes, filename: str = ""):
    """Return (gray uint8, rgb uint8, meta). Accepts PNG / JPG / DICOM."""
    name = filename.lower()
    is_dicom = name.endswith((".dcm", ".dicom")) or data[128:132] == b"DICM"
    if is_dicom:
        import pydicom
        from pydicom.pixels import apply_voi_lut

        try:
            ds = pydicom.dcmread(io.BytesIO(data), force=True)
            arr = ds.pixel_array.astype(np.float32)
        except Exception as e:  # noqa: BLE001
            raise ImageError(f"Could not read the DICOM file: {e}")
        if arr.ndim == 3 and arr.shape[-1] != 3:  # multi-frame: take the middle slice
            arr = arr[arr.shape[0] // 2]
        try:
            arr = apply_voi_lut(arr, ds).astype(np.float32)
        except Exception:  # noqa: BLE001
            arr = arr * float(getattr(ds, "RescaleSlope", 1)) + float(getattr(ds, "RescaleIntercept", 0))
        if arr.ndim == 3:
            arr = arr.mean(axis=-1)
        if getattr(ds, "PhotometricInterpretation", "") == "MONOCHROME1":
            arr = arr.max() - arr
        arr = (arr - arr.min()) / max(float(arr.max() - arr.min()), 1e-6) * 255
        gray = arr.astype(np.uint8)
        rgb = np.stack([gray] * 3, axis=-1)
        meta = {"format": "DICOM", "dicom_modality": str(getattr(ds, "Modality", ""))}
    else:
        try:
            img = Image.open(io.BytesIO(data))
            img.load()
        except Exception:  # noqa: BLE001
            raise ImageError("The file is not a readable PNG, JPG or DICOM image")
        if img.format not in ("PNG", "JPEG", "MPO"):
            raise ImageError(f"Unsupported image format {img.format}; use PNG, JPG or DICOM")
        rgb = np.array(img.convert("RGB"))
        gray = np.array(img.convert("L"))
        meta = {"format": "JPEG" if img.format == "MPO" else img.format, "dicom_modality": ""}
    if min(gray.shape) < 64:
        raise ImageError("Image is too small (minimum 64 px per side)")
    meta["width"], meta["height"] = int(gray.shape[1]), int(gray.shape[0])
    return gray, rgb, meta


def colourfulness(rgb: np.ndarray) -> float:
    """Mean HSV saturation (0-1) of reasonably bright pixels; radiographs are close to 0."""
    small = cv2.resize(rgb, (128, 128), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(small, cv2.COLOR_RGB2HSV)
    bright = hsv[..., 2] > 40
    if bright.sum() < 50:
        return 0.0
    return float(hsv[..., 1][bright].mean() / 255.0)


def preprocess(gray: np.ndarray, size: int = CLS_SIZE):
    """Resize -> denoise -> CLAHE. Returns the three intermediate uint8 images."""
    resized = cv2.resize(gray, (size, size), interpolation=cv2.INTER_AREA)
    denoised = cv2.fastNlMeansDenoising(resized, None, h=5, templateWindowSize=7, searchWindowSize=15)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(denoised)
    return {"resized": resized, "denoised": denoised, "enhanced": clahe}


def to_tensor_array(enhanced: np.ndarray) -> np.ndarray:
    """uint8 HxW -> float32 3xHxW normalised with ImageNet statistics."""
    x = enhanced.astype(np.float32) / 255.0
    x = np.stack([x, x, x], axis=0)
    return (x - MEAN[:, None, None]) / STD[:, None, None]


def to_seg_array(gray: np.ndarray) -> np.ndarray:
    """U-Net input: CLAHE-enhanced 256x256, scaled 0-1, shape 1xHxW."""
    enh = preprocess(gray, SEG_SIZE)["enhanced"]
    return (enh.astype(np.float32) / 255.0)[None]


def ct_lung_mask(gray: np.ndarray) -> np.ndarray:
    """Classical CT lung field estimate: dark regions enclosed by the body outline."""
    g = cv2.GaussianBlur(gray, (5, 5), 0)
    _, body = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(body)
    if n <= 1:
        return np.ones_like(gray, dtype=np.uint8)
    largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    body = (labels == largest).astype(np.uint8) * 255
    contours, _ = cv2.findContours(body, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filled = np.zeros_like(body)
    cv2.drawContours(filled, contours, -1, 255, thickness=cv2.FILLED)
    lungs = ((filled > 0) & (body == 0)).astype(np.uint8)
    lungs = cv2.morphologyEx(lungs, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(lungs)
    keep = np.zeros_like(lungs)
    min_area = 0.005 * gray.size
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= min_area:
            keep[labels == i] = 1
    if keep.sum() < 0.02 * gray.size:
        return (filled > 0).astype(np.uint8)  # fall back to the whole body region
    return keep


def png_bytes(img: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".png", cv2.cvtColor(img, cv2.COLOR_RGB2BGR) if img.ndim == 3 else img)
    return buf.tobytes()


def view(img: np.ndarray) -> np.ndarray:
    return cv2.resize(img, (VIEW_SIZE, VIEW_SIZE), interpolation=cv2.INTER_LINEAR)


def mask_overlay(gray: np.ndarray, mask: np.ndarray) -> np.ndarray:
    base = cv2.cvtColor(view(gray), cv2.COLOR_GRAY2RGB).astype(np.float32)
    m = cv2.resize(mask.astype(np.uint8), (VIEW_SIZE, VIEW_SIZE), interpolation=cv2.INTER_NEAREST) > 0
    tint = np.array([34, 197, 94], dtype=np.float32)
    base[m] = base[m] * 0.6 + tint * 0.4
    out = base.clip(0, 255).astype(np.uint8)
    contours, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(out, contours, -1, (22, 163, 74), 2)
    return out


def heatmap_overlay(gray: np.ndarray, cam: np.ndarray) -> np.ndarray:
    base = cv2.cvtColor(view(gray), cv2.COLOR_GRAY2RGB).astype(np.float32)
    c = cv2.resize(cam.astype(np.float32), (VIEW_SIZE, VIEW_SIZE))
    colour = cv2.cvtColor(cv2.applyColorMap((c * 255).astype(np.uint8), cv2.COLORMAP_JET), cv2.COLOR_BGR2RGB)
    alpha = (0.25 + 0.35 * c)[..., None]
    return (base * (1 - alpha) + colour * alpha).clip(0, 255).astype(np.uint8)
