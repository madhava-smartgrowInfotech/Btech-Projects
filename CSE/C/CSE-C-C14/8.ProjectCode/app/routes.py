"""HTTP routes for VeriVision AI."""
import json
import logging
import os
import traceback

from flask import Blueprint, jsonify, render_template, request

from . import config, explainability, inference, models, preprocessing

log = logging.getLogger("verivision")
logging.basicConfig(level=logging.INFO)

bp = Blueprint("main", __name__)

BRANCH_DISPLAY = {
    "a1": "EfficientNet A1",
    "a2": "EfficientNet A2",
    "b": "ResNet50",
    "c": "MobileNetV3",
}

HEATMAP_NOTE = (
    "Highlighted regions indicate image areas that contributed strongly to the "
    "model's prediction. This visualization is an explanation aid, not proof of authenticity."
)


def _metrics_or_none(filename):
    path = os.path.join(config.METRICS_DIR, filename)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _confusion_exists():
    return os.path.exists(os.path.join(config.METRICS_DIR, "confusion_matrix.png"))


@bp.route("/", methods=["GET"])
def index():
    return render_template(
        "index.html",
        max_mb=config.MAX_UPLOAD_MB,
        ensemble_weights=config.ENSEMBLE_WEIGHTS,
    )


@bp.route("/health", methods=["GET"])
def health():
    try:
        inference.ensure_models_loaded()
        ready = True
        err = None
    except Exception as exc:
        ready = False
        err = str(exc)
    status = "ok" if ready else "degraded"
    code = 200 if ready else 503
    return jsonify({
        "status": status,
        "models_loaded": ready,
        "device": inference.get_device_name(),
        "error": err,
    }), code


def _run_analysis(pil_image, original_data_url, filename):
    pred = inference.predict_image(pil_image)
    branches = []
    for key in ("a1", "a2", "b", "c"):
        lp = pred["branch_probabilities"][key]
        branches.append({
            "key": key,
            "name": BRANCH_DISPLAY[key],
            "label": pred["branch_labels"][key],
            "prob_real": lp[0],
            "prob_fake": lp[1],
        })
    # Grad-CAM overlays for selectable branches
    cams = {}
    for branch in ("a1", "b", "c"):
        try:
            overlay, _heat, _raw = explainability.generate_gradcam_overlay(
                pil_image, branch=branch, predicted_class=pred["predicted_class"]
            )
            cams[branch] = explainability.pil_to_data_url(overlay)
        except Exception as exc:
            log.warning("Grad-CAM failed for branch %s: %s", branch, exc)
            cams[branch] = None
    # Robustness check
    try:
        robustness = inference.predict_with_robustness(pil_image)
    except Exception as exc:
        log.warning("Robustness check failed: %s", exc)
        robustness = {"outcomes": {}, "consistency": "n/a"}
    return {
        "filename": filename,
        "original_image": original_data_url,
        "predicted_label": pred["predicted_label"],
        "confidence": pred["confidence"],
        "confidence_pct": round(pred["confidence"] * 100, 2),
        "confidence_word": pred["confidence_word"],
        "prob_real": pred["prob_real"],
        "prob_fake": pred["prob_fake"],
        "branches": branches,
        "cams": cams,
        "heatmap_note": HEATMAP_NOTE,
        "agreement_count": pred["agreement_count"],
        "excluded_branch": pred["excluded_branch"],
        "gate1_reason": pred["gate1_reason"],
        "gate2_applied": pred["gate2_applied"],
        "gate2_reason": pred["gate2_reason"],
        "active_weights": pred["active_weights"],
        "robustness": robustness,
        "device": pred["device"],
    }


@bp.route("/predict", methods=["POST"])
def predict():
    try:
        inference.ensure_models_loaded()
    except FileNotFoundError as exc:
        return render_template("error.html", message=str(exc)), 503
    except Exception as exc:
        log.exception("Model loading failed")
        return render_template("error.html", message="Image analysis is temporarily unavailable. Please try again later."), 500
    try:
        upload = request.files.get("image")
        raw, _ext = preprocessing.validate_upload(upload)
        pil_image = preprocessing.decode_image(raw)
        data_url = explainability.pil_to_data_url(pil_image)
        ctx = _run_analysis(pil_image, data_url, upload.filename)
        return render_template("result.html", **ctx, max_mb=config.MAX_UPLOAD_MB)
    except preprocessing.PreprocessingError as exc:
        return render_template("error.html", message=str(exc)), 400
    except Exception:
        log.exception("Inference failed")
        return render_template("error.html", message="Could not analyze this image. Please try a different file."), 500


@bp.route("/api/predict", methods=["POST"])
def api_predict():
    try:
        inference.ensure_models_loaded()
    except Exception as exc:
        return jsonify({"error": str(exc)}), 503
    try:
        upload = request.files.get("image")
        raw, _ext = preprocessing.validate_upload(upload)
        pil_image = preprocessing.decode_image(raw)
        pred = inference.predict_image(pil_image)
        return jsonify({
            "predicted_label": pred["predicted_label"],
            "prob_real": pred["prob_real"],
            "prob_fake": pred["prob_fake"],
            "confidence": pred["confidence"],
            "confidence_word": pred["confidence_word"],
            "branch_labels": pred["branch_labels"],
            "agreement_count": pred["agreement_count"],
        })
    except preprocessing.PreprocessingError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        log.exception("API inference failed")
        return jsonify({"error": "Could not analyze this image."}), 500


@bp.route("/insights", methods=["GET"])
def insights():
    ensemble_m = _metrics_or_none("ensemble_metrics.json")
    model_m = _metrics_or_none("model_metrics.json")
    robust_m = _metrics_or_none("robustness_metrics.json")
    available = ensemble_m is not None
    return render_template(
        "insights.html",
        available=available,
        ensemble=ensemble_m,
        models=model_m,
        robustness=robust_m,
        confusion_exists=_confusion_exists(),
        max_mb=config.MAX_UPLOAD_MB,
    )


@bp.route("/artifacts/confusion_matrix.png", methods=["GET"])
def confusion_png():
    from flask import send_file
    path = os.path.join(config.METRICS_DIR, "confusion_matrix.png")
    if not os.path.exists(path):
        return jsonify({"error": "Evaluation artifacts unavailable."}), 404
    return send_file(path, mimetype="image/png")
