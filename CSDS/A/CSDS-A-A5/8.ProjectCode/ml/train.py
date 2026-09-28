"""Train the JEPA behaviour encoder on the committed GST dataset (CPU, about a minute).

Saves models/jepa.pt and experiments/metrics.json.
Usage: python -m ml.train [--epochs 100] [--seed 42]
"""
import argparse
import json
import os
import platform

import torch

from ml.pipeline import train_model

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(ROOT, "data", "generated"))
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    model_path = os.path.join(ROOT, "models", "jepa.pt")
    _, _, info = train_model(a.data, model_path, a.epochs, a.seed,
                             progress=lambda s, p, m: print(f"  {m}"))
    info.update(model_file="models/jepa.pt", data=os.path.relpath(a.data, ROOT).replace("\\", "/"),
                parameters=sum(p.numel() for p in torch.load(model_path, weights_only=False)["state_dict"].values()),
                device="cpu", torch=torch.__version__, python=platform.python_version())
    os.makedirs(os.path.join(ROOT, "experiments"), exist_ok=True)
    with open(os.path.join(ROOT, "experiments", "metrics.json"), "w") as f:
        json.dump(info, f, indent=2)
    print(f"trained in {info['train_seconds']}s, final loss {info['final_loss']}")


if __name__ == "__main__":
    main()
