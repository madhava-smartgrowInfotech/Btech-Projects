"""Chapter 1: Introduction."""

from . import facts as F
from .blocks import B, EQ, H1, H2, N, P, TAB
from .refs import N as C


def trim(blocks, drop=(), drop_sections=(), replace=None, table_rows=None):
    """Report-mode trimming helper (shared by the other chapter modules). drop: block-text prefixes to remove; drop_sections: heading
    prefixes whose whole section is removed; replace: {prefix: block}; table_rows: {caption prefix: keep(row)}."""
    replace = replace or {}
    table_rows = table_rows or {}
    out, skip_level = [], None
    for b in blocks:
        if b[0] in ("h1", "h2", "h3"):
            lvl = int(b[0][1])
            if skip_level is not None and lvl <= skip_level:
                skip_level = None
            if skip_level is None and any(b[1].startswith(x) for x in drop_sections):
                skip_level = lvl
        if skip_level is not None:
            continue
        v = b[1]
        k = v[0] if isinstance(v, list) and v else (v if isinstance(v, str) else "")
        if any(k.startswith(x) for x in drop):
            continue
        hit = next((x for x in replace if k.startswith(x)), None)
        if hit:
            if replace[hit] is not None:
                out.append(replace[hit])
            continue
        if b[0] == "tab":
            cap = next((x for x in table_rows if b[1].startswith(x)), None)
            if cap:
                b = ("tab", b[1], b[2], [r for r in b[3] if table_rows[cap](r)], b[4], b[5], b[6])
        out.append(b)
    return out


