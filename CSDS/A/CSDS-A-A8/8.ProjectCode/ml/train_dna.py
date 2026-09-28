"""DNA encoder (F4): k-mer tokens + JEPA latent prediction of masked k-mer spans, then classification.

Baselines: masked-token (MLM) reconstruction pre-training with the same encoder, and training from scratch.
Tasks:
  repeat    STR repeat type of a 100 bp read (none / di / tri / tetra / penta) - data/dna/repeat_sequences.csv
  organism  class label of the Kaggle DNA classification dataset - data/dna/synthetic_dna_dataset.csv

Usage:  python ml/train_dna.py
"""
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nets import (DNA_GRID, DNA_TOKENS, MASK_ID, MultiScalePredictor, SeqClassifier, dna_encoder,  # noqa: E402
                  ema_copy, ema_update, kmer_tokens, span_mask_1d)

ROOT = Path(__file__).resolve().parents[1]
DNA = ROOT / "data" / "dna"
MODELS = ROOT / "models"
EXP = ROOT / "experiments"
SEED = 42
REPEAT_LABELS = ["none", "dinucleotide", "trinucleotide", "tetranucleotide", "pentanucleotide"]


def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def split(n, rng, test=0.2):
    p = rng.permutation(n)
    k = int(round(test * n))
    return p[k:], p[:k]


def load_tasks():
    rng = np.random.default_rng(SEED)
    rep = read_csv(DNA / "repeat_sequences.csv")
    org = read_csv(DNA / "synthetic_dna_dataset.csv")
    org_labels = sorted({r["Class_Label"] for r in org})
    tasks = {}
    for name, rows, seq_key, lab_key, labels in (("repeat", rep, "sequence", "label", REPEAT_LABELS),
                                                 ("organism", org, "Sequence", "Class_Label", org_labels)):
        X = torch.tensor([kmer_tokens(r[seq_key]) for r in rows])
        y = torch.tensor([labels.index(r[lab_key]) for r in rows])
        tr, te = split(len(rows), rng)
        tasks[name] = {"X": X, "y": y, "tr": tr, "te": te, "labels": labels}
    return tasks


def pretrain(kind, pool, epochs=15, bs=64):
    torch.manual_seed(SEED)
    rng = np.random.default_rng(SEED)
    gen = torch.Generator().manual_seed(SEED)
    enc = dna_encoder()
    if kind == "jepa":
        tgt = ema_copy(enc)
        pred = MultiScalePredictor(enc.dim, DNA_GRID, (1, 4), dim=96, depth=2)
        extra = pred
    else:
        extra = nn.Linear(enc.dim, 4 ** 4)
    params = list(enc.parameters()) + list(extra.parameters())
    opt = torch.optim.AdamW(params, lr=5e-4, weight_decay=0.04)
    steps = epochs * (len(pool) // bs)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=5e-4, total_steps=steps, pct_start=0.05)
    step, hist, t0 = 0, [], time.time()
    for ep in range(epochs):
        losses = []
        perm = rng.permutation(len(pool))
        for i in range(0, len(perm) - bs + 1, bs):
            x = pool[perm[i:i + bs]]
            ctx_idx, tgt_idx = span_mask_1d(DNA_TOKENS, gen)
            if kind == "jepa":
                with torch.no_grad():
                    h = tgt(x)
                    h = F.layer_norm(h, (h.shape[-1],))[:, tgt_idx]
                p = pred(enc(x, keep_idx=ctx_idx), ctx_idx, tgt_idx)
                loss = F.smooth_l1_loss(p, h)
            else:
                xm = x.clone()
                xm[:, tgt_idx] = MASK_ID
                logits = extra(enc(xm))[:, tgt_idx]
                labels = x[:, tgt_idx]
                keep = labels < 4 ** 4
                loss = F.cross_entropy(logits[keep], labels[keep])
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 3.0)
            opt.step()
            sched.step()
            if kind == "jepa":
                ema_update(tgt, enc, 0.996 + 0.004 * step / steps)
            losses.append(loss.item())
            step += 1
        hist.append({"epoch": ep + 1, "loss": float(np.mean(losses))})
        if (ep + 1) % 5 == 0:
            print(f"[dna-{kind}] epoch {ep + 1}/{epochs} loss={hist[-1]['loss']:.4f} ({time.time() - t0:.0f}s)",
                  flush=True)
    keep_enc = tgt if kind == "jepa" else enc
    torch.save({"encoder": keep_enc.state_dict()}, MODELS / f"dna_{kind}_encoder.pt")
    return {"epochs": epochs, "history": hist, "seconds": round(time.time() - t0, 1)}


