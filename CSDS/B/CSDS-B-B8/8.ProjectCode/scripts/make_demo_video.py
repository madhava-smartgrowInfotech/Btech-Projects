"""Build the sample video data/sample/demo_fall.mp4 from dataset stills (seeded, deterministic).

Sample data: 5 s of a standing person, then 15 s of a person lying on the floor, taken from the
Fall Detection Dataset validation images. It lets the smoke test and a first demo drive the real
pipeline (pose model, classifier, fall detector, alerts) without a camera.

    python scripts/make_demo_video.py
"""
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.features import body_geometry  # noqa: E402
from app.services.pose import PoseEstimator  # noqa: E402

OUT = ROOT / "data" / "sample" / "demo_fall.mp4"
W, H, FPS = 640, 480, 15


def letterbox(img):
    h, w = img.shape[:2]
    s = min(W / w, H / h)
    r = cv2.resize(img, (int(w * s), int(h * s)))
    out = np.zeros((H, W, 3), np.uint8)
    y, x = (H - r.shape[0]) // 2, (W - r.shape[1]) // 2
    out[y:y + r.shape[0], x:x + r.shape[1]] = r
    return out


def labels(img_path):
    lab = ROOT / "data" / "fall_detection" / "labels" / "val" / (img_path.stem + ".txt")
    return [int(l.split()[0]) for l in lab.read_text().split("\n") if l.strip()] if lab.exists() else []


def single_pose(est, frame):
    people = est.detect(frame)
    if len(people) != 1:
        return None
    return body_geometry(people[0]["kpts"])


def main():
    est = PoseEstimator(imgsz=480)
    imgs = sorted((ROOT / "data" / "fall_detection" / "images" / "val").glob("*.jpg"))
    standing = [p for p in imgs if labels(p) == [1]]
    lying = [p for p in imgs if labels(p) == [0]]
    for s in standing:
        fs = letterbox(cv2.imread(str(s)))
        gs = single_pose(est, fs)
        if gs is None or gs[2] > 20:
            continue
        for l in lying:
            fl = letterbox(cv2.imread(str(l)))
            gl = single_pose(est, fl)
            if gl is None or gl[2] < 60:
                continue
            drop = (gl[0][1] - gs[0][1]) / gs[5]
            if drop > 0.45:
                OUT.parent.mkdir(parents=True, exist_ok=True)
                vw = cv2.VideoWriter(str(OUT), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
                for _ in range(5 * FPS):
                    vw.write(fs)
                for _ in range(15 * FPS):
                    vw.write(fl)
                vw.release()
                print(f"standing={s.name} lying={l.name} drop={drop:.2f} body heights -> {OUT}")
                return
    raise SystemExit("No suitable standing/lying pair found")


if __name__ == "__main__":
    main()
