"""Measure SignSpeak's real numbers and write docs/metrics/metrics.json (used by the report documents).

What it measures, all from this project's own artefacts (nothing is typed in by hand):
  * model size / parameters (models/asl_cnn_model.keras)
  * the held-out 15% test split, rebuilt with the same seed as training (data/ -> dataset.load_dataset)
  * a larger check on archive photos that were NOT copied into data/ (never seen in training/validation/test)
  * the 28 official Kaggle test photos
  * accuracy against confidence threshold, and robustness to brightness / noise / blur
  * latency of each pipeline stage and of the HTTP round trip (a throw-away uvicorn on port 8398)
  * seconds per training epoch (a 2-epoch run into a temp folder; models/ is not touched)

Run with the project venv (TensorFlow 2.15):   .venv\\Scripts\\python scripts\\measure_metrics.py
"""

from __future__ import annotations

import tensorflow as tf  # noqa: F401  (must be imported before scikit-learn on Windows)

import json
import platform
import random
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import cv2
import httpx
import numpy as np
from sklearn.metrics import accuracy_score, f1_score

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sign_language_app import config, dataset                     # noqa: E402
from sign_language_app.preprocessing import (                      # noqa: E402
    crop_roi, get_roi_box, normalize_for_model, segment_hand,
)

ARCHIVE = ROOT / "archive" / "asl_alphabet_train" / "asl_alphabet_train"
ARCHIVE_TEST = ROOT / "archive" / "asl_alphabet_test" / "asl_alphabet_test"
OUT = ROOT / "docs" / "metrics" / "metrics.json"
PER_CLASS_UNSEEN = 100
PERTURB_PER_CLASS = 20
rng = random.Random(7)


def stats(ms: list[float]) -> dict:
    ms = sorted(ms)
    return {
        "median_ms": round(statistics.median(ms), 3),
        "mean_ms": round(statistics.fmean(ms), 3),
        "p95_ms": round(ms[int(0.95 * (len(ms) - 1))], 3),
        "n": len(ms),
    }


def predict_raw(model, labels, raws: list[np.ndarray]) -> np.ndarray:
    x = np.stack([normalize_for_model(segment_hand(r)) for r in raws])
    return model.predict(x, verbose=0, batch_size=128)


def metrics_of(y_true, probs, labels) -> dict:
    y_pred = probs.argmax(1)
    top3 = float(np.mean([t in np.argsort(p)[-3:] for t, p in zip(y_true, probs)]))
    return {
        "n": int(len(y_true)),
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "macro_f1": round(float(f1_score(y_true, y_pred, average="macro")), 4),
        "weighted_f1": round(float(f1_score(y_true, y_pred, average="weighted")), 4),
        "top3_accuracy": round(top3, 4),
    }


