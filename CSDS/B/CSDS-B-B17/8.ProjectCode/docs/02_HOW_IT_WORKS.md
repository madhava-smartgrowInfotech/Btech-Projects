# CallSense - how it works

## Architecture
```
React + Vite (5217) --/api proxy--> FastAPI (8217) --> SQLite (data/app.db)
                                         |
                                         +--> background worker: the call pipeline (one call at a time)
                                         +--> scripts/tts_worker.py subprocess (offline voices for the studio)
```

## The call pipeline (`backend/app/services/pipeline.py`)
1. **Decode** - PyAV (bundled with faster-whisper) decodes any common format to 16 kHz. A stereo file whose two
   channels differ is treated as a two-speaker recording.
2. **Transcribe** (`speech.py`) - faster-whisper `small`, int8, CPU, English, VAD filter, word timestamps.
   - *Stereo*: each channel is transcribed separately; the channel that speaks first is the agent. Words from both
     channels are interleaved by time and grouped into turns (a turn ends when the other side speaks or after a
     1.5 s pause). Raw per-speaker speech intervals are kept for the talk-time metrics.
   - *Mono*: simple turn split - a new turn starts after a 0.7 s pause that follows the end of a sentence, and
     turns alternate agent / customer starting with the agent.
3. **Text sentiment** (`nlp.py`) - TF-IDF (word 1-2 grams + char 2-5 grams) + logistic regression, trained on
   customer-service messages. Score = P(positive) - P(negative).
4. **Voice emotion** - `superb/wav2vec2-base-superb-er` (pretrained, 4 classes: neutral, happy, angry, sad) on each
   turn's audio from that speaker's channel (middle 8 s at most).
5. **Fusion** (`analysis.py`) - valence = 0.75 x text score + 0.25 x (happy - angry - 0.5 x sad). Labels:
   `<= -0.3` frustrated (angry when the voice is angry and the text negative), `< -0.1` concerned, `< 0.2`
   neutral, otherwise satisfied, or **relieved** when the same speaker was negative earlier in the call.
6. **Escalation flags** - escalation language (manager, complaint, unacceptable, ...), strong negative emotion
   (valence <= -0.45), three negative customer turns in a row, and silences of 5 s or more.
7. **Intent & topic** - every sentence of the first four customer turns is classified by the Bitext model; sentence
   probabilities are averaged with weights = confidence² x position decay, so the sentence that states the reason
   dominates. The topic is the Bitext category of the intent. Keywords are the top TF-IDF terms of the call,
   minus conversational filler.
8. **Scorecard** (weights add up to 100):

   | Item | Weight | Rule |
   |------|-------:|------|
   | Greeting & introduction | 10 | greeting phrase 60 % + agent introduces themself 40 % (first agent turn) |
   | Empathy | 15 | 0 statements -> 0, 1 -> 60 %, 2+ -> 100 % ("sorry", "I understand", "apologise", ...) |
   | Talk / listen ratio | 15 | agent share of talk time 35-60 % = full marks, linear fall-off outside |
   | Dead air / silence | 10 | loses marks for every second of silence beyond 3 s (0 at 8 s over) |
   | Interruptions | 10 | -35 % per agent interruption, -20 % per customer talk-over |
   | Resolution | 25 | completed action 50 % (hand-off 20 %) + customer ends positive 30 % + closing check 20 % |
   | Sentiment change | 15 | 0.5 + 0.5 x end valence + 0.5 x (end - start), clipped to 0-1 |
9. **Summary** (`summary.py`) - Gemini (`GEMINI_MODEL`, JSON mode) gets the time-stamped, speaker-labelled transcript
   and returns summary, reason, resolution, status, action items and customer mood. Busy / quota / retired-model
   errors fall through `GEMINI_FALLBACK_MODELS`. If Gemini is unreachable the rest of the analysis is still saved
   and the summary can be regenerated from the call page.

## Sample call studio (`studio.py`, `scripts/tts_worker.py`)
A script line is `Agent: text` or `Customer [negative|neutral|positive]: text`. Each line is rendered with pyttsx3
(offline Windows voices: the agent voice and the customer voice), trimmed, resampled to 16 kHz and placed on the
agent (left) or customer (right) channel with seeded pauses; stock scripts can add holds (`pause_before`) and
talk-over (`overlap`). The tone tag only sets the speaking rate and is stored as ground truth - the pipeline never sees it.
The ten bundled scripts (`data/sample/scripts/calls.json`) are rendered by `scripts/generate_sample_calls.py`
into `data/sample/calls/*.flac` + `*.json` (line timings). They are loaded from the Calls page ("Load sample calls")
with dates spread over the previous ten days so the trend chart has shape; all are labelled Sample.

