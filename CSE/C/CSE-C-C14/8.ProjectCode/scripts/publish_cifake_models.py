"""Install the CIFAKE-trained checkpoints and their measured metrics as the models the app serves.

    python scripts/publish_cifake_models.py

1. copies the demo-data checkpoints, metadata and metric files to models/demo_backup/ and artifacts/demo_backup/ (once);
2. copies models/cifake/*.pt over models/*.pt;
3. writes artifacts/metrics/{model,ensemble,robustness}_metrics.json, confusion_matrix.png and models/model_metadata.json
   from experiments/cifake/metrics.json, in the same format scripts/evaluate.py writes, so /api/insights and the
   Model insights page show the real numbers.
"""
import datetime
import json
import os
import shutil

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(BASE, "models")
METRICS = os.path.join(BASE, "artifacts", "metrics")
FILES = {"efficientnet_a1": ("a1", 224), "efficientnet_a2": ("a2", 224), "resnet50_b": ("b", 320), "mobilenetv3_c": ("c", 224)}
DATASET = "cifake-subset"


def main():
    res = json.load(open(os.path.join(BASE, "experiments", "cifake", "metrics.json"), encoding="utf-8"))
    bk_m, bk_a = os.path.join(MODELS, "demo_backup"), os.path.join(BASE, "artifacts", "demo_backup")
    if not os.path.isdir(bk_m):
        os.makedirs(bk_m)
        for f in os.listdir(MODELS):
            p = os.path.join(MODELS, f)
            if os.path.isfile(p):
                shutil.copy2(p, bk_m)
        shutil.copytree(METRICS, bk_a)
        print("demo models and metrics backed up")
    for name in FILES:
        shutil.copy2(os.path.join(MODELS, "cifake", name + ".pt"), os.path.join(MODELS, name + ".pt"))
        h = os.path.join(MODELS, "cifake", name + "_history.json")
        if os.path.exists(h):
            shutil.copy2(h, os.path.join(MODELS, name + "_history.json"))

    clean = res["clean"]
    model_metrics = {}
    for name, (br, resn) in FILES.items():
        m = dict(clean["branches"][br])
        m.update({"dataset": DATASET, "seed": res["seed"], "resolution": resn})
        model_metrics[name] = m
    ens = dict(clean["ensemble"])
    ens.update({"dataset": DATASET, "seed": res["seed"]})
    rob = res["robustness"]
    robust = {"clean": {"accuracy": rob["clean_subset"]["ensemble"]["accuracy"], "f1": rob["clean_subset"]["ensemble"]["f1"],
                        "n_samples": rob["clean_subset"]["ensemble"]["n_samples"]}}
    for k in ("jpeg", "resize", "blur", "noise"):
        e = rob[k]["ensemble"]
        robust[k] = {"accuracy": e["accuracy"], "f1": e["f1"], "n_samples": e["n_samples"]}
    for fn, obj in (("model_metrics.json", model_metrics), ("ensemble_metrics.json", ens), ("robustness_metrics.json", robust)):
        json.dump(obj, open(os.path.join(METRICS, fn), "w", encoding="utf-8"), indent=2)

    cm = np.array(ens["confusion_matrix"])
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    ax.imshow(cm, cmap="Blues")
    ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
    ax.set_xticklabels(["REAL", "AI_GENERATED"]); ax.set_yticklabels(["REAL", "AI_GENERATED"])
    ax.set_xlabel("Predicted"); ax.set_ylabel("True")
    ax.set_title("Ensemble Confusion Matrix (held-out test)", fontsize=11)
    for r in range(2):
        for c in range(2):
            ax.text(c, r, str(cm[r, c]), ha="center", va="center", fontsize=14, color="white" if cm[r, c] > cm.max() / 2 else "black")
    fig.tight_layout()
    fig.savefig(os.path.join(METRICS, "confusion_matrix.png"), dpi=150)
    plt.close(fig)

    meta = [{"model_name": n, "branch": br, "training_dataset": DATASET, "image_resolution": resn,
             "class_mapping": {"0": "REAL", "1": "AI_GENERATED"}, "checkpoint_path": os.path.join("models", n + ".pt"),
             "validation": {k: model_metrics[n].get(k) for k in ("accuracy", "f1", "roc_auc")}} for n, (br, resn) in FILES.items()]
    json.dump({"created": datetime.datetime.now().isoformat(timespec="seconds"), "models": meta},
              open(os.path.join(MODELS, "model_metadata.json"), "w", encoding="utf-8"), indent=2)
    print("published: ensemble acc=%.4f f1=%.4f auc=%.4f" % (ens["accuracy"], ens["f1"], ens["roc_auc"]))


if __name__ == "__main__":
    main()
