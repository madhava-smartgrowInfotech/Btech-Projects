import numpy as np
from skimage.metrics import peak_signal_noise_ratio, structural_similarity


def imperceptibility(cover: np.ndarray, stego: np.ndarray) -> dict:
    changed = int(np.count_nonzero(cover != stego))
    if changed == 0:
        psnr = float("inf")
    else:
        psnr = float(peak_signal_noise_ratio(cover, stego, data_range=255))
    ssim = float(structural_similarity(cover, stego, channel_axis=2, data_range=255))
    mse = float(np.mean((cover.astype(np.float64) - stego.astype(np.float64)) ** 2))
    return {
        "psnr_db": None if psnr == float("inf") else round(psnr, 3),
        "ssim": round(ssim, 6),
        "mse": round(mse, 6),
        "max_abs_change": int(np.max(np.abs(cover.astype(np.int16) - stego.astype(np.int16)))),
        "values_changed": changed,
        "values_total": int(cover.size),
        "changed_pct": round(100 * changed / cover.size, 4),
    }
