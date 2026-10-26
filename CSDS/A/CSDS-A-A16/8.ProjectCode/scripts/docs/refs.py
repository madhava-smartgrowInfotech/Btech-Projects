"""
Reference list for the Mosaic (CSDS-A-A16) documents, IEEE style, numbered by list order (REFS[0] is [1]).

Content modules cite entries through CITE['key'] (a number).  REF_NOTES records how each entry was checked:
  - PDF read: the base-paper PDF (Documentary/) or a PDF in archived_base_papers/ was read this run;
  - Crossref: title, authors, venue, volume, pages were read from the Crossref REST API this run (scripts/crossref_check.py);
  - classic: a standard citation written from memory whose pages were not re-fetched.
Entries 3 and 5 are items of the batch literature survey (5.LITERATURE SURVEY.docx): their bibliographic records were verified with
Crossref but no abstract or full text could be read, so their results are never quoted.  Italics use *...* markup (kit.add_runs).
"""

KEYS = [
    "base", "cdgan", "migan", "nstgan", "facecycle",
    "galkaduwa", "abaw7", "su",
    "du2014", "ekman", "fer2013", "rafdb", "ckplus", "affectnet", "lideng",
    "gan", "cgan", "dcgan", "stargan", "ganimation", "fid", "improvedgan",
    "viola", "adam", "bn", "dropout", "multilabel", "pytorch", "opencv", "fastapi", "nextjs",
]

