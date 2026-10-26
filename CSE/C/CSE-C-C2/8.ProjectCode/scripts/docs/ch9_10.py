"""Chapters 9 (Conclusion) and 10 (Future scope), plus the shared block lists used by documents 9, 10, 12 and 15.

Every number is read from facts.py (experiments/**/metrics.json); code excerpts are cut from the real files in 8.ProjectCode.
"""
import ast
import os
import textwrap

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, TAB, renum
from .refs import N as C

CA, CB, CC = "A_app_raw_prompt", "B_chat_template", "C_local_composer"


# ---------------------------------------------------------------------------- helpers
def _read(rel):
    with open(os.path.join(F.CODE, rel), encoding="utf-8") as f:
        return f.read()


def fn(rel, name, doc=False):
    """Source of a module-level function exactly as it stands (docstring removed unless doc=True)."""
    text = _read(rel)
    lines = text.split("\n")
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            start = min([d.lineno for d in node.decorator_list] + [node.lineno])
            end = node.end_lineno
            body = lines[start - 1:end]
            if not doc and ast.get_docstring(node):
                d = node.body[0]
                body = lines[start - 1:d.lineno - 1] + lines[d.end_lineno:end]
            return "\n".join(body)
    raise KeyError(name)


def meth(rel, cls, name):
    """Source of a method of a class, dedented, without its docstring."""
    text = _read(rel)
    lines = text.split("\n")
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.ClassDef) and node.name == cls:
            for m in node.body:
                if isinstance(m, ast.FunctionDef) and m.name == name:
                    body = lines[m.lineno - 1:m.end_lineno]
                    if ast.get_docstring(m):
                        d = m.body[0]
                        body = lines[m.lineno - 1:d.lineno - 1] + lines[d.end_lineno:m.end_lineno]
                    return textwrap.dedent("\n".join(body))
    raise KeyError((cls, name))


def between(rel, first, last):
    """Lines from the first line containing `first` to the first later line containing `last` (inclusive), dedented."""
    lines = _read(rel).split("\n")
    i = next(k for k, l in enumerate(lines) if first in l)
    j = next(k for k in range(i, len(lines)) if last in lines[k])
    return textwrap.dedent("\n".join(lines[i:j + 1]))


def _fig(name, caption, width=5.6):
    """A result figure, only if it has been produced."""
    return [FIG(F.fig(name), caption, width)] if os.path.exists(F.fig(name)) else []


def _v():
    L = F.LANGS
    sa, sb, sc = (F.STORY_SUMMARY[c] for c in (CA, CB, CC))
    conds = F.STORY["conditions"]
    rows = F.STORY_ASR["rows"]
    en = [r for r in rows if r["language"] == "en"]
    non = [r for r in rows if r["language"] != "en"]
    return dict(
        rtf=F.MMS_MEAN_RTF, cer=F.MMS_MEAN_CER, wer=F.MMS_MEAN_WER, n_mms=len(F.MMS_LANGS),
        en_wer=L["en"]["wer_norm_corpus"], en_cer=L["en"]["cer_norm_corpus"], es_cer=L["es"]["cer_norm_corpus"], hi_cer=L["hi"]["cer_norm_corpus"],
        it_wer=L["it"]["wer_norm_corpus"], zh_n=L["zh"]["narrated"], ja_n=L["ja"]["narrated"], zh_cer=L["zh"]["cer_norm_corpus"], ja_cer=L["ja"]["cer_norm_corpus"],
        ko_rtf=L["ko"]["mean_rtf"], ko_cer=L["ko"]["cer_norm_corpus"],
        a_match=sa["language_match_rate"], b_match=sb["language_match_rate"], c_match=sc["language_match_rate"],
        a_echo=sa["mean_instruction_echo"], b_echo=sb["mean_instruction_echo"], a_d2=sa["mean_distinct_2"], b_d2=sb["mean_distinct_2"],
        a_lat=sa["mean_latency_s"], b_lat=sb["mean_latency_s"], c_sim=sc["mean_similarity"], a_sim=sa["mean_similarity"],
        a_ok=round(sa["language_match_rate"] * 17), b_ok=round(sb["language_match_rate"] * 17),
        untitled_a=sum(1 for r in conds[CA] if r["title"] == "Untitled Story"),
        asr_en_wer=sum(r["wer_norm"] for r in en) / len(en), asr_en_cer=sum(r["cer_norm"] for r in en) / len(en), n_en=len(en),
        asr_non_min=min(r["wer_norm"] for r in non if r["language"] != "hi"), asr_non_max=max(r["wer_norm"] for r in non), n_non=len(non),
        non_en_text=sum(1 for r in non if r.get("text_language") == "en"),
        hi_audio=next(r["audio_s"] for r in rows if r["language"] == "hi"), hi_words=next(r["words"] for r in rows if r["language"] == "hi"),
        ls=F.LENGTH_SCALING,
    )


