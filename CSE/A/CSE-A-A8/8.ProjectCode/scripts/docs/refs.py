"""
IEEE-style reference list. [1] was checked against the base-paper PDF; [2]-[5] and [12] against arXiv / the publisher
DOI record; [6]-[11] are from the base paper's own reference list (checked against the PDF) or are well-known
publications. Entries [25]-[27] are title / year / source triples recorded in the batch literature survey; their
authors and details could not be verified and are not guessed - they are never cited as evidence.
"""

REFS = [
    # 1
    "A. Karhade, I. Verma, V. Gadaokar, and J. Mahajan, \"RAG-based blood test report analysis to reverse metabolic syndrome,\" Commun. Appl. Nonlinear Anal., vol. 32, no. 10s, pp. 2771-2779, 2025, doi: 10.52783/cana.v32.5718.",
    # 2
    "X. Ren, D. Dou, X. He, F. Cui, and J. Zhao, \"A serialization method for digitizing the image-based medical laboratory report,\" Digital Health, 2025, doi: 10.1177/20552076251334431.",
    # 3
    "S. Xiang, S. Chen, K. Q. Lin, J. Yu, Y. Sun, P. Torr, and A. Atapour-Abarghouei, \"Checkup2Action: A multimodal clinical check-up report dataset for patient-oriented action card generation,\" arXiv:2605.11533, 2026.",
    # 4
    "N. Bakhsheshi and H. Beigy, \"Analysis of blood report images using general-purpose vision-language models,\" arXiv:2509.06033, 2025.",
    # 5
    "V.-T. Nguyen, H.-D. Pham, T.-H. To, C.-T. H. Do, T.-T.-T. Dong, V.-T. D. Le, and V.-P. Hoang, \"Medalyze: Lightweight medical report summarization application using FLAN-T5-Large,\" arXiv:2505.17059, 2025.",
    # 6
    "P. Lewis et al., \"Retrieval-augmented generation for knowledge-intensive NLP tasks,\" in Advances in Neural Information Processing Systems, vol. 33, 2020, pp. 9459-9474.",
    # 7
    "M. Salvagno, F. S. Taccone, and A. G. Gerli, \"Evaluating the feasibility of ChatGPT in healthcare: An analysis of multiple clinical and research scenarios,\" J. Med. Syst., vol. 47, no. 1, p. 33, 2023.",
    # 8
    "V. X. Liu, C. A. Sinsky, S. Lin et al., \"AI-generated draft replies integrated into health records and physicians' electronic communication,\" JAMA Netw. Open, vol. 7, no. 3, p. e2417615, 2024.",
    # 9
    "Y. Shokrollahi, S. Yarmohammadtoosky, M. M. Nikahd et al., \"A comprehensive review of generative AI in healthcare,\" arXiv:2310.00795, 2023.",
    # 10
    "H.-L. Hsu, C.-T. Dao, L. Wang et al., \"MEDPLAN: A two-stage RAG-based system for personalized medical plan generation,\" arXiv:2503.17900, 2025.",
    # 11
    "I. Kataria, R. Chadha, and R. Pathak, \"Dietary and lifestyle modification in metabolic syndrome: A review of randomized control trials in different population groups,\" Rev. Health Care, vol. 6, no. 3, pp. 97-103, 2015.",
    # 12
    "Y. Du, C. Li, R. Guo, X. Yin, W. Liu, J. Zhou, Y. Bai, Z. Yu, Y. Yang, Q. Dang, and H. Wang, \"PP-OCR: A practical ultra lightweight OCR system,\" arXiv:2009.09941, 2020.",
    # 13
    "R. Smith, \"An overview of the Tesseract OCR engine,\" in Proc. 9th Int. Conf. Document Analysis and Recognition (ICDAR), 2007, pp. 629-633.",
    # 14
    "J. Lafferty, A. McCallum, and F. Pereira, \"Conditional random fields: Probabilistic models for segmenting and labeling sequence data,\" in Proc. 18th Int. Conf. Machine Learning (ICML), 2001, pp. 282-289.",
    # 15
    "G. Salton and C. Buckley, \"Term-weighting approaches in automatic text retrieval,\" Inf. Process. Manag., vol. 24, no. 5, pp. 513-523, 1988.",
    # 16
    "F. Pedregosa et al., \"Scikit-learn: Machine learning in Python,\" J. Mach. Learn. Res., vol. 12, pp. 2825-2830, 2011.",
    # 17
    "G. Bradski, \"The OpenCV library,\" Dr. Dobb's Journal of Software Tools, 2000.",
    # 18
    "N. Reimers and I. Gurevych, \"Sentence-BERT: Sentence embeddings using Siamese BERT-networks,\" in Proc. EMNLP-IJCNLP, 2019, pp. 3982-3992.",
    # 19
    "M. Bayer, \"SQLAlchemy,\" in The Architecture of Open Source Applications, vol. 2, A. Brown and G. Wilson, Eds. 2012.",
    # 20
    "Artifex Software, \"PyMuPDF documentation.\" [Online]. Available: https://pymupdf.readthedocs.io",
    # 21
    "S. Ramirez, \"FastAPI framework documentation.\" [Online]. Available: https://fastapi.tiangolo.com",
    # 22
    "Recharts contributors, \"Recharts: A composable charting library built on React components.\" [Online]. Available: https://recharts.org",
    # 23
    "Anthropic, \"Messages API reference.\" [Online]. Available: https://docs.anthropic.com",
    # 24
    "M. Honnibal and I. Montani, \"spaCy 2: Natural language understanding with Bloom embeddings, convolutional neural networks and incremental parsing,\" 2017. [Online]. Available: https://spacy.io",
    # 25
    "\"P-025 Health and safety in medical analysis laboratory,\" Occupational Medicine, 2024. (Listed in the batch literature survey; authors and details not verified.)",
    # 26
    "\"Analysis of laboratory data of RT-PCR testing for SARS-CoV-2 in SVRDL at Government Medical College, Nagpur,\" Himalayan J. Community Med. Public Health, 2024. (Listed in the batch literature survey; authors and details not verified.)",
    # 27
    "\"Inter-laboratory study for extraction testing of medical devices,\" J. Pharm. Biomed. Anal., 2025. (Listed in the batch literature survey; authors and details not verified.)",
]


def n(*nums):
    """Citation string for reference numbers, e.g. n(1, 3) -> [1], [3]."""
    return ", ".join(f"[{k}]" for k in nums)
