"""F7 - evaluation numbers: per-architecture metrics, cluster recovery and the scalability sweep.

    python -m ml.eval                 # reads experiments/metrics.json, runs the scalability sweep,
                                      # writes experiments/eval/metrics.json and experiments/scalability.json
"""
from __future__ import annotations

import json
import time

import numpy as np
import torch
import torch.nn.functional as F

from . import config as C, data, gnn

SCALES = [1, 2, 4, 8]
TIMED_EPOCHS = 10


def replicate(g: dict, k: int) -> tuple[np.ndarray, np.ndarray]:
    """k disjoint copies of the graph (features and edges) - a clean way to grow nodes and edges."""
    n = len(g["y"])
    X = np.tile(g["X"], (k, 1))
    ei = np.concatenate([g["edge_index"] + i * n for i in range(k)])
    return X, ei


def scalability(g: dict) -> dict:
    rows = []
    for k in SCALES:
        X, ei = replicate(g, k)
        Xs, _, _ = gnn.standardise(X)
        n = len(X)
        yk = np.tile(g["y"], k)
        t0 = time.perf_counter()
        graph = gnn.Graph(n, ei)
        build_s = time.perf_counter() - t0
        x = torch.as_tensor(Xs)
        row = {"scale": k, "nodes": int(n), "edges": int(len(ei)), "graph_build_seconds": build_s, "models": {}}
        for name in C.ALL_MODELS:
            torch.manual_seed(0)
            model = gnn.Net(name, x.shape[1])
            opt = torch.optim.Adam(model.parameters(), lr=C.LR)
            tr = torch.arange(n)
            y_t = torch.as_tensor(yk)
            t0 = time.perf_counter()
            for _ in range(TIMED_EPOCHS):
                model.train()
                opt.zero_grad()
                logits, _ = model(x, graph)
                F.cross_entropy(logits[tr], y_t[tr]).backward()
                opt.step()
            train_s = (time.perf_counter() - t0) / TIMED_EPOCHS
            model.eval()
            times = []
            for _ in range(3):
                t0 = time.perf_counter()
                with torch.no_grad():
                    model(x, graph)
                times.append(time.perf_counter() - t0)
            row["models"][name] = {"train_seconds_per_epoch": train_s, "inference_seconds": float(np.median(times))}
            print(f"  x{k:<2} {n:>6} nodes {len(ei):>8} edges  {name:<8} train {train_s:6.3f}s/epoch  infer {np.median(times):6.3f}s", flush=True)
        rows.append(row)
    return {"epochs_timed": TIMED_EPOCHS, "method": "disjoint copies of the account graph", "rows": rows}


def run() -> dict:
    g = data.load()
    base = json.loads((C.EXPERIMENTS / "metrics.json").read_text())
    sc = scalability(g)
    (C.EXPERIMENTS / "scalability.json").write_text(json.dumps(sc, indent=2))
    ev = C.EXPERIMENTS / "eval"
    ev.mkdir(exist_ok=True, parents=True)
    compact = {
        "split": base["meta"]["splits"], "best_architecture": base["meta"]["best"],
        "models": {n: {k: base["models"][n][k] for k in ("label", "accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc", "train_seconds")}
                   for n in base["models"]},
        "baseline_f1": base["models"][C.BASELINE]["f1"]["mean"],
        "graph_lift_f1": {a: base["models"][a]["f1"]["mean"] - base["models"][C.BASELINE]["f1"]["mean"] for a in C.ARCHS},
        "cluster_recovery": {k: v for k, v in base["cluster_recovery"].items() if k != "per_botnet"},
        "scalability": [{"nodes": r["nodes"], "edges": r["edges"], **{m: r["models"][m] for m in r["models"]}} for r in sc["rows"]],
    }
    (ev / "metrics.json").write_text(json.dumps(compact, indent=2))
    return compact


if __name__ == "__main__":
    run()
    print("wrote experiments/eval/metrics.json")
