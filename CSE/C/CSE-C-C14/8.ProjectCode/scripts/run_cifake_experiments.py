"""Real-data evaluation of the four-branch ensemble (CIFAKE subset) -> experiments/cifake/metrics.json.

Run after scripts/prepare_cifake.py and the four training scripts (models/cifake/*.pt):

    .venv\\Scripts\\python.exe scripts\\run_cifake_experiments.py

Steps (branch logits are cached in experiments/cifake/logits.npz so analysis can be re-run quickly):
  1. clean held-out test (official CIFAKE test split subset): per-branch and ensemble metrics, ablations of the
     fusion rule and the two gates, threshold sweep, bootstrap intervals, calibration;
  2. robustness: JPEG q60, 2x down/up-sample, Gaussian blur, noise on a 1,000-image subset of the test set;
  3. cross-domain probe (data/xdomain): high-resolution photographs vs AI-generated images from other sources.
"""
import io
import json
import os
import sys
import time

import cv2
import numpy as np
import torch
from PIL import Image
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score, roc_curve)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from app import config, ensemble as ens  # noqa: E402
from app.models import BUILDERS  # noqa: E402
from scripts.common import collect_split, eval_transform, get_device  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "experiments", "cifake")
MODEL_DIR = os.path.join(BASE, "models", "cifake")
RES = {"a1": 224, "a2": 224, "b": 320, "c": 224}
FILES = {"a1": "efficientnet_a1.pt", "a2": "efficientnet_a2.pt", "b": "resnet50_b.pt", "c": "mobilenetv3_c.pt"}
BRANCHES = ["a1", "a2", "b", "c"]
ROBUST_N_PER_CLASS = 500
CONDITIONS = ["jpeg", "resize", "blur", "noise"]


