"""Turn the seed-42 official-partition experiment into a bundle the API can serve.

Writes experiments/unsw_nb15/official/reports/metrics.json (same schema as reports/metrics.json) and
feature_info.json next to the models, plus data/samples/real_unsw_nb15_sample_120.csv (60 normal + 60
attack flows drawn from the official testing set). Serve the bundle with

    set CIPHERGUARD_MODELS_DIR=experiments\\unsw_nb15\\official\\models
    set CIPHERGUARD_REPORTS_DIR=experiments\\unsw_nb15\\official\\reports
    python scripts\\serve.py
"""
import torch  # noqa: F401  (first heavy import on this Windows host)
import json
import sys
from pathlib import Path

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cipherguard.ids.features import FEATURE_NAMES  # noqa: E402

OFF = ROOT / "experiments" / "unsw_nb15" / "official"


def main():
    m = json.loads((OFF / "metrics.json").read_text())
    s = m["seed42"]["stack"]
    meta = joblib.load(OFF / "models" / "stacking_meta.joblib")
    dim = m["n_features_after_encoding"]
    neg, pos = 0, 0
    tr = pd.read_parquet(ROOT / "data" / "external" / "unsw_nb15" / "train.parquet", columns=["label"])
    neg, pos = int((tr.label == 0).sum()), int((tr.label == 1).sum())
    out = {
        "data_mode": "real UNSW-NB15 (official training set -> official testing set, seed 42)",
        "dataset_rows": m["train_rows"] + m["test_rows"],
        "splits": {"train": m["fit_rows"], "val": m["val_rows"], "test": m["test_rows"]},
        "accuracy": s["accuracy"], "precision": s["precision"], "recall": s["recall"], "f1": s["f1"], "roc_auc": s["roc_auc"],
        "confusion_matrix": s["confusion_matrix"], "confusion_labels": ["normal", "attack"],
        "xgb_accuracy": m["seed42"]["xgb"]["accuracy"], "cnn_accuracy": m["seed42"]["cnn"]["accuracy"],
        "meta_coef": meta.coef_.tolist(), "meta_intercept": meta.intercept_.tolist(),
        "class_balance": {"neg": neg, "pos": pos}, "input_dim": dim, "cnn_backend": "torch",
        "technology": {
            "model_a": "XGBoost (Gradient-boosted trees)",
            "model_b": "1D Convolutional Neural Network (2 conv layers + pooling + dense, PyTorch)",
            "fusion": "Logistic Regression stacking",
            "dataset": "UNSW-NB15 (real flows)",
            "crypto": "AES-256-GCM + ECDH P-256 + HKDF-SHA256",
        },
    }
    (OFF / "reports").mkdir(exist_ok=True)
    (OFF / "reports" / "metrics.json").write_text(json.dumps(out, indent=2))
    (OFF / "models" / "feature_info.json").write_text(json.dumps(
        {"input_dim": dim, "feature_names": FEATURE_NAMES, "data_mode": out["data_mode"], "cnn_backend": "torch"}, indent=2))
    te = pd.read_parquet(ROOT / "data" / "external" / "unsw_nb15" / "test.parquet")
    sample = pd.concat([te[te.label == 0].sample(60, random_state=11), te[te.label == 1].sample(60, random_state=11)]).sample(frac=1, random_state=11)
    dest = ROOT / "data" / "samples"
    dest.mkdir(parents=True, exist_ok=True)
    sample.to_csv(dest / "real_unsw_nb15_sample_120.csv", index=False)
    print("bundle written; sample", sample.shape, sample.label.value_counts().to_dict())


if __name__ == "__main__":
    main()
