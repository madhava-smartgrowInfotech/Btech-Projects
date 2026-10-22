"""Lightweight robustness variants for the UI consistency check."""
import io

import cv2
import numpy as np
from PIL import Image


def make_variants(pil_image):
    """Return dict name -> PIL image for original, jpeg, resize, blur."""
    variants = {"original": pil_image}
    arr = np.array(pil_image)
    # JPEG compression simulation (quality 60)
    try:
        buf = io.BytesIO()
        pil_image.save(buf, format="JPEG", quality=60)
        buf.seek(0)
        variants["jpeg"] = Image.open(buf).convert("RGB")
    except Exception:
        pass
    # Downsample / upsample
    try:
        w, h = pil_image.size
        small = pil_image.resize((max(8, w // 2), max(8, h // 2)), Image.BILINEAR)
        variants["resize"] = small.resize((w, h), Image.BILINEAR)
    except Exception:
        pass
    # Gaussian blur
    try:
        blurred = cv2.GaussianBlur(arr, (5, 5), 1.0)
        variants["blur"] = Image.fromarray(blurred)
    except Exception:
        pass
    return variants
