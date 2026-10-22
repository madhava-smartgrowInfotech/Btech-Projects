"""Central configuration for VeriVision AI.

All tunable product settings live here. Environment variables override
defaults so deployments can adjust behaviour without code changes.
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Class mapping used consistently across training, inference, Grad-CAM, UI.
CLASS_NAMES = ["REAL", "AI_GENERATED"]
CLASS_REAL = 0
CLASS_FAKE = 1

# Flask
FLASK_HOST = os.environ.get("VERIVISION_HOST", "127.0.0.1")
FLASK_PORT = int(os.environ.get("VERIVISION_PORT", "8414"))
MAX_UPLOAD_MB = int(os.environ.get("VERIVISION_MAX_UPLOAD_MB", "10"))
MAX_CONTENT_LENGTH = MAX_UPLOAD_MB * 1024 * 1024
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

# Model artifacts
MODELS_DIR = os.path.join(BASE_DIR, "models")
ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")
METRICS_DIR = os.path.join(ARTIFACTS_DIR, "metrics")
MODEL_FILES = {
    "a1": os.environ.get("VERIVISION_MODEL_A1", os.path.join(MODELS_DIR, "efficientnet_a1.pt")),
    "a2": os.environ.get("VERIVISION_MODEL_A2", os.path.join(MODELS_DIR, "efficientnet_a2.pt")),
    "b": os.environ.get("VERIVISION_MODEL_B", os.path.join(MODELS_DIR, "resnet50_b.pt")),
    "c": os.environ.get("VERIVISION_MODEL_C", os.path.join(MODELS_DIR, "mobilenetv3_c.pt")),
}
METADATA_FILE = os.path.join(MODELS_DIR, "model_metadata.json")

# Input resolutions per route
RESOLUTION_A = 224
RESOLUTION_B = 320
RESOLUTION_C = 224

# ImageNet normalization expected by pretrained backbones
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# Ensemble weights (normalized at load time; configurable and transparent)
ENSEMBLE_WEIGHTS = {
    "a1": float(os.environ.get("VERIVISION_W_A1", "0.35")),
    "a2": float(os.environ.get("VERIVISION_W_A2", "0.15")),
    "b": float(os.environ.get("VERIVISION_W_B", "0.25")),
    "c": float(os.environ.get("VERIVISION_W_C", "0.25")),
}

# Gating parameters (product-level engineering defaults)
GATE_TAU_B = float(os.environ.get("VERIVISION_GATE_TAU_B", "2.5"))
GATE_TAU_C = float(os.environ.get("VERIVISION_GATE_TAU_C", "2.5"))
GATE_CORRECTION = float(os.environ.get("VERIVISION_GATE_CORRECTION", "0.75"))

# Confidence wording thresholds (on winning-class probability)
CONF_HIGH = 0.85
CONF_MODERATE = 0.60

# Training / data
RANDOM_SEED = int(os.environ.get("VERIVISION_SEED", "42"))
DATA_DIR = os.path.join(BASE_DIR, "data")

SECRET_KEY = os.environ.get("VERIVISION_SECRET_KEY", "verivision-local-dev-key")

# Demo sign-in for the web UI (local demo only - override via .env)
DEMO_EMAIL = os.environ.get("VERIVISION_DEMO_EMAIL", "demo@verivision.ai")
DEMO_PASSWORD = os.environ.get("VERIVISION_DEMO_PASSWORD", "Demo@1234")
DEMO_NAME = os.environ.get("VERIVISION_DEMO_NAME", "Demo User")