def blocks():
    A, Bc = F.STORY_SUMMARY["A_app_raw_prompt"], F.STORY_SUMMARY["B_chat_template"]
    en = F.LANGS["en"]
    ls = {r["length"]: r for r in F.LENGTH_SCALING}
    out = [
        H1("CHAPTER 1: INTRODUCTION"),
        H2("1.1 Introduction to the Project Domain"),
        P("Storytelling is one of the oldest ways of teaching and one of the most effective: children learn vocabulary, values and sequence from stories, adults use them to learn languages, and every culture keeps its own. "
          "Producing a good story, however, takes a writer, and producing it in several languages takes a writer, a translator and, if it is to be heard rather than read, a narrator for each language. "
          "That cost is the reason why most multilingual story material is limited to a few widely spoken languages and a few fixed titles."),
        P(f"Two areas of artificial intelligence now make it possible to attack the cost. Natural language processing (NLP) with large language models {C('transformer')} can write coherent narrative text from a short instruction, "
          f"and neural text-to-speech (TTS) {C('vits')} can turn text into natural-sounding audio. Joining the two gives an end-to-end experience from a single prompt: a story idea goes in and a spoken story comes out. "
          f"The difficulty is to do it for many languages, because a model that writes fluent English may write poorly or not at all in another language, and because speech models exist for a language only when someone has trained one {C('mms')}."),
        P("Terms used throughout: a **prompt** or **story idea** is the user's short instruction; a **story model** is the language model that writes the story; a **speech model** turns text into a waveform; "
          "a **recogniser** is an automatic speech recognition (ASR) model that turns audio back into text; a **round trip** synthesises text and transcribes it again to check that the speech is intelligible; "
          "**WER** and **CER** (word and character error rate) measure how far the transcript is from the original text; and the **real-time factor (RTF)** is synthesis time divided by audio duration, so values below 1 mean faster than real time."),
        H2("1.2 Background and Motivation"),
        P(f"The batch's base paper is \"SAM Translator: Self-paced learning and mixture-of-experts for cross-lingual text-to-speech translation\" by Tran and Sakti {C('base')}. "
          f"It translates text in one language into speech in English with a direct text-to-unit model: an mBART encoder-decoder {C('mbart')} with sparse mixture-of-experts layers {C('moe')}, trained with a self-paced curriculum {C('spl')} "
          "and extra synthetic data (data-augmented self-training), whose speech units are turned into audio by a vocoder, and it measures the result by transcribing the speech and computing BLEU on the CVSS-C and CoVoST-2 corpora. "
          "It is a research model trained on a data-centre GPU for one and a half to two days, aimed at better translation quality for low-resource languages."),
        P("The batch abstract takes its motivation from that paper but sets a different goal: not translation research, but an application that a student, a teacher or a parent can run to get a story in a chosen language and hear it read aloud. "
          "We therefore treat the base paper as the reference for multilingual speech output and for evaluating speech by transcription, and we build the application from pretrained components that run on an ordinary computer: "
          f"Qwen3-0.6B {C('qwen3')} for the story, MMS-TTS {C('mms')} for the voice, and Whisper {C('whisper')} to check the voice. "
          "None of the base paper's training techniques is implemented here, and Chapters 2 and 8 state plainly why its BLEU scores cannot be compared with the error rates reported in this report."),
        P("The motivation is practical. A tool that runs locally keeps the child's prompts and the stories on the family computer, works without a subscription after the models are downloaded once, "
          "and can be inspected and measured end to end. That last point matters: a pipeline of three models can fail at any joint, and a user needs to know, with numbers, where it works and where it does not. "
          "This report therefore measures the pipeline in 15 languages and says what it found, including that the 0.6-billion-parameter story model often answers in English whatever language was asked for."),
        H2("1.3 Problem Statement"),
        P("The batch problem statement lists four difficulties: producing multilingual stories by hand requires writers and narrators for every language; generic text-to-speech sounds mechanical and unsuited to narrative delivery; "
          "low-resource Indian languages have limited synthesis support and poor voice quality; and existing tools handle either text generation or speech synthesis, not both together. "
          "The need is a single system that generates a story from a prompt and narrates it naturally in the user's chosen language."),
        P("We restate the problem as one that can be tested. **Given a short story idea, a target language, a style and a length, build a system that writes a story, reads it aloud in the chosen language on a CPU-only computer, keeps the result, "
          "and measures with real numbers how well each stage does: whether the story is in the requested language, whether the speech is intelligible when transcribed again, how fast each stage runs, and how the overall response time grows with story length.**"),
        P("In symbols, let x be the idea, l the language, s the style and n the length. The story model produces text t = G(x, l, s, n); the speech model produces a waveform a = S(t, l) of duration d(a) in a synthesis time T; "
          "the recogniser produces a transcript t' = R(a, l). The measured quantities are:"),
        EQ("RTF = T / d(a),     WER = (S + D + I) / N  between t and t',     CER = the same count over characters"),
        P("where S, D and I are the word substitutions, deletions and insertions needed to turn t' into t and N is the number of words in t. A story that is written in the wrong language is not penalised by RTF, "
          "but it is by WER and CER, because the speech model for l reads text it was not trained on; this is why the three numbers are reported together."),
        H2("1.4 Need for the Proposed System"),
        B("**One pipeline, not two tools.** Story generators produce text and speech tools read text; a user must carry the text from one to the other and cannot compare the result across languages. StoryVox runs both in one request and stores the story with its audio.",
          "**Many languages from one interface.** The system offers 15 languages with a single dropdown and a per-language speech model, so adding a language means adding a checkpoint name, not building a new application.",
          "**Local and private.** Models run on the user's CPU; prompts, stories and audio stay in a local SQLite database and a local folder, with no account and no cloud call after the one-time model download.",
          "**Honest measurement built in.** An evaluation page measures round-trip WER and CER, topic similarity, ROUGE-L, latency and RTF on real outputs instead of showing pre-filled numbers.",
          "**Graceful degradation.** If the story model fails or returns too little text, an offline composer still returns a story; if the multilingual speech model is unavailable, an operating-system voice is used. The user always gets a result, and the model name is shown so the fallback is never hidden."),
        H2("1.5 Project Objectives"),
        P("The six objectives set for the batch, and where this report addresses each, are listed in the table below. The outcome column is the short version; Chapter 8 gives the measurements and Chapter 9 the full verdict."),
        TAB("Objectives of the project and their outcome", ["No.", "Objective", "Outcome (summary)"],
            [["1", "Accept a user prompt specifying theme, characters and target language", "Achieved: Studio page with an idea box (2,000-character limit), 15 languages, 8 styles; input is validated by the API."],
             ["2", "Generate coherent narrative text with controls for length and reading level", f"Partly: 3 lengths (220, 420 and 700 new tokens) and 8 styles; no reading-level control. Short, Medium and Long stories took {ls['Short']['gen_s']:.0f}, {ls['Medium']['gen_s']:.0f} and {ls['Long']['gen_s']:.0f} s to write on the CPU."],
             ["3", "Translate the story into the selected target languages", f"Not implemented as translation: the language is requested in the prompt and the model answers in it directly. With the shipped prompt the text was in the requested language in {F.pct(A['language_match_rate'], 0)} of 17 cases."],
             ["4", "Convert the story into natural speech with multilingual TTS", f"Achieved for {len(F.MMS_LANGS)} languages with MMS (mean RTF {F.MMS_MEAN_RTF:.2f}, mean CER {F.pct(F.MMS_MEAN_CER)}); Italian, Chinese and Japanese use an English-only OS voice."],
             ["5", "Provide playback with adjustable voice, speed and language selection", "Partly: browser player with play, seek and WAV download; language chosen when generating; no voice or speed selection."],
             ["6", "Evaluate coherence, translation quality and naturalness through user rating", "Partly: automated evaluation (WER, CER, similarity, ROUGE-L, RTF); no user-rating collection, so naturalness was not rated by people."]],
            widths=[0.45, 2.9, 3.2], align=["c", "l", "l"], size=10),
        H2("1.6 Scope of the Project"),
        P("**In scope.** Entering a story idea; choosing one of 15 languages, one of 8 styles and one of 3 lengths; generating the story with Qwen3-0.6B or, as a fallback, the offline composer; narrating it with the MMS speech model for the language or an operating-system voice; "
          "saving stories, audio files and evaluation runs in SQLite and on disk; a history page to view, replay, download and delete; an evaluation page that runs the measurement pipeline; "
          "an API with 11 routes; and the tests and scripts that reproduce every number in this report."),
        P("**Out of scope.** Training or fine-tuning any model; translating an existing story; reading-level control; voice cloning and reference-audio upload; selecting voice or speed; collecting user ratings; user accounts; "
          "multi-user deployment; GPU-specific optimisation; and human evaluation of story quality or of voice naturalness."),
        H2("1.7 Project Contributions"),
        N(f"**A working end-to-end local pipeline.** A React web application with five pages over a FastAPI service with 11 routes and a SQLite store, covered by {F.PYTEST_PASSED} passing tests ({F.PYTEST_API} on the API and {F.PYTEST_UNIT} on helpers, the offline composer and edge cases).",
          "**A provider abstraction with visible fallbacks.** Speech goes through a `TTSProvider` interface with an MMS provider and an operating-system provider, and every story and audio record names the model that really produced it.",
          "**A round-trip speech measurement in 15 languages.** Ten FLEURS test sentences per language were synthesised with the application's own services and transcribed with Whisper-small, giving real-time factor, WER and CER per language (Chapter 8).",
          f"**A controlled look at the story model.** Three conditions (the shipped prompt, a chat-template variant and the offline composer) on 17 test cases show that the shipped path mostly answers in English, with a language match of {F.pct(A['language_match_rate'], 0)} against {F.pct(Bc['language_match_rate'], 0)} for the chat template.",
          "**Documented defects and dependencies.** The application's own evaluation cannot score story-length audio because the recogniser rejects clips over 30 seconds; three MMS checkpoints named in the configuration do not exist; ffmpeg and the uroman package are undeclared dependencies. Each is reproduced and reported."),
        P(f"In one paragraph, what the measurements show: the speech half of StoryVox works well and quickly (mean RTF {F.MMS_MEAN_RTF:.2f} over {len(F.MMS_LANGS)} languages, English WER {F.pct(en['wer_norm_corpus'])} and CER {F.pct(en['cer_norm_corpus'])} on the round trip), "
          f"while the story half is limited by the size of the model: a Short story takes about {ls['Short']['gen_s']:.0f} s to write and most requests for a non-English story come back in English, which the matching voice then reads badly. "
          "The honest conclusion is that the pipeline is complete and the speech is good, but the claim of a multilingual story generator holds today for a handful of languages only."),
        H2("1.8 Limitations and Assumptions"),
        B("**Small story model.** Qwen3-0.6B was chosen so that the whole system runs on a CPU. It often ignores the target language and the requested style, and sometimes repeats the instruction text; story quality was measured only with automatic proxies, and no person rated a story.",
          "**Language coverage.** MMS checkpoints exist for 12 of the 15 languages in the interface; Italian, Chinese and Japanese fall back to an operating-system voice that, on the test machine, has English voices only.",
          "**Evaluation limits.** The round trip mixes the speech model's error with Whisper-small's own error; Whisper's error floor on natural recordings was not measured. Test sets are small (10 sentences per language, 17 story prompts), so differences of a few points are not significant. WER is not reported for Chinese and Japanese.",
          "**Single machine.** All timings are from one CPU-only computer (12 threads, 15.7 GB). A GPU would change every latency but was not available.",
          "**Assumptions.** The user has a one-time internet connection to download model weights (several gigabytes), ffmpeg is installed for the recogniser, and prompts are in a language the story model understands.",
          "**Documentation environment.** The project's virtual environment pointed at a Python version that is no longer installed and the disk had little free space, so the measurements were run with the system Python 3.11.9; `run.bat` itself was not exercised."),
        H2("1.9 Organization of the Report"),
        P("Chapter 2 surveys the literature and analyses the base paper. Chapter 3 studies feasibility and Chapter 4 sets out the existing and proposed systems and the requirements. "
          "Chapter 5 gives the design: architecture, workflow, data flow and UML diagrams, the database and the user interface. Chapter 6 describes the methodology and implementation: "
          "the models, the prompt and chunking logic, the evaluation formulas, the API, error handling and how to install and run it. Chapter 7 reports testing. "
          "Chapter 8 presents every output screen, the measured results, the comparison with the base paper (stating where the two cannot be compared), failure analysis and the objectives against outcomes. Chapter 9 concludes and Chapter 10 sets out the future scope. "
          "The references and three appendices (important code, installation and user guide, additional screens) follow."),
    ]
    if F.REPORT:   # compact report variant: drop passages that the abstract and later chapters repeat
        out = trim(out, drop=("In one paragraph, what the measurements show", "The motivation is practical.", "In symbols, let x", "where S, D and I", "RTF = T / d(a)"))
    return out
