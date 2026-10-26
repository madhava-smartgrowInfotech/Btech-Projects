"""
IEEE-style reference list for the A6 documents. NUMBERS ARE FIXED: chapters, decks and the paper cite them as n(1, 9).

Verification status (26 Oct 2026; details and URLs in docs/LIT_NOTES.md):
  read from the supplied PDFs ............ 1, 2, 3
  checked on the web (publisher, arXiv, Crossref, WHO) ... 4, 6, 8, 9, 10, 11, 12, 13, 14, 16, 17, 20, 21, 25, 27, 28, 29, 30
  checked in part (see the entry's note in LIT_NOTES.md) .. 5 (repository record, abstract only), 15 (corporate Tech Brief),
                                                           18 (edition), 26 (page range not confirmed, so omitted)
  title and year only (could not be found) ................ 7
"""

REFS = [
    # 1 base paper (read from the PDF in Documentary/)
    "C.-L. Feng and T.-H. S. Li, \"Robust driver state assessment on an embedded platform using a fuzzy belief rule-based fusion of eye aspect ratio and voice commands,\" IEEE Access, vol. 14, pp. 36158-36175, 2026, doi: 10.1109/ACCESS.2026.3670924.",
    # 2 companion paper (read from the PDF in archived_base_papers/)
    "B. Baroutian, A. Aghaei, and M. Ebrahimi Moghaddam, \"Detection of intoxicated individuals from facial video sequences via a recurrent fusion model,\" arXiv:2512.04536, Dec. 2025.",
    # 3 (read from the PDF in archived_base_papers/)
    "R. Deuber et al., \"Detecting drunk driving using off-the-shelf smartwatches,\" arXiv:2605.23663, May 2026 (manuscript under review).",
    # 4 (web: arXiv record)
    "V. Mehta, D. P. Yadav, S. S. Katta, and A. Dhall, \"DIF: Dataset of perceived intoxicated faces for drunk person identification,\" arXiv:1805.10030, 2018 (revised 2019).",
    # 5 batch survey item 2 (Iowa State University repository record; abstract only)
    "L. P. Acharya, \"Infrared deep learning system for non-invasive drunk detection and alcohol level classification,\" Iowa State Univ., Ames, IA, USA, Dec. 2024. [Online]. Available: https://dr.lib.iastate.edu/handle/20.500.12876/105973",
    # 6 batch survey item 3 (AHFE open-access page)
    "F. Deiana, J. Jackson, and C. Periago, \"Development and verification of a testing methodology for driver alcohol intoxication detection systems,\" in Human Systems Engineering and Design (IHSED2026): Future Trends and Applications, AHFE Int., 2026, doi: 10.54941/ahfe1008145.",
    # 7 batch survey item 4 (not found on the web; title and year only)
    "\"Alcohol detection and vehicle immobilization system for enhanced taxi driver safety and drunk driving prevention,\" in Proc. 9th Int. Conf. Trends in Electronics and Informatics (ICOEI), 2026 (entry recorded in the batch literature survey; not located online).",
    # 8 batch survey item 5 (MDPI Information)
    "C.-H. Chai, S. F. Abdul Razak, S. Yogarayan, and R. Shanmugam, \"Drunk driver detection using thermal facial images,\" Information, vol. 16, no. 5, Art. no. 413, 2025.",
    # 9 (web: CVWW proceedings)
    "T. Soukupova and J. Cech, \"Real-time eye blink detection using facial landmarks,\" in Proc. 21st Computer Vision Winter Workshop, Rimske Toplice, Slovenia, Feb. 2016.",
    # 10 (web: arXiv / Google Research)
    "Y. Kartynnik, A. Ablavatski, I. Grishchenko, and M. Grundmann, \"Real-time facial surface geometry from monocular video on mobile GPUs,\" arXiv:1907.06724, 2019.",
    # 11 (web: arXiv)
    "C. Lugaresi et al., \"MediaPipe: A framework for building perception pipelines,\" arXiv:1906.08172, 2019.",
    # 12 (web: Crossref; CEW dataset)
    "F. Song, X. Tan, X. Liu, and S. Chen, \"Eyes closeness detection from still images with multi-scale histograms of principal oriented gradients,\" Pattern Recognit., vol. 47, no. 9, pp. 2825-2838, Sep. 2014, doi: 10.1016/j.patcog.2014.03.024.",
    # 13 (web: UMass tech report; LFW)
    "G. B. Huang, M. Ramesh, T. Berg, and E. Learned-Miller, \"Labeled faces in the wild: A database for studying face recognition in unconstrained environments,\" Univ. Massachusetts Amherst, Amherst, MA, USA, Tech. Rep. 07-49, Oct. 2007.",
    # 14 (web: Crossref; the NTHU-DDD dataset used by the base paper)
    "C.-H. Weng, Y.-H. Lai, and S.-H. Lai, \"Driver drowsiness detection via a hierarchical temporal deep belief network,\" in Computer Vision - ACCV 2016 Workshops (Lecture Notes in Computer Science). Cham, Switzerland: Springer, 2017, pp. 117-133, doi: 10.1007/978-3-319-54526-4_9.",
    # 15 (web: ROSAP record; corporate author, no individual authors listed there)
    "Federal Motor Carrier Safety Administration, \"PERCLOS: A valid psychophysiological measure of alertness as assessed by psychomotor vigilance,\" Tech Brief FHWA-MCRT-98-006, Washington, DC, USA, Oct. 1998.",
    # 16 (web: Crossref)
    "J. A. Stern, D. Boyer, and D. Schroeder, \"Blink rate: A possible measure of fatigue,\" Human Factors, vol. 36, no. 2, pp. 285-297, 1994, doi: 10.1177/001872089403600209.",
    # 17 (web: WHO news release of 13 Dec 2023 quotes 1.19 million deaths, -5 % since 2010, 21 % powered two- and three-wheelers)
    "World Health Organization, \"Global status report on road safety 2023,\" Geneva, Switzerland, Dec. 2023.",
    # 18 (web: NHTSA document page)
    "National Highway Traffic Safety Administration, \"DWI detection and standardized field sobriety testing (SFST) participant manual,\" U.S. Dept. Transportation, Washington, DC, USA, 2023 ed.",
    # 19
    "G. Bradski, \"The OpenCV library,\" Dr. Dobb's Journal of Software Tools, 2000.",
    # 20 (web)
    "C. R. Harris et al., \"Array programming with NumPy,\" Nature, vol. 585, pp. 357-362, Sep. 2020, doi: 10.1038/s41586-020-2649-2.",
    # 21 (web: Crossref)
    "J. D. Hunter, \"Matplotlib: A 2D graphics environment,\" Comput. Sci. Eng., vol. 9, no. 3, pp. 90-95, 2007, doi: 10.1109/MCSE.2007.55.",
    # 22
    "S. Ramirez, \"FastAPI framework, high performance, easy to learn, fast to code, ready for production.\" [Online]. Available: https://fastapi.tiangolo.com",
    # 23
    "Meta Platforms, Inc., \"React: The library for web and native user interfaces.\" [Online]. Available: https://react.dev",
    # 24 (the guide named in the project README)
    "Google AI Edge, \"Face landmarker guide for Python,\" MediaPipe Solutions documentation. [Online]. Available: https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker/python",
    # 25 (web: Crossref)
    "T. Fawcett, \"An introduction to ROC analysis,\" Pattern Recognit. Lett., vol. 27, no. 8, pp. 861-874, Jun. 2006, doi: 10.1016/j.patrec.2005.10.010.",
    # 26 (web: arXiv 2010.16061 / ResearchGate record; page range not confirmed so omitted)
    "D. M. W. Powers, \"Evaluation: From precision, recall and F-measure to ROC, informedness, markedness and correlation,\" J. Mach. Learn. Technol., vol. 2, no. 1, 2011, arXiv:2010.16061.",
    # 27 (web: Crossref)
    "S. Abtahi, M. Omidyeganeh, S. Shirmohammadi, and B. Hariri, \"YawDD: A yawning detection dataset,\" in Proc. 5th ACM Multimedia Syst. Conf. (MMSys), 2014, pp. 24-28, doi: 10.1145/2557642.2563678.",
    # 28 (web: Crossref)
    "Q. Ji, Z. Zhu, and P. Lan, \"Real-time nonintrusive monitoring and prediction of driver fatigue,\" IEEE Trans. Veh. Technol., vol. 53, no. 4, pp. 1052-1068, Jul. 2004, doi: 10.1109/TVT.2004.830974.",
    # 29 (web: PMLR; cited by the base paper for its voice module)
    "A. Radford, J. W. Kim, T. Xu, G. Brockman, C. McLeavey, and I. Sutskever, \"Robust speech recognition via large-scale weak supervision,\" in Proc. Int. Conf. Mach. Learn. (ICML), PMLR vol. 202, 2023, pp. 28492-28518.",
    # 30 (web: Crossref; cited by the base paper for belief rule bases)
    "J.-B. Yang, J. Liu, J. Wang, H.-S. Sii, and H.-W. Wang, \"Belief rule-base inference methodology using the evidential reasoning approach - RIMER,\" IEEE Trans. Syst., Man, Cybern. A, Syst., Humans, vol. 36, no. 2, pp. 266-285, Mar. 2006, doi: 10.1109/TSMCA.2005.851270.",
]