REFS = [
    # 1 - base paper
    "W. S. S. Khine, P. Siritanawan and K. Kotani, \"Complex emotion estimation using analysis-by-synthesis of facial expression images,\" "
    "*IEEE Access*, vol. 13, pp. 88731-88744, 2025, doi: 10.1109/ACCESS.2025.3570167.",
    # 2-5 - the batch literature survey
    "S. Liu, S. Ni and H. Cai, \"Facial expression recognition with contrastive disentangled generative adversarial network,\" *Electronics*, vol. 14, no. 19, "
    "p. 3795, Sep. 2025, doi: 10.3390/electronics14193795.",
    "S. Ni, S. Liu, H. Cai, H. Wang and H. Xiao, \"Facial expression recognition with multi-level integration disentangled generative adversarial network,\" in "
    "*Proc. 2024 IEEE Int. Conf. Ind. Technol. (ICIT)*, 2024, doi: 10.1109/ICIT58233.2024.10540810.",
    "F. Khemakhem and H. Ltifi, \"Neural style transfer generative adversarial network (NST-GAN) for facial expression recognition,\" *Int. J. Multimedia Inf. Retr.*, "
    "vol. 12, no. 2, Art. no. 26, 2023, doi: 10.1007/s13735-023-00285-6.",
    "Y. Zhou, B. Yang, Z. Liu, Q. Wang and P. Xiong, \"Cross-domain facial expression recognition by combining transfer learning and face-cycle generative adversarial network,\" "
    "*Multimedia Tools Appl.*, vol. 83, no. 42, pp. 90289-90314, 2024, doi: 10.1007/s11042-024-18713-y.",
    # 6-8 - papers kept in the batch folder
    "C. Galkaduwa, \"An empirical study of handcrafted feature learning and convolutional neural networks for facial expression recognition,\" arXiv:2607.15288, Jun. 2026.",
    "X. Liu *et al.*, \"Compound expression recognition via multi model ensemble for the ABAW7 challenge,\" arXiv:2407.12257, Jul. 2024.",
    "Y. Su and F. Rosdi, \"A systematic review of deep learning approaches in multimodal emotion recognition,\" *IEEE Access*, May 2026, doi: 10.1109/ACCESS.2026.3694527.",
    # 9-15 - emotion theory, datasets, surveys
    "S. Du, Y. Tao and A. M. Martinez, \"Compound facial expressions of emotion,\" *Proc. Nat. Acad. Sci. USA*, vol. 111, no. 15, pp. E1454-E1462, Apr. 2014, "
    "doi: 10.1073/pnas.1322355111.",
    "P. Ekman and W. V. Friesen, \"Constants across cultures in the face and emotion,\" *J. Personality Social Psychol.*, vol. 17, no. 2, pp. 124-129, 1971, doi: 10.1037/h0030377.",
    "I. J. Goodfellow *et al.*, \"Challenges in representation learning: A report on three machine learning contests,\" *Neural Netw.*, vol. 64, pp. 59-63, 2015, "
    "doi: 10.1016/j.neunet.2014.09.005.",
    "S. Li, W. Deng and J. Du, \"Reliable crowdsourcing and deep locality-preserving learning for expression recognition in the wild,\" in *Proc. IEEE Conf. Comput. Vis. "
    "Pattern Recognit. (CVPR)*, 2017, pp. 2584-2593, doi: 10.1109/CVPR.2017.277.",
    "P. Lucey, J. F. Cohn, T. Kanade, J. Saragih, Z. Ambadar and I. Matthews, \"The extended Cohn-Kanade dataset (CK+): A complete dataset for action unit and emotion-specified "
    "expression,\" in *Proc. IEEE CVPR Workshops*, 2010, pp. 94-101, doi: 10.1109/CVPRW.2010.5543262.",
    "A. Mollahosseini, B. Hasani and M. H. Mahoor, \"AffectNet: A database for facial expression, valence, and arousal computing in the wild,\" *IEEE Trans. Affect. Comput.*, "
    "vol. 10, no. 1, pp. 18-31, 2019, doi: 10.1109/TAFFC.2017.2740923.",
    "S. Li and W. Deng, \"Deep facial expression recognition: A survey,\" *IEEE Trans. Affect. Comput.*, vol. 13, no. 3, pp. 1195-1215, 2022, doi: 10.1109/TAFFC.2020.2981446.",
    # 16-22 - generative models
    "I. Goodfellow *et al.*, \"Generative adversarial nets,\" in *Adv. Neural Inf. Process. Syst. (NIPS)*, vol. 27, 2014, pp. 2672-2680.",
    "M. Mirza and S. Osindero, \"Conditional generative adversarial nets,\" arXiv:1411.1784, Nov. 2014.",
    "A. Radford, L. Metz and S. Chintala, \"Unsupervised representation learning with deep convolutional generative adversarial networks,\" arXiv:1511.06434, Nov. 2015.",
    "Y. Choi, M. Choi, M. Kim, J.-W. Ha, S. Kim and J. Choo, \"StarGAN: Unified generative adversarial networks for multi-domain image-to-image translation,\" in *Proc. IEEE/CVF CVPR*, "
    "2018, pp. 8789-8797, doi: 10.1109/CVPR.2018.00916.",
    "A. Pumarola, A. Agudo, A. M. Martinez, A. Sanfeliu and F. Moreno-Noguer, \"GANimation: One-shot anatomically consistent facial animation,\" *Int. J. Comput. Vis.*, vol. 128, no. 3, "
    "pp. 698-713, 2020, doi: 10.1007/s11263-019-01210-3.",
    "M. Heusel, H. Ramsauer, T. Unterthiner, B. Nessler and S. Hochreiter, \"GANs trained by a two time-scale update rule converge to a local Nash equilibrium,\" in *Adv. Neural Inf. "
    "Process. Syst. (NIPS)*, vol. 30, 2017, pp. 6626-6637.",
    "T. Salimans, I. Goodfellow, W. Zaremba, V. Cheung, A. Radford and X. Chen, \"Improved techniques for training GANs,\" in *Adv. Neural Inf. Process. Syst. (NIPS)*, vol. 29, 2016, pp. 2234-2242.",
    # 23-29 - methods and software
    "P. Viola and M. Jones, \"Rapid object detection using a boosted cascade of simple features,\" in *Proc. IEEE Comput. Soc. Conf. Comput. Vis. Pattern Recognit. (CVPR)*, vol. 1, 2001, pp. I-511-I-518, "
    "doi: 10.1109/CVPR.2001.990517.",
    "D. P. Kingma and J. Ba, \"Adam: A method for stochastic optimization,\" arXiv:1412.6980, Dec. 2014.",
    "S. Ioffe and C. Szegedy, \"Batch normalization: Accelerating deep network training by reducing internal covariate shift,\" in *Proc. 32nd Int. Conf. Mach. Learn. (ICML)*, 2015, pp. 448-456.",
    "N. Srivastava, G. Hinton, A. Krizhevsky, I. Sutskever and R. Salakhutdinov, \"Dropout: A simple way to prevent neural networks from overfitting,\" *J. Mach. Learn. Res.*, vol. 15, "
    "pp. 1929-1958, 2014.",
    "M.-L. Zhang and Z.-H. Zhou, \"A review on multi-label learning algorithms,\" *IEEE Trans. Knowl. Data Eng.*, vol. 26, no. 8, pp. 1819-1837, Aug. 2014, doi: 10.1109/TKDE.2013.39.",
    "A. Paszke *et al.*, \"PyTorch: An imperative style, high-performance deep learning library,\" in *Adv. Neural Inf. Process. Syst. (NeurIPS)*, vol. 32, 2019, pp. 8024-8035.",
    "G. Bradski, \"The OpenCV library,\" *Dr. Dobb's J. Softw. Tools*, vol. 25, no. 11, pp. 120-125, 2000.",
    "S. Ramirez, \"FastAPI: Modern, fast web framework for building APIs with Python,\" software documentation. [Online]. Available: https://fastapi.tiangolo.com",
    "Vercel, Inc., \"Next.js: The React framework for the web,\" software documentation. [Online]. Available: https://nextjs.org",
]

