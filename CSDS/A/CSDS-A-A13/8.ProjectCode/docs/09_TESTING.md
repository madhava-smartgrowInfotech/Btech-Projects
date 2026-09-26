# Testing

SeatWise is checked at four levels:

1. backend tests (pytest)
2. frontend type checks and a production build
3. the scripted demo scenario against a running installation
4. the engine benchmark

## 1. Backend tests (pytest)

```bat
cd backend
..\venv\Scripts\python -m pytest          :: about a minute
..\venv\Scripts\python -m pytest -v tests\test_engine.py
```

The tests use a throw-away SQLite database (see `tests/conftest.py`), so your data is never touched. They import the committed sample workbook through the real API.

**Result: 58 passed.**

| File | Tests | What is covered |
|---|---|---|
| `test_auth.py` | 8 | Health; sign-in and `/me`; wrong password; protected routes need a token; registration waits for approval, duplicates refused, admin approves; invigilators cannot manage the team; the last admin cannot be disabled; default rules and rule validation. |
| `test_engine.py` | 14 | Seat labels round-trip (A1 ... AA1); neighbours respect aisles and blocked seats; colour classes never touch (4 and 8 neighbours); roll-number parsing and gap; **every hard rule met**; **same seed reproduces the plan**; different seeds give different plans; 4-neighbour and balanced fill; compact uses fewer halls; impossible inputs explain why (seats, dominant paper, accessible seats); the validator catches every kind of violation; roll-order seating creates conflicts the engine avoids; custom roll gap honoured. |
| `test_imports.py` | 9 | Templates and samples download; candidates without courses are refused; the sample workbook imports cleanly (908 candidates, 49 courses, 14 halls, 6 sittings, shared paper, default accessible seats); re-import updates instead of duplicating, and a batch cannot be applied twice; row-level errors with row numbers; hall layout errors; timetable clash and split paper group; unreadable files; invigilators cannot import. |
| `test_plans.py` | 6 | Generated plan meets every rule, avoids more than 500 conflicts, assigns invigilators; same seed -> same result and **Verify** confirms it; publishing archives the previous version, published plans cannot be deleted; hall map, illegal swap refused with a reason, legal swap applied and audited, fingerprints updated; invigilators only see their halls; impossible request explains why and is audited. |
| `test_exports.py` | 7 | Seating charts, invigilator sheets and QR slips are valid PDFs (one chart page per hall); single-hall chart; hall-lists workbook (sheet per hall, roll-ordered door list with every candidate); attendance workbook; invigilators cannot export everything. |
| `test_attendance.py` | 5 | My halls; marking and scanning (URL and lower-case roll number, already present); scanning someone from another hall says where they sit; submit needs everyone marked, locks the register, only admins reopen; unassigned halls are forbidden. |
| `test_public.py` | 5 | Lookup shows published seats only, shortened name, no private fields; unknown ID and unpublished plan; slip PDF and QR PNG; home-page benchmark summary; rate limiting (429). |
| `test_analytics.py` | 4 | Overview figures match the plan; plan analytics (comparison, neighbour-pair breakdown adds up); engine benchmark and its charts are served, path tricks refused; invigilators cannot see analytics. |

## 2. Frontend

```bat
cd frontend
npm run typecheck     :: TypeScript, strict
npm run build         :: type check + production bundle in frontend\dist
```

**Result:** no type errors, and the production build succeeds (about 6 s). Large libraries - charts, motion and React - are split into their own chunks, and every page is loaded on demand.

### UI checks

Every screen was walked through in a browser (Microsoft Edge, headless) during development, in light and dark themes, on a desktop (1440 px), a tablet (820 px) and a phone (360-390 px). The checks were:

- import, validation report, preview and commit
- plan generation with live progress, **Verify**, publishing, audit trail
- seat map: pick up a candidate, red and green targets with reasons, a blocked move, a drag-and-drop swap
- exports page and the PDF and Excel files (rendered and inspected)
- tablet attendance: typed/scanned roll number, list and seat-map views, counters, submit bar
- public lookup with QR slip, analytics (plans and engine), dashboard, landing page including reduced-motion mode

