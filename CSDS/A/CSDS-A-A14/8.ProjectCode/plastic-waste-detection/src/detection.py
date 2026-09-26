"""
detection.py
------------
Runs YOLO inference on a single image and returns both a
human-readable list of detections and an annotated image with
bounding boxes, class labels and confidence scores drawn on it.
"""

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class Detection:
    class_name: str
    confidence: float
    x1: int
    y1: int
    x2: int
    y2: int


def run_detection(model, image_bgr: np.ndarray, conf_threshold: float = 0.5):
    """
    Run the YOLO model on a single BGR image (numpy array).

    Returns:
        annotated_image (np.ndarray): BGR image with boxes drawn
        detections (list[Detection]): structured detection results
    """
    results = model.predict(source=image_bgr, conf=conf_threshold, verbose=False)
    result = results[0]

    detections = []
    annotated = image_bgr.copy()

    names = result.names if hasattr(result, "names") else model.names

    if result.boxes is not None and len(result.boxes) > 0:
        for box in result.boxes:
            xyxy = box.xyxy[0].cpu().numpy().astype(int)
            x1, y1, x2, y2 = xyxy.tolist()
            conf = float(box.conf[0].cpu().numpy())
            cls_id = int(box.cls[0].cpu().numpy())
            class_name = names.get(cls_id, str(cls_id)) if isinstance(names, dict) else str(names[cls_id])

            detections.append(Detection(class_name, conf, x1, y1, x2, y2))

            # Draw bounding box
            color = (0, 255, 0)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

            # Draw label with confidence
            label = f"{class_name} {conf * 100:.1f}%"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, max(0, y1 - th - 8)),
                          (x1 + tw + 4, y1), color, -1)
            cv2.putText(annotated, label, (x1 + 2, max(12, y1 - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

    # Sort by confidence descending so the UI can show the most
    # confident detections first.
    detections.sort(key=lambda d: d.confidence, reverse=True)

    return annotated, detections


def detections_to_rows(detections: list[Detection]) -> list[dict]:
    """Convert Detection objects into plain dicts for a results table."""
    rows = []
    for i, d in enumerate(detections, start=1):
        rows.append({
            "Object": i,
            "Class": d.class_name,
            "Confidence": f"{d.confidence * 100:.1f}%",
            "BBox (x1,y1,x2,y2)": f"({d.x1}, {d.y1}, {d.x2}, {d.y2})",
        })
    return rows
