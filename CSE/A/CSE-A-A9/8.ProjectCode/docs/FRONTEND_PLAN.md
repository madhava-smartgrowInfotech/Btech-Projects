# Frontend plan - BotGraph

Design: **V4 - Soft Pastel Calm** (kit copied into `frontend/src`). Ports: API 8309, web app 5309.

## 0. Starting point (what was found)

The folder held only the product brief and the environment file: no backend, no frontend, no models, no data.
The brief's own build (backend, ML pipeline, data, then UI) was therefore carried out first, and the frontend was
built on top of it. The backend and ML pipeline are described in `02_HOW_IT_WORKS.md`.

## 1. Backend endpoints (inventory)

All routes except `/api/health` and `/api/auth/login` need `Authorization: Bearer <token>`.

| Method | Path | Request | Response |
| --- | --- | --- | --- |
| GET | `/api/health` | - | status, account and tie counts, served model, flagged count, botnet count, best and baseline F1 |
| POST | `/api/auth/login` | `{email, password}` | `{token, user{id,email,name,role}}` |
| GET | `/api/auth/me` | - | the signed-in user |
| GET | `/api/graph/summary` | - | node / edge counts (real vs injected), class balance, split, 23 feature summaries, degree histogram, dataset provenance |
| GET | `/api/overview` | - | KPIs, score histogram, model F1 list, top accounts, top clusters, recent decisions |
| GET | `/api/accounts` | `q, status, flagged_only, cluster, sort, order, page, page_size` | one page of ranked accounts |
| GET | `/api/accounts/{id}` | - | score, per-model scores, top contributing features, neighbourhood summary, profile, decision history |
| GET | `/api/accounts/{id}/neighbourhood` | `limit` | nodes and links for the graph view |
| GET | `/api/clusters` | - | detected clusters with size, density, shared hour, status |
| GET | `/api/clusters/{id}` | - | members, shared behaviour, reach, graph nodes and links, headline |
| GET | `/api/queue` | `kind (accounts|clusters), state (pending|decided), page, page_size` | queue page and summary counts |
| POST | `/api/queue/decisions` | `{target_type, target_id, decision, note}` (moderator only) | the logged decision |
| DELETE | `/api/queue/decisions/{id}` | - (moderator only) | removes a decision not yet used in training |
| GET | `/api/decisions` | `limit` | decision log |
| GET | `/api/models` | - | per-architecture metrics, ROC points, confusion matrices, cluster recovery, retraining runs |
| GET | `/api/models/scalability` | - | training / inference time as the graph grows |
| POST | `/api/models/retrain` | - (moderator only) | starts a retraining run on the logged decisions |
| GET | `/api/models/retrain/status` | - | state, progress, message |

Added for the UI (thin, read-only, additive): `/api/overview`, `/api/graph/summary`, `/api/accounts/{id}/neighbourhood`,
and the public statistics in `/api/health` used by the landing page.

## 2. Features that must keep working

| ID | Feature | Screen |
| --- | --- | --- |
| F1 | Graph builder: nodes, edges, documented schema | Graph & features |
| F2 | Node features (profile, posting, timing, interaction) | Graph & features |
| F3 | GCN, GAT, GraphSAGE and a no-graph baseline on one split | Models & scale |
| F4 | Account scoring with top features and neighbourhood view | Accounts, Account detail |
| F5 | Botnet clusters with an interactive graph | Botnet clusters, Cluster detail |
| F6 | Moderator queue: confirm / dismiss, logged, feeds the next training run | Moderator queue |
| F7 | Evaluation per architecture plus scalability chart | Models & scale |
| - | Sign-in for analyst and moderator, demo logins | Login |

## 3. Screen map

| Route | Screen | Kit pieces |
| --- | --- | --- |
| `/` | Landing (light and dark) | hero, Blobs, Reveal, Stagger, CountUp, Marquee, MagneticButton |
| `/login` | Sign in with demo accounts | Input, Button, Callout, Blobs |
| `/app` | Overview | StatCard, BarCompare, Table, Timeline |
| `/app/graph` | Graph & features | StatCard, BarCompare, GroupedBars, Table, Callout |
| `/app/accounts` | Ranked accounts, filters, paging | Table, SearchField, Select, Segmented |
| `/app/accounts/:id` | Account detail, reasons, neighbourhood graph, decision | Card, Gauge, KeyValueList, Timeline, Modal, force graph |
| `/app/clusters` | Cluster list | Table, Badge |
| `/app/clusters/:id` | Cluster explorer (graph, members, decision) | StatCard, force graph, Table, Modal |
| `/app/queue` | Queue (accounts, clusters, decision log) and retraining | Tabs, Segmented, Table, ProgressBar, Toast |
| `/app/models` | Comparison, scalability, retraining runs | Tabs, GroupedBars, LineCompare, Table |

Every screen has a loading skeleton, an empty state with an action, an error state with a retry, and visible success feedback (toasts).

## 4. Verification (all ticked)

- [x] `npm run build` succeeds
- [x] F1 graph summary renders node and edge counts and the feature table
- [x] F2 features listed by group with genuine / fake means
- [x] F3 + F7 comparison table, precision / recall / F1 chart, ROC curves, confusion matrix, scalability charts
- [x] F4 ranked accounts, search, filters, detail with top features, neighbourhood graph
- [x] F5 clusters list, cluster graph, members, shared behaviour
- [x] F6 confirm / dismiss accounts and clusters, decision log, undo, retraining on the decisions
- [x] Sign-in for both roles; analyst is read-only
- [x] Dark mode toggle persists; reduced motion respected; keyboard focus rings; Escape closes dialogs
- [x] 360 px, 768 px and 1440 px without sideways scroll, light and dark (`scripts/ui_checks.py`)
- [x] Console clean on every screen (`scripts/capture_screens.py`)
- [x] `scripts/smoke_test.py` passes
- [x] Screenshots saved to `docs/screenshots`
