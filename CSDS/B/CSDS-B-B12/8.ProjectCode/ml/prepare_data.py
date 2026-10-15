"""Build seeded train/val/test splits and cache preprocessed arrays.

python ml/prepare_data.py            (needs scripts/download_data.py to have run)
Outputs: experiments/splits.json, data/raw/cache/*.npz, data/sample/*
"""
import hashlib
import json
import os
import random
import shutil
from multiprocessing import Pool

import cv2
import numpy as np

from common import CACHE, CT_CLASSES, EXPERIMENTS, ROOT, SEED, SPLITS, XRAY_CLASSES, dataset_roots, imaging, read_gray

# images per class: train / val / test (small, CPU-friendly config)
XRAY_PER_CLASS = {"train": 500, "val": 100, "test": 200}
TB_PER_CLASS = {"train": 400, "val": 100, "test": 200}
SEG_PER_CLASS = {"train": 300, "val": 50, "test": 100}
COVID_DIRS = {"COVID-19": "COVID", "Viral Pneumonia": "Viral Pneumonia", "Lung Opacity": "Lung_Opacity", "Normal": "Normal"}
CT_DIRS = {"adenocarcinoma": 0, "large.cell.carcinoma": 1, "squamous.cell.carcinoma": 2, "normal": 3}


def take(files, counts, rng):
    files = sorted(files)
    rng.shuffle(files)
    out, i = {}, 0
    for split, n in counts.items():
        out[split] = files[i:i + n]
        i += n
    return out


def build_splits():
    rng = random.Random(SEED)
    roots = dataset_roots()
    xray = {s: [] for s in XRAY_PER_CLASS}
    seg = {s: [] for s in SEG_PER_CLASS}
    for label, d in COVID_DIRS.items():
        files = [f"{d}/images/{f}" for f in os.listdir(os.path.join(roots["covid"], d, "images"))]
        counts = XRAY_PER_CLASS if label != "Normal" else {k: v // 2 for k, v in XRAY_PER_CLASS.items()}
        chosen = take(files, counts, rng)
        used = set(sum(chosen.values(), []))
        for s, fs in chosen.items():
            xray[s] += [["covid", f, XRAY_CLASSES.index(label)] for f in fs]
        rest = [f for f in files if f not in used]
        for s, fs in take(rest, SEG_PER_CLASS, rng).items():
            seg[s] += [["covid", f, f.replace("/images/", "/masks/")] for f in fs]
    for label, d, counts in [("Tuberculosis", "Tuberculosis", TB_PER_CLASS),
                             ("Normal", "Normal", {k: v // 2 for k, v in XRAY_PER_CLASS.items()})]:
        files = [f"{d}/{f}" for f in os.listdir(os.path.join(roots["tb"], d))]
        for s, fs in take(files, counts, rng).items():
            xray[s] += [["tb", f, XRAY_CLASSES.index(label)] for f in fs]

    # CT: keep the published split, drop byte-identical duplicates within and across splits
    ct = {"train": [], "val": [], "test": []}
    seen, dropped = set(), 0
    for split, folder in [("train", "train"), ("val", "valid"), ("test", "test")]:
        base = os.path.join(roots["ct"], folder)
        for d in sorted(os.listdir(base)):
            label = next(v for k, v in CT_DIRS.items() if d.startswith(k))
            for f in sorted(os.listdir(os.path.join(base, d))):
                digest = hashlib.md5(open(os.path.join(base, d, f), "rb").read()).hexdigest()
                if digest in seen:
                    dropped += 1
                    continue
                seen.add(digest)
                ct[split].append(["ct", f"{folder}/{d}/{f}", label])
    splits = {"seed": SEED, "xray": xray, "seg": seg, "ct": ct, "ct_duplicates_dropped": dropped}
    SPLITS.parent.mkdir(parents=True, exist_ok=True)
    SPLITS.write_text(json.dumps(splits))
    print({k: {s: len(v) for s, v in splits[k].items()} for k in ("xray", "seg", "ct")}, "CT duplicates dropped:", dropped)
    return splits


def _cls_item(item):
    key, rel, label = item
    return imaging.preprocess(read_gray(key, rel))["enhanced"], label


def _seg_item(item):
    key, rel, mask_rel = item
    gray = read_gray(key, rel)
    mask = cv2.imread(os.path.join(dataset_roots()[key], mask_rel), cv2.IMREAD_GRAYSCALE)
    mask = cv2.resize(mask, (imaging.SEG_SIZE, imaging.SEG_SIZE), interpolation=cv2.INTER_NEAREST) > 127
    return imaging.to_seg_array(gray)[0], mask


def cache(splits):
    CACHE.mkdir(parents=True, exist_ok=True)
    with Pool(max(1, (os.cpu_count() or 2) - 2)) as pool:
        for task in ("xray", "ct"):
            for split, items in splits[task].items():
                out = pool.map(_cls_item, items, chunksize=16)
                np.savez_compressed(CACHE / f"{task}_{split}.npz", x=np.stack([o[0] for o in out]), y=np.array([o[1] for o in out]))
                print("cached", task, split, len(out))
        for split, items in splits["seg"].items():
            out = pool.map(_seg_item, items, chunksize=16)
            np.savez_compressed(CACHE / f"seg_{split}.npz", x=np.stack([o[0] for o in out]).astype(np.float16), m=np.stack([o[1] for o in out]))
            print("cached seg", split, len(out))


def samples(splits):
    """Copy a small labelled sample of the X-ray test split into data/sample/ (committed)."""
    roots = dataset_roots()
    out = ROOT / "data" / "sample"
    per_class = {}
    for key, rel, label in splits["xray"]["test"]:
        name = XRAY_CLASSES[label]
        if per_class.get(name, 0) >= 6:
            continue
        per_class[name] = per_class.get(name, 0) + 1
        dst = out / "xray" / name.replace(" ", "_").replace("-", "")
        dst.mkdir(parents=True, exist_ok=True)
        shutil.copy(os.path.join(roots[key], rel), dst / os.path.basename(rel))
    for key, rel, mask_rel in splits["seg"]["test"][:6]:
        (out / "lung_masks" / "images").mkdir(parents=True, exist_ok=True)
        (out / "lung_masks" / "masks").mkdir(parents=True, exist_ok=True)
        shutil.copy(os.path.join(roots[key], rel), out / "lung_masks" / "images" / os.path.basename(rel))
        shutil.copy(os.path.join(roots[key], mask_rel), out / "lung_masks" / "masks" / os.path.basename(rel))
    # non-chest images for the modality check (scikit-learn's bundled public-domain photos)
    from sklearn.datasets import load_sample_images

    (out / "other").mkdir(parents=True, exist_ok=True)
    for i, img in enumerate(load_sample_images().images):
        cv2.imwrite(str(out / "other" / f"photo_{i + 1}.jpg"), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    print("samples written to", out)


if __name__ == "__main__":
    s = build_splits()
    cache(s)
    samples(s)
    EXPERIMENTS.mkdir(exist_ok=True)
