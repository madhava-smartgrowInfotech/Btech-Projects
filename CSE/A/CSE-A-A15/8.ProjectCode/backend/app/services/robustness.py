"""Attack the stego image and report whether the payload still comes out intact."""
import io
import time

import numpy as np
from PIL import Image

from . import crypto, lsb

EXPLAIN = {
    "png_resave": "Lossless re-save. Pixel values are untouched, so the payload survives.",
    "jpeg_q95": "JPEG discards low-order detail. Even at quality 95 the least significant bits are rewritten.",
    "jpeg_q75": "JPEG at quality 75 quantises every 8x8 block; the hidden bits are destroyed.",
    "jpeg_q50": "JPEG at quality 50 quantises heavily; the hidden bits are destroyed.",
    "noise_s1": "Gaussian noise (sigma 1) flips about half of the least significant bits.",
    "noise_s3": "Gaussian noise (sigma 3) flips about half of the least significant bits.",
    "resize_90": "Resampling to 90% moves every pixel; the bit stream is no longer aligned.",
    "crop_bottom_10": "Only the bottom rows are removed. Bits are stored from the top row downwards, so the payload "
                      "survives while it fits in the rows that remain.",
    "crop_left_10": "Removing left columns changes the row width, so every later bit lands in the wrong place.",
}


def _png_resave(a):
    return lsb_roundtrip(a)


def lsb_roundtrip(a):
    return np.array(Image.open(io.BytesIO(lsb.to_png_bytes(a))).convert("RGB"))


def _jpeg(q):
    def f(a):
        buf = io.BytesIO()
        Image.fromarray(a, "RGB").save(buf, format="JPEG", quality=q)
        return np.array(Image.open(io.BytesIO(buf.getvalue())).convert("RGB"))
    return f


def _noise(sigma):
    def f(a):
        rng = np.random.default_rng(7)
        return np.clip(np.rint(a + rng.normal(0, sigma, a.shape)), 0, 255).astype(np.uint8)
    return f


def _resize(frac):
    def f(a):
        h, w = a.shape[:2]
        img = Image.fromarray(a, "RGB").resize((int(w * frac), int(h * frac)), Image.BILINEAR)
        return np.array(img)
    return f


def _crop_bottom(frac):
    return lambda a: a[: int(a.shape[0] * (1 - frac))].copy()


def _crop_left(frac):
    return lambda a: a[:, int(a.shape[1] * frac):].copy()


ATTACKS = [
    ("png_resave", "Lossless PNG re-save", _png_resave),
    ("jpeg_q95", "JPEG quality 95", _jpeg(95)),
    ("jpeg_q75", "JPEG quality 75", _jpeg(75)),
    ("jpeg_q50", "JPEG quality 50", _jpeg(50)),
    ("noise_s1", "Gaussian noise sigma 1", _noise(1)),
    ("noise_s3", "Gaussian noise sigma 3", _noise(3)),
    ("resize_90", "Resize to 90%", _resize(0.9)),
    ("crop_bottom_10", "Crop bottom 10%", _crop_bottom(0.10)),
    ("crop_left_10", "Crop left 10%", _crop_left(0.10)),
]


def run_attacks(stego: np.ndarray, private_pem: str, original_sha256: str, bundle_len: int) -> list[dict]:
    n_bits = (bundle_len + 4) * 8
    ref_bits = lsb.lsb_stream(stego, n_bits)
    results = []
    for key, label, fn in ATTACKS:
        attacked = fn(stego)
        t = time.perf_counter()
        ber = None
        flat_bits = lsb.lsb_stream(attacked, n_bits)
        m = min(flat_bits.size, ref_bits.size)
        if m:
            ber = round(float(np.mean(flat_bits[:m] != ref_bits[:m])), 4)
        status, detail = "lost", ""
        try:
            bundle = lsb.extract(attacked)
            name, data, info = crypto.decrypt_bundle(private_pem, bundle)
            if info["output_sha256"] == original_sha256:
                status, detail = "recovered", "Byte-for-byte identical to the original file."
            else:
                detail = "Decrypted but hash differs."
        except (lsb.StegoError, crypto.CryptoError) as exc:
            detail = str(exc)
        except Exception as exc:  # corrupted header can raise anything while parsing
            detail = f"Payload could not be parsed ({type(exc).__name__})"
        results.append({
            "attack": key, "label": label, "status": status, "detail": detail,
            "bit_error_rate": ber, "why": EXPLAIN[key],
            "elapsed_ms": round((time.perf_counter() - t) * 1000, 2),
            "size": f"{attacked.shape[1]}x{attacked.shape[0]}",
        })
    return results
