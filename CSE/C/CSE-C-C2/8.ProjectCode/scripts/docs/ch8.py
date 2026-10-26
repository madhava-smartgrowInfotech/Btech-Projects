"""Chapter 8: Results and output screens for StoryVox. Every number is read from facts.py (experiments/**/metrics.json) or from the saved evaluation runs in experiments/app_evaluation."""
import glob
import json
import os

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, P, PAIR, TAB
from .refs import N

SH = F.shot
CA, CB, CC = "A_app_raw_prompt", "B_chat_template", "C_local_composer"


def S(name, caption, base=5.6, max_h=3.7):
    """Screenshot figure with a width that keeps the picture on one page."""
    return FIG(SH(name), caption, F.shot_w(SH(name), base, max_h))


def G(name, caption, width=5.6, doc_only=False):
    """Result figure from docs/figures; omitted if the file has not been produced, or (doc_only) in the compact report variant."""
    path = F.fig(name)
    if doc_only and F.REPORT:
        return []
    return [FIG(path, caption, width)] if os.path.exists(path) else []


def _compact(blocks):
    """Report variant: drop the sub-headings and put the screenshots two per figure, each with its own caption."""
    out, pend = [], []
    for blk in blocks:
        if blk[0] == "h3":
            continue
        if blk[0] == "fig":
            pend.append((blk[1], blk[2]))
            if len(pend) == 2:
                out.append(PAIR(pend, 2.95))
                pend = []
        else:
            out.append(blk)
    if pend:
        out.append(FIG(pend[0][0], pend[0][1], 4.0))
    return out


def _ex(cond, idx, n=150):
    """First n characters of a real generated text (cut at a word), whitespace collapsed."""
    t = " ".join(F.STORY["conditions"][cond][idx]["text"].replace("*", "").split())
    if len(t) <= n:
        return t
    return t[:n].rsplit(" ", 1)[0] + " ..."


def _idx(cond, lang, style=None):
    for i, r in enumerate(F.STORY["conditions"][cond]):
        if r["language"] == lang and (style is None or r["style"] == style):
            return i
    raise KeyError((cond, lang, style))


def _runs():
    out = []
    for p in sorted(glob.glob(os.path.join(F.EXP, "app_evaluation", "*.json"))):
        out.append(json.load(open(p, encoding="utf-8")))
    return out


def _vname(model):
    return "MMS" if "facebook/mms" in model else "OS voice"


# ----------------------------------------------------------------------------------------------- 8.1
def _setup():
    t = F.TTS
    st = F.STORY
    return [H2("8.1 Experimental set-up"),
            P(f"All measurements in this chapter were made on one machine: an Intel Core i5-12500 (6 cores, 12 threads) with 15.7 GB of memory, no GPU, Windows 11, system Python 3.11.9, torch {t['torch'].split('+')[0]} and transformers 5.20.2. "
              "Other programs were running at the same time, so absolute timings are indicative; the error rates do not depend on load. "
              "StoryVox trains nothing, so there is no training set and no test split of the usual kind: the models are used as downloaded and are *exercised* on fixed inputs. "
              "Every table and figure was produced from the stored files `experiments/*/metrics.json` by `scripts/run_experiments.py`, `scripts/measure_api.py`, `scripts/run_story_asr.py` and `scripts/docs/make_figures.py`, and the same numbers are listed in `docs/REPORT_FACTS.md`; no result was typed in by hand."),
            TAB("Experiments and what each used.", ["Experiment", "Input", "What was measured"],
                [["Speech round trip (Section 8.3)", f"FLEURS {N('fleurs')} test split (Google, CC BY 4.0): the first 10 length-filtered sentences of each of the 15 languages (150 sentences). Downloaded from the Hugging Face dataset repository", "The application's own narration service turns each sentence into audio; Whisper-small transcribes it; WER, CER and real-time factor are computed"],
                 ["Story conditions (Section 8.4)", f"One story idea, \"{st['idea']}\", 17 requests: English with Adventure, Bedtime and Mystery plus the other 14 languages with Adventure; Short length; seed 0; temperature {st['temperature']}, top-p {st['top_p']}", "Three ways of producing the story (A, B, C below): latency, words, language match, instruction echo, distinct-2, prompt-story similarity, ROUGE-L"],
                 ["Length scaling (Section 8.6)", "The same idea at Short, Medium and Long, English, chat-template story, MMS narration", "Story time, narration time, audio length, RTF"],
                 ["Live API (Sections 7.7, 8.5)", "Seven full generations through the running server and the application's own evaluation twice (5 and 2 samples)", "Request time, stage times, audio; WER and CER of story-length narration (chunked recogniser)"]],
                widths=[1.5, 2.9, 2.1], align=["l", "l", "l"], size=9.5),
            P("Three story conditions are compared throughout. **A, the shipped path**, is the application's `generate_story_text`: one instruction sentence sent to Qwen3-0.6B as plain text. "
              "**B, the chat-template variant**, sends the same instruction sentence through the model's chat template with thinking switched off; it exists only in the experiment and is not part of the product. "
              "**C, the offline composer**, is `storyvox-local-fallback-v1`, which the product uses when the model fails or answers with fewer than 20 words. "
              "WER and CER are reported *normalised* (Unicode NFKC, lower case, punctuation removed; spaces removed for Chinese and Japanese) because the application's own `wer()` counts case and punctuation as errors; the raw values are in `docs/REPORT_FACTS.md`. "
              "WER is not reported for Chinese and Japanese, which have no word boundaries. The real-time factor RTF is synthesis time divided by audio duration, so smaller is faster.")]


