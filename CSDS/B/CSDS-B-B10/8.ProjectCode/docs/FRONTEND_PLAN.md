# Frontend plan - SkyCipher (Kinetic Mono, kit V5)

Step 1 inventory. Backend is unchanged. Ports confirmed in `.env`: backend **8210**, frontend **5210**.
Backend health checked: `GET /api/health` returns `{"status":"ok"}` on 8210.

Legend for Step 4: `[ ]` = not yet verified in the new UI. Tick to `[x]` once walked end to end.

---

## 1. Backend endpoints (all under `/api`)

Auth column: **B** = `Authorization: Bearer <token>` required; **-** = none.

| # | Method | Path | Auth | Request | Response |
|---|---|---|---|---|---|
| 1 | GET | `/health` | - | - | `{status}` |
| 2 | POST | `/auth/register` | - | JSON `{name, email, password}` (password >= 6) | `{token, user:{id,name,email}}` |
| 3 | POST | `/auth/login` | - | JSON `{email, password}` | `{token, user:{id,name,email}}` |
| 4 | GET | `/auth/me` | B | - | `{id,name,email}` |
| 5 | GET | `/samples` | - | - | `[{kind, name}]` (kinds: `visdrone`, `sipi`) |
| 6 | GET | `/samples/file/{kind}/{name}` | - | - | image file |
| 7 | GET | `/keys/new` | B | - | `{key}` (256-bit hex) |
| 8 | POST | `/studio/encrypt` | B | multipart: `file` **or** `sample_kind`+`sample_name`; optional `key` | `{job, key, resized, key_setup_ms, plain, cipher, coefficients, subbands, histograms:{plain,cipher}}` |
| 9 | POST | `/studio/decrypt` | B | form: `key` + (`job_id`) **or** (`file` cipher PNG + `nonce`) | `{decrypted, dec_ms, sha256, expected_sha256, match, key_matches_job, histogram}` |
| 10 | GET | `/studio/jobs` | B | - | `[job]` (latest 50) |
| 11 | GET | `/studio/jobs/{job_id}/cipher.png` | B | - | PNG attachment |
| 12 | POST | `/lab/analyze` | B | multipart: `file` / `sample_kind`+`sample_name` / `job_id`; optional `key` | `{id, created_at, entropy, chi_square, correlation, differential, quality, key_sensitivity, key_space, timing, image, key_fp, nonce, image_name, source, resized, thumbs?}` |
| 13 | POST | `/attacks/run` | B | multipart: same input as 12; optional `key`, `report_id` | `{results:[...], image_name}` (results carry preview images) |
| 14 | GET | `/lab/reports` | B | - | `[{id, image_name, created_at, entropy, npcr, uaci, has_attacks}]` (latest 50) |
| 15 | GET | `/lab/reports/{rid}` | B | - | `{id, created_at, ...report}` |
| 16 | GET | `/lab/reports/{rid}/export?fmt=html\|json` | B | query `fmt` | HTML or JSON attachment |
| 17 | POST | `/bench/run` | B | JSON `{size: 256\|512\|1024, images: 1-20, repeats: 1-10}` | `{id, created_at, ...bench result, image_names}` |
| 18 | GET | `/bench/runs` | B | - | `[{id, created_at, ...bench result}]` (latest 10) |
| 19 | GET | `/live/sequences` | B | - | `[{name, frames}]` |
| 20 | POST | `/live/start` | B | JSON `{sequence, key, fps: 1-30, width: 64-1280}` | `{started:true}` |
| 21 | POST | `/live/stop` | B | - | `{stopped:true}` |
| 22 | GET | `/live/status` | B | - | `{sender, uplink, ground_stations}` |
| 23 | WS | `/live/uplink?token=` | token | UAV side: binary packets | none (relayed to ground stations) |
| 24 | WS | `/live/ground?token=` | token | first text msg `{key}` | `{ready:true}`, then per-frame decrypted output + link stats; `{error}` on bad key |
| 25 | WS | `/live/camera?token=` | token | first text msg `{key, width}`, then binary JPEG frames | per frame `{frame, enc_ms, bytes}` |

Notes
- Endpoints 5 and 6 are open (no token). All others require the token except WebSockets, which take it as a query param.
- Endpoints 12 and 13 also accept `job_id` (a saved studio job) as an input source.
- `/studio/encrypt` does not accept `job_id`; only `/lab/*` and `/attacks/run` do.

---

## 2. Features and screens that exist today

Source: `frontend/src/pages/*.jsx`, README, `docs/`.

**Account**
- F1 Register and sign in (demo account pre-filled). Screen: Login `/login`. Uses endpoints 2, 3.
- F2 Session check and sign out (topbar shows name). Uses 4. Expired token returns to sign-in.

