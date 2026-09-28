"""Evaluation summary for every objective -> experiments/eval/metrics.json

- MRI: label efficiency of JEPA vs supervised U-Net, reconstruction (MAE) and scratch baselines (from train_mri.py)
- DNA: repeat-type and organism classification vs MLM reconstruction and scratch baselines (from train_dna.py)
- STR: identification rank and LR calibration on simulated casework queries (computed here, seeded)
- MRI inference check: the saved few-label model re-scored on the committed sample slices (CPU)
"""
import json
import random
import statistics
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.services import mri, str_match  # noqa: E402

EXP = ROOT / "experiments"
OUT = EXP / "eval" / "metrics.json"
SEED = 11


def load(name):
    p = EXP / name
    return json.loads(p.read_text()) if p.exists() else {}


def str_eval(n_true=200, n_non=200):
    freqs, db = str_match.load()
    rng = random.Random(SEED)
    loci = db["loci"]
    rank1, lrs_true = 0, []
    for _ in range(n_true):
        src = rng.choice(db["profiles"])
        use = rng.sample(loci, rng.randint(10, 20))  # partial profile (drop-out of whole loci)
        q = {}
        for l in use:
            g = list(src["genotype"][l])
            if rng.random() < 0.03:  # typing error at ~3% of loci
                g[rng.randrange(2)] = rng.choice(list(freqs[l]))
            q[l] = "/".join(g)
        top = str_match.match(q, top_k=1)["matches"][0]
        rank1 += top["id"] == src["id"]
        lrs_true.append(str_match.compare(str_match.parse_profile(q), src["genotype"])[0])
    non_lrs = []
    for _ in range(n_non):
        q = {}
        for l in rng.sample(loci, rng.randint(10, 20)):
            q[l] = "/".join(rng.choices(list(freqs[l]), list(freqs[l].values()), k=2))
        query = str_match.parse_profile(q)
        for p in db["profiles"]:
            non_lrs.append(str_match.compare(query, p["genotype"])[0])
    non = np.array(non_lrs)
    return {
        "true_source_queries": n_true, "rank1_accuracy": round(rank1 / n_true, 4),
        "median_log10_lr_true_source": round(statistics.median(lrs_true), 2),
        "min_log10_lr_true_source": round(min(lrs_true), 2),
        "non_contributor_queries": n_non, "comparisons": int(len(non)),
        "non_contributor_lr_gt1_rate": round(float((non > 0).mean()), 6),
        "max_log10_lr_non_contributor": round(float(non.max()), 2),
    }


def mri_sample_check():
    rows = mri.list_samples()
    out = {}
    for key in ("jepa_10", "jepa_100", "unet_100"):
        try:
            mri.load_model(key)
        except FileNotFoundError:
            continue
        tp = fp = fn = 0
        for r in rows:
            gt = np.asarray(Image.open(mri.SAMPLE_DIR / r["file"].replace(".png", "_mask.png")).convert("L")) > 127
            res = mri.segment((mri.SAMPLE_DIR / r["file"]).read_bytes(), key, 1.0)
            pred = np.asarray(Image.open(__import__("io").BytesIO(
                __import__("base64").b64decode(res["mask_png"].split(",")[1])))) > 127
            tp += int((pred & gt).sum())
            fp += int((pred & ~gt).sum())
            fn += int((~pred & gt).sum())
        out[key] = {"slices": len(rows), "dice_256px": round(2 * tp / max(1, 2 * tp + fp + fn), 4)}
    return out


def main():
    m, d = load("mri_metrics.json"), load("dna_metrics.json")
    ft = m.get("finetune", {})
    summary = {"mri": {"label_efficiency": {k: {"dice": v["dice"], "iou": v["iou"]} for k, v in ft.items()}}}
    if "jepa_10" in ft and "unet_100" in ft:
        summary["mri"]["jepa10_vs_unet100_dice_ratio"] = round(ft["jepa_10"]["dice"] / ft["unet_100"]["dice"], 4)
    if "jepa_10" in ft and "unet_10" in ft:
        summary["mri"]["jepa10_minus_unet10_dice"] = round(ft["jepa_10"]["dice"] - ft["unet_10"]["dice"], 4)
    if "jepa_10" in ft and "mae_10" in ft:
        summary["mri"]["jepa10_minus_mae10_dice"] = round(ft["jepa_10"]["dice"] - ft["mae_10"]["dice"], 4)
    print("MRI sample re-check ...", flush=True)
    summary["mri"]["sample_inference_check"] = mri_sample_check()
    if d:
        summary["dna"] = {
            "repeat_type": {k: {"accuracy": v["accuracy"], "macro_f1": v["macro_f1"]} for k, v in d["repeat"].items()},
            "organism_class": {k: {"accuracy": v["accuracy"], "chance": v["chance_accuracy"]} for k, v in d["organism"].items()},
        }
    print("STR evaluation ...", flush=True)
    summary["str"] = str_eval()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
