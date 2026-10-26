# LIT_NOTES - CipherVault (CSE-C-C13)

What was verified for each entry of `scripts/docs/refs.py` (34 refs, numbering stable; base paper = [1]). Checked 2026-10-26 against the batch PDFs, Crossref DOI records, standards-body pages (rfc-editor.org, csrc.nist.gov, w3.org), USENIX/NDSS/ACL pages and search records.
Keys are used as `N('key')`; `UNVERIFIED = ('s2','s3','s4')` must never be quoted for content and never cited in the IEEE paper.

## Numbering

| # | key | status |
|---|---|---|
| 1 | base | verified (full PDF read) |
| 2 | ijedr | verified (full PDF read) |
| 3 | s2 | NOT independently verified (IRJMETS title only) |
| 4 | s3 | NOT independently verified (ICPCSN title only) |
| 5 | s4 | NOT independently verified (chaotic-mapping title only) |
| 6 | geo (= batch survey item 5, key `s5` aliases it) | verified (ITM Web of Conferences page + abstract) |
| 7 | sagi | verified (journal page + abstract) |
| 8 | mega | verified (DBLP/ePrint records) |
| 9 | boeck | verified (USENIX WOOT'16 page) |
| 10 | sirius | verified (NDSS accepted-papers page, Stanford page); page range NOT confirmed, so none given |
| 11 | plutus | verified (USENIX page; pp. 29-42) |
| 12 | tahoe | verified (Crossref, 10.1145/1456469.1456474, pp. 21-26) |
| 13 | cryptdb | verified (Crossref, 10.1145/2043556.2043566, pp. 85-100) |
| 14 | kamara | verified from two reference lists (LNCS 6054, pp. 136-149); Springer page not opened |
| 15 | rbac01 | verified (Crossref: TISSEC 4(3), 224-274, Aug 2001) |
| 16 | rbac96 | verified (several bibliographies: IEEE Computer 29(2), 38-47, Feb 1996) |
| 17 | saltzer | verified (Proc. IEEE 63(9), 1278-1308, Sep 1975) |
| 18 | abe06 | verified (Crossref pp. 89-98) |
| 19 | cpabe | verified (Crossref pp. 321-334, 10.1109/SP.2007.11) |
| 20 | pre06 | verified (Crossref TISSEC 9(1), 1-30, Feb 2006) |
| 21 | gcm | verified (NIST CSRC: SP 800-38D, Nov 2007) |
| 22 | aes | verified (FIPS 197, 26 Nov 2001, updated 9 May 2023) |
| 23 | sha | verified (FIPS 180-4, Aug 2015) |
| 24 | oaep | verified (RFC 8017, Nov 2016) |
| 25 | oaep94 | verified (IACR listing, Eurocrypt '94, LNCS 950, pp. 92-111; published 1995) |
| 26 | pbkdf2 | verified (RFC 8018, Jan 2017) |
| 27 | sp800132 | verified (NIST SP 800-132, Dec 2010) |
| 28 | bcrypt | verified (USENIX ATC 1999, pp. 81-92 per two listings) |
| 29 | jwt | verified (RFC 7519, May 2015) |
| 30 | webcrypto | verified (W3C Recommendation 26 Jan 2017, editor Mark Watson; Level 2 exists only as a Working Draft) |
| 31 | audit99 | verified (Crossref: TISSEC 2(2), 159-176, May 1999; Schneier's site prints "v. 1, n. 3", which is his typo) |
| 32 | tamper09 | verified (USENIX Security 2009 page; pp. 317-334 from two secondary lists) |
| 33 | clinbert | verified (ACL Anthology W19-1909, pp. 72-78) |
| 34 | fabric | verified (EuroSys '18, doi 10.1145/3190508.3190538; article number not confirmed so none given) |

Surname spelling: "Bock" is used for Bock/Boeck (Hanno Boeck) in ASCII; "Mazieres" for Mazieres.

## Base paper - Nekouie et al. (read in full, `Documentary/BASEPAPER_*.pdf`)

- Sci. Rep. 16, 8673 (2026); received 3 Jun 2025, accepted 6 Feb 2026; Crossref issued date 17 Feb 2026. Authors: A. Nekouie, M. Vafaei Jahan, M. H. Moattar, R. Sheibani (Islamic Azad University, Mashhad).
- Method: ClinicalBERT extracts data attributes from unstructured notes; ECC-based dual-attribute (user + data) ciphertext-policy ABE; several key-generation centres (no key escrow); private Hyperledger Fabric ledger stores attribute public keys and policies (kilobytes per attribute, files off-chain); 23 phases; fixed 160-bit ECC key; the user hashes the decrypted record and compares with the stored hash.
- Evaluation is a CALCULATION: Table 3 primitive timings (OpenSSL) x operation counts in Table 4 (x = 5 encryption attributes, l = 10 leaf nodes, r = 30 matrix rows, Raspberry Pi timings). It states security via IND-CPA, collusion resistance and escrow-freeness proof sketches. No dataset, no ClinicalBERT extraction accuracy, no end-to-end measurement was found in the text; "data and code available from the corresponding author upon request".
- Test hardware: HPE server, six-core E5-2620 v3 at 2.40 GHz, 32 GB RAM, Ubuntu 20.04; Raspberry Pi 3 B+ (1.4 GHz quad-core Cortex-A53, 1 GB RAM, 64-bit Raspbian 12); OpenSSL on both.
- Table 3 (microseconds, Raspberry Pi / HPE): random number 11.1 / 2.2; hash 2.3 / 0.11; symmetric enc/dec 0.5 / 0.11; EC point multiplication 557 / 67; EC point addition 2.3 / 0.3; exponentiation 1187 / 137; bilinear pairing 1520 / 175; modular multiplication 0.5 / 0.06; modular addition 0.2 / 0.02.
- Proposed scheme cost (Pi timings): encryption ~1362.3x + 1131 us, decryption ~0.2x + 563 us, total ~1362.5x + 1694 = ~8,506 us at x = 5. Compared totals in Table 4: 8,812; 8,912; 8,912; 11,577; 11,697; 21,166; 40,605; 41,647; 71,296; 71,323 us. The paper claims the best decryption and total times.
- Gap vs this project: no file upload/download, no role model, no audit-log cost, no failure study. Same exported data in `lit.BASE_ANALYSIS["numbers"]`.

## Closest-architecture paper - Sowmiya et al., IJEDR (read in full, `archived_base_papers/`)

Vol. 14, issue 2, pp. 576-579, April 2026, paper IJEDR2602501; Dept. of IT, The Kavery Engineering College, Salem. Values re-checked against the PDF text:
- Architecture: client-side AES-256-GCM (128-bit IV in the table), RSA-2048 OAEP-SHA256 wrapping, RBAC Owner / Editor / Viewer, SHA-256 chained audit log with server ECDSA signature per entry, TOTP MFA (RFC 6238, PyOTP), S3 + PostgreSQL + HashiCorp Vault, React 18 + Web Crypto, 4 MB chunks with independent GCM tags, PBKDF2 310,000 iterations, rate limiting + CAPTCHA, NIST 800-88 cryptographic erasure.
- Results (50 users, 3 roles): +320 ms upload for a 10 MB file; 98.6% access-control accuracy (13 edge-case misclassifications of 900 attempts); 0 unauthorised exposure events in 30-day adversarial testing; 100% of 1,240 simulated credential-stuffing MFA bypass attempts blocked; 100% audit tamper detection (all 50 simulated events). Qualitative: 38/50 "as fast as Google Drive", 44/50 "intuitive sharing".
- Limits it states: key recovery needs admin escrow; Web Crypto keys last a session; >1 GB adds ~1.8 s; no offline mode.
- Not given: client hardware, per-operation timings, tamper methods, test protocol details. Note: its sample code uses a 16-byte GCM IV and its table says 128-bit IV; CipherVault uses the 96-bit IV the standard recommends.

## Other facts used (all from abstracts or standards pages, no numbers beyond these)

- Geocrypt: P. Thenmozhi, V. D. Saralesh, R. Sakthi (St. Joseph's College of Engineering, Chennai), presented at ICNEXTS'25, published online 4 Feb 2026; RSA file exchange, location + time-limited-session gating, Ethereum smart contracts (Truffle, Ganache). Only abstract/front matter read; no numbers.
- Saginayev et al.: authors E. Saginayev, A. Niyazov, A. Razaque, Zh. Kalpeyeva, A. Urazgaliyeva (Satbayev University); "Secure file storage on cloud using hybrid cryptography"; AES-256 + RSA + SHA-256 before encryption / after decryption; abstract has no figures. The issue page shows 2025-04-30 as the issue date although the paper is labelled 2024 (the batch survey does not list this paper; it is an addition by us). An MMU repository entry with the same title names ElGamal instead of RSA - possibly another version.
- MEGA: five attacks, full compromise of file confidentiality; developers later added RSA key checks (Albrecht et al., Eurocrypt 2023 mention it).
- Boeck et al.: scan found 184 HTTPS servers repeating GCM nonces; >70,000 using random nonces.
- Plutus: filegroups, read/write separation, efficient revocation, untrusted-server write check, OpenAFS prototype; security comparable to encrypting all network traffic at similar overhead.
- CryptDB: 126 million-query trace, 99.5% of 128,840 columns supportable.
- Tahoe: capabilities + cryptography + erasure coding.
- Goyal et al.: introduces key-policy ABE, also audit-log sharing and broadcast encryption; CCS 2016 test-of-time award.
- Crosby & Wallach: tree-based log with logarithmic proofs; Schneier & Kelsey: pre-compromise entries cannot be read or undetectably modified.
- Ateniese et al.: proxy re-encryption applied to access control on the SFS read-only file system; first appeared at NDSS 2005.

## Not located (listed, not quoted, never cited in the paper)

Batch survey item 2 (IRJMETS 2026 "Secure file storage on cloud using AES encryption"), item 3 (ICPCSN 2026 "Secure cloud-based file storage system with enhanced data integrity and access control"), item 4 ("An integrated image encryption and secure transmission scheme for cloud environments using chaotic mapping and cryptographic access control"). Searched by exact title on 2026-10-26: no match. The alternates named in `archived_base_papers/BASEPAPER_REFERENCES.md` (IJSAT hybrid cryptography 2025, Springer RBAC and third-party auditing, "AES and RSA with RBAC") were not used.

## Wording rules for later forks

- The batch names the EHR paper as base paper (kept as [1]); the IJEDR paper is the closest-architecture comparison and may be called "the closest published architecture". Say plainly that the base paper's numbers are calculated, in microseconds, on other hardware, so CipherVault's measurements are not ranked against them.
- Never quote a result for refs 3-5. Cite them only as "listed in the batch survey".
