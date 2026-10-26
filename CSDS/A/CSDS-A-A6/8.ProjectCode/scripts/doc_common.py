"""Shared facts for the ClauseGuard submission documents. Every figure comes from docs/REPORT_FACTS.md and experiments/**/metrics.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT.parent
DIAG = ROOT / "docs" / "diagrams"
SHOTS = ROOT / "docs" / "screenshots"
CHARTS = ROOT / "docs" / "charts"
SAMPLES = ROOT / "docs" / "sample_inputs"
EXPDIR = ROOT / "experiments"

PRODUCT = "ClauseGuard"
TITLE = "ClauseGuard: Legal Contract Complexity and Predatory Clause Detector"
SUBTITLE = "Legal Contract Complexity and Predatory Clause Detector"
DEPT = "Department of Computer Science and Engineering (Data Science)"
BATCH_NAME = "Batch A6 (CSE - Data Science, Section A)"
COLLEGE = "[COLLEGE NAME]"
YEAR = "[ACADEMIC YEAR]"
GUIDE = "[GUIDE NAME]"  # the batch file shows the placeholder "GUIDE NAME"
GUIDE_DESIG = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"

STUDENTS = [
    ("CH.PRANATHI", "23K91A6744"),
    ("G.PRANAVI", "23K91A6762"),
    ("G.CHARAN JOSEPH", "23K91A6753"),
    ("G.BHAGWATH", "23K91A6760"),
]


def metrics(name: str) -> dict:
    """experiments/<name>/metrics.json (names: eval, classification, rules, corpus, parity, api)."""
    return json.loads((EXPDIR / name / "metrics.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------------ references (IEEE style; the number is the position in this list)
# 1 is the base paper (batch file 3.BASE PAPER.docx; read in full); 2-4 are papers whose PDFs are in the batch folder and were read;
# 5-7 are items of the batch literature survey that could NOT be retrieved here (listed as given, never quoted for any result);
# the rest are standard, verifiable method, dataset, legal and software references.
REFERENCES = [
    'F. Almutairy, S. Almutairi, M. Abdullah, and S. Salman, "SmartLaw Advisor: AI-powered legal consultation and contract analysis for Saudi Arabia," IEEE Access, vol. 14, pp. 32638 ff., 2026, doi: 10.1109/ACCESS.2026.3665420.',
    'S. Liu, Z. Li, R. Ma, H. Zhao, and M. Du, "ContractEval: Benchmarking LLMs for clause-level legal risk identification in commercial contracts," arXiv:2508.03080, Aug. 2025.',
    'N. Lincoln, N. Whitehouse, J. Mar, and R. Perera, "A few good clauses: Comparing LLMs vs domain-trained small language models on structured contract extraction," arXiv:2605.05532, May 2026.',
    'D. Charan R, S. Siddarth, and M. Jeevitha, "Automated legal clause extraction and risk scoring using NLP and generative AI," Int. J. Res. Appl. Sci. Eng. Technol. (IJRASET), vol. 14, no. IV, Apr. 2026, doi: 10.22214/ijraset.2026.79369.',
    '"ClauseMiner: Prompt-engineered large language model for accurate, scalable legal clause extraction," Eng. Appl. Artif. Intell., 2026 (listed in the batch literature survey; not retrieved).',
    '"Autonomous contract analysis and clause risk detection using Legal-BERT," in Proc. 2025 Int. Conf. Sustainable Communication Networks and Application (ICSCN), 2025 (listed in the batch literature survey; not retrieved).',
    '"A study on large language model-based approach for construction contract risk detection," in Proc. 2024 Int. Conf. Big Data and Digital Management, 2024 (listed in the batch literature survey; not retrieved).',
    'D. Hendrycks, C. Burns, A. Chen, and S. Ball, "CUAD: An expert-annotated NLP dataset for legal contract review," in Proc. NeurIPS Datasets and Benchmarks Track, 2021, arXiv:2103.06268.',
    'I. Chalkidis, M. Fergadiotis, P. Malakasiotis, N. Aletras, and I. Androutsopoulos, "LEGAL-BERT: The muppets straight out of law school," in Findings of the Assoc. Computational Linguistics: EMNLP 2020, 2020, pp. 2898-2904.',
    'J. Devlin, M.-W. Chang, K. Lee, and K. Toutanova, "BERT: Pre-training of deep bidirectional transformers for language understanding," in Proc. NAACL-HLT, 2019, pp. 4171-4186.',
    'P. Lewis et al., "Retrieval-augmented generation for knowledge-intensive NLP tasks," in Advances in Neural Information Processing Systems (NeurIPS), vol. 33, 2020, pp. 9459-9474.',
    'N. Reimers and I. Gurevych, "Sentence-BERT: Sentence embeddings using Siamese BERT-networks," in Proc. EMNLP-IJCNLP, 2019, pp. 3982-3992.',
    'J. Lee et al., "Gemini Embedding: Generalizable embeddings from Gemini," arXiv:2503.07891, 2025.',
    'G. Salton and C. Buckley, "Term-weighting approaches in automatic text retrieval," Information Processing and Management, vol. 24, no. 5, pp. 513-523, 1988.',
    'R. Flesch, "A new readability yardstick," J. Applied Psychology, vol. 32, no. 3, pp. 221-233, 1948.',
    'A. A. Hagberg, D. A. Schult, and P. J. Swart, "Exploring network structure, dynamics, and function using NetworkX," in Proc. 7th Python in Science Conf. (SciPy), 2008, pp. 11-15.',
    'F. Pedregosa et al., "Scikit-learn: Machine learning in Python," J. Machine Learning Research, vol. 12, pp. 2825-2830, 2011.',
    'N. Provos and D. Mazieres, "A future-adaptable password scheme," in Proc. USENIX Annual Technical Conf. (FREENIX Track), 1999, pp. 81-91.',
    'M. Jones, J. Bradley, and N. Sakimura, "JSON Web Token (JWT)," RFC 7519, Internet Engineering Task Force, May 2015.',
    'Government of India, "The Indian Contract Act, 1872 (Act No. 9 of 1872)," sections 27, 73 and 74.',
    'Government of India, "The Arbitration and Conciliation Act, 1996 (Act No. 26 of 1996)."',
    'Government of India, "The Consumer Protection Act, 2019 (Act No. 35 of 2019)."',
    'Government of India, "The Copyright Act, 1957 (Act No. 14 of 1957)."',
]
BASE_PAPER = REFERENCES[0]
