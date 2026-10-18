"""Shared facts for the submission documents.

Identity strings come from the batch documents; every measured number is loaded from the JSON written by the
measurement scripts, so it matches docs/REPORT_FACTS.md (generated from the same files).
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT.parent
DIAG = ROOT / "docs" / "diagrams"
SHOTS = ROOT / "docs" / "screenshots"
CHARTS = ROOT / "docs" / "charts"
PAPERFIG = ROOT / "docs" / "paper"

PRODUCT = "AutoSecAI"
TITLE = "AutoSecAI: Autonomous Pull Request Analysis for Security, Vulnerability Detection, and Code Quality using Multi-Agent LLMs"
DEPT = "Department of Computer Science and Engineering"
BATCH_NAME = "Batch A11 (CSE, Section A)"
COLLEGE = "TKR College of Engineering & Technology (Autonomous)"
YEAR = "[ACADEMIC YEAR]"
GUIDE = "P. KISHORE"
GUIDE_DESIG = "[DESIGNATION]"

STUDENTS = [
    ("CHEPURI RISHIVARDHAN", "23K91A0553"),
    ("BODA SANDEEP", "23K91A0539"),
    ("DHARAVATH SEETHARAM", "23K91A0562"),
    ("NARISIMHA REDDY", "24K95A0501"),
]

BASE_PAPER = ('B. K. E. Abbasi and A. Shameli-Sendi, "Leveraging key source code metrics for predicting software vulnerabilities with machine '
              'learning," IEEE Access, vol. 14, pp. 52610-52625, 2026, doi: 10.1109/ACCESS.2026.3679930.')

# IEEE numbered references: base paper first, then the literature-survey sources, then the methods AutoSecAI builds on.
REFERENCES = [
    BASE_PAPER,
    'D. Zhang, S. Zhang, Z. Jin, J. Luo, S. Fu and E. Nallipogu, "Sphinx: Benchmarking and modeling for LLM-driven pull request review," arXiv:2601.04252, Jan. 2026.',
    '"Enhancing software security with CNN-LSTM hybrid model: Vulnerability detection," 2025 (listed in the batch literature survey; not independently retrieved).',
    '"Real-time AI code security auditing: Automated vulnerability detection and remediation through meta-experimental analysis," 2025 (listed in the batch literature survey; not independently retrieved).',
    '"Improving software security: A multi-modal framework for vulnerability detection using code simplification and meta-learning," 2025 (listed in the batch literature survey; not independently retrieved).',
    '"Advancing software security: DcodeBERT for automatic vulnerability detection and repair," 2024 (listed in the batch literature survey; not independently retrieved).',
    'H. Shahriar and M. Zulkernine, "Mitigating program security vulnerabilities: Approaches and challenges," ACM Comput. Surv., vol. 44, no. 3, pp. 1-46, Jun. 2012.',
    'Y. Shin and L. Williams, "Can traditional fault prediction models be used for vulnerability prediction?" Empirical Softw. Eng., vol. 18, no. 1, pp. 25-59, Feb. 2013.',
    'B. Chernis and R. Verma, "Machine learning methods for software vulnerability detection," in Proc. 4th ACM Int. Workshop Secur. Privacy Anal., Mar. 2018, pp. 31-39.',
    'F. Yamaguchi, M. Lottmann and K. Rieck, "Generalized vulnerability extrapolation using abstract syntax trees," in Proc. 28th Annu. Comput. Secur. Appl. Conf., Dec. 2012, pp. 359-368.',
    'R. Russell et al., "Automated vulnerability detection in source code using deep representation learning," in Proc. 17th IEEE Int. Conf. Mach. Learn. Appl. (ICMLA), Dec. 2018, pp. 757-762.',
    'Z. Li, D. Zou, S. Xu, X. Ou, H. Jin, S. Wang, Z. Deng and Y. Zhong, "VulDeePecker: A deep learning-based system for vulnerability detection," arXiv:1801.01681, 2018.',
    'L. Wartschinski, Y. Noller, T. Vogel, T. Kehrer and L. Grunske, "VUDENC: Vulnerability detection with deep learning on a natural codebase for Python," Inf. Softw. Technol., vol. 144, Art. no. 106809, Apr. 2022.',
    'H. Hanif, M. H. N. Md Nasir, M. F. Ab Razak, A. Firdaus and N. B. Anuar, "The rise of software vulnerability: Taxonomy of software vulnerabilities detection and machine learning approaches," J. Netw. Comput. Appl., vol. 179, Art. no. 103009, Apr. 2021.',
    'N. V. Chawla, K. W. Bowyer, L. O. Hall and W. P. Kegelmeyer, "SMOTE: Synthetic minority over-sampling technique," J. Artif. Intell. Res., vol. 16, pp. 321-357, 2002.',
    'I. Tomek, "Two modifications of CNN," IEEE Trans. Syst., Man, Cybern., vol. SMC-6, no. 11, pp. 769-772, Nov. 1976.',
    'G. E. A. P. A. Batista, R. C. Prati and M. C. Monard, "A study of the behavior of several methods for balancing machine learning training data," ACM SIGKDD Explor. Newsl., vol. 6, no. 1, pp. 20-29, 2004.',
    'L. Breiman, "Random forests," Mach. Learn., vol. 45, no. 1, pp. 5-32, 2001.',
    'T. Chen and C. Guestrin, "XGBoost: A scalable tree boosting system," in Proc. 22nd ACM SIGKDD Int. Conf. Knowl. Discovery Data Mining, 2016, pp. 785-794.',
    'F. Pedregosa et al., "Scikit-learn: Machine learning in Python," J. Mach. Learn. Res., vol. 12, pp. 2825-2830, 2011.',
    'T. J. McCabe, "A complexity measure," IEEE Trans. Softw. Eng., vol. SE-2, no. 4, pp. 308-320, Dec. 1976.',
    'G. Salton and C. Buckley, "Term-weighting approaches in automatic text retrieval," Inf. Process. Manage., vol. 24, no. 5, pp. 513-523, 1988.',
    'L. Page, S. Brin, R. Motwani and T. Winograd, "The PageRank citation ranking: Bringing order to the web," Stanford InfoLab, Stanford, CA, USA, Tech. Rep. 1999-66, 1999.',
    'OWASP Foundation, "OWASP Top 10:2021," 2021. [Online]. Available: https://owasp.org/Top10/',
    'MITRE Corporation, "Common Weakness Enumeration (CWE)." [Online]. Available: https://cwe.mitre.org/',
    'OASIS, "Static Analysis Results Interchange Format (SARIF) Version 2.1.0," OASIS Standard, Mar. 2020.',
    'M. Jones, J. Bradley and N. Sakimura, "JSON Web Token (JWT)," IETF RFC 7519, May 2015.',
    'N. Provos and D. Mazieres, "A future-adaptable password scheme," in Proc. USENIX Annu. Tech. Conf., 1999, pp. 81-91.',
]

# ------------------------------------------------------------------ measured facts (loaded, never typed by hand)
REP = json.loads((ROOT / "autosecai/artifacts/report.json").read_text())
MF = json.loads((ROOT / "docs/measured_facts.json").read_text())
API = json.loads((ROOT / "docs/measured_api_latency.json").read_text())

MODELS = REP["results"]                      # name -> accuracy / precision / recall / f1 / auc
BEST = REP["best"]                           # "XGBoost"
EV = MF["engine_vs_ml"]                      # rule_engine / ml_model / combined_or / combined_and
SEEDS = MF["seeds"]
LAT = MF["latency"]
RET = MF["retrieval"]
SIZE = MF["size"]
DEMO = LAT["demo"]


def f3(x: float) -> str:
    return f"{x:.3f}"


# Hard counts verified by running the checks on 18 Oct 2026 (see docs/REPORT_FACTS.md section 10).
TESTS_ENGINE, TESTS_API = 10, 7
SMOKE_CHECKS, UI_FLOWS = 16, 22
ROUTES_PUBLIC, ROUTES_PROTECTED = 7, 18
RULE_ENTRIES, RULES_SECURITY, RULES_QUALITY = 43, 30, 12
