"""
IEEE-style reference list. Every entry is either (a) taken from the base paper's own reference
list (checked against the PDF), (b) a standard, well-known publication, or (c) a title/year pair
recorded in the batch literature survey (authors were not recorded there and are not guessed).
"""

REFS = [
    # 1
    "S. M. Mahin, T. Hasan, S. Karim, M. B. R. Nuha, E. H. Tusher, A. R. Hussain, J. Uddin, and D. Ghose, \"From pneumonia to multi-disease: Interpretable and uncertainty-aware semi-supervised learning strategies for chest X-ray classification,\" IEEE Access, vol. 14, pp. 127532-127551, 2026, doi: 10.1109/ACCESS.2026.3722370.",
    # 2
    "World Health Organization, \"Pneumonia,\" fact sheet, 2024. [Online]. Available: https://www.who.int/news-room/fact-sheets/detail/pneumonia",
    # 3
    "D. S. Kermany et al., \"Identifying medical diagnoses and treatable diseases by image-based deep learning,\" Cell, vol. 172, no. 5, pp. 1122-1131, Feb. 2018.",
    # 4
    "D. Kermany, K. Zhang, and M. Goldbaum, \"Labeled optical coherence tomography (OCT) and chest X-ray images for classification,\" Mendeley Data, v3, 2018, doi: 10.17632/rscbjbr9sj.3.",
    # 5
    "A. O. Khadidos, A. Nanyonga, A. O. Khadidos, O. M. Mirza, and M. T. Yilmaz, \"Explainable deep learning for pediatric pneumonia detection in chest X-ray images,\" arXiv:2601.09814, Jan. 2026.",
    # 6
    "K. Shahi and A. Bagale, \"Weakly supervised pneumonia localization from chest X-rays using deep neural network and Grad-CAM explanations,\" arXiv:2511.00456, 2025.",
    # 7
    "P. Rajpurkar et al., \"CheXNet: Radiologist-level pneumonia detection on chest X-rays with deep learning,\" arXiv:1711.05225, 2017.",
    # 8
    "X. Wang, Y. Peng, L. Lu, Z. Lu, M. Bagheri, and R. M. Summers, \"ChestX-ray8: Hospital-scale chest X-ray database and benchmarks on weakly-supervised classification and localization of common thorax diseases,\" in Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR), Jul. 2017, pp. 3462-3471.",
    # 9
    "R. R. Selvaraju, M. Cogswell, A. Das, R. Vedantam, D. Parikh, and D. Batra, \"Grad-CAM: Visual explanations from deep networks via gradient-based localization,\" Int. J. Comput. Vis., vol. 128, no. 2, pp. 336-359, Feb. 2020.",
    # 10
    "O. Ronneberger, P. Fischer, and T. Brox, \"U-Net: Convolutional networks for biomedical image segmentation,\" in Proc. Med. Image Comput. Comput.-Assist. Intervent. (MICCAI), 2015, pp. 234-241.",
    # 11
    "K. Zuiderveld, \"Contrast limited adaptive histogram equalization,\" in Graphics Gems IV, P. S. Heckbert, Ed. San Diego, CA, USA: Academic Press, 1994, pp. 474-485.",
    # 12
    "A. G. Howard et al., \"MobileNets: Efficient convolutional neural networks for mobile vision applications,\" arXiv:1704.04861, 2017.",
    # 13
    "A. Howard et al., \"Searching for MobileNetV3,\" in Proc. IEEE/CVF Int. Conf. Comput. Vis. (ICCV), Sep. 2019, pp. 1314-1324.",
    # 14
    "K. Sohn et al., \"FixMatch: Simplifying semi-supervised learning with consistency and confidence,\" in Proc. Adv. Neural Inf. Process. Syst., vol. 33, 2020, pp. 596-608.",
    # 15
    "Y. Gal and Z. Ghahramani, \"Dropout as a Bayesian approximation: Representing model uncertainty in deep learning,\" in Proc. Int. Conf. Mach. Learn. (ICML), 2016, pp. 1050-1059.",
    # 16
    "D. P. Kingma and J. Ba, \"Adam: A method for stochastic optimization,\" arXiv:1412.6980, 2014.",
    # 17
    "S. Ioffe and C. Szegedy, \"Batch normalization: Accelerating deep network training by reducing internal covariate shift,\" in Proc. Int. Conf. Mach. Learn. (ICML), 2015, pp. 448-456.",
    # 18
    "N. Srivastava, G. Hinton, A. Krizhevsky, I. Sutskever, and R. Salakhutdinov, \"Dropout: A simple way to prevent neural networks from overfitting,\" J. Mach. Learn. Res., vol. 15, pp. 1929-1958, 2014.",
    # 19
    "M. Abadi et al., \"TensorFlow: A system for large-scale machine learning,\" in Proc. 12th USENIX Symp. Oper. Syst. Design Implement. (OSDI), 2016, pp. 265-283.",
    # 20
    "T. Ozturk, M. Talo, E. A. Yildirim, U. B. Baloglu, O. Yildirim, and U. R. Acharya, \"Automated detection of COVID-19 cases using deep neural networks with X-ray images,\" Comput. Biol. Med., vol. 121, Art. no. 103792, Jun. 2020.",
    # 21
    "L. Wang, Z. Q. Lin, and A. Wong, \"COVID-Net: A tailored deep convolutional neural network design for detection of COVID-19 cases from chest X-ray images,\" Sci. Rep., vol. 10, no. 1, Art. no. 19549, Nov. 2020.",
    # 22
    "F. Alshanketi et al., \"Pneumonia detection from chest X-ray images using deep learning and transfer learning for imbalanced datasets,\" J. Imaging Inform. Med., vol. 38, no. 4, pp. 2021-2040, Nov. 2024.",
    # 23
    "H. Malik, T. Anees, M. Din, and A. Naeem, \"CDC_Net: Multi-classification convolutional neural network model for detection of COVID-19, pneumothorax, pneumonia, lung cancer, and tuberculosis using chest X-rays,\" Multimedia Tools Appl., vol. 82, no. 9, pp. 13855-13880, Apr. 2023.",
    # 24
    "R. Kumar, C.-T. Pan, Y.-M. Lin, S. Yow-Ling, T.-S. Chung, and U. G. S. Janesha, \"Enhanced multi-model deep learning for rapid and precise diagnosis of pulmonary diseases using chest X-ray imaging,\" Diagnostics, vol. 15, no. 3, p. 248, 2025.",
    # 25
    "R. Siddiqi and S. Javaid, \"Deep learning for pneumonia detection in chest X-ray images: A comprehensive survey,\" J. Imaging, vol. 10, no. 8, p. 176, Jul. 2024.",
    # 26
    "M. F. Hashmi, A. A. Husain, D. M. Kotambkar, and K. D. Kumar, \"Hybrid deep learning and handcrafted feature fusion for pneumonia detection in chest X-rays,\" J. Electr. Syst. Inf. Technol., vol. 12, no. 1, p. 94, Nov. 2025.",
    # 27
    "R. Vyas and D. R. Khadatkar, \"Ensemble of deep learning architectures with machine learning for pneumonia classification using chest X-rays,\" J. Imaging Inform. Med., vol. 38, no. 2, pp. 727-746, Aug. 2024.",
    # 28
    "G. Litjens et al., \"A survey on deep learning in medical image analysis,\" Med. Image Anal., vol. 42, pp. 60-88, 2017.",
    # 29
    "C. Guo, G. Pleiss, Y. Sun, and K. Q. Weinberger, \"On calibration of modern neural networks,\" in Proc. Int. Conf. Mach. Learn. (ICML), 2017, pp. 1321-1330.",
    # 30
    "\"Pneumonia detection from chest X-ray images using convolutional neural networks,\" 2025 (entry recorded in the batch literature survey).",
    # 31
    "\"PseudoColorViT-CXR: Colormap-enhanced vision transformers for tuberculosis and pneumonia detection from grayscale chest X-ray images,\" 2025 (entry recorded in the batch literature survey).",
    # 32
    "\"Pneumonia detection using chest X-ray,\" Int. Sci. J. Eng. Manag., 2025 (entry recorded in the batch literature survey).",
    # 33
    "\"Reproducibility and external threshold-transfer audit of transfer-learning CNNs for pediatric chest X-ray pneumonia detection,\" 2026 (entry recorded in the batch literature survey).",
    # 34
    "S. Ramirez, \"FastAPI framework, high performance, easy to learn, fast to code, ready for production.\" [Online]. Available: https://fastapi.tiangolo.com",
    # 35
    "G. Bradski, \"The OpenCV library,\" Dr. Dobb's Journal of Software Tools, 2000.",
    # 36
    "A. Ronacher and Pallets Projects, \"Flask web development, one drop at a time.\" [Online]. Available: https://flask.palletsprojects.com",
    # 37
    "A. Chattopadhay, A. Sarkar, P. Howlader, and V. N. Balasubramanian, \"Grad-CAM++: Generalized gradient-based visual explanations for deep convolutional networks,\" in Proc. IEEE Winter Conf. Appl. Comput. Vis. (WACV), Mar. 2018, pp. 839-847.",
]


def n(*nums):
    """Citation string for reference numbers, e.g. n(1, 3) -> '[1], [3]'."""
    return ", ".join(f"[{k}]" for k in nums)
