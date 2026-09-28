"""Fetch the datasets CallSense uses (Kaggle, through kagglehub).

Usage: python scripts/download_data.py          # small datasets + the committed emotion-speech sample
       python scripts/download_data.py --full   # also the complete RAVDESS and CREMA-D archives into data/raw/

Everything except data/raw/ is already committed, so this script is only needed to rebuild the data folder.
Public datasets download without a Kaggle token. If Kaggle ever asks for one, set KAGGLE_USERNAME and KAGGLE_KEY
in .env (https://www.kaggle.com/settings -> API -> Create New Token).
"""
import os
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
load_dotenv(ROOT / ".env")
for k in ("KAGGLE_USERNAME", "KAGGLE_KEY"):
    if not os.getenv(k):
        os.environ.pop(k, None)

import kagglehub  # noqa: E402  (imported after empty credentials are removed)

BITEXT = "bitext/bitext-gen-ai-chatbot-customer-support-dataset"
CALLS = "oleksiymaliovanyy/call-center-transcripts-dataset"
AIRLINE = "crowdflower/twitter-airline-sentiment"
RAVDESS = "uwrfkaggler/ravdess-emotional-speech-audio"
CREMAD = "ejlok1/cremad"

# Voice-emotion evaluation sample: 4 emotions shared with the pretrained model (neutral, happy, sad, angry)
RAVDESS_EMO = {"01": "neutral", "03": "happy", "04": "sad", "05": "angry"}
CREMAD_EMO = {"NEU": "neutral", "HAP": "happy", "SAD": "sad", "ANG": "angry"}
N_ACTORS = 10


def copy_dataset(handle, dest, pattern="*"):
    src = Path(kagglehub.dataset_download(handle))
    dest.mkdir(parents=True, exist_ok=True)
    for f in src.rglob(pattern):
        if f.is_file():
            shutil.copy(f, dest / f.name)
    print(f"{handle} -> {dest.relative_to(ROOT)}")


def emotion_sample():
    out = DATA / "sample" / "emotion"
    for actor in range(1, N_ACTORS + 1):
        for code, emo in RAVDESS_EMO.items():
            intensity = "01" if code == "01" else "02"
            name = f"03-01-{code}-{intensity}-01-01-{actor:02d}.wav"
            dest = out / "ravdess" / name
            if not dest.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(kagglehub.dataset_download(RAVDESS, path=f"Actor_{actor:02d}/{name}"), dest)
        for code in CREMAD_EMO:
            name = f"{1000 + actor}_DFA_{code}_XX.wav"
            dest = out / "cremad" / name
            if not dest.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(kagglehub.dataset_download(CREMAD, path=f"AudioWAV/{name}"), dest)
    print(f"Emotion-speech sample -> {out.relative_to(ROOT)} ({len(list(out.rglob('*.wav')))} clips)")


def main():
    copy_dataset(BITEXT, DATA / "bitext", "*.csv")
    copy_dataset(CALLS, DATA / "call_center")
    copy_dataset(AIRLINE, DATA / "airline", "Tweets.csv")
    emotion_sample()
    if "--full" in sys.argv:
        for handle, name in ((RAVDESS, "ravdess"), (CREMAD, "cremad")):
            src = Path(kagglehub.dataset_download(handle))
            shutil.copytree(src, DATA / "raw" / name, dirs_exist_ok=True)
            print(f"{handle} (full) -> data/raw/{name}")


if __name__ == "__main__":
    main()
