"""Speech: decoding, faster-whisper transcription with agent/customer separation, and voice emotion."""
import threading
from functools import lru_cache

import numpy as np

from ..config import EMOTION_MODEL, WHISPER_COMPUTE_TYPE, WHISPER_MODEL

SR = 16000
_lock = threading.Lock()


def probe(path):
    import av
    with av.open(str(path)) as f:
        s = f.streams.audio[0]
        dur = float(f.duration / 1e6) if f.duration else None
        return {"channels": s.channels or 1, "duration": dur}


def load_audio(path):
    """-> (mono, [left, right] or None). A stereo file whose channels are the same is treated as mono."""
    from faster_whisper.audio import decode_audio
    info = probe(path)
    if info["channels"] >= 2:
        left, right = decode_audio(str(path), sampling_rate=SR, split_stereo=True)
        n = min(len(left), len(right))
        left, right = left[:n], right[:n]
        diff = np.mean(np.abs(left - right))
        level = np.mean(np.abs(left)) + np.mean(np.abs(right)) + 1e-9
        if diff / level > 0.2:
            return (left + right) / 2, [left, right]
        return (left + right) / 2, None
    return decode_audio(str(path), sampling_rate=SR), None


@lru_cache(maxsize=1)
def whisper():
    from faster_whisper import WhisperModel
    return WhisperModel(WHISPER_MODEL, device="cpu", compute_type=WHISPER_COMPUTE_TYPE)


def _words(audio):
    """Word-level timestamps (segment-level ends drift into the following silence when VAD is on)."""
    with _lock:
        segs, _ = whisper().transcribe(audio, language="en", beam_size=1, vad_filter=True,
                                       vad_parameters={"min_silence_duration_ms": 400},
                                       condition_on_previous_text=False, word_timestamps=True)
        return [w for s in segs for w in (s.words or []) if w.word.strip()]


def _seg(ws, speaker):
    return {"start": round(ws[0].start, 2), "end": round(ws[-1].end, 2), "speaker": speaker,
            "text": "".join(w.word for w in ws).strip()}


def transcribe_stereo(left, right, gap=1.5):
    """Each channel is one speaker. The channel that speaks first is the agent (agents open the call).
    Words of both channels are interleaved by time; a turn ends when the other speaker talks or after a
    pause of `gap` seconds."""
    a, b = _words(left), _words(right)
    a_first = (a[0].start if a else 1e9) <= (b[0].start if b else 1e9)
    agent, customer = (a, b) if a_first else (b, a)
    tagged = sorted([(w, "agent") for w in agent] + [(w, "customer") for w in customer], key=lambda x: x[0].start)
    segs, cur, who = [], [], None
    for w, spk in tagged:
        if cur and (spk != who or w.start - cur[-1].end >= gap):
            segs.append(_seg(cur, who))
            cur = []
        cur.append(w)
        who = spk
    if cur:
        segs.append(_seg(cur, who))
    activity = {"agent": _intervals(agent), "customer": _intervals(customer)}
    return segs, ("left" if a_first else "right"), activity


def _intervals(words, join=0.35):
    """Speech intervals [[start, end], ...] of one speaker, joining words closer than `join` seconds."""
    out = []
    for w in words:
        if out and w.start - out[-1][1] < join:
            out[-1][1] = round(w.end, 2)
        else:
            out.append([round(w.start, 2), round(w.end, 2)])
    return out


def activity_from_segments(segs):
    return {spk: [[s["start"], s["end"]] for s in segs if s["speaker"] == spk] for spk in ("agent", "customer")}


def transcribe_mono(audio, gap=0.7):
    """Simple turn split for single-channel audio: a new turn starts after a pause of `gap` seconds that
    follows the end of a sentence. Turns alternate speakers, starting with the agent."""
    words = _words(audio)
    turns, cur = [], []
    for w in words:
        if cur and w.start - cur[-1].end >= gap and cur[-1].word.strip()[-1:] in ".?!":
            turns.append(cur)
            cur = []
        cur.append(w)
    if cur:
        turns.append(cur)
    out = []
    for i, t in enumerate(turns):
        text = "".join(w.word for w in t).strip()
        if text:
            out.append({"start": round(t[0].start, 2), "end": round(t[-1].end, 2),
                        "speaker": "agent" if i % 2 == 0 else "customer", "text": text})
    return out


@lru_cache(maxsize=1)
def emotion_model():
    import torch
    from transformers import AutoFeatureExtractor, AutoModelForAudioClassification
    torch.set_num_threads(max(1, (torch.get_num_threads() or 2)))
    fe = AutoFeatureExtractor.from_pretrained(EMOTION_MODEL)
    model = AutoModelForAudioClassification.from_pretrained(EMOTION_MODEL).eval()
    return fe, model


LABELS = {"neu": "neutral", "hap": "happy", "ang": "angry", "sad": "sad"}


def voice_emotion(clip):
    """Probabilities over neutral / happy / angry / sad for one speech clip (16 kHz mono)."""
    import torch
    if len(clip) < SR * 0.5:
        return None
    if len(clip) > SR * 8:  # the middle 8 seconds are enough and keep CPU time low
        mid = len(clip) // 2
        clip = clip[mid - SR * 4: mid + SR * 4]
    fe, model = emotion_model()
    inputs = fe(clip.astype(np.float32), sampling_rate=SR, return_tensors="pt")
    with torch.no_grad():
        p = torch.softmax(model(**inputs).logits[0], dim=-1).numpy()
    return {LABELS.get(model.config.id2label[i], model.config.id2label[i]): round(float(p[i]), 3)
            for i in range(len(p))}
