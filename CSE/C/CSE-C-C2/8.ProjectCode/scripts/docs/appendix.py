"""Appendices A (important code), B (installation and user guide) and C (additional screens)."""
import ast
import os
import textwrap

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, N, P, PAIR, TAB


# ---------------------------------------------------------------------------- helpers (self-contained: cut from the real source files)
def _read(rel):
    with open(os.path.join(F.CODE, rel), encoding="utf-8") as f:
        return f.read()


def fn(rel, name, doc=False):
    """Source of a function, a class ('Class') or a method ('Class.method') exactly as it stands (docstrings removed unless doc=True), dedented."""
    text = _read(rel)
    lines = text.split("\n")
    tree = ast.parse(text)
    parts = name.split(".")
    scope = tree.body
    node = None
    for part in parts:
        node = next(n for n in scope if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == part)
        scope = node.body
    start = min([d.lineno for d in node.decorator_list] + [node.lineno])
    body = lines[start - 1:node.end_lineno]
    if not doc and isinstance(node, ast.FunctionDef) and ast.get_docstring(node):
        d = node.body[0]
        body = lines[start - 1:d.lineno - 1] + lines[d.end_lineno:node.end_lineno]
    return textwrap.dedent("\n".join(body))


def between(rel, first, last):
    """Lines from the first line containing `first` to the first later line containing `last` (inclusive), dedented."""
    lines = _read(rel).split("\n")
    i = next(k for k, l in enumerate(lines) if first in l)
    j = next(k for k in range(i, len(lines)) if last in lines[k])
    return textwrap.dedent("\n".join(lines[i:j + 1]))


# ------------------------------------------------------------------------------ Appendix A
def _intro():
    return [
        H1("APPENDIX A: IMPORTANT CODE"),
        P("The key functions are copied from `8.ProjectCode` as they stood when the results were measured; docstrings are removed to save space (the full files are in the repository). "
          "The prompt, chunking and fallback logic are also explained in Chapter 6, and the evaluation formulas in Chapter 6 and Chapter 8."),
    ]


def _common():
    return _intro() + [
        H2("A.1 Prompt construction and output parsing (`app/services/story_generator.py`)"),
        P("The prompt names the language, style and paragraph budget in plain text and is sent to the model without a chat template; the parser takes the first short line as the title and treats the rest as the story body."),
        CODE(fn("app/services/story_generator.py", "build_prompt") + "\n\n" + fn("app/services/story_generator.py", "_parse_model_output"), 7.6),
        H2("A.2 Story generation with fallback (`app/services/story_generator.py`)"),
        P("If the pipeline cannot be loaded or the text has fewer than 20 words, the offline composer answers and the returned model name says so."),
        CODE(fn("app/services/story_generator.py", "generate_story_text"), 7.6),
        H2("A.3 Splitting text for the speech model (`app/utils/__init__.py`)"),
        P("The speech model is run on pieces of at most 380 characters, cut at sentence ends (including the Devanagari danda) and, for a single very long sentence, at the character limit."),
        CODE(fn("app/utils/__init__.py", "chunk_text"), 7.6),
        H2("A.4 MMS narration (`app/services/tts_service.py`)"),
        P("Each chunk is synthesised by the VITS checkpoint of the language, peak-normalised, joined with a 0.25 s pause and checked for silence before it is returned."),
        CODE(fn("app/services/tts_service.py", "MMSTTSProvider.synthesize"), 7.6),
        H2("A.5 Provider chain and saved audio (`app/services/tts_service.py`)"),
        CODE(fn("app/services/tts_service.py", "synthesize_story_narration"), 7.4),
        H2("A.6 Speech recognition and error rates (`asr_service.py`, `metrics.py`)"),
        P("Whisper transcribes the narration in the requested language; the same functions score the round trip. The recogniser call is the one that rejects audio longer than 30 seconds (Chapter 8)."),
        CODE(fn("app/services/asr_service.py", "transcribe_wav") + "\n\n" + fn("app/utils/metrics.py", "_levenshtein") + "\n\n" + fn("app/utils/metrics.py", "wer") + "\n\n" + fn("app/utils/metrics.py", "cer"), 7.6),
        H2("A.7 The generate route (`app/api/routes.py`)"),
        CODE(fn("app/api/routes.py", "generate_story"), 7.4),
        H2("A.8 Database models (`app/models/__init__.py`)"),
        CODE(fn("app/models/__init__.py", "Story") + "\n\n" + fn("app/models/__init__.py", "AudioOutput") + "\n\n" + fn("app/models/__init__.py", "Evaluation"), 7.6),
        H2("A.9 The evaluation run (`app/services/evaluation_service.py`)"),
        CODE(between("app/services/evaluation_service.py", "for item in prompts:", "per_sample.append(row)"), 7.4),
        H2("A.10 Round-trip normalisation in the experiment harness (`scripts/run_experiments.py`)"),
        P("The measured WER and CER in Chapter 8 are reported raw (the application's own functions) and normalised with this function: NFKC, lower case, punctuation and symbols removed, and spaces removed for Chinese and Japanese."),
        CODE(fn("scripts/run_experiments.py", "norm"), 7.6),
    ]


