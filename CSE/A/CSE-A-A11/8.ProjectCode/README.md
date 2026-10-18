# AutoSecAI v2 — Autonomous PR analysis (pure Python)

Implements the abstract (multi-agent PR security review + codebase intelligence) on top of the base paper
*Leveraging Key Source Code Metrics for Predicting Software Vulnerabilities With ML* (IEEE Access 2026).

## Run (new web app)
    run.bat                       # API :8311 + React app :5311 - see docs/03_HOW_TO_RUN.md
Demo sign-in: `demo@autosecai.dev` / `Demo@1234`. The original Streamlit UI still runs with `run_streamlit.bat`.

## Run (original Streamlit UI)
    pip install -r requirements.txt
    streamlit run app.py          # or double-click run_streamlit.bat
    python -m pytest tests -q     # 10 tests

The first launch trains the models (~30 s) into `autosecai/artifacts/`.

## Layout
| File | Role |
|---|---|
| `app.py` | Streamlit UI: Overview, PR Review, Codebase Assistant, Model Lab, History, About |
| `autosecai/agents.py` | 7-agent pipeline: ingestion, static, ML risk, reasoner, remediation (verified patches), quality, judge |
| `autosecai/rules.py` | AST + taint engine (SQLi, CMDi, XSS, path traversal, deserialization, SSRF, secrets, crypto…) + regex rules for JS/PHP/Java |
| `autosecai/metrics.py`, `dataset.py`, `mlmodel.py` | Base paper: 14 metrics, 7 feature selectors, SmoteTomek, 9 models, type classifier |
| `autosecai/codeintel.py` | TF-IDF + concept + import/call-graph retrieval for repo Q&A |
| `backend/` | FastAPI layer (reviews, codebase, lab, auth) over the package above |
| `frontend/` | React + Tailwind app (kit V1 Aurora Glass) |
| `autosecai/diffutil.py`, `report.py`, `store.py` | Diff/GitHub/zip ingestion, MD/SARIF/JSON/CSV export, SQLite history |

## Inputs
Demo PR · pasted/uploaded diff · before/after versions · GitHub PR URL · uploaded files/zip/folder.

## Honest notes
- ML corpus is *generated* Python code (paper's C datasets are unavailable); metrics are real AST measurements. Results differ from the paper's.
- Optional Claude explanations: set an API key in the sidebar (off by default; nothing leaves the machine otherwise).
