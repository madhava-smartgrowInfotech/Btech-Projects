"""Runtime configuration for the Nuvara API."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "nuvara.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Fixed seed keeps the synthetic catalogue, shopper population and behaviour
# stream identical across restarts so intelligence metrics are comparable.
RANDOM_SEED = 20240917

CATALOG_SIZE = 148
POPULATION_SIZE = 50
DEMO_PERSONA_COUNT = 8

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

# Default blend used the first time the service boots with an empty database.
DEFAULT_WEIGHTS = {
    "collaborative": 0.34,
    "content": 0.30,
    "trending": 0.22,
    "diversity": 0.14,
}

# No single agent is ever allowed to collapse to zero influence.
WEIGHT_FLOOR = 0.05
LEARNING_RATE = 0.35

# Impression cache that backs the explainability endpoint.
REC_CACHE_MAX = 6000
REC_CACHE_TTL_S = 7200

# Traffic simulation.
TRAFFIC_TICK_S = 1.0
BASELINE_RPS = 145.0
WORKER_CAPACITY_RPS = 22.0
