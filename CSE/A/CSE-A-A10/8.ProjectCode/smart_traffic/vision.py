"""Computer-vision layer: YOLOv8 vehicle detection, light-bar emergency detection,
traffic-density estimation and a synthetic scene generator (no dataset needed)."""
from __future__ import annotations

import os

import cv2
import numpy as np

COCO_VEHICLES = {2: "car", 3: "bike", 5: "bus", 7: "truck"}
PCU = {"car": 1.0, "bike": 0.5, "bus": 3.0, "truck": 2.0, "ambulance": 1.0}
BOX_COLORS = {"car": (80, 200, 120), "bike": (255, 180, 60), "bus": (255, 120, 60),
              "truck": (60, 160, 255), "ambulance": (60, 60, 255)}

_MODEL = {}


def yolo_available():
    try:
        import ultralytics  # noqa: F401
        return True
    except Exception:
        return False


def load_yolo(name="yolov8n.pt"):
    if name not in _MODEL:
        from ultralytics import YOLO
        _MODEL[name] = YOLO(name)
    return _MODEL[name]


def sample_image_path():
    try:
        from ultralytics.utils import ASSETS
        p = os.path.join(str(ASSETS), "bus.jpg")
        return p if os.path.exists(p) else None
    except Exception:
        return None


# ------------------------------------------------------------- light-bar detector
def lightbar_masks(bgr):
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    red = cv2.inRange(hsv, (0, 120, 190), (8, 255, 255)) | cv2.inRange(hsv, (172, 120, 190), (180, 255, 255))
    blue = cv2.inRange(hsv, (100, 120, 190), (130, 255, 255))
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    return cv2.morphologyEx(red, cv2.MORPH_OPEN, k), cv2.morphologyEx(blue, cv2.MORPH_OPEN, k)


def detect_lightbars(bgr, min_area=12):
    """Find red+blue emergency light-bar clusters. Returns list of (x, y, w, h, score)."""
    red, blue = lightbar_masks(bgr)
    h, w = red.shape
    dil = max(3, int(min(h, w) * 0.05))
    kern = np.ones((dil, dil), np.uint8)
    # a light bar = red and blue blobs touching after dilation
    both = cv2.dilate(red, kern) & cv2.dilate(blue, kern)
    n, _, stats, _ = cv2.connectedComponentsWithStats(both)
    out = []
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        rr = int(np.count_nonzero(red[y:y + bh, x:x + bw]))
        bb = int(np.count_nonzero(blue[y:y + bh, x:x + bw]))
        if rr >= min_area and bb >= min_area:
            score = min(1.0, 2 * min(rr, bb) / (rr + bb) * min(1.0, (rr + bb) / 120))
            out.append((int(x), int(y), int(bw), int(bh), float(score)))
    return out


def _lightbar_in_box(bars, box):
    x1, y1, x2, y2 = box
    bh = y2 - y1
    for bx, by, bw, bhh, sc in bars:
        cx, cy = bx + bw / 2, by + bhh / 2
        if x1 - 5 <= cx <= x2 + 5 and y1 - 0.3 * bh <= cy <= y1 + 0.6 * bh:
            return sc
    return 0.0


# ---------------------------------------------------------------------- detectors
def detect_yolo(bgr, conf=0.3, model="yolov8n.pt"):
    m = load_yolo(model)
    res = m.predict(bgr, conf=conf, verbose=False, classes=list(COCO_VEHICLES))[0]
    bars = detect_lightbars(bgr)
    dets = []
    for b in res.boxes:
        cls = COCO_VEHICLES[int(b.cls[0])]
        x1, y1, x2, y2 = [float(v) for v in b.xyxy[0]]
        sc = _lightbar_in_box(bars, (x1, y1, x2, y2))
        if sc > 0.25:
            cls = "ambulance"
        dets.append(dict(cls=cls, conf=float(b.conf[0]), box=(x1, y1, x2, y2), lightbar=sc))
    return dets, bars