At 360 px no page scrolls sideways. Wide content such as seat maps and tables scrolls inside its own panel. No browser console errors appeared.

## 3. Demo scenario

With SeatWise running (`run.bat`):

```bat
venv\Scripts\python scripts\demo_scenario.py            :: add/update the sample data
venv\Scripts\python scripts\demo_scenario.py --reset    :: start from an empty workspace
venv\Scripts\python scripts\demo_scenario.py --out C:\temp\seatwise-demo   :: keep the downloaded files
```

It performs the definition-of-done scenario through the API and stops at the first failure. Output from a fresh `setup.bat` + `run.bat`:

```
== 1. Import candidates, halls and timetable
   OK  validation passed: 1020 rows, 10 warnings
   OK  imported 908 candidates, 49 courses, 14 halls, 6 sittings
== 2. Generate plans for three sittings
   OK  Mon 12 Oct 2026 · Morning: 451 candidates in 6 halls, 0 same-paper neighbours, 1099 avoided, 2.9 s, seed 414169745 - published
   OK  Mon 12 Oct 2026 · Afternoon: 457 candidates in 7 halls, 0 same-paper neighbours, 1175 avoided, 2.8 s, seed 100853765 - published
   OK  Tue 13 Oct 2026 · Morning: 451 candidates in 6 halls, 0 same-paper neighbours, 1105 avoided, 2.7 s, seed 1737902151 - published
== 3. Illegal swap and downloads
   OK  moving A1 to A2 was blocked: This move is not allowed: ACF25015 would sit next to ACF25016 (A3) - both write ACF-101. ...
   OK  seating-charts.pdf (135 KB)
   OK  invigilator-sheets.pdf (144 KB)
   OK  qr-slips.pdf (1666 KB)
   OK  hall-lists.xlsx (47 KB)
   OK  attendance.xlsx (28 KB)
== 4. Seat lookup, QR slip and attendance
   OK  DAN25047 (Arjun L.) sits in EW-205 seat A2
   OK  QR slip downloaded (64 KB)
   OK  Sam Taylor marked 2 candidates present in EW-205 (2 present, 72 to mark)
Demo scenario passed in 16.2 s.
```

The (10 warnings) are the halls that received the default accessible seats.

### Installation check

`setup.bat` was run on a clean copy of the committed folder, with no `venv`, `node_modules` or `.env`. It created the environment, installed all packages, generated `.env` and the database, and passed every check in 108 s. `run.bat` then started both servers, waited for them, opened the browser and printed the addresses, and `stop.bat` stopped them.

## 4. Engine benchmark

`venv\Scripts\python -m ml.benchmark` evaluates the engine on 8 scenarios x 3 seeds against three manual methods, measures unpredictability, and tunes the time budget. Result: **24 of 24 plans met every hard rule**, with 2.4 s for 600 candidates and 4.8 s for 2,000. Details and tables are in [05_MODELS_AND_TRAINING.md](05_MODELS_AND_TRAINING.md).

## Definition-of-done checklist

| Item | Status |
|---|---|
| Import candidates, halls and timetable; validation passes | Done |
| Plans for three sittings solved in seconds with zero same-paper neighbours | Done (2.7-2.9 s each, 0 pairs) |
| Illegal swap blocked with a reason; PDFs and Excel download | Done |
| Candidate seat lookup and QR slip; invigilator attendance | Done |
| Every feature F1-F8 works end to end in the UI | Done |
| Engine evaluated; metrics in the product and in docs | Done |
| `setup.bat` / `run.bat` on a fresh copy | Done |
| Backend tests pass; frontend production build succeeds | Done (58 passed) |
| No placeholder text or hard-coded secrets | Done (secrets only in `.env`) |
| Fixed ports 8113 / 5113 | Done (`strictPort`, `run.bat` refuses busy ports) |