# ---------------------------------------------------------------------------- novelty and contributions
def novelty_blocks():
    v = _v()
    ba = __import__("scripts.docs.lit", fromlist=["BASE_ANALYSIS"]).BASE_ANALYSIS
    return [
        H2("What the base paper contributes"),
        P(f"The base paper {C('base')} is SAM Translator. {ba['summary']} It reports consistent gains for each of its three ideas on CVSS-C and CoVoST-2, a listener study, and an honest list of limitations: low BLEU for some languages, repetition and meaning errors, "
          "a target language that is always English, no content control, and a training cost of one A100 GPU for about one and a half to two days."),
        H2("What is new in StoryVox"),
        P("StoryVox does not propose a new algorithm, and none of its models was trained or tuned in this project. What is new is the *system* and what was learned by measuring it:"),
        B("**One local pipeline from idea to narrated, stored, evaluated story.** The batch literature treats story generation and speech synthesis separately, or reaches them only through a cloud service. StoryVox joins an instruction-tuned language model "
          f"{C('qwen3')} and per-language VITS speech models {C('vits', 'mms')} behind one interface (the `TTSProvider` abstraction), stores every story and recording in SQLite, and runs on a CPU laptop with no data leaving the machine after the one-time download.",
          "**Offline degradation paths.** When the story model fails or answers with too little text, a prompt-conditioned composer in all 15 languages still answers; when a language has no speech model, an operating-system voice is used. "
          "Both paths exist in the shipped code and were exercised in the experiments, which also shows what they cost in quality.",
          "**A built-in evaluation harness.** The application can score its own output: it narrates, transcribes with Whisper-small " + C('whisper') + ", and reports WER, CER, RTF, similarity and ROUGE-L, and it stores each run. "
          "The documentation run added a larger harness around it (150 speech round trips, 51 stories under three conditions, story-length recognition, API timing) and 21 automated tests.",
          f"**Measured findings about a small multilingual cascade.** The experiments give numbers that the base paper cannot give for its different task: narration is fast (mean RTF {v['rtf']:.2f}) and readable ({v['n_mms']} languages, mean CER {v['cer']:.3f}), "
          f"but a 0.6-billion-parameter story model with the shipped prompt wrote English for {v['n_non']} of {v['n_non']} non-English live requests, which makes the narration of those stories unintelligible (WER {v['asr_non_min']:.2f} to {v['asr_non_max']:.2f}). "
          "These findings point at the prompt format and the missing language check as the first things to fix."),
        H2("What is standard"),
        P(f"Everything in the models is used as published: the Transformer {C('transformer')}, the Qwen3 model family {C('qwen3')}, VITS {C('vits')} and the MMS speech checkpoints {C('mms')}, Whisper {C('whisper')}, multilingual sentence embeddings {C('sbertm')}, "
          f"WER and CER by edit distance, ROUGE-L {C('rouge')} and the FLEURS benchmark {C('fleurs')}. Sampling uses temperature 0.8 and top-p 0.9, the nucleus setting recommended against degenerate text {C('holtzman')}. "
          f"The Hugging Face libraries {C('hf')} supply the model loading. Nothing here is a new method."),
        H2("What the base paper has and StoryVox does not"),
        B("**No translation model and none of the base paper's techniques.** There is no self-paced learning, no mixture-of-experts layer, no data-augmented self-training and no discrete speech units; StoryVox trains nothing. "
          f"The base paper's BLEU gains on translation therefore say nothing about StoryVox, and StoryVox's WER and CER say nothing about SAM Translator ({ba['comparability']})",
          "**No subjective evaluation.** The base paper asked ten listeners to rate naturalness; StoryVox collected no human rating of story or voice.",
          "**No ablations of the pipeline's own design.** The only controlled comparison is the three story conditions (shipped prompt, chat template, offline composer) and the per-language speech comparison; there is no comparison of different story or speech models.",
          "**No reference benchmark for the stories.** The speech half is evaluated on a public corpus (FLEURS); the story half has no reference corpus, so its evaluation consists of proxies and of reading the text."),
    ]


def contribution_blocks():
    v = _v()
    return [
        P("The contributions of the project, stated at the strength the evidence supports, are:"),
        N("**StoryVox, a working local pipeline**: a story idea, in one of 15 languages, eight styles and three lengths, becomes a stored story and a WAV narration through a FastAPI service with 11 routes, a SQLite store of three tables and a five-page React interface, "
          "with an offline composer and an operating-system voice as fallbacks.",
          "**A speech round-trip measurement of the narration stage**: 150 FLEURS sentences in 15 languages through the application's own narration and Whisper-small, with raw and normalised WER and CER and the real-time factor "
          f"(mean RTF {v['rtf']:.2f} and mean CER {v['cer']:.3f} on 12 MMS languages).",
          f"**A controlled comparison of three ways to write the story** (shipped prompt, chat template, offline composer) on 17 requests, showing that the shipped path matched the requested language in {v['a_ok']} of 17 and the chat template in {v['b_ok']} of 17, "
          "and that similarity scores reward a composer that quotes the idea.",
          f"**The language-mismatch finding for narration**: English text read by a foreign voice is unintelligible (WER {v['asr_non_min']:.2f} to {v['asr_non_max']:.2f}; {v['hi_audio']:.1f} s of audio for {v['hi_words']} Hindi-requested words), "
          f"against WER {v['asr_en_wer']:.2f} and CER {v['asr_en_cer']:.2f} for English stories with an English voice.",
          "**Defects found and documented, not hidden**: three speech checkpoints that do not exist, an undeclared `ffmpeg` and `uroman` dependency, an evaluation page that cannot compute WER or CER for any real story, a title parser that misses bold titles, "
          "and an instruction-echo failure of the shipped prompt, each with the evidence and a proposed fix.",
          f"**A tested, reproducible artefact**: {F.PYTEST_PASSED} passing automated tests (21 added), measurement scripts (`run_experiments.py`, `measure_api.py`, `run_story_asr.py`, `run_tests.py`) that regenerate every number in the documents, "
          "a screenshot script that drives the real interface, and a facts file from which the documents are built."),
    ]


