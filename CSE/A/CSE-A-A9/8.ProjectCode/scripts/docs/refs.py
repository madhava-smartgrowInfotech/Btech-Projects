"""
Reference list for the BotGraph (CSE-A-A9) documents, IEEE style, numbered by list order (REFS[0] is [1]).

Other modules cite entries through CITE['key'] (key -> number). The key list below is a fixed contract:
  base rabot hwgnn lgb botdgt bottgcl msgs gcn gat sage louvain snap adam pytorch sklearn networkx cresci ferrara
  twibot20 botrgcn twibot22 prufer dropout elu gradxinput smote fastapi sqlalchemy jwt bcrypt insta twitter
  sharma adaptgn arabic stackmeta
REF_NOTES records how each entry was checked. The three batch-survey items adaptgn, arabic and stackmeta could not be verified and
are never cited for a claim or a number anywhere in the documents.
Italics use *...* markup (rendered by kit.add_runs).
"""

KEYS = [
    "base", "rabot", "hwgnn", "lgb", "botdgt", "bottgcl", "msgs", "gcn", "gat", "sage",
    "louvain", "snap", "adam", "pytorch", "sklearn", "networkx", "cresci", "ferrara", "twibot20", "botrgcn",
    "twibot22", "prufer", "dropout", "elu", "gradxinput", "smote", "fastapi", "sqlalchemy", "jwt", "bcrypt",
    "insta", "twitter", "sharma", "adaptgn", "arabic", "stackmeta",
]

