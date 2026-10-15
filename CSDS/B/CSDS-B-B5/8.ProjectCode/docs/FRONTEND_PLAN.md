# SignBridge - Frontend Plan (kit V5 "Kinetic Mono")

Backend: FastAPI on **8205**; frontend: Vite on **5205** (both set in `.env`, verified). Vite proxies `/api` to the backend.
The project already has a working Tailwind frontend (`frontend/src/pages/*`, `hooks/*`). It is rebuilt on the V5 kit
below; the recognition/subtitle hooks and API logic are kept (they are the product), the look is replaced.

## 1. Backend endpoints (no changes planned)

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| POST | `/api/auth/register` | - | `{name, email, password>=6}` | `{token, user:{id,name,email}}` |
| POST | `/api/auth/login` | - | `{email, password}` | `{token, user}` (401 "Wrong email or password") |
| GET | `/api/auth/me` | JWT | - | `{id,name,email}` |
| POST | `/api/recognize/frame?session=&mode=words\|letters` | JWT | body: one JPEG | `{hands, landmarks{left,right}, events[], live[], spelling, latency_ms{total,..}, fps}`; events: `sign{gloss,text,confidence,fingerspelled}`, `letter{letter,confidence,spelling}`, `rejected{reason,top[]}` |
| POST | `/api/recognize/reset?session=` | JWT | - | `{ok}` |
| POST | `/api/sentence` | JWT | `{glosses[], use_gemini}` | `{sentence, draft, source: rules\|gemini, online, model?, latency_ms}` |
| POST | `/api/tts` | JWT | `{text, rate}` | `audio/wav`, header `X-Latency-Ms` |
| POST | `/api/speech/transcribe?language=en\|hi\|auto` | JWT | body: 16 kHz mono int16 PCM | `{text, language, audio_seconds, latency_ms}` (503 while model loads) |
| POST | `/api/conversations` | JWT | `{title, messages[{side,text,gloss,confidence,latency_ms,source}]}` | `{id,title,messages}` |
| GET | `/api/conversations` | JWT | - | `[{id,title,created_at,messages}]` |
| GET | `/api/conversations/{id}` | JWT | - | `{id,title,created_at,messages[]}` |
| POST | `/api/conversations/{id}/messages` | JWT | one message | message |
| DELETE | `/api/conversations/{id}` | JWT | - | `{ok}` |
| GET | `/api/health` | - | - | `{status, models_loaded, speech_ready, speech_model, online, gemini_configured}` |
| GET | `/api/vocab` | - | - | `{words[{gloss,text,category}], letters[]}` |
| GET | `/api/metrics` | - | - | `{evaluation, training, live{frames,avg_frame_ms,p95_frame_ms}}` |

## 2. Features (each is ticked in section 4 after Step 4)

1. Landing page; 2. Register / sign in (demo account pre-filled), sign out
3. Webcam sign recognition with hand-skeleton overlay, FPS + latency, hands-detected badge, live top-3 guess
4. Words mode (50 signs) and fingerspelling mode (A-Z, 1-9) with live spelling
5. Recognised-sign chips (remove one, clear all), confidence per sign
6. Sentence building: manual button, auto after 3 s pause, Gemini polish toggle, rules/gemini source + latency + rule draft
7. Speak aloud (auto toggle + replay button) via offline TTS
8. Live subtitles: mic capture, partial + final text, English / Hindi / Auto, level meter, latency
9. Transcript of both sides, auto-scroll, download .txt, clear, save to History (append on re-save)
10. Practice mode: pick sign/letter (+ random), correct/wrong feedback, session score and attempt list, reset
11. History: list, open transcript, download .txt, delete
12. Model performance: stat tiles, word/letter tabs, confusion matrix with hover, per-class F1 table, latency table, live latency, reliability notes
13. Online / offline indicator + backend/speech-model status (from `/api/health`)
14. Dark mode toggle (persisted), 401 -> back to sign in, error state with retry on every fetch

## 3. Screen map (kit components)

