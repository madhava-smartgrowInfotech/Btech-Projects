"""Central configuration for PhishGuard."""
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
MODEL_DIR = ROOT_DIR / "models"

DATASET_CSV = DATA_DIR / "urls_sample.csv"        # columns: url,label (1 = phishing)
FULL_DATASET_URL = (
    "https://raw.githubusercontent.com/faizann24/"
    "Using-machine-learning-to-detect-malicious-URLs/master/data/data.csv"
)

TI_DATABASE = DATA_DIR / "threat_intel.db"        # crowdsourced reports (SQLite)
METRICS_JSON = MODEL_DIR / "metrics.json"
BEST_MODEL_FILE = MODEL_DIR / "best_model.joblib"
MODEL_FILES = {
    "random_forest": MODEL_DIR / "random_forest.joblib",
    "xgboost": MODEL_DIR / "xgboost.joblib",
    "logistic_regression": MODEL_DIR / "logistic_regression.joblib",
}

RANDOM_STATE = 42
TEST_SIZE = 0.2

# Crowdsourced threat-intelligence settings
CONSENSUS_THRESHOLD = 2         # net phishing votes needed to confirm a URL
AUTO_RETRAIN_EVERY = 25         # retrain automatically after N new confirmed URLs
CROWD_SAMPLE_WEIGHT = 3.0       # confirmed community URLs count this much in training

# Public feeds used by `sync` (optional; failures are tolerated)
THREAT_FEEDS = {
    "openphish": "https://openphish.com/feed.txt",
    "urlhaus": "https://urlhaus.abuse.ch/downloads/text_online/",
}

# Verdict thresholds on phishing probability
PHISHING_THRESHOLD = 0.60
SUSPICIOUS_THRESHOLD = 0.35
