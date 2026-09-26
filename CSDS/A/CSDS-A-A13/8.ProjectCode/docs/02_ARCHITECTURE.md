# Architecture

SeatWise is a single-machine web product: a **FastAPI** backend with an **SQLite** database, and a **React** frontend served by **Vite**. Everything runs offline once installed.

## Components

```mermaid
flowchart LR
  subgraph Browsers["Browsers - PC, tablet, phone"]
    PUB["Home page + public seat lookup"]
    ADM["Administrator console"]
    INV["Invigilator console (tablet)"]
  end

  subgraph FE["Frontend - React 18 + Vite (port 5113)"]
    UI["Pages, seat maps, charts<br/>React Router + TanStack Query"]
  end

  subgraph BE["Backend - FastAPI (port 8113)"]
    API["REST API /api<br/>JWT auth, roles"]
    IMP["Importer<br/>parse -> validate -> commit"]
    ENG["Seating engine<br/>OR-Tools CP-SAT"]
    VAL["Independent validator"]
    SWP["Swap checker"]
    EXP["Exports<br/>ReportLab, openpyxl, qrcode"]
    ATT["Attendance"]
    ANA["Analytics"]
    AUD["Audit trail"]
  end

  DB[("SQLite<br/>data/app.db")]
  PROF[["models/engine_profile.json<br/>experiments/ (benchmark)"]]

  Browsers --> FE
  FE -- "/api (proxied)" --> API
  API --> IMP & ENG & SWP & EXP & ATT & ANA & AUD
  ENG --> VAL
  SWP --> VAL
  IMP & ENG & ATT & AUD --> DB
  EXP & ANA --> DB
  PROF -. "tuned budget, benchmark metrics" .-> ENG & ANA
```

- The browser only talks to port **5113**. The Vite server forwards `/api` to the backend on **8113**, so tablets and phones need a single address.
- The backend owns every rule. The frontend never decides whether a seat move is legal: it asks the API, so the seat map, the exports and the benchmark all apply identical checks.
- A plan is always re-checked by the **independent validator** (plain Python, no solver) before it is stored.

## Data model

```mermaid
erDiagram
  DEPARTMENT ||--o{ COURSE : runs
  DEPARTMENT ||--o{ CANDIDATE : has
  CANDIDATE ||--o{ REGISTRATION : takes
  COURSE ||--o{ REGISTRATION : "taken by"
  EXAM_SESSION ||--o{ SESSION_PAPER : schedules
  COURSE ||--o| SESSION_PAPER : "examined in"
  EXAM_SESSION ||--o{ PLAN : "seated by"
  PLAN ||--o{ SEAT_ASSIGNMENT : contains
  HALL ||--o{ SEAT_ASSIGNMENT : hosts
  CANDIDATE ||--o{ SEAT_ASSIGNMENT : "sits at"
  PLAN ||--o{ INVIGILATOR_ASSIGNMENT : staffs
  USER ||--o{ INVIGILATOR_ASSIGNMENT : supervises
  PLAN ||--o{ ATTENDANCE : records
  PLAN ||--o{ HALL_SUBMISSION : locks
  PLAN ||--o{ AUDIT_EVENT : logs
```

| Table | Purpose |
|---|---|
| `users` | Administrators and invigilators (bcrypt password hash, role, status active/pending/disabled). |
| `departments`, `courses` | Course catalogue. |
| `candidates`, `registrations` | Candidates and the courses each one sits. |
| `halls` | Rows x columns, blocked seats, accessible seats, aisles, availability. |
| `exam_sessions`, `session_papers` | The timetable: sittings and the courses in each (with optional shared-paper group). |
| `plans` | A seating plan version: status, seed, rules, fingerprints, solve time, scorecard, roll-order baseline. |
| `seat_assignments` | Candidate -> hall, row, column, seat label. |
| `invigilator_assignments` | Who supervises which hall in a plan. |
| `attendance`, `hall_submissions` | Marks per candidate and the lock when a register is submitted. |
| `import_batches` | Every upload with its validation report. |
| `audit_events` | Append-only log of plans, seeds, moves, publications, imports, exports and attendance. |
| `settings` | Default seating rules. |

The database file is created automatically on first start (`SQLAlchemy create_all`).

## The seating engine

Code: `backend/app/services/engine/`.

```mermaid
flowchart TD
  A["Candidates of the sitting<br/>+ selected halls + rules + seed"] --> B["Pre-checks<br/>capacity, accessible seats, largest paper"]
  B -->|problem| X["Plain-language reason<br/>+ suggestion"]
  B --> C["Stage A - hall + colour-class allocation<br/>(CP-SAT, two passes)"]
  C --> D["Split candidates between halls<br/>(seeded shuffle)"]
  D --> E1["Stage B - hall 1<br/>CP-SAT"] & E2["Stage B - hall 2<br/>CP-SAT"] & E3["Stage B - hall n<br/>CP-SAT"]
  E1 & E2 & E3 --> F{"every hall solved?"}
  F -->|no| C
  F -->|yes| G["Independent validator<br/>scorecard + violations"]
  G --> H["Plan stored with seed,<br/>rules and fingerprints"]
```

