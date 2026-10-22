"""
Reference list for the PeerScope (CSE-C-C8) documents, IEEE style, numbered by list order (REFS[0] is [1]).

Every entry was checked against the base-paper PDF, the archived PDFs, the Crossref API, the arXiv API or the
OpenAlex API during the C8 documentation run; REF_NOTES records how, and which items are weak.
Italics use *...* markup (rendered by kit.add_runs). Cite from other modules with CITE['key'].
"""

REFS = [
    # ---- 1-5: the batch literature survey (5.LITERATURE SURVEY.docx), base paper first
    "F. Bagheri, D. Buscaldi and D. Reforgiato Recupero, \"LLM-assisted reviewer assignment via auditable expertise matching,\" "
    "*IEEE Access*, vol. 14, pp. 127834-127863, 2026, doi: 10.1109/ACCESS.2026.3724622.",
    "F. Torrielli, S. Locci, A. Rapp and L. Di Caro, \"How to get your paper accepted by an AI reviewer: indirect prompt injection in peer review,\" "
    "Research Square preprint, Jan. 2026, doi: 10.21203/rs.3.rs-8432945/v1. (Published as \"Exploiting large language models in peer review: indirect prompt "
    "injection attacks and integrity probes,\" *Scientometrics*, vol. 131, no. 7, pp. 4889-4951, 2026, doi: 10.1007/s11192-026-05695-x.)",
    "Y. Sermet and I. Demir, \"Unveiling the reviewer mindset: evidence-based insights into scholarly peer review,\" ScienceOpen, May 2025, "
    "doi: 10.14293/ease.2025.037.",
    "Anonymous reviewer, \"Review of: Performance evaluation of adaptive introgression classification methods. Round#1/Reviewer#2,\" "
    "*Peer Community in Evolutionary Biology*, Jun. 2024, doi: 10.24072/pci.evolbiol.100835.rev12.",
    "Anonymous reviewer, \"Review of: Performance evaluation of adaptive introgression classification methods. Round#2/Reviewer#2,\" "
    "*Peer Community in Evolutionary Biology*, Dec. 2024, doi: 10.24072/pci.evolbiol.100835.rev22.",
    # ---- 6-7: supporting papers archived with the batch
    "S. Wu, O. Jiang, Y. Zhao, T. Hu, Y. Ma, K. Zhang, M. Patwardhan and A. Cohan, \"Can AI be a good peer reviewer? A survey of peer review process, "
    "evaluation, and the future,\" arXiv:2604.27924, Apr. 2026.",
    "S. Li, L. Fan, Y. Lin, Z. Li, X. Wei, S. Ni, H. Alinejad-Rokny and M. Yang, \"Automatic paper reviewing with heterogeneous graph reasoning over "
    "LLM-simulated reviewer-author debates,\" arXiv:2511.08317, Nov. 2025 (AAAI 2026 copyright notice on the PDF).",
    # ---- 8-16: reviewer assignment
    "J. Jovanovic and E. Bagheri, \"Reviewer assignment problem: a scoping review,\" arXiv:2305.07887, May 2023.",
    "X. Zhao and Y. Zhang, \"Reviewer assignment algorithms for peer review automation: a survey,\" *Inf. Process. Manage.*, vol. 59, no. 5, "
    "Art. no. 103028, Sep. 2022, doi: 10.1016/j.ipm.2022.103028.",
    "L. Charlin, R. S. Zemel and C. Boutilier, \"A framework for optimizing paper matching,\" arXiv:1202.3706, Feb. 2012.",
    "D. Mimno and A. McCallum, \"Expertise modeling for matching papers with reviewers,\" in *Proc. 13th ACM SIGKDD Int. Conf. Knowl. Discovery "
    "Data Mining*, 2007, pp. 500-509, doi: 10.1145/1281192.1281247.",
    "I. Stelmakh, N. B. Shah and A. Singh, \"PeerReview4All: fair and accurate reviewer assignment in peer review,\" arXiv:1806.06237, 2018 "
    "(*Proc. Algorithmic Learn. Theory*, 2019, pp. 828-856, as cited in [1]).",
    "A. Beygelzimer, Y. N. Dauphin, P. Liang and J. W. Vaughan, \"Has the machine learning review process become more arbitrary as the field has grown? "
    "The NeurIPS 2021 consistency experiment,\" arXiv:2306.03262, Jun. 2023.",
    "K. Bouanane, A. N. Medakene, A. Benbelghit and S. B. Belhaouari, \"FairColor: an efficient algorithm for the balanced and fair reviewer assignment "
    "problem,\" *Inf. Process. Manage.*, vol. 61, no. 6, Art. no. 103865, Nov. 2024, doi: 10.1016/j.ipm.2024.103865.",
    "S. Jecmen, H. Zhang, R. Liu, N. B. Shah, V. Conitzer and F. Fang, \"Mitigating manipulation in peer review via randomized reviewer assignments,\" "
    "arXiv:2006.16437, Jun. 2020.",
    "Y. Zhang, Y. Shen, S. Kang, X. Chen, B. Jin and J. Han, \"Chain-of-factors paper-reviewer matching,\" in *Proc. ACM Web Conf. 2025*, Apr. 2025, "
    "pp. 1901-1910, doi: 10.1145/3696410.3714708.",
    # ---- 17-21: text representation and similarity
    "G. Salton and C. Buckley, \"Term-weighting approaches in automatic text retrieval,\" *Inf. Process. Manage.*, vol. 24, no. 5, pp. 513-523, 1988, "
    "doi: 10.1016/0306-4573(88)90021-0.",
    "K. Sparck Jones, \"A statistical interpretation of term specificity and its application in retrieval,\" *J. Documentation*, vol. 28, no. 1, "
    "pp. 11-21, 1972, doi: 10.1108/eb026526.",
    "N. Reimers and I. Gurevych, \"Sentence-BERT: sentence embeddings using Siamese BERT-networks,\" in *Proc. EMNLP-IJCNLP*, 2019, pp. 3980-3990, "
    "doi: 10.18653/v1/D19-1410.",
    "W. Wang, F. Wei, L. Dong, H. Bao, N. Yang and M. Zhou, \"MiniLM: deep self-attention distillation for task-agnostic compression of pre-trained "
    "transformers,\" arXiv:2002.10957, Feb. 2020.",
    "A. Cohan, S. Feldman, I. Beltagy, D. Downey and D. S. Weld, \"SPECTER: document-level representation learning using citation-informed "
    "transformers,\" in *Proc. 58th Annu. Meeting Assoc. Comput. Linguistics*, 2020, pp. 2270-2282, doi: 10.18653/v1/2020.acl-main.207.",
    # ---- 22-26: automated review and decision prediction
    "D. Kang, W. Ammar, B. Dalvi, M. van Zuylen, S. Kohlmeier, E. Hovy and R. Schwartz, \"A dataset of peer reviews (PeerRead): collection, insights and "
    "NLP applications,\" in *Proc. NAACL-HLT*, 2018, pp. 1647-1661, doi: 10.18653/v1/N18-1149.",
    "W. Yuan, P. Liu and G. Neubig, \"Can we automate scientific reviewing?,\" *J. Artif. Intell. Res.*, vol. 75, pp. 171-212, 2022, "
    "doi: 10.1613/jair.1.12862.",
    "W. Liang et al., \"Can large language models provide useful feedback on research papers? A large-scale empirical analysis,\" *NEJM AI*, vol. 1, no. 8, "
    "Jul. 2024, doi: 10.1056/AIoa2400196.",
    "M. Zhu, Y. Weng, L. Yang and Y. Zhang, \"DeepReview: improving LLM-based paper review with human-like deep thinking process,\" in *Proc. 63rd Annu. "
    "Meeting Assoc. Comput. Linguistics*, 2025, pp. 29330-29355, doi: 10.18653/v1/2025.acl-long.1420.",
    "Z. Zhuang, J. Chen, H. Xu, Y. Jiang and J. Lin, \"Large language models for automated scholarly paper review: a survey,\" *Inf. Fusion*, vol. 124, "
    "Art. no. 103332, Dec. 2025, doi: 10.1016/j.inffus.2025.103332.",
    # ---- 27: integrity and robustness
    "J. Keuper, \"Prompt injection attacks on LLM generated reviews of scientific publications,\" arXiv:2509.10248, Sep. 2025.",
    # ---- 28-32: models, tools and data sources used by PeerScope
    "A. Vaswani et al., \"Attention is all you need,\" in *Proc. Adv. Neural Inf. Process. Syst.*, vol. 30, 2017 (arXiv:1706.03762).",
    "A. Yang et al. (Qwen Team), \"Qwen2.5 technical report,\" arXiv:2412.15115, Dec. 2024.",
    "T. Wolf et al., \"Transformers: state-of-the-art natural language processing,\" in *Proc. EMNLP: System Demonstrations*, 2020, pp. 38-45, "
    "doi: 10.18653/v1/2020.emnlp-demos.6.",
    "F. Pedregosa et al., \"Scikit-learn: machine learning in Python,\" *J. Mach. Learn. Res.*, 2011 (arXiv:1201.0490).",
    "J. Priem, H. Piwowar and R. Orr, \"OpenAlex: a fully-open index of scholarly works, authors, venues, institutions, and concepts,\" arXiv:2205.01833, 2022.",
]

