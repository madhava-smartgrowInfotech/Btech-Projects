"""Brain-MRI training: JEPA pre-training (F1), few-label segmentation (F2) and label-efficiency runs (F3).

Stages (results are cached in experiments/mri_metrics.json, so the script can be re-run to resume):
  pretrain-jepa  I-JEPA style latent prediction on unlabelled slices (no masks used)
  pretrain-mae   reconstruction baseline (masked-autoencoder pixel prediction), same encoder and budget
  finetune       ViT + light decoder from {jepa, mae, scratch} and a U-Net baseline, at 10% and 100% of masks

Usage:  python ml/train_mri.py --stage all [--quick]
"""
import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from timm.models.vision_transformer import Block

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nets import (IMG_GRID, PATCH, MultiScalePredictor, UNet, ViTSeg, block_mask_2d, ema_copy, ema_update,  # noqa: E402
                  image_encoder, sincos_grid)

ROOT = Path(os.getenv("BIOSIGHT_ROOT", Path(__file__).resolve().parents[1]))
DATA = Path(os.getenv("LGG_NPZ", ROOT / "data" / "raw" / "lgg128.npz"))
MODELS = ROOT / "models"
EXP = ROOT / "experiments"
METRICS = EXP / "mri_metrics.json"
SEED = 42
DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_metrics():
    return json.loads(METRICS.read_text()) if METRICS.exists() else {"pretrain": {}, "finetune": {}}


def save_metrics(m):
    EXP.mkdir(exist_ok=True)
    METRICS.write_text(json.dumps(m, indent=2))


def load_data():
    d = np.load(DATA)
    X, Y, split = d["X"], d["Y"], d["split"]
    tr, te = np.where(split == "train")[0], np.where(split == "test")[0]
    # channel statistics in chunks (avoids a full float copy of the training set)
    s1, s2, n = np.zeros(3), np.zeros(3), 0
    for i in range(0, len(tr), 256):
        xf = X[tr[i:i + 256]].astype(np.float64) / 255.0
        s1 += xf.sum(axis=(0, 1, 2))
        s2 += (xf ** 2).sum(axis=(0, 1, 2))
        n += xf.shape[0] * xf.shape[1] * xf.shape[2]
    mean = s1 / n
    std = np.sqrt(s2 / n - mean ** 2)
    return X, Y, tr, te, {"mean": mean.tolist(), "std": std.tolist()}


def to_tensor(xb, norm):
    x = torch.from_numpy(xb).permute(0, 3, 1, 2).float() / 255.0
    m = torch.tensor(norm["mean"]).view(1, 3, 1, 1)
    s = torch.tensor(norm["std"]).view(1, 3, 1, 1)
    return ((x - m) / s).to(DEV)


def cosine_lr(step, total, base, warmup):
    if step < warmup:
        return base * (step + 1) / warmup
    return base * 0.5 * (1 + math.cos(math.pi * (step - warmup) / max(1, total - warmup)))


def batches(idx, bs, rng, drop_last=True):
    p = rng.permutation(idx)
    stop = len(p) - (len(p) % bs if drop_last else 0)
    for i in range(0, stop, bs):
        yield p[i:i + bs]


# ---------------------------------------------------------------- pre-training

