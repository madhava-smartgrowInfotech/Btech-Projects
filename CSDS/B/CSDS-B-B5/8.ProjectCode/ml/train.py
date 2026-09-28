"""Train the word and letter models on CPU and export them to ONNX.

    python -m ml.train            # both
    python -m ml.train words      # or: letters

Writes models/word_model.onnx, models/letter_model.onnx, models/labels.json,
experiments/train_metrics.json and training-curve plots in experiments/.
"""
import json
import sys
import time
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import torch
from torch import nn

from ml.features import T, WORD_DIM, LETTER_DIM, letter_features, word_features
from ml.models import LetterMLP, WordTransformer
from ml.vocab import LETTERS, WORD_GLOSSES

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA, MODELS, EXP = ROOT / "data", ROOT / "models", ROOT / "experiments"
SEED = 42


# ---------------------------------------------------------------- data
def load_words():
    """-> dict split -> (X (N,T,49,2), y, source) for include + own-pipeline video clips."""
    split = json.loads((DATA / "splits.json").read_text())
    out = {"train": [], "test": [], "video_test": []}
    for name, source in (("words_landmarks.npz", "include"), ("word_videos_landmarks.npz", "video")):
        path = DATA / name
        if not path.exists():
            continue
        d = np.load(path)
        for x, g, t in zip(d["X"], d["gloss"], d["take"]):
            s = split.get(f"{g}/{t}", "train")
            key = "video_test" if (source == "video" and s == "test") else s
            out[key].append((x.astype(np.float32), WORD_GLOSSES.index(str(g))))
    return {k: (np.stack([a for a, _ in v]), np.array([b for _, b in v])) for k, v in out.items() if v}


def augment_seq(seq, rng):
    seq = seq.copy()
    ang = np.deg2rad(rng.uniform(-12, 12))
    rot = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]], np.float32)
    seq = seq @ rot.T * rng.uniform(0.85, 1.15) + rng.uniform(-0.12, 0.12, 2).astype(np.float32)
    # time warp: jittered, sorted frame indices
    idx = np.sort(np.clip(np.arange(T) + rng.normal(0, 1.2, T), 0, T - 1)).round().astype(int)
    seq = seq[idx]
    seq = seq + rng.normal(0, 0.01, seq.shape).astype(np.float32)
    for k in (slice(7, 28), slice(28, 49)):  # occasional dropped hand frames
        drop = rng.random(T) < 0.05
        seq[drop, k] = np.nan
    return seq


def word_batch(X, rng=None):
    feats = []
    for s in X:
        if rng is not None:
            feats.append(word_features(augment_seq(s, rng), mirror=rng.random() < 0.5))
        else:
            feats.append(word_features(s))
    return torch.tensor(np.stack(feats))


def load_letters():
    df = pd.read_csv(DATA / "letters_landmarks.csv", dtype={"label": str})
    hands = df[[c for c in df.columns if c.startswith("h")]].values.reshape(-1, 2, 21, 2).astype(np.float32)
    y = df["label"].astype(str).map(LETTERS.index).values
    rng = np.random.default_rng(SEED)
    test = np.zeros(len(df), bool)
    for c in np.unique(y):
        idx = np.where(y == c)[0]
        test[rng.choice(idx, max(1, len(idx) // 5), replace=False)] = True
    return hands, df["n_hands"].values, y, test


def letter_batch(hands, n, rng=None):
    feats = []
    for h, k in zip(hands, n):
        hs = [h[i].copy() for i in range(k)]
        if rng is not None:
            ang = np.deg2rad(rng.uniform(-15, 15))
            rot = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]], np.float32)
            s = rng.uniform(0.85, 1.15)
            hs = [(x - 0.5) @ rot.T * s + 0.5 + rng.normal(0, 0.004, x.shape).astype(np.float32) for x in hs]
            feats.append(letter_features(hs, mirror=rng.random() < 0.5))
        else:
            feats.append(letter_features(hs))
    return torch.tensor(np.stack(feats))


