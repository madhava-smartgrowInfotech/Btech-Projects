"""Security analysis: entropy, histogram uniformity, correlation, NPCR/UACI, PSNR/MSE/SSIM, key sensitivity."""
import math
import time

import numpy as np
from skimage.metrics import structural_similarity

from . import cipher as C
from .imaging import histograms, preview_b64

CHI2_CRIT = 293.2478          # chi-square critical value, 255 d.o.f., alpha = 0.05
IDEAL_NPCR = 99.6094
IDEAL_UACI = 33.4635


def _channels(img):
    return [img] if img.ndim == 2 else [img[:, :, i] for i in range(img.shape[2])]


def entropy(img) -> dict:
    vals = []
    for ch in _channels(img):
        p = np.bincount(ch.reshape(-1), minlength=256) / ch.size
        p = p[p > 0]
        vals.append(float(-(p * np.log2(p)).sum()))
    return {"per_channel": vals, "mean": float(np.mean(vals))}


def chi_square(img) -> dict:
    vals = []
    for ch in _channels(img):
        obs = np.bincount(ch.reshape(-1), minlength=256).astype(np.float64)
        exp = ch.size / 256.0
        vals.append(float(((obs - exp) ** 2 / exp).sum()))
    return {"per_channel": vals, "critical": CHI2_CRIT, "uniform": bool(all(v < CHI2_CRIT for v in vals))}


_DIRS = {"horizontal": (0, 1), "vertical": (1, 0), "diagonal": (1, 1)}


def correlation(img, seed: int = 7, scatter: int = 0) -> dict:
    """Pearson correlation over every adjacent pixel pair (mean over channels); scatter = sampled pairs for plots."""
    rng = np.random.default_rng(seed)
    out, pts = {}, {}
    h, w = img.shape[:2]
    for name, (dy, dx) in _DIRS.items():
        if h - dy < 1 or w - dx < 1:
            out[name] = 0.0
            continue
        coefs = []
        for ch in _channels(img):
            a = ch[:h - dy, :w - dx].reshape(-1).astype(np.float64)
            b = ch[dy:, dx:].reshape(-1).astype(np.float64)
            if a.std() == 0 or b.std() == 0:
                coefs.append(1.0 if np.array_equal(a, b) else 0.0)
            else:
                coefs.append(float(np.corrcoef(a, b)[0, 1]))
            if scatter and name not in pts:
                idx = rng.integers(0, a.size, scatter)
                pts[name] = np.stack([a[idx], b[idx]], 1).astype(int).tolist()
        out[name] = float(np.mean(coefs))
    if scatter:
        out["scatter"] = pts
    return out


def npcr_uaci(c1, c2) -> dict:
    diff = c1 != c2
    uaci = np.abs(c1.astype(np.int16) - c2.astype(np.int16)).mean() / 255.0 * 100
    return {"npcr": float(diff.mean() * 100), "uaci": float(uaci)}


def mse_psnr(a, b) -> dict:
    mse = float(np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2))
    psnr = float("inf") if mse == 0 else 10 * math.log10(255.0 ** 2 / mse)
    return {"mse": mse, "psnr": psnr}


def ssim(a, b) -> float:
    if min(a.shape[:2]) < 7:
        return float(np.array_equal(a, b))
    kw = {"channel_axis": 2} if a.ndim == 3 else {}
    return float(structural_similarity(a, b, data_range=255, **kw))


def jsonable(x):
    """Replace inf / nan so the result can be stored as JSON."""
    if isinstance(x, dict):
        return {k: jsonable(v) for k, v in x.items()}
    if isinstance(x, list):
        return [jsonable(v) for v in x]
    if isinstance(x, float) and (math.isinf(x) or math.isnan(x)):
        return "inf" if x > 0 else None
    return x


def analyze(img: np.ndarray, key: str, nonce: str, seed: int = 11, thumbs: bool = True) -> dict:
    rng = np.random.default_rng(seed)
    t0 = time.perf_counter()
    enc = C.encrypt(img, key, nonce)
    t1 = time.perf_counter()
    dec = C.decrypt(enc, key, nonce)
    t2 = time.perf_counter()

    # plaintext sensitivity (differential attack): change one pixel by 1, same key and nonce
    diffs = []
    for _ in range(3):
        p2 = img.copy()
        idx = int(rng.integers(0, p2.size))
        p2.flat[idx] = (int(p2.flat[idx]) + 1) % 256
        r = npcr_uaci(enc, C.encrypt(p2, key, nonce))
        r["pixel_index"] = idx
        diffs.append(r)

    # key sensitivity: flip single key bits
    key_tests = []
    wrong_dec = None
    for bit in rng.choice(256, 4, replace=False):
        k2 = C.flip_key_bit(key, int(bit))
        enc2 = C.encrypt(img, k2, nonce)
        d2 = C.decrypt(enc, k2, nonce)
        if wrong_dec is None:
            wrong_dec = d2
        key_tests.append({
            "bit": int(bit),
            "cipher_diff": npcr_uaci(enc, enc2),
            "wrong_key_decrypt": {**npcr_uaci(img, d2), **mse_psnr(img, d2)},
        })

    res = {
        "image": {"width": int(img.shape[1]), "height": int(img.shape[0]),
                  "channels": 1 if img.ndim == 2 else int(img.shape[2]), "bytes": int(img.size)},
        "timing": {"encrypt_ms": (t1 - t0) * 1000, "decrypt_ms": (t2 - t1) * 1000,
                   "throughput_mbps": img.size / 1e6 / max(t1 - t0, 1e-9)},
        "entropy": {"plain": entropy(img), "cipher": entropy(enc)},
        "chi_square": {"plain": chi_square(img), "cipher": chi_square(enc)},
        "correlation": {"plain": correlation(img, scatter=400), "cipher": correlation(enc, scatter=400)},
        "differential": {"trials": diffs,
                         "npcr": float(np.mean([d["npcr"] for d in diffs])),
                         "uaci": float(np.mean([d["uaci"] for d in diffs])),
                         "ideal_npcr": IDEAL_NPCR, "ideal_uaci": IDEAL_UACI},
        "quality": {"decrypted": {**mse_psnr(img, dec), "ssim": ssim(img, dec), "identical": bool(np.array_equal(img, dec)),
                                  "plain_sha256": C.pixel_sha256(img), "decrypted_sha256": C.pixel_sha256(dec)},
                    "cipher_vs_plain": {**mse_psnr(img, enc), "ssim": ssim(img, enc)}},
        "key_sensitivity": {"tests": key_tests,
                            "min_cipher_npcr": min(t["cipher_diff"]["npcr"] for t in key_tests),
                            "wrong_key_recovers": any(t["wrong_key_decrypt"]["npcr"] < 50 for t in key_tests)},
        "key_space": {"key_bits": 256, "log2": 256, "nonce_bits": 128,
                      "note": "Brute force needs 2^256 trials; 2^100 is the usual safety threshold."},
        "histograms": {"plain": histograms(img), "cipher": histograms(enc)},
    }
    if thumbs:
        res["thumbs"] = {"plain": preview_b64(img, 200), "cipher": preview_b64(enc, 200),
                         "decrypted": preview_b64(dec, 200), "wrong_key": preview_b64(wrong_dec, 200)}
    return jsonable(res)