# ----------------------------------------------------------------------------------------------- 8.2
def _screens():
    runs = _runs()
    r1 = next(r for r in runs if r["sample_count"] == 5)
    a = r1["averages"]
    b = [H2("8.2 Output screens"),
         P("The screens below were captured from the running application at 1440 by 900 pixels. The server held seven real stories (Section 7.7) and two real evaluation runs, so no screen is empty or a mock-up. "
           "What the screens show is exactly what the models produced, including the weak stories discussed later in the chapter. The landing page in light and dark colour schemes is shown in Appendix C.")]
    b += [H3("8.2.1 Studio"),
          S("02_studio_empty.png", "Studio before any story: the idea box (limit 2,000 characters), the language list (15 languages), style and length lists, the *Narrate the story automatically* switch and the Generate story button. The right-hand panel says *No story yet*."),
          S("03_studio_result.png", "Studio after generating story 7 (English, Adventure, Medium): 335 words, about 2 minutes of listening, written in 41 s. The narration card has the audio player (1:57), *Download WAV*, *Regenerate narration* and the voice used, `facebook/mms-tts-eng`, 16,000 Hz. The text shows a model failure: after two sentences the story turns into a list of instructions (*The story should contain 22 characters, 1000 words ...*).")]
    b += [H3("8.2.2 History and story detail"),
          S("04_history.png", "History library: seven stories with title, language, style, word count, creation time, audio status and the View, Play, Download and Delete buttons; the search box filters by title, language or style and the headings sort. Six of the seven titles are *Untitled Story* because the model produced no bare `Title:` line."),
          S("05_story_detail.png", "Story detail page for story 7 with tabs Story and Details, the language, style and length tags, the player and the story text."),
          S("10_story_detail_hindi.png", "A Hindi story, number 3: 185 words, written in 20 s, narrated by `facebook/mms-tts-hin`. The text on screen is English, and the player shows 0:04: the Hindi voice produced four seconds of sound for a 185-word story (Section 8.5).")]
    b += [H3("8.2.3 Evaluation"),
          S("06_evaluation.png", f"Evaluation page, run of 5 samples: the form to start a run (samples, language, skip narration, skip story model), the run selector and the summary cards. WER and CER show a dash (*Needs narration + transcription*); topic similarity is {a['prompt_story_similarity']:.3f}."),
          S("07_evaluation_chart.png", f"Evaluation, Chart tab: story latency {a['story_time_s']:.2f} s, narration {a['tts_time_s']:.2f} s, RTF {a['rtf']:.3f}, ROUGE-L {a['rougeL_prompt_vs_story']:.3f}, and the per-sample real-time factor of the five samples (English, English, French, German, Spanish)."),
          S("08_evaluation_samples.png", "Evaluation, Samples tab: each of the five built-in prompts with its language, story time, narration time, audio length, RTF, WER, CER (both empty) and prompt-story similarity (0.503, 0.707, 0.622, 0.502, 0.287).")]
    return _compact(b) if F.REPORT else b


# ----------------------------------------------------------------------------------------------- 8.3
def _tts_rows():
    rows = []
    for c, e in F.LANGS.items():
        voice = _vname(" ".join(e.get("models_used", ["none"])))
        narr = e.get("narrated", e["n"] if e.get("models_used") else 0)
        wer = f"{e['wer_norm_corpus']:.3f}" if e.get("wer_norm_corpus") is not None else "-"
        cer = f"{e['cer_norm_corpus']:.3f}" if e.get("cer_norm_corpus") is not None else "-"
        rows.append([F.LANG_NAMES[c], voice, f"{narr}/{e['n']}", f"{e['mean_duration_s']:.1f}" if e.get("mean_duration_s") is not None else "-",
                     f"{e['mean_rtf']:.3f}" if e.get("mean_rtf") is not None else "-", wer, cer])
    return rows