# ---------------------------------------------------------------- training loop
def fit(model, make_train, Xte, yte, epochs, lr, name):
    torch.manual_seed(SEED)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-2)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, lr, total_steps=epochs)
    loss_fn = nn.CrossEntropyLoss(label_smoothing=0.1)
    hist, best, best_state = [], -1, None
    for ep in range(epochs):
        model.train()
        xb_all, yb_all = make_train()
        perm = torch.randperm(len(yb_all))
        tot = 0.0
        for i in range(0, len(perm), 64):
            b = perm[i: i + 64]
            opt.zero_grad()
            loss = loss_fn(model(xb_all[b]), yb_all[b])
            loss.backward()
            opt.step()
            tot += loss.item() * len(b)
        sched.step()
        model.eval()
        with torch.no_grad():
            acc = (model(Xte).argmax(1) == yte).float().mean().item()
        hist.append({"epoch": ep + 1, "loss": tot / len(perm), "test_acc": acc})
        if acc >= best:
            best, best_state = acc, {k: v.clone() for k, v in model.state_dict().items()}
        if (ep + 1) % 10 == 0:
            print(f"[{name}] epoch {ep + 1}/{epochs} loss {tot / len(perm):.3f} test acc {acc:.3f}")
    model.load_state_dict(best_state)
    return hist, best


def plot(hist, name):
    ep = [h["epoch"] for h in hist]
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.2))
    ax[0].plot(ep, [h["loss"] for h in hist]); ax[0].set_title(f"{name}: training loss"); ax[0].set_xlabel("epoch")
    ax[1].plot(ep, [h["test_acc"] for h in hist]); ax[1].set_title(f"{name}: test accuracy"); ax[1].set_xlabel("epoch")
    fig.tight_layout()
    fig.savefig(EXP / f"{name}_training.png", dpi=110)
    plt.close(fig)


def export(model, dim, path, seq):
    model.eval()
    dummy = torch.zeros((1, T, dim) if seq else (1, dim))
    torch.onnx.export(model, dummy, str(path), input_names=["x"], output_names=["logits"],
                      dynamic_axes={"x": {0: "batch"}, "logits": {0: "batch"}}, opset_version=17, dynamo=False)


def train_words(epochs=150):
    d = load_words()
    Xtr, ytr = d["train"]
    Xte, yte = d["test"]
    print(f"words: train {len(ytr)}  test {len(yte)}  video_test {len(d.get('video_test', ([], []))[1])}")
    rng = np.random.default_rng(SEED)
    Xte_t, yte_t = word_batch(Xte), torch.tensor(yte)
    model = WordTransformer(len(WORD_GLOSSES))
    t0 = time.time()
    hist, best = fit(model, lambda: (word_batch(Xtr, rng), torch.tensor(ytr)), Xte_t, yte_t, epochs, 2e-3, "words")
    torch.save(model.state_dict(), MODELS / "word_model.pt")
    export(model, WORD_DIM, MODELS / "word_model.onnx", seq=True)
    plot(hist, "words")
    return {"test_accuracy": best, "train_samples": int(len(ytr)), "test_samples": int(len(yte)),
            "epochs": epochs, "train_seconds": round(time.time() - t0, 1), "history": hist}


def train_letters(epochs=60):
    hands, n, y, test = load_letters()
    print(f"letters: train {(~test).sum()}  test {test.sum()}")
    rng = np.random.default_rng(SEED)
    Xte, yte = letter_batch(hands[test], n[test]), torch.tensor(y[test])
    model = LetterMLP(len(LETTERS))
    t0 = time.time()
    hist, best = fit(model, lambda: (letter_batch(hands[~test], n[~test], rng), torch.tensor(y[~test])),
                     Xte, yte, epochs, 3e-3, "letters")
    torch.save(model.state_dict(), MODELS / "letter_model.pt")
    export(model, LETTER_DIM, MODELS / "letter_model.onnx", seq=False)
    plot(hist, "letters")
    return {"test_accuracy": best, "train_samples": int((~test).sum()), "test_samples": int(test.sum()),
            "epochs": epochs, "train_seconds": round(time.time() - t0, 1), "history": hist}


if __name__ == "__main__":
    MODELS.mkdir(exist_ok=True)
    EXP.mkdir(exist_ok=True)
    parts = sys.argv[1:] or ["words", "letters"]
    path = EXP / "train_metrics.json"
    metrics = json.loads(path.read_text()) if path.exists() else {}
    for p in parts:
        metrics[p] = train_words() if p == "words" else train_letters()
    path.write_text(json.dumps(metrics, indent=2))
    (MODELS / "labels.json").write_text(json.dumps({"words": WORD_GLOSSES, "letters": LETTERS}, indent=2))
    for p in parts:
        print(p, "best test accuracy", round(metrics[p]["test_accuracy"], 4))
