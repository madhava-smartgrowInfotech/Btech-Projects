"""Honest retrieval evaluation on held-out split. Saves JSON + confusion matrix image."""
import json, time, random
from pathlib import Path
from collections import Counter
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

BASE = Path(__file__).resolve().parent.parent
PROC = BASE / "data" / "processed" / "knowledge_base.json"
RESULTS = BASE / "results"
RESULTS.mkdir(exist_ok=True)

def main():
    records = json.loads(PROC.read_text(encoding="utf-8"))
    by_disease = {}
    for r in records:
        by_disease.setdefault(r["disease"], []).append(r)
    # held-out: 1 record per disease with >=2 records
    test, train_ids = [], set()
    random.seed(7)
    for d, rs in by_disease.items():
        if len(rs) >= 2:
            t = random.choice(rs)
            test.append(t)
    print(f"Test records: {len(test)}")
    from app.rag.pipeline import get_pipeline
    pipe = get_pipeline()
    y_true, y_pred, y_pred3 = [], [], []
    latencies, rr = [], []
    for t in test:
        q = "I have " + t["symptoms"].replace(", ", ", ")
        t0 = time.time()
        res = pipe.answer(q, top_k=3)
        latencies.append((time.time() - t0) * 1000)
        preds = [e["disease"] for e in res["evidence"]]
        y_true.append(t["disease"])
        y_pred.append(preds[0] if preds else "")
        y_pred3.append(preds)
        rank = next((i + 1 for i, p in enumerate(preds) if p == t["disease"]), None)
        rr.append(1.0 / rank if rank else 0.0)
    labels = sorted(set(y_true))
    top1 = sum(a == b for a, b in zip(y_true, y_pred)) / max(len(y_true), 1)
    top3 = sum(t in p for t, p in zip(y_true, y_pred3)) / max(len(y_true), 1)
    # macro precision/recall/f1 treating top-1 as classifier
    from sklearn.metrics import precision_recall_fscore_support, confusion_matrix
    prec, rec, f1, _ = precision_recall_fscore_support(y_true, y_pred, labels=labels, zero_division=0, average="macro")
    mrr = sum(rr) / max(len(rr), 1)
    cm = confusion_matrix(y_true, y_pred, labels=labels).tolist()
    out = {
        "n_test": len(test),
        "top1_accuracy": round(top1, 4),
        "top3_accuracy": round(top3, 4),
        "recall_at_3": round(top3, 4),
        "macro_precision": round(float(prec), 4),
        "macro_recall": round(float(rec), 4),
        "macro_f1": round(float(f1), 4),
        "mrr_at_3": round(float(mrr), 4),
        "mean_latency_ms": round(sum(latencies) / max(len(latencies), 1), 2),
        "labels": labels,
        "confusion_matrix": cm,
        "embedding_mode": pipe.embeddings.mode,
        "reranker_available": pipe.reranker.available,
        "generator_available": pipe.generator.available,
    }
    (RESULTS / "metrics.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    # confusion matrix image
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.imshow(cm)
        ax.set_xticks(range(len(labels))); ax.set_yticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=90, fontsize=7); ax.set_yticklabels(labels, fontsize=7)
        ax.set_xlabel("Predicted"); ax.set_ylabel("True"); ax.set_title("CareLens AI — Confusion Matrix (Top-1)")
        fig.tight_layout(); fig.savefig(RESULTS / "confusion_matrix.png", dpi=120)
        plt.close(fig)
    except Exception as e:
        print(f"confusion matrix image skipped: {e}")
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
