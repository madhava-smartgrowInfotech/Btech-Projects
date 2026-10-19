# ParkSure — Smart Parking Reservation Platform

ParkSure is a commercial-style web app where drivers search for parking, reserve in advance, pay online via Stripe (test mode), and manage bookings with in-app Check In / Check Out. Admins manage locations, users, bookings, payments, and view **Strategy Insights** — real analytics computed from stored booking history. The differentiator is the **Smart Availability Engine**: a per-location hold-back buffer plus a driver **Trust Score** system.

## Stack (exact)
- Language: **Python 3.11+** (tested 3.11–3.14)
- Backend: **FastAPI 0.115**, **SQLAlchemy 2.0**, **SQLite** (zero-config file `parksure.db`), **APScheduler 3.10** (buffer-reset job), **python-jose + passlib/bcrypt** (JWT auth), **Stripe SDK 10.x** (Checkout + webhook, test mode with demo fallback)
- Frontend: **React 19 + Vite** (JavaScript), design kit **V3 Depth Studio** (three.js hero, framer-motion, GSAP, Recharts), in `frontend/`. Dev server on port **5403** proxies `/api` to the backend on **8403**. The original vanilla pages in `static/` are still served by FastAPI at the backend port.
- Docs/PDF: **reportlab**; screenshots via **Playwright**.

## Quick start
Double-click `run.bat` (needs Python 3.11+ and Node 20+) → http://127.0.0.1:5403. Manual steps are in `HOW_TO_RUN.md`.

Demo logins: `admin@parksure.app / admin123`, `driver1@parksure.app / driver123`.

## Core rules (implemented for real)
- **Buffer policy**: each location starts at `BUFFER_INIT=1`; +1 on every on-time checkout up to `BUFFER_MAX=5`; scheduled job (`app/engine.py::reset_buffers_if_due`, every 30 min) resets locations whose `last_buffer_reset` is older than 24h. Admission: accept only if `overlapping_bookings + buffer < capacity`.
- **Arrival edge case**: if the site is physically full at check-in, the engine picks exactly one nearest alternate by **haversine** distance with forecasted space and auto-creates a reservation there; if none exists the booking is marked `failed` and the fee is credited/refunded automatically.
- **Trust Score** (0–5, starts at 3): on-time checkout = Benefit; B=3 consecutive Benefits → +1 (cap 5). Late checkout = Warning, streak reset; W=2 warnings → −1 (floor 0). Fees: multiplier table `{0:1.75,1:1.5,2:1.25,3:1.0,4:0.95,5:0.9}` applied at quote time. Trust below 1.5 with a violation in the last 14 days → next booking refused + 24h cooldown (`suspended_until`).
- **Strategy Insights** (`scripts/compute_buffer_strategy_metrics.py`, also `GET /api/admin/insights`): per location + totals of *Unable to Park* (status `failed`) and *Declined* (status `declined`), plus deterministic replay of the same request history under buffers 0 / 1 / 3 / dynamic. Rendered as a Chart.js bar chart. Nothing is hardcoded.

## Project layout
```
app/main.py      FastAPI app, all routes, scheduler, static serving
app/models.py    users, parking_locations, reservations, payments, trust_events
app/engine.py    buffer/trust/haversine/fee logic
app/auth.py      JWT + bcrypt + role guards
app/seed.py      realistic demo data (on-time + overstay mix)
scripts/compute_buffer_strategy_metrics.py   deterministic simulation + CLI
frontend/        React + Vite app (src/pages, src/components = kit V3 + ParkSure screens)
static/          original vanilla pages (superseded by frontend/, still served by the backend)
docs/            FRONTEND_PLAN.md (endpoints, features, screen map), screenshots/
screenshots/     real captures of the running app
run.bat / run-docker.bat / Dockerfile / docker-compose.yml
ParkSure_Product_Documentation.pdf
```

## Assumptions & engineering decisions
- Two-process app: FastAPI backend plus a React/Vite frontend; `run.bat` starts both. (The earlier single-service static UI remains under `static/`.)
- SQLite chosen for zero-config deploy; schema migrates via `Base.metadata.create_all`; swap `PARKSURE_DB` for Postgres in production.
- Stripe works in test mode when keys are set; otherwise a demo checkout keeps the product fully usable offline — clearly labelled in the UI.
- Geolocation uses self-implemented haversine on stored lat/long; no external geo API.
- Entry/exit is software-managed (Check In/Out buttons + admin panel); no hardware simulation.
- No ML component: insights are deterministic rule replays, which is auditable and appropriate for this product.
- Seed data (seeded demo users with mixed punctuality) exists so Strategy Insights has real history on a fresh install.

## API summary
Auth: `POST /api/auth/register|login`, `GET /api/auth/me` · Locations: `GET /api/locations`, `POST/PUT/DELETE /api/locations/*` (admin) · `GET /api/search?start_time&end_time` · Reservations: `POST /api/reservations`, `GET /api/reservations`, `POST /api/reservations/{id}/cancel|checkin|checkout` · Trust: `GET /api/trust` · Payments: `GET /api/payments/demo-confirm`, `POST /api/payments/{id}/confirm`, `POST /api/stripe/webhook` · Admin: `GET /api/admin/overview|users|bookings|insights`, `POST /api/admin/reset-buffers`. All endpoints validate input and return clear errors.
