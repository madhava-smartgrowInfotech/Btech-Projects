# API reference

- **Base URL:** `http://localhost:5113/api` through the web server, or `http://localhost:8113/api` directly.
- **Interactive documentation:** http://localhost:8113/docs (OpenAPI; the schema is at `/openapi.json`).
- **Authentication:** `Authorization: Bearer <access_token>` from `POST /auth/login`. Tokens last `JWT_EXPIRE_MINUTES` (12 hours by default). In the docs page, click **Authorize** and paste the token.
- **Roles:** *public* (no token), *signed-in* (any active account), *admin* (administrators only). Invigilators may use hall-level endpoints only for halls they are assigned to in published plans.
- **Errors** are JSON: `{"detail": "a readable message", "details": ...}`. Codes used:

| Code | Meaning |
|---|---|
| 400 | Bad input |
| 401 | Not signed in, or the session expired |
| 403 | Not allowed for this role |
| 404 | Not found |
| 409 | Conflicts with the current state (for example a blocked seat move or a locked register) |
| 422 | Validation failed, or no plan is possible |
| 429 | Rate limited |

All examples below are real responses from the sample data (shortened where marked `...`).

---

## Health and authentication

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/health` | public | Service and database health |
| POST | `/auth/login` | public | Sign in, receive a token |
| POST | `/auth/register` | public | Request an invigilator account (starts as *pending*) |
| GET | `/auth/me` | signed-in | The signed-in user |
| GET | `/auth/demo` | public | Demo accounts for the sign-in page (only when `SEED_DEMO_USERS=true`) |

```http
POST /api/auth/login
{"email": "admin@seatwise.local", "password": "SeatWise@2026"}
```
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5...",
  "token_type": "bearer",
  "expires_at": "2026-09-22T01:42:48.826665Z",
  "user": {"id": 1, "email": "admin@seatwise.local", "full_name": "Alex Morgan", "role": "admin",
           "status": "active", "created_at": "2026-09-21T13:31:51.033290", "last_login_at": "2026-09-21T13:42:48.823670"}
}
```
Wrong password: `401 {"detail": "Email or password is incorrect."}`. Pending account: `403 {"detail": "Your account is waiting for an administrator to approve it."}`.

```http
POST /api/auth/register
{"full_name": "Maya Fernandes", "email": "maya@example.org", "password": "at-least-8"}
```
Returns `201` with the user (`"status": "pending"`).

## Team (admin)

| Method | Path | Purpose |
|---|---|---|
| GET | `/users` | All accounts |
| POST | `/users` | Create an active account: `{"full_name", "email", "password", "role": "invigilator" \| "admin"}` |
| PATCH | `/users/{id}` | Any of `{"full_name", "role", "status": "active" \| "pending" \| "disabled", "password"}`. The last active administrator cannot be demoted or disabled (`409`). |

