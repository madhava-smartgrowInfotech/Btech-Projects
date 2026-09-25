# ClauseGuard - How it works

## Pipeline (backend/app/services/pipeline.py)

1. **Parse** (`services/parsing.py`) - PyMuPDF extracts PDF text per page; python-docx extracts
   DOCX text (treated as a single page, since python-docx has no native page breaks). Numbered
   headings (`1.`, `Section 2.1`, ...) split the page into clauses; if fewer than two headings are
   found, the page falls back to paragraph-grouping.
2. **Classify** (`services/classification.py`, F2) - each clause is embedded with the Gemini
   embedding model (`models/text-embedding-004`). Classification is nearest-centroid: one
   centroid embedding per CUAD-style category, built once from `data/sample/cuad_train_examples.json`
   and cached to `data/cuad_centroids.npz`. When the top two candidates are close
   (cosine-similarity gap < 0.03) and not confident, Gemini `generateContent` breaks the tie by
   picking among the top 3 candidates given the clause text.
3. **Detect predatory clauses** (`services/rules.py`, F3) - a curated set of 8 deterministic
   regex-based rules grounded in Indian contract law (Indian Contract Act 1872 Sections 27/28/74,
   Arbitration and Conciliation Act 1996, Copyright Act 1957, Consumer Protection Act 2019). The
   rule engine is auditable and reproducible; Gemini is only used afterwards
   (`services/explain.py`) to write the plain-language reason, quote the triggering provision, and
   draft safer wording for each flagged clause - so nothing is hard-coded, but the risky/not-risky
   decision itself is not left to the LLM.
4. **Detect risky combinations** (`services/graph.py`, F4) - a NetworkX graph is built per
   contract with one node per clause. Three curated combination patterns (e.g. unilateral
   termination + no-refund + penalty) are checked against the set of rule ids present anywhere in
   the contract; matches produce edges between the involved clauses.
5. **Score complexity** (`services/complexity.py`, F5) - Flesch reading ease, legalese-term
   density (curated legal-jargon list), cross-reference count (regex for "Section X", "herein",
   etc.) and average sentence length are combined into a weighted 0-100 difficulty score, then
   bucketed into a letter grade A-F.
6. **Summarize** (`services/explain.py`, F6) - Gemini writes a plain-language summary and key
   obligations list from the clause texts and the flags already detected.

## Storage

- SQLite (SQLAlchemy 2 models in `backend/app/db.py`): users, contracts, clauses, flags.
- Clause embeddings are stored as raw float32 blobs in SQLite and compared with NumPy cosine
  similarity (`services/vectorstore.py`) - this is the "local vector store" called for in
  `MASTER_PROMPT_FAST.md` section 6 (no ChromaDB/pgvector).
- The clause graph (F4) is rebuilt on demand from stored flags rather than persisted, since it is
  cheap to compute and always derived from the same source of truth (the `flags` table).

## Data sources

| Source | Licence | What's committed |
|---|---|---|
| CUAD v1 (Atticus Project), via `github.com/TheAtticusProject/cuad` (same source as the HF mirror `theatticusproject/cuad-qa`) | CC BY 4.0 | Full corpus at `data/cuad/CUADv1.json` (~40 MB, fits the "commit in full" size rule). `scripts/download_data.py` re-fetches it if missing. |
| Derived CUAD samples | derived from the above | `data/sample/cuad_train_examples.json` (500 examples, 20 categories, seed 42) used to build classification centroids; `data/sample/cuad_eval_set.json` (240 held-out examples) used by `ml/eval.py` for F7. Built by `scripts/build_cuad_samples.py`. |
| Indian predatory-clause rules | authored for this project | `backend/app/services/rules.py` |
| Predatory-detection test set | authored for this project | `data/sample/predatory_test_set.json` (40 labelled clauses) used by `ml/eval.py` for F7 |

CUAD covers 41 clause categories; ClauseGuard classifies against a 20-category substantive subset
(excludes purely administrative categories like Document Name/Parties/Agreement Date, which are
metadata rather than clause types) - see `CATEGORIES` in `scripts/build_cuad_samples.py`.

## Evaluation (F7, `ml/eval.py`)

Two scores are reported **separately**, matching objective 6:

- **Predatory-clause detection**: precision/recall/F1 (overall and per-rule) of the rule engine
  against `data/sample/predatory_test_set.json`. Rule-based, so this runs without any API key.
- **CUAD clause classification**: top-1 and top-3 accuracy of the embedding + tie-break
  classifier against `data/sample/cuad_eval_set.json`. Requires `GEMINI_API_KEY` (calls the
  embedding API once per held-out example).

Results are written to `experiments/eval/metrics.json` and served at `GET /api/eval/metrics` for
the Evaluation screen.
