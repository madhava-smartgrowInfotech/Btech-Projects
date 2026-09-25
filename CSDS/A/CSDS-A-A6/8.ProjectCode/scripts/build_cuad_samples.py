"""Derive small, seeded train/eval samples from data/cuad/CUADv1.json for the
20 substantive CUAD clause categories ClauseGuard classifies (F2/F7). Skips
purely administrative categories (Document Name, Parties, Agreement Date,
Effective Date, Expiration Date) since those are metadata, not clause types.

Output:
  data/sample/cuad_train_examples.json - per-category example clause texts
    used to build classification centroids (services/classification.py).
  data/sample/cuad_eval_set.json - held-out labelled examples for
    ml/eval.py's CUAD classification score (F7).

Deterministic: fixed random seed, so re-running reproduces the same split.
"""
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC = ROOT_DIR / "data" / "cuad" / "CUADv1.json"
OUT_DIR = ROOT_DIR / "data" / "sample"
SEED = 42

CATEGORIES = [
    "Governing Law", "Termination For Convenience", "Non-Compete", "Exclusivity",
    "Audit Rights", "Cap On Liability", "Change Of Control", "Insurance",
    "Ip Ownership Assignment", "License Grant", "Liquidated Damages",
    "Minimum Commitment", "No-Solicit Of Customers", "No-Solicit Of Employees",
    "Non-Disparagement", "Post-Termination Services", "Renewal Term",
    "Revenue/Profit Sharing", "Uncapped Liability", "Warranty Duration",
]

MAX_TRAIN_PER_CAT = 25
MAX_EVAL_PER_CAT = 12
MIN_LEN = 40
MAX_LEN = 900


def main():
    with open(SRC, encoding="utf-8") as f:
        data = json.load(f)

    by_category = defaultdict(list)
    for doc in data["data"]:
        for para in doc["paragraphs"]:
            for qa in para["qas"]:
                category = qa["id"].split("__")[-1]
                if category not in CATEGORIES:
                    continue
                for ans in qa.get("answers", []):
                    text = ans["text"].strip().replace("\n", " ")
                    text = " ".join(text.split())
                    if MIN_LEN <= len(text) <= MAX_LEN:
                        by_category[category].append(text)

    rng = random.Random(SEED)
    train_examples = {}
    eval_examples = []
    for cat in CATEGORIES:
        texts = list(dict.fromkeys(by_category.get(cat, [])))  # dedupe, keep order
        rng.shuffle(texts)
        train = texts[:MAX_TRAIN_PER_CAT]
        held_out = texts[MAX_TRAIN_PER_CAT:MAX_TRAIN_PER_CAT + MAX_EVAL_PER_CAT]
        train_examples[cat] = train
        for t in held_out:
            eval_examples.append({"text": t, "label": cat})
        print(f"{cat}: {len(train)} train, {len(held_out)} eval (of {len(texts)} total)")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "cuad_train_examples.json", "w", encoding="utf-8") as f:
        json.dump({"categories": CATEGORIES, "examples": train_examples}, f, indent=2)

    rng.shuffle(eval_examples)
    with open(OUT_DIR / "cuad_eval_set.json", "w", encoding="utf-8") as f:
        json.dump(eval_examples, f, indent=2)

    print(f"\nWrote {sum(len(v) for v in train_examples.values())} train examples "
          f"and {len(eval_examples)} eval examples across {len(CATEGORIES)} categories.")


if __name__ == "__main__":
    main()