def macro_f1(y, p, k):
    f1s = []
    for c in range(k):
        tp = int(((p == c) & (y == c)).sum())
        fp = int(((p == c) & (y != c)).sum())
        fn = int(((p != c) & (y == c)).sum())
        f1s.append(2 * tp / max(1, 2 * tp + fp + fn))
    return float(np.mean(f1s))


def finetune(task, name, init, frac, steps, probe=False, bs=64):
    torch.manual_seed(SEED)
    rng = np.random.default_rng(SEED)
    X, y, tr, te, labels = task["X"], task["y"], task["tr"], task["te"], task["labels"]
    lab = np.random.default_rng(SEED).permutation(tr)[: max(bs, int(round(frac * len(tr))))]
    model = SeqClassifier(dna_encoder(), len(labels))
    if init != "scratch":
        model.encoder.load_state_dict(torch.load(MODELS / f"dna_{init}_encoder.pt", map_location="cpu")["encoder"])
    if probe:
        for p in model.encoder.parameters():
            p.requires_grad_(False)
        opt = torch.optim.AdamW(model.head.parameters(), lr=3e-3, weight_decay=0.01)
    else:
        enc_lr = 5e-4 if init == "scratch" else 2e-4
        opt = torch.optim.AdamW([{"params": model.encoder.parameters(), "lr": enc_lr},
                                 {"params": model.head.parameters(), "lr": 2e-3}], weight_decay=0.01)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=[g["lr"] for g in opt.param_groups],
                                                total_steps=steps, pct_start=0.05)
    t0, step = time.time(), 0
    model.train()
    while step < steps:
        perm = rng.permutation(lab)
        for i in range(0, len(perm) - bs + 1, bs):
            if step >= steps:
                break
            b = perm[i:i + bs]
            loss = F.cross_entropy(model(X[b]), y[b])
            opt.zero_grad()
            loss.backward()
            opt.step()
            sched.step()
            step += 1
    model.eval()
    with torch.no_grad():
        pred = model(X[te]).argmax(1).numpy()
    yt = y[te].numpy()
    k = len(labels)
    cm = np.zeros((k, k), dtype=int)
    for a, b in zip(yt, pred):
        cm[a, b] += 1
    res = {"accuracy": round(float((pred == yt).mean()), 4), "macro_f1": round(macro_f1(yt, pred, k), 4),
           "labelled_sequences": int(len(lab)), "steps": steps, "seconds": round(time.time() - t0, 1),
           "chance_accuracy": round(1.0 / k, 4), "confusion": cm.tolist(), "labels": labels}
    print(f"[{name}] {res['accuracy']=} {res['macro_f1']=}", flush=True)
    return model, res


def main():
    torch.set_num_threads(int(sys.argv[1]) if len(sys.argv) > 1 else torch.get_num_threads())
    MODELS.mkdir(exist_ok=True)
    EXP.mkdir(exist_ok=True)
    tasks = load_tasks()
    pool = torch.cat([tasks[t]["X"][tasks[t]["tr"]] for t in tasks])
    out = {"pretrain": {}, "repeat": {}, "organism": {}, "pretrain_sequences": int(len(pool))}
    for kind in ("jepa", "mlm"):
        out["pretrain"][kind] = pretrain(kind, pool)
    for frac, steps in ((0.1, 300), (1.0, 600)):
        pct = int(frac * 100)
        for init in ("jepa", "mlm", "scratch"):
            model, res = finetune(tasks["repeat"], f"repeat-{init}-{pct}", init, frac, steps)
            out["repeat"][f"{init}_{pct}"] = res
            if init == "jepa" and pct == 100:
                torch.save({"model": model.state_dict(), "labels": REPEAT_LABELS, "metrics": res},
                           MODELS / "dna_repeat_classifier.pt")
    _, out["repeat"]["jepa_probe_100"] = finetune(tasks["repeat"], "repeat-jepa-linear-probe", "jepa", 1.0, 600,
                                                  probe=True)
    for init in ("jepa", "mlm", "scratch"):
        model, res = finetune(tasks["organism"], f"organism-{init}-100", init, 1.0, 600)
        out["organism"][f"{init}_100"] = res
        if init == "jepa":
            torch.save({"model": model.state_dict(), "labels": tasks["organism"]["labels"], "metrics": res},
                       MODELS / "dna_organism_classifier.pt")
    (EXP / "dna_metrics.json").write_text(json.dumps(out, indent=2))
    print("saved experiments/dna_metrics.json")


if __name__ == "__main__":
    main()
