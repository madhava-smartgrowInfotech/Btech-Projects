"""Grad-CAM example grids for the documents -> docs/figures/f14_gradcam_examples.png and f15_gradcam_xdomain.png.

Run after the CIFAKE models are installed in models/ (scripts/publish_cifake_models.py), with the project venv:
    .venv\\Scripts\\python.exe scripts\\docs_build\\make_gradcam_figure.py
The overlays come from app.explainability (the same code the web app uses); images are the first correctly classified
test images of each class, so the figure shows typical behaviour and is not cherry-picked for neat heat maps.
"""
import glob
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from app import explainability, inference  # noqa: E402

OUT = os.path.join(ROOT, "docs", "figures")
LABEL = {0: "REAL", 1: "AI_GENERATED"}


def grid(paths_labels, name, title):
    rows = len(paths_labels)
    fig, axs = plt.subplots(rows, 4, figsize=(7.6, 1.95 * rows))
    for r, (p, y) in enumerate(paths_labels):
        img = Image.open(p).convert("RGB")
        pred = inference.predict_image(img)
        cls = pred["predicted_class"]
        axs[r, 0].imshow(img.resize((224, 224), Image.NEAREST))
        axs[r, 0].set_title(f"true {LABEL[y]}\nfused: {pred['predicted_label']} ({pred['confidence'] * 100:.0f}%)", fontsize=7.5)
        for c, br in enumerate(("a1", "b", "c"), start=1):
            ov, _h, _raw = explainability.generate_gradcam_overlay(img, branch=br, predicted_class=cls)
            axs[r, c].imshow(ov)
            axs[r, c].set_title({"a1": "Route A1 (EfficientNet)", "b": "Route B (ResNet50)", "c": "Route C (MobileNetV3)"}[br] if r == 0 else "", fontsize=7.5)
        for a in axs[r]:
            a.axis("off")
    fig.suptitle(title, fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, name), dpi=150, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    print("saved", name, flush=True)


def correct_examples(folder_glob, y, k):
    out = []
    for p in sorted(glob.glob(folder_glob)):
        if len(out) >= k:
            break
        img = Image.open(p).convert("RGB")
        if inference.predict_image(img)["predicted_class"] == y:
            out.append((p, y))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    inference.ensure_models_loaded()
    real = correct_examples(os.path.join(ROOT, "data", "cifake", "test", "real", "*.png"), 0, 3)
    fake = correct_examples(os.path.join(ROOT, "data", "cifake", "test", "fake", "*.png"), 1, 3)
    grid(real + fake, "f14_gradcam_examples.png", "Grad-CAM on the predicted class: first three correctly classified REAL and AI_GENERATED test images")
    xr = sorted(glob.glob(os.path.join(ROOT, "data", "xdomain", "test", "real", "*.jpg")))[:2]
    xf = sorted(glob.glob(os.path.join(ROOT, "data", "xdomain", "test", "fake", "*.jpg")))[:2]
    grid([(p, 0) for p in xr] + [(p, 1) for p in xf], "f15_gradcam_xdomain.png", "Grad-CAM on cross-domain images (first two real photographs and two AI images of the probe set; the verdict may be wrong)")


if __name__ == "__main__":
    main()
