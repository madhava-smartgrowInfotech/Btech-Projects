"""The send / receive pipeline shared by the API, the benchmark and ml/eval.py."""
import time

import numpy as np

from . import crypto, lsb, metrics


def _ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 3)


def hide(public_pem: str, filename: str, data: bytes, cover: np.ndarray) -> dict:
    t = time.perf_counter()
    bundle, enc_info = crypto.encrypt_bundle(public_pem, filename, data)
    encrypt_ms = _ms(t)

    cap = lsb.capacity_bytes(cover)
    t = time.perf_counter()
    stego = lsb.embed(cover, bundle)  # raises StegoError when it does not fit
    embed_ms = _ms(t)

    t = time.perf_counter()
    png = lsb.to_png_bytes(stego)
    encode_ms = _ms(t)

    t = time.perf_counter()
    quality = metrics.imperceptibility(cover, stego)
    metrics_ms = _ms(t)

    h, w = cover.shape[:2]
    return {
        "stego": stego, "stego_png": png, "bundle_len": len(bundle),
        "info": enc_info,
        "capacity": {
            "width": w, "height": h, "pixels": w * h,
            "max_bundle_bytes": cap,
            "max_file_bytes": max(0, cap - (len(bundle) - len(data))),
            "bundle_bytes": len(bundle), "used_pct": round(100 * len(bundle) / cap, 3),
            "payload_bits_per_pixel": round(len(bundle) * 8 / (w * h), 5),
        },
        "timings_ms": {"encrypt": encrypt_ms, "embed": embed_ms, "png_encode": encode_ms, "metrics": metrics_ms},
        "quality": quality,
    }


def reveal(private_pem: str, stego: np.ndarray) -> dict:
    t = time.perf_counter()
    bundle = lsb.extract(stego)
    extract_ms = _ms(t)
    t = time.perf_counter()
    name, data, info = crypto.decrypt_bundle(private_pem, bundle)
    decrypt_ms = _ms(t)
    return {"filename": name, "data": data, "info": info, "bundle_len": len(bundle),
            "timings_ms": {"extract": extract_ms, "decrypt": decrypt_ms}}