def pretrain_jepa(X, tr, norm, epochs, bs):
    torch.manual_seed(SEED)
    rng = np.random.default_rng(SEED)
    gen = torch.Generator().manual_seed(SEED)
    enc = image_encoder().to(DEV)
    tgt = ema_copy(enc)
    pred = MultiScalePredictor(enc.dim, IMG_GRID, (2, 2)).to(DEV)
    params = list(enc.parameters()) + list(pred.parameters())
    opt = torch.optim.AdamW(params, lr=5e-4, weight_decay=0.04)
    steps_per_epoch = len(tr) // bs
    total = epochs * steps_per_epoch
    step, hist, start = 0, [], 0
    ck_path = MODELS / "_resume_jepa.pt"
    if ck_path.exists():
        ck = torch.load(ck_path, map_location="cpu")
        enc.load_state_dict(ck["enc"]); tgt.load_state_dict(ck["tgt"]); pred.load_state_dict(ck["pred"])
        opt.load_state_dict(ck["opt"])
        step, hist, start = ck["step"], ck["hist"], ck["epoch"]
        print(f"[jepa] resuming after epoch {start}", flush=True)
    t0 = time.time()
    for ep in range(start, epochs):
        losses = []
        for b in batches(tr, bs, rng):
            x = to_tensor(X[b], norm)
            if rng.random() < 0.5:
                x = x.flip(-1)
            ctx_idx, tgt_idx = (i.to(DEV) for i in block_mask_2d(IMG_GRID, gen))
            for g in opt.param_groups:
                g["lr"] = cosine_lr(step, total, 5e-4, steps_per_epoch)
            with torch.no_grad():
                h = tgt(x)
                h = F.layer_norm(h, (h.shape[-1],))[:, tgt_idx]
            z = enc(x, keep_idx=ctx_idx)
            p = pred(z, ctx_idx, tgt_idx)
            loss = F.smooth_l1_loss(p, h)
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 3.0)
            opt.step()
            ema_update(tgt, enc, 0.996 + (1.0 - 0.996) * step / total)
            losses.append(loss.item())
            step += 1
        with torch.no_grad():
            feat_std = tgt(to_tensor(X[tr[:64]], norm)).std(0).mean().item()
        hist.append({"epoch": ep + 1, "loss": float(np.mean(losses)), "target_feature_std": feat_std})
        print(f"[jepa] epoch {ep + 1}/{epochs} loss={hist[-1]['loss']:.4f} feat_std={feat_std:.3f} "
              f"({time.time() - t0:.0f}s)", flush=True)
        torch.save({"enc": enc.state_dict(), "tgt": tgt.state_dict(), "pred": pred.state_dict(),
                    "opt": opt.state_dict(), "step": step, "hist": hist, "epoch": ep + 1}, ck_path)
    # the EMA target encoder is the one kept for downstream use (as in I-JEPA)
    torch.save({"encoder": tgt.cpu().state_dict(), "norm": norm}, MODELS / "mri_jepa_encoder.pt")
    ck_path.unlink(missing_ok=True)
    return {"epochs": epochs, "history": hist, "seconds": round(time.time() - t0, 1)}


class MAEDecoder(nn.Module):
    def __init__(self, enc_dim, dim=96, depth=2, heads=4):
        super().__init__()
        self.inp = nn.Linear(enc_dim, dim)
        self.mask_token = nn.Parameter(torch.zeros(1, 1, dim))
        self.register_buffer("pos", sincos_grid(IMG_GRID, dim)[None], persistent=False)
        self.blocks = nn.ModuleList([Block(dim, heads, qkv_bias=True) for _ in range(depth)])
        self.out = nn.Sequential(nn.LayerNorm(dim), nn.Linear(dim, PATCH * PATCH * 3))
        nn.init.normal_(self.mask_token, std=0.02)

    def forward(self, z, vis_idx, n):
        b = z.shape[0]
        t = self.mask_token.expand(b, n, -1).clone()
        t[:, vis_idx] = self.inp(z)
        t = t + self.pos
        for blk in self.blocks:
            t = blk(t)
        return self.out(t)


