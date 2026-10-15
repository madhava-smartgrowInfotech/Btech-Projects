# SignBridge

Real-time, two-way communication between **Indian Sign Language** users and hearing people:
signs become text and speech, speech becomes live subtitles, all on one screen and all running
offline on an ordinary laptop CPU.

## Features

- **Live sign recognition**: webcam -> MediaPipe landmarks -> small ONNX models, with a confidence for every
  sign. Covers 50 everyday words plus fingerspelling A-Z and 1-9, with a live top-3 guess and a hand skeleton overlay.
- **Sentence formation**: a pause closes the sentence. Offline grammar rules build it ("HELLO HOW-ARE-YOU" ->
  "Hello, how are you?"); when online, Gemini polishes the wording (bounded to 5 s, falls back to the rules).
- **Speech output**: the sentence is spoken with offline text-to-speech.
- **Live subtitles**: the hearing person speaks; faster-whisper on this computer shows large live subtitles
  (English, Hindi or auto-detect).
- **Conversation mode**: both directions side by side, with a transcript you can save to History and download as .txt.
- **Offline and fast**: FPS and per-frame latency always visible, plus an online/offline indicator.
- **Practice mode**: pick a sign or letter, sign it, and get instant right/wrong feedback and a score.
- **Model performance page**: accuracy, confusion matrices, per-class F1, latency and reliability.

## Quick start (Windows)

```bat
setup.bat      :: one time: venv + packages + offline speech model + frontend packages
run.bat        :: starts backend :8205 and frontend :5205, opens http://localhost:5205
```

**Demo login:** `demo@signbridge.app` / `demo1234` (pre-filled on the sign-in page).

Needs Python 3.11+, Node.js LTS, a webcam and a microphone. Internet is needed only for setup.
Details and manual commands: [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md).

## Evaluation results

Held-out test data, measured on CPU with `python -m ml.eval` (full output in
[experiments/eval/metrics.json](experiments/eval/metrics.json); confusion matrices in `experiments/eval/`).

| Measure | Result |
|---------|--------|
| Word signs (50 classes, 184 held-out takes) | **98.4 %** accuracy, 99.5 % top-3, macro F1 98.4 % |
| Fingerspelling A-Z, 1-9 (35 classes, 2 074 images) | **99.8 %** accuracy, macro F1 99.8 % |
| Continuous signing (60 streams x 3 signs through the live segmenter) | **97.2 %** signs correct, WER 1.7 %, 95 % of sequences fully correct |
| Live-pipeline reliability (53 held-out clips re-extracted with SignBridge's own MediaPipe pipeline, 16 words) | 81.1 % (100 % on the same takes from reference landmarks) |
| Robustness: rotation / scale / jitter / dropped frames; mirrored (left-handed) signing | 97.3 %; 97.3 % |
| Sentence formation (rules vs reference sentences) | 16 / 16 exact |
| Speech-to-text (faster-whisper small, int8, CPU) | WER 3.4 %, real-time factor 0.49 |
| Latency per camera frame (landmarks + model) | **37 ms** mean, 42 ms p95 (~27 FPS possible) |
| Word model / letter model (ONNX Runtime) | 1.2 ms / 0.04 ms |
| Speech-to-text per utterance / text-to-speech per sentence | 1.5 s / 0.3 s |

The weakest words are OFFICE (F1 67 %) and BROTHER (86 %). The 81 % live-pipeline figure shows the domain
gap between the training landmarks and SignBridge's own extractor; those clips are low-resolution
(224 px) with drawn-on overlays, so a normal webcam view is usually easier.

## Documentation

| Document | Contents |
|----------|----------|
| [docs/01_OVERVIEW.md](docs/01_OVERVIEW.md) | Problem, users, features, screens, vocabulary |
| [docs/02_HOW_IT_WORKS.md](docs/02_HOW_IT_WORKS.md) | Architecture, models, segmentation, sentence rules, speech, evaluation, datasets and licences |
| [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md) | Setup, running, demo walkthrough, checks, retraining, troubleshooting |
| [docs/PLAN.md](docs/PLAN.md) | Build plan: endpoints, tables, screens |

## Tech stack

React + Vite + Tailwind + three.js / framer-motion / GSAP (JavaScript, design kit V5 "Kinetic Mono") · FastAPI + SQLAlchemy + SQLite · PyJWT + bcrypt · MediaPipe Holistic / Hands ·
PyTorch -> ONNX Runtime · faster-whisper · pyttsx3 · Gemini (optional).

## Project layout

```
backend/app/     FastAPI app: routes/ (auth, recognize, speech, conversations, info), services/ (landmarks, recognizer, sentence, tts, stt)
frontend/src/    pages/ (Landing, Auth, Conversation, Practice, History, Performance), hooks/, lib/, components/ (ui, motion, reactbits)
ml/              vocab, features, models, prepare_data, train, eval
scripts/         download_data.py, smoke_test.py, make_kaggle_notebook.py
notebooks/       Kaggle GPU training notebook (optional; CPU training takes ~4 minutes)
data/            committed landmark datasets + samples (raw downloads in data/raw/, git-ignored)
models/          word_model.onnx, letter_model.onnx, labels.json (+ .pt weights)
experiments/     training curves, train_metrics.json, eval/ (metrics.json, confusion matrices)
```

## Checks

```bat
venv\Scripts\python scripts\smoke_test.py    :: drives the running API end to end (all checks pass)
cd frontend && npm run build                  :: production build
```

## Data and licences

INCLUDE ISL landmarks (MIT), ISL words with landmarks (CC BY-SA 4.0) and the ISL A-Z / 1-9 image set
(CC BY-SA 4.0), all from Kaggle. See [docs/02_HOW_IT_WORKS.md](docs/02_HOW_IT_WORKS.md#data) for what is committed.