REFS = [
    # 1 base paper
    "A. Saha, N. K. Sarkar and S. Pratihar, \"PruferNET: An augmented graph neural network for influential node detection in social networks,\" "
    "*IEEE Access*, vol. 14, pp. 79940-79959, 2026, doi: 10.1109/ACCESS.2026.3695637.",
    # 2 RABot
    "L. Zhang, X. Wang, H. Du, Y. Xu, Z. Liu and Y. Liu, \"RABot: Reinforcement-guided graph augmentation for imbalanced and noisy social bot detection,\" "
    "arXiv:2602.21749, Feb. 2026.",
    # 3 HW-GNN
    "Z. Liu, J. Gao, Z. Ji and L. Zhao, \"HW-GNN: Homophily-aware Gaussian-window constrained graph spectral network for social network bot detection,\" "
    "arXiv:2511.22493, Nov. 2025.",
    # 4 LGB
    "M. Zhou, D. Zhang, Y. Wang, Y. Geng, Y. Dong and J. Tang, \"LGB: Language model and graph neural network-driven social bot detection,\" "
    "arXiv:2406.08762, Jun. 2024.",
    # 5 BotDGT
    "B. He, Y. Yang, Q. Wu, H. Liu, R. Yang, H. Peng, X. Wang, Y. Liao and P. Zhou, \"BotDGT: Dynamicity-aware social bot detection with dynamic graph transformers,\" "
    "arXiv:2404.15070, Apr. 2024 (IJCAI 2024 per the arXiv record).",
    # 6 BotTGCL
    "W. Wang, T. Zang and X. Zhang, \"Temporal-aware social bot detection with graph contrastive learning,\" in *Computational Science - ICCS 2025*, Springer, 2025.",
    # 7 MSGS
    "S. Shi, K. Qiao, Z. Wang, J. Yang, B. Song, J. Chen and B. Yan, \"Multi-scale graph neural network with signed-attention for social bot detection: A frequency perspective,\" "
    "arXiv:2307.01968, Jul. 2023.",
    # 8 GCN
    "T. N. Kipf and M. Welling, \"Semi-supervised classification with graph convolutional networks,\" in *Proc. Int. Conf. Learn. Represent. (ICLR)*, 2017, arXiv:1609.02907.",
    # 9 GAT
    "P. Velickovic, G. Cucurull, A. Casanova, A. Romero, P. Lio and Y. Bengio, \"Graph attention networks,\" in *Proc. Int. Conf. Learn. Represent. (ICLR)*, 2018, arXiv:1710.10903.",
    # 10 GraphSAGE
    "W. L. Hamilton, R. Ying and J. Leskovec, \"Inductive representation learning on large graphs,\" in *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 30, 2017, pp. 1024-1034.",
    # 11 Louvain
    "V. D. Blondel, J.-L. Guillaume, R. Lambiotte and E. Lefebvre, \"Fast unfolding of communities in large networks,\" *J. Stat. Mech.: Theory Exp.*, no. 10, p. P10008, 2008.",
    # 12 SNAP circles
    "J. McAuley and J. Leskovec, \"Learning to discover social circles in ego networks,\" in *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 25, 2012, pp. 539-547.",
    # 13 Adam
    "D. P. Kingma and J. Ba, \"Adam: A method for stochastic optimization,\" in *Proc. Int. Conf. Learn. Represent. (ICLR)*, 2015, arXiv:1412.6980.",
    # 14 PyTorch
    "A. Paszke *et al.*, \"PyTorch: An imperative style, high-performance deep learning library,\" in *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 32, 2019, arXiv:1912.01703.",
    # 15 scikit-learn
    "F. Pedregosa *et al.*, \"Scikit-learn: Machine learning in Python,\" *J. Mach. Learn. Res.*, vol. 12, pp. 2825-2830, 2011.",
    # 16 NetworkX
    "A. A. Hagberg, D. A. Schult and P. J. Swart, \"Exploring network structure, dynamics, and function using NetworkX,\" in *Proc. 7th Python in Science Conf. (SciPy)*, 2008, pp. 11-15.",
    # 17 Cresci survey
    "S. Cresci, \"A decade of social bot detection,\" *Commun. ACM*, vol. 63, no. 10, pp. 72-83, Oct. 2020.",
    # 18 Ferrara
    "E. Ferrara, O. Varol, C. Davis, F. Menczer and A. Flammini, \"The rise of social bots,\" *Commun. ACM*, vol. 59, no. 7, pp. 96-104, Jul. 2016.",
    # 19 TwiBot-20
    "S. Feng, H. Wan, N. Wang, J. Li and M. Luo, \"TwiBot-20: A comprehensive Twitter bot detection benchmark,\" in *Proc. 30th ACM Int. Conf. Inf. Knowl. Manag. (CIKM)*, 2021, pp. 4485-4494.",
    # 20 BotRGCN
    "S. Feng, H. Wan, N. Wang and M. Luo, \"BotRGCN: Twitter bot detection with relational graph convolutional networks,\" in *Proc. IEEE/ACM Int. Conf. Adv. Soc. Netw. Anal. Min. (ASONAM)*, 2021, pp. 236-239.",
    # 21 TwiBot-22
    "S. Feng *et al.*, \"TwiBot-22: Towards graph-based Twitter bot detection,\" in *Advances in Neural Information Processing Systems (NeurIPS), Datasets and Benchmarks Track*, vol. 35, 2022.",
    # 22 Prufer
    "H. Prüfer, \"Neuer Beweis eines Satzes über Permutationen,\" *Arch. Math. Phys.*, vol. 27, pp. 142-144, 1918.",
    # 23 Dropout
    "N. Srivastava, G. Hinton, A. Krizhevsky, I. Sutskever and R. Salakhutdinov, \"Dropout: A simple way to prevent neural networks from overfitting,\" *J. Mach. Learn. Res.*, vol. 15, pp. 1929-1958, 2014.",
    # 24 ELU
    "D.-A. Clevert, T. Unterthiner and S. Hochreiter, \"Fast and accurate deep network learning by exponential linear units (ELUs),\" in *Proc. Int. Conf. Learn. Represent. (ICLR)*, 2016, arXiv:1511.07289.",
    # 25 gradient x input
    "A. Shrikumar, P. Greenside, A. Shcherbina and A. Kundaje, \"Not just a black box: Learning important features through propagating activation differences,\" arXiv:1605.01713, 2016.",
    # 26 SMOTE
    "N. V. Chawla, K. W. Bowyer, L. O. Hall and W. P. Kegelmeyer, \"SMOTE: Synthetic minority over-sampling technique,\" *J. Artif. Intell. Res.*, vol. 16, pp. 321-357, 2002.",
    # 27 FastAPI
    "S. Ramírez, \"FastAPI,\" software framework, https://fastapi.tiangolo.com (accessed Oct. 2026).",
    # 28 SQLAlchemy
    "M. Bayer, \"SQLAlchemy,\" in *The Architecture of Open Source Applications, Volume II*, A. Brown and G. Wilson, Eds. 2012.",
    # 29 JWT
    "M. Jones, J. Bradley and N. Sakimura, \"JSON Web Token (JWT),\" IETF RFC 7519, May 2015.",
    # 30 bcrypt
    "N. Provos and D. Mazières, \"A future-adaptable password scheme,\" in *Proc. USENIX Annu. Tech. Conf., FREENIX Track*, 1999, pp. 81-91.",
    # 31 Instagram dataset
    "free4ever1, \"Instagram fake spammer genuine accounts,\" Kaggle dataset, licence CC BY 3.0, https://www.kaggle.com/datasets/free4ever1/instagram-fake-spammer-genuine-accounts (accessed Oct. 2026).",
    # 32 Twitter dataset
    "goyaladi, \"Twitter bot detection dataset,\" Kaggle dataset, licence CC0, https://www.kaggle.com/datasets/goyaladi/twitter-bot-detection-dataset (accessed Oct. 2026).",
    # 33 nearest match to batch survey item 4 (abstract read through the journal page record)
    "J. Sharma and S. Borah, \"Stacking of machine learning classifiers for bot detection using account level data,\" *Int. J. Informatics Commun. Technol. (IJ-ICT)*, "
    "vol. 15, no. 2, pp. 477-487, Jun. 2026, doi: 10.11591/ijict.v15i2.pp477-487 (nearest match to batch survey item 4; the batch title could not be found).",
    # 34-36 batch-survey items that could not be verified
    "\"AdapTGN: An adaptive temporal-relational graph neural network for social media bot detection,\" 2026 (listed in the batch survey; not independently verified).",
    "\"A novel graph neural network approach for social network fake news identification in Arabic,\" in *Proc. 18th Int. Conf. Agents Artif. Intell.*, 2026 "
    "(listed in the batch survey; not independently verified).",
    "\"Social media bot detection using account metadata, advanced feature selection, and stacking,\" *Int. J. Sci. Res. (IJSR)*, 2026 "
    "(listed in the batch survey; not independently verified; see [33] for the nearest match found).",
]

