"""
make_deck_assets.py - figures used only by the Review decks.

    python -X utf8 scripts/make_deck_assets.py

Writes docs/figures/ocr_preprocess_demo.png: the real `preprocess_image_for_ocr` (grayscale, denoise,
adaptive threshold, deskew) applied to a rendered demo report page. The page is clean text, so a scan defect is
SIMULATED (2 degree rotation, Gaussian noise, uneven lighting) to show what the step does; this is a demonstration,
not an accuracy measurement (Tesseract is not installed on the build machine, so no OCR text is produced).
"""

import os
import sys
from datetime import datetime

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pymupdf  # noqa: E402

import ocr_processor as ocr  # noqa: E402
from backend.demo_data import render_pdf  # noqa: E402

OUT = os.path.join(ROOT, "docs", "figures", "ocr_preprocess_demo.png")


def main():
    pdf = render_pdf(2, datetime(2026, 8, 2))
    doc = pymupdf.open(stream=pdf, filetype="pdf")
    pix = doc[0].get_pixmap(matrix=pymupdf.Matrix(300 / 72, 300 / 72), colorspace=pymupdf.csRGB)
    img = cv2.cvtColor(np.frombuffer(pix.samples, np.uint8).reshape(pix.h, pix.w, 3), cv2.COLOR_RGB2BGR)
    h, w = img.shape[:2]
    img = img[int(h * 0.05):int(h * 0.385), int(w * 0.05):int(w * 0.78)]

    rng = np.random.default_rng(42)
    sh, sw = img.shape[:2]
    m = cv2.getRotationMatrix2D((sw // 2, sh // 2), 2.0, 1.0)
    scan = cv2.warpAffine(img, m, (sw, sh), borderValue=(255, 255, 255))
    light = np.tile(np.linspace(0.78, 1.0, sw), (sh, 1))[..., None]
    scan = np.clip(scan * light + rng.normal(0, 14, scan.shape), 0, 255).astype(np.uint8)
    out = ocr.preprocess_image_for_ocr(scan)

    fig, ax = plt.subplots(1, 2, figsize=(10, 3.6), dpi=150)
    ax[0].imshow(cv2.cvtColor(scan, cv2.COLOR_BGR2RGB))
    ax[0].set_title("Simulated scan: 2 deg rotation, noise, uneven light", fontsize=9)
    ax[1].imshow(out, cmap="gray")
    ax[1].set_title("After preprocess_image_for_ocr (grayscale, denoise, threshold, deskew)", fontsize=9)
    for a in ax:
        a.axis("off")
    fig.tight_layout()
    fig.savefig(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
