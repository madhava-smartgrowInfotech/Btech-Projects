"""
Reference list for the AegisBallot (CSE-C-C1) documents, IEEE style, numbered by list order (REFS[0] is [1]).

Verification status (see REF_NOTES): entries 1-3 were read from the PDFs kept with the batch (Documentary/ and archived_base_papers/);
entries 4-7 are the four other survey items named in 5.LITERATURE SURVEY.docx, whose title, authors and venue were confirmed on the web
(SSRN, the journal site, the journal DOI landing page) but whose full text was not read - they are used only for what their abstracts say.
Entry 8-9 were confirmed through Crossref / the publisher. Entries 10-31 are standard, well-known works and standards given as published.
Italics use *...* markup (rendered by kit.add_runs). Cite from other modules with CITE['key'].
"""

REFS = [
    # ---- 1-3: base paper and the two papers kept in archived_base_papers/ (read from the PDFs)
    "A. Shaikh, N. Adhikari, A. Nazir, A. S. Shah, S. Baig and H. Al Shihi, \"Blockchain-enhanced electoral integrity: a robust model for secure digital voting systems in Oman,\" "
    "*F1000Research*, vol. 14, art. 223, version 3, Sep. 2025, doi: 10.12688/f1000research.160087.3.",
    "S. Chouhan and G. Sharma, \"A new era of elections: leveraging blockchain for fair and transparent voting,\" arXiv:2502.16127, Feb. 2025.",
    "T. Lloyd, D. O Broin and M. Harrigan, \"The on-chain and off-chain mechanisms of DAO-to-DAO voting,\" arXiv:2603.00708, Feb. 2026.",
    # ---- 4-7: the other batch literature-survey items (title, authors and venue confirmed online; full text not read)
    "M. Ray, V. Ojha and W. Rhmann, \"Electronic voting system powered by blockchain technology: a study,\" *SSRN Electronic Journal*, 2024, doi: 10.2139/ssrn.4483852. "
    "[SSRN lists the posting as May 2023 (ICCS 2023); the batch records 2024.]",
    "K. Krishan, S. Raj and P. Raj, \"Decentralized trust: a blockchain-based framework for secure electronic voting,\" SSRN preprint, Mar. 2026.",
    "T. Aswini, \"Blockchain in electronic voting systems: trust and security challenges,\" *Sci. J. Artif. Intell. Blockchain Technol.*, vol. 2, no. 4, pp. 69-77, Oct.-Dec. 2025, "
    "doi: 10.63345/sjaibt.v2.i4.108.",
    "S. Bramasto, S. F. Savitri and E. R. Djuwitaningrum, \"Electronic voting (e-voting) sebagai aplikasi terdesentralisasi pada Vexanium blockchain,\" *Faktor Exacta*, vol. 17, no. 2, "
    "pp. 96-107, Jun. 2024, doi: 10.30998/faktorexacta.v17i2.19405.",
    # ---- 8-9: other blockchain e-voting surveys
    "U. Jafar, M. J. Ab Aziz and Z. Shukur, \"Blockchain for electronic voting system - review and open research challenges,\" *Sensors*, vol. 21, no. 17, art. 5874, 2021.",
    "H. O. Ohize *et al.*, \"Blockchain for securing electronic voting systems: a survey of architectures, trends, solutions, and challenges,\" *Cluster Comput.*, vol. 28, no. 2, art. 132, "
    "2025 (online Nov. 2024), doi: 10.1007/s10586-024-04709-8.",
    # ---- 10-14: real deployments and analyses of e-voting
    "D. Springall *et al.*, \"Security analysis of the Estonian internet voting system,\" in *Proc. ACM SIGSAC Conf. Comput. Commun. Secur. (CCS)*, 2014, pp. 703-715.",
    "B. Adida, \"Helios: web-based open-audit voting,\" in *Proc. 17th USENIX Security Symp.*, 2008, pp. 335-348.",
    "M. A. Specter, J. Koppel and D. Weitzner, \"The ballot is busted before the blockchain: a security analysis of Voatz, the first internet voting application used in U.S. federal elections,\" "
    "in *Proc. 29th USENIX Security Symp.*, 2020, pp. 1535-1553.",
    "F. S. Hjalmarsson, G. K. Hreioarsson, M. Hamdaqa and G. Hjalmtysson, \"Blockchain-based e-voting system,\" in *Proc. IEEE 11th Int. Conf. Cloud Comput. (CLOUD)*, 2018, pp. 983-986.",
    "N. Kshetri and J. Voas, \"Blockchain-enabled e-voting,\" *IEEE Softw.*, vol. 35, no. 4, pp. 95-99, Jul./Aug. 2018.",
    # ---- 15-19: blockchain and consensus foundations
    "S. Nakamoto, \"Bitcoin: a peer-to-peer electronic cash system,\" 2008. [Online]. Available: https://bitcoin.org/bitcoin.pdf",
    "V. Buterin, \"A next-generation smart contract and decentralized application platform (Ethereum white paper),\" 2014.",
    "E. Androulaki *et al.*, \"Hyperledger Fabric: a distributed operating system for permissioned blockchains,\" in *Proc. 13th EuroSys Conf.*, 2018, art. 30.",
    "M. Castro and B. Liskov, \"Practical Byzantine fault tolerance,\" in *Proc. 3rd Symp. Operating Syst. Design Implement. (OSDI)*, 1999, pp. 173-186.",
    "R. C. Merkle, \"A digital signature based on a conventional encryption function,\" in *Advances in Cryptology - CRYPTO '87*, ser. LNCS, vol. 293. Berlin, Germany: Springer, 1988, pp. 369-378.",
    # ---- 20-26: cryptographic building blocks and security standards
    "National Institute of Standards and Technology, \"Secure hash standard (SHS),\" FIPS PUB 180-4, Aug. 2015.",
    "M. Dworkin, \"Recommendation for block cipher modes of operation: Galois/Counter Mode (GCM) and GMAC,\" NIST Special Publication 800-38D, Nov. 2007.",
    "S. Josefsson and I. Liusvaara, \"Edwards-curve digital signature algorithm (EdDSA),\" IETF RFC 8032, Jan. 2017.",
    "A. Biryukov, D. Dinu and D. Khovratovich, \"Argon2: new generation of memory-hard functions for password hashing and other applications,\" in *Proc. IEEE Eur. Symp. Secur. Privacy (EuroS&P)*, 2016, pp. 292-302.",
    "A. Biryukov, D. Dinu, D. Khovratovich and S. Josefsson, \"Argon2 memory-hard function for password hashing and proof-of-work applications,\" IETF RFC 9106, Sep. 2021.",
    "J. Verhoeff, \"Error detecting decimal codes,\" Mathematisch Centrum, Amsterdam, The Netherlands, Math. Centre Tract 29, 1969.",
    "D. L. Chaum, \"Untraceable electronic mail, return addresses, and digital pseudonyms,\" *Commun. ACM*, vol. 24, no. 2, pp. 84-90, 1981.",
    # ---- 27-28: Aadhaar and security guidance
    "Government of India, \"The Aadhaar (Targeted Delivery of Financial and Other Subsidies, Benefits and Services) Act, 2016,\" The Gazette of India, Act No. 18 of 2016.",
    "OWASP Foundation, \"OWASP Application Security Verification Standard (ASVS) version 4.0.3,\" 2021. [Online]. Available: https://owasp.org/www-project-application-security-verification-standard/",
    # ---- 29-31: software used
    "S. Ramirez, \"FastAPI documentation,\" 2024. [Online]. Available: https://fastapi.tiangolo.com/",
    "M. Bayer, \"SQLAlchemy,\" in *The Architecture of Open Source Applications, Volume II*, A. Brown and G. Wilson, Eds. 2012.",
    "Meta Platforms, Inc., \"React documentation,\" 2024. [Online]. Available: https://react.dev/",
]

