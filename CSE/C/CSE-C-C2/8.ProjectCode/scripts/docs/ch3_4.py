"""Chapters 3 (Feasibility Study) and 4 (System Requirements and Analysis) for StoryVox.

Every measured number is read from facts.py (experiments/*/metrics.json); nothing is typed in by hand except
values that come straight from the source tree (ports, limits, versions recorded in REPORT_FACTS.md).
"""

import os

from . import facts as F
from .blocks import B, FIG, H1, H2, N, P, TAB
from .refs import N as C


def blocks():
    out = chapter3() + chapter4()
    if F.REPORT:   # compact report variant: the workflow diagram is shown in Chapter 5 and the phase list becomes a paragraph
        out = _trim(out)
    return out


def _trim(bl):
    res = []
    for b in bl:
        if b[0] == "fig" and b[1].endswith("02_high_level_workflow.png"):
            continue
        if b[0] == "tab" and b[1].startswith("Project phases"):
            res.append(P("The work followed the dependencies of the pipeline, with calendar dates left as placeholders [DATES]: problem study and base-paper reading; the service layer (story generator, speech providers, recogniser, database); "
                         "the React web application; the evaluation pipeline and the first automated tests; and finally the documentation run with its experiments, added tests, diagrams and screenshots. "
                         "Each phase depends on the previous one, and the schedule risk was model download and CPU time rather than programming effort."))
            continue
        res.append(b)
    return res


def _api(key):
    return F.API["endpoints"][key]


def _ok(code):
    e = F.LANGS[code]
    return e.get("narrated", e["scored"])


def _gen(order):
    return next(r for r in F.API["generate"] if r["order"] == order)


