"""Chapter 6: Methodology and Software Implementation for StoryVox.

methodology_blocks() is also rendered (renumbered) by document 9, application_blocks() by document 12; blocks() is the report chapter.
Numbers come from facts.py (experiments/*/metrics.json); formulas are exactly what app/ and the experiment scripts compute.
StoryVox trains nothing, so "model architecture and training" is an inference configuration (Section 6.7).
"""

import os

from . import facts as F
from .blocks import B, CODE, EQ, FIG, H1, H2, H3, N, P, TAB
from .diagram_index import DIAGRAMS
from .refs import N as cite

_D = {k: (t, f, cap) for k, t, f, cap, _ in DIAGRAMS}


def _dg(key, caption=None, width=5.4):
    t, f, cap = _D[key]
    path = F.diag(f)
    return [FIG(path, caption or cap, width)] if os.path.exists(path) else []


def _fg(name, caption, width=5.6):
    path = F.fig(name)
    return [FIG(path, caption, width)] if os.path.exists(path) else []


def _gen(order):
    return next(r for r in F.API["generate"] if r["order"] == order)


def methodology_blocks():
    a, b_, c = (F.STORY_SUMMARY[k] for k in ("A_app_raw_prompt", "B_chat_template", "C_local_composer"))
    en, hi = F.LANGS["en"], F.LANGS["hi"]
    short, medium, long_ = F.LENGTH_SCALING
    st = F.STORY
    b = []

    # ------------------------------------------------------------------ 6.1
    b += [H2("6.1 Overall methodology"),
          P(f"StoryVox treats story narration as a cascade of pretrained models joined by ordinary software: a language model writes the text, a speech model reads it aloud, and, for the evaluation only, a recogniser and a sentence encoder measure the result. "
            f"The base paper {cite('base')} takes the opposite route for its task: it trains one end-to-end model (an mBART encoder-decoder with self-paced learning, a sparse mixture of experts and data-augmented self-training) to turn text in one language into speech in another, "
            "and reports translation quality by BLEU. StoryVox shares the goal of multilingual speech output and nothing of the method; it trains no model, so its methodology is a pipeline design and an evaluation protocol. The method has eight steps."),
          N("**Validate.** Reject an empty idea, an idea over 2,000 characters and an unknown language, style or length before any model runs.",
            "**Prompt.** Build one instruction from the style guidance, the language name, the paragraph target and the title rule, followed by the user's idea.",
            "**Generate.** Sample the story from Qwen3-0.6B " + cite("qwen3") + " with the length-dependent token budget; use the offline composer if the model is unavailable, fails, or returns fewer than 20 words.",
            "**Parse and save.** Take the `Title:` line (or a short first line) as the title and the rest as the body; count the words; store the row with the model id and the generation time.",
            "**Chunk and narrate.** Cut the body into chunks of at most 380 characters at sentence ends, synthesise each chunk with the MMS-TTS checkpoint of the language " + cite("mms", "vits") + ", normalise, join with pauses, reject silence, and fall back to the operating-system voice if needed.",
            "**Store and play.** Write the WAV file and the audio row (duration, model id, synthesis time, real-time factor); the browser streams it.",
            "**Evaluate.** Transcribe the narration with Whisper-small " + cite("whisper") + " and compare with the source text (WER, CER); compare the story with the idea (sentence-encoder cosine, ROUGE-L " + cite("rouge") + "); record latency and real-time factor.",
            "**Report.** Save every run as a database row and as JSON and CSV files; show the cards, the chart, the per-sample table and the method notes."),
          *_dg("algo", None, 5.2)]

    # ------------------------------------------------------------------ 6.2
    b += [H2("6.2 Dataset"),
          P("StoryVox needs no dataset to run: the input is the user's idea. Datasets appear only in the evaluation. "
            f"Narration is evaluated on **FLEURS** {cite('fleurs')}, Google's multilingual read-speech benchmark, using the text of its test split for the 15 languages of the application "
            "(English en_us, Hindi hi_in, Spanish es_419, French fr_fr, German de_de, Italian it_it, Portuguese pt_br, Russian ru_ru, Arabic ar_eg, Turkish tr_tr, Dutch nl_nl, Polish pl_pl, Mandarin cmn_hans_cn, Japanese ja_jp and Korean ko_kr). "
            "The dataset is released under CC BY 4.0; only the raw-transcription column of the `test.tsv` file is downloaded from the Hugging Face dataset repository, no audio is used and nothing is stored in the project. "
            f"For each language the first {en['n']} sentences that fit a length window (6 to 30 words; 12 to 70 characters for Chinese and Japanese, which have no spaces) and are not repeated were taken, giving {en['n'] * len(F.LANGS)} sentences in all."),
          TAB("Data used in the measurements.",
              ["Item", "Value"],
              [["Evaluation text", f"FLEURS test split, {en['n']} sentences per language, {len(F.LANGS)} languages ({en['n'] * len(F.LANGS)} sentences), CC BY 4.0"],
               ["Story-generation experiment", f"One idea ('{st['idea']}'), Short length, {a['n']} items: English with Adventure, Bedtime and Mystery plus the other 14 languages with Adventure; seed {st['seed']}"],
               ["Length experiment", "The same idea in English, Adventure, at Short, Medium and Long"],
               ["Built-in evaluation prompts", "Five prompts (English x 2, French, German, Spanish) in `evaluation_service.default_eval_prompts`"],
               ["API stories", f"{len(F.API['generate'])} stories generated through the running API (en, en, hi, fr, de, es, en) and narrated; transcribed again with chunked Whisper"],
               ["Training data", "None: no model was trained or fine-tuned"]],
              widths=[1.9, 4.6], align=["l", "l"], size=10),
          P("Three properties of this data shape every result. FLEURS sentences are short (about 8 to 14 s of speech), so the narration results describe sentences and not whole stories; story-length audio was measured separately on only seven stories. "
            "The evaluation text consists of sentences taken from Wikimedia texts, which differ from the simple narrative English that the story model writes. "
            "And the story experiment uses a single idea, so it measures how the pipeline handles one prompt in many languages, not how it handles many prompts.")]

    # ------------------------------------------------------------------ 6.3
    b += [H2("6.3 Preprocessing"),
          P("There is no data cleaning in the usual sense; preprocessing is the handling of text and audio on the way through the pipeline. It is implemented in `app/services/*` and `app/utils/*` and is the same in the web application, the tests and the experiments."),
          H3("6.3.1 Text handling"),
          P("The route strips the idea, rejects it if empty or longer than 2,000 characters, and stores the stripped text. The model's raw output is parsed by `_parse_model_output`: a line of the form `Title: ...` is taken as the title (cut at 150 characters) and the text after it as the body; "
            "if there is no such line and the first line is shorter than 120 characters and followed by more lines, that line becomes the title with its leading `#`, `*` and spaces removed; otherwise the title is `Untitled Story`. Runs of three or more line breaks collapse to one blank line. "
            "The word count is the number of tokens matched by a Unicode word pattern, the reading time is the word count divided by 200 words per minute, and the listening time is the audio duration (or, without audio, the word count divided by 150)."),
          P(f"The parser is the reason for a visible defect: with the raw prompt, the model rarely writes a `Title:` line, so the title is often `Untitled Story`, and when the model repeats the instruction the parser can take the repeated text as the title (one German evaluation sample was titled with the sentence \"The title should include 'Brot' and 'Berg'...\"). "
            "Chapter 8 counts how often the story text itself repeats the instruction."),
          H3("6.3.2 Chunking"),
          P("`chunk_text` collapses whitespace and splits at the end of a sentence (a full stop, question mark, exclamation mark, the Devanagari danda or the ideographic full stop followed by a space) and then packs whole sentences into chunks of at most 380 characters. "
            "A single sentence longer than the limit is cut into pieces of 380 characters (a 1,000-character word run becomes pieces of 380, 380 and 240 characters, which a unit test checks). Languages written without spaces after a full stop, such as Chinese or Japanese, therefore usually end up as one long sentence that is cut at 380 characters, possibly in the middle of a word."),
          H3("6.3.3 Audio handling"),
          P("Each chunk is synthesised separately. Its waveform is scaled so that its largest absolute value is 0.9, which levels the chunks against each other; the chunks are joined with 0.25 s of silence between them at 16,000 Hz; "
            "the result is rejected if its root-mean-square value is below 1e-4 (silence). Audio from the operating-system voice is read back from its temporary file, mixed to mono and resampled to 16 kHz by linear interpolation. The final signal is written as 16-bit PCM WAV."),
          H3("6.3.4 Normalisation for scoring"),
          P("The application's own WER and CER compare the story text and the transcript as they are, so capitalisation and punctuation count as errors. The experiments report these as the **raw** values and add **normalised** values: Unicode NFKC, lower case, punctuation and symbols removed, spaces collapsed, and for Chinese and Japanese the spaces removed altogether. "
            f"For English the corpus-level normalised WER is {F.pct(en['wer_norm_corpus'])} against a mean raw sentence WER of {F.pct(en['wer_raw_mean'])}; the normalised figures are the ones quoted in this report unless stated.")]

    # ------------------------------------------------------------------ 6.4
    b += [H2("6.4 Prompt construction and sampling"),
          P("The only control StoryVox has over the story is the prompt. `build_prompt` produces one string; for the idea used in the experiments it is exactly the text below (the line break is added for printing):"),
          CODE("Write an original adventure story in English, full of discovery, movement, and courage. Target length: short (about 3 short paragraphs).\n"
               "Start the first line with 'Title: ' followed by a short evocative title, then a blank line, then the story body only. Story idea: A young inventor discovers a hidden library.", 8.5),
          TAB("The controls that the prompt and the configuration expose.",
              ["Control", "Values", "Effect"],
              [["Style (8)", "Adventure, Fantasy, Educational, Bedtime, Mystery, Inspirational, Funny, Custom", "A fixed phrase is inserted: for example 'full of discovery, movement, and courage' (Adventure) or 'calm, soothing, and comforting with a peaceful ending' (Bedtime)"],
               ["Length (3)", f"Short, Medium, Long", f"Paragraph target 3, 5, 8 in the prompt; token budget {st['max_new_tokens']}, 420, 700 new tokens"],
               ["Language (15)", "en, hi, es, fr, de, it, pt, ru, ar, tr, nl, pl, zh, ja, ko", "The language name is inserted in the prompt; the same code selects the speech checkpoint"],
               ["Sampling", f"temperature {st['temperature']}, top-p {st['top_p']}, sampling on", "Set in the environment; the same for all lengths"]],
              widths=[1.3, 2.6, 2.6], align=["l", "l", "l"], size=9.5),
          P("The prompt is passed to the text-generation pipeline **as raw text, without the chat template** that Qwen3 was tuned to expect, and `return_full_text` is false so that only the continuation is returned. "
            "This matters. A small instruction-tuned model given an instruction as plain text tends to continue it as a document, which in our runs produced instruction-like sentences (\"The story should end with...\") and text about the story rather than the story. "
            f"To measure the effect the experiments add a second condition (B) that wraps the same prompt in the chat template with thinking disabled; it is **not** part of the product. In the 17 items, the share of sentences that repeat the instruction fell from {F.pct(a['mean_instruction_echo'])} (condition A, as shipped) to {F.pct(b_['mean_instruction_echo'])} (B)."),
          P(f"Sampling uses `torch.manual_seed(0)` in the experiments so that runs can be repeated; the product sets no seed. With the same seed, condition A produced almost the same English text for most languages, because the language word changes only a few tokens of a long prompt; "
            "the 17 items therefore show how often the model follows the language instruction, but they are not 17 independent stories.")]

    # ------------------------------------------------------------------ 6.5
    b += [H2("6.5 Algorithm choice and justification"),
          P(f"The choices were made for a machine without a graphics card. **Qwen3-0.6B** {cite('qwen3')} is the smallest Qwen3 language model; it fits in 1.5 GB on disk and generates {F.f1(a['mean_tok_per_s'])} tokens per second on the test CPU, which makes a three-paragraph story a matter of seconds and not minutes. "
            f"**MMS-TTS** {cite('mms')} offers one small VITS model {cite('vits')} per language (145 MB each), so adding a language adds a file and not a retraining; VITS is a single-pass generator, which is why the mean real-time factor is {F.f2(F.MMS_MEAN_RTF)}. "
            f"**Whisper-small** {cite('whisper')} is multilingual and, being used only to judge the narration, does not need to be the best recogniser. The **multilingual MiniLM** encoder {cite('sbertm')} compares a prompt with a story in any of the 15 languages."),
          P(f"Larger systems were not used. OmniVoice {cite('omni')} and XTTS {cite('xtts')} cover more languages or clone voices, but they are much larger models and running them on this CPU-only machine was outside the project, and the base paper's end-to-end model {cite('base')} was trained for 1.5 to 2 days on an A100 graphics card; we did not look for released weights. "
            "Whether the small choices are good enough is a measured question, and the measurements below show that the speech half is, while the text half is not."),
          TAB("Story-generation conditions on the 17 items (Short length, same idea).",
              ["Measure", "A: shipped (raw prompt)", "B: chat template", "C: offline composer"],
              [["Mean latency (s)", f"{F.f1(a['mean_latency_s'])}", f"{F.f1(b_['mean_latency_s'])}", "< 0.001"],
               ["Mean words", f"{F.f1(a['mean_words'])}", f"{F.f1(b_['mean_words'])}", f"{F.f1(c['mean_words'])}"],
               ["Tokens per second", f"{F.f2(a['mean_tok_per_s'])}", f"{F.f2(b_['mean_tok_per_s'])}", "n/a"],
               ["Story in the requested language", F.pct(a["language_match_rate"]), F.pct(b_["language_match_rate"]), F.pct(c["language_match_rate"])],
               ["Sentences that repeat the instruction", F.pct(a["mean_instruction_echo"]), F.pct(b_["mean_instruction_echo"]), F.pct(c["mean_instruction_echo"])],
               ["Distinct-2 (variety)", F.f3(a["mean_distinct_2"]), F.f3(b_["mean_distinct_2"]), F.f3(c["mean_distinct_2"])],
               ["Idea-story similarity (MiniLM)", F.f3(a["mean_similarity"]), F.f3(b_["mean_similarity"]), F.f3(c["mean_similarity"])],
               ["ROUGE-L, idea vs. story", F.f3(a["mean_rougeL"]), F.f3(b_["mean_rougeL"]), F.f3(c["mean_rougeL"])]],
              widths=[2.3, 1.4, 1.4, 1.4], align=["l", "r", "r", "r"], size=9.5),
          *_fg("f03_story_conditions.png", "Four measures of the three story-generation conditions on the 17 items.", 5.6),
          P(f"Three readings follow. **The language instruction is mostly ignored**: with the shipped prompt only {F.pct(a['language_match_rate'], 0)} of the stories were detected as being in the requested language (the English ones); the chat template raises this to {F.pct(b_['language_match_rate'], 0)}, still below half. "
            f"**The composer scores highest on similarity ({F.f2(c['mean_similarity'])}) only because it quotes the idea word for word**, which is why similarity to the prompt cannot be read as quality. "
            "**Speed is the same for A and B** because the same model and token budget are used. The language detector is itself unreliable on very short or mixed text, so the match rates are indicative, not exact."),
          P(f"For speech the corresponding evidence is in Chapter 8: {len(F.MMS_LANGS)} languages are narrated by MMS-TTS with a mean normalised CER of {F.pct(F.MMS_MEAN_CER)} after a round trip through Whisper-small, "
            f"and the best and worst are {F.LANG_NAMES[F.BEST_CER]} ({F.pct(F.LANGS[F.BEST_CER]['cer_norm_corpus'])}) and {F.LANG_NAMES[F.WORST_CER]} ({F.pct(F.LANGS[F.WORST_CER]['cer_norm_corpus'])}). "
            "This mixes the error of the speech model with that of the recogniser, whose own error on natural speech was not measured separately, so the speech figures are upper bounds on the narration error.")]

    # ------------------------------------------------------------------ 6.6
    b += [H2("6.6 Mathematical formulation"),
          H3("6.6.1 Sampling"),
          P(f"The language model gives, at each step, a score z_i to every token i of its vocabulary. With temperature T the probabilities are p_i = softmax(z / T). "
            f"Nucleus sampling {cite('holtzman')} keeps the smallest set V of tokens whose probabilities add up to at least top-p, renormalises inside V and draws the next token from it:"),
          EQ("p_i = exp(z_i / T) / sum_j exp(z_j / T),   V = smallest set with sum_{i in V} p_i >= top-p,   token ~ p_i / sum_{j in V} p_j"),
          P(f"StoryVox uses T = {st['temperature']} and top-p = {st['top_p']}. A higher temperature flattens the distribution and makes the text more varied and more error-prone; a lower one makes it repetitive."),
          H3("6.6.2 Narration"),
          P("Let the text be cut into chunks x_1 ... x_m and let s_k be the waveform of chunk k at 16,000 Hz. Each waveform is scaled to a peak of 0.9 and the chunks are joined with a pause of 0.25 s of zeros, so the duration of the narration is"),
          EQ("s'_k = 0.9 * s_k / max|s_k|,   audio = s'_1 || 0 || s'_2 || 0 || ... || s'_m,   duration D = ( sum_k len(s_k) + (m - 1) * 0.25 * 16000 ) / 16000"),
          P("The real-time factor is the synthesis time divided by the duration; values below 1 mean faster than real time:"),
          EQ("RTF = T_synth / D"),
          H3("6.6.3 Intelligibility metrics"),
          P("For a reference text r and a recogniser transcript h, the word error rate is the word-level edit distance divided by the number of reference words; the character error rate is the same at character level:"),
          EQ("WER = (S + D + I) / N_words(r),   CER = (S + D + I) / N_chars(r)"),
          P("S, D and I are the substitutions, deletions and insertions of the minimum edit alignment. The application computes WER and CER with jiwer for each sample and averages them; the experiments also report a **corpus** value in which the edit counts and the reference lengths are first summed over all sentences of a language, which weights long sentences more and is the figure used for the language tables. "
            "WER can exceed 1 when the transcript is much longer than the reference."),
          H3("6.6.4 Similarity and variety metrics"),
          P(f"The idea-story similarity is the cosine of the sentence embeddings u (idea) and v (story) of the multilingual MiniLM encoder {cite('sbertm')}; if the encoder cannot be loaded, the application falls back to a cosine of word-count vectors and says so in the row. "
            f"ROUGE-L {cite('rouge')} is the F-measure of the longest common subsequence of the two texts. Distinct-2 is the share of different word pairs among all word pairs of a story (characters for text without spaces), a simple measure of repetition. "
            "The instruction-echo ratio is the share of the sentences of a story that contain a phrase from a fixed list of instruction fragments (for example 'the story should', 'blank line', 'title:')."),
          EQ("cos(u, v) = u . v / (|u| |v|),   Distinct-2 = |unique bigrams| / |bigrams|,   echo = (sentences matching a fragment) / (all sentences)"),
          P("The language-match rate is the share of stories for which the `langdetect` library names the requested language. It was applied to texts of 100 to 200 words; it is reported as an indicator because the library can mislabel short or mixed-script text.")]

    # ------------------------------------------------------------------ 6.7
    b += [H2("6.7 Model architecture and inference configuration"),
          *_dg("model", None, 5.2),
          P("**No model was trained or fine-tuned in this project**, so there are no training curves, no loss, no learning rate and no hyper-parameter search to report. What the project fixes is the way pretrained models are run; the table lists every setting."),
          TAB("Models and their inference settings.",
              ["Model", "Role", "Settings"],
              [["Qwen/Qwen3-0.6B", "Story text", f"transformers text-generation pipeline; float32 on CPU (float16 if CUDA is found); sampling on; temperature {st['temperature']}; top-p {st['top_p']}; max new tokens {st['max_new_tokens']} / 420 / 700; raw prompt; loaded once under a lock ({F.f1(st['model_load_s'])} s from the cache)"],
               ["facebook/mms-tts-*", "Narration", f"VITS checkpoint chosen by language; tokenizer from the same repository; 16 kHz output; chunks of at most 380 characters; peak 0.9; pause 0.25 s; first load {F.f1(F.LANGS['en']['mms_load_s'])} s from the cache, 19 to 25 s when downloaded; one model per language kept in memory"],
               ["System voice (pyttsx3)", "Fallback narration", "Operating-system voice at rate 170, text cut at 4,000 characters, WAV read back and resampled to 16 kHz; only English voices (David, Zira) existed on the test machine"],
               ["openai/whisper-small", "Recogniser (evaluation)", f"Transformers speech-recognition pipeline; language forced to the story language; task transcribe; no chunking in the product (chunk_length_s = 30 in the story-audio experiment); load {F.f1(F.TTS['asr_load_s'])} s"],
               ["paraphrase-multilingual-MiniLM-L12-v2", "Similarity (evaluation)", "Sentence-transformers encoder with normalised embeddings; re-created at every evaluation sample in the product; in the experiments loaded once"]],
              widths=[1.7, 1.2, 3.6], align=["l", "l", "l"], size=9),
          P("Two implementation details have consequences. The text pipeline is created with `trust_remote_code=True`, which allows code from the model repository to run at load time; this is a security trade-off, and we did not test whether the model loads without it. "
            "And the speech tokenizer for some languages (Korean) needs the `uroman` romaniser, which is not in `requirements.txt`; without it Korean text reaches the tokenizer unconverted.")]

    # ------------------------------------------------------------------ 6.8
    b += [H2("6.8 Evaluation protocol"),
          *_dg("tts_eval", None, 5.4),
          P("The protocol has five parts, each implemented by a script that calls the application's own services so that the numbers describe the shipped behaviour."),
          N(f"**Narration round trip** (`scripts/run_experiments.py tts_asr`). For each language, {en['n']} FLEURS sentences are narrated through `synthesize_story_narration`, transcribed by Whisper-small with the language forced, and scored against the source sentence. The first sentence of a language is not discarded; model-load time is measured separately.",
            f"**Chinese and Japanese fallback** (`run_experiments.py cjk`). Because no MMS checkpoint exists for these two languages, each sentence is narrated in its own child process with a 90 s limit (the operating-system engine can hang on text it has no voice for) and scored the same way; {F.LANGS['zh']['narrated']} of {F.LANGS['zh']['n']} Chinese and {F.LANGS['ja']['narrated']} of {F.LANGS['ja']['n']} Japanese sentences were narrated.",
            f"**Story generation** (`run_experiments.py story`). The 17 items are generated under conditions A, B and C and scored with the measures of Section 6.6; a second part generates the Short, Medium and Long English story with condition B and narrates each with MMS ({F.f1(short['total_s'])}, {F.f1(medium['total_s'])} and {F.f1(long_['total_s'])} s in total).",
            "**API measurement** (`scripts/measure_api.py`). A running server is called 10 to 30 times on each cheap endpoint and seven times on `POST /api/stories/generate` with narration; the first call is cold. The seven stories remain in the database and feed the screenshots.",
            "**Story-length intelligibility** (`scripts/run_story_asr.py`). The seven API stories and their WAV files are transcribed with chunked Whisper (30 s windows) and scored with normalised WER and CER, because the application's own evaluation cannot score audio longer than 30 s."),
          P(f"The application's built-in evaluation (`POST /api/evaluations/run`) was also run twice through the API (5 samples and 2 English samples) to populate the Evaluation page; both runs report WER and CER as empty, for the reason in Chapter 8. Tests are run with `scripts/run_tests.py`, which stores the pytest outcome ({F.PYTEST_PASSED} of {F.PYTEST_TOTAL} passed). "
            "The environment was CPU-only (Intel Core i5-12500, 15.7 GB), Python 3.11.9, PyTorch 2.14.1, Transformers 5.20.2, with other jobs running on the same machine, so timings are indicative."),
          P("**Limits of the protocol.** The narration scores include the error of the recogniser, which was not separated. Only ten sentences per language were used, so differences of a few points between languages are within the noise (for example, the 12 MMS languages range from "
            f"{F.pct(F.LANGS[F.BEST_CER]['cer_norm_corpus'])} to {F.pct(F.LANGS[F.WORST_CER]['cer_norm_corpus'])} CER). No human listened to the audio and no human rated a story, so naturalness, coherence and narrative quality were not measured; the automatic story measures are proxies. "
            "One idea and one seed were used for the story experiment.")]
    return b


