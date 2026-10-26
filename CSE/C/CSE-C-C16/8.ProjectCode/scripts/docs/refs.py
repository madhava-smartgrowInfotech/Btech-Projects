"""
Reference list (IEEE style); the position in REFS (1-based) is the number used in the text, [n].

Entries 1-3 were read from the PDFs in the batch folder (Documentary/, archived_base_papers/); entry 4 was read from the arXiv copy of the PlantDoc paper;
21-24 are taken from the reference list of the base paper (entry 1) as printed there. 5-20 are standard, widely cited works whose bibliographic details are
given as recorded by their publishers. Entries 25-28 are the sources named in the batch literature survey (5.LITERATURE SURVEY.docx): only title, year and
venue are recorded there, a web search could not locate them, so their authors and findings are NOT verified, no result is quoted from them and they are
never cited in the IEEE paper.
"""

REFS = [
    # 1 base paper
    "N. Pakka, T. Wilkerson, L. Chen and N.-F. Tzeng, \"Foliagen: Framework for crop foliage image generation from individual leaf images,\" IEEE Access, 2026, "
    "doi: 10.1109/ACCESS.2026.3727421.",
    # 2
    "S. Sherifi, E. Rustemi, S. Ismaili, E. Rufati and F. Idrizi, \"A compact and efficient 1.251 million parameter machine learning CNN model PD36-C for plant "
    "disease detection: A case study,\" arXiv:2604.11332, Apr. 2026.",
    # 3
    "S. Kanakala and S. Ningappa, \"Detection and classification of diseases in multi-crop leaves using LSTM and CNN models,\" J. Innovative Image Processing, "
    "vol. 7, no. 1, pp. 161-181, Mar. 2025, doi: 10.36548/jiip.2025.1.008.",
    # 4
    "D. Singh, N. Jain, P. Jain, P. Kayal, S. Kumawat and N. Batra, \"PlantDoc: A dataset for visual plant disease detection,\" in Proc. 7th ACM IKDD CoDS and "
    "25th COMAD, Hyderabad, India, 2020, pp. 249-253; arXiv:1911.10317.",
    # 5
    "D. P. Hughes and M. Salathe, \"An open access repository of images on plant health to enable the development of mobile disease diagnostics,\" "
    "arXiv:1511.08060, 2015.",
    # 6
    "S. P. Mohanty, D. P. Hughes and M. Salathe, \"Using deep learning for image-based plant disease detection,\" Frontiers in Plant Science, vol. 7, "
    "Art. no. 1419, 2016.",
    # 7
    "K. P. Ferentinos, \"Deep learning models for plant disease detection and diagnosis,\" Computers and Electronics in Agriculture, vol. 145, pp. 311-318, 2018.",
    # 8
    "J. G. A. Barbedo, \"Factors influencing the use of deep learning for plant disease recognition,\" Biosystems Engineering, vol. 172, pp. 84-91, 2018.",
    # 9
    "M. Sandler, A. Howard, M. Zhu, A. Zhmoginov and L.-C. Chen, \"MobileNetV2: Inverted residuals and linear bottlenecks,\" in Proc. IEEE/CVF Conf. Comput. "
    "Vision Pattern Recognit. (CVPR), 2018, pp. 4510-4520.",
    # 10
    "F. Chollet, \"Xception: Deep learning with depthwise separable convolutions,\" in Proc. IEEE Conf. Comput. Vision Pattern Recognit. (CVPR), 2017, pp. 1251-1258.",
    # 11
    "S. Ioffe and C. Szegedy, \"Batch normalization: Accelerating deep network training by reducing internal covariate shift,\" in Proc. 32nd Int. Conf. "
    "Machine Learning (ICML), 2015, pp. 448-456.",
    # 12
    "D. P. Kingma and J. Ba, \"Adam: A method for stochastic optimization,\" in Proc. 3rd Int. Conf. Learning Representations (ICLR), 2015; arXiv:1412.6980.",
    # 13
    "J. Deng, W. Dong, R. Socher, L.-J. Li, K. Li and L. Fei-Fei, \"ImageNet: A large-scale hierarchical image database,\" in Proc. IEEE Conf. Comput. Vision "
    "Pattern Recognit. (CVPR), 2009, pp. 248-255.",
    # 14
    "M. Tan and Q. V. Le, \"EfficientNet: Rethinking model scaling for convolutional neural networks,\" in Proc. 36th Int. Conf. Machine Learning (ICML), 2019, "
    "pp. 6105-6114.",
    # 15
    "K. He, X. Zhang, S. Ren and J. Sun, \"Deep residual learning for image recognition,\" in Proc. IEEE Conf. Comput. Vision Pattern Recognit. (CVPR), 2016, "
    "pp. 770-778.",
    # 16
    "K. Simonyan and A. Zisserman, \"Very deep convolutional networks for large-scale image recognition,\" in Proc. 3rd Int. Conf. Learning Representations "
    "(ICLR), 2015.",
    # 17
    "R. R. Selvaraju, M. Cogswell, A. Das, R. Vedantam, D. Parikh and D. Batra, \"Grad-CAM: Visual explanations from deep networks via gradient-based "
    "localization,\" in Proc. IEEE Int. Conf. Comput. Vision (ICCV), 2017, pp. 618-626.",
    # 18
    "L. Breiman, \"Random forests,\" Machine Learning, vol. 45, no. 1, pp. 5-32, 2001.",
    # 19
    "F. Pedregosa et al., \"Scikit-learn: Machine learning in Python,\" J. Mach. Learn. Res., vol. 12, pp. 2825-2830, 2011.",
    # 20
    "M. Abadi et al., \"TensorFlow: A system for large-scale machine learning,\" in Proc. 12th USENIX Symp. Operating Systems Design and Implementation (OSDI), "
    "2016, pp. 265-283.",
    # 21 (from the base paper's reference list)
    "M. Gehlot, R. K. Saxena and G. C. Gandhi, \"Tomatovillage: A dataset for end-to-end tomato disease detection in a real-world environment,\" "
    "Multimedia Systems, vol. 29, no. 6, pp. 3305-3328, 2023.",
    # 22
    "E. Moupojou, A. Tagne, F. Retraint, A. Tadonkemwa, D. Wilfried, H. Tapamo and M. Nkenlifack, \"FieldPlant: A dataset of field plant images for plant disease "
    "detection and classification with deep learning,\" IEEE Access, vol. 11, pp. 35398-35410, 2023.",
    # 23
    "Q. Wu, X. Ma, H. Liu, C. Bi, H. Yu, M. Liang, J. Zhang, Q. Li, Y. Tang and G. Ye, \"A classification method for soybean leaf diseases based on an improved "
    "ConvNeXt model,\" Scientific Reports, vol. 13, no. 1, Art. no. 19141, 2023.",
    # 24
    "A. Abbas, S. Jain, M. Gour and S. Vankudothu, \"Tomato plant disease detection using transfer learning with C-GAN synthetic images,\" Computers and "
    "Electronics in Agriculture, vol. 187, Art. no. 106279, 2021.",
    # 25-28: named in the batch literature survey, details NOT verified (title, year, venue only)
    "\"Leaf based crop disease detection,\" Int. J. Research Publication and Reviews, 2026. [Listed in the batch literature survey; authors and content not verified.]",
    "\"Explainable CNN framework for accurate crop disease detection using plant leaf images,\" Scientific Reports, 2026. [Listed in the batch literature survey; "
    "authors and content not verified.]",
    "\"AI-driven plant disease detection: Leveraging deep learning for accurate plant disease detection from leaf images,\" Int. J. Science and Research (IJSR), 2024. "
    "[Listed in the batch literature survey; authors and content not verified.]",
    "\"Plant leaf disease detection: Review report,\" Int. J. Science and Research (IJSR), 2025. [Listed in the batch literature survey; authors and content not verified.]",
]

KEY = {"base": 1, "pd36c": 2, "lstm": 3, "plantdoc": 4, "plantvillage": 5, "mohanty": 6, "ferentinos": 7, "barbedo": 8, "mobilenet": 9, "xception": 10, "bn": 11,
       "adam": 12, "imagenet": 13, "efficientnet": 14, "resnet": 15, "vgg": 16, "gradcam": 17, "rf": 18, "sklearn": 19, "tf": 20, "tomatovillage": 21,
       "fieldplant": 22, "convnext": 23, "cgan": 24, "s1": 25, "s2": 26, "s3": 27, "s4": 28}


def cite(*keys):
    return "[" + ", ".join(str(KEY[k]) for k in keys) + "]"
