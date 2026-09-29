"""Low-light enhancement + pretrained YOLO11n-pose keypoint extraction."""
import threading

import cv2
import numpy as np

from ..config import POSE_MODEL

DARK_THRESHOLD = 80  # mean grey level below which a frame counts as dim


def brightness(frame):
    return float(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).mean())


def enhance(frame, gamma=0.5):
    """Gamma lift followed by CLAHE on the L channel."""
    lut = np.array([((i / 255.0) ** gamma) * 255 for i in range(256)], dtype=np.uint8)
    out = cv2.LUT(frame, lut)
    lab = cv2.cvtColor(out, cv2.COLOR_BGR2LAB)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def maybe_enhance(frame, mode="auto"):
    b = brightness(frame)
    if mode == "on" or (mode == "auto" and b < DARK_THRESHOLD):
        return enhance(frame), True, b
    return frame, False, b


def darken(frame, factor=0.25, gamma=1.8, noise=6.0, rng=None):
    """Simulate a dim room: lower exposure, crush shadows, add sensor noise."""
    rng = rng or np.random.default_rng(0)
    f = (frame.astype(np.float32) / 255.0) ** gamma * factor * 255.0
    f += rng.normal(0, noise, f.shape)
    return np.clip(f, 0, 255).astype(np.uint8)


class PoseEstimator:
    def __init__(self, imgsz=480):
        from ultralytics import YOLO

        self.model = YOLO(str(POSE_MODEL))
        self.imgsz = imgsz
        self.lock = threading.Lock()

    def detect(self, frame, conf=0.25):
        """List of people: dict(kpts=[17,3] px, box=[x1,y1,x2,y2], conf)."""
        with self.lock:
            r = self.model.predict(frame, imgsz=self.imgsz, conf=conf, verbose=False, device="cpu")[0]
        people = []
        if r.keypoints is None or r.boxes is None or len(r.boxes) == 0:
            return people
        kx = r.keypoints.data.cpu().numpy()  # [n,17,3]
        boxes = r.boxes.xyxy.cpu().numpy()
        confs = r.boxes.conf.cpu().numpy()
        for i in range(len(boxes)):
            people.append({"kpts": kx[i].astype(np.float32), "box": boxes[i], "conf": float(confs[i])})
        return people

    @staticmethod
    def main_person(people):
        if not people:
            return None
        return max(people, key=lambda p: (p["box"][2] - p["box"][0]) * (p["box"][3] - p["box"][1]))


_estimator = None
_elock = threading.Lock()


def get_estimator():
    global _estimator
    with _elock:
        if _estimator is None:
            _estimator = PoseEstimator()
        return _estimator
