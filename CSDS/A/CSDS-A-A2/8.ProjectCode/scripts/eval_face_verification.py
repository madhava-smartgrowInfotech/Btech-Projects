"""
Identity / duplicate-face threshold evaluation on the public LFW benchmark.

The product ships no trained model of its own: identity and duplicate checks use InsightFace
`buffalo_l` (ArcFace) through core.face_match.embed() and a cosine-similarity threshold. This script
measures how those two thresholds (AM_IDENTITY_THRESHOLD = 0.40, AM_DUPLICATE_THRESHOLD = 0.45)
behave on the standard LFW verification protocol (pairs.txt: 10 folds x 300 matched + 300 mismatched).

    venv\\Scripts\\python scripts\\eval_face_verification.py --lfw <dir with lfw/ and pairs.txt>

Output: docs/evaluation/face_verification.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from core import face_match  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--lfw", required=True, help="directory holding lfw/ (images) and pairs.txt")
ap.add_argument("--cache", default=None, help="optional .npz cache of embeddings")
args = ap.parse_args()
LFW = Path(args.lfw)
OUT = ROOT / "docs" / "evaluation"
OUT.mkdir(parents=True, exist_ok=True)


def img_path(name: str, idx: int) -> Path:
    return LFW / "lfw" / name / f"{name}_{idx:04d}.jpg"


def read_pairs():
    lines = (LFW / "pairs.txt").read_text().strip().splitlines()
    folds, per = (int(x) for x in lines[0].split())
    pairs = []  # (fold, label, pathA, pathB)
    k = 0
    for ln in lines[1:]:
        f = ln.split()
        fold = k // (2 * per)
        if len(f) == 3:
            pairs.append((fold, 1, img_path(f[0], int(f[1])), img_path(f[0], int(f[2]))))
        else:
            pairs.append((fold, 0, img_path(f[0], int(f[1])), img_path(f[2], int(f[3]))))
        k += 1
    return folds, pairs


def main() -> None:
    folds, pairs = read_pairs()
    unique = sorted({p for _, _, a, b in pairs for p in (a, b)})
    print(f"{len(pairs)} pairs, {len(unique)} unique images", flush=True)

    cache = {}
    if args.cache and Path(args.cache).exists():
        z = np.load(args.cache, allow_pickle=True)
        cache = dict(z["cache"].item())
    face_match.get_embedder()  # warm
    times, failed = [], {}
    t0 = time.time()
    for i, p in enumerate(unique):
        key = str(p)
        if key in cache:
            continue
        img = cv2.imread(key)
        t = time.perf_counter()
        try:
            cache[key] = face_match.embed(img)
        except face_match.FaceError as exc:
            cache[key] = None
            failed[key] = str(exc)
        times.append((time.perf_counter() - t) * 1000)
        if i % 500 == 0:
            print(f"  {i}/{len(unique)}  {time.time() - t0:.0f}s", flush=True)
    if args.cache:
        np.savez(args.cache, cache=np.array(cache, dtype=object))

    sims, labels, fold_ids, usable = [], [], [], []
    n_fail_pairs = 0
    for fold, label, a, b in pairs:
        ea, eb = cache[str(a)], cache[str(b)]
        if ea is None or eb is None:
            n_fail_pairs += 1
            continue
        sims.append(face_match.cosine(ea, eb))
        labels.append(label)
        fold_ids.append(fold)
    sims, labels, fold_ids = np.array(sims), np.array(labels), np.array(fold_ids)
    gen, imp = sims[labels == 1], sims[labels == 0]

    def rates(th: float) -> dict:
        return {"threshold": th,
                "tar": float((gen >= th).mean()),            # genuine accepted
                "frr": float((gen < th).mean()),             # genuine rejected
                "far": float((imp >= th).mean()),            # impostor accepted
                "accuracy": float(((sims >= th) == (labels == 1)).mean())}

    ths = np.round(np.arange(-0.2, 1.0001, 0.01), 2)
    sweep = [rates(float(t)) for t in ths]
    eer_row = min(sweep, key=lambda r: abs(r["far"] - r["frr"]))
    best_row = max(sweep, key=lambda r: r["accuracy"])

    # standard 10-fold protocol: pick threshold on 9 folds, test on the held-out fold
    fold_acc = []
    for f in range(folds):
        tr, te = fold_ids != f, fold_ids == f
        best_t = max(ths, key=lambda t: ((sims[tr] >= t) == (labels[tr] == 1)).mean())
        fold_acc.append(float(((sims[te] >= best_t) == (labels[te] == 1)).mean()))

    # AUC by rank statistic
    order = np.argsort(np.concatenate([gen, imp]))
    ranks = np.empty(len(order))
    ranks[order] = np.arange(1, len(order) + 1)
    auc = float((ranks[: len(gen)].sum() - len(gen) * (len(gen) + 1) / 2) / (len(gen) * len(imp)))

    result = {
        "dataset": "LFW (Labeled Faces in the Wild), standard verification protocol pairs.txt",
        "model": f"insightface {config.INSIGHTFACE_MODEL} via core.face_match.embed (CPU)",
        "images_unique": len(unique), "pairs_total": len(pairs), "pairs_scored": int(len(sims)),
        "pairs_dropped_no_single_face": n_fail_pairs, "images_without_single_face": len(failed),
        "genuine_pairs": int(len(gen)), "impostor_pairs": int(len(imp)),
        "genuine_mean": float(gen.mean()), "genuine_std": float(gen.std()),
        "genuine_min": float(gen.min()), "genuine_p05": float(np.percentile(gen, 5)),
        "impostor_mean": float(imp.mean()), "impostor_std": float(imp.std()),
        "impostor_max": float(imp.max()), "impostor_p95": float(np.percentile(imp, 95)),
        "impostor_p99": float(np.percentile(imp, 99)),
        "auc": auc, "eer": float((eer_row["far"] + eer_row["frr"]) / 2), "eer_threshold": eer_row["threshold"],
        "best_accuracy": best_row, "ten_fold_accuracy_mean": float(np.mean(fold_acc)),
        "ten_fold_accuracy_std": float(np.std(fold_acc)), "ten_fold_accuracy": fold_acc,
        "at_identity_threshold": rates(config.IDENTITY_THRESHOLD),
        "at_duplicate_threshold": rates(config.DUPLICATE_THRESHOLD),
        "sweep": sweep,
        "embed_ms_mean": float(np.mean(times)) if times else None,
        "embed_ms_p50": float(np.percentile(times, 50)) if times else None,
        "embed_ms_p95": float(np.percentile(times, 95)) if times else None,
        "genuine_sims": [round(float(x), 4) for x in gen], "impostor_sims": [round(float(x), 4) for x in imp],
    }
    (OUT / "face_verification.json").write_text(json.dumps(result))
    print(json.dumps({k: v for k, v in result.items() if k not in ("sweep", "genuine_sims", "impostor_sims", "ten_fold_accuracy")}, indent=1))


if __name__ == "__main__":
    main()