# Short names for readability in the content modules: chapters cite numbers directly via n(1, 9).
BASE, COMPANION, WATCH, DIF = 1, 2, 3, 4
SURVEY_IR, SURVEY_AHFE, SURVEY_ICOEI, SURVEY_THERMAL = 5, 6, 7, 8
EAR_REF, FACEMESH, MEDIAPIPE, CEW_REF, LFW_REF, NTHU, PERCLOS, BLINK = 9, 10, 11, 12, 13, 14, 15, 16
WHO, SFST, OPENCV, NUMPY, MATPLOTLIB, FASTAPI_REF, REACT_REF, LANDMARKER_GUIDE = 17, 18, 19, 20, 21, 22, 23, 24
ROC_REF, PRF_REF, YAWDD, JI2004, WHISPER, RIMER = 25, 26, 27, 28, 29, 30


def n(*nums):
    """Citation string for reference numbers, e.g. n(1, 3) -> '[1], [3]'."""
    return ", ".join(f"[{k}]" for k in nums)


# ---------------------------------------------------------------------------------------------------------------
# WHAT EACH REFERENCE IS USED FOR (guide for the other chapters, decks and the paper)
#  1  Base paper. EAR + head pose + voice fused by a fuzzy belief rule base; EAR-4; NTHU-DDD 4 subjects; Jetson Orin Nano 25 FPS.
#  2  Companion: video-based intoxication detection (GAT landmarks + 3D ResNet), 202 YouTube videos -> 3,542 clips, 95.82 % accuracy.
#     Notes prolonged eye closure / head tilt as intoxication-like cues; DIF source videos no longer reachable.
#  3  Wrist-worn smartwatch drunk-driving detection, N = 54 test-track study, CNN AUROC 0.88 (any alcohol) / 0.86 (> 0.05 g/dL).
#  4  DIF: the earlier intoxicated-face video dataset (audio-visual, from online sources).
#  5  Thermal (FLIR ONE) deep-learning drunk detection, 50 volunteers, 4 levels, NasNetMobile 85.10 % (abstract only).
#  6  Testing methodology for alcohol-intoxication detection systems (IDIADA proving-ground pilot; no numbers in the abstract).
#  7  Taxi alcohol detection + immobilisation (ICOEI 2026). TITLE ONLY: do not quote any result.
#  8  Thermal facial images, sober vs intoxicated, MLP about 90 % accuracy (Tufts Face Database + self-collected images).
#  9  Origin of the eye aspect ratio (EAR) and EAR-based blink detection.
# 10  MediaPipe Face Mesh (468-vertex mesh); the landmark family the project uses.
# 11  MediaPipe framework paper.
# 12  CEW dataset (closed eyes in the wild) used for the EAR evaluation. 13 LFW, source of CEW's open-eye faces.
# 14  NTHU-DDD dataset paper (used by the base paper). 15 PERCLOS (share of time eyes at least 80 % closed) - what 'closed fraction' resembles.
# 16  Blink rate and fatigue. 17 WHO road-safety statistics (1.19 million deaths a year, -5 % since 2010; powered two- and three-wheeler
#     riders 21 % of deaths, pedestrians 23 %, cyclists 6 %). 18 NHTSA SFST manual (police field sobriety tests: gaze nystagmus etc.).
# 19 OpenCV. 20 NumPy. 21 Matplotlib. 22 FastAPI. 23 React. 24 MediaPipe Face Landmarker guide (official).
# 25 ROC/AUC. 26 precision/recall/F1 and chance-corrected measures. 27 YawDD driver yawning dataset.
# 28 Ji et al.: real-time nonintrusive driver fatigue monitoring (eyelid, gaze, head, face pose fusion). 29 Whisper (base paper voice module).
# 30 RIMER belief rule-base (base paper's reasoning method).
# ---------------------------------------------------------------------------------------------------------------
