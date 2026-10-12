"""LSB substitution: one bit per colour-channel value, row-major order, 32-bit length prefix."""
import io

import numpy as np
from PIL import Image

LEN_BITS = 32


class StegoError(ValueError):
    pass


def load_rgb(source) -> np.ndarray:
    """Accept bytes or a path; return an HxWx3 uint8 array (alpha dropped)."""
    try:
        img = Image.open(io.BytesIO(source) if isinstance(source, (bytes, bytearray)) else source)
        img.load()
    except Exception as exc:
        raise StegoError("Could not read this file as an image") from exc
    return np.array(img.convert("RGB"), dtype=np.uint8)


def to_png_bytes(arr: np.ndarray) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(arr, "RGB").save(buf, format="PNG", compress_level=6)
    return buf.getvalue()


def capacity_bytes(arr: np.ndarray) -> int:
    """Largest bundle (bytes) that fits in this image."""
    return max(0, (arr.size - LEN_BITS) // 8)


def embed(arr: np.ndarray, bundle: bytes) -> np.ndarray:
    cap = capacity_bytes(arr)
    if len(bundle) > cap:
        raise StegoError(f"Payload needs {len(bundle)} bytes but this cover holds only {cap} bytes. "
                         "Choose a larger cover or a smaller file.")
    framed = len(bundle).to_bytes(4, "big") + bundle
    bits = np.unpackbits(np.frombuffer(framed, dtype=np.uint8))
    flat = arr.reshape(-1).copy()
    flat[:bits.size] = (flat[:bits.size] & 0xFE) | bits
    return flat.reshape(arr.shape)


def extract(arr: np.ndarray) -> bytes:
    flat = arr.reshape(-1)
    if flat.size < LEN_BITS:
        raise StegoError("Image is too small to contain a payload")
    length = int.from_bytes(np.packbits(flat[:LEN_BITS] & 1).tobytes(), "big")
    if length == 0 or length > capacity_bytes(arr):
        raise StegoError("No hidden payload found (length header is invalid)")
    bits = flat[LEN_BITS:LEN_BITS + length * 8] & 1
    return np.packbits(bits).tobytes()


def lsb_stream(arr: np.ndarray, n_bits: int) -> np.ndarray:
    return arr.reshape(-1)[:n_bits] & 1
