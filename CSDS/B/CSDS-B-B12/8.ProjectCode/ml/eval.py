"""Evaluate every model on held-out test data -> experiments/eval/metrics.json + confusion matrix plots.

python ml/eval.py
Uses the cached test arrays from ml/prepare_data.py. If they are missing (fresh clone without the
full datasets), it falls back to the committed data: the CT test split and data/sample/.
"""
import datetime
import json
import os
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402
import torch.nn.functional as F  # noqa: E402
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support  # noqa: E402

from common import CACHE, CT_CLASSES, EXPERIMENTS, MODELS, ROOT, XRAY_CLASSES, imaging  # noqa: E402
from app.services.nets import make_backbone, make_classifier, make_unet  # noqa: E402

OUT = EXPERIMENTS / "eval"
torch.set_num_threads(os.cpu_count() or 4)


def load_cache(name):
    p = CACHE / f"{name}.npz"
    return np.load(p) if p.exists() else None


def load_folder(folder, classes, dir_to_label):
    xs, ys = [], []
    for d in sorted(os.listdir(folder)):
        label = dir_to_label(d)
        for f in sorted(os.listdir(os.path.join(folder, d))):
            with open(os.path.join(folder, d, f), "rb") as fh:
                gray, _, _ = imaging.load_image(fh.read(), f)
            xs.append(imaging.preprocess(gray)["enhanced"])
            ys.append(label)
    return {"x": np.stack(xs), "y": np.array(ys)}


@torch.no_grad()
def logits_for(model, x, bs=64):
    out = []
    for i in range(0, len(x), bs):
        out.append(model(torch.from_numpy(np.stack([imaging.to_tensor_array(im) for im in x[i:i + bs]]))))
    return torch.cat(out)


def plot_cm(cm, classes, title, path):
    fig, ax = plt.subplots(figsize=(6.2, 5.2))
    norm = cm / cm.sum(1, keepdims=True).clip(min=1)
    ax.imshow(norm, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(classes)), classes, rotation=35, ha="right", fontsize=8)
    ax.set_yticks(range(len(classes)), classes, fontsize=8)
    for i in range(len(classes)):
        for j in range(len(classes)):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=9, color="white" if norm[i, j] > 0.5 else "black")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def eval_classifier(task, classes, data, source):
    ckpt = torch.load(MODELS / f"{task}_classifier.pt", map_location="cpu")
    model = make_classifier(len(classes))
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    logits = logits_for(model, data["x"])
    probs = torch.softmax(logits / ckpt["temperature"], 1).numpy()
    y, pred = data["y"], probs.argmax(1)
    p, r, f1, s = precision_recall_fscore_support(y, pred, labels=range(len(classes)), zero_division=0)
    cm = confusion_matrix(y, pred, labels=range(len(classes)))
    plot_cm(cm, classes, f"{task.upper()} classifier - test set", OUT / f"confusion_{task}.png")
    conf = probs.max(1)
    bins = np.linspace(0, 1, 11)
    ece = sum(abs((pred[m] == y[m]).mean() - conf[m].mean()) * m.mean()
              for lo, hi in zip(bins[:-1], bins[1:]) if (m := (conf > lo) & (conf <= hi)).any())
    return {
        "source": source, "test_images": int(len(y)), "accuracy": float(accuracy_score(y, pred)),
        "macro_f1": float(f1_score(y, pred, average="macro")), "expected_calibration_error": float(ece),
        "per_class": {c: {"sensitivity": float(r[i]), "precision": float(p[i]), "f1": float(f1[i]), "support": int(s[i])} for i, c in enumerate(classes)},
        "confusion_matrix": cm.tolist(), "classes": classes,
    }


@torch.no_grad()
def eval_segmentation():
    data = load_cache("seg_test")
    source = "COVID-19 Radiography Database masks (cached test split)"
    if data is None:  # committed sample
        base = ROOT / "data" / "sample" / "lung_masks"
        import cv2

        xs, ms = [], []
        for f in sorted(os.listdir(base / "images")):
            with open(base / "images" / f, "rb") as fh:
                gray, _, _ = imaging.load_image(fh.read(), f)
            xs.append(imaging.to_seg_array(gray)[0])
            m = cv2.imread(str(base / "masks" / f), cv2.IMREAD_GRAYSCALE)
            ms.append(cv2.resize(m, (imaging.SEG_SIZE, imaging.SEG_SIZE), interpolation=cv2.INTER_NEAREST) > 127)
        data, source = {"x": np.stack(xs), "m": np.stack(ms)}, "data/sample/lung_masks"
    ckpt = torch.load(MODELS / "lung_unet.pt", map_location="cpu")
    model = make_unet()
    model.load_state_dict(ckpt["state_dict"])
    model.eval()
    x, m = data["x"].astype(np.float32), data["m"].astype(bool)
    dice, iou = [], []
    for i in range(0, len(x), 32):
        p = (torch.sigmoid(model(torch.from_numpy(x[i:i + 32][:, None]))) > 0.5).numpy()[:, 0]
        g = m[i:i + 32]
        inter = (p & g).sum((1, 2))
        union = (p | g).sum((1, 2))
        dice += list(2 * inter / (p.sum((1, 2)) + g.sum((1, 2)) + 1e-6))
        iou += list(inter / (union + 1e-6))
    return {"source": source, "test_images": int(len(x)), "dice": float(np.mean(dice)), "iou": float(np.mean(iou)),
            "dice_std": float(np.std(dice))}


