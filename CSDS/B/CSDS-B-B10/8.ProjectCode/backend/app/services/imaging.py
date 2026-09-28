"""Image I/O helpers and sub-band views."""
import base64
from pathlib import Path

import cv2
import numpy as np
import pywt

from ..db import SAMPLE_DIR

MAX_SIDE = 1024
SAMPLE_KINDS = {"visdrone": SAMPLE_DIR / "visdrone" / "images", "sipi": SAMPLE_DIR / "sipi"}
SEQ_DIR = SAMPLE_DIR / "visdrone" / "sequences"
IMG_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}


def decode(data: bytes, limit: bool = True) -> tuple:
    """Bytes -> RGB (or single-channel) uint8 array. Returns (img, resized_flag)."""
    arr = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_UNCHANGED)
    if arr is None:
        raise ValueError("Unsupported or corrupt image file")
    if arr.dtype != np.uint8:
        arr = cv2.normalize(arr, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    if arr.ndim == 3:
        if arr.shape[2] == 4:
            arr = arr[:, :, :3]
        arr = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
        if np.array_equal(arr[:, :, 0], arr[:, :, 1]) and np.array_equal(arr[:, :, 1], arr[:, :, 2]):
            arr = arr[:, :, 0]
    resized = False
    if limit and max(arr.shape[:2]) > MAX_SIDE:
        s = MAX_SIDE / max(arr.shape[:2])
        arr = cv2.resize(arr, (round(arr.shape[1] * s), round(arr.shape[0] * s)), interpolation=cv2.INTER_AREA)
        resized = True
    return np.ascontiguousarray(arr), resized


def read_path(path: Path, limit: bool = True):
    return decode(Path(path).read_bytes(), limit)


def to_bgr(img):
    return cv2.cvtColor(img, cv2.COLOR_RGB2BGR) if img.ndim == 3 else img


def png_bytes(img: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".png", to_bgr(img), [cv2.IMWRITE_PNG_COMPRESSION, 1])
    return buf.tobytes()


def jpg_bytes(img: np.ndarray, q: int = 80) -> bytes:
    ok, buf = cv2.imencode(".jpg", to_bgr(img), [cv2.IMWRITE_JPEG_QUALITY, q])
    return buf.tobytes()


def preview_b64(img: np.ndarray, max_side: int = 640, lossless: bool = True) -> str:
    """Data URL for display (downscaled for the browser; lossless PNG keeps the noise pattern honest)."""
    if max(img.shape[:2]) > max_side:
        s = max_side / max(img.shape[:2])
        img = cv2.resize(img, (max(1, round(img.shape[1] * s)), max(1, round(img.shape[0] * s))),
                         interpolation=cv2.INTER_NEAREST)
    if lossless:
        return "data:image/png;base64," + base64.b64encode(png_bytes(img)).decode()
    return "data:image/jpeg;base64," + base64.b64encode(jpg_bytes(img)).decode()


def gray(img):
    return img if img.ndim == 2 else cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)


def subband_views(img: np.ndarray) -> dict:
    """PyWavelets Haar DWT of the luminance - LL, LH, HL, HH scaled for display."""
    ll, (lh, hl, hh) = pywt.dwt2(gray(img).astype(np.float64), "haar")
    out = {}
    for name, band in (("LL", ll), ("LH", lh), ("HL", hl), ("HH", hh)):
        if name == "LL":
            v = band / 2.0
        else:
            v = np.clip(np.abs(band) * 4.0, 0, 255)
        out[name] = preview_b64(np.clip(v, 0, 255).astype(np.uint8), 320)
    return out


def histograms(img: np.ndarray) -> dict:
    chans = ["gray"] if img.ndim == 2 else ["r", "g", "b"]
    out = {}
    for i, c in enumerate(chans):
        ch = img if img.ndim == 2 else img[:, :, i]
        out[c] = np.bincount(ch.reshape(-1), minlength=256).tolist()
    return out


def list_samples() -> list:
    items = []
    for kind, d in SAMPLE_KINDS.items():
        if not d.exists():
            continue
        for p in sorted(d.iterdir()):
            if p.suffix.lower() in IMG_EXT:
                items.append({"kind": kind, "name": p.name})
    return items


def sample_path(kind: str, name: str) -> Path:
    d = SAMPLE_KINDS.get(kind)
    if d is None:
        raise ValueError("Unknown sample set")
    p = (d / name).resolve()
    if p.parent != d.resolve() or not p.exists():
        raise ValueError("Sample image not found")
    return p


def list_sequences() -> list:
    if not SEQ_DIR.exists():
        return []
    out = []
    for d in sorted(SEQ_DIR.iterdir()):
        if d.is_dir():
            frames = sorted(p for p in d.iterdir() if p.suffix.lower() in IMG_EXT)
            if frames:
                out.append({"name": d.name, "frames": len(frames)})
    return out


def sequence_frames(name: str) -> list:
    d = (SEQ_DIR / name).resolve()
    if d.parent != SEQ_DIR.resolve() or not d.is_dir():
        raise ValueError("Sequence not found")
    return sorted(p for p in d.iterdir() if p.suffix.lower() in IMG_EXT)
