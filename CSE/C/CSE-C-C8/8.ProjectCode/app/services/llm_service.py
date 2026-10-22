"""PeerScope local LLM service (lazy Qwen load, CPU, graceful fallback)."""
from __future__ import annotations

import os
import threading
from typing import Optional

from app.config import FALLBACK_LLM_MODEL, HF_CACHE_DIR, PRIMARY_LLM_MODEL

_lock = threading.Lock()
_pipe = None
_pipe_model: str | None = None
_pipe_error: str | None = None
_attempted = False


def llm_status() -> dict:
    return {
        "model_requested": PRIMARY_LLM_MODEL,
        "fallback_model": FALLBACK_LLM_MODEL,
        "loaded_model": _pipe_model,
        "available": _pipe is not None,
        "error": _pipe_error,
    }


def _try_load(model_id: str):
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

    import torch

    tok = AutoTokenizer.from_pretrained(model_id, cache_dir=HF_CACHE_DIR, trust_remote_code=True)
    mdl = AutoModelForCausalLM.from_pretrained(
        model_id, cache_dir=HF_CACHE_DIR, trust_remote_code=True,
        torch_dtype=torch.float32, low_cpu_mem_usage=True,
    )
    gen = pipeline("text-generation", model=mdl, tokenizer=tok, max_new_tokens=512,
                   do_sample=False, temperature=0.0, return_full_text=False)
    return gen


def ensure_llm(timeout_note: str = ""):
    """Lazily load the local model. Returns pipeline or None (never raises)."""
    global _pipe, _pipe_model, _pipe_error, _attempted
    if _pipe is not None:
        return _pipe
    if _attempted and _pipe is None:
        return None
    with _lock:
        if _pipe is not None:
            return _pipe
        _attempted = True
        os.environ.setdefault("HF_HUB_OFFLINE", "0")
        try:
            _pipe = _try_load(PRIMARY_LLM_MODEL)
            _pipe_model = PRIMARY_LLM_MODEL
        except Exception as exc_primary:  # try fallback
            try:
                _pipe = _try_load(FALLBACK_LLM_MODEL)
                _pipe_model = FALLBACK_LLM_MODEL
                _pipe_error = f"Primary model unavailable ({exc_primary}); using fallback."
            except Exception as exc2:
                _pipe = None
                _pipe_model = None
                _pipe_error = f"Local LLM unavailable: {exc_primary} | fallback: {exc2}"
        return _pipe


def generate(prompt: str, max_new_tokens: int = 512) -> dict:
    pipe = ensure_llm()
    if pipe is None:
        return {"status": "unavailable", "text": "", "error": _pipe_error or "LLM not loaded"}
    try:
        out = pipe(prompt, max_new_tokens=max_new_tokens)
        text = out[0]["generated_text"] if out else ""
        return {"status": "ok", "text": str(text).strip(), "model": _pipe_model}
    except Exception as exc:
        return {"status": "error", "text": "", "error": str(exc)}
