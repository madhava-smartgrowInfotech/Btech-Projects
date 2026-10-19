"""StoryVox audio file helpers (read/concat/probe)."""
from __future__ import annotations

from pathlib import Path

import numpy as np


def read_wav_mono(path: Path, target_sr: int = 16000) -> tuple[np.ndarray, int]:
    import soundfile as sf

    data, sr = sf.read(str(path), always_2d=False)
    audio = np.asarray(data, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != target_sr:
        audio = _resample_linear(audio, sr, target_sr)
        sr = target_sr
    return audio.astype(np.float32), sr


def _resample_linear(audio: np.ndarray, src_sr: int, dst_sr: int) -> np.ndarray:
    if len(audio) == 0 or src_sr == dst_sr:
        return audio
    duration = len(audio) / float(src_sr)
    target_len = max(1, int(round(duration * dst_sr)))
    old_idx = np.linspace(0, 1, len(audio))
    new_idx = np.linspace(0, 1, target_len)
    return np.interp(new_idx, old_idx, audio).astype(np.float32)


def write_wav_mono(path: Path, audio: np.ndarray, sample_rate: int = 16000) -> None:
    import soundfile as sf

    path.parent.mkdir(parents=True, exist_ok=True)
    clip = np.asarray(audio, dtype=np.float32).ravel()
    peak = float(np.max(np.abs(clip))) if clip.size else 0.0
    if peak > 1.0:
        clip = clip / peak
    sf.write(str(path), clip, sample_rate, subtype="PCM_16")


def concat_wav_segments(segments: list[np.ndarray], sample_rate: int = 16000, pause_seconds: float = 0.25) -> np.ndarray:
    pause = np.zeros(max(0, int(sample_rate * pause_seconds)), dtype=np.float32)
    parts: list[np.ndarray] = []
    for i, seg in enumerate(segments):
        seg = np.asarray(seg, dtype=np.float32).ravel()
        if seg.size == 0:
            continue
        parts.append(seg)
        if i < len(segments) - 1:
            parts.append(pause)
    if not parts:
        return np.zeros(0, dtype=np.float32)
    return np.concatenate(parts)


def audio_duration_seconds(audio: np.ndarray, sample_rate: int) -> float:
    if sample_rate <= 0 or audio.size == 0:
        return 0.0
    return round(float(len(audio)) / float(sample_rate), 3)


def rms_energy(audio: np.ndarray) -> float:
    if audio.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.asarray(audio, dtype=np.float64) ** 2)))


def is_silent(audio: np.ndarray, threshold: float = 1e-4) -> bool:
    return rms_energy(audio) < threshold
