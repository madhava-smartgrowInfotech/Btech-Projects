# SignBridge - How it works

## Architecture

```
Browser (React, port 5205)                         Backend (FastAPI, port 8205, CPU only)
---------------------------------                  ----------------------------------------------------------
webcam 480px JPEG, up to 15 fps  ---- /api/recognize/frame --> MediaPipe Holistic (words) / Hands (letters)
                                                              -> landmark features -> ONNX Runtime model
                                 <--- sign events, live top-3, hand landmarks, FPS, latency
sign strip + 3 s pause           ---- /api/sentence --------> grammar rules (offline) -> Gemini polish (online)
                                 ---- /api/tts -------------> pyttsx3 (SAPI5 / espeak) -> WAV
microphone 16 kHz PCM            ---- /api/speech/transcribe> faster-whisper small (int8) -> subtitle text
transcript                       ---- /api/conversations ---> SQLite (users, conversations, messages)
```

`vite` proxies `/api` to the backend, so the browser only talks to one origin.

## F1 - Sign recognition

**Landmarks.** Each frame goes through MediaPipe Holistic. SignBridge keeps 7 upper-body pose points
(nose, shoulders, elbows, wrists) and the 21 points of each hand. Coordinates are converted to a
*body frame*: origin at the shoulder centre, unit = shoulder width, x corrected for the image aspect.
This makes the features independent of where the person sits and of camera resolution.

**Word features (184 per frame).** Pose points (14) + both hands in body coordinates (84) + both hands
relative to their own wrist, scaled by palm size (84, the hand *shape*) + two hand-present flags.

**Segmentation (sliding window over the stream).** Frames with a visible hand open a segment. When the hands
are lowered for 0.45 s (or a segment passes 3.5 s), the segment is trimmed to the hands-visible part,
resampled to 32 frames and classified. While a segment is open the model runs on the frames so far and
the UI shows a live top-3 guess with confidence bars. Predictions under 40 % confidence are rejected.

**Word model.** A small Transformer encoder: linear embedding (184 -> 128) + learned positions, 2 pre-norm
layers (4 heads, FF 256), mean pooling, linear head over the 50 words (~0.3 M parameters). Trained with label
smoothing, AdamW and a one-cycle schedule; augmentation: rotation +-12 deg, scale, shift, time warping,
jitter, dropped hand frames, and mirroring (left-handed signing). Exported to ONNX, run with ONNX Runtime.

**Fingerspelling.** Letters use MediaPipe Hands (works when only the hands are in view). Features (87):
each hand's shape relative to its wrist (hands ordered left to right) + the offset between the two hands.
A 3-layer MLP classifies 35 classes (A-Z, 1-9). A letter is accepted when it wins 5 of the last 7 frames with
mean confidence >= 60 %; letters build a word that is emitted as one sign when the hands drop for 1.2 s.

## F2 - Sentence formation

Recognised signs (glosses) collect in a strip. A 3 s pause after the last sign closes the window.

1. **Rules (always, offline):** collapse repeats, split greetings (`HELLO` -> "Hello,"), questions
   (`HOW_ARE_YOU` -> "how are you?"), move time words to the front, add the verb after a subject
   (`I SICK` -> "I am sick.", `SHE DOCTOR` -> "She is a doctor.", `I HOSPITAL` -> "I need to go to the hospital.",
   `HE MEDICINE` -> "He needs medicine."), fingerspelled names (`I RAVI` -> "I am Ravi.").
2. **Gemini polish (when online and enabled):** the gloss list plus the rule draft go to Gemini
   (`GEMINI_MODEL`, falling back to `gemini-flash-lite-latest`), which returns one natural sentence.
   Any failure or no network -> the rule sentence is used. The UI shows which one was used.

## F3 - Speech output

`pyttsx3` renders the sentence to a WAV file (Windows SAPI5 voices; espeak on Linux) in a short-lived child
process (pyttsx3 can hang on repeated calls inside one process). The browser plays the WAV.

## F4 - Live subtitles

