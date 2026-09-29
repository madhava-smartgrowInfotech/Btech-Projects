"""Activity recognition over a sliding window of keypoints (scikit-learn classifier)."""
from collections import deque

import joblib
import numpy as np

from ..config import ACTIVITY_MODEL
from .features import WINDOW, window_features

_bundle = None


def load_bundle():
    global _bundle
    if _bundle is None:
        if not ACTIVITY_MODEL.exists():
            raise RuntimeError("Activity model missing - run: python ml/train.py")
        _bundle = joblib.load(ACTIVITY_MODEL)
        _bundle["model"].n_jobs = 1  # one window at a time: thread start-up would cost more than the trees
    return _bundle


class ActivityRecognizer:
    def __init__(self):
        b = load_bundle()
        self.model = b["model"]
        self.classes = list(b["classes"])
        self.window = deque(maxlen=WINDOW)
        self.smooth = None
        self.last_seen = None

    def update(self, t, k):
        """Returns (label, confidence, {class: prob}). label is 'no_person' when nobody is visible."""
        self.window.append((t, k))
        if k is not None:
            self.last_seen = t
        if self.last_seen is None or t - self.last_seen > 1.5:
            self.smooth = None
            return "no_person", 1.0, {}
        if len(self.window) < WINDOW // 2:
            return "detecting", 0.0, {}
        f = window_features(list(self.window))
        if f is None:
            return "detecting", 0.0, {}
        p = self.model.predict_proba(f[None])[0]
        self.smooth = p if self.smooth is None else 0.6 * self.smooth + 0.4 * p
        i = int(np.argmax(self.smooth))
        probs = {c: round(float(v), 3) for c, v in zip(self.classes, self.smooth)}
        return self.classes[i], float(self.smooth[i]), probs
