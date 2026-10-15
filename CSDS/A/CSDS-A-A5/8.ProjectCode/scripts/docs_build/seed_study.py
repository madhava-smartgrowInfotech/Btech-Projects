"""Re-run the whole pipeline (generate -> train JEPA -> analyse -> evaluate) on other generator seeds and
write experiments/seed_study.json, plus a risk-threshold sweep on the bundled seed-42 ecosystem.

Usage (from 8.ProjectCode):  venv\\Scripts\\python scripts\\docs_build\\seed_study.py
Nothing here changes the product; it only measures it on more ecosystems for the report.
"""
import json
import os
import shutil
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

import numpy as np  # noqa: E402

from ml.pipeline import run_pipeline  # noqa: E402
from scripts.generate_gst_data import generate  # noqa: E402

SEEDS = [1, 2, 3, 7, 11]
N = 600


def summarise(state):
    ev = state["evaluation"]
    k = str(ev["n_fraud"])
    m, b = ev["taxpayer"]["model"], ev["taxpayer"]["rule_baseline"]
    return dict(n_fraud=ev["n_fraud"], flagged=m["at_threshold"]["flagged"],
                p_at_k=m["precision_at_k"][k], r_at_k=m["recall_at_k"][k], precision=m["at_threshold"]["precision"],
                recall=m["at_threshold"]["recall"], f1=m["at_threshold"]["f1"], roc_auc=m["roc_auc"], ap=m["average_precision"],
                base_p_at_k=b["precision_at_k"][k], base_f1=b["at_threshold"]["f1"], base_roc_auc=b["roc_auc"],
                base_flagged=b["at_threshold"]["flagged"],
                invoice_f1=ev["invoice"]["model"]["at_threshold"]["f1"], rings_injected=ev["rings"]["injected"],
                rings_recovered=ev["rings"]["recovered"], seconds=state["stats"]["seconds"],
                per_pattern={r: v["model_recall"] for r, v in ev["per_pattern"].items()})


def run_one(seed):
    tmp = tempfile.mkdtemp(prefix="seedstudy_")
    try:
        t0 = time.time()
        d = os.path.join(tmp, f"s{seed}")
        generate(seed, N, d)
        st = run_pipeline(d, train=True, seed=seed, save_model_to=os.path.join(d, "jepa.pt"))
        res = summarise(st)
        with open(os.path.join(ROOT, "experiments", f"_seed_{seed}.json"), "w") as f:
            json.dump(res, f)
        print(seed, res["f1"], round(time.time() - t0, 1), "s", flush=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    out = {"n_taxpayers": N, "seeds": {}}
    for seed in SEEDS:
        with open(os.path.join(ROOT, "experiments", f"_seed_{seed}.json")) as f:
            out["seeds"][str(seed)] = json.load(f)
    keys = ["p_at_k", "precision", "recall", "f1", "roc_auc", "ap", "base_p_at_k", "base_f1", "base_roc_auc", "invoice_f1"]
    out["mean"] = {k: round(float(np.mean([v[k] for v in out["seeds"].values()])), 4) for k in keys}
    out["std"] = {k: round(float(np.std([v[k] for v in out["seeds"].values()])), 4) for k in keys}
    out["min"] = {k: round(float(np.min([v[k] for v in out["seeds"].values()])), 4) for k in keys}
    out["max"] = {k: round(float(np.max([v[k] for v in out["seeds"].values()])), 4) for k in keys}

    # threshold sweep on the bundled seed-42 ecosystem (state of the running app is the same deterministic result)
    base = os.path.join(ROOT, "data", "generated")
    st = run_pipeline(base, model_path=os.path.join(ROOT, "models", "jepa.pt"), train=False)
    risk = np.array([t["risk"] for t in st["taxpayers"]])
    y = np.array([t["label"]["is_fraud"] for t in st["taxpayers"]])
    sweep = []
    for th in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
        pred = risk >= th
        tp, fp, fn = int((pred & (y == 1)).sum()), int((pred & (y == 0)).sum()), int((~pred & (y == 1)).sum())
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        f = 2 * p * r / (p + r) if p + r else 0.0
        sweep.append(dict(threshold=th, flagged=int(pred.sum()), tp=tp, fp=fp, fn=fn, tn=int((~pred & (y == 0)).sum()),
                          precision=round(p, 4), recall=round(r, 4), f1=round(f, 4)))
    out["threshold_sweep_seed42"] = sweep
    out["risk_scores_seed42"] = dict(fraud=[round(float(v), 4) for v in risk[y == 1]], legit=[round(float(v), 4) for v in risk[y == 0]])
    # layer scores of fraud vs legit taxpayers (mean), seed 42
    out["layer_means_seed42"] = {
        layer: dict(fraud=round(float(np.mean([t[layer] for t in st["taxpayers"] if t["label"]["is_fraud"]])), 3),
                    legit=round(float(np.mean([t[layer] for t in st["taxpayers"] if not t["label"]["is_fraud"]])), 3))
        for layer in ("jepa", "behaviour", "network", "invoice")}

    # error analysis on seed 42: which taxpayers are false positives / false negatives at the 0.5 threshold
    errs = dict(false_positives=[], false_negatives=[])
    for t in st["taxpayers"]:
        fraud = bool(t["label"]["is_fraud"])
        if t["flagged"] and not fraud:
            errs["false_positives"].append(t)
        if fraud and not t["flagged"]:
            errs["false_negatives"].append(t)
    keep = ("gstin", "legal_name", "sector", "constitution", "registration_date", "risk", "jepa", "behaviour", "network", "invoice", "patterns", "rank", "cluster", "rings")
    out_err = {k: [dict({f: t[f] for f in keep}, roles=t["label"]["roles"]) for t in v] for k, v in errs.items()}
    # invoice level: false positives by flag combination
    from collections import Counter
    inv_fp = Counter(); inv_fn = Counter()
    for r in st["invoices"]:
        flagged = r["anomaly"] >= 0.5
        if flagged and not r["is_fraud"]:
            inv_fp[",".join(sorted(r["flags"]))] += 1
        if r["is_fraud"] and not flagged:
            inv_fn[",".join(sorted(r["flags"])) or "(no flags)"] += 1
    out_err["invoice_false_positive_flags"] = inv_fp.most_common(8)
    out_err["invoice_false_negative_flags"] = inv_fn.most_common(8)
    ring_info = [dict(id=r["id"], score=r["score"], size=len(r["nodes"]), with_fraud=any(st["taxpayers"][v]["label"]["is_fraud"] for v in r["nodes"])) for r in st["rings"]]
    out_err["rings"] = ring_info
    with open(os.path.join(ROOT, "experiments", "error_analysis.json"), "w") as f:
        json.dump(out_err, f, indent=1)
    with open(os.path.join(ROOT, "experiments", "seed_study.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("mean", out["mean"])
    print("std", out["std"])


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--seed":
        run_one(int(sys.argv[2]))
    else:
        main()
