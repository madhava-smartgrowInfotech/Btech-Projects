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
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        res = self.holistic.process(rgb)
        pose, lh, rh = _arr(res.pose_landmarks), _arr(res.left_hand_landmarks), _arr(res.right_hand_landmarks)
        if lh is None or rh is None:
            lh, rh = self._fill_hands(rgb, pose, lh, rh)
        return body_frame(pose, lh, rh, w / h), {"pose": pose, "left": lh, "right": rh, "aspect": w / h}

    def _fill_hands(self, rgb, pose, lh, rh):
        """Holistic finds hands through the pose; when it misses one, ask the stand-alone hand detector
        and give each found hand to the nearest pose wrist (15 = signer's left, 16 = right)."""
        if not hasattr(self, "hands"):
            self.hands = mp.solutions.hands.Hands(static_image_mode=False, max_num_hands=2,
                                                  min_detection_confidence=0.4, min_tracking_confidence=0.4)
        found = [_arr(x) for x in (self.hands.process(rgb).multi_hand_landmarks or [])]
        for hand in found:
            if pose is not None:
                d_left = np.linalg.norm(hand[0] - pose[15, :2])
                d_right = np.linalg.norm(hand[0] - pose[16, :2])
                is_left = d_left < d_right
            else:  # camera is not mirrored: the signer's left hand is on the image right
                is_left = hand[0, 0] > 0.5
            if is_left and lh is None:
                lh = hand
            elif not is_left and rh is None:
                rh = hand
        return lh, rh


class HandExtractor:
    """MediaPipe Hands for fingerspelling - works even when only the hands are in view."""

    def __init__(self):
        self.hands = mp.solutions.hands.Hands(static_image_mode=False, max_num_hands=2,
                                              min_detection_confidence=0.5, min_tracking_confidence=0.5)

    def frame(self, bgr):
        """BGR image -> list of (21,2) hands in normalised image coords."""
        res = self.hands.process(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        return [_arr(h) for h in (res.multi_hand_landmarks or [])][:2]
