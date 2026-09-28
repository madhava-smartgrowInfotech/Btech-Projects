"""SkyCipher engine.

Pipeline (encryption):
  1. Integer Haar lifting DWT in Z_256 on every channel -> LL | HL / LH | HH quadrants (exactly reversible).
  2. Key-driven permutation of all coefficients (Henon map key stream, argsort).
  3. XOR diffusion with 2-D logistic (sine-modulated) key streams, chained with modular addition and a
     3-bit rotation (add-rotate-xor), forward then backward, two rounds -> a one-pixel change spreads over
     every byte and every bit-plane of the cipher image.

Decryption applies the exact inverse of every step, so the recovered image is bit-identical.
Key: 256 bits. Nonce: 128 bits, public, one per image / video frame (so key streams never repeat).
"""
import hashlib
import os
from collections import OrderedDict

import numpy as np

KEY_BYTES = 32
NONCE_BYTES = 16
LANES = 4096          # independent chaotic trajectories iterated in parallel (vectorised)
BURN_IN = 64          # iterations discarded before key stream bytes are taken
ROUNDS = 2            # diffusion rounds (each = forward + backward chained pass)
ROT = 3               # bit rotation applied after every diffusion pass

_perm_cache: "OrderedDict[tuple, tuple]" = OrderedDict()


# ---------------------------------------------------------------- keys
def new_key() -> str:
    return os.urandom(KEY_BYTES).hex()


def new_nonce() -> str:
    return os.urandom(NONCE_BYTES).hex()


def parse_key(key_hex: str) -> bytes:
    key_hex = (key_hex or "").strip().lower()
    try:
        key = bytes.fromhex(key_hex)
    except ValueError:
        raise ValueError("Key must be hexadecimal")
    if len(key) != KEY_BYTES:
        raise ValueError("Key must be 64 hex characters (256 bits)")
    return key


def parse_nonce(nonce_hex: str) -> bytes:
    try:
        nonce = bytes.fromhex((nonce_hex or "").strip())
    except ValueError:
        raise ValueError("Nonce must be hexadecimal")
    if len(nonce) != NONCE_BYTES:
        raise ValueError("Nonce must be 32 hex characters (128 bits)")
    return nonce


