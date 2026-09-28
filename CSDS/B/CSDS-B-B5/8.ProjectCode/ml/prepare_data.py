"""Build the committed landmark datasets from data/raw/ (run scripts/download_data.py first).

    python -m ml.prepare_data            # everything
    python -m ml.prepare_data letters    # one part: letters | include | videos

Outputs (all committed):
    data/letters_landmarks.csv      hand landmarks for A-Z / 1-9 images (seeded subset per class)
    data/words_landmarks.npz        INCLUDE takes for the 50-word vocabulary, (N, 32, 49, 2) body coords
    data/word_videos_landmarks.npz  word-video clips re-extracted with SignBridge's own live pipeline
    data/splits.json                seeded train / test split by take id (shared by both word sources)
    data/sample/                    a few raw images / takes / clips
"""
import json
import random
import shutil
import sys
from multiprocessing import Pool
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

from ml.features import body_frame, resample_sequence
from ml.vocab import LETTERS, WORD_VIDEO_FOLDERS, WORDS

ROOT = Path(__file__).resolve().parents[1]
RAW, DATA, SAMPLE = ROOT / "data" / "raw", ROOT / "data", ROOT / "data" / "sample"
SEED = 42
LETTER_IMAGES_PER_CLASS = 300
INCLUDE_ASPECT = 16 / 9  # INCLUDE source videos are 1920x1080
SAMPLE_CLIPS = {"GOOD": "MVI_9268", "MORNING": "MVI_5061", "TIME": "MVI_5078"}


# ---------------------------------------------------------------- letters
def _letter_rows(args):
    label, paths = args
    import mediapipe as mp

    rows = []
    with mp.solutions.hands.Hands(static_image_mode=True, max_num_hands=2, min_detection_confidence=0.3) as hands:
        for p in paths:
            img = cv2.imread(str(p))
            img = cv2.resize(img, (256, 256), interpolation=cv2.INTER_CUBIC)
            res = hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            if not res.multi_hand_landmarks:
                continue
            coords = np.zeros((2, 21, 2), np.float32)
            for k, hl in enumerate(res.multi_hand_landmarks[:2]):
                coords[k] = [[lm.x, lm.y] for lm in hl.landmark]
            n = min(len(res.multi_hand_landmarks), 2)
            rows.append([label, p.name, n] + coords.ravel().round(5).tolist())
    return rows


def prepare_letters():
    src = RAW / "letters" / "Indian"
    rng = random.Random(SEED)
    jobs = []
    for label in LETTERS:
        files = sorted((src / label).glob("*.jpg"))
        jobs.append((label, rng.sample(files, min(LETTER_IMAGES_PER_CLASS, len(files)))))
        out = SAMPLE / "letters" / label
        out.mkdir(parents=True, exist_ok=True)
        for p in files[:2]:
            shutil.copyfile(p, out / p.name)
    with Pool(6) as pool:
        rows = [r for part in pool.map(_letter_rows, jobs) for r in part]
    cols = ["label", "image", "n_hands"] + [f"h{k}_{a}{i}" for k in range(2) for i in range(21) for a in "xy"]
    df = pd.DataFrame(rows, columns=cols)
    df.to_csv(DATA / "letters_landmarks.csv", index=False)
    print(f"letters: {len(df)} / {sum(len(j[1]) for j in jobs)} images with hands detected")


# ---------------------------------------------------------------- INCLUDE takes
def _points(g, n):
    arr = np.full((n, 2), np.nan, np.float32)
    arr[g.landmark_index.values] = g[["x", "y"]].values
    return None if np.isnan(arr).all() else arr


def include_take(path):
    df = pd.read_parquet(path, columns=["frame", "type", "landmark_index", "x", "y"])
    df = df[df.type != "face"]
    frames = []
    for _, f in df.groupby("frame", sort=True):
        parts = {t: g for t, g in f.groupby("type")}
        pose = _points(parts["pose"], 33) if "pose" in parts else None
        lh = _points(parts["left_hand"], 21) if "left_hand" in parts else None
        rh = _points(parts["right_hand"], 21) if "right_hand" in parts else None
        frames.append(body_frame(pose, lh, rh, INCLUDE_ASPECT))
    return resample_sequence(frames)


