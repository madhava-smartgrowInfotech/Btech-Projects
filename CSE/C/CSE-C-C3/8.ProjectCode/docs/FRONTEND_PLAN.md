# Frontend Plan - ParkSure (Online Vehicle Parking Reservation System)

Design: **V3 Depth Studio** (kit copied into `frontend/src`). Ports: backend **8403**, frontend **5403**.
The Vite dev server proxies `/api` to `http://127.0.0.1:8403`, so the browser only ever talks to 5403.

## 1. Backend endpoint inventory

Auth = Bearer JWT from `/api/auth/login|register`. Errors are `{detail: string}` (422 gives a list).

| # | Method | Path | Auth | Request | Response |
|---|--------|------|------|---------|----------|
| 1 | POST | `/api/auth/register` | - | `{name(2-120), email, password(6-128)}` | `{token, user}` (first account on an empty DB becomes admin) |
| 2 | POST | `/api/auth/login` | - | `{email, password}` | `{token, user}`; 401 on bad credentials |
| 3 | GET | `/api/auth/me` | user | - | `user` = `{id,name,email,role,trust_score,benefit_streak,warning_count,account_credit,suspended_until}` |
| 4 | GET | `/api/locations` | - | - | `[{id,name,address,latitude,longitude,capacity,buffer_size,price_per_hour}]` |
| 5 | POST | `/api/locations` | admin | `{name,address,latitude,longitude,capacity,price_per_hour,buffer_size}` | location |
| 6 | PUT | `/api/locations/{id}` | admin | same as 5 | location; 404 |
| 7 | DELETE | `/api/locations/{id}` | admin | - | `{ok:true}`; 404 |
| 8 | GET | `/api/search?start_time&end_time` | - | ISO datetimes, window <= 30 days | locations + `{overlapping, bookable, available}` |
| 9 | POST | `/api/reservations` | user | `{location_id,start_time,end_time}` | reservation + `{credit_applied, amount_due, checkout{url,session_id,provider}, stripe_configured}`; 403 suspended, 409 full (both store a `declined` row) |
| 10 | GET | `/api/reservations` | user | - | my reservations (newest first) |
| 11 | POST | `/api/reservations/{id}/cancel` | owner/admin | - | reservation (credit refunded if paid) |
| 12 | POST | `/api/reservations/{id}/checkin` | owner/admin | - | `{moved, failed?, reservation, message, alternate?, distance_km?}` |
| 13 | POST | `/api/reservations/{id}/checkout` | owner/admin | - | `{reservation, on_time, message}` |
| 14 | GET | `/api/trust` | user | - | `{trust_score, benefit_streak, warning_count, next_reward_in, fee_multiplier, events[{kind,detail,at}]}` |
| 15 | GET | `/api/payments/demo-confirm?reservation_id&session_id` | - | - | `{ok, status}` |
| 16 | POST | `/api/payments/{rid}/confirm` | owner/admin | - | `{ok, status}` |
| 17 | POST | `/api/stripe/webhook` | Stripe sig | raw event | `{received}` (server-to-server, no UI) |
| 18 | GET | `/api/admin/overview` | admin | - | `{users,locations,reservations,revenue,unable_to_park,declined}` |
| 19 | GET | `/api/admin/users` | admin | - | `[user]` |
| 20 | GET | `/api/admin/bookings` | admin | - | last 300 reservations (with `location_name`, payment fields) |
| 21 | POST | `/api/admin/reset-buffers` | admin | - | `{reset_by_policy, forced}` |
| 22 | GET | `/api/admin/insights?window_days` | admin | - | `{window_days, per_location[], totals{fixed_0,fixed_1,fixed_3,dynamic}, policy, note}` |

Reservation shape: `{id,location_id,location_name,start_time,end_time,status,fee,fee_multiplier,checked_in_at,checked_out_at,decline_reason,parent_id,payment_status,payment_provider}`.
Statuses: `reserved | active | completed | cancelled | failed | declined`.

**Gaps the UI needs:** none blocking. There is no admin "list all users with bookings" beyond endpoints 19/20, which is enough. No backend change is planned.

## 2. Existing features / screens (old vanilla UI in `static/`, README, HOW_TO_RUN)

- [x] F1  Landing page: pitch, how it works, demo logins, location list
- [x] F2  Availability search by arrival/departure -> per-location free slots, buffer, price, "Full" state
- [x] F3  Reserve from a search result (redirects to login when signed out)
- [x] F4  Log in / create account (first account = admin), role-based redirect
- [x] F5  Log out; session persisted; 401 sends user back to login
- [x] F6  Dashboard: new reservation form (location, arrival, departure) with fee / credit / amount due feedback
- [x] F7  My bookings table: status badge, window, fee x multiplier, payment status, decline reason, "(alternate)" marker
- [x] F8  Booking actions: Check in, Cancel, Check out, Pay (Stripe link or demo confirm)
- [x] F9  Check-in edge cases: moved to nearest alternate (distance), failed + credited
- [x] F10 Check-out result: on time vs late overstay message
- [x] F11 Trust Score card: score/5 stars, fee multiplier, benefit streak, next reward, warnings, event history, suspension notice
- [x] F12 Account credit balance shown
- [x] F13 Admin overview stats (users, locations, reservations, paid revenue, unable to park, declined)
- [x] F14 Admin locations: list, add, edit, delete, reset all buffers
- [x] F15 Admin Strategy Insights: recompute, bar chart (buffer 0 / 1 / 3 / dynamic), per-location actual vs simulated table, policy note
- [x] F16 Admin recent bookings table
- [x] F17 Admin users list (endpoint exists, old UI never showed it)
- [x] F18 Pay-return banners (`/?paid=` and `/?cancelled=` from Stripe success/cancel URLs)

