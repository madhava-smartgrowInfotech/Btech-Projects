"""
How much of the official Kermany test split shares a patient id with the training data, and what the
model scores on the part that does not.

    python scripts/leakage_analysis.py --data_root <chest_xray> --exp exp01_custom_cnn_clahe

Background: Shahi and Bagale (arXiv:2511.00456) report that some patient ids appear in both the official
training and test folders. Pneumonia file names carry a patient id (person123_virus_45.jpeg); normal file
names carry a study id (IM-0115-0001.jpeg). This script counts the overlap and recomputes the headline
metrics on the test images whose id does not occur in train/val. It reads experiments/<exp>/test_predictions.csv
written by scripts/train_experiment.py and writes experiments/<exp>/patient_disjoint_subset.json.
"""

import argparse
import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import numpy as np

from scripts.train_experiment import group_of, list_images  # noqa: E402

CLASSES = ["Normal", "Bacterial Pneumonia", "Viral Pneumonia"]


def metrics(rows):
    y = np.array([CLASSES.index(r["true"]) for r in rows])
    p = np.array([CLASSES.index(r["pred"]) for r in rows])
    n = len(y)
    cm = np.zeros((3, 3), int)
    for a, b in zip(y, p):
        cm[a, b] += 1
    out = {"n": n, "accuracy": float((y == p).mean()), "confusion_matrix": cm.tolist(),
           "support": [int((y == c).sum()) for c in range(3)]}
    per = {}
    f1s = []
    for c, name in enumerate(CLASSES):
        tp = cm[c, c]
        pr = tp / cm[:, c].sum() if cm[:, c].sum() else 0.0
        rc = tp / cm[c].sum() if cm[c].sum() else 0.0
        f1 = 2 * pr * rc / (pr + rc) if pr + rc else 0.0
        per[name] = {"precision": float(pr), "recall": float(rc), "f1": float(f1), "support": int(cm[c].sum())}
        if cm[c].sum():
            f1s.append(f1)
    out["per_class"] = per
    out["macro_f1_present_classes"] = float(np.mean(f1s))
    yb, pb = (y > 0), (p > 0)
    tp = int((yb & pb).sum()); tn = int((~yb & ~pb).sum()); fp = int((~yb & pb).sum()); fn = int((yb & ~pb).sum())
    out["binary_normal_vs_pneumonia"] = {
        "tp": tp, "tn": tn, "fp": fp, "fn": fn,
        "accuracy": (tp + tn) / n,
        "sensitivity": tp / (tp + fn) if tp + fn else None,
        "specificity": tn / (tn + fp) if tn + fp else None,
    }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_root", required=True)
    ap.add_argument("--exp", default="exp02_custom_cnn_tuned")
    a = ap.parse_args()

    pool = list_images(os.path.join(a.data_root, "train")) + list_images(os.path.join(a.data_root, "val"))
    train_ids = {group_of(p) for p in pool}
    rows = list(csv.DictReader(open(os.path.join(ROOT, "experiments", a.exp, "test_predictions.csv"))))
    for r in rows:
        r["group"] = group_of(r["file"])
        r["shared"] = r["group"] in train_ids
    shared = [r for r in rows if r["shared"]]
    disjoint = [r for r in rows if not r["shared"]]
    by_class = {c: {"test": sum(r["true"] == c for r in rows), "sharing_patient_id_with_training": sum(r["true"] == c for r in shared)} for c in CLASSES}
    res = {
        "experiment": a.exp,
        "test_images": len(rows),
        "sharing_patient_id_with_training": len(shared),
        "patient_disjoint_images": len(disjoint),
        "by_class": by_class,
        "full_test": metrics(rows),
        "patient_disjoint_subset": metrics(disjoint),
        "note": "pneumonia ids are patient ids (person123); normal ids are study ids (IM-0115). The normal test images share no id with training.",
    }
    path = os.path.join(ROOT, "experiments", a.exp, "patient_disjoint_subset.json")
    json.dump(res, open(path, "w"), indent=2)
    print(json.dumps({k: res[k] for k in ("test_images", "sharing_patient_id_with_training", "patient_disjoint_images", "by_class")}, indent=1))
    print("full accuracy", round(res["full_test"]["accuracy"], 4), "| disjoint subset accuracy", round(res["patient_disjoint_subset"]["accuracy"], 4))
    print("wrote", path)


if __name__ == "__main__":
    main()
