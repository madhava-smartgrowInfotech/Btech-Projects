"""IEEE-style reference list. Order = citation number in the report. Use N('key') to get the number for a key.

Every entry was checked against the paper itself (both batch papers are PDFs in the batch folder), a publisher/standards-body page,
a DOI record (Crossref) or a proceedings page; see docs/LIT_NOTES.md for what was checked for each entry.
Batch-survey items (5.LITERATURE SURVEY.docx):
  1 base paper (read in full), 2 IRJMETS, 3 ICPCSN, 4 chaotic-mapping image encryption, 5 Geocrypt.
  Items 2, 3 and 4 could not be located online; they are listed as the batch gives them and are never quoted for any result.
  Item 5 (Geocrypt) and the batch-folder paper by Sowmiya et al. (IJEDR) were read or checked and may be quoted.

REF_INDEX documents the number of each key (a dict key -> citation number), so decks and the paper can cite by key.
UNVERIFIED lists the keys that must never be quoted for content (and never cited in the IEEE paper).
"""

_R = [
    # --- base paper, closest-architecture paper, then the rest of the batch literature survey
    ("base", "A. Nekouie, M. Vafaei Jahan, M. H. Moattar and R. Sheibani, \"Secure electronic health record access control via blockchain, dual-attribute encryption, and large language model-based attribute extraction,\" Scientific Reports, vol. 16, art. no. 8673, 2026, doi: 10.1038/s41598-026-39690-2."),
    ("ijedr", "G. Sowmiya, R. Nivas and E. Vikram, \"Secure cloud file storage architecture with client-side encryption and access control,\" Int. J. Eng. Develop. Res. (IJEDR), vol. 14, no. 2, pp. 576-579, Apr. 2026, paper IJEDR2602501."),
    ("s2", "\"Secure file storage on cloud using AES encryption,\" Int. Res. J. Modernization in Engineering, Technology and Science (IRJMETS), 2026 (title as listed in the batch literature survey; not located online and not quoted)."),
    ("s3", "\"Secure cloud-based file storage system with enhanced data integrity and access control,\" in Proc. 6th Int. Conf. Pervasive Computing and Social Networking (ICPCSN), 2026 (title as listed in the batch literature survey; not located online and not quoted)."),
    ("s4", "\"An integrated image encryption and secure transmission scheme for cloud environments using chaotic mapping and cryptographic access control,\" 2026 (title as listed in the batch literature survey; not located online and not quoted)."),
    ("geo", "P. Thenmozhi, V. D. Saralesh and R. Sakthi, \"Geocrypt: Location-based secure file encryption and access control,\" ITM Web of Conferences, vol. 82, art. no. 03019, 2026, doi: 10.1051/itmconf/20268203019."),
    ("sagi", "E. Saginayev, A. Niyazov, A. Razaque, Zh. Kalpeyeva and A. Urazgaliyeva, \"Secure file storage on cloud using hybrid cryptography,\" Computing & Engineering, vol. 2, no. 2, pp. 1-7, 2024, doi: 10.51301/ce.2024.i2.01."),
    # --- attacks on and lessons from deployed end-to-end encrypted storage
    ("mega", "M. Backendal, M. Haller and K. G. Paterson, \"MEGA: Malleable encryption goes awry,\" in Proc. IEEE Symp. Security and Privacy (SP), 2023, pp. 146-163."),
    ("boeck", "H. Bock, A. Zauner, S. Devlin, J. Somorovsky and P. Jovanovic, \"Nonce-disrespecting adversaries: Practical forgery attacks on GCM in TLS,\" in Proc. 10th USENIX Workshop on Offensive Technologies (WOOT), Austin, TX, USA, Aug. 2016."),
    # --- cryptographic storage and sharing systems
    ("sirius", "E.-J. Goh, H. Shacham, N. Modadugu and D. Boneh, \"SiRiUS: Securing remote untrusted storage,\" in Proc. Network and Distributed System Security Symp. (NDSS), 2003."),
    ("plutus", "M. Kallahalla, E. Riedel, R. Swaminathan, Q. Wang and K. Fu, \"Plutus: Scalable secure file sharing on untrusted storage,\" in Proc. 2nd USENIX Conf. File and Storage Technologies (FAST), San Francisco, CA, USA, 2003, pp. 29-42."),
    ("tahoe", "Z. Wilcox-O'Hearn and B. Warner, \"Tahoe: The least-authority filesystem,\" in Proc. 4th ACM Int. Workshop on Storage Security and Survivability (StorageSS), 2008, pp. 21-26, doi: 10.1145/1456469.1456474."),
    ("cryptdb", "R. A. Popa, C. M. S. Redfield, N. Zeldovich and H. Balakrishnan, \"CryptDB: Protecting confidentiality with encrypted query processing,\" in Proc. 23rd ACM Symp. Operating Systems Principles (SOSP), 2011, pp. 85-100, doi: 10.1145/2043556.2043566."),
    ("kamara", "S. Kamara and K. Lauter, \"Cryptographic cloud storage,\" in Financial Cryptography and Data Security Workshops 2010, Lecture Notes in Computer Science, vol. 6054, Springer, 2010, pp. 136-149."),
    # --- access control models and cryptographic access control
    ("rbac01", "D. F. Ferraiolo, R. Sandhu, S. Gavrila, D. R. Kuhn and R. Chandramouli, \"Proposed NIST standard for role-based access control,\" ACM Trans. Inf. Syst. Secur., vol. 4, no. 3, pp. 224-274, Aug. 2001, doi: 10.1145/501978.501980."),
    ("rbac96", "R. S. Sandhu, E. J. Coyne, H. L. Feinstein and C. E. Youman, \"Role-based access control models,\" IEEE Computer, vol. 29, no. 2, pp. 38-47, Feb. 1996."),
    ("saltzer", "J. H. Saltzer and M. D. Schroeder, \"The protection of information in computer systems,\" Proc. IEEE, vol. 63, no. 9, pp. 1278-1308, Sep. 1975."),
    ("abe06", "V. Goyal, O. Pandey, A. Sahai and B. Waters, \"Attribute-based encryption for fine-grained access control of encrypted data,\" in Proc. 13th ACM Conf. Computer and Communications Security (CCS), 2006, pp. 89-98, doi: 10.1145/1180405.1180418."),
    ("cpabe", "J. Bethencourt, A. Sahai and B. Waters, \"Ciphertext-policy attribute-based encryption,\" in Proc. IEEE Symp. Security and Privacy (SP), 2007, pp. 321-334, doi: 10.1109/SP.2007.11."),
    ("pre06", "G. Ateniese, K. Fu, M. Green and S. Hohenberger, \"Improved proxy re-encryption schemes with applications to secure distributed storage,\" ACM Trans. Inf. Syst. Secur., vol. 9, no. 1, pp. 1-30, Feb. 2006, doi: 10.1145/1127345.1127346."),
    # --- primitives and standards the system uses
    ("gcm", "M. Dworkin, \"Recommendation for block cipher modes of operation: Galois/Counter Mode (GCM) and GMAC,\" NIST Special Publication 800-38D, Nov. 2007."),
    ("aes", "National Institute of Standards and Technology, \"Advanced Encryption Standard (AES),\" Federal Information Processing Standards Publication 197, Nov. 2001 (updated May 2023)."),
    ("sha", "National Institute of Standards and Technology, \"Secure Hash Standard (SHS),\" Federal Information Processing Standards Publication 180-4, Aug. 2015."),
    ("oaep", "K. Moriarty, Ed., B. Kaliski, J. Jonsson and A. Rusch, \"PKCS #1: RSA cryptography specifications version 2.2,\" IETF RFC 8017, Nov. 2016."),
    ("oaep94", "M. Bellare and P. Rogaway, \"Optimal asymmetric encryption,\" in Advances in Cryptology - EUROCRYPT '94, Lecture Notes in Computer Science, vol. 950, Springer, 1995, pp. 92-111."),
    ("pbkdf2", "K. Moriarty, Ed., B. Kaliski and A. Rusch, \"PKCS #5: Password-based cryptography specification version 2.1,\" IETF RFC 8018, Jan. 2017."),
    ("sp800132", "M. S. Turan, E. Barker, W. Burr and L. Chen, \"Recommendation for password-based key derivation, part 1: Storage applications,\" NIST Special Publication 800-132, Dec. 2010."),
    ("bcrypt", "N. Provos and D. Mazieres, \"A future-adaptable password scheme,\" in Proc. USENIX Annual Technical Conf., Monterey, CA, USA, Jun. 1999, pp. 81-92."),
    ("jwt", "M. Jones, J. Bradley and N. Sakimura, \"JSON Web Token (JWT),\" IETF RFC 7519, May 2015."),
    ("webcrypto", "M. Watson, Ed., \"Web Cryptography API,\" W3C Recommendation, Jan. 26, 2017. [Online]. Available: https://www.w3.org/TR/2017/REC-WebCryptoAPI-20170126/"),
    # --- tamper-evident audit logging
    ("audit99", "B. Schneier and J. Kelsey, \"Secure audit logs to support computer forensics,\" ACM Trans. Inf. Syst. Secur., vol. 2, no. 2, pp. 159-176, May 1999."),
    ("tamper09", "S. A. Crosby and D. S. Wallach, \"Efficient data structures for tamper-evident logging,\" in Proc. 18th USENIX Security Symp., Montreal, QC, Canada, Aug. 2009, pp. 317-334."),
    # --- technologies named by the base paper
    ("clinbert", "E. Alsentzer et al., \"Publicly available clinical BERT embeddings,\" in Proc. 2nd Clinical Natural Language Processing Workshop, Minneapolis, MN, USA, Jun. 2019, pp. 72-78, doi: 10.18653/v1/W19-1909."),
    ("fabric", "E. Androulaki et al., \"Hyperledger Fabric: A distributed operating system for permissioned blockchains,\" in Proc. 13th EuroSys Conf., Porto, Portugal, Apr. 2018, doi: 10.1145/3190508.3190538."),
]
REFS = [t for _, t in _R]
_IDX = {k: i + 1 for i, (k, _) in enumerate(_R)}
_IDX["s5"] = _IDX["geo"]    # batch-survey numbering: item 5 is Geocrypt
REF_INDEX = _IDX            # documented alias: key -> citation number

# Items that were not located online (or are titles only): list them, never quote them, never cite them in the IEEE paper.
UNVERIFIED = ("s2", "s3", "s4")


def N(*keys):
    """Citation text like [3] or [3], [7] for one or more keys."""
    return ", ".join(f"[{_IDX[k]}]" for k in keys)
