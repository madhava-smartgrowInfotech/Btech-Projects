# MediQueue - frontend plan (Kinetic Mono, kit V5)

Step 1 inventory. Backend contracts are unchanged. Every item in section 3 must be ticked in Step 4.

Ports: backend **8215**, frontend **5215** (from `.env`). Backend start verified: `GET /api/health` -> `{"ok": true}`, 60 hospitals loaded.

---

## 1. Backend endpoints (every route in `backend/app/`)

Auth header `Authorization: Bearer <token>` on everything except the public ones marked *public*.
Roles: **patient**, **staff** (one hospital desk), **admin** (district, any hospital).

| # | Method + path | Who | Request | Response | Used by existing UI |
|---|---|---|---|---|---|
| 1 | `POST /api/auth/login` | public | `{email, password}` | `{token, user}` | Login |
| 2 | `POST /api/auth/register` | public | `{name, email, password, age?, gender? (M/F), phone?}` | `{token, user}` | Login (register tab) |
| 3 | `GET /api/auth/me` | any | - | user object | **no** (unused) |
| 4 | `GET /api/health` | public | - | `{ok}` | **no** (smoke test only) |
| 5 | `GET /api/hospitals` | public | - | `[hospital]` (id, name, lat, lon, address, ownership, specialties, has_emergency, op_limit, emergency_quota, avg_consult_min, op_start, booked, expected_attendance, quota_used, hard_cap) | Console (hospital picker) |
| 6 | `GET /api/hospitals/{hid}` | public | - | `hospital` | **no** (unused) |
| 7 | `PATCH /api/hospitals/{hid}` | staff (own) / admin | any of `op_limit, emergency_quota, avg_consult_min, op_start, specialties[], has_emergency` | `hospital` | Console - Settings |
| 8 | `GET /api/specialties` | public | - | `[string]` | Console (settings, refer modal) |
| 9 | `GET /api/symptoms` | public | - | `[{key, label, weight}]` | Book (symptom picker) |
| 10 | `POST /api/triage/map-text` | public | `{text}` (2-1000 chars) | `{symptoms[], source: "gemini" \| "keyword"}` | Book, Console (emergency) |
| 11 | `POST /api/triage` | public | `{symptoms[]}` | `{severity, score, red_flags, reasons, condition, specialty, advice, emergency, disclaimer, symptoms[]}` | Book |
| 12 | `POST /api/recommend` | public | `{lat, lon, severity, specialty?, date?, limit?, exclude[]?}` | `[{id, name, lat, lon, address, distance_km, specialties, has_emergency, op_limit, booked, free_slots, specialty_match, score, why[]}]` | Book (map + list) |
| 13 | `POST /api/bookings` | patient | `{hospital_id, date, symptoms[], patient_name?, age?, gender?}` | `booking` + `allocation`, `advice`, `disclaimer` (422 bad date/symptoms, 409 hospital full) | Book |
| 14 | `GET /api/bookings/mine` | patient | - | `[booking]` (last 50) | My tokens |
| 15 | `GET /api/bookings/{bid}` | owner / hospital manager | - | `booking` | Token detail |
| 16 | `GET /api/console/{hid}?date=` | staff / admin (own hospital) | - | `{hospital, date, booked, expected_attendance, quota_used, consult_min, severity_mix, called[], waiting[], finished[]}` | Console |
| 17 | `POST /api/console/{hid}/call-next` | staff / admin | - | `{called, queue}` | Console |
| 18 | `POST /api/console/bookings/{bid}/status` | staff / admin | `{status: "done" \| "no_show"}` | `booking` (409 if already finished) | Console |
| 19 | `POST /api/console/{hid}/emergency` | staff / admin | `{patient_name, age?, gender?, symptoms[], notes?}` | `booking` + `quota_note` | Console (emergency form) |
| 20 | `GET /api/referrals/targets?booking_id=&specialty=` | staff / admin | - | `{specialty, hospitals[]}` | Refer modal |
| 21 | `POST /api/referrals` | staff / admin | `{booking_id, to_hospital_id, specialty?, reason (3-500), notes?, consent_confirmed?}` | `referral` | Refer modal |
| 22 | `GET /api/referrals` | any (scoped by role) | - | `[referral]` (latest 200) | My tokens, Referrals |
| 23 | `POST /api/referrals/{rid}/consent` | patient | `{consent: bool}` | `referral` | Referrals |
| 24 | `POST /api/referrals/{rid}/accept` | receiving hospital | - | `referral` + `allocation` | Referrals |
| 25 | `POST /api/referrals/{rid}/complete` | receiving hospital | - | `referral` | Referrals |
| 26 | `POST /api/referrals/{rid}/decline` | receiving hospital | - | `referral` | Referrals |
| 27 | `GET /api/dashboard?date=` | admin | - | `{date, totals, severity, referrals, hospitals[]}` | Dashboard |
| 28 | `WS /api/ws/hospital/{hid}` | any | client sends `"ping"` every 25 s | server pushes `{type: "queue_changed", hospital_id, at}`; `hid = 0` = all hospitals | Console, Token detail, Dashboard |

