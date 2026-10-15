"""Train PulmoVision models from the cached arrays (run ml/prepare_data.py first).

python ml/train.py xray      EfficientNet-B0, 5 X-ray classes
python ml/train.py ct        EfficientNet-B0, 4 CT classes
python ml/train.py unet      U-Net (MobileNetV2 encoder) lung segmentation
python ml/train.py modality  ImageNet EfficientNet-B0 embedding bank for the X-ray / CT / other check
Options: --epochs N  --device cuda
"""
import argparse
import json
import math
import os
import random
import time

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from sklearn.metrics import f1_score

from common import CACHE, CT_CLASSES, EXPERIMENTS, MODELS, SEED, XRAY_CLASSES, imaging
from app.services.nets import make_backbone, make_classifier, make_unet

torch.set_num_threads(os.cpu_count() or 4)


def seed_all():
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)


def load(name):
    return np.load(CACHE / f"{name}.npz")


def augment(img, rng):
    h, w = img.shape
    angle = rng.uniform(-8, 8)
    scale = rng.uniform(0.9, 1.1)
    m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, scale)
    m[:, 2] += rng.uniform(-0.05, 0.05, 2) * w
    out = cv2.warpAffine(img, m, (w, h), borderMode=cv2.BORDER_REFLECT)
    alpha, beta = rng.uniform(0.85, 1.15), rng.uniform(-15, 15)
    return np.clip(out.astype(np.float32) * alpha + beta, 0, 255).astype(np.uint8)


def batches(x, y, bs, train, rng):
    idx = np.arange(len(x))
    if train:
        rng.shuffle(idx)
    for i in range(0, len(idx), bs):
        b = idx[i:i + bs]
        imgs = [augment(x[j], rng) if train else x[j] for j in b]
        yield torch.from_numpy(np.stack([imaging.to_tensor_array(im) for im in imgs])), torch.from_numpy(y[b]).long()


@torch.no_grad()
def predict_logits(model, x, device, bs=64):
    model.eval()
    out = []
    for i in range(0, len(x), bs):
        xb = torch.from_numpy(np.stack([imaging.to_tensor_array(im) for im in x[i:i + bs]])).to(device)
        out.append(model(xb).float().cpu())
    return torch.cat(out)


def fit_temperature(logits, y):
    """Temperature scaling on the validation set (calibrated confidence)."""
    t = torch.zeros(1, requires_grad=True)
    opt = torch.optim.LBFGS([t], lr=0.1, max_iter=100)
    yt = torch.from_numpy(y).long()

    def closure():
        opt.zero_grad()
        loss = F.cross_entropy(logits / t.exp(), yt)
        loss.backward()
        return loss

    opt.step(closure)
    return float(t.exp().item())


