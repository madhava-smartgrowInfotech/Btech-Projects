<p align="center">
  <img src="frontend/public/favicon.svg" width="72" alt="SeatWise logo" />
</p>

<h1 align="center">SeatWise</h1>

<p align="center"><strong>Constraint-optimised, cheat-resistant exam seating plans - generated in seconds.</strong></p>

SeatWise turns a candidate list, hall layouts and a timetable into seating plans where **no two neighbours write the same paper**, diagonals included. Close roll numbers are kept apart, and accessible seats go to the candidates who need them. Every plan is a random valid choice from a recorded seed, so nobody can predict a seat and anyone can reproduce the plan to verify it.

Around the engine, SeatWise provides:

- seating charts and hall lists, ready to print
- a drag-to-swap seat map that checks every move live
- tablet attendance at the hall door
- a public "where do I sit?" page with QR seat slips
- analytics for the whole examination

## Key features

| | Feature |
|---|---|
| F1 | **Validated import** - Excel/CSV templates for courses, halls, candidates and timetable, with row-by-row checks including timetable clashes |
| F2 | **Constraint optimisation** - OR-Tools CP-SAT covering capacity, same-paper separation (8 neighbours), roll-number gap, department mix and accessible seats |
| F3 | **Seeded, fair randomness** - reproducible from its seed, fingerprinted, one-click **Verify**, full audit trail |
| F4 | **Visual seat maps** - drag or tap to swap, with green and red targets and the reason for every refusal |
| F5 | **Outputs** - seating charts, invigilator sheets and QR seat slips (PDF); hall lists, door list and attendance report (Excel) |
| F6 | **Tablet attendance** - tap or scan a slip, mark the rest absent, submit and lock, live progress |
| F7 | **Seat lookup and QR slip** - a public page with a hall map showing the seat |
| F8 | **Analytics** - seats filled, rules met, conflicts avoided compared with roll order, attendance, solve times and the engine benchmark |

**Benchmark:** 24 of 24 plans met every hard rule, with 0 same-paper neighbours (roll-order seating: 1,253 in a 600-candidate sitting). A 600-candidate sitting is seated in about 2.4 s and 2,000 candidates in 4.8 s. The roll-to-seat correlation is 0.06. Details are in [docs/05_MODELS_AND_TRAINING.md](docs/05_MODELS_AND_TRAINING.md).

## Quick start (Windows 10/11)

You need **Python 3.11** and **Node.js LTS**; step-by-step install help is in [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md).

```bat
setup.bat      :: once: environment, packages, .env, database (about 5 minutes)
run.bat        :: starts SeatWise and opens http://localhost:5113
stop.bat       :: stops it
```

| Service | Address |
|---|---|
| Web app | http://localhost:5113 |
| API and interactive docs | http://localhost:8113/docs |

The ports are fixed, so SeatWise runs alongside other products.

## Demo sign-in

| Role | Email | Password |
|---|---|---|
| Exam controller (admin) | `admin@seatwise.local` | `SeatWise@2026` |
| Invigilator | `invigilator@seatwise.local` | `SeatWise@2026` |

Then open **Import data**, choose **Templates & samples > Sample workbook**, upload it and click **Import**. Next, in **Sittings & plans**, click **Generate plan**. The sample data is fictional. To check the whole scenario automatically, run `venv\Scripts\python scripts\demo_scenario.py`.

## Tech stack

- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, Motion, GSAP, Lenis, React Bits, Recharts
- **Backend:** Python 3.11, FastAPI, SQLAlchemy 2 with SQLite, JWT and bcrypt
- **Engine and outputs:** Google OR-Tools CP-SAT; ReportLab, openpyxl and qrcode

Everything runs offline once installed, and no API keys are needed.

## Documentation index for maintainers

| Document | What it covers |
|---|---|
| [docs/01_OVERVIEW.md](docs/01_OVERVIEW.md) | What SeatWise is, the problem, users, features, rules |
| [docs/02_ARCHITECTURE.md](docs/02_ARCHITECTURE.md) | Components, data model, the seating engine, main flows (Mermaid diagrams), security |
| [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md) | Prerequisites, setup, start, first sign-in, stop, reset, tablets and phones |
| [docs/04_DATASET.md](docs/04_DATASET.md) | Sample data generator, schema of every import file, what is committed |
| [docs/05_MODELS_AND_TRAINING.md](docs/05_MODELS_AND_TRAINING.md) | Engine evaluation: method, settings, tuning, full results and plots |
| [docs/06_API_REFERENCE.md](docs/06_API_REFERENCE.md) | Every endpoint with request and response examples |
| [docs/07_USER_GUIDE.md](docs/07_USER_GUIDE.md) | Screen-by-screen guide |
| [docs/08_CONFIGURATION.md](docs/08_CONFIGURATION.md) | Every `.env` setting |
| [docs/09_TESTING.md](docs/09_TESTING.md) | Tests, results, the demo scenario, installation check |
| [docs/10_TROUBLESHOOTING.md](docs/10_TROUBLESHOOTING.md) | Common problems and fixes |
| [docs/11_PROJECT_STRUCTURE.md](docs/11_PROJECT_STRUCTURE.md) | Folder-by-folder guide to the code |
| [docs/PLAN.md](docs/PLAN.md) | The original build plan and design decisions |