## Settings

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/settings/rules` | signed-in | Default rules |
| PUT | `/settings/rules` | admin | Change the defaults |
| POST | `/settings/reset-workspace` | admin | `{"confirm": "RESET"}` - deletes all exam data (accounts, settings and audit are kept) |

```json
{"adjacency": 8, "roll_gap": 5, "department_mix": true, "fill_strategy": "compact", "accessible_per_hall": 2}
```

## Import (admin)

| Method | Path | Purpose |
|---|---|---|
| GET | `/imports/templates/{kind}?format=xlsx\|csv` | Empty template; `kind` = `courses`, `candidates`, `halls`, `timetable` or `workbook` (xlsx only) |
| GET | `/imports/samples/{kind}` | The committed sample data (`workbook` = xlsx, others = csv) |
| POST | `/imports/{kind}/validate` | Multipart: `file` (.csv/.xlsx) and `mode` = `update` \| `replace`. Parses and validates only - nothing is saved. |
| POST | `/imports/{batch_id}/commit` | Re-validates against the current data, then applies. `409` if the data changed and it no longer passes, or if it was already applied. |
| GET | `/imports` | Recent imports |
| GET | `/imports/{batch_id}` | One import with its report |

Validate response (abridged):
```json
{
  "id": 1, "kind": "workbook", "filename": "seatwise_sample_workbook.xlsx", "status": "validated",
  "rows_total": 1020, "rows_valid": 1020,
  "report": {
    "mode": "update",
    "kinds": {"courses": {"rows_total": 49, "rows_valid": 49, "new": 49, "updated": 0, "errors": 0, "warnings": 0}, "...": "..."},
    "errors": 0, "warnings": 10,
    "issues": [{"kind": "halls", "row": 4, "column": "accessible_seats", "level": "warning",
                "message": "No accessible seats given: A1, A2 (front row, nearest the door) were used."}],
    "preview": {"courses": [{"course_code": "ACF-101", "course_name": "Principles of Accounting", "...": "..."}]}
  }
}
```
An error issue looks like: `{"kind": "timetable", "row": null, "column": "course_code", "level": "error", "message": "ACF-201 and ACF-202 are both in the sitting on 2026-11-02 at 09:30, but 63 candidate(s) take both (...). Move one course to another sitting."}`

## Data

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/data/summary` | signed-in | Counts |
| GET | `/departments` | admin | Departments with course and candidate counts |
| GET | `/courses?q=` | admin | Courses with candidate counts, sitting and paper group |
| GET | `/candidates?q=&department=&accessible=&page=&page_size=` | signed-in | Search (roll number or name), paginated |
| GET | `/candidates/{id}` | signed-in | A candidate with their published seats |
| GET | `/halls` | signed-in | Halls with layouts and the per-paper ceiling |
| PATCH | `/halls/{id}` | admin | `{"is_active": false}` - exclude from new plans |
| GET | `/sessions` | signed-in | Sittings with papers, candidate counts and plan status |
| GET | `/sessions/{id}` | signed-in | One sitting |

```json
GET /api/data/summary
{"departments": 7, "courses": 49, "candidates": 908, "accessible_candidates": 10, "registrations": 2724,
 "halls": 14, "active_halls": 14, "seats": 871, "sessions": 6, "papers": 49}
```
```json
GET /api/sessions  (first item, abridged)
{"id": 1, "code": "S20261012-0930", "label": "Mon 12 Oct 2026 · Morning", "date": "2026-10-12",
 "start_time": "09:30", "end_time": "12:30",
 "papers": [{"course_id": 1, "course_code": "ACF-101", "course_name": "Principles of Accounting",
             "department_code": "ACF", "paper_group": null, "candidates": 65}, "..."],
 "candidates": 451, "accessible_candidates": 7,
 "plans": {"count": 1, "latest_id": 1, "latest_status": "published", "published_id": 1}}
```

## Plans

| Method | Path | Access | Purpose |
|---|---|---|---|
| POST | `/sessions/{id}/plans` | admin | Generate a plan: `{"rules": {...}, "hall_ids": [..] \| null, "seed": 123 \| null}` -> `201` plan. `422` with reasons if impossible. |
| GET | `/sessions/{id}/plans` | signed-in | Versions of a sitting |
| GET | `/plans?status=` | signed-in | All plans |
| GET | `/plans/{id}` | signed-in | Plan with scorecard, halls, baseline, fingerprints |
| POST | `/plans/{id}/publish` | admin | Publish (the previous published version becomes *archived*) |
| POST | `/plans/{id}/verify` | admin | Re-run the engine with the stored seed and compare |
| PUT | `/plans/{id}/invigilators` | admin | `{"assignments": [{"hall_id": 11, "user_ids": [2]}]}` |
| DELETE | `/plans/{id}` | admin | Delete a draft or archived version (`409` for published or after attendance) |