## 3. Screen map (React Router)

| Route | Screen | Kit pieces | API | Features |
|-------|--------|-----------|-----|----------|
| `/` | Landing - three.js hero, scroll storytelling (search -> reserve -> check in -> trust), live location marquee/stats, demo logins, CTA | Reveal, Parallax, Marquee, MagneticButton, CountUp, HeroVisual, landing.css | 4 | F1, F18 |
| `/login` | Sign in / create account tabs, demo-login chips | Tabs, Input, Button, Toast | 1, 2 | F4 |
| `/app/find` | Find parking: time range, results grid, reserve modal with fee quote, post-booking success + pay | Card, Input, Badge, Modal, Skeleton, EmptyState, ErrorState | 8, 9, 15, 16 | F2, F3, F6, F12 |
| `/app/bookings` | My bookings: status tabs, sortable table / cards, check in / out / cancel / pay, alternate-move notice | Table, Tabs, Badge, Modal (confirm), Toast | 10-13, 15, 16 | F7-F10 |
| `/app/trust` | Trust Score: radial score, multiplier ladder, streak progress, event timeline, suspension notice | StatCard, ProgressBar, Timeline, KeyValueList | 14, 3 | F11, F12 |
| `/app/admin` | Overview: stat cards + insights headline chart | StatCard, ChartCard, GroupedBarChart | 18, 22 | F13 |
| `/app/admin/locations` | Locations CRUD + reset buffers | Table, Modal, Input, Toast | 4-7, 21 | F14 |
| `/app/admin/insights` | Strategy Insights: window selector, grouped bars, per-location table, policy | ChartCard, GroupedBarChart, Table | 22 | F15 |
| `/app/admin/bookings` | All recent bookings (+ search/filter) | Table, SearchField, Badge | 20 | F16 |
| `/app/admin/users` | Users with trust and credit | Table, Badge | 19 | F17 |

Sidebar shows Driver group always, Admin group only for `role === admin`. Topbar: page title, theme toggle (persisted), credit pill, user menu / log out.

## 4. Environment

- `.env` (git-ignored) and `.env.example`: `PARKSURE_PORT=8403`, `FRONTEND_PORT=5403`.
- `run.bat` starts uvicorn on 8403 and the Vite dev server on 5403, then opens http://localhost:5403.
- The old `static/` UI is left in place (still served by FastAPI on 8403) but is no longer the entry point.
- Backend start confirmed on 8403 (`GET /api/locations` returned the 5 seeded locations).

## 5. Verification (all 18 features above ticked after checking in a real browser)

How each was checked (Playwright against the running app, backend on 8403, frontend on 5403):

- F1 landing, F18 Stripe return banners (`/?paid=` and `/?cancelled=`), theme toggle + persistence: browser walk.
- F2-F3 search and reserve, F6 fee / credit / amount due, F8 pay (demo checkout): browser walk and `scripts/smoke_test.py`.
- F4-F5 sign in, register errors, log out, expired token sends you to login: browser walk.
- F7-F10 bookings table, check in, check out, cancel (with confirm dialog), alternate booking after a full lot (a one-bay location filled by an earlier check-in moved the second driver to the nearest location): browser walk.
- F9 "unable to park, fee credited" (no alternate exists) is rendered from the same API response as the alternate case; the backend path was not triggered in the browser.
- F11-F12 trust score, history and credit: browser walk.
- F13-F17 admin overview, locations add / edit / delete / reset buffers, insights with window selector, all bookings (search + status filter), users: browser walk and smoke test.
- Layout: 360, 768 and 1440 px, light and dark, driver and admin routes - no horizontal overflow. Sidebar becomes a drawer on small screens; tables become cards.
- Reduced motion: no WebGL canvas (static fallback image), marquee static. Keyboard: visible focus ring, Escape closes dialogs and the drawer, every input has a label.
- Console: no errors or unhandled rejections on any screen. The only 401 logged is the deliberate wrong-password test.

## 6. Decisions and limits

- `app/main.py`: one-line fix, `FastAPI(..., lifespan=lifespan)`. The lifespan hook (create tables, seed demo data, start the buffer-reset scheduler) was defined but never attached, so a checkout without a `parksure.db` had no tables. No logic or API contract changed.
- `requirements.txt`: added `httpx2` (the smoke test's test client needs it).
- Pending Stripe payments can only be paid from the tab opened at reservation time: the API does not return the checkout URL again. Demo-provider payments can always be confirmed from My bookings.
- The backend has no "quote" endpoint, so the reserve dialog shows an estimate using the same formula (hours x rate x trust multiplier, minimum 15 minutes); the confirmation shows the server's figure.
- `parksure.db` and `.env` are git-ignored; the database is re-created and seeded on first start.
- Docker still runs the backend only (and the old `static/` pages).
