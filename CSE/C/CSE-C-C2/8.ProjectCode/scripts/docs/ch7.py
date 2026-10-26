"""Chapter 7: System Testing for StoryVox. Numbers come from facts.py (experiments/**/metrics.json: tests, api_timing, story_generation, tts_asr)."""
import os

from . import facts as F
from .blocks import B, FIG, H1, H2, P, TAB


def _endpoint_rows():
    rows = []
    for name, e in F.API["endpoints"].items():
        rows.append([name.replace(" (empty prompt, 422)", " (empty prompt, answers 422)"), str(e["n"]), f"{e['median_ms']:.1f}", f"{e['p95_ms']:.1f}", f"{e['max_ms']:.1f}"])
    return rows


def _generate_rows():
    rows = []
    for r in F.API["generate"]:
        rows.append([str(r["order"]) + (" (cold)" if r["cold"] else ""), f"{F.LANG_NAMES[r['language']]}, {r['style']}, {r['length']}", f"{r['request_s']:.1f}",
                     str(r["words"]), f"{r['story_gen_s']:.1f}", f"{r['audio_s']:.1f}", f"{r['tts_s']:.1f}", f"{r['rtf']:.3f}"])
    return rows


def _length_rows():
    return [[r["length"], str(r["max_new_tokens"]), f"{r['gen_s']:.1f}", str(r["words"]), f"{r['audio_s']:.1f}", f"{r['tts_s']:.1f}", f"{r['rtf']:.3f}", f"{r['total_s']:.1f}"]
            for r in F.LENGTH_SCALING]


