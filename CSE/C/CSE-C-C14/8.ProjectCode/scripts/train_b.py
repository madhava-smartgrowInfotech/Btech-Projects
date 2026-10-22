"""Route B: ResNet50, 320px, moderate augmentation, CrossEntropy."""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from app.models import build_resnet50  # noqa: E402
from scripts.common import collect_split, get_device, set_seed, train_one_model  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=int(os.environ.get("VERIVISION_EPOCHS", "8")))
    ap.add_argument("--batch-size", type=int, default=int(os.environ.get("VERIVISION_BATCH", "16")))
    ap.add_argument("--data-root", default=os.path.join(BASE, "data"))
    ap.add_argument("--out", default=os.path.join(BASE, "models", "resnet50_b.pt"))
    args = ap.parse_args()

    set_seed(44)
    print(f"Training B on {get_device()}", flush=True)
    train = collect_split(args.data_root, "train")
    val = collect_split(args.data_root, "val")
    print(f"train={len(train)} val={len(val)}", flush=True)
    model = build_resnet50()
    for name, p in model.named_parameters():
        p.requires_grad = name.startswith("layer4") or name.startswith("fc")
    train_one_model(model, train, val, route="b", resolution=320, out_path=args.out,
                    epochs=args.epochs, batch_size=args.batch_size, lr=2e-4)


if __name__ == "__main__":
    main()
