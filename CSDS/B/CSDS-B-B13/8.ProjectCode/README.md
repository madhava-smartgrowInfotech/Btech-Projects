# APISentry

**Automated security testing for payment APIs.** APISentry imports a REST API
spec, runs the OWASP API Security Top 10 plus AI-generated business-logic tests,
scores the API 0–100, and gives developers clear, reproducible fixes before they
deploy.

![stack](https://img.shields.io/badge/stack-FastAPI%20%2B%20React%20%2B%20SQLite-2563eb)

## Features
- **F1 Target import** — OpenAPI/Swagger or Postman collection, or manual
  endpoints, with auth profiles (bearer JWT / API key) and two test users.
- **F2 Scope guard** — scans only run against allow-listed hosts (localhost by
  default) after the user confirms authorisation.
- **F3 OWASP API Top 10** — BOLA/IDOR, broken auth, excessive data exposure &
  mass assignment, missing rate limiting, function-level auth, injection, and
  security misconfiguration (CORS, headers, verbose errors).
- **F4 AI-generated tests** — Gemini proposes business-logic abuse tests
  (negative amounts, changed account ids, replayed payment ids); the scanner runs
  them. A built-in generator is the fallback when no key is set.
- **F5 Security score** — 0–100 with a grade, weighted by severity, plus a
  per-endpoint breakdown.
- **F6 Findings** — evidence, a curl command to reproduce, OWASP mapping, and a
  fix recommendation with a code snippet.
- **F7 Reports & CLI** — HTML/PDF reports and `apisentry scan --fail-on high`
  for CI pipelines.
- **F8 Validation** — findings compared with a target's known-vulnerability list
  for a detection rate and false-positive count.

## Quick start
```bat
setup.bat      REM one-time: venv + backend + frontend deps, creates .env
run.bat        REM starts targets + backend + frontend, opens the browser
```
Then open **http://localhost:5213**.

**Demo login:** `demo@apisentry.local` / `demo12345`

Two deliberately vulnerable practice targets (DemoPay, VulnBank) come pre-loaded
so you can scan safely on localhost immediately.

> Optional: set `GEMINI_API_KEY` in `.env` (from https://aistudio.google.com/apikey)
> to power AI tests with Gemini. Without it, a built-in generator is used.

## CLI (CI/CD)
```bat
venv\Scripts\python.exe apisentry.py scan --spec targets\demopay_openapi.json ^
  --auth targets\demopay_vulns.json --known targets\demopay_vulns.json --fail-on high
```
Exits non-zero when findings at/above the chosen severity exist.

## Evaluation results
Produced by `ml/eval.py` → `experiments/eval/metrics.json` (both practice targets):

| Target | Score | Grade | Findings | Detection rate | False positives |
|--------|:-----:|:-----:|:--------:|:--------------:|:---------------:|
| DemoPay | 38/100 | D | 12 | 100% (12/12) | 0 |
| VulnBank | 80/100 | B | 3 | 75% (3/4)* | 0 |
| **Overall** | — | — | — | **93.8% (15/16)** | **0** |

\* VulnBank intentionally includes one BOLA on an unguessable id that generic
integer enumeration cannot reach — a realistic miss that keeps the evaluation honest.

AI-generated business-logic tests found **3/3** abuse cases on DemoPay
(negative amount, foreign-account transfer, replayed payment).

## Tech stack
- **Frontend:** React + Vite (JavaScript), Tailwind CSS, react-router-dom, axios,
  lucide-react. Ports: frontend **5213**, backend **8213**.
- **Backend:** Python 3.11+, FastAPI + Uvicorn, SQLAlchemy 2 + SQLite, PyJWT +
  bcrypt, httpx, Typer (CLI), Jinja2 + ReportLab (reports), Gemini (AI tests).

## Documentation
- [docs/01_OVERVIEW.md](docs/01_OVERVIEW.md) — what it is and who it's for
- [docs/02_HOW_IT_WORKS.md](docs/02_HOW_IT_WORKS.md) — architecture, pipeline, data
- [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md) — setup, run, CLI, tests
- [docs/PLAN.md](docs/PLAN.md) — build plan

## Project layout
```
backend/app/     FastAPI app: routes/, services/ (scanner, ai_tests, reports, …)
frontend/src/    React app: pages/, components/, api.js
targets/         DemoPay + VulnBank vulnerable APIs, specs and known-vuln lists
scripts/         smoke_test.py, gen_specs.py
ml/              eval.py
experiments/eval metrics.json
docs/            overview, how-it-works, how-to-run, plan
apisentry.py     CLI entrypoint     setup.bat  run.bat
```

## Safety
APISentry is a defensive security testing tool. It refuses to scan hosts that are
not explicitly allow-listed, and requires the user to confirm they are authorised
to test each target. Only test systems you own or have permission to test.