def _report():
    return _intro() + [
        H2("A.1 Prompt construction and output parsing (`story_generator.py`)"),
        CODE(fn("app/services/story_generator.py", "build_prompt") + "\n\n" + fn("app/services/story_generator.py", "generate_story_text"), 7.0),
        H2("A.2 Splitting text for the speech model (`app/utils/__init__.py`)"),
        CODE(fn("app/utils/__init__.py", "chunk_text"), 7.0),
        H2("A.3 MMS narration (`tts_service.py`)"),
        CODE(fn("app/services/tts_service.py", "MMSTTSProvider.synthesize"), 7.0),
        H2("A.4 Speech recognition (`asr_service.py`)"),
        CODE(fn("app/services/asr_service.py", "transcribe_wav"), 7.0),
        H2("A.5 The generate route (`routes.py`)"),
        CODE(fn("app/api/routes.py", "generate_story"), 6.8),
    ]


def code_blocks():
    return _report() if F.REPORT else _common()


# ------------------------------------------------------------------------------ Appendix B
def guide_blocks():
    out = [
        H1("APPENDIX B: INSTALLATION AND USER GUIDE"),
        H2("B.1 Requirements"),
        TAB("Requirements", ["Item", "Needed"],
            [["Operating system", "Windows 10/11 (run.bat); the Python and Node commands also work on Linux and macOS. The measurements were made on Windows 11"],
             ["Python", "3.11 or newer on PATH (measured with 3.11.9, torch 2.14.1, transformers 5.20.2)"],
             ["Node.js and npm", "Node 20 or newer (the interface uses React 19 and Vite 8; measured with Node 24)"],
             ["Python packages", "`requirements.txt` (23 packages: FastAPI, SQLAlchemy, torch, transformers, sentence-transformers, jiwer, pyttsx3 and others)"],
             ["ffmpeg", "On PATH. Not listed in `requirements.txt`, but Whisper cannot read the WAV files without it: without ffmpeg every evaluation sample records an error and WER and CER stay empty"],
             ["uroman", "`pip install uroman`. Needed for Korean narration (the Korean MMS tokenizer expects romanised text); not listed in `requirements.txt`"],
             ["Disk and memory", "Several gigabytes of disk for model weights (downloaded on the first run) and 8 GB of RAM recommended; the measurement machine had 15.7 GB"],
             ["Internet", "Required once, to download Qwen3-0.6B, Whisper-small, MiniLM and the MMS checkpoints of the languages used; cached afterwards"]],
            widths=[1.5, 5.1], align=["l", "l"], size=10),
        H2("B.2 Installation and start with run.bat"),
        N("Copy or clone the project so that `8.ProjectCode` is on a local disk.",
          "Double-click `run.bat`. It rebuilds `.venv` if the existing one points at a missing Python, installs `requirements.txt` and, if `frontend\\node_modules` is missing, runs `npm install`.",
          "It starts the API on port 8402 in one window (`uvicorn app.main:app`) and the Vite web app on port 5402 in another, and opens `http://localhost:5402`. Keep both windows open.",
          "The first story downloads the story model and the speech model of its language; allow 10 to 30 minutes on a slow connection. Later runs use the cache.",
          "During the documentation run `run.bat` was not used: the project's `.venv` pointed at a Python version that was no longer installed and the disk had too little free space to rebuild it, so the servers were started manually (B.3) with the system Python."),
        H2("B.3 Manual start"),
        CODE("# API (from 8.ProjectCode)\npip install -r requirements.txt\npip install uroman            # Korean narration\npython -m uvicorn app.main:app --host 127.0.0.1 --port 8402\n\n"
             "# web app, development server on 5402 (from 8.ProjectCode/frontend)\nnpm install\nnpm run dev\n\n"
             "# or one port: build once, then the API serves the app at http://127.0.0.1:8402\nnpm run build", 8.5),
        H2("B.4 Configuration (`.env`)"),
        TAB("Settings read from .env (defaults in .env.example)", ["Key", "Meaning"],
            [["STORY_MODEL, ASR_MODEL, TTS_MODEL", "Hugging Face ids of the story model (default Qwen/Qwen3-0.6B), the recogniser (openai/whisper-small) and the default speech checkpoint"],
             ["STORY_MAX_NEW_TOKENS_SHORT / MEDIUM / LONG", "Token budgets 220, 420 and 700"],
             ["STORY_TEMPERATURE, STORY_TOP_P", "Sampling settings, 0.8 and 0.9"],
             ["MAX_PROMPT_CHARS", "Longest accepted story idea (2000)"],
             ["PORT, FRONTEND_PORT, HOST", "API port 8402, web port 5402, host 127.0.0.1"],
             ["STORYVOX_DB_PATH, STORYVOX_AUDIO_DIR, STORYVOX_EVAL_DIR", "Where the SQLite file, the WAV files and the evaluation JSON/CSV are written (data/storyvox.db, data/audio, data/evaluations)"]],
            widths=[2.5, 4.1], align=["l", "l"], size=10),
        H2("B.5 Using the application"),
        TAB("Pages and what to do on them", ["Page", "What to do", "Output"],
            [["Home", "Read the summary: 15 languages, 8 styles, 3 lengths, the story model; press Write a story", "Landing page with the language ticker"],
             ["Studio", "Type the story idea, choose language, style and length, keep or clear Narrate the story automatically, press Generate story", "The story, its tags, an audio player with Download WAV and Regenerate narration"],
             ["History", "Search or sort the library; View, Play, Download or Delete a story", "Table of every saved story with an audio badge"],
             ["Story page", "Open one story; the Details tab lists your idea, the creation time, reading time, narration model, synthesis time and real-time factor", "Story text, audio player, metadata"],
             ["Evaluation", "Choose the number of samples (1 to 30) and a language filter, optionally skip narration or the story model, press Run evaluation; pick a saved run", "Metric cards, a per-sample chart, a samples table and the method notes"]],
            widths=[1.2, 3.4, 2.0], align=["l", "l", "l"], size=9.5),
        P("The model name under each narration (for example `facebook/mms-tts-eng` or `system-tts-offline-fallback`) shows which voice produced it. The first generation after a restart is slower because the models are loaded then."),
        H2("B.6 API quick reference"),
        CODE("curl http://127.0.0.1:8402/api/health\n"
             "curl http://127.0.0.1:8402/api/languages\n"
             "curl -X POST -H \"Content-Type: application/json\" -d '{\"prompt\":\"A young inventor discovers a hidden library.\",\"language_code\":\"en\",\"style\":\"Adventure\",\"length_option\":\"Short\",\"synthesize\":true}' http://127.0.0.1:8402/api/stories/generate\n"
             "curl http://127.0.0.1:8402/api/stories\n"
             "curl -o story.wav http://127.0.0.1:8402/api/audio/1\n"
             "curl -X POST -H \"Content-Type: application/json\" -d '{\"samples\":5}' http://127.0.0.1:8402/api/evaluations/run\n"
             "curl -X DELETE http://127.0.0.1:8402/api/stories/1", 7.6),
        H2("B.7 Tests, experiments and screenshots"),
        CODE("python -m pytest tests -q                      # 29 tests, about 5 s, models stubbed\n"
             "python scripts/run_tests.py                    # same, result written to experiments/tests/metrics.json\n"
             "python -u scripts/run_experiments.py tts_asr   # 15 languages x 10 FLEURS sentences\n"
             "python -u scripts/run_experiments.py cjk       # Chinese and Japanese fallback voice\n"
             "python -u scripts/run_experiments.py story     # 3 conditions x 17 prompts + length scaling\n"
             "python scripts/measure_api.py                  # latencies against a running server\n"
             "python scripts/run_story_asr.py                # story-length audio scored with chunked Whisper\n"
             "python scripts/capture_screens.py             # 1440x900 screenshots into docs/screenshots\n"
             "python scripts/make_report_facts.py            # docs/REPORT_FACTS.md", 8.2),
        H2("B.8 Troubleshooting"),
        TAB("Common problems", ["Symptom", "Cause and fix"],
            [["WER and CER show a dash on the Evaluation page", "Two causes. Without ffmpeg Whisper cannot read the WAV; with ffmpeg, narration longer than 30 seconds is rejected by the recogniser call (\"more than 3000 mel input features\"). The error is stored in each sample as `asr_error`"],
             ["Italian, Chinese or Japanese narration sounds wrong or fails", "`facebook/mms-tts-ita`, `-cmn` and `-jpn` do not exist on the model hub, so the operating-system voice is used; on the test machine it had English voices only"],
             ["A non-English story is written in English", "The 0.6B story model often ignores the requested language; the voice for that language then reads English text badly (Chapter 8)"],
             ["Korean narration fails or is garbled", "Install `uroman` (`pip install uroman`)"],
             ["\"Narration could not be generated\"", "The speech checkpoint is still downloading, or there is no usable voice for the language; retry and read the server window"],
             ["Port 8402 or 5402 already in use", "Another copy is running; stop it or change PORT and FRONTEND_PORT in `.env`"],
             ["The web app says the API is offline", "Start the API again (run.bat or the uvicorn command) and press Retry"],
             ["Each call takes about 2 seconds from Python scripts", "Use `127.0.0.1` instead of `localhost` (measured on this machine)"],
             ["`run.bat` reports a broken .venv or the install fails", "The environment was copied from another computer; delete `.venv` and run again, with enough free disk space for torch and the model weights"]],
            widths=[2.3, 4.3], align=["l", "l"], size=9.5),
    ]
    return _guide_trim(out) if F.REPORT else out


