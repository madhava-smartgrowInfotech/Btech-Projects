"""Literature rows shared by the report (Chapter 2), the decks and the paper:
(key, work, approach, data, reported result, limitation). Only facts checked against the paper itself, its arXiv abstract page or a proceedings page.
The batch-survey items that could not be located (refs s2, s4, s5) are deliberately absent from ROWS: nothing is claimed about them."""

from .refs import N as C

ROWS = [
    ("base", "Tran and Sakti, SAM Translator (base paper)",
     "Text-to-speech translation: mBART text-to-unit model with self-paced learning (SPL), sparse mixture-of-experts feed-forward layers (8 experts, top-2) and data-augmented self-training (DAST); HuBERT units (K=200) decoded by Grad-TTS",
     "CVSS-C (21 source languages to English speech) and CoVoST-2 (about 209K / 14K / 14K train / dev / test)",
     "BLEU of the ASR transcript: relative +2-3% (high-resource) and +7-10% (low-resource) over mBART on CVSS-C; DAST about +21.6% (Welsh) and +25.83% (Mongolian); +4-6% on CoVoST-2",
     "Target side is English only; cascaded model still better for some languages; low BLEU for Welsh and Tamil; repetition errors; 611M vs 1.7B parameters, A100 80 GB, 1.5-2 days of training"),
    ("omni", "Zhu et al., OmniVoice",
     "Zero-shot TTS: non-autoregressive masked-diffusion language model over 8-codebook acoustic tokens, bidirectional Transformer initialised from Qwen3-0.6B",
     "581k hours, 646 languages (open data); test on FLEURS-Multilingual-102",
     "Average CER 4.00% against 5.11% for the ground-truth recordings; 82 of 102 languages at CER <= 5%; RTF 0.0319 (16 steps, batch 1, H20 GPU)",
     "Trained on 8 H800 GPUs for 9.66 days; speech generation only, no story text; the authors flag misuse risk of voice cloning"),
    ("multigen", "Gao, Zhang and Chen, MultiGen",
     "Child-friendly multilingual speech generator: LLM speech-token model fine-tuned from CosyVoice-300M with child speaker x-vectors, flow matching and HiFi-GAN",
     "Private corpora: Malay children 30,000 utterances (104 speakers), Malay adults 23,897, Tamil adult 33,830, Singapore Mandarin 1,400",
     "CER Tamil 9.6 -> 2.1, Malay 3.4 -> 2.3, Mandarin 10.7 -> 4.0 (%); Tamil MOS quality 4.05 vs 2.51 (VITS); 30 native listeners",
     "Three languages; relies on collected child-speech data that is not public; no story generation"),
    ("emo", "Park and Nakamura, EmoSSLSphere",
     "Multilingual emotional TTS combining spherical emotion vectors with discrete tokens from self-supervised speech models",
     "English and Japanese corpora",
     "Reports gains in intelligibility, spectral quality and prosody and better naturalness and expressiveness in listening tests",
     "Two languages; emotion control rather than story content"),
    ("kahaani", "Arif et al., Kahaani",
     "Co-creative storytelling for children: LLM story co-creation with text-to-speech, text-to-music and text-to-video",
     "Not specified on the arXiv page",
     "Interactive multimodal system; described as an educational storytelling aid",
     "English-language learning focus; the arXiv page does not report multilingual narration"),
    ("vits", "Kim, Kong and Son, VITS",
     "End-to-end TTS: conditional VAE with normalising flow, adversarial training and a stochastic duration predictor, so text maps straight to a waveform",
     "LJ Speech and VCTK",
     "Reported MOS close to ground-truth recordings on LJ Speech; one-stage training and parallel synthesis",
     "Single language per checkpoint; quality depends on the training corpus"),
    ("mms", "Pratap et al., MMS",
     "Massively multilingual speech: wav2vec 2.0 pre-training, ASR and VITS-based TTS checkpoints",
     "Religious-text recordings and other public corpora; 1,107 languages for TTS",
     "One TTS model per language; the ASR model more than halves Whisper's word error rate on 54 FLEURS languages",
     "Per-language checkpoints are single-speaker and narrow in domain; some scripts need romanisation"),
    ("whisper", "Radford et al., Whisper",
     "Encoder-decoder Transformer ASR trained with weak supervision on web audio",
     "680,000 hours of multilingual, multitask data",
     "Robust zero-shot transcription across many benchmarks and languages",
     "Error rates differ widely between languages; can hallucinate on poor audio"),
    ("qwen3", "Yang et al., Qwen3",
     "Open decoder-only language-model family with dense and mixture-of-experts variants and a thinking / non-thinking switch",
     "Pre-training coverage expanded from 29 to 119 languages and dialects; sizes 0.6B to 235B parameters",
     "Reported competitive results against open and proprietary models (as stated by the authors)",
     "The smallest model (0.6B) is far weaker than the flagship; needs the chat template to follow instructions"),
    ("tinystories", "Eldan and Li, TinyStories",
     "Shows that very small language models trained on synthetic children's stories produce fluent, consistent short stories",
     "Stories synthesised with a larger model from a child-level vocabulary",
     "Small models reach coherent English storytelling when the data are narrow and simple",
     "English only; the stories come from a restricted vocabulary and domain"),
    ("fan", "Fan, Lewis and Dauphin",
     "Hierarchical story generation: first a prompt-to-premise step, then a convolutional seq2seq model writes the story with a fusion mechanism",
     "WritingPrompts, about 300K human-written stories paired with prompts",
     "Better prompt relevance and human preference than non-hierarchical baselines",
     "English only; pre-Transformer scale; long-range plot consistency still weak"),
    ("holtzman", "Holtzman et al.",
     "Nucleus (top-p) sampling for open-ended text generation, avoiding the repetition of likelihood-maximising decoding",
     "Open-ended generation from GPT-2 class models",
     "Text closer to human text statistics than greedy or beam search",
     "A decoding rule only; it cannot fix a model that ignores the instruction"),
    ("xtts", "Casanova et al., XTTS",
     "Zero-shot multilingual TTS that builds on the Tortoise model with modifications for multilingual training and voice cloning",
     "Trained in 16 languages",
     "Reported state-of-the-art results in most of its 16 languages",
     "Built for voice cloning from a reference clip; 16 languages only; no story text"),
    ("fish", "Liao et al., Fish-Speech",
     "LLM-based multilingual TTS: serial fast-slow Dual-AR architecture over grouped finite scalar vector quantisation; the LLM replaces grapheme-to-phoneme conversion",
     "Large multilingual speech corpus (see paper)",
     "Reported to outperform baseline models on complex linguistic scenarios and voice cloning",
     "Technical report; large LLM-based model; no evaluation on story-length input"),
    ("fleurs", "Conneau et al., FLEURS",
     "n-way parallel read-speech benchmark: the same sentences read in many languages",
     "102 languages",
     "Standard test set for multilingual ASR and speech evaluation",
     "Read speech of Wikipedia-style sentences, not narrative text"),
]

