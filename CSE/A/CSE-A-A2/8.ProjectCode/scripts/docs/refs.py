"""
Reference list for the ResQAI (CSE-A-A2) documents, IEEE style, numbered by list order (REFS[0] is [1]).

Verification (see REF_NOTES): [1] was read in full from the base-paper PDF; [6] and [7] from the PDFs in archived_base_papers/;
[8]-[12] are the related works GreenBox itself cites (bibliographic data copied from its reference list, no results quoted);
[15]-[19] are copied from the base paper's own reference list; [13] and [14] were checked on the publisher / OpenAlex pages;
[20]-[28] are standard, widely cited papers and standards. [2]-[5] come from the batch literature survey with title, year and source
only: web searches did not locate them, so they carry a "not verified" note and are never cited for a claim.
Italics use *...* markup (rendered by kit.add_runs). Cite from other modules with CITE['key'] (the number).
"""

_ITEMS = [
    ("base", "Y. Wang, Z. Liang and Y. He, \"Multi-Task FT-Transformer: A high-performance and interpretable framework for traffic accident severity prediction,\" "
             "*IEEE Access*, vol. 14, pp. 21585-21606, 2026, doi: 10.1109/ACCESS.2026.3658687."),
    ("survey2", "\"Machine learning-based prediction of road accident severity,\" *Int. J. Res. Publication and Reviews*, 2025. "
                "[Listed in the batch literature survey; authors, volume and pages could not be verified.]"),
    ("survey3", "\"Advancing road safety: Road accident severity prediction using deep learning models,\" in *Proc. IEEE 27th Int. Conf. Intelligent Transportation Systems (ITSC)*, 2024. "
                "[Listed in the batch literature survey; authors and pages could not be verified.]"),
    ("survey4", "\"Avoiding road accidents by improving accident severity prediction rates,\" in *Proc. IEEE 21st India Council Int. Conf. (INDICON)*, 2024. "
                "[Listed in the batch literature survey; authors and pages could not be verified.]"),
    ("survey5", "\"A comprehensive review of machine learning and explainable AI approaches for road accident severity prediction,\" *Iconic Research and Engineering Journals*, 2026. "
                "[Listed in the batch literature survey; authors, volume and pages could not be verified.]"),
    ("greenbox", "J. Rocha, S. Soares, A. Valente and F. C. Pinto, \"GreenBox: Prototyping of an automatic road accident detection system with real-time notification SMS,\" "
                 "arXiv:2606.16468 [eess.SY], Jun. 2026."),
    ("cirs", "S. Ayesha, A. Aslam, M. H. Zaheer and M. B. Khan, \"CIRS: A multi-agent machine learning framework for real-time accident detection and emergency response,\" "
             "*Sensors*, vol. 25, no. 18, Art. no. 5845, Sep. 2025, doi: 10.3390/s25185845."),
    ("dashora", "C. Dashora, P. E. Sudhagar and J. Marietta, \"IoT based framework for the detection of vehicle accident,\" *Cluster Comput.*, vol. 23, no. 2, pp. 1235-1250, 2020."),
    ("karthik", "M. Karthik, L. Sreevidya, K. Vinodha, M. Thangaraj, G. Hemalatha and T. Viswak Sena, \"Automatic messaging system by detecting the road accidents for vehicle applications,\" "
                "*Mater. Today: Proc.*, vol. 80, pp. 3124-3128, 2023."),
    ("anilkumar", "M. Anil Kumar, M. Venkata Suman, Y. Misra and M. Geetha Pratyusha, \"Intelligent vehicle black box using IoT,\" *Int. J. Eng. Technol.*, vol. 7, no. 2.7, pp. 215-218, Mar. 2018."),
    ("uma", "S. Uma and R. Eswari, \"Accident prevention and safety assistance using IoT and machine learning,\" *J. Reliable Intell. Environ.*, vol. 8, no. 2, pp. 79-103, Jun. 2022."),
    ("sharma", "S. Sharma and S. Sebastian, \"IoT based car accident detection and notification algorithm for general road accidents,\" *Int. J. Elect. Comput. Eng. (IJECE)*, vol. 9, no. 5, pp. 4020-4026, 2019."),
    ("hamdan", "N. Hamdan and T. Sipos, \"Advancements in machine learning for traffic accident severity prediction: A comprehensive review,\" "
               "*Period. Polytech. Transp. Eng.*, vol. 53, no. 3, pp. 347-355, 2025, doi: 10.3311/PPtr.40369."),
    ("pei", "Y. Pei, Y. Wen and S. Pan, \"Road traffic accident risk prediction and key factor identification framework based on explainable deep learning,\" "
            "*IEEE Access*, vol. 12, pp. 120597-120611, 2024, doi: 10.1109/ACCESS.2024.3451522."),
    ("lin", "C. Lin, D. Wu, H. Liu, X. Xia and N. Bhattarai, \"Factor identification and prediction for teen driver crash severity using machine learning: A case study,\" *Appl. Sci.*, vol. 10, no. 5, p. 1675, Mar. 2020."),
    ("chen", "M.-M. Chen and M.-C. Chen, \"Modeling road accident severity with comparisons of logistic regression, decision tree and random forest,\" *Information*, vol. 11, no. 5, p. 270, May 2020."),
    ("sameen", "M. Sameen and B. Pradhan, \"Severity prediction of traffic accidents with recurrent neural networks,\" *Appl. Sci.*, vol. 7, no. 6, p. 476, Jun. 2017."),
    ("zheng", "M. Zheng, T. Li, R. Zhu, J. Chen, Z. Ma, M. Tang, Z. Cui and Z. Wang, \"Traffic accident's severity prediction: A deep-learning approach-based CNN network,\" *IEEE Access*, vol. 7, pp. 39897-39910, 2019."),
    ("gorishniy", "Y. Gorishniy, I. Rubachev, V. Khrulkov and A. Babenko, \"Revisiting deep learning models for tabular data,\" in *Proc. Adv. Neural Inf. Process. Syst.*, vol. 34, Dec. 2021, pp. 18932-18943."),
    ("kendall", "A. Kendall, Y. Gal and R. Cipolla, \"Multi-task learning using uncertainty to weigh losses for scene geometry and semantics,\" in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)*, Jun. 2018, pp. 7482-7491."),
    ("breiman", "L. Breiman, \"Random forests,\" *Mach. Learn.*, vol. 45, no. 1, pp. 5-32, Oct. 2001."),
    ("sklearn", "F. Pedregosa *et al.*, \"Scikit-learn: Machine learning in Python,\" *J. Mach. Learn. Res.*, vol. 12, pp. 2825-2830, 2011."),
    ("smote", "N. V. Chawla, K. W. Bowyer, L. O. Hall and W. P. Kegelmeyer, \"SMOTE: Synthetic minority over-sampling technique,\" *J. Artif. Intell. Res.*, vol. 16, pp. 321-357, 2002."),
    ("shap", "S. M. Lundberg and S.-I. Lee, \"A unified approach to interpreting model predictions,\" in *Proc. Adv. Neural Inf. Process. Syst.*, vol. 30, 2017, pp. 4765-4774."),
    ("haversine", "R. W. Sinnott, \"Virtues of the haversine,\" *Sky and Telescope*, vol. 68, no. 2, p. 159, 1984."),
    ("who", "World Health Organization, *Global Status Report on Road Safety 2023*. Geneva, Switzerland: WHO, Dec. 2023."),
    ("scrypt", "C. Percival and S. Josefsson, \"The scrypt password-based key derivation function,\" IETF RFC 7914, Aug. 2016."),
    ("react", "Meta Platforms, Inc., \"React: A JavaScript library for building user interfaces,\" software, 2013-2026. [Online]. Available: https://react.dev"),
]

