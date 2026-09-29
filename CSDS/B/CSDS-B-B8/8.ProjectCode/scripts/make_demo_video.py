"""Build the sample video data/sample/demo_fall.mp4 from dataset stills (deterministic).

Sample data: 5 s of a standing person, then 15 s of a person lying on the floor, taken from the
Fall Detection Dataset validation images. It lets the smoke test and a first demo drive the real
pipeline (enhancement, pose model, classifier, fall detector, alerts) without a camera.
The first standing/lying pair (in file order) that the live pipeline reads correctly - standing
recognised as standing, lying as lying, and a fall confirmed - is used.

    python scripts/make_demo_video.py
"""
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.activity import ActivityRecognizer  # noqa: E402
from app.services.fall import FallDetector  # noqa: E402
from app.services.features import body_geometry  # noqa: E402
from app.services.pose import get_estimator, maybe_enhance  # noqa: E402

OUT = ROOT / "data" / "sample" / "demo_fall.mp4"
W, H, FPS = 640, 480, 15
STAND_S, LIE_S = 5, 15


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


def single_kpts(est, frame):
    img, _, _ = maybe_enhance(frame, "auto")
    people = est.detect(img)
    return people[0]["kpts"] if len(people) == 1 else None


def simulate(ks, kl, fps=8):
    """Run the live recogniser + fall detector over the video at the live frame rate."""
    rec, fd = ActivityRecognizer(), FallDetector(confirm_seconds=3.0)
    seen_stand, seen_lie, fell = [], [], False
    n = (STAND_S + LIE_S) * fps
    for i in range(n):
        t = i / fps
        k = ks if t < STAND_S else kl
        lab, _, pr = rec.update(t, k)
        ev = fd.update(t, k, pr.get("lying", 0.0))
        fell |= bool(ev and ev["type"] == "fall")
        if 2 <= t < STAND_S:
            seen_stand.append(lab)
        elif t >= STAND_S + 2:
            seen_lie.append(lab)
    ok_stand = np.mean([l == "standing" for l in seen_stand]) > 0.8
    ok_lie = np.mean([l == "lying" for l in seen_lie]) > 0.8
    return ok_stand and ok_lie and fell


def main():
    est = get_estimator()
    imgs = sorted((ROOT / "data" / "fall_detection" / "images" / "val").glob("*.jpg"))
    standing = [p for p in imgs if labels(p) == [1]]
    lying = [p for p in imgs if labels(p) == [0]]
    lie_k = []
    for l in lying:
        fl = letterbox(cv2.imread(str(l)))
        k = single_kpts(est, fl)
        if k is not None and body_geometry(k) and body_geometry(k)[2] > 60:
            lie_k.append((l, fl, k))
    for s in standing:
        fs = letterbox(cv2.imread(str(s)))
        ks = single_kpts(est, fs)
        if ks is None or body_geometry(ks) is None or body_geometry(ks)[2] > 20:
            continue
        for l, fl, kl in lie_k:
            if simulate(ks, kl):
                OUT.parent.mkdir(parents=True, exist_ok=True)
                vw = cv2.VideoWriter(str(OUT), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))
                for _ in range(STAND_S * FPS):
                    vw.write(fs)
                for _ in range(LIE_S * FPS):
                    vw.write(fl)
                vw.release()
                print(f"standing={s.name} lying={l.name} -> {OUT}")
                return
    raise SystemExit("No suitable standing/lying pair found")


if __name__ == "__main__":
    main()
