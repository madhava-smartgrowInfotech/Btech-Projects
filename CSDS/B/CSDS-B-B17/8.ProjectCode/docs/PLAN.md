# CallSense - build plan

**Architecture.** React + Vite (5217, `/api` proxy) -> FastAPI (8217) -> SQLite. A single background worker
thread runs the call pipeline: decode (PyAV) -> faster-whisper `small` (CPU int8, VAD) per stereo channel
or mono + turn split -> per-segment text sentiment (scikit-learn) + voice emotion (Hugging Face
`superb/wav2vec2-base-superb-er`) -> fused emotion timeline + escalation flags -> intent/topic (scikit-learn,
Bitext) + TF-IDF keywords -> Gemini summary (reason, resolution, action items) -> rule-based agent scorecard.
Sample calls are synthesised offline with pyttsx3 (SAPI voices, agent left / customer right channel).

**Endpoints.** `POST /api/auth/login`, `GET /api/auth/me`, `GET /api/agents`,
`GET/POST /api/calls` (list + search `?q=`, bulk upload), `GET/DELETE /api/calls/{id}`, `GET /api/calls/{id}/audio`,
`POST /api/calls/{id}/reprocess`, `POST /api/calls/{id}/summary`, `GET /api/studio/scripts`,
`POST /api/studio/generate`, `POST /api/studio/import-samples`, `GET /api/analytics`, `GET /api/metrics`, `GET /api/health`.

**Tables.** `users` (supervisor | agent), `calls` (audio, agent, status, segments JSON, intent, topic, keywords,
emotion timeline, flags, summary, scorecard, score, is_sample, reference script for evaluation).

**Screens.** Landing, Login, Calls (list, search, upload, microphone), Call detail (player, transcript,
emotion timeline, summary, scorecard), Sample call studio, Analytics, Model performance.

**Data.** Bitext customer-support (intent + topic training, committed), Call Center Transcripts (committed,
sentiment/keyword corpus), RAVDESS + CREMA-D (small committed sample for voice-emotion evaluation +
`scripts/download_data.py`), generated sample calls from committed scripts (seeded).

**Models.** `ml/train.py` -> `models/intent.joblib`, `models/sentiment.joblib`, `experiments/metrics.json`.
`ml/eval.py` -> `experiments/eval/metrics.json` (intent acc + macro-F1, sentiment F1, WER, voice emotion).