def _include_job(args):
    gloss, path = args
    return gloss, Path(path).stem, include_take(path)


def prepare_include():
    jobs = []
    for w in WORDS:
        for p in sorted((RAW / "include" / "keypoints" / w["source"]).glob("*.parquet")):
            jobs.append((w["gloss"], str(p)))
    with Pool(6) as pool:
        res = pool.map(_include_job, jobs)
    X = np.stack([r[2] for r in res]).astype(np.float16)
    np.savez_compressed(DATA / "words_landmarks.npz", X=X, gloss=np.array([r[0] for r in res]),
                        take=np.array([r[1] for r in res]))
    # seeded, stratified 80/20 split by take id
    rng = random.Random(SEED)
    split = {}
    for w in WORDS:
        takes = sorted(r[1] for r in res if r[0] == w["gloss"])
        rng.shuffle(takes)
        n_test = max(2, round(len(takes) * 0.2))
        for i, t in enumerate(takes):
            split[f"{w['gloss']}/{t}"] = "test" if i < n_test else "train"
    (DATA / "splits.json").write_text(json.dumps(split, indent=0, sort_keys=True))
    out = SAMPLE / "include"
    out.mkdir(parents=True, exist_ok=True)
    for gloss, path in jobs:
        if gloss in ("HELLO", "HOW_ARE_YOU", "YOU") and not (out / f"{gloss}.parquet").exists():
            shutil.copyfile(path, out / f"{gloss}.parquet")
    print(f"include: {len(X)} takes, {len(set(r[0] for r in res))} words")


# ---------------------------------------------------------------- word videos (own pipeline)
def video_sequence(path, holistic=None):
    """Run the same MediaPipe Holistic config the live backend uses over a video."""
    from backend.app.services.landmarks import Extractor

    ext = holistic or Extractor()
    cap = cv2.VideoCapture(str(path))
    frames = []
    while True:
        ok, img = cap.read()
        if not ok:
            break
        frames.append(ext.frame(img)[0])
    cap.release()
    ext.reset()
    return resample_sequence(frames) if frames else None


def _video_job(paths):
    from backend.app.services.landmarks import Extractor

    ext = Extractor()
    return [(g, Path(p).stem, video_sequence(p, ext)) for g, p in paths]


def prepare_videos():
    src = RAW / "word_videos" / "ProcessedData_vivit"
    jobs = [(WORD_VIDEO_FOLDERS[d.name], str(p)) for d in sorted(src.iterdir())
            if d.name in WORD_VIDEO_FOLDERS for p in sorted(d.glob("*.MOV"))]
    chunks = [jobs[i::6] for i in range(6)]
    with Pool(6) as pool:
        res = [r for part in pool.map(_video_job, chunks) for r in part if r[2] is not None]
    X = np.stack([r[2] for r in res]).astype(np.float16)
    np.savez_compressed(DATA / "word_videos_landmarks.npz", X=X, gloss=np.array([r[0] for r in res]),
                        take=np.array([r[1] for r in res]))
    out = SAMPLE / "word_videos"
    out.mkdir(parents=True, exist_ok=True)
    for g, p in jobs:  # held-out (test split) clips where MediaPipe sees the hands well
        if SAMPLE_CLIPS.get(g) == Path(p).stem:
            shutil.copyfile(p, out / f"{g}.MOV")
    print(f"word videos: {len(X)} clips, {len(set(r[0] for r in res))} words")


if __name__ == "__main__":
    parts = sys.argv[1:] or ["letters", "include", "videos"]
    for part in parts:
        {"letters": prepare_letters, "include": prepare_include, "videos": prepare_videos}[part]()
