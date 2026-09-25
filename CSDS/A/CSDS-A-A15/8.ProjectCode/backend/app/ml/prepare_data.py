"""
One-off script: reorganizes the raw NEU-CLS export into a stratified
train/val/test ImageFolder layout the training script can consume directly.

Run once:  python -m app.ml.prepare_data
"""
import random
import shutil
from collections import defaultdict
from pathlib import Path

from app.ml.labels import CLASS_NAMES

RAW_ROOT = Path(__file__).resolve().parents[2] / "data" / "NEU-CLS"
OUT_ROOT = Path(__file__).resolve().parents[2] / "data" / "processed"
SPLIT_RATIOS = {"train": 0.70, "val": 0.15, "test": 0.15}
SEED = 42


def collect_images_by_class() -> dict[str, list[Path]]:
    by_class: dict[str, list[Path]] = defaultdict(list)
    for sub in ["train/train/images", "valid/valid/images"]:
        folder = RAW_ROOT / sub
        for img_path in folder.glob("*.jpg"):
            for cls in CLASS_NAMES:
                if img_path.stem.startswith(cls + "_"):
                    by_class[cls].append(img_path)
                    break
    return by_class


def main() -> None:
    random.seed(SEED)
    if OUT_ROOT.exists():
        shutil.rmtree(OUT_ROOT)

    by_class = collect_images_by_class()
    summary = {}

    for cls, paths in by_class.items():
        paths = sorted(paths)
        random.shuffle(paths)
        n = len(paths)
        n_train = int(n * SPLIT_RATIOS["train"])
        n_val = int(n * SPLIT_RATIOS["val"])

        splits = {
            "train": paths[:n_train],
            "val": paths[n_train : n_train + n_val],
            "test": paths[n_train + n_val :],
        }
        summary[cls] = {k: len(v) for k, v in splits.items()}

        for split_name, split_paths in splits.items():
            dest_dir = OUT_ROOT / split_name / cls
            dest_dir.mkdir(parents=True, exist_ok=True)
            for src in split_paths:
                shutil.copy2(src, dest_dir / src.name)

    print("Dataset prepared at:", OUT_ROOT)
    for cls, counts in summary.items():
        print(f"  {cls:18s} train={counts['train']:>3} val={counts['val']:>3} test={counts['test']:>3}")


if __name__ == "__main__":
    main()
