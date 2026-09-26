"""
train.py
--------
Training pipeline for the plastic-waste YOLO detector.

Usage:
    python train.py
    python train.py --epochs 100 --img-size 640 --batch-size 16
    python train.py --data data/data.yaml --weights yolov8n.pt

REQUIRED USER INPUT:
This script expects an annotated dataset already placed under
data/images/{train,val,test} and data/labels/{train,val,test}
in YOLO format (see data/data.yaml and README.md for the exact
layout). Without a dataset, this script will fail at the
data-loading step — that is expected, not a bug.

Uses transfer learning: training starts from COCO-pretrained
YOLOv8 weights rather than random initialisation, which needs
far less data/epochs to converge — important for a small,
manually-annotated ocean-plastic dataset.
"""

import argparse
import shutil
from pathlib import Path

from ultralytics import YOLO

from src.model import get_device
from src.utils import MODELS_DIR, PROJECT_ROOT, RESULTS_DIR, ensure_dirs

# ---- Configurable defaults (override via CLI flags) ----
EPOCHS = 50
IMG_SIZE = 640
BATCH_SIZE = 16
PRETRAINED_WEIGHTS = "yolov8n.pt"  # small/fast; swap for yolov8s/m for higher accuracy


def parse_args():
    parser = argparse.ArgumentParser(description="Train the plastic-waste YOLO model.")
    parser.add_argument("--data", type=str, default=str(PROJECT_ROOT / "data" / "data.yaml"),
                         help="Path to data.yaml")
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    parser.add_argument("--img-size", type=int, default=IMG_SIZE)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--weights", type=str, default=PRETRAINED_WEIGHTS,
                         help="Starting weights for transfer learning")
    parser.add_argument("--project-name", type=str, default="plastic_waste_run",
                         help="Name for this training run's output folder")
    return parser.parse_args()


def main():
    args = parse_args()
    device = get_device()
    ensure_dirs(MODELS_DIR, RESULTS_DIR)

    print(f"Device: {device}")
    print(f"Data config: {args.data}")
    print(f"Epochs: {args.epochs} | Image size: {args.img_size} | Batch size: {args.batch_size}")

    if not Path(args.data).exists():
        raise FileNotFoundError(
            f"Dataset config not found at {args.data}. REQUIRED USER INPUT: "
            "create/annotate your dataset and data.yaml before training. "
            "See README.md -> 'Dataset requirements'."
        )

    # Load a COCO-pretrained model as the starting point (transfer learning)
    model = YOLO(args.weights)

    # Train
    results = model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.img_size,
        batch=args.batch_size,
        device=device,
        project=str(PROJECT_ROOT / "runs"),
        name=args.project_name,
        exist_ok=True,
    )

    # Locate ultralytics' own run folder (contains weights + plots)
    run_dir = Path(results.save_dir)
    best_weights = run_dir / "weights" / "best.pt"

    if best_weights.exists():
        shutil.copy(best_weights, MODELS_DIR / "best.pt")
        print(f"Saved best model to {MODELS_DIR / 'best.pt'}")
    else:
        print("WARNING: best.pt not found in run output — check training logs above.")

    # Copy key training plots into results/ so the Streamlit app can display them
    for plot_name in ["results.png", "confusion_matrix.png", "P_curve.png",
                       "R_curve.png", "PR_curve.png"]:
        src_plot = run_dir / plot_name
        if src_plot.exists():
            shutil.copy(src_plot, RESULTS_DIR / plot_name)

    print(f"Training complete. Full run artifacts: {run_dir}")
    print(f"Plots copied to: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
