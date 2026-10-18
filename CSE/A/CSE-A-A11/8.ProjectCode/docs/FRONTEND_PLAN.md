# AutoSecAI - Frontend plan (kit V1, Aurora Glass)

Ports: backend **8311**, frontend **5311** (from `.env`).
The existing product is a **Streamlit** app (`app.py`) with **no HTTP API**. It stays untouched. A thin FastAPI layer in
`backend/` imports the existing `autosecai.*` functions and exposes them; a new React app lives in `frontend/`.

## 1. Backend inventory (what exists today)

There are no HTTP endpoints. The product logic is a Python package; the Streamlit UI calls it directly.

| Capability | Existing function(s) | Used by Streamlit page |
|---|---|---|
| Parse a unified diff | `diffutil.parse_unified_diff(text)` | PR Review |
| Before/after of one file | `diffutil.diff_from_versions(old, new, path)` | PR Review |
| GitHub PR diff + metadata | `diffutil.fetch_github_pr_diff(url, token)` | PR Review |
| Uploaded files / zip / local folder | `files_from_zip`, `files_from_dir`, `full_files_to_changed` | PR Review, Codebase |
| GitHub repo zip | `diffutil.fetch_github_repo_zip(url, token)` | Codebase |
| 7-agent review pipeline | `agents.review_changes(changed, title, source_label, use_llm, api_key, ml, min_severity, progress)` | PR Review |
| Review history (SQLite) | `store.save / list_reviews / load / delete` | PR Review, History, Overview |
| Exports | `report.to_markdown / to_sarif / to_json / to_csv` | PR Review > Export |
| Repo index + Q&A | `codeintel.RepoIndex(files, name)` -> `.ask()`, `.overview()`, `.onboarding_guide()`, `.file_graph()` | Codebase Assistant |
| Model report | `mlmodel.load_report()`, `load_bundle()["safe_stats"]` | Model Lab, PR Review (radar) |
| Score one function | `metrics.metrics_for_source`, `mlmodel.predict_metrics`, `rules.analyze_source` | Model Lab > Try it |
| Retrain | `mlmodel.train_all()` | Model Lab |
| Demo material | `samples.DEMO_DIFF / BEFORE / AFTER / DEMO_REPO` | Overview, PR Review, Codebase |
| Optional LLM (Anthropic key) | `llm.available / ask` | Settings |

### New HTTP API (`backend/main.py`, FastAPI, port 8311) - thin wrappers only