assert len(KEYS) == len(REFS), (len(KEYS), len(REFS))
CITE = {k: i + 1 for i, k in enumerate(KEYS)}

REF_NOTES = {
    "base": "PDF read (Documentary/BASEPAPER_Complex_Emotion_Estimation_Using.pdf): title, authors, volume 13, pages 88731-88744, Tables 2-5 read from page images.",
    "cdgan": "Crossref record (Electronics 14(19), 3795, published 25 Sep 2025); abstract paraphrased from Crossref: separate identity and expression encoders, semi-supervised contrastive learning, results comparable to state of the art. No numbers quoted.",
    "migan": "Crossref record only (ICIT 2024; authors Ni, Liu, Cai, Wang, Xiao). No abstract; results not quoted.",
    "nstgan": "Crossref record (IJMIR 12(2), Art. 26, first online 23 Aug 2023); abstract (publisher page via search): removes identity cues, tested on CK+, FER-2013 and JAFFE, reported to outperform other methods. No numbers quoted.",
    "facecycle": "Crossref record only (MTAP 83(42), pp. 90289-90314). No abstract; results not quoted.",
    "galkaduwa": "PDF read (archived_base_papers/, arXiv 2607.15288): Table VI FER-2013 accuracy HOG+SVM 44.0, LBP+LogReg 25.0, CNN 51.6; CK+ 98.4 / 25.0 / 96.9; KDEF 58.2 / 14.7 / 72.4.",
    "abaw7": "PDF read (archived_base_papers/, arXiv 2407.12257): RAF-DB compound validation Table 1: ViT acc 62.13 / F1 54.23, PosterV2 64.34 / 55.36, ResNet 60.35 / 51.54 over seven compound classes.",
    "su": "PDF read (archived_base_papers/): systematic review of 62 multimodal emotion-recognition studies 2020-2025 (PRISMA); CNNs remain the main visual feature extractor.",
    "du2014": "Reference [6] of the base paper PDF; Crossref record confirms DOI, vol. 111, issue 15.",
    "ekman": "Crossref record (JPSP 17(2), 124-129).",
    "fer2013": "Crossref record (Neural Networks 64, 59-63).",
    "rafdb": "Crossref record (CVPR 2017, pp. 2584-2593).",
    "ckplus": "Crossref record (CVPRW 2010, pp. 94-101).",
    "affectnet": "Crossref record (IEEE TAC 10(1), 18-31).",
    "lideng": "Crossref record (IEEE TAC 13(3), 1195-1215).",
    "stargan": "Crossref record (CVPR 2018, pp. 8789-8797).",
    "ganimation": "Crossref record (IJCV 128(3), 698-713).",
    "viola": "Crossref record (CVPR 2001, vol. 1, I-511 to I-518).",
    "multilabel": "Crossref record (IEEE TKDE 26(8), 1819-1837).",
    "gan": "Classic; pages written from memory (NIPS 27, 2672-2680), not re-fetched.",
    "cgan": "Classic (arXiv 1411.1784); not re-fetched.",
    "dcgan": "Classic (arXiv 1511.06434); not re-fetched.",
    "fid": "Classic (NIPS 30, 6626-6637); also reference [51] of the base paper PDF.",
    "improvedgan": "Classic (NIPS 29, 2234-2242); also reference [49] of the base paper PDF.",
    "adam": "Classic (arXiv 1412.6980); not re-fetched.",
    "bn": "Classic (ICML 2015, 448-456); not re-fetched.",
    "dropout": "Classic (JMLR 15, 1929-1958); not re-fetched.",
    "pytorch": "Classic (NeurIPS 32, 8024-8035); not re-fetched.",
    "opencv": "Classic; not re-fetched.",
    "fastapi": "Software documentation URL; not fetched.",
    "nextjs": "Software documentation URL; not fetched.",
}
