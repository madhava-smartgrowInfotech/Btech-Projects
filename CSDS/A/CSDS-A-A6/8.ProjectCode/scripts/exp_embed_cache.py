"""Step 1 of the classification experiments: embed the 500 CUAD training examples and the 240
held-out examples with the same Gemini embedding calls the product makes, and cache the vectors.

    venv\\Scripts\\python.exe scripts\\exp_embed_cache.py

Output: experiments/classification/embeddings.npz (resumable). It also writes data/cuad_centroids.npz in
the exact format of services/classification.py when that cache does not exist yet, so the product and
ml/eval.py do not have to embed the 500 training examples a second time.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import DATA_DIR  # noqa: E402
from app.services import gemini_client  # noqa: E402

OUT = ROOT / "experiments" / "classification"
OUT.mkdir(parents=True, exist_ok=True)
CACHE = OUT / "embeddings.npz"


def embed(text: str, task: str) -> list[float]:
    for attempt in range(8):
        try:
            return gemini_client.embed_text(text, task_type=task)
        except Exception as exc:  # noqa: BLE001
            wait = 5 * (attempt + 1)
            print(f"  embed retry {attempt + 1}: {str(exc)[:90]} (sleep {wait}s)", flush=True)
            time.sleep(wait)
    raise RuntimeError("embedding kept failing")


def main():
    train = json.loads((ROOT / "data/sample/cuad_train_examples.json").read_text(encoding="utf-8"))
    cats = train["categories"]
    train_items = [(c, t) for c in cats for t in train["examples"][c]]
    eval_items = json.loads((ROOT / "data/sample/cuad_eval_set.json").read_text(encoding="utf-8"))

    state = {}
    if CACHE.exists():
        z = np.load(CACHE, allow_pickle=True)
        state = {k: z[k] for k in z.files}
    tr = list(state.get("train", []))
    ev = list(state.get("eval", []))
    t0 = time.time()

    def save():
        np.savez(CACHE, train=np.asarray(tr, dtype=np.float32), eval=np.asarray(ev, dtype=np.float32))

    for i in range(len(tr), len(train_items)):
        tr.append(embed(train_items[i][1], "RETRIEVAL_DOCUMENT"))
        if (i + 1) % 50 == 0:
            save()
            print(f"train {i + 1}/{len(train_items)}  {time.time() - t0:.0f}s", flush=True)
    save()
    for i in range(len(ev), len(eval_items)):
        ev.append(embed(eval_items[i]["text"], "RETRIEVAL_QUERY"))
        if (i + 1) % 40 == 0:
            save()
            print(f"eval {i + 1}/{len(eval_items)}  {time.time() - t0:.0f}s", flush=True)
    save()

    centroid_cache = DATA_DIR / "cuad_centroids.npz"
    if not centroid_cache.exists():
        arr = np.asarray(tr, dtype=np.float32)
        labels = np.array([c for c, _ in train_items])
        centroids = np.vstack([arr[labels == c].mean(axis=0) for c in cats])
        np.savez(centroid_cache, categories=np.array(cats, dtype=object), centroids=centroids)
        print("wrote", centroid_cache)
    print(f"done in {time.time() - t0:.0f}s: train {len(tr)}, eval {len(ev)}, dim {len(tr[0])}")


if __name__ == "__main__":
    main()
