"""Held-out evaluation: per-model metrics + ensemble + robustness + confusion matrix."""
import io
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from PIL import Image
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, confusion_matrix,
                             f1_score, precision_score, recall_score, roc_auc_score)
from torch.utils.data import DataLoader

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from app import config, ensemble as ens  # noqa: E402
from app.models import BUILDERS  # noqa: E402
from scripts.common import ImageFolderList, collect_split, eval_transform, get_device, set_seed  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRANCH_RES = {"a1": 224, "a2": 224, "b": 320, "c": 224}
CKPTS = {
    "efficientnet_a1": ("a1", os.path.join(BASE, "models", "efficientnet_a1.pt")),
    "efficientnet_a2": ("a2", os.path.join(BASE, "models", "efficientnet_a2.pt")),
    "resnet50_b": ("b", os.path.join(BASE, "models", "resnet50_b.pt")),
    "mobilenetv3_c": ("c", os.path.join(BASE, "models", "mobilenetv3_c.pt")),
}


def degrade_jpeg(pil_img, quality=60):
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def load_branch(branch, ckpt_path, device):
    model = BUILDERS[branch]()
    state = torch.load(ckpt_path, map_location=device)
    if isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]
    model.load_state_dict(state)
    model.to(device).eval()
    return model


@torch.no_grad()
def branch_logits_on_samples(model, samples, resolution, device, tta_flip=False, batch_size=32):
    from torchvision import transforms as T
    tf = eval_transform(resolution)
    ds = ImageFolderList(samples, transform=tf)
    loader = DataLoader(ds, batch_size=batch_size, shuffle=False)
    logits_all, labels_all = [], []
    for xb, yb in loader:
        xb = xb.to(device)
        out = model(xb)
        if tta_flip:
            out = (out + model(torch.flip(xb, dims=[3]))) / 2.0
        logits_all.extend(out.cpu().tolist())
        labels_all.extend(yb.tolist())
    return np.array(logits_all), np.array(labels_all)


