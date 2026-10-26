"""
Reference list for the ATHENA (CSE-A-A7) documents, IEEE style, numbered by list order (REFS[0] is [1]).

The numbering is a fixed contract: other modules cite entries through CITE['key']. REF_NOTES records how each entry was checked
(the base-paper PDF and its reference list, web search of the publisher / indexing record, or the author's knowledge of a standard
reference) and which entries are weak. Italics use *...* markup (rendered by kit.add_runs).
"""

KEYS = [
    "base", "s_obst", "s_acmj", "s_horse", "s_nepal", "cheng", "jang", "fernandes", "hinson", "hong",
    "levin", "raita", "xie", "esi", "xgboost", "shap", "treeshap", "zadrozny", "niculescu", "guo",
    "grinsztajn", "biobert", "ppocr", "breiman", "sklearn", "lime", "plaza", "chen_icd", "takita", "tripod",
    "richens", "vasey",
]

REFS = [
    # 1 - base paper
    "M. Mlodawski, S. Deniziak, M. Plaza, A. Kwiatkowska, D. Jaszczyk, A. Gajda and K. Twardowski, \"Multidimensional analysis of the diagnostic "
    "performance of machine learning models in disease classification: implications for clinical decision support systems,\" *IEEE Access*, "
    "vol. 14, pp. 92149-92177, 2026, doi: 10.1109/ACCESS.2026.3703248.",
    # 2-5 - the batch literature survey (5.LITERATURE SURVEY.docx)
    "\"Identifying the high-risk obstetric patient at triage,\" *J. Emerg. Nurs.*, 2026 (authors, volume and pages not verified).",
    "\"The effects of patient triage management strategies on clinical outcomes and risk management in emergency departments: a prospective "
    "comparative study,\" *Anatolian Curr. Med. J.*, vol. 7, no. 1, Jan. 2025.",
    "T. L. Pinn-Woodcock, J. Pigott and S. A. L. DeNotta, \"Emergency diagnostic assessment during triage,\" in *Emergency Triage of the Horse*. "
    "Hoboken, NJ, USA: Wiley, 2025, ch. 6, p. 91.",
    "\"Assessment of knowledge of triage among patient attendants presenting in the emergency department: a single center observational study,\" "
    "*J. Gen. Pract. Emerg. Med. Nepal*, 2024 (authors and pages not verified).",
    # 6-7 - companion and archived papers
    "H. Cheng, C. Yu, Y. Shi, C. Wang, C. Liu and Z. Jin, \"Collaborative medical triage under uncertainty: a multi-agent dynamic matching "
    "approach,\" arXiv:2507.22504, Jul. 2025.",
    "H. Jang, G. Chu, C. Kim, J. Park et al., \"TRIAGE: dialectical reasoning for explainable risk prediction on irregularly sampled medical "
    "time series with LLMs,\" arXiv:2606.09030, Jun. 2026.",
    # 8-14 - triage and emergency-department prediction
    "M. Fernandes, S. M. Vieira, F. Leite, C. Palos, S. Finkelstein and J. M. C. Sousa, \"Clinical decision support systems for triage in the "
    "emergency department using intelligent systems: a review,\" *Artif. Intell. Med.*, vol. 102, Art. no. 101762, Jan. 2020, "
    "doi: 10.1016/j.artmed.2019.101762.",
    "J. S. Hinson, D. A. Martinez, S. Cabral et al., \"Triage performance in emergency medicine: a systematic review,\" *Ann. Emerg. Med.*, "
    "vol. 74, no. 1, pp. 140-152, Jul. 2019, doi: 10.1016/j.annemergmed.2018.09.022.",
    "W. S. Hong, A. D. Haimovich and R. A. Taylor, \"Predicting hospital admission at emergency department triage using machine learning,\" "
    "*PLoS ONE*, vol. 13, no. 7, Art. no. e0201016, Jul. 2018, doi: 10.1371/journal.pone.0201016.",
    "S. Levin et al., \"Machine-learning-based electronic triage more accurately differentiates patients with respect to clinical outcomes "
    "compared with the Emergency Severity Index,\" *Ann. Emerg. Med.*, vol. 71, no. 5, pp. 565-574, May 2018, "
    "doi: 10.1016/j.annemergmed.2017.08.005.",
    "Y. Raita et al., \"Emergency department triage prediction of clinical outcomes using machine learning models,\" *Crit. Care*, vol. 23, "
    "Art. no. 64, Feb. 2019, doi: 10.1186/s13054-019-2351-7.",
    "F. Xie et al., \"Benchmarking emergency department prediction models with machine learning and public electronic health records,\" "
    "*Sci. Data*, vol. 9, Art. no. 658, Oct. 2022, doi: 10.1038/s41597-022-01782-9.",
    "N. Gilboy, P. Tanabe, D. Travers and A. M. Rosenau, *Emergency Severity Index (ESI): A Triage Tool for Emergency Department Care, "
    "Version 4, Implementation Handbook 2012 Edition*, AHRQ Pub. no. 12-0014. Rockville, MD, USA: Agency for Healthcare Research and Quality, 2011.",
    # 15-21 - methods
    "T. Chen and C. Guestrin, \"XGBoost: a scalable tree boosting system,\" in *Proc. 22nd ACM SIGKDD Int. Conf. Knowl. Discovery Data Mining*, "
    "San Francisco, CA, USA, 2016, pp. 785-794, doi: 10.1145/2939672.2939785.",
    "S. M. Lundberg and S.-I. Lee, \"A unified approach to interpreting model predictions,\" in *Proc. Adv. Neural Inf. Process. Syst. (NeurIPS)*, "
    "vol. 30, 2017, pp. 4765-4774, arXiv:1705.07874.",
    "S. M. Lundberg et al., \"From local explanations to global understanding with explainable AI for trees,\" *Nat. Mach. Intell.*, vol. 2, "
    "no. 1, pp. 56-67, Jan. 2020, doi: 10.1038/s42256-019-0138-9.",
    "B. Zadrozny and C. Elkan, \"Transforming classifier scores into accurate multiclass probability estimates,\" in *Proc. 8th ACM SIGKDD Int. "
    "Conf. Knowl. Discovery Data Mining*, Edmonton, AB, Canada, 2002, pp. 694-699, doi: 10.1145/775047.775151.",
    "A. Niculescu-Mizil and R. Caruana, \"Predicting good probabilities with supervised learning,\" in *Proc. 22nd Int. Conf. Mach. Learn. "
    "(ICML)*, Bonn, Germany, 2005, pp. 625-632, doi: 10.1145/1102351.1102430.",
    "C. Guo, G. Pleiss, Y. Sun and K. Q. Weinberger, \"On calibration of modern neural networks,\" in *Proc. 34th Int. Conf. Mach. Learn. (ICML)*, "
    "PMLR vol. 70, 2017, pp. 1321-1330.",
    "L. Grinsztajn, E. Oyallon and G. Varoquaux, \"Why do tree-based models still outperform deep learning on typical tabular data?\" in *Proc. "
    "Adv. Neural Inf. Process. Syst. (NeurIPS) Datasets Benchmarks Track*, vol. 35, 2022, pp. 507-520, arXiv:2207.08815.",
    "J. Lee, W. Yoon, S. Kim, D. Kim, S. Kim, C. H. So and J. Kang, \"BioBERT: a pre-trained biomedical language representation model for "
    "biomedical text mining,\" *Bioinformatics*, vol. 36, no. 4, pp. 1234-1240, Feb. 2020, doi: 10.1093/bioinformatics/btz682.",
    "Y. Du et al., \"PP-OCR: a practical ultra lightweight OCR system,\" arXiv:2009.09941, Sep. 2020.",
    "L. Breiman, \"Random forests,\" *Mach. Learn.*, vol. 45, no. 1, pp. 5-32, Oct. 2001, doi: 10.1023/A:1010933404324.",
    "F. Pedregosa et al., \"Scikit-learn: machine learning in Python,\" *J. Mach. Learn. Res.*, vol. 12, pp. 2825-2830, 2011.",
    "M. T. Ribeiro, S. Singh and C. Guestrin, \"'Why should I trust you?': explaining the predictions of any classifier,\" in *Proc. 22nd ACM "
    "SIGKDD Int. Conf. Knowl. Discovery Data Mining*, San Francisco, CA, USA, 2016, pp. 1135-1144, doi: 10.1145/2939672.2939778.",
    # 27-32 - cited by the base paper, bibliographic data taken from its reference list; plus reporting guidance
    "M. Plaza, \"Multimodal system for automated medical documentation and clinical decision support integrating contact center solutions,\" "
    "*Sci. Rep.*, vol. 16, no. 1, p. 15017, Mar. 2026, doi: 10.1038/s41598-026-45879-2.",
    "P.-F. Chen et al., \"Automatic international classification of diseases coding system: deep contextualized language model with rule-based "
    "approaches,\" *JMIR Med. Informat.*, vol. 10, no. 6, Art. no. e37557, Jun. 2022, doi: 10.2196/37557.",
    "H. Takita et al., \"A systematic review and meta-analysis of diagnostic performance comparison between generative AI and physicians,\" "
    "*npj Digit. Med.*, vol. 8, no. 1, p. 175, Mar. 2025, doi: 10.1038/s41746-025-01543-z.",
    "G. S. Collins et al., \"TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine "
    "learning methods,\" *BMJ*, vol. 385, Art. no. e078378, Apr. 2024, doi: 10.1136/bmj-2023-078378.",
    "J. G. Richens, C. M. Lee and S. Johri, \"Improving the accuracy of medical diagnosis with causal machine learning,\" *Nat. Commun.*, "
    "vol. 11, no. 1, p. 3923, Aug. 2020, doi: 10.1038/s41467-020-17419-7.",
    "B. Vasey et al., \"Association of clinician diagnostic performance with machine learning-based decision support systems: a systematic "
    "review,\" *JAMA Netw. Open*, vol. 4, no. 3, Art. no. e211276, Mar. 2021, doi: 10.1001/jamanetworkopen.2021.1276.",
]

