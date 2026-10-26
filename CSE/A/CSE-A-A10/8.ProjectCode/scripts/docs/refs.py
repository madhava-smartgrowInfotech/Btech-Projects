"""
Reference list for the FlowSense (CSE-A-A10) documents, IEEE style, numbered by list order (REFS[0] is [1]).

Content modules cite entries through CITE['key'] (a number).  REF_NOTES records how each entry was checked: Crossref REST API
(title, authors, venue, volume, pages read this run), the base-paper PDF reference list, or the archived arXiv PDFs in this batch.
Entries 2-5 are the batch literature survey (5.LITERATURE SURVEY.docx): their authors/results could not be verified (web search
found no record), so they are listed exactly as the survey gives them and are never quoted for numbers.
Italics use *...* markup (rendered by kit.add_runs).
"""

KEYS = [
    "base", "s_signaliq", "s_cisct", "s_i2itcon", "s_incip", "astm", "necdm", "gasgd",
    "sasikala", "zlatkovic", "prajwal", "chowdhury", "giordano", "jayakumar",
    "phuong", "khalili", "fahim", "suhana", "satyanarayana", "sharma",
    "yolo", "ultralytics", "coco", "sumo", "webster", "varaiya", "intellilight",
    "gbm", "rf", "sklearn", "hcm", "ds_traffic", "ds_ambulance",
]