def patchify(x):
    b, c, h, w = x.shape
    x = x.reshape(b, c, h // PATCH, PATCH, w // PATCH, PATCH).permute(0, 2, 4, 3, 5, 1)
    return x.reshape(b, (h // PATCH) * (w // PATCH), PATCH * PATCH * c)


def pretrain_mae(X, tr, norm, epochs, bs):
    torch.manual_seed(SEED)
    rng = np.random.default_rng(SEED + 1)
    enc = image_encoder().to(DEV)
    dec = MAEDecoder(enc.dim).to(DEV)
    params = list(enc.parameters()) + list(dec.parameters())
    opt = torch.optim.AdamW(params, lr=5e-4, weight_decay=0.05)
    n = IMG_GRID[0] * IMG_GRID[1]
    steps_per_epoch = len(tr) // bs
    total = epochs * steps_per_epoch
    step, hist, start = 0, [], 0
    ck_path = MODELS / "_resume_mae.pt"
    if ck_path.exists():
        ck = torch.load(ck_path, map_location="cpu")
        enc.load_state_dict(ck["enc"]); dec.load_state_dict(ck["dec"]); opt.load_state_dict(ck["opt"])
        step, hist, start = ck["step"], ck["hist"], ck["epoch"]
        print(f"[mae] resuming after epoch {start}", flush=True)
    t0 = time.time()
    for ep in range(start, epochs):
        losses = []
        for b in batches(tr, bs, rng):
            x = to_tensor(X[b], norm)
            if rng.random() < 0.5:
                x = x.flip(-1)
            perm = torch.from_numpy(rng.permutation(n)).to(DEV)
            vis_idx, mask_idx = perm[: n // 4].sort().values, perm[n // 4:].sort().values
            for g in opt.param_groups:
                g["lr"] = cosine_lr(step, total, 5e-4, steps_per_epoch)
            target = patchify(x)
            target = (target - target.mean(-1, keepdim=True)) / (target.var(-1, keepdim=True) + 1e-6).sqrt()
            out = dec(enc(x, keep_idx=vis_idx), vis_idx, n)
            loss = F.mse_loss(out[:, mask_idx], target[:, mask_idx])
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 3.0)
            opt.step()
            losses.append(loss.item())
            step += 1
        hist.append({"epoch": ep + 1, "loss": float(np.mean(losses))})
        print(f"[mae] epoch {ep + 1}/{epochs} loss={hist[-1]['loss']:.4f} ({time.time() - t0:.0f}s)", flush=True)
        torch.save({"enc": enc.state_dict(), "dec": dec.state_dict(), "opt": opt.state_dict(), "step": step,
                    "hist": hist, "epoch": ep + 1}, ck_path)
    torch.save({"encoder": enc.cpu().state_dict(), "norm": norm}, MODELS / "mri_mae_encoder.pt")
    ck_path.unlink(missing_ok=True)
    return {"epochs": epochs, "history": hist, "seconds": round(time.time() - t0, 1)}


# ---------------------------------------------------------------- segmentation

def dice_loss(logits, y):
    p = torch.sigmoid(logits)
    inter = (p * y).sum((1, 2, 3))
    return (1 - (2 * inter + 1) / (p.sum((1, 2, 3)) + y.sum((1, 2, 3)) + 1)).mean()


@torch.no_grad()
def evaluate(model, X, Y, idx, norm, bs=64):
    model.eval()
    tp = fp = fn = 0
    per_slice = []
    for i in range(0, len(idx), bs):
        b = idx[i:i + bs]
        pr = (torch.sigmoid(model(to_tensor(X[b], norm))) > 0.5).squeeze(1).cpu().numpy()
        gt = Y[b].astype(bool)
        tp += int((pr & gt).sum())
        fp += int((pr & ~gt).sum())
        fn += int((~pr & gt).sum())
        for p1, g1 in zip(pr, gt):
            if g1.any():
                per_slice.append(2 * (p1 & g1).sum() / (p1.sum() + g1.sum()))
    model.train()
    return {"dice": round(2 * tp / max(1, 2 * tp + fp + fn), 4), "iou": round(tp / max(1, tp + fp + fn), 4),
            "mean_dice_tumour_slices": round(float(np.mean(per_slice)), 4)}


def build_seg(kind):
    if kind == "unet":
        return UNet(), None
    model = ViTSeg(image_encoder())
    if kind in ("jepa", "mae"):
        ck = torch.load(MODELS / f"mri_{kind}_encoder.pt", map_location="cpu")
        model.encoder.load_state_dict(ck["encoder"])
    return model, model.encoder


def finetune(kind, frac, X, Y, tr, te, norm, steps, bs):
    torch.manual_seed(SEED)
    rng = np.random.default_rng(SEED)
    lab = np.random.default_rng(SEED).permutation(tr)[: max(bs, int(round(frac * len(tr))))]
    model, enc = build_seg(kind)
    model.to(DEV)
    if enc is not None:
        enc_params = list(enc.parameters())
        enc_ids = {id(p) for p in enc_params}
        rest = [p for p in model.parameters() if id(p) not in enc_ids]
        enc_lr = 2e-4 if kind in ("jepa", "mae") else 5e-4
        groups = [{"params": enc_params, "base": enc_lr}, {"params": rest, "base": 1e-3}]
    else:
        groups = [{"params": list(model.parameters()), "base": 1e-3}]
    opt = torch.optim.AdamW([{"params": g["params"], "lr": g["base"]} for g in groups], weight_decay=0.01)
    bases = [g["base"] for g in groups]
    t0 = time.time()
    step = 0
    model.train()
    while step < steps:
        for b in batches(lab, bs, rng):
            if step >= steps:
                break
            x = to_tensor(X[b], norm)
            y = torch.from_numpy(Y[b]).float().unsqueeze(1).to(DEV)
            if rng.random() < 0.5:
                x, y = x.flip(-1), y.flip(-1)
            for g, base in zip(opt.param_groups, bases):
                g["lr"] = cosine_lr(step, steps, base, max(1, steps // 20))
            logits = model(x)
            loss = F.binary_cross_entropy_with_logits(logits, y) + dice_loss(logits, y)
            opt.zero_grad()
            loss.backward()
            opt.step()
            step += 1
            if step % 100 == 0:
                print(f"[{kind}-{int(frac * 100)}%] step {step}/{steps} loss={loss.item():.4f} "
                      f"({time.time() - t0:.0f}s)", flush=True)
    res = evaluate(model, X, Y, te, norm)
    res.update({"labelled_slices": int(len(lab)), "steps": steps, "seconds": round(time.time() - t0, 1)})
    model.cpu()
    torch.save({"model": model.state_dict(), "kind": kind, "frac": frac, "norm": norm, "metrics": res},
               MODELS / f"mri_seg_{kind}_{int(frac * 100)}.pt")
    print(f"[{kind}-{int(frac * 100)}%] test {res}", flush=True)
    return res


def make_plots(m):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ft = m["finetune"]
    kinds = [k for k in ("jepa", "mae", "scratch", "unet") if f"{k}_10" in ft or f"{k}_100" in ft]
    labels = {"jepa": "ViT + JEPA pre-train", "mae": "ViT + MAE (reconstruction)", "scratch": "ViT from scratch",
              "unet": "U-Net (supervised)"}
    fig, ax = plt.subplots(figsize=(7, 4))
    w = 0.2
    for i, k in enumerate(kinds):
        vals = [ft.get(f"{k}_{p}", {}).get("dice", 0) for p in (10, 100)]
        ax.bar(np.arange(2) + i * w, vals, w, label=labels[k])
    ax.set_xticks(np.arange(2) + w * (len(kinds) - 1) / 2)
    ax.set_xticklabels(["10% of masks", "100% of masks"])
    ax.set_ylabel("Test Dice")
    ax.set_title("Label efficiency - brain MRI tumour segmentation")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(EXP / "mri_label_efficiency.png", dpi=120)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(6, 3.5))
    for k in ("jepa", "mae"):
        if k in m["pretrain"]:
            h = m["pretrain"][k]["history"]
            ax.plot([e["epoch"] for e in h], [e["loss"] for e in h], marker="o", label=k.upper())
    ax.set_xlabel("epoch")
    ax.set_ylabel("pre-training loss")
    ax.legend()
    fig.tight_layout()
    fig.savefig(EXP / "mri_pretrain_loss.png", dpi=120)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all", choices=["all", "pretrain-jepa", "pretrain-mae", "finetune", "plots"])
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--steps-full", type=int, default=500)
    ap.add_argument("--steps-few", type=int, default=300)
    ap.add_argument("--bs", type=int, default=32)
    ap.add_argument("--only", default="", help="comma list of finetune runs, e.g. jepa_10,unet_100")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--threads", type=int, default=0)
    a = ap.parse_args()
    if a.threads:
        torch.set_num_threads(a.threads)
    MODELS.mkdir(exist_ok=True)
    EXP.mkdir(exist_ok=True)
    X, Y, tr, te, norm = load_data()
    print(f"train slices={len(tr)} test slices={len(te)} threads={torch.get_num_threads()}", flush=True)
    m = load_metrics()
    m["data"] = {"train_slices": int(len(tr)), "test_slices": int(len(te)), "image_size": 128, "patch": PATCH}
    if a.stage in ("all", "pretrain-jepa") and (a.force or "jepa" not in m["pretrain"]):
        m["pretrain"]["jepa"] = pretrain_jepa(X, tr, norm, a.epochs, a.bs)
        save_metrics(m)
    if a.stage in ("all", "pretrain-mae") and (a.force or "mae" not in m["pretrain"]):
        m["pretrain"]["mae"] = pretrain_mae(X, tr, norm, a.epochs, a.bs)
        save_metrics(m)
    if a.stage in ("all", "finetune"):
        runs = [(k, 0.1) for k in ("jepa", "unet", "mae", "scratch")] + [(k, 1.0) for k in ("jepa", "unet", "mae", "scratch")]
        only = set(filter(None, a.only.split(",")))
        for kind, frac in runs:
            key = f"{kind}_{int(frac * 100)}"
            if (only and key not in only) or (key in m["finetune"] and not a.force):
                continue
            steps = a.steps_few if frac < 1 else a.steps_full
            m["finetune"][key] = finetune(kind, frac, X, Y, tr, te, norm, steps, a.bs)
            save_metrics(m)
    make_plots(m)
    save_metrics(m)


if __name__ == "__main__":
    main()
