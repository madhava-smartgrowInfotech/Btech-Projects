"""Evaluate both trained models on their held-out test splits.

Usage: python ml/eval.py
Output: experiments/eval/metrics.json (accuracy, sensitivity, specificity, F1, ROC-AUC, confusion matrices, ROC curves)
Needs the full retinopathy dataset in data/raw (python scripts/download_data.py). If it is missing, the retina
section is evaluated on the committed sample in data/sample/fundus instead (and labelled as such).
"""
import csv
import json
from datetime import datetime, timezone

import cv2
import joblib
import numpy as np
import pandas as pd
import torch

from common import ROOT, binary_metrics, hr_image_dir, hr_label_csv, write_json

from app.services.heart import FEATURES
from app.services.lenet import LeNet
from app.services.preprocess import preprocess
from app.services.wavelet import feature_stack
from train_heart import load as load_heart, split as split_heart

EXP = ROOT / "experiments"


@torch.no_grad()
def retina_probs(model, paths) -> np.ndarray:
    out = []
    for p in paths:
        x = torch.from_numpy(feature_stack(preprocess(cv2.imread(str(p), cv2.IMREAD_COLOR))["input"]))[None]
        out.append(float(torch.sigmoid(model(x)).item()))
    return np.array(out)


def eval_retina() -> dict:
    meta = json.loads((ROOT / "models" / "lenet_hr.json").read_text())
    train = json.loads((EXP / "retina" / "metrics.json").read_text())
    model = LeNet()
    model.load_state_dict(torch.load(ROOT / "models" / "lenet_hr.pt", map_location="cpu"))
    model.eval()
    try:
        labels = pd.read_csv(hr_label_csv())
        labels.columns = ["Image", "label"]
        test = json.loads((EXP / "retina" / "split.json").read_text())["test"]
        lab = labels.set_index("Image").loc[test, "label"].to_numpy()
        paths = [hr_image_dir() / n for n in test]
        source = "held-out test split of the full dataset"
    except SystemExit:
        d = ROOT / "data" / "sample" / "fundus"
        rows = list(csv.DictReader((d / "labels.csv").open()))
        lab = np.array([int(r["hypertensive_retinopathy"]) for r in rows])
        paths = [d / r["image"] for r in rows]
        source = "committed sample images only (full dataset not downloaded)"
    probs = retina_probs(model, paths)
    return {
        "model": "LeNet CNN on 2-level Haar wavelet sub-bands",
        "dataset": "Hypertension & Hypertensive Retinopathy Dataset (HRDC task 2, 712 images)",
        "evaluated_on": source,
        "split": train["split"],
        "epochs": train["epochs"],
        "train_seconds": train["train_seconds"],
        "test": binary_metrics(lab, probs, meta["threshold"]),
        "notes": "Threshold chosen on the validation split (Youden's J). Small CPU model; results are for decision support only.",
    }


def eval_heart() -> dict:
    train = json.loads((EXP / "heart" / "metrics.json").read_text())
    df = load_heart()
    _, te = split_heart(df)
    model = joblib.load(ROOT / "models" / "heart_rf.joblib")
    probs = model.predict_proba(df[FEATURES].iloc[te])[:, 1]
    return {
        "model": train["model"],
        "dataset": train["dataset"],
        "split": train["split"],
        "cv_roc_auc_mean": train["cv_roc_auc_mean"],
        "test": binary_metrics(df["disease"].to_numpy()[te], probs, 0.5),
        "feature_importance": train["feature_importance"],
        "notes": f"5-fold cross-validated ROC-AUC on the training part: {train['cv_roc_auc_mean']:.3f}. "
                 "Duplicate rows removed before splitting; label aligned with the UCI source (1 = heart disease).",
    }


def main():
    res = {"generated_at": datetime.now(timezone.utc).isoformat(), "retina": eval_retina(), "heart": eval_heart()}
    write_json(EXP / "eval" / "metrics.json", res)
    for k in ("retina", "heart"):
        t = res[k]["test"]
        print(f"{k:6s} acc {t['accuracy']:.3f} sens {t['sensitivity']:.3f} spec {t['specificity']:.3f} "
              f"f1 {t['f1']:.3f} auc {t['roc_auc']:.3f} cm {t['confusion_matrix']}")


if __name__ == "__main__":
    main()