Notes on the contract (no change needed, recorded for the UI):
- `booking` object: id, token, status (waiting / called / done / no_show / referred), position, ahead, wait_min, eta, consult_min, hospital, hospital_id, date, requested_date, moved, patient_name, severity, condition, specialty, symptoms[], noshow_prob, uses_quota, kind (op / emergency), referral_id, has_account, notes, created_at.
- `referral` object: id, booking_id, status (pending_consent -> sent -> accepted -> completed; or declined), from_hospital, to_hospital, specialty, reason, summary (only shown to the receiving side after consent), consent, new_booking, created_at, updated_at.
- Errors come back as FastAPI `{detail}`; `errMsg()` in `api.js` already turns them into text.

**Not in the API (needed for the kit UI):** nothing. The screens below use only the endpoints above. No new endpoint is planned.

---

## 2. Existing features and screens (from README, docs/PLAN.md and `frontend/src`)

| Screen (route) | Role | What it does today | Endpoints |
|---|---|---|---|
| Landing `/` | public | Hero, six feature cards, emergency notice, CTA to book or staff login | none |
| Login `/login` (`?role=staff`) | public | Login and register tabs, demo-account buttons (password `demo1234`) | 1, 2 |
| Book a visit `/book` | patient | Pick or type symptoms -> severity -> pick date -> hospitals on a Leaflet/OSM map -> book token | 9, 10, 11, 12, 13 |
| My tokens `/tokens` | patient | List of own tokens; banner for referrals awaiting consent | 14, 22 |
| Token detail `/tokens/:id` | patient / hospital | Token, position, est. wait, moved-day reason, live updates | 15, 28 |
| Hospital console `/console` | staff / admin | Hospital picker, date, OP booked / limit, expected attendance, emergency quota, severity mix, call next, done / no-show, refer, finished list, add emergency, live updates | 5, 16, 17, 18, 19, 10, 28 |
| Refer modal (inside console) | staff / admin | Department, ranked receiving hospitals, reason, notes, consent | 8, 20, 21 |
| Settings panel (inside console) | staff / admin | Edit OP limit, emergency quota, consult minutes, opening time, departments, emergency toggle | 8, 7 |
| Referrals `/referrals` | patient / staff / admin | Open / closed filter, step tracker, summary (locked until consent), consent, accept, decline, mark completed | 22, 23, 24, 25, 26 |
| District dashboard `/dashboard` | admin | Totals, load map (Leaflet), per-hospital table (load, waits, no-shows, severity), severity mix, referrals, live updates | 27, 28 |
| Global shell | all | Nav by role, log in / out, mobile menu, footer disclaimer, decision-support notice | - |

Behaviours that must survive the rebuild:
- Role guards: patients only book; staff only see their own hospital; admin sees everything; wrong role redirects to their home.
- Token page explains a move to a later day ("day was full").
- Emergency adds a booking with a quota note ("quota exceeded, still admitted" when over).
- Referral summary stays hidden from the receiving hospital until the patient consents.
- Gemini-or-keyword source is shown on the booking screen.

---

## 3. Feature checklist (ticked in Step 4 once walked end-to-end in the new UI)

- [x] Landing page with the Kinetic Mono character
- [ ] Register and log in (patient); log in as staff desk and admin; demo buttons; log out
- [x] Describe symptoms in free text (Gemini or keyword fallback shown)
- [ ] Pick symptoms from the list
- [x] Severity result with reasons, advice, emergency notice and disclaimer
- [x] Hospital suggestions for severity, specialty and date, on a map and in a list
- [x] Book a token; allocation reason shown; redirect to token page
- [ ] Booking rejected for a full hospital or bad date - error shown with what to do
- [x] My tokens list with status
- [ ] Token detail: position, est. wait, live update over WebSocket, moved-day reason
- [ ] Console: hospital picker (staff own / admin any), date switch
- [x] Console: stats (OP booked / limit, expected, quota, consult time, severity mix)
- [x] Console: call next (live), mark done / no-show
- [ ] Console: add emergency (with optional free-text symptoms), quota note
- [ ] Console: settings (limits, quota, consult minutes, opening time, departments, emergency toggle)
- [ ] Refer a patient: department, receiving hospital list, reason, notes, consent, send
- [ ] Referrals: list and filters, step tracker
- [ ] Referrals: patient consent / decline
- [ ] Referrals: receiving hospital accept / decline / mark completed
- [x] District dashboard: totals, load map, hospital table, severity mix, referral counts, live update
- [ ] Role-based navigation and redirects
- [x] Mobile menu (drawer) and responsive layout at 360 px

Added by the kit brief (not in the old app, must work): dark mode toggle (persisted), reduced motion, skeleton / empty / error / success states on every screen.

---

## 4. Kit mapping (kit V5, `D:\abstracts\Frontend_Kits\V5`)