Everything except `/api/health`, `/api/public/*` and `/api/auth/{login,register,demo}` needs `Authorization: Bearer <jwt>`.

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/api/health` | - | `{status, version}` |
| GET | `/api/public/stats` | - | real numbers from the trained model report (landing page) |
| GET | `/api/public/example` | - | one real finding from the demo PR (landing page) |
| GET | `/api/public/rules` | - | weakness-class titles from the rule knowledge base |
| GET | `/api/auth/demo` | - | the seeded demo credentials |
| POST | `/api/auth/login`, `/api/auth/register` | `{email, password[, name]}` | `{token, user}` |
| GET | `/api/auth/me` | - | current user |
| GET | `/api/meta` | - | version, severities, 7-step pipeline, 14 metrics with safe-function means, suggested questions, llm env flag |
| GET | `/api/samples` | - | demo diff, before/after versions, demo repo file list |
| POST | `/api/reviews` | `{kind: demo-diff / demo-versions / diff / versions / github / folder, title?, diff?, old?, new?, filename?, url?, folder?, options{ml,min_severity,use_llm,api_key,gh_token}}` | `202 {job_id}` |
| POST | `/api/reviews/upload` | multipart `files[]`, `title`, `options` (JSON) | `202 {job_id}` |
| GET | `/api/jobs/{id}` | - | `{status: running/done/error, messages[] (live agent progress), result{review_id,verdict,score}, error, seconds}` |
| GET | `/api/reviews` | `?limit=` | list of `{id, created, title, source, score, verdict, findings, security}` |
| GET | `/api/reviews/{id}` | - | full review object (what `review_changes` returns) |
| DELETE | `/api/reviews/{id}` | - | `{deleted}` |
| GET | `/api/reviews/{id}/export/{md,sarif,json,csv}` | - | file download |
| GET | `/api/reviews/{id}/patched?path=` | - | auto-fixed file download |
| POST | `/api/codebase/index` | `{source: demo / self / folder / github, folder?, url?, gh_token?}` | `{index_id, name, files, units, overview, guide, graph}` |
| POST | `/api/codebase/index/upload` | multipart zip(s) | same |
| GET | `/api/codebase/{index_id}` | - | same payload again |
| POST | `/api/codebase/{index_id}/ask` | `{question, k, use_llm, api_key}` | `{answer, hits[], intents[]}` |
| GET | `/api/lab/report` | - | `load_report()` |
| POST | `/api/lab/analyze` | `{code}` | per-function metrics, probability, type, drivers + static security findings |
| POST | `/api/lab/retrain` | - | `202 {job_id}` (about 30 s) |

Additive pieces that did not exist as functions: the HTTP layer itself, the **login** (the product had none: SQLite users in
`data/app.db`, bcrypt, JWT; a demo account `demo@autosecai.dev` / `Demo@1234` is seeded), the background **job** wrapper that
turns the existing `progress` callback into polled agent messages, the public landing-page reads, and export / patched-file downloads.
Nothing in `autosecai/` changed. "AutoSecAI (this project)" indexing leaves out `frontend/`, `docs/`, `scripts/`, `data/` and `.env`.

## 2. Feature inventory (every Streamlit feature)

**Overview** - hero + 3 feature cards with jump buttons; "How the agents work together" pipeline (7 steps);
"Run demo pull request review" one-click; "Your activity" (reviews, avg risk, blocked).

**PR Review** - five input modes: Demo PR (vulnerable Flask diff / before-after file, with preview), Paste diff (+ upload
.diff/.patch), Compare two versions (title, file name, before, after), GitHub PR link, Upload files / zip / local folder.
Run multi-agent review with live agent progress. Result: verdict banner, risk gauge, KPIs (security findings, critical+high,
quality issues, auto-fixes verified), tabs:
Findings (severity filter, category filter, only-changed-lines toggle, search, donut + CWE bar + per-file bar, finding cards
with explanation / impact / exploit / flow / remediation / safe example / patch / verified / ML corroboration, 50-card cap
note), Function risk (ML table, inspect function, radar vs safe mean, drivers, metrics table), Files (table + function
complexity), Agent trace, Export (PR comment preview, .md, SARIF, JSON, CSV, patched files).

**Codebase Assistant** - repository source (demo shop, this project, upload zip, local folder, GitHub URL), Index
repository, tabs: Ask (suggested questions, chat, hits with code + why chips), Repository map (KPIs, API routes, where
things live, complexity hotspots, module dependency graph), Onboarding guide.

**Model Lab** - header KPIs; data note; tabs: Pipeline & data (steps, 14 metrics, balance chart, type counts), Feature
selection (heatmap, k-curve, votes), Models (grouped bars, table, RF importance), ROC & confusion, Vulnerability types,
Ablation, Try it (paste function -> gauge, type, drivers, metrics, static findings); Retrain models.

**History** - table (created, title, verdict, score, security, findings, id), risk-over-time chart, open a review (full
review view), delete a review.

**About** - project/abstract, base paper, paper-to-product table, known limitations, run locally.

**Settings (Streamlit sidebar)** - ML risk agent toggle, minimum severity, Anthropic API key (optional), LLM explanations
toggle, GitHub token (optional), "runs 100 % locally" note.

## 3. Screen map (new React app)

| Route | Screen | Covers |
|---|---|---|
| `/` | Landing page (Aurora Glass hero, stats strip from the real model report, live example finding, how-it-works, CTA) | new; marketing front door |
| `/login` | Sign in / create account / use the demo account | new (the product had no login) |
| `/app` | Overview | Overview |
| `/app/review` | New PR review | PR Review input modes + run + agent progress |
| `/app/review/:id` | Review result | verdict, KPIs, 5 tabs (Findings, Function risk, Files, Agent trace, Export) |
| `/app/codebase` | Codebase Assistant | index + Ask / Repository map / Onboarding |
| `/app/lab` | Model Lab | all 7 tabs + retrain |
| `/app/history` | History | list, trend, open, delete |
| `/app/settings` | Settings | sidebar settings (persisted in the browser) |
| `/app/about` | About | About |

The product had no authentication; a login with a seeded demo account was added on request.

## 4. Feature checklist (ticked in Step 4)

- [x] Overview: hero, 3 feature cards with jumps, pipeline, demo run, activity KPIs
- [x] PR Review: demo diff, demo before/after, paste diff (+ file upload), compare versions, GitHub PR link, upload files/zip, local folder
- [x] PR Review: live agent progress, verdict banner, gauge, 4 KPIs
- [x] Findings tab: filters, search, charts, finding cards, patches, 50-card cap
- [x] Function risk tab: table, inspect, radar, drivers, metrics
- [x] Files tab, Agent trace tab
- [x] Export tab: PR comment preview, .md, SARIF, JSON, CSV, patched files
- [x] Codebase: 5 sources, index, Ask with suggestions, hits, repo map (KPIs, routes, concepts, hotspots, graph), onboarding
- [x] Model Lab: KPIs, data note, 7 tabs, Try it, retrain
- [x] History: table, trend, open, delete
- [x] About
- [x] Settings: ML toggle, min severity, API key, LLM toggle, GitHub token
- [x] Kit: dark mode, reduced motion, 360px, keyboard, every state designed
- [x] Added: login + register + demo account, protected routes, sign out

## 5. Environment check

- `.env` has `BACKEND_PORT=8311`, `FRONTEND_PORT=5311` - confirmed; both ports free.
- Engine imports and `pytest tests/test_core.py`: **10 passed**.
- Streamlit and Plotly are not installed on this machine, so the original UI cannot be started here. It is left untouched.
  The new backend does not need either (it never imports `app.py` or `autosecai/ui.py`).
- FastAPI 0.110, uvicorn 0.29, python-multipart 0.0.9, Node 24, npm 11 available.

## 6. Verification (Step 4)

- `npm run build` passes (tsc + vite, route-level code splitting; charts, markdown and scroll libraries are separate chunks).
- `python scripts/smoke_test.py`: 16 API checks pass. `python -m pytest tests -q`: 17 pass (10 engine + 7 API).
- `python scripts/ui_flows.py`: 22 UI flows pass with **0 console errors** - every input mode, filters, exports (downloads checked),
  delete with confirm + Escape, codebase sources, lab tabs + Try it, settings persistence, theme persistence, keyboard, reduced motion,
  API-down error state, 404s.
- `python scripts/capture_screens.py`: 25 screenshots in `docs/screenshots/` (landing in light and dark), no console errors, no 4xx/5xx.
- Overflow checked at 360 px and 768 px in light and dark on every screen: none.
- The Streamlit app is untouched (`run_streamlit.bat`); `autosecai/` is unchanged.
