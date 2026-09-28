"""Render lines of speech to WAV files with the offline system voices (pyttsx3).

Runs as its own process because the Windows speech engine (SAPI/COM) is not safe to drive from server threads.
Usage: python scripts/tts_worker.py jobs.json
jobs.json = [{"text": "...", "voice": "agent" | "customer", "rate": 175, "volume": 0.9, "out": "path.wav"}, ...]
"""
import json
import sys

import pyttsx3


def pick_voices(engine):
    voices = engine.getProperty("voices")
    if not voices:
        raise SystemExit("No offline text-to-speech voices are installed on this computer")
    male = next((v for v in voices if "david" in v.name.lower() or "male" in str(getattr(v, "gender", "")).lower()
                 and "female" not in str(getattr(v, "gender", "")).lower()), voices[0])
    female = next((v for v in voices if "zira" in v.name.lower() or "female" in str(getattr(v, "gender", "")).lower()),
                  voices[-1])
    return {"agent": male.id, "customer": female.id}


def main(path):
    jobs = json.load(open(path, encoding="utf-8"))
    engine = pyttsx3.init()
    voices = pick_voices(engine)
    # queue every line and run the loop once: a second runAndWait() hangs on some Windows setups
    for job in jobs:
        engine.setProperty("voice", voices[job.get("voice", "agent")])
        engine.setProperty("rate", int(job.get("rate", 175)))
        engine.setProperty("volume", float(job.get("volume", 0.9)))
        engine.save_to_file(job["text"], job["out"])
    engine.runAndWait()
    print(json.dumps({"ok": len(jobs), "voices": voices}))


if __name__ == "__main__":
    main(sys.argv[1])