CITE = {
    "base": 1, "newera": 2, "dao": 3,
    "ray": 4, "krishan": 5, "aswini": 6, "vexanium": 7,
    "jafar": 8, "ohize": 9,
    "estonia": 10, "helios": 11, "voatz": 12, "hjalmarsson": 13, "kshetri": 14,
    "bitcoin": 15, "ethereum": 16, "fabric": 17, "pbft": 18, "merkle": 19,
    "sha2": 20, "gcm": 21, "eddsa": 22, "argon2": 23, "argon2rfc": 24, "verhoeff": 25, "chaum": 26,
    "aadhaar_act": 27, "asvs": 28,
    "fastapi": 29, "sqlalchemy": 30, "react": 31,
}

assert len(REFS) == 31 and set(CITE.values()) == set(range(1, 32))

REF_NOTES = {
    1: "verified from the PDF in Documentary/ (title, six authors, F1000Research 14:223, version 3, DOI); the Figure 6/9 times quoted in the documents were read by eye from the charts",
    2: "verified from the PDF in archived_base_papers/ (Aadhaar / driving-licence hashing with BLAKE2b-512, fingerprint and picture-rotation factors, SHA-256 hash chain; no throughput results)",
    3: "verified from the PDF in archived_base_papers/ (DAO-to-DAO voting; arXiv 2603.00708)",
    4: "confirmed on SSRN (authors Milan Ray, Vishal Ojha, Wasiur Rhmann; DOI 10.2139/ssrn.4483852); abstract only, full text not available",
    5: "confirmed on SSRN (Kunal Krishan, Saumya Raj, Pratik Raj; Institute of Engineering and Management, Salt Lake; permissioned ledger with smart contracts, hashing for anonymity); abstract only",
    6: "confirmed on the journal site (single author Dr T. Aswini, KL University; vol. 2 no. 4, pp. 69-77, DOI 10.63345/sjaibt.v2.i4.108); abstract: trust and security concerns, hybrid designs with ZKP, homomorphic encryption and sharding",
    7: "confirmed on the journal site (Faktor Exacta vol. 17 no. 2, pp. 96-107, Jun 2024; DApp on the Vexanium blockchain, PHP 8.2, Apache, PostgreSQL, black-box tests passed)",
    8: "confirmed on MDPI / PMC (Sensors 21(17):5874)",
    9: "confirmed through Crossref (eleven authors, Cluster Computing 28(2):132)",
}
