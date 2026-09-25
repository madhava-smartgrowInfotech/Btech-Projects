"""Central configuration and constants shared across the ML pipeline and API."""
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
ARTIFACTS_DIR = BACKEND_ROOT / "artifacts"
DATA_DIR = BACKEND_ROOT / "data"

ARTIFACTS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

DATASET_DIR = DATA_DIR / "synthetic_dataset"
DATASET_CSV = DATA_DIR / "synthetic_dataset.csv"

ENCODER_WEIGHTS_PATH = ARTIFACTS_DIR / "encoder.pt"
CLASSIFIER_PATH = ARTIFACTS_DIR / "classifier.json"
SCALER_PATH = ARTIFACTS_DIR / "tabular_scaler.joblib"
SEED_TYPE_ENCODER_PATH = ARTIFACTS_DIR / "seed_type_encoder.joblib"
METRICS_PATH = ARTIFACTS_DIR / "metrics.json"
FEATURE_NAMES_PATH = ARTIFACTS_DIR / "feature_names.json"

DB_PATH = DATA_DIR / "seediq.db"
DB_URL = f"sqlite:///{DB_PATH.as_posix()}"

SEED_TYPES = [
    "Pearl Millet",
    "Finger Millet",
    "Foxtail Millet",
    "Little Millet",
    "Kodo Millet",
    "Proso Millet",
    "Barnyard Millet",
]

IMAGE_SIZE = 64  # encoder input resolution
EMBEDDING_DIM = 48

MODEL_VERSION = "seediq-classifier-v1"
ENCODER_VERSION = "seediq-patch-encoder-v1"
