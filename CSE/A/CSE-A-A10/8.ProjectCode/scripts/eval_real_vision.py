"""Evaluate the shipped vision layer (YOLOv8n + HSV light-bar rule) on two public real-image sets.

Needs data/external (python scripts/fetch_real_images.py).  Writes experiments/vision_real/metrics.json.
No threshold is tuned on these images: the app's own defaults (conf 0.3) are used.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

try:
    import torch  # noqa: F401
except Exception:
    pass

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from smart_traffic import vision as V  # noqa: E402

EXT = ROOT / "data" / "external"
CLS = {1: "2-wheeler", 2: "3-wheeler", 3: "4-wheeler"}
PRED_MAP = {"bike": 1, "car": 3, "bus": 3, "truck": 3, "ambulance": 3}


def iou(a, b):
    ix, iy = max(0, min(a[2], b[2]) - max(a[0], b[0])), max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def mixed_traffic(conf=0.3):
    imgs = sorted((EXT / "mixed_traffic" / "images").rglob("*.jpg"))
    stats = {k: dict(tp=0, fp=0, fn=0) for k in (1, 2, 3, "any")}
    count_err, lat, n_gt_tot, n_pred_tot = [], [], 0, 0
    for p in imgs:
        img = cv2.imread(str(p))
        h, w = img.shape[:2]
        lab = EXT / "mixed_traffic" / "labels" / p.parent.name / (p.stem + ".txt")
        gts = []
        for ln in lab.read_text().splitlines() if lab.exists() else []:
            c, x, y, bw, bh = ln.split()
            c = int(c)
            if c == 0:
                continue
            x, y, bw, bh = float(x) * w, float(y) * h, float(bw) * w, float(bh) * h
            gts.append((c, (x - bw / 2, y - bh / 2, x + bw / 2, y + bh / 2)))
        t = time.perf_counter()
        dets, _ = V.detect_yolo(img, conf)
        lat.append((time.perf_counter() - t) * 1000)
        preds = sorted(((PRED_MAP[d["cls"]], d["box"], d["conf"]) for d in dets), key=lambda x: -x[2])
        n_gt_tot += len(gts)
        n_pred_tot += len(preds)
        count_err.append(abs(len(preds) - len(gts)))
        for mode in (1, 2, 3, "any"):
            g = [(c, b) for c, b in gts if mode == "any" or c == mode]
            pr = [(c, b) for c, b, _ in preds if mode == "any" or c == mode]
            used = set()
            tp = 0
            for pc, pb in pr:
                best, bi = 0.0, -1
                for i, (gc, gb) in enumerate(g):
                    if i in used:
                        continue
                    o = iou(pb, gb)
                    if o > best:
                        best, bi = o, i
                if best >= 0.5:
                    used.add(bi)
                    tp += 1
            stats[mode]["tp"] += tp
            stats[mode]["fp"] += len(pr) - tp
            stats[mode]["fn"] += len(g) - tp
    out = {}
    for k, s in stats.items():
        p = s["tp"] / max(s["tp"] + s["fp"], 1)
        r = s["tp"] / max(s["tp"] + s["fn"], 1)
        out[CLS.get(k, "any vehicle class")] = dict(**s, precision=p, recall=r, f1=2 * p * r / max(p + r, 1e-9),
                                                    n_gt=s["tp"] + s["fn"])
    return dict(images=len(imgs), gt_boxes_excluding_pedestrians=n_gt_tot, predicted_boxes=n_pred_tot, conf=conf, iou_match=0.5,
                per_class=out, count_mae_per_image=float(np.mean(count_err)),
                latency_ms_mean=float(np.mean(lat[1:])), latency_ms_median=float(np.median(lat[1:])))


def ambulance(conf=0.3):
    rows = []
    for label, folder in ((1, "ambulance"), (0, "noambulance")):
        for p in sorted((EXT / "ambulance_cls" / folder).iterdir()):
            img = cv2.imread(str(p))
            if img is None:
                continue
            dets, bars = V.detect_yolo(img, conf)
            rows.append(dict(y=label, lightbar=len(bars) > 0, amb=any(d["cls"] == "ambulance" for d in dets),
                             n_veh=len(dets)))

    def metrics(key):
        tp = sum(r["y"] and r[key] for r in rows)
        fp = sum((not r["y"]) and r[key] for r in rows)
        fn = sum(r["y"] and not r[key] for r in rows)
        tn = sum((not r["y"]) and not r[key] for r in rows)
        p, rc = tp / max(tp + fp, 1), tp / max(tp + fn, 1)
        return dict(tp=int(tp), fp=int(fp), fn=int(fn), tn=int(tn), precision=p, recall=rc,
                    f1=2 * p * rc / max(p + rc, 1e-9), accuracy=(tp + tn) / len(rows),
                    false_alarm_rate=fp / max(fp + tn, 1))
    pos = [r for r in rows if r["y"]]
    return dict(images=len(rows), ambulance_images=len(pos), no_ambulance_images=len(rows) - len(pos), conf=conf,
                note="first 300 files (by name) of each folder; positives include photos where the lights are off or not visible",
                lightbar_cluster_any=metrics("lightbar"), ambulance_flag_yolo_plus_lightbar=metrics("amb"),
                yolo_found_any_vehicle_in_ambulance_images=float(np.mean([r["n_veh"] > 0 for r in pos])))


if __name__ == "__main__":
    out = dict(model="yolov8n.pt (COCO, not fine-tuned)", mixed_traffic=mixed_traffic(), ambulance_classification=ambulance())
    d = ROOT / "experiments" / "vision_real"
    d.mkdir(parents=True, exist_ok=True)
    (d / "metrics.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=1))
