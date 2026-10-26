"""Shared facts for the CropSight submission documents. Every figure comes from docs/REPORT_FACTS.md and experiments/*/metrics.json."""
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

PRODUCT = "CropSight"
TITLE = "CropSight: Smart Crop Delivery with AI-Based Price and Quality Intelligence"
SUBTITLE = "Smart Crop Delivery with AI-Based Price and Quality Intelligence"
DEPT = "Department of Computer Science and Engineering (Data Science)"
BATCH_NAME = "Batch A17 (CSE - Data Science, Section A)"
COLLEGE = "[COLLEGE NAME]"
YEAR = "[ACADEMIC YEAR]"
GUIDE = "K. Mounika"
GUIDE_DESIG = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"

STUDENTS = [
    ("G.PRANAVI", "23K91A6765"),
    ("G.SIRI CHANDANA", "23K91A6763"),
    ("A.NIKHIL", "23K91A6715"),
    ("G.VISHNU VARDHAN", "23K91A6754"),
]


def metrics(name: str) -> dict:
    return json.loads((EXPDIR / name / "metrics.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------------ references (IEEE style; numbering is the order here)
# 1 is the base paper (batch file 3.BASE PAPER.docx); 2-5 are the batch literature-survey papers (2-5 could not be retrieved
# independently, so they are listed as given and are NOT quoted for any result); 6-7 are real papers whose PDFs are in
# archived_base_papers/ and were read; the rest are standard, verifiable method and software references.
REFERENCES = [
    'A. Khaliq, A. Khan, S. Jan, M. Umair, A. Gulshair, A. Ali, and U. A. Shah, "AI-driven smart agriculture: An integrated approach for soil analysis, irrigation, and crop-fertilizer recommendations," IEEE Access, vol. 13, pp. 141124-141138, 2025, doi: 10.1109/ACCESS.2025.3594162.',
    '"Cross-task consistent multi-task learning for fine-grained crop leaf disease diagnosis and severity grading," in Proc. 2026 7th Int. Conf. Computer Vision, Image and Deep Learning (CVIDL), 2026 (listed in the batch literature survey; not independently retrieved).',
    '"Design of agricultural product quality inspection and e-commerce grading system based on image recognition," in Proc. 2nd Int. Conf. Artificial Intelligence, Deep Learning, and Neural Networks (AIDLNN 2025), 2026 (listed in the batch literature survey; not independently retrieved).',
    '"Crop and market price prediction system using machine learning," Int. Research J. Modernization in Engineering Technology and Science (IRJMETS), 2023 (listed in the batch literature survey; not independently retrieved).',
    '"Crop price prediction using machine learning," J. Electrical Systems, 2024 (listed in the batch literature survey; not independently retrieved).',
    'L. Wang and B. Zhang, "The promise of time-series foundation models for agricultural forecasting: Evidence from commodity prices," arXiv:2601.06371, Jan. 2026.',
    'L. Feng and S. Zong, "Large-scale crop image recognition based on ConvLSTM spatiotemporal feature extraction and LCMST-Net model," IEEE Access, vol. 14, pp. 10719-10734, 2026, doi: 10.1109/ACCESS.2026.3653414.',
    'N. Sultana, M. Jahan, and M. S. Uddin, "An extensive dataset for successful recognition of fresh and rotten fruits," Data in Brief, vol. 44, Art. no. 108552, 2022, doi: 10.1016/j.dib.2022.108552.',
    'Project-AgML, "Vegetable classification (Bangladesh)," Hugging Face dataset repository, CC BY 4.0. [Online]. Available: https://huggingface.co/datasets/Project-AgML/vegetable_classification_bangladesh',
    'L. Breiman, "Random forests," Machine Learning, vol. 45, no. 1, pp. 5-32, 2001.',
    'J. H. Friedman, "Greedy function approximation: A gradient boosting machine," Annals of Statistics, vol. 29, no. 5, pp. 1189-1232, 2001.',
    'R. Koenker and G. Bassett, "Regression quantiles," Econometrica, vol. 46, no. 1, pp. 33-50, 1978.',
    'S. M. Lundberg and S.-I. Lee, "A unified approach to interpreting model predictions," in Advances in Neural Information Processing Systems (NeurIPS), vol. 30, 2017, pp. 4765-4774.',
    'S. M. Lundberg et al., "From local explanations to global understanding with explainable AI for trees," Nature Machine Intelligence, vol. 2, no. 1, pp. 56-67, 2020.',
    'R. M. Haralick, K. Shanmugam, and I. Dinstein, "Textural features for image classification," IEEE Trans. Systems, Man, and Cybernetics, vol. SMC-3, no. 6, pp. 610-621, 1973.',
    'J. Canny, "A computational approach to edge detection," IEEE Trans. Pattern Analysis and Machine Intelligence, vol. PAMI-8, no. 6, pp. 679-698, 1986.',
    'N. Otsu, "A threshold selection method from gray-level histograms," IEEE Trans. Systems, Man, and Cybernetics, vol. SMC-9, no. 1, pp. 62-66, 1979.',
    'F. Pedregosa et al., "Scikit-learn: Machine learning in Python," J. Machine Learning Research, vol. 12, pp. 2825-2830, 2011.',
    'S. van der Walt et al., "scikit-image: Image processing in Python," PeerJ, vol. 2, Art. no. e453, 2014.',
    'G. Bradski, "The OpenCV library," Dr. Dobb\'s Journal of Software Tools, 2000.',
    'M. T. Ribeiro, S. Singh, and C. Guestrin, "\'Why should I trust you?\': Explaining the predictions of any classifier," in Proc. 22nd ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining, 2016, pp. 1135-1144.',
    'S. O. Arik and T. Pfister, "TabNet: Attentive interpretable tabular learning," in Proc. AAAI Conf. Artificial Intelligence, vol. 35, no. 8, 2021, pp. 6679-6687.',
    'M. Jones, J. Bradley, and N. Sakimura, "JSON Web Token (JWT)," RFC 7519, Internet Engineering Task Force, May 2015.',
]
BASE_PAPER = REFERENCES[0]
