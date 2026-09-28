"""Hypertensive retinopathy inference: wavelet stack -> LeNet -> probability, Grad-CAM and Frangi vessel map."""
import json
from functools import lru_cache

import cv2
import numpy as np
import torch
from skimage.filters import frangi

from ..config import MODELS_DIR
from .lenet import LeNet
from .wavelet import feature_stack

MODEL_PATH = MODELS_DIR / "lenet_hr.pt"
META_PATH = MODELS_DIR / "lenet_hr.json"


@lru_cache(maxsize=1)
def load_model():
    if not MODEL_PATH.exists():
        raise RuntimeError("Retina model not trained yet. Run: python ml/train_retina.py")
    model = LeNet()
    model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
    model.eval()
    meta = json.loads(META_PATH.read_text()) if META_PATH.exists() else {}
    return model, meta


def predict_with_cam(norm_img: np.ndarray) -> tuple[float, np.ndarray]:
    """Returns (probability, Grad-CAM map in [0, 1] at 128 x 128)."""
    model, _ = load_model()
    x = torch.from_numpy(feature_stack(norm_img))[None]
    store = {}
    layer = model.features[-1]  # ReLU after the last conv block
    h1 = layer.register_forward_hook(lambda m, i, o: store.__setitem__("act", o))
    h2 = layer.register_full_backward_hook(lambda m, gi, go: store.__setitem__("grad", go[0]))
    try:
        x.requires_grad_(True)
        logit = model(x)
        model.zero_grad()
        logit.sum().backward()
    finally:
        h1.remove()
        h2.remove()
    prob = float(torch.sigmoid(logit).item())
    act, grad = store["act"][0].detach(), store["grad"][0].detach()
    weights = grad.mean(dim=(1, 2))
    cam = torch.relu((weights[:, None, None] * act).sum(0)).numpy()
    cam = cv2.resize(cam, (128, 128), interpolation=cv2.INTER_LINEAR)
    cam = cam / (cam.max() + 1e-8)
    return prob, cam


def heatmap_overlay(base_bgr: np.ndarray, cam: np.ndarray, mask: np.ndarray) -> np.ndarray:
    size = base_bgr.shape[:2][::-1]
    cam = cv2.resize(cam, size, interpolation=cv2.INTER_CUBIC)
    cam = np.clip(cam, 0, 1)
    cam[~mask] = 0
    color = cv2.applyColorMap((cam * 255).astype(np.uint8), cv2.COLORMAP_JET)
    out = cv2.addWeighted(base_bgr, 0.55, color, 0.45, 0)
    out[~mask] = 0
    return out


def vessel_map(enhanced: np.ndarray, mask: np.ndarray) -> tuple[np.ndarray, dict]:
    """Frangi vesselness on the CLAHE green channel (vessels are dark ridges)."""
    img = enhanced.astype(np.float32) / 255.0
    v = frangi(img, sigmas=range(1, 6), black_ridges=True)
    inner = cv2.erode(mask.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool)
    v[~inner] = 0
    hi = np.percentile(v[inner], 99.5) if inner.any() else v.max()
    v = np.clip(v / (hi + 1e-12), 0, 1)
    binary = v > 0.15
    density = float(binary[inner].mean()) if inner.any() else 0.0
    # Calibre proxy: twice the mean distance to the vessel edge over vessel pixels (px at 512 display size)
    dist = cv2.distanceTransform(binary.astype(np.uint8), cv2.DIST_L2, 3)
    vals = dist[binary]
    width = float(2 * vals.mean()) if vals.size else 0.0
    view = (v * 255).astype(np.uint8)
    return view, {"vessel_density": round(density, 4), "mean_vessel_width_px": round(width, 2)}


def analyse(pre: dict) -> dict:
    prob, cam = predict_with_cam(pre["input"])
    _, meta = load_model()
    threshold = float(meta.get("threshold", 0.5))
    vessels, vstats = vessel_map(pre["clahe"], pre["mask"])
    heat = heatmap_overlay(pre["original"], cam, pre["mask"])
    positive = prob >= threshold
    return {
        "probability": prob,
        "threshold": threshold,
        "positive": positive,
        "label": "Hypertensive retinopathy signs" if positive else "No hypertensive retinopathy signs",
        "vessels": vstats,
        "images": {"heatmap": heat, "vessels": vessels},
    }
