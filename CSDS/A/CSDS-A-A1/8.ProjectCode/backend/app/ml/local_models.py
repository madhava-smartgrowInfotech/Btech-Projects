"""Lazy, thread-safe loading of the pre-trained local models (CPU).

* embedder  - sentence-transformers/all-MiniLM-L6-v2      (dense retrieval)
* reranker  - cross-encoder/ms-marco-MiniLM-L6-v2         (re-ranking)
* nli       - cross-encoder/nli-deberta-v3-xsmall         (faithfulness)

Weights live in ``models/hf/<org>__<name>`` (downloaded by ``scripts/download_models.py``).
If a folder is missing, the model is fetched from the Hugging Face Hub on first use.
"""

from __future__ import annotations

import os
import threading
import time
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger, log_event

log = get_logger("models")

MODEL_IDS = {
    "embedder": "sentence-transformers/all-MiniLM-L6-v2",
    "reranker": "cross-encoder/ms-marco-MiniLM-L6-v2",
    "nli": "cross-encoder/nli-deberta-v3-xsmall",
}

_lock = threading.Lock()
_models: dict[str, Any] = {}
_load_ms: dict[str, int] = {}
_torch_ready = False


def _prepare_torch() -> None:
    global _torch_ready
    if _torch_ready:
        return
    import torch

    torch.set_num_threads(max(1, min(6, (os.cpu_count() or 4) - 2)))
    _torch_ready = True


def model_path(key: str) -> str:
    repo = MODEL_IDS[key]
    local = get_settings().hf_dir / repo.replace("/", "__")
    has_weights = local.exists() and any(local.glob("*.safetensors")) or (local / "pytorch_model.bin").exists()
    return str(local) if has_weights else repo


def _load(key: str) -> Any:
    if key in _models:
        return _models[key]
    with _lock:
        if key in _models:
            return _models[key]
        _prepare_torch()
        start = time.perf_counter()
        path = model_path(key)
        if key == "embedder":
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(path, device="cpu")
        else:
            from sentence_transformers import CrossEncoder

            model = CrossEncoder(path, device="cpu", max_length=512)
        _models[key] = model
        _load_ms[key] = round((time.perf_counter() - start) * 1000)
        log_event(log, "model_loaded", model=key, source=path, ms=_load_ms[key])
        return model


def get_embedder():  # noqa: ANN201 - SentenceTransformer
    return _load("embedder")


def get_reranker():  # noqa: ANN201 - CrossEncoder
    return _load("reranker")


def get_nli():  # noqa: ANN201 - CrossEncoder
    return _load("nli")


def nli_label_index() -> dict[str, int]:
    """Map 'entailment' / 'contradiction' / 'neutral' to logit positions for the NLI model."""
    model = get_nli()
    config = getattr(model, "config", None) or getattr(getattr(model, "model", None), "config", None)
    id2label = getattr(config, "id2label", None) or {0: "contradiction", 1: "entailment", 2: "neutral"}
    return {str(label).lower(): int(idx) for idx, label in id2label.items()}


def warm_up() -> None:
    for key in ("embedder", "reranker", "nli"):
        _load(key)


def models_status() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, repo in MODEL_IDS.items():
        path = model_path(key)
        out[key] = {
            "model": repo,
            "downloaded": path != repo,
            "loaded": key in _models,
            "load_ms": _load_ms.get(key),
        }
    return out
