"""VenturePulse central configuration."""
from pathlib import Path

APP_NAME = "VenturePulse"
BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"
DATA_SAMPLE = BASE_DIR / "data" / "sample"
MODELS_DIR = BASE_DIR / "models"
EVAL_DIR = BASE_DIR / "evaluation"
STATIC_IMG = APP_DIR / "static" / "img"

HOST = "127.0.0.1"
PORT = 8000
BASE_URL = f"http://localhost:{PORT}"

RANDOM_STATE = 42
TEST_SIZE = 0.2
N_SPLITS = 5
ALPHA = 0.5  # structured-block weight in fused representation
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
DEFAULT_K = 50
RETRIEVAL_KS = [10, 20, 30, 50]
MAX_DESC_LEN = 2000

TARGET_COL_CANDIDATES = ["status", "status(acquired/closed)", "status_acquired_closed", "outcome", "label"]
SUCCESS_VALUES = {"acquired", "success", "1", "true", "yes", "ipo"}
FAILURE_VALUES = {"closed", "failure", "0", "false", "no"}

NUMERIC_FEATURES = [
    "age_first_funding_year",
    "age_last_funding_year",
    "age_first_milestone_year",
    "age_last_milestone_year",
    "relationships",
    "funding_rounds",
    "funding_total_usd",
    "milestones",
    "avg_participants",
]
BINARY_FEATURES = [
    "has_VC",
    "has_angel",
    "has_roundA",
    "has_roundB",
    "has_roundC",
    "has_roundD",
    "is_top500",
]
CATEGORICAL_FEATURES = ["state", "industry_type"]
TEXT_FIELD = "description"

KAGGLE_DATASET = "manishkc06/startup-success-prediction"
KAGGLE_URL = "https://www.kaggle.com/datasets/manishkc06/startup-success-prediction"
