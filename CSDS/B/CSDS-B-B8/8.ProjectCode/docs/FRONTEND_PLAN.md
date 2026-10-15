# CareWatch - Frontend plan (kit V3 "Depth Studio")

Batch CSDS-B-B8 · backend port **8208** · frontend port **5208** (both confirmed in `.env`, `run.bat`, `vite.config.js`).
The backend starts cleanly (`GET /api/health` -> `{"status":"ok"}`).

> Starting point: a Vite + React (JS) frontend already exists in `frontend/` (Tailwind v4, axios, 7 pages). It is
> rebuilt on the kit V3 copy; the existing pages are the feature source of truth.

## 1. Backend endpoints

Auth: `Authorization: Bearer <jwt>`; `?token=` is also accepted (used by `<img>`). All except register/login/health need it.

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/api/health` | - | `{status, monitoring}` |
| POST | `/api/auth/register` | `{name, email, password>=6}` | `{token, user:{id,name,email}}` |
| POST | `/api/auth/login` | `{email, password}` | `{token, user}` |
| GET | `/api/auth/me` | - | `{id,name,email}` |
| POST | `/api/monitor/start` | `{source?}` | monitor state |
| POST | `/api/monitor/stop` | - | monitor state |
| GET | `/api/monitor/state` | - | state (`running, fps, activity, confidence, probs, keypoints, frame_w/h, fall_state, inactive_seconds, enhanced, brightness, person, segment, recording, last_clip, ended, error`) + `alert:{id,detected_at,seconds_left}|null` |
| GET | `/api/monitor/frame.jpg` | `?token=` | JPEG (404 when privacy mode) |
| POST | `/api/monitor/record` | `{label, seconds 2-30}` | `{recording}` |
| GET | `/api/alerts` | `?limit=` | `[alert]` (id, kind, status, detected_at, impact_at, deadline, seconds_left, resolved_at/by, sent_at, detection_latency_ms, dispatch_ms, detected_to_sent_ms, has_snapshot, channels, details) |
| POST | `/api/alerts/{id}/ok` | - | alert (cancelled) |
| POST | `/api/alerts/test` | - | alert (dispatched test) |
| GET | `/api/alerts/{id}/snapshot` | `?token=` | JPEG |
| GET/POST | `/api/contacts` | `{name, relation, email, telegram_chat_id, active}` | `[contact]` / contact |
| PUT/DELETE | `/api/contacts/{id}` | same / - | contact / `{deleted}` |
| GET | `/api/telegram/chats` | - | chats that messaged the bot |
| GET/PUT | `/api/settings` | `{room_name, camera_source, privacy_mode, low_light, confirm_seconds, countdown_seconds, inactivity_minutes}` | settings + `channels:{telegram,email}` |
| GET | `/api/reports/daily` | `?day=YYYY-MM-DD` | totals, timeline, warnings, falls, seconds |
| GET | `/api/reports/days` | - | `[YYYY-MM-DD]` |
| GET | `/api/metrics` | - | `{training, evaluation, live}` |

No backend change is planned.

## 2. Features / screens that exist today (must all survive)

- [x] F1 Landing page (hero, six feature cards, sign-in/open-monitor CTA)
- [x] F2 Sign in / create account (demo login `demo@carewatch.app`), token persisted, 401 -> back to login
- [x] F3 Live monitor: start/stop, camera source field, live fps/stopped chip, low-light badge, brightness
- [x] F4 Privacy mode toggle: skeleton-only view vs. (unstored) video frames
- [x] F5 Skeleton canvas from live keypoints, red/teal by fall state
- [x] F6 Current activity + confidence + per-class probability bars, "nobody in view"
- [x] F7 Fall-detection state card (normal / possible / confirmed) + stillness time
- [x] F8 Record a training clip (label, seconds, progress, saved filename)
- [x] F9 Live activity timeline - last 30 minutes
- [x] F10 Global "I'm OK" countdown overlay on every screen + post-alert notice
- [x] F11 Alerts history: status, timings (detection / dispatch / total), channel results, snapshot, I'm OK, send test alert, Telegram/email configured state
- [x] F12 Contacts CRUD (name, relation, email, Telegram chat ID, active) + "Look up chats"
- [x] F13 Monitoring settings (room, camera source, privacy, low-light, confirm / countdown / inactivity thresholds)
- [x] F14 Daily report: date picker, days-with-data chips, 4 stat tiles, day timeline, time per activity, inactivity warnings + falls
- [x] F15 Model performance: per-condition accuracy, per-activity accuracy/F1 table, confusion matrices, fall sensitivity/specificity + scenario table, alert latency, training info, live alert stats
- [x] F16 Responsive nav, sign-out, error / empty / loading states

## 3. Screen map (kit V3)

| Route | Screen | Kit pieces | API |
|---|---|---|---|
| `/` | Landing - three.js hero (lazy), scroll-driven feature story, CTA | HeroVisual/HeroScene, motion helpers, landing.css | - |
| `/login` | Sign in / register tabs | Tabs, Card, Button, Toast | auth |
| `/monitor` | Live monitor | AppShell, Card, StatCard, Button, Modal, Skeleton, charts | monitor/*, settings, reports/daily |
| `/alerts` | Alerts + test alert + snapshot modal | Table, Modal, EmptyState, Toast | alerts/*, settings |
| `/contacts` | Contacts table + add/edit modal + settings form + Telegram lookup | Table, Modal, Toast, EmptyState | contacts, settings, telegram/chats |
| `/report` | Daily report | StatCard, charts, Table, EmptyState | reports/* |
| `/performance` | Model performance | StatCard, charts, Table | metrics |
| overlay | Fall countdown (every protected screen) | Modal | monitor/state, alerts |

Cross-cutting: dark/light toggle (kit theme helper, persisted), reduced-motion, drawer nav < 768px, focus rings.

## 4. Verification log

Built on kit V3 (copied to `frontend/src`, nothing imported from outside the folder). Old Tailwind/axios UI removed.
Backend logic and API contracts are unchanged; no endpoint was added.

| Check | Result |
|---|---|
| `npm run build` | passes (three.js chunk is lazy-loaded for the landing hero) |
| `scripts/smoke_test.py` | **SMOKE TEST PASSED** (login, contacts, monitoring, fall + I'm OK, second fall + expiry, dispatch, report, metrics) |
| Browser walk, every screen, 360 / 768 / 1440 px, light and dark | no console errors, warnings, failed requests or 404s; no horizontal overflow |
| Sign in (wrong password error, demo login), sign out | works |
| Contacts: add, edit, validation error, Escape closes modal, Telegram lookup error text | works |
| Settings save (toast) | works |
| Live monitor: start on the sample video, skeleton + activity + fall card, privacy toggle, record clip, stop | works |
| Fall countdown overlay on every screen: appears, Escape does not dismiss it, "I'm OK" cancels with a toast, countdown expiry closes it and reports the outcome | works (360 px light and 1280 px dark checked) |
| Alerts: history table, detail modal, test alert | works |
| Daily report, Model performance (charts, tables, confusion matrix) | work with real data |
| Dark mode toggle persisted; `prefers-reduced-motion` honoured (hero falls back to a static image, motion collapses to fades) | works |

Defaults chosen: routes moved under `/app/*` (old `/monitor` etc. redirect); the landing page figures come from
`experiments/eval/metrics.json` (see README); the fall overlay is intentionally not dismissable except by "I'm OK".
