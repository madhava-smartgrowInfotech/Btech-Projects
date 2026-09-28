# TaxSentinel - build plan

**Architecture:** React (Vite, Tailwind) on :5105 -> FastAPI on :8105 -> in-memory pipeline state (pickled to `data/workspace/`) + SQLite (`data/app.db`). Gemini writes case narratives.

**Pipeline (`ml/`):** seeded generator -> feature layers (invoice / behaviour / network per taxpayer-month) -> JEPA encoder (PyTorch, CPU) -> NetworkX cycles, shared-identity clusters, Louvain communities -> invoice anomaly flags -> noisy-OR risk per taxpayer and invoice chain -> evidence list (E1..En) -> evaluation vs injected labels and a rule baseline.

**Endpoints:**
- `POST /api/auth/register|login`, `GET /api/auth/me`
- `POST /api/pipeline/run`, `GET /api/pipeline/status|runs`
- `GET /api/overview`, `GET /api/taxpayers`, `GET /api/taxpayers/{gstin}`
- `GET /api/chains`, `GET /api/chains/{id}`, `GET /api/structures`, `GET /api/graph?focus|ring|cluster|chain`
- `POST /api/explanations/{gstin}`, `GET /api/metrics`, `GET /api/health`

**Tables:** `users`, `pipeline_runs`, `explanations`.

**Screens:** Landing, Login/Register, Overview, Taxpayers (ranking + profile), Fraud-ring graph, Case detail (evidence + written explanation), Model performance.

**Data:** synthetic GST ecosystem from `scripts/generate_gst_data.py` (seed 42, 600 taxpayers, 12 months, committed); PaySim 100k-row sample (`scripts/download_data.py`), used as a transfer check for the JEPA module in evaluation.

**Fraud patterns injected:** shell entities (shared address/contact), fake invoices bought from shells, circular trading rings (3-5 parties), ITC spikes above GSTR-2B.