def main() -> None:
    result: dict = {"generated": time.strftime("%Y-%m-%d %H:%M:%S")}
    labels = dataset.load_labels()
    from tensorflow.keras.models import load_model
    model = load_model(config.MODEL_PATH)

    result["environment"] = {
        "os": platform.platform(),
        "python": platform.python_version(),
        "tensorflow": tf.__version__,
        "opencv": cv2.__version__,
        "numpy": np.__version__,
        "cpu": "12th Gen Intel Core i5-12500 (6 cores / 12 threads)",
        "ram_gb": 15.7,
        "gpu_used": False,
    }
    result["model"] = {
        "parameters": int(model.count_params()),
        "file_size_mb": round(config.MODEL_PATH.stat().st_size / 1e6, 2),
        "input": [config.IMG_SIZE, config.IMG_SIZE, config.MODEL_CHANNELS],
        "classes": len(labels),
    }

    # ---- 1. held-out test split (same seed and code path as training) ----
    t0 = time.time()
    ds = dataset.load_dataset()
    result["dataset"] = {
        "images_in_data_folder": int(len(ds.x_train) + len(ds.x_val) + len(ds.x_test)),
        "train": int(len(ds.x_train)), "validation": int(len(ds.x_val)), "test": int(len(ds.x_test)),
        "per_class_in_data_folder": {c: n for c, n in dataset.class_counts().items()},
        "archive_images_per_class": 3000,
        "archive_total_images": 3000 * len(labels),
        "load_and_preprocess_seconds": round(time.time() - t0, 1),
    }
    probs = model.predict(ds.x_test, verbose=0)
    y_true = ds.y_test.argmax(1)
    loss = float(tf.keras.losses.categorical_crossentropy(ds.y_test, probs).numpy().mean())
    result["test_split"] = {**metrics_of(y_true, probs, labels), "loss": round(loss, 4)}
    result["test_split"]["per_class_f1"] = {
        l: round(float(f), 4) for l, f in zip(labels, f1_score(y_true, probs.argmax(1), average=None))
    }

    # ---- 2. confidence-threshold analysis on the test split ----
    conf = probs.max(1)
    correct = probs.argmax(1) == y_true
    rows = []
    for t in (0.0, 0.5, 0.6, 0.7, 0.75, 0.8, 0.9, 0.95, 0.99):
        keep = conf >= t
        rows.append({
            "threshold": t,
            "coverage": round(float(keep.mean()), 4),
            "accuracy_on_accepted": round(float(correct[keep].mean()), 4) if keep.any() else None,
        })
    result["threshold_analysis"] = rows

    # ---- 3. archive photos never used by data/ ----
    used = {(c, p.name) for c in labels for p in (config.DATA_DIR / c).glob("*.*")}
    unseen: list[tuple[np.ndarray, int]] = []
    for idx, c in enumerate(labels):
        pool = [p for p in sorted((ARCHIVE / c).glob("*.jpg")) if (c, p.name) not in used]
        for p in rng.sample(pool, PER_CLASS_UNSEEN):
            unseen.append((cv2.imread(str(p)), idx))
    raws = [r for r, _ in unseen]
    y_un = np.array([i for _, i in unseen])
    p_un = predict_raw(model, labels, raws)
    result["unseen_archive"] = {
        **metrics_of(y_un, p_un, labels),
        "note": "100 random archive photos per class that were not copied into data/ (never trained on)",
    }
    pc = {}
    for idx, c in enumerate(labels):
        m = y_un == idx
        pc[c] = round(float((p_un[m].argmax(1) == idx).mean()), 4)
    result["unseen_archive"]["per_class_accuracy"] = pc

    # ---- 4. the 28 official Kaggle test photos ----
    official = []
    for p in sorted(ARCHIVE_TEST.glob("*.jpg")):
        cls = p.stem.replace("_test", "")
        if cls in labels:
            official.append((cv2.imread(str(p)), labels.index(cls), cls))
    p_off = predict_raw(model, labels, [o[0] for o in official])
    result["official_test_28"] = {
        "n": len(official),
        "correct": int(sum(int(p.argmax() == o[1]) for p, o in zip(p_off, official))),
        "wrong": [{"true": o[2], "predicted": labels[int(p.argmax())], "confidence": round(float(p.max()), 3)}
                  for p, o in zip(p_off, official) if int(p.argmax()) != o[1]],
    }

    # ---- 5. robustness on a 20-per-class slice of the unseen photos ----
    sub = [(r, i) for k in range(len(labels)) for r, i in
           [x for x in unseen if x[1] == k][:PERTURB_PER_CLASS]]
    sub_raw = [r for r, _ in sub]
    y_sub = np.array([i for _, i in sub])
    nrng = np.random.default_rng(0)

    def bright(img, f):
        return np.clip(img.astype(np.float32) * f, 0, 255).astype(np.uint8)

    def noise(img, s):
        return np.clip(img.astype(np.float32) + nrng.normal(0, s, img.shape), 0, 255).astype(np.uint8)

    def rotate(img, a):
        h, w = img.shape[:2]
        return cv2.warpAffine(img, cv2.getRotationMatrix2D((w / 2, h / 2), a, 1.0), (w, h), borderMode=cv2.BORDER_REPLICATE)

    tests = {
        "clean": lambda i: i,
        "brightness x0.5": lambda i: bright(i, 0.5),
        "brightness x1.5": lambda i: bright(i, 1.5),
        "gaussian noise s=10": lambda i: noise(i, 10),
        "gaussian noise s=25": lambda i: noise(i, 25),
        "blur 5x5": lambda i: cv2.GaussianBlur(i, (5, 5), 0),
        "rotate +10 deg": lambda i: rotate(i, 10),
        "rotate -10 deg": lambda i: rotate(i, -10),
    }
    rob = {}
    for name, fn in tests.items():
        pr = predict_raw(model, labels, [fn(r) for r in sub_raw])
        rob[name] = round(float((pr.argmax(1) == y_sub).mean()), 4)
    result["robustness"] = {"n": len(sub), "accuracy": rob}

    # ---- 6. latency of each stage ----
    frames = []
    for r, _ in unseen[::29][:100]:
        f = np.full((540, 960, 3), (46, 38, 34), np.uint8)
        f[90:390, 620:920] = cv2.resize(r, (300, 300))
        frames.append(f)
    jpegs = [cv2.imencode(".jpg", f)[1].tobytes() for f in frames]
    model.predict(np.zeros((1, 64, 64, 1), np.float32), verbose=0)           # warm-up
    t_dec, t_pre, t_cnn, t_all = [], [], [], []
    for rep in range(3):
        for jb in jpegs:
            a = time.perf_counter()
            fr = cv2.imdecode(np.frombuffer(jb, np.uint8), cv2.IMREAD_COLOR)
            b = time.perf_counter()
            roi = crop_roi(fr, get_roi_box(fr.shape[1], fr.shape[0]))
            x = normalize_for_model(segment_hand(roi))[None]
            c = time.perf_counter()
            model.predict(x, verbose=0)
            d = time.perf_counter()
            t_dec.append((b - a) * 1e3); t_pre.append((c - b) * 1e3); t_cnn.append((d - c) * 1e3); t_all.append((d - a) * 1e3)
    result["latency"] = {
        "jpeg_decode_960x540": stats(t_dec),
        "roi_crop_and_segmentation_and_normalisation": stats(t_pre),
        "cnn_forward_batch1": stats(t_cnn),
        "server_side_total_per_frame": stats(t_all),
        "jpeg_payload_kb_mean": round(statistics.fmean(len(j) for j in jpegs) / 1024, 1),
    }
    result["latency"]["max_fps_server_side"] = round(1000 / result["latency"]["server_side_total_per_frame"]["median_ms"], 1)

    # ---- 7. HTTP round trip against a real uvicorn ----
    port = 8398
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--port", str(port), "--log-level", "warning"],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        base = f"http://127.0.0.1:{port}/api"
        for _ in range(120):
            try:
                if httpx.get(base + "/health", timeout=2).json().get("model_loaded"):
                    break
            except httpx.HTTPError:
                pass
            time.sleep(1)
        client = httpx.Client(base_url=base, timeout=30)
        sid = client.post("/recognize/session").json()["session_id"]
        ms = []
        for rep in range(3):
            for jb in jpegs:
                a = time.perf_counter()
                r = client.post("/recognize/frame", files={"frame": ("f.jpg", jb, "image/jpeg")}, data={"session_id": sid})
                ms.append((time.perf_counter() - a) * 1e3)
                assert r.status_code == 200
        result["latency"]["http_recognize_frame_round_trip"] = stats(ms)
        result["latency"]["http_round_trip_fps_sequential"] = round(1000 / statistics.median(ms), 1)
        h = []
        for _ in range(50):
            a = time.perf_counter(); client.get("/health"); h.append((time.perf_counter() - a) * 1e3)
        result["latency"]["http_health"] = stats(h)
    finally:
        proc.terminate()

    # ---- 8. training speed: 2 epochs into a temp folder ----
    from sign_language_app import train as train_mod
    tmp = Path(tempfile.mkdtemp(prefix="signspeak_trainbench_"))
    saved = (config.MODEL_PATH, config.LABELS_PATH, config.HISTORY_PATH, config.REPORT_PATH)
    config.MODEL_PATH, config.LABELS_PATH = tmp / "m.keras", tmp / "labels.json"
    config.HISTORY_PATH, config.REPORT_PATH = tmp / "h.json", tmp / "r.txt"
    stamps = []
    t_start = time.time()
    try:
        train_mod.train_model(epochs=2, epoch_cb=lambda e, n, logs: stamps.append(time.time()))
    finally:
        config.MODEL_PATH, config.LABELS_PATH, config.HISTORY_PATH, config.REPORT_PATH = saved
    result["training_speed"] = {
        "epochs_measured": 2,
        "total_seconds_including_data_load": round(time.time() - t_start, 1),
        "seconds_per_epoch": round((stamps[-1] - stamps[0]) / max(1, len(stamps) - 1), 1) if len(stamps) > 1 else None,
        "note": "measured on the CPU listed above; the saved 30-epoch run's wall-clock time was not recorded",
    }

    # ---- 9. training history facts from the saved run ----
    h = json.loads(config.HISTORY_PATH.read_text())
    best = int(np.argmax(h["val_accuracy"]))
    result["saved_training_run"] = {
        "epochs": len(h["accuracy"]),
        "best_val_accuracy": round(max(h["val_accuracy"]), 4),
        "best_epoch": best + 1,
        "final_train_accuracy": round(h["accuracy"][-1], 4),
        "final_val_accuracy": round(h["val_accuracy"][-1], 4),
        "final_train_loss": round(h["loss"][-1], 4),
        "final_val_loss": round(h["val_loss"][-1], 4),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
