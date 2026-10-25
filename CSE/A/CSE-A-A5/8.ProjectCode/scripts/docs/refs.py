"""
Reference list for the CipherGuard Shield (CSE-A-A5) documents, IEEE style, numbered by list order (REFS[0] is [1]).

Entries 1-30 are a fixed contract (other modules cite them through CITE['key']); 31-40 are extras added and verified in the
documentation run. REF_NOTES records how each entry was checked (Crossref REST API, OpenAlex API, DataCite, the base-paper PDF
reference list, the archived arXiv PDF) and which ones are weak. Italics use *...* markup (rendered by kit.add_runs).
"""

KEYS = [
    "base", "s_fmdb", "s_ijsr", "s_blowfish", "s_hybrid_gmr", "arxiv", "unsw15", "unsw16", "xgboost", "lenet",
    "stacking", "gcm", "sp80056a", "hkdf", "aes", "oaep", "sklearn", "pytorch", "adam", "kadry",
    "nadeem", "bakro", "mbaya", "rahman", "alrayes", "lin", "alani", "qazi", "hdaib", "vengala",
    # extras (31-40)
    "kasongo", "vinayakumar", "ahmad", "ring", "zoghi", "goldschmidt", "mahalle", "rao", "sudha", "hybrid_ijsea",
]