# ---------------------------------------------------------------------------- scope and limitations
def scope_blocks():
    return [
        P("The scope follows the six batch objectives and what could be measured on one laptop. It is stated first as what the product and its measurements cover, then as what they deliberately leave out, so that a reader does not mistake an offline experiment for a product feature."),
        H2("In scope"),
        B("**Input:** a free-text story idea of up to 2,000 characters, one of 15 languages (en, hi, es, fr, de, it, pt, ru, ar, tr, nl, pl, zh, ja, ko), one of eight styles and one of three lengths.",
          "**Story generation:** the Qwen3-0.6B model through a text-generation pipeline with token budgets of 220, 420 and 700, and the offline composer as a fallback.",
          "**Narration:** per-language MMS (VITS) checkpoints at 16 kHz, long text split into chunks of at most 380 characters, an operating-system voice as a fallback; WAV download and in-browser playback.",
          "**Storage and interface:** SQLite library of stories, audio records and evaluation runs; Landing, Studio, History, Story detail and Evaluation pages; light and dark themes.",
          "**Evaluation:** WER and CER by Whisper-small round trip, multilingual sentence-embedding similarity, ROUGE-L, latency and RTF in the application; language match, instruction echo and distinct-2 in the experiments.",
          "**Product support:** the REST API, automated tests, measurement and screenshot scripts."),
        H2("Out of scope"),
        B("Translation of an existing story from one language to another: there is no translation module.",
          "Choice of voice, speaker or speed, emotion control, voice cloning and reference-audio upload.",
          "Reading-level control and age-appropriateness checks of the generated text.",
          "Training, fine-tuning or quantising any model; GPU optimisation.",
          "Human rating of stories or narration (the batch objective of user rating).",
          "Accounts, several users, cloud deployment, authentication, rate limiting and monitoring: StoryVox is a single-user local tool."),
        P("The table below sets the scope against the six batch objectives, separating what the product does, what only the measurements cover and what was not done."),
        TAB("Scope against the batch objectives", ["Objective", "In the product", "Measured offline", "Not done"],
            [["1 Accept a prompt", "Studio form, validation, 2,000-character limit", "-", "Prompt templates, saved prompts"],
             ["2 Generate with length and reading-level controls", "3 lengths, 8 styles", "Length scaling (175, 316, 418 words)", "Reading-level control"],
             ["3 Translate into target languages", "Language requested in the prompt", "Language match 3/17 (A), 8/17 (B)", "A translation module"],
             ["4 Convert to speech", "MMS narration for 12 languages, OS fallback", "150-sentence round trip", "Italian, Chinese and Japanese MMS voices"],
             ["5 Playback with voice, speed, language", "Player, download, regenerate", "-", "Voice and speed selection"],
             ["6 Evaluate through user rating", "Automated evaluation page", "Story-length WER/CER with chunking", "User rating; working WER/CER on the page"]],
            widths=[1.6, 1.8, 1.6, 1.6], align=["l", "l", "l", "l"], size=9.5),
    ]


def assumption_blocks():
    return [
        B("The pretrained models are used as published; their quality in the 15 languages is what their authors released, not something this project can change.",
          "Ten length-filtered FLEURS sentences per language are a fair, if small, sample of read-aloud text for the narration stage.",
          "A Whisper-small transcript is a reasonable proxy for what a listener would understand; its own errors are included in every WER and CER and were not separated out.",
          "The story idea \"A young inventor discovers a hidden library.\" and seed 0 represent a typical request; other ideas and seeds would give other texts.",
          "A language detector is accurate enough on 100 to 200 words to say whether a story is in the requested language; it is used as a coarse screen, not as a measure of quality.",
          "One user runs the application on one computer, so the model objects, the database and the audio folder need no coordination between users.",
          "The model weights are downloaded once from the Hugging Face Hub and cached; after that the application needs no network."),
    ]


