# PolicyLens

**Understand your health insurance, clause by clause.**

PolicyLens reads a person's own health-insurance policy wording, answers questions with the exact **clause and page** it relies on, flags the fine print that costs money at claim time, and walks them through a claim - in English, Hindi or Telugu.

![Stack](https://img.shields.io/badge/backend-FastAPI%20%7C%20Python%203.11-0d9488) ![Stack](https://img.shields.io/badge/web-React%2018%20%7C%20Vite%20%7C%20Tailwind-0d9488) ![AI](https://img.shields.io/badge/AI-Gemini%20%7C%20ChromaDB%20%7C%20BM25-0d9488)

---

## Key features

| | Feature | |
|---|---|---|
| F1 | **Policy upload and parsing** | PDF -> numbered clauses with pages and highlight positions (two-column layouts, tables, IRDAI exclusion codes); original PDF viewable |
| F2 | **Policy Card** | Sum insured, deductible, co-pay, room rent, waiting periods, sub-limits, exclusions, deadlines - every value linked to its clause and page and verified against the text |
| F3 | **Clause-grounded chat** | Plain-language answers citing clause and page; says "not covered in this policy" instead of guessing |
| F4 | **Hybrid retrieval** | BM25 keyword search + MiniLM embeddings in ChromaDB, fused (RRF) and re-ranked by a cross-encoder |
| F5 | **Claim Copilot** | Covered / partly covered / not covered with reasons, calculated eligibility checks and cost estimate, document checklist and claim steps |
| F6 | **Plan comparison** | Two policies side by side with trade-offs and "choose A if / choose B if" |
| F7 | **Risk highlights** | Waiting-period, sub-limit, co-pay and room-rent traps flagged by severity |
| F8 | **Multilingual answers** | English, हिन्दी, తెలుగు |
| F9 | **Faithfulness score** | An independent NLI model scores how well each answer is supported by its cited text |

Plus a dashboard, a **Model performance** page with measured accuracy, light/dark themes and a phone-friendly layout.

## Measured quality

On a hand-built set of 57 questions, 14 claim scenarios and 52 Policy Card values from four real policy wordings (method, charts and limits in [docs/05_MODELS_AND_TRAINING.md](docs/05_MODELS_AND_TRAINING.md)):

| Right clause in top 5 | Answers correct | Citations correct | Out-of-scope declined | Claim verdicts | Card values | Median answer time |
|---|---|---|---|---|---|---|
| 100% | 51 / 51 | 100% | 6 / 6 (0 false) | 14 / 14 | 51 / 52 | 4.3 s |

---

## Quick start (Windows 10/11)

Prerequisites: **Python 3.11**, **Node.js LTS**, a free **Gemini API key** from https://aistudio.google.com/apikey.

```bat
setup.bat          :: one time - installs everything, downloads the local models, prepares sample data
notepad .env       :: paste your key after GEMINI_API_KEY=
run.bat            :: starts the API (8101) and web app (5101) and opens the browser
```

Open **http://localhost:5101**. Stop with `stop.bat`. Full guide: [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md).

## Demo login

| Email | Password |
|---|---|
| `demo@policylens.app` | `Demo@12345` |

The demo account comes with four sample policy wordings (Star Health Family Health Optima, HDFC ERGO Optima Secure, Niva Bupa ReAssure 2.0, Care Supreme). Try: *"Is cataract surgery covered and after how long?"*, then **Claim Copilot -> Knee replacement**, then **Compare plans**.

## Ports

| Service | Port |
|---|---|
| API (FastAPI, docs at `/docs`) | **8101** |
| Web app (Vite) | **5101** |

Both are fixed so PolicyLens can run beside other applications; change them in `.env` if needed.

## Tech stack

- **Web:** React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui (Radix), Lucide, React Router, TanStack Query, Axios, Motion, GSAP + ScrollTrigger, Lenis, React Bits, Recharts
- **API:** Python 3.11, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2 + SQLite, JWT (PyJWT) + bcrypt, pytest
- **AI / retrieval:** Google Gemini (google-genai, JSON-schema output, fallback models), ChromaDB, rank-bm25, sentence-transformers (all-MiniLM-L6-v2, ms-marco-MiniLM-L6-v2 cross-encoder, nli-deberta-v3-xsmall), PyMuPDF, scikit-learn, pandas, matplotlib

---

## Documentation index for maintainers

| Document | Contents |
|---|---|
| [docs/PLAN.md](docs/PLAN.md) | Original build plan: architecture, modules, data model, API, milestones, risks |
| [docs/01_OVERVIEW.md](docs/01_OVERVIEW.md) | What PolicyLens is, the problem, users, features, limits |
| [docs/02_ARCHITECTURE.md](docs/02_ARCHITECTURE.md) | Components, data flow and sequence diagrams, data model, design decisions |
| [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md) | Prerequisites, setup, first login, stopping, resetting, phone access |
| [docs/04_DATASET.md](docs/04_DATASET.md) | Sample policy wordings, processed data, evaluation set, licences |
| [docs/05_MODELS_AND_TRAINING.md](docs/05_MODELS_AND_TRAINING.md) | Models used, how they are evaluated, results tables and plots |
| [docs/06_API_REFERENCE.md](docs/06_API_REFERENCE.md) | Every endpoint with request and response examples |
| [docs/07_USER_GUIDE.md](docs/07_USER_GUIDE.md) | Screen-by-screen walkthrough |
| [docs/08_CONFIGURATION.md](docs/08_CONFIGURATION.md) | Every `.env` key and how to obtain it |
| [docs/09_TESTING.md](docs/09_TESTING.md) | Automated tests, build, demo scenario and results |
| [docs/10_TROUBLESHOOTING.md](docs/10_TROUBLESHOOTING.md) | Common problems and fixes |
| [docs/11_PROJECT_STRUCTURE.md](docs/11_PROJECT_STRUCTURE.md) | Folder-by-folder explanation of the code |

---

PolicyLens explains policy wordings; the insurer makes the final decision on any claim.
