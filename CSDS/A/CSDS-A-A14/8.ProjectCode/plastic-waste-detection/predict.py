"""
predict.py
----------
Command-line single-image inference — useful for quick testing
without launching the Streamlit app, and reused by the app
itself via src/detection.py + src/model.py.

Usage:
    python predict.py --image path/to/image.jpg
    python predict.py --image path/to/image.jpg --conf 0.4
"""

import argparse
import json
from pathlib import Path

import cv2

from src.database import add_record
from src.detection import detections_to_rows, run_detection
from src.model import load_model
from src.preprocessing import preprocess_image
from src.utils import REPORTS_DIR, RESULTS_DIR, ensure_dirs, is_valid_image_file, timestamp_now


def parse_args():
    parser = argparse.ArgumentParser(description="Run plastic-waste detection on a single image.")
    parser.add_argument("--image", type=str, required=True, help="Path to input image")
    parser.add_argument("--conf", type=float, default=0.5, help="Confidence threshold (0.1-0.9)")
    parser.add_argument("--no-preprocess", action="store_true",
                         help="Skip the preprocessing pipeline (raw image only)")
    parser.add_argument("--save-history", action="store_true",
                         help="Log this run to the SQLite detection history")
    return parser.parse_args()


def main():
    args = parse_args()
    ensure_dirs(RESULTS_DIR, REPORTS_DIR)

    image_path = Path(args.image)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")
    if not is_valid_image_file(image_path.name):
        raise ValueError("Unsupported file type. Use .jpg, .jpeg or .png")

    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Could not read image (corrupted or invalid file): {image_path}")

    model, device, used_fallback, msg = load_model()
    print(f"Device: {device}")
    if used_fallback:
        print(f"WARNING: {msg}")

    processed = image if args.no_preprocess else preprocess_image(image)
    annotated, detections = run_detection(model, processed, conf_threshold=args.conf)

    print(f"Detected Plastic Objects: {len(detections)}")
    for i, d in enumerate(detections, start=1):
        print(f"Plastic {i} -> {d.confidence * 100:.1f}%")

    out_image_path = RESULTS_DIR / f"detected_{image_path.stem}.jpg"
    cv2.imwrite(str(out_image_path), annotated)
    print(f"Saved annotated image to {out_image_path}")

    avg_conf = (sum(d.confidence for d in detections) / len(detections)) if detections else 0.0
    report = {
        "image_name": image_path.name,
        "detection_count": len(detections),
        "detections": detections_to_rows(detections),
        "average_confidence": round(avg_conf * 100, 2),
        "timestamp": timestamp_now(),
    }
    report_path = REPORTS_DIR / f"report_{image_path.stem}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Saved report to {report_path}")

    if args.save_history:
        add_record(image_path.name, len(detections), avg_conf, timestamp_now())
        print("Logged this run to detection history.")


if __name__ == "__main__":
    main()
