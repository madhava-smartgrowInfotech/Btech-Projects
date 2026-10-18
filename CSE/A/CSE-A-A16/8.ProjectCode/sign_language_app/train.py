"""Training pipeline. Runnable standalone (`python -m sign_language_app.train`)
or invoked programmatically by the GUI's Train tab (which passes callbacks
to stream progress into the UI on a background thread).
"""

from __future__ import annotations

import json

import numpy as np
from tensorflow.keras.callbacks import Callback, EarlyStopping, ModelCheckpoint
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.metrics import classification_report, confusion_matrix

from . import config
from .dataset import Dataset, load_dataset, save_labels
from .model import build_cnn


class StreamingCallback(Callback):
    """Forwards per-epoch metrics to a GUI-supplied callback and lets the
    caller request an early stop (e.g. user clicked 'Stop')."""

    def __init__(self, epoch_cb=None, stop_flag=None):
        super().__init__()
        self.epoch_cb = epoch_cb
        self.stop_flag = stop_flag  # callable returning True to request stop

    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        if self.epoch_cb:
            self.epoch_cb(epoch + 1, self.params.get("epochs", 0), dict(logs))
        if self.stop_flag and self.stop_flag():
            self.model.stop_training = True


def train_model(
    epochs: int = config.DEFAULT_EPOCHS,
    batch_size: int = config.DEFAULT_BATCH_SIZE,
    learning_rate: float = config.DEFAULT_LEARNING_RATE,
    data_progress_cb=None,
    epoch_cb=None,
    stop_flag=None,
):
    """Loads data, trains the CNN, evaluates it, and persists artifacts.

    Returns a dict summary (final metrics + history) for the caller to
    display.
    """
    dataset: Dataset = load_dataset(progress_cb=data_progress_cb)
    save_labels(dataset.labels)

    model = build_cnn(num_classes=len(dataset.labels), learning_rate=learning_rate)

    augmenter = ImageDataGenerator(
        rotation_range=12,
        width_shift_range=0.1,
        height_shift_range=0.1,
        zoom_range=0.12,
        shear_range=0.08,
        fill_mode="nearest",
    )
    train_flow = augmenter.flow(
        dataset.x_train, dataset.y_train, batch_size=batch_size, seed=config.RANDOM_SEED
    )

    callbacks = [
        StreamingCallback(epoch_cb=epoch_cb, stop_flag=stop_flag),
        EarlyStopping(monitor="val_accuracy", patience=6, restore_best_weights=True),
        ModelCheckpoint(
            str(config.MODEL_PATH), monitor="val_accuracy", save_best_only=True
        ),
    ]

    history = model.fit(
        train_flow,
        steps_per_epoch=max(1, len(dataset.x_train) // batch_size),
        epochs=epochs,
        validation_data=(dataset.x_val, dataset.y_val),
        callbacks=callbacks,
        verbose=0,
    )

    model.save(config.MODEL_PATH)

    test_loss, test_acc = model.evaluate(dataset.x_test, dataset.y_test, verbose=0)

    y_pred = np.argmax(model.predict(dataset.x_test, verbose=0), axis=1)
    y_true = np.argmax(dataset.y_test, axis=1)
    report = classification_report(
        y_true, y_pred, target_names=dataset.labels, zero_division=0
    )
    cm = confusion_matrix(y_true, y_pred)

    with open(config.REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(f"Test accuracy: {test_acc:.4f}\nTest loss: {test_loss:.4f}\n\n")
        f.write(report)

    hist_dict = {k: [float(v) for v in vals] for k, vals in history.history.items()}
    with open(config.HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(hist_dict, f, indent=2)

    return {
        "labels": dataset.labels,
        "test_accuracy": float(test_acc),
        "test_loss": float(test_loss),
        "history": hist_dict,
        "confusion_matrix": cm.tolist(),
        "report": report,
    }


if __name__ == "__main__":
    summary = train_model(
        epoch_cb=lambda e, total, logs: print(
            f"epoch {e}/{total} - " + " ".join(f"{k}={v:.4f}" for k, v in logs.items())
        ),
        data_progress_cb=lambda done, total: print(f"\rloading data {done}/{total}", end=""),
    )
    print("\nTest accuracy:", summary["test_accuracy"])
    print(summary["report"])
