"""Extra measurements for the project documents (threshold sweep, error analysis, feature-group ablation).

    python scripts/run_extra_experiments.py

Reads the shipped graph and scores, trains small ablation models in memory and writes experiments/extra/metrics.json.
It never touches models/ or the other experiment files.
"""
import torch  # noqa: F401  (must be imported before numpy / pandas on this machine)

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ml import config as C, data, gnn  # noqa: E402

OUT = ROOT / "experiments" / "extra"
SEEDS = [0, 1, 2]


def threshold_sweep(g, z):
    y, split = g["y"], g["split"]
    te = split == 2
    rows = {}
    for name in ("baseline", "sage"):
        p = z[f"p_{name}"]
        rows[name] = []
        for t in np.round(np.arange(0.1, 0.951, 0.05), 2):
            m = gnn.metrics(y[te], p[te], float(t))
            c = m["confusion"]
            rows[name].append({"threshold": float(t), "precision": m["precision"], "recall": m["recall"], "f1": m["f1"],
                               "fp": c["fp"], "fn": c["fn"], "tp": c["tp"], "flagged": c["tp"] + c["fp"]})
    return rows


def error_analysis(g, z, thr):
    y, split, acc = g["y"], g["split"], g["accounts"]
    te = np.where(split == 2)[0]
    deg = np.bincount(g["edge_index"].ravel(), minlength=len(y))
    out = {"threshold": thr}
    ps, pb = z["p_sage"], z["p_baseline"]
    fake_te = te[y[te] == 1]
    kind = np.where(g["cluster"][fake_te] >= 0, "botnet member", "lone spammer")
    caught_s = ps[fake_te] >= thr
    caught_b = pb[fake_te] >= 0.5
    out["test_fake"] = int(len(fake_te))
    out["by_kind"] = {}
    for k in ("botnet member", "lone spammer"):
        mk = kind == k
        out["by_kind"][k] = {"n": int(mk.sum()), "sage_caught": int(caught_s[mk].sum()), "baseline_caught": int(caught_b[mk].sum())}
    out["rescued_by_graph"] = int((caught_s & ~caught_b).sum())     # missed by baseline, caught by GraphSAGE
    out["lost_by_graph"] = int((~caught_s & caught_b).sum())        # caught by baseline, missed by GraphSAGE
    out["missed_by_both"] = int((~caught_s & ~caught_b).sum())
    d = deg[fake_te]
    out["degree_fake_caught_median"] = float(np.median(d[caught_s])) if caught_s.any() else None
    out["degree_fake_missed_median"] = float(np.median(d[~caught_s])) if (~caught_s).any() else None
    gen_te = te[y[te] == 0]
    fp_ids = gen_te[ps[gen_te] >= thr]
    out["false_positives"] = int(len(fp_ids))
    out["false_positive_origin"] = {str(k): int(v) for k, v in zip(*np.unique(acc.loc[fp_ids, "origin"], return_counts=True))}
    out["false_positive_degree"] = [int(deg[i]) for i in fp_ids]
    miss = fake_te[~caught_s]
    out["missed"] = [{"id": int(i), "kind": "botnet member" if g["cluster"][i] >= 0 else "lone spammer",
                      "score": round(float(ps[i]), 3), "baseline_score": round(float(pb[i]), 3), "degree": int(deg[i])} for i in miss]
    return out


def ablation(g):
    names = data.FEATURES
    grp = lambda *gs: [i for i, f in enumerate(names) if data.FEATURE_GROUPS[f] in gs]
    allf = list(range(len(names)))
    deg = np.log1p(np.bincount(g["edge_index"].ravel(), minlength=len(g["y"]))).astype(np.float32)[:, None]
    variants = {
        "all 23 features": allf,
        "without profile metadata": [i for i in allf if i not in grp("Profile metadata")],
        "without posting behaviour": [i for i in allf if i not in grp("Posting behaviour")],
        "without temporal pattern": [i for i in allf if i not in grp("Temporal pattern")],
        "without interaction frequency": [i for i in allf if i not in grp("Interaction frequency")],
        "profile metadata only": grp("Profile metadata"),
        "behaviour only (posting, temporal, interaction)": grp("Posting behaviour", "Temporal pattern", "Interaction frequency"),
        "degree only (structure, no attributes)": "degree",
    }
    y, split = g["y"], g["split"]
    tr, va, te = (np.where(split == i)[0] for i in range(3))
    graph = gnn.Graph(len(y), g["edge_index"])
    res = {}
    for vname, cols in variants.items():
        X = deg if isinstance(cols, str) else g["X"][:, cols]
        x = torch.as_tensor(gnn.standardise(X)[0])
        res[vname] = {"n_features": int(X.shape[1])}
        for arch in ("baseline", "sage"):
            f1s, ps, rs = [], [], []
            for s in SEEDS:
                model, _ = gnn.train_model(arch, x, graph, y, tr, va, seed=s)
                p, _ = gnn.prob_fake(model, x, graph)
                thr = gnn.best_threshold(y[va], p[va])
                m = gnn.metrics(y[te], p[te], thr)
                f1s.append(m["f1"]); ps.append(m["precision"]); rs.append(m["recall"])
            res[vname][arch] = {"f1_mean": float(np.mean(f1s)), "f1_std": float(np.std(f1s)),
                                "precision_mean": float(np.mean(ps)), "recall_mean": float(np.mean(rs)), "f1_per_seed": f1s}
        print(f"  {vname:<52} baseline {res[vname]['baseline']['f1_mean']:.3f}   sage {res[vname]['sage']['f1_mean']:.3f}", flush=True)
    return res


def main():
    t0 = time.perf_counter()
    g = data.load()
    z = np.load(C.MODELS / "scores.npz")
    meta = json.loads((C.MODELS / "meta.json").read_text())
    out = {"note": "threshold sweep and error analysis use the shipped scores (seed 0 models); ablation retrains in memory, 3 seeds",
           "served_threshold": meta["threshold"]}
    out["threshold_sweep"] = threshold_sweep(g, z)
    out["error_analysis"] = error_analysis(g, z, meta["threshold"])
    print("ablation (F1, 3 seeds)")
    out["ablation"] = ablation(g)
    out["seconds"] = round(time.perf_counter() - t0, 1)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "metrics.json").write_text(json.dumps(out, indent=2))
    print("wrote", OUT / "metrics.json", f"({out['seconds']} s)")


if __name__ == "__main__":
    main()