| Route | Screen | Kit pieces |
|---|---|---|
| `/` | Landing | Backdrop (three.js grid, lazy), Typewriter, Reveal/Stagger, CountUp (real metrics from `/api/metrics`), MagneticButton, ActivityLog-style terminal demo |
| `/login`, `/register` | Auth | Card, Input, Button, ErrorState, Toast |
| `/app` | Conversation | AppShell, PageHeader, Card x4, Button, Switch, Select, Badge, Tabs (words/letters), StatusDot, ProgressBar, Toast |
| `/app/practice` | Practice | Card, Select, Button, StatCard, Timeline/list, EmptyState |
| `/app/history` | History | Table (cards on mobile), Modal/Drawer for transcript, ConfirmDialog via Modal, EmptyState, Skeleton |
| `/app/performance` | Performance | StatCard, Tabs, Table, charts.jsx (bar of per-class F1, latency), confusion grid, Skeleton, ErrorState |
| shell | Sidebar -> drawer <1024px, topbar (theme toggle, online badge, command palette, activity log, sign out) | AppShell, CommandPalette, ActivityLog |

## 4. Kit gaps found (adapted in this project's copy only)

The kit's 14 files import files that are **not in the kit**: `src/api.js`, `src/format.js`, `src/lib/reduced`, `src/lib/activity`,
`src/lib/auth`, `src/components/reactbits/Backdrop` (three.js grid). `AppShell` NAV and health polling are specific to
the source product (taxpayers, `/pipeline/status`). All of these will be written/adapted inside `frontend/src/`.
The kit also expects `styles/tokens.css`; its token CSS lives in `index.css`, which will be imported once from `main.jsx`.

## 5. Verification (Step 4)

Run against the live backend (8205) and dev server (5205) in Chrome via Playwright, with a recorded sign clip as the
camera, synthesised speech as the microphone, light + dark mode, 360 / 768 / 1440 px.

| # | Feature | Status |
|---|---|---|
| 1 | Landing page (Kinetic Mono: three.js grid, typewriter terminal, live metrics + vocabulary marquee) | [x] |
| 2 | Register / sign in (demo pre-filled), wrong-password error state, sign out, private-route redirect | [x] |
| 3 | Webcam recognition with hand skeleton, FPS + latency badges, hands-detected badge, live top-3 | [x] (GOOD recognised from the sample clip, 68-92 %) |
| 4 | Words mode and fingerspelling mode (live spelling) | [x] (letters path covered by `smoke_test.py`; tabs switch + reset session) |
| 5 | Recognised-sign chips: remove one, clear all, confidence | [x] |
| 6 | Sentence building: button, auto after 3 s pause, Gemini polish toggle, source + latency + rule draft | [x] ("Good." built offline after pause) |
| 7 | Speak aloud (auto toggle + replay) via offline TTS | [x] (`/api/tts` 200 from the UI; WAV verified by smoke test) |
| 8 | Live subtitles: mic, partial/final text, EN / HI / auto, level meter, latency | [x] (synthesised phrase -> subtitle -> transcript) |
| 9 | Transcript: auto-scroll, download .txt, clear, save to History (append on re-save) | [x] |
| 10 | Practice: pick sign/letter + random, correct/wrong feedback, score + attempt list, reset; palette deep link `?target=` | [x] |
| 11 | History: list (table / cards < 640 px), open transcript, download .txt, delete with confirm | [x] |
| 12 | Performance: stat tiles, words/letters tabs, confusion matrix, per-class F1 table, latency chart + table, reliability, training | [x] |
| 13 | Online/offline indicator + system status (models, speech model) from `/api/health` | [x] |
| 14 | Dark mode toggle (persisted), 401 -> sign in, error state + retry on every fetch | [x] |

Other checks: `npm run build` passes; `scripts/smoke_test.py` ALL PASSED; console clean (no errors/warnings, no 4xx assets)
on every screen at 360 / 768 / 1440 px in both themes; no horizontal overflow; reduced motion (no typewriter caret,
marquee stopped, WebGL drawn once); mobile drawer + Escape; focus rings; every input labelled.
