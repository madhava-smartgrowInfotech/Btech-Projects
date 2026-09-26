"""
evaluate.py
-----------
Evaluates a trained model on the validation/test split and
reports Precision, Recall, mAP@0.5 and mAP@0.5:0.95 — using
Ultralytics' built-in validation, so numbers are computed from
the actual model, never fabricated.

Usage:
    python evaluate.py
    python evaluate.py --weights models/best.pt --data data/data.yaml --split test
"""

import argparse
import json
import shutil
from pathlib import Path

from ultralytics import YOLO

from src.model import get_device
from src.utils import MODELS_DIR, PROJECT_ROOT, RESULTS_DIR, ensure_dirs


def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate the trained plastic-waste model.")
    parser.add_argument("--weights", type=str, default=str(MODELS_DIR / "best.pt"))
    parser.add_argument("--data", type=str, default=str(PROJECT_ROOT / "data" / "data.yaml"))
    parser.add_argument("--split", type=str, default="val", choices=["val", "test"])
    return parser.parse_args()


def main():
    args = parse_args()
    ensure_dirs(RESULTS_DIR)
    device = get_device()

    weights_path = Path(args.weights)
    if not weights_path.exists():
        raise FileNotFoundError(
            f"No trained weights found at {weights_path}. REQUIRED USER INPUT: "
            "run train.py first to produce models/best.pt."
        )
    if not Path(args.data).exists():
        raise FileNotFoundError(f"Dataset config not found at {args.data}.")

    model = YOLO(str(weights_path))

    metrics = model.val(data=args.data, split=args.split, device=device,
                         project=str(PROJECT_ROOT / "runs"), name="evaluation",
                         exist_ok=True)

    # Pull out the headline numbers Ultralytics computes
    summary = {
        "precision": float(metrics.box.mp),         # mean precision across classes
        "recall": float(metrics.box.mr),             # mean recall across classes
        "map50": float(metrics.box.map50),            # mAP@0.5
        "map50_95": float(metrics.box.map),           # mAP@0.5:0.95
    }

    print("Evaluation results (computed from the actual model — not fabricated):")
    for k, v in summary.items():
        print(f"  {k}: {v:.4f}")

    # Save summary as JSON for the Streamlit Evaluation page to read
    with open(RESULTS_DIR / "eval_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    # Copy confusion matrix / PR curve plots produced by val() into results/
    run_dir = Path(metrics.save_dir)
    for plot_name in ["confusion_matrix.png", "confusion_matrix_normalized.png",
                       "P_curve.png", "R_curve.png", "PR_curve.png", "F1_curve.png"]:
        src_plot = run_dir / plot_name
        if src_plot.exists():
            shutil.copy(src_plot, RESULTS_DIR / plot_name)

    print(f"Summary saved to {RESULTS_DIR / 'eval_summary.json'}")
    print(f"Plots copied to {RESULTS_DIR}")


if __name__ == "__main__":
    main()