REFS = [
    # 1 - base paper
    "M. Lamrabet, M. Alami Chentoufi and R. Ellaia, \"Emergency-aware adaptive traffic signal control using YOLO-based light-bar detection and "
    "SUMO system-level validation,\" *IEEE Access*, vol. 14, pp. 104922-104933, 2026, doi: 10.1109/ACCESS.2026.3710015.",
    # 2-5 - the batch literature survey (authors not verified)
    "\"Signal-IQ: an integrated, low-cost, and hardware-validated adaptive traffic signal control system using YOLOv8-based vehicle and "
    "emergency-vehicle detection,\" 2026 (as listed in the batch literature survey; authors and venue not verified).",
    "\"Adaptive traffic signal control system for vehicle detection and traffic density estimation,\" in *Proc. 4th Int. Conf. Innovative "
    "Sustainable Computational Technologies (CISCT)*, 2024 (as listed in the batch literature survey; authors not verified).",
    "\"Accelerated emergency vehicle detection and intelligent traffic signal control,\" in *Proc. Int. Conf. Information, Implementation, and "
    "Innovation in Technology (I2ITCON)*, 2025 (as listed in the batch literature survey; authors not verified).",
    "\"Intelligent traffic management system using real-time vehicle detection and dynamic signal control with client-server architecture,\" in "
    "*Proc. Int. Conf. Next Generation Communication & Information Processing (INCIP)*, 2025 (as listed in the batch literature survey; authors not verified).",
    # 6-8 - companion / archived papers
    "C. R. Goenawan, \"ASTM: Autonomous smart traffic management system using artificial intelligence CNN and LSTM,\" arXiv:2410.10929, 2024.",
    "K. Gupta, D. Saxena, A. K. Singh and C.-N. Lee, \"Neighbor-embedded graph neural network-based crowd delivery traffic management in smart city,\" "
    "*IEEE Trans. Emerg. Topics Comput. Intell.*, vol. 10, no. 3, 2026, arXiv:2608.22555.",
    "M. Lamrabet, R. Ellaia and M. Alami Chentoufi, \"Simulation-based optimization of traffic signals using a hybrid GA-SGD approach: a case study of "
    "Morocco,\" *Innov. Infrastruct. Solutions*, vol. 10, no. 11, p. 511, Nov. 2025, doi: 10.1007/s41062-025-02319-w.",
    # 9-14 - emergency pre-emption: IoT / connected vehicle / acoustic (as cited in the base paper)
    "N. Sasikala, S. Sridhar, S. H. Reddy, S. John and S. Shrinikethan, \"Emergency traffic prioritization system with priority-based dynamic route "
    "optimization and IoT-enabled dynamic signal control,\" in *Proc. 5th Int. Conf. Intell. Technol. (CONIT)*, Jun. 2025, pp. 1-5, doi: 10.1109/CONIT65521.2025.11166819.",
    "M. Zlatkovic, Z. Cvijovic, A. Stevanovic and Y. Song, \"Concepts of signal control preemption for emergency vehicles in connected vehicle "
    "environments,\" *J. Road Traffic Eng.*, vol. 69, no. 2, pp. 1-7, Jun. 2023, doi: 10.31075/pis.69.02.01.",
    "V. Prajwal, I. Rahul, S. A. A and M. Chayadevi, \"Increasing emergency response time: a smart GPS and IoT-based approach for ambulance "
    "optimization,\" in *Proc. 2nd Int. Conf. Adv. Inf. Technol. (ICAIT)*, Jul. 2024, pp. 1-5, doi: 10.1109/ICAIT61638.2024.10690489.",
    "A. Chowdhury, S. Kaisar, M. E. Khoda, R. Naha, M. A. Khoshkholghi and M. Aiash, \"IoT-based emergency vehicle services in intelligent "
    "transportation system,\" *Sensors*, vol. 23, no. 11, p. 5324, Jun. 2023, doi: 10.3390/s23115324.",
    "M. Giordano, S. Giacomelli, C. Rinaldi and F. Graziosi, \"Real-time emergency vehicle siren detection with efficient CNNs on embedded hardware,\" arXiv:2507.01563, 2025.",
    "D. Jayakumar, M. Krishnaiah, S. Kollem, S. Peddakrishna, N. Chandrasekhar and M. Thirupathi, \"Emergency vehicle classification using combined "
    "temporal and spectral audio features with machine learning algorithms,\" *Electronics*, vol. 13, no. 19, p. 3873, Sep. 2024, doi: 10.3390/electronics13193873.",
    # 15-20 - YOLO-based vehicle / emergency vehicle detection (as cited in the base paper)
    "T. V. Phuong, C. Tran, T. Vo, K.-D. Nguyen and N. D. Vo, \"Real-time vehicle detection using surveillance cameras: an empirical evaluation in "
    "Vietnamese traffic scenes,\" in *Proc. 13th Int. Conf. Control, Autom. Inf. Sci. (ICCAIS)*, Nov. 2024, pp. 1-6, doi: 10.1109/ICCAIS63750.2024.10814528.",
    "B. Khalili and A. W. Smyth, \"SOD-YOLOv8 - enhancing YOLOv8 for small object detection in traffic scenes,\" arXiv:2408.04786, 2024.",
    "S. A. Fahim, \"Finetuning YOLOv9 for vehicle detection: deep learning for intelligent transportation systems in Dhaka, Bangladesh,\" arXiv:2410.08230, 2024.",
    "S. Suhana, B. Prathap Rudra, K. Narang and I. Anto, \"IoT based emergency vehicle detection using YOLOv8,\" *J. Autom., Mobile Robot. Intell. Syst.*, "
    "vol. 19, no. 2, pp. 79-88, Jun. 2025, doi: 10.14313/jamris-2025-018.x.",
    "K. N. V. Satyanarayana, R. G. Prasanna, R. R. K. S. Satwik, P. Rupchand, P. Srihaas and S. Bhuvanapriya, \"Smart traffic management for emergency "
    "vehicles using YOLOv8 algorithm,\" in *Advances in Computational Intelligence and Robotics*, Hershey, PA, USA: IGI Global, 2025, pp. 491-510, doi: 10.4018/979-8-3693-9375-8.ch029.",
    "V. Sharma, A. A. Shah and M. Makwana, \"Traffic categorization with emergency vehicle identification using YOLOv5,\" in *Proc. 8th Int. Conf. "
    "Comput. Methodologies Commun. (ICCMC)*, Jul. 2025, pp. 1779-1784, doi: 10.1109/ICCMC65190.2025.11140676.",
    # 21-23 - detection tools and data
    "J. Redmon, S. Divvala, R. Girshick and A. Farhadi, \"You only look once: unified, real-time object detection,\" in *Proc. IEEE Conf. Comput. Vis. "
    "Pattern Recognit. (CVPR)*, Las Vegas, NV, USA, Jun. 2016, pp. 779-788, doi: 10.1109/CVPR.2016.91.",
    "G. Jocher, A. Chaurasia and J. Qiu, \"Ultralytics YOLOv8,\" version 8.0.0, 2023. [Online]. Available: https://github.com/ultralytics/ultralytics",
    "T.-Y. Lin *et al.*, \"Microsoft COCO: common objects in context,\" in *Computer Vision - ECCV 2014*, Lecture Notes in Computer Science, Springer, 2014, pp. 740-755, doi: 10.1007/978-3-319-10602-1_48.",
    # 24-27 - traffic control and simulation
    "P. A. Lopez *et al.*, \"Microscopic traffic simulation using SUMO,\" in *Proc. 21st IEEE Int. Conf. Intell. Transp. Syst. (ITSC)*, Maui, HI, USA, Nov. 2018, pp. 2575-2582, doi: 10.1109/ITSC.2018.8569938.",
    "F. V. Webster, \"Traffic signal settings,\" Road Research Technical Paper No. 39, Road Research Laboratory, HMSO, London, U.K., 1958.",
    "P. Varaiya, \"Max pressure control of a network of signalized intersections,\" *Transp. Res. C, Emerg. Technol.*, vol. 36, pp. 177-195, Nov. 2013, doi: 10.1016/j.trc.2013.08.014.",
    "H. Wei, G. Zheng, H. Yao and Z. Li, \"IntelliLight: a reinforcement learning approach for intelligent traffic light control,\" in *Proc. 24th ACM SIGKDD Int. Conf. "
    "Knowl. Discovery Data Mining*, London, U.K., Jul. 2018, pp. 2496-2505, doi: 10.1145/3219819.3220096.",
    # 28-31 - machine learning and standards
    "J. H. Friedman, \"Greedy function approximation: a gradient boosting machine,\" *Ann. Statist.*, vol. 29, no. 5, pp. 1189-1232, Oct. 2001, doi: 10.1214/aos/1013203451.",
    "L. Breiman, \"Random forests,\" *Mach. Learn.*, vol. 45, no. 1, pp. 5-32, Oct. 2001, doi: 10.1023/A:1010933404324.",
    "F. Pedregosa *et al.*, \"Scikit-learn: machine learning in Python,\" *J. Mach. Learn. Res.*, vol. 12, pp. 2825-2830, 2011.",
    "Transportation Research Board, *Highway Capacity Manual: A Guide for Multimodal Mobility Analysis*, 6th ed. Washington, DC, USA: National Academies Press, 2016.",
    # 32-33 - public datasets used for the real-image evaluation
    "Visaitech, \"Visaitech mixed-traffic vehicle detection dataset (v0.1),\" Hugging Face, CC BY 4.0. [Online]. Available: https://huggingface.co/datasets/visaitech/vehicle-mixed-traffic-detection",
    "shravya11, \"Ambulance classification dataset (ambulance / no-ambulance images),\" Hugging Face, CC BY 4.0. [Online]. Available: https://huggingface.co/datasets/shravya11/ambulance-images",
]

