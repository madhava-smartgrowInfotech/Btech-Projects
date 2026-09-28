"""End-to-end smoke test against the running backend (start it with run.bat or uvicorn first).

    venv\\Scripts\\python scripts\\smoke_test.py

Drives the real pipeline: login -> camera frames from a sample sign clip -> recognised sign ->
sentence -> speech (WAV) -> speech back to subtitles -> saved transcript -> metrics.
"""
import io
import os
import sys
import time
import uuid
import wave
from pathlib import Path

import cv2
import numpy as np
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
BASE = f"http://127.0.0.1:{os.getenv('BACKEND_PORT', '8205')}/api"
failures = []


def check(name, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""))
    if not cond:
        failures.append(name)


def jpeg(img):
    return cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])[1].tobytes()


def pcm16k(wav_bytes):
    with wave.open(io.BytesIO(wav_bytes)) as w:
        rate, ch = w.getframerate(), w.getnchannels()
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)
    if ch > 1:
        a = a.reshape(-1, ch).mean(1)
    t = np.arange(0, len(a) / rate, 1 / 16000)
    return np.interp(t, np.arange(len(a)) / rate, a).astype(np.int16).tobytes()


def main():
    for _ in range(60):  # wait for the server
        try:
            health = requests.get(f"{BASE}/health", timeout=5).json()
            break
        except requests.RequestException:
            time.sleep(2)
    else:
        sys.exit("Backend is not reachable on " + BASE)
    check("health", health["status"] == "ok" and health["models_loaded"], str(health))

    # auth
    email = f"smoke-{uuid.uuid4().hex[:8]}@signbridge.app"
    r = requests.post(f"{BASE}/auth/register", json={"name": "Smoke Test", "email": email, "password": "secret123"})
    check("register", r.ok, r.text[:120])
    r = requests.post(f"{BASE}/auth/login", json={"email": "demo@signbridge.app", "password": "demo1234"})
    check("demo login", r.ok)
    r = requests.post(f"{BASE}/auth/login", json={"email": email, "password": "wrong"})
    check("wrong password rejected", r.status_code == 401)
    token = requests.post(f"{BASE}/auth/login", json={"email": email, "password": "secret123"}).json()["token"]
    H = {"Authorization": f"Bearer {token}"}
    check("protected route needs login", requests.get(f"{BASE}/conversations").status_code == 401)

    vocab = requests.get(f"{BASE}/vocab").json()
    check("vocabulary", len(vocab["words"]) == 50 and len(vocab["letters"]) == 35)

    # F1: word signs from a real sample clip, streamed frame by frame, then hands down
    session = uuid.uuid4().hex[:10]
    signs, latencies = [], []
    for clip in ("GOOD", "MORNING", "TIME"):  # held-out clips
        requests.post(f"{BASE}/recognize/reset", params={"session": session}, headers=H)
        cap = cv2.VideoCapture(str(ROOT / "data" / "sample" / "word_videos" / f"{clip}.MOV"))
        frames = []
        while True:
            ok, img = cap.read()
            if not ok:
                break
            frames.append(img)
        rest = np.full_like(frames[0], 235)  # empty scene - no hands
        for img in frames + [rest] * 8:
            # the sample clips are tiny (224 px), so send them losslessly
            r = requests.post(f"{BASE}/recognize/frame", params={"session": session, "mode": "words"},
                              data=cv2.imencode(".png", img)[1].tobytes(), headers={**H, "Content-Type": "image/png"})
            r.raise_for_status()
            d = r.json()
            latencies.append(d["latency_ms"]["total"])
            signs += [(clip, e) for e in d["events"] if e["type"] == "sign"]
            if img is rest:
                time.sleep(0.08)  # hands lowered long enough to close the sign
    got = [(c, e["gloss"], e["confidence"]) for c, e in signs]
    check("word signs recognised", len(signs) == 3, str(got))
    check("sample signs correct", all(c == g for c, g, _ in got), str(got))
    check("frame latency reported", np.mean(latencies) > 0, f"avg {np.mean(latencies):.0f} ms/frame")

    # F1: fingerspelling from sample letter images
    session2 = uuid.uuid4().hex[:10]
    letters = []
    for letter in ("B", "C"):
        img_path = sorted((ROOT / "data" / "sample" / "letters" / letter).glob("*.jpg"))[0]
        img = cv2.resize(cv2.imread(str(img_path)), (256, 256), interpolation=cv2.INTER_CUBIC)
        for _ in range(10):
            d = requests.post(f"{BASE}/recognize/frame", params={"session": session2, "mode": "letters"},
                              data=jpeg(img), headers={**H, "Content-Type": "image/jpeg"}).json()
            letters += [e["letter"] for e in d["events"] if e["type"] == "letter"]
        blank = np.full((256, 256, 3), 30, np.uint8)
        d = requests.post(f"{BASE}/recognize/frame", params={"session": session2, "mode": "letters"},
                          data=jpeg(blank), headers={**H, "Content-Type": "image/jpeg"}).json()
    check("letters recognised", letters == ["B", "C"], str(letters))
    time.sleep(1.3)
    d = requests.post(f"{BASE}/recognize/frame", params={"session": session2, "mode": "letters"},
                      data=jpeg(blank), headers={**H, "Content-Type": "image/jpeg"}).json()
    spelled = [e["gloss"] for e in d["events"] if e["type"] == "sign"]
    check("fingerspelled word emitted", spelled == ["BC"], str(spelled))

    # F2: sentence formation (offline rules, with and without online polish)
    r = requests.post(f"{BASE}/sentence", json={"glosses": ["HELLO", "HOW_ARE_YOU", "YOU"], "use_gemini": False}, headers=H).json()
    check("offline sentence", r["sentence"] == "Hello, how are you?", str(r))
    r2 = requests.post(f"{BASE}/sentence", json={"glosses": ["TODAY", "MOTHER", "SICK"]}, headers=H).json()
    check("sentence (online if available)", bool(r2["sentence"]), f"{r2['source']}: {r2['sentence']}")

    # F3: speech output
    r = requests.post(f"{BASE}/tts", json={"text": r["sentence"]}, headers=H)
    check("text-to-speech WAV", r.ok and r.content[:4] == b"RIFF", f"{len(r.content)} bytes, {r.headers.get('X-Latency-Ms')} ms")

    # F4: speech -> subtitles (feed the synthesised speech back through offline speech recognition)
    wav = requests.post(f"{BASE}/tts", json={"text": "Please take a seat, the doctor will see you soon."}, headers=H).content
    r = requests.post(f"{BASE}/speech/transcribe", params={"language": "en"}, data=pcm16k(wav),
                      headers={**H, "Content-Type": "application/octet-stream"}, timeout=180)
    text = r.json().get("text", "") if r.ok else r.text
    check("speech to subtitles", r.ok and "doctor" in text.lower(), f"{text!r} {r.json().get('latency_ms') if r.ok else ''} ms")

    # F5: transcript saved with both sides
    conv = {"title": "Smoke test", "messages": [
        {"side": "signer", "text": "Hello, how are you?", "gloss": ["HELLO", "HOW_ARE_YOU"], "confidence": 0.9, "source": "rules"},
        {"side": "hearing", "text": text or "fine", "source": "whisper"}]}
    r = requests.post(f"{BASE}/conversations", json=conv, headers=H)
    check("save conversation", r.ok, r.text[:100])
    cid = r.json()["id"]
    requests.post(f"{BASE}/conversations/{cid}/messages", json={"side": "signer", "text": "Thank you."}, headers=H)
    full = requests.get(f"{BASE}/conversations/{cid}", headers=H).json()
    check("history shows both sides", {m["side"] for m in full["messages"]} == {"signer", "hearing"} and len(full["messages"]) == 3)
    check("history list", any(c["id"] == cid for c in requests.get(f"{BASE}/conversations", headers=H).json()))

    # F6/F7: metrics
    m = requests.get(f"{BASE}/metrics").json()
    check("evaluation metrics available", "evaluation" in m and "confusion" in m["evaluation"]["words"])
    check("live latency tracked", (m["live"]["frames"] or 0) > 0, str(m["live"]))

    print("\nALL PASSED" if not failures else f"\n{len(failures)} FAILED: {failures}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