def detect_classical(bgr, min_area=350):
    """Contour-based detector used for the synthetic overhead scenes."""
    bg = np.full(bgr.shape[:2], 0, np.uint8)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    road = (hsv[..., 1] < 40) & (hsv[..., 2] > 40) & (hsv[..., 2] < 110)
    white = ((hsv[..., 1] < 30) & (hsv[..., 2] > 200)).astype(np.uint8)
    thick = cv2.morphologyEx(white, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    lane = (white > 0) & (thick == 0)                   # thin lane paint only
    grass = (hsv[..., 0] > 35) & (hsv[..., 0] < 85) & (hsv[..., 1] > 50)
    fg = (~road & ~lane & ~grass).astype(np.uint8) * 255
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, _, stats, _ = cv2.connectedComponentsWithStats(fg | bg)
    bars = detect_lightbars(bgr, min_area=6)
    dets = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area < min_area or w > bgr.shape[1] * 0.9:
            continue
        box = (float(x), float(y), float(x + w), float(y + h))
        sc = _lightbar_in_box(bars, box)
        long_side = max(w, h)
        cls = "bike" if area < 900 else "car" if long_side < 95 else "truck" if long_side < 130 else "bus"
        if sc > 0.2:
            cls = "ambulance"
        dets.append(dict(cls=cls, conf=min(0.99, 0.72 + area / 9000), box=box, lightbar=sc))
    return dets, bars


# -------------------------------------------------------------- density estimator
def density_report(dets, road_capacity_pcu=14):
    counts = {k: 0 for k in PCU}
    for d in dets:
        counts[d["cls"]] += 1
    pcu = sum(PCU[k] * n for k, n in counts.items())
    ratio = pcu / road_capacity_pcu
    level = "LOW" if ratio < 0.35 else "MEDIUM" if ratio < 0.7 else "HIGH" if ratio < 1.0 else "JAMMED"
    emg = counts["ambulance"] > 0
    green = 12 if emg else int(min(60, max(15, 12 + 3.2 * pcu)))
    return dict(counts=counts, pcu=pcu, ratio=ratio, level=level, emergency=emg, green=green)


def annotate(bgr, dets, bars=(), show_bars=True):
    img = bgr.copy()
    for d in dets:
        x1, y1, x2, y2 = [int(v) for v in d["box"]]
        col = BOX_COLORS[d["cls"]]
        cv2.rectangle(img, (x1, y1), (x2, y2), col, 2)
        label = f"{d['cls']} {d['conf']:.2f}" + (" LIGHT-BAR" if d["lightbar"] > 0.25 else "")
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(img, (x1, max(0, y1 - th - 6)), (x1 + tw + 6, y1), col, -1)
        cv2.putText(img, label, (x1 + 3, max(th, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    if show_bars:
        for x, y, w, h, s in bars:
            cv2.ellipse(img, (x + w // 2, y + h // 2), (w + 8, h + 8), 0, 0, 360, (255, 0, 255), 2)
    return img


# ------------------------------------------------------------- synthetic scene
def render_scene(n_vehicles=8, emergency=True, phase=0, seed=0, size=(640, 420)):
    """Overhead 4-lane road with cars, trucks, bikes and (optionally) a flashing ambulance."""
    W, H = size
    rng = np.random.default_rng(seed)
    img = np.zeros((H, W, 3), np.uint8)
    img[:] = (70, 130, 60)                              # grass
    road_top, road_bot = int(H * 0.2), int(H * 0.8)
    img[road_top:road_bot] = (68, 68, 72)               # asphalt
    for x in range(0, W, 60):
        cv2.line(img, (x, H // 2), (x + 30, H // 2), (235, 235, 235), 3)
    cv2.line(img, (0, road_top + 4), (W, road_top + 4), (235, 235, 235), 3)
    cv2.line(img, (0, road_bot - 4), (W, road_bot - 4), (235, 235, 235), 3)
    lanes = [road_top + 0.13 * (road_bot - road_top), road_top + 0.37 * (road_bot - road_top),
             road_top + 0.63 * (road_bot - road_top), road_top + 0.87 * (road_bot - road_top)]
    palette = [(200, 60, 40), (40, 40, 200), (200, 200, 200), (30, 30, 30), (40, 170, 200), (90, 90, 230)]
    truth = []
    slots = [(li, xi) for li in range(4) for xi in range(5)]
    rng.shuffle(slots)
    n = min(n_vehicles, len(slots) - 1)
    amb_slot = slots.pop() if emergency else None
    for li, xi in slots[:n]:
        kind = rng.choice(["car", "car", "car", "truck", "bike", "bus"])
        w, h = {"car": (70, 34), "truck": (108, 40), "bike": (38, 18), "bus": (135, 42)}[kind]
        cx = int(60 + xi * (W - 120) / 4 + rng.integers(-14, 14))
        cy = int(lanes[li])
        x1, y1 = cx - w // 2, cy - h // 2
        col = palette[int(rng.integers(len(palette)))] if kind != "bus" else (40, 140, 240)
        cv2.rectangle(img, (x1, y1), (x1 + w, y1 + h), col, -1, cv2.LINE_AA)
        cv2.rectangle(img, (x1 + int(w * 0.62), y1 + 4), (x1 + int(w * 0.85), y1 + h - 4), (190, 170, 120), -1)
        truth.append((kind, (x1, y1, x1 + w, y1 + h)))
    if amb_slot:
        li, xi = amb_slot
        w, h = 92, 40
        cx, cy = int(60 + xi * (W - 120) / 4), int(lanes[li])
        x1, y1 = cx - w // 2, cy - h // 2
        cv2.rectangle(img, (x1, y1), (x1 + w, y1 + h), (245, 245, 245), -1, cv2.LINE_AA)
        cv2.rectangle(img, (x1 + int(w * 0.68), y1 + 4), (x1 + int(w * 0.88), y1 + h - 4), (190, 170, 120), -1)
        cv2.line(img, (x1 + 12, y1 + h // 2), (x1 + 34, y1 + h // 2), (40, 40, 220), 4)
        cv2.line(img, (x1 + 23, y1 + h // 2 - 11), (x1 + 23, y1 + h // 2 + 11), (40, 40, 220), 4)
        red_first = phase % 2 == 0                      # flashing alternates each frame
        cv2.circle(img, (x1 + 40, y1 + 8), 6, (0, 0, 255) if red_first else (255, 60, 0), -1)
        cv2.circle(img, (x1 + 54, y1 + 8), 6, (255, 60, 0) if red_first else (0, 0, 255), -1)
        cv2.circle(img, (x1 + 47, y1 + 8), 4, (0, 0, 255), -1)
        cv2.circle(img, (x1 + 47, y1 + 8), 2, (255, 60, 0), -1)
        truth.append(("ambulance", (x1, y1, x1 + w, y1 + h)))
    return img, truth