assert len(REFS) == len(KEYS) == 36
CITE = {k: i + 1 for i, k in enumerate(KEYS)}

REF_NOTES = {
    "base": "PDF in Documentary/ read in full (20 pages): title, authors, Prufer/MST method, GraphSAGE settings, 60/20/20 split, Facebook 4,039 nodes / 88,234 edges, Email-Eu-core 986 / 16,064, "
            "99.63 % vs 96.54 % accuracy, T4 GPU. Pages 79940-79959 are the first and last page numbers printed in the PDF (the last page holds author biographies). DOI from the PDF header.",
    "rabot": "Archived PDF read: AAAI-2026 style copyright line, arXiv:2602.21749; Cresci-15, Twibot-20, MGTAB; best-in-paper 99.14 % accuracy / 98.94 % F1 (Cresci-15, RGT backbone).",
    "hwgnn": "Archived PDF read: arXiv:2511.22493, 27 Nov 2025; Peking University authors; five benchmarks (TwiBot-20, TwiBot-22, MGTAB, T-Social, T-Finance); average +4.3 % F1 over baselines.",
    "lgb": "arXiv abstract page fetched: submitted 13 Jun 2024; up to 10.95 % improvement on two real-world datasets. The venue named in the batch survey (Research Digest on Engineering Management and Social Innovations) was NOT confirmed, so only the arXiv preprint is cited.",
    "botdgt": "arXiv abstract page fetched: submitted 23 Apr 2024; comment field names IJCAI 2024.",
    "bottgcl": "ICCS 2025 PDF fetched from iccs-meeting.org and read (title, authors, abstract). Springer volume/pages not on the PDF, so omitted.",
    "msgs": "arXiv abstract page fetched: 5 Jul 2023; title spelled 'Muti-scale' on arXiv, corrected here.",
    "gcn": "Well-known classic (ICLR 2017, arXiv:1609.02907); cited from memory of the arXiv record.",
    "gat": "Well-known classic (ICLR 2018, arXiv:1710.10903); cited from memory.",
    "sage": "Well-known classic (NeurIPS 2017, pp. 1024-1034); cited from memory.",
    "louvain": "Well-known classic (J. Stat. Mech. 2008 P10008); cited from memory. networkx.community.louvain_communities implements it.",
    "snap": "The Facebook ego-network data come from this work (SNAP); the project uses a Kaggle mirror (dhruvb2028/social-circles-facebook). Cited from memory (NIPS 2012, vol. 25, pp. 539-547).",
    "adam": "Well-known classic; the project trains every model with Adam (lr 0.01).",
    "pytorch": "NeurIPS 2019; arXiv:1912.01703; cited from memory.",
    "sklearn": "JMLR 12:2825-2830, 2011; used for the metrics and the threshold search.",
    "networkx": "SciPy 2008 proceedings, pp. 11-15; cited from memory. Louvain is called through NetworkX 3.x.",
    "cresci": "Commun. ACM 63(10):72-83, 2020; cited by RABot's introduction (seen in the archived PDF); venue and pages from memory.",
    "ferrara": "Commun. ACM 59(7):96-104, 2016; cited by RABot's introduction (seen in the archived PDF); venue and pages from memory.",
    "twibot20": "CIKM 2021 pp. 4485-4494; named as the dataset of Feng et al. in the RABot and HW-GNN PDFs; venue and pages from memory. WEAK on page numbers.",
    "botrgcn": "ASONAM 2021 pp. 236-239; named as Feng et al. 2021b in the RABot PDF; venue and pages from memory. WEAK on page numbers.",
    "twibot22": "NeurIPS 2022 Datasets and Benchmarks; named as Feng et al. 2022b in the HW-GNN PDF; cited from memory.",
    "prufer": "Pruefer's 1918 note, as cited as [19] in the base paper; journal details from memory.",
    "dropout": "JMLR 15:1929-1958, 2014; classic; dropout 0.3 is used in every model.",
    "elu": "ICLR 2016, arXiv:1511.07289; ELU is the activation used in ml/gnn.py.",
    "gradxinput": "arXiv:1605.01713 (Shrikumar et al.); the 'gradient x input' attribution used for the account explanations is described there; cited from memory.",
    "smote": "JAIR 16:321-357, 2002; classic reference for class-imbalance oversampling (not used by BotGraph, which uses class-weighted loss).",
    "fastapi": "Software, no formal paper; cited as a software reference.",
    "sqlalchemy": "Book chapter; from memory.",
    "jwt": "RFC 7519; from memory.",
    "bcrypt": "USENIX 1999 FREENIX; from memory.",
    "insta": "Dataset record as given in docs/02_HOW_IT_WORKS.md; licence CC BY 3.0 as recorded there.",
    "twitter": "Dataset record as given in docs/02_HOW_IT_WORKS.md; licence CC0 as recorded there.",
    "sharma": "Web search record: IJ-ICT vol. 15 no. 2, June 2026, pp. 477-487, DOI 10.11591/ijict.v15i2.pp477-487; reported RF 89 %, stacked 90 %. Only the web-search summary was read, not the paper; the authors' initials are from that summary. It is the nearest match to batch survey item 4 (title and journal differ). Not cited for any claim in the documents beyond its existence.",
    "adaptgn": "Web search found no page under this title: NOT VERIFIED. Listed only because the batch literature survey names it.",
    "arabic": "Not searched beyond the batch listing; NOT VERIFIED.",
    "stackmeta": "Exact title not found in IJSR; NOT VERIFIED (see 'sharma' for the nearest match).",
}