# ----------------------------------------------------------------------------- degradations (same as scripts/evaluate.py)
def degrade(img, kind, seed):
    if kind == "jpeg":
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=60)
        buf.seek(0)
        return Image.open(buf).convert("RGB")
    if kind == "resize":
        w, h = img.size
        return img.resize((max(8, w // 2), max(8, h // 2)), Image.BILINEAR).resize((w, h), Image.BILINEAR)
    if kind == "blur":
        return Image.fromarray(cv2.GaussianBlur(np.array(img), (5, 5), 1.0))
    if kind == "noise":
        arr = np.array(img).astype(np.float32) + np.random.RandomState(seed).normal(0, 6, (*img.size[::-1], 3))
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return img


def load_models(device):
    models = {}
    for b in BRANCHES:
        m = BUILDERS[b]()
        st = torch.load(os.path.join(MODEL_DIR, FILES[b]), map_location=device)
        m.load_state_dict(st["state_dict"] if "state_dict" in st else st)
        models[b] = m.to(device).eval()
    return models


@torch.no_grad()
def branch_logits(models, samples, kind, device, bs=50):
    """samples: [(path, label)]. Returns {branch: (n,2)} and labels."""
    tfs = {b: eval_transform(RES[b]) for b in BRANCHES}
    out = {b: [] for b in BRANCHES}
    labels = []
    for s in range(0, len(samples), bs):
        chunk = samples[s:s + bs]
        imgs = []
        for i, (p, y) in enumerate(chunk):
            with Image.open(p) as im:
                img = im.convert("RGB")
            if kind != "clean":
                img = degrade(img, kind, seed=s + i)
            imgs.append(img)
            labels.append(y)
        for b in BRANCHES:
            x = torch.stack([tfs[b](im) for im in imgs]).to(device)
            o = models[b](x)
            if b == "b":
                o = (o + models[b](torch.flip(x, dims=[3]))) / 2.0
            out[b].append(o.cpu().numpy())
        print(f"  {kind}: {min(s + bs, len(samples))}/{len(samples)}", flush=True)
    return {b: np.concatenate(v) for b, v in out.items()}, np.array(labels)


# ----------------------------------------------------------------------------- metrics
def metrics(logits, labels, thr=0.5):
    p = torch.softmax(torch.tensor(logits, dtype=torch.float32), 1)[:, 1].numpy()
    pred = (p >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(labels, pred, labels=[0, 1]).ravel()
    return {
        "accuracy": float(accuracy_score(labels, pred)),
        "precision": float(precision_score(labels, pred, zero_division=0)),
        "recall": float(recall_score(labels, pred, zero_division=0)),
        "f1": float(f1_score(labels, pred, zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(labels, pred)),
        "roc_auc": float(roc_auc_score(labels, p)) if len(set(labels)) > 1 else None,
        "n_samples": int(len(labels)),
        "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
        "fpr": float(fp / max(fp + tn, 1)),
        "fnr": float(fn / max(fn + tp, 1)),
        "predicted_fake_rate": float(pred.mean()),
    }


def fuse_all(lg, variant="full", weights=None):
    """Fuse cached branch logits per sample with the deployed rule or an ablation. Returns (n,2) fused logits and gate stats."""
    w = dict(config.ENSEMBLE_WEIGHTS if weights is None else weights)
    n = len(lg["a1"])
    fused = np.zeros((n, 2))
    g1 = g2 = 0
    for i in range(n):
        per = {b: [float(lg[b][i][0]), float(lg[b][i][1])] for b in BRANCHES}
        if variant == "full":
            r = ens.ensemble_predict(per, weights=w)
            fused[i] = r["fused_logits"]
            g1 += r["excluded_branch"] is not None
            g2 += bool(r["gate2_applied"])
        elif variant == "no_gates":
            fused[i] = ens.fuse_logits(per, w)
        elif variant == "gate1_only":
            aw, ex, _ = ens.apply_gate1(per, w)
            fused[i] = ens.fuse_logits(per, aw)
        elif variant == "gate2_only":
            f0 = ens.fuse_logits(per, w)
            fused[i], _, _ = ens.apply_gate2(f0, per)
        elif variant == "equal_weights":
            r = ens.ensemble_predict(per, weights={b: 0.25 for b in BRANCHES})
            fused[i] = r["fused_logits"]
        elif variant == "prob_avg":
            nw = ens.normalize_weights(w)
            pr = sum(nw[b] * np.array(ens.softmax(per[b])) for b in BRANCHES)
            fused[i] = np.log(np.clip(pr, 1e-9, 1))
        elif variant == "majority":
            votes = sum(ens.branch_direction(per[b]) for b in BRANCHES)
            # tie (2-2) falls back to the weighted fusion so the vote always decides
            f0 = ens.fuse_logits(per, w)
            fused[i] = [0.0, 1.0] if votes > 2 else ([1.0, 0.0] if votes < 2 else f0)
    return fused, {"gate1_fired": int(g1), "gate2_fired": int(g2)}


def ece(prob_fake, labels, bins=15):
    conf = np.maximum(prob_fake, 1 - prob_fake)
    pred = (prob_fake >= 0.5).astype(int)
    acc = (pred == labels).astype(float)
    edges = np.linspace(0.5, 1.0, bins + 1)
    e = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            e += m.mean() * abs(acc[m].mean() - conf[m].mean())
    return float(e)


def bootstrap_ci(correct, n_boot=2000, seed=0):
    rng = np.random.RandomState(seed)
    idx = rng.randint(0, len(correct), (n_boot, len(correct)))
    accs = correct[idx].mean(1)
    return [float(np.percentile(accs, 2.5)), float(np.percentile(accs, 97.5))]


def analyse(lg, labels, tag):
    res = {"branches": {b: metrics(lg[b], labels) for b in BRANCHES}}
    variants = {}
    for v in ("full", "no_gates", "gate1_only", "gate2_only", "equal_weights", "prob_avg", "majority"):
        fused, gs = fuse_all(lg, v)
        m = metrics(fused, labels)
        if v == "full":
            m.update(gs)
            res["fused_logits_full"] = fused
        variants[v] = m
    res["ensemble_variants"] = variants
    res["ensemble"] = variants["full"]
    return res


def main():
    os.makedirs(OUT, exist_ok=True)
    device = get_device()
    torch.set_num_threads(6)
    models = load_models(device)
    cache = os.path.join(OUT, "logits.npz")
    store = dict(np.load(cache, allow_pickle=True)) if os.path.exists(cache) else {}

    def get(key, samples, kind):
        if f"{key}__labels" not in store:
            t0 = time.time()
            lg, y = branch_logits(models, samples, kind, device)
            for b in BRANCHES:
                store[f"{key}__{b}"] = lg[b]
            store[f"{key}__labels"] = y
            store[f"{key}__seconds"] = np.array(time.time() - t0)
            np.savez(cache, **store)
        return {b: store[f"{key}__{b}"] for b in BRANCHES}, store[f"{key}__labels"]

    test = collect_split(os.path.join(BASE, "data", "cifake"), "test")
    lg, y = get("clean", test, "clean")
    out = {"dataset": "CIFAKE subset (official test split, class-balanced)", "seed": 42, "n_test": int(len(y))}
    full = analyse(lg, y, "clean")
    fused = full.pop("fused_logits_full")
    pf = torch.softmax(torch.tensor(fused, dtype=torch.float32), 1)[:, 1].numpy()
    out["clean"] = full
    out["bootstrap_ci_accuracy"] = {b: bootstrap_ci((lg[b].argmax(1) == y).astype(float)) for b in BRANCHES}
    out["bootstrap_ci_accuracy"]["ensemble"] = bootstrap_ci(((pf >= 0.5).astype(int) == y).astype(float))
    out["ece_ensemble"] = ece(pf, y)
    out["ece_branches"] = {b: ece(torch.softmax(torch.tensor(lg[b], dtype=torch.float32), 1)[:, 1].numpy(), y) for b in BRANCHES}

    # threshold sweep on the fused fake probability
    sweep = []
    for t in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
        m = metrics(fused, y, thr=t)
        sweep.append({"threshold": t, **{k: m[k] for k in ("accuracy", "precision", "recall", "f1", "fpr", "fnr")}})
    out["threshold_sweep"] = sweep
    fpr, tpr, _ = roc_curve(y, pf)
    step = max(1, len(fpr) // 120)
    out["roc_curve"] = {"fpr": fpr[::step].tolist(), "tpr": tpr[::step].tolist()}
    # fused-logit margin vs correctness, for the failure analysis
    margin = fused[:, 1] - fused[:, 0]
    wrong = (np.argmax(fused, 1) != y)
    out["error_analysis"] = {
        "n_wrong": int(wrong.sum()),
        "false_positive_indices": np.where(wrong & (y == 0))[0][:12].tolist(),
        "false_negative_indices": np.where(wrong & (y == 1))[0][:12].tolist(),
        "mean_abs_margin_correct": float(np.abs(margin[~wrong]).mean()),
        "mean_abs_margin_wrong": float(np.abs(margin[wrong]).mean()) if wrong.any() else None,
        "test_paths": [p for p, _ in test],
    }
    # how often each branch disagrees with the final ensemble
    pred_e = np.argmax(fused, 1)
    out["branch_vs_ensemble_agreement"] = {b: float((lg[b].argmax(1) == pred_e).mean()) for b in BRANCHES}
    out["unanimous_rate"] = float(np.mean([len({int(lg[b][i].argmax()) for b in BRANCHES}) == 1 for i in range(len(y))]))
    out["inference_seconds_per_image_batched"] = float(store["clean__seconds"]) / len(y)

    # robustness subset
    sub = [s for s in test if s[1] == 0][:ROBUST_N_PER_CLASS] + [s for s in test if s[1] == 1][:ROBUST_N_PER_CLASS]
    rob = {}
    lgc, yc = get("robust_clean", sub, "clean")
    rob["clean_subset"] = {"ensemble": metrics(fuse_all(lgc, "full")[0], yc),
                           "branches": {b: metrics(lgc[b], yc) for b in BRANCHES}}
    for cond in CONDITIONS:
        lgd, yd = get(f"robust_{cond}", sub, cond)
        rob[cond] = {"ensemble": metrics(fuse_all(lgd, "full")[0], yd),
                     "branches": {b: metrics(lgd[b], yd) for b in BRANCHES}}
    out["robustness"] = rob
    out["robustness_n"] = int(len(yc))

    # cross-domain probe
    xs = collect_split(os.path.join(BASE, "data", "xdomain"), "test")
    if xs:
        lgx, yx = get("xdomain", xs, "clean")
        out["xdomain"] = {"ensemble": metrics(fuse_all(lgx, "full")[0], yx),
                          "branches": {b: metrics(lgx[b], yx) for b in BRANCHES},
                          "n": int(len(yx))}

    # training histories
    hist = {}
    for b in BRANCHES:
        hp = os.path.join(MODEL_DIR, FILES[b].replace(".pt", "_history.json"))
        if os.path.exists(hp):
            hist[b] = json.load(open(hp))
    out["histories"] = hist
    out["weights"] = config.ENSEMBLE_WEIGHTS
    out["gates"] = {"tau_b": config.GATE_TAU_B, "tau_c": config.GATE_TAU_C, "correction": config.GATE_CORRECTION}
    with open(os.path.join(OUT, "metrics.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    e = out["clean"]["ensemble"]
    print("ENSEMBLE acc=%.4f f1=%.4f auc=%.4f" % (e["accuracy"], e["f1"], e["roc_auc"]))
    for b in BRANCHES:
        m = out["clean"]["branches"][b]
        print(b, "acc=%.4f f1=%.4f auc=%.4f" % (m["accuracy"], m["f1"], m["roc_auc"]))


if __name__ == "__main__":
    main()
