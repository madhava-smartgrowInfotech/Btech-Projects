# APISentry - Build Plan

**Product:** APISentry - automated security testing for payment APIs. Imports REST API
specs, runs OWASP API Top 10 checks + AI-generated business-logic tests, scores the API
0-100, and reports fixes before deployment.

## Architecture
- **Backend** FastAPI + Uvicorn (port 8213), SQLAlchemy 2 + SQLite (`data/app.db`),
  JWT+bcrypt auth. Async scan engine (httpx) with a scope guard (allow-list).
- **Scanner** `services/scanner.py` orchestrates check modules (BOLA, auth, data
  exposure/mass-assignment, rate limit, function auth, injection, misconfig), scores
  findings by severity, maps each to OWASP API Top 10.
- **AI tests** `services/ai_tests.py` - Gemini reads the spec, proposes business-logic
  tests; falls back to a built-in generator when no key. Scanner executes them.
- **Reports** Jinja2 HTML + ReportLab PDF. **CLI** Typer `apisentry scan --spec ...`.
- **Targets** `targets/demopay.py` (deliberately vulnerable payment API, port 12130) +
  `targets/vulnbank.py` (second target, port 12131) each ship a known-vuln list.
- **Frontend** React+Vite (JS) + Tailwind (port 5213), axios, react-router.

## Endpoints (/api)
- auth: POST /auth/register, /auth/login, GET /auth/me
- targets: GET/POST/DELETE /targets, POST /targets/import-spec
- scans: POST /scans (start), GET /scans, GET /scans/{id}, GET /scans/{id}/findings
- ai: POST /scans/{id}/ai-tests (generate+run)
- reports: GET /scans/{id}/report.html, /report.pdf
- validation: GET /scans/{id}/validation
- catalog: GET /owasp, GET /targets/known-vulns

## Tables
users, targets, scans, findings, ai_tests

## Screens
Landing, Login/Register, Targets, Scan progress, Results, Finding detail, Reports, Validation

## Defaults
Ports 8213/5213/12130-12131. Demo login seeded. Scope allow-list = localhost only.
Gemini optional (built-in fallback). DemoPay demo target scores ~38/100 (grade D).
