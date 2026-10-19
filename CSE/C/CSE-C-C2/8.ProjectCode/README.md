# StoryVox

**StoryVox** is a local-first multilingual AI storytelling application. Enter a story idea, pick a language, style and length — StoryVox writes an original story with a pretrained language model and narrates it with a pretrained multilingual speech model. Listen in the browser, download the narration, revisit history, and review genuinely measured pipeline metrics.

## Main features

- Story creator: prompt box, dynamic language selector, style and length selectors, optional auto-narration
- Structured story output: title, body, language, style, word count, reading/listening time, generation time
- Natural speech narration: multilingual TTS with audio player and WAV download, regenerate-narration action
- History: view, play, download and delete past stories (deletion removes DB rows and audio files)
- Evaluation dashboard: real computed WER/CER, topic similarity, ROUGE-L, latency and RTF — never pre-filled
- Lazy model loading, CPU support with CUDA auto-detection, clean `TTSProvider` adapter interface
- SQLite + local audio storage with a privacy note in the UI

## Supported languages

Exposed live at `GET /api/languages` and stored per story as code + display name:

English (en), Hindi (hi), Spanish (es), French (fr), German (de), Italian (it), Portuguese (pt), Russian (ru), Arabic (ar), Turkish (tr), Dutch (nl), Polish (pl), Chinese Mandarin (zh), Japanese (ja), Korean (ko).

Each language maps to a matching `facebook/mms-tts-*` checkpoint. If a checkpoint cannot load in the local environment, StoryVox uses an offline OS speech fallback and records the actual model id — it never serves silent or placeholder audio as speech.

## Architecture

Single FastAPI service bound to `127.0.0.1`:

```
Browser (React + Vite, kit V2 Neo Brutal Grid) -> FastAPI REST (/api/*) -> services/
  story_generator.py (Qwen3 instruction model, prompt-conditioned)
  tts_service.py (TTSProvider: MMS checkpoint per language + offline fallback)
  asr_service.py (Whisper transcription for evaluation)
  evaluation_service.py (WER/CER/similarity/latency/RTF)
-> SQLite (stories, audio_outputs, evaluations) + WAV files in data/audio/
```

## Models actually used

- Story generation: `Qwen/Qwen3-0.6B` by default (override with `STORY_MODEL`, e.g. `Qwen/Qwen3-1.7B` on stronger machines). Offline fallback composer `storyvox-local-fallback-v1` is prompt-conditioned and labeled as such.
- Speech synthesis: `facebook/mms-tts-*` per-language checkpoints (VITS). Fallback: offline OS speech (`system-tts-offline-fallback`). The concrete `tts_model` is stored on every audio row.
- Speech recognition (evaluation only): `openai/whisper-small`.
- Similarity (evaluation): `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` when installed, otherwise a locally computed TF-IDF cosine proxy (the method name is reported alongside the score).

## Dataset / evaluation strategy

- Preferred: small cached Hugging Face subsets (see `scripts/download_data.py`, default `google/fleurs` slice). Downloads are cached and never repeated silently.
- If the network or dataset access fails, a small **synthetic** set with `provenance: synthetic` is written so the pipeline stays testable. Synthetic data is labeled and never presented as benchmark results.
- Story prompts cover several languages/styles; intelligibility = transcribe narration with Whisper and compute WER/CER vs. the story text; topic fit = prompt-story similarity; performance = generation/TTS latency and RTF = synthesis_time / audio_duration.
- Results persist as JSON + CSV under `data/evaluations/` and render in the Evaluation tab.

## Installation / running / evaluation

See **HOW_TO_RUN.md** (Methods A/B/C) and:

```bash
python scripts/download_data.py --limit 20
python scripts/evaluate.py --samples 5
pytest -q
```

Web app: `http://localhost:5402` (API on `http://localhost:8402`, docs at `http://localhost:8402/docs`).

## Project structure

```
StoryVox/
  app/main.py, app/config.py, app/database.py, app/models/, app/schemas.py
  app/api/routes.py
  app/services/story_generator.py, tts_service.py, asr_service.py, evaluation_service.py
  app/utils/ (+ audio.py, metrics.py)
  frontend/ (Vite + React: src/pages, src/components/ui, src/components/motion, src/styles)
  legacy_frontend/ (the previous plain HTML/JS interface, kept for reference)
  scripts/download_data.py, evaluate.py, build_docs.py
  tests/test_api.py
  scripts/smoke_test.py, capture_screens.py
  docs/FRONTEND_PLAN.md, docs/screenshots/
  data/audio|datasets|evaluations/
  requirements.txt, Dockerfile, docker-compose.yml, run.bat, run-docker.bat
  README.md, HOW_TO_RUN.md, StoryVox_Product_Documentation.pdf
```

## Limitations

- First run downloads model weights (internet + disk required); CPU inference is slower.
- Narration quality varies by language/checkpoint; offline fallback voices are more robotic.
- Very long stories are capped by token budgets to keep generation practical.
- Evaluation with TTS+ASR is slow on CPU; use `--samples 2` for a quick smoke run.

## Privacy

Stories, audio and evaluation files stay on the local machine by default. No analytics or external uploads. Uploaded/reference audio is not enabled in this build; if added later it will be size-validated and stored locally.