assert len(REFS) == len(KEYS) == 32
CITE = {k: i + 1 for i, k in enumerate(KEYS)}

REF_NOTES = {
    "base": "PDF in Documentary/ read in full (29 pages, 92149-92177); title, authors, volume, pages and DOI checked against the first page. Named as the base paper by 1.A7_BATCH_DETAILS.docx and 3.BASE PAPER.docx.",
    "s_obst": "From the batch literature survey. Web search found no record of this title in the Journal of Emergency Nursing; authors, volume and pages unknown. WEAK: listed for completeness, never cited as evidence.",
    "s_acmj": "From the batch survey. Found at dergipark.org.tr/tr/pub/acmj/article/1579702 (vol. 7, no. 1, Jan 2025): prospective comparison of ESI and Manchester triage, 6,000 patients each, a state hospital in Turkey. Authors not retrieved.",
    "s_horse": "From the batch survey. The record is chapter 6 of the Wiley book Emergency Triage of the Horse (2025): veterinary, so out of domain for human triage. Listed with that caveat, never cited as evidence.",
    "s_nepal": "From the batch survey. Single-centre cross-sectional study of 284 patient attendants at BPKIHS, Dharan, Nepal (nepjol.info jgpemn article 87619). The 2024 date comes from the batch file and was not confirmed.",
    "cheng": "Companion reference paper kept in archived_base_papers/; arXiv:2507.22504 (30 Jul 2025). Cited from its title and the archive record only.",
    "jang": "Archived base-paper record names this as an earlier base paper; arXiv:2606.09030 (8 Jun 2026). Authors beyond the first four not in the record. Cited from title only.",
    "fernandes": "Web search: AI in Medicine vol. 102, Art. 101762, Jan 2020, doi 10.1016/j.artmed.2019.101762; review of intelligent triage CDSS; several studies lacked an implementation phase.",
    "hinson": "Web search: Ann Emerg Med 2019;74(1):140-152, doi 10.1016/j.annemergmed.2018.09.022; 182 eligible studies, sensitivity for critical illness below 80 percent.",
    "hong": "Web search: PLoS ONE 13(7):e0201016, 20 Jul 2018; 560,486 visits; triage-only AUC about 0.87, full-variable about 0.91-0.92.",
    "levin": "Web search: Ann Emerg Med 71(5):565-574, doi 10.1016/j.annemergmed.2017.08.005; 172,726 visits; random forest e-triage AUC 0.73-0.92; matched or beat ESI.",
    "raita": "Web search: Crit Care 23:64, doi 10.1186/s13054-019-2351-7; 135,470 NHAMCS visits; deep neural network AUC 0.86 vs 0.74 for an ESI model on critical care.",
    "xie": "Web search: Sci Data 9:658, 27 Oct 2022, doi 10.1038/s41597-022-01782-9; MIMIC-IV-ED benchmark for hospitalisation, critical outcome and 72-hour reattendance.",
    "esi": "Standard AHRQ handbook (Gilboy et al., ESI version 4, 2012 edition, pub. 12-0014); cited from the author's knowledge of the record, not re-fetched.",
    "xgboost": "Standard reference, KDD 2016 pp. 785-794; doi from the author's knowledge of the record.",
    "shap": "Standard reference, NeurIPS 2017; the base paper cites the same work as arXiv:1705.07874 (its ref. [39]).",
    "treeshap": "Standard reference, Nat Mach Intell 2020; the TreeExplainer algorithm used by the product. From the author's knowledge of the record, not re-fetched.",
    "zadrozny": "Standard reference for isotonic calibration of multiclass scores; from the author's knowledge of the record.",
    "niculescu": "Standard reference on calibrating classifier scores; from the author's knowledge of the record.",
    "guo": "Standard reference on calibration and expected calibration error; from the author's knowledge of the record.",
    "grinsztajn": "Standard reference on tree-based models and tabular data; arXiv:2207.08815; from the author's knowledge of the record.",
    "biobert": "Standard reference; the batch abstract names BioBERT but the product does not use it. From the author's knowledge of the record.",
    "ppocr": "arXiv:2009.09941; PaddleOCR family. RapidOCR runs PaddleOCR-family models through ONNX Runtime. From the author's knowledge of the record.",
    "breiman": "Standard reference, Mach Learn 45(1):5-32, 2001.",
    "sklearn": "Standard reference, JMLR 12:2825-2830, 2011.",
    "lime": "Standard reference; the batch abstract names LIME, which the product does not implement. From the author's knowledge of the record.",
    "plaza": "Base paper ref. [7], bibliographic data copied from the base paper's reference list (PARROT AI multimodal assistant).",
    "chen_icd": "Base paper ref. [13], data copied from its reference list (BioBERT with rule-based ICD coding, F1 0.769 per the base paper).",
    "takita": "Base paper ref. [15], data copied from its reference list.",
    "tripod": "Base paper ref. [34], data copied from its reference list; reporting guidance for prediction models.",
    "richens": "Base paper ref. [32], data copied from its reference list.",
    "vasey": "Base paper ref. [5], data copied from its reference list.",
}