def train_classifier(task, epochs, device):
    classes = XRAY_CLASSES if task == "xray" else CT_CLASSES
    tr, va = load(f"{task}_train"), load(f"{task}_val")
    xtr, ytr, xva, yva = tr["x"], tr["y"], va["x"], va["y"]
    model = make_classifier(len(classes), pretrained=True).to(device)
    for p in list(model.conv_stem.parameters()) + list(model.bn1.parameters()) + list(model.blocks[:2].parameters()):
        p.requires_grad = False  # freeze the earliest layers: faster CPU training, little accuracy cost
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=6e-4, weight_decay=1e-4)
    bs = 32
    steps = epochs * math.ceil(len(xtr) / bs)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=6e-4, total_steps=steps, pct_start=0.15)
    counts = np.bincount(ytr, minlength=len(classes))
    weights = torch.tensor(len(ytr) / (len(classes) * counts), dtype=torch.float32, device=device)
    rng = np.random.default_rng(SEED)
    best, best_state, history = -1, None, []
    for ep in range(epochs):
        model.train()
        t0, total, n = time.time(), 0.0, 0
        for xb, yb in batches(xtr, ytr, bs, True, rng):
            xb, yb = xb.to(device), yb.to(device)
            loss = F.cross_entropy(model(xb), yb, weight=weights, label_smoothing=0.1)
            opt.zero_grad()
            loss.backward()
            opt.step()
            sched.step()
            total += loss.item() * len(yb)
            n += len(yb)
        logits = predict_logits(model, xva, device)
        pred = logits.argmax(1).numpy()
        acc = float((pred == yva).mean())
        f1 = float(f1_score(yva, pred, average="macro"))
        history.append({"epoch": ep + 1, "loss": total / n, "val_acc": acc, "val_macro_f1": f1, "seconds": round(time.time() - t0, 1)})
        print(history[-1], flush=True)
        if f1 > best:
            best, best_state = f1, {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            MODELS.mkdir(exist_ok=True)  # save every improvement so an interrupted run keeps its best model
            torch.save({"state_dict": best_state, "classes": classes, "temperature": 1.0, "arch": "efficientnet_b0",
                        "input_size": imaging.CLS_SIZE, "partial": True}, MODELS / f"{task}_classifier.pt")
    model.load_state_dict(best_state)
    temperature = fit_temperature(predict_logits(model, xva, device), yva)
    MODELS.mkdir(exist_ok=True)
    torch.save({"state_dict": best_state, "classes": classes, "temperature": temperature,
                "arch": "efficientnet_b0", "input_size": imaging.CLS_SIZE}, MODELS / f"{task}_classifier.pt")
    (EXPERIMENTS / f"{task}_training.json").write_text(json.dumps({"history": history, "best_val_macro_f1": best, "temperature": temperature,
                                                                  "train_images": int(len(xtr)), "val_images": int(len(xva))}, indent=2))
    print(f"saved models/{task}_classifier.pt  best val macro-F1 {best:.3f}  T={temperature:.2f}")


def dice_loss(logits, target):
    p = torch.sigmoid(logits)
    inter = (p * target).sum((1, 2, 3))
    return 1 - ((2 * inter + 1) / (p.sum((1, 2, 3)) + target.sum((1, 2, 3)) + 1)).mean()


def train_unet(epochs, device):
    tr, va = load("seg_train"), load("seg_val")
    xtr, mtr = tr["x"].astype(np.float32), tr["m"].astype(np.float32)
    xva, mva = va["x"].astype(np.float32), va["m"].astype(np.float32)
    model = make_unet(pretrained=True).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    rng = np.random.default_rng(SEED)
    bs, best, best_state, history = 16, -1, None, []
    for ep in range(epochs):
        model.train()
        t0 = time.time()
        idx = rng.permutation(len(xtr))
        for i in range(0, len(idx), bs):
            b = idx[i:i + bs]
            xb = torch.from_numpy(xtr[b][:, None]).to(device)
            mb = torch.from_numpy(mtr[b][:, None]).to(device)
            if rng.random() < 0.5:  # brightness / contrast jitter
                xb = (xb * rng.uniform(0.85, 1.15) + rng.uniform(-0.06, 0.06)).clamp(0, 1)
            out = model(xb)
            loss = F.binary_cross_entropy_with_logits(out, mb) + dice_loss(out, mb)
            opt.zero_grad()
            loss.backward()
            opt.step()
        model.eval()
        dices = []
        with torch.no_grad():
            for i in range(0, len(xva), 32):
                p = (torch.sigmoid(model(torch.from_numpy(xva[i:i + 32][:, None]).to(device))) > 0.5).float().cpu().numpy()[:, 0]
                g = mva[i:i + 32]
                inter = (p * g).sum((1, 2))
                dices += list((2 * inter + 1e-6) / (p.sum((1, 2)) + g.sum((1, 2)) + 1e-6))
        d = float(np.mean(dices))
        history.append({"epoch": ep + 1, "val_dice": d, "seconds": round(time.time() - t0, 1)})
        print(history[-1], flush=True)
        if d > best:
            best, best_state = d, {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
    torch.save({"state_dict": best_state, "encoder": "mobilenet_v2", "input_size": imaging.SEG_SIZE}, MODELS / "lung_unet.pt")
    (EXPERIMENTS / "unet_training.json").write_text(json.dumps({"history": history, "best_val_dice": best}, indent=2))
    print(f"saved models/lung_unet.pt  best val Dice {best:.3f}")


@torch.no_grad()
def embed(model, x, device):
    e = predict_logits(model, x, device)
    return F.normalize(e, dim=1).numpy()


def train_modality(device):
    """Reference bank of ImageNet embeddings for X-ray and CT; the threshold is set on held-out images."""
    model = make_backbone(pretrained=True).to(device)
    xr = load("xray_train")["x"]
    ct = load("ct_train")["x"]
    bank = np.concatenate([embed(model, xr, device), embed(model, ct, device)])
    labels = np.array([0] * len(xr) + [1] * len(ct))
    xv, cv = load("xray_val")["x"], load("ct_val")["x"]
    sims = []
    for x in (xv, cv):
        s = embed(model, x, device) @ bank.T
        sims += list(np.sort(s, axis=1)[:, -5:].mean(1))
    # margin below the weakest held-out chest images; natural photos score far lower (~0.2-0.35)
    threshold = float(np.clip(np.percentile(sims, 0.5) - 0.1, 0.4, 0.6))
    torch.save(model.state_dict(), MODELS / "modality_backbone.pt")
    np.savez_compressed(MODELS / "modality_bank.npz", bank=bank.astype(np.float16), labels=labels, threshold=threshold)
    print(f"modality bank {bank.shape}, threshold {threshold:.3f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("task", choices=["xray", "ct", "unet", "modality"])
    ap.add_argument("--epochs", type=int, default=None)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    a = ap.parse_args()
    seed_all()
    EXPERIMENTS.mkdir(exist_ok=True)
    if a.task in ("xray", "ct"):
        train_classifier(a.task, a.epochs or (5 if a.task == "xray" else 10), a.device)
    elif a.task == "unet":
        train_unet(a.epochs or 4, a.device)
    else:
        train_modality(a.device)
