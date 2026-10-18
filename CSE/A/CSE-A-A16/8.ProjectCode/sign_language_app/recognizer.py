"""Real-time inference wrapper: loads the trained CNN and turns a stream of
preprocessed ROI frames into a stable, debounced letter prediction.
"""

from __future__ import annotations

from collections import Counter, deque

import numpy as np

from . import config
from .dataset import load_labels
from .preprocessing import preprocess_roi


class SignRecognizer:
    def __init__(self):
        self.model = None
        self.labels: list[str] = []
        self._history: deque[str] = deque(maxlen=config.PREDICTION_HISTORY_LEN)
        self._stable_label = None
        self._stable_count = 0
        self._last_committed = None

    @property
    def is_loaded(self) -> bool:
        return self.model is not None

    def load(self) -> bool:
        if not config.MODEL_PATH.exists():
            return False
        from tensorflow.keras.models import load_model  # local import: slow to import

        self.model = load_model(config.MODEL_PATH)
        self.labels = load_labels()
        self._history.clear()
        self._stable_label = None
        self._stable_count = 0
        return True

    def predict_frame(self, roi_bgr: np.ndarray):
        """Run one frame through the pipeline.

        Returns a dict: {label, confidence, mask, committed}
        `committed` is the letter to append to the output sentence, or None
        if the current prediction hasn't been held stably for long enough.
        """
        if not self.is_loaded:
            return None

        model_input, mask = preprocess_roi(roi_bgr)
        batch = np.expand_dims(model_input, axis=0)
        probs = self.model.predict(batch, verbose=0)[0]
        top_idx = int(np.argmax(probs))
        confidence = float(probs[top_idx])
        label = self.labels[top_idx] if top_idx < len(self.labels) else "?"

        accepted = label if confidence >= config.CONFIDENCE_THRESHOLD else "nothing"
        self._history.append(accepted)
        majority_label, _ = Counter(self._history).most_common(1)[0]

        if majority_label == self._stable_label:
            self._stable_count += 1
        else:
            self._stable_label = majority_label
            self._stable_count = 1

        committed = None
        if (
            self._stable_count >= config.STABLE_FRAMES_TO_COMMIT
            and majority_label not in ("nothing",)
            and majority_label != self._last_committed
        ):
            committed = majority_label
            self._last_committed = majority_label
            self._stable_count = 0
        elif majority_label == "nothing":
            self._last_committed = None

        return {
            "label": label,
            "confidence": confidence,
            "mask": mask,
            "stable_label": majority_label,
            "committed": committed,
        }