@torch.no_grad()
def eval_modality(xray, ct):
    """Route chest images to the right model and reject non-chest images (same logic as the API)."""
    from sklearn.datasets import load_sample_images

    bank = np.load(MODELS / "modality_bank.npz")
    emb_bank = torch.from_numpy(bank["bank"].astype(np.float32))
    labels, threshold = bank["labels"], float(bank["threshold"])
    model = make_backbone()
    model.load_state_dict(torch.load(MODELS / "modality_backbone.pt", map_location="cpu"))
    model.eval()

    def decide(x):
        e = F.normalize(logits_for(model, x), dim=1)
        sims = (e @ emb_bank.T).numpy()
        sx = np.sort(sims[:, labels == 0], 1)[:, -5:].mean(1)
        sc = np.sort(sims[:, labels == 1], 1)[:, -5:].mean(1)
        route = (sc > sx).astype(int)
        accepted = np.maximum(sx, sc) >= threshold
        return route, accepted

    # non-chest set: crops / rotations / grey versions of scikit-learn's two bundled photographs
    rng = np.random.default_rng(0)
    others = []
    for img in load_sample_images().images:
        grey = np.array(np.dot(img[..., :3], [0.299, 0.587, 0.114]), dtype=np.uint8)
        for _ in range(20):
            h, w = grey.shape
            s = int(rng.integers(160, min(h, w)))
            y0, x0 = int(rng.integers(0, h - s)), int(rng.integers(0, w - s))
            crop = np.rot90(grey[y0:y0 + s, x0:x0 + s], int(rng.integers(0, 4)))
            others.append(imaging.preprocess(np.ascontiguousarray(crop))["enhanced"])
    others = np.stack(others)
    rx, ax = decide(xray["x"][:300])
    rc, ac = decide(ct["x"])
    _, ao = decide(others)
    routed = np.concatenate([rx == 0, rc == 1])
    accepted = np.concatenate([ax, ac])
    return {"test_images": int(len(routed) + len(others)), "routing_accuracy": float(routed.mean()),
            "chest_accept_rate": float(accepted.mean()), "other_reject_rate": float((~ao).mean()),
            "other_images": int(len(others)), "threshold": threshold,
            "note": "Non-chest set = 40 grey crops of two bundled photographs; colour images are also rejected by a saturation check before this step."}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    xray = load_cache("xray_test")
    xray_src = "COVID-19 Radiography DB + TB Chest X-ray DB (held-out test split)"
    if xray is None:
        xray = load_folder(ROOT / "data" / "sample" / "xray", XRAY_CLASSES,
                           lambda d: [c.replace(" ", "_").replace("-", "") for c in XRAY_CLASSES].index(d))
        xray_src = "data/sample/xray (small committed sample)"
    ct = load_cache("ct_test")
    ct_src = "Chest CT-Scan Images, published test split (duplicates of train/valid removed)"
    if ct is None:
        from prepare_data import CT_DIRS

        ct = load_folder(ROOT / "data" / "chest_ct" / "test", CT_CLASSES, lambda d: next(v for k, v in CT_DIRS.items() if d.startswith(k)))
        ct_src = "data/chest_ct/test (full published test split)"
    metrics = {
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "segmentation": eval_segmentation(),
        "xray": eval_classifier("xray", XRAY_CLASSES, xray, xray_src),
        "ct": eval_classifier("ct", CT_CLASSES, ct, ct_src),
        "modality": eval_modality(xray, ct),
        "notes": [
            "All models were trained with a small CPU configuration (balanced subsets, 224 px, a few epochs); see experiments/*_training.json.",
            "Confidence is temperature-scaled on the validation split; expected calibration error is reported per classifier.",
            "The CT dataset contains many near-duplicate slices; exact duplicates across splits were removed before evaluation.",
        ],
    }
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2))
    s, x, c, m = metrics["segmentation"], metrics["xray"], metrics["ct"], metrics["modality"]
    print(f"Segmentation  Dice {s['dice']:.3f}  IoU {s['iou']:.3f}  (n={s['test_images']})")
    print(f"X-ray         acc {x['accuracy']:.3f}  macro-F1 {x['macro_f1']:.3f}  (n={x['test_images']})")
    print(f"CT            acc {c['accuracy']:.3f}  macro-F1 {c['macro_f1']:.3f}  (n={c['test_images']})")
    print(f"Modality      routing {m['routing_accuracy']:.3f}  chest accepted {m['chest_accept_rate']:.3f}  other rejected {m['other_reject_rate']:.3f}")
    for task in ("xray", "ct"):
        print(task, {k: round(v["sensitivity"], 3) for k, v in metrics[task]["per_class"].items()})


if __name__ == "__main__":
    main()
