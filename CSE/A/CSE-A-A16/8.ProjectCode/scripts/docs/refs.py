"""
Reference list (IEEE style). Entries 1-27 are published works or software whose bibliographic details are stated in the base paper's own
reference list or were checked on the web; 28-31 are the sources named in the batch literature survey (5.LITERATURE SURVEY.docx) whose
title, year and venue are all that the survey records - their authors and findings were not verified, so no result is quoted from them.
The index in this list is the number used in the text, [n].
"""

REFS = [
    # 1
    "D. T. D. Vo, V. D. Nguyen, T. H. M. Nguyen and M. H. Vo, \"MAG-KD: Mask-guided adaptive gating knowledge distillation for skeleton-based sign "
    "language recognition on edge devices,\" IEEE Access, vol. 14, pp. 54761-54775, 2026, doi: 10.1109/ACCESS.2026.3681176.",
    # 2
    "B. A. Al Abdullah, G. A. Amoudi and H. S. Alghamdi, \"Advancements in sign language recognition: A comprehensive review and future prospects,\" "
    "IEEE Access, vol. 12, pp. 128871-128895, 2024.",
    # 3
    "R. Rastgoo, K. Kiani and S. Escalera, \"Sign language recognition: A deep survey,\" Expert Syst. Appl., vol. 164, Art. no. 113794, Feb. 2021.",
    # 4
    "T. Starner, J. Weaver and A. Pentland, \"Real-time American Sign Language recognition using desk and wearable computer based video,\" "
    "IEEE Trans. Pattern Anal. Mach. Intell., vol. 20, no. 12, pp. 1371-1375, Dec. 1998.",
    # 5
    "N. Pugeault and R. Bowden, \"Spelling it out: Real-time ASL fingerspelling recognition,\" in Proc. IEEE Int. Conf. Comput. Vis. Workshops "
    "(ICCV Workshops), Barcelona, Spain, Nov. 2011, pp. 1114-1119.",
    # 6
    "V. Bheda and D. Radpour, \"Using deep convolutional networks for gesture recognition in American Sign Language,\" 2017, arXiv:1710.06836.",
    # 7
    "Y. LeCun, L. Bottou, Y. Bengio and P. Haffner, \"Gradient-based learning applied to document recognition,\" Proc. IEEE, vol. 86, no. 11, "
    "pp. 2278-2324, Nov. 1998.",
    # 8
    "A. Krizhevsky, I. Sutskever and G. E. Hinton, \"ImageNet classification with deep convolutional neural networks,\" Commun. ACM, vol. 60, no. 6, "
    "pp. 84-90, May 2017.",
    # 9
    "D. Tran, L. Bourdev, R. Fergus, L. Torresani and M. Paluri, \"Learning spatiotemporal features with 3D convolutional networks,\" in Proc. IEEE "
    "Int. Conf. Comput. Vis. (ICCV), Dec. 2015, pp. 4489-4497.",
    # 10
    "J. Carreira and A. Zisserman, \"Quo vadis, action recognition? A new model and the Kinetics dataset,\" in Proc. IEEE Conf. Comput. Vis. "
    "Pattern Recognit. (CVPR), Jul. 2017, pp. 4724-4733.",
    # 11
    "S. Yan, Y. Xiong and D. Lin, \"Spatial temporal graph convolutional networks for skeleton-based action recognition,\" in Proc. AAAI Conf. "
    "Artif. Intell., vol. 32, no. 1, 2018.",
    # 12
    "G. Hinton, O. Vinyals and J. Dean, \"Distilling the knowledge in a neural network,\" 2015, arXiv:1503.02531.",
    # 13
    "C. Lugaresi et al., \"MediaPipe: A framework for building perception pipelines,\" 2019, arXiv:1906.08172.",
    # 14
    "O. M. Sincan and H. Y. Keles, \"AUTSL: A large scale multi-modal Turkish Sign Language dataset and baseline methods,\" IEEE Access, vol. 8, "
    "pp. 181340-181355, 2020.",
    # 15
    "D. Li, C. R. Opazo, X. Yu and H. Li, \"Word-level deep sign language recognition from video: A new large-scale dataset and methods comparison,\" "
    "in Proc. IEEE Winter Conf. Appl. Comput. Vis. (WACV), Mar. 2020, pp. 1448-1458.",
    # 16
    "N. C. Camgoz, S. Hadfield, O. Koller, H. Ney and R. Bowden, \"Neural sign language translation,\" in Proc. IEEE/CVF Conf. Comput. Vis. Pattern "
    "Recognit. (CVPR), Jun. 2018, pp. 7784-7793.",
    # 17
    "N. Otsu, \"A threshold selection method from gray-level histograms,\" IEEE Trans. Syst., Man, Cybern., vol. SMC-9, no. 1, pp. 62-66, Jan. 1979.",
    # 18
    "R. C. Gonzalez and R. E. Woods, Digital Image Processing, 4th ed. New York, NY, USA: Pearson, 2018.",
    # 19
    "S. Ioffe and C. Szegedy, \"Batch normalization: Accelerating deep network training by reducing internal covariate shift,\" in Proc. 32nd Int. "
    "Conf. Mach. Learn. (ICML), 2015, pp. 448-456.",
    # 20
    "N. Srivastava, G. Hinton, A. Krizhevsky, I. Sutskever and R. Salakhutdinov, \"Dropout: A simple way to prevent neural networks from "
    "overfitting,\" J. Mach. Learn. Res., vol. 15, no. 56, pp. 1929-1958, 2014.",
    # 21
    "D. P. Kingma and J. Ba, \"Adam: A method for stochastic optimization,\" in Proc. Int. Conf. Learn. Represent. (ICLR), 2015, arXiv:1412.6980.",
    # 22
    "C. Shorten and T. M. Khoshgoftaar, \"A survey on image data augmentation for deep learning,\" J. Big Data, vol. 6, Art. no. 60, 2019.",
    # 23
    "M. Abadi et al., \"TensorFlow: A system for large-scale machine learning,\" in Proc. 12th USENIX Symp. Oper. Syst. Design Implement. (OSDI), "
    "2016, pp. 265-283.",
    # 24
    "G. Bradski, \"The OpenCV library,\" Dr. Dobb's J. Softw. Tools, 2000.",
    # 25
    "Akash, \"ASL Alphabet,\" Kaggle dataset (grassknoted/asl-alphabet). [Online]. Available: https://www.kaggle.com/datasets/grassknoted/asl-alphabet "
    "(accessed Oct. 2026).",
    # 26
    "F. Chollet et al., \"Keras,\" 2015. [Online]. Available: https://keras.io",
    # 27
    "S. Ramirez, \"FastAPI.\" [Online]. Available: https://fastapi.tiangolo.com (accessed Oct. 2026).",
    # 28-31: named in the batch literature survey; only title, year and venue are recorded there
    "\"Sign language recognition,\" in Sign Language Processing, 2024. (Listed in the project literature survey; authors not recorded there and not verified.)",
    "\"Gesture recognition for sign language with AI,\" 2024. (Listed in the project literature survey; authors and venue not recorded there and not verified.)",
    "\"Implementation of a dynamic gesture recognition based Indian Sign Language,\" i-manager's J. Pattern Recognit., 2024. (Listed in the project "
    "literature survey; authors not recorded there and not verified.)",
    "\"Translation independent gesture recognition system for multilingual sign language,\" 2025. (Listed in the project literature survey; authors and "
    "venue not recorded there and not verified.)",
]
