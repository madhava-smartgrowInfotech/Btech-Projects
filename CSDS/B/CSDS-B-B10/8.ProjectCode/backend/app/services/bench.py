"""Speed comparison: SkyCipher vs AES-256-CTR vs ChaCha20 on the same images."""
import os
import time

import cv2
import numpy as np
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from . import cipher as C
from .metrics import correlation, entropy


def _aes_ctr(key: bytes, nonce: bytes, data: bytes, encrypt: bool) -> bytes:
    c = Cipher(algorithms.AES(key), modes.CTR(nonce))
    ctx = c.encryptor() if encrypt else c.decryptor()
    return ctx.update(data) + ctx.finalize()


def _chacha(key: bytes, nonce: bytes, data: bytes, encrypt: bool) -> bytes:
    c = Cipher(algorithms.ChaCha20(key, nonce), mode=None)
    ctx = c.encryptor() if encrypt else c.decryptor()
    return ctx.update(data) + ctx.finalize()


def _time(fn, repeats):
    best = []
    for _ in range(repeats):
        t = time.perf_counter()
        out = fn()
        best.append((time.perf_counter() - t) * 1000)
    return float(np.median(best)), out


def run(images: list, size: int = 512, repeats: int = 3) -> dict:
    key_hex = C.new_key()
    key = bytes.fromhex(key_hex)
    rows = {name: {"enc_ms": [], "dec_ms": [], "entropy": [], "corr_h": [], "exact": True}
            for name in ("SkyCipher", "AES-256-CTR", "ChaCha20")}
    for img in images:
        img = cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)
        img = np.ascontiguousarray(img)
        raw = img.tobytes()
        nonce_hex = C.new_nonce()
        nonce = bytes.fromhex(nonce_hex)
        C.encrypt(img, key_hex, nonce_hex)  # warm-up (builds the cached permutation for this size)

        ms, enc = _time(lambda: C.encrypt(img, key_hex, nonce_hex), repeats)
        dms, dec = _time(lambda: C.decrypt(enc, key_hex, nonce_hex), repeats)
        _add(rows["SkyCipher"], ms, dms, enc, np.array_equal(dec, img))

        for name, fn in (("AES-256-CTR", _aes_ctr), ("ChaCha20", _chacha)):
            ms, ct = _time(lambda: fn(key, nonce, raw, True), repeats)
            dms, pt = _time(lambda: fn(key, nonce, ct, False), repeats)
            _add(rows[name], ms, dms, np.frombuffer(ct, np.uint8).reshape(img.shape), pt == raw)

    nbytes = size * size * (1 if images[0].ndim == 2 else 3)
    summary = []
    for name, r in rows.items():
        enc_ms, dec_ms = float(np.mean(r["enc_ms"])), float(np.mean(r["dec_ms"]))
        summary.append({
            "algorithm": name, "enc_ms": enc_ms, "dec_ms": dec_ms,
            "enc_mbps": nbytes / 1e6 / (enc_ms / 1000), "dec_mbps": nbytes / 1e6 / (dec_ms / 1000),
            "fps_capacity": 1000.0 / (enc_ms + dec_ms),
            "cipher_entropy": float(np.mean(r["entropy"])), "cipher_corr_h": float(np.mean(r["corr_h"])),
            "lossless": r["exact"],
        })
    return {"size": size, "images": len(images), "repeats": repeats, "bytes_per_image": nbytes,
            "cpu": os.cpu_count(), "results": summary}


def _add(row, ms, dms, enc, exact):
    row["enc_ms"].append(ms)
    row["dec_ms"].append(dms)
    row["entropy"].append(entropy(enc)["mean"])
    row["corr_h"].append(abs(correlation(enc)["horizontal"]))
    row["exact"] = row["exact"] and bool(exact)