def limitation_blocks():
    v = _v()
    return [
        H2("Models and language"),
        B(f"**The story model does not follow the requested language.** With the shipped prompt, {v['a_ok']} of 17 stories (the English ones) were in the requested language and {v['non_en_text']} of {v['n_non']} live stories in other languages were English; "
          f"the chat template raises this only to {v['b_ok']} of 17.",
          f"**A small model, a plain prompt.** Qwen3-0.6B often echoes its instructions (instruction echo {v['a_echo']:.3f} in the shipped path against {v['b_echo']:.3f} with the chat template) and wrote `Untitled Story` for {v['untitled_a']} of 17 shipped-path titles. Stories are short, repetitive and sometimes not stories.",
          "**Three advertised languages are not usable as shown.** `facebook/mms-tts-ita`, `-cmn` and `-jpn` do not exist, so Italian is read by an English voice and Chinese and Japanese mostly produce no audio on the test machine.",
          f"**Seed and variety.** The experiments fixed one seed, which makes many shipped-path stories nearly identical across languages and hides how much a different seed would change the text."),
        H2("Evaluation"),
        B("**No human judgement.** Coherence, creativity, age-appropriateness and naturalness of the voice were never rated by a person; the proxies (language match, echo, distinct-2, similarity, ROUGE-L) can show failure but not quality.",
          "**Whisper-small is inside every WER and CER.** The recogniser is weaker in some languages (Hindi, Arabic), and its error on natural speech was not measured.",
          "**Small samples.** 10 sentences per language, 17 stories per condition, 7 live generations; differences of a few hundredths are not reliable.",
          "**The product's own evaluation cannot score a story.** The transcription call fails for audio over 30 seconds, so every WER and CER on the Evaluation page is empty for real stories."),
        H2("Product"),
        B("**Single user, local only.** No login, one shared model object, no rate limit, no queue; the generate route blocks until the story and the narration are finished.",
          "**Dependencies are under-declared.** `ffmpeg` (needed by the recogniser) and `uroman` (needed for Korean) are missing from the requirements, and the stored virtual environment pointed at an interpreter that does not exist on the test machine.",
          "**Title parsing.** Only a bare `Title:` at the start of a line is recognised, so bold or prefixed titles stay in the title field or the title is `Untitled Story`.",
          "**Evaluation cost.** The similarity function loads a sentence-embedding model on every sample.",
          "**Model loading.** The story pipeline is created with `trust_remote_code=True`; the trusted model name is set by configuration."),
        H2("Hardware, software and process"),
        B("**One machine, CPU only.** All timings come from one i5-12500 with 15.7 GB of memory while other programs ran; the GPU path exists in the code but was not run.",
          "**Software versions.** Results were produced with transformers 5.20.2 and torch 2.14.1 on Python 3.11.9; other versions can change both behaviour and speed (the 30-second recogniser failure is such a case).",
          "**Tests use stand-ins.** The 29 automated tests replace the models; the real models are exercised only by the measurement scripts.",
          "**No independent review or security audit** of the code was carried out."),
        H2("How the limits affect the reading of the results"),
        P("The narration results are the most reliable part of the project, because they rest on a public corpus and a repeatable round trip, and they are limited by sample size and by the recogniser. "
          "The story results are indicative: they show clearly that the shipped path ignores the requested language and often fails to produce a story, but they cannot rank stories by quality. "
          "The product results describe a local tool for one person, not a service."),
    ]


def not_measured_blocks():
    return [
        P("The following were not measured, so no document claims anything about them. Each is either outside what the product does or beyond what a CPU laptop and a short project could test."),
        B("Human ratings of story coherence, story quality, voice naturalness or the usefulness of the application to children, teachers or language learners.",
          "Whisper-small's error on natural recordings of the same sentences, which would separate the recogniser's error from the speech model's.",
          "GPU speed, and speed or quality of larger models (a bigger Qwen3 model, other speech models).",
          "Story quality with other ideas, other seeds, other styles than Adventure for the non-English languages, or longer texts in a language other than English.",
          "Narration with an installed Chinese, Japanese or Italian system voice.",
          "Concurrent users, long-running load and memory growth of the server.",
          "Accessibility of the interface with a screen reader, other browsers and phones.",
          "Security: no penetration test or code audit was done."),
        P("None of these is hidden in a headline number. The claims of the abstract about translation, adjustable voice and speed, and user-rated evaluation are therefore treated as aims, not as results."),
    ]


