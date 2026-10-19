"""StoryVox TTS layer: pretrained multilingual synthesis behind a TTSProvider interface."""
from __future__ import annotations

import abc
import logging
import threading
import time
from pathlib import Path

import numpy as np

from app.config import LANGUAGE_MAP, get_settings
from app.utils import chunk_text
from app.utils.audio import concat_wav_segments, is_silent, read_wav_mono, write_wav_mono

logger = logging.getLogger("storyvox.tts")

_lock = threading.Lock()
_mms_cache: dict[str, tuple] = {}
TARGET_SR = 16000


class TTSProvider(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    def synthesize(self, text: str, language_code: str) -> tuple[np.ndarray, int, str]:
        """Return (mono float32 audio, sample_rate, actual_model_id)."""


class MMSTTSProvider(TTSProvider):
    name = "mms"

    def _load(self, checkpoint: str):
        with _lock:
            if checkpoint in _mms_cache:
                return _mms_cache[checkpoint]
            try:
                from transformers import AutoTokenizer, VitsModel

                import torch

                logger.warning("StoryVox: loading speech model '%s' (first run downloads weights)...", checkpoint)
                tokenizer = AutoTokenizer.from_pretrained(checkpoint)
                model = VitsModel.from_pretrained(checkpoint)
                model.eval()
                if torch.cuda.is_available():
                    model = model.to("cuda")
                _mms_cache[checkpoint] = (tokenizer, model)
                logger.warning("StoryVox: speech model '%s' ready.", checkpoint)
                return tokenizer, model
            except Exception as exc:
                logger.warning("StoryVox: pretrained speech checkpoint unavailable (%s).", exc)
                raise

    def synthesize(self, text: str, language_code: str) -> tuple[np.ndarray, int, str]:
        lang = LANGUAGE_MAP.get(language_code)
        if lang is None:
            raise ValueError("This language is not currently supported for narration.")
        checkpoint = lang["tts_checkpoint"]
        tokenizer, model = self._load(checkpoint)
        import torch

        device = next(model.parameters()).device
        segments: list[np.ndarray] = []
        for chunk in chunk_text(text, max_chars=380):
            inputs = tokenizer(chunk, return_tensors="pt")
            inputs = {k: (v.to(device) if hasattr(v, "to") else v) for k, v in inputs.items()}
            with torch.no_grad():
                out = model(**inputs).waveform
            wav = out.squeeze().detach().float().cpu().numpy().astype(np.float32)
            if wav.size:
                peak = float(np.max(np.abs(wav)))
                if peak > 0:
                    wav = (wav / max(peak, 1e-6) * 0.9).astype(np.float32)
                segments.append(wav)
        if not segments:
            raise RuntimeError("Narration could not be generated. Check the server log for details.")
        audio = concat_wav_segments(segments, sample_rate=TARGET_SR)
        if audio.size == 0 or is_silent(audio):
            raise RuntimeError("Narration could not be generated. Check the server log for details.")
        # MMS checkpoints natively emit 16 kHz; keep TARGET_SR for consistency.
        return audio.astype(np.float32), TARGET_SR, checkpoint


class SystemTTSProvider(TTSProvider):
    """Offline OS speech fallback (SAPI5 on Windows via pyttsx3). Produces real speech."""

    name = "system-fallback"

    def synthesize(self, text: str, language_code: str) -> tuple[np.ndarray, int, str]:
        import tempfile

        try:
            import pyttsx3  # type: ignore
        except Exception as exc:
            raise RuntimeError(
                "The speech model is still loading. Please try again in a moment."
            ) from exc
        tmp = Path(tempfile.mkdtemp(prefix="storyvox_tts_"))
        out_wav = tmp / "voice.wav"
        try:
            engine = pyttsx3.init()
            try:
                engine.setProperty("rate", 170)
            except Exception:
                pass
            engine.save_to_file(text[:4000], str(out_wav))
            engine.runAndWait()
            try:
                engine.stop()
            except Exception:
                pass
        except Exception as exc:
            raise RuntimeError("Narration could not be generated. Check the server log for details.") from exc
        if not out_wav.exists() or out_wav.stat().st_size < 1000:
            raise RuntimeError("Narration could not be generated. Check the server log for details.")
        audio, sr = read_wav_mono(out_wav, target_sr=TARGET_SR)
        if audio.size == 0 or is_silent(audio):
            raise RuntimeError("Narration could not be generated. Check the server log for details.")
        return audio, TARGET_SR, "system-tts-offline-fallback"


def get_provider() -> TTSProvider:
    return MMSTTSProvider()


def synthesize_story_narration(story_text: str, language_code: str) -> tuple[Path, float, int, str, float, float]:
    """Synthesize narration, persist WAV under data/audio, return file metadata.

    Returns (relative_path, duration_s, sample_rate, model_id, synth_time_s, rtf).
    Raises RuntimeError with a human-readable message on failure. Never writes silence.
    """
    from app.utils import unique_audio_filename

    settings = get_settings()
    if not story_text or not story_text.strip():
        raise ValueError("There is no story text to narrate yet.")
    if language_code not in LANGUAGE_MAP:
        raise ValueError("This language is not currently supported for narration.")
    started = time.perf_counter()
    last_error: Exception | None = None
    audio: np.ndarray | None = None
    sample_rate = TARGET_SR
    model_id = ""
    for provider in (MMSTTSProvider(), SystemTTSProvider()):
        try:
            audio, sample_rate, model_id = provider.synthesize(story_text, language_code)
            break
        except ValueError:
            raise
        except Exception as exc:
            last_error = exc
            logger.warning("StoryVox: TTS provider %s failed: %s", provider.name, exc)
            continue
    if audio is None or audio.size == 0 or is_silent(audio):
        if isinstance(last_error, (ValueError, RuntimeError)):
            raise last_error
        raise RuntimeError("Narration could not be generated. Check the server log for details.")
    synth_time = round(time.perf_counter() - started, 3)
    duration = round(float(len(audio)) / float(sample_rate), 3) if sample_rate else 0.0
    if duration <= 0:
        raise RuntimeError("Narration could not be generated. Check the server log for details.")
    rtf = round(synth_time / duration, 4) if duration else 0.0
    audio_dir = settings.resolved_audio_dir
    audio_dir.mkdir(parents=True, exist_ok=True)
    filename = unique_audio_filename(0)
    abs_path = audio_dir / filename
    write_wav_mono(abs_path, audio, sample_rate)
    rel_path = Path(settings.audio_dir) / filename if not Path(settings.audio_dir).is_absolute() else abs_path
    return Path(str(rel_path)).as_posix(), duration, sample_rate, model_id, synth_time, rtf


def resolve_audio_abs_path(stored_path: str) -> Path:
    from app.config import BASE_DIR

    p = Path(stored_path)
    if p.is_absolute():
        return p
    return (BASE_DIR / p).resolve()
