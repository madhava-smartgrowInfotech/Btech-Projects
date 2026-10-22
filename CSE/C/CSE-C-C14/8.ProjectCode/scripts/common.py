"""Shared training utilities: seeds, data loading, augmentation, training loop."""
import copy
import json
import math
import os
import random

import numpy as np
import torch
import torch.nn as nn
from PIL import Image, ImageEnhance, ImageFilter
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

SEED_DEFAULT = 42


def set_seed(seed=SEED_DEFAULT):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    try:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    except Exception:
        pass


def get_device():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


class JpegCompress:
    """Simulate JPEG compression artifacts at training time."""

    def __init__(self, quality_range=(40, 90), p=0.5):
        self.quality_range = quality_range
        self.p = p

    def __call__(self, img):
        import io
        if random.random() > self.p:
            return img
        q = random.randint(*self.quality_range)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=q)
        buf.seek(0)
        return Image.open(buf).convert("RGB")


class AddGaussianNoise:
    def __init__(self, std_range=(3.0, 12.0), p=0.4):
        self.std_range = std_range
        self.p = p

    def __call__(self, img):
        if random.random() > self.p:
            return img
        arr = np.array(img).astype(np.float32)
        std = random.uniform(*self.std_range)
        arr = arr + np.random.normal(0, std, arr.shape)
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


class DownUpSample:
    """Downsample then upsample to simulate resizing distortion."""

    def __init__(self, scale_range=(0.4, 0.8), p=0.4):
        self.scale_range = scale_range
        self.p = p

    def __call__(self, img):
        if random.random() > self.p:
            return img
        w, h = img.size
        s = random.uniform(*self.scale_range)
        small = img.resize((max(8, int(w * s)), max(8, int(h * s))), Image.BILINEAR)
        return small.resize((w, h), Image.BILINEAR)


class ImageFolderList(Dataset):
    """Minimal image-folder dataset returning (tensor, label)."""

    def __init__(self, samples, transform=None):
        self.samples = samples
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        with Image.open(path) as im:
            img = im.convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, label


def collect_split(data_root, split):
    """Collect [(path, label)] for data/<split>/{real,fake} with label 0/1."""
    out = []
    for cls_name, label in (("real", 0), ("fake", 1)):
        folder = os.path.join(data_root, split, cls_name)
        if not os.path.isdir(folder):
            continue
        for fname in sorted(os.listdir(folder)):
            if fname.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp")):
                out.append((os.path.join(folder, fname), label))
    return out


def imagenet_norm():
    return [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]


def train_transform(route, resolution):
    mean, std = imagenet_norm()
    if route == "a1":
        return transforms.Compose([
            transforms.RandomResizedCrop(resolution, scale=(0.8, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.1),
            transforms.ToTensor(),
            transforms.Normalize(mean=mean, std=std),
        ])
    if route == "a2":
        return transforms.Compose([
            transforms.RandomResizedCrop(resolution, scale=(0.6, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(12),
            transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2, hue=0.05),
            transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 1.5)),
            AddGaussianNoise(),
            JpegCompress(),
            DownUpSample(),
            transforms.ToTensor(),
            transforms.Normalize(mean=mean, std=std),
        ])
    # routes b and c: moderate distortion hardening
    return transforms.Compose([
        transforms.RandomResizedCrop(resolution, scale=(0.75, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(8),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.15),
        transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 1.2)),
        JpegCompress(quality_range=(50, 95), p=0.35),
        transforms.ToTensor(),
        transforms.Normalize(mean=mean, std=std),
    ])


def eval_transform(resolution):
    mean, std = imagenet_norm()
    return transforms.Compose([
        transforms.Resize((resolution, resolution)),
        transforms.ToTensor(),
        transforms.Normalize(mean=mean, std=std),
    ])


class FocalLoss(nn.Module):
    def __init__(self, gamma=2.0, weight=None):
        super().__init__()
        self.gamma = gamma
        self.ce = nn.CrossEntropyLoss(weight=weight, reduction="none")

    def forward(self, logits, targets):
        ce = self.ce(logits, targets)
        pt = torch.exp(-ce)
        return ((1 - pt) ** self.gamma * ce).mean()


def train_one_model(model, train_samples, val_samples, route, resolution,
                    out_path, epochs=8, batch_size=32, lr=3e-4, use_focal=False,
                    patience=3, num_workers=0, seed=SEED_DEFAULT):
    """Train with early stopping on validation F1. Returns history dict."""
    from sklearn.metrics import f1_score
    set_seed(seed)
    device = get_device()
    model.to(device)
    train_ds = ImageFolderList(train_samples, transform=train_transform(route, resolution))
    val_ds = ImageFolderList(val_samples, transform=eval_transform(resolution))
    pin = device.type == "cuda"
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True,
                              num_workers=num_workers, pin_memory=pin)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False,
                            num_workers=num_workers, pin_memory=pin)
    criterion = FocalLoss(gamma=2.0) if use_focal else nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(epochs, 1))

    best_f1 = -1.0
    best_state = None
    bad_epochs = 0
    history = {"train_loss": [], "val_loss": [], "val_f1": [], "val_acc": []}

    for epoch in range(epochs):
        model.train()
        running = 0.0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()
            running += loss.item() * xb.size(0)
        train_loss = running / max(len(train_loader.dataset), 1)

        model.eval()
        val_loss_sum = 0.0
        all_pred, all_true = [], []
        with torch.no_grad():
            for xb, yb in val_loader:
                xb, yb = xb.to(device), yb.to(device)
                out = model(xb)
                val_loss_sum += nn.CrossEntropyLoss()(out, yb).item() * xb.size(0)
                all_pred.extend(out.argmax(1).cpu().tolist())
                all_true.extend(yb.cpu().tolist())
        val_loss = val_loss_sum / max(len(val_loader.dataset), 1)
        val_f1 = float(f1_score(all_true, all_pred, zero_division=0)) if all_true else 0.0
        val_acc = float(np.mean(np.array(all_pred) == np.array(all_true))) if all_true else 0.0
        scheduler.step()

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["val_f1"].append(val_f1)
        history["val_acc"].append(val_acc)
        print(f"epoch {epoch+1}/{epochs} train_loss={train_loss:.4f} val_loss={val_loss:.4f} "
              f"val_acc={val_acc:.4f} val_f1={val_f1:.4f}", flush=True)

        if val_f1 > best_f1 + 1e-4:
            best_f1 = val_f1
            best_state = copy.deepcopy(model.state_dict())
            bad_epochs = 0
        else:
            bad_epochs += 1
            if bad_epochs >= patience:
                print(f"Early stopping at epoch {epoch+1} (best val F1 {best_f1:.4f})", flush=True)
                break

    if best_state is not None:
        model.load_state_dict(best_state)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "best_val_f1": best_f1,
                "history": history, "route": route, "resolution": resolution}, out_path)
    # Also save a plain state_dict file for the app loader (same path holds dict wrapper;
    # loader handles both). Additionally write history alongside.
    hist_path = os.path.splitext(out_path)[0] + "_history.json"
    with open(hist_path, "w", encoding="utf-8") as fh:
        json.dump(history, fh, indent=2)
    return history
