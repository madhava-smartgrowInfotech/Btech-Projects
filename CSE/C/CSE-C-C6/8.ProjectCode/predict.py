"""Quick inference helper: python predict.py --text "..."  / --csv batch.csv"""
import os
import sys
import argparse
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.pipeline import FakeNewsMSVMPipeline
from src.preprocessing import ID2LABEL

BASE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(BASE, "models", "msvm_model.pkl")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default=None)
    ap.add_argument("--csv", default=None)
    ap.add_argument("--model", default=MODEL)
    args = ap.parse_args()
    pipe = FakeNewsMSVMPipeline.load(args.model)
    if args.text:
        ids, proba = pipe.predict([args.text])
        print(f"Prediction: {ID2LABEL[int(ids[0])]}")
        if proba is not None:
            for i, p in enumerate(proba[0]):
                print(f"  {ID2LABEL[i]}: {p:.3f}")
    elif args.csv:
        df = pd.read_csv(args.csv)
        col = "text" if "text" in df.columns else df.columns[0]
        ids, proba = pipe.predict(df[col].fillna("").tolist())
        df["predicted"] = [ID2LABEL[int(i)] for i in ids]
        out = args.csv.replace(".csv", "_predicted.csv")
        df.to_csv(out, index=False)
        print(f"Saved -> {out}")
    else:
        ap.error("provide --text or --csv")


if __name__ == "__main__":
    main()
