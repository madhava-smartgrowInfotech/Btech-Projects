# CallSense

**Analyses every customer call automatically** - transcripts, intent, sentiment and voice emotion, summaries and
agent scorecards - for contact-centre supervisors, QA teams, agents and CX managers.

## Features
- **Call ingestion** - upload one or many recordings, or record from the microphone.
- **Transcription** - faster-whisper (`small`, CPU) with timestamps; agent / customer separation by stereo channel or a turn split.
- **Intent & topics** - 27 support intents / 11 topics (trained on Bitext) plus keyword extraction.
- **Sentiment & emotion** - text sentiment per turn + pretrained wav2vec2 voice emotion, drawn as an emotion timeline with escalation flags.
- **Call summary** - Gemini writes the reason for the call, the resolution and the action items.
- **Agent scorecard** - greeting, empathy, talk/listen ratio, silence, interruptions, resolution and sentiment change -> score /100 with evidence.
- **Sample call studio** - scripts rendered into realistic two-voice stereo calls with offline voices, clearly labelled *Sample*.
- **Analytics** - call volumes, top intents, sentiment trend, agent leaderboard, escalations and transcript search.
- **Evaluation** - intent accuracy / macro-F1, sentiment F1, word error rate, speaker attribution, voice-emotion accuracy.

## Quick start (Windows)
```bat
setup.bat      :: venv + Python packages + npm install + models + speech model download (first run only)
run.bat        :: API on :8217, web app on :5217, opens the browser
```
Put your Gemini key in `.env` (`GEMINI_API_KEY`); `setup.bat` creates `.env` from `.env.example` if it is missing.
Full instructions: [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md).

## Demo login
| Role | Email | Password |
|------|-------|----------|
| Supervisor | supervisor@callsense.local | CallSense@123 |
| Agent | agent@callsense.local (also sam@ / jordan@callsense.local) | CallSense@123 |

Demo: on **Calls** press *Load sample calls*; in **Sample studio** generate *Refund request - returned headphones*.
The call is split by speaker, classified as `get_refund`, its emotion timeline goes frustrated/angry -> relieved,
and the Gemini summary and scorecard (97-98/100 for this well-handled call) appear with evidence.

## Evaluation results
From `ml/train.py` (`experiments/metrics.json`) and `ml/eval.py` (`experiments/eval/metrics.json`).

| Objective | Test set | Result |
|-----------|----------|--------|
| Intent classification | Bitext held-out (5,375 utterances, 27 intents) | accuracy **99.8 %**, macro-F1 **0.998** |
| Intent, end to end | 10 sample calls (audio -> transcript -> intent) | accuracy **80 %** (8/10; misses: get_invoice -> check_invoice, payment_issue -> contact_customer_service) |
| Sentiment | Airline customer-service messages held-out (2,928) | accuracy 80.1 %, macro-F1 **0.750** |
| Sentiment | Sample-call script lines (86) | accuracy 73.3 %, macro-F1 **0.717** |
| Sentiment, end to end | Transcribed customer turns of the sample calls (38) | accuracy 84.2 %, macro-F1 **0.841** |
| Sentiment | 20 real call-centre transcripts (call level) | accuracy 60 %, macro-F1 **0.618** (same on reference and ASR text) |
| Transcription | 20 real call-centre recordings | WER **4.7 %** |
| Transcription | 10 sample calls | WER **0.45 %** |
| Speaker separation | 10 stereo sample calls (86 lines) | speaker attribution **100 %** |
| Voice emotion (pretrained) | RAVDESS sample (40 clips, 4 emotions) | accuracy 47.5 %, macro-F1 0.421 |
| Voice emotion (pretrained) | CREMA-D sample (40 clips, 4 emotions) | accuracy 42.5 %, macro-F1 0.348 |

Notes: the sample calls use synthetic voices, so their WER is an optimistic bound - the real-recording WER is the
representative figure. The pretrained voice-emotion model transfers poorly to acted RAVDESS/CREMA-D speech, which is
why the emotion timeline weights text sentiment 0.75 and voice 0.25.

## Tech stack
React + Vite + Tailwind (JavaScript) - FastAPI, SQLAlchemy 2, SQLite, PyJWT + bcrypt - faster-whisper, PyTorch (CPU),
transformers (`superb/wav2vec2-base-superb-er`), scikit-learn, librosa - Gemini (`google-genai`) - pyttsx3.

## Project layout
```
backend/app/        main.py, db.py, auth.py, config.py, routes/ (calls, studio, misc), services/ (pipeline, speech, nlp, analysis, summary, studio)
frontend/src/       pages/ (Landing, Login, Calls, CallDetail, Studio, Analytics, Performance), components/, api.js
ml/                 train.py, eval.py
scripts/            smoke_test.py, download_data.py, generate_sample_calls.py, tts_worker.py
data/               bitext/, call_center/, airline/, sample/ (scripts, calls, emotion clips)
models/ experiments/  trained models, training and evaluation metrics
docs/               01_OVERVIEW.md, 02_HOW_IT_WORKS.md, 03_HOW_TO_RUN.md
```

## Documentation
- [docs/01_OVERVIEW.md](docs/01_OVERVIEW.md) - problem, users, features, screens
- [docs/02_HOW_IT_WORKS.md](docs/02_HOW_IT_WORKS.md) - pipeline, scorecard rules, models, evaluation, data sources and licences, API
- [docs/03_HOW_TO_RUN.md](docs/03_HOW_TO_RUN.md) - setup, run, demo walk-through, troubleshooting
- [docs/PLAN.md](docs/PLAN.md) - build plan
