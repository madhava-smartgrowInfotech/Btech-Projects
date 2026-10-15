# Frontend plan - CallSense (kit V2, Neo Brutal Grid)

Ports: backend **8217**, frontend **5217** (confirmed in `.env`, `vite.config.js` and `run.bat`). Backend starts and `/api/health` returns `models_ready: true`.

## 1. Backend endpoints (all under `/api`, JWT bearer unless noted)

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | `/auth/login` | `{email, password}` | `{token, user{id,name,email,role}}`; 401 on bad credentials |
| GET | `/auth/me` | - | user |
| GET | `/health` (public) | - | `{ok, models_ready, gemini_configured, queue}` |
| GET | `/agents` | - | `[{id,name,email}]` (agents see only themselves) |
| GET | `/calls` | query `q, agent_id, intent, status, limit` | `{calls:[brief], queue}`; brief = id,title,source,is_sample,status,stage,error,duration,agent,agent_id,intent,topic,sentiment,score,flags(count),recorded_at,summary(text),snippet |
| POST | `/calls` | multipart `files[]`, `agent_id?`, `source`, `title?` | `{calls:[brief]}`; 400 on bad type/size |
| GET | `/calls/{id}` | - | brief + channels, segments[], intent_confidence, intent_top[], intent_evidence, keywords[], sentiment_change, flags[], summary{}, summary_error, scorecard{}, reference{}, processed_at |
| GET | `/calls/{id}/audio` | token in header or `?token=` | audio file |
| POST | `/calls/{id}/reprocess` | - | brief; 409 if running |
| POST | `/calls/{id}/summary` | - | full call; 409 if not done, 502 if Gemini fails |
| DELETE | `/calls/{id}` | - | `{ok}`; 409 if running |
| GET | `/analytics` | query `days` | `{days, totals, trend[], intents[], topics[], emotions[], leaderboard[], recent_escalations[]}` |
| GET | `/metrics` | - | `{training, evaluation}` (either may be null) |
| GET | `/studio/scripts` | - | `[{id,title,intent,agent,text}]` |
| POST | `/studio/generate` | `{script_id?, script_text?, title?, agent_id?}` | brief; 400 on bad script |
| POST | `/studio/import-samples` | supervisor only | `{added, skipped, calls[]}` |

No backend change is needed; no endpoint will be added.

## 2. Features / screens that exist today

| # | Feature | Where |
|---|---------|-------|
| F1 | Public landing page with product pitch and six feature cards | `/` |
| F2 | Sign in, demo-account quick fill (supervisor / agent), error message, token stored | `/login` |
| F3 | Route guard + sign out + user name/role shown | shell |
| F4 | Call list: transcript search (with snippet), agent filter (supervisor), sample/microphone badges, flag count, status badge, auto-poll while analysing | `/calls` |
| F5 | Upload one or many recordings (+ assign agent for supervisors) | `/calls` |
| F6 | Record from microphone, stop and analyse | `/calls` |
| F7 | Load the 10 bundled sample calls (supervisor) | `/calls` |
| F8 | Call detail header: agent, date, length, status, Re-run analysis, Delete | `/calls/:id` |
| F9 | Audio player with seek from transcript, flags and timeline | `/calls/:id` |
| F10 | Pipeline progress state (queued / processing stage) and failed state | `/calls/:id` |
| F11 | Emotion timeline (customer valence line, emotion dots, flag markers, playhead, show-agent toggle, legend, customer journey) | `/calls/:id` |
| F12 | Escalation flags list (click to seek) | `/calls/:id` |
| F13 | Transcript with speaker, emotion, text sentiment, voice emotion, active-line highlight | `/calls/:id` |
| F14 | Gemini summary: reason, resolution + status, customer mood, action items, model; Regenerate | `/calls/:id` |
| F15 | Intent, topic, confidence, evidence, runners-up, sample ground-truth tick, keywords, sentiment average and change | `/calls/:id` |
| F16 | Agent scorecard (total /100, per-criterion points, bar, evidence, speaker mode) | `/calls/:id` |
| F17 | Sample call studio: script list, edit title/agent/script text, write-your-own, generate and analyse | `/studio` |
| F18 | Analytics: period select (7/30/90 d), 6 stat tiles, volume + sentiment trend, top intents, leaderboard, topics, customer emotions, recent escalations, 15 s refresh | `/analytics` |
| F19 | Model performance: headline stats, intent / sentiment / voice-emotion / transcription tables, per-class F1 bars, sample calls end-to-end table, notes | `/performance` |