| Need | Kit piece |
|---|---|
| Shell, nav, drawer | `ui/AppShell` (Sidebar, Container, PageHeader), `ui/nav` (NAV) |
| Buttons, forms | `ui/controls` (Button, IconButton, Input, Select, Textarea, Checkbox, Switch, SearchField) |
| Cards, stats, badges, severity | `ui/display` (Card, StatCard, Badge, RiskBadge, Severity, ScoreBar, Timeline, KeyValueList), `ui/feedback` (Modal, Drawer, useToast/ToastProvider, Tooltip, ProgressBar, Skeleton, PageSkeleton, EmptyState, ErrorState) |
| Tables | `ui/Table` |
| Tabs, wizard steps | `ui/feedback` (Tabs, TabPanel, Stepper, Breadcrumbs) |
| Charts | `ui/charts` (ChartFrame, MonoTooltip, ChartLegend, Sparkline, useChartTheme) |
| Live log in console / dashboard | `ui/ActivityLog` |
| Motion | `motion/index` (FadeIn, SlideUp, Stagger, Reveal, Parallax, PageTransition, MagneticButton, CountUp, Marquee) |
| Typing effect (landing) | `ui/Typewriter` |
| Theme | `lib/theme` (ThemeProvider, useTheme) |
| Command palette | `ui/CommandPalette` (optional; not required by the product) |

Gaps between the brief and the kit (to resolve in Step 2, copy only, kit untouched):
1. The brief names `styles/tokens.css` and `components/three`, `components/charts`. The kit has **none of these**: the stylesheet is `src/index.css` and charts live in `ui/charts.jsx`.
2. The brief asks for a **three.js grid background** on the landing page. The kit has **no three.js component**. Plan: write one small grid component in `frontend/src/components/three/` using `three` (lazy-loaded, disabled under reduced motion).
3. The brief asks for a **landing page from the kit's landing pieces**. The kit has **no landing page**. Plan: compose the landing from `Typewriter`, `Stagger`, `CountUp`, `Card`, `StatCard` and `MagneticButton`.
4. The brief lists `FileDrop`. The product has **no file upload**, so it stays unused.
5. The brief says to copy config files from the kit top level. The kit has **none** (Tailwind is wired by `@tailwindcss/vite`, already in `vite.config.js`).
6. The kit has **no map**. The product uses a Leaflet/OSM map in Book and Dashboard. Plan: keep `leaflet` (already in `package.json`), restyle `MapView` in kit tokens. Leaflet is not in the brief's install list, so it stays as the existing dependency.

---

## 5. Decisions taken (defaults, to be reviewed)

- Keep every route path and role guard as they are today.
- Keep Leaflet for maps. It is an existing feature and no kit piece replaces it.
- Keep the current `api.js` (axios, `/api` base, token handling) and `useQueueSocket` (WebSocket with reconnect). Only the UI is replaced.
- Heavy kit pieces (`three`, `react-force-graph-2d`, `gsap`, `lenis`) are lazy-loaded; `react-force-graph-2d` is only pulled in if a screen uses it. Initial plan: no screen uses it.
- The live-updates WebSocket is unchanged.
- Commit at Step 4 uses the prompt's message. Before committing, MASTER_PROMPT*.md and 2.ABSTRACT.docx must stay out of the product commit (see memory notes).


---

## 5. Step 4 verification record

Checked in this run:
- `npm run build`: passes (main bundle 627 kB / 214 kB gzipped; Dashboard, Console, Book, MapView and Backdrop load as separate chunks).
- `scripts/smoke_test.py` against the running API: 15 of 15 checks pass.
- Browser walk (Playwright, installed Chrome, offline so OSM tiles and Google Fonts are aborted): landing at 360 / 768 / 1440 px (dark), landing light; patient demo login -> free-text mapping -> severity -> hospitals -> booked token -> My tokens; hospital desk login -> call next (toast) -> limits modal -> emergency modal; admin login -> dashboard at 1440 and 768 px; referrals pages; 360 px drawer opens and Escape closes it. Result: no console errors, page errors, failed same-origin requests or horizontal overflow.

Not yet verified in a browser (ticks above are left open for these):
- Register a new patient account and log out (the demo logins were used instead).
- Clicking individual symptom chips (the walk used free text).
- Booking-rejected error screen (full hospital or bad date).
- Live WebSocket updates on the token page and the dashboard (the API smoke test covers the live push).
- Console: done / no-show buttons, emergency and limits saves, hospital picker for admin.
- Referrals: refer modal submit, patient consent / decline, receiving accept / decline / complete in the UI (API flow verified by the smoke test).
- Reduced-motion setting, and the light theme at 360 and 768 px.
- Dark-theme map tiles (tiles were unavailable offline).

Notes for the next person:
- Gemini is tried first for free-text mapping; offline it falls back after about 3 seconds. Online, each model can take up to 20 seconds before the keyword fallback, so the Book screen shows a loading state during that time.
- `frontend/src/components/ui.jsx` (old file, unreferenced) and `frontend/src/components/ui/CommandPalette.jsx` (kit file, unreferenced, TaxSentinel-only) are left in place. They are not imported and do not affect the build. Safe to delete.