# short key -> reference number (1-based, as printed)
CITE = {
    "base": 1, "inject_aro": 2, "reviewer_mindset": 3, "pci_r1": 4, "pci_r2": 5,
    "survey_wu": 6, "reviewgraph": 7,
    "rap_scoping": 8, "rap_survey": 9, "tpms": 10, "mimno": 11, "peerreview4all": 12, "neurips_consistency": 13,
    "faircolor": 14, "jecmen": 15, "chain_of_factors": 16,
    "tfidf": 17, "idf": 18, "sbert": 19, "minilm": 20, "specter": 21,
    "peerread": 22, "reviewadvisor": 23, "liang_llm_feedback": 24, "deepreview": 25, "llm_review_survey": 26,
    "keuper": 27,
    "transformer": 28, "qwen25": 29, "hf_transformers": 30, "sklearn": 31, "openalex": 32,
}

assert len(REFS) == 32 and set(CITE.values()) == set(range(1, 33))

REF_NOTES = {
    1: "verified from PDF (Documentary/BASEPAPER_LLM_Assisted_...pdf: title, authors, vol. 14, pp. 127834-127863 by running page numbers) and Crossref",
    2: "verified via Crossref and OpenAlex: Research Square preprint posted 2026-01-05 (the title in the batch survey); later journal version in Scientometrics 131(7):4889-4951 (Crossref)",
    3: "verified via Crossref (ScienceOpen proceedings-article, 2025-05-14); venue name not stated in the record beyond the 'ease' DOI prefix, so none is claimed",
    4: "record verified via Crossref (2024-06-26); it is an anonymous review report, not research literature; its text could not be read (site blocked automated access)",
    5: "record verified via Crossref (2024-12-01); anonymous review report, not research literature; text not read",
    6: "verified from PDF and arXiv API (8 authors, 2026-04-30)",
    7: "verified from PDF and arXiv API (8 authors, 2025-11-11); 'AAAI 2026' taken from the copyright line in the PDF - proceedings pages not verified",
    8: "verified via arXiv API", 9: "verified via Crossref and OpenAlex abstract",
    10: "verified via arXiv API; the base paper cites the 2013 Toronto Paper Matching System technical report, which could not be located, so this verifiable paper by the same group is cited instead",
    11: "verified via Crossref and OpenAlex abstract", 12: "verified via arXiv API; venue/pages as printed in the base paper's reference [4]",
    13: "verified via arXiv API", 14: "verified via Crossref (abstract not available; content known only from the base paper's description)",
    15: "verified via arXiv API (venue not verified, so only arXiv is cited)",
    16: "verified via Crossref (WWW 2025, pp. 1901-1910) and OpenAlex abstract; full author list from Crossref",
    17: "verified via Crossref", 18: "verified via Crossref", 19: "verified via Crossref and arXiv", 20: "verified via arXiv API (venue not verified)",
    21: "verified via Crossref and arXiv", 22: "verified via Crossref and arXiv", 23: "verified via Crossref (JAIR 75:171-212) and arXiv",
    24: "verified via Crossref and arXiv API (abstract numbers quoted in LITERATURE_FACTS.md)", 25: "verified via Crossref (ACL 2025 long papers) and arXiv",
    26: "verified via Crossref (abstract not available)", 27: "verified via arXiv API; also published in Pattern Recognition (LNCS), Aug. 2026, doi 10.1007/978-3-032-31335-5_9, pp. 122-134 (Crossref)",
    28: "verified via arXiv API; venue as printed in the base paper's reference [10]", 29: "verified via arXiv API", 30: "verified via Crossref and arXiv",
    31: "verified via arXiv API (journal_ref gives only 'JMLR (2011)', so volume and pages are not stated)", 32: "verified via arXiv API",
}
