"""Grad-CAM visual explanations generated from real model gradients."""
import base64
import io

import cv2
import numpy as np
import torch
from PIL import Image
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
from torchvision import transforms

from . import config, inference


def _target_layer(model, branch):
    if branch in ("a1", "a2"):
        # EfficientNet-B0 final conv block
        return model.features[-1]
    if branch == "b":
        return model.layer4[-1]
    if branch == "c":
        return model.features[-1]
    raise ValueError(f"Unknown branch: {branch}")


def _input_tensor(pil_image, branch):
    res = config.RESOLUTION_B if branch == "b" else config.RESOLUTION_A
    t = transforms.Compose([
        transforms.Resize((res, res)),
        transforms.ToTensor(),
        transforms.Normalize(mean=config.IMAGENET_MEAN, std=config.IMAGENET_STD),
    ])(pil_image).unsqueeze(0)
    return t


def generate_gradcam_overlay(pil_image, branch="a1", predicted_class=1):
    """Run Grad-CAM on one branch and return (overlay_pil, heatmap_pil, png_bytes)."""
    inference.ensure_models_loaded()
    model = inference._BRANCH_MODELS[branch]
    device = next(model.parameters()).device
    target_layer = _target_layer(model, branch)
    input_tensor = _input_tensor(pil_image, branch).to(device)
    # NB: grad-cam pairs each target with one batch element, so targets must
    # accept 1-D per-image outputs — use the standard ClassifierOutputTarget.
    cam = GradCAM(model=model, target_layers=[target_layer])
    try:
        grayscale = cam(input_tensor=input_tensor,
                        targets=[ClassifierOutputTarget(predicted_class)])[0]
    finally:
        try:
            cam.activations_and_grads.release()
        except Exception:
            pass
    if grayscale is None or getattr(grayscale, "size", 0) == 0:
        raise RuntimeError(f"Grad-CAM produced an empty heatmap for branch '{branch}'.")
    # Overlay on resized original
    res = config.RESOLUTION_B if branch == "b" else config.RESOLUTION_A
    rgb_small = np.array(pil_image.resize((res, res)).convert("RGB")).astype(np.float32) / 255.0
    overlay = show_cam_on_image(rgb_small, grayscale, use_rgb=True)
    overlay_pil = Image.fromarray(overlay)
    heat = (grayscale * 255).astype(np.uint8)
    heat_color = cv2.applyColorMap(heat, cv2.COLORMAP_JET)
    heat_color = cv2.cvtColor(heat_color, cv2.COLOR_BGR2RGB)
    heatmap_pil = Image.fromarray(heat_color).resize(pil_image.size)
    buf = io.BytesIO()
    overlay_pil.save(buf, format="PNG")
    return overlay_pil, heatmap_pil, buf.getvalue()


def png_bytes_to_data_url(png_bytes):
    return "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")


def pil_to_data_url(pil_image, fmt="PNG"):
    buf = io.BytesIO()
    pil_image.save(buf, format=fmt)
    mime = "image/png" if fmt.upper() == "PNG" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(buf.getvalue()).decode("ascii")
