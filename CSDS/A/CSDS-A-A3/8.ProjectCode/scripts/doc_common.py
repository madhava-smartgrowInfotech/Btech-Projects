"""Shared facts for the submission documents. Every figure comes from docs/REPORT_FACTS.md and the measured JSON files."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT.parent
DIAG = ROOT / "docs" / "diagrams"
SHOTS = ROOT / "docs" / "screenshots"
CHARTS = ROOT / "docs" / "charts"
EXPD = ROOT / "docs" / "experiments"

PRODUCT = "PhishGuard"
TITLE = "A Dynamic Phishing URL Detection System Integrating Advanced Machine Learning and Crowdsourced Threat Intelligence"
DEPT = "Department of Computer Science and Engineering (Data Science)"
BATCH_NAME = "Batch A3 (CSE - Data Science, Section A)"
COLLEGE = "[COLLEGE NAME]"
YEAR = "[ACADEMIC YEAR]"
GUIDE = "Mr. G. Ravi"
GUIDE_DESIG = "[DESIGNATION]"

STUDENTS = [
    ("D.ANISH MEGHAN", "23K91A6750"),
    ("B.AKSHAYA", "23K91A6737"),
    ("B.TANUJA", "23K91A6736"),
    ("CH.SAI CHETHAN", "23K91A6742"),
]

M = json.loads((ROOT / "models" / "metrics.json").read_text())
R = json.loads((EXPD / "measured.json").read_text())
T = json.loads((EXPD / "test_results.json").read_text())
V2 = json.loads((EXPD / "demo_retrain_metrics_v2.json").read_text())
DEMO = json.loads((EXPD / "demo_scenario.json").read_text())
X = M["models"]["xgboost"]
RF = M["models"]["random_forest"]
LR = M["models"]["logistic_regression"]
CV = R["cv5"]
LAT = R["latency"]


def p(v, d=2):
    """0.9293 -> '92.93 %'"""
    return f"{v * 100:.{d}f} %"


BASE_PAPER = ('L. Aldhuwayhi and A. Alromih, "A dynamic phishing URL detection system integrating advanced machine learning and crowdsourced '
              'threat intelligence," IEEE Access, vol. 14, pp. 88393-88404, 2026, doi: 10.1109/ACCESS.2026.3700833.')

REFERENCES = [
    BASE_PAPER,
    '"Phishing URL detection using machine learning," Journal of Advanced Research in Production and Industrial Engineering, 2023.',
    '"Real-time phishing URL detection using reinforcement learning," International Journal of Science and Research (IJSR), 2025.',
    '"Phishing URL detection using machine learning and deep learning," in Proc. 2024 IEEE World AI IoT Congress (AIIoT), 2024.',
    '"Automated phishing detection through URL analysis and machine learning," Communications on Applied Nonlinear Analysis, 2025.',
    'V. Vajrobol, B. B. Gupta and A. Gaurav, "Mutual information based logistic regression for phishing URL detection," Cyber Security and Applications, vol. 2, p. 100044, Jan. 2024, doi: 10.1016/j.csa.2024.100044.',
    'T. Etem and M. Teke, "Advanced phishing detection: Leveraging t-SNE feature extraction and machine learning on a comprehensive URL dataset," Acta Infologica, vol. 231, no. 221, pp. 213-221, 2024, doi: 10.26650/acin.1521835.',
    'S. Alnemari and M. Alshammari, "Detecting phishing domains using machine learning," Applied Sciences, vol. 13, no. 8, p. 4649, Apr. 2023, doi: 10.3390/app13084649.',
    'U. A. Butt, R. Amin, H. Aldabbas, S. Mohan, B. Alouffi and A. Ahmadian, "Cloud-based email phishing attack using machine and deep learning algorithm," Complex & Intelligent Systems, vol. 9, no. 3, pp. 3043-3070, Jun. 2023, doi: 10.1007/s40747-022-00760-3.',
    'D. Rathee and S. Mann, "Detection of e-mail phishing attacks - using machine learning and deep learning," International Journal of Computer Applications, vol. 183, no. 47, pp. 1-7, Jan. 2022, doi: 10.5120/ijca2022921868.',
    'K. S. Priya, J. Chandrika and M. P. Lakshmi, "Machine learning-based phishing website detection: a comprehensive approach for cyber security," in Proc. 5th Int. Conf. Recent Trends in Computer Science and Technology (ICRTCST), Apr. 2024, pp. 344-349, doi: 10.1109/ICRTCST61793.2024.10578472.',
    'S. Sawant, R. Savakhande, O. Sankhe and S. Tamboli, "Phishing detection by integrating machine learning and deep learning," in Proc. 11th Int. Conf. Computing for Sustainable Global Development (INDIACom), Feb. 2024, pp. 1078-1083, doi: 10.23919/INDIACom61295.2024.10499100.',
    'Z. Fan, "Detecting and classifying phishing websites by machine learning," in Proc. 3rd Int. Conf. Applied Machine Learning (ICAML), Jul. 2021, pp. 48-51, doi: 10.1109/ICAML54311.2021.00018.',
    'A. Assefa and R. Katarya, "Intelligent phishing website detection using deep learning," in Proc. 8th Int. Conf. Advanced Computing and Communication Systems (ICACCS), vol. 1, Mar. 2022, pp. 1741-1745, doi: 10.1109/ICACCS54159.2022.9785003.',
    'H. Huang, N. Sun, M. Tani, Y. Zhang, J. Jiang and S. Jha, "Unmasking disinformation: Enhancing cyber threat intelligence through crowdsourced analysis and AI-driven training," in Proc. 59th Hawaii Int. Conf. System Sciences (HICSS), 2026, pp. 6049-6058, doi: 10.24251/HICSS.2026.743.',
    'K. Lazaros, A. G. Vrahatis and S. Kotsiantis, "Human-in-the-loop artificial intelligence: A systematic review of concepts, methods, and applications," Entropy, vol. 28, no. 4, p. 377, Mar. 2026, doi: 10.3390/e28040377.',
    'A. Prasad and S. Chandra, "PhiUSIIL phishing URL (website)," UCI Machine Learning Repository, 2024, doi: 10.1016/j.cose.2023.103545.',
    'J. Ma, L. K. Saul, S. Savage and G. M. Voelker, "Beyond blacklists: Learning to detect malicious web sites from suspicious URLs," in Proc. 15th ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining, 2009, pp. 1245-1254.',
    'O. K. Sahingoz, E. Buber, O. Demir and B. Diri, "Machine learning based phishing detection from URLs," Expert Systems with Applications, vol. 117, pp. 345-357, 2019.',
    'K. Krombholz, H. Hobel, M. Huber and E. Weippl, "Advanced social engineering attacks," Journal of Information Security and Applications, vol. 22, pp. 113-122, Jun. 2015, doi: 10.1016/j.jisa.2014.09.005.',
    'L. Breiman, "Random forests," Machine Learning, vol. 45, no. 1, pp. 5-32, 2001.',
    'T. Chen and C. Guestrin, "XGBoost: A scalable tree boosting system," in Proc. 22nd ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining, 2016, pp. 785-794.',
    'F. Pedregosa et al., "Scikit-learn: Machine learning in Python," Journal of Machine Learning Research, vol. 12, pp. 2825-2830, 2011.',
    'C. E. Shannon, "A mathematical theory of communication," Bell System Technical Journal, vol. 27, no. 3, pp. 379-423, Jul. 1948.',
    '"Using machine learning to detect malicious URLs," public dataset repository (data/data.csv). [Online]. Available: https://github.com/faizann24/Using-machine-learning-to-detect-malicious-URLs',
    'OpenPhish, "Phishing feed," and abuse.ch, "URLhaus: online malware URL feed." [Online]. Available: https://openphish.com and https://urlhaus.abuse.ch',
    'Pallets Projects, "Flask documentation." [Online]. Available: https://flask.palletsprojects.com',
    'Meta Platforms, "React documentation." [Online]. Available: https://react.dev',
]
REF_NOTE = ("References 2 to 5 are the works listed in the batch literature survey; they were recorded by title, venue and year only and were "
            "not independently retrieved, so this report does not describe their methods or results.")