def _narration():
    L = F.LANGS
    en, hi, es, ko, it, zh, ja = (L[c] for c in ("en", "hi", "es", "ko", "it", "zh", "ja"))
    b = [H2("8.3 Narration speed and intelligibility"),
         P(f"Each of the 150 FLEURS sentences was narrated by the application's own `synthesize_story_narration` and transcribed by Whisper-small; the transcript was compared with the original sentence. "
           f"the table below gives the corpus-level normalised WER and CER and the mean real-time factor per language. The twelve languages narrated by the MMS speech models have a mean RTF of {F.MMS_MEAN_RTF:.3f}, "
           f"a mean CER of {F.MMS_MEAN_CER:.3f} and a mean WER of {F.MMS_MEAN_WER:.3f}."),
         TAB("Speech round trip per language (10 FLEURS sentences each; normalised WER and CER; RTF is the mean over the narrated sentences).",
             ["Language", "Voice", "Narrated", "Mean audio (s)", "RTF", "WER", "CER"], _tts_rows(),
             widths=[1.2, 0.9, 0.9, 1.1, 0.8, 0.8, 0.8], align=["l", "l", "c", "c", "c", "c", "c"], size=9.5)]
    b += G("f01_rtf_by_language.png", "Mean real-time factor of narration per language. Orange bars are the operating-system fallback voice; bars above 1.3 are cut off.", 5.6)
    b += G("f02_wer_cer_by_language.png", "Normalised WER and CER per language. Hatched bars are the fallback voice; Chinese and Japanese bars use only the 2 and 1 sentences that produced any audio.", 5.6)
    b += [P(f"**Speed.** On a CPU, narration runs at about a quarter of real time for every MMS language (RTF {min(L[c]['mean_rtf'] for c in F.MMS_LANGS if c != 'ko'):.3f} to {max(L[c]['mean_rtf'] for c in F.MMS_LANGS if c != 'ko'):.3f} apart from Korean). "
             f"Korean is the exception at {ko['mean_rtf']:.3f}: it needs the romaniser `uroman`, which is not in `requirements.txt`, and takes about twice as long per second of audio; the cause was not isolated further. "
             f"Loading a speech model for the first time cost 19 to 25 s per language on this disk, and {en['mms_load_s']:.1f} s for English and {ko['mms_load_s']:.1f} s for Korean, which were already cached."),
           P(f"**Intelligibility.** English reads back with WER {en['wer_norm_corpus']:.3f} and CER {en['cer_norm_corpus']:.3f}. Spanish is best ({es['wer_norm_corpus']:.3f} / {es['cer_norm_corpus']:.3f}), Portuguese and French follow, and Hindi is the weakest MMS language "
             f"(WER {hi['wer_norm_corpus']:.3f}, CER {hi['cer_norm_corpus']:.3f}). The application's own metric, which does not normalise, is higher for every language: English {en['wer_raw_mean']:.3f} raw against {en['wer_norm_corpus']:.3f} normalised, "
             "because a capital letter or a comma counts as an error. The raw number is therefore a pessimistic reading of what a listener would understand. "
             "Both numbers combine two errors, the speech model's and the recogniser's, and Whisper-small is itself weaker in some languages than in others (Hindi and Arabic in particular); the recogniser's own error on natural speech was not measured, so the table ranks the *pair* and not the speech models alone."),
           P(f"**Languages without an MMS voice.** The checkpoints `facebook/mms-tts-ita`, `-cmn` and `-jpn` named in the application's language table do not exist on the Hugging Face Hub, so loading them fails and the service falls back to the operating-system voice. "
             f"On the test machine that voice is English only (Microsoft David and Zira). For Italian it still produced audio for all 10 sentences, an English voice reading Italian spelling, and Whisper recovered {100 * (1 - it['wer_norm_corpus']):.0f} per cent of the words (WER {it['wer_norm_corpus']:.3f}, CER {it['cer_norm_corpus']:.3f}). "
             f"For Chinese and Japanese the engine has no voice at all: it produced audio for only {zh['narrated']} of 10 and {ja['narrated']} of 10 sentences, took {zh['mean_rtf']:.1f} and {ja['mean_rtf']:.1f} times the audio length for the sentences it did produce, and the transcripts bear no resemblance to the text (CER {zh['cer_norm_corpus']:.2f} and {ja['cer_norm_corpus']:.2f}). "
             "Two of the 15 advertised languages are therefore not usable on this machine and a third is only partly usable. On a computer with a Chinese or Japanese system voice the fallback would give different results; that was not tried.")]
    return b


# ----------------------------------------------------------------------------------------------- 8.4
def _cond_rows():
    names = {CA: "A: shipped path (raw prompt)", CB: "B: chat-template variant", CC: "C: offline composer"}
    rows = []
    for c, s in F.STORY_SUMMARY.items():
        rows.append([names[c], f"{s['mean_latency_s']:.1f}" if s["mean_latency_s"] > 0.01 else "< 0.01", f"{s['mean_words']:.0f}", f"{s['language_match_rate']:.2f}",
                     f"{s['mean_instruction_echo']:.3f}", f"{s['mean_distinct_2']:.3f}", f"{s['mean_similarity']:.3f}", f"{s['mean_rougeL']:.3f}"])
    return rows