**Image studio** `/studio`
- F3 Pick a sample (VisDrone / SIPI) or upload an image. Uses 5, 6, 8.
- F4 Generate a key or enter one. Uses 7 (and 8 with `key`).
- F5 Encrypt and show: plain, cipher, coefficient map, Haar sub-bands, histograms. Uses 8.
- F6 Decrypt the last result and show "Checksum matches". Uses 9 (`job_id`).
- F7 Try a key with 1 bit flipped and show decryption failing. Uses 9.
- F8 Download the cipher PNG. Uses 11.
- F9 Decrypt an uploaded cipher file with its nonce. Uses 9 (`file`+`nonce`).
- F10 Recent encryptions list. Uses 10.

**Security lab** `/lab`
- F11 Run security analysis on a sample, upload or saved job: entropy, chi-square, correlation (scatter), NPCR, UACI, PSNR/MSE/SSIM, key sensitivity, key space. Uses 12.
- F12 Run attack tests (noise and cropping on the cipher) and attach to a report. Uses 13 with `report_id`.
- F13 Saved reports list. Uses 14.
- F14 Open a saved report. Uses 15.
- F15 Export a report as HTML or JSON. Uses 16.

**Live UAV link** `/live`
- F16 Sequence choice and sender start / stop, with FPS and width. Uses 19, 20, 21, 22.
- F17 Webcam sender (camera WebSocket). Uses 25.
- F18 Ground station: enter key, connect, show decrypted frames, FPS, latency, throughput. Uses 24.
- F19 "Flip 1 bit" on ground key and reconnect shows noise. Uses 24.

**Benchmark** `/benchmark`
- F20 Run benchmark (size, image count, repeats) against AES-256-CTR and ChaCha20. Uses 17.
- F21 Past runs list. Uses 18.

**Landing and shell**
- F22 Landing page describing the product (`/`), no API call.
- F23 Topbar nav (Studio, Lab, Live, Benchmark), user name, sign out, dark-mode toggle (new).

Every existing feature (F1-F23) is in section 4 below.

---

## 3. Screen map (what gets built)

Routes stay the same as today so bookmarks and the README keep working.

| Route | Screen (kit components) | Features | Endpoints |
|---|---|---|---|
| `/` | Landing (kit landing + motion + three.js grid background, lazy-loaded) | F22 | - |
| `/login` | Login (kit Card, Input, Tabs for sign in / register, Button) | F1 | 2, 3 |
| `/studio` | Image studio (AppShell, FileDrop, Tabs, Table for jobs, ChartFrame for histograms, Modal for key help) | F3-F10 | 5-11 |
| `/lab` | Security lab (StatCard, ChartFrame for scatter and histograms, Table, Tabs, Modal, Toast) | F11-F15 | 12-16 |
| `/live` | Live UAV link (ActivityLog terminal panel, StatCard for FPS/latency, Button, Input) | F16-F19 | 19-25 |
| `/benchmark` | Benchmark (ChartFrame bar chart, Table of runs, Stepper for run settings) | F20, F21 | 17, 18 |
| all app routes | AppShell (sidebar becomes drawer under 768px), CommandPalette, ActivityLog, theme toggle | F23 | 4 |

States on every screen: Skeleton while loading, EmptyState with an action, ErrorState naming the failure and the next step, Toast for success.

---

## 4. Feature checklist (Step 4)

Tick each one when walked in the new UI with the call reaching the API and the response rendering.

- [x] F1 Register and sign in
- [x] F2 Session check and sign out
- [x] F3 Pick a sample or upload an image
- [x] F4 Generate or enter a key
- [x] F5 Encrypt and show all previews and histograms
- [x] F6 Decrypt the last result, checksum matches
- [x] F7 Decrypt with 1 bit flipped key fails
- [x] F8 Download cipher PNG
- [x] F9 Decrypt uploaded cipher file with nonce
- [x] F10 Recent encryptions list
- [x] F11 Security analysis
- [x] F12 Attack tests attached to a report
- [x] F13 Saved reports list
- [x] F14 Open a saved report
- [x] F15 Export report as HTML and JSON
- [x] F16 Live sequence sender start and stop
- [x] F17 Webcam sender
- [x] F18 Ground station decrypts frames
- [x] F19 Flip 1 bit on ground key shows noise
- [x] F20 Run benchmark
- [x] F21 Past benchmark runs
- [x] F22 Landing page
- [x] F23 Topbar, dark mode persisted, sign out

---

## 5. Problems found in the kit and the prompt (decisions needed)

