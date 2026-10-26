"""Chapter 5: System Design for StoryVox.

build_docs.doc12 renders blocks()[1:], so the first element must be the chapter H1.
Line counts are measured from the code at build time; diagrams are drawn by make_diagrams.py.
"""

import os

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .diagram_index import DIAGRAMS
from .refs import N as cite

_D = {k: (t, f, cap, txt) for k, t, f, cap, txt in DIAGRAMS}


def _lines(rel):
    path = os.path.join(F.CODE, rel)
    with open(path, encoding="utf-8", errors="ignore") as fh:
        return sum(1 for _ in fh)


def _tree_lines(rel, exts):
    total = 0
    for root, _, files in os.walk(os.path.join(F.CODE, rel)):
        for f in files:
            if f.endswith(exts):
                with open(os.path.join(root, f), encoding="utf-8", errors="ignore") as fh:
                    total += sum(1 for _ in fh)
    return total


def _dg(key, width=5.4):
    """Diagram figure block, or nothing if the file has not been drawn yet."""
    t, f, cap, _ = _D[key]
    path = F.diag(f)
    return [FIG(path, cap, width)] if os.path.exists(path) else []


_DROP_P = ("The deliberate gaps", "Three decisions about this structure", "Four design rules", "Every design has costs", "Two further choices",
           "The model itself is", "Three files persist")
_DROP_TAB = ("Principal design decisions", "Console pages and the endpoints")


def _trim(out):
    """Report variant: same 12 diagrams, but no design screenshots (Chapter 8 shows the screens) and fewer tables."""
    res = []
    for b in out:
        if b[0] == "p" and b[1].startswith(_DROP_P):
            continue
        if b[0] == "tab" and b[1].startswith(_DROP_TAB):
            continue
        if b[0] == "fig" and os.sep + "screenshots" + os.sep in b[1]:
            continue
        res.append(b)
    return res


