"""MediaPipe Holistic landmark extraction (CPU, offline)."""
import threading

import cv2
import mediapipe as mp
import numpy as np

from ml.features import body_frame


def _arr(lms):
    return None if lms is None else np.array([[p.x, p.y] for p in lms.landmark], np.float32)


class Extractor:
    """Wraps one Holistic tracker. Not thread-safe on its own - callers hold `lock`."""

    def __init__(self):
        self.lock = threading.Lock()
        self._new()

    def _new(self):
        self.holistic = mp.solutions.holistic.Holistic(
            static_image_mode=False, model_complexity=1, smooth_landmarks=True,
            min_detection_confidence=0.5, min_tracking_confidence=0.5,
        )

    def reset(self):
        self.holistic.close()
        self._new()

    def frame(self, bgr):
        """BGR image -> (body-coordinate frame (49,2), raw dict for drawing / letters)."""
        h, w = bgr.shape[:2]
        res = self.holistic.process(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        pose, lh, rh = _arr(res.pose_landmarks), _arr(res.left_hand_landmarks), _arr(res.right_hand_landmarks)
        return body_frame(pose, lh, rh, w / h), {"pose": pose, "left": lh, "right": rh, "aspect": w / h}


class HandExtractor:
    """MediaPipe Hands for fingerspelling - works even when only the hands are in view."""

    def __init__(self):
        self.hands = mp.solutions.hands.Hands(static_image_mode=False, max_num_hands=2,
                                              min_detection_confidence=0.5, min_tracking_confidence=0.5)

    def frame(self, bgr):
        """BGR image -> list of (21,2) hands in normalised image coords."""
        res = self.hands.process(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        return [_arr(h) for h in (res.multi_hand_landmarks or [])][:2]
