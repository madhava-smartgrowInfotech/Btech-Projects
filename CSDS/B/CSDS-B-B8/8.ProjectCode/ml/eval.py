"""CareWatch evaluation (F8): activity accuracy/F1 (normal, dim, occluded), fall sensitivity/specificity,
and alert latency.   python ml/eval.py   ->  experiments/eval/metrics.json
"""
import json
import sqlite3
import sys
import time
from collections import deque
from pathlib import Path

import cv2
import joblib
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, recall_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml"))
sys.path.insert(0, str(ROOT / "backend"))
from sequences import LOWER, Builder, canon, load_poses, own_clip_windows, pose_pool  # noqa: E402
from train import CLASSES, build_set  # noqa: E402
from app.services.fall import FallDetector  # noqa: E402
from app.services.features import WINDOW, window_features  # noqa: E402
from app.services.pose import PoseEstimator, maybe_enhance  # noqa: E402

SEED = 7
FPS = 10
COUNTDOWN_S = 20
OUT = ROOT / "experiments" / "eval" / "metrics.json"


def activity_eval(model, d):
    conds = {
        "normal": (["normal", "gt"], None),
        "dim_no_enhancement": (["dark"], None),
        "dim_enhanced": (["dark_enh"], None),
        "occluded_legs": (["normal", "gt"], LOWER),
    }
    out = {}
    for name, (variants, block) in conds.items():
        X, y, pools = build_set(d, "test", variants, 250, SEED, force_block=block)
        p = model.predict(X)
        present = [c for c in CLASSES if (y == c).any()]
        rec = recall_score(y, p, labels=present, average=None, zero_division=0)
        f1 = f1_score(y, p, labels=present, average=None, zero_division=0)
        out[name] = {
            "windows": int(len(y)),
            "accuracy": round(accuracy_score(y, p), 4),
            "macro_f1": round(float(np.mean(f1)), 4),
            "per_class": {c: {"accuracy": round(float(r), 4), "f1": round(float(f), 4)} for c, r, f in zip(present, rec, f1)},
            "base_poses": pools,
        }
        print(f"  activity [{name}] acc={out[name]['accuracy']} macroF1={out[name]['macro_f1']}")
    clips = [(lab, w) for lab, s, w in own_clip_windows() if s == "test" and lab in CLASSES]
    if clips:
        X, y = [], []
        for lab, (t, ks) in clips:
            f = window_features(list(zip(t, ks)))
            if f is not None:
                X.append(f)
                y.append(lab)
        if X:
            p = model.predict(np.stack(X))
            out["own_clips"] = {"windows": len(y), "accuracy": round(accuracy_score(y, p), 4),
                                "macro_f1": round(f1_score(y, p, average="macro", zero_division=0), 4), "per_class": {}}
    # how often the pose model finds the person at all, per lighting condition
    det = {}
    imgs = {v: set(d["image"][(d["variant"] == v) & (d["split"] == "test")]) for v in ("normal", "dark", "dark_enh")}
    allimg = set().union(*imgs.values())
    for v, s in imgs.items():
        det[v] = round(len(s) / max(len(allimg), 1), 4)
    return out, det


def smoothed_lying_probs(model, t, frames):
    """Replicates the live recogniser: classifier over the trailing window + exponential smoothing."""
    classes = list(model.classes_)
    li = classes.index("lying")
    feats, idx = [], []
    win = deque(maxlen=WINDOW)
    for i, (ti, k) in enumerate(zip(t, frames)):
        win.append((ti, k))
        if len(win) >= WINDOW // 2:
            f = window_features(list(win))
            if f is not None:
                feats.append(f)
                idx.append(i)
    probs = np.zeros(len(frames))
    if feats:
        P = model.predict_proba(np.stack(feats))[:, li]
        s = None
        for i, p in zip(idx, P):
            s = p if s is None else 0.6 * s + 0.4 * p
            probs[i] = s
    return probs


