# ClauseGuard

Contract complexity scoring and predatory-clause detection for Indian agreements, with
plain-language explanations. Upload a PDF or DOCX contract and get a clause-by-clause risk
breakdown, an overall complexity grade, and safer alternative wording for anything flagged.

## Features

- **Upload & segment** - PDF/DOCX parsed into clauses with page numbers (PyMuPDF / python-docx).
- **Clause classification** - each clause labelled with a CUAD-style type via Gemini embeddings +
  nearest-centroid search, with Gemini as a tie-breaker.
- **Predatory-clause detection** - 8 curated Indian contract-law rules (restraint of trade,
  penalty vs liquidated damages, unilateral termination, unlimited liability, one-sided
  arbitration, auto-renewal, IP overreach, no-refund) with reason, quoted provision, and safer
  wording for every flag.
- **Risky combinations** - a NetworkX clause graph flags combinations that are harmless alone but
  dangerous together (e.g. unilateral termination + no-refund + penalty).
- **Complexity score** - readability, legalese density, cross-references and sentence length,
  shown as an A-F grade.
- **Plain-language summary** - key obligations and overall risk picture for the whole contract.
- **Evaluation** - clause classification scored on CUAD, predatory detection scored on a curated
  Indian-law test set, reported separately.

## Quick start

```bat
setup.bat
```

Then set `GEMINI_API_KEY` in `.env` (get a free key at https://aistudio.google.com/apikey), and:

```bat
run.bat
```

Opens the app at `http://localhost:5106` (backend on `http://localhost:8106`). Full instructions,
including troubleshooting, are in `docs/03_HOW_TO_RUN.md`.

## Demo login

No pre-seeded account - click **Sign up** on the landing page and register with any email and a
6+ character password. Every result comes from the real pipeline; there is no fake/mocked data
path.

## Evaluation results

From `experiments/eval/metrics.json` (regenerate with `venv\Scripts\python.exe ml\eval.py`):

**Predatory-clause detection** (40 curated Indian-law test examples, rule-based, no API needed):

| Metric | Score |
|---|---|
| Precision | 1.00 |
| Recall | 0.94 |
| F1 | 0.97 |

**CUAD clause classification** (240 held-out examples across 20 categories): not yet computed in
this environment - it requires a real `GEMINI_API_KEY`. Add your key to `.env` and re-run
`ml/eval.py`; the Evaluation screen and this metrics file will fill in automatically.

## Tech stack

React + Vite (JavaScript) + Tailwind on the frontend; FastAPI + SQLAlchemy 2 + SQLite on the
backend; Gemini for embeddings, clause classification, explanations and summaries; NumPy as a
local vector store; NetworkX for the clause graph. See `docs/02_HOW_IT_WORKS.md` for the full
pipeline and the reasoning behind these choices (a fast, dependency-light build - no
pgvector/Neo4j/ChromaDB).

## Documentation index

- `docs/01_OVERVIEW.md` - what ClauseGuard does and who it's for
- `docs/02_HOW_IT_WORKS.md` - pipeline, storage, data sources, evaluation methodology
- `docs/03_HOW_TO_RUN.md` - setup, run, smoke test, evaluation, troubleshooting
- `docs/PLAN.md` - architecture/endpoint/table plan written before the build

## Defaults chosen during the build

- Python 3.10.11 was used (the only interpreter available in this environment); the stack is
  fully compatible despite the spec's 3.11+ suggestion.
- CUAD v1 (~40 MB) is committed in full at `data/cuad/CUADv1.json` rather than as a sample, since
  it comfortably fits the "commit in full" size rule.
- Classification targets a 20-category substantive subset of CUAD's 41 categories (excludes
  purely administrative categories like Document Name/Parties/Agreement Date).
- No git remote was configured in this environment, so commits made during the build are local
  only - push to your own remote when ready.