## 3. Screen map (kit V2)

| Route | Shell | Kit pieces | Covers |
|-------|-------|------------|--------|
| `/` | `PublicShell` | Brand, ThemeToggle, Button, Reveal/Stagger/CountUp, Marquee-style ticker (CSS), live `/health` + `/metrics` figures | F1 |
| `/login` | split-screen brutal card | Field/Input, Button, Alert, Badge | F2 |
| `/calls` | `AppShell` | PageHeader, SearchField, Select, Table (cards on mobile), Badge, FileDrop, Modal (add calls), Toast, EmptyState, ErrorState, Skeleton | F3-F7 |
| `/calls/:id` | `AppShell` | Breadcrumbs, Tabs (Transcript / Summary / Scorecard), Card, KeyValueList, ProgressBar, Alert, Modal (delete confirm), custom `EmotionTimeline` (SVG, theme tokens) | F8-F16 |
| `/studio` | `AppShell` | Card list of scripts, Input, Select, Textarea, Button, Toast | F17 |
| `/analytics` | `AppShell` | StatCard + CountUp, recharts (lazy) bar/line, Table, Select, EmptyState | F18 |
| `/performance` | `AppShell` | StatCard, Table, bar chart (lazy), Tabs | F19 |

Cross-cutting: dark mode toggle in topbar (persisted by kit theme helper), skeleton / empty / error / success states on every screen, drawer sidebar under 1024px, reduced motion respected, lazy-loaded route chunks, keyboard focus rings and Escape-closes-overlay.

## 4. Tick-off (verified in the browser against the live API, plus `scripts/smoke_test.py` 20/20)

- [x] F1 landing - [x] F2 login + demo chips + error - [x] F3 route guard, sign out, user shown - [x] F4 list, search + snippets, agent filter, auto-poll
- [x] F5 upload (multi-file) - [x] F6 microphone recorder (button + graceful permission-denied error; real recording needs a mic) - [x] F7 load sample calls
- [x] F8 detail header, re-run, delete (confirm modal, Escape closes) - [x] F9 audio + seek from timeline, transcript and flags - [x] F10 queued / processing / failed states
- [x] F11 emotion timeline + journey - [x] F12 escalation flags - [x] F13 transcript - [x] F14 summary + regenerate - [x] F15 intent / topic / keywords
- [x] F16 scorecard - [x] F17 sample studio (stock script, custom script, invalid-script error) - [x] F18 analytics (period, tiles, charts, leaderboard, escalations)
- [x] F19 model performance (tiles, five tabs)

Cross-cutting checks: console clean (no errors, no 404s except the expected "call not found" for another agent's call); no horizontal overflow at 360 / 768 / 1440 in light and dark; dark mode persists; reduced motion renders all content; mobile drawer + bottom bar; keyboard focus rings, Escape closes overlays.

## 5. Notes
- Kit files referenced `lib/auth`, `lib/storage` and `lib/gsap`, which the kit does not ship; they were written inside this project (`frontend/src/lib`). `Layout.jsx` (navigation), `FileDrop.jsx` (audio, multiple files), `Display.jsx` (call status badge) and `Charts.jsx` (horizontal bars, trend chart) are adapted copies; the kit folder itself was not touched.
- Tailwind was removed (the kit is plain CSS). Fonts come from `@fontsource` packages so the app has no external requests.
- No backend change and no new endpoint.
- `leaflet` is installed because the kit install command lists it, but no screen uses it.