## Models and training (`ml/train.py`, about a minute on CPU)
| Model | Data | Result (held-out 20 %) |
|-------|------|------------------------|
| Intent (27 classes) | Bitext, 26.9k utterances | accuracy 0.998, macro-F1 0.998 |
| Sentiment (3 classes) | Twitter US Airline Sentiment, 14.6k messages | accuracy 0.801, macro-F1 0.750 |
| Keywords | TF-IDF vocabulary over all support text | 49.9k terms |
| Voice emotion | pretrained `superb/wav2vec2-base-superb-er` | evaluated only (see below) |

Artifacts: `models/*.joblib`, metrics in `experiments/metrics.json` (seed 42).

## Evaluation (`ml/eval.py`)
Writes `experiments/eval/metrics.json`; results are listed in the README and on the Model performance page.
- Intent: Bitext held-out split, and the full pipeline on the 10 sample calls (call-level accuracy / macro-F1).
- Sentiment: script lines of the sample calls, transcribed customer turns (end to end), and the 20 real call-centre
  transcripts (Angry/Frustrated -> negative, Happy -> positive, Neutral/Confused -> neutral).
- Transcription: WER on the sample calls and on the 20 real recordings (lower case, no punctuation, digits spelled
  out; long digit strings read digit by digit), plus speaker-attribution accuracy on the stereo sample calls.
- Voice emotion: accuracy / macro-F1 on the committed RAVDESS and CREMA-D sample.

## Data sources and licences
| Dataset | Source | Licence | In the repository |
|---------|--------|---------|-------------------|
| Bitext Customer Support (27k) | kaggle.com/datasets/bitext/bitext-gen-ai-chatbot-customer-support-dataset | CDLA-Sharing-1.0 | full CSV, `data/bitext/` (19 MB) |
| Call Center Transcripts | kaggle.com/datasets/oleksiymaliovanyy/call-center-transcripts-dataset | MIT | full (20 wav + CSV), `data/call_center/` (21 MB) |
| Twitter US Airline Sentiment | kaggle.com/datasets/crowdflower/twitter-airline-sentiment | CC BY-NC-SA 4.0 | `Tweets.csv`, `data/airline/` (3.3 MB) |
| RAVDESS Emotional Speech | kaggle.com/datasets/uwrfkaggler/ravdess-emotional-speech-audio | CC BY-NC-SA 4.0 | sample: 40 clips (actors 1-10 x neutral/happy/sad/angry), `data/sample/emotion/ravdess/` |
| CREMA-D | kaggle.com/datasets/ejlok1/cremad | ODC-By | sample: 40 clips (actors 1001-1010, sentence DFA), `data/sample/emotion/cremad/` |
| Sample calls | generated by `scripts/generate_sample_calls.py` | - | `data/sample/calls/` (10 stereo FLAC, 15 MB) |

`scripts/download_data.py` re-downloads everything through `kagglehub`; `--full` also fetches the complete RAVDESS
(563 MB) and CREMA-D (578 MB) archives into the git-ignored `data/raw/`. The Twitter Airline set was added because
the listed datasets carry no per-utterance sentiment labels (the Call Center set has only 20 labelled calls, which is
used for evaluation instead).

## API
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/auth/login`, GET `/api/auth/me` | JWT login (bcrypt passwords) |
| GET | `/api/agents` | agents (supervisor: all, agent: self) |
| GET / POST | `/api/calls` | list + search (`q`, `agent_id`, `intent`, `status`) / multi-file upload |
| GET / DELETE | `/api/calls/{id}` | full analysis / delete |
| GET | `/api/calls/{id}/audio` | audio stream (`?token=` for the player) |
| POST | `/api/calls/{id}/reprocess`, `/api/calls/{id}/summary` | re-run the pipeline / regenerate the summary |
| GET / POST | `/api/studio/scripts`, `/api/studio/generate`, `/api/studio/import-samples` | sample call studio |
| GET | `/api/analytics?days=`, `/api/metrics`, `/api/health` | dashboards, model metrics, status |

## Database
`users` (email, name, role supervisor | agent, bcrypt hash) and `calls` (audio path, agent, status and stage,
segments JSON with per-turn sentiment / voice emotion / valence / emotion, transcript text for search, intent, topic,
keywords, sentiment, flags, summary, scorecard, score, reference script for sample calls, timestamps).
