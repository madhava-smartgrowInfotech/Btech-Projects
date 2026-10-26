"""
Liveness-challenge evaluation (MediaPipe Face Mesh metrics + core.liveness.verify_challenge).

No camera and no human volunteers are involved, so this script measures what can be measured honestly
from still images of the public LFW dataset:

  A. neutral-frame acceptance rate           (usability of the first photo)
  B. metric distributions                    (yaw, pitch, roll, MAR, EAR on accepted neutral frames)
  C. static replay attack                    (same photo submitted as neutral AND challenge frame)
  D. rotated-photo attack on TILT challenges (photo rotated by a signed angle, sweep -30..+30 deg)
  E. photo-bank attack                       (attacker owns several real photos of the victim and picks
                                              the best one for the challenge that was issued)

Genuine user performance (a live person actually performing the action) is NOT measured here.

    venv\\Scripts\\python scripts\\eval_liveness.py --lfw <dir with lfw/>
Output: docs/evaluation/liveness.json
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from core import liveness  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--lfw", required=True)
ap.add_argument("--n-sample", type=int, default=1000)
ap.add_argument("--seed", type=int, default=7)
args = ap.parse_args()
LFW = Path(args.lfw) / "lfw"
OUT = ROOT / "docs" / "evaluation"
OUT.mkdir(parents=True, exist_ok=True)
CHALLENGES = list(liveness.CHALLENGES)

_cache: dict[str, liveness.FaceMetrics] = {}


def metrics(path: Path) -> liveness.FaceMetrics:
    k = str(path)
    if k not in _cache:
        _cache[k] = liveness.analyze(cv2.imread(k))
    return _cache[k]


def rotate(img: np.ndarray, angle: float) -> np.ndarray:
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)


def main() -> None:
    rng = random.Random(args.seed)
    people = {d.name: sorted(d.glob("*.jpg")) for d in LFW.iterdir() if d.is_dir()}
    all_imgs = [p for v in people.values() for p in v]
    sample = rng.sample(all_imgs, args.n_sample)
    print(f"{len(all_imgs)} LFW images, sample {len(sample)}", flush=True)

    # ---- A. neutral acceptance ------------------------------------------------ #
    reasons = defaultdict(int)
    neutral_ok = []
    for p in sample:
        m = metrics(p)
        err = liveness.check_neutral(m)
        if err is None:
            neutral_ok.append(p)
        elif "No face" in err:
            reasons["no_face"] += 1
        elif "faces detected" in err:
            reasons["multiple_faces"] += 1
        elif "straight" in err:
            reasons["not_frontal"] += 1
        else:
            reasons["mouth_open"] += 1
    print(f"A. neutral accepted {len(neutral_ok)}/{len(sample)}", flush=True)

    # ---- B. distributions on accepted neutral frames -------------------------- #
    def stats(vals):
        a = np.array(vals)
        return {"mean": float(a.mean()), "std": float(a.std()), "p05": float(np.percentile(a, 5)),
                "p50": float(np.percentile(a, 50)), "p95": float(np.percentile(a, 95))}
    dist = {n: stats([getattr(metrics(p), n) for p in neutral_ok]) for n in ("yaw", "pitch", "roll_deg", "mar", "ear")}

    # ---- C. static replay ------------------------------------------------------ #
    static = {}
    for c in CHALLENGES:
        ok = sum(liveness.verify_challenge(c, metrics(p), metrics(p)).passed for p in neutral_ok)
        static[c] = {"passed": ok, "total": len(neutral_ok), "rate": ok / len(neutral_ok)}
    print("C. static replay", {c: round(v["rate"], 3) for c, v in static.items()}, flush=True)

    # ---- D. rotation sweep ----------------------------------------------------- #
    rot_sample = neutral_ok[:300]
    angles = [-30, -25, -20, -15, -12, -10, -8, -5, -2, 0, 2, 5, 8, 10, 12, 15, 20, 25, 30]
    rot = {"angles": angles, "n": len(rot_sample), "TILT_LEFT": [], "TILT_RIGHT": [], "measured_roll_delta_mean": []}
    for a in angles:
        pl = pr = 0
        deltas = []
        for p in rot_sample:
            img = cv2.imread(str(p))
            m0 = metrics(p)
            m1 = liveness.analyze(rotate(img, a))
            if not m1.ok:
                continue
            deltas.append(m1.roll_deg - m0.roll_deg)
            pl += liveness.verify_challenge("TILT_LEFT", m0, m1).passed
            pr += liveness.verify_challenge("TILT_RIGHT", m0, m1).passed
        n_ok = max(1, len(deltas))
        rot["TILT_LEFT"].append(pl / len(rot_sample))
        rot["TILT_RIGHT"].append(pr / len(rot_sample))
        rot["measured_roll_delta_mean"].append(float(np.mean(deltas)) if deltas else None)
    print("D. rotation sweep done", flush=True)

    # ---- E. photo-bank attack --------------------------------------------------- #
    victims = {n: v for n, v in people.items() if len(v) >= 10}
    bank = {c: {"success": 0, "victims": 0} for c in CHALLENGES}
    bank_by_k = {k: {c: 0 for c in CHALLENGES} for k in (2, 5, 10)}
    n_victims = 0
    for name, imgs in victims.items():
        ms = [(p, metrics(p)) for p in imgs]
        neutrals = [(p, m) for p, m in ms if liveness.check_neutral(m) is None]
        if not neutrals:
            continue
        n_victims += 1
        np_, nm = neutrals[0]
        others = [(p, m) for p, m in ms if p != np_ and m.ok]
        for c in CHALLENGES:
            bank[c]["victims"] += 1
            if any(liveness.verify_challenge(c, nm, m).passed for _, m in others):
                bank[c]["success"] += 1
            for k in bank_by_k:
                if any(liveness.verify_challenge(c, nm, m).passed for _, m in others[:k - 1]):
                    bank_by_k[k][c] += 1
    for c in CHALLENGES:
        bank[c]["rate"] = bank[c]["success"] / max(1, bank[c]["victims"])
    bank_k = {str(k): {c: v / max(1, n_victims) for c, v in d.items()} for k, d in bank_by_k.items()}
    print("E. photo-bank", {c: round(v["rate"], 3) for c, v in bank.items()}, flush=True)

    result = {
        "dataset": "LFW (still images, 250x250); no live subjects",
        "metrics_backend": liveness.get_detector().backend,
        "thresholds": {"yaw_delta": config.LIVENESS_YAW_DELTA, "pitch_delta": config.LIVENESS_PITCH_DELTA,
                       "roll_deg": config.LIVENESS_ROLL_DEG, "mar": config.LIVENESS_MOUTH_OPEN_MAR,
                       "ear": config.LIVENESS_EYES_CLOSED_EAR, "neutral_max_yaw": config.NEUTRAL_MAX_YAW,
                       "neutral_max_mar": config.NEUTRAL_MAX_MAR, "camera_mirrored": config.CAMERA_MIRRORED},
        "A_neutral": {"sample": len(sample), "accepted": len(neutral_ok), "rate": len(neutral_ok) / len(sample),
                      "rejected_by": dict(reasons)},
        "B_distributions": dist,
        "C_static_replay": static,
        "D_rotation_sweep": rot,
        "E_photo_bank": {"victims": n_victims, "min_photos_per_victim": 10, "by_challenge": bank, "by_photos_available": bank_k},
    }
    (OUT / "liveness.json").write_text(json.dumps(result, indent=1))
    print("wrote", OUT / "liveness.json")


if __name__ == "__main__":
    main()
