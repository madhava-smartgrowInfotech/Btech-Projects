# StoryVox - Frontend Plan (Kit V2 · Neo Brutal Grid)

Ports: backend **8402**, frontend **5402**. Frontend: Vite + React (JavaScript), kit copied into `frontend/src/`.

## 1. Backend inventory (FastAPI, prefix `/api`)

| # | Method | Path | Request | Response |
|---|--------|------|---------|----------|
| 1 | GET | `/api/health` | - | `{status, app, cuda, time}` |
| 2 | GET | `/api/languages` | - | `[{code, name, tts_checkpoint}]` (15 languages) |
| 3 | GET | `/api/meta` | - | `{app, styles[8], lengths[3], story_model, asr_model}` |
| 4 | POST | `/api/stories/generate` | `{prompt, language_code, style, length_option, synthesize}` | `Story` (below); 422 with `detail` on bad input, 500 on model failure |
| 5 | POST | `/api/stories/{id}/synthesize` | - | `Audio`; 404 / 422 / 500 with `detail` |
| 6 | GET | `/api/stories?limit=1..200` | - | `[{id, title, language_code, language_name, style, word_count, created_at, has_audio, audio_id}]` |
| 7 | GET | `/api/stories/{id}` | - | `Story`; 404 |
| 8 | DELETE | `/api/stories/{id}` | - | `{status:"deleted", id}`; removes DB rows and WAV files |
| 9 | GET | `/api/audio/{audio_id}` | - | `audio/wav` stream (also the download link); 404 / 400 |
| 10 | GET | `/api/evaluations` | - | `[{id, evaluation_type, language_code, sample_count, metrics_json, created_at}]` newest first (falls back to JSON files on disk) |
| 11 | POST | `/api/evaluations/run` | `{samples 1..30, language_code?, skip_tts?, skip_story?}` | `{id, metrics}` (slow on CPU) |

`Story` = `{id, prompt, title, story_text, language_code, language_name, style, length_option, word_count, reading_time_minutes, listening_time_minutes, generation_time_seconds, created_at, audio: Audio|null}`
`Audio` = `{id, story_id, file_path:"/api/audio/{id}", duration_seconds, sample_rate, tts_model, synthesis_time_seconds, rtf, created_at}`
`metrics` = `{evaluation_type, sample_count, languages[], created_at, averages{prompt_story_similarity, rougeL_prompt_vs_story, wer, cer, story_time_s, tts_time_s, rtf}, metric_notes{...}, asr_model, story_model, samples[...]}`

Not exposed by the API: `MAX_PROMPT_CHARS` (2000, hard-coded in the UI as the textarea limit).

## 2. Existing features (from README, HOW_TO_RUN and the old vanilla UI in `frontend/`)

1. Story creator: prompt box (max 2000 chars), language selector (dynamic), style selector, length selector, auto-narration checkbox
2. Generate story with progress/status and validation errors
3. Structured story result: title, body, language, style, length, word count, listening time, generation time
4. Audio player for narration + WAV download
5. Regenerate narration (also the way to get audio when it was skipped or failed)
6. History: list stories; view, play inline, download audio, delete (with confirmation; removes audio files)
7. Evaluation dashboard: latest saved evaluation, run a new one with N samples, metric cards (samples, WER, CER, topic similarity, story latency, TTS latency, RTF), per-sample table, provenance (time, story model, ASR model)
8. Honest empty state when evaluation was never run ("Not run yet", nothing pre-filled)
9. Privacy note (data stays on this machine)
10. Toast feedback on finish / delete

## 3. Screen map

