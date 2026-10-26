"""Story-length narration intelligibility (documentation run).

The application's evaluation transcribes each narration with a plain Whisper pipeline call, which fails for audio longer than 30 s
(transformers asks for chunking), so the shipped evaluation reports no WER/CER for real stories. This script reads the stories and WAV files that a
running StoryVox server holds and transcribes them with chunk_length_s=30, leaving the product code untouched.

    python scripts/run_story_asr.py http://127.0.0.1:8402
"""
from __future__ import annotations

import json
import sys
import time
import unicodedata
import urllib.request
from pathlib import Path

import torch  # noqa: F401  (torch before other imports)
import jiwer
from transformers import pipeline

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8402").rstrip("/")
import tempfile

TMP = Path(tempfile.mkdtemp(prefix="storyvox_asr_"))
OUT = Path(__file__).resolve().parent.parent / "experiments" / "story_asr"


def get(path):
    return json.load(urllib.request.urlopen(BASE + path, timeout=60))


def norm(t: str) -> str:
    t = unicodedata.normalize("NFKC", t or "").lower()
    t = "".join(c for c in t if unicodedata.category(c)[0] not in ("P", "S"))
    return " ".join(t.split())


asr = pipeline("automatic-speech-recognition", model="openai/whisper-small", chunk_length_s=30, device=-1)
rows = []
for s in get("/api/stories?limit=100"):
    if not s.get("has_audio"):
        continue
    full = get(f"/api/stories/{s['id']}")
    audio = full["audio"]
    wav = TMP / f"story_{s['id']}.wav"
    wav.write_bytes(urllib.request.urlopen(BASE + f"/api/audio/{audio['id']}", timeout=60).read())   # the same download the browser player uses
    t0 = time.perf_counter()
    hyp = asr(str(wav), generate_kwargs={"language": s["language_code"], "task": "transcribe"})["text"].strip()
    secs = round(time.perf_counter() - t0, 2)
    ref, hy = norm(full["story_text"]), norm(hyp)
    try:
        from langdetect import DetectorFactory, detect

        DetectorFactory.seed = 0
        text_lang = detect(full["story_text"])
    except Exception:
        text_lang = None
    row = {"text_language": text_lang, "story_id": s["id"], "language": full["language_code"], "style": full["style"], "length": full["length_option"], "words": full["word_count"],
           "tts_model": audio["tts_model"], "audio_s": audio["duration_seconds"], "asr_s": secs,
           "wer_norm": round(jiwer.wer(ref, hy), 4), "cer_norm": round(jiwer.cer(ref, hy), 4), "hyp_words": len(hy.split())}
    rows.append(row)
    print(row, flush=True)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "metrics.json").write_text(json.dumps({"experiment": "story_length_asr", "asr": "openai/whisper-small, chunk_length_s=30", "rows": rows}, indent=2), encoding="utf-8")
print("saved", OUT / "metrics.json")