def _guide_trim(out):
    """Compact variant for the full report: requirements as one paragraph, shorter page table, no API quick reference, short troubleshooting."""
    res, skip = [], False
    for b in out:
        if b[0] == "h2":
            skip = b[1].startswith(("B.1", "B.6", "B.7"))
            if b[1].startswith("B.1"):
                res.append(("h2", "B.1 Requirements"))
                res.append(("p", "Python 3.11 or newer (3.11.9 was used), Node.js 20 or newer, the packages in `requirements.txt`, and two things it does not list: ffmpeg on PATH (without it Whisper cannot read the WAV files and WER and CER stay empty) "
                                 "and `pip install uroman` for Korean. Several gigabytes of disk and an internet connection are needed once, to download the model weights."))
            if b[1].startswith("B.7"):
                res.append(("h2", "B.7 Tests and experiments"))
                res.append(("code", "python -m pytest tests -q\npython -u scripts/run_experiments.py tts_asr\npython -u scripts/run_experiments.py story\npython scripts/measure_api.py\npython scripts/capture_screens.py", 8.0))
        if skip:
            continue
        if b[0] == "tab" and b[1].startswith("Pages and what to do"):
            b = ("tab", b[1], ["Page", "What to do"], [[r[0], r[1]] for r in b[3]], [1.2, 5.4], ["l", "l"], 9.0)
        if b[0] == "tab" and b[1].startswith("Common problems"):
            keep = ("WER and CER show", "Italian, Chinese", "A non-English story", "Korean narration", "The web app says")
            b = ("tab", b[1], b[2], [r for r in b[3] if r[0].startswith(keep)]) + tuple(b[4:])
        if b[0] == "tab" and b[1].startswith("Settings read from .env"):
            b = ("tab", b[1], b[2], b[3][:5]) + tuple(b[4:])
        res.append(b)
    return res


