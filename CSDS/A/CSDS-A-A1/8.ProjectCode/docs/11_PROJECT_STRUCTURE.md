# Project structure

```
./
├── backend/                  FastAPI application (Python 3.11)
│   ├── app/
│   │   ├── main.py           App factory: CORS, error handlers, request log, start-up (DB, seed, worker, warm-up)
│   │   ├── api/              REST routers (one file per area) - see 06_API_REFERENCE.md
│   │   ├── core/             config (.env), db (SQLite/SQLAlchemy), security (JWT, bcrypt), logging, errors
│   │   ├── models/           SQLAlchemy tables: user, document (+clauses, card, risks), policy, chat, claim, comparison, translation, llm_call
│   │   ├── schemas/          Pydantic request/response models and the Policy Card extraction schema
│   │   ├── services/         Business logic (below)
│   │   └── ml/               Local models and retrieval (below)
│   ├── tests/                pytest suite + deterministic test-PDF generator (fixtures.py)
│   ├── requirements.txt
│   └── pytest.ini
├── frontend/                 React 18 + Vite + TypeScript web app
│   ├── src/
│   │   ├── main.tsx, App.tsx Providers and routes
│   │   ├── pages/            Landing, Login, Register, Dashboard, Policies, PolicyView, Chat, ClaimCopilot, Compare, ModelPerformance, Settings, NotFound
│   │   ├── components/
│   │   │   ├── ui/           shadcn/ui components (Radix based)
│   │   │   ├── reactbits/    React Bits effects: Aurora, BlurText, ShinyText, SpotlightCard
│   │   │   ├── layout/       App shell (sidebar, mobile sheet, top bar), auth layout
│   │   │   ├── brand/        Logo
│   │   │   ├── common/       States (loading/empty/error), badges, page header, stat tile, dialogs, language picker
│   │   │   ├── charts/       Chart card with table view and tooltip (Recharts)
│   │   │   ├── policy/       Upload, processing steps, Policy Card, risks, PDF page viewer, clause search, source chips
│   │   │   ├── chat/         Answer renderer with citation chips, faithfulness badge, citation sheet
│   │   │   └── claims/       Claim Copilot result
│   │   └── lib/              API client, auth, theme, TanStack Query hooks, types, i18n, utils
│   ├── public/favicon.svg
│   ├── index.html, vite.config.ts, tsconfig*.json, components.json, package.json
├── ml/                       Evaluation (no training is needed)
│   ├── run_all.py            Runs everything, writes experiments/<run>/ and experiments/latest.json
│   ├── eval_retrieval.py     BM25 vs dense vs hybrid vs hybrid+re-rank
│   ├── eval_answers.py       Answer accuracy, citations, abstention, faithfulness, latency, multilingual
│   ├── eval_claims.py        Claim Copilot verdicts + confusion matrix
│   ├── eval_extraction.py    Policy Card fields vs hand-checked values
│   ├── metrics.py, plots.py, experiment.py, common.py
├── notebooks/
│   └── evaluation_report.ipynb   Reproduces the tables and plots from the latest run
├── experiments/              One folder per evaluation run (metrics.json, *.jsonl predictions, eval.log, plots/*.png) + latest.json
├── models/
│   ├── manifest.json         Local model IDs, revisions, licences, sizes
│   └── hf/                   Downloaded weights (git-ignored, created by setup)
├── data/
│   ├── policies/             Sample policy wording PDFs
│   ├── processed/            Parsed clauses + Policy Cards for the samples (loaded at setup, no AI calls)
│   ├── eval/                 Evaluation set (qa.jsonl, qa_multilingual.jsonl, claims.jsonl, cards.json)
│   └── app.db, chroma/, uploads/, pages/, cache/   Created at run time (git-ignored)
├── scripts/
│   ├── check_gemini.py       Test the Gemini key and models
│   ├── download_models.py    Fetch the local models into models/hf
│   ├── init_env.py           Create .env and a JWT secret
│   ├── init_app.py           Database, demo account, samples, search index
│   ├── process_samples.py    Process PDFs in data/policies into data/processed
│   ├── wait_for.py           Used by run.bat to wait for a server
│   └── reset.bat             Wipe run-time data and re-seed
├── docs/                     This documentation (PLAN.md + 01-11)
├── setup.bat, run.bat, stop.bat
├── .env.example              Every setting, documented (copy to .env)
└── README.md
```

## Backend services (`backend/app/services/`)

| File | Role |
|---|---|
| `pdf_parser.py` | PyMuPDF text with positions and fonts; header/footer removal; reading order for two-column pages; table rows; letter-spaced text repair; scan detection |
| `segmenter.py` | Clause detection and heading hierarchy; chunking with highlight boxes; UIN detection |
| `ingestion.py` | Background worker: parse -> index -> extract; status updates; resume after restart |
| `gemini_client.py` | JSON-schema calls, fallback chain with cool-down, pacing, disk cache, usage log, start-up model probe |
| `extractor.py` | Policy Card extraction and quote verification |
| `risk_engine.py` | Rule-based risk highlights + de-duplicated AI findings |
| `answerer.py` | Grounded, cited answers; abstention; citation filtering |
| `claim_copilot.py` / `eligibility.py` | Claim verdict, checklist and steps / calculated waiting-period, co-payment and cost checks |
| `comparator.py` | Plan comparison table and trade-offs |
| `language.py` | Script detection, query translation, cached translation of cards and risks |
| `page_renderer.py` | PDF page -> PNG (cached) |
| `seed.py` | Demo account and sample policies |
| `text_match.py` | Fuzzy text containment used for quote verification and evaluation |

## Backend ML (`backend/app/ml/`)

| File | Role |
|---|---|
| `local_models.py` | Lazy, thread-safe loading of the embedder, re-ranker and NLI model from `models/hf` |
| `embeddings.py` | Local MiniLM or Gemini embeddings |
| `faithfulness.py` | NLI-based claim support score with number checks |
| `retrieval/text.py` | Tokeniser and insurance synonym expansion |
| `retrieval/bm25_index.py` | BM25Okapi per document |
| `retrieval/dense_index.py` | ChromaDB collection per embedding provider |
| `retrieval/fusion.py` | Reciprocal Rank Fusion |
| `retrieval/reranker.py` | Cross-encoder scores |
| `retrieval/hybrid.py` | The four retrieval modes used by the product and the evaluation |
| `retrieval/clause_cache.py` | In-memory clause cache per document |
