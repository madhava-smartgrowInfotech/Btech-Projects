"""Route C: MobileNetV3-Large, 224px, focal loss (gamma=2), backbone mostly frozen."""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from app.models import build_mobilenetv3_large  # noqa: E402
from scripts.common import collect_split, get_device, set_seed, train_one_model  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=int(os.environ.get("VERIVISION_EPOCHS", "8")))
    ap.add_argument("--batch-size", type=int, default=int(os.environ.get("VERIVISION_BATCH", "32")))
    ap.add_argument("--data-root", default=os.path.join(BASE, "data"))
    ap.add_argument("--out", default=os.path.join(BASE, "models", "mobilenetv3_c.pt"))
    args = ap.parse_args()

    set_seed(45)
    print(f"Training C on {get_device()}", flush=True)
    train = collect_split(args.data_root, "train")
    val = collect_split(args.data_root, "val")
    print(f"train={len(train)} val={len(val)}", flush=True)
    model = build_mobilenetv3_large()
    for name, p in model.named_parameters():
        p.requires_grad = name.startswith("features.1") is False  # placeholder, refined below
    for name, p in model.named_parameters():
        # Freeze early backbone; train final feature blocks + classifier
        keep = name.startswith("classifier") or "features.15" in name or "features.16" in name
        p.requires_grad = keep
    train_one_model(model, train, val, route="c", resolution=224, out_path=args.out,
                    epochs=args.epochs, batch_size=args.batch_size, lr=3e-4, use_focal=True)


if __name__ == "__main__":
    main()
