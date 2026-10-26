"""
Reference list for the SentinelFlow (CSE-C-C15) documents, IEEE style, numbered by list order (REFS[0] is [1]).

Content modules cite entries through CITE['key'] (a number).  REF_NOTES records how each entry was checked: Crossref REST API
(title, authors, venue, volume, pages read this run), the base-paper PDF (Documentary/), the archived PDFs in archived_base_papers/,
or the CICIDS2017 dataset card.  Entries 2, 4 and 5 are items of the batch literature survey (5.LITERATURE SURVEY.docx): their
bibliographic records were verified with Crossref, but no abstract or full text could be read, so their results are never quoted.
Entry 3 has an abstract in Crossref (PeerJ, open access) and is quoted from it.  Italics use *...* markup (rendered by kit.add_runs).
"""

KEYS = [
    "base", "s_ijesat", "s_wisne", "s_ddqn", "s_ijarcce",
    "carpet", "rahman", "cicids", "engelen", "sommer", "mirkovic",
    "breiman", "sklearn", "alashhab", "zaman", "alduailij", "su", "becerra", "hossain",
    "sahoo", "varghese", "musumeci", "braga", "akroma",
    "scapy", "flask", "psutil", "rfc4987", "rfc2827",
]

REFS = [
    # 1 - base paper
    "M. M. Trigui, M. S. Islam, M. D. Gambo, M. S. Alam and T. Helmy, \"Resource-aware ensemble framework for DDoS detection in SDN via novel "
    "game-theoretic feature selection,\" *IEEE Access*, vol. 14, pp. 1666-1676, 2026, doi: 10.1109/ACCESS.2025.3618519.",
    # 2-5 - the batch literature survey
    "S. Areef and G. Vijayasri, \"DDoS attack detection and mitigation,\" *Int. J. Eng. Sci. Adv. Technol.*, vol. 26, no. 4, pp. 115-120, 2026, "
    "doi: 10.64771/ijesat.2026.v26.i6.3198 (record as given by Crossref; abstract not available).",
    "N. Raghavendran and Y. H. Robinson, \"IoT-based WISNE-SDN detection and DDoS attack mitigation using machine learning techniques,\" "
    "*PeerJ Comput. Sci.*, vol. 12, Art. no. e3572, Feb. 2026, doi: 10.7717/peerj-cs.3572.",
    "M. Jadric and S. Mladenovic, \"DDoS attack detection and mitigation using double deep Q-networks,\" in *Proc. 2025 Int. Conf. Software, "
    "Telecommun. Comput. Netw. (SoftCOM)*, Split, Croatia, Sep. 2025, pp. 1-6, doi: 10.23919/SoftCOM66362.2025.11197364.",
    "\"AI-driven DDoS attack detection and mitigation in SDN,\" *IJARCCE*, vol. 14, no. 4, 2025, doi: 10.17148/IJARCCE.2025.144107 "
    "(authors not listed in Crossref; abstract not available).",
    # 6-11 - carpet-bombing, reference paper, dataset, critiques, taxonomy
    "M. N. Swileh, S. Zhang and K. Lei, \"Intelligent detection and mitigation of carpet-bombing DDoS attacks in SDN using retrieval-augmented "
    "generation and large language models,\" arXiv:2605.26307, May 2026.",
    "M. A. Rahman, \"Detection of distributed denial of service attacks based on machine learning algorithms,\" arXiv:2502.00975, Feb. 2025.",
    "I. Sharafaldin, A. Habibi Lashkari and A. A. Ghorbani, \"Toward generating a new intrusion detection dataset and intrusion traffic characterization,\" "
    "in *Proc. 4th Int. Conf. Inf. Syst. Secur. Privacy (ICISSP)*, Funchal, Portugal, Jan. 2018, pp. 108-116, doi: 10.5220/0006639801080116.",
    "G. Engelen, V. Rimmer and W. Joosen, \"Troubleshooting an intrusion detection dataset: The CICIDS2017 case study,\" in *Proc. 2021 IEEE Secur. "
    "Privacy Workshops (SPW)*, May 2021, pp. 7-12, doi: 10.1109/SPW53761.2021.00009.",
    "R. Sommer and V. Paxson, \"Outside the closed world: On using machine learning for network intrusion detection,\" in *Proc. 2010 IEEE Symp. Secur. "
    "Privacy*, 2010, pp. 305-316, doi: 10.1109/SP.2010.25.",
    "J. Mirkovic and P. Reiher, \"A taxonomy of DDoS attack and DDoS defense mechanisms,\" *ACM SIGCOMM Comput. Commun. Rev.*, vol. 34, no. 2, pp. 39-53, "
    "Apr. 2004, doi: 10.1145/997150.997156.",
    # 12-13 - algorithms and software
    "L. Breiman, \"Random forests,\" *Mach. Learn.*, vol. 45, no. 1, pp. 5-32, Oct. 2001, doi: 10.1023/A:1010933404324.",
    "F. Pedregosa *et al.*, \"Scikit-learn: Machine learning in Python,\" *J. Mach. Learn. Res.*, vol. 12, pp. 2825-2830, 2011.",
    # 14-24 - related work on DDoS detection (records verified with Crossref; cited by the base paper)
    "A. A. Alashhab, M. S. Zahid, B. Isyaku, A. A. Elnour, W. Nagmeldin, A. Abdelmaboud, T. A. A. Abdullah and U. D. Maiwada, \"Enhancing DDoS attack "
    "detection and mitigation in SDN using an ensemble online machine learning model,\" *IEEE Access*, vol. 12, pp. 51630-51649, 2024, doi: 10.1109/ACCESS.2024.3384398.",
    "A. Zaman, S. A. Khan, N. Mohammad, A. A. Ateya, S. Ahmad and M. A. ElAffendi, \"Distributed denial of service attack detection in software-defined networks "
    "using decision tree algorithms,\" *Future Internet*, vol. 17, no. 4, p. 136, Mar. 2025, doi: 10.3390/fi17040136.",
    "M. Alduailij, Q. W. Khan, M. Tahir, M. Sardaraz, M. Alduailij and F. Malik, \"Machine-learning-based DDoS attack detection using mutual information and "
    "random forest feature importance method,\" *Symmetry*, vol. 14, no. 6, p. 1095, May 2022, doi: 10.3390/sym14061095.",
    "Y. Su, D. Xiong, K. Qian and Y. Wang, \"A comprehensive survey of distributed denial of service detection and mitigation technologies in software-defined "
    "network,\" *Electronics*, vol. 13, no. 4, p. 807, Feb. 2024, doi: 10.3390/electronics13040807.",
    "F. L. Becerra-Suarez, I. Fernandez-Roman and M. G. Forero, \"Improvement of distributed denial of service attack detection through machine learning and "
    "data processing,\" *Mathematics*, vol. 12, no. 9, p. 1294, Apr. 2024, doi: 10.3390/math12091294.",
    "M. A. Hossain and M. S. Islam, \"Enhancing DDoS attack detection with hybrid feature selection and ensemble-based classifier: A promising solution for "
    "robust cybersecurity,\" *Meas.: Sensors*, vol. 32, Art. no. 101037, Apr. 2024, doi: 10.1016/j.measen.2024.101037.",
    "K. S. Sahoo, B. K. Tripathy, K. Naik, S. Ramasubbareddy, B. Balusamy, M. Khari and D. Burgos, \"An evolutionary SVM model for DDoS attack detection in "
    "software defined networks,\" *IEEE Access*, vol. 8, pp. 132502-132513, 2020, doi: 10.1109/ACCESS.2020.3009733.",
    "J. E. Varghese and B. Muniyal, \"An efficient IDS framework for DDoS attacks in SDN environment,\" *IEEE Access*, vol. 9, pp. 69680-69699, 2021, "
    "doi: 10.1109/ACCESS.2021.3078065.",
    "F. Musumeci, A. C. Fidanci, F. Paolucci, F. Cugini and M. Tornatore, \"Machine-learning-enabled DDoS attacks detection in P4 programmable networks,\" "
    "*J. Netw. Syst. Manage.*, vol. 30, no. 1, Art. no. 21, 2022, doi: 10.1007/s10922-021-09633-5.",
    "R. Braga, E. Mota and A. Passito, \"Lightweight DDoS flooding attack detection using NOX/OpenFlow,\" in *Proc. IEEE 35th Conf. Local Comput. Netw. (LCN)*, "
    "Oct. 2010, pp. 408-415, doi: 10.1109/LCN.2010.5735752.",
    "A. J. Akroma and E. O. K. Mohamed, \"Analysis of DDoS attacks and development of software solutions using machine learning for detection and mitigation,\" "
    "*Bani Waleed Univ. J. Humanities Appl. Sci.*, vol. 10, no. 2, pp. 39-50, Apr. 2025, doi: 10.58916/jhas.v10i2.720.",
    # 25-29 - software and standards used by the product
    "P. Biondi *et al.*, \"Scapy: Interactive packet manipulation program,\" software documentation. [Online]. Available: https://scapy.net",
    "Pallets Projects, \"Flask: A lightweight WSGI web application framework,\" documentation. [Online]. Available: https://flask.palletsprojects.com",
    "G. Rodola, \"psutil: Cross-platform library for retrieving information on running processes and system utilisation,\" software documentation. "
    "[Online]. Available: https://github.com/giampaolo/psutil",
    "W. Eddy, \"TCP SYN flooding attacks and common mitigations,\" IETF, RFC 4987, Aug. 2007.",
    "P. Ferguson and D. Senie, \"Network ingress filtering: Defeating denial of service attacks which employ IP source address spoofing,\" IETF, RFC 2827 (BCP 38), May 2000.",
]

