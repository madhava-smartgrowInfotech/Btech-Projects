"""Text of 19.IEEE_Paper.docx (StoryVox). Every number is read from facts.py (experiments/*/metrics.json) and agrees with docs/REPORT_FACTS.md.

Citations are written {r:key,key} (keys of refs.py); Paper.expand numbers them in order of first appearance, the base paper being [1].
"""
from . import facts as F
from . import paper_figs
from .paper import Paper

L = F.LANGS
S = F.STORY_SUMMARY
A, B, C = S["A_app_raw_prompt"], S["B_chat_template"], S["C_local_composer"]
LS = F.LENGTH_SCALING
EP = F.API["endpoints"]
GEN = F.API["generate"]
SA = F.STORY_ASR["rows"]
EN_SA = [r for r in SA if r["language"] == "en"]
NON_SA = [r for r in SA if r["language"] != "en"]
BCOND = F.STORY["conditions"]["B_chat_template"]
B_OK_NON_EN = [r["language"] for r in BCOND if r["language"] != "en" and r["language_match"]]


def _w(c, k):
    return L[c][k]


def build(path):
    figs = paper_figs.make()
    P = Paper()
    en_wer = sum(r["wer_norm"] for r in EN_SA) / len(EN_SA)
    en_cer = sum(r["cer_norm"] for r in EN_SA) / len(EN_SA)
    non_wer = (min(r["wer_norm"] for r in NON_SA if r["language"] != "hi"), max(r["wer_norm"] for r in NON_SA if r["language"] != "hi"))
    hi = next(r for r in SA if r["language"] == "hi")
    mms_rtf = [L[c]["mean_rtf"] for c in F.MMS_LANGS]
    ep_med = [EP[k]["median_ms"] for k in EP if "422" not in k]
    stories_words = hi["words"]

    authors = [[n.upper(), f"Roll No. {r}", "Dept. of Computer Science and Engineering", F.COLLEGE_SHORT, "Hyderabad, India", "[EMAIL]"] for n, r in F.STUDENTS]
    authors.append([F.GUIDE.upper(), f"{F.GUIDE_DESIGNATION} (project guide)", "Dept. of Computer Science and Engineering", F.COLLEGE_SHORT, "Hyderabad, India", "[EMAIL]"])
    P.title_block("StoryVox: A Multilingual Story Generation and Speech System", authors)
    P.begin_two_columns()

    P.abstract(
        "Reading aloud a story that was written on demand, in the listener's own language, needs a text generator and a speech synthesiser that are usually studied apart. "
        "StoryVox joins them in one locally runnable application: a story idea, a language, a style and a length go to a 0.6-billion-parameter language model, and the text is "
        "narrated by a per-language VITS speech model, with every result stored in a library and scored by a speech recogniser. Nothing in the system is trained; it is a cascade of pretrained models. "
        f"We measured it on one CPU laptop. Narration in {len(F.MMS_LANGS)} languages ran at a mean real-time factor of {F.MMS_MEAN_RTF:.2f} with a mean normalised character error rate of {F.MMS_MEAN_CER:.3f} "
        f"after transcription. Story generation is the weak link: with the shipped prompt the model answered in the requested language for only {A['language_match_rate']:.2f} of 17 test cases, and four of four non-English stories "
        "were narrated by a foreign voice. The built-in evaluation also returns no error rates for story-length audio. We report these findings and the fixes they suggest.",
        ["cascade pipeline", "multilingual speech synthesis", "real-time factor", "speech recognition", "story generation", "text-to-speech evaluation", "word error rate"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para("Children's tales, language lessons and accessibility tools all benefit from stories that are read aloud, and large language models can now write a story from a one-line idea. "
           "Turning that text into speech in many languages is a separate problem: one line of work scales text-to-speech to hundreds of languages {r:mms,omni}, another builds expressive or child-directed voices for a few {r:emo,multigen}, "
           "and a third translates text into speech directly {r:base}. A person who simply wants a story in Hindi or Spanish today has to run a language model, find a speech model for the language and check by ear whether the result is usable. "
           "Most of these systems also expect a GPU or large amounts of training data, which a school or a home laptop does not have. "
           "The problem addressed here is therefore practical rather than architectural: can a student-built application, using only pretrained parts and a CPU, generate a short story on request in a chosen language, read it aloud, "
           "and report honestly how well each step worked? The intended users are teachers, parents and learners who want a story on a topic of their choice, and the same pipeline could serve accessibility tools that read generated text aloud.")
    P.para("StoryVox closes that loop on a CPU. It is a web application over a FastAPI service that accepts a story idea (up to 2,000 characters), a language (15 offered), a style (8) and a length (3), generates the story with Qwen3-0.6B {r:qwen3}, "
           "narrates it with the language's MMS-TTS checkpoint {r:mms} and saves story and audio so that they can be replayed and downloaded. An evaluation page transcribes the narration with Whisper {r:whisper} "
           "and reports word and character error rates, topic similarity, ROUGE-L and real-time factor.")
    P.para("Contributions: (1) StoryVox, a tested, locally runnable pipeline and console from story idea to saved narration. "
           f"(2) A round-trip measurement of narration across 15 languages on the FLEURS benchmark {{r:fleurs}}, giving speed and intelligibility per language. "
           "(3) A controlled comparison of three story-generation conditions on 17 test cases that exposes a language-mismatch problem. "
           "(4) A list of defects found while measuring, among them an evaluation page that cannot score audio longer than 30 s, with a separate script that does. "
           "Section II reviews related work, Section III describes the method, Section IV gives results and Section V concludes.")
    P.sub("A", "System Hardware")
    P.para("Every number was measured on one machine: Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB RAM, Windows 11, no GPU, so all models ran on the CPU.")
    P.sub("B", "Software Requirements")
    P.para("Python 3.11.9, PyTorch 2.14.1 and Hugging Face Transformers 5.20.2 {r:hf}; FastAPI with SQLite for the service, React 19 with Vite for the console, jiwer for error rates, sentence-transformers for similarity, "
           "and ffmpeg so that Whisper can read WAV files. The first run downloads the model weights; afterwards no data leave the machine.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para("**Base paper.** Tran and Sakti {r:base} (SAM Translator) translate source-language text into target speech without a cascade. A multilingual BART {r:mbart} encoder-decoder predicts discrete speech units from text and a Grad-TTS decoder "
           "turns them into a waveform. Three additions raise quality: self-paced learning {r:spl} orders training examples from easy to hard, sparse mixture-of-experts layers {r:moe} (8 experts, top-2 routing) raise capacity "
           "from 611M to 1.7B parameters, and data-augmented self-training adds synthetic pairs for low-resource languages. Output speech is transcribed and scored with BLEU on CVSS-C (21 source languages to English) and CoVoST-2. "
           "Reported gains are about 2-3% relative for high-resource and 7-10% for low-resource languages on CVSS-C, and about 21.6% for Welsh with self-training. "
           "The authors note an English-only target, weaker results than a cascade for some languages, repetition errors and a heavy budget: an A100 GPU for 1.5-2 days.")
    P.para("**Speech at scale.** VITS {r:vits} maps text directly to a waveform with a variational autoencoder, a normalising flow and adversarial training; MMS {r:mms} released one such checkpoint for 1,107 languages. "
           "OmniVoice {r:omni} covers 646 languages with a diffusion language model and reports a 4.00% average character error rate on FLEURS at RTF 0.0319 on a GPU; MultiGen {r:multigen} fine-tunes a language model for child-friendly Malay, Tamil and Mandarin; "
           "EmoSSLSphere {r:emo} adds emotion control. **Stories.** TinyStories {r:tinystories} shows that very small models write coherent short English stories when the data are narrow; hierarchical generation {r:fan} and nucleus sampling {r:holtzman} "
           "address plot and repetition; Qwen3 {r:qwen3} is an open family whose 0.6B member fits a laptop; Kahaani {r:kahaani} pairs story co-creation with speech for children. "
           "**Evaluation.** Speech is commonly judged by transcribing it with a recogniser {r:whisper} on a multilingual benchmark {r:fleurs}; topic fit uses multilingual sentence embeddings {r:sbertm} and ROUGE {r:rouge}.")
    P.table("Related work compared", ["Work", "Approach", "Data", "Reported result", "Limitation"],
            [["SAM Translator {r:base}", "mBART units + Grad-TTS, SPL, MoE", "CVSS-C, CoVoST-2", "BLEU +2-10% rel.; Welsh +21.6%", "English target; A100, 1.5-2 days"],
             ["OmniVoice {r:omni}", "Diffusion LM, zero-shot TTS", "581k h, 646 languages", "Mean CER 4.00%; RTF 0.0319", "8 GPUs, 9.7 days; no story text"],
             ["MultiGen {r:multigen}", "LLM speech tokens, child voices", "Private Malay, Tamil, Mandarin", "Tamil CER 9.6% to 2.1%", "3 languages; data not public"],
             ["EmoSSLSphere {r:emo}", "Spherical emotion vectors", "English, Japanese", "Better prosody (listening test)", "2 languages; no story content"],
             ["Kahaani {r:kahaani}", "LLM story co-creation + speech", "Not specified", "Interactive system", "No multilingual narration reported"],
             ["MMS {r:mms}", "VITS checkpoint per language", "1,107 languages", "ASR halves Whisper WER (54 languages)", "Single voice; narrow domain"]],
            [0.62, 0.7, 0.62, 0.78, 0.68], size=5.8, align=["l", "l", "l", "l", "l"])
    P.para("**Gap.** The surveyed systems advance speech translation, massively multilingual synthesis and speech evaluation, but none joins controllable story generation to multilingual narration in one locally runnable application and then measures "
           "the whole chain with the story model, the speech model and a recogniser. Translation papers report BLEU and synthesis papers report MOS or CER on read sentences; neither says whether a small model on a laptop can tell a story in Hindi.")

    P.para("**Positioning.** StoryVox borrows rather than competes. From MMS it takes the per-language checkpoints, from Whisper the role of judge, and from the base paper the idea of scoring speech by transcribing it; "
           "it does not take the base paper's training recipe. The datasets it relies on are the pretrained models' own training corpora, which it does not touch, and FLEURS {r:fleurs}, a read-speech benchmark with the same sentences in 102 languages, which supplies the test text. "
           "The algorithms are standard: autoregressive sampling with a temperature and a nucleus cut-off {r:holtzman}, sentence chunking, a VITS forward pass, and edit-distance error rates. "
           "The strengths of this design are that it runs offline on modest hardware and that every stage can be inspected; the weaknesses are the small story model, one fixed voice per language, and error that accumulates along the chain.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.sub("A", "Pipeline and Design Choice")
    P.para("StoryVox is a cascade of three pretrained models behind one API (Fig. 1); no model was trained or fine-tuned. A cascade was chosen over a single end-to-end model because each stage can be replaced, "
           "each runs on a CPU and each can be measured separately, whereas the base paper's model needs a GPU and a training run that a student project cannot repeat. "
           "The speech stage sits behind an abstract provider interface with two implementations, MMS-TTS first and an operating-system voice second, so that a missing checkpoint degrades the result instead of stopping the request.")
    P.figure(figs["arch"], "System architecture of StoryVox: web app, FastAPI service, three model services and storage.")
    P.sub("B", "Story Generation")
    P.para("The prompt names the idea, the language, the style and the paragraph count (3, 5 or 8 for Short, Medium and Long) and asks for a title line followed by the story. It is sent unchanged, without the model's chat template, "
           "to a Transformers text-generation pipeline with Qwen3-0.6B, temperature 0.8, nucleus probability 0.9 and a budget of 220, 420 or 700 new tokens. The first line becomes the title. "
           "If the output has fewer than 20 words or the pipeline fails, an offline composer writes a template story that quotes the idea and says so in its model field. "
           "The eight styles (Adventure, Fantasy, Educational, Bedtime, Mystery, Inspirational, Funny, Custom) only change the style word and a short guidance phrase in the prompt; there is no separate model or adapter per style, and no reading-level control exists. "
           "At each step the model assigns a score z to every word piece; with temperature T the sampling distribution is")
    P.eq("p_T(w) = exp(z_w / T) / sum_v exp(z_v / T)", size=10)
    P.para("and nucleus sampling {r:holtzman} draws only from the smallest set of word pieces whose probabilities add up to 0.9. A lower T or a smaller nucleus makes the text more predictable and repetitive; T = 0.8 and 0.9 are the application's settings, and we did not tune them. "
           "Story generation is the expensive stage because it is autoregressive: each new token needs one forward pass of the 0.6B model, so time grows with the token budget, whereas the VITS decoder produces a whole chunk at once.")
    P.sub("C", "Narration")
    P.para("The text is split at sentence ends into chunks of at most 380 characters; each chunk is synthesised by the language's MMS-TTS checkpoint {r:mms}, a VITS model {r:vits} that outputs a 16 kHz waveform. "
           "Chunks are peak-normalised to 0.9 and joined with 0.25 s of silence, and a silent result is rejected. Languages without a checkpoint use the OS voice. A VITS model is deterministic enough that one forward pass per chunk is used; the checkpoints are cached in memory after the first call, which is why the first story in a language is slower. Korean text must first be romanised with uroman. Speed is the real-time factor")
    P.eq("RTF = t_synth / t_audio", size=10)
    P.para("where t_synth is wall-clock synthesis time and t_audio the duration of the audio; values below 1 are faster than real time.")
    P.sub("D", "Evaluation Protocol")
    P.para("Round trip: ten sentences per language (6-30 words, 12-70 characters for Chinese and Japanese) are taken from the FLEURS test split {r:fleurs} (CC BY 4.0), narrated by the application's own service and transcribed by Whisper-small with the language forced. "
           "Error rates use the usual definition")
    P.eq("WER = (S + D + I) / N", size=10)
    P.para("with S, D and I the substitutions, deletions and insertions against N reference words; CER is the same at character level. We report normalised scores (Unicode NFKC, lower case, punctuation removed, spaces removed for Chinese and Japanese, "
           "where WER is not reported) because the application's own function compares raw strings. The error rates combine the speech model's and the recogniser's errors; the recogniser's own floor was not measured.")
    P.para("Story study: one idea (\"A young inventor discovers a hidden library.\"), Short length, seed 0, 17 cases (English in three styles and the other 14 languages in the Adventure style) under three conditions: "
           "A the shipped path; B the same prompt through the Qwen3 chat template with thinking disabled (an experiment, not in the product); C the offline composer. "
           "Metrics are generation latency, language match (langdetect), the share of sentences that repeat instructions, distinct bigrams, and multilingual MiniLM {r:sbertm} cosine and ROUGE-L {r:rouge} between idea and story. "
           "These are proxies for on-topic, varied text; no person rated the stories.")
    P.figure(figs["flow"], "Main flow: from story idea to saved narration (left) and the evaluation branch (right).")
    P.sub("E", "Implementation")
    P.para(f"The service has 11 routes, three SQLite tables (stories, audio_outputs, evaluations) and validates every request (empty or over-long prompt, unknown language, style or length return 422; unknown ids 404). "
           f"The console has five pages. {F.PYTEST_TOTAL} automated tests pass ({F.PYTEST_API} on the API and {F.PYTEST_UNIT} on helpers, the composer in all 15 languages and edge cases); they stub the models, so the real models are exercised by the measurement scripts. "
           "Failures are reported instead of hidden: a silent waveform is rejected, a model that fails to load falls back to the next provider, and an unreadable audio path is refused (a test checks that a path escaping the audio folder is rejected). "
           "Deleting a story removes its audio file and its rows. The service is meant for one user on one machine: it has no accounts or authentication, SQLite foreign-key enforcement is not switched on, and the story model is loaded with remote-code execution enabled in the Transformers call, a setting a deployment should review.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.sub("A", "Test Conditions")
    P.para(f"CPU only, one run per case, seed 0 where sampling is used. Whisper-small loaded in {F.TTS['asr_load_s']:.1f} s and Qwen3-0.6B in {F.STORY['model_load_s']:.1f} s; ten of the twelve MMS checkpoints took 19-25 s to load, English and Korean 1.8 s. "
           "Numbers from ten sentences per language carry wide uncertainty and should be read as indications.")
    P.sub("B", "Narration Speed and Intelligibility")
    P.para(f"Twelve languages are narrated by MMS (Fig. 3). The mean real-time factor is {F.MMS_MEAN_RTF:.3f}; eleven of them lie between {min(mms_rtf):.3f} and {sorted(mms_rtf)[-2]:.3f} and Korean is slower at {L['ko']['mean_rtf']:.2f}. "
           f"Mean normalised CER is {F.MMS_MEAN_CER:.3f} and mean WER {F.MMS_MEAN_WER:.3f}. Spanish is clearest (WER {_w('es', 'wer_norm_corpus'):.3f}, CER {_w('es', 'cer_norm_corpus'):.3f}) and Hindi worst (WER {_w('hi', 'wer_norm_corpus'):.3f}, CER {_w('hi', 'cer_norm_corpus'):.3f}); "
           f"English reaches WER {_w('en', 'wer_norm_corpus'):.3f} and CER {_w('en', 'cer_norm_corpus'):.3f}. "
           "WER is roughly two to four times CER in every language, as expected, because one wrong character makes a whole word wrong. "
           "Because a round trip scores the speech model and Whisper-small together, a high Hindi error may come from either; we did not run the recogniser on natural Hindi speech to separate them.")
    P.table("Measured results (CPU, normalised scores)", ["Measurement", "Value"],
            [[f"Narration, {len(F.MMS_LANGS)} MMS languages: mean RTF", f"{F.MMS_MEAN_RTF:.3f}"],
             ["Mean CER / WER after round trip", f"{F.MMS_MEAN_CER:.3f} / {F.MMS_MEAN_WER:.3f}"],
             ["English WER / CER (10 sentences)", f"{_w('en', 'wer_norm_corpus'):.3f} / {_w('en', 'cer_norm_corpus'):.3f}"],
             ["Italian (OS voice) WER / CER", f"{_w('it', 'wer_norm_corpus'):.3f} / {_w('it', 'cer_norm_corpus'):.3f}"],
             ["Chinese / Japanese: sentences spoken, CER", f"{L['zh']['narrated']}/10, {_w('zh', 'cer_norm_corpus'):.2f} / {L['ja']['narrated']}/10, {_w('ja', 'cer_norm_corpus'):.2f}"],
             ["Story latency, shipped path A (Short)", f"{A['mean_latency_s']:.1f} s ({A['mean_tok_per_s']:.1f} tok/s)"],
             ["Language match A / B / C", f"{A['language_match_rate']:.2f} / {B['language_match_rate']:.2f} / {C['language_match_rate']:.2f}"],
             ["Instruction repeats A / B / C", f"{A['mean_instruction_echo']:.3f} / {B['mean_instruction_echo']:.3f} / {C['mean_instruction_echo']:.3f}"],
             ["Distinct bigrams A / B / C", f"{A['mean_distinct_2']:.2f} / {B['mean_distinct_2']:.2f} / {C['mean_distinct_2']:.2f}"],
             ["Idea-story similarity A / B / C", f"{A['mean_similarity']:.2f} / {B['mean_similarity']:.2f} / {C['mean_similarity']:.2f}"],
             ["End to end, Short / Medium / Long", f"{LS[0]['total_s']:.0f} / {LS[1]['total_s']:.0f} / {LS[2]['total_s']:.0f} s"],
             ["English story WER / CER (chunked ASR, n=3)", f"{en_wer:.2f} / {en_cer:.2f}"],
             ["API median latency, non-model routes", f"{min(ep_med):.1f}-{max(ep_med):.1f} ms"]],
            [2.3, 1.1], size=6.5, align=["l", "c"])
    P.figure(figs["results"], "Normalised WER and CER per language (10 FLEURS sentences each). Hatched bars (*) use the OS voice because no MMS checkpoint exists. Chinese and Japanese are omitted (CER 0.85 and 1.00).")
    P.para(f"Italian, Chinese and Japanese have no MMS checkpoint on the model hub (the checkpoint names the application requests do not exist on the hub), so the operating-system voice speaks them. On the test machine only English voices are installed: Italian is read with an English voice (WER {_w('it', 'wer_norm_corpus'):.2f}), "
           f"and the fallback produced audio for only {L['zh']['narrated']} of 10 Chinese and {L['ja']['narrated']} of 10 Japanese sentences, with CER {_w('zh', 'cer_norm_corpus'):.2f} and {_w('ja', 'cer_norm_corpus'):.2f}. Korean works only after installing the romaniser uroman, which the requirements file does not list.")
    P.para(f"Speed is almost independent of language: ten of the twelve MMS languages lie within {min(mms_rtf):.2f}-{max(L[c]['mean_rtf'] for c in F.MMS_LANGS if c != 'ko'):.2f}, because the VITS decoder cost depends on audio length, not on the script. "
           f"Arabic sentences were the longest ({L['ar']['mean_duration_s']:.1f} s of audio on average against {L['en']['mean_duration_s']:.1f} s for English) yet kept the same factor. "
           f"The Korean factor of {L['ko']['mean_rtf']:.2f} includes romanisation. At these factors a one-minute narration costs about 15 s of synthesis on the CPU, so playback can start after a short wait but not instantly.")
    P.sub("C", "Story Generation")
    P.para(f"Story latency is about {A['mean_latency_s']:.0f} s for a Short story at {A['mean_tok_per_s']:.1f} tokens/s and scales with the token budget (Table II, Fig. 7). With the shipped prompt the model wrote in the requested language in {A['language_match_rate']:.2f} of 17 cases, which are the three English cases; "
           f"for every other language it produced the same English tale, often headed \"Untitled Story\", and {A['mean_instruction_echo']:.0%} of its sentences repeated the instructions on average. "
           f"With the chat template (B) the match rises to {B['language_match_rate']:.2f} and instruction repeats nearly vanish, but target-language text appears only for {', '.join(F.LANG_NAMES[c] for c in B_OK_NON_EN)}; Hindi, French, Italian, Russian, Arabic, Turkish, Polish, Japanese and Korean stay English. "
           f"The composer is instant but template-like; its high idea-story similarity ({C['mean_similarity']:.2f}) comes from quoting the idea and is not a quality signal. Because condition A with seed 0 repeats near-identical text, its variety score is low.")
    P.para(f"Length scales roughly linearly with the token budget. A Short story (220 tokens) took {LS[0]['gen_s']:.0f} s to write and {LS[0]['tts_s']:.0f} s to narrate ({LS[0]['words']} words, {LS[0]['audio_s']:.0f} s of audio); Medium (420 tokens) {LS[1]['gen_s']:.0f} s and {LS[1]['tts_s']:.0f} s "
           f"({LS[1]['words']} words, {LS[1]['audio_s']:.0f} s); Long (700 tokens) {LS[2]['gen_s']:.0f} s and {LS[2]['tts_s']:.0f} s ({LS[2]['words']} words, {LS[2]['audio_s']:.0f} s). Writing therefore takes 60-65% of the end-to-end time. "
           f"Over seven real calls through the API, the request took {min(g['request_s'] for g in GEN):.0f}-{max(g['request_s'] for g in GEN):.0f} s, the first (cold) call {GEN[0]['request_s']:.0f} s, while the routes that load no model answered in {min(ep_med):.1f}-{max(ep_med):.1f} ms at the median.")
    P.sub("D", "Story-Length Narration and the Evaluation Defect")
    P.para(f"Narration of a story lasts 44-137 s in our runs (Hindi aside). Whisper's pipeline call used by the application's evaluation rejects audio longer than 30 s under Transformers 5.20, so all five samples of its evaluation run carry an ASR error and the page shows WER and CER as dashes (Fig. 5). "
           f"Scoring the same audio with 30 s chunking gives WER {en_wer:.2f} and CER {en_cer:.2f} for the three English stories. The four stories requested in Hindi, French, German and Spanish were English text read by that language's voice: "
           f"WER was {non_wer[0]:.2f}-{non_wer[1]:.2f} for French, German and Spanish, and the Hindi voice produced {hi['audio_s']:.1f} s of audio for {stories_words} words. The fix is one argument; we did not change the product.")
    P.para("Failure cases seen in the saved stories: an English story that opens with the line \"Now, write the story in the required format\", a German request whose title came back as the instruction \"The title should include ...\", "
           "and a Short English story whose text states that it \"should contain 22 characters, 1000 words\" (visible in Fig. 4). Such lines are the model continuing the prompt instead of answering it, which the chat template largely removes.")
    P.sub("E", "Output Screens")
    P.figure(figs["studio"], "Studio page with a generated English story, its narration player and the model that produced the voice (real capture, crop).", width=3.1)
    P.figure(figs["eval"], "Evaluation page (real capture; metric cards and Samples tab joined): speed, latency and similarity are measured; WER and CER are empty because the ASR step failed on audio over 30 s.")
    P.figure(figs["lang"], "Did the story come out in the requested language (green) or not (red)? 17 cases, three conditions; en-Ad, en-Be and en-My are English in the Adventure, Bedtime and Mystery styles.")
    P.figure(figs["scale"], "End-to-end time by story length on the CPU: generation grows with the token budget; narration follows the audio length.")
    P.sub("F", "Comparison with the Base Paper")
    P.para("The scores cannot be compared. SAM Translator {r:base} reports BLEU for translation into English speech on CVSS-C and CoVoST-2 after training on a GPU; StoryVox translates nothing, trains nothing and reports round-trip error rates and speed on FLEURS sentences. "
           "OmniVoice's 4.00% CER {r:omni} was measured on a GPU over 102 languages; our CER is not comparable either, since the recogniser, the sample (ten sentences) and the hardware all differ. What can be compared is the design: a cascade of small pretrained parts "
           f"that runs on a CPU in about {LS[0]['total_s']:.0f} s for a Short story versus a trained model with 1.7 billion parameters.")
    P.sub("G", "Reproducibility")
    P.para("All figures in this section are read from JSON files written by four scripts in the repository (round-trip and story experiments, API timing, test run, and chunked story scoring); each script calls the application's own service functions, "
           "so the numbers describe the shipped behaviour rather than a re-implementation. The Hugging Face hub supplies FLEURS and all weights, and the machine and library versions are given in Section I.")
    P.sub("H", "Objectives against Outcomes")
    P.para("The batch objectives were: (1) accept a prompt, met; (2) generate a story with length and reading-level controls, partly met (three lengths and eight styles, no reading level); (3) translate into target languages, not met, since the language "
           "is only requested in the prompt and the small model usually ignores it; (4) convert to speech, met for twelve languages and unreliable for Italian, Chinese and Japanese; (5) play back with adjustable voice, speed and language, partly met "
           "(a browser player with seek and download, language fixed at generation, no voice or speed choice); (6) evaluate coherence, translation quality and naturalness through user rating, partly met "
           "(automatic proxies and a recogniser-based score, no ratings from people).")
    P.sub("I", "Limits")
    P.para("Threats to validity: language identification with langdetect is unreliable on short text; the idea-story similarity rewards copying; one seed gives one sample of each condition; the chat-template condition was not applied to the product. "
           "Ten sentences per language, one machine, one idea and one seed; no human listeners; the recogniser's error floor unmeasured; story quality judged only by proxies. Translation, voice or speed selection and user ratings, which the project objectives list, are not implemented.")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion and Future Scope")
    P.para("StoryVox shows that a cascade of small pretrained models can turn an idea into a stored narration on a CPU in 37-80 s, and that narration is the strong stage: twelve languages are read at about a quarter of real time with a mean normalised CER of "
           f"{F.MMS_MEAN_CER:.3f}. The main finding is negative: the 0.6B story model, prompted as shipped, writes English whatever language is requested, so the speech model then reads text it was not built for. "
           "Of the six objectives, prompt input and speech output are met, story length and style controls partly, and translation, voice and speed choice and user rating not at all. "
           "Four changes would help most: apply the chat template and check the language of the output, chunk audio in the evaluation, add the missing checkpoints and dependencies to the requirements, "
           "and add a translation step or a larger model. Listening tests with people would turn the proxy scores into evidence of quality.")
    P.para("Future scope in order of expected value: (1) a language check on the generated text with an automatic retry or a translation fallback; (2) a larger or multilingual-tuned story model, or a two-step design that writes in English and translates with a dedicated model; "
           "(3) voice and speed selection, and per-language checkpoints beyond MMS for Italian, Chinese and Japanese; (4) a human rating form in the console, which would also meet the user-rating objective; "
           "(5) measuring the recogniser's own error on natural speech so that the speech model's share of each error rate can be separated; (6) a GPU or quantised build to bring a Short story well under half a minute.")
    P.references()
    P.save(path)
    return P
