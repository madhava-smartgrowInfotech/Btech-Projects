"""Shared facts for the ForgetSafe submission documents. Every figure comes from docs/REPORT_FACTS.md and experiments/*/metrics.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT.parent
DIAG = ROOT / "docs" / "diagrams"
SHOTS = ROOT / "docs" / "screenshots"
CHARTS = ROOT / "docs" / "charts"
EXPDIR = ROOT / "experiments"

PRODUCT = "ForgetSafe"
TITLE = "Privacy-Preserving Machine Unlearning in Federated LLMs: A Certified Right-to-Be-Forgotten Framework"
SUBTITLE = "A Certified Right-to-Be-Forgotten Framework"
DEPT = "Department of Computer Science and Engineering (Data Science)"
BATCH_NAME = "Batch A9 (CSE - Data Science, Section A)"
COLLEGE = "[COLLEGE NAME]"
YEAR = "[ACADEMIC YEAR]"
GUIDE = "[GUIDE NAME]"          # the batch file holds the literal text "GUIDE NAME"
GUIDE_DESIG = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"

STUDENTS = [
    ("G.SHASHANK", "23K91A6761"),
    ("B.SATHISH", "23K91A6719"),
    ("G.RAKESH", "23K91A6759"),
    ("B.AKHIL", "23K91A6721"),
]


def metrics(name: str) -> dict:
    return json.loads((EXPDIR / name / "metrics.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------------ references (IEEE style; the numbering is the order here)
# [1] is the base paper recorded in the batch files (3.BASE PAPER.docx); only its review METHOD is adopted.
# [2]-[4] are PDFs kept in archived_base_papers/ and were read; [2] is the technical base paper named in
# archived_base_papers/BASEPAPER_REFERENCES.md.  [5], [6], [8] are batch literature-survey items that could not be
# found by web search: listed exactly as given, never quoted for any claim.  [7] was verified online.
# [9]-[22] are standard, verifiable method references.
REFERENCES = [
    'A. Khan, S. Jin, G.-H. Lee, G. E. Arzu, L. M. Dang, T. N. Nguyen, W. Choi, and H. Moon, "Deep learning approaches for continuous sign language recognition: A comprehensive review," IEEE Access, vol. 13, pp. 55524-55544, 2025, doi: 10.1109/ACCESS.2025.3554046.',
    'J. Wei, Y. Zhang, H. Zhang, L. Y. Zhang, C. Chen, K.-L. Ong, J. Zhang, and Y. Xiang, "Rethinking federated unlearning via the lens of memorization," in Proc. 32nd ACM SIGKDD Conf. Knowledge Discovery and Data Mining (KDD \'26), Jeju Island, South Korea, Aug. 2026, doi: 10.1145/3770855.3817785; arXiv:2605.24545.',
    'F. Zhang, X. Yan, T. Wu, W. Li, T. Chen, Y. Cao, R. Yan, L. Huang, W. Y. B. Lim, and Q. Yang, "Oblivionis: A lightweight learning and unlearning framework for federated large language models," arXiv:2508.08875, Aug. 2025.',
    'Y. Jiang, X. Tong, Z. Liu, X. Zhang, K.-Y. Lam, and C. W. Tan, "Certifying the right to be forgotten: Primal-dual optimization for sample and label unlearning in vertical federated learning," arXiv:2512.23171, 2025.',
    '"Federated illusion: Multi-level geometric privacy audit for federated graph unlearning," Information, 2026 (listed in the batch literature survey; not independently retrieved).',
    '"Computationally efficient federated unlearning," in Proc. 26th Int. Middleware Conf., 2025 (listed in the batch literature survey; not independently retrieved).',
    'W. Zhang, "A comprehensive investigation of federated unlearning: Challenges, methods and future prospects in privacy-sensitive applications," in Proc. 2nd Int. Conf. Data Analysis and Machine Learning (DAML), SciTePress, 2024, pp. 569-573, doi: 10.5220/0013528500004619.',
    '"Unlearning under siege: Robustness risks of certified machine unlearning," Neurocomputing, 2026 (listed in the batch literature survey; not independently retrieved).',
    'H. B. McMahan, E. Moore, D. Ramage, S. Hampson, and B. Aguera y Arcas, "Communication-efficient learning of deep networks from decentralized data," in Proc. 20th Int. Conf. Artificial Intelligence and Statistics (AISTATS), PMLR vol. 54, 2017, pp. 1273-1282.',
    'C. Dwork and A. Roth, "The algorithmic foundations of differential privacy," Foundations and Trends in Theoretical Computer Science, vol. 9, no. 3-4, pp. 211-407, 2014.',
    'M. Abadi, A. Chu, I. Goodfellow, H. B. McMahan, I. Mironov, K. Talwar, and L. Zhang, "Deep learning with differential privacy," in Proc. ACM SIGSAC Conf. Computer and Communications Security (CCS), 2016, pp. 308-318.',
    'L. Bourtoule, V. Chandrasekaran, C. A. Choquette-Choo, H. Jia, A. Travers, B. Zhang, D. Lie, and N. Papernot, "Machine unlearning," in Proc. IEEE Symp. Security and Privacy (SP), 2021, pp. 141-159.',
    'C. Guo, T. Goldstein, A. Hannun, and L. van der Maaten, "Certified data removal from machine learning models," in Proc. 37th Int. Conf. Machine Learning (ICML), PMLR vol. 119, 2020, pp. 3832-3842.',
    'A. Sekhari, J. Acharya, G. Kamath, and A. T. Suresh, "Remember what you want to forget: Algorithms for machine unlearning," in Advances in Neural Information Processing Systems (NeurIPS), vol. 34, 2021, pp. 18075-18086.',
    'R. Shokri, M. Stronati, C. Song, and V. Shmatikov, "Membership inference attacks against machine learning models," in Proc. IEEE Symp. Security and Privacy (SP), 2017, pp. 3-18.',
    'S. Yeom, I. Giacomelli, M. Fredrikson, and S. Jha, "Privacy risk in machine learning: Analyzing the connection to overfitting," in Proc. IEEE 31st Computer Security Foundations Symp. (CSF), 2018, pp. 268-282.',
    'G. Liu, X. Ma, Y. Yang, C. Wang, and J. Liu, "FedEraser: Enabling efficient client-level data removal from federated learning models," in Proc. IEEE/ACM 29th Int. Symp. Quality of Service (IWQoS), 2021, pp. 1-10.',
    'Y. Cao and J. Yang, "Towards making systems forget with machine unlearning," in Proc. IEEE Symp. Security and Privacy (SP), 2015, pp. 463-480.',
    'B. Balle and Y.-X. Wang, "Improving the Gaussian mechanism for differential privacy: Analytical calibration and optimal denoising," in Proc. 35th Int. Conf. Machine Learning (ICML), PMLR vol. 80, 2018, pp. 394-403.',
    'European Parliament and Council, "Regulation (EU) 2016/679 (General Data Protection Regulation)," Official Journal of the European Union, L 119, May 2016, Art. 17 (right to erasure).',
    'N. Carlini, F. Tramer, E. Wallace, M. Jagielski, A. Herbert-Voss, K. Lee, A. Roberts, T. Brown, D. Song, U. Erlingsson, A. Oprea, and C. Raffel, "Extracting training data from large language models," in Proc. 30th USENIX Security Symp., 2021, pp. 2633-2650.',
    'E. J. Hu, Y. Shen, P. Wallis, Z. Allen-Zhu, Y. Li, S. Wang, L. Wang, and W. Chen, "LoRA: Low-rank adaptation of large language models," in Proc. Int. Conf. Learning Representations (ICLR), 2022.',
]
BASE_PAPER = REFERENCES[0]
# reference numbers by short key, for citing in prose
REF = {"base": 1, "memprune": 2, "oblivionis": 3, "fedora": 4, "illusion": 5, "middleware": 6, "investigation": 7, "siege": 8,
       "fedavg": 9, "dwork": 10, "dpsgd": 11, "sisa": 12, "certremoval": 13, "sekhari": 14, "shokri": 15, "yeom": 16,
       "federaser": 17, "caoyang": 18, "balle": 19, "gdpr": 20, "carlini": 21, "lora": 22}
UNVERIFIED = (5, 6, 8)
