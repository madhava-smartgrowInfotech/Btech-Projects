"""PeerScope application configuration (single source of truth for tunable settings)."""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    """Minimal .env reader (KEY=VALUE lines); real environment variables always win."""
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    except OSError:
        pass


_load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
UPLOAD_TMP = Path(os.environ.get("PEERSCOPE_TMP", str(BASE_DIR / "data" / "tmp")))

HOST = os.environ.get("PEERSCOPE_HOST", "127.0.0.1")
PORT = int(os.environ.get("PEERSCOPE_PORT", "8408"))

MAX_UPLOAD_MB = int(os.environ.get("PEERSCOPE_MAX_UPLOAD_MB", "20"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

PRIMARY_LLM_MODEL = os.environ.get("PEERSCOPE_LLM_MODEL", "Qwen/Qwen2.5-1.5B-Instruct")
FALLBACK_LLM_MODEL = os.environ.get("PEERSCOPE_LLM_FALLBACK", "Qwen/Qwen2.5-0.5B-Instruct")
EMBEDDING_MODEL = os.environ.get("PEERSCOPE_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
HF_CACHE_DIR = os.environ.get("PEERSCOPE_HF_CACHE", str(MODELS_DIR / "hf_cache"))

LITERATURE_COUNT = int(os.environ.get("PEERSCOPE_LITERATURE_COUNT", "6"))
LITERATURE_TIMEOUT_S = float(os.environ.get("PEERSCOPE_LITERATURE_TIMEOUT", "8"))

MODEL_ARTIFACT = MODELS_DIR / "decision_model.joblib"
VECTORIZER_ARTIFACT = MODELS_DIR / "tfidf_vectorizer.joblib"
METRICS_ARTIFACT = MODELS_DIR / "metrics.json"
PROCESSED_DATASET = DATA_DIR / "processed_dataset.csv"

DATABASE_URL = os.environ.get("PEERSCOPE_DB", f"sqlite:///{(DATA_DIR / 'peerscope.db').as_posix()}")

# Auditable reviewer-matching weights (documented; sum of positive weights = 1.0).
MATCH_WEIGHTS = {
    "expertise_similarity": float(os.environ.get("PEERSCOPE_W_EXPERTISE", "0.55")),
    "keyword_score": float(os.environ.get("PEERSCOPE_W_KEYWORD", "0.20")),
    "method_score": float(os.environ.get("PEERSCOPE_W_METHOD", "0.15")),
    "availability_score": float(os.environ.get("PEERSCOPE_W_AVAIL", "0.10")),
    "conflict_penalty": float(os.environ.get("PEERSCOPE_W_CONFLICT", "0.60")),
}

DATABASE_PATH = DATA_DIR / "peerscope.db"

for _p in (DATA_DIR, MODELS_DIR, UPLOAD_TMP, DATA_DIR / "demo", Path(HF_CACHE_DIR)):
    _p.mkdir(parents=True, exist_ok=True)