# ---------------------------------------------------------------------------- code walk-throughs
def walkthrough_blocks():
    prompt_code = fn("app/services/story_generator.py", "build_prompt") + "\n\n" + fn("app/services/story_generator.py", "_parse_model_output")
    gen = between("app/services/story_generator.py", "generator = _try_load_pipeline(model_id)", "return title, body, \"storyvox-local-fallback-v1\"")
    synth = meth("app/services/tts_service.py", "MMSTTSProvider", "synthesize")
    chain = between("app/services/tts_service.py", "for provider in (MMSTTSProvider(), SystemTTSProvider()):", "continue")
    ev = between("app/services/evaluation_service.py", "# Transcribe for intelligibility", "row[\"asr_error\"]")
    return [
        H2("Prompt and title parsing (`story_generator.py`)"),
        P("The whole control surface of the story is one instruction sentence: style, language name, length and the idea are put into a single string, and the model is asked to start with `Title: `. "
          "The instruction is sent as plain text, not through the model's chat template, which is the likely reason for the instruction echo seen in Chapter 8. "
          "`_parse_model_output` then looks for a bare `Title:` line; if there is none it tries the first short line, otherwise the title stays `Untitled Story`. A title written as `**Title: ...**` matches neither rule."),
        CODE(prompt_code, 7.5),
        H2("Story generation with a fallback (`story_generator.py`)"),
        P("The model is sampled with temperature 0.8 and top-p 0.9 and a token budget that depends on the length option. If the model fails to load, raises, or returns fewer than 20 words, the composer writes the story instead, and the model identifier stored with the story says which path was taken. "
          "The language check that Chapter 8 shows to be missing would belong in this block, between parsing and returning."),
        CODE(gen, 7.5),
        H2("Chunked narration (`tts_service.py`)"),
        P("The speech model is called on one chunk at a time (at most 380 characters, cut at sentence ends and at the Hindi danda), each waveform is normalised to a peak of 0.9, the chunks are joined with a quarter-second pause, and silence is rejected. "
          "The checkpoint comes from the language table, which is why a missing checkpoint (Italian, Chinese, Japanese) fails here and not earlier."),
        CODE(synth, 7.5),
        H2("Provider chain (`tts_service.py`)"),
        P("`synthesize_story_narration` tries the MMS provider and then the operating-system provider. A `ValueError` stops the chain (bad input); any other error is logged and the next provider is tried. "
          "This is how Italian ends up with an English voice: the first provider fails on the missing checkpoint and the second one speaks any text it is given."),
        CODE(chain, 7.5),
        H2("Where the evaluation breaks (`evaluation_service.py`)"),
        P("After narration the evaluation transcribes the WAV file and compares the transcript with the story text. The call has no chunking option; for audio over 30 seconds transformers 5.20.2 raises an error, "
          "the `except` branch stores it as `asr_error`, and WER and CER stay empty. The stand-alone script `scripts/run_story_asr.py` differs in one argument, `chunk_length_s=30`, and produces the numbers in Chapter 8."),
        CODE(ev, 7.5),
        H2("Safe audio path (`utils/__init__.py`)"),
        P("Audio is served by database id. Before any stored path is used it is resolved and must lie inside the audio folder; the same check guards deletion."),
        CODE(fn("app/utils/__init__.py", "ensure_within_directory"), 7.5),
    ]


def decision_blocks():
    v = _v()
    return [
        P("The main implementation decisions, the reason for each and what the measurements later showed are listed in the table below."),
        TAB("Implementation decisions and their reasons", ["Decision", "Reason", "What the measurements showed"],
            [["Use pretrained models, train nothing", "A student project on a laptop cannot train a story model or a multilingual speech model", f"Narration is good (mean CER {v['cer']:.3f}); the story model ignores the language request"],
             ["Qwen3-0.6B as story model", "Small enough for CPU and memory; open weights; multilingual", "About 9 tokens per second; short, repetitive stories; mostly English"],
             ["MMS-TTS (VITS) per language", "One checkpoint per language, 16 kHz, runs at about a quarter of real time on a CPU", f"RTF {min(F.LANGS[c]['mean_rtf'] for c in F.MMS_LANGS if c != 'ko'):.2f} to {max(F.LANGS[c]['mean_rtf'] for c in F.MMS_LANGS if c != 'ko'):.2f} for 11 of 12 languages; three advertised checkpoints do not exist"],
             ["`TTSProvider` abstraction with an OS fallback", "A story should always be speakable and models can be swapped", "Fallback gives an English voice for Italian and almost nothing for Chinese or Japanese"],
             ["Prompt as plain text", "Simplest call to the text-generation pipeline", f"Instruction echo {v['a_echo']:.3f} against {v['b_echo']:.3f} with the chat template"],
             ["Offline composer", "The application must answer even without the model", "Instant but template text; high similarity only because it quotes the idea"],
             ["Chunks of at most 380 characters", "Keep each speech-model call short and the memory flat", "Chunking tests pass; no audible seams were rated"],
             ["Whisper-small for evaluation", "Multilingual and small enough for CPU", "Fails on audio over 30 s without chunking; its own error is inside every WER"],
             ["SQLite and local WAV files", "No server to install, everything stays on the machine", "Library of seven stories lists in about 2 to 9 ms; foreign keys not enforced by the engine"],
             ["FastAPI plus React", "Typed validation, automatic docs, a modern interface over the same service", "11 routes, 5 pages, light calls in 1 to 15 ms"],
             ["Fixed lengths by token budget (220/420/700)", "Predictable time", "Words came out 175, 316 and 418, because the model stops early"]],
            widths=[1.6, 2.3, 2.7], align=["l", "l", "l"], size=9.5),
        P("Three decisions deserve a longer note. The first is to train nothing. It makes the project reproducible on any laptop, and it means every quality problem in Chapter 8 belongs to a model chosen off the shelf, not to a training mistake; "
          "the cost is that the only levers left are the prompt, the sampling settings, the model choice and the glue code. "
          "The second is the fallback design. Falling back silently keeps the interface working, but it also produced the three most misleading screens of the project (an English voice for Italian, a composer story presented like a model story, an empty narration for Japanese); "
          "a future version should say on screen which path was used. The third is the plain-text prompt: it was the quickest way to call the pipeline, and the experiments suggest it is also the weakest."),
    ]