def application_blocks():
    api = F.API
    ep = api["endpoints"]
    first, warm = _gen(1), _gen(2)
    b = []

    b += [H2("6.9 Application architecture"),
          P(f"The product is one FastAPI service (`app/main.py`, port {F.API_PORT}) and one React 19 application built with Vite (port {F.WEB_PORT} in development, served by the same service after a build). "
            "The service is organised around one idea: **a route does only HTTP work**. It validates the request with Pydantic and explicit checks, calls a service function, stores the result through a SQLAlchemy session and maps exceptions to status codes. "
            "The services hold the logic and the models, each loaded on first use and cached in a module variable behind a lock."),
          *_dg("arch", None, 5.4),
          P("The narration service shows the pattern best. It tries the providers in order, stops at the first that returns audio, and refuses to write a file if all fail or the result is silent. The loop below is the core of `synthesize_story_narration`."),
          CODE("for provider in (MMSTTSProvider(), SystemTTSProvider()):\n"
               "    try:\n"
               "        audio, sample_rate, model_id = provider.synthesize(story_text, language_code)\n"
               "        break\n"
               "    except ValueError:\n"
               "        raise                       # unsupported language: a user error, do not fall back\n"
               "    except Exception as exc:\n"
               "        last_error = exc\n"
               "        logger.warning(\"StoryVox: TTS provider %s failed: %s\", provider.name, exc)\n"
               "        continue\n"
               "if audio is None or audio.size == 0 or is_silent(audio):\n"
               "    raise RuntimeError(\"Narration could not be generated. Check the server log for details.\")", 8.5),
          P("The front end loads the languages, the styles and lengths and the server health once through a context provider and shows the result in the top bar (`API online - CPU`, or `API offline`). Pages call the API through one fetch wrapper that returns the server's `detail` message as the error text "
            "and a fixed message ('Could not reach the StoryVox server.') when the server cannot be reached. Studio keeps the id of the last story in the address (`?story=12`) so that a reload restores the result; History and Evaluation are tables and charts over the stored rows.")]

    b += [H2("6.10 API design"),
          P("Chapter 5 lists the 11 routes. This section shows the shape of the main exchange. The request is a five-field JSON document and the response carries everything the page draws, so the page makes one call and no further computation happens in the browser. "
            f"The values below are those of the first real call of the measurement run (English, Adventure, Short, with narration; long fields abbreviated)."),
          CODE("POST /api/stories/generate\n"
               "{ \"prompt\": \"A young inventor discovers a hidden library.\", \"language_code\": \"en\",\n"
               "  \"style\": \"Adventure\", \"length_option\": \"Short\", \"synthesize\": true }\n\n"
               "200 OK\n"
               f"{{ \"id\": {first['story_id']}, \"title\": \"Untitled Story\", \"story_text\": \"The library is built by a time traveler ...\",\n"
               f"  \"language_code\": \"en\", \"language_name\": \"English\", \"style\": \"Adventure\", \"length_option\": \"Short\",\n"
               f"  \"word_count\": {first['words']}, \"generation_time_seconds\": {first['story_gen_s']},\n"
               f"  \"audio\": {{ \"id\": {first['audio_id']}, \"file_path\": \"/api/audio/{first['audio_id']}\", \"duration_seconds\": {first['audio_s']}, \"sample_rate\": 16000,\n"
               f"             \"tts_model\": \"{first['tts_model']}\", \"synthesis_time_seconds\": {first['tts_s']}, \"rtf\": {first['rtf']} }} }}", 8.5),
          P(f"The response shows two honest details: the title is `Untitled Story`, because the model did not write a `Title:` line, and the story starts with 'The library is built by a time traveler', which shows how the raw prompt turns the idea into a description. "
            "The audio route returns the file with the media type `audio/wav` and a download name `storyvox_narration_{id}.wav`, which is what the browser player and the download button use."),
          P(f"**Measured behaviour** (127.0.0.1, other jobs on the machine). The lightweight routes answer in a median of {ep['GET /api/health']['median_ms']:.1f} ms (health), {ep['GET /api/languages']['median_ms']:.1f} ms (languages), {ep['GET /api/meta']['median_ms']:.2f} ms (meta) and {ep['GET /api/stories']['median_ms']:.2f} ms (empty story list, 30 calls each); "
            f"an invalid generate request is rejected in {ep['POST /api/stories/generate (empty prompt, 422)']['median_ms']:.1f} ms; the WAV download takes {ep['GET /api/audio/{id} (WAV download)']['median_ms']:.1f} ms (median of 10 downloads of a {first['audio_s']:.0f} s file). "
            f"A real generate call with narration took {first['request_s']} s for the first (cold) request and {warm['request_s']} s for a comparable warm one; the Medium story took {_gen(7)['request_s']} s. The time is spent in the two models, not in the API."),
          *_fg("f05_api_latency.png", "Median and 95th-percentile latency of the endpoints that do not run a model (127.0.0.1).", 5.4),
          *_fg("f08_generate_calls.png", "The seven measured generate-with-narration calls: story generation and narration time.", 5.4)]

    b += [H2("6.11 Security and error handling"),
          P("StoryVox is a local single-user application and its security model is correspondingly simple. We list what exists and what does not, so that nobody assumes more."),
          B("**No authentication or accounts.** Anyone who can reach the port can use the tool and read every story. The server is started on 127.0.0.1, which is the protection; the Docker command in the guide publishes the port only to 127.0.0.1 as well.",
            "**Same origin.** The browser reaches the API through the Vite proxy in development and through the same process in production, so the application defines no CORS rules and a page from another origin cannot read its responses.",
            "**Input validation.** The idea must be non-empty and at most 2,000 characters; the language, style and length must be among the offered values; the evaluation sample count must be 1 to 30 and the story list limit 1 to 200. Invalid values answer 422 with a sentence. Database access goes through the ORM, so values are parameterised.",
            "**Audio paths.** The path stored with each audio row is generated by the server (a unique file name with a time stamp and a random token inside the audio folder), and the client never supplies a path. The delete route removes a file only if the audio folder is among its parents. "
            "A helper `ensure_within_directory` that rejects paths outside the folder exists and is unit-tested, but no route calls it; the stream route resolves the stored path without that check, and its `except ValueError` branch can therefore never run. Because the paths come from the server's own database, we found no way for a request to exploit this, but the check should be wired in.",
            "**Secrets.** The application needs no API key. `.env` holds ports, model names and limits, is git-ignored, and the repository ships only `.env.example`. The only network access is the model download from the Hugging Face hub; `trust_remote_code=True` lets code from the model repository run at load time.",
            "**Cross-site scripting.** The front end renders story text as React text and uses no raw HTML insertion.",
            "**Failure behaviour.** A failed story model falls back to the composer; a failed narration leaves the story saved without audio; a failed recogniser leaves WER and CER empty with the error stored in the row; unexpected exceptions answer 500 with a generic sentence and are logged with a stack trace on the server.",
            "**Concurrency and limits.** Model loading is serialised by locks; every request uses its own database session; no rate limit, request-size limit beyond the idea length, HTTPS or queue exists, and no concurrent-load test was done."),
          P(f"The automated tests cover the validation messages, the 404 cases, the delete cascade, the streamed WAV and the directory helper (Chapter 7). They replace the models with stubs, so model failures are covered only by the experiment runs.")]

    b += [H2("6.12 Installation and execution"),
          P("The project guide asks for Python 3.11 or newer, Node.js 20 or newer, 8 GB of free disk space for the models and 8 GB of memory, and internet access on the first run. `requirements.txt` lists fastapi, uvicorn, sqlalchemy, pydantic, pydantic-settings, python-multipart, numpy, soundfile, jiwer, nltk, rouge-score, torch, transformers, accelerate, sentencepiece, tokenizers, datasets, librosa, pyttsx3, sentence-transformers, reportlab, pytest and httpx without version pins. "
            "The measurements in this report used Python 3.11.9, PyTorch 2.14.1, Transformers 5.20.2, FastAPI 0.143.3 and NumPy 1.26.4."),
          N("Open the project folder `8.ProjectCode` and (optionally) copy `.env.example` to `.env`; ports 8402 and 5402 are preset.",
            "Double-click `run.bat`. It rebuilds a `.venv` copied from another computer, installs `requirements.txt` and, if needed, `npm install` in `frontend/`, starts the API with uvicorn and the web application with Vite in two windows and opens http://localhost:5402. The first run downloads the models and can take 10 to 30 minutes or more.",
            "Open **Studio**, type an idea, choose language, style and length, press **Generate story**, then play or download the narration. **History** lists past stories and **Evaluation** runs the measurement loop.",
            "Run `python -m pytest tests -q` for the automated tests ({} passed in {} s here). `scripts/smoke_test.py` walks the main flow through a running server; it was not run during this documentation work.".format(F.PYTEST_PASSED, F.TESTS["seconds"]),
            "To use Docker, build the image and run it with the port published to 127.0.0.1:8402; the image contains the built web application, `ffmpeg` and `espeak-ng`. The Docker route was not tested; note that its start command binds 127.0.0.1 inside the container, which may stop a published port from reaching it."),
          P("Three practical notes come from this project's own run. **`run.bat` was not used**: the `.venv` in the folder pointed at a Python 3.14 that is not installed and the drive had too little free space to rebuild it, so the service was started with `python -m uvicorn app.main:app --host 127.0.0.1 --port 8402` from the system Python and the built web application was served by the same process. "
            "**`ffmpeg` must be on the PATH** for the evaluation, because Whisper reads the WAV file through it; it is not in `requirements.txt` (the Dockerfile installs it). **`pip install uroman`** is needed for Korean. "
            "To reproduce the numbers of this report run, from `8.ProjectCode`: `python scripts/run_experiments.py all` (then `cjk`), `python scripts/measure_api.py` against a running server, `python scripts/run_story_asr.py`, `python scripts/run_tests.py` and `python scripts/make_report_facts.py`. "
            "Appendix B repeats the instructions as a user guide with the screens.")]
    return b


def _trim(bl):
    """Report variant: the diagrams already appear in Chapter 5 and the result charts in Chapter 8, so only the text, tables and code are kept."""
    out = []
    for b in bl:
        if b[0] == "fig" and (os.sep + "diagrams" + os.sep in b[1] or os.path.basename(b[1]).startswith("f0")):
            continue
        out.append(b)
    return out


def blocks():
    bl = [H1("CHAPTER 6: METHODOLOGY AND SOFTWARE IMPLEMENTATION")] + methodology_blocks() + application_blocks()
    return _trim(bl) if F.REPORT else bl
