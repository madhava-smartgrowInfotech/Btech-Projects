# StoryVox - canonical narrative for every document

All documents (decks, six chapter documents, the report, the paper) must agree with this file and with `REPORT_FACTS.md`.
Numbers come from `scripts/docs/facts.py` (it loads `experiments/*/metrics.json`); never type a measured number by hand when a
facts value exists, and never invent one. Where something was not measured, say so.

## What StoryVox is
- A local, offline-capable pipeline: **story idea -> story text (Qwen3-0.6B) -> narration (MMS-TTS VITS) -> saved library + evaluation**.
  React web app (5 pages) over a FastAPI service and SQLite, runs on a CPU laptop, no data leaves the machine after the one-time model download.
- It is a **cascade of pretrained models. No model was trained or fine-tuned in this project.** Therefore "training configuration" slides/sections
  describe the *inference configuration* (sampling temperature 0.8, top_p 0.9, token budgets 220/420/700, chunk size 380 characters, 16 kHz, pause 0.25 s, peak normalisation 0.9) and say plainly that no training took place.
- 15 languages, 8 styles, 3 lengths; 11 REST routes (+ SPA fallback); 3 SQLite tables (stories, audio_outputs, evaluations).
- Two TTS providers behind an abstract `TTSProvider`: `MMSTTSProvider` then `SystemTTSProvider` (OS voice, pyttsx3). Two story paths: the model and the offline
  composer `storyvox-local-fallback-v1` (used when the model output has < 20 words or the pipeline fails).

## Base paper and comparability
- Base paper (batch documents): Tran and Sakti, **SAM Translator**, IEEE Access 14, 2742-2752, 2026 (reference [1] in refs.py): mBART + self-paced learning + sparse mixture-of-experts
  (8 experts, top-2; 611M vs 1.7B parameters) + data-augmented self-training for cross-lingual text-to-speech *translation*, evaluated with BLEU on CVSS-C and CoVoST-2, trained on one A100 for 1.5-2 days.
- **StoryVox implements none of SPL, MoE, DAST or unit-based speech translation.** It shares only the *goal* of multilingual speech output. Numbers are **not comparable**:
  SAM reports BLEU on translation; StoryVox reports TTS->ASR WER/CER, RTF and story-generation checks. State this wherever a comparison appears. Compare design choices (cascade vs end-to-end,
  compute, scale), not scores.
- Supporting references: OmniVoice [arXiv 2604.00688] (646 languages, avg CER 4.00%, RTF 0.0319 on its hardware), MultiGen [2508.08715], MMS, VITS, Whisper, Qwen3 (all in refs.py).
- (Mention once, in the literature chapter / paper, that the repository note `BASEPAPER_REFERENCES.md` also lists OmniVoice; the batch documents name SAM Translator, which is used as base paper.)

## Objectives (from the batch documents) and honest status
1. Accept a user prompt - **achieved** (Studio page, 2000-character limit, validated).
2. Generate a story with length and (reading-level) controls - **partly**: 3 lengths and 8 styles exist; **no reading-level control**.
3. Translate into target languages - **not implemented as translation**: the language is requested in the prompt and the model answers directly in it (or fails to). There is no translation module.
4. Convert to speech - **achieved** for 12 languages with MMS; Italian, Chinese, Japanese have no MMS checkpoint on the Hub and fall back to an OS voice (English David/Zira on the test machine).
5. Playback with adjustable voice, speed, language - **partly**: browser audio player (play/pause/seek/download), language chosen at generation time; **no voice or speed selection**.
6. Evaluate coherence, translation quality, naturalness through user rating - **partly**: automated evaluation (WER/CER, similarity, ROUGE-L, RTF); **no user-rating collection**.
Also not implemented: reference-audio upload / voice cloning.

