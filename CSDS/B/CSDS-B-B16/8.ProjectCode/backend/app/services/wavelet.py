"""2-level Haar wavelet decomposition used as the LeNet input."""
import cv2
import numpy as np
import pywt

BANDS = ["LL", "LH", "HL", "HH"]


def haar2(img: np.ndarray) -> dict:
    """Returns {'level1': {LL,LH,HL,HH}, 'level2': {...}} for a 2-D float image."""
    ll1, (lh1, hl1, hh1) = pywt.dwt2(img, "haar")
    ll2, (lh2, hl2, hh2) = pywt.dwt2(ll1, "haar")
    return {
        "level1": dict(zip(BANDS, [ll1, lh1, hl1, hh1])),
        "level2": dict(zip(BANDS, [ll2, lh2, hl2, hh2])),
    }


def _std(x: np.ndarray) -> np.ndarray:
    return ((x - x.mean()) / (x.std() + 1e-6)).astype(np.float32)


def feature_stack(img: np.ndarray) -> np.ndarray:
    """8 x 128 x 128 tensor: level-1 bands + level-2 bands upsampled to the same grid."""
    w = haar2(img)
    size = w["level1"]["LL"].shape[::-1]
    chans = [_std(w["level1"][b]) for b in BANDS]
    chans += [_std(cv2.resize(w["level2"][b], size, interpolation=cv2.INTER_NEAREST)) for b in BANDS]
    return np.stack(chans).astype(np.float32)


def band_image(x: np.ndarray, detail: bool) -> np.ndarray:
    """Contrast-stretch a sub-band for display. Detail bands use |x| so vessel edges show bright."""
    v = np.abs(x) if detail else x
    lo, hi = np.percentile(v, 1), np.percentile(v, 99.5)
    v = np.clip((v - lo) / (hi - lo + 1e-6), 0, 1)
    out = (v * 255).astype(np.uint8)
    return cv2.resize(out, (256, 256), interpolation=cv2.INTER_NEAREST)


def band_images(img: np.ndarray) -> dict:
    w = haar2(img)
    return {f"{lvl[-1]}_{b}": band_image(w[lvl][b], b != "LL") for lvl in ("level1", "level2") for b in BANDS}
