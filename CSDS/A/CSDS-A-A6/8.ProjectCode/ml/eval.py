"""F7: evaluation script - scores clause classification on a CUAD held-out
set and predatory-clause detection on a curated labelled set, reported
separately. Writes experiments/eval/metrics.json (used by the Evaluation
screen and README).

Run from the backend virtual environment:
    backend\\venv\\Scripts\\python.exe ml\\eval.py
"""
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "backend"))

from app.config import gemini_configured, EXPERIMENTS_DIR  # noqa: E402
from app.services.rules import detect_flags  # noqa: E402

CUAD_EVAL_PATH = ROOT_DIR / "data" / "sample" / "cuad_eval_set.json"
PREDATORY_TEST_PATH = ROOT_DIR / "data" / "sample" / "predatory_test_set.json"
METRICS_PATH = EXPERIMENTS_DIR / "metrics.json"


def eval_predatory_detection() -> dict:
    with open(PREDATORY_TEST_PATH, encoding="utf-8") as f:
        items = json.load(f)

    tp = fp = fn = 0
    per_rule = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    for item in items:
        predicted = {r.id for r in detect_flags(item["text"])}
        expected = set(item["expected_rules"])
        for rule_id in predicted | expected:
            if rule_id in predicted and rule_id in expected:
                per_rule[rule_id]["tp"] += 1
            elif rule_id in predicted:
                per_rule[rule_id]["fp"] += 1
            else:
                per_rule[rule_id]["fn"] += 1
        tp += len(predicted & expected)
        fp += len(predicted - expected)
        fn += len(expected - predicted)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "num_examples": len(items),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "per_rule": {
            rule_id: {
                **counts,
                "precision": round(counts["tp"] / (counts["tp"] + counts["fp"]), 3) if (counts["tp"] + counts["fp"]) else 0.0,
                "recall": round(counts["tp"] / (counts["tp"] + counts["fn"]), 3) if (counts["tp"] + counts["fn"]) else 0.0,
            }
            for rule_id, counts in per_rule.items()
        },
    }


def eval_cuad_classification() -> dict:
    from app.services.classification import classify_clause, build_or_load_centroids

    with open(CUAD_EVAL_PATH, encoding="utf-8") as f:
        items = json.load(f)

    print("Building/loading CUAD classification centroids (one-time embedding cost)...")
    build_or_load_centroids()

    correct = 0
    top3_correct = 0
    total = len(items)
    per_category = defaultdict(lambda: {"correct": 0, "total": 0})

    from app.services import gemini_client
    from app.services.vectorstore import cosine_similarity_matrix
    categories, centroids = build_or_load_centroids()

    for i, item in enumerate(items):
        embedding = gemini_client.embed_text(item["text"], task_type="RETRIEVAL_QUERY")
        emb = np.asarray(embedding, dtype="float32")
        sims = cosine_similarity_matrix(emb, centroids)
        order = list(reversed(sorted(range(len(categories)), key=lambda k: sims[k])))
        top1 = categories[order[0]]
        top3 = {categories[order[j]] for j in range(3)}

        per_category[item["label"]]["total"] += 1
        if top1 == item["label"]:
            correct += 1
            per_category[item["label"]]["correct"] += 1
        if item["label"] in top3:
            top3_correct += 1

        if (i + 1) % 20 == 0:
            print(f"  ...{i + 1}/{total}")

    return {
        "num_examples": total,
        "num_categories": len(categories),
        "top1_accuracy": round(correct / total, 3) if total else 0.0,
        "top3_accuracy": round(top3_correct / total, 3) if total else 0.0,
        "per_category_accuracy": {
            cat: round(v["correct"] / v["total"], 3) if v["total"] else 0.0
            for cat, v in per_category.items()
        },
    }


def main():
    print("Evaluating predatory-clause detection (rule-based, no API needed)...")
    predatory_metrics = eval_predatory_detection()
    print(json.dumps({k: v for k, v in predatory_metrics.items() if k != "per_rule"}, indent=2))

    cuad_metrics = None
    if gemini_configured():
        print("\nEvaluating CUAD clause classification (uses Gemini embeddings API)...")
        start = time.time()
        cuad_metrics = eval_cuad_classification()
        print(f"Done in {time.time() - start:.1f}s")
        print(json.dumps({k: v for k, v in cuad_metrics.items() if k != "per_category_accuracy"}, indent=2))
    else:
        print("\nSkipping CUAD classification eval: GEMINI_API_KEY not set in .env.")
        print("Add your key and re-run `python ml/eval.py` to fill this in.")

    result = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "predatory_detection": predatory_metrics,
        "cuad_classification": cuad_metrics,
    }
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved metrics to {METRICS_PATH}")


if __name__ == "__main__":
    main()