## Key measured findings (details and values: REPORT_FACTS.md; use facts.py)
- **Narration works; generation is the weak link.** MMS narration on CPU: 12 languages, mean RTF 0.247 (0.22-0.46 range), mean normalised CER 0.088 (best Spanish 0.021, worst Hindi 0.180), English WER 0.206 / CER 0.091 on 10 FLEURS sentences. WER/CER mix TTS error with Whisper-small's own error, whose floor was not measured separately.
- **Qwen3-0.6B with the shipped raw prompt (condition A) mostly answers in English** whatever language is requested (language match 3/17 = 0.176), often with "Untitled Story"/echoed instructions (one German title echoed the instruction text). The Qwen3 chat template (condition B, experiment only, not shipped) raises the match to 0.47 and removes instruction echo (0.097 -> 0.006) but is still English for hi/fr/it/ru/ar/tr/pl/ja/ko; target-language text appeared for es, de, pt, nl, zh. The offline composer (C) is instant but template-like and quotes the idea verbatim (prompt-story similarity 0.68 is an artefact, not quality).
- **Language mismatch breaks narration**: all 4 non-English stories generated through the API (hi, fr, de, es) came out as English text and were read by the foreign voice: Hindi voice produced 4.4 s of audio for 185 words; fr/de/es story-length WER 0.6-1.3. English stories: WER 0.25 / CER 0.21 (chunked Whisper).
- **The app's own evaluation reports no WER/CER for story-length audio**: Whisper's plain pipeline call rejects >30 s audio under transformers 5.x ("more than 3000 mel input features"), so every sample in the shipped evaluation carries `asr_error` and the Evaluation page shows WER/CER as "-" (reproduced on 5 of 5 samples); `ffmpeg` is also an undeclared dependency. Fix is a one-line `chunk_length_s=30`; it was **not** applied to the product (documentation task), the experiments score story audio with a separate script (`scripts/run_story_asr.py`).
- Italian/Chinese/Japanese: `facebook/mms-tts-ita/-cmn/-jpn` do not exist on the Hub. Fallback voice narrated 10/10 Italian (English voice reading Italian; WER 0.49) but only 2/10 Chinese (CER 0.85) and 1/10 Japanese (CER 1.00) sentences. Korean works with `uroman` (not in requirements.txt): RTF 0.46, CER 0.121.
- Speed: story generation about 22 s for a Short story (220 tokens, ~9 tokens/s on CPU); Medium 39 s, Long 50 s; narration about 0.22-0.25 RTF; end-to-end Short 37 s, Medium 60 s, Long 80 s (length-scaling experiment). API: non-model endpoints answer in about 1-15 ms median; real generate-with-narration calls 22-67 s, first call (cold) 42 s.
- Tests: 29 pytest tests pass (8 original API tests + 21 added in this documentation run: text/audio/metric helpers, prompt builder, composer in all 15 languages, validation and API edge cases). They use stubbed models; they do **not** exercise the real models (those are exercised by the experiment scripts).
- Environment facts: all runs CPU only (i5-12500, 12 threads, 15.7 GB), system Python 3.11.9, torch 2.14.1, transformers 5.20.2; the project `.venv` points at a missing Python 3.14 and D: had ~1.5 GB free so it could not be rebuilt; `run.bat` therefore was not used (the app was started with uvicorn directly). The 29 tests and all experiments ran against the application's own code.
- Data: FLEURS test split (Google, CC BY 4.0), first 10 length-filtered sentences per language, downloaded from the Hugging Face dataset repo. No other dataset; nothing was trained.

## Conditions in the story experiment (always use these names)
- **A** "shipped path" = app's `generate_story_text`, raw prompt, no chat template.
- **B** "chat-template variant" = same model, Qwen3 chat template with thinking disabled (experiment only, not in the product).
- **C** "offline composer" = `storyvox-local-fallback-v1`.
- 17 items: English x {Adventure, Bedtime, Mystery} + the other 14 languages x Adventure; idea "A young inventor discovers a hidden library."; Short; seed 0; T=0.8, top_p=0.9.
  Condition A with the same seed produces nearly the same English text for most languages - say so (limits variety evidence).
- Metrics: latency, words, tokens/s, language match (langdetect; unreliable on very short text), instruction-echo ratio, distinct-2, MiniLM prompt-story cosine, ROUGE-L.
  These are *proxies*; none measures narrative quality. No human rating was done.

## House terms
- Say "story model" (Qwen3-0.6B), "speech model" (MMS-TTS), "recogniser" (Whisper-small), "composer" (offline fallback), "library" (History page), "round trip" (TTS then ASR).
- RTF = synthesis time / audio duration (lower is faster). WER/CER normalised = NFKC, lower-case, punctuation removed (spaces removed for zh/ja; WER not reported for zh/ja).
- Never claim: translation, voice/speed control, user ratings, training/fine-tuning, GPU use, comparison of scores with the base paper, human-judged quality, security audit.
- Placeholders stay in square brackets: [ACADEMIC YEAR], [PLACE], [DATE], [DESIGNATION], [HOD NAME], [PRINCIPAL NAME]; college name from facts.COLLEGE (verify in the batch documents before relying on it).
