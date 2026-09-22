"""Process-wide access to the loaded models (loaded once at start-up, reloadable after retraining)."""
from __future__ import annotations

from ..core.config import settings
from .service import ModelService

_service: ModelService | None = None


def load_models() -> ModelService:
    global _service
    _service = ModelService(settings.models_dir)
    return _service


def get_models() -> ModelService:
    return _service if _service is not None else load_models()
