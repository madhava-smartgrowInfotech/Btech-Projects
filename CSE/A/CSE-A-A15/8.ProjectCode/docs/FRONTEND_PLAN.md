# CipherVeil - frontend plan (V5 Kinetic Mono)

Step 1 inventory. Ports: backend **8315**, frontend **5315** (confirmed in `.env`). Backend starts and answers `GET /api/health`.

## 1. Backend endpoints

All under `/api`. Every route except `auth/*` and `health` needs `Authorization: Bearer <jwt>`.

| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/health` | - | `{status}` |
| POST | `/auth/register` | JSON `{username, password}` | `{token, username}` |
| POST | `/auth/login` | JSON `{username, password}` | `{token, username}` |
| GET | `/auth/me` | - | `{id, username}` |
| GET | `/keys` | - | `[{id, name, bits, fingerprint, has_private, public_pem, created_at}]` |
| POST | `/keys/generate` | JSON `{name, bits}` (2048/3072/4096) | key object |
| POST | `/keys/import` | JSON `{name, pem}` (private or public PEM) | key object |
| GET | `/keys/{id}/export?part=public\|private` | - | PEM text |
| DELETE | `/keys/{id}` | - | `{ok}` |
| GET | `/samples/covers` | - | `[{name, width, height, size_bytes, capacity_bytes}]` |
| GET | `/samples/payloads` | - | `[{name, size_bytes}]` |
| GET | `/samples/covers/{name}` | - | PNG file |
| GET | `/samples/payloads/{name}` | - | file |
| POST | `/send` | multipart: `key_id`, `payload` or `payload_sample`, `cover` or `cover_sample` | `{op_id, key_id, key_name, fingerprint, key_bits, filename, payload_bytes, cover, input_sha256, bundle_bytes, capacity{width,height,pixels,max_bundle_bytes,max_file_bytes,bundle_bytes,used_pct,payload_bits_per_pixel}, timings_ms{encrypt,embed,png_encode,metrics}, quality{psnr_db,ssim,mse,max_abs_change,changed_pct,values_changed,values_total}}` |
| POST | `/receive` | multipart: `key_id`, `stego` or `from_op` | `{op_id, key_id, key_name, fingerprint, source, filename, output_bytes, bundle_bytes, embedded_sha256, output_sha256, hash_match, gcm_verified, timings_ms{extract,decrypt}}` |
| GET | `/ops/{op_id}/cover\|stego` | - | PNG (send ops only) |
| GET | `/ops/{op_id}/restored` | - | original file bytes (receive ops only) |
| GET | `/analysis/{op_id}` | - | `{op_id, ...send details}` (quality, capacity, timings) |
| GET | `/analysis/{op_id}/histogram.png` | - | PNG |
| GET | `/analysis/{op_id}/bitplanes.png` | - | PNG |
| POST | `/robustness/{op_id}` | - | `{op_id, results[{attack,label,size,status,detail,bit_error_rate,why,elapsed_ms}], survived[], lost[]}` |
| GET | `/robustness/{op_id}` | - | last report or `null` |
| GET | `/benchmark/capacity` | - | `[{cover,width,height,pixels,max_bundle_bytes,max_bundle_kib,max_bits_per_pixel}]` |
| POST | `/benchmark/run` | - | `{key_bits, repeats, rows[{cover,payload_bytes,fits,pixels,used_pct,bits_per_pixel,psnr_db,ssim,changed_pct,encrypt_ms,embed_ms,extract_ms,decrypt_ms,round_trip_ok}]}` |
| GET | `/log?op=&limit=` | query | `[{id, op, ok, created_at, details}]` |

Backend changes needed for the V5 UI: **none so far.** Any extra data the UI wants that no endpoint returns will be listed here before it is added.

## 2. Features and screens that exist today

| # | Feature | Current screen / route | Endpoints used |
|---|---|---|---|
| F1 | Landing page | `/` (`Landing.jsx`) | - |
| F2 | Sign in and create account | `/login` (`Login.jsx`) | `auth/login`, `auth/register` |
| F3 | Sign out, session guard | `Layout.jsx` (nav + sign out) | `auth/me` not used; token in localStorage |
| F4 | Generate keypair (2048/3072/4096) | `/keys` (`Keys.jsx`) | `keys/generate` |
| F5 | Import key (private or public PEM) | `/keys` | `keys/import` |
| F6 | List keys, copy/download public, download private, delete | `/keys` | `keys`, `keys/{id}/export`, `DELETE keys/{id}` |
| F7 | Encrypt and hide a file (sample or upload, sample or upload cover) | `/send` (`Send.jsx`, `SendPicker`) | `samples/covers`, `samples/payloads`, `keys`, `send`, `ops/{id}/stego` |
| F8 | Download stego PNG | `/send` result | `ops/{id}/stego` |
| F9 | Receive: extract, unwrap, verify, restore | `/receive` (`Receive.jsx`) | `keys`, `log?op=send`, `receive`, `ops/{id}/restored` |
| F10 | Receive a message sent from this app (`?op=`) | `/receive?op=` | `log?op=send`, `receive` (`from_op`) |
| F11 | Cover and stego side by side, PSNR/SSIM/MSE, capacity, timings | `/analysis?op=` (`Analysis.jsx`) | `analysis/{op}`, `ops/{op}/cover`, `ops/{op}/stego`, `analysis/{op}/histogram.png`, `analysis/{op}/bitplanes.png` |
| F12 | Pick a sent message | `SendPicker.jsx` (on Analysis, Receive) | `log?op=send` |
| F13 | Robustness attacks on a stego image (JPEG, noise, resize, crop) | `/robustness` (`Robustness.jsx`) | `robustness/{op}` GET and POST, `log?op=send` |
| F14 | Capacity per cover | `/robustness` | `benchmark/capacity` |
| F15 | Speed and quality benchmark | `/robustness` | `benchmark/run` |
| F16 | Operation log, filter by op, expandable details | `/log` (`Log.jsx`) | `log` |
| F17 | Error messages from API | everywhere | `errText` in `api.js` |
| F18 | 401 redirects to login | `api.js` interceptor | - |

Existing UI pieces with no V5 equivalent yet: `components/ui.jsx` (PageHead, Stat, Timings, ErrorBox, HashLine, AuthImage, Badge, Spinner), `index.css` (btn-*, input, label, card classes), Tailwind v3 config.

## 3. Screen map for the V5 build

| Screen | Route | Kit pieces | Keeps |
|---|---|---|---|
| Landing | `/` | `Logo`, `Typewriter`, `Marquee`, `Reveal`, `FadeIn`, `Stagger`, `MagneticButton`, `CountUp`, `Backdrop` (three.js grid, lazy) | F1; "Get started" / "Open app" by session state |
| Login | `/login` | `Card`, `Input`, `Label`, `Button`, `Tabs` (sign in / create), `ErrorState` | F2 |
| App shell | all `/app` routes | `AppShell`, `Sidebar`, `CommandPalette`, `ActivityLog`, `ThemeProvider` (topbar toggle, persisted), `Drawer` on mobile | F3, F18 |
| Keys | `/keys` | `Card`, `Select`, `Input`, `Table` (wide) or cards on mobile, `Modal` (import PEM, confirm delete), `Toast`, `EmptyState`, `Skeleton` | F4, F5, F6 |
| Send | `/send` | `Stepper` (key, file, cover, run), `FileDrop`, `Select`, `Card`, `StatCard`, `Button`, `Toast`, `Skeleton`, `ErrorState` | F7, F8 |
| Receive | `/receive` | `Stepper`, `FileDrop`, `Select`, `KeyValueList`, `StatCard`, `Button`, `EmptyState` (no sent message yet) | F9, F10, F12 |
| Analysis | `/analysis` | `Tabs` (metrics, images, histograms, bit planes), `StatCard`, `ChartFrame`, `ProgressBar`, `Skeleton` | F11, F12 |
| Robustness and benchmark | `/robustness` | `Table`, `ScoreBar`, `StatusDot`, `Badge`/`Severity`, `ChartFrame`, `Button`, `ProgressBar`, `Skeleton` | F13, F14, F15 |
| Log | `/log` | `Table`, `Select` (op filter), `KeyValueList` (expanded row), `EmptyState`, `Skeleton` | F16 |

Every screen gets: skeleton while loading, a real empty state with an action, an error state that names the failure and the next step, and a visible success toast or banner.

## 4. Kit gaps found in Step 1 (fixed in the copy during Step 2)

The kit at `D:\abstracts\Frontend_Kits\V5` is **not self-contained**. Its files import modules that are not in the kit, so it will not compile as delivered:

| Kit file imports | Missing module | What it must provide (from the kit's own usage) |
|---|---|---|
| `components/ui/AppShell.jsx`, `CommandPalette.jsx` | `src/api.js` | default axios instance; `errorMessage(err)` |
| `components/ui/display.jsx`, `CommandPalette.jsx`, `ActivityLog.jsx` | `src/format.js` | `clock`, `riskVar`, `PATTERN_LABELS`, `PATTERN_TONE` |
| `ActivityLog.jsx`, `AppShell.jsx` | `src/lib/activity.js` | `useActivity`, `clearActivity`, `logEvent` |
| `AppShell.jsx` | `src/lib/auth.js` | `useAuth` (adapter over this project's `getToken`/`getUser`) |
| `motion/index.jsx`, `charts.jsx`, `feedback.jsx`, `nav.jsx`, `Typewriter.jsx`, `ActivityLog.jsx` | `src/lib/reduced.js` | `useReducedMotion`, `useSize` |
| `AppShell.jsx` | `src/components/reactbits/Backdrop.jsx` | three.js grid background. Not in the kit at all; `three` is never imported in the kit |

Other mismatches with the prompt:

- **Tailwind version.** The kit's `index.css` uses Tailwind **v4** (`@import "tailwindcss"`, `@theme inline`), and the kit expects `@tailwindcss/vite`. This project is on Tailwind **v3.4** with `tailwind.config.js` and `postcss.config.js`. Plan: move to v4 and delete the v3 config files.
- **Step 2.2 says copy config files from the kit top.** The kit has none: only `MANIFEST.md` and `src/`.
- **Step 2.5 names `styles/tokens.css`.** The kit has `src/index.css` (tokens inside). Plan: import `./index.css` from `main.jsx`.
- **Step 3 names `Table`, `Card`, `Toast`, etc.** These exist. `FileDrop`, `Stepper`, `Drawer` and `Modal` are also in the kit.
- **Kit domain.** `riskVar`, `PATTERN_LABELS` and `Severity`/`RiskBadge` come from another product. Adapt the copies: map risk/pattern to this product's concepts (for example Badge/Severity for attack survival), not the originals.

## 5. Defaults I plan to use (unless you say otherwise)

- Keep the existing `api.js` (axios, Bearer header, 401 redirect, `errText`) as the only HTTP layer. The kit's `api` import is served by a thin adapter that re-exports it.
- Token and username stay in `localStorage` (`cv_token`, `cv_user`); they are the existing contract.
- Routes unchanged, so bookmarks and `?op=` links keep working.
- Landing copy uses only facts from `README.md` (AES-256-GCM, RSA-OAEP, LSB, measured PSNR/SSIM). No invented numbers.
- Three.js backdrop is a small local component, lazy-loaded, disabled under `prefers-reduced-motion`.
- Copy of the kit lives in `frontend/src/` only. Nothing imports from outside this folder.

## 6. Risks to settle before Step 4

- **`.env` is tracked by git and holds a live `GEMINI_API_KEY`.** The git repo root is `D:/abstracts/Madhav`, and `.env` is not in this folder's `.gitignore`. `git add -A .` in Step 4 would publish that key. Proposed fix: `git rm --cached .env`, add `.env` to `.gitignore`, and rotate the key. Needs your go-ahead.
- **Push.** Step 4 ends with `git push`. This environment has no stored git credentials, so the push will likely need you to run it.
- **Running backend.** I started uvicorn on 8315 for this check (log: `data/scratch_backend.log`, git-ignored). Stop it before `run.bat` or the port will clash.

## 7. Feature tick-off (verified in the built app)

Checked in a headless Chrome walk (Playwright, channel `chrome`) against the running backend on 8315 and the Vite app on 5315:

- [x] F1 - Landing page (measured figures from README, animated counters, three.js backdrop present)
- [x] F2 - Sign in and create account (register creates a new account and lands on Keys)
- [x] F3 - Sign out, route guard (signed-out `/keys` redirects to `/login`)
- [x] F4 - Generate keypair (2048 tested; success toast and new row)
- [x] F5 - Import a public PEM (success toast, row shows "public only")
- [x] F6 - List keys, copy, download public and private, delete via confirm dialog
- [x] F7 - Encrypt and hide with a sample file and with an uploaded file, sample cover; capacity meter
- [x] F8 - Download stego PNG
- [x] F9 - Receive from a sent message and from an uploaded PNG: restored byte for byte, tag verified
- [x] F10 - Receive opened from a send result (`?op=`)
- [x] F11 - Analysis: PSNR/SSIM/MSE, cover and stego images, histograms, bit planes, timing chart
- [x] F12 - Sent-message picker (Analysis, Robustness, Receive), synced to `?op=`
- [x] F13 - Robustness attacks: result table, LSB error rate chart, survive/lost summary, JPEG warning
- [x] F14 - Capacity per cover table
- [x] F15 - Speed and quality benchmark (table incl. "does not fit" rows)
- [x] F16 - Operation log: filter, paging, expandable details
- [x] F17 - Errors say what failed and what to do (receive on a PNG without payload shows the reason and a hint)
- [x] F18 - Invalid session: API 401 clears the session and redirects to `/login`

Other checks that passed:

- `npm run build` passes (no errors).
- `scripts/smoke_test.py` passes (all checks, including byte-exact round trip and wrong-key rejection).
- Console and network clean on every desktop flow (no errors, no 4xx/5xx, no 404 assets).
- No horizontal overflow at 360, 768 and 1440 px, in light and dark.
- Dark mode toggle in the topbar, persisted in `localStorage`; follows the OS until the user picks.
- `prefers-reduced-motion` walk completes with no errors.
- Keyboard: `/` search, `g` + letter jumps, `?` help, Escape closes overlays, Tab trapped in dialogs.
- 360 px: sidebar becomes a drawer; tables scroll horizontally.

**Status: Frontend rebuilt with kit V5. All features ticked above.**
