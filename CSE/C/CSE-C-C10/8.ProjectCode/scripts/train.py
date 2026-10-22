"""Train + evaluate VenturePulse pipeline."""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # lets "python scripts/train.py" find the app package

from app.ml.dataset import load_dataset
from app.ml.preprocessing import prepare_frame
from app.ml.evaluation import run_evaluation

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    df_raw, meta = load_dataset()
    print("Source:", meta)
    df = prepare_frame(df_raw)
    print("Prepared:", df.shape, "success:", int((df.label == 1).sum()))
    res = run_evaluation(df, meta)
    print("Best:", res["best_model"])
    for m, v in res["models"].items():
        print(f"{m}: bal_acc={v['balanced_accuracy']['mean']:.4f}±{v['balanced_accuracy']['std']:.4f} f1={v['f1']['mean']:.4f}")
