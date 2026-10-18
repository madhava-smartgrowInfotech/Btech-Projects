"""Runs sign_language_app.train.train_model on a background thread and exposes its progress.

Mirrors what gui/train_tab.py does with its queue, but keeps the state in a lock-guarded dict
that the API polls.
"""

from __future__ import annotations

import json
import threading
import time
from typing import Callable, Optional

from sign_language_app import config

CONFUSION_PATH = config.MODELS_DIR / "confusion_matrix.json"


class TrainJob:
    def __init__(self, on_finished: Optional[Callable[[], object]] = None):
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._on_finished = on_finished
        self._state = self._fresh()

    @staticmethod
    def _fresh() -> dict:
        return {
            "state": "idle",            # idle | loading | training | done | error
            "data": {"done": 0, "total": 0},
            "epoch": 0,
            "epochs": 0,
            "history": {"accuracy": [], "val_accuracy": [], "loss": [], "val_loss": []},
            "summary": None,
            "error": None,
            "stopping": False,
            "started_at": None,
            "finished_at": None,
        }

    def snapshot(self) -> dict:
        with self._lock:
            return json.loads(json.dumps(self._state))

    def start(self, epochs: int, batch_size: int, learning_rate: float) -> bool:
        with self._lock:
            if self._state["state"] in ("loading", "training"):
                return False
            self._state = self._fresh()
            self._state.update(state="loading", epochs=epochs, started_at=time.time())
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, args=(epochs, batch_size, learning_rate), daemon=True
        )
        self._thread.start()
        return True

    def request_stop(self) -> None:
        with self._lock:
            if self._state["state"] in ("loading", "training"):
                self._state["stopping"] = True
        self._stop.set()

    def _run(self, epochs: int, batch_size: int, learning_rate: float) -> None:
        try:
            from sign_language_app.train import train_model   # imports TensorFlow

            def data_cb(done, total):
                with self._lock:
                    self._state["data"] = {"done": done, "total": total}

            def epoch_cb(epoch, total, logs):
                with self._lock:
                    s = self._state
                    s["state"] = "training"
                    s["epoch"], s["epochs"] = epoch, total
                    for key in s["history"]:
                        if key in logs:
                            s["history"][key].append(float(logs[key]))

            summary = train_model(
                epochs=epochs,
                batch_size=batch_size,
                learning_rate=learning_rate,
                data_progress_cb=data_cb,
                epoch_cb=epoch_cb,
                stop_flag=self._stop.is_set,
            )
            CONFUSION_PATH.write_text(
                json.dumps({"labels": summary["labels"], "matrix": summary["confusion_matrix"]}),
                encoding="utf-8",
            )
            if self._on_finished:           # load the new model before announcing "done"
                self._on_finished()
            with self._lock:
                self._state.update(
                    state="done",
                    finished_at=time.time(),
                    summary={
                        "labels": summary["labels"],
                        "test_accuracy": summary["test_accuracy"],
                        "test_loss": summary["test_loss"],
                    },
                )
        except Exception as exc:   # surfaced to the UI like the desktop "Error: ..." label
            with self._lock:
                self._state.update(state="error", error=str(exc) or exc.__class__.__name__, finished_at=time.time())
