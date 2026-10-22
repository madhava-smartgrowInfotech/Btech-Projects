"""JSON API used by the React frontend (additive: the HTML routes in routes.py are untouched)."""
import hmac
import json
import logging
import os
import time
from functools import wraps

from flask import Blueprint, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.exceptions import HTTPException

from . import config, explainability, inference, preprocessing
from .routes import _confusion_exists, _metrics_or_none, _run_analysis

log = logging.getLogger("verivision")

api_bp = Blueprint("api", __name__, url_prefix="/api")

TOKEN_MAX_AGE = 60 * 60 * 12  # a demo session lasts 12 hours

# Static description of each ensemble route (resolution comes from config so it never drifts).
BRANCH_INFO = [
    {"key": "a1", "name": "EfficientNet A1", "backbone": "EfficientNet-B0", "resolution": config.RESOLUTION_A,
     "loss": "CrossEntropy", "role": "Standard detector with normal augmentation"},
    {"key": "a2", "name": "EfficientNet A2", "backbone": "EfficientNet-B0", "resolution": config.RESOLUTION_A,
     "loss": "CrossEntropy", "role": "Distortion-hardened twin (blur, noise, JPEG, resampling)"},
    {"key": "b", "name": "ResNet50", "backbone": "ResNet50", "resolution": config.RESOLUTION_B,
     "loss": "CrossEntropy", "role": "Higher-resolution route with horizontal-flip TTA"},
    {"key": "c", "name": "MobileNetV3", "backbone": "MobileNetV3-Large", "resolution": config.RESOLUTION_C,
     "loss": "Focal (gamma=2)", "role": "Lightweight heterogeneous route"},
]


def _serializer():
    return URLSafeTimedSerializer(config.SECRET_KEY, salt="verivision-demo-session")


def _issue_token(email):
    return _serializer().dumps({"email": email, "iat": int(time.time())})


def _token_user():
    header = request.headers.get("Authorization", "")
    if not header.lower().startswith("bearer "):
        return None
    try:
        data = _serializer().loads(header[7:].strip(), max_age=TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    return data.get("email")


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if _token_user() is None:
            return jsonify({"error": "Please sign in to analyze images."}), 401
        return fn(*args, **kwargs)
    return wrapper


@api_bp.route("/auth/login", methods=["POST"])
def login():
    body = request.get_json(silent=True) or {}
    email = str(body.get("email", "")).strip().lower()
    password = str(body.get("password", ""))
    ok_email = hmac.compare_digest(email, config.DEMO_EMAIL.lower())
    ok_pass = hmac.compare_digest(password, config.DEMO_PASSWORD)
    if not (ok_email and ok_pass):
        return jsonify({"error": "Email or password is not correct."}), 401
    return jsonify({"token": _issue_token(email), "user": {"email": email, "name": config.DEMO_NAME}})


@api_bp.route("/auth/me", methods=["GET"])
def me():
    email = _token_user()
    if email is None:
        return jsonify({"error": "Not signed in."}), 401
    return jsonify({"user": {"email": email, "name": config.DEMO_NAME}})


@api_bp.route("/config", methods=["GET"])
def get_config():
    metadata = None
    try:
        with open(config.METADATA_FILE, "r", encoding="utf-8") as fh:
            metadata = json.load(fh)
    except (OSError, ValueError):
        metadata = None
    return jsonify({
        "max_mb": config.MAX_UPLOAD_MB,
        "allowed_extensions": sorted(config.ALLOWED_EXTENSIONS),
        "ensemble_weights": config.ENSEMBLE_WEIGHTS,
        "branches": BRANCH_INFO,
        "gates": {"tau_b": config.GATE_TAU_B, "tau_c": config.GATE_TAU_C, "correction": config.GATE_CORRECTION},
        "confidence_thresholds": {"high": config.CONF_HIGH, "moderate": config.CONF_MODERATE},
        "model_metadata": metadata,
        "demo_account": {"email": config.DEMO_EMAIL, "password": config.DEMO_PASSWORD},
    })


@api_bp.route("/insights", methods=["GET"])
def insights():
    ensemble_m = _metrics_or_none("ensemble_metrics.json")
    return jsonify({
        "available": ensemble_m is not None,
        "ensemble": ensemble_m,
        "models": _metrics_or_none("model_metrics.json"),
        "robustness": _metrics_or_none("robustness_metrics.json"),
        "confusion_exists": _confusion_exists(),
    })


@api_bp.route("/analyze", methods=["POST"])
@login_required
def analyze():
    """Full analysis (verdict, branches, Grad-CAM, robustness) as JSON - the data /predict renders into HTML."""
    try:
        inference.ensure_models_loaded()
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 503
    except Exception:
        log.exception("Model loading failed")
        return jsonify({"error": "Image analysis is temporarily unavailable. Please try again later."}), 500
    try:
        upload = request.files.get("image")
        raw, _ext = preprocessing.validate_upload(upload)
        pil_image = preprocessing.decode_image(raw)
        data_url = explainability.pil_to_data_url(pil_image)
        ctx = _run_analysis(pil_image, data_url, upload.filename)
        ctx["max_mb"] = config.MAX_UPLOAD_MB
        return jsonify(ctx)
    except preprocessing.PreprocessingError as exc:
        return jsonify({"error": str(exc)}), 400
    except HTTPException:
        raise  # e.g. 413 - handled by the app's JSON-aware error handler
    except Exception:
        log.exception("Inference failed")
        return jsonify({"error": "Could not analyze this image. Please try a different file."}), 500