assert len(KEYS) == len(REFS), (len(KEYS), len(REFS))
CITE = {k: i + 1 for i, k in enumerate(KEYS)}

REF_NOTES = {
    "base": "Base paper PDF in Documentary/ (title, authors, date of publication 7 Oct 2025, volume 14, first/last page 1666 and 1676 read from the PDF).",
    "s_ijesat": "Crossref record (authors Shaik Areef, G Vijayasri; vol. 26, issue 4, pages 115-120; DOI as printed there). No abstract; results not quoted.",
    "s_wisne": "Crossref record with abstract (CC BY 4.0, PeerJ): KNN 97 %, XGB 100 % accuracy on a testbed dataset; quoted from the abstract only.",
    "s_ddqn": "Crossref record (authors Mia Jadric, Sasa Mladenovic; SoftCOM 2025, Split, 18-20 Sep 2025, pp. 1-6). No abstract; results not quoted.",
    "s_ijarcce": "Crossref record (vol. 14, issue 4, 5 May 2025; no authors listed). No abstract; results not quoted.",
    "carpet": "archived_base_papers/ PDF (30 pages) read: RAG + FAISS + LLM framework, Mininet + Ryu, hping3 carpet-bombing traffic; Gemma-4-31B-IT accuracy 99.94 %, ~2 s per request.",
    "rahman": "archived_base_papers/ PDF read: SVM 0.971, decision tree 0.827, logistic regression 0.593 accuracy on a CIC dataset sample (Table II).",
    "cicids": "Crossref record; dataset card of the Hugging Face mirror cites this paper.",
    "engelen": "Crossref record (SPW 2021, pp. 7-12).",
    "sommer": "Crossref record (IEEE S&P 2010, pp. 305-316).",
    "mirkovic": "Crossref record (CCR 34(2), pp. 39-53).",
    "breiman": "Crossref record (Mach. Learn. 45(1), pp. 5-32).",
    "sklearn": "Standard citation (JMLR 12, 2825-2830, 2011); not re-checked this run.",
}