REFS = [
    # 1 - base paper
    "V. Kalyanasundaram, S. Raja and S. Kanthimathi, \"Intrusion detection model using fused quantum NN-LeNet with improved elliptic curve "
    "cryptography based data security,\" *IEEE Access*, vol. 14, pp. 63767-63779, 2026, doi: 10.1109/ACCESS.2026.3686106.",
    # 2-5 - the batch literature survey (5.LITERATURE SURVEY.docx)
    "H. Boye, \"Strengthening cloud security through advanced encryption and anomaly detection techniques for secure data storage and transmission,\" "
    "*FMDB Trans. Sustain. Comput. Lett.*, vol. 2, no. 3, pp. 153-163, 2024, doi: 10.69888/FTSCL.2024.000241.",
    "J. Singh and G. S. Bhathal, \"An automated data deletion: a secure method for multi-cloud security with intrusion detection system,\" "
    "*Int. J. Sci. Res. (IJSR)*, vol. 13, no. 8, pp. 213-217, Aug. 2024, doi: 10.21275/SR24730194843.",
    "M. B. Shinde and P. P. Ghadekar, \"Federated learning-based attack detection and secure data transmission in cloud using improved Blowfish "
    "encryption,\" *Eng. Appl. Artif. Intell.*, vol. 182, Art. no. 115975, 2026, doi: 10.1016/j.engappai.2026.115975.",
    "N. Pamarthi and N. Rao N, \"A cloud-based data privacy framework using hybrid encryption algorithms for secure data transmission,\" "
    "*Genet. Mol. Res.*, 2026, doi: 10.4238/mq5a9v31.",
    # 6 - archived (ML-half) base paper
    "M. M. Alhusseini, A. Rouhi and M.-R. Feizi-Derakhshi, \"AI-powered hybrid intrusion detection framework for cloud security using novel "
    "metaheuristic optimization,\" arXiv:2601.01134, Jan. 2026.",
    # 7-8 - UNSW-NB15
    "N. Moustafa and J. Slay, \"UNSW-NB15: a comprehensive data set for network intrusion detection systems (UNSW-NB15 network data set),\" in "
    "*Proc. Mil. Commun. Inf. Syst. Conf. (MilCIS)*, Canberra, Australia, 2015, pp. 1-6, doi: 10.1109/MilCIS.2015.7348942.",
    "N. Moustafa and J. Slay, \"The evaluation of network anomaly detection systems: statistical analysis of the UNSW-NB15 data set and the "
    "comparison with the KDD99 data set,\" *Inf. Secur. J.: Global Perspective*, vol. 25, no. 1-3, pp. 18-31, 2016, doi: 10.1080/19393555.2015.1125974.",
    # 9-11 - models
    "T. Chen and C. Guestrin, \"XGBoost: a scalable tree boosting system,\" in *Proc. 22nd ACM SIGKDD Int. Conf. Knowl. Discovery Data Mining*, "
    "San Francisco, CA, USA, 2016, pp. 785-794, doi: 10.1145/2939672.2939785.",
    "Y. LeCun, L. Bottou, Y. Bengio and P. Haffner, \"Gradient-based learning applied to document recognition,\" *Proc. IEEE*, vol. 86, no. 11, "
    "pp. 2278-2324, Nov. 1998, doi: 10.1109/5.726791.",
    "D. H. Wolpert, \"Stacked generalization,\" *Neural Netw.*, vol. 5, no. 2, pp. 241-259, 1992, doi: 10.1016/S0893-6080(05)80023-1.",
    # 12-16 - cryptographic standards
    "M. Dworkin, \"Recommendation for block cipher modes of operation: Galois/Counter Mode (GCM) and GMAC,\" NIST Special Publication 800-38D, "
    "Nov. 2007, doi: 10.6028/NIST.SP.800-38D.",
    "E. Barker, L. Chen, A. Roginsky, A. Vassilev and R. Davis, \"Recommendation for pair-wise key-establishment schemes using discrete logarithm "
    "cryptography,\" NIST Special Publication 800-56A, Rev. 3, Apr. 2018, doi: 10.6028/NIST.SP.800-56Ar3.",
    "H. Krawczyk and P. Eronen, \"HMAC-based extract-and-expand key derivation function (HKDF),\" IETF RFC 5869, May 2010, doi: 10.17487/RFC5869.",
    "National Institute of Standards and Technology, \"Advanced Encryption Standard (AES),\" Federal Information Processing Standards Publication 197, "
    "Nov. 2001 (updated May 2023), doi: 10.6028/NIST.FIPS.197-upd1.",
    "K. Moriarty, B. Kaliski, J. Jonsson and A. Rusch, \"PKCS #1: RSA cryptography specifications version 2.2,\" IETF RFC 8017, Nov. 2016, "
    "doi: 10.17487/RFC8017.",
    # 17-19 - libraries and training method
    "F. Pedregosa et al., \"Scikit-learn: machine learning in Python,\" *J. Mach. Learn. Res.*, vol. 12, pp. 2825-2830, 2011.",
    "A. Paszke et al., \"PyTorch: an imperative style, high-performance deep learning library,\" in *Adv. Neural Inf. Process. Syst. (NeurIPS)*, "
    "vol. 32, 2019, arXiv:1912.01703.",
    "D. P. Kingma and J. Ba, \"Adam: a method for stochastic optimization,\" in *Proc. 3rd Int. Conf. Learn. Represent. (ICLR)*, 2015, arXiv:1412.6980.",
    # 20-30 - related work cited by the base paper
    "H. Kadry, A. Farouk, E. A. Zanaty and O. Reyad, \"Intrusion detection model using optimized quantum neural network and elliptical curve "
    "cryptography for data security,\" *Alexandria Eng. J.*, vol. 71, pp. 491-500, May 2023, doi: 10.1016/j.aej.2023.03.072.",
    "M. Nadeem, A. Arshad, S. Riaz, S. S. Band and A. Mosavi, \"Intercept the cloud network from brute force and DDoS attacks via intrusion "
    "detection and prevention system,\" *IEEE Access*, vol. 9, pp. 152300-152309, 2021, doi: 10.1109/ACCESS.2021.3126535.",
    "M. Bakro, R. R. Kumar, A. A. Alabrah, Z. Ashraf, M. N. Ahmed, M. Shameem and A. Abdelsalam, \"An improved design for a cloud intrusion "
    "detection system using hybrid features selection approach with ML classifier,\" *IEEE Access*, vol. 11, pp. 64228-64247, 2023, "
    "doi: 10.1109/ACCESS.2023.3289405.",
    "E. B. Mbaya, E. Adetiba, J. A. Badejo, J. S. Wejin, O. Oshin and O. Isife, \"SecFedIDM-V1: a secure federated intrusion detection model with "
    "blockchain and deep bidirectional long short-term memory,\" *IEEE Access*, vol. 11, pp. 116011-116025, 2023, doi: 10.1109/ACCESS.2023.3325992.",
    "S. Rahman, S. Pal, S. Mittal, T. Chawla and C. Karmakar, \"SYN-GAN: a robust intrusion detection system using GAN-based synthetic data for "
    "IoT security,\" *Internet Things*, vol. 26, Art. no. 101212, Jul. 2024, doi: 10.1016/j.iot.2024.101212.",
    "F. Alrayes, M. Zakariah, S. Amin, Z. Khan and J. Alqurni, \"Network security enhanced with deep neural network-based intrusion detection "
    "system,\" *Comput. Mater. Continua*, vol. 80, no. 1, pp. 1457-1490, 2024, doi: 10.32604/cmc.2024.051996.",
    "S. Lin, C. Feng, T. Jiang and H. Jing, \"Evaluation of network security grade protection combined with deep learning for intrusion "
    "detection,\" *IEEE Access*, vol. 11, pp. 130990-131000, 2023, doi: 10.1109/ACCESS.2023.3333013.",
    "M. M. Alani, A. I. Awad and E. Barka, \"A hybrid ensemble learning-based intrusion detection system for the Internet of Things,\" in "
    "*Proc. IEEE Int. Conf. Cyber Secur. Resilience (CSR)*, 2024, pp. 1-8, doi: 10.1109/CSR61664.2024.10679427.",
    "E.-U.-H. Qazi, T. Zia, M. H. Faheem, K. Shahzad, M. Imran and Z. Ahmed, \"Zero-touch network security (ZTNS): a network intrusion detection "
    "system based on deep learning,\" *IEEE Access*, vol. 12, pp. 141625-141638, 2024, doi: 10.1109/ACCESS.2024.3466470.",
    "M. Hdaib, S. Rajasegarar and L. Pan, \"Quantum deep learning-based anomaly detection for enhanced network security,\" *Quantum Mach. Intell.*, "
    "vol. 6, no. 1, Art. no. 26, 2024, doi: 10.1007/s42484-024-00163-2.",
    "D. Vengala, D. Kavitha and A. P. S. Kumar, \"Three factor authentication system with modified ECC based secured data transfer: untrusted "
    "cloud environment,\" *Complex Intell. Syst.*, vol. 9, no. 3, pp. 2915-2928, 2023, doi: 10.1007/s40747-021-00305-0.",
    # 31-40 - extras verified in the documentation run
    "S. M. Kasongo and Y. Sun, \"Performance analysis of intrusion detection systems using a feature selection method on the UNSW-NB15 dataset,\" "
    "*J. Big Data*, vol. 7, Art. no. 105, 2020, doi: 10.1186/s40537-020-00379-6.",
    "R. Vinayakumar et al., \"Deep learning approach for intelligent intrusion detection system,\" *IEEE Access*, vol. 7, pp. 41525-41550, 2019, "
    "doi: 10.1109/ACCESS.2019.2895334.",
    "Z. Ahmad et al., \"Network intrusion detection system: a systematic study of machine learning and deep learning approaches,\" *Trans. Emerg. "
    "Telecommun. Technol.*, vol. 32, no. 1, Art. no. e4150, 2021, doi: 10.1002/ett.4150.",
    "M. Ring et al., \"A survey of network-based intrusion detection data sets,\" *Comput. Secur.*, vol. 86, pp. 147-167, Sep. 2019, "
    "doi: 10.1016/j.cose.2019.06.005.",
    "Z. Zoghi and G. Serpen, \"UNSW-NB15 computer security dataset: analysis through visualization,\" arXiv:2101.05067, 2021.",
    "P. Goldschmidt and D. Chuda, \"Network intrusion datasets: a survey, limitations, and recommendations,\" arXiv:2502.06688, 2025.",
    "V. Mahalle and A. Shahade, \"Enhancing the data security in cloud by implementing hybrid (RSA & AES) encryption algorithm,\" in *Proc. Int. Conf. "
    "Power, Autom. Commun. (INPAC)*, 2014, pp. 146-149, doi: 10.1109/INPAC.2014.6981152.",
    "B. Ranganatha Rao and B. Sujatha, \"A hybrid elliptic curve cryptography (HECC) technique for fast encryption of data for public cloud "
    "security,\" *Meas.: Sens.*, vol. 29, Art. no. 100870, Oct. 2023, doi: 10.1016/j.measen.2023.100870.",
    "L. Sudha and C. Arunachalaperumal, \"Optimized hybrid advanced encryption standard and elliptic curve cryptography-based secure data storage "
    "in cloud environment,\" *Iran. J. Sci. Technol., Trans. Electr. Eng.*, vol. 49, no. 3, pp. 1045-1070, 2025, doi: 10.1007/s40998-025-00816-3.",
    "\"Securing data transmission and storage in cloud computing using hybrid AES-256 and RSA encryption and key management technique,\" "
    "*Int. J. Sci. Eng. Appl.*, Mar. 2025, doi: 10.7753/IJSEA1403.1013 (authors not listed in the Crossref or OpenAlex records).",
]

