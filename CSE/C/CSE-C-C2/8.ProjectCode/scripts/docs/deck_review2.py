"""13.Review_2_PPT.pptx: 20 slides, design, methodology and progress. Built from D:\\abstracts\\Templates\\Review_2_PPT.pptx.

Self-contained: the small slide helpers are defined here. All numbers come from facts.py (experiments/**/metrics.json).
    python -m scripts.docs.deck_review2        # from 8.ProjectCode
"""
import os
import tempfile

from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER

from . import facts as F
from . import pptkit as K

TEMPLATE = r"D:\abstracts\Templates\Review_2_PPT.pptx"
LAYOUT_FOOTER_OLD = "The Hidden Risk of Social Media"
OUT = os.path.join(F.BATCH, "13.Review_2_PPT.pptx")


# ------------------------------------------------------------------ helpers
def is_ph(sh, *types):
    return sh.is_placeholder and sh.placeholder_format.type in types


def prepare(prs, review_label):
    for lay in prs.slide_layouts:
        for sh in lay.shapes:
            if sh.has_text_frame and LAYOUT_FOOTER_OLD in sh.text_frame.text:
                K.replace_text(sh, f"{F.PRODUCT}  ·  {review_label}")
    cp = prs.core_properties
    cp.title = f"{F.FULL_TITLE}: {review_label}"
    cp.subject = f"Batch {F.BATCH_NO} ({F.SECTION})"
    cp.author = ", ".join(n for n, _ in F.STUDENTS)
    cp.keywords = "multilingual story generation, text-to-speech, MMS-TTS, Qwen3, Whisper, speech evaluation"
    cp.comments = ""
    cp.last_modified_by = ""


def set_title(slide, text, size=None):
    for sh in slide.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE):
            K.replace_text(sh, text, size)
            return sh


def wipe(slide):
    K.clear(slide, lambda sh: sh.is_placeholder)


def agenda(slide, items, colors, cols=4):
    n = len(items)
    rows = (n + cols - 1) // cols
    gx, gy = 0.29, 0.3
    w = (12.13 - gx * (cols - 1)) / cols
    h = min(1.45, (5.3 - gy * (rows - 1)) / rows)
    x0, y0 = 0.6, 1.55
    for i, (n_, label) in enumerate(items):
        r, c = divmod(i, cols)
        x, y = x0 + c * (w + gx), y0 + r * (h + gy)
        K.box(slide, x, y, w, h)
        K.text(slide, x + 0.25, y + 0.14, 1.0, 0.5, n_, size=26, color=colors[i % len(colors)], bold=True, font="Cambria")
        K.text(slide, x + 0.25, y + 0.72, w - 0.5, 0.65, label, size=16, color=K.INK, bold=True)


def title_slide(s, subtitle, label):
    for sh in s.shapes:
        nm = sh.name
        if is_ph(sh, PP_PLACEHOLDER.CENTER_TITLE, PP_PLACEHOLDER.TITLE):
            K.replace_text(sh, F.TITLE, 28)
        elif is_ph(sh, PP_PLACEHOLDER.SUBTITLE, PP_PLACEHOLDER.BODY):
            K.replace_text(sh, subtitle, 18)
        elif nm == "review label":
            K.replace_text(sh, label)
        elif nm == "team":
            K.replace_text(sh, "\n".join(f"{n_}  {r_}" for n_, r_ in F.STUDENTS))
        elif nm == "Text 6":
            K.replace_text(sh, f"{F.GUIDE}, {F.GUIDE_DESIGNATION}")
        elif nm == "Text 7":
            K.replace_text(sh, f"{F.DEPT}\n{F.COLLEGE_SHORT}  ·  Batch {F.BATCH_NO} ({F.SECTION})  ·  {F.YEAR}")


def thank_you(s):
    for sh in s.shapes:
        if is_ph(sh, PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE):
            K.replace_text(sh, "Thank you")
        elif is_ph(sh, PP_PLACEHOLDER.BODY, PP_PLACEHOLDER.SUBTITLE):
            K.replace_text(sh, "Questions and suggestions are welcome.")