GAP = ("The surveyed work advances cross-lingual text-to-speech, massively multilingual synthesis and speech evaluation, and a few systems combine an LLM with speech for children, "
       "but none of them joins controllable story generation (language, style and length chosen by the user) to multilingual narration in one locally runnable application "
       "and then measures the whole chain honestly, with the story model, the speech model and a speech recogniser used as the judge. "
       "Papers on speech translation report BLEU on benchmark corpora, papers on TTS report MOS or CER on read sentences, and neither tells a user whether a story told in Hindi or Korean "
       "actually comes out in that language, is intelligible when spoken, and finishes in a practical time on a laptop CPU.")

THEMES = [
    ("Neural story generation",
     f"Story generation moved from convolutional sequence models conditioned on a short premise {C('fan')} to Transformer language models {C('transformer')}. "
     f"Fluent text is not enough: likelihood-maximising decoding repeats itself, and nucleus sampling {C('holtzman')} became the standard remedy. "
     f"TinyStories {C('tinystories')} showed that even very small models write coherent short stories when the training data are simple and narrow, "
     f"which is why a 0.6-billion-parameter instruction model such as Qwen3-0.6B {C('qwen3')} is a plausible choice for a laptop. "
     f"Kahaani {C('kahaani')} pairs LLM story co-creation with speech, music and video for children, but with an English-skills goal. "
     "These works either leave out speech or stay in English; none measures what happens when a small model is asked for a story in several languages."),
    ("Multilingual and low-resource text-to-speech",
     f"End-to-end synthesis replaced concatenative and statistical parametric systems with Tacotron 2 {C('taco2')}, FastSpeech 2 {C('fs2')} and VITS {C('vits')}, using neural vocoders such as HiFi-GAN {C('hifigan')}. "
     f"The Massively Multilingual Speech project {C('mms')} released one VITS-style checkpoint for each of 1,107 languages, which is the cheapest route to many languages and the one StoryVox uses. "
     f"Newer systems scale or clone voices: XTTS {C('xtts')}, Fish-Speech {C('fish')} and OmniVoice {C('omni')}, which covers 646 languages with a diffusion language model and reports an average CER of 4.00% on FLEURS-Multilingual-102. "
     f"MultiGen {C('multigen')} shows that a fine-tuned LLM-based generator beats a VITS baseline in Malay, Tamil and Singapore Mandarin, with Tamil CER falling from 9.6% to 2.1%, "
     f"and EmoSSLSphere {C('emo')} adds emotion control for English and Japanese. A survey of controllable synthesis {C('ctrl')} places these systems in context. "
     "Most of these models need a GPU and a reference voice, and none produces the story text."),
    ("Cross-lingual and direct speech translation (the base-paper theme)",
     f"Text-to-speech translation converts text in one language into speech in another. The usual cascade translates and then synthesises; the base paper {C('base')} follows direct text-to-unit models: "
     f"HuBERT units {C('hubert')} are predicted from source text by an mBART model {C('mbart')} and turned into speech by a Grad-TTS decoder {C('gradtts')}. "
     f"SAM Translator adds self-paced learning {C('spl')}, sparse mixture-of-experts layers {C('moe')}, {C('switch')} and self-training on synthetic pairs. "
     "It is evaluated by transcribing the output and scoring BLEU on CVSS-C and CoVoST-2. This addresses a different problem from StoryVox, which generates the story itself in the target language "
     "and does not translate; the base paper is used as the reference point for multilingual speech output, for evaluating speech by transcription, and for the low-resource-language motivation."),
    ("Evaluating generated speech: WER, CER and real-time factor",
     f"Objective speech evaluation commonly synthesises text, transcribes it with an ASR model and compares the transcript with the input; the base paper does this with a wav2vec 2.0 recogniser, "
     f"MultiGen with Whisper for Mandarin, and OmniVoice with ASR-based CER on the FLEURS benchmark {C('fleurs')}. Whisper {C('whisper')} is trained on 680,000 hours and is the usual multilingual judge. "
     f"Character error rate is preferred where words are not space-separated, and real-time factor (synthesis time divided by audio duration) reports speed; OmniVoice reports RTF 0.0319 on an H20 GPU. "
     f"Topic fit of a story can be scored with multilingual sentence embeddings {C('sbert')}, {C('sbertm')} and ROUGE-L {C('rouge')}. "
     "The weakness of the method is that the judge has its own errors, so a round trip measures the pair of models, not the speech model alone."),
    ("Low-resource languages",
     f"Low-resource languages are the central concern of the base paper {C('base')}, which uses data-augmented self-training for Welsh and Mongolian and still reports low scores for Welsh and Tamil, "
     f"of MultiGen {C('multigen')}, which fine-tunes with collected speech, and of OmniVoice {C('omni')}, which trains on 581k hours. "
     f"Checkpoint coverage is the practical problem for an application: the number of languages a toolkit lists is not the number it can speak, because a language needs both a text model that writes it and a speech model that reads it {C('mms')}, {C('hf')}."),
]