def fall_eval(model, d):
    b = Builder(SEED)
    stand = pose_pool(d, "standing", "test", ["normal", "gt"])
    lie = pose_pool(d, "lying", "test", ["normal", "gt"])
    sit = pose_pool(d, "sitting", "test", ["normal", "gt"])
    pick = lambda pool: canon(pool[b.rng.integers(len(pool))])  # noqa: E731

    def trans(target_pool, dur, ease, scale=1.0, occl=False):
        size, pos = b.scene()
        t, frames, t_end = b.transition(pick(stand), pick(target_pool), size, pos, dur, 20, 100, FPS,
                                        ease=ease, target_scale=scale)
        if occl:  # legs hidden behind furniture after the fall
            for k in frames[int(t_end * FPS):]:
                k[LOWER, 2] = 0
        return t, frames, t_end

    def activity(maker, n=80):
        t, frames = maker(n)
        return t, frames, None

    scenarios = {
        "fall_fast": (True, lambda: trans(lie, b.rng.uniform(0.3, 0.6), "gravity")),
        "fall_slow_collapse": (True, lambda: trans(lie, b.rng.uniform(0.8, 1.4), "gravity")),
        "fall_legs_occluded": (True, lambda: trans(lie, b.rng.uniform(0.3, 1.0), "gravity", occl=True)),
        "sit_down": (False, lambda: trans(sit, b.rng.uniform(0.8, 2.0), "cosine", scale=0.72)),
        "lie_down_slowly": (False, lambda: trans(lie, b.rng.uniform(3.5, 6.0), "cosine")),
        "pick_up_object": (False, lambda: activity(lambda n: b.picking_up(stand, n))),
        "walking": (False, lambda: activity(lambda n: b.walking(stand, n))),
        "standing": (False, lambda: activity(lambda n: b.still(stand, n))),
    }
    by, lat = {}, []
    tp = fn = tn = fp = 0
    for name, (is_fall, make) in scenarios.items():
        alerts = 0
        for _ in range(80):
            t, frames, t_end = make()
            t = np.arange(len(frames)) / FPS  # evaluation runs at a fixed 10 fps
            p_lying = smoothed_lying_probs(model, t, frames)
            det = FallDetector(confirm_seconds=3.0)
            hit = None
            for ti, k, pl in zip(t, frames, p_lying):
                ev = det.update(float(ti), k, float(pl))
                if ev and ev["type"] == "fall":
                    hit = float(ti)
                    break
            if hit is not None:
                alerts += 1
                if is_fall:
                    lat.append(hit - t_end)
            if is_fall:
                tp += hit is not None
                fn += hit is None
            else:
                fp += hit is not None
                tn += hit is None
        by[name] = {"is_fall": is_fall, "n": 80, "alerts": alerts}
        print(f"  fall [{name}] alerts {alerts}/80")
    lat = np.array(lat) if lat else np.array([np.nan])
    return {
        "positives": tp + fn, "negatives": tn + fp, "tp": tp, "fn": fn, "tn": tn, "fp": fp,
        "sensitivity": round(tp / max(tp + fn, 1), 4), "specificity": round(tn / max(tn + fp, 1), 4),
        "by_scenario": by,
        "detection_latency_s": {"mean": round(float(np.nanmean(lat)), 3), "median": round(float(np.nanmedian(lat)), 3),
                                "p95": round(float(np.nanpercentile(lat, 95)), 3), "max": round(float(np.nanmax(lat)), 3)},
        "confirm_window_s": 3.0,
    }


def latency_eval(model):
    est = PoseEstimator(imgsz=480)
    imgs = sorted((ROOT / "data" / "fall_detection" / "images" / "val").glob("*.jpg"))[:40]
    frames = [cv2.imread(str(p)) for p in imgs]
    est.detect(frames[0])  # warm-up
    t0 = time.perf_counter()
    kp = []
    for f in frames:
        img, _, _ = maybe_enhance(f, "auto")
        p = est.main_person(est.detect(img))
        kp.append(p["kpts"] if p else None)
    pose_ms = (time.perf_counter() - t0) * 1000 / len(frames)
    win = [(i / FPS, k) for i, k in enumerate(kp[:WINDOW]) if k is not None]
    t0 = time.perf_counter()
    for _ in range(20):
        f = window_features(win)
        if f is not None:
            model.predict_proba(f[None])
    clf_ms = (time.perf_counter() - t0) * 1000 / 20

    dispatch_ms, note = None, "Telegram/email not configured yet - measured on live alerts once keys are set"
    db = ROOT / "data" / "app.db"
    if db.exists():
        con = sqlite3.connect(db)
        rows = con.execute("SELECT dispatch_ms FROM alerts WHERE status='sent' AND dispatch_ms IS NOT NULL").fetchall()
        con.close()
        if rows:
            dispatch_ms = round(float(np.mean([r[0] for r in rows])), 1)
            note = f"mean over {len(rows)} delivered alerts"
    return {"pose_ms_per_frame": round(pose_ms, 1), "classifier_ms_per_window": round(clf_ms, 2),
            "pipeline_fps": round(1000 / (pose_ms + clf_ms), 1), "countdown_s": COUNTDOWN_S,
            "dispatch_ms": dispatch_ms, "dispatch_note": note}


def main():
    d = load_poses()
    model = joblib.load(ROOT / "models" / "activity_rf.joblib")["model"]
    print("Activity recognition...")
    act, det = activity_eval(model, d)
    print("Fall detection...")
    fall = fall_eval(model, d)
    print("Latency...")
    lat = latency_eval(model)
    lat["end_to_end_s"] = round(fall["detection_latency_s"]["mean"] + COUNTDOWN_S + (lat["dispatch_ms"] or 0) / 1000, 2)
    res = {
        "activity": {
            "classes": CLASSES, "conditions": act, "person_detection_rate": det,
            "note": "Test windows come from held-out images (never used in training). Motion is added to real "
                    "extracted poses by the seeded sequence builder; 'dim' uses darkened copies of the test images.",
        },
        "fall": fall,
        "latency": lat,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2))
    print(json.dumps({"activity_accuracy": {k: v["accuracy"] for k, v in act.items()},
                      "fall_sensitivity": fall["sensitivity"], "fall_specificity": fall["specificity"],
                      "detection_latency_s": fall["detection_latency_s"], "latency": lat}, indent=2))


if __name__ == "__main__":
    main()