The browser captures 16 kHz mono audio (Web Audio). A simple energy-based voice detector with an adaptive
noise floor finds speech. While someone talks, the growing utterance is sent every ~1.2 s for a *partial*
subtitle; after 0.8 s of silence (or 12 s) it is finalised and added to the transcript. The backend runs
faster-whisper `small` with int8 weights on CPU (English, Hindi or auto-detect), beam size 1, VAD filter on.
The model is loaded from the local cache (`local_files_only`) so it works with no network.

## F5 - Conversation and history

Signer sentences and hearing-person subtitles form one transcript. **Save** stores it in SQLite
(`conversations`, `messages` with side, text, gloss, confidence, latency, source); saving again appends
only new messages. History lists, shows, downloads (.txt) and deletes conversations.

## F6 - Offline operation and latency

MediaPipe, ONNX Runtime, faster-whisper and pyttsx3 all run locally on the CPU; only the optional Gemini
polish uses the network. The header shows *Online* / *Offline mode* (checked every 15-20 s). The camera
view shows FPS, round-trip latency and server processing time for every frame.

## F7 - Evaluation

`python -m ml.eval` writes `experiments/eval/metrics.json` and confusion-matrix images:

- word and letter accuracy, top-3 accuracy, macro F1, per-class precision / recall / F1, confusion matrices;
- **live-pipeline reliability:** word clips re-extracted with SignBridge's own MediaPipe pipeline (a different
  landmark extractor from the training data) - measures the domain shift the live app faces;
- **robustness:** accuracy under perturbation (rotation, scale, jitter, dropped frames) and mirrored signing;
- **continuous signing:** 60 streams of 3 test signs fed frame by frame (15 fps, hands lowered between signs)
  through the live segmenter -> sign accuracy, word error rate, exact-sequence rate;
- **sentence formation:** exact match of the rules against reference sentences;
- **speech-to-text:** word error rate and real-time factor on phrases rendered by the offline TTS;
- **latency:** landmarks, word model, letter model, whole frame, sentence rules, speech-to-text, text-to-speech.

## Data

| Dataset | Licence | Used for | Committed |
|---------|---------|----------|-----------|
| [ISL MediaPipe Holistic Landmarks (INCLUDE)](https://www.kaggle.com/datasets/swaptr/indian-sign-language-mediapipe-holistic-landmarks) - landmark form of [AI4Bharat INCLUDE](https://github.com/AI4Bharat/INCLUDE), 3.5 GB | MIT | 935 takes of the 50 chosen words (by 7 to 21 takes per word) | `data/words_landmarks.npz` (resampled 32-frame pose + hand points, float16) and 3 sample takes in `data/sample/include/` |
| [ISL words with landmarks](https://www.kaggle.com/datasets/kaushikyh/indian-sign-language-words-with-landmarks), 48.8 MB video clips | CC BY-SA 4.0 | 262 clips of the 16 overlapping words, re-extracted with SignBridge's own pipeline: extra training data + live-pipeline test | `data/word_videos_landmarks.npz` and 3 sample clips in `data/sample/word_videos/` |
| [Indian Sign Language (ISL)](https://www.kaggle.com/datasets/prathumarikeri/indian-sign-language-isl), 285 MB images | CC BY-SA 4.0 | 300 seeded images per class for A-Z and 1-9 -> hand landmarks | `data/letters_landmarks.csv` (10 388 rows) and 2 sample images per class in `data/sample/letters/` |

The full downloads live in `data/raw/` (git-ignored) and are fetched by `scripts/download_data.py`
(kagglehub; for INCLUDE only the needed takes are downloaded). `ml/prepare_data.py` (seed 42) builds the
committed files and `data/splits.json`: a stratified 80 / 20 train / test split **by take**, shared by both word
sources, so the same recording never appears in both train and test. Letters use a seeded 80 / 20 split per class.

## Code map

```
backend/app/main.py            FastAPI app, startup (DB, demo user, models)
backend/app/routes/            auth, recognize, speech (sentence/tts/transcribe), conversations, info (health/vocab/metrics)
backend/app/services/          landmarks (MediaPipe), recognizer (segmentation + ONNX), sentence, tts, stt
ml/                            vocab, features, models, prepare_data, train, eval
scripts/                       download_data.py, smoke_test.py, make_kaggle_notebook.py
frontend/src/                  pages/ (Landing, Login, Conversation, Practice, History, Performance), hooks/, components/
```
