import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    HOST: str = os.getenv("CARELENS_HOST", "127.0.0.1")
    PORT: int = int(os.getenv("CARELENS_PORT", "8000"))
    DATABASE_PATH: str = os.getenv("CARELENS_DB_PATH", str(BASE_DIR / "data" / "carelens.db"))
    SECRET_KEY: str = os.getenv("CARELENS_SECRET_KEY", "carelens-local-dev-secret-change-me")
    TOKEN_EXPIRE_MINUTES: int = int(os.getenv("CARELENS_TOKEN_EXPIRE_MIN", "1440"))
    EMBEDDING_MODEL: str = os.getenv("CARELENS_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    RERANKER_MODEL: str = os.getenv("CARELENS_RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
    GENERATOR_MODEL: str = os.getenv("CARELENS_GENERATOR_MODEL", "google/flan-t5-small")
    RETRIEVAL_TOP_K: int = int(os.getenv("CARELENS_TOP_K", "5"))
    CANDIDATE_K: int = int(os.getenv("CARELENS_CANDIDATE_K", "15"))
    HYBRID_SEMANTIC_WEIGHT: float = float(os.getenv("CARELENS_HYBRID_SEM", "0.65"))
    HYBRID_LEXICAL_WEIGHT: float = float(os.getenv("CARELENS_HYBRID_LEX", "0.35"))
    DATA_SOURCE_LABEL: str = os.getenv("CARELENS_DATA_SOURCE", "synthetic")
    MAX_QUERY_CHARS: int = 2000

settings = Settings()
