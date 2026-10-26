"""Chapter 2: Literature survey."""

from . import facts as F
from . import lit
from .blocks import B, H1, H2, P, TAB
from .refs import N as C


def blocks():
    out = _blocks()
    if F.REPORT:   # compact report variant
        from .ch1 import trim
        out = trim(out, drop=("The four titles of the batch survey that follow",),
                   replace={"Comparison of the surveyed work": ("tab", "Comparison of the surveyed work", ["Work", "Approach", "Reported result", "Limitation"],
                                                               [[r[1], r[2], r[4], r[5]] for r in lit.ROWS if r[0] in ("base", "omni", "multigen", "emo", "kahaani", "vits", "mms", "whisper", "qwen3", "tinystories")],
                                                               [1.1, 2.3, 1.6, 1.5], ["l", "l", "l", "l"], 8.5)})
        out.insert(len(out) - 2, P("The four remaining titles of the batch survey (references " + C('s2', 's3', 's4', 's5') + ") are cited as the batch lists them; only EmoSSLSphere could be located and read, "
                                   "and the other three are listed in the reference list without any claim about their content."))
    return out


def _blocks():
    ba = lit.BASE_ANALYSIS
    a = F.STORY_SUMMARY["A_app_raw_prompt"]
    return [
        H1("CHAPTER 2: LITERATURE SURVEY"),
        H2("2.1 Overview"),
        P("The survey has four threads, because the project joins four bodies of work. The first is neural story generation with small language models. The second is multilingual and low-resource text-to-speech. "
          f"The third is cross-lingual speech translation, which is the subject of the base paper {C('base')}. The fourth is how generated speech is evaluated: transcription-based error rates, real-time factor and embedding similarity. "
          "The base paper is analysed in depth in Section 2.2; every claim about it in this report was checked against the paper itself, which is in the batch folder. "
          "Claims about the other works come from their own papers, abstracts or proceedings pages and are limited to what those sources state."),
        P("The batch literature survey (5.LITERATURE SURVEY.docx) lists five works: the base paper and four papers from 2025 and 2026 on multilingual story generation, emotional speech synthesis, speech for programming languages and speech-guided motion synthesis. "
          f"We searched for all four by title. EmoSSLSphere {C('emo')} was located (arXiv 2508.11273) and is described below; the other three were not found online, so they are listed in the reference list as the batch gave them and are not described or used for any claim here. "
          f"We added companion work that the application actually uses or that bears directly on its design: OmniVoice {C('omni')}, MultiGen {C('multigen')}, Kahaani {C('kahaani')}, VITS {C('vits')}, MMS {C('mms')}, Whisper {C('whisper')} and Qwen3 {C('qwen3')}. "
          "(The repository note `archived_base_papers/BASEPAPER_REFERENCES.md` names OmniVoice as base paper; the batch documents name SAM Translator, so SAM Translator is the base paper used here and OmniVoice is cited as supporting work.)"),
        H2("2.2 Base Paper Analysis"),
        P(f"**Reference.** C. Tran and S. Sakti, \"SAM Translator: Self-paced learning and mixture-of-experts for cross-lingual text-to-speech translation,\" IEEE Access, vol. 14, pp. 2742-2752, 2026, doi 10.1109/ACCESS.2025.3644647 {C('base')}."),
        P("**Problem.** Text-to-speech translation turns text in one language into speech in another. A cascade of translation and synthesis accumulates errors and needs a model for each step; "
          "direct text-to-unit models predict discrete speech units straight from source text, but their quality drops for low-resource languages where parallel data are scarce. "
          "The authors ask how to improve a direct model without collecting more real data."),
        P(f"**Method.** {ba['summary']}"),
        P("**Data.** CVSS-C (speech-translation data covering 21 source languages into English speech) and CoVoST-2 (about 209K, 14K and 14K train, dev and test utterances). "
          "The target is always English speech, and the model's output is judged by transcribing it and scoring BLEU against the reference translation."),
        TAB("Base paper at a glance", ["Aspect", "What the base paper reports"],
            [["Architecture", "mBART text-to-unit model; feed-forward layers replaced by a sparse mixture of 8 experts (top-2 routing); HuBERT-Base units, K-means K = 200, 50 units per second; Grad-TTS decoder"],
             ["Training tricks", "Self-paced learning (threshold tau starts at 2, +0.25 every 2,000 steps); data-augmented self-training with 5K, 10K and 15K filtered synthetic pairs for six low-BLEU languages"],
             ["Scale and cost", "611M-parameter baseline, 1.7B-parameter MoE model; one A100 80 GB GPU; about 1.5 to 2 days of training"],
             ["Evaluation", "wav2vec 2.0 recogniser transcribes the output; BLEU on CVSS-C and CoVoST-2; subjective study with 10 listeners and 15 samples per system"],
             ["Headline results", "Relative BLEU gains of about 2-3% (high-resource) and 7-10% (low-resource) over mBART on CVSS-C; DAST about +21.6% for Welsh and +25.83% for Mongolian; +4-6% on CoVoST-2"],
             ["Subjective study", "Naturalness 4.12 +/- 0.14 for speech units against 4.15 +/- 0.14 for text-based synthesis"]],
            widths=[1.5, 5.0], align=["l", "l"], size=10),
        P("**Strengths.** " + " ".join(ba["strengths"])),
        P("**Limitations.** " + " ".join(ba["limitations"])),
        P("**What this project takes and what it does not.** StoryVox takes " + "; ".join(x[0].lower() + x[1:].rstrip(".") for x in ba["adopts"]) + ". It does not take: "
          + " ".join(ba["not_adopts"])),
        TAB("Base paper and StoryVox compared", ["Aspect", "Base paper", "StoryVox"],
            [["Task", "Translate text into English speech", "Generate a story in a chosen language and narrate it"],
             ["Model", "One trained mBART + MoE text-to-unit model, Grad-TTS vocoder", "Pretrained Qwen3-0.6B (story) + pretrained MMS-TTS VITS (voice); nothing trained"],
             ["Training", "Self-paced learning, mixture-of-experts, data-augmented self-training", "None"],
             ["Hardware", "One A100 80 GB GPU", "CPU only (12 threads)"],
             ["Languages", "21 source languages to English", f"15 requested; speech models for {len(F.MMS_LANGS)} (MMS), OS voice for the rest"],
             ["Evaluation", "BLEU of the ASR transcript on CVSS-C and CoVoST-2", "Round-trip WER and CER on 10 FLEURS sentences per language, RTF, story-level proxies"],
             ["Comparability", "-", lit.BASE_ANALYSIS["comparability"]]],
            widths=[1.2, 2.5, 2.8], align=["l", "l", "l"], size=10),
        H2("2.3 " + lit.THEMES[0][0]),
        P(lit.THEMES[0][1]),
        P(f"The measurement in Chapter 8 supports the cautious reading of this literature. With the application's own prompt, the 0.6-billion-parameter model produced text in the requested language in only {F.pct(a['language_match_rate'], 0)} of 17 test cases; "
          "small models can tell a fluent short story in the language they know best, but the language-following ability of a model this small is limited."),
        H2("2.4 " + lit.THEMES[1][0]),
        P(lit.THEMES[1][1]),
        H2("2.5 " + lit.THEMES[2][0]),
        P(lit.THEMES[2][1]),
        H2("2.6 " + lit.THEMES[3][0]),
        P(lit.THEMES[3][1]),
        H2("2.7 " + lit.THEMES[4][0]),
        P(lit.THEMES[4][1]),
        P("The four titles of the batch survey that follow the base paper are, as listed there: *AI-based multilingual story generation and speech synthesis system* (2026); *EmoSSLSphere: multilingual emotional speech synthesis with spherical vectors and discrete speech tokens* (2025); "
          "*Multilingual text-to-speech system for programming languages using RAG and neural speech synthesis* (2026); and *Vividtalker: improving zero-shot text-driven motion generation in the framework of speech-text-guided motion synthesis* (2025). "
          f"They are cited as {C('s2', 's3', 's4', 's5')}. From its title the first is the closest in goal to StoryVox; it could not be located, so no claim is made about its content, and the same holds for the third and fourth."),
        H2("2.8 Datasets and Algorithms Used in Related Work"),
        TAB("Data sets and algorithms in the surveyed work", ["Work", "Data set", "Algorithms"],
            [["Base paper", "CVSS-C, CoVoST-2", "mBART, sparse mixture-of-experts, self-paced learning, data-augmented self-training, HuBERT units, Grad-TTS, wav2vec 2.0 ASR"],
             ["OmniVoice", "581k hours, 646 languages; test on FLEURS-Multilingual-102", "Masked-diffusion language model over acoustic tokens, Qwen3-0.6B initialisation"],
             ["MultiGen", "Malay, Tamil and Mandarin corpora, including child speech", "LLM speech-token model with flow matching and HiFi-GAN vocoder"],
             ["EmoSSLSphere", "English and Japanese emotional speech", "Spherical emotion vectors with discrete self-supervised speech tokens"],
             ["Kahaani", "Not specified", "LLM story co-creation with TTS, music and video generation"],
             ["VITS / MMS", "LJ Speech, VCTK / religious-text recordings in 1,107 languages", "Conditional VAE with flow and adversarial training; one checkpoint per language"],
             ["Whisper", "680,000 hours of web audio", "Encoder-decoder Transformer ASR"],
             ["Qwen3 / TinyStories", "Large web corpus / synthetic children's stories", "Decoder-only Transformer; small models trained on narrow data"],
             ["This project", "FLEURS test split (10 sentences per language, CC BY 4.0); 17 story prompts; nothing trained", "Qwen3-0.6B, MMS-TTS (VITS), Whisper-small, MiniLM embeddings, WER, CER, ROUGE-L, RTF"]],
            widths=[1.4, 2.4, 2.7], align=["l", "l", "l"], size=10),
        P(f"FLEURS {C('fleurs')} is a read-speech benchmark in which the same sentences are read in many languages; StoryVox uses its text side as the reference for a round trip, which is a standard way to check intelligibility without recordings of people. "
          f"Similarity between a prompt and a story is scored with a multilingual sentence-embedding model {C('sbertm')} and ROUGE-L {C('rouge')}, and the speech is judged by Whisper {C('whisper')}."),
        H2("2.9 Strengths and Limitations of Existing Research"),
        P("The table below lists each surveyed work with its approach, data, reported result and limitation, using only what its paper or abstract states."),
        TAB("Comparison of the surveyed work", ["Work", "Approach", "Data", "Reported result", "Limitation"], lit.rows(),
            widths=[0.95, 1.65, 1.15, 1.35, 1.4], align=["l", "l", "l", "l", "l"], size=8.5),
        P("**Strengths.** End-to-end synthesis such as VITS and its per-language MMS checkpoints give good speech cheaply; ASR round trips give an objective, recording-free check; "
          "small language models trained or tuned on narrow story data write fluent short stories; and the base paper shows how a curriculum, sparse experts and synthetic data lift low-resource quality when training is possible."),
        P("**Limitations.** The strongest speech systems need GPUs, reference voices or private data; speech-translation papers report BLEU on benchmark sentences, not on narrative text; none of the surveyed systems measures a story generator and a speech model together; "
          "and a model's language list says little about whether it can write in each of those languages."),
        H2("2.10 Research Gap"),
        P(lit.GAP),
        P("Put as questions this project can answer with the data it has: for a story idea in each of 15 languages, does the pipeline produce a story in that language, is the narration intelligible when transcribed, and how long does each stage take on a laptop CPU? "
          "And which of the failures lie in the story model, which in the speech model and which in the application around them? Chapters 6 and 8 give the method and the answers."),
    ]