def trim(path, tag):
    """Copy of a diagram with its white margins removed (written to the temp folder, source untouched)."""
    from PIL import Image, ImageChops

    with Image.open(path) as im:
        im = im.convert("RGB")
        bbox = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
        if bbox:
            pad = 12
            bbox = (max(bbox[0] - pad, 0), max(bbox[1] - pad, 0), min(bbox[2] + pad, im.size[0]), min(bbox[3] + pad, im.size[1]))
            im = im.crop(bbox)
        out = os.path.join(tempfile.gettempdir(), f"storyvox_r2_{tag}.png")
        im.save(out)
    return out


def shot_box(slide, name, x, y, w, h, caption):
    K.picture(slide, F.shot(name), x, y, w, h - 0.5, border=True)
    K.text(slide, x, y + h - 0.45, w, 0.45, caption, size=11, color=K.TXT, align="c", italic=True)


def src_lines():
    out = {}
    for rel in ("app/main.py", "app/config.py", "app/schemas.py", "app/database.py", "app/api/routes.py", "app/models/__init__.py", "app/services/story_generator.py",
                "app/services/tts_service.py", "app/services/asr_service.py", "app/services/evaluation_service.py", "app/utils/__init__.py",
                "app/utils/audio.py", "app/utils/metrics.py"):
        with open(os.path.join(F.CODE, rel), encoding="utf-8") as f:
            out[rel] = sum(1 for _ in f)
    return out


