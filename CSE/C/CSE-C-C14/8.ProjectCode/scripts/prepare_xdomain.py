"""Cross-domain probe set: 300 real photographs + 300 AI-generated images at native resolution.

Source: Hugging Face `Parveshiiii/AI-vs-Real` (MIT licence; mirror labels 0 = AI-generated, 1 = real).
Real photographs come from shard 0 (about 640 px wide), AI-generated images from shard 1 (1024x1024 JPEG).
The dataset card does not name the generators, so this set tests transfer to *some* unseen generator and
content domain, not to a specific model. Download the shards into data/xdomain_raw/ first.
"""
import io
import os

import numpy as np
import pandas as pd
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "xdomain_raw")
OUT = os.path.join(BASE, "data", "xdomain")
N = 300


def main():
    rng = np.random.RandomState(42)
    for cls, shard in (("real", "s0"), ("fake", "s1")):
        df = pd.read_parquet(os.path.join(RAW, f"{shard}.parquet"))
        folder = os.path.join(OUT, "test", cls)
        os.makedirs(folder, exist_ok=True)
        for n, i in enumerate(rng.permutation(len(df))[:N]):
            Image.open(io.BytesIO(df.iloc[i]["image"]["bytes"])).convert("RGB").save(
                os.path.join(folder, f"{cls}_{n:04d}.jpg"), quality=95)
        print(cls, N, flush=True)


if __name__ == "__main__":
    main()