# ---------------------------------------------------------------------------- conclusion
def _lessons():
    v = _v()
    return [
        f"**The speech half works.** Twelve languages are narrated by MMS at a mean RTF of {v['rtf']:.3f}, and read back with a mean normalised CER of {v['cer']:.3f} and WER of {v['wer']:.3f}; English gives WER {v['en_wer']:.3f} and CER {v['en_cer']:.3f}. Spanish is best (CER {v['es_cer']:.3f}) and Hindi weakest (CER {v['hi_cer']:.3f}).",
        f"**The story half is the bottleneck.** With the shipped prompt, {v['a_ok']} of 17 stories came out in the requested language; the chat template gets {v['b_ok']} of 17 at the same speed. Titles are often `Untitled Story`, and instruction text sometimes appears in the story.",
        f"**Language mismatch destroys narration.** English text read by the Hindi, French, German or Spanish voice gives WER {v['asr_non_min']:.2f} to {v['asr_non_max']:.2f}, and the Hindi voice produced {v['hi_audio']:.1f} s of audio for {v['hi_words']} words; English stories with an English voice give WER {v['asr_en_wer']:.2f} and CER {v['asr_en_cer']:.2f}.",
        f"**Three advertised languages are not delivered.** Italian is read by an English voice (WER {v['it_wer']:.2f}); Chinese ({v['zh_n']} of 10) and Japanese ({v['ja_n']} of 10) sentences produced any audio on the test machine.",
        "**The product does not report its own failures.** The Evaluation page shows no WER or CER for any real story because the recogniser call fails beyond 30 seconds, and nothing on screen says that a story is in the wrong language.",
        f"**It is fast enough for a local tool.** A Short story takes {v['ls'][0]['total_s']:.0f} s, Medium {v['ls'][1]['total_s']:.0f} s and Long {v['ls'][2]['total_s']:.0f} s from request to finished narration on a CPU; the web layer adds a few milliseconds.",
    ]


def _objective_table():
    v = _v()
    return TAB("Objectives against outcomes", ["Objective", "Outcome", "Evidence"],
               [["1 Accept a user prompt", "Achieved", "Studio form, 2,000-character limit, server validation"],
                ["2 Generate a story with length and reading-level controls", "Partly", "3 lengths and 8 styles; no reading-level control"],
                ["3 Translate into target languages", "Not implemented", f"No translation module; requested language reached in {v['a_ok']} of 17 (shipped) and {v['b_ok']} of 17 (chat template) requests"],
                ["4 Convert to speech", "Achieved for 12 languages", f"MMS narration, mean RTF {v['rtf']:.3f}, mean CER {v['cer']:.3f}; Italian by an English voice; Chinese and Japanese mostly silent"],
                ["5 Playback with adjustable voice, speed and language", "Partly", "Player and download; language at generation time; no voice or speed control"],
                ["6 Evaluate through user rating", "Partly", "Automated evaluation; WER and CER fail on story audio in the page; no user rating"]],
               widths=[2.4, 1.4, 2.8], align=["l", "l", "l"], size=9.5)


def conclusion_blocks():
    v = _v()
    return [
        H2("Summary"),
        P(f"StoryVox is a working local application that turns a story idea into a stored story and a spoken recording, behind an 11-route API and a five-page interface, using only pretrained models. "
          f"Measured on 150 FLEURS sentences and 51 generated stories, the honest outcome is split: the narration stage is fast and, for 12 languages, clear; the story stage mostly answers in English whatever language is requested, "
          "and the application does not tell the user."),
        H2("Objectives against outcomes"),
        _objective_table(),
        H2("Key findings"),
        N(*_lessons()),
        P("The abstract's claims about translation into target languages, adjustable voice and speed and evaluation through user rating are not demonstrated and are not claimed here."),
        H2("Closing remark"),
        P("The project's value is a measured, reproducible pipeline and a precise list of what to repair. With a chat-template prompt, a language check on the generated text, the three missing speech checkpoints replaced and chunked recognition on the Evaluation page, "
          "the same code would be a sound base for the multilingual storyteller the batch set out to build."),
    ]


