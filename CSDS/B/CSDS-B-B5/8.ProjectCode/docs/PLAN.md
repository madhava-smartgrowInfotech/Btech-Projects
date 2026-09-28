# SignBridge - Build Plan

**Architecture:** React/Vite UI (5205) -> FastAPI (8205) -> MediaPipe Holistic landmarks -> ONNX models (CPU)
-> sentence builder (rules offline, Gemini polish online) -> pyttsx3 WAV. Speech -> faster-whisper (small, int8, CPU) -> subtitles.

**Data:**
- INCLUDE holistic landmarks (Kaggle, MIT): 50-word everyday subset (greetings, pronouns, family, places, feelings, time) -> `data/words_landmarks.npz`
- ISL words with landmarks (Kaggle, CC BY-SA 4.0): videos re-extracted with our own live pipeline -> extra training + cross-extractor test
- ISL A-Z / 1-9 images (Kaggle, CC BY-SA 4.0): hand landmarks -> `data/letters_landmarks.csv` + image sample

**Models:** word model = small Transformer encoder on 32-frame landmark sequences; letter model = MLP on
two-hand landmarks. Both PyTorch -> ONNX. Small enough to train on CPU in minutes (Kaggle notebook also provided).

**Tables:** users, conversations, messages (side = signer | hearing, text, gloss, confidence, latency_ms).

**Endpoints:**
- `POST /api/auth/register|login`, `GET /api/auth/me`
- `POST /api/recognize/frame` (JPEG frame -> landmarks, sign events, fps/latency), `POST /api/recognize/reset`
- `POST /api/sentence` (glosses -> sentence, rules/Gemini), `POST /api/tts` (text -> WAV)
- `POST /api/speech/transcribe` (16 kHz PCM -> text)
- `GET/POST /api/conversations`, `POST /api/conversations/{id}/messages`, `GET /api/conversations/{id}`
- `GET /api/vocab`, `GET /api/metrics`, `GET /api/health` (online/offline status)

**Screens:** Landing, Login/Register, Conversation (camera + skeleton, gloss strip, sentence, live subtitles,
transcript + save), Practice (pick a sign/letter, get live feedback), History, Model performance.

**Evaluation:** `ml/eval.py` -> accuracy, per-class F1, confusion matrices, inference latency (p50/p95),
cross-extractor reliability -> `experiments/eval/metrics.json`.
