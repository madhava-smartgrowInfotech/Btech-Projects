"""Extract YOLO11n-pose keypoints from the dataset images -> data/keypoints/poses.npz.

Each image is processed three ways so the classifier learns dim-room poses (F4):
  normal    - original image
  dark      - darkened copy (exposure x0.25, gamma 1.8, sensor noise), no enhancement
  dark_enh  - darkened copy after CLAHE + gamma enhancement (what the live pipeline does)
CCTV images also contribute their annotated keypoints ("gt").
Seeded; run:  python ml/extract_keypoints.py
"""
import csv
import random
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.pose import PoseEstimator, darken, enhance  # noqa: E402

DATA = ROOT / "data"
OUT = DATA / "keypoints" / "poses.npz"
SEED = 42


def iou(a, b):
    x1, y1, x2, y2 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0


def yolo_boxes(label_file, w, h):
    out = []
    if not label_file.exists():
        return out
    for line in label_file.read_text().split("\n"):
        p = line.split()
        if len(p) < 5:
            continue
        c, cx, cy, bw, bh = int(p[0]), *map(float, p[1:5])
        box = [(cx - bw / 2) * w, (cy - bh / 2) * h, (cx + bw / 2) * w, (cy + bh / 2) * h]
        kp = None
        if len(p) >= 5 + 51:
            v = np.array(list(map(float, p[5:56]))).reshape(17, 3)
            kp = np.stack([v[:, 0] * w, v[:, 1] * h, np.where(v[:, 2] > 0, 0.9, 0.0)], 1).astype(np.float32)
        out.append((c, box, kp))
    return out


def items():
    """(source, image_path, split, spec) - spec is (source, label_file, class_map) or ("har", label)."""
    rng = random.Random(SEED)
    fd = DATA / "fall_detection"
    fmap = {0: "lying", 1: "standing", 2: "sitting"}
    for split_dir, split in (("train", "train"), ("val", "test")):
        for img in sorted((fd / "images" / split_dir).glob("*.jpg")):
            yield "fall_detection", img, split, ("fall_detection", fd / "labels" / split_dir / (img.stem + ".txt"), fmap)

    cc = DATA / "cctv_lying"
    imgs = sorted((cc / "images").glob("*.png"))
    for img in imgs:
        split = "test" if rng.random() < 0.25 else "train"
        yield "cctv", img, split, ("cctv", cc / "labels" / (img.stem + ".txt"), {0: "lying", 1: "standing"})

    har = DATA / "raw" / "har" if (DATA / "raw" / "har" / "labels.csv").exists() else DATA / "sample" / "har"
    hmap = {"drinking": "drinking", "sitting": "sitting", "sleeping": "lying"}
    with open(har / "labels.csv", newline="") as f:
        rows = sorted(csv.DictReader(f), key=lambda r: r["filename"])
    for r in rows:
        split = "test" if rng.random() < 0.25 else "train"
        yield "har", har / "images" / r["filename"], split, ("har", hmap[r["label"]])


PARTIAL = DATA / "keypoints" / "partial.pkl"


def main():
    import pickle

    est = PoseEstimator(imgsz=640)
    rec = {k: [] for k in ("kpts", "label", "source", "image", "split", "variant")}
    start = 0
    if PARTIAL.exists():  # resume after an interruption
        start, rec = pickle.loads(PARTIAL.read_bytes())
        print(f"resuming at image {start}")
    t0 = time.time()
    all_items = list(items())
    print(f"{len(all_items)} images", flush=True)
    for n, (source, img_path, split, spec) in enumerate(all_items):
        if n < start:
            continue
        rng = np.random.default_rng(SEED + n)  # per-image seed keeps results identical after a resume
        if n % 100 == 0 and n > start:
            PARTIAL.parent.mkdir(parents=True, exist_ok=True)
            PARTIAL.write_bytes(pickle.dumps((n, rec)))
        frame = cv2.imread(str(img_path))
        if frame is None:
            continue
        h, w = frame.shape[:2]
        dark = darken(frame, factor=rng.uniform(0.18, 0.35), gamma=rng.uniform(1.5, 2.2), rng=rng)
        variants = {"normal": frame, "dark": dark, "dark_enh": enhance(dark)}
        boxes = yolo_boxes(spec[1], w, h) if spec[0] in ("fall_detection", "cctv") else None
        for vname, img in variants.items():
            people = est.detect(img)
            picks = []
            if boxes is None:  # HAR: one label per image -> largest person
                p = PoseEstimator.main_person(people)
                if p is not None:
                    picks.append((spec[1], p["kpts"]))
            else:
                for c, box, _ in boxes:
                    best = max(people, key=lambda p: iou(p["box"], box), default=None)
                    if best is not None and iou(best["box"], box) > 0.3 and c in spec[2]:
                        picks.append((spec[2][c], best["kpts"]))
            for label, k in picks:
                for key, val in (("kpts", k), ("label", label), ("source", source),
                                 ("image", f"{source}/{img_path.name}"), ("split", split), ("variant", vname)):
                    rec[key].append(val)
        if boxes is not None and spec[0] == "cctv":
            for c, _, gt in boxes:
                if gt is not None and c in spec[2]:
                    for key, val in (("kpts", gt), ("label", spec[2][c]), ("source", source),
                                     ("image", f"{source}/{img_path.name}"), ("split", split), ("variant", "gt")):
                        rec[key].append(val)
        if n % 200 == 0:
            print(f"  {n}/{len(all_items)}  poses={len(rec['kpts'])}  {time.time() - t0:.0f}s", flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT, kpts=np.stack(rec["kpts"]).astype(np.float32),
                        **{k: np.array(v) for k, v in rec.items() if k != "kpts"})
    PARTIAL.unlink(missing_ok=True)
    print(f"saved {len(rec['kpts'])} poses -> {OUT} in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
