"""IEEE-style reference list. Order = citation number in the report. Use N('key') to get the number for a key.

Every entry was checked against the paper itself (base paper PDF in Documentary/, companion papers in archived_base_papers/),
the arXiv abstract page, a publisher/proceedings page (PMLR, JMLR) or a search index record.
Batch-survey items:
  s3 (EmoSSLSphere) was located (arXiv 2508.11273, comment: 13th ISCA Speech Synthesis Workshop) and is the only one that may be quoted.
  s2, s4 and s5 could not be located on the web; they are listed as given in 5.LITERATURE SURVEY.docx and are never quoted for numbers.
  (s5, "Vividtalker", is a motion-synthesis title that does not concern speech or story generation.)

REF_INDEX documents the number of each key (a dict key -> citation number), so decks and the paper can cite by key.
"""

_R = [
    # --- base paper, then the batch literature survey, then companion papers
    ("base", "C. Tran and S. Sakti, \"SAM Translator: Self-paced learning and mixture-of-experts for cross-lingual text-to-speech translation,\" IEEE Access, vol. 14, pp. 2742-2752, 2026, doi: 10.1109/ACCESS.2025.3644647."),
    ("s2", "\"AI-based multilingual story generation and speech synthesis system,\" International Journal of Data Science and IoT Management System, 2026 (title as listed in the batch literature survey; not located online and not quoted)."),
    ("emo", "J. Park and K. Nakamura, \"EmoSSLSphere: Multilingual emotional speech synthesis with spherical vectors and discrete speech tokens,\" in Proc. 13th ISCA Speech Synthesis Workshop (SSW), 2025, arXiv:2508.11273."),
    ("s4", "\"Multilingual text-to-speech system for programming languages using RAG and neural speech synthesis,\" Progressive Computational Intelligence, Information Technology and Networking, 2026 (title as listed in the batch literature survey; not located online and not quoted)."),
    ("s5", "\"Vividtalker: Improving zero-shot text-driven motion generation in the framework of speech-text-guided motion synthesis,\" 2025 (title as listed in the batch literature survey; not located online, appears to concern motion synthesis, and is not quoted)."),
    ("omni", "H. Zhu, L. Ye, W. Kang, Z. Yao, L. Guo, F. Kuang, Z. Han, W. Zhuang, L. Lin and D. Povey, \"OmniVoice: Towards omnilingual zero-shot text-to-speech with diffusion language models,\" arXiv:2604.00688, Apr. 2026."),
    ("multigen", "X. Gao, H. Zhang and N. F. Chen, \"MultiGen: Child-friendly multilingual speech generator with LLMs,\" in Companion Proc. 27th Int. Conf. Multimodal Interaction (ICMI Companion '25), Canberra, Australia, Oct. 2025, doi: 10.1145/3747327.3764897."),
    ("kahaani", "S. Arif, M. S. Haroon, A. J. Khan, T. Arif, A. A. Raza and A. Athar, \"Kahaani: A multimodal co-creative storytelling system,\" arXiv:2409.11261, 2024 (rev. Feb. 2026)."),
    # --- models and components StoryVox uses
    ("vits", "J. Kim, J. Kong and J. Son, \"Conditional variational autoencoder with adversarial learning for end-to-end text-to-speech,\" in Proc. 38th Int. Conf. Machine Learning (ICML), PMLR vol. 139, Jul. 2021, pp. 5530-5540."),
    ("mms", "V. Pratap et al., \"Scaling speech technology to 1,000+ languages,\" Journal of Machine Learning Research, vol. 25, no. 97, pp. 1-52, 2024."),
    ("whisper", "A. Radford, J. W. Kim, T. Xu, G. Brockman, C. McLeavey and I. Sutskever, \"Robust speech recognition via large-scale weak supervision,\" in Proc. 40th Int. Conf. Machine Learning (ICML), PMLR vol. 202, 2023, pp. 28492-28518."),
    ("qwen3", "A. Yang et al., \"Qwen3 technical report,\" arXiv:2505.09388, May 2025."),
    ("sbert", "N. Reimers and I. Gurevych, \"Sentence-BERT: Sentence embeddings using Siamese BERT-networks,\" in Proc. Conf. Empirical Methods in Natural Language Processing and 9th Int. Joint Conf. Natural Language Processing (EMNLP-IJCNLP), 2019, pp. 3982-3992."),
    ("sbertm", "N. Reimers and I. Gurevych, \"Making monolingual sentence embeddings multilingual using knowledge distillation,\" in Proc. Conf. Empirical Methods in Natural Language Processing (EMNLP), 2020, pp. 4512-4525."),
    ("rouge", "C.-Y. Lin, \"ROUGE: A package for automatic evaluation of summaries,\" in Text Summarization Branches Out, Proc. ACL-04 Workshop, Barcelona, Spain, 2004, pp. 74-81."),
    ("fleurs", "A. Conneau, M. Ma, S. Khanuja, Y. Zhang, V. Axelrod, S. Dalmia, J. Riesa, C. Rivera and A. Bapna, \"FLEURS: Few-shot learning evaluation of universal representations of speech,\" in Proc. IEEE Spoken Language Technology Workshop (SLT), 2022, arXiv:2205.12446."),
    ("hf", "T. Wolf et al., \"Transformers: State-of-the-art natural language processing,\" in Proc. Conf. Empirical Methods in Natural Language Processing: System Demonstrations (EMNLP), 2020, pp. 38-45."),
    ("transformer", "A. Vaswani et al., \"Attention is all you need,\" in Proc. Advances in Neural Information Processing Systems (NIPS), 2017, pp. 5998-6008."),
    # --- story generation
    ("tinystories", "R. Eldan and Y. Li, \"TinyStories: How small can language models be and still speak coherent English?,\" arXiv:2305.07759, 2023."),
    ("fan", "A. Fan, M. Lewis and Y. Dauphin, \"Hierarchical neural story generation,\" in Proc. 56th Annual Meeting of the Association for Computational Linguistics (ACL), 2018, pp. 889-898."),
    ("holtzman", "A. Holtzman, J. Buys, L. Du, M. Forbes and Y. Choi, \"The curious case of neural text degeneration,\" in Proc. 8th Int. Conf. Learning Representations (ICLR), 2020."),
    # --- speech synthesis and cross-lingual / direct speech translation
    ("taco2", "J. Shen et al., \"Natural TTS synthesis by conditioning WaveNet on mel spectrogram predictions,\" in Proc. IEEE Int. Conf. Acoustics, Speech and Signal Processing (ICASSP), Apr. 2018, pp. 4779-4783."),
    ("fs2", "Y. Ren, C. Hu, X. Tan, T. Qin, S. Zhao, Z. Zhao and T.-Y. Liu, \"FastSpeech 2: Fast and high-quality end-to-end text to speech,\" in Proc. 9th Int. Conf. Learning Representations (ICLR), 2021."),
    ("hifigan", "J. Kong, J. Kim and J. Bae, \"HiFi-GAN: Generative adversarial networks for efficient and high fidelity speech synthesis,\" in Proc. Advances in Neural Information Processing Systems (NeurIPS), 2020, pp. 17022-17033."),
    ("gradtts", "V. Popov, I. Vovk, V. Gogoryan, T. Sadekova and M. Kudinov, \"Grad-TTS: A diffusion probabilistic model for text-to-speech,\" in Proc. 38th Int. Conf. Machine Learning (ICML), PMLR vol. 139, 2021, pp. 8599-8608."),
    ("xtts", "E. Casanova et al., \"XTTS: A massively multilingual zero-shot text-to-speech model,\" in Proc. Interspeech, 2024, arXiv:2406.04904."),
    ("fish", "S. Liao, Y. Wang, T. Li, Y. Cheng, R. Zhang, R. Zhou and Y. Xing, \"Fish-Speech: Leveraging large language models for advanced multilingual text-to-speech synthesis,\" arXiv:2411.01156, 2024."),
    ("ctrl", "T. Xie, Y. Rong, P. Zhang, W. Wang and L. Liu, \"Towards controllable speech synthesis in the era of large language models: A systematic survey,\" in Proc. Conf. Empirical Methods in Natural Language Processing (EMNLP), 2025, arXiv:2412.06602."),
    ("hubert", "W.-N. Hsu, B. Bolte, Y.-H. H. Tsai, K. Lakhotia, R. Salakhutdinov and A. Mohamed, \"HuBERT: Self-supervised speech representation learning by masked prediction of hidden units,\" IEEE/ACM Trans. Audio, Speech, and Language Processing, vol. 29, pp. 3451-3460, 2021."),
    ("mbart", "Y. Liu, J. Gu, N. Goyal, X. Li, S. Edunov, M. Ghazvininejad, M. Lewis and L. Zettlemoyer, \"Multilingual denoising pre-training for neural machine translation,\" Trans. Association for Computational Linguistics, vol. 8, pp. 726-742, 2020."),
    # --- techniques named by the base paper
    ("spl", "M. P. Kumar, B. Packer and D. Koller, \"Self-paced learning for latent variable models,\" in Proc. Advances in Neural Information Processing Systems (NIPS), vol. 23, 2010, pp. 1189-1197."),
    ("moe", "N. Shazeer, A. Mirhoseini, K. Maziarz, A. Davis, Q. Le, G. Hinton and J. Dean, \"Outrageously large neural networks: The sparsely-gated mixture-of-experts layer,\" in Proc. 5th Int. Conf. Learning Representations (ICLR), 2017."),
    ("switch", "W. Fedus, B. Zoph and N. Shazeer, \"Switch Transformers: Scaling to trillion parameter models with simple and efficient sparsity,\" Journal of Machine Learning Research, vol. 23, no. 120, pp. 1-39, 2022."),
]
REFS = [t for _, t in _R]
_IDX = {k: i + 1 for i, (k, _) in enumerate(_R)}
_IDX["s3"] = _IDX["emo"]    # batch-survey numbering: item 3 is EmoSSLSphere
REF_INDEX = _IDX            # documented alias: key -> citation number


def N(*keys):
    """Citation text like [3] or [3], [7] for one or more keys."""
    return ", ".join(f"[{_IDX[k]}]" for k in keys)