1. **The kit is not self-contained.** `components/ui/*` and `components/motion` import six modules the kit does
   not ship: `api`, `format`, `lib/activity`, `lib/auth`, `lib/reduced`, `components/reactbits/Backdrop`.
   Plan: write small adapter modules in `frontend/src/` (copies only, the kit is untouched):
   - `api.js` (already exists in this project, keep it and its token handling),
   - `lib/auth.jsx` (wraps `sc_token` / `sc_user`),
   - `lib/reduced.js` (`useReducedMotion` from `matchMedia`),
   - `lib/activity.js` (small in-memory log for ActivityLog),
   - `format.js` (clock / number formatting),
   - `Backdrop`: the three.js grid background is the Kinetic Mono character. Plan: write a small local three.js grid
     component in `components/three/` (the prompt names that folder), lazy-loaded.
2. **Tailwind version mismatch.** The kit's `index.css` uses Tailwind **v4** (`@import "tailwindcss"`, `@theme`,
   `@custom-variant`) and the kit installs `@tailwindcss/vite`. This project uses Tailwind **v3** with
   `tailwind.config.js` and `postcss.config.js`. Plan: use the v4 Vite plugin and remove the v3 config files from
   `frontend/`. Tell the user if this breaks anything.
3. **Paths in the prompt do not match the kit.** The prompt says `styles/tokens.css`, `components/charts`, and kit
   config files at the top of the folder. The kit has `index.css` at the root, `components/ui/charts.jsx`, and no
   config files. Plan: copy as-is and import `./index.css` in `main.jsx`. `components/charts` is not created unless
   needed.
4. **Git repo is the shared parent `D:/abstracts/Madhav`.** Several CSDS products share it. In this folder these
   are already staged or untracked and are NOT product changes: `MASTER_PROMPT.md`, `MASTER_PROMPT_FAST.md`,
   `.env.example` (staged), and `FRONTEND_PROMPT.md` (untracked). The prompt's `git add -A .` would sweep them into
   the product commit. Plan: commit with pathspec excludes (`:!MASTER_PROMPT*.md :!FRONTEND_PROMPT.md`), and ask the
   user what to do with the staged `.env.example` change before committing.
5. **Push needs the user.** This session has no stored git credentials. Plan: ask the user to run `! git push`
   themselves once the commit is ready.
6. `.env` holds real secrets (JWT, Gemini key). It is gitignored in this folder. It must not be committed.

---

## 6. Current state of the frontend

- `frontend/src/`: 7 JSX files (App, api, components/ui, index.css, main, 6 pages). Pages are styled with Tailwind v3
  utilities. These are replaced by the kit, not patched.
- Existing API calls are kept as-is in the new pages (same paths, same form fields), so the backend is unchanged.
- `scripts/smoke_test.py` exists and will be run in Step 4.
- Sample data (`data/sample/`) is present, so the sample and benchmark flows work without downloads.

---

## 7. Step 4 result

Checks run on the finished build:

- `npm run build` in `frontend/`: passes. Three.js is a separate lazy chunk; the main bundle is about 835 kB (276 kB gzip), which is above Vite's 500 kB warning limit and is accepted.
- `scripts/smoke_test.py` against the backend on 8210: `ALL SMOKE TESTS PASSED`.
- Browser walk (Playwright, Chrome): every screen opened and every feature in section 4 was exercised. Each call reached the API and its response rendered. Downloads worked for the cipher PNG and the HTML report.
- Console: 0 errors, 0 warnings. Network: 0 failed or 4xx/5xx requests.
- Layout: no horizontal scroll on 6 routes at 1440, 768 and 360 px, in light and dark themes.
- Keyboard: `/` opens the screen-jump palette and Escape closes it (checked in the walk). Focus rings use the kit's `:focus-visible` style; not separately tested.
- Reduced motion: implemented with the kit's rules and fallbacks; NOT tested in the browser walk.

Decisions taken while building (listed so they can be changed):

- Routes kept as they were (`/studio`, `/lab`, `/live`, `/benchmark`). The kit's `/app/...` routes were not used.
- Kit files were copied into `frontend/src/` and then adapted in the copy. The kit folder itself is unchanged.
- Tailwind v4 via `@tailwindcss/vite`; the v3 `tailwind.config.js` and `postcss.config.js` were removed.
- Theme storage key is `sc_theme`; the kit's default `ts_theme` was renamed.
- Fraud-specific kit parts (taxpayer search, pipeline status, risk colours) were removed. The command palette jumps between the four screens only.
- Landing page evaluation numbers come from the README table, not from a live call, and are labelled as such.
- Installed as the kit specifies, but `lenis` and `react-force-graph-2d` are not used by any screen; they can be removed to shrink `node_modules`.