assert len(REFS) == len(KEYS) == 40
CITE = {k: i + 1 for i, k in enumerate(KEYS)}

REF_NOTES = {
    "base": "Opened the PDF in 8.ProjectCode (13 pages); title, authors, volume/pages and DOI checked against the PDF and the Crossref record 10.1109/access.2026.3686106 (IEEE Access, vol. 14, pp. 63767-63779).",
    "s_fmdb": "Crossref 10.69888/ftscl.2024.000241: sole author Harikiran Boye, FMDB Transactions on Sustainable Computer Letters, vol. 2 no. 3, pp. 153-163, 1 Sep 2024. Abstract read via Crossref/OpenAlex. The abstract gives no numeric results ('high accuracy').",
    "s_ijsr": "Crossref 10.21275/sr24730194843 and the IJSR abstract page: Jashanbir Singh and Gurjit Singh Bhathal, IJSR vol. 13 no. 8, pp. 213-217, Aug 2024. Abstract read: a 'brief idea' of an automated data-deletion system triggered by intrusion; no evaluation. A longer companion paper exists (IJCSE vol. 12 no. 7, doi 10.26438/ijcse/v12i7.3340, qualitative study) - not cited.",
    "s_blowfish": "Crossref 10.1016/j.engappai.2026.115975: Madhumati B. Shinde and Premanand P. Ghadekar, Eng. Appl. Artif. Intell. vol. 182, Art. 115975 (issue date 2026-10 in Crossref; OpenAlex gives 2026-08-12 online). WEAK: no abstract could be retrieved (ScienceDirect blocks scripted access, OpenAlex/Crossref carry none), so only the title and venue are verified - do not state its results.",
    "s_hybrid_gmr": "Crossref 10.4238/mq5a9v31: Nagaraju Pamarthi and Nagamalleswara Rao N, Genetics and Molecular Research, 5 Aug 2026; no volume or pages in the record. Abstract read: AES + RSA/MECC with XOR key masking, inputs 2-12 KB, encrypt 2.09 s / decrypt 2.45 s, security score 96. Unusual venue for a computing paper; numbers are the authors' own simulation.",
    "arxiv": "Archived PDF read (18 pages): Alhusseini (Middle Technical University, Baghdad), Rouhi and Feizi-Derakhshi; arXiv:2601.01134, 3 Jan 2026. Summary and numbers in docs/LITERATURE_FACTS.md. It covers the ML half only (no encryption).",
    "unsw15": "Crossref 10.1109/milcis.2015.7348942 (MilCIS 2015, pp. 1-6, N. Moustafa and J. Slay); also cited as [31] in the base paper.",
    "unsw16": "Crossref 10.1080/19393555.2015.1125974: Information Security Journal: A Global Perspective, vol. 25, no. 1-3, pp. 18-31, 11 Jan 2016.",
    "xgboost": "Crossref 10.1145/2939672.2939785 (KDD 2016, pp. 785-794). Crossref lists the title as 'XGBoost'; the full title 'XGBoost: a scalable tree boosting system' is the well-known proceedings title.",
    "lenet": "Crossref 10.1109/5.726791 (Proc. IEEE vol. 86 no. 11, pp. 2278-2324, 1998). The base paper cites a LeNet application paper [27] instead of the original.",
    "stacking": "Crossref 10.1016/s0893-6080(05)80023-1 (Neural Networks vol. 5 no. 2, pp. 241-259, 1992).",
    "gcm": "NIST SP 800-38D, Nov 2007, Morris Dworkin; DOI 10.6028/NIST.SP.800-38D (from memory of the NIST record; not re-fetched in this run - standard document, low risk).",
    "sp80056a": "NIST SP 800-56A Rev. 3, Apr 2018, authors Barker, Chen, Roginsky, Vassilev, Davis; DOI 10.6028/NIST.SP.800-56Ar3 (from memory of the NIST record; not re-fetched).",
    "hkdf": "RFC 5869 (Krawczyk and Eronen, May 2010), DOI 10.17487/RFC5869 (from memory; the HKDF info string used by the code is 'cipherguard-shield-v1').",
    "aes": "FIPS 197; the 2001 original and the May 2023 update (FIPS 197-upd1) share the standard; cited with the update DOI (from memory; not re-fetched).",
    "oaep": "RFC 8017 (PKCS #1 v2.2, Nov 2016; Moriarty, Kaliski, Jonsson, Rusch), DOI 10.17487/RFC8017 (from memory; not re-fetched). Used only to describe the RSA-OAEP benchmark baseline.",
    "sklearn": "JMLR 12:2825-2830, 2011 (well-known; Crossref lookup returned only secondary books, so DOI omitted).",
    "pytorch": "NeurIPS 2019 vol. 32; arXiv:1912.01703 (from memory; Crossref lookup returned only secondary items).",
    "adam": "ICLR 2015; arXiv:1412.6980 (from memory; the project trains the CNN with Adam, lr 1e-3).",
    "kadry": "Crossref 10.1016/j.aej.2023.03.072: real title 'Intrusion detection model using optimized quantum neural network and elliptical curve cryptography for data security' (the base paper shortens it to 'Intrusion detection using optimized QNN and ECC'). Abstract read: WOA-selected features, QNN, ECC; accuracy 98.5%; context is wireless mesh networks.",
    "nadeem": "Crossref 10.1109/access.2021.3126535: real title 'Intercept the cloud network from brute force and DDoS attacks via intrusion detection and prevention system', IEEE Access 9, pp. 152300-152309. The base paper's ref [25] gives a shortened title and authors Nadeem, Arshad, Riaz, Band, Mosavi. Note: the base paper's description of SMOTE/CS/IG/PSO + RF belongs to Bakro et al., not to this paper.",
    "bakro": "Crossref 10.1109/access.2023.3289405, IEEE Access 11, pp. 64228-64247. Abstract read: SMOTE + IG/CS/PSO feature selection + random forest, over 98% (UNSW-NB15) and 99% (Kyoto) multi-class accuracy; the abstract does not state the split protocol.",
    "mbaya": "Crossref 10.1109/access.2023.3325992, IEEE Access 11, pp. 116011-116025. Abstract read: BiLSTM on CIDDS (not UNSW-NB15), Hyperledger Fabric signature store; precision 0.99624, recall 0.99906, FPR 0.00094 for the 80:10:10 BiLSTM.",
    "rahman": "Crossref 10.1016/j.iot.2024.101212: Internet of Things vol. 26, Art. 101212, Jul 2024 (title 'SYN-GAN: a robust intrusion detection system using GAN-based synthetic data for IoT security'). Only the title/venue were read.",
    "alrayes": "Crossref 10.32604/cmc.2024.051996: CMC vol. 80 no. 1, pp. 1457-1490, 2024. Only title/venue read.",
    "lin": "Crossref 10.1109/access.2023.3333013: IEEE Access 11, pp. 130990-131000 (the base paper's reference list also gives 130990-131000). Only title/venue read.",
    "alani": "Crossref 10.1109/csr61664.2024.10679427 (IEEE CSR 2024, pp. 1-8); authors M. Alani, A. Awad, E. Barka. Only title/venue read.",
    "qazi": "Crossref 10.1109/access.2024.3466470: IEEE Access 12, pp. 141625-141638 (DL-NIDS-ZTN, CNN, CICIDS-2018, 99.80% accuracy per the abstract). Co-authors M. Imran and Z. Ahmed taken from the base paper's reference [1] (Crossref lists the first four only in the slice read).",
    "hdaib": "Crossref 10.1007/s42484-024-00163-2: Quantum Mach. Intell. vol. 6 no. 1, Art. 26, 2 May 2024. Only title/venue read.",
    "vengala": "Crossref 10.1007/s40747-021-00305-0: published online Mar 2021, in vol. 9 no. 3, pp. 2915-2928 (2023). Abstract read: SHA-512 + CCP authentication, compression, modified ECC encryption.",
    "kasongo": "Crossref 10.1186/s40537-020-00379-6, OpenAlex abstract read: XGBoost filter-based feature reduction on UNSW-NB15; the decision tree's binary test accuracy rose from 88.13% to 90.85%.",
    "vinayakumar": "Crossref 10.1109/access.2019.2895334 (IEEE Access 7, pp. 41525-41550); abstract read (DNN IDS evaluated on several datasets). Full author list not retrieved, hence 'et al.'.",
    "ahmad": "Crossref 10.1002/ett.4150 (Trans. Emerg. Telecommun. Technol. 32(1), e4150, Oct 2020 online / 2021 issue); abstract read (taxonomy and review of ML/DL NIDS). Full author list not retrieved, hence 'et al.'.",
    "ring": "Crossref 10.1016/j.cose.2019.06.005 (Comput. Secur. 86, pp. 147-167). Title/venue only; full author list not retrieved, hence 'et al.'.",
    "zoghi": "DataCite record for arXiv:2101.05067 (Zeinab Zoghi and Gursel Serpen, 2021); abstract read: visual analysis identifies class imbalance and class overlap as the two main problems of UNSW-NB15.",
    "goldschmidt": "DataCite record for arXiv:2502.06688 (Patrik Goldschmidt and Daniela Chuda, 2025): systematic review of 89 NIDS datasets. A web-search summary attributes mislabelling, simulation artefacts and limited diversity of UNSW-NB15 to it via its reference [8]; that specific claim was NOT read in the paper itself, so it is not used as a quotation.",
    "mahalle": "Crossref 10.1109/inpac.2014.6981152 (INPAC 2014, pp. 146-149); abstract read (hybrid RSA & AES for secure upload/download in a cloud). Authors' middle initials not in the record. Weak venue.",
    "rao": "Crossref 10.1016/j.measen.2023.100870, abstract read: HECC with Edwards-curve keys and Diffie-Hellman exchange, key generation 0.000025 s, encryption 0.00349 s, throughput 693.10 KB/s (author-reported).",
    "sudha": "Crossref 10.1007/s40998-025-00816-3 (title, authors, vol. 49 no. 3, pp. 1045-1070, 2025). WEAK: no abstract retrieved, so no result is quoted.",
    "hybrid_ijsea": "Crossref/OpenAlex 10.7753/ijsea1403.1013 (Mar 2025); abstract read: AES-256 for data and RSA for key exchange, authors report 35% lower encryption time and 28% lower decryption time. WEAK: no author list in the records, volume/pages absent, small journal.",
}
