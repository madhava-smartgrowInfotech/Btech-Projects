"""Live sign recognition: frames -> landmarks -> ONNX models -> sign events.

Words: frames with a visible hand are collected into a segment. When the hands drop (or the
segment gets long) the segment is resampled to 32 frames and classified. While a segment is
open, the same model runs on the frames so far to give a live top-3 guess.

Letters: every frame with a hand is classified; a letter is accepted once it wins most of the
last few frames. Letters build up a fingerspelled word that is emitted when the hands drop.
"""
import json
import threading
import time
from collections import deque

import cv2
import numpy as np
import onnxruntime as ort

from ml.features import has_hand, letter_features, resample_sequence, word_features
from ml.vocab import WORD_TEXT

from ..config import MODELS_DIR
from .landmarks import Extractor, HandExtractor

WORD_MIN_CONF = 0.40
HANDS_DOWN_S = 0.45  # a pause this long closes a word segment
MAX_SEGMENT_S = 3.5
MIN_SEGMENT_FRAMES = 5
LETTER_WINDOW, LETTER_VOTES, LETTER_MIN_CONF = 7, 5, 0.6
SPELL_END_S = 1.2


def softmax(z):
    z = z - z.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


class Models:
    def __init__(self):
        labels = json.loads((MODELS_DIR / "labels.json").read_text())
        self.words, self.letters = labels["words"], labels["letters"]
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 2
        self.word = ort.InferenceSession(str(MODELS_DIR / "word_model.onnx"), opts, providers=["CPUExecutionProvider"])
        self.letter = ort.InferenceSession(str(MODELS_DIR / "letter_model.onnx"), opts, providers=["CPUExecutionProvider"])

    def word_probs(self, frames):
        x = word_features(resample_sequence(frames))[None]
        return softmax(self.word.run(None, {"x": x})[0][0])

    def letter_probs(self, hands):
        x = letter_features(hands)[None]
        return softmax(self.letter.run(None, {"x": x})[0][0])

    def top(self, probs, labels, k=3):
        idx = np.argsort(probs)[::-1][:k]
        return [{"label": labels[i], "confidence": round(float(probs[i]), 3)} for i in idx]


class SessionState:
    def __init__(self):
        self.segment, self.seg_start, self.last_hand = [], None, 0.0
        self.votes = deque(maxlen=LETTER_WINDOW)
        self.spelling, self.last_letter, self.letter_released = "", None, True
        self.frame_times = deque(maxlen=30)
        self.touched = time.time()


class Recognizer:
    def __init__(self):
        self.models = Models()
        self.extractor = Extractor()
        self.hand_extractor = HandExtractor()
        self.sessions: dict[str, SessionState] = {}
        self.lock = threading.Lock()
        self.recent_latency = deque(maxlen=300)  # server-side ms per frame

    def reset(self, sid):
        with self.lock:
            self.sessions.pop(sid, None)

    def _state(self, sid):
        now = time.time()
        for k in [k for k, s in self.sessions.items() if now - s.touched > 600]:
            del self.sessions[k]
        st = self.sessions.setdefault(sid, SessionState())
        st.touched = now
        return st

    def process(self, jpeg: bytes, sid: str, mode: str = "words"):
        t0 = time.perf_counter()
        img = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode the camera frame")
        with self.lock:
            if mode == "letters":
                hands = self.hand_extractor.frame(img)
                raw = {"left": hands[0] if hands else None, "right": hands[1] if len(hands) > 1 else None,
                       "hands": hands, "aspect": img.shape[1] / img.shape[0]}
                frame = None
            else:
                frame, raw = self.extractor.frame(img)
            t1 = time.perf_counter()
            st = self._state(sid)
            now = time.time()
            st.frame_times.append(now)
            events, live = (self._letters if mode == "letters" else self._words)(st, frame, raw, now)
            t2 = time.perf_counter()
        ms = {"landmarks": round((t1 - t0) * 1000, 1), "model": round((t2 - t1) * 1000, 1),
              "total": round((t2 - t0) * 1000, 1)}
        self.recent_latency.append(ms["total"])
        ft = st.frame_times
        fps = (len(ft) - 1) / (ft[-1] - ft[0]) if len(ft) > 1 and ft[-1] > ft[0] else 0.0
        return {
            "hands": bool(raw.get("hands")) if frame is None else bool(has_hand(frame)),
            "landmarks": {k: (None if raw[k] is None else raw[k].round(4).tolist()) for k in ("left", "right")},
            "events": events,
            "live": live,
            "spelling": st.spelling,
            "latency_ms": ms,
            "fps": round(fps, 1),
        }

    # ------------------------------------------------------------ words
    def _classify_segment(self, st, frames, reason):
        probs = self.models.word_probs(frames)
        top = self.models.top(probs, self.models.words)
        if top[0]["confidence"] < WORD_MIN_CONF:
            return [{"type": "rejected", "reason": reason, "top": top}]
        g = top[0]["label"]
        return [{"type": "sign", "gloss": g, "text": WORD_TEXT.get(g, g.lower()),
                 "confidence": top[0]["confidence"], "top": top, "frames": len(frames)}]

    def _words(self, st, frame, raw, now):
        events, live = [], None
        if has_hand(frame):
            if not st.segment:
                st.seg_start = now
            st.segment.append(frame)
            st.last_hand = now
            if len(st.segment) >= MIN_SEGMENT_FRAMES:
                live = self.models.top(self.models.word_probs(st.segment), self.models.words)
            if now - st.seg_start > MAX_SEGMENT_S:
                events = self._classify_segment(st, st.segment, "long")
                st.segment = []
        elif st.segment:
            st.segment.append(frame)
            if now - st.last_hand > HANDS_DOWN_S:
                if sum(has_hand(f) for f in st.segment) >= MIN_SEGMENT_FRAMES:
                    events = self._classify_segment(st, st.segment, "hands_down")
                st.segment = []
        return events, live

    # ------------------------------------------------------------ letters
    def _letters(self, st, frame, raw, now):
        events, live = [], None
        hands = [h * np.array([raw["aspect"], 1.0], np.float32) for h in raw["hands"]]
        if hands:
            st.last_hand = now
            probs = self.models.letter_probs(hands)
            live = self.models.top(probs, self.models.letters)
            st.votes.append((live[0]["label"], live[0]["confidence"]))
            labels = [v[0] for v in st.votes]
            best = max(set(labels), key=labels.count)
            confs = [c for l, c in st.votes if l == best]
            if labels.count(best) >= LETTER_VOTES and np.mean(confs) >= LETTER_MIN_CONF:
                if best != st.last_letter or st.letter_released:
                    st.spelling += best
                    st.last_letter, st.letter_released = best, False
                    st.votes.clear()
                    events.append({"type": "letter", "letter": best, "confidence": round(float(np.mean(confs)), 3),
                                   "spelling": st.spelling})
        else:
            st.votes.clear()
            st.letter_released = True
            if st.spelling and now - st.last_hand > SPELL_END_S:
                word = st.spelling
                st.spelling, st.last_letter = "", None
                events.append({"type": "sign", "gloss": word, "text": word.capitalize() if word.isalpha() else word,
                               "confidence": 1.0, "fingerspelled": True})
        return events, live

    def word_latency_benchmark(self, n=50):
        frames = [np.zeros((49, 2), np.float32)] * 32
        t = time.perf_counter()
        for _ in range(n):
            self.models.word_probs(frames)
        return (time.perf_counter() - t) / n * 1000
