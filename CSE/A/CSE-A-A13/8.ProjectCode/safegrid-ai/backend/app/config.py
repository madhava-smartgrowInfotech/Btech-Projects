"""Central configuration. Values come from environment variables (optionally a .env file). No secrets in code."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _f(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return float(default)


@dataclass(frozen=True)
class Settings:
    app_env: str
    llm_provider: str
    llm_api_key: str
    llm_model: str
    llm_api_style: str
    llm_base_url: str
    llm_timeout_s: float
    database_url: str
    voltage_min: float
    voltage_max: float
    line_max_loading_pct: float
    trafo_max_loading_pct: float
    default_time_step_minutes: int
    default_seed: int
    cors_origins: tuple[str, ...]
    results_dir: str

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_api_key and self.llm_model)


@lru_cache
def get_settings() -> Settings:
    backend_dir = Path(__file__).resolve().parents[1]
    _load_dotenv(backend_dir / ".env")
    return Settings(
        app_env=os.environ.get("APP_ENV", "development"),
        llm_provider=os.environ.get("LLM_PROVIDER", "mock").lower(),
        llm_api_key=os.environ.get("LLM_API_KEY", ""),
        llm_model=os.environ.get("LLM_MODEL", ""),
        llm_api_style=os.environ.get("LLM_API_STYLE", "anthropic").lower(),
        llm_base_url=os.environ.get("LLM_BASE_URL", ""),
        llm_timeout_s=_f("LLM_TIMEOUT_SECONDS", 20),
        database_url=os.environ.get("DATABASE_URL", "sqlite:///./safegrid.db"),
        voltage_min=_f("VOLTAGE_MIN", 0.95),
        voltage_max=_f("VOLTAGE_MAX", 1.05),
        line_max_loading_pct=_f("LINE_MAX_LOADING_PCT", 100),
        trafo_max_loading_pct=_f("TRAFO_MAX_LOADING_PCT", 100),
        default_time_step_minutes=int(_f("DEFAULT_TIME_STEP_MINUTES", 15)),
        default_seed=int(_f("DEFAULT_SEED", 42)),
        cors_origins=tuple(o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()),
        results_dir=os.environ.get("RESULTS_DIR", str(backend_dir / "results")),
    )