| Route | Screen | Features covered | Kit pieces |
|-------|--------|------------------|------------|
| `/` | **Landing** (public shell) | pitch, 15 live languages (from API), style list, how it works, privacy (#9), CTA to the studio | `MaskHeadline`, `Marquee`, `Reveal`, `Stagger`, `CountUp`, `MagneticButton`, `InkRule`, `Card` |
| `/studio` | **Studio** (create) | 1, 2, 3, 4, 5, 9, 10 | `Textarea`, `Select`, `Checkbox`, `Button`, `Stepper`, `ProgressBar`, `Skeleton`, `Alert`, `EmptyState`, `ErrorState`, `Toast` |
| `/stories` | **History** | 6, 10 | `Table`, `SearchField`, `Modal` (delete confirm), `EmptyState`, `ErrorState`, `Skeleton` |
| `/stories/:id` | **Story detail** | 3, 4, 5, 6 (view/play/download/delete) | `PageHeader`, `Breadcrumbs`, `KeyValueList`, `Badge`, `Tabs` |
| `/evaluation` | **Evaluation** | 7, 8 | `StatCard`, `BarBlocks` (lazy Recharts), `Table`, `Tabs`, `ProgressBar`, `Alert`, `KeyValueList` |
| `*` | 404 | - | `EmptyState` |

Shell: `AppShell` (sidebar → drawer + bottom bar under 900px) for Studio/History/Evaluation, `PublicShell` for the landing. Topbar carries the dark-mode toggle (persisted) and a live API/CUDA status pill from `/api/health`.

## 4. Kit adaptation notes (copies only; the kit folder is never edited)

- Kit `Layout.jsx` is hard-wired to another product (faculty nav, `useAuth`, "Attendance Magic" brand). Copy is re-pointed to StoryVox nav; the auth parts are removed (StoryVox has no login).
- Kit imports `lib/auth`, `lib/gsap` and `lib/storage`, which are not in the kit. They are written fresh in `frontend/src/lib/`.
- `lib/format.js` carries another product's labels; replaced with StoryVox helpers.
- Kit `Charts.jsx` only allowed whole-number Y ticks, which hid sub-1 metrics such as RTF 0.007; the copy now allows decimals.

## 5. Run / ports

- `.env`: `PORT=8402`, `FRONTEND_PORT=5402` (`.env.example` updated). Vite dev server on 5402 proxies `/api` to 8402.
- `run.bat` starts both servers from the project root.

## 6. Feature verification (ticked in Step 4)

- [x] 1 Creator form (prompt, language, style, length, auto-narration)
- [x] 2 Generate with status and validation errors
- [x] 3 Structured story result
- [x] 4 Audio player + WAV download
- [x] 5 Regenerate narration
- [x] 6 History: view / play / download / delete
- [x] 7 Evaluation: view latest, run, cards, table, provenance
- [x] 8 Evaluation honest empty state
- [x] 9 Privacy note
- [x] 10 Toast feedback

## 7. Verification log (Step 4)

- `npm run build` passes. `python scripts/smoke_test.py` passes (13 checks, through the web app on 5402). Existing `pytest` suite: 8 passed.
- Walked every screen in Chrome via Playwright: empty-idea validation, generate (French / Mystery / Medium), narration player, regenerate narration, reload restoring `?story=`, history search / sort / play / download / delete (Escape closes the dialog), story detail tabs, 404 story and 404 route, evaluation view / run / run selector / chart / samples / method tabs, theme toggle persisted across reload.
- No horizontal overflow at 360, 768 and 1440 px in light and dark on all five screens; sidebar becomes a drawer plus bottom bar under 1024px; reduced-motion renders the headline.
- Console clean. The only non-2xx response is the deliberate 404 when opening a story id that does not exist (the screen then shows "Story not found").
- Screenshots: `docs/screenshots/` (regenerate with `python scripts/capture_screens.py`).
- Environment limits on the test machine: `torch`/`transformers` were not installed (C: drive full), so stories came from the app's labelled offline fallback composer and narration from its OS-voice fallback; WER/CER stay "—" because the ASR model could not load. With the full `requirements.txt` installed (run.bat does this) the same screens show Qwen / MMS output.