# =====================================================================================================================
def chapter3():
    cold, warm = _gen(1), _gen(2)
    short, medium, long_ = F.LENGTH_SCALING
    a, b, c = (F.STORY_SUMMARY[k] for k in ("A_app_raw_prompt", "B_chat_template", "C_local_composer"))
    en = F.LANGS["en"]
    return [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        H2("3.1 Technical Feasibility"),
        P("**Hardware.** Every measurement in this report was taken on an Intel Core i5-12500 (12 logical threads) with 15.7 GB of memory, with no graphics card used for computation, running Windows 11 Pro. "
          f"The story model, the speech models and the speech recogniser all ran on the processor (the server reports `cuda: false`). The project therefore shows that the complete pipeline, from story idea to a narrated WAV file, "
          "runs on an ordinary office PC; smaller machines and machines with a graphics card were not tested."),
        P(f"**Software.** The components are open-source packages: Python {F.TESTS['python']}, PyTorch 2.14.1 and Hugging Face Transformers 5.20.2 {C('hf')} for the models, FastAPI 0.143.3 with Uvicorn 0.54.0 and SQLAlchemy 2.0.30 for the service, "
          "SQLite for storage, and React 19 with Vite and Recharts for the web application. `requirements.txt` lists the Python packages without version pins. "
          "Three needs are not in that list and were found only by running the system: `ffmpeg` (Whisper reads the WAV file through it), the `uroman` romaniser (the Korean speech checkpoint needs it) and the operating-system speech voices; "
          "the Dockerfile installs `ffmpeg` and `espeak-ng`, which suggests the authors met the first one before."),
        P("**Models.** StoryVox uses four pretrained models and trains none of them. The table gives their role and the disk space each occupies in the local Hugging Face cache on the test machine (measured with a directory-size count)."),
        TAB("Pretrained models used and their size on disk", ["Model", "Role", "Size on disk"],
            [["Qwen/Qwen3-0.6B " + C("qwen3"), "Story generation (decoder-only language model)", "1,519 MB"],
             ["facebook/mms-tts-* " + C("mms", "vits"), "Narration, one VITS checkpoint per language; 12 languages were fetched in the experiments", "145 MB each"],
             ["openai/whisper-small " + C("whisper"), "Speech recognition for the evaluation only", "971 MB"],
             ["paraphrase-multilingual-MiniLM-L12-v2 " + C("sbertm"), "Prompt-story similarity in the evaluation only", "480 MB"]],
            widths=[2.4, 3.0, 1.1], align=["l", "l", "r"], size=9.5),
        P("The four models together need roughly 4.7 GB of disk once the twelve narration checkpoints are cached. The process that held the story model, the recogniser and the similarity model during the experiments was observed at 3.7 to 4.9 GB of resident memory; "
          "this was watched during the runs and not logged as a formal measurement."),
        P("**Data.** The pipeline needs no dataset to run: the user types the story idea. Evaluation uses the FLEURS speech corpus " + C("fleurs") +
          f" (test split, CC BY 4.0), of which only {F.TTS['languages']['en']['n']} short sentences per language were taken. It is downloaded from the Hugging Face dataset repository on demand and not stored in the project."),
        P("**Evidence from measurement.** The main technical risks were tested directly instead of argued. The table lists them with what was measured."),
        TAB("Technical risks and the measurements that retired them", ["Risk", "Measurement", "Verdict"],
            [["A 0.6 B-parameter story model is too slow on a CPU",
              f"{F.f1(a['mean_tok_per_s'])} tokens per second; a Short story ({F.STORY['max_new_tokens']} new tokens) takes {F.f1(short['gen_s'])} s, Medium {F.f1(medium['gen_s'])} s, Long {F.f1(long_['gen_s'])} s", "Feasible, slow"],
             ["Neural narration is too slow without a GPU",
              f"Mean real-time factor {F.f2(F.MMS_MEAN_RTF)} over {len(F.MMS_LANGS)} languages (range {F.f2(min(F.LANGS[c]['mean_rtf'] for c in F.MMS_LANGS))} to {F.f2(max(F.LANGS[c]['mean_rtf'] for c in F.MMS_LANGS))}): 10 s of speech in about {F.f1(10 * F.MMS_MEAN_RTF)} s", "Feasible"],
             ["The whole chain is too slow to be interactive",
              f"Short story with narration {F.f1(short['total_s'])} s, Medium {F.f1(medium['total_s'])} s, Long {F.f1(long_['total_s'])} s; the first API call after start-up (cold, models loading) took {cold['request_s']} s against {warm['request_s']} s for a comparable warm call", "Usable, not instant"],
             ["Speech is not intelligible",
              f"Round trip through Whisper-small on FLEURS sentences: mean normalised CER {F.pct(F.MMS_MEAN_CER)}, English WER {F.pct(en['wer_norm_corpus'])} / CER {F.pct(en['cer_norm_corpus'])}", "Feasible for the 12 MMS languages"],
             ["All 15 languages can be narrated",
              f"`facebook/mms-tts-ita`, `-cmn` and `-jpn` do not exist on the model hub; the operating-system voice narrated {_ok('it')} of {F.LANGS['it']['n']} Italian (read by an English voice), {_ok('zh')} of {F.LANGS['zh']['n']} Chinese and {_ok('ja')} of {F.LANGS['ja']['n']} Japanese sentences", "Not feasible for it, zh, ja"],
             ["The small model writes in the requested language",
              f"Language match {F.pct(a['language_match_rate'], 0)} with the shipped prompt, {F.pct(b['language_match_rate'], 0)} with the chat template; all 4 non-English API stories came out in English", "Not established"],
             ["The evaluation measures story-length narration",
              "The recogniser call fails for audio longer than 30 s, so the shipped evaluation returns no WER or CER (5 of 5 samples); a chunked call works", "Needs a one-line fix"]],
            widths=[1.9, 3.4, 1.2], align=["l", "l", "l"], size=9),
        P("**Environment problems that did occur.** The project's `.venv` was created on another machine and points at a Python 3.14 that is not installed, and the project drive had about 1.5 GB free, so it could not be rebuilt; "
          "every run used the system Python 3.11.9, and `run.bat` was not used (the server was started with `uvicorn` directly). The speech checkpoints are fetched on first use, which took 19 to 25 s for each of the ten languages loaded for the first time and 1.8 s for English and Korean, which were already cached. "
          "A Python client calling the service through the name `localhost` added about two seconds per request on this machine, so all API timings use 127.0.0.1. "
          "None of these blocks the project, and each is recorded where it matters."),
        H2("3.2 Economic Feasibility"),
        P("The project was built with no software licence cost: Python, PyTorch, Transformers, FastAPI, SQLite, React and Vite are open source, and the four models are downloaded free of charge. "
          "After the one-time download the system needs no internet connection and calls no paid service, so there is no per-story or per-minute fee; the cost of a story is the processor time shown in Section 3.1."),
        P("Licences of the models matter as much as their price. As we read the model cards, Qwen3-0.6B, Whisper-small and the MiniLM model carry permissive licences, whereas the MMS-TTS checkpoints are released under a non-commercial licence (CC BY-NC 4.0). "
          "We did not verify this against the legal texts; anyone who wants to use StoryVox commercially must check the licence of every checkpoint first. The FLEURS data are CC BY 4.0 and are used here for evaluation only."),
        P("The hardware is a standard computer that the team already had. Electricity and the team's own time were the only costs, and we put no money figures on them because none were recorded. "
          "For a school or a family the economic question is whether a local tool replaces a subscription service for narrated stories; this project does not measure that comparison, "
          "and it also does not show that the story quality is good enough to replace one (Chapter 8)."),
        H2("3.3 Operational Feasibility"),
        P("A user needs no programming skill. The web application has five pages: Home, Studio, History, Story and Evaluation. In the Studio the user types an idea, chooses a language, a style and a length, and presses one button; "
          "the page shows an elapsed-time counter while the models work, then the story with an audio player and a download button. History lists the saved stories and offers view, play, download and delete; "
          "Evaluation runs and shows the measurement loop. Errors come back as plain sentences ('Please enter a story idea.', 'This language is not currently supported for narration.'), not as stack traces."),
        P("Operation is deliberately simple. The application is single-user and local: it listens on 127.0.0.1, keeps stories in a SQLite file and narration in WAV files under `data/`, has no login, and loads each model lazily at first use. "
          f"That suits one person on one machine; it does not suit several simultaneous users, because a generation request holds a worker for about {F.f1(short['gen_s'])} to {F.f1(long_['gen_s'])} s and no concurrency test was done. "
          f"Maintenance is light: the Python code is 16 small files, and {F.PYTEST_TOTAL} automated tests ({F.PYTEST_API} written with the application and {F.PYTEST_UNIT} added during the documentation run) catch regressions in the service layer, although they replace the models with stubs (Chapter 7)."),
        H2("3.4 Schedule Feasibility"),
        P("The work divides into phases that follow the dependencies of the pipeline. Calendar dates are left as placeholders because the batch file does not record them; the order and the output of each phase are what the report can state truthfully."),
        TAB("Project phases", ["Phase", "Work", "Output", "Dates"],
            [["1", "Problem study and base-paper reading", "Abstract, objectives, literature survey", "[DATES]"],
             ["2", "Service layer: story generator, speech providers, recogniser, database", "app/ package: 11 routes, 3 tables, 4 services", "[DATES]"],
             ["3", "Web application", "React console with 5 pages and its own UI kit; first plain HTML interface kept in legacy_frontend/", "[DATES]"],
             ["4", "Evaluation pipeline and first tests", "evaluation_service, metrics helpers, 8 API tests", "[DATES]"],
             ["5", "Documentation run: experiments, added tests, screenshots, diagrams", f"21 added tests, experiments/ with 5 metric files, 12 diagrams, 8 result figures, {len(os.listdir(F.SHOTS))} screenshots", "[DATES]"],
             ["6", "Documents: reviews, report, paper", "Decks, chapter documents, report, IEEE paper", "[DATES]"]],
            widths=[0.6, 2.6, 2.4, 0.9], align=["c", "l", "l", "c"], size=10),
        P("The schedule is feasible because every phase depends only on the previous one and each is small; the heaviest compute step, the whole experiment suite, ran in a few hours on the CPU, mostly waiting for story generation at about 22 s per story. "
          "The risk to the schedule was not programming but the environment: model downloads, a broken virtual environment, a full disk and a library upgrade that changed how Whisper handles long audio."),
        H2("3.5 Advantages and Constraints"),
        B("**Advantages.** No licence cost for the software; runs on a desktop; local and private (no story leaves the machine after the downloads); one interface for writing, listening, keeping and measuring; "
          "a replaceable speech provider behind an abstract class; every number in this report is reproducible by a script.",
          f"**Constraints.** The 0.6 B story model usually answers in English whatever language is requested ({F.pct(a['language_match_rate'], 0)} language match); three of the 15 languages have no neural speech checkpoint; "
          "there is no translation module, no voice or speed control and no rating form; the evaluation fails for story-length audio without a fix; models need about 4.7 GB of disk and several GB of memory; "
          "the first request after start-up is slow; one user at a time."),
    ]