BASE_ANALYSIS = {
    "summary": "SAM Translator replaces the shared feed-forward layers of an mBART text-to-unit model with a sparse mixture of eight experts (top-2 routing, load-balancing loss alpha = 0.001), "
               "trains with a self-paced curriculum (threshold tau starts at 2 and grows by 0.25 every 2,000 steps until all samples are used), and adds filtered synthetic pairs for six low-BLEU languages (5K, 10K and 15K pairs). "
               "Speech units come from HuBERT-Base with K-means (K = 200, 50 units per second), and Grad-TTS turns units into audio. Evaluation transcribes the output with a wav2vec 2.0 recogniser and reports BLEU.",
    "strengths": ["Benchmarks on two public corpora, CVSS-C and CoVoST-2, so the numbers can be reproduced by others.",
                  "Each of the three ideas is ablated: SPL improved 18 of 21 languages, MoE gave consistent gains over the baseline, and 10K synthetic pairs gave the largest low-resource gains.",
                  "A subjective study (10 listeners, 15 samples per system) rates naturalness 4.12 +/- 0.14 for speech units against 4.15 +/- 0.14 for text-based synthesis.",
                  "Honest limitations: low BLEU for Welsh and Tamil, repetition and semantic errors, and a worse result than the cascade for some languages such as Russian."],
    "limitations": ["Target language is English in both datasets, so it does not show many-target narration.",
                    "It translates; it does not write stories, and no content control (style, length, theme) exists.",
                    "Cost: 611M-parameter baseline and 1.7B-parameter MoE model, one A100 80 GB GPU, about 1.5-2 days of training.",
                    "More synthetic data (15K) lowered scores for Japanese, Mongolian and Welsh."],
    "adopts": ["Multilingual speech output as the final product, evaluated by transcribing the audio with an ASR model.",
               "The use of an ASR round trip as an objective, text-based quality check.",
               "The motivation for education and for under-served languages."],
    "not_adopts": ["Self-paced learning, mixture-of-experts layers, data-augmented self-training and discrete speech units are not implemented: StoryVox trains nothing.",
                   "No translation step: the story is generated directly in the chosen language by the language model.",
                   "StoryVox cascades two off-the-shelf pretrained models (an instruction-tuned LLM, then a per-language VITS checkpoint), run on a CPU."],
    "comparability": "The base paper reports BLEU on CVSS-C / CoVoST-2 for translation into English; StoryVox reports TTS-to-ASR round-trip WER/CER, real-time factor and story-level checks on its own small test sets. "
                     "The numbers measure different things on different data and must not be compared.",
}


def rows():
    return [[w, a, d, r, l] for _, w, a, d, r, l in ROWS]
