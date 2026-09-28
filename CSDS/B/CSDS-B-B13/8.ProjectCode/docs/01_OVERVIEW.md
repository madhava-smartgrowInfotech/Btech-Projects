# APISentry — Overview

APISentry is an automated security-testing tool for REST APIs, with a focus on
payment APIs. It imports an API specification, runs the **OWASP API Security
Top 10** checks plus **AI-generated business-logic tests**, produces a
**0–100 security score with a grade**, and gives developers **clear, reproducible
fixes** before they deploy.

## The problem
- Payment APIs are frequent targets of cyberattacks.
- Security testing usually requires skilled professionals and expensive tools.
- Critical vulnerabilities often remain undetected before deployment.
- Developers lack simple, actionable security feedback.

APISentry gives any backend or QA engineer a one-click, low-cost way to test an
API and get concrete remediation guidance.

## Who it is for
- Backend and API developers at fintech and payment companies
- QA and security engineers
- Engineering managers who need a security score

## What it does (features)
| # | Feature | Summary |
|---|---------|---------|
| F1 | **Target import** | OpenAPI/Swagger or Postman collection, or manual endpoints, with auth profiles (bearer JWT / API key) and two test users for access-control checks. |
| F2 | **Scope guard** | Scans run only against allow-listed hosts (localhost by default) after the user confirms they are authorised. |
| F3 | **OWASP API Top 10 tests** | BOLA/IDOR, broken authentication, excessive data exposure & mass assignment, missing rate limiting, function-level authorization, injection, and security misconfiguration (CORS, headers, verbose errors). |
| F4 | **AI-generated tests** | Gemini reads the spec and proposes business-logic abuse tests (negative amounts, changed account ids, replayed payment ids); the scanner runs them. A built-in generator is used when no Gemini key is set. |
| F5 | **Security score** | 0–100 with a letter grade, weighted by severity, plus a severity breakdown and per-endpoint findings. |
| F6 | **Findings** | Request/response evidence, a curl command to reproduce, the OWASP mapping, and a fix recommendation with a code snippet. |
| F7 | **Reports & CLI** | Shareable HTML/PDF reports, and `apisentry scan --spec … --fail-on high` for CI pipelines. |
| F8 | **Validation** | Findings compared against each target's known-vulnerability list to give a detection rate and false-positive count. |

## Screens
Landing · Login/Register · Targets · Scan progress · Results · Finding detail ·
Reports · Validation.

## Practice targets
Two deliberately vulnerable APIs are included so the tool can be demonstrated and
validated safely on localhost:
- **DemoPay** (`targets/demopay.py`, port 12130) — a vulnerable payment API.
- **VulnBank** (`targets/vulnbank.py`, port 12131) — a partially hardened banking API.

See `02_HOW_IT_WORKS.md` for the architecture and `03_HOW_TO_RUN.md` to run it.