# ------------------------------------------------------------------------------ Appendix C
def screens_blocks():
    SH = F.shot
    shots = ["01_landing_light.png", "01_landing_dark.png", "02_studio_empty.png", "07_evaluation_chart.png", "08_evaluation_samples.png", "09_landing_full_page.png", "10_story_detail_hindi.png"]
    missing = [s for s in shots if not os.path.exists(SH(s))]
    assert not missing, missing
    out = [
        H1("APPENDIX C: ADDITIONAL SCREENS"),
        P("The screens below are captures that are not shown in Chapter 8: the landing page in the light and dark themes and in full, the empty Studio, the Evaluation chart and samples views, and a Hindi story page. "
          "All were taken from the running application at 1440 x 900 with real stories and a real evaluation run in the library (the data came from the model runs described in Chapter 8; nothing is mocked)."),
        PAIR([(SH("01_landing_light.png"), "Additional screen: landing page in the light theme, with the counters for languages, styles, lengths and the story model."),
              (SH("01_landing_dark.png"), "Additional screen: the same landing page in the dark theme.")], 2.95),
        FIG(SH("02_studio_empty.png"), "Additional screen: Studio before a story exists, with the idea box, language, style and length selectors.", 3.4),
        P("The landing page is public. Its counters (15 languages, 8 styles, 3 lengths, Qwen/Qwen3-0.6B) restate the configuration, and the ticker below the headline lists the supported languages. "
          "The empty Studio shows the form on the left and an explanatory empty state on the right, with a link to History instead of an error message."),
        FIG(SH("09_landing_full_page.png"), "Additional screen: the whole landing page, scrolled from top to bottom.", F.shot_w(SH("09_landing_full_page.png"), 3.0, 6.0)),
        P("The full page shows the sections below the headline: three steps (say the idea, a model writes it, a voice reads it), six feature cards (multilingual, styles and lengths, natural narration, your library, honest metrics, local-first), "
          "the list of narration languages and the call to action. The language list shows all 15 languages, including Italian, Chinese and Japanese, for which no MMS checkpoint exists (Chapter 8); the page does not distinguish them."),
        PAIR([(SH("07_evaluation_chart.png"), "Additional screen: Evaluation page, Chart tab, with the per-sample real-time factor for the five evaluation prompts."),
              (SH("08_evaluation_samples.png"), "Additional screen: Evaluation page, Samples tab, with latency, audio duration, real-time factor and similarity per prompt.")], 2.95),
        P("In this saved run (5 samples) the cards show the story latency, the narration latency, the real-time factor and ROUGE-L, and every sample's real-time factor lies near 0.22, as in Chapter 8. "
          "The WER and CER columns hold a dash for every sample: the recogniser call failed on narration longer than 30 seconds, so the evaluation page honestly shows no value (Chapter 8)."),
        FIG(SH("10_story_detail_hindi.png"), "Additional screen: story page for a request in Hindi; the story text is English and contains echoed instruction text, and the Hindi voice produced only 4.4 seconds of audio.", F.shot_w(SH("10_story_detail_hindi.png"), 5.0, 4.4)),
        P("This capture shows the failure case discussed in Chapter 8. The request was for a Hindi story, the model wrote English and repeated part of the instructions, and the Hindi speech model, given English letters, produced a very short clip for a text of 185 words. "
          "The model name under the player (`facebook/mms-tts-hin`) and the Hindi tag are what the application recorded; the application does not detect that the text language differs from the requested one."),
    ]
    return _screens_trim(out) if F.REPORT else out


def _screens_trim(out):
    """Compact variant for the full report: shorter explanations, the full landing page dropped."""
    res, drop_next = [], False
    for b in out:
        if b[0] == "fig" and "09_landing_full_page" in b[1]:
            drop_next = True       # full-page picture and its paragraph
            continue
        if drop_next and b[0] == "p":
            drop_next = False
            continue
        if b[0] == "p" and b[1].startswith("The landing page is public"):
            b = ("p", "The landing page is public and needs no data; the empty Studio shows the form and an empty state with a link to History instead of an error.")
        if b[0] == "p" and b[1].startswith("In this saved run"):
            b = ("p", "Every sample's real-time factor lies near 0.22; the WER and CER columns hold a dash because the recogniser call failed on narration longer than 30 seconds.")
        if b[0] == "p" and b[1].startswith("This capture shows the failure case"):
            b = ("p", "The request was for Hindi, the model wrote English and repeated part of its instructions, and the Hindi speech model, given English letters, produced a very short clip.")
        res.append(b)
    return res
