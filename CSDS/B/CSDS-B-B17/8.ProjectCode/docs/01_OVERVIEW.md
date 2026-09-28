# CallSense - overview

## The problem
Contact centres review only a small sample of calls by hand. Manual monitoring is slow, subjective and costly;
customer emotion, intent and recurring issues are not captured systematically, and insights arrive too late to act on.

## What CallSense does
CallSense analyses **every** call automatically and turns the recording into insight for supervisors, QA teams,
agents and customer-experience managers.

| # | Feature | What you get |
|---|---------|--------------|
| F1 | Call ingestion | Upload one or many recordings (wav, mp3, flac, ogg, webm, m4a) or record from the microphone. |
| F2 | Transcription | faster-whisper (`small`, CPU) with word timestamps. Stereo calls are split by channel (agent / customer); single-channel audio uses a pause-based turn split. |
| F3 | Intent & topics | 27 customer-support intents and 11 topics from a model trained on the Bitext dataset, plus TF-IDF keywords. |
| F4 | Sentiment & emotion | Text sentiment per turn + voice emotion (pretrained wav2vec2) fused into an emotion timeline with escalation flags. |
| F5 | Call summary | Gemini writes a summary, the reason for the call, the resolution (resolved / partially / unresolved) and action items. |
| F6 | Agent scorecard | Greeting, empathy, talk/listen ratio, silence, interruptions, resolution and sentiment change -> score out of 100 with the evidence for each item. |
| F7 | Sample call studio | Turns a two-speaker script into a stereo recording with two offline voices, then analyses it. Every such call is labelled **Sample**. |
| F8 | Analytics | Call volume, top intents, topics, sentiment trend, customer emotions, agent leaderboard, recent escalations and full-text transcript search. |
| F9 | Evaluation | Intent accuracy and macro-F1, sentiment F1, word error rate, speaker attribution and voice-emotion accuracy. |

## Users and roles
- **Supervisor / QA** - sees every call, assigns uploads to agents, loads the sample calls, sees the whole leaderboard.
- **Agent** - sees and uploads only their own calls and scorecards.

## Screens
Landing - Login - Calls (list, search, upload, microphone) - Call detail (player, transcript, emotion timeline,
summary, scorecard) - Sample call studio - Analytics - Model performance.

## Design choices
- Everything except the summary runs locally on CPU, so audio never leaves the machine for transcription.
- Scorecard rules are transparent: each item shows the quote, timing or measurement it is based on.
- Calls are analysed by one background worker, so uploads return immediately and pages poll for progress.
