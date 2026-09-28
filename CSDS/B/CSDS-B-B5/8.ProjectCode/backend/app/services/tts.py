"""Offline text-to-speech with pyttsx3 (Windows SAPI5 / espeak), rendered to WAV for the browser.

pyttsx3 can hang on its second runAndWait() in a long-lived process, so each phrase is
rendered in a short-lived child process.
"""
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

WORKER = """
import sys, pyttsx3
text, out, rate = sys.argv[1], sys.argv[2], int(sys.argv[3])
e = pyttsx3.init()
e.setProperty("rate", rate)
e.save_to_file(text, out)
e.runAndWait()
"""


def synth(text: str, rate: int = 165, timeout: float = 30) -> tuple[bytes, float]:
    t = time.perf_counter()
    fd, name = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    path = Path(name)
    try:
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        r = subprocess.run([sys.executable, "-c", WORKER, text, str(path), str(rate)],
                           capture_output=True, timeout=timeout, creationflags=flags)
        data = path.read_bytes() if path.exists() else b""
        if r.returncode != 0 or len(data) < 100:
            raise RuntimeError("Text-to-speech failed: " + r.stderr.decode(errors="ignore")[-300:])
        return data, (time.perf_counter() - t) * 1000
    finally:
        path.unlink(missing_ok=True)