```json
POST /api/sessions/3/plans  ->  201 (summary fields)
{"id": 3, "version": 1, "status": "draft", "seed": 1737902151, "solve_ms": 2737, "swaps": 0,
 "candidates": 451, "halls_used": 6, "utilisation": 0.9223,
 "same_paper_pairs": 0, "roll_gap_violations": 0, "accessible_violations": 0, "same_department_pairs": 0,
 "hard_ok": true, "conflicts_avoided": 1105,
 "rules": {"adjacency": 8, "roll_gap": 5, "department_mix": true, "fill_strategy": "compact", "accessible_per_hall": 2},
 "engine_version": "1.0.0", "data_fingerprint": "...", "solver_hash": "a10285d4...", "assignment_hash": "a10285d4...",
 "scorecard": {"...": "..."},
 "baseline": {"method": "sequential roll order", "same_paper_pairs": 1105, "roll_gap_violations": 342,
              "same_department_pairs": 1194, "accessible_violations": 7, "neighbour_pairs": 1315},
 "stats": {"engine_version": "1.0.0", "hall_budget": 0.15, "halls_used": 6, "retries": 0, "solve_ms": 2737,
           "attempts": 1, "stage_a_ms": 1575, "stage_b_ms": 1160},
 "halls": [{"hall_id": 11, "code": "EW-205", "name": "East Wing Lecture Room", "capacity": 79, "placed": 75,
            "utilisation": 0.9494, "papers": {"ACF-102": 10, "BMG-202": 16, "...": "..."},
            "invigilators": [{"id": 10, "full_name": "Kenji Watanabe"}]}, "..."]}
```
Impossible request: `422 {"detail": "A plan could not be generated: 451 candidates but only 36 usable seats in the selected halls. Select halls with at least 415 more seats.", "details": ["..."]}`

```json
POST /api/plans/3/verify
{"plan_id": 3, "seed": 1737902151, "data_unchanged": true, "reproduced": true,
 "stored_solver_hash": "a10285d448ce235f160b3ba6fcdd286a5a829a0955099e8b391684caec593b00",
 "recomputed_hash": "a10285d448ce235f160b3ba6fcdd286a5a829a0955099e8b391684caec593b00",
 "manual_moves": 0, "engine_version": "1.0.0", "solve_ms": 2470}
```

## Seat maps and moves

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/plans/{id}/halls/{hall_id}` | admin or assigned invigilator | Hall layout, seats, legend, violations, attendance counts |
| GET | `/plans/{id}/halls/{hall_id}/swap-check?seat=C4` | admin | For the candidate on C4: every other seat, whether moving there keeps the rules, and why not |
| POST | `/plans/{id}/swap` | admin | `{"hall_id": 11, "from_seat": "A4", "to_seat": "A6"}` - move or swap; `409` with reasons if not allowed |

```json
GET /api/plans/3/halls/11/swap-check?seat=A4  (two of the targets)
{"seat": "A4", "candidate": "SWE24055", "targets": [
  {"seat": "A6", "occupied": true, "ok": true, "reasons": [], "notes": ["MCD24037 and MCD24013 are both from MCD."]},
  {"seat": "A1", "occupied": true, "ok": false, "notes": [], "reasons": [
    "SWE24055 would sit next to SWE24044 (A2) - both write SWE-201.",
    "BMG24026 would sit next to BMG24040 (A3) - both write BMG-202."]}]}
```
```json
POST /api/plans/3/swap {"hall_id": 11, "from_seat": "A4", "to_seat": "A1"}  ->  409
{"detail": "This move is not allowed: SWE24055 would sit next to SWE24044 (A2) - both write SWE-201. ...",
 "details": {"ok": false, "reasons": ["..."], "notes": []}}
```
A successful move returns `{"ok": true, "message": "Swapped ...", "notes": [...], "assignment_hash": "...", "hard_ok": true}`.

## Exports

All take an optional `?hall_id=` to limit the file to one hall. Invigilators may download only with the `hall_id` of a hall they supervise. Every download is recorded in the audit trail.

| Method | Path | File |
|---|---|---|
| GET | `/plans/{id}/exports/seating-charts.pdf` | One landscape page per hall |
| GET | `/plans/{id}/exports/invigilator-sheets.pdf` | Instructions, paper counts, seat list with present and signature columns |
| GET | `/plans/{id}/exports/hall-lists.xlsx` | Summary, one sheet per hall, roll-order door list |
| GET | `/plans/{id}/exports/qr-slips.pdf` | Six seat slips per page |
| GET | `/plans/{id}/exports/attendance.xlsx` | Attendance by hall and course |

## Attendance

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/attendance/assignments` | signed-in | My halls (all halls for administrators) with counts |
| PUT | `/plans/{id}/halls/{hall_id}/attendance/{candidate_id}` | admin or assigned | `{"status": "present" \| "absent" \| null}` |
| POST | `/plans/{id}/halls/{hall_id}/attendance/scan` | admin or assigned | `{"code": "<slip URL or roll number>"}` -> marks present |
| POST | `/plans/{id}/halls/{hall_id}/attendance/mark-remaining-absent` | admin or assigned | Everyone unmarked becomes absent |
| POST | `/plans/{id}/halls/{hall_id}/attendance/submit` | admin or assigned | Lock the register (`409` while anyone is unmarked) |
| POST | `/plans/{id}/halls/{hall_id}/attendance/reopen` | admin | Unlock |

