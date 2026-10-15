# CivicPulse - Frontend rebuild plan (Kit V1, Aurora Glass)

Ports: backend **8201**, frontend **5201** (confirmed in `.env`, `vite.config.js`, `run.bat`).
Backend start-up verified: `GET /api/health` -> `{"status":"ok","model_version":1,"gemini_configured":true}`.

## 1. Backend endpoints (unchanged by this rebuild)

Auth = `Authorization: Bearer <jwt>`; roles: citizen, officer, admin. "staff" = officer or admin.

| # | Method | Path | Role | Request | Response (shape) |
|---|---|---|---|---|---|
| 1 | POST | `/api/auth/login` | public | `{email, password}` | `{token, user:{id,name,email,role,department}}` |
| 2 | POST | `/api/auth/register` | public | `{name, email, password}` | `{token, user}` (citizen) |
| 3 | GET | `/api/auth/me` | any | - | `user` |
| 4 | GET | `/api/meta` | public | - | `{categories:[{name,department}], departments:[{id,name,sla_days}], priorities[], wards:[{name,lat,lng}]}` |
| 5 | GET | `/api/health` | public | - | `{status, model_version, gemini_configured}` |
| 6 | PUT | `/api/departments/{id}` | admin | `{sla_days}` (1-90) | `{id,name,sla_days}` |
| 7 | POST | `/api/complaints` | citizen | multipart: `text`, `lat?`, `lng?`, `photo?` (jpg/png/webp, <8 MB) | citizen view: `{id,tracking_id,text,language,photo_url,lat,lng,ward,status,created_at,resolved_at,department,expected_days,expected_by,timeline[],is_sample}` |
| 8 | GET | `/api/complaints/mine` | any | - | `[citizen view]` |
| 9 | GET | `/api/complaints/track/{tracking_id}` | any | - | citizen view (404 if not own) |
| 10 | GET | `/api/photos/{name}` | public | - | image file |
| 11 | GET | `/api/officer/queue` | staff | query `status`(Submitted/Assigned/In Progress/Resolved/Rejected/Open) `department` `priority` `q` | `{items:[queue item], total, counts:{status:n}}` |
| 12 | GET | `/api/complaints/{id}` | staff | - | detail: complaint + `ai` (category/department/priority + confidences, top3, proba, expected_days, explanations{category_words, priority_factors, time_factors}), `extraction`, `extraction_status`, `final`, `current`, `feedback[]`, `events[]`, `statuses` |
| 13 | POST | `/api/complaints/{id}/decision` | staff | `{category, department, priority, reasons:{field:text}, note}` | detail |
| 14 | POST | `/api/complaints/{id}/status` | staff | `{status: In Progress/Resolved/Rejected, note}` | detail |
| 15 | POST | `/api/complaints/{id}/extract` | staff | - | `{extraction, extraction_status}` (503 if Gemini fails) |
| 16 | POST | `/api/complaints/{id}/draft-reply` | staff | `{note}` | `{draft, ...}` (503 if Gemini unavailable) |
| 17 | POST | `/api/complaints/{id}/reply` | staff | `{message}` | detail |
| 18 | GET | `/api/model/metrics` | staff | - | `{current, model_version, new_labels_since_last_run, total_officer_labels, runs[]}` |
| 19 | POST | `/api/model/retrain` | staff | - | `{before, after}` metrics |
| 20 | GET | `/api/analytics/summary` | staff | - | KPI totals, by_status, open_by_priority, by_language, ai_acceptance, updated_at |
| 21 | GET | `/api/analytics/hotspots` | staff | `days`, `category` | `{days, wards[], recurring[], points[]}` |
| 22 | GET | `/api/analytics/sla` | staff | - | per-department SLA rows |
| 23 | GET | `/api/analytics/trends` | staff | `weeks` | `{weeks[], series:[{category,counts,total}]}` |

No new endpoints are needed - every screen below is served by the list above.

## 2. Existing features and screens

Features (README / docs/01_OVERVIEW.md): F1 complaint intake (text EN/HI/Hinglish, photo, map pin, tracking ID),
F2 classification + Gemini extraction, F3 priority, F4 resolution time + SLA flag, F5 LIME/SHAP explanations,
F6 officer workbench (accept/override with reason, status updates, retrain with before/after), F7 hotspots &
analytics (map, recurring, SLA table with admin edit, trends, model performance, 20 s live refresh), F8 draft reply
in the citizen's language.

Existing screens (frontend/src/pages): Landing, Login (+register, demo accounts), FileComplaint, Track (My
complaints + tracking-ID search + live 20 s refresh), Queue, ComplaintDetail, Analytics. Route guard by role, JWT in
localStorage, 401 -> redirect to login.

