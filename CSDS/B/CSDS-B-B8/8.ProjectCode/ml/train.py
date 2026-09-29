"""Train the activity classifier on keypoint windows (CPU, ~1 min).

    python ml/train.py

Outputs: models/activity_rf.joblib and experiments/metrics.json
"""
import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml"))
sys.path.insert(0, str(ROOT / "backend"))
from sequences import Builder, load_poses, own_clip_windows, pose_pool  # noqa: E402
from app.services.features import WINDOW, window_features  # noqa: E402

CLASSES = ["walking", "standing", "sitting", "lying", "drinking", "picking_up"]
SEED = 42
ALL_VARIANTS = ["normal", "gt", "dark", "dark_enh"]


def build_set(d, split, variants, n_per_class, seed, force_block=None):
    b = Builder(seed)
    b.force_block = force_block
    pools = {c: pose_pool(d, c, split, variants) for c in ("standing", "sitting", "lying", "drinking")}
    makers = {
        "walking": lambda: b.walking(pools["standing"]),
        "standing": lambda: b.still(pools["standing"]),
        "sitting": lambda: b.still(pools["sitting"]),
        "lying": lambda: b.still(pools["lying"], amp=0.002),
        "drinking": lambda: b.drinking(pools["drinking"]),
        "picking_up": lambda: b.picking_up(pools["standing"]),
    }
    needs = {"walking": "standing", "standing": "standing", "sitting": "sitting", "lying": "lying",
             "drinking": "drinking", "picking_up": "standing"}
    X, y = [], []
    for c in CLASSES:
        if not pools[needs[c]]:
            continue  # e.g. no pose found in any dim image of this class
        made = 0
        while made < n_per_class:
            t, frames = makers[c]()
            f = window_features(list(zip(t, frames)))
            if f is not None:
                X.append(f)
                y.append(c)
                made += 1
    return np.stack(X), np.array(y), {c: len(p) for c, p in pools.items()}


def clip_set(split):
    X, y = [], []
    for label, s, (t, ks) in own_clip_windows():
        if s != split or label not in CLASSES or len(ks) < WINDOW // 2:
            continue
        f = window_features(list(zip(t, ks)))
        if f is not None:
            X.append(f)
            y.append(label)
    return X, y


def main():
    t0 = time.time()
    d = load_poses()
    X, y, pools = build_set(d, "train", ALL_VARIANTS, 1500, SEED)
    cx, cy = clip_set("train")
    if cx:
        X, y = np.vstack([X, np.stack(cx)]), np.concatenate([y, cy])
    print(f"train windows: {len(y)} (own-clip windows: {len(cy)}), base poses: {pools}")

    model = RandomForestClassifier(n_estimators=300, min_samples_leaf=2, class_weight="balanced_subsample",
                                   n_jobs=-1, random_state=SEED)
    model.fit(X, y)

    Xt, yt, test_pools = build_set(d, "test", ["normal", "gt"], 300, SEED + 1)
    tx, ty = clip_set("test")
    if tx:
        Xt, yt = np.vstack([Xt, np.stack(tx)]), np.concatenate([yt, ty])
    pred = model.predict(Xt)
    rep = classification_report(yt, pred, labels=CLASSES, output_dict=True, zero_division=0)
    metrics = {
        "model": "RandomForest(300 trees) over 20-frame YOLO11n-pose keypoint windows",
        "classes": CLASSES,
        "train_windows": int(len(y)),
        "own_clip_train_windows": len(cy),
        "base_poses_train": pools,
        "base_poses_test": test_pools,
        "test_windows": int(len(yt)),
        "test_accuracy": round(accuracy_score(yt, pred), 4),
        "macro_f1": round(rep["macro avg"]["f1-score"], 4),
        "per_class": {c: {k: round(rep[c][k], 4) for k in ("precision", "recall", "f1-score")} for c in CLASSES},
        "confusion_matrix": confusion_matrix(yt, pred, labels=CLASSES).tolist(),
        "train_seconds": round(time.time() - t0, 1),
    }
    (ROOT / "models").mkdir(exist_ok=True)
    joblib.dump({"model": model, "classes": list(model.classes_), "window": WINDOW}, ROOT / "models" / "activity_rf.joblib",
                compress=3)
    (ROOT / "experiments").mkdir(exist_ok=True)
    (ROOT / "experiments" / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps({k: metrics[k] for k in ("test_accuracy", "macro_f1", "per_class")}, indent=2))


if __name__ == "__main__":
    main()