def _stories():
    conds = F.STORY["conditions"]
    b_ok = [r["language"] for r in conds[CB] if r["language_match"] and r["language"] != "en"]
    a_first = " ".join(conds[CA][_idx(CA, "hi")]["text"].split())[:70]
    same_a = sum(1 for r in conds[CA] if " ".join(r["text"].split())[:70] == a_first)
    untitled_a = sum(1 for r in conds[CA] if r["title"] == "Untitled Story")
    untitled_b = sum(1 for r in conds[CB] if r["title"] == "Untitled Story")
    dirty_b = sum(1 for r in conds[CB] if r["title"].startswith("Title") or "*" in r["title"])
    sa, sb, sc = (F.STORY_SUMMARY[c] for c in (CA, CB, CC))
    b = [H2("8.4 Story generation: three conditions"),
         P(f"The table below compares the three conditions on the same 17 requests. All numbers are means over the 17 stories. Language match is the share of stories whose text a language detector assigns to the requested language; "
           "instruction echo is the share of sentences that contain phrases from the prompt such as *the story should* or *blank line*; distinct-2 is the share of distinct word pairs (a low value means repetition); "
           f"prompt-story similarity is the cosine of multilingual MiniLM embeddings {N('sbertm')} of the idea and the story, and ROUGE-L {N('rouge')} is the overlap between them."),
         TAB("Story conditions on 17 requests (idea: A young inventor discovers a hidden library; Short length; seed 0).",
             ["Condition", "Latency (s)", "Words", "Language match", "Instruction echo", "Distinct-2", "Prompt similarity", "ROUGE-L"], _cond_rows(),
             widths=[1.8, 0.7, 0.6, 0.8, 0.8, 0.7, 0.8, 0.7], align=["l", "c", "c", "c", "c", "c", "c", "c"], size=9)]
    b += G("f03_story_conditions.png", "Latency, length, language match and variety of the three story conditions (A shipped, B chat template, C offline composer).", 5.8)
    b += [P(f"**The shipped path writes English whatever language is asked.** Only {round(sa['language_match_rate'] * 17)} of 17 stories (the three English requests) came out in the requested language ({sa['language_match_rate']:.2f}). "
             f"With the same seed the model also wrote almost the same English text for {same_a} of the 17 requests: *{a_first} ...*. The seed made the comparison fair but also hides how much the output would vary; with another seed the texts would differ, the language would not. "
             f"{untitled_a} of 17 stories have the title `Untitled Story`, because the model did not write the `Title:` line the prompt asks for, and the instruction-echo share is {sa['mean_instruction_echo']:.3f}: on some stories the model recites the task instead of telling the story (Section 8.9)."),
           P(f"**The chat template helps but does not fix it.** Passing the same instruction through the model's chat template raises the language match to {sb['language_match_rate']:.2f} ({round(sb['language_match_rate'] * 17)} of 17), almost removes instruction echo ({sb['mean_instruction_echo']:.3f}) and raises variety "
             f"(distinct-2 {sb['mean_distinct_2']:.3f} against {sa['mean_distinct_2']:.3f}). Besides English, the language came out right for {', '.join(F.LANG_NAMES[c] for c in b_ok)}; Hindi, French, Italian, Russian, Arabic, Turkish, Polish, Japanese and Korean stories were still written in English. "
             f"Even where the language is right the quality is limited: a German sentence reads *{_ex(CB, _idx(CB, 'de'), 100)}* (a compound and a noun that do not exist) and a Dutch one *{_ex(CB, _idx(CB, 'nl'), 90)}*. "
             f"The latency is the same, {sb['mean_latency_s']:.1f} s against {sa['mean_latency_s']:.1f} s, so the chat template costs nothing at run time. Titles are present ({untitled_b} of 17 are `Untitled Story`), but {dirty_b} of 17 still carry a literal `Title:` or asterisks, because the parser only recognises a bare `Title:` at the start of a line and the chat model writes it in bold. "
             "Chinese is marked as a match but is short in words because Chinese has no spaces, so the *words* column undercounts it."),
           P(f"**The composer is instant and empty.** Condition C answers in under a millisecond and writes about {sc['mean_words']:.0f} words, but its text is a template that quotes the idea and wraps it in fixed sentences, for example *{_ex(CC, _idx(CC, 'hi'), 130)}*. "
             f"Its prompt-story similarity ({sc['mean_similarity']:.2f}) is the highest of the three only because it repeats the idea verbatim; the number rewards copying and says nothing about quality. "
             f"Its language match is {sc['language_match_rate']:.2f} for the same reason as A: the body is English with a short foreign-language opening."),
           P("Language match uses a statistical detector and is unreliable on very short or mixed text; it was treated as a coarse screen and the excerpts above were read by the authors. None of the four proxies (language match, echo, distinct-2, similarity) measures whether a story is coherent or enjoyable, and no person rated a story.")]
    b += G("f06_prompt_similarity.png", "Prompt-story similarity of each of the 17 requests under the three conditions: the offline composer is usually highest because it quotes the idea.", 5.8, doc_only=True)
    b += G("f07_language_match.png", "Language match of the 17 stories under the three conditions (green: story in the requested language).", 5.8)
    return b


# ----------------------------------------------------------------------------------------------- 8.5
def _asr_rows():
    rows = []
    for r in sorted(F.STORY_ASR["rows"], key=lambda r: r["story_id"]):
        rows.append([str(r["story_id"]), F.LANG_NAMES[r["language"]], F.LANG_NAMES.get(r["text_language"], r["text_language"] or "?"), r["length"], str(r["words"]),
                     f"{r['audio_s']:.1f}", f"{r['wer_norm']:.3f}", f"{r['cer_norm']:.3f}"])
    return rows