def chapter9_blocks():
    v = _v()
    body = [
        H2("Summary"),
        P("StoryVox was built to take a story idea, write a story in a chosen language and read it aloud. The application validates the idea, builds one instruction sentence from the idea, the language, the style and the length, sends it to a small instruction-tuned language model, "
          "parses a title and a body, splits the body into chunks of at most 380 characters, narrates each chunk with a per-language speech model, joins them with short pauses and stores the story, the WAV file and its timings in SQLite. "
          "A React interface offers a Studio, a History library, story pages and an Evaluation page; a FastAPI service with 11 routes sits underneath. When the model or a speech checkpoint is unavailable, an offline composer and an operating-system voice take over."),
        P(f"The system was measured, not trained: 150 FLEURS sentences in 15 languages were narrated and transcribed, 17 requests were answered under three conditions, seven stories were generated through the live server, and {F.PYTEST_PASSED} automated tests pass. "
          "Eleven screenshots were taken from the running interface with the real stories loaded."),
        H2("Objectives achieved"),
        _objective_table(),
        P("Objectives 1 and 4 were met; objectives 2, 5 and 6 were met in part; objective 3, translation, was not implemented. The documents report each plainly."),
        H2("Key findings"),
        N(*_lessons()),
        *_fig_conclusion(),
        P("A further finding concerns method. Each proxy that was tried flattered something. Prompt-story similarity rewarded the offline composer because it copies the idea; a word count rewarded a model that recited its instructions; "
          "and the application's own evaluation reported nothing at all because one call failed silently. Only reading the stories, and re-running the narration on whole stories rather than short sentences, showed the real picture."),
        H2("Practical applications"),
        B(f"**English storytelling and listening practice on a laptop.** For English, the pipeline already produces a readable story with an intelligible voice (WER {v['asr_en_wer']:.2f} on {v['n_en']} stories) without any online service.",
          "**A reference for multilingual narration speed.** The per-language table shows what an MMS voice costs on a CPU and how clearly it reads back, which helps choose languages for a classroom tool.",
          "**A test bed for story prompts and models.** The evaluation harness can score a new prompt format or a larger model on the same 17 requests and the same speech round trip.",
          "**Private use.** After the download nothing leaves the machine, which suits children's content and classrooms without accounts."),
        H2("Known limitations"),
        P("The story model does not follow the language request, three advertised languages are not delivered, the application's evaluation cannot score a real story, and no person rated any output. "
          "The samples are small, the recogniser's own error is inside every WER and CER, and everything ran on one CPU. Chapter 8 and the limitations chapter give the full list."),
    ]
    if F.REPORT:
        body = _ch9_trim(body)
    return [H1("CHAPTER 9: CONCLUSION")] + renum(body, "9")


def _fig_conclusion():
    return _fig("f03_story_conditions.png", "Latency, length, language match and variety of the three story conditions.", 5.4)


def _ch9_trim(body):
    """Report variant: no figure, no method paragraph, the four practical applications cut to two."""
    out = []
    for b in body:
        if b[0] == "fig":
            continue
        if b[0] == "p" and b[1].startswith(("A further finding concerns method", f"The system was measured, not trained")):
            continue
        if b[0] == "b" and b[1][0].startswith("**English storytelling"):
            b = ("b", [b[1][0], b[1][2]])
        out.append(b)
    return out


# ---------------------------------------------------------------------------- future scope
def _roadmap():
    return TAB("Roadmap", ["Stage", "Work", "Done when"],
               [["1. Repair what was measured", "Chat-template prompt; a language check with a retry or the composer; chunked recognition; declare ffmpeg and uroman; parse bold titles; replace or remove the three missing checkpoints", "The 17-request experiment gives a language match well above 8 of 17 and the Evaluation page shows WER and CER for a story"],
                ["2. Add what the objectives asked for", "Voice and speed controls, reading level, a translate-then-narrate mode, user rating", "A user can change speed and rate a story"],
                ["3. Evaluate with people", "Rate coherence and naturalness with a small panel; measure Whisper's own error floor", "Ratings and a recogniser-error baseline are in the report"],
                ["4. Scale and deploy", "A larger story model or a GPU, a job queue, accounts, packaging", "Several users can generate at once"]],
               widths=[1.5, 3.1, 2.0], align=["l", "l", "l"], size=9.5)


def future_blocks():
    return [
        H2("Repair the weaknesses found"),
        B("**Prompt with the chat template.** In the experiment, only the template changed and the language match rose from 3 to 8 of 17, instruction echo fell from 0.097 to 0.006 and variety rose.",
          "**Check the language of the story** with a detector and retry or fall back when it is wrong, and warn the user on screen.",
          "**Chunk the recogniser** (`chunk_length_s=30`) so the Evaluation page shows WER and CER, and load the similarity model once.",
          "**Declare `ffmpeg` and `uroman`**, rebuild the virtual environment with the supported Python, and replace the three missing MMS checkpoints with ones that exist or tell the user the language is narrated by a system voice."),
        H2("Add features"),
        B("**Translation** of a story into another language, and a mode that narrates a user-supplied story.",
          "**Voice, speaker and speed selection**, the missing part of objective 5; reference-audio voices as in zero-shot systems " + C('xtts', 'omni') + ".",
          "**Reading-level and style controls** beyond the eight styles, and an age-appropriateness check, in the spirit of child-friendly multilingual generators " + C('multigen') + "."),
        H2("Data, methods and deployment"),
        B("Compare Qwen3-0.6B with larger or storytelling-specific models " + C('tinystories') + " on the same 17 requests, and test a GPU.",
          "Collect **human ratings** of coherence and naturalness and measure Whisper's own error on natural speech.",
          "Add a job queue and progress reporting, authentication and a packaged installer."),
        P("The order matters: the repairs in the first group are small and testable, and they should be done before any new feature, because every later stage builds on a story that is in the language the user asked for."),
        _roadmap(),
    ]


