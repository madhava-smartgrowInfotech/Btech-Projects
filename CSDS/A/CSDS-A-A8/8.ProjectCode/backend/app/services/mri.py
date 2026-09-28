"""Tumour segmentation on brain-MRI slices with the JEPA-pre-trained ViT + light decoder."""
import base64
import csv
import io
from functools import lru_cache

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

from ..config import DATA, MODELS
from nets import IMG_SIZE, ViTSeg, image_encoder, UNet  # noqa: E402

SAMPLE_DIR = DATA / "sample" / "lgg"
MODEL_CHOICES = {
    "jepa_10": "ViT + JEPA pre-training, fine-tuned on 10% of masks",
    "jepa_100": "ViT + JEPA pre-training, fine-tuned on 100% of masks",
    "unet_100": "U-Net baseline, supervised on 100% of masks",
}


@lru_cache(maxsize=4)
def load_model(key):
    path = MODELS / f"mri_seg_{key}.pt"
    if not path.exists():
        raise FileNotFoundError(f"Model file {path.name} not found - run ml/train_mri.py")
    ck = torch.load(path, map_location="cpu")
    model = UNet() if ck["kind"] == "unet" else ViTSeg(image_encoder())
    model.load_state_dict(ck["model"])
    model.eval()
    return model, ck["norm"], ck.get("metrics", {})


def available_models():
    return [{"key": k, "label": v, "available": (MODELS / f"mri_seg_{k}.pt").exists()} for k, v in MODEL_CHOICES.items()]


def _png_b64(arr):
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _edge(mask):
    m = mask.astype(bool)
    inner = m.copy()
    inner[1:-1, 1:-1] = m[1:-1, 1:-1] & m[:-2, 1:-1] & m[2:, 1:-1] & m[1:-1, :-2] & m[1:-1, 2:]
    return m & ~inner


def segment(image_bytes, model_key="jepa_10", pixel_spacing_mm=1.0, gt_mask=None):
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        raise ValueError("Could not read the image. Upload a PNG, JPG or TIF brain-MRI slice.")
    model, norm, train_metrics = load_model(model_key)
    rgb = np.asarray(img)
    h, w = rgb.shape[:2]
    x = torch.from_numpy(np.asarray(img.resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR))).permute(2, 0, 1)[None].float()
    x = (x / 255.0 - torch.tensor(norm["mean"]).view(1, 3, 1, 1)) / torch.tensor(norm["std"]).view(1, 3, 1, 1)
    with torch.no_grad():
        logits = model(x)
        prob = torch.sigmoid(F.interpolate(logits, size=(h, w), mode="bilinear", align_corners=False))[0, 0].numpy()
    mask = prob > 0.5
    area_px = int(mask.sum())
    brain_px = int((rgb.mean(axis=2) > 12).sum())

    overlay = rgb.astype(np.float32).copy()
    overlay[mask] = overlay[mask] * 0.45 + np.array([239, 68, 68]) * 0.55
    overlay[_edge(mask)] = [255, 230, 0]
    result = {
        "model": model_key,
        "model_label": MODEL_CHOICES[model_key],
        "image_size": [w, h],
        "tumour_detected": area_px > 0,
        "area_pixels": area_px,
        "pixel_spacing_mm": pixel_spacing_mm,
        "area_mm2": round(area_px * pixel_spacing_mm ** 2, 1),
        "percent_of_brain": round(100.0 * area_px / brain_px, 2) if brain_px else 0.0,
        "mean_confidence": round(float(prob[mask].mean()), 3) if area_px else round(float(1 - prob.max()), 3),
        "max_probability": round(float(prob.max()), 3),
        "overlay_png": _png_b64(overlay.clip(0, 255).astype(np.uint8)),
        "mask_png": _png_b64((mask * 255).astype(np.uint8)),
        "model_test_dice": train_metrics.get("dice"),
    }
    if area_px:
        ys, xs = np.nonzero(mask)
        cx, cy = float(xs.mean()), float(ys.mean())
        result.update({
            "bounding_box": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
            "centroid": [round(cx, 1), round(cy, 1)],
            "location": f"{'upper' if cy < h / 2 else 'lower'} {'left' if cx < w / 2 else 'right'} of the image",
            "max_extent_mm": round(max(xs.max() - xs.min() + 1, ys.max() - ys.min() + 1) * pixel_spacing_mm, 1),
        })
    if gt_mask is not None:
        g = gt_mask.astype(bool)
        inter = int((mask & g).sum())
        denom = int(mask.sum() + g.sum())
        result["ground_truth"] = {
            "area_pixels": int(g.sum()),
            "dice": round(2 * inter / denom, 4) if denom else 1.0,
            "iou": round(inter / int((mask | g).sum()), 4) if (mask | g).any() else 1.0,
        }
    return result


@lru_cache(maxsize=1)
def list_samples():
    rows = []
    with open(SAMPLE_DIR / "manifest.csv", newline="") as f:
        for r in csv.DictReader(f):
            rows.append({"file": r["file"], "patient": r["patient"], "tumour_pixels": int(r["tumour_pixels_256"])})
    return rows


def sample_path(name):
    names = {r["file"] for r in list_samples()}
    if name not in names:
        raise ValueError("Unknown sample slice")
    return SAMPLE_DIR / name, SAMPLE_DIR / name.replace(".png", "_mask.png")


def segment_sample(name, model_key, pixel_spacing_mm):
    img_path, mask_path = sample_path(name)
    gt = np.asarray(Image.open(mask_path).convert("L")) > 127
    res = segment(img_path.read_bytes(), model_key, pixel_spacing_mm, gt_mask=gt)
    res["sample"] = name
    return res