def blocks():
    b = [H1("CHAPTER 7: SYSTEM TESTING")]

    # ------------------------------------------------------------------ 7.1
    b += [H2("7.1 Testing strategy"),
          P("StoryVox joins three pretrained models behind a small web service, so its testing has to answer two different questions. The first is whether the code around the models is correct: "
            "text is split at sentence boundaries, audio is joined and normalised, error rates are computed correctly, every language has a prompt and a fallback, and the API refuses bad input with the right status code. "
            "These questions have exact answers and are tested with automated unit and API tests. The second question is whether the models, once joined, produce stories and speech that are good enough. "
            "That question has no exact answer; it is addressed by measurement scripts that run the application's own services on fixed inputs and store every result (Chapter 8). "
            "The two are kept apart on purpose. The automated tests replace the story model and the speech model with small stand-ins, so they run in seconds and never download a model, but for the same reason they cannot say anything about story or speech quality."),
          P("The delivered application already contained eight pytest tests (`tests/test_api.py`). The documentation run added 21 more (`tests/test_services.py`), a live-server timing script (`scripts/measure_api.py`), "
            "the experiment script (`scripts/run_experiments.py`), a story-length speech-recognition script (`scripts/run_story_asr.py`) and a screenshot script that drives the real interface (`scripts/capture_screens.py`)."),
          TAB("Test levels, tools and results.",
              ["Level", "Tool and scope", "Count", "Result"],
              [["Unit", "pytest, tests/test_services.py: text, audio and metric helpers, prompt builder, offline composer, configuration", "15 tests", "All passed"],
               ["API / component", "pytest with FastAPI TestClient, models stubbed: tests/test_api.py (8) and the API cases of tests/test_services.py (6)", "14 tests", "All passed"],
               ["Integration (live server)", f"scripts/measure_api.py against a running server on 127.0.0.1, port {F.API_PORT}, real Qwen3 and MMS models", "6 endpoint groups x 30 calls, 7 full generations", "All answered as expected (Section 7.7)"],
               ["Model validation", "scripts/run_experiments.py: 15 languages x 10 FLEURS sentences; 17 prompts x 3 story conditions; length scaling", "150 round trips, 51 stories", "Chapter 8"],
               ["Functional / screens", "Playwright walk of the interface with real stories (scripts/capture_screens.py)", "11 screenshots", "Rendered with real data (Section 7.8)"]],
              widths=[1.3, 3.2, 1.2, 1.0], align=["l", "l", "l", "l"], size=9.5),
          P(f"All tests ran on one machine: Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB RAM, no GPU, Windows 11, system Python 3.11.9, torch 2.14.1 and transformers 5.20.2. "
            f"The complete pytest suite of {F.PYTEST_TOTAL} tests finished in {F.TESTS['seconds']:.1f} seconds. Timings in Section 7.7 were taken on a machine that was not otherwise idle and are indicative. "
            "The project's own virtual environment was not used: it was created on another computer and points at a Python interpreter that does not exist here, and the drive that holds the project had too little free space to rebuild it, so the tests and the experiments ran with the system interpreter.")]

    # ------------------------------------------------------------------ 7.2
    b += [H2("7.2 Unit testing"),
          P(f"The file `tests/test_services.py` holds **{F.PYTEST_UNIT} tests, and all of them passed**. Fifteen are pure unit tests that need no server and no model; the other six use the API test client and are described in Section 7.3. "
            "Every assertion is about one rule with a known answer, which is why synthetic inputs (a 220 Hz sine wave, a string of sixty numbered sentences) are the right tool here."),
          TAB("Unit tests by module (tests/test_services.py).",
              ["Module (tests)", "What is asserted"],
              [["utils text helpers (5): word count and times, chunking, long sentence, Devanagari danda, file names",
                "`word_count('Once upon a time')` is 4 and the empty string gives 0; 200 words read in 1.0 minute and 90 s of audio listens in 1.5 minutes; "
                "`chunk_text` never exceeds the limit, loses no word and keeps the order (sixty sentences, 120-character limit); one 1,000-character sentence is cut into 380 + 380 + 240; "
                "the Hindi sentence mark U+0964 is a sentence boundary; `sanitize_filename` strips accents and symbols, `???` becomes `storyvox`, and two generated audio names for the same story differ"],
               ["utils audio (2): round trip and resampling",
                "A 1 s tone survives write and read at 16 kHz; silence is detected and a tone is not; two tones joined with a 0.25 s pause last 2.25 s; a 22.05 kHz file is resampled to 16 kHz within two samples"],
               ["utils metrics (2): WER, CER, ROUGE-L, TF-IDF",
                "Identical text gives WER 0; one wrong word in three gives 1/3; an empty hypothesis gives 1.0; one wrong character in four gives CER 0.25; ROUGE-L of identical text is 1.0 and all scores stay within [0, 1]; TF-IDF cosine of empty or disjoint texts is 0"],
               ["story generator, offline parts (5): prompt, parsing, budgets, composer, validation",
                "The prompt carries the style, the language name, the paragraph target (8 for Long) and the idea; `Title:` lines, a short first line and empty output are parsed to the right title and body (the last gives `Untitled Story`); "
                "token budgets rise with length and the paragraph targets are 3, 5 and 8; the offline composer quotes the idea and returns exactly five paragraphs for Medium in **every one of the 15 languages**; "
                "an unknown language, style or length and an empty prompt raise `ValueError`"],
               ["configuration (1): language table",
                "15 languages, 8 styles and 3 lengths are defined, and every language names a `facebook/mms-tts-*` checkpoint"]],
              widths=[2.3, 4.1], align=["l", "l"], size=9.5),
          P("Two of these tests guard behaviour that the documents later rely on. The composer test fails if any language loses its prompt-conditioned opening, which would silently turn the offline fallback into a fixed story. "
            "The chunking test fails if a long paragraph can reach the speech model unsplit; the model's behaviour on long input is not specified, and splitting keeps every call below 380 characters. "
            "The tests do not, and cannot, check that the chunk boundaries sound natural.")]

    # ------------------------------------------------------------------ 7.3
    b += [H2("7.3 Integration and API testing"),
          P(f"The API is tested through FastAPI's test client with a temporary database, a temporary audio folder and two stubs: a story function that returns `A Tale of <idea>` and a narration function that writes a half-second two-tone WAV file. "
            f"The stubs make the tests fast and deterministic and test everything around the models: validation, persistence, the link between a story and its audio, file streaming and deletion. "
            f"Of the **{F.PYTEST_API + 6} API-level tests**, eight are in the original file and six were added; all passed."),
          *([] if F.REPORT else [          TAB("API tests (tests/test_api.py and the API cases of tests/test_services.py).",
                  ["No.", "Test", "What it checks"],
                  [["1", "health", "GET /api/health answers 200 with status ok"],
                   ["2", "languages only supported", "GET /api/languages returns at least ten languages including en, fr, de, es"],
                   ["3", "empty prompt rejected", "A prompt of spaces answers 400 or 422"],
                   ["4", "bad language rejected", "Language code `xx` answers 422"],
                   ["5", "full story workflow", "Generate without narration, list, fetch, synthesize afterwards, delete, then the story answers 404"],
                   ["6", "audio path escape", "`ensure_within_directory` raises for a path outside the audio folder"],
                   ["7", "metrics are real", "WER, CER and TF-IDF cosine return the known values on identical and different text"],
                   ["8", "evaluation serialisation", "POST /api/evaluations/run stores a run and GET /api/evaluations lists it (with the evaluation stubbed)"],
                   ["9", "unknown ids give 404", "Get, delete, synthesize and audio download for story 999 all answer 404"],
                   ["10", "over-long prompt and bad options", "A 2,001-character prompt, style `Horror`, length `Epic` and a missing prompt all answer 422"],
                   ["11", "generate with narration", "A French Funny story returns language French, the stub voice, an audio URL that streams `audio/wav` starting with RIFF, and the list shows `has_audio`"],
                   ["12", "delete removes audio and rows", "After delete the audio id answers 404 and the library is empty"],
                   ["13", "meta and unknown API path", "Meta lists Bedtime and the lengths Short, Medium, Long; `/api/nothing-here` answers 404, not the web page"],
                   ["14", "evaluation validation", "Language `xx` and zero samples both answer 422"]],
                  widths=[0.4, 2.0, 4.0], align=["c", "l", "l"], size=9.5)]),
          *([P("The 14 tests run in this order: health; languages list; empty prompt (400 or 422); unknown language (422); a full workflow of generate, list, fetch, synthesize and delete ending in 404; the audio path guard; the real metric helpers; evaluation serialisation; unknown ids (404 for get, delete, synthesize and audio); over-long prompt, bad style, bad length and missing prompt (422); generation with narration and a streamed `audio/wav` file starting with RIFF; deletion that removes the audio and the rows; the meta route and an unknown API path (404, not the web page); and evaluation validation (422).")] if F.REPORT else []),
          P("Test 13 matters because the server also serves the built web application for every path that is not an API path: without the guard, a mistyped API call would return an HTML page with status 200. "
            "Test 12 checks the one place where the application deletes files, and it deletes only files that lie inside the audio folder.")]

    # ------------------------------------------------------------------ 7.4
    b += [H2("7.4 Functional testing"),
          P(f"Functional testing used the live server with the real models. `scripts/measure_api.py` calls the light endpoints 30 times each and then performs seven complete generations (story, then narration) in the languages and styles listed in the table of Section 7.7; every call returned HTTP 200 and an audio file. "
            "The seven stories became the content of the History page, so every screenshot in Chapter 8 shows real output. "
            "The same server then ran the application's own evaluation twice (five samples, then two English samples). Both runs completed and were saved to the database and to JSON and CSV files, "
            "so the evaluation route works end to end, **but neither run produced a WER or CER value** (Section 7.6)."),
          P("The interface offers writing an idea, choosing language, style and length, switching narration off, playing and downloading the WAV file, regenerating narration, searching and sorting the library, opening and deleting a story, and starting an evaluation run. The browser walk (Section 7.8) shows these controls on screen with real data; the routes behind them (generate, synthesize, list, fetch, audio, delete, evaluation) are the ones exercised by the API tests and the live runs, but no test clicks the buttons themselves.")]

    # ------------------------------------------------------------------ 7.5
    b += [H2("7.5 Security testing"),
          P("StoryVox is a single-user tool that runs on the user's own computer. Its security measures are therefore small, and none has been penetration-tested. This section states what exists and what does not."),
          TAB("Security-relevant behaviour of the product.", ["Area", "What exists", "What does not exist"],
              [["Access control", "The server binds to 127.0.0.1 by default (`HOST` setting)", "No login, roles or tokens: anyone who can reach the port can generate, listen to and delete stories and run evaluations"],
               ["Input validation", "Request bodies are typed with pydantic; the prompt is limited to 2,000 characters; language, style and length must come from fixed lists; the library limit is 1-200; tests 3, 4, 10 and 14 cover these", "No rate limit and no queue: every generate call occupies the model for tens of seconds, so repeated calls would simply wait"],
               ["File access", "Audio is served by database id, never by a client-supplied path; stored paths are resolved and must lie inside the audio folder (test 6); the web-page route resolves a path and refuses anything outside the built frontend", "No signing or expiry on audio URLs"],
               ["Database", "All access goes through the SQLAlchemy ORM with bound parameters", "SQLite foreign keys are declared (`ON DELETE CASCADE`) but the pragma is not switched on; deletion relies on the ORM cascade instead"],
               ["Model loading", "Model weights come from the Hugging Face Hub by name and are cached locally", "The story pipeline is created with `trust_remote_code=True`, which lets a model repository run its own Python code when loaded; the configured model is trusted by choice, but a changed `STORY_MODEL` setting would extend that trust"],
               ["Data leaving the machine", "After the one-time model download nothing is sent anywhere; stories and audio stay in `data/`", "No encryption at rest; the files are plain"],
               ["Error messages", "Server errors return a fixed sentence (`Check the server log for details`); the stack trace goes to the log only", "-"]],
              widths=[1.1, 3.0, 2.4], align=["l", "l", "l"], size=9.5)]

    # ------------------------------------------------------------------ 7.6
    b += [H2("7.6 Validation and edge cases"),
          P("The cases below were exercised by the automated tests or by the live runs unless a note says otherwise. Several of them found real defects rather than passes; those are reported plainly because they decide how far the product can be trusted."),
          TAB("Edge cases, expected behaviour and observed result.", ["Case", "Expected behaviour", "Observed"],
              [["Empty or over-long prompt", "422 with a clear message", "Passed (tests 3 and 10; the live server answered 422 in a median of 10.8 ms)"],
               ["Unknown language, style or length", "422", "Passed (tests 4, 10 and 14)"],
               ["Unknown story or audio id", "404", "Passed (test 9)"],
               ["Sentence longer than the chunk limit", "Cut into pieces of at most 380 characters", "Passed (unit test)"],
               ["Hindi text", "Split at the danda (U+0964)", "Passed (unit test)"],
               ["Story requested in a non-English language", "Story written in that language, then read by that language's voice", f"**Failed for the shipped path**: in 4 of 4 live generations (Hindi, French, German, Spanish) the story text came out in English and was then read by the foreign voice (Section 8.5)"],
               ["Narration for a language with no MMS checkpoint (Italian, Chinese, Japanese)", "Fall back to an operating-system voice", "Italian: 10 of 10 sentences narrated, but by an English voice; Chinese 2 of 10 and Japanese 1 of 10 produced any audio (Section 8.3)"],
               ["Korean text", "Narrated by the Korean MMS model", "Works only after the `uroman` package is installed; it is not in requirements.txt"],
               ["Story-length audio sent to the recogniser", "WER and CER computed", "**Failed**: with transformers 5.20.2 the recogniser rejects audio over 30 s (`You have passed more than 3000 mel input features`), so all 7 evaluation samples of the two live runs carry `asr_error` and the Evaluation page shows WER and CER as a dash"],
               ["`ffmpeg` missing", "Recogniser reads the WAV", "Failed on the test machine until a portable ffmpeg was put on the path; ffmpeg is not listed as a requirement"],
               ["Model output with fewer than 20 words", "Offline composer is used", "Passed by design (not triggered in the live runs)"],
               ["Model echoes its instructions or invents a title", "Title parsed from a `Title:` line, otherwise `Untitled Story`", f"Title was `Untitled Story` in {sum(1 for r in F.STORY['conditions']['A_app_raw_prompt'] if r['title'] == 'Untitled Story')} of 17 shipped-path stories; one evaluation story was titled with an instruction sentence (Section 8.7)"]],
              widths=[1.9, 2.0, 2.6], align=["l", "l", "l"], size=9),
          P("The two recogniser failures are why the application's own Evaluation page, in the state in which it was delivered, shows speed and similarity but no intelligibility figure. "
            "They were not repaired in the product during this documentation run; the experiments score the same audio with a separate script that cuts it into 30-second chunks (`scripts/run_story_asr.py`), "
            "so the intelligibility results in Chapter 8 are real even though the page cannot show them. Because the fix is a single option, `chunk_length_s=30`, it is listed in Chapter 10 as the first piece of future work.")]

    # ------------------------------------------------------------------ 7.7
    b += [H2("7.7 Performance testing"),
          P("`scripts/measure_api.py` measures a running server. Calls go to 127.0.0.1 because on this machine the name `localhost` adds about two seconds to every request through an IPv6 fallback, which would make every light call look a thousand times slower than it is."),
          TAB("Latency of repeated calls to the endpoints that do not run a model (milliseconds).", ["Endpoint", "Calls", "Median", "95th percentile", "Maximum"], _endpoint_rows(),
              widths=[2.9, 0.6, 0.8, 1.2, 0.9], align=["l", "c", "c", "c", "c"], size=9.5)]
    fig5 = F.fig("f05_api_latency.png")
    if os.path.exists(fig5) and not F.REPORT:
        b.append(FIG(fig5, "Median and 95th-percentile latency of the endpoints that do not run a model.", 5.6))
    b += [P("The light endpoints answer in a few to fifteen milliseconds at the median and in under 50 ms at the 95th percentile, including a library list with seven stories and the download of a 55-second WAV file (1.8 MB). "
            "They are not a concern. Everything a user waits for is the two model calls."),
          TAB("Seven complete generations with narration through the live API (seconds).",
              ["No.", "Language, style, length", "Request", "Words", "Story", "Audio", "Narration", "RTF"], _generate_rows(),
              widths=[0.8, 2.0, 0.7, 0.6, 0.6, 0.6, 0.8, 0.6], align=["l", "l", "c", "c", "c", "c", "c", "c"], size=9),
          P(f"A Short story takes 20 to 29 seconds to write (about 9 tokens per second on this CPU) plus 9 to 18 seconds to narrate, so 30 to 42 seconds end to end (23 s for the Hindi story, whose narration was almost empty); the first call took 42.1 s because the models were loaded inside that request. "
            f"Narration runs at a real-time factor of about 0.21 to 0.25 for the English, French, German and Spanish voices, so a minute of speech costs a quarter of a minute. "
            f"The Hindi call is the odd one: its narration lasted 4.4 s for a 185-word story, which gives an RTF of 0.557 only because there was almost nothing to say. The Hindi voice was given English text (Section 8.5)."),
          TAB("Story length against time: chat-template story plus English MMS narration (seconds, one run each).",
              ["Length", "Token budget", "Story", "Words", "Audio", "Narration", "RTF", "Total"], _length_rows(),
              widths=[0.8, 0.9, 0.7, 0.7, 0.7, 0.9, 0.7, 0.7], align=["l", "c", "c", "c", "c", "c", "c", "c"], size=9.5)]
    fig4 = F.fig("f04_length_scaling.png")
    if os.path.exists(fig4):
        b.append(FIG(fig4, "End-to-end time by story length: story generation and narration, stacked.", 5.0))
    b += [P("Story time grows with the token budget but less than proportionally: 220, 420 and 700 tokens took 22, 39 and 50 seconds, because the model finished before using its whole budget (175, 316 and 418 words), and the narration RTF fell slightly from 0.25 to 0.22. "
            "A Long story therefore needs about 80 seconds on a CPU laptop and yields about 137 seconds of speech. "
            "No graphics card was available, so the figures say nothing about GPU speed; the code uses a GPU automatically when `torch.cuda.is_available()` is true, but that path was never run.")]

    # ------------------------------------------------------------------ 7.8
    b += [H2("7.8 User acceptance and the browser walk-through"),
          P("**No user study was run.** No teacher, parent or student outside the project team used StoryVox under observation, so there are no task times, ratings or satisfaction scores, and none is claimed. "
            "The batch objective of judging coherence and naturalness through user rating is therefore not met (Chapter 8, Section 8.13)."),
          P("What was done instead is a scripted walk of the interface that a user would follow. `scripts/capture_screens.py` opens the application in headless Chrome at 1440 by 900 pixels and visits the landing page in light and dark colour schemes, "
            "the empty Studio, a generated story in the Studio, the History library, a story detail page, the Hindi story, and the Evaluation page on its chart, samples and summary views, saving 11 screenshots from the live application with real stories. "
            "The screens render with the data from Section 7.7, the audio player shows the real duration (for example 1:57 for the 335-word story), and the dark theme and the sidebar behave as designed. "
            "The walk does not exercise the generate button itself, because a generation takes tens of seconds; the stories were created through the API with the same code path."),
          P("The walk is also the evidence for a point that tests cannot make: the interface is honest about missing data. The Evaluation page shows a dash for WER and CER, with the hint *Needs narration + transcription*, instead of a zero, "
            "and the story page shows the title `Untitled Story` exactly as the model left it, so what the screenshots show is what the model produced.")]

    # ------------------------------------------------------------------ 7.9
    b += [H2("7.9 Limits of the testing done"),
          B("**The automated tests use stand-ins for both models.** They prove the code around the models; they say nothing about story or speech quality. Quality is covered only by the experiment scripts.",
            "**Quality is measured by proxies.** Language match (a language detector), instruction echo, distinct-2, a sentence-embedding similarity and ROUGE-L can show that a story is in the wrong language or repeats itself; they cannot show that a story is good. No person rated any story or any narration.",
            "**The recogniser sits inside every intelligibility figure.** WER and CER compare the text with what Whisper-small heard; they contain Whisper's own mistakes, and Whisper's error on natural recordings of the same sentences was not measured.",
            "**Small samples.** Ten FLEURS sentences per language, seventeen stories per condition, seven live generations and one run of each timing. The numbers show orders of magnitude and clear differences, not narrow ones.",
            "**One machine, CPU only, one seed.** Story sampling used seed 0, which makes condition A nearly identical across languages; a different seed would give different texts.",
            "**No load or concurrency test.** One request at a time was tried; two simultaneous generations would share one model object behind a lock and simply queue.",
            "**One browser and one viewport.** The walk used headless Chrome at 1440 by 900 only; phones, other browsers and screen readers were not checked.",
            "**No security audit** beyond the notes in Section 7.5, and no accessibility audit."),
          P(f"In short: the rules in the code are covered by {F.PYTEST_TOTAL} passing automated tests; the live server answers correctly and quickly apart from the model calls; and the quality of the stories and the speech is established by experiments, which found real defects "
            "that the automated tests could not have found.")]
    return b
