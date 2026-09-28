"""Generate notebooks/signbridge_kaggle_train.ipynb from the project's own ml/ code (keeps them in sync)."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def src(name):
    code = (ROOT / "ml" / name).read_text()
    return re.sub(r"^from ml\.\S+ import .*$", "", code, flags=re.M)


def cell(kind, text):
    c = {"cell_type": kind, "metadata": {}, "source": text.strip("\n").splitlines(keepends=True)}
    if kind == "code":
        c.update(outputs=[], execution_count=None)
    return c


cells = [
    cell("markdown", """
# SignBridge - word model training on a Kaggle GPU

1. **Add Data** -> search *Indian Sign Language Mediapipe Holistic Landmarks* (swaptr) and add it.
2. **Settings -> Accelerator -> GPU**, then **Run All**.
3. Download `word_model.onnx`, `word_model.pt`, `labels.json` (-> `models/`) and `metrics.json`, `*.png` (-> `experiments/kaggle/`) from the Output tab.

The same code also runs on a laptop CPU in a few minutes (`python -m ml.train`), because the model is small.
"""),
    cell("code", """
import glob, json, os, random, time
import numpy as np, pandas as pd, torch
from torch import nn
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
INPUT = glob.glob('/kaggle/input/*/keypoints')[0] if glob.glob('/kaggle/input/*/keypoints') else 'data/raw/include/keypoints'
OUT = '/kaggle/working' if os.path.exists('/kaggle/working') else '.'
EPOCHS, SEED = 150, 42
print(DEVICE, INPUT)
"""),
    cell("markdown", "## Vocabulary and landmark features (same code as `ml/vocab.py`, `ml/features.py`)"),
    cell("code", src("vocab.py")),
    cell("code", src("features.py")),
    cell("code", src("models.py")),
    cell("markdown", "## Load the 50-word subset and build 32-frame sequences"),
    cell("code", """
INCLUDE_ASPECT = 16 / 9

def points(g, n):
    arr = np.full((n, 2), np.nan, np.float32)
    arr[g.landmark_index.values] = g[['x', 'y']].values
    return None if np.isnan(arr).all() else arr

def take(path):
    df = pd.read_parquet(path, columns=['frame', 'type', 'landmark_index', 'x', 'y'])
    df = df[df.type != 'face']
    frames = []
    for _, f in df.groupby('frame', sort=True):
        p = {t: g for t, g in f.groupby('type')}
        frames.append(body_frame(points(p['pose'], 33) if 'pose' in p else None,
                                 points(p['left_hand'], 21) if 'left_hand' in p else None,
                                 points(p['right_hand'], 21) if 'right_hand' in p else None, INCLUDE_ASPECT))
    return resample_sequence(frames)

rng = random.Random(SEED)
train, test = [], []
for i, w in enumerate(WORDS):
    files = sorted(glob.glob(f"{INPUT}/{w['source']}/*.parquet"))
    rng.shuffle(files)
    n_test = max(2, round(len(files) * 0.2))
    for k, f in enumerate(files):
        (test if k < n_test else train).append((take(f), i))
print(len(train), 'train', len(test), 'test')
"""),
    cell("markdown", "## Train (augmentation: rotation, scale, shift, time warp, mirrored signing)"),
    cell("code", """
def augment(seq, r):
    ang = np.deg2rad(r.uniform(-12, 12))
    rot = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]], np.float32)
    seq = seq @ rot.T * r.uniform(0.85, 1.15) + r.uniform(-0.12, 0.12, 2).astype(np.float32)
    idx = np.sort(np.clip(np.arange(T) + r.normal(0, 1.2, T), 0, T - 1)).round().astype(int)
    return seq[idx] + r.normal(0, 0.01, seq.shape).astype(np.float32)

nr = np.random.default_rng(SEED)
Xte = torch.tensor(np.stack([word_features(s) for s, _ in test])).to(DEVICE)
yte = torch.tensor([y for _, y in test]).to(DEVICE)
torch.manual_seed(SEED)
model = WordTransformer(len(WORDS)).to(DEVICE)
opt = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-2)
sched = torch.optim.lr_scheduler.OneCycleLR(opt, 2e-3, total_steps=EPOCHS)
loss_fn = nn.CrossEntropyLoss(label_smoothing=0.1)
hist, best, best_state, t0 = [], 0, None, time.time()
for ep in range(EPOCHS):
    model.train()
    X = torch.tensor(np.stack([word_features(augment(s, nr), mirror=nr.random() < 0.5) for s, _ in train])).to(DEVICE)
    Y = torch.tensor([y for _, y in train]).to(DEVICE)
    perm = torch.randperm(len(Y))
    for i in range(0, len(perm), 64):
        b = perm[i:i + 64]
        opt.zero_grad(); loss = loss_fn(model(X[b]), Y[b]); loss.backward(); opt.step()
    sched.step()
    model.eval()
    with torch.no_grad():
        acc = (model(Xte).argmax(1) == yte).float().mean().item()
    hist.append({'epoch': ep + 1, 'loss': loss.item(), 'test_acc': acc})
    if acc >= best:
        best, best_state = acc, {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
    if (ep + 1) % 10 == 0:
        print(ep + 1, round(loss.item(), 3), round(acc, 3))
print('best test accuracy', best, 'in', round(time.time() - t0), 's')
"""),
    cell("markdown", "## Export ONNX, metrics and plots"),
    cell("code", """
import matplotlib.pyplot as plt
model = WordTransformer(len(WORDS)); model.load_state_dict(best_state); model.eval()
torch.save(best_state, f'{OUT}/word_model.pt')
torch.onnx.export(model, torch.zeros(1, T, WORD_DIM), f'{OUT}/word_model.onnx', input_names=['x'], output_names=['logits'],
                  dynamic_axes={'x': {0: 'batch'}, 'logits': {0: 'batch'}}, opset_version=17, dynamo=False)
with torch.no_grad():
    pred = model(Xte.cpu()).argmax(1).numpy()
cm = np.zeros((len(WORDS), len(WORDS)), int)
for a, b in zip(yte.cpu().numpy(), pred):
    cm[a, b] += 1
json.dump({'words': WORD_GLOSSES, 'letters': LETTERS}, open(f'{OUT}/labels.json', 'w'), indent=2)
json.dump({'test_accuracy': best, 'epochs': EPOCHS, 'device': DEVICE, 'train_samples': len(train),
           'test_samples': len(test), 'confusion': cm.tolist(), 'history': hist}, open(f'{OUT}/metrics.json', 'w'), indent=1)
fig, ax = plt.subplots(1, 2, figsize=(10, 3.5))
ax[0].plot([h['test_acc'] for h in hist]); ax[0].set_title('test accuracy')
ax[1].imshow(cm, cmap='Blues'); ax[1].set_title('confusion matrix')
fig.savefig(f'{OUT}/training.png', dpi=110)
print(os.listdir(OUT))
"""),
]

nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                   "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
(ROOT / "notebooks").mkdir(exist_ok=True)
(ROOT / "notebooks" / "signbridge_kaggle_train.ipynb").write_text(json.dumps(nb, indent=1))
print("wrote notebooks/signbridge_kaggle_train.ipynb")