# =====================================================================================================================
def chapter4():
    cold = _gen(1)
    short, medium, long_ = F.LENGTH_SCALING
    health, langs, meta = _api("GET /api/health"), _api("GET /api/languages"), _api("GET /api/meta")
    stories, aud = _api("GET /api/stories"), _api("GET /api/audio/{id} (WAV download)")
    a = F.STORY_SUMMARY["A_app_raw_prompt"]
    return [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        H2("4.1 Existing System"),
        P("Two things count as the existing system. In practice, someone who wants a narrated story in another language combines separate tools by hand: a text generator or a book for the story, a translation service if the language differs, and a text-to-speech service or app for the voice. "
          "Each step has its own interface, its own account or licence, and no shared record of what was produced. Related research systems address parts of this chain: story co-creation tools such as Kahaani " + C("kahaani") +
          ", a child-friendly multilingual speech generator built around large language models " + C("multigen") + ", and broad multilingual speech synthesisers " + C("omni", "xtts") + "."),
        P("In the project's own history, the existing system was the first interface in `legacy_frontend/` (three files, 358 lines of plain HTML, CSS and JavaScript). It called the same API (`/api/stories/generate`, `/api/audio/{id}`, `/api/evaluations`) "
          "and asked for confirmation before deleting, but it offered no routed pages, no searchable or sortable library, no per-story detail page and no evaluation charts. It was replaced by the React application, and the folder is kept for reference."),
        H2("4.2 Limitations of the Existing System"),
        B("**Separate tools** make the user copy text between programs, give no record of which language, style or voice produced a file, and rarely run offline.",
          "**Cloud services** send the user's ideas to a third party, charge per use or per month and change without notice.",
          "**Narration of a story** needs the text to be in the language of the voice; a tool that does not check this reads text in the wrong language.",
          "**None of them** tells the user how intelligible the speech is or how long it takes; the speed and the error rate are rarely measured in the same place as the product.",
          "**The first plain interface** was a single page with no search, sorting, detail view or charts."),
        H2("4.3 Proposed System"),
        P("StoryVox joins the steps into one local pipeline. The user types a story idea and chooses a language, a style and a length. The service builds a prompt, asks the Qwen3-0.6B language model for a title and a story, "
          "stores them, splits the text into sentence-sized chunks and narrates each chunk with the VITS checkpoint of the chosen language, joins the audio and stores it as a WAV file. "
          "When the language model is unavailable or returns too little text, an offline composer writes a prompt-conditioned story instead, and when the neural checkpoint is unavailable or silent, the operating-system voice narrates. "
          "A History page keeps every story and its audio, and an Evaluation page runs a measurement loop that transcribes the narration with Whisper and reports error rates, similarity and speed."),
        FIG(F.diag("02_high_level_workflow.png"), "High-level workflow of StoryVox from the story idea to the stored narration and the evaluation.", 5.8),
        P("Two design rules shape the proposed system. First, **the model id is always recorded**: each story row and each audio row says which model produced it (`Qwen/Qwen3-0.6B` or `storyvox-local-fallback-v1`; `facebook/mms-tts-*` or `system-tts-offline-fallback`), "
          "so a fallback can never pass as the neural model. Second, **nothing is pre-filled**: every number on the Evaluation page is computed at the moment the evaluation runs, and a value that cannot be computed is shown as a dash, not as zero."),
        P("The proposed system does not translate: the objectives in the batch document speak of translating the story into the target language, but StoryVox asks the model to write directly in that language, and Chapter 8 measures how often it does so. "
          "It also has no voice, speed or reading-level control and no user rating form; these objectives are stated as not met in Chapters 8 and 9."),
        H2("4.4 Advantages of the Proposed System"),
        B("One interface for writing, listening, keeping and measuring a story, with a library that stores the text, the audio file, the model ids and the timing of every item.",
          "Local and private: stories and audio stay on the machine; no account, no subscription, no per-use cost.",
          "Fifteen languages offered; twelve narrated by a neural model whose measured speed is faster than real time on a CPU.",
          "An abstract speech provider with an ordered fallback chain and a silence check, so a failure of the neural model produces a clear result and never an empty audio file.",
          f"Honest measurement built into the product: round-trip error rates, similarity, ROUGE-L, latency and real-time factor, with the method named next to the score; {F.PYTEST_TOTAL} automated tests and scripts that regenerate every number in this report."),
        TAB("Manual practice and the first interface compared with StoryVox", ["Aspect", "Separate tools (typical practice)", "First plain interface", "StoryVox"],
            [["Interface", "Several programs", "One HTML page", "React application, 5 routed pages"],
             ["Story and voice in one step", "No", "Yes", "Yes"],
             ["Languages", "Depends on the tools", "15 offered", "15 offered, 12 with neural narration"],
             ["Library of past stories", "Manual files", "Basic list", "Searchable, sortable table; play, download, delete with confirmation"],
             ["Records which model produced an item", "No", "Yes (database)", "Yes, shown on screen"],
             ["Measured quality and speed", "No", "Evaluation call without charts", "Evaluation page with cards, chart, per-sample table and method notes"],
             ["Works offline after set-up", "Rarely", "Yes", "Yes"]],
            widths=[1.5, 1.6, 1.4, 2.0], align=["l", "l", "l", "l"], size=9.5),
        H2("4.5 Functional Requirements"),
        P("The requirements below are those the delivered system meets; each is tied to the page that offers it and the route(s) behind it."),
        TAB("Functional requirements", ["ID", "Requirement", "Page", "Route(s)"],
            [["FR-1", "Accept a story idea of 1 to 2,000 characters and reject an empty or over-long one with a plain message", "Studio", "POST /api/stories/generate"],
             ["FR-2", "Let the user choose one of 15 languages, one of 8 styles and one of 3 lengths", "Studio", "GET /api/languages, /api/meta"],
             ["FR-3", "Generate a title and a story with the language model, or with the offline composer when the model fails or returns fewer than 20 words", "Studio", "POST /api/stories/generate"],
             ["FR-4", "Save the story with its language, style, length, word count and generation time", "Studio", "POST /api/stories/generate"],
             ["FR-5", "Narrate the story chunk by chunk with the neural checkpoint of the language, falling back to the operating-system voice, and store a non-silent WAV file", "Studio, Story", "POST /api/stories/generate, POST /api/stories/{id}/synthesize"],
             ["FR-6", "Play the narration in the browser and download it as a WAV file; show duration, sample rate, model and real-time factor", "Studio, Story, History", "GET /api/audio/{id}"],
             ["FR-7", "List stories (up to 200) with title, language, style, words, date and audio status; open one story; regenerate its narration", "History, Story", "GET /api/stories, GET /api/stories/{id}"],
             ["FR-8", "Delete a story together with its audio rows and files", "History", "DELETE /api/stories/{id}"],
             ["FR-9", "Run an evaluation of 1 to 30 samples (the built-in set has 5 prompts), optionally for one language, with narration and story generation each skippable", "Evaluation", "POST /api/evaluations/run"],
             ["FR-10", "Report WER, CER, prompt-story similarity, ROUGE-L, story and narration latency and RTF; save the run as JSON and CSV and as a database row", "Evaluation", "POST /api/evaluations/run, GET /api/evaluations"],
             ["FR-11", "Report health, the story and recogniser model names, the styles and the lengths", "All pages", "GET /api/health, /api/meta"]],
            widths=[0.55, 3.15, 1.1, 1.7], align=["c", "l", "l", "l"], size=9),
        P("Input rules enforced by the service: the idea may not be empty or longer than 2,000 characters (`MAX_PROMPT_CHARS`); the language, style and length must be among the offered values, otherwise the answer is HTTP 422; "
          "an evaluation sample count must lie between 1 and 30; the story list limit lies between 1 and 200."),
        P("Requirements in the batch objectives that the delivered system does **not** meet: translation of the story into a target language; adjustable voice and speed; a reading-level control; "
          "collection of user ratings for coherence, translation quality and naturalness; and upload of reference audio. They appear in the table of objectives in Chapter 8 with their status."),
        H2("4.6 Non-Functional Requirements"),
        TAB("Non-functional requirements and measured values", ["ID", "Requirement", "Measured value or evidence"],
            [["NFR-1", "Performance: narration faster than real time on the target machine",
              f"Mean RTF {F.f2(F.MMS_MEAN_RTF)} for the {len(F.MMS_LANGS)} MMS languages; Short story with narration {F.f1(short['total_s'])} s, Long {F.f1(long_['total_s'])} s"],
             ["NFR-2", "Latency: ordinary routes answer within interactive time",
              f"Median {health['median_ms']:.1f} ms (health), {langs['median_ms']:.1f} ms (languages), {meta['median_ms']:.2f} ms (meta), {stories['median_ms']:.2f} ms (story list, empty) and {aud['median_ms']:.1f} ms (WAV download) over 10 to 30 calls each, 127.0.0.1"],
             ["NFR-3", "Correctness: silence is never served as speech", "Audio with RMS below 1e-4 is rejected and the next provider is tried; tested with a synthetic silent signal"],
             ["NFR-4", "Reliability: invalid input returns a clear error, not a crash", "422 for bad language, style, length or empty idea; 404 for unknown story or audio; 500 with a plain message for model failure; tested"],
             ["NFR-5", "Reproducibility: every reported number can be regenerated", "scripts/run_experiments.py, run_story_asr.py, measure_api.py and run_tests.py write experiments/*/metrics.json; docs/REPORT_FACTS.md is generated from them"],
             ["NFR-6", "Usability: guided and accessible", "Elapsed-time counter, character counter, confirmation before delete, light and dark theme, labelled controls; no accessibility audit and no user study were done"],
             ["NFR-7", "Privacy: stories stay on the machine", "Server bound to 127.0.0.1; SQLite and WAV files under data/; the only network use is the model download"],
             ["NFR-8", "Portability: runs on a standard computer", "Windows 11, Python 3.11, Node; no GPU; Docker files exist but were not tested"],
             ["NFR-9", "Maintainability: tested and modular", f"{F.PYTEST_PASSED} pytest tests ({F.PYTEST_API} API, {F.PYTEST_UNIT} unit) all passing in {F.TESTS['seconds']} s; models replaced by stubs in the API tests"]],
            widths=[0.65, 2.45, 3.4], align=["c", "l", "l"], size=9.5),
        P("Security is modest by design for a single-user tool. The service is bound to 127.0.0.1, the browser reaches it through the same origin (the Vite proxy in development, the FastAPI static route in production), so the application sets no cross-origin rules; "
          "there is no sign-in; the audio route serves only files whose records the server itself wrote; and the story text is rendered as text in the page. A deployment shared between users would need authentication, per-user storage and a request queue, which are listed as future scope."),
        H2("4.7 Hardware Requirements"),
        TAB("Hardware", ["Item", "Minimum we would suggest", "Used for the measurements"],
            [["Processor", "Any recent 4-core CPU", "Intel Core i5-12500, 12 logical threads"],
             ["Memory", "8 GB (the project guide's recommendation)", "15.7 GB; 3.7 to 4.9 GB resident was seen for the process holding the models"],
             ["Storage", "8 GB free (the project guide's figure) for models, packages and audio", "About 4.7 GB of models in the cache, on the system drive"],
             ["Graphics", "None", "No GPU used (`cuda: false`)"],
             ["Display and audio", "1280 x 800 and a speaker or headphones", "Screenshots at 1440 x 900"]],
            widths=[1.2, 2.5, 2.8], align=["l", "l", "l"], size=10),
        P("The suggested minimums are our estimates and were not tested; only the right-hand column was measured or observed."),
        H2("4.8 Software Requirements"),
        TAB("Software", ["Component", "Version used", "Role"],
            [["Python", F.TESTS["python"], "Language of the service and the experiments"],
             ["PyTorch / Transformers", "2.14.1 / 5.20.2", "Model execution; text-generation, speech and recogniser pipelines"],
             ["FastAPI / Uvicorn / Pydantic", "0.143.3 / 0.54.0 / 2.14.1", "REST service and validation"],
             ["SQLAlchemy / SQLite", "2.0.30 / bundled", "Story, audio and evaluation storage"],
             ["jiwer / rouge-score / sentence-transformers", "4.0.0 / 0.1.2 / 6.2.0", "WER and CER, ROUGE-L, similarity"],
             ["soundfile / NumPy / pyttsx3", "0.14.0 / 1.26.4 / 2.99", "WAV input and output, arrays, operating-system voice"],
             ["ffmpeg, uroman, langdetect", "portable build / 1.3.1.1 / 1.0.9", "Whisper file reading (not declared), Korean romanisation (not declared), language check in the experiments"],
             ["React 19, Vite 8, Recharts 3", "as in package.json", "Web application"],
             ["pytest / httpx", "8.2.0 / 0.28.1", "Automated tests"],
             ["Operating system / browser", "Windows 11 Pro / Chrome", "Platform used; Playwright drove Chrome for the screenshots"]],
            widths=[2.2, 1.6, 2.7], align=["l", "l", "l"], size=10),
        H2("4.9 User Roles and System Constraints"),
        P("There is one role, the **user** (a storyteller, parent, teacher or evaluator) who writes, listens, manages the library and runs the evaluation; there is no sign-in, because the product is a local single-user tool. "
          "A second role, the **developer or evaluator**, runs the scripts and tests that import the same `app/` package. The Hugging Face hub and the operating-system speech engine are supporting systems, not users."),
        B("**Single user and no queue.** Requests are served one worker at a time; a generation request holds its worker for about 20 s to a minute.",
          "**First use needs the internet.** Each model is downloaded once; the Italian, Chinese and Japanese checkpoints that the configuration names do not exist, so those languages use the operating-system voice, which on the test machine had only English voices.",
          "**Language fidelity.** The story language is requested in the prompt only; a 0.6 B model often answers in English, and an English text read by a foreign-language voice is unintelligible (Chapter 8).",
          f"**Story length.** Short, Medium and Long mean 220, 420 and 700 new tokens; the stories measured in the length experiment had {short['words']}, {medium['words']} and {long_['words']} words.",
          "**Evaluation.** The built-in set has five prompts in four languages; for story-length audio the recogniser needs chunked decoding, which the shipped code does not use."),
    ]