## 3. Screen map to build (every existing feature appears)

| Route | Role | Kit pieces | Endpoints | Features |
|---|---|---|---|---|
| `/` Landing | public | motion (Reveal, Stagger, CountUp, Parallax), landing/HowItWorks, StatsStrip, ExampleAnswer, MagneticButton, aurora hero | `/health`, `/meta` (real counts: categories, departments) | marketing of F1-F8 |
| `/login` | public | Card, Field, Tabs, Button | 1, 2 | login, register, demo accounts |
| `/file` | citizen | AppShell, Card, Field/Textarea, FileDrop, map picker (Leaflet, kept), Toast | 7 | F1 |
| `/track`, `/track/:id` | citizen | Card, Badge, Table/list, timeline, EmptyState, Skeleton | 8, 9 | F1 status timeline, replies, search, 20 s refresh |
| `/queue` | staff | Tabs, Table/cards, Select, Badge, Skeleton, EmptyState | 11, 4 | F2-F5 summary per row, SLA flag, key words, filters, 20 s refresh |
| `/complaints/:id` | staff | Card, Tabs, Select, Modal (confirm), Toast, Chart wrappers (diverging bars), Leaflet mini-map | 12-19, 4 | F5 explanations, F6 decision/status/retrain, F2 extraction, F8 draft + send reply |
| `/analytics` | staff | StatCard, Chart wrappers (trends), Table, Leaflet hotspot map, Modal | 20-23, 18, 19, 6, 4 | F7 KPIs, map, recurring, SLA table (+admin edit), trends, model performance, retrain |

Cross-cutting: AppShell (sidebar -> drawer under 1024 px), dark-mode toggle (persisted), role-based nav, toasts,
skeleton / empty / error states everywhere, `prefers-reduced-motion`, lazy-loaded Leaflet and charts, 360 px layout.

## 4. Feature checklist (verified after the rebuild)

Verified with Playwright (real Chrome) against the running API: `scripts/`-style walk of every screen at 360 / 768 / 1440 px in
light and dark (no horizontal overflow, empty console, no 4xx except the error states deliberately triggered), plus a scripted
end-to-end flow (register -> file with photo + pin -> officer override -> reply -> resolve -> citizen sees it -> admin SLA edit).

- [x] F1 File complaint: text, example chips, photo (type/size validation), map pin + "use my location", tracking ID success screen
- [x] F1 My complaints list, tracking-ID search, detail with department / expected date / ward / timeline, 20 s refresh
- [x] Register citizen account, log in, demo-account fill, log out, role redirect, 401 handling
- [x] F2 Queue shows category -> department with confidence, key words, language, ward, photo flag, Sample badge
- [x] F3/F4 Priority badge, expected days, SLA risk / breached flags
- [x] Queue tabs with counts, department / priority filters, text search, refresh, 20 s auto-refresh
- [x] F5 Complaint detail: LIME words, SHAP priority factors, SHAP time factors
- [x] F2 Gemini key details: pending polling, extract / re-run, failure message (*the UI path was verified; the Gemini API itself currently answers `400 Request contains an invalid argument`, so a successful extraction could not be shown - see summary*)
- [x] F6 Accept & assign / override with required reasons, note for citizen, change decision, overridden tags
- [x] F6 Status update (In progress / Resolved / Reject with reason + confirm dialog), activity log with internal tags
- [x] F8 Draft reply with Gemini (error path verified, same Gemini 400), edit, send, citizen sees it on the timeline
- [x] F6 Retrain model now with before / after table (detail page and analytics)
- [x] F7 KPI tiles, hotspot map (wards / complaints modes, window + category filters), recurring issues
- [x] F7 SLA table, admin-only SLA edit (modal, 1-90 validation from the API)
- [x] F7 Category trends (charts + table toggle), model performance card, live 20 s refresh
- [x] Dark mode (persisted), reduced motion, keyboard / focus (Escape closes drawer and dialogs), responsive 360 / 768 / 1440
- [x] `npm run build` passes (tsc + vite); smoke test passes its first 12 checks, then stops at the Gemini 400 above; console clean

## 5. Additions

- `GET /api/public/stats` (new, read-only, no auth): headline numbers from `experiments/eval/metrics.json` for the landing page.
- Kit copied into `frontend/src/` (ui, motion, charts, landing, brand, lib); product-specific parts adapted in the copy
  (AppShell navigation by role, Logo, HowItWorks steps, StatsStrip numbers, theme storage key). The kit folder was not touched.
