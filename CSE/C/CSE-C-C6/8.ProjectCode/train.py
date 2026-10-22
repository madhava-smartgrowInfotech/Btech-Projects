"""CLI training entry-point: python train.py [--csv PATH] [--n N] ..."""
import os
import sys
import argparse
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.pipeline import FakeNewsMSVMPipeline
from src.dataset import load_csv, build_demo_dataset

BASE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser(description="Train PCA+Firefly+MSVM fake-news model")
    ap.add_argument("--csv", default=None, help="CSV file or folder with text+label")
    ap.add_argument("--n", type=int, default=300, help="demo samples per class (if no --csv)")
    ap.add_argument("--fireflies", type=int, default=10)
    ap.add_argument("--generations", type=int, default=12)
    ap.add_argument("--max-tfidf", type=int, default=4000)
    ap.add_argument("--out", default=os.path.join(BASE, "models", "msvm_model.pkl"))
    args = ap.parse_args()

    if args.csv:
        print(f"Loading dataset from {args.csv} ...")
        texts, y = load_csv(args.csv)
    else:
        print(f"Building demo dataset ({args.n}/class) ...")
        texts, y = build_demo_dataset(n_per_class=args.n)
    print(f"Docs: {len(texts)} | class dist: "
          f"REAL={(y==0).sum()} PARTIAL={(y==1).sum()} FAKE={(y==2).sum()}")

    pipe = FakeNewsMSVMPipeline(max_tfidf=args.max_tfidf,
                                n_fireflies=args.fireflies,
                                n_generations=args.generations)
    pipe.fit(texts, y, verbose=True)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    pipe.save(args.out)
    print(f"\nSaved model -> {args.out}")
    s = pipe.stats_
    print(f"Accuracy={s['accuracy']:.4f} F1-macro={s['f1_macro']:.4f} "
          f"PCA {s['n_total_features']}->{s['n_pca']}->{s['n_selected']} feats")
    with open(os.path.join(BASE, "models", "metrics.json"), "w") as f:
        json.dump({k: v for k, v in s.items()
                   if k not in ("y_test", "y_pred")}, f, indent=2)


if __name__ == "__main__":
    main()
