# CareLens AI

CareLens AI is a local web-based symptom-monitoring and preliminary health-guidance assistant. Describe symptoms in everyday language and receive grounded, evidence-backed health information with clear safety guidance.

## Key capabilities

- Secure local accounts (bcrypt hashing, signed sessions)
- Conversational symptom analysis with hybrid retrieval (FAISS + BM25), cross-encoder reranking, and grounded local generation
- Possible-condition cards, contributing-symptom evidence, match-relevance display, safety escalation
- Consultation history with search, detail view, and deletion — stored locally in SQLite

## Architecture

`symptoms → preprocessing → HyDE-style local expansion → embeddings → hybrid retrieval → fusion → rerank → grounded generation → safety filter → UI + SQLite`

## Technology stack

React + Vite (frontend, kit V2 "Neo Brutal Grid"), Python, FastAPI, Uvicorn, SQLite, SQLAlchemy, Pydantic, Jinja2, Sentence Transformers (`all-MiniLM-L6-v2`), FAISS CPU, rank-bm25, Cross-Encoder (`ms-marco-MiniLM-L-6-v2`), Flan-T5 small with evidence-based fallback, scikit-learn, pandas, numpy.

## Data pipeline

`scripts/prepare_data.py` builds a normalized knowledge base (`record_id, disease, symptoms, description, guidance, severity, red_flags, source`) at `data/processed/`, with canonical retrieval text `Disease: ... Symptoms: ... Description: ... Guidance: ...`. The bundled knowledge base is a clearly labeled synthetic fallback (see `source_type: synthetic`) used when the public download is unavailable; the same pipeline works with a downloaded CSV.

## Retrieval pipeline

Candidate pool (~15) from FAISS semantic and BM25 lexical paths, min-max normalized fusion (`0.65 * semantic + 0.35 * lexical`, configurable), reranked to top-5. Scores are shown to users as a simple match-relevance indicator.

## Safety design

Rule-based emergency detection (chest pain, breathing difficulty, bleeding, unconsciousness, stroke-like signs, anaphylaxis, self-harm, seizures, severe abdominal pain) with prominent urgent-care advice plus a permanent non-diagnosis disclaimer. No medication prescriptions.

## Evaluation

`scripts/evaluate.py` holds out one record per condition and reports Top-1/Top-3 accuracy, macro precision/recall/F1, Recall@3, MRR, latency, and a confusion-matrix image in `results/`. Only these measured values are reported.

## Project structure

See the repository layout: `app/` (FastAPI + RAG pipeline + legacy templates/static), `frontend/` (React app), `docs/` (plan + screenshots), `data/`, `scripts/`, `tests/`, `results/`, `screenshots/`.

## Quick start

Double-click `run.bat`, then use `http://localhost:5412` (API on 8412). Demo login: `demo@carelens.ai` / `Demo@1234`. Details in `HOW_TO_RUN.md`.

## Limitations

Preliminary information only — not a diagnosis. The knowledge base is limited; similarity is not medical probability. Always consult a qualified professional; in emergencies seek immediate care.

## Responsible use

Private by design: local SQLite storage, no paid external APIs for symptom data, no trackers, per-user history isolation, deletion supported.
