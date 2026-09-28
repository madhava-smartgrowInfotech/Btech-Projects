"""Offline speech-to-text with faster-whisper on CPU."""
import threading
import time

import numpy as np

from ..config import WHISPER_MODEL


class STT:
    def __init__(self, size=WHISPER_MODEL):
        self.size, self.model, self.error = size, None, None
        self.lock = threading.Lock()
        self.loaded = threading.Event()
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        from faster_whisper import WhisperModel

        try:
            try:  # offline first: use the cached model without touching the network
                self.model = WhisperModel(self.size, device="cpu", compute_type="int8", local_files_only=True)
            except Exception:
                self.model = WhisperModel(self.size, device="cpu", compute_type="int8")
        except Exception as e:
            self.error = str(e)
        self.loaded.set()

    @property
    def ready(self):
        return self.model is not None

    def transcribe(self, pcm16: bytes, language: str | None = "en"):
        if not self.loaded.wait(120) or self.model is None:
            raise RuntimeError(f"Speech model not available: {self.error or 'still loading'}")
        audio = np.frombuffer(pcm16, np.int16).astype(np.float32) / 32768.0
        seconds = len(audio) / 16000
        if seconds < 0.3:
            return {"text": "", "audio_seconds": round(seconds, 2), "latency_ms": 0.0}
        t = time.perf_counter()
        with self.lock:
            segments, info = self.model.transcribe(
                audio, language=language or None, beam_size=1, vad_filter=True,
                condition_on_previous_text=False, without_timestamps=True,
            )
            text = " ".join(s.text.strip() for s in segments).strip()
        return {"text": text, "language": info.language, "audio_seconds": round(seconds, 2),
                "latency_ms": round((time.perf_counter() - t) * 1000, 1)}
