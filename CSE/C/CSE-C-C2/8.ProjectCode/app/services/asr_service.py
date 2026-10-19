"""StoryVox ASR service (Whisper) used by the evaluation pipeline."""
from __future__ import annotations

import logging
import threading
from pathlib import Path

logger = logging.getLogger("storyvox.asr")

_lock = threading.Lock()
_asr = None
_asr_model_id: str | None = None


def _load_asr(model_id: str):
    global _asr, _asr_model_id
    with _lock:
        if _asr is not None and _asr_model_id == model_id:
            return _asr
        try:
            import torch
            from transformers import pipeline

            device = 0 if torch.cuda.is_available() else -1
            logger.warning("StoryVox: loading speech-recognition model '%s'...", model_id)
            dtype = torch.float16 if torch.cuda.is_available() else torch.float32
            _asr = pipeline("automatic-speech-recognition", model=model_id, device=device, torch_dtype=dtype)
            _asr_model_id = model_id
            return _asr
        except Exception as exc:
            logger.warning("StoryVox: ASR model unavailable (%s).", exc)
            raise RuntimeError("Speech recognition model could not be loaded. Check the server log.") from exc


def transcribe_wav(path: Path, language_code: str = "en") -> str:
    from app.config import get_settings

    settings = get_settings()
    pipe = _load_asr(settings.asr_model)
    result = pipe(str(path), generate_kwargs={"language": language_code, "task": "transcribe"})
    text = result.get("text", "") if isinstance(result, dict) else str(result)
    return (text or "").strip()
