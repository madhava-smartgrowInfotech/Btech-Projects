"""Shared facts for the SHEGUARD submission documents. Every figure comes from docs/REPORT_FACTS.md and experiments/**/*.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT.parent
DIAG = ROOT / "docs" / "diagrams"
SHOTS = ROOT / "docs" / "screenshots"
CHARTS = ROOT / "docs" / "charts"
EXPDIR = ROOT / "experiments"
STUDY = EXPDIR / "study"

PRODUCT = "SHEGUARD"
TITLE = "SHEGUARD: AI Powered Women's Safety Platform"
SUBTITLE = "AI Powered Women's Safety Platform"
DEPT = "Department of Computer Science and Engineering (Data Science)"
BATCH_NAME = "Batch A7 (CSE - Data Science, Section A)"
COLLEGE = "[COLLEGE NAME]"
YEAR = "[ACADEMIC YEAR]"
GUIDE = "[GUIDE NAME]"
GUIDE_DESIG = "[DESIGNATION]"
HOD = "[HOD NAME]"
PRINCIPAL = "[PRINCIPAL NAME]"

STUDENTS = [
    ("CH.AARTHI", "23K91A6741"),
    ("D.PRANATHI", "23K91A6748"),
    ("BALA VIGNESH", "23K91A6717"),
    ("A.VISHAL", "23K91A6704"),
]


def study(name: str) -> dict:
    return json.loads((STUDY / name).read_text(encoding="utf-8"))


def metrics() -> dict:
    return study("metrics.json")


# ------------------------------------------------------------------ references (IEEE style; the numbering is the order here)
# 1 = base paper (batch file 3.BASE PAPER.docx). 2 read in full (Documentary/Base paper_.pdf). 3-5 are the batch literature-survey
# entries that could not be retrieved independently: listed as given, never quoted for any result. 6-8 are PDFs in archived_base_papers/
# that were read. 9-15 are the classical methods; 16-30 standard software, services, datasets and specifications.
REFERENCES = [
    'K. Agrawal, A. Srivastava, K. Sharma, S. K. Satapathy, S.-B. Cho, S. Mishra, A. Chowdhury, and A. Pal, "SafeRoutes: Charting a secure path - A holistic approach to women\'s safety through advanced clustering and GPS integration," IEEE Access, vol. 12, pp. 166368-166378, 2024, doi: 10.1109/ACCESS.2024.3488784.',
    'M. S. Farooq, A. Masooma, U. Omer, R. Tehseen, S. A. M. Gilani, and Z. Atal, "The role of IoT in woman\'s safety: A systematic literature review," IEEE Access, vol. 11, pp. 69807-69825, 2023, doi: 10.1109/ACCESS.2023.3252903.',
    '"A mobile-based women safety application with real-time emergency alert and location tracking," Int. Scientific J. of Engineering and Management, 2026 (listed in the batch literature survey; not independently retrieved).',
    '"Shake-to-Alert: An automated mobile safety application for women with emergency notification via motion detection," in Proc. Int. Conf. IT Innovation and Knowledge Discovery (ITIKD), 2025 (listed in the batch literature survey; not independently retrieved).',
    '"Cross-platform women safety mobile application with real-time alert system and GPS tracking," in Proc. Int. Conf. Electronic Systems and Intelligent Computing (ICESIC), 2026 (listed in the batch literature survey; not independently retrieved).',
    'A. Thawale, H. Pal, M. Thakur, M. A. Bhave, P. Asokan, and M. Amnerkar, "Women safety mobile application using ESP32 camera and real-time crime data analysis," Int. J. Electrical, Electronics and Computer Systems, 2025.',
    'R. Shinde, H. Nerkar, T. Kad, V. Gayake, and K. Chobe, "SafeGuard - Safe route recommendation system," Int. Research J. Modernization in Engineering, Technology and Science (IRJMETS), vol. 7, no. 3, Mar. 2025.',
    'Sangeeta, M. S. Prajwal, D. P. Dogra, K. V. Thakare, H. Jung, I.-J. Kim, and H. Choi, "ExtrAnom: A VAD benchmark emphasizing the need for women\'s safety in society," arXiv:2605.25806, 2026.',
    'J. MacQueen, "Some methods for classification and analysis of multivariate observations," in Proc. 5th Berkeley Symp. Mathematical Statistics and Probability, vol. 1, 1967, pp. 281-297.',
    'S. P. Lloyd, "Least squares quantization in PCM," IEEE Trans. Information Theory, vol. IT-28, no. 2, pp. 129-137, 1982.',
    'P. J. Rousseeuw, "Silhouettes: A graphical aid to the interpretation and validation of cluster analysis," J. Computational and Applied Mathematics, vol. 20, pp. 53-65, 1987.',
    'D. L. Davies and D. W. Bouldin, "A cluster separation measure," IEEE Trans. Pattern Analysis and Machine Intelligence, vol. PAMI-1, no. 2, pp. 224-227, 1979.',
    'T. Calinski and J. Harabasz, "A dendrite method for cluster analysis," Communications in Statistics, vol. 3, no. 1, pp. 1-27, 1974.',
    'A. P. Dempster, N. M. Laird, and D. B. Rubin, "Maximum likelihood from incomplete data via the EM algorithm," J. Royal Statistical Society: Series B, vol. 39, no. 1, pp. 1-38, 1977.',
    'J. H. Ward, "Hierarchical grouping to optimize an objective function," J. American Statistical Association, vol. 58, no. 301, pp. 236-244, 1963.',
    'F. Pedregosa et al., "Scikit-learn: Machine learning in Python," J. Machine Learning Research, vol. 12, pp. 2825-2830, 2011.',
    'D. Luxen and C. Vetter, "Real-time routing with OpenStreetMap data," in Proc. 19th ACM SIGSPATIAL Int. Conf. Advances in Geographic Information Systems, 2011, pp. 513-516.',
    'M. Haklay and P. Weber, "OpenStreetMap: User-generated street maps," IEEE Pervasive Computing, vol. 7, no. 4, pp. 12-18, 2008.',
    'M. Jones, J. Bradley, and N. Sakimura, "JSON Web Token (JWT)," RFC 7519, Internet Engineering Task Force, May 2015.',
    'I. Fette and A. Melnikov, "The WebSocket protocol," RFC 6455, Internet Engineering Task Force, Dec. 2011.',
    'N. Provos and D. Mazieres, "A future-adaptable password scheme," in Proc. USENIX Annual Technical Conf., 1999, pp. 81-91.',
    '"Secure hash standard (SHS)," Federal Information Processing Standards Publication FIPS PUB 180-4, National Institute of Standards and Technology, Aug. 2015.',
    'rajanand, "Crime in India," Kaggle dataset (district-wise crimes against women, 2001-2012), CC0 public domain. [Online]. Available: https://www.kaggle.com/datasets/rajanand/crime-in-india',
    'balajivaraprasad, "Crimes against women in India 2001-2021," Kaggle dataset, CC0 public domain. [Online]. Available: https://www.kaggle.com/datasets/balajivaraprasad/crimes-against-women-in-india-2001-2021',
    '"Web Speech API," W3C Community Group specification. [Online]. Available: https://webaudio.github.io/web-speech-api/',
    'Google, "Gemini API: generateContent," Google AI for Developers documentation. [Online]. Available: https://ai.google.dev/gemini-api/docs',
    'S. Ramirez, "FastAPI," software documentation. [Online]. Available: https://fastapi.tiangolo.com',
    'V. Agafonkin, "Leaflet: an open-source JavaScript library for interactive maps." [Online]. Available: https://leafletjs.com',
    'Nominatim contributors, "Nominatim: open-source geocoding with OpenStreetMap data" and usage policy. [Online]. Available: https://nominatim.org',
    'Telegram, "Telegram Bot API." [Online]. Available: https://core.telegram.org/bots/api',
]
BASE_PAPER = REFERENCES[0]
NOT_RETRIEVED = {3, 4, 5}   # reference numbers that were not independently retrieved