assert len(KEYS) == len(REFS), (len(KEYS), len(REFS))
CITE = {k: i + 1 for i, k in enumerate(KEYS)}

REF_NOTES = {
    "base": "Read in full from Documentary/BASEPAPER_*.pdf (12 pages); Crossref 10.1109/ACCESS.2026.3710015 confirms title, three authors, vol. 14, pp. 104922-104933, 2026.",
    "s_signaliq": "Batch survey item 2 (2026). Web search found no record of this title; authors, venue and results NOT verified; never quoted for numbers.",
    "s_cisct": "Batch survey item 3 (2024). Web search found no exact record; authors NOT verified; never quoted for numbers.",
    "s_i2itcon": "Batch survey item 4 (2025). Web search found no exact record; authors NOT verified; never quoted for numbers.",
    "s_incip": "Batch survey item 5 (2025). Web search found no exact record; authors NOT verified; never quoted for numbers.",
    "astm": "Read from archived_base_papers/REFERENCE_PAPER_ASTM_*.pdf (8 pages): YOLOv5 detection, RNN-LSTM 12-hour vehicle count forecast (MSE 4.521, RMSE 2.232), CARLA simulation: 21 vs ~15 vehicles/min and 5 s vs ~12 s pass delay.",
    "necdm": "Read the first page of archived_base_papers/BASEPAPER_Neighbor_embedded_*.pdf: NeCDM, GNN congestion prediction for crowd delivery; reductions up to 4.03 % L1, 16.66 % L2 loss, 7.64 % computation time. Archived second candidate base paper.",
    "gasgd": "Crossref 10.1007/s41062-025-02319-w: Innovative Infrastructure Solutions vol. 10 no. 11, published 24 Oct 2025 (the base paper's reference [1] gives p. 511, Nov. 2025).",
    "sasikala": "Crossref 10.1109/CONIT65521.2025.11166819 confirms authors and title; base paper reports a 35 % ambulance response-time reduction for it.",
    "zlatkovic": "Entry copied from the base paper's reference list [3] (not re-fetched); base paper reports up to 36 % emergency delay reduction in VISSIM.",
    "prajwal": "Entry copied from the base paper's reference list [4]; Crossref DOI not re-fetched.",
    "chowdhury": "Entry copied from the base paper's reference list [5].",
    "giordano": "Entry copied from the base paper's reference list [6] (arXiv:2507.01563).",
    "jayakumar": "Entry copied from the base paper's reference list [7]; base paper reports 99.5 % accuracy with SVM and ensembles.",
    "phuong": "Entry copied from the base paper's reference list [9].",
    "khalili": "Entry copied from the base paper's reference list [10] (arXiv:2408.04786).",
    "fahim": "Entry copied from the base paper's reference list [11] (arXiv:2410.08230).",
    "suhana": "Entry copied from the base paper's reference list [16].",
    "satyanarayana": "Entry copied from the base paper's reference list [18].",
    "sharma": "Entry copied from the base paper's reference list [19].",
    "yolo": "Crossref 10.1109/CVPR.2016.91: authors Redmon, Divvala, Girshick, Farhadi; pp. 779-788; June 2016.",
    "ultralytics": "Software citation in the form Ultralytics asks for (version 8.0.0, 2023); the installed package here is ultralytics 8.4.186 running yolov8n.pt.",
    "coco": "Crossref 10.1007/978-3-319-10602-1_48: Lin, Maire, Belongie, Hays, Perona, Ramanan et al., LNCS (ECCV 2014), pp. 740-755. yolov8n.pt is trained on COCO.",
    "sumo": "Crossref 10.1109/ITSC.2018.8569938: Lopez, Wiessner, Behrisch, Bieker-Walz, Erdmann, Flotterod et al., ITSC 2018, pp. 2575-2582.",
    "webster": "Classic report (Road Research Technical Paper 39, HMSO, 1958); cited from memory of the standard record, not re-fetched; used only to describe fixed-time signal setting.",
    "varaiya": "Crossref 10.1016/j.trc.2013.08.014: Transportation Research Part C vol. 36, pp. 177-195, Nov 2013. The advanced controller's pressure score is pressure-style in spirit only; it is not max-pressure.",
    "intellilight": "Crossref 10.1145/3219819.3220096: Wei, Zheng, Yao, Li; KDD 2018, pp. 2496-2505.",
    "gbm": "Crossref 10.1214/aos/1013203451: Ann. Statist. 29(5), 1189-1232, 2001. The forecaster is scikit-learn's GradientBoostingRegressor.",
    "rf": "Crossref 10.1023/A:1010933404324: Machine Learning 45(1), 5-32, 2001.",
    "sklearn": "JMLR 12:2825-2830, 2011 (well known; cited from memory).",
    "hcm": "Transportation Research Board, Highway Capacity Manual 6th ed., 2016 (source of passenger-car-equivalent practice); cited from memory of the standard record, not re-fetched.",
    "ds_traffic": "Dataset card read this run (293 frames, 1,506 boxes, 4 classes, CC BY 4.0).",
    "ds_ambulance": "Dataset card read this run (2,121 ambulance and 2,628 non-ambulance images, CC BY 4.0).",
}