# ------------------------------------------------------------------ the deck
def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 2")
    S = list(prs.slides)
    assert len(S) == 20, len(S)
    notes = {}

    L = F.LANGS
    en = L["en"]
    A = F.STORY["conditions"]["A_app_raw_prompt"]
    B = F.STORY["conditions"]["B_chat_template"]
    SS = F.STORY_SUMMARY
    a_match = sum(1 for r in A if r["language_match"])
    b_match = sum(1 for r in B if r["language_match"])
    sasr = F.STORY_ASR["rows"]
    non_en = [r for r in sasr if r["language"] != "en"]
    non_en_english = sum(1 for r in non_en if r.get("text_language") == "en")
    hi_row = next(r for r in sasr if r["language"] == "hi")
    en_rows = [r for r in sasr if r["language"] == "en"]
    en_wer = sum(r["wer_norm"] for r in en_rows) / len(en_rows)
    en_cer = sum(r["cer_norm"] for r in en_rows) / len(en_rows)
    gen = F.API["generate"]
    cold = next(r for r in gen if r["cold"])
    ep = F.API["endpoints"]
    lines = src_lines()
    ls = F.LENGTH_SCALING

    # ---- 1 title
    title_slide(S[0], "Design, methodology and progress: a local pipeline that writes a story with Qwen3-0.6B and narrates it with MMS-TTS in 15 languages",
                "REVIEW 2  ·  DESIGN, METHODOLOGY AND PROGRESS")
    notes[1] = ("This review shows how StoryVox is designed and built, what is implemented, the first measured results, and the open items. "
                "Introduce the four team members and the guide.")

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Recap and architecture"), ("02", "Methodology and dataset"), ("03", "Preprocessing and model"), ("04", "Inference configuration and decision logic"),
               ("05", "Data flow, modules, UML"), ("06", "Technology stack"), ("07", "Implementation progress"), ("08", "Preliminary results"),
               ("09", "Output screens"), ("10", "Testing"), ("11", "Challenges"), ("12", "Next steps")],
           [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE])
    notes[2] = "Agenda for the design and progress review."

    # ---- 3 recap
    s = S[2]
    set_title(s, "Recap: problem and proposed system")
    wipe(s)
    W = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Problem", "Multilingual stories need a writer and a narrator for every language. Generic speech sounds mechanical, low-resource languages have thin support, and tools do either text or speech, not both.", K.ORANGE, "!"),
        ("Proposed system", "StoryVox takes an idea, a language, a style and a length, writes the story with Qwen3-0.6B, narrates it with a per-language MMS-TTS voice, stores both in a library and judges the result with Whisper-small.", K.BLUE, "i"),
        ("Base paper link", "SAM Translator (Tran and Sakti) is a speech-translation system with mixture-of-experts and self-paced learning. We share only the goal of multilingual speech judged by ASR; none of its techniques. Scores are not comparable.", K.GREEN, "B"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.6, W, 4.9, t, b_, col, gl, body_size=18)
    notes[3] = ("Recap of Review 1. The base paper reports BLEU on translation into English; we report round-trip error rates, real-time factor and story checks. We compare design choices and compute cost only.")

    # ---- 4 architecture
    s = S[3]
    set_title(s, "System architecture")
    wipe(s)
    K.picture(s, trim(F.diag("01_system_architecture.png"), "01"), 0.6, 1.3, 7.7, 5.7)
    K.text(s, 8.55, 1.45, 4.2, 5.4, [
        ("**Four tiers, all local**", {"space_after": 8}),
        (f"App: React 19 + Vite, 5 pages; port {F.WEB_PORT} in development, or served by the API.", {"bullet": True}),
        (f"API: FastAPI on port {F.API_PORT}; 11 routes under /api plus an SPA fallback.", {"bullet": True}),
        ("Services: story generator, TTS provider chain, ASR, evaluation.", {"bullet": True}),
        ("Storage: SQLite (3 tables) and WAV files; models cached by Hugging Face.", {"bullet": True}),
    ], size=15, color=K.INK)
    notes[4] = "The routes live in app/api/routes.py (254 lines) and call the services; models load lazily on first use, which is why the first request is slow."

    # ---- 5 methodology workflow
    s = S[4]
    set_title(s, "Methodology: write, narrate, store, judge")
    wipe(s)
    K.picture(s, trim(F.diag("02_high_level_workflow.png"), "02"), 0.6, 1.4, 7.5, 5.0)
    for i, (t, b_) in enumerate([("Write", "Validate the request, build one instruction, generate with Qwen3-0.6B, split the output into a title and a body; fall back to the composer if the output is too short."),
                                 ("Narrate and store", "Split the text into chunks of at most 380 characters, synthesise each with the language's MMS voice, join with pauses, save the WAV and the database rows."),
                                 ("Judge", "Transcribe the audio with Whisper-small, compute WER and CER, similarity, ROUGE-L, latency and real-time factor.")]):
        y = 1.4 + i * 1.78
        K.box(s, 8.35, y, 4.38, 1.65)
        K.text(s, 8.5, y + 0.07, 4.1, 0.4, t, size=15, color=K.INK, bold=True)
        K.text(s, 8.5, y + 0.42, 4.1, 1.2, b_, size=13, color=K.TXT)
    K.text(s, 0.6, 6.5, 7.5, 0.45, "High-level workflow as implemented in the API.", size=12, color=K.TXT, align="c", italic=True)
    notes[5] = "Generation and narration run in one request; evaluation is a separate route that repeats the same steps for five built-in prompts."

    # ---- 6 dataset
    s = S[5]
    set_title(s, "Dataset: FLEURS, used only to evaluate narration")
    wipe(s)
    for i, (v, l, c) in enumerate([("15", "languages in the evaluation set", K.ORANGE),
                                   ("150", "test sentences (10 per language)", K.BLUE),
                                   ("0", "training examples: no model was trained", K.GREEN),
                                   ("CC BY 4.0", "licence of the FLEURS test data", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.4, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["", "Round-trip evaluation of narration", "Story-generation experiment"],
            ["Source", "Google FLEURS test split, read speech transcripts (Conneau et al.), downloaded from the Hugging Face dataset repo", "One fixed idea: 'A young inventor discovers a hidden library.'"],
            ["Size", "First 10 sentences per language within a length window (6-30 words; 12-70 characters for zh and ja)", "17 items: English with 3 styles plus 14 other languages with Adventure; Short length"],
            ["Use", "Synthesise with the app's own TTS chain, transcribe with Whisper-small, score WER and CER against the sentence", "Compare three conditions: shipped prompt, chat template, offline composer"],
            ["Library", "Stories created through the API: 7 (3 English, one each Hindi, French, German, Spanish)", "Used for the screenshots and the story-length intelligibility check"],
            ["Limits", "Read Wikipedia-style sentences, not narrative; 10 sentences per language is a small sample", "A single idea and seed 0; proxies, no human rating"]]
    K.table(s, 0.6, 2.95, [1.2, 5.9, 5.03], rows, font_size=12.5, row_h=0.66, first_bold=True)
    notes[6] = ("FLEURS is a public benchmark of the same sentences read in many languages. We use it only as test text for the speech chain; no training or tuning took place. "
                "The seven library stories are real outputs of the running application.")

    # ---- 7 preprocessing
    s = S[6]
    set_title(s, "Preprocessing: from request to audio chunks")
    wipe(s)
    K.flow(s, 0.6, 1.45, 12.13, 1.0, [("Validate request", K.NAVY), ("Build prompt", K.PURPLE), ("Parse title and body", K.PURPLE),
                                       ("Chunk at 380 chars", K.GREEN), ("VITS per chunk", K.GREEN), ("Normalise and join", K.ORANGE)], size=12, gap=0.22)
    for i, (v, l, c) in enumerate([("2,000", "characters allowed in the idea; unknown language, style or length is rejected with HTTP 422", K.ORANGE),
                                   ("0.25 s", "pause between chunks; peak-normalised to 0.9; empty or silent audio is rejected", K.BLUE)]):
        K.tile(s, 0.6 + i * 6.2, 2.8, 5.95, 1.25, v, l, c, vsize=28, lsize=11.5)
    K.text(s, 0.6, 4.3, 12.13, 2.7, [
        ("The prompt names the language, style guidance, a paragraph target of 3, 5 or 8, and a rule that the first line starts with 'Title:'.", {"bullet": True}),
        ("The output is split into title and body; an output under 20 words or any model failure switches to the offline composer.", {"bullet": True}),
        ("Text is cut at sentence boundaries (including the Devanagari danda) into chunks of at most 380 characters; a single longer sentence is split by length.", {"bullet": True}),
        ("For scoring, text is normalised: NFKC, lower-case, punctuation removed; spaces also removed for Chinese and Japanese, where WER is not reported.", {"bullet": True}),
    ], size=16, color=K.INK, space_after=9)
    notes[7] = "The chunker and the normaliser are covered by unit tests (the limit, the one-long-sentence case and the Devanagari danda)."

    # ---- 8 model
    s = S[7]
    set_title(s, "Model architecture: pretrained models in a cascade")
    wipe(s)
    K.picture(s, trim(F.diag("12_model_architecture.png"), "12"), 0.6, 1.35, 7.6, 5.0)
    K.text(s, 8.5, 1.45, 4.25, 5.4, [
        ("**Story model**: Qwen3-0.6B, a decoder-only language model, sampled with temperature 0.8 and top-p 0.9.", {"bullet": True, "space_after": 7}),
        ("**Narration model**: facebook/mms-tts-<language>, a VITS model (text encoder, duration predictor, flow, HiFi-GAN decoder) at 16 kHz.", {"bullet": True, "space_after": 7}),
        ("**Judges** (evaluation only): Whisper-small for WER and CER, a multilingual MiniLM for prompt-story similarity.", {"bullet": True, "space_after": 7}),
        ("Nothing is trained or fine-tuned; the models are downloaded once from Hugging Face.", {"bullet": True, "italic": True, "color": K.TXT}),
    ], size=13.5, color=K.INK)
    K.text(s, 0.6, 6.45, 7.6, 0.45, "The four models and the stages inside each.", size=12, color=K.TXT, align="c", italic=True)
    notes[8] = "A cascade was chosen because the pretrained parts exist and run on a CPU; training a joint model needs data and GPUs that were not available."

    # ---- 9 inference configuration
    s = S[8]
    set_title(s, "Inference configuration (nothing was trained)")
    wipe(s)
    rows = [["Setting", "Value"],
            ["Story model", "Qwen/Qwen3-0.6B via the transformers text-generation pipeline; raw prompt, no chat template; temperature 0.8, top-p 0.9"],
            ["Token budget", "220 / 420 / 700 new tokens for Short / Medium / Long; paragraph target 3 / 5 / 8; fallback below 20 words"],
            ["Narration", "facebook/mms-tts-* VITS, 16 kHz, 380-character chunks, 0.25 s pause, peak 0.9; fallback: OS voice through pyttsx3"],
            ["Recogniser", f"openai/whisper-small, language forced to the requested language; loaded in {F.TTS['asr_load_s']:.1f} s"],
            ["Similarity", "paraphrase-multilingual-MiniLM-L12-v2 cosine; TF-IDF cosine if the model is missing; ROUGE-L F1"],
            ["Experiments", "seed 0; FLEURS 10 sentences per language; story idea fixed; same code path as the application"],
            ["Machine", "Intel Core i5-12500 (12 threads), 15.7 GB RAM, CPU only; Python 3.11.9, torch 2.14.1, transformers 5.20.2"]]
    K.table(s, 0.6, 1.45, [2.3, 9.83], rows, font_size=13, row_h=0.66, first_bold=True)
    notes[9] = "All later numbers use exactly this configuration. The project's own .venv was unusable here, so system Python was used."

    # ---- 10 decision logic
    s = S[9]
    set_title(s, "Decision logic: fallbacks and story conditions")
    wipe(s)
    K.picture(s, trim(F.diag("10_flowchart_algorithm.png"), "10"), 0.6, 1.3, 6.2, 5.7)
    K.text(s, 7.1, 1.45, 5.65, 5.5, [
        ("**Story path**: validate, build the prompt, call Qwen3-0.6B; if the output has under 20 words or any error occurs, the offline composer answers and its model id is recorded.", {"bullet": True, "space_after": 8}),
        ("**Voice path**: MMS-TTS first; on a load or inference error, or silent audio, the OS voice; if that fails too, HTTP 500.", {"bullet": True, "space_after": 8}),
        ("**Experiment conditions**: A = shipped path; B = same model through the Qwen3 chat template (not shipped); C = offline composer.", {"bullet": True, "space_after": 8}),
        ("**Reported as measured**: a mismatch between requested language and story language is counted, not hidden.", {"bullet": True}),
    ], size=15, color=K.INK)
    notes[10] = "The flowchart is the code of generate_story_text. The narration and evaluation flowchart is in the report."

    # ---- 11 data flow and modules
    s = S[10]
    set_title(s, "Data flow and modules")
    wipe(s)
    K.picture(s, trim(F.diag("04_dfd_level1.png"), "04"), 0.6, 1.3, 6.4, 5.2)
    K.text(s, 0.6, 6.55, 6.4, 0.4, "DFD level 1: the processes and the data stores.", size=12, color=K.TXT, align="c", italic=True)
    mods = [["Module", "Lines", "Role"],
            ["services/story_generator.py", lines["app/services/story_generator.py"], "prompt, Qwen3, composer"],
            ["services/tts_service.py", lines["app/services/tts_service.py"], "MMS and OS voice"],
            ["services/asr_service.py", lines["app/services/asr_service.py"], "Whisper transcription"],
            ["services/evaluation_service.py", lines["app/services/evaluation_service.py"], "metrics, JSON and CSV"],
            ["api/routes.py", lines["app/api/routes.py"], "11 routes"],
            ["models/__init__.py", lines["app/models/__init__.py"], "3 tables"],
            ["config.py, schemas.py", lines["app/config.py"] + lines["app/schemas.py"], "settings, validation"],
            ["utils/ (3 files)", lines["app/utils/__init__.py"] + lines["app/utils/audio.py"] + lines["app/utils/metrics.py"], "chunking, audio, WER"]]
    K.table(s, 7.25, 1.45, [2.75, 0.7, 2.03], mods, font_size=11, row_h=0.5, first_bold=True, align=["l", "r", "l"])
    notes[11] = "Module sizes counted from the files (app/ is 1,401 lines in total). The API layer validates, calls a service and shapes the JSON."

    # ---- 12 database and UML
    s = S[11]
    set_title(s, "Database design and UML")
    wipe(s)
    K.picture(s, trim(F.diag("06_uml_class.png"), "06"), 0.6, 1.3, 5.5, 5.5)
    K.text(s, 0.6, 6.75, 5.5, 0.35, "UML class diagram.", size=11.5, color=K.TXT, align="c", italic=True)
    K.picture(s, trim(F.diag("09_er_diagram.png"), "09"), 6.4, 1.3, 6.33, 3.55)
    K.text(s, 6.4, 4.85, 6.33, 0.35, "Entity-relationship diagram of the SQLite database.", size=11.5, color=K.TXT, align="c", italic=True)
    K.box(s, 6.4, 5.3, 6.33, 1.7)
    K.text(s, 6.55, 5.38, 6.05, 1.6, [
        ("**stories** (prompt, title, text, language, style, length, words, time) has many **audio_outputs** (file path, duration, model, RTF).", {"bullet": True}),
        ("**evaluations** keeps one JSON metrics document per run. SQLite foreign keys are declared but not switched on.", {"bullet": True}),
    ], size=11.5, color=K.INK, space_after=4)
    notes[12] = "SQLAlchemy 2.0 declarative models; deleting a story removes its audio rows and the WAV file in the route."

    # ---- 13 technology stack
    s = S[12]
    set_title(s, "Technology stack")
    wipe(s)
    stack = [("Python 3.11.9", "FastAPI 0.143.3, uvicorn 0.54, pydantic 2.14", K.BLUE), ("PyTorch 2.14.1", "transformers 5.20.2 runs Qwen3, MMS-TTS and Whisper", K.ORANGE),
             ("Qwen3-0.6B", "story model, Hugging Face hub", K.GREEN), ("MMS-TTS (VITS)", "one checkpoint per language, 16 kHz", K.PURPLE),
             ("Whisper-small", "recogniser; jiwer 4.0 for WER and CER", K.BLUE), ("sentence-transformers 6.2", "multilingual MiniLM similarity; rouge-score", K.ORANGE),
             ("SQLite + SQLAlchemy 2.0", "stories, audio_outputs, evaluations", K.GREEN), ("React 19 + Vite 8", "5 pages, Recharts, GSAP, Framer Motion", K.PURPLE)]
    for i, (t, b_, col) in enumerate(stack):
        r, c = divmod(i, 4)
        x, y = 0.6 + c * 3.09, 1.5 + r * 2.5
        K.box(s, x, y, 2.85, 2.25)
        K.circle(s, x + 0.22, y + 0.22, 0.5, col, str(i + 1), 16)
        K.text(s, x + 0.22, y + 0.9, 2.45, 0.45, t, size=15, color=K.INK, bold=True)
        K.text(s, x + 0.22, y + 1.35, 2.45, 0.85, b_, size=12.5, color=K.TXT)
    K.text(s, 0.6, 6.6, 12.13, 0.4, "Everything runs on CPU on one machine; tests use pytest 8.2, screenshots use Playwright with Chrome.", size=13, color=K.TXT, italic=True)
    notes[13] = "Versions are those installed on the measuring machine; requirements.txt only gives lower bounds."

    # ---- 14 implementation progress
    s = S[13]
    set_title(s, "Implementation progress")
    wipe(s)
    rows = [["Component", "Status", "Evidence"],
            ["Story generation (prompt, Qwen3, composer)", "Done, weak", f"target-language text in {a_match} of {len(A)} cases with the shipped prompt"],
            ["Narration (MMS, OS fallback)", "Done", f"{len(F.MMS_LANGS)} languages by MMS, mean RTF {F.MMS_MEAN_RTF:.3f}; it, zh, ja use the OS voice"],
            ["Evaluation service", "Built, partly failing", "WER and CER are null for story-length audio (Whisper rejects audio over 30 s)"],
            ["FastAPI service and SQLite library", "Done", "11 routes, 3 tables, delete removes audio and rows"],
            ["React app", "Done", "Landing, Studio, History, Story detail, Evaluation"],
            ["Translation, voice and speed, rating, voice cloning", "Not implemented", "in the objectives but absent from the code"],
            ["Automated tests", "Done", f"{F.PYTEST_PASSED} of {F.PYTEST_TOTAL} pass ({F.PYTEST_API} original, {F.PYTEST_UNIT} added); models are stubbed"]]
    K.table(s, 0.6, 1.45, [4.3, 2.1, 5.73], rows, font_size=13, row_h=0.64, first_bold=True)
    notes[14] = "Honest status: the pipeline and the app work end to end; the story model is the weak link, and four objectives are not implemented."

    # ---- 15 preliminary results
    s = S[14]
    set_title(s, "Preliminary results")
    wipe(s)
    langs = [c for c in F.MMS_LANGS]
    K.bar_chart(s, 0.6, 1.3, 6.9, 3.5, [F.LANG_NAMES[c] for c in langs],
                [("WER (normalised)", [round(L[c]["wer_norm_corpus"], 3) for c in langs]), ("CER (normalised)", [round(L[c]["cer_norm_corpus"], 3) for c in langs])],
                colors=[K.NAVY, K.GREEN], number_format="0.00", font_size=9, max_value=0.6, label_size=7)
    K.text(s, 0.6, 4.8, 6.9, 0.35, "Round trip on 10 FLEURS sentences per language (MMS voices); lower is better.", size=11, color=K.TXT, align="c", italic=True)
    crows = [["Condition (17 items)", "Latency", "Language match", "Instr. echo", "Distinct-2"]]
    for key, name in (("A_app_raw_prompt", "A shipped prompt"), ("B_chat_template", "B chat template"), ("C_local_composer", "C offline composer")):
        sm = SS[key]
        crows.append([name, f"{sm['mean_latency_s']:.1f} s" if sm["mean_latency_s"] >= 0.1 else "<0.01 s", f"{F.pct(sm['language_match_rate'], 0)}", f"{sm['mean_instruction_echo']:.3f}", f"{sm['mean_distinct_2']:.2f}"])
    K.table(s, 7.75, 1.4, [1.75, 0.8, 0.95, 0.75, 0.75], crows, font_size=10.5, row_h=0.5, first_bold=True, align=["l", "r", "r", "r", "r"], header_size=10)
    K.text(s, 7.75, 3.55, 5.0, 1.4, [
        (f"Speed: narration RTF {F.MMS_MEAN_RTF:.2f}; a Short story takes {ls[0]['total_s']:.0f} s end to end, Medium {ls[1]['total_s']:.0f} s, Long {ls[2]['total_s']:.0f} s.", {"bullet": True}),
    ], size=12.5, color=K.INK)
    K.text(s, 0.6, 5.25, 12.13, 1.8, [
        (f"Narration is good where an MMS voice exists: mean CER {F.pct(F.MMS_MEAN_CER)}, from {F.pct(L[F.BEST_CER]['cer_norm_corpus'])} (Spanish) to {F.pct(L[F.WORST_CER]['cer_norm_corpus'])} (Hindi). English: WER {F.pct(en['wer_norm_corpus'])}, CER {F.pct(en['cer_norm_corpus'])}.", {"bullet": True}),
        (f"Story generation is the weak link: the shipped prompt answers in the requested language in {a_match} of {len(A)} cases; the chat template reaches {b_match}. {non_en_english} of {len(non_en)} stories made through the API were English.", {"bullet": True}),
        (f"Story-length audio, English only: WER {F.pct(en_wer)}, CER {F.pct(en_cer)} (chunked Whisper); the app's own evaluation reports none because transcription fails above 30 s.", {"bullet": True}),
    ], size=13, color=K.INK, space_after=5)
    notes[15] = ("Results are reported as measured, including the negative ones. Language match uses a language detector, which is unreliable on very short text; "
                 "WER and CER mix speech-model error with Whisper-small's own error.")

    # ---- 16 output screens
    s = S[15]
    set_title(s, "Output screens")
    wipe(s)
    shot_box(s, "03_studio_result.png", 0.6, 1.4, 3.95, 2.85, "Studio: English Adventure story with narration player")
    shot_box(s, "04_history.png", 4.69, 1.4, 3.95, 2.85, "History: seven stories with language, style, words, audio")
    shot_box(s, "10_story_detail_hindi.png", 8.78, 1.4, 3.95, 2.85, "Hindi request: English text, 4.4 s of audio")
    shot_box(s, "06_evaluation.png", 0.6, 4.35, 3.95, 2.7, "Evaluation: WER and CER show a dash")
    shot_box(s, "07_evaluation_chart.png", 4.69, 4.35, 3.95, 2.7, "Per-sample real-time factor chart")
    shot_box(s, "08_evaluation_samples.png", 8.78, 4.35, 3.95, 2.7, "Per-sample table: five prompts, no WER or CER")
    notes[16] = "All screens are captures of the running application with real generated stories. The dash in WER and CER is the real result of the Whisper 30-second limit."

    # ---- 17 testing
    s = S[16]
    set_title(s, "Initial testing and observations")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{F.PYTEST_PASSED} / {F.PYTEST_TOTAL}", f"pytest tests pass ({F.PYTEST_API} original, {F.PYTEST_UNIT} added)", K.GREEN),
                                   (f"{cold['request_s']:.0f} s", "first generate request (models load inside it)", K.BLUE),
                                   (f"{gen[1]['request_s']:.0f} s", "warm Short story with narration (English, Bedtime)", K.ORANGE),
                                   (f"{ep['GET /api/stories']['median_ms']:.1f} ms", "median for listing stories", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.09, 1.4, 2.85, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["Endpoint (n calls)", "Median ms", "p95 ms"]]
    for name in ("GET /api/health", "GET /api/languages", "GET /api/stories", "GET /api/evaluations", "POST /api/stories/generate (empty prompt, 422)", "GET /api/audio/{id} (WAV download)"):
        e = ep[name]
        rows.append([f"{name.replace(' (empty prompt, 422)', ' (422)')} ({e['n']})", f"{e['median_ms']:.1f}", f"{e['p95_ms']:.1f}"])
    K.table(s, 0.6, 3.0, [4.2, 1.1, 1.1], rows, font_size=11.5, row_h=0.46, first_bold=True, align=["l", "r", "r"])
    K.text(s, 7.3, 3.0, 5.45, 4.0, [
        ("**What the tests cover**: chunking, audio and metric helpers, prompt builder, the composer in all 15 languages, validation errors, 404s, delete and streaming.", {"bullet": True, "space_after": 7}),
        ("**What they do not cover**: the real models; those are exercised by the experiment scripts.", {"bullet": True, "space_after": 7}),
        ("**Not done**: user study, load test, security audit, browsers other than Chrome. The app has no sign-in.", {"bullet": True, "space_after": 7}),
        ("Timings are from one CPU machine with 127.0.0.1 as host.", {"bullet": True, "italic": True, "color": K.TXT}),
    ], size=14, color=K.INK)
    notes[17] = "The shipped evaluation also served as a test: it exposed the 30-second limit of the transcription call."

    # ---- 18 challenges
    s = S[17]
    set_title(s, "Challenges and corrective actions")
    wipe(s)
    rows = [["Challenge", "What we found", "Action"],
            ["Story language", f"The 0.6B model with the raw prompt answers in English; {a_match} of {len(A)} matches", "Chat-template variant measured (B: " + f"{b_match}); not yet shipped"],
            ["Missing checkpoints", "facebook/mms-tts-ita, -cmn, -jpn do not exist on the Hub", "OS fallback reported; zh and ja narrate 2 and 1 of 10 sentences"],
            ["Whisper 30 s limit", "Story-length audio makes the app's evaluation fail; WER and CER stay null", "Separate chunked scoring script; one-line fix proposed"],
            ["Hidden dependencies", "ffmpeg and uroman (for Korean) are not in requirements.txt", "Documented; installed for the experiments"],
            ["Environment", "The project .venv pointed to a missing Python; D: had little space", "Ran on system Python 3.11.9 and recorded versions"],
            ["Titles", "Many stories are 'Untitled Story'; one title echoed the instruction text", "Reported; parser change planned"]]
    K.table(s, 0.6, 1.4, [2.5, 5.2, 4.43], rows, font_size=13.5, row_h=0.78, first_bold=True)
    notes[18] = "Each challenge is a measured finding; the evidence is in docs/REPORT_FACTS.md."

    # ---- 19 next steps
    s = S[18]
    set_title(s, "Next steps")
    wipe(s)
    W = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Fix and re-measure", "Use the chat template for the story model, add chunking to the transcription call, parse titles more safely, and re-run the 15-language evaluation with the same scripts.", K.ORANGE, "1"),
        ("Close the gaps", "Add a translation step or a stronger multilingual story model, voice and speed controls, user ratings, and checkpoints or voices for Italian, Chinese and Japanese.", K.BLUE, "2"),
        ("Deliver", "Finish the final report and the IEEE paper from the measured results, rehearse the demo, and keep every number tied to the metrics files.", K.GREEN, "3"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.6, W, 3.9, t, b_, col, gl, body_size=17)
    notes[19] = "The open items are the ones identified by the measurements, in priority order."

    # ---- 20 thank you
    thank_you(S[19])
    notes[20] = "Close the review and invite questions."

    for i, t in notes.items():
        K.set_notes(S[i - 1], t)
    prs.save(out_path)
    K.rename_theme(out_path, F.PRODUCT)
    return out_path


def main():
    build(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
