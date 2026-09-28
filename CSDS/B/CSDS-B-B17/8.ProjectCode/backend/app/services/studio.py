"""Sample call studio: turns a two-speaker script into a stereo call recording with offline voices.

The agent is rendered on the left channel and the customer on the right channel, which is how most
contact-centre recorders store calls. Timing (pauses, holds, talk-over) comes from the script and a seeded RNG.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

from ..config import ROOT, SCRIPTS_FILE

SR = 16000
WORKER = ROOT / "scripts" / "tts_worker.py"
RATES = {"negative": (192, 1.0), "neutral": (172, 0.9), "positive": (166, 0.9)}


def load_scripts():
    return json.loads(SCRIPTS_FILE.read_text(encoding="utf-8"))


def get_script(script_id):
    return next((s for s in load_scripts() if s["id"] == script_id), None)


def normalise_lines(lines):
    """Script lines -> [{speaker, text, sentiment, pause_before?, overlap?}]."""
    out = []
    for ln in lines:
        if isinstance(ln, dict):
            item = dict(ln)
        else:
            item = {"speaker": ln[0], "text": ln[1], "sentiment": ln[2] if len(ln) > 2 else "neutral"}
            if len(ln) > 3 and isinstance(ln[3], dict):
                item.update(ln[3])
        item["speaker"] = "agent" if str(item["speaker"]).upper().startswith("A") else "customer"
        item["sentiment"] = item.get("sentiment") or "neutral"
        item["text"] = str(item["text"]).strip()
        if item["text"]:
            out.append(item)
    return out


LINE_RE = re.compile(r"^\s*(agent|customer|a|c)\s*(?:\[(negative|neutral|positive)\])?\s*:\s*(.+)$", re.I)


def parse_script_text(text):
    """Parse 'Agent: ...' / 'Customer [negative]: ...' lines typed in the studio."""
    lines, bad = [], []
    for i, raw in enumerate(text.splitlines(), 1):
        if not raw.strip():
            continue
        m = LINE_RE.match(raw)
        if not m:
            bad.append(i)
            continue
        lines.append({"speaker": m.group(1), "text": m.group(3), "sentiment": (m.group(2) or "neutral").lower()})
    return normalise_lines(lines), bad


def _render_lines(lines, tmp):
    jobs = []
    for i, ln in enumerate(lines):
        rate, vol = RATES.get(ln["sentiment"], RATES["neutral"])
        if ln["speaker"] == "agent":
            rate, vol = 172, 0.9
        jobs.append({"text": ln["text"], "voice": ln["speaker"], "rate": rate, "volume": vol,
                     "out": str(Path(tmp) / f"line_{i:03d}.wav")})
    job_file = Path(tmp) / "jobs.json"
    job_file.write_text(json.dumps(jobs), encoding="utf-8")
    res = subprocess.run([sys.executable, str(WORKER), str(job_file)], capture_output=True, text=True, timeout=600)
    if res.returncode != 0:
        raise RuntimeError(f"Speech synthesis failed: {(res.stderr or res.stdout)[-400:]}")
    return [j["out"] for j in jobs]


def _load_mono(path):
    import librosa
    y, sr = sf.read(path, dtype="float32", always_2d=True)
    y = y.mean(axis=1)
    if sr != SR:
        y = librosa.resample(y, orig_sr=sr, target_sr=SR)
    # trim the synthesiser's leading/trailing silence so pauses come only from the script timing
    nz = np.flatnonzero(np.abs(y) > 0.01)
    if len(nz):
        y = y[max(0, nz[0] - 800): nz[-1] + 1600]
    return y


def synthesize(lines, out_path, seed=7):
    """Render script lines to a stereo FLAC. Returns the reference timeline (start/end per line)."""
    lines = normalise_lines(lines)
    if len(lines) < 2:
        raise ValueError("A call script needs at least two lines")
    rng = np.random.default_rng(seed)
    with tempfile.TemporaryDirectory() as tmp:
        clips = [_load_mono(p) for p in _render_lines(lines, tmp)]
    timeline, t, prev_end = [], 0.4, 0.0
    for ln, clip in zip(lines, clips):
        start = prev_end + float(ln.get("pause_before", rng.uniform(0.35, 0.8))) if timeline else t
        if ln.get("overlap"):
            start = max(0.0, prev_end - float(ln["overlap"]))
        end = start + len(clip) / SR
        timeline.append({**ln, "start": round(start, 2), "end": round(end, 2)})
        prev_end = max(prev_end, end)
    total = int((prev_end + 0.8) * SR)
    stereo = np.zeros((total, 2), dtype=np.float32)
    for ln, clip in zip(timeline, clips):
        ch = 0 if ln["speaker"] == "agent" else 1
        s = int(ln["start"] * SR)
        stereo[s:s + len(clip), ch] += clip
    stereo += rng.normal(0, 0.0015, stereo.shape).astype(np.float32)  # faint line noise
    stereo = np.clip(stereo, -1, 1)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    sf.write(out_path, stereo, SR, format="FLAC")
    return {"lines": timeline, "duration": round(total / SR, 2)}
