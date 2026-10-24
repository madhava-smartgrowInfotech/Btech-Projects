"""F3 + F7 - train the feature-only baseline and the three GNNs on one split, write the served artifacts.

    python -m ml.train                 # full run: several seeds per model -> experiments/metrics.json
    python -m ml.train --quick         # one seed (used by the in-app retrain)
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone

import numpy as np
import torch
from sklearn.metrics import roc_curve

from . import clustering, config as C, data, gnn

METRIC_KEYS = ["accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc"]


def _decimate(a: np.ndarray, n: int = 60) -> list[float]:
    idx = np.unique(np.linspace(0, len(a) - 1, n).astype(int))
    return [round(float(v), 4) for v in a[idx]]


def fit_all(g: dict, seeds: list[int], feedback: dict[int, int] | None = None, progress=None) -> dict:
    """Train every model for every seed. feedback maps account id -> moderator label (0/1)."""
    X, mu, sd = gnn.standardise(g["X"])
    y, split = g["y"], g["split"]
    graph = gnn.Graph(len(y), g["edge_index"])
    x = torch.as_tensor(X)
    tr, va, te = (np.where(split == i)[0] for i in range(3))

    y_train = y.copy()
    n_fb = 0
    if feedback:
        fb_ids = np.array([i for i in feedback if split[i] != 2], dtype=np.int64)   # never touch the test split
        if len(fb_ids):
            for i in fb_ids:
                y_train[i] = feedback[int(i)]
            tr = np.union1d(tr, fb_ids)
            va = np.setdiff1d(va, fb_ids)
            n_fb = len(fb_ids)

    models, per_seed, served = {}, {m: [] for m in C.ALL_MODELS}, {}
    total, done = len(C.ALL_MODELS) * len(seeds), 0
    for name in C.ALL_MODELS:
        for s in seeds:
            model, info = gnn.train_model(name, x, graph, y, tr, va, seed=s, y_train=y_train)
            p, emb = gnn.prob_fake(model, x, graph)
            thr = gnn.best_threshold(y[va], p[va])
            m = gnn.metrics(y[te], p[te], thr)
            m.update(train_seconds=info["train_seconds"], epochs_run=info["epochs_run"], seed=s,
                     val_f1=gnn.metrics(y[va], p[va], thr)["f1"])
            fpr, tpr, _ = roc_curve(y[te], p[te])
            m["roc"] = {"fpr": _decimate(fpr), "tpr": _decimate(tpr)}
            per_seed[name].append(m)
            if s == seeds[0]:
                models[name] = model
                served[name] = {"p": p, "emb": emb, "thr": thr}
            done += 1
            if progress:
                progress(done / total, f"{C.MODEL_LABELS[name]} - seed {s}")

    summary = {}
    for name, runs in per_seed.items():
        summary[name] = {
            "label": C.MODEL_LABELS[name], "uses_graph": name != C.BASELINE,
            "seeds": [r["seed"] for r in runs],
            **{k: {"mean": float(np.mean([r[k] for r in runs])), "std": float(np.std([r[k] for r in runs]))} for k in METRIC_KEYS},
            "val_f1": float(np.mean([r["val_f1"] for r in runs])),
            "train_seconds": float(np.mean([r["train_seconds"] for r in runs])),
            "threshold": float(runs[0]["threshold"]), "confusion": runs[0]["confusion"], "roc": runs[0]["roc"],
            "per_seed": [{k: r[k] for k in METRIC_KEYS + ["seed", "threshold"]} for r in runs],
        }
    best = max(C.ARCHS, key=lambda a: summary[a]["val_f1"])
    for name in C.ALL_MODELS:
        summary[name]["is_best"] = name == best
    return {"summary": summary, "best": best, "models": models, "served": served, "mu": mu, "sd": sd,
            "splits": {"train": len(tr), "val": len(va), "test": len(te)}, "feedback_labels_used": n_fb}


def write_artifacts(g: dict, res: dict, kind: str = "full") -> dict:
    """Persist weights, scores, clusters and the metrics file the API serves."""
    C.MODELS.mkdir(parents=True, exist_ok=True)
    C.EXPERIMENTS.mkdir(parents=True, exist_ok=True)
    for name, m in res["models"].items():
        torch.save(m.state_dict(), C.MODELS / f"{name}.pt")
    served = res["served"]
    np.savez_compressed(
        C.MODELS / "scores.npz", mu=res["mu"], sd=res["sd"], emb=served[res["best"]]["emb"],
        **{f"p_{n}": served[n]["p"].astype(np.float32) for n in C.ALL_MODELS},
    )
    best = res["best"]
    thr = served[best]["thr"]
    p, emb = served[best]["p"], served[best]["emb"]
    comms = clustering.detect(emb, p, g["edge_index"])
    rec = clustering.recovery(comms, g["cluster"], g["y"])
    clusters = []
    for k, members in enumerate(comms):
        d = clustering.describe(members, g["accounts"], p, g["edge_index"], thr)
        d["id"] = f"BN-{int(members.min()):05d}"
        d["rank"] = k + 1
        d["members"] = [int(m) for m in members]
        d["kind"] = "coordinated" if d["density"] >= 0.05 else "diffuse"
        clusters.append(d)
    (C.MODELS / "clusters.json").write_text(json.dumps(clusters))
    meta = {
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "kind": kind, "best": best,
        "threshold": thr, "splits": res["splits"], "feedback_labels_used": res["feedback_labels_used"],
        "config": {"hidden": C.HIDDEN, "epochs": C.EPOCHS, "patience": C.PATIENCE, "lr": C.LR, "dropout": C.DROPOUT,
                   "weight_decay": C.WEIGHT_DECAY, "seeds": res["summary"][best]["seeds"]},
    }
    (C.MODELS / "meta.json").write_text(json.dumps(meta, indent=2))
    out = {"meta": meta, "models": res["summary"], "cluster_recovery": rec}
    (C.EXPERIMENTS / ("metrics.json" if kind == "full" else "metrics_retrain.json")).write_text(json.dumps(out, indent=2))
    return out


def run(seeds: list[int] | None = None, kind: str = "full") -> dict:
    g = data.load()
    t0 = time.perf_counter()
    res = fit_all(g, seeds or C.EVAL_SEEDS, progress=lambda f, msg: print(f"  [{f:4.0%}] {msg}", flush=True))
    out = write_artifacts(g, res, kind)
    print(f"trained in {time.perf_counter() - t0:.0f}s - best architecture: {C.MODEL_LABELS[res['best']]}")
    for n, s in res["summary"].items():
        print(f"  {s['label']:<28} F1 {s['f1']['mean']:.3f} ± {s['f1']['std']:.3f}   P {s['precision']['mean']:.3f}   R {s['recall']['mean']:.3f}")
    r = out["cluster_recovery"]
    print(f"  botnets recovered {r['recovered']}/{r['botnets']} (mean recall {r['mean_recall']:.2f}, precision {r['mean_precision']:.2f})")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="single seed")
    a = ap.parse_args()
    run([0] if a.quick else None, "quick" if a.quick else "full")
