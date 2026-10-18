"""Offline text-to-speech wrapper (pyttsx3 / Windows SAPI5).

pyttsx3's runAndWait() blocks and its engine is not safe to share across
threads while speaking, so every Speak request spins up its own short-lived
engine instance on a daemon thread. This keeps the GUI responsive and avoids
"run loop already started" errors from reusing one engine.
"""

from __future__ import annotations

import threading


def speak_async(text: str, rate: int = 165) -> None:
    text = (text or "").strip()
    if not text:
        return

    def _run():
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.setProperty("rate", rate)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as exc:  # pragma: no cover - best effort TTS
            print(f"[tts] speech failed: {exc}")

    threading.Thread(target=_run, daemon=True).start()
