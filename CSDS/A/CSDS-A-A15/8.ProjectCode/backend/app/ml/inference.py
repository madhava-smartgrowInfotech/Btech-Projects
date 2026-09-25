import base64
import io
import json

import numpy as np
import torch
from PIL import Image
from torchvision import transforms

from app.config import settings
from app.ml.gradcam import GradCAM
from app.ml.labels import CLASS_NAMES, DEFECT_INFO
from app.ml.model import build_model

IMG_SIZE = 224
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

_preprocess = transforms.Compose(
    [
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.Grayscale(num_output_channels=3),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ]
)


class DefectInspector:
    """Loads the trained classifier once and serves predictions + Grad-CAM heatmaps."""

    def __init__(self):
        if settings.class_names_path.exists():
            self.class_names: list[str] = json.loads(settings.class_names_path.read_text())
        else:
            self.class_names = sorted(CLASS_NAMES)

        self.model = build_model(num_classes=len(self.class_names), pretrained=not settings.model_path.exists())
        if settings.model_path.exists():
            state = torch.load(settings.model_path, map_location="cpu")
            self.model.load_state_dict(state)
        self.model.eval()

        self.gradcam = GradCAM(self.model, target_layer=self.model.layer4[-1])

    def predict(self, image_bytes: bytes) -> dict:
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        input_tensor = _preprocess(pil_image).unsqueeze(0)
        input_tensor.requires_grad_(False)

        cam, class_idx, probs = self.gradcam(input_tensor)
        label = self.class_names[class_idx]
        confidence = float(probs[class_idx])

        heatmap_overlay_b64 = self._make_overlay(pil_image, cam)

        class_probabilities = [
            {
                "label": cls,
                "display_name": DEFECT_INFO.get(cls, {}).get("display_name", cls),
                "probability": float(p),
            }
            for cls, p in zip(self.class_names, probs)
        ]
        class_probabilities.sort(key=lambda x: x["probability"], reverse=True)

        coverage = self._heatmap_coverage(cam)
        severity = self._severity(label, confidence, coverage)

        return {
            "defect_type": label,
            "display_name": DEFECT_INFO.get(label, {}).get("display_name", label),
            "confidence": confidence,
            "severity": severity,
            "heatmap_coverage": coverage,
            "class_probabilities": class_probabilities,
            "heatmap_png_b64": heatmap_overlay_b64,
            "description": DEFECT_INFO.get(label, {}).get("description", ""),
        }

    @staticmethod
    def _heatmap_coverage(cam: np.ndarray, threshold: float = 0.6) -> float:
        return float((cam >= threshold).sum() / cam.size)

    @staticmethod
    def _severity(label: str, confidence: float, coverage: float) -> str:
        baseline = DEFECT_INFO.get(label, {}).get("severity_baseline", "medium")
        baseline_rank = {"low": 0, "medium": 1, "high": 2}[baseline]

        score = baseline_rank + (confidence > 0.85) * 1 + (coverage > 0.25) * 1
        if score >= 3:
            return "high"
        if score >= 1:
            return "medium"
        return "low"

    @staticmethod
    def _make_overlay(pil_image: Image.Image, cam: np.ndarray) -> str:
        cam_img = Image.fromarray((cam * 255).astype(np.uint8)).resize(
            (IMG_SIZE, IMG_SIZE), resample=Image.BILINEAR
        )
        cam_arr = np.array(cam_img).astype(np.float32) / 255.0

        heat_rgb = np.zeros((IMG_SIZE, IMG_SIZE, 3), dtype=np.float32)
        heat_rgb[..., 0] = np.clip(1.5 * cam_arr, 0, 1)  # red channel
        heat_rgb[..., 1] = np.clip(1.2 * (cam_arr - 0.4), 0, 1)  # green mid
        heat_rgb[..., 2] = np.clip(1.0 - cam_arr, 0, 1) * 0.3  # slight blue base

        base = pil_image.resize((IMG_SIZE, IMG_SIZE)).convert("RGB")
        base_arr = np.array(base).astype(np.float32) / 255.0

        alpha = np.clip(cam_arr[..., None] * 0.65, 0, 0.65)
        blended = base_arr * (1 - alpha) + heat_rgb * alpha
        blended = (np.clip(blended, 0, 1) * 255).astype(np.uint8)

        out_img = Image.fromarray(blended)
        buf = io.BytesIO()
        out_img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")


_inspector: DefectInspector | None = None


def get_inspector() -> DefectInspector:
    global _inspector
    if _inspector is None:
        _inspector = DefectInspector()
    return _inspector