```json
POST /api/plans/1/halls/11/attendance/scan {"code": "http://192.168.1.20:5113/lookup/DAN25047"}
{"candidate": {"id": 374, "roll_no": "DAN25047", "full_name": "Arjun Lambert"}, "seat": "A2", "already_present": false,
 "counts": {"total": 74, "present": 2, "absent": 0, "unmarked": 72, "submitted_at": null}}
```
Wrong hall: `409 {"detail": "... sits in MB-101 (Room 101), seat C4 - please send them there."}`. Not in this sitting: `404`.

## Public (no sign-in)

Rate-limited per device (`LOOKUP_RATE_LIMIT_PER_MINUTE`, `429` when exceeded). Only published plans are shown.

| Method | Path | Purpose |
|---|---|---|
| GET | `/public/lookup/{roll_no}` | The candidate's seats (roll numbers are case-insensitive) |
| GET | `/public/slip/{roll_no}/{plan_id}.pdf` | Seat slip with QR code |
| GET | `/public/qr/{roll_no}.png` | The QR code image |
| GET | `/public/engine-summary` | Headline benchmark figures for the home page |

```json
GET /api/public/lookup/MCD24037  (first seat)
{"candidate": {"roll_no": "MCD24037", "name": "Yusuf A."},
 "seats": [{"plan_id": 1,
            "session": {"label": "Mon 12 Oct 2026 · Morning", "date": "2026-10-12", "start_time": "09:30", "end_time": "12:30"},
            "status": "upcoming", "course": {"code": "MCD-202", "name": "Machine Design"},
            "hall": {"code": "MB-101", "name": "Room 101", "where": "Main Building, floor 1", "rows": 8, "cols": 8,
                     "blocked": [], "accessible": ["A1", "A2"], "aisles": [4]},
            "seat": {"label": "H3", "row": 7, "col": 2, "accessible": false}}, "..."]}
```
Unknown ID: `404 {"detail": "We could not find a published seat for this candidate ID. Check the ID, or look again closer to the exam."}`

```json
GET /api/public/engine-summary
{"available": true, "run_date": "2026-09-21T12:41:23+00:00", "typical_candidates": 600, "typical_solve_s": 2.36,
 "conflicts_avoided": 1253, "same_paper_pairs": 0.0, "roll_seat_correlation": 0.065, "neighbour_overlap": 0.0101,
 "runs": 24, "largest_candidates": 2000, "largest_solve_s": 4.8, "all_hard_rules_satisfied": true}
```

## Analytics and audit (admin)

| Method | Path | Purpose |
|---|---|---|
| GET | `/analytics/overview` | Counts, totals (conflicts avoided, solve times, rules met), attendance, per-sitting rows, solve-time list, hall usage |
| GET | `/analytics/plans/{id}` | Per-hall utilisation and departments, SeatWise vs roll-order comparison, neighbour-pair breakdown, attendance per hall |
| GET | `/analytics/engine` | The benchmark run in `models/engine_profile.json` (profile, metrics, plot URLs) |
| GET | `/analytics/engine/plots/{name}` | A benchmark chart (only names listed in the run) |
| GET | `/audit?plan_id=&action=&limit=` | Audit events, newest first (`action` matches by prefix, e.g. `plan.`) |

```json
GET /api/audit?limit=1
[{"id": 14, "at": "2026-09-21T13:42:51.415741", "action": "plan.verified",
  "summary": "Alex Morgan verified version 1 of Tue 13 Oct 2026 · Morning: reproduced exactly",
  "actor": "Alex Morgan", "plan_id": 3, "details": {"seed": 1737902151, "reproduced": true, "...": "..."}}]
```

Audit actions: `user.registered`, `user.created`, `user.updated`, `settings.rules`, `workspace.reset`, `import.committed`, `hall.updated`, `plan.generated`, `plan.failed`, `plan.published`, `plan.verified`, `plan.seat_moved`, `plan.invigilators`, `plan.exported`, `plan.deleted`, `attendance.submitted`, `attendance.reopened`.