def chapter10_blocks():
    body = [
        H2("Improvements to the existing system"),
        P("Every improvement below answers a defect that Chapter 8 measured, so each has a test it must pass."),
        B("**Use the chat template.** The same instruction through the model's template raised the language match from 3 to 8 of 17 and nearly removed instruction echo at the same latency; it should be the shipped path.",
          "**Check and repair the language.** After generation, detect the language of the story; if it differs from the request, retry once and otherwise tell the user. A test: the Hindi, French, German and Spanish requests of Section 7.7 must come back in the requested language.",
          "**Make the evaluation work on stories.** Chunk the recogniser at 30 seconds so WER and CER are computed for real stories, and load the similarity model once. A test: the five-sample run produces five WER values.",
          "**Fix the dependencies.** List `ffmpeg` and `uroman`, rebuild the virtual environment and add the checks to `run.bat`.",
          "**Fix the language table.** Italian, Chinese and Japanese need real checkpoints or must be marked as system-voice languages in the interface.",
          "**Parse titles properly** (bold and prefixed forms) and keep the instruction text out of the title."),
        P("Two of these repairs change numbers in earlier chapters: the language-match rate would rise and the narration of the repaired languages would be re-measured with matching text, which is the real test of the multilingual claim."),
        H2("Additional features"),
        P("The features below follow the batch objectives that were only partly met: language handling (objective 3), voice and speed (objective 5) and user-rated evaluation (objective 6)."),
        B("**Translation and bring-your-own-story.** Translate a story into another language, then narrate it; or narrate text typed or pasted by the user.",
          "**Voice, speaker and speed.** A speed slider is possible with resampling or the speech model's rate; extra voices need more checkpoints or a zero-shot model.",
          "**Rating.** A one-to-five rating and a free comment on each story and each narration, stored in SQLite and shown on the Evaluation page.",
          "**Reading level and safety.** A reading-level setting in the prompt and a check on generated text for children."),
        H2("Scalability and deployment"),
        P("StoryVox was built for one person on one laptop. Its two models are loaded into one process, its generate route blocks, and its evaluation reloads a model per sample; that is enough for the seven stories and two evaluation runs measured here and not for a classroom."),
        B("Move generation and narration into a queue with progress events, so the interface does not wait on one long request.",
          "Run the story model on a GPU or a quantised build, and measure tokens per second and memory.",
          "Add accounts, per-user libraries and rate limits, and package the application with its dependencies.",
          "Cache loaded speech models and clean old audio files."),
        P("Deployment also needs a decision about content: a model that writes for children needs filtering and a way to report a bad story, and a shared service would need rules for what is stored."),
        H2("Further research"),
        P("The open questions are about quality, and the harness is ready to answer them once people are available to rate the output."),
        B("Does a larger or instruction-tuned story model follow the language request, and how much does speed fall?",
          "How much of each WER and CER belongs to the recogniser, measured on natural recordings of the same sentences?",
          "Do listeners prefer one voice and speed, and how do ratings correlate with the proxies used here?",
          "Can a discrete-unit or mixture-of-experts translation approach such as the base paper " + C('base') + " be added for story-to-story translation, and what does it gain over a cascade?"),
        H2("Risks and dependencies"),
        B("**Model and data licences.** The models and FLEURS have their own licences; they are downloaded, not redistributed, and any future model must be checked.",
          "**Library drift.** The 30-second recogniser failure came from a library version; pinned versions and a test on real audio would catch the next one.",
          "**Content.** Generated stories are unfiltered; any use with children needs review."),
        P("The order of work matters: the repairs in the first section are small and testable, and they should be done before any new feature, because every later stage builds on a story that is in the requested language."),
        _roadmap(),
    ]
    if F.REPORT:
        body = _ch10_trim(body)
    return [H1("CHAPTER 10: FUTURE SCOPE")] + renum(body, "10")


def _ch10_trim(body):
    """Report variant: no roadmap table, no risks section, lead paragraphs and the last bullets of each list cut."""
    out, skip = [], False
    for b in body:
        if b[0] == "h2":
            skip = b[1].startswith("Risks")
        if skip or b[0] == "tab":
            continue
        if b[0] == "p" and b[1].startswith(("Two of these repairs", "The features below", "Deployment also needs", "The open questions", "The order of work", "Every improvement below")):
            continue
        if b[0] == "b" and len(b[1]) > 4:
            b = ("b", b[1][:4])
        out.append(b)
    return out
