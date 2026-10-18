"""Unit tests for the temporal smoothing / auto-commit logic of SignRecognizer (stub model, no TensorFlow weights)."""

import numpy as np

from sign_language_app import config
from sign_language_app.recognizer import SignRecognizer

LABELS = ["A", "B", "space", "del", "nothing"]


class StubModel:
    """Returns a fixed probability vector; set .probs between calls."""

    def __init__(self):
        self.probs = np.array([0.0] * len(LABELS))

    def predict(self, batch, verbose=0):
        return np.array([self.probs])


def make(label, confidence):
    p = np.full(len(LABELS), (1 - confidence) / (len(LABELS) - 1))
    p[LABELS.index(label)] = confidence
    return p


def recognizer():
    rec = SignRecognizer()
    rec.model, rec.labels = StubModel(), LABELS
    return rec


ROI = np.zeros((300, 300, 3), np.uint8)


def feed(rec, label, confidence, frames):
    rec.model.probs = make(label, confidence)
    return [rec.predict_frame(ROI) for _ in range(frames)]


def test_not_loaded_returns_none():
    assert SignRecognizer().predict_frame(ROI) is None


def test_commits_after_stable_frames_exactly_once():
    rec = recognizer()
    results = feed(rec, "A", 0.95, config.STABLE_FRAMES_TO_COMMIT + 10)
    committed = [r["committed"] for r in results if r["committed"]]
    assert committed == ["A"]
    first = next(i for i, r in enumerate(results) if r["committed"])
    assert first == config.STABLE_FRAMES_TO_COMMIT - 1


def test_no_commit_before_threshold_frames():
    rec = recognizer()
    results = feed(rec, "B", 0.95, config.STABLE_FRAMES_TO_COMMIT - 1)
    assert all(r["committed"] is None for r in results)


def test_low_confidence_is_treated_as_nothing():
    rec = recognizer()
    results = feed(rec, "A", config.CONFIDENCE_THRESHOLD - 0.1, 40)
    assert all(r["committed"] is None for r in results)
    assert results[-1]["stable_label"] == "nothing"


def test_same_letter_needs_a_pause_to_repeat():
    rec = recognizer()
    feed(rec, "A", 0.95, 40)
    assert [r["committed"] for r in feed(rec, "A", 0.95, 40) if r["committed"]] == []
    feed(rec, "nothing", 0.99, config.PREDICTION_HISTORY_LEN + 2)
    again = [r["committed"] for r in feed(rec, "A", 0.95, 40) if r["committed"]]
    assert again == ["A"]


def test_control_labels_are_committed():
    rec = recognizer()
    assert "space" in [r["committed"] for r in feed(rec, "space", 0.95, 30)]


def test_single_noisy_frame_does_not_change_stable_label():
    rec = recognizer()
    feed(rec, "A", 0.95, 12)
    feed(rec, "B", 0.95, 1)
    result = feed(rec, "A", 0.95, 1)[0]
    assert result["stable_label"] == "A"