REFS = [t for _, t in _ITEMS]
CITE = {k: i + 1 for i, (k, _) in enumerate(_ITEMS)}
NOT_VERIFIED = ["survey2", "survey3", "survey4", "survey5"]   # never cite these for a claim

REF_NOTES = {
    "base": "Read in full from the base-paper PDF (22 pages): 30,442 Dongguan crash records (19,483 / 4,871 / 6,088), accuracy 70.31 % / 90.38 % / 80.79 % for injury, fatal and property-loss severity. Pages 21585-21606.",
    "survey2-5": "Listed in 5.LITERATURE SURVEY.docx (title, year, source). Web searches (Oct 2026) did not locate any of the four; they are listed with a not-verified note and are not cited for any claim.",
    "greenbox-cirs": "Read in archived_base_papers/. GreenBox reports no accuracy or latency numbers (qualitative 'SMS in a matter of seconds'); CIRS reports YOLOv11 top-1 accuracy 86.5 %, precision 0.866, recall 0.856, F1 0.861 on 5,200 + 4,800 camera frames.",
    "dashora-sharma": "Bibliographic data copied from the reference list of GreenBox [6] (its refs 13-17). Only their approach (accelerometer / GSM / GPS alert) is described; no results are quoted.",
    "hamdan-pei": "Checked on the publisher page (Periodica Polytechnica) and on OpenAlex (IEEE Access 12:120597-120611). Hamdan and Sipos is a review with no numeric results in its abstract.",
    "lin-zheng": "Bibliographic data copied from the base paper's own reference list ([27], [28], [31], [32], [47], [53]); the figures quoted for them in the text (73.76 % RNN, 83.2 % SVM) are those the base paper states.",
    "standard": "Breiman, scikit-learn, SMOTE, SHAP, haversine, WHO report, scrypt RFC, React: standard sources whose bibliographic data are well established; only their method is used.",
}
