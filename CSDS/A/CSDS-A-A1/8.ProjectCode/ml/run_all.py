"""Run the full PolicyLens evaluation and write experiments/eval-YYYYMMDD-HHMM/.

Usage (from the project root, with the backend stopped):
    venv\\Scripts\\python ml\\run_all.py                  # everything (uses Gemini for answers + claims)
    venv\\Scripts\\python ml\\run_all.py --skip-llm       # retrieval + extraction only (no API calls)
    venv\\Scripts\\python ml\\run_all.py --run-name eval-20260921-2330   # resume / re-plot an earlier run

Outputs: metrics.json, retrieval.jsonl, answers.jsonl, claims.jsonl, extraction.jsonl, eval.log and
plots/*.png. experiments/latest.json points the in-app "Model performance" page at the newest run.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ml import common  # noqa: E402
from ml.experiment import ExperimentRun  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run-name", help="reuse this run folder (resumes answers/claims already done)")
    parser.add_argument("--skip-llm", action="store_true", help="skip the Gemini-based answer and claim evaluation")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    run = ExperimentRun.create("eval", name=args.run_name)
    log = run.logger.info
    doc_ids = common.prepare_app()
    log(f"Sample documents: {doc_ids}")

    from app.core.config import get_settings
    from app.ml.retrieval import hybrid
    from app.services import answerer
    from ml import eval_answers, eval_claims, eval_extraction, eval_retrieval, plots

    items = common.load_jsonl("qa.jsonl")
    multilingual = common.load_jsonl("qa_multilingual.jsonl")
    scenarios = common.load_jsonl("claims.jsonl")
    truth = common.load_json("cards.json")

    def write_rows(name: str, rows: list[dict]) -> None:
        with (run.path / name).open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")

    log("== Retrieval ablation")
    retrieval, rows = eval_retrieval.run(doc_ids, items, log)
    run.update_metrics("retrieval", retrieval)
    write_rows("retrieval.jsonl", rows)

    log("== Policy Card extraction")
    extraction, rows = eval_extraction.run(doc_ids, truth, log)
    run.update_metrics("extraction", extraction)
    write_rows("extraction.jsonl", rows)

    answer_rows: list[dict] = []
    if not args.skip_llm:
        log("== Answers (Gemini + faithfulness)")
        answers, answer_rows = eval_answers.run(doc_ids, items + multilingual, log, run)
        run.update_metrics("answers", answers)
        log("== Claim Copilot scenarios")
        claims, _ = eval_claims.run(doc_ids, scenarios, log, run)
        run.update_metrics("claims", claims)

    s = get_settings()
    m = run.metrics
    answers_m = m.get("answers") or {}
    used_models = Counter(r.get("model") for r in answer_rows if r.get("model"))
    m["headline"] = {
        "retrieval_hit_at_5": (m.get("retrieval") or {}).get("hybrid_rerank", {}).get("hit@5"),
        "answer_accuracy": answers_m.get("answer_accuracy"),
        "citation_accuracy": answers_m.get("citation_accuracy"),
        "faithfulness_mean": (answers_m.get("faithfulness") or {}).get("mean"),
        "abstention_accuracy": (answers_m.get("abstention") or {}).get("accuracy"),
        "latency_p50_ms": (answers_m.get("latency_ms") or {}).get("p50_ms"),
        "extraction_accuracy": (m.get("extraction") or {}).get("accuracy"),
        "claim_verdict_accuracy": (m.get("claims") or {}).get("accuracy"),
    }
    m["models"] = [
        {"role": "Answers, claims, comparison", "model": ", ".join(used_models) or s.gemini_model,
         "purpose": "Grounded generation with JSON schema output"},
        {"role": "Policy Card extraction", "model": ", ".join(extraction.get("models", [])) or s.gemini_model,
         "purpose": "Schema-constrained long-context extraction"},
        {"role": "Dense embeddings", "model": "sentence-transformers/all-MiniLM-L6-v2", "purpose": "Semantic retrieval"},
        {"role": "Re-ranker", "model": "cross-encoder/ms-marco-MiniLM-L6-v2", "purpose": "Re-ranking fused candidates"},
        {"role": "Faithfulness (NLI)", "model": "cross-encoder/nli-deberta-v3-xsmall", "purpose": "Claim support score"},
        {"role": "Keyword search", "model": "BM25Okapi (k1=1.4, b=0.7)", "purpose": "Exact-term retrieval"},
        {"role": "Vector store", "model": "ChromaDB (cosine, persistent)", "purpose": "Dense index"},
    ]
    run.save(
        dataset={
            "qa_items": len(items),
            "answerable": sum(1 for i in items if i["answerable"]),
            "unanswerable": sum(1 for i in items if not i["answerable"]),
            "multilingual_items": len(multilingual),
            "claim_scenarios": len(scenarios),
            "card_checks": sum(len(v) for k, v in truth.items() if not k.startswith("_")),
            "policies": len(doc_ids),
            "split": "Held-out test set - every item is used only for evaluation (no model is trained)",
            "source": "data/eval/ - written by hand from the policy wordings in data/policies/",
        },
        settings={
            "answer_top_k": answerer.TOP_K,
            "candidates_per_retriever": hybrid.CANDIDATES,
            "rerank_pool": hybrid.RERANK_POOL,
            "rrf_k": 60,
            "abstain_below_rerank": answerer.ABSTAIN_BELOW,
            "gemini_model": s.gemini_model,
            "gemini_fallback_models": ", ".join(s.gemini_fallback_models),
            "thinking_level": "low",
            "temperature": 0.2,
            "embedding_provider": s.embedding_provider,
        },
    )
    made = plots.make_all(m, run.plot_path("x").parent)
    m["plots"] = made
    run.save()
    run.mark_latest()
    log(f"Headline: {json.dumps(m['headline'])}")
    log(f"Done -> {run.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