1. **Seat graph and colouring.** Each hall is a graph: seats are nodes, and neighbouring seats are joined. There are 8 neighbours by default, including diagonals; aisles and blocked seats remove edges. SeatWise colours the grid by (row parity, column parity) - 4 classes, or 2 with 4-neighbour adjacency. Seats of one class are never neighbours.
2. **Stage A - allocation (CP-SAT).** It decides how many candidates of each (paper, department, accessible-need) group go to each hall, and which colour class each paper uses in each hall. Confining a paper to one class per hall makes same-paper neighbours impossible *by construction*.
   - The compact strategy first picks the fewest, largest halls that provably fit.
   - Pass 1 then minimises peak fill and spreads papers and departments.
   - Pass 2 keeps that optimum and follows seeded random weights, so which class a paper gets cannot be predicted.
3. **Stage B - seat layout per hall (CP-SAT).** `x[candidate, seat]` booleans, restricted to the candidate's class and to accessible seats for those who need them. Constraints: one seat per candidate and at most one candidate per seat. Roll-number spacing is enforced by "if A sits on s, B sits on none of s's neighbours" clauses. The objective minimises same-department neighbours, then maximises a seeded random weight, so the result is one random valid layout. Halls are solved **in parallel threads**, each with one deterministic worker.
4. **Recovery.** A hall that finds nothing within its budget gets one try with four times the budget. If it still fails, Stage A re-balances with that hall eased (bounded retries).
5. **Validation.** `validator.py` re-checks every rule without the solver and produces the scorecard (placed, same-paper pairs, roll-gap violations, accessible misses, same-department pairs, utilisation, per-hall figures).

**Reproducibility.** Every sub-seed is derived from the plan seed with SHA-256, CP-SAT uses one worker per hall with a *deterministic* time budget, and candidates are processed in a fixed order. As a result, the same data, rules, seed and engine version give the same plan. The plan stores:

| Field | Contents |
|---|---|
| `data_fingerprint` | SHA-256 of the inputs, rules and budget |
| `solver_hash` | SHA-256 of what the engine produced |
| `assignment_hash` | SHA-256 of the current seating, which changes after manual moves |

**Verify** re-runs the engine and compares the hashes.

## Main flows

### Import

```mermaid
sequenceDiagram
  actor Admin
  participant UI
  participant API
  participant Importer
  participant DB
  Admin->>UI: Choose kind + file
  UI->>API: POST /api/imports/{kind}/validate (multipart)
  API->>Importer: parse (CSV/XLSX, header aliases)
  Importer->>DB: read current data (for references, clashes)
  Importer-->>API: report (errors, warnings, preview)
  API-->>UI: batch id + report
  Admin->>UI: Import N rows
  UI->>API: POST /api/imports/{id}/commit
  API->>Importer: re-validate against current data, then apply
  Importer->>DB: insert / update, audit event
```

### Generate and publish a plan

```mermaid
sequenceDiagram
  actor Admin
  participant UI
  participant API
  participant Engine
  participant Validator
  participant DB
  Admin->>UI: Rules, halls, seed -> Generate
  UI->>API: POST /api/sessions/{id}/plans
  API->>DB: candidates of the sitting, hall layouts
  API->>Engine: solve(candidates, halls, rules, seed, budget)
  Engine-->>API: placements (or reasons)
  API->>Validator: validate + roll-order baseline
  API->>DB: plan, seats, invigilators, audit (seed, fingerprints)
  API-->>UI: plan + scorecard
  Admin->>UI: Publish
  UI->>API: POST /api/plans/{id}/publish
  API->>DB: status published (previous version archived), audit
```

### Move a candidate on the seat map

```mermaid
sequenceDiagram
  actor Admin
  participant Map as Seat map
  participant API
  Admin->>Map: pick up seat C4
  Map->>API: GET /plans/{id}/halls/{hall}/swap-check?seat=C4
  API-->>Map: every seat: ok / reasons
  Map-->>Admin: green and red targets
  Admin->>Map: drop on D6
  Map->>API: POST /plans/{id}/swap
  API->>API: check again, move, re-validate, audit
  API-->>Map: result (or 409 with reasons)
```

### On the day

```mermaid
sequenceDiagram
  actor Candidate
  actor Invigilator
  participant Lookup as Public lookup
  participant Tablet as Attendance screen
  participant API
  Candidate->>Lookup: candidate ID
  Lookup->>API: GET /api/public/lookup/{id}
  API-->>Lookup: hall, seat, map (published plans only)
  Candidate->>Lookup: download slip
  Lookup->>API: GET /api/public/slip/{id}/{plan}.pdf
  Invigilator->>Tablet: scan the slip's QR code
  Tablet->>API: POST .../attendance/scan
  API-->>Tablet: present at seat C4 (or: sits in another hall)
  Invigilator->>Tablet: mark remaining absent, submit
  Tablet->>API: POST .../attendance/submit (locks register)
```

## Security

- Passwords are hashed with bcrypt. Sign-in issues a signed JWT (HS256) whose secret lives only in `.env`.
- Roles: administrators do everything; invigilators only see and mark the halls they are assigned to in published plans.
- Public endpoints expose published seats only, a shortened name ("Maya F.") and no email or date of birth. They are rate-limited per device.
- Every change that matters is written to the append-only audit trail.

## Technology

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui (Radix), Lucide icons, React Router, TanStack Query, Axios, Motion, GSAP + ScrollTrigger, Lenis, React Bits, Recharts, dnd-kit, sonner |
| Backend | Python 3.11, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2, SQLite, PyJWT, passlib/bcrypt, python-dotenv |
| Engine and outputs | Google OR-Tools CP-SAT, NumPy, pandas, openpyxl, ReportLab, qrcode, matplotlib (benchmark plots) |
| Tests | pytest (backend), TypeScript type checks and production build (frontend), `scripts/demo_scenario.py` |