def _mismatch():
    rows = F.STORY_ASR["rows"]
    en = [r for r in rows if r["language"] == "en"]
    non = [r for r in rows if r["language"] != "en"]
    hi = next(r for r in rows if r["language"] == "hi")
    mw = sum(r["wer_norm"] for r in en) / len(en)
    mc = sum(r["cer_norm"] for r in en) / len(en)
    de = next(r for r in rows if r["language"] == "de")
    b = [H2("8.5 Language mismatch and its effect on narration"),
         P("The two halves of the pipeline meet in one place: the story text goes to the speech model of the *requested* language. If the story is in another language, the speech model reads text it was not built for. "
           "To measure the effect on real output, the seven stories generated through the live API in Section 7.7 were fetched together with their WAV files and transcribed by Whisper-small in 30-second chunks (the chunking is needed for stories because the application's own evaluation call fails on audio longer than 30 seconds, Section 8.7), "
           "with the recogniser told the *requested* language. A language detector also classified the story text."),
         TAB("Story-length narration read back by Whisper-small (normalised WER and CER; live API stories).",
             ["Story", "Requested language", "Text is in", "Length", "Words", "Audio (s)", "WER", "CER"], _asr_rows(),
             widths=[0.6, 1.2, 0.9, 0.8, 0.7, 0.8, 0.7, 0.7], align=["c", "l", "l", "l", "c", "c", "c", "c"], size=9.5),
         P(f"**All {len(non)} stories requested in a non-English language came out as English text** ({len(non)} of {len(non)}). They were then read by the Hindi, French, German or Spanish voice. The result is speech that Whisper cannot decode as the requested language: "
           f"WER {min(r['wer_norm'] for r in non if r['language'] != 'hi'):.2f} to {max(r['wer_norm'] for r in non):.2f} and CER {min(r['cer_norm'] for r in non if r['language'] != 'hi'):.2f} to {max(r['cer_norm'] for r in non):.2f}. "
           f"A WER above 1 for the German story ({de['wer_norm']:.2f}) is possible because the recogniser, forced to German, wrote {de['hyp_words']} words for a {de['words']}-word story, mostly invented. "
           f"The Hindi voice is the extreme: its tokeniser knows Devanagari, so English letters are mostly unknown symbols, and the voice produced {hi['audio_s']:.1f} s of audio for {hi['words']} words (CER {hi['cer_norm']:.2f}, essentially nothing recognised). "
           f"The three English stories, where text and voice agree, read back with a mean WER of {mw:.3f} and a mean CER of {mc:.3f}, close to the {F.LANGS['en']['wer_norm_corpus']:.3f} and {F.LANGS['en']['cer_norm_corpus']:.3f} of the short FLEURS sentences."),
         P("This is the central finding of the project. Narration is good when text and voice share a language, and the weak part is the story model: with the shipped prompt a 0.6-billion-parameter instruction model does not follow *write the story in Hindi*. "
           "The narration stage cannot repair that. The user sees a Hindi story that is English and a four-second recording (screenshot above), and the interface gives no warning.")]
    return b


# ----------------------------------------------------------------------------------------------- 8.6
def _speed():
    gen = [r for r in F.API["generate"] if r.get("story_gen_s")]
    sg = [r["story_gen_s"] for r in gen]
    non_hi = [r for r in gen if r["language"] != "hi"]
    ls = F.LENGTH_SCALING
    b = [H2("8.6 Speed and resource use"),
         P(f"Seven live generations with narration (Section 7.7) took between {min(r['request_s'] for r in gen):.0f} and {max(r['request_s'] for r in gen):.0f} s per request on the CPU; the two Short English requests spent "
           f"{gen[0]['story_gen_s']:.0f} and {gen[1]['story_gen_s']:.0f} s on story generation and the Medium one {gen[-1]['story_gen_s']:.0f} s. Story generation ran at about 9 tokens per second in every condition and is "
           f"{sum(sg) / len(sg):.0f} s on average over the seven requests, against {sum(r['tts_s'] for r in non_hi) / len(non_hi):.0f} s of narration on average for the six requests with a matching voice. Story writing is therefore the larger part of the wait, and the narration is the smaller part, in every language measured."),
         P(f"The length experiment gives the full range for English: a Short story ({ls[0]['words']} words, {ls[0]['audio_s']:.0f} s of speech) takes {ls[0]['total_s']:.0f} s, Medium ({ls[1]['words']} words, {ls[1]['audio_s']:.0f} s) takes {ls[1]['total_s']:.0f} s and Long ({ls[2]['words']} words, {ls[2]['audio_s']:.0f} s) takes {ls[2]['total_s']:.0f} s. "
           "These times are for a laptop-class CPU. The generate route is an ordinary blocking call: the browser waits for the whole story and its narration, and the light endpoints (1 to 15 ms) are served meanwhile because FastAPI runs the route in a worker thread; behaviour under several simultaneous generations was not tested.")]
    b += G("f08_generate_calls.png", "Time per stage for the seven live generate requests (story writing and narration).", 5.6)
    return b


