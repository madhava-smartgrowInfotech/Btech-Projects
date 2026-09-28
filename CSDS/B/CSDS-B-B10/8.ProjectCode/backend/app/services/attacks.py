"""Channel-damage tests: corrupt the cipher image, decrypt, and measure how much of the image recovers."""
import cv2
import numpy as np

from . import cipher as C
from .imaging import preview_b64
from .metrics import jsonable, mse_psnr, ssim

DEFAULT_SUITE = [
    {"type": "salt_pepper", "level": 0.001},
    {"type": "salt_pepper", "level": 0.01},
    {"type": "salt_pepper", "level": 0.05},
    {"type": "gaussian", "level": 2},
    {"type": "gaussian", "level": 10},
    {"type": "crop", "level": 1 / 16},
    {"type": "crop", "level": 1 / 4},
]


def apply_attack(enc: np.ndarray, kind: str, level: float, seed: int = 3) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = enc.copy()
    if kind == "salt_pepper":
        mask = rng.random(enc.shape[:2]) < level
        vals = np.where(rng.random(int(mask.sum())) < 0.5, 0, 255).astype(np.uint8)
        out[mask] = vals[:, None] if enc.ndim == 3 else vals
    elif kind == "gaussian":
        noise = rng.normal(0, level, enc.shape)
        out = np.clip(enc.astype(np.float64) + noise, 0, 255).round().astype(np.uint8)
    elif kind == "crop":
        h, w = enc.shape[:2]
        side = np.sqrt(level)
        ch, cw = max(1, int(h * side)), max(1, int(w * side))
        y0, x0 = (h - ch) // 2, (w - cw) // 2
        out[y0:y0 + ch, x0:x0 + cw] = 0
    else:
        raise ValueError(f"Unknown attack type: {kind}")
    return out


def label(kind: str, level: float) -> str:
    if kind == "salt_pepper":
        return f"Salt & pepper {level * 100:g}%"
    if kind == "gaussian":
        return f"Gaussian noise sigma={level:g}"
    return f"Cropping {level * 100:g}% of area"


def run(img: np.ndarray, key: str, nonce: str, suite=None, previews: bool = True) -> dict:
    enc = C.encrypt(img, key, nonce)
    results = []
    for a in suite or DEFAULT_SUITE:
        kind, level = a["type"], float(a["level"])
        attacked = apply_attack(enc, kind, level)
        rec = C.decrypt(attacked, key, nonce)
        filtered = cv2.medianBlur(rec, 3)
        r = {
            "type": kind, "level": level, "label": label(kind, level),
            "cipher_bytes_changed_pct": float((attacked != enc).mean() * 100),
            "recovered": {**mse_psnr(img, rec), "ssim": ssim(img, rec),
                          "intact_pct": float((rec == img).mean() * 100)},
            "median_filtered": {**mse_psnr(img, filtered), "ssim": ssim(img, filtered)},
        }
        if previews:
            r["attacked_preview"] = preview_b64(attacked, 320)
            r["recovered_preview"] = preview_b64(rec, 320)
            r["filtered_preview"] = preview_b64(filtered, 320)
        results.append(r)
    return jsonable({"results": results})