def flip_key_bit(key_hex: str, bit: int) -> str:
    key = bytearray(parse_key(key_hex))
    key[bit // 8] ^= 1 << (bit % 8)
    return key.hex()


def key_fingerprint(key_hex: str) -> str:
    return hashlib.sha256(b"fp" + parse_key(key_hex)).hexdigest()[:12]


def _lane_seeds(key: bytes, nonce: bytes, label: bytes) -> tuple:
    """Two uniform vectors in (0, 1) derived from key+nonce+label (SHAKE-256)."""
    raw = hashlib.shake_256(b"skycipher|" + label + b"|" + key + nonce).digest(LANES * 16)
    u = np.frombuffer(raw, dtype="<u8").reshape(2, LANES)
    return ((u[0] >> 11).astype(np.float64) + 0.5) / 2.0 ** 53, ((u[1] >> 11).astype(np.float64) + 0.5) / 2.0 ** 53


# ---------------------------------------------------------------- chaotic maps
def _slmm(x, y):
    """2-D logistic map with sine modulation (alpha=1, beta=3); stays inside (0, 1)."""
    x = (np.sin(np.pi * y) + 3.0) * x * (1.0 - x)
    y = (np.sin(np.pi * x) + 3.0) * y * (1.0 - y)
    # keep trajectories off the absorbing points 0 and 1 (deterministic, so decryption matches)
    x = np.where((x < 1e-9) | (x > 1 - 1e-9), 0.3183098861837907, x)
    y = np.where((y < 1e-9) | (y > 1 - 1e-9), 0.7071067811865476, y)
    return x, y


def _henon(x, y, a=1.4, b=0.3):
    x, y = 1.0 - a * x * x + y, b * x
    bad = ~np.isfinite(x) | (np.abs(x) > 2.0)
    if bad.any():
        x = np.where(bad, 0.1, x)
        y = np.where(bad, 0.05, y)
    return x, y


def keystream(key: bytes, nonce: bytes, label: bytes, n: int) -> np.ndarray:
    """n key-stream bytes from the 2-D logistic map (8 bytes per lane per iteration)."""
    x, y = _lane_seeds(key, nonce, label)
    x = 0.01 + 0.98 * x
    y = 0.01 + 0.98 * y
    for _ in range(BURN_IN):
        x, y = _slmm(x, y)
    steps = -(-n // (LANES * 8))
    words = np.empty((steps, 2, LANES), dtype=np.uint64)
    for s in range(steps):
        x, y = _slmm(x, y)
        # bits 16..47 of the 52-bit fraction of each coordinate -> 4 bytes each
        words[s, 0] = (x * 2.0 ** 52).astype(np.uint64) >> np.uint64(16)
        words[s, 1] = (y * 2.0 ** 52).astype(np.uint64) >> np.uint64(16)
    b = words.view(np.uint8).reshape(-1, 8)[:, :4]
    return np.ascontiguousarray(b).reshape(-1)[:n]


def permutation(key: bytes, n: int) -> tuple:
    """Key-dependent permutation of n positions from the Henon map (cached per key and size)."""
    ck = (key, n)
    if ck in _perm_cache:
        _perm_cache.move_to_end(ck)
        return _perm_cache[ck]
    u, v = _lane_seeds(key, b"", b"perm")
    x, y = 0.2 * (u - 0.5), 0.2 * (v - 0.5)
    for _ in range(BURN_IN * 4):
        x, y = _henon(x, y)
    steps = -(-n // LANES)
    seq = np.empty((steps, LANES), dtype=np.float64)
    for s in range(steps):
        x, y = _henon(x, y)
        seq[s] = x
    # fractional part of a scaled trajectory breaks the attractor's density bias
    vals = (seq.reshape(-1)[:n] * 1e6) % 1.0
    perm = np.argsort(vals, kind="stable")
    inv = np.empty_like(perm)
    inv[perm] = np.arange(n)
    _perm_cache[ck] = (perm, inv)
    if len(_perm_cache) > 16:
        _perm_cache.popitem(last=False)
    return perm, inv


# ---------------------------------------------------------------- integer Haar lifting (mod 256)
def _lift_1d(a, axis):
    ev = np.take(a, np.arange(0, a.shape[axis], 2), axis=axis)
    od = np.take(a, np.arange(1, a.shape[axis], 2), axis=axis)
    d = od - ev                      # uint8 arithmetic wraps mod 256
    s = ev + (d >> 1)
    return s, d


def _unlift_1d(s, d, axis):
    ev = s - (d >> 1)
    od = d + ev
    shape = list(s.shape)
    shape[axis] *= 2
    out = np.empty(shape, dtype=np.uint8)
    idx = [slice(None)] * len(shape)
    idx[axis] = slice(0, None, 2)
    out[tuple(idx)] = ev
    idx[axis] = slice(1, None, 2)
    out[tuple(idx)] = od
    return out


def dwt_forward(img: np.ndarray) -> np.ndarray:
    """One-level integer Haar DWT per channel; odd last row/column passes through unchanged."""
    h, w = img.shape[:2]
    he, we = h - h % 2, w - w % 2
    out = img.copy()
    if he == 0 or we == 0:
        return out
    region = img[:he, :we]
    lo, hi = _lift_1d(region, axis=1)            # along width
    ll, lh = _lift_1d(lo, axis=0)                # along height
    hl, hh = _lift_1d(hi, axis=0)
    h2, w2 = he // 2, we // 2
    out[:h2, :w2], out[:h2, w2:we] = ll, hl
    out[h2:he, :w2], out[h2:he, w2:we] = lh, hh
    return out


def dwt_inverse(coef: np.ndarray) -> np.ndarray:
    h, w = coef.shape[:2]
    he, we = h - h % 2, w - w % 2
    out = coef.copy()
    if he == 0 or we == 0:
        return out
    h2, w2 = he // 2, we // 2
    ll, hl = coef[:h2, :w2], coef[:h2, w2:we]
    lh, hh = coef[h2:he, :w2], coef[h2:he, w2:we]
    lo = _unlift_1d(ll, lh, axis=0)
    hi = _unlift_1d(hl, hh, axis=0)
    out[:he, :we] = _unlift_1d(lo, hi, axis=1)
    return out


# ---------------------------------------------------------------- diffusion
def _fwd(x, k, iv):
    # running sum mod 256 chains every byte to all bytes before it
    return np.cumsum(x ^ k, dtype=np.uint8) + np.uint8(iv)


def _fwd_inv(c, k, iv):
    prev = np.empty_like(c)
    prev[0] = iv
    prev[1:] = c[:-1]
    return (c - prev) ^ k


def _bwd(x, k, iv):
    return _fwd(x[::-1], k[::-1], iv)[::-1]


def _bwd_inv(c, k, iv):
    return _fwd_inv(c[::-1], k[::-1], iv)[::-1]


def _rotl(x, r=ROT):
    # byte rotation moves carry bits into low bit-planes (add-rotate-xor), so no bit-plane is left unmixed
    return (x << np.uint8(r)) | (x >> np.uint8(8 - r))


def _rotr(x, r=ROT):
    return (x >> np.uint8(r)) | (x << np.uint8(8 - r))


def _streams(key: bytes, nonce: bytes, n: int):
    ks = keystream(key, nonce, b"diff", n * 2 * ROUNDS)
    ivs = hashlib.sha256(b"iv" + key + nonce).digest()
    return ks.reshape(2 * ROUNDS, n), ivs


# ---------------------------------------------------------------- public API
def encrypt(img: np.ndarray, key_hex: str, nonce_hex: str) -> np.ndarray:
    key, nonce = parse_key(key_hex), parse_nonce(nonce_hex)
    img = np.ascontiguousarray(img, dtype=np.uint8)
    flat = dwt_forward(img).reshape(-1)
    n = flat.size
    perm, _ = permutation(key, n)
    x = flat[perm]
    ks, ivs = _streams(key, nonce, n)
    for r in range(ROUNDS):
        x = _rotl(_fwd(x, ks[2 * r], ivs[2 * r]))
        x = _rotl(_bwd(x, ks[2 * r + 1], ivs[2 * r + 1]))
    return x.reshape(img.shape)


def decrypt(cipher: np.ndarray, key_hex: str, nonce_hex: str) -> np.ndarray:
    key, nonce = parse_key(key_hex), parse_nonce(nonce_hex)
    cipher = np.ascontiguousarray(cipher, dtype=np.uint8)
    x = cipher.reshape(-1)
    n = x.size
    ks, ivs = _streams(key, nonce, n)
    for r in reversed(range(ROUNDS)):
        x = _bwd_inv(_rotr(x), ks[2 * r + 1], ivs[2 * r + 1])
        x = _fwd_inv(_rotr(x), ks[2 * r], ivs[2 * r])
    _, inv = permutation(key, n)
    coef = x[inv].reshape(cipher.shape)
    return dwt_inverse(coef)


def pixel_sha256(img: np.ndarray) -> str:
    h = hashlib.sha256()
    h.update(str(img.shape).encode())
    h.update(np.ascontiguousarray(img).tobytes())
    return h.hexdigest()
