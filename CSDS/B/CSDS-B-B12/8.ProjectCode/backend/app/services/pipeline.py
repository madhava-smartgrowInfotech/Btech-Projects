"""End-to-end analysis: modality check -> preprocessing -> segmentation -> classification -> Grad-CAM -> severity."""
import threading

import cv2
import numpy as np
import torch
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget

from ..config import MODELS_DIR
from . import imaging
from .nets import make_backbone, make_classifier, make_unet

torch.set_num_threads(4)
MAX_SATURATION = 0.12  # radiographs are grey; colour photos are rejected
SEVERITY_BANDS = [(15.0, "Mild"), (35.0, "Moderate"), (101.0, "Severe")]


class RejectedImage(ValueError):
    pass


class Engine:
    def __init__(self):
        self.lock = threading.Lock()
        self.loaded = False

    def load(self):
        with self.lock:
            if self.loaded:
                return
            self.classifiers = {}
            for task in ("xray", "ct"):
                ckpt = torch.load(MODELS_DIR / f"{task}_classifier.pt", map_location="cpu")
                m = make_classifier(len(ckpt["classes"]))
                m.load_state_dict(ckpt["state_dict"])
                self.classifiers[task] = (m.eval(), ckpt["classes"], float(ckpt["temperature"]))
            u = torch.load(MODELS_DIR / "lung_unet.pt", map_location="cpu")
            self.unet = make_unet()
            self.unet.load_state_dict(u["state_dict"])
            self.unet.eval()
            self.backbone = make_backbone()
            self.backbone.load_state_dict(torch.load(MODELS_DIR / "modality_backbone.pt", map_location="cpu"))
            self.backbone.eval()
            bank = np.load(MODELS_DIR / "modality_bank.npz")
            self.bank = torch.from_numpy(bank["bank"].astype(np.float32))
            self.bank_labels = bank["labels"]
            self.threshold = float(bank["threshold"])
            self.loaded = True

    # ---- steps -------------------------------------------------------------
    def modality(self, gray, rgb, meta, enhanced):
        sat = colour = imaging.colourfulness(rgb)
        if sat > MAX_SATURATION:
            raise RejectedImage(f"This looks like a colour photograph (saturation {colour:.2f}), not a chest X-ray or CT image.")
        with torch.no_grad():
            e = self.backbone(torch.from_numpy(imaging.to_tensor_array(enhanced))[None])
            e = torch.nn.functional.normalize(e, dim=1)
            sims = (e @ self.bank.T)[0].numpy()
        scores = {}
        for label, name in [(0, "xray"), (1, "ct")]:
            s = np.sort(sims[self.bank_labels == label])[-5:]
            scores[name] = float(s.mean())
        modality = max(scores, key=scores.get)
        tag = meta.get("dicom_modality", "").upper()
        if tag == "CT":
            modality = "ct"
        elif tag in ("CR", "DX"):
            modality = "xray"
        if scores[modality] < self.threshold:
            raise RejectedImage(
                f"Not recognised as a chest X-ray or chest CT (similarity {scores[modality]:.2f}, needs {self.threshold:.2f}). Please upload a chest radiograph or CT slice."
            )
        return modality, scores

    def lung_mask(self, gray, modality):
        if modality == "ct":
            small = cv2.resize(gray, (imaging.CLS_SIZE, imaging.CLS_SIZE), interpolation=cv2.INTER_AREA)
            return imaging.ct_lung_mask(small), "Intensity-based lung field (CT)"
        with torch.no_grad():
            prob = torch.sigmoid(self.unet(torch.from_numpy(imaging.to_seg_array(gray))[None]))[0, 0].numpy()
        mask = (prob > 0.5).astype(np.uint8)
        n, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
        if n > 3:  # keep the two lungs (largest components)
            keep = 1 + np.argsort(stats[1:, cv2.CC_STAT_AREA])[-2:]
            mask = np.isin(labels, keep).astype(np.uint8)
        mask = cv2.resize(mask, (imaging.CLS_SIZE, imaging.CLS_SIZE), interpolation=cv2.INTER_NEAREST)
        return mask, "U-Net (MobileNetV2 encoder)"

    def classify(self, enhanced, modality):
        model, classes, temperature = self.classifiers[modality]
        x = torch.from_numpy(imaging.to_tensor_array(enhanced))[None]
        with torch.no_grad():
            probs = torch.softmax(model(x) / temperature, dim=1)[0].numpy()
        idx = int(probs.argmax())
        cam = GradCAM(model=model, target_layers=[model.conv_head])
        heat = cam(input_tensor=x, targets=[ClassifierOutputTarget(idx)])[0]
        return classes, probs, idx, heat

    # ---- main entry --------------------------------------------------------
    def analyze(self, data: bytes, filename: str):
        self.load()
        try:
            gray, rgb, meta = imaging.load_image(data, filename)
        except imaging.ImageError as e:
            raise RejectedImage(str(e))
        steps = imaging.preprocess(gray)
        with self.lock:
            modality, mod_scores = self.modality(gray, rgb, meta, steps["enhanced"])
            mask, mask_method = self.lung_mask(gray, modality)
            classes, probs, idx, heat = self.classify(steps["enhanced"], modality)
        prediction = classes[idx]
        lung_px = int(mask.sum())
        hot = (heat >= 0.5) & (mask > 0)
        affected = 100.0 * hot.sum() / lung_px if lung_px else 0.0
        if prediction == "Normal":
            severity = "None"
        else:
            severity = next(name for limit, name in SEVERITY_BANDS if affected < limit)
        images = {
            "original": imaging.png_bytes(imaging.view(gray)),
            "resized": imaging.png_bytes(steps["resized"]),
            "denoised": imaging.png_bytes(steps["denoised"]),
            "enhanced": imaging.png_bytes(steps["enhanced"]),
            "mask": imaging.png_bytes(imaging.mask_overlay(steps["resized"], mask)),
            "heatmap": imaging.png_bytes(imaging.heatmap_overlay(steps["resized"], heat)),
        }
        norm = imaging.to_tensor_array(steps["enhanced"])
        return {
            "modality": modality,
            "modality_score": mod_scores[modality],
            "prediction": prediction,
            "confidence": float(probs[idx]),
            "probabilities": {c: round(float(p), 4) for c, p in zip(classes, probs)},
            "severity": severity,
            "affected_pct": round(float(affected), 1),
            "images": images,
            "details": {
                "input": meta,
                "modality_scores": {k: round(v, 3) for k, v in mod_scores.items()},
                "modality_threshold": round(self.threshold, 3),
                "mask_method": mask_method,
                "lung_area_pct": round(100.0 * lung_px / mask.size, 1),
                "preprocessing": [
                    {"step": "Resize", "detail": f"{meta['width']}x{meta['height']} -> {imaging.CLS_SIZE}x{imaging.CLS_SIZE} (area interpolation)", "image": "resized"},
                    {"step": "Noise reduction", "detail": "Non-local means denoising (h=5)", "image": "denoised"},
                    {"step": "Contrast enhancement", "detail": "CLAHE (clip 2.0, 8x8 tiles)", "image": "enhanced"},
                    {"step": "Normalisation", "detail": f"Scaled to 0-1, ImageNet mean/std; tensor mean {norm.mean():.2f}, std {norm.std():.2f}", "image": None},
                ],
            },
        }


engine = Engine()