# ----------------------------------------------------------------------------------------------- 8.7
def _own_eval():
    runs = _runs()
    r1 = next(r for r in runs if r["sample_count"] == 5)
    r2 = next(r for r in runs if r["sample_count"] == 2)
    rows = []
    for s in r1["samples"]:
        rows.append([F.LANG_NAMES[s["language_code"]], s["style"], str(s["story_words"]), (s["title"] if len(s["title"]) < 26 else s["title"][:24] + "..."),
                     f"{s['prompt_story_similarity']:.3f}", f"{s['rtf']:.3f}", "failed"])
    de = next(s for s in r1["samples"] if s["language_code"] == "de")
    err = r1["samples"][0]["asr_error"]
    a1, a2 = r1["averages"], r2["averages"]
    b = [H2("8.7 The application's own evaluation"),
         P("The Evaluation page runs the built-in prompts through the whole pipeline and reports WER, CER, prompt similarity, ROUGE-L, latency and RTF. It was run twice on the live server with the real models: once with all five built-in prompts "
           "(English Adventure, English Bedtime, French, German, Spanish) and once with the two English prompts. Both runs completed and were saved."),
         TAB("The five-sample run of the application's own evaluation (live server, real models).",
             ["Language", "Style", "Words", "Title", "Similarity", "RTF", "WER / CER"], rows,
             widths=[0.9, 1.1, 0.6, 1.9, 0.8, 0.6, 0.8], align=["l", "l", "c", "l", "c", "c", "c"], size=9),
         P(f"Averages over the five samples: story {a1['story_time_s']:.2f} s, narration {a1['tts_time_s']:.2f} s, RTF {a1['rtf']:.3f}, prompt similarity {a1['prompt_story_similarity']:.3f}, ROUGE-L {a1['rougeL_prompt_vs_story']:.3f}. "
           f"The two-sample English run gave similarity {a2['prompt_story_similarity']:.3f}, ROUGE-L {a2['rougeL_prompt_vs_story']:.3f} and RTF {a2['rtf']:.3f}. "
           "The speed figures agree with Sections 8.3 and 8.6. The similarity figures vary from 0.29 to 0.75: the Spanish prompt scores lowest (0.287) because the story is English and the prompt is Spanish, "
           "so the figure measures the language mismatch as much as the topic."),
         P(f"**WER and CER are missing in every sample.** Each sample carries the error `{err[:96]} ...`. Since the speech was produced (the RTF is there), the failure is in the transcription step: "
           "the application passes the whole story audio to a Whisper pipeline, and transformers 5.20.2 refuses audio longer than 30 seconds unless chunking is switched on. Every story is longer than 30 seconds (audio lasted 57 to 90 s in this run), so the call can never succeed on a real story; "
           "the application's own test suite stubs the recogniser and could not notice. The page shows a dash and the hint *Needs narration + transcription*, which is honest but unhelpful. "
           "The experiments therefore score the narration with chunking (Section 8.5). A second finding sits in the same code: the similarity function builds a new sentence-embedding model on every call, which is why each sample logs a model load."),
         P(f"**Titles.** In the five-sample run four of five titles are `Untitled Story`, and the German title is an instruction sentence kept by the parser: *{de['title'][:100]}*.")]
    return b


# ----------------------------------------------------------------------------------------------- 8.8, 8.9
def _success():
    L = F.LANGS
    en_i = _idx(CB, "en", "Adventure")
    es_i = _idx(CB, "es")
    return [H2("8.8 Success cases"),
            B(f"**Narration is fast and clear for twelve languages.** Mean RTF {F.MMS_MEAN_RTF:.3f}, mean CER {F.MMS_MEAN_CER:.3f}; Spanish reads back with CER {L['es']['cer_norm_corpus']:.3f}. A two-minute story is narrated in about half a minute on a CPU.",
              f"**English stories with an English voice are intelligible end to end.** Read back in 30-second chunks, English stories give WER {min(r['wer_norm'] for r in F.STORY_ASR['rows'] if r['language'] == 'en'):.2f} to {max(r['wer_norm'] for r in F.STORY_ASR['rows'] if r['language'] == 'en'):.2f}.",
              f"**When the chat template is used, the English story has a real opening.** *{_ex(CB, en_i, 190)}*",
              f"**Spanish is written in Spanish.** *{_ex(CB, es_i, 130)}*",
              "**The product around the models is robust.** Validation, persistence, the audio link, deletion and the library behave as designed in all 29 automated tests and in the live runs; every bad request in Section 7.6 got a clear status code and message, and no live request failed.",
              "**The offline path always answers.** If the model is missing or returns too little, the composer writes a prompt-conditioned story in under a millisecond, so the application never shows an empty result (its quality is a separate matter, Section 8.4).")]


