"""Inference: preprocessing per route, branch logits, TTA, fusion."""
import io
import threading

import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

from . import config, ensemble, models

_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_LOCK = threading.Lock()
_BRANCH_MODELS = {}
_LOADED = False
_LOAD_ERROR = None


def _transform_for(resolution):
    mean, std = config.IMAGENET_MEAN, config.IMAGENET_STD
    return transforms.Compose([
        transforms.Resize((resolution, resolution)),
        transforms.ToTensor(),
        transforms.Normalize(mean=mean, std=std),
    ])


def get_device_name():
    return str(_DEVICE)


def ensure_models_loaded():
    global _LOADED, _LOAD_ERROR
    if _LOADED:
        return
    with _LOCK:
        if _LOADED:
            return
        try:
            missing = models.missing_artifacts()
            if missing:
                raise FileNotFoundError(
                    "Model artifacts missing: "
                    + ", ".join(f"{k} -> {p}" for k, p in missing.items())
                    + ". Run the training workflow (see HOW_TO_RUN.md) to generate them."
                )
            for branch in ("a1", "a2", "b", "c"):
                _BRANCH_MODELS[branch] = models.load_branch_model(branch, _DEVICE)
            _LOADED = True
        except Exception as exc:
            _LOAD_ERROR = str(exc)
            raise


def models_ready():
    return _LOADED


def load_error():
    return _LOAD_ERROR


def _logits_for_tensor(model, tensor):
    with torch.no_grad():
        out = model(tensor.to(_DEVICE))
        return [float(v) for v in out[0].detach().cpu().tolist()]


def branch_logits(pil_image):
    """Run all branches and return raw logits dict."""
    ensure_models_loaded()
    t_a = _transform_for(config.RESOLUTION_A)(pil_image).unsqueeze(0)
    t_b = _transform_for(config.RESOLUTION_B)(pil_image).unsqueeze(0)
    t_c = _transform_for(config.RESOLUTION_C)(pil_image).unsqueeze(0)
    # Horizontal-flip TTA for Route B
    t_b_flip = torch.flip(t_b, dims=[3])
    with torch.no_grad():
        out_b = _BRANCH_MODELS["b"](t_b.to(_DEVICE))
        out_b_flip = _BRANCH_MODELS["b"](t_b_flip.to(_DEVICE))
        avg_b = ((out_b + out_b_flip) / 2.0)[0].detach().cpu().tolist()
    logits = {
        "a1": _logits_for_tensor(_BRANCH_MODELS["a1"], t_a),
        "a2": _logits_for_tensor(_BRANCH_MODELS["a2"], t_a),
        "b": [float(avg_b[0]), float(avg_b[1])],
        "c": _logits_for_tensor(_BRANCH_MODELS["c"], t_c),
    }
    return logits


def confidence_word(prob):
    if prob >= config.CONF_HIGH:
        return "High confidence"
    if prob >= config.CONF_MODERATE:
        return "Moderate confidence"
    return "Low confidence"


def predict_image(pil_image):
    """Full prediction for a PIL image. Returns a JSON-serializable dict."""
    logits = branch_logits(pil_image)
    result = ensemble.ensemble_predict(logits)
    probs = result["probabilities"]
    pred = result["predicted_class"]
    branch_probs = {}
    for branch, pair in logits.items():
        branch_probs[branch] = ensemble.softmax(pair)
    branch_labels = {b: ("REAL" if d == 0 else "AI_GENERATED") for b, d in result["branch_directions"].items()}
    return {
        "predicted_label": result["predicted_label"],
        "predicted_class": pred,
        "prob_real": probs[0],
        "prob_fake": probs[1],
        "confidence": max(probs),
        "confidence_word": confidence_word(max(probs)),
        "fused_logits": result["fused_logits"],
        "branch_logits": logits,
        "branch_probabilities": branch_probs,
        "branch_labels": branch_labels,
        "agreement_count": result["agreement_count"],
        "excluded_branch": result["excluded_branch"],
        "gate1_reason": result["gate1_reason"],
        "gate2_applied": result["gate2_applied"],
        "gate2_reason": result["gate2_reason"],
        "active_weights": result["active_weights"],
        "device": get_device_name(),
    }


def predict_with_robustness(pil_image):
    """Predict original plus JPEG/resize/blur variants; report consistency."""
    from .robustness import make_variants
    variants = make_variants(pil_image)
    outcomes = {}
    for name, img in variants.items():
        try:
            pred = predict_image(img)
            outcomes[name] = pred["predicted_label"]
        except Exception as exc:
            outcomes[name] = f"error: {exc}"
    labels = [v for v in outcomes.values() if v in ("REAL", "AI_GENERATED")]
    base = outcomes.get("original")
    consistent = sum(1 for v in labels if v == base) if base else 0
    return {"outcomes": outcomes, "consistency": f"{consistent}/{len(labels)}" if labels else "0/0"}
