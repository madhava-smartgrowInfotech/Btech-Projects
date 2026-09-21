"""Answer quality: accuracy (key facts), citation accuracy, abstention, faithfulness and latency.

Every question goes through the product's real answer pipeline (hybrid retrieval -> Gemini ->
citation check -> NLI faithfulness). Gemini responses are cached on disk, so re-running the
evaluation does not spend quota twice for identical requests.
"""

from __future__ import annotations

import statistics
from typing import Any

from ml import common  # noqa: F401
from ml.metrics import citation_hit, key_fact_match, latency_stats

BINS = [("0-49", 0, 50), ("50-79", 50, 80), ("80-100", 80, 101)]
_SCRIPTS = {"hi": (0x0900, 0x097F), "te": (0x0C00, 0x0C7F)}


def _in_script(text: str, lang: str) -> bool:
    if lang not in _SCRIPTS:
        return True
    lo, hi = _SCRIPTS[lang]
    letters = [c for c in text if c.isalpha()]
    native = sum(1 for c in letters if lo <= ord(c) <= hi)
    return bool(letters) and native / len(letters) >= 0.4


def _answer(doc_id: int, question: str, language: str) -> Any:
    from app.services.answerer import answer_question

    return answer_question(doc_id, question, language, [], None, cache=True)


def run(doc_ids: dict[str, int], items: list[dict[str, Any]], log=print, run=None) -> tuple[dict, list[dict]]:  # noqa: ANN001,A002
    done = {p["id"]: p for p in (run.load_predictions("answers.jsonl") if run else [])}
    rows: list[dict] = []
    for item in items:
        if item["id"] in done:
            rows.append(done[item["id"]])
            continue
        language = item.get("language", "en")
        try:
            result = _answer(doc_ids[item["policy"]], item["question"], language)
        except Exception as exc:  # noqa: BLE001 - record the failure and continue
            log(f"answer {item['id']}: ERROR {exc}")
            row = {"id": item["id"], "error": str(exc)[:300]}
            rows.append(row)
            continue
        cited_pages = [c["page"] for c in result.citations] + [c.get("page_end", c["page"]) for c in result.citations]
        cited_texts = [c["quote"] for c in result.citations]
        from app.ml.retrieval.clause_cache import load_clauses

        clause_text = {c.ordinal: c.text for c in load_clauses(doc_ids[item["policy"]])}
        cited_full = [clause_text.get(c["ordinal"], "") for c in result.citations]
        row = {
            "id": item["id"],
            "policy": item["policy"],
            "category": item["category"],
            "language": language,
            "answerable": item["answerable"],
            "question": item["question"],
            "status": result.status,
            "answer_en": result.answer_en,
            "answer": result.answer if language != "en" else None,
            "key_fact_recall": key_fact_match(result.answer_en, item.get("key_facts", [])) if item["answerable"] else None,
            "citation_correct": citation_hit(cited_pages, cited_texts + cited_full, item.get("pages", []),
                                             item.get("evidence", [])) if item["answerable"] else None,
            "in_language": _in_script(result.answer, language),
            "faithfulness": result.faithfulness.get("score"),
            "citations": [{"ordinal": c["ordinal"], "page": c["page"], "label": c["label"]} for c in result.citations],
            "timings": result.timings,
            "model": result.model,
            "cached": result.extra.get("cached", False),
        }
        rows.append(row)
        if run:
            run.append_prediction(row, "answers.jsonl")
        log(f"answer {item['id']}: status={row['status']} facts={row['key_fact_recall']} "
            f"cite={row['citation_correct']} faith={row['faithfulness']} ms={result.timings.get('total_ms')}")
    return summarise(rows), rows


def summarise(rows: list[dict]) -> dict:
    ok = [r for r in rows if "error" not in r]
    english = [r for r in ok if r.get("language", "en") == "en"]
    answerable = [r for r in english if r["answerable"]]
    unanswerable = [r for r in english if not r["answerable"]]
    correct = [r for r in answerable if r["status"] != "not_in_policy" and (r["key_fact_recall"] or 0) >= 1.0]
    faith = [r["faithfulness"] for r in ok if r["faithfulness"] is not None]
    by_category: dict[str, dict] = {}
    for r in answerable:
        cat = by_category.setdefault(r["category"], {"n": 0, "correct": 0})
        cat["n"] += 1
        cat["correct"] += int(r in correct)
    for cat in by_category.values():
        cat["accuracy"] = round(cat["correct"] / cat["n"], 4)
    multilingual = [r for r in ok if r.get("language", "en") != "en"]
    stage = {}
    for key in ("retrieval_ms", "generation_ms", "faithfulness_ms", "translate_ms"):
        values = [r["timings"].get(key) for r in ok if r.get("timings") and r["timings"].get(key) is not None]
        if values and any(values):
            stage[key.replace("_ms", "")] = latency_stats(values)
    return {
        "n": len(rows),
        "errors": len(rows) - len(ok),
        "answerable": len(answerable),
        "answer_accuracy": round(len(correct) / len(answerable), 4) if answerable else None,
        "key_fact_recall": round(statistics.fmean(r["key_fact_recall"] or 0 for r in answerable), 4) if answerable else None,
        "citation_accuracy": round(sum(1 for r in answerable if r["citation_correct"]) / len(answerable), 4)
        if answerable else None,
        "faithfulness": {
            "mean": round(statistics.fmean(faith), 1) if faith else None,
            "median": round(statistics.median(faith), 1) if faith else None,
            "bins": [{"bin": label, "count": sum(1 for f in faith if lo <= f < hi)} for label, lo, hi in BINS],
        },
        "abstention": {
            "n": len(unanswerable),
            "accuracy": round(sum(1 for r in unanswerable if r["status"] == "not_in_policy") / len(unanswerable), 4)
            if unanswerable else None,
            "false_abstentions": sum(1 for r in answerable if r["status"] == "not_in_policy"),
        },
        "multilingual": {
            "n": len(multilingual),
            "in_requested_language": round(sum(1 for r in multilingual if r["in_language"]) / len(multilingual), 4)
            if multilingual else None,
            "key_fact_recall": round(statistics.fmean(r["key_fact_recall"] or 0 for r in multilingual), 4)
            if multilingual else None,
        },
        "latency_ms": latency_stats([r["timings"].get("total_ms") for r in ok if r.get("timings")]),
        "stage_latency_ms": stage,
        "by_category": by_category,
    }