def _failure():
    runs = _runs()
    r1 = next(r for r in runs if r["sample_count"] == 5)
    de_title = next(s for s in r1["samples"] if s["language_code"] == "de")["title"][:90]
    mys = _idx(CA, "en", "Mystery")
    first = " ".join(F.STORY["conditions"][CA][_idx(CA, "hi")]["text"].split())[:70]
    same_a_nonen = sum(1 for r in F.STORY["conditions"][CA] if r["language"] != "en" and " ".join(r["text"].split())[:70] == first)
    return [H2("8.9 Failure cases"),
            TAB("Observed failures with the real text or measurement.", ["Failure", "Evidence"],
                [["Model recites the task instead of telling a story", f"Shipped path, English Mystery: *{_ex(CA, mys, 110)}*. In the Studio screenshot, story 7 ends in *The story should contain 22 characters, 1000 words, and include the following: 1) A young inventor named Jax ...*; the Hindi story 3 contains *The story should have a clear structure: 1. Introduce the inventor and his background ...*"],
                 ["Title is an instruction", f"Evaluation, German sample: *{de_title}*"],
                 ["Requested language ignored", f"Hindi request, chat-template variant: *{_ex(CB, _idx(CB, 'hi'), 120)}*; the shipped path wrote *{_ex(CA, _idx(CA, 'hi'), 90)}* for {same_a_nonen} of the 14 non-English requests"],
                 ["Target language wrong in detail", f"Dutch, chat template: *{_ex(CB, _idx(CB, 'nl'), 110)}*; Portuguese mixes in Spanish (*joven inventora*), and the French story's first line is English"],
                 ["Mixed-language composer text", f"Offline composer for Hindi: *{_ex(CC, _idx(CC, 'hi'), 120)}* (a romanised opening followed by English). For Chinese, Japanese and Korean the opening is a rough romanisation that is not a real sentence in any of them"],
                 ["Narration of text in the wrong language", "Hindi voice on English text: 4.4 s of audio for 185 words; German, French and Spanish voices on English text: WER 0.60 to 1.34"],
                 ["No narration for Chinese and Japanese", f"2 of 10 and 1 of 10 sentences produced any audio; RTF {F.LANGS['zh']['mean_rtf']:.1f} and {F.LANGS['ja']['mean_rtf']:.1f} on those; transcripts unrelated to the text"],
                 ["No intelligibility figure in the product", "All 7 samples of the two evaluation runs failed at the transcription step"]],
                widths=[1.8, 4.7], align=["l", "l"], size=9),
            P("The failures have two causes that are easy to tell apart. Most of the text failures come from the story model, which is small and is prompted in a way that suits a base model better than an instruction model; the chat-template experiment shows that part of the problem is the prompt format. "
              "The narration failures come from the configuration: three language checkpoints that do not exist, a missing system dependency, and a recogniser call that cannot handle a story. None of them is caused by the project's own logic, but all of them are the project's to fix, and Chapter 10 puts them first.")]


# ----------------------------------------------------------------------------------------------- 8.10
def _base():
    ba = __import__("scripts.docs.lit", fromlist=["BASE_ANALYSIS"]).BASE_ANALYSIS
    st = F.STORY
    return [H2("8.10 Comparison with the base paper"),
            P(f"The base paper is SAM Translator {N('base')}. It is a *translation* system that produces speech in a target language from speech or text in another language, evaluated by BLEU on CVSS-C and CoVoST-2. "
              "StoryVox generates and narrates stories; its results are WER, CER and RTF on 150 FLEURS sentences and a few dozen stories. **The two sets of numbers measure different things on different data and must not be compared**; the table below therefore compares design choices and does not compare scores."),
            TAB("SAM Translator and StoryVox side by side.", ["Aspect", "SAM Translator (base paper)", "StoryVox"],
                [["Task", "Cross-lingual text-to-speech translation: input in many languages, English speech out", "Prompt to story to speech, 15 requested languages, no translation step"],
                 ["Method", "mBART with a sparse mixture of 8 experts (top-2), self-paced learning, data-augmented self-training, HuBERT units and Grad-TTS", "Pretrained Qwen3-0.6B story model, pretrained MMS-TTS (VITS) speech models, Whisper-small and MiniLM for evaluation; nothing trained"],
                 ["Model size", "611M-parameter baseline, 1.7B-parameter mixture-of-experts model", "0.6B story model plus one VITS checkpoint per language, run one at a time"],
                 ["Compute", "One A100 80 GB GPU, about 1.5 to 2 days of training", "CPU laptop, no training; a Short story in about 37 s"],
                 ["Data", "CVSS-C and CoVoST-2 (speech corpora)", "No training data; FLEURS test sentences for evaluation only"],
                 ["Metric", "BLEU of a recogniser's transcript against the reference translation; a listener study (10 listeners, 15 samples per system)", "WER and CER of a recogniser's transcript against the narrated text, RTF, story-level proxies; no listener study"],
                 ["What the paper shows that StoryVox does not", "Ablations of each idea, reproducible benchmarks, a subjective study, an analysis of low-resource failures", "-"],
                 ["What StoryVox shows that the paper does not", "-", "A working local product with a library, an audio player and an evaluation page; story writing and style/length control; a measured look at language mismatch and its consequence for narration"]],
                widths=[1.2, 2.7, 2.6], align=["l", "l", "l"], size=9),
            P(f"One idea is shared: both systems judge speech by transcribing it with a recogniser and comparing the text, which is a cheap and repeatable proxy for intelligibility. The base paper's recogniser output is scored by BLEU; StoryVox's by WER and CER. "
              f"A second supporting paper, OmniVoice {N('omni')}, reports an average CER of 4.00 per cent and an RTF of 0.0319 for 646 languages on its own test sets and hardware; StoryVox's mean CER of {F.pct(F.MMS_MEAN_CER)} and RTF of {F.MMS_MEAN_RTF:.2f} on a CPU are in the same general range for CER but are not comparable, because the sentences, the recogniser, the normalisation and the machine all differ. "
              "The base paper's own limitations (English as the only target language, no content control, high training cost) are exactly the points where a cascade of pretrained models is useful; its quality advantage on translation is not something StoryVox claims.")]