def metrics_from_logits(logits, labels):
    preds = logits.argmax(1)
    probs_fake = torch.softmax(torch.tensor(logits), dim=1)[:, 1].numpy()
    out = {
        "accuracy": float(accuracy_score(labels, preds)),
        "precision": float(precision_score(labels, preds, zero_division=0)),
        "recall": float(recall_score(labels, preds, zero_division=0)),
        "f1": float(f1_score(labels, preds, zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(labels, preds)),
        "n_samples": int(len(labels)),
    }
    try:
        out["roc_auc"] = float(roc_auc_score(labels, probs_fake))
    except ValueError:
        out["roc_auc"] = 0.5
    out["confusion_matrix"] = confusion_matrix(labels, preds).tolist()
    return out, preds, probs_fake


def main():
    set_seed(config.RANDOM_SEED)
    device = get_device()
    data_root = os.path.join(BASE, "data")
    test_samples = collect_split(data_root, "test")
    if not test_samples:
        raise SystemExit("No test data found. Run scripts/prepare_dataset.py first.")
    print(f"Evaluating on {len(test_samples)} test images ({device})", flush=True)

    source = "cifake" if not os.path.exists(os.path.join(data_root, "FALLBACK_DATA_README.txt")) else "synthetic-demo-fallback"
    per_branch_logits, labels_ref = {}, None
    model_metrics = {}
    for display, (branch, ckpt) in CKPTS.items():
        model = load_branch(branch, ckpt, device)
        logits, labels = branch_logits_on_samples(
            model, test_samples, BRANCH_RES[branch], device, tta_flip=(branch == "b"))
        per_branch_logits[display] = logits
        labels_ref = labels
        m, _, _ = metrics_from_logits(logits, labels)
        m.update({"dataset": source, "seed": config.RANDOM_SEED, "resolution": BRANCH_RES[branch]})
        model_metrics[display] = m
        print(f"{display}: acc={m['accuracy']:.4f} f1={m['f1']:.4f} auc={m['roc_auc']:.4f}", flush=True)

    w = config.ENSEMBLE_WEIGHTS
    key_map = {"efficientnet_a1": "a1", "efficientnet_a2": "a2", "resnet50_b": "b", "mobilenetv3_c": "c"}
    fused = []
    for i in range(len(test_samples)):
        per = {short: [float(per_branch_logits[disp][i][0]), float(per_branch_logits[disp][i][1])]
               for disp, short in key_map.items()}
        r = ens.ensemble_predict(per, weights=w)
        fused.append(r["fused_logits"])
    fused = np.array(fused)
    em, epred, _ = metrics_from_logits(fused, labels_ref)
    em.update({"dataset": source, "seed": config.RANDOM_SEED})

    # Confusion matrix figure (ensemble)
    cm = np.array(em["confusion_matrix"])
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
    ax.set_xticklabels(["REAL", "AI_GENERATED"]); ax.set_yticklabels(["REAL", "AI_GENERATED"])
    ax.set_xlabel("Predicted"); ax.set_ylabel("True")
    ax.set_title("Ensemble Confusion Matrix (held-out test)", fontsize=11)
    for r in range(2):
        for c in range(2):
            ax.text(c, r, str(cm[r, c]), ha="center", va="center", fontsize=14,
                    color="white" if cm[r, c] > cm.max() / 2 else "black")
    fig.tight_layout()
    os.makedirs(config.METRICS_DIR, exist_ok=True)
    fig.savefig(os.path.join(config.METRICS_DIR, "confusion_matrix.png"), dpi=150)
    plt.close(fig)

    with open(os.path.join(config.METRICS_DIR, "model_metrics.json"), "w", encoding="utf-8") as fh:
        json.dump(model_metrics, fh, indent=2)
    with open(os.path.join(config.METRICS_DIR, "ensemble_metrics.json"), "w", encoding="utf-8") as fh:
        json.dump(em, fh, indent=2)

    # Robustness: degraded variants evaluated through branch models + fusion
    import cv2
    conditions = {}

    def variant_images(kind):
        out = []
        for path, label in test_samples:
            with Image.open(path) as im:
                img = im.convert("RGB")
            if kind == "jpeg":
                out.append((degrade_jpeg(img), label))
            elif kind == "resize":
                w, h = img.size
                small = img.resize((max(8, w // 2), max(8, h // 2)), Image.BILINEAR)
                out.append((small.resize((w, h), Image.BILINEAR), label))
            elif kind == "blur":
                arr = cv2.GaussianBlur(np.array(img), (5, 5), 1.0)
                out.append((Image.fromarray(arr), label))
            elif kind == "noise":
                arr = np.array(img).astype(np.float32) + np.random.RandomState(7).normal(0, 6, (*img.size[::-1], 3))
                out.append((Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)), label))
        return out

    # Save variants to temp files so the folder dataset can read them
    import tempfile
    robust = {"clean": {"accuracy": em["accuracy"], "f1": em["f1"], "n_samples": em["n_samples"]}}
    # Rebuild branch models for robustness variants
    branch_models = {}
    for disp, (br, ck) in CKPTS.items():
        branch_models[disp] = (load_branch(br, ck, device), br)
    for kind in ("jpeg", "resize", "blur", "noise"):
        var = variant_images(kind)
        with tempfile.TemporaryDirectory() as tmp:
            tmp_samples = []
            for i, (img, label) in enumerate(var):
                p = os.path.join(tmp, f"{i}.png")
                img.save(p)
                tmp_samples.append((p, label))
            per = {}
            for disp, (model, br) in branch_models.items():
                lg, lb = branch_logits_on_samples(model, tmp_samples, BRANCH_RES[br], device,
                                                  tta_flip=(br == "b"))
                per[disp] = lg
            fused_v = []
            for i in range(len(tmp_samples)):
                d = {short: [float(per[disp][i][0]), float(per[disp][i][1])]
                     for disp, short in key_map.items()}
                fused_v.append(ens.ensemble_predict(d, weights=w)["fused_logits"])
            m, _, _ = metrics_from_logits(np.array(fused_v), lb)
            robust[kind] = {"accuracy": m["accuracy"], "f1": m["f1"], "n_samples": m["n_samples"]}
            print(f"robustness {kind}: acc={m['accuracy']:.4f} f1={m['f1']:.4f}", flush=True)
    with open(os.path.join(config.METRICS_DIR, "robustness_metrics.json"), "w", encoding="utf-8") as fh:
        json.dump(robust, fh, indent=2)

    # Model metadata
    meta = []
    for disp, (br, ck) in CKPTS.items():
        meta.append({
            "model_name": disp,
            "branch": br,
            "training_dataset": source,
            "image_resolution": BRANCH_RES[br],
            "class_mapping": {"0": "REAL", "1": "AI_GENERATED"},
            "checkpoint_path": os.path.relpath(ck, BASE),
            "validation": {k: model_metrics[disp].get(k) for k in ("accuracy", "f1", "roc_auc")},
        })
    import datetime
    with open(os.path.join(BASE, "models", "model_metadata.json"), "w", encoding="utf-8") as fh:
        json.dump({"created": datetime.datetime.now().isoformat(timespec="seconds"), "models": meta}, fh, indent=2)
    print("Evaluation artifacts written.", flush=True)


if __name__ == "__main__":
    main()