def blocks():
    a, w = F.API_PORT, F.WEB_PORT
    shot = lambda n, cap, base=5.0, mh=3.6: [FIG(F.shot(n), cap, F.shot_w(F.shot(n), base, mh))] if os.path.exists(F.shot(n)) else []  # noqa: E731
    short, medium, long_ = F.LENGTH_SCALING
    mods = [
        ("`app/main.py`", "app/main.py", "Creates the FastAPI application, mounts the built web application and the single-page-app fallback route"),
        ("`app/config.py`", "app/config.py", "Settings read from the environment; the 15 languages with their checkpoints, 8 styles and 3 lengths"),
        ("`app/database.py`", "app/database.py", "SQLite engine, session factory, table creation and creation of the data folders"),
        ("`app/models/__init__.py`", "app/models/__init__.py", "ORM classes Story, AudioOutput and Evaluation"),
        ("`app/schemas.py`", "app/schemas.py", "Pydantic request and response models (generate request, story, audio, evaluation run)"),
        ("`app/api/routes.py`", "app/api/routes.py", "The 11 REST routes, validation and error mapping"),
        ("`app/services/story_generator.py`", "app/services/story_generator.py", "Prompt builder, lazily loaded Qwen3 pipeline, output parser, offline composer"),
        ("`app/services/tts_service.py`", "app/services/tts_service.py", "TTSProvider interface, MMS and operating-system providers, WAV writing"),
        ("`app/services/asr_service.py`", "app/services/asr_service.py", "Lazily loaded Whisper pipeline for the evaluation"),
        ("`app/services/evaluation_service.py`", "app/services/evaluation_service.py", "Built-in prompts, the measurement loop, JSON and CSV output"),
        ("`app/utils/__init__.py`", "app/utils/__init__.py", "Word count, reading time, sentence chunking, file-name helpers, directory guard"),
        ("`app/utils/audio.py`", "app/utils/audio.py", "WAV read, write, resample, join with pauses, RMS and silence test"),
        ("`app/utils/metrics.py`", "app/utils/metrics.py", "WER, CER, TF-IDF cosine and ROUGE-L"),
    ]
    mod_rows = [[n, str(_lines(rel)), d] for n, rel, d in mods]
    fe_lines, test_lines = _tree_lines("frontend/src", (".jsx", ".js", ".css")), _tree_lines("tests", (".py",))
    mod_rows.append(["`frontend/src/`", f"{fe_lines:,}", "React 19 application: 5 pages, in-house UI kit, charts, API client, theme and motion helpers"])
    mod_rows.append(["`tests/`", str(test_lines), f"{F.PYTEST_TOTAL} pytest tests ({F.PYTEST_API} API tests, {F.PYTEST_UNIT} unit and edge-case tests)"])
    mod_rows.append(["`scripts/`", "-", "Experiment, measurement and screenshot scripts; the smoke test, the data download and the evaluation command line"])

    routes = [
        ["GET", "/api/health", "Liveness check: status, application name, whether CUDA is available, server time", "-"],
        ["GET", "/api/languages", "The 15 supported languages with their speech checkpoints", "-"],
        ["GET", "/api/meta", "Styles, lengths, story model name and recogniser model name", "-"],
        ["POST", "/api/stories/generate", "Validate, generate a story, save it and (if asked) narrate it; returns the story with its audio record", "422 empty, over-long, unknown language, style or length; 500 model failure"],
        ["POST", "/api/stories/{id}/synthesize", "Narrate a saved story again and add an audio record", "404 unknown story; 422; 500 narration failure"],
        ["GET", "/api/stories", "Stories, newest first, with an audio flag; `limit` 1 to 200 (default 50)", "422 limit out of range"],
        ["GET", "/api/stories/{id}", "One story with reading time, listening time and the latest audio", "404"],
        ["DELETE", "/api/stories/{id}", "Delete the story, its audio rows and the WAV files inside the audio folder", "404"],
        ["GET", "/api/audio/{id}", "Stream the stored WAV file as audio/wav with a download file name", "404 record or file missing; 400 invalid stored path"],
        ["GET", "/api/evaluations", "Saved evaluation runs (50 newest rows; if the table is empty, up to 20 JSON files on disk)", "-"],
        ["POST", "/api/evaluations/run", "Run the measurement loop (`samples` 1 to 30, optional language, skip narration, skip story) and save the result", "422 unknown language; 500 failure"],
    ]

    out = [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        P("This chapter describes how StoryVox is put together: the architecture and workflow, the data flow, the UML and data design, the modules, the API and the user interface. "
          "The diagrams were drawn from the code in `app/`; the complete set, each with a longer explanation, is also in the Block Diagrams document. "
          "A note on scope: the product is a single-user local application. It has no accounts, no queue and no scheduler, and these absences are design choices that the sections below explain rather than hide."),

        H2("5.1 Design goals and architecture"),
        P("Five goals shaped the design. First, **local first**: after the one-time model download nothing leaves the machine, and every story and narration is stored in a SQLite file and a folder of WAV files. "
          "Second, **truthful provenance**: every story row and every audio row records the identifier of the model that produced it, so a fallback can never pass as the neural model. "
          "Third, **never serve silence**: the narration service rejects empty or silent audio and moves to the next provider; if all fail the request returns an error and the story is kept without audio. "
          "Fourth, **honest evaluation**: every number on the Evaluation page is computed at run time from real outputs, and a number that cannot be computed is shown as a dash. "
          "Fifth, **thin routes**: the routes validate input and map errors, and the work lives in four service modules, so the same functions serve the web application, the test suite and the experiment scripts."),
        *_dg("arch", 5.6),
        P(f"In development the React application is served by Vite on port {w} and the Vite proxy forwards every `/api` request to the FastAPI application on 127.0.0.1:{a}; in production `npm run build` writes `frontend/dist`, "
          "and the same FastAPI process serves the built files, with a fallback route that returns `index.html` for any path that is not an API route or an asset, so the browser always sees one origin. "
          "For that reason the application defines no cross-origin rules. The application has one router with 11 routes. Settings come from environment variables (read on every instantiation so that tests can isolate them), "
          "the models are loaded lazily on first use under a lock and cached in module variables, and a request that arrives while a model is loading simply waits for the lock."),
        P("The deliberate gaps in this architecture are worth stating. There is no authentication because the tool runs on one machine for one person, and the server is bound to 127.0.0.1. "
          "There is no job queue: a generation request runs inside the request, so the browser waits (about 22 s for a Short story on this CPU), and a second request waits for the same processor. "
          "SQLite is opened with `check_same_thread=False` and every request uses its own session, which is adequate for one user and was not tested under concurrent load. "
          "The configuration also defines `MAX_AUDIO_UPLOAD_MB` and a dataset folder that no route uses; they are leftovers from the reference-audio objective that was not built."),

        H2("5.2 High-level workflow"),
        *_dg("flow", 5.6),
        P("The workflow has seven stages. **Validate**: the route rejects an empty or over-long idea and an unknown language, style or length. **Prompt**: the service builds one instruction that names the style, the language, the paragraph target (3, 5 or 8) and the rule that the first line must start with `Title:`. "
          f"**Generate**: the language model samples at temperature 0.8 and top-p 0.9 up to 220, 420 or 700 new tokens; if it cannot be loaded or returns fewer than 20 words, the offline composer writes the story. "
          "**Save**: the title, body, word count and generation time become a `stories` row. **Narrate**: the text is cut into chunks of at most 380 characters at sentence ends, every chunk is synthesised, normalised to a peak of 0.9 and joined with 0.25 s pauses, and the WAV file and an `audio_outputs` row are written. "
          "**Play and manage**: the browser plays and downloads the audio; History lists, opens, re-narrates and deletes. **Evaluate**: the Evaluation page runs the loop of Section 5.6."),
        P("Two properties of this workflow matter for the results in Chapter 8. There is no translation step: the language is a word in the prompt and nothing checks that the output is in that language. "
          "And narration depends only on the language code, not on the language of the text, so a story that came out in English is read by the checkpoint of whatever language was requested."),

        H2("5.3 Data flow diagrams"),
        H3("5.3.1 Level 0: context"),
        *_dg("dfd0", 4.8),
        P("At level 0 StoryVox is one process with three external entities. The **user** supplies story ideas, choices and evaluation requests and receives stories, audio, the story list and metrics. "
          "The **Hugging Face hub** is the source of model weights and tokenizers; it is contacted only when a model is not yet in the local cache. The **operating-system speech engine** receives text and returns audio only when the neural checkpoint cannot be used. "
          "No analytics service and no cloud storage appear because the product does not use them."),
        H3("5.3.2 Level 1: five processes"),
        *_dg("dfd1", 5.4),
        P("Level 1 shows the five processes and four data stores. **1.0 Validate** checks the request. **2.0 Generate story** writes the title, body and word count to D1 (stories). **3.0 Synthesise narration** writes the WAV file to D3 (audio folder) and the duration, model id, synthesis time and real-time factor to D2 (audio_outputs). "
          "**4.0 Manage history** reads D1, D2 and D3 to list, open, stream and delete stories and to regenerate narration. **5.0 Run evaluation** calls processes 2.0 and 3.0 on built-in prompts, transcribes the audio and writes the metrics to D4 (one evaluations row plus a JSON and a CSV file)."),
        H3("5.3.3 Level 2: narration"),
        *_dg("dfd2", 5.4),
        P("Narration is expanded to level 2 because it is where the product can fail and where most of the measured time goes. Seven sub-processes take the story text to a stored WAV file: chunking, loading the checkpoint once and caching it, running the VITS model on each chunk, normalising and joining, rejecting empty or silent audio, the operating-system fallback, and computing the duration and real-time factor. "
          "A silent result, an empty result or any load or inference error sends the text to the fallback; the fallback's result is resampled to 16 kHz so that the rest of the system sees one format."),

        H2("5.4 UML design"),
        H3("5.4.1 Class diagram"),
        *_dg("uml", 5.6),
        P("Most of the code base is modules of functions, which suits a pipeline in which each step takes text or audio and returns text or audio; the diagram draws each module as a class-like box. "
          "The real classes are the abstract `TTSProvider` with its two implementations `MMSTTSProvider` and `SystemTTSProvider`, the Pydantic schemas of the API, and the three ORM classes. "
          "`Story` owns zero or more `AudioOutput` objects through a cascading relationship; `Evaluation` stands alone and keeps its metrics in one JSON column."),
        TAB("Principal modules and the data they pass on.",
            ["Module", "Takes", "Returns"],
            [["story_generator", "Idea, language code, style, length", "Title, body, model id, elapsed seconds"],
             ["tts_service", "Story text, language code", "Relative WAV path, duration, sample rate, model id, synthesis time, RTF"],
             ["asr_service", "WAV path, language code", "Transcript text"],
             ["evaluation_service", "Sample count, optional language, skip flags", "Metrics dictionary with averages and per-sample rows; JSON and CSV files"],
             ["utils.metrics", "Reference and hypothesis text", "WER, CER, TF-IDF cosine, ROUGE-L"],
             ["utils.audio", "Waveform arrays, WAV paths", "Joined audio, resampled audio, silence decision"]],
            widths=[1.7, 2.3, 2.5], align=["l", "l", "l"], size=9.5),
        H3("5.4.2 Sequence diagram"),
        *_dg("seq", 5.4),
        P("The sequence follows `POST /api/stories/generate` with narration. The route validates the request, calls `generate_story_text`, inserts the `stories` row and then, if `synthesize` is true, calls `synthesize_story_narration` and inserts the `audio_outputs` row. "
          "If narration raises an error the story is still saved and returned without audio so that it can be narrated later through `POST /api/stories/{id}/synthesize`. "
          f"The measured end-to-end time of this call for a Short story was {F.f1(short['total_s'])} s in the length experiment, of which {F.f1(short['gen_s'])} s was generation, and the browser then fetches the audio with `GET /api/audio/{{id}}`."),
        H3("5.4.3 Use-case diagram"),
        *_dg("usecase", 4.8),
        P("The product has no accounts, so the two actors are roles of the same local user. The story creator works in the Studio: enters an idea, chooses language, style and length, generates, narrates, plays and downloads. "
          "The library and evaluation user works on History, Story and Evaluation: browses, opens, regenerates narration, deletes, runs an evaluation and reads the metrics. "
          "The model cache and the operating-system speech engine are supporting systems. Translation, rating, voice choice, speed control and reference-audio upload are not use cases of this build."),

        H2("5.5 Database design"),
        *_dg("er", 5.4),
        P("The database `data/storyvox.db` has three tables created by SQLAlchemy at start-up. The tables and their columns are listed below. "
          "A story can have several narrations because regenerating narration adds a row instead of replacing one."),
        TAB("Tables of the SQLite database.", ["Table", "Columns", "Notes"],
            [["stories", "id, prompt, title (300), story_text, language_code, language_name, style, length_option, word_count, created_at, generation_time_seconds", "One row per generated story; title and body are stored as the parser produced them"],
             ["audio_outputs", "id, story_id (foreign key), file_path, duration_seconds, sample_rate, tts_model, synthesis_time_seconds, rtf, created_at", "One row per narration; `tts_model` is the speech checkpoint or `system-tts-offline-fallback`"],
             ["evaluations", "id, evaluation_type, language_code, sample_count, metrics_json (JSON), created_at", "Stand-alone; the same payload is written to data/evaluations as JSON and CSV"]],
            widths=[1.2, 3.4, 1.9], align=["l", "l", "l"], size=9.5),
        P("The foreign key is declared with `ON DELETE CASCADE` and the ORM relationship cascades deletes, but SQLite does not enforce foreign keys unless the pragma is switched on, and the application does not switch it on; "
          "deleting a story therefore removes its audio rows through the ORM, not through the database, and the delete route also removes the WAV files. "
          "Three folders persist across restarts: `data/audio` (WAV files), `data/evaluations` (JSON and CSV) and `data/datasets` (created at start-up and not used by any route). The `.gitignore` excludes the database, the audio and the evaluation files."),

        H2("5.6 Core algorithm design"),
        *_dg("algo", 5.4),
        P("The story algorithm is a short chain with two guards. Input guards reject an unknown language, style or length, an empty idea and an idea over 2,000 characters before any model runs. "
          "The output guard is the 20-word rule: a body shorter than 20 words, or any exception in the pipeline, switches to the offline composer, which always returns a story that quotes the idea, and the model id returned to the caller says which path produced the text. "
          "The parser takes a `Title:` line (or a short first line) as the title and the rest as the body; when neither exists the title is `Untitled Story`. "
          "A consequence, measured in Chapter 8, is that the guard checks length only, not language, not instruction echo and not narrative quality."),
        *_dg("tts_eval", 5.4),
        P("On the left of the second flowchart, narration tries the neural provider first and the operating-system provider second, and applies the silence test to whatever comes back; the real-time factor is synthesis time divided by audio duration. "
          "On the right, the evaluation takes the first n of five built-in prompts (English adventure, English bedtime, French fantasy, German inspirational, Spanish mystery), generates and narrates a story for each, computes the prompt-story similarity and ROUGE-L, transcribes the audio with Whisper and computes WER and CER against the story text. "
          "If the recogniser raises an error the message is stored in the row and WER and CER stay empty, which is exactly what happened for story-length audio in this project (Chapter 8)."),
        *_dg("model", 5.4),
        P("StoryVox trains no model. The Qwen3-0.6B decoder continues the prompt token by token; each MMS checkpoint is a VITS model whose text encoder, duration predictor and flow produce a latent representation that a HiFi-GAN decoder turns into a 16 kHz waveform " + cite("vits", "mms") + "; "
          "Whisper-small and the multilingual MiniLM encoder are used only by the evaluation " + cite("whisper", "sbertm") + ". Supporting a language means mapping its code to a checkpoint in `app/config.py`, which is also where the three non-existent checkpoints (Italian, Chinese, Japanese) are named."),

        H2("5.7 Module design"),
        P("The code is split so that each file has one reason to change. Line counts below were measured from the repository."),
        TAB("Modules, sizes and responsibilities.", ["Module", "Lines", "Responsibility"], mod_rows, widths=[2.2, 0.6, 3.7], align=["l", "r", "l"], size=9.5),
        P("Three decisions about this structure are worth recording. The routes do not contain pipeline logic: `routes.py` validates, calls a service and maps exceptions to status codes. "
          "The experiment scripts import the same `app.services` functions as the API, so the numbers in Chapter 8 come from the product's code and not from a parallel implementation. "
          "And the web application has its own small UI kit (buttons, cards, tables, tabs, toasts, charts), so the pages contain layout and calls and no styling."),

        H2("5.8 API design"),
        P("All routes live under `/api`. Reads are GET and actions are POST or DELETE. Failures return the FastAPI `detail` string, which the web application shows verbatim, so messages are written for the user: 'Please enter a story idea.' is what a 422 says. "
          "The status codes follow one rule: 422 means the request was understood but a value is not acceptable, 404 means a story, an audio record or a file is missing, and 500 means a model or the speech engine failed; the detail never contains a stack trace, which goes to the server log."),
        TAB("The 11 routes of the StoryVox API (plus the single-page-app fallback).", ["Method", "Path", "Purpose", "Errors"], routes, widths=[0.7, 1.55, 3.0, 1.25], align=["c", "l", "l", "l"], size=8.5),
        P("`POST /api/stories/generate` is the main route. Its body has the idea, the language code, the style, the length option and a `synthesize` flag (default true). The response is a `StoryResponse` with the story, its word count, reading and listening time, the generation time and, when narration ran, an `audio` object whose `file_path` is the URL `/api/audio/{id}`. "
          "Interactive documentation is generated by FastAPI at `/docs`."),

        H2("5.9 User interface design"),
        P("The web application has five pages: a public Home page, the Studio, History, a Story page and Evaluation, plus a not-found page. Pages are loaded lazily so that the Home page does not pay for the charts. "
          "The visual language is a flat, high-contrast grid with thick borders, one accent colour and monospace labels; a light and a dark theme are available from every page, and the choice is kept in browser storage guarded by try and catch."),
        TAB("Application pages and the endpoints they use.", ["Page", "Route", "Endpoints used"],
            [["Home", "/", "None (public page)"],
             ["Studio", "/studio", "GET /api/languages, /api/meta; POST /api/stories/generate; GET /api/stories/{id} (to restore ?story=)"],
             ["History", "/stories", "GET /api/stories?limit=100, /api/audio/{id}; DELETE /api/stories/{id}; the shell reads /api/languages, /api/meta, /api/health once"],
             ["Story", "/stories/:id", "GET /api/stories/{id}, /api/audio/{id}; POST /api/stories/{id}/synthesize"],
             ["Evaluation", "/evaluation", "GET /api/evaluations; POST /api/evaluations/run"]],
            widths=[1.2, 1.4, 3.9], align=["l", "l", "l"], size=9.5),
        P("Four design rules were applied to every working page. Each page opens with its purpose. Long actions show a busy state with an elapsed-time counter and finish with a notice. "
          "Numbers that are missing are shown as a dash with the reason ('Needs narration + transcription'), never as zero. Errors from the API are shown in a panel with a retry button, and deleting asks for confirmation and says that the audio will be removed too. "
          "Chapter 8 shows every page with real data; the three screens below illustrate the design itself."),
        *shot("02_studio_empty.png", "Studio before generating: idea box with character counter, language, style and length selectors and the automatic-narration option.", 5.0, 3.5),
        *shot("04_history.png", "History page: searchable, sortable story library with play, download and delete actions.", 5.0, 3.5),
        *shot("06_evaluation.png", "Evaluation page: run form, run selector and metric cards; WER and CER show a dash because the recogniser could not process story-length audio.", 5.0, 3.5),

        H2("5.10 Design decisions and trade-offs"),
        P("Every design has costs. The table records the main decisions, what each bought and what it cost, so that the limitations in Chapter 9 can be traced back to a choice and not to an accident."),
        TAB("Principal design decisions.",
            ["Decision", "Reason", "Cost"],
            [["Cascade of pretrained models instead of training one", "No training data, hardware or time were needed; each part can be replaced; the base paper's end-to-end systems need a GPU for days", "Quality is that of the weakest part; a 0.6 B model rarely writes in the requested language"],
             ["Ask the model for the language in the prompt, with no translation step", "One model call; simple code", "No check that the output is in the language; mismatched text is narrated by the wrong voice"],
             ["Abstract `TTSProvider` with an ordered fallback chain", "A missing checkpoint or a silent result never becomes an empty file; new engines can be added", "The fallback voice may not speak the language (English voices only on the test machine) and still counts as narration"],
             ["Run generation inside the request", "No queue, worker or job table to build", "The browser waits 20 s to a minute; one request at a time"],
             ["Lazy model loading under a lock", "Fast start-up; memory used only when needed", "The first request is slow (cold call 42 s versus about 30 s warm)"],
             ["SQLite and WAV files in `data/`", "No server to install; easy to back up and delete", "Single user; foreign keys not enforced by the database"],
             ["Report failures as measured", "The aim is to learn what the pipeline really does", "The headline numbers are modest"]],
            widths=[2.0, 2.4, 2.1], align=["l", "l", "l"], size=9),
        P("Two further choices concern what was left out. Translation, voice and speed control, user rating and reference-audio upload were not built, although the batch objectives mention them; the design offers the extension point for the voice (a new `TTSProvider`) but nothing else. "
          "And the evaluation uses a plain recogniser call that fails above 30 s of audio; the fix is a chunked call, which the experiment script uses and the product does not yet."),
    ]
    return _trim(out) if F.REPORT else out