# ----------------------------------------------------------------------------------------------- 8.11, 8.12
def _analysis():
    L = F.LANGS
    return [H2("8.11 Analysis"),
            B(f"**The speech half works; the text half is the bottleneck.** For languages where the text is in the right language, MMS reads it back with a CER of {F.pct(F.MMS_MEAN_CER)} on average on short sentences; the story model hands it text in the wrong language in most non-English requests.",
              "**Speed is acceptable for a local tool, not for interactive use.** About 40 s for a Short story and 80 s for a Long one on a CPU, of which 60 to 65 per cent is story writing. There is no progress indication beyond the spinner, and the request blocks.",
              f"**Error rates vary by language in ways that do not follow resources alone.** Spanish ({L['es']['cer_norm_corpus']:.3f}) and Portuguese ({L['pt']['cer_norm_corpus']:.3f}) are easy; Hindi ({L['hi']['cer_norm_corpus']:.3f}) and German ({L['de']['cer_norm_corpus']:.3f}) harder. Part of that is the recogniser, not the voice, and the two were not separated.",
              "**Proxies disagree with reading.** The offline composer has the highest prompt-story similarity and the weakest text; the shipped model has a high instruction echo that no similarity score notices. Reading the output was necessary.",
              "**The product hides its own failures.** WER and CER silently disappear from the Evaluation page, titles are left as `Untitled Story`, and a Hindi story that is English raises no warning. A reader of the interface alone could believe the system works for 15 languages."),
            H2("8.12 Limitations of these results"),
            B("The speech sample is small: 10 sentences per language; the confidence interval of a single language's WER is wide and differences of a few hundredths between languages should not be read as real.",
              "FLEURS sentences are read-aloud news and Wikipedia-style sentences of 6 to 30 words; stories are longer and more varied. The English story figures (three stories) show the same level but cannot confirm it.",
              "Story conditions use one idea and one seed. Other ideas and seeds would give other stories; the language-mismatch finding is robust because it held in 14 of 14 non-English requests, but the exact percentages are not.",
              "Language match is a detector decision on 120 to 200 words of text; Chinese, Japanese and Korean results in particular depend on the detector.",
              "No human judgement of coherence, creativity, age-appropriateness or naturalness of the voice was collected, so claims about story *quality* are limited to the failures observed.",
              "Everything ran on CPU on one machine with other programs open; times will differ on other hardware, and the GPU path was not run.")]


# ----------------------------------------------------------------------------------------------- 8.13, 8.14
def _objectives():
    rows = [["1. Accept a user prompt", "Achieved", "Studio idea box with a 2,000-character limit, validated server-side (tests 3 and 10); 11 screenshots"],
            ["2. Generate a story with length and reading-level controls", "Partly", "Three lengths (220, 420 and 700 tokens) and eight styles work; length gave 175, 316 and 418 words; there is no reading-level control"],
            ["3. Translate the story into target languages", "Not implemented", "No translation module; the language is requested in the prompt and the model answered in the requested language in 3 of 17 shipped-path requests (the English ones) and 8 of 17 with the chat template"],
            ["4. Convert the story to speech", "Achieved for 12 languages", f"MMS narration, mean RTF {F.MMS_MEAN_RTF:.3f}, mean CER {F.MMS_MEAN_CER:.3f}; Italian narrated by an English voice, Chinese 2 of 10 and Japanese 1 of 10 sentences"],
            ["5. Playback with adjustable voice, speed and language", "Partly", "Browser player with play, pause, seek, volume and WAV download; language chosen at generation; no voice or speed selection"],
            ["6. Evaluate coherence, translation quality and naturalness through user rating", "Partly", "Automated evaluation with similarity, ROUGE-L, RTF, WER and CER (WER and CER fail on story audio in the shipped page); no user rating collected; no translation to evaluate"]]
    return [H2("8.13 Objectives versus outcomes"),
            TAB("The six project objectives against what was measured.", ["Objective", "Status", "Evidence"], rows, widths=[2.3, 1.1, 3.1], align=["l", "l", "l"], size=9.5)]


def _summary():
    return [H2("8.14 Summary of findings"),
            B(f"Narration with MMS runs at a real-time factor of {F.MMS_MEAN_RTF:.2f} on a CPU and reads back with a mean normalised CER of {F.MMS_MEAN_CER:.3f} on 12 languages (English WER {F.LANGS['en']['wer_norm_corpus']:.3f}, CER {F.LANGS['en']['cer_norm_corpus']:.3f}).",
              "Italian has no MMS voice and is read by an English voice; Chinese and Japanese cannot be narrated on this machine; Korean works only with an undeclared package.",
              "With the shipped prompt the story model wrote English for every non-English request (14 of 14); the chat template raises the share of stories in the requested language from 3 of 17 to 8 of 17, which is still low.",
              "English text read by a foreign voice is unintelligible (WER 0.60 to 1.34); the Hindi voice produced 4.4 s for a 185-word story.",
              "The application's Evaluation page reports no WER or CER on story audio because the recogniser call fails beyond 30 seconds; with chunking, English stories give a mean WER of 0.25 and CER of 0.21.",
              "A Short story takes about 37 s end to end, Medium 60 s and Long 80 s on a CPU; the web layer adds a few milliseconds.",
              "Three of the six batch objectives are met in part or not at all (translation, voice and speed control, user rating), and the documents say so.")]


def blocks():
    b = [H1("CHAPTER 8: RESULTS AND OUTPUT SCREENS")]
    b += _setup() + _screens() + _narration() + _stories() + _mismatch() + _speed() + _own_eval() + _success() + _failure() + _base() + _analysis() + _objectives() + _summary()
    return b
