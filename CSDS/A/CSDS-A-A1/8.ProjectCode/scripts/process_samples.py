"""Process the sample policy PDFs and export the results to data/processed/.

Usage (from the project root, with the backend stopped):
    venv\\Scripts\\python scripts\\process_samples.py            # process new PDFs, then export all
    venv\\Scripts\\python scripts\\process_samples.py --reparse  # re-parse every sample (keeps cached AI output)
    venv\\Scripts\\python scripts\\process_samples.py --export-only

For each PDF in data/policies/ this runs the real product pipeline - PyMuPDF parsing, clause
segmentation, dense indexing and Gemini Policy Card extraction - then writes:

    data/processed/<slug>/document.json   file, hash, pages, insurer, product, UIN, parse statistics
    data/processed/<slug>/clauses.jsonl   one clause per line (text, pages, highlight boxes)
    data/processed/<slug>/card.json       Policy Card, summary and risk highlights, with the model used

The committed export lets a fresh install show complete sample policies without any API calls.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy import select  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.db import SessionLocal, init_db  # noqa: E402
from app.core.logging import configure_logging  # noqa: E402
from app.models import Document, PolicyCard, RiskFlag  # noqa: E402


def export_document(doc: Document, out_root: Path) -> Path:
    slug = doc.sample_slug or Path(doc.file_name).stem
    folder = out_root / slug
    folder.mkdir(parents=True, exist_ok=True)
    meta = {
        "slug": slug, "file_name": doc.file_name, "file_path": doc.file_path, "sha256": doc.sha256,
        "size_bytes": doc.size_bytes, "page_count": doc.page_count, "insurer": doc.insurer,
        "product_name": doc.product_name, "uin": doc.uin, "parse_stats": doc.parse_stats,
        "index_version": doc.index_version,
        "processed_at": doc.processed_at.isoformat() if doc.processed_at else None,
    }
    (folder / "document.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with (folder / "clauses.jsonl").open("w", encoding="utf-8") as fh:
        for c in doc.clauses:
            fh.write(json.dumps({
                "ordinal": c.ordinal, "clause_ref": c.clause_ref, "heading": c.heading,
                "section_path": c.section_path, "text": c.text, "page_start": c.page_start,
                "page_end": c.page_end, "bboxes": c.bboxes, "word_count": c.word_count,
            }, ensure_ascii=False) + "\n")
    with SessionLocal() as db:
        card = db.scalar(select(PolicyCard).where(PolicyCard.document_id == doc.id))
        risks = db.scalars(select(RiskFlag).where(RiskFlag.document_id == doc.id)).all()
        if card is not None:
            payload = {
                "model": card.model, "prompt_version": card.prompt_version, "verified_ratio": card.verified_ratio,
                "latency_ms": card.latency_ms, "created_at": card.created_at.isoformat(),
                "data": card.data, "summary": card.summary,
                "risks": [{"title": r.title, "category": r.category, "severity": r.severity,
                           "explanation": r.explanation, "clause_ordinal": r.clause_ordinal, "page": r.page,
                           "quote": r.quote, "source": r.source, "rule_id": r.rule_id} for r in risks],
            }
            (folder / "card.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                                              encoding="utf-8")
    return folder


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reparse", action="store_true", help="re-run the full pipeline for every sample")
    parser.add_argument("--export-only", action="store_true", help="only export what is already processed")
    parser.add_argument("--rebuild-risks", action="store_true",
                        help="recompute risk highlights from the stored Policy Cards (no API calls)")
    parser.add_argument("--reextract", choices=["lite", "all"],
                        help="re-run Gemini extraction for cards made by a Flash-Lite fallback ('lite') or for all")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    configure_logging()
    init_db()
    settings = get_settings()
    from app.services import ingestion
    from app.services.seed import queue_raw_sample

    if not args.export_only:
        ingestion.start_worker()
        for pdf in sorted(settings.policies_dir.glob("*.pdf")):
            doc_id = queue_raw_sample(pdf)
            if args.reparse:
                ingestion.enqueue(doc_id, "full")
        if args.reextract:
            with SessionLocal() as db:
                for card in db.scalars(select(PolicyCard)).all():
                    if args.reextract == "all" or "lite" in card.model:
                        print(f"Re-extracting document {card.document_id} (was {card.model})", flush=True)
                        ingestion.enqueue(card.document_id, "reextract")
        start = time.time()
        print("Processing samples - this takes a few minutes (parsing, indexing, AI extraction)...", flush=True)
        ingestion.wait_until_idle(timeout=3600)
        print(f"Done in {time.time() - start:.0f}s", flush=True)

    if args.rebuild_risks:
        from app.ml.retrieval.clause_cache import load_clauses
        from app.services.extractor import save_card
        from app.services.risk_engine import build_risks

        with SessionLocal() as db:
            cards = db.scalars(select(PolicyCard)).all()
            for card in cards:
                ai = [{"title": r.title, "severity": r.severity, "category": r.category, "explanation": r.explanation,
                       "clause_ordinal": r.clause_ordinal, "page": r.page, "quote": r.quote, "source": "ai"}
                      for r in db.scalars(select(RiskFlag).where(RiskFlag.document_id == card.document_id,
                                                                 RiskFlag.source == "ai")).all()]
                risks = build_risks(card.data, ai, load_clauses(card.document_id))
                save_card(card.document_id, card.data, card.summary, risks, model=card.model,
                          latency_ms=card.latency_ms, prompt_version=card.prompt_version)
                print(f"[OK]   Rebuilt {len(risks)} risk highlights for document {card.document_id}")

    out_root = settings.processed_dir
    with SessionLocal() as db:
        docs = db.scalars(select(Document).where(Document.is_sample.is_(True)).order_by(Document.id)).all()
        for doc in docs:
            status = f"{doc.status}" + (f" (card error: {doc.extraction_error})" if doc.extraction_error else "")
            if doc.status != "ready":
                print(f"[SKIP] {doc.file_name}: {status} {doc.error or ''}")
                continue
            folder = export_document(doc, out_root)
            has_card = (folder / "card.json").exists()
            print(f"[OK]   {doc.file_name}: {len(doc.clauses)} clauses, card={'yes' if has_card else 'no'} "
                  f"-> {folder.relative_to(ROOT)} {status if not has_card else ''}")
    ingestion.stop_worker()
    return 0


if __name__ == "__main__":
    sys.exit(main())
