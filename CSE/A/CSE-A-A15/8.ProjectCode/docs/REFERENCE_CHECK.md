# Reference check (scripts/docs/refs.py)

Checked on 2026-10-26 with web search, DBLP/Crossref/publisher snippets and the PDFs in this batch folder. "Verified" = authors, title, venue, volume/issue/pages and year agree with at least one independent source. Crossref API returned HTTP 429 for several calls, so some entries were checked through search results that quote DBLP, IEEE Xplore, NIST or the author pages.

| # | Entry | Result | Source |
|---|---|---|---|
| 1 | Ahmad and Rass, ProSt, IEEE Access 14, 2026 | Verified against the PDF: article starts on page number 14393 and the last page (author biographies) is 14409; DOI 10.1109/ACCESS.2026.3656995 printed on page 1 | `Documentary/BASEPAPER_ProSt...pdf` |
| 2 | Fatemieh et al., arXiv:2605.03494 | Verified (title, three authors, arXiv:2605.03494v2, May 2026) | `archived_base_papers/BASEPAPER_Design_of_Memristive...pdf` |
| 3 | Raiyan and Kabir, SCReedSolo, arXiv:2503.12368 | Verified (title, authors, arXiv:2503.12368v3, Nov 2025). "ACPR 2025" comes from `BASEPAPER_REFERENCES.md`, not from the PDF text | `archived_base_papers/REFERENCE_PAPER_SCReedSolo...pdf` |
| 4 | Triple layered image data hiding using visual cryptography, 2024 | **Corrected (partly completed).** Authors Bhawna Kukreja and Sanjay Malik found on an Authorea preprint page (search result; page itself returned 403). Venue and publication year are not confirmed, so the entry says so | https://www.authorea.com/users/723326/articles/708268-an-steganography-based-triple-layered-image-data-hiding-using-visual-cryptography |
| 5 | Steganography - data hiding using image object, Gurukul Int. Multidisciplinary Research J., 2024 | Not verifiable (no web record found); kept title-only, no result quoted | web search, two attempts |
| 6 | Hybrid steganography: chaotic encryption and CNN, 7th ICMRA 2024 | Not verifiable (no authors or proceedings listing found); kept title-only | web search, two attempts |
| 7 | Enhanced image steganography with AES and hybrid DWT-DCT, Int. J. Advanced Research, 2025 | Not verifiable; kept title-only | web search, two attempts |
| 8 | Fridrich, Steganography in Digital Media, CUP | Verified exists (xxii+437 pp., ISBN 9780521190190). Catalogues give 2010; the base paper cites 2009. Entry keeps 2009 (first publication / base-paper citation); note the difference if asked | https://librarysearch.aut.ac.nz/vufind/Record/1277117 |
| 9 | Cox et al., Digital Watermarking and Steganography, 2nd ed., Morgan Kaufmann, 2008 | Verified (catalogue 2008, ISBN 9780123725851; one Elsevier page shows 2014 as e-book date) | https://shop.elsevier.com/books/digital-watermarking-and-steganography/cox/978-0-12-372585-1 |
| 10 | Provos and Honeyman, IEEE S&P 1(3) 32-44, 2003 | Verified (Crossref) | api.crossref.org query |
| 11 | Chan and Cheng, Pattern Recognition 37(3) 469-474, 2004 | Verified (Crossref) | api.crossref.org query |
| 12 | Mielikainen, LSB matching revisited, IEEE SPL 13(5) 285-287, 2006 | Verified (Crossref) | api.crossref.org query |
| 13 | Filler, Judas, Fridrich, STC, IEEE TIFS 6(3) 920-935, Sep 2011 | Verified | https://ieeexplore.ieee.org/abstract/document/5740590 |
| 14 | Cachin, Information-theoretic model for steganography, LNCS 1525, 306-318, 1998 | Verified | https://www.doi.org/10.1007/3-540-49380-8_21 |
| 15 | Westfeld and Pfitzmann, Attacks on steganographic systems, LNCS 1768, 61-76 | Verified (DBLP key conf/ih/WestfeldP99; some citations print 61-75; volume published 2000, workshop 1999) | https://dblp.org/db/conf/ih/ih99.html |
| 16 | Fridrich, Goljan, Du, IEEE MultiMedia 8(4) 22-28, 2001 | Verified, DOI 10.1109/93.959097 | https://ieeexplore.ieee.org/document/959097 |
| 17 | Dumitrescu, Wu, Wang, SPA, IEEE TSP 51(7) 1995-2007, 2003 | Verified, DOI 10.1109/TSP.2003.812753 (third author is Zhe Wang) | https://www.ece.mcmaster.ca/~sorina/papers/LSBfinalTSP.pdf |
| 18 | Fridrich and Goljan, Proc. SPIE 5306, 23-34, 2004 | Verified (SUNY Binghamton record) | https://researchconnect.suny.edu/en/publications/on-estimation-of-secret-message-length-in-lsb-steganography-in-sp/ |
| 19 | Ker and Bohme, Revisiting weighted stego-image steganalysis, Proc. SPIE 6819, 2008 | **Corrected**: "p. 681905" changed to "Art. no. 681905" (681905 is the SPIE article number; one reference list gives pages 56-72, not confirmed independently, so no page range is printed) | Crossref record via search; https://www.cs.ox.ac.uk/people/andrew.ker/publications.html |
| 20 | NIST FIPS 197, Nov 2001 | Verified (published 26 Nov 2001; withdrawn 2023 and superseded by FIPS 197-upd1, no technical change) | https://csrc.nist.gov/publications/detail/fips/197/final |
| 21 | Dworkin, NIST SP 800-38D, Nov 2007 | Verified | https://csrc.nist.gov/pubs/sp/800/38/d/final |
| 22 | Rivest, Shamir, Adleman, CACM 21(2) 120-126, 1978 | Verified for authors, title, year (Crossref); volume, issue and pages not returned by the lookup, kept as printed (standard citation) | api.crossref.org query |
| 23 | RFC 8017, Moriarty (Ed.), Kaliski, Jonsson, Rusch, Nov 2016 | Verified | https://www.rfc-editor.org/rfc/rfc8017 |
| 24 | Bellare and Rogaway, OAEP, EUROCRYPT '94, LNCS 950, 92-111 | Verified (DBLP conf/eurocrypt/BellareR94; conference 1994, Springer volume dated 1995 - entry uses 1995) | https://dblp.org/db/conf/eurocrypt/eurocrypt94.html |
| 25 | Katz and Lindell, 2nd ed., CRC, 2014 | Verified (ISBN 9781466570269; British Library 2014, some catalogues 2015) | https://eld.bl.uk/catalog/016977609 |
| 26 | Wang et al., SSIM, IEEE TIP 13(4) 600-612, Apr 2004 | Verified, DOI 10.1109/TIP.2003.819861 | https://ece.uwaterloo.ca/~z70wang/publications/ssim.html |
| 27 | Huynh-Thu and Ghanbari, Electronics Letters 44(13) 800-801, 2008 | Verified, DOI 10.1049/el:20080522 | MathWorks and Wikipedia-derived listings |
| 28 | Gentry, STOC 2009, 169-178 | Verified, DOI 10.1145/1536414.1536440 | https://crypto.stanford.edu/craig |
| 29 | Costan and Devadas, Intel SGX Explained, ePrint 2016/086 | Verified | https://eprint.iacr.org/2016/086 |

Order and count (29) unchanged; `CITE` keys untouched. Entries [5]-[7] must stay title-only in every document and no result may be attributed to them. Entry [4] gives authors only; do not quote its results.
