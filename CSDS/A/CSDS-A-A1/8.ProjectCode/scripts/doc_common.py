"""Shared facts for the submission documents. Every figure here comes from docs/REPORT_FACTS.md."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT.parent
DIAG = ROOT / "docs" / "diagrams"
SHOTS = ROOT / "docs" / "screenshots"
RUN = "eval-20260922-0027"
EXP = ROOT / "experiments" / RUN / "plots"
CHARTS = ROOT / "docs" / "charts"

PRODUCT = "PolicyLens"
TITLE = "AI Health Insurance Assistance Using LLM + RAG"
DEPT = "Department of Computer Science and Engineering (Data Science)"
BATCH_NAME = "Batch A1 (CSE - Data Science, Section A)"
COLLEGE = "[COLLEGE NAME]"
YEAR = "[ACADEMIC YEAR]"
GUIDE = "[GUIDE NAME]"
GUIDE_DESIG = "[DESIGNATION]"

STUDENTS = [
    ("G.PRANATHI", "23K91A6764"),
    ("CH.AISHWARYA", "23K91A6747"),
    ("BHAVANSH MANE", "23K91A6728"),
    ("B.DEEKSHITH", "24K95A6701"),
]

BASE_PAPER = ('M. A. A. Albayati and O. Findik, "A hybrid transformer-based framework for multi-document summarization of Turkish legal '
              'documents," IEEE Access, vol. 13, pp. 37165-37181, 2025, doi: 10.1109/ACCESS.2025.3545750.')

# IEEE numbered references: base paper first, then the literature-survey sources, then the methods PolicyLens builds on.
REFERENCES = [
    BASE_PAPER,
    'D. Beauchemin, R. Khoury and Z. Gagnon, "Quebec automobile insurance question-answering with retrieval-augmented generation," in Proc. Natural Legal Language Processing Workshop (NLLP), Miami, FL, USA, 2024, pp. 48-60, doi: 10.18653/v1/2024.nllp-1.5.',
    '"A medical insurance question answering system based on multi-strategy retrieval-augmented generation," in Proc. 2026 5th Int. Symp. Computer Applications and Information Technology (ISCAIT), 2026 (listed in the batch literature survey; not independently retrieved).',
    '"Artificial intelligence chatbot in Iran Health Insurance Organization: A new era in service providing," Iranian Journal of Health Insurance, 2023 (listed in the batch literature survey; not independently retrieved).',
    'S. Knollmeyer, O. Caymazer and D. Grossmann, "Document GraphRAG: Knowledge graph enhanced retrieval augmented generation for document question answering within the manufacturing domain," Electronics, vol. 14, no. 11, Art. 2102, 2025, doi: 10.3390/electronics14112102.',
    'A. Maharjan and U. Yadav, "Chunking, retrieval, and re-ranking: An empirical evaluation of RAG architectures for policy document question answering," arXiv:2601.15457, Jan. 2026.',
    'P. Lewis et al., "Retrieval-augmented generation for knowledge-intensive NLP tasks," in Advances in Neural Information Processing Systems (NeurIPS), vol. 33, 2020, pp. 9459-9474.',
    'S. Robertson and H. Zaragoza, "The probabilistic relevance framework: BM25 and beyond," Foundations and Trends in Information Retrieval, vol. 3, no. 4, pp. 333-389, 2009.',
    'G. V. Cormack, C. L. A. Clarke and S. Buettcher, "Reciprocal rank fusion outperforms Condorcet and individual rank learning methods," in Proc. 32nd Int. ACM SIGIR Conf. Research and Development in Information Retrieval, 2009, pp. 758-759.',
    'N. Reimers and I. Gurevych, "Sentence-BERT: Sentence embeddings using Siamese BERT-networks," in Proc. EMNLP-IJCNLP, 2019, pp. 3982-3992.',
    'W. Wang, F. Wei, L. Dong, H. Bao, N. Yang and M. Zhou, "MiniLM: Deep self-attention distillation for task-agnostic compression of pre-trained transformers," in Advances in Neural Information Processing Systems (NeurIPS), vol. 33, 2020, pp. 5776-5788.',
    'R. Nogueira and K. Cho, "Passage re-ranking with BERT," arXiv:1901.04085, 2019.',
    'P. He, J. Gao and W. Chen, "DeBERTaV3: Improving DeBERTa using ELECTRA-style pre-training with gradient-disentangled embedding sharing," arXiv:2111.09543, 2021.',
    'A. Williams, N. Nangia and S. Bowman, "A broad-coverage challenge corpus for sentence understanding through inference," in Proc. NAACL-HLT, 2018, pp. 1112-1122.',
    'T. Bajaj et al., "MS MARCO: A human generated machine reading comprehension dataset," arXiv:1611.09268, 2016.',
    'Z. Ji et al., "Survey of hallucination in natural language generation," ACM Computing Surveys, vol. 55, no. 12, Art. 248, 2023.',
    'Gemini Team, Google, "Gemini: A family of highly capable multimodal models," arXiv:2312.11805, 2023.',
    'V. Karpukhin et al., "Dense passage retrieval for open-domain question answering," in Proc. EMNLP, 2020, pp. 6769-6781.',
    'C.-Y. Lin, "ROUGE: A package for automatic evaluation of summaries," in Text Summarization Branches Out, ACL Workshop, Barcelona, Spain, 2004, pp. 74-81.',
]

# ------------------------------------------------------------------ measured facts (docs/REPORT_FACTS.md, run eval-20260922-0027)
RETR = [  # method, hit@1, hit@3, hit@5, mrr@10, recall@5, p50 ms, p95 ms
    ("BM25 (keywords)", 0.647, 0.922, 1.000, 0.779, 1.000, 1.1, 32.2),
    ("Dense (MiniLM + Chroma)", 0.490, 0.765, 0.804, 0.632, 0.794, 10.7, 15.7),
    ("Hybrid (RRF)", 0.686, 0.882, 0.961, 0.795, 0.951, 11.0, 16.6),
    ("Hybrid + re-rank (used)", 0.804, 0.980, 1.000, 0.897, 0.990, 878.9, 995.5),
]
CATS = [("Waiting periods", 14), ("Benefits", 15), ("Claim process", 8), ("Exclusions", 5), ("Policy terms", 4), ("Room rent", 3), ("Sub-limits", 2)]
POLICIES = [  # name, insurer, UIN, pages, words, clauses, layout, parse s, card verified, risks, qa, card values correct/checked
    ("Family Health Optima", "Star Health and Allied Insurance", "SHAHLIP26046V092526", 44, 17135, 219, "two-column A4", 3.2, 0.909, 9, 14, "14/14"),
    ("my: Optima Secure", "HDFC ERGO General Insurance", "HDFHLIP25041V062425", 53, 20958, 207, "single column, Def. N", 4.2, 1.000, 4, 13, "13/14"),
    ("ReAssure 2.0", "Niva Bupa Health Insurance", "NBHHLIP23169V012223", 24, 12852, 166, "single column, multi-level", 3.2, 1.000, 6, 12, "11/11"),
    ("Care Supreme", "Care Health Insurance", "CHIHLIP23128V012223", 45, 22056, 209, "small-page two-column", 4.1, 0.967, 4, 12, "13/13"),
]
RUNS = [  # run, change, hit@5, answer acc, citation acc, false abstentions, claim verdicts
    ("eval-20260921-2353", "Baseline", "98.0%", "88.2%", "92.2%", "5", "14/14"),
    ("eval-20260922-0008", "Abstain only if both scores are low; rule and governed tables sent together", "98.0%", "98.0%", "96.1%", "1", "14/14"),
    ("eval-20260922-0027", "Exclusion-code list items become separate clauses; prompt says an exclusion is an answer; non-network co-pay not applied to cashless", "100%", "100%", "100%", "0", "14/14"),
]
TESTS = [("test_auth.py", 6), ("test_faithfulness.py", 3), ("test_parser.py", 3), ("test_policy_flow.py", 7), ("test_units.py", 6)]
CONFUSION = [[5, 0, 0, 0], [0, 1, 0, 0], [0, 0, 7, 0], [0, 0, 0, 1]]
CLAIM_LABELS = ["covered", "partly covered", "not covered", "needs info"]
ENDPOINTS = 42
