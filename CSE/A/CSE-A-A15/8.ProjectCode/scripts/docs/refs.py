"""IEEE-numbered reference list of the CipherVeil report. The ORDER IS FIXED: chapters, decks and the paper cite these numbers.

[1] is the base paper; [2]-[3] are the other papers of the batch folder; [4]-[7] are the survey papers named in 5.LITERATURE SURVEY.docx
(title, year and source only - the batch file gives nothing more and they could not be verified on the web, so no result is quoted from them).
"""

REFS = [
    # --- the batch's own papers
    "S. Ahmad and S. Rass, \"ProSt: Provably secure homomorphic steganography,\" *IEEE Access*, vol. 14, pp. 14393-14409, 2026, doi: 10.1109/ACCESS.2026.3656995.",
    "S. E. Fatemieh, R. Shahdi Alizadeh, and E. Zarezadeh, \"Design of memristive lightweight encryption for in-memory image steganography,\" arXiv:2605.03494, May 2026.",
    "S. R. Raiyan and M. H. Kabir, \"SCReedSolo: A secure and robust LSB image steganography framework with randomized symmetric encryption and Reed-Solomon coding,\" arXiv:2503.12368, 2025 (ACPR 2025).",
    "B. Kukreja and S. Malik, \"An steganography-based triple layered image data hiding using visual cryptography,\" 2024 (authors as listed on the Authorea preprint page; venue and year of formal publication not confirmed).",
    "\"Steganography - data hiding using image object,\" *Gurukul International Multidisciplinary Research Journal*, 2024.",
    "\"Hybrid steganography: Leveraging chaotic encryption and CNN for robust image hiding,\" in *Proc. 7th Int. Conf. Mechatronics, Robotics and Automation (ICMRA)*, 2024.",
    "\"Enhanced image steganography with AES encryption and hybrid DWT-DCT transform for secure data hiding,\" *International Journal of Advanced Research*, 2025.",
    # --- steganography foundations
    "J. Fridrich, *Steganography in Digital Media: Principles, Algorithms, and Applications*. Cambridge, U.K.: Cambridge Univ. Press, 2009.",
    "I. J. Cox, M. L. Miller, J. A. Bloom, J. Fridrich, and T. Kalker, *Digital Watermarking and Steganography*, 2nd ed. Burlington, MA, USA: Morgan Kaufmann, 2008.",
    "N. Provos and P. Honeyman, \"Hide and seek: An introduction to steganography,\" *IEEE Security & Privacy*, vol. 1, no. 3, pp. 32-44, May/Jun. 2003.",
    "C.-K. Chan and L. M. Cheng, \"Hiding data in images by simple LSB substitution,\" *Pattern Recognition*, vol. 37, no. 3, pp. 469-474, Mar. 2004.",
    "J. Mielikainen, \"LSB matching revisited,\" *IEEE Signal Processing Letters*, vol. 13, no. 5, pp. 285-287, May 2006.",
    "T. Filler, J. Judas, and J. Fridrich, \"Minimizing additive distortion in steganography using syndrome-trellis codes,\" *IEEE Trans. Information Forensics and Security*, vol. 6, no. 3, pp. 920-935, Sep. 2011.",
    "C. Cachin, \"An information-theoretic model for steganography,\" in *Information Hiding (IH 1998)*, Lecture Notes in Computer Science, vol. 1525. Berlin, Germany: Springer, 1998, pp. 306-318.",
    # --- steganalysis
    "A. Westfeld and A. Pfitzmann, \"Attacks on steganographic systems,\" in *Information Hiding (IH 1999)*, Lecture Notes in Computer Science, vol. 1768. Berlin, Germany: Springer, 2000, pp. 61-76.",
    "J. Fridrich, M. Goljan, and R. Du, \"Detecting LSB steganography in color and gray-scale images,\" *IEEE MultiMedia*, vol. 8, no. 4, pp. 22-28, Oct.-Dec. 2001.",
    "S. Dumitrescu, X. Wu, and Z. Wang, \"Detection of LSB steganography via sample pair analysis,\" *IEEE Trans. Signal Processing*, vol. 51, no. 7, pp. 1995-2007, Jul. 2003.",
    "J. Fridrich and M. Goljan, \"On estimation of secret message length in LSB steganography in spatial domain,\" in *Proc. SPIE*, vol. 5306, Security, Steganography, and Watermarking of Multimedia Contents VI, 2004, pp. 23-34.",
    "A. D. Ker and R. Bohme, \"Revisiting weighted stego-image steganalysis,\" in *Proc. SPIE*, vol. 6819, Security, Forensics, Steganography, and Watermarking of Multimedia Contents X, 2008, Art. no. 681905.",
    # --- cryptography and quality measures
    "Advanced Encryption Standard (AES), Federal Information Processing Standards Publication 197, NIST, Nov. 2001.",
    "M. Dworkin, \"Recommendation for block cipher modes of operation: Galois/Counter Mode (GCM) and GMAC,\" NIST Special Publication 800-38D, Nov. 2007.",
    "R. L. Rivest, A. Shamir, and L. Adleman, \"A method for obtaining digital signatures and public-key cryptosystems,\" *Communications of the ACM*, vol. 21, no. 2, pp. 120-126, Feb. 1978.",
    "K. Moriarty, B. Kaliski, J. Jonsson, and A. Rusch, \"PKCS #1: RSA cryptography specifications version 2.2,\" IETF RFC 8017, Nov. 2016.",
    "M. Bellare and P. Rogaway, \"Optimal asymmetric encryption,\" in *Advances in Cryptology - EUROCRYPT '94*, Lecture Notes in Computer Science, vol. 950. Berlin, Germany: Springer, 1995, pp. 92-111.",
    "J. Katz and Y. Lindell, *Introduction to Modern Cryptography*, 2nd ed. Boca Raton, FL, USA: Chapman & Hall/CRC, 2014.",
    "Z. Wang, A. C. Bovik, H. R. Sheikh, and E. P. Simoncelli, \"Image quality assessment: From error visibility to structural similarity,\" *IEEE Trans. Image Processing*, vol. 13, no. 4, pp. 600-612, Apr. 2004.",
    "Q. Huynh-Thu and M. Ghanbari, \"Scope of validity of PSNR in image/video quality assessment,\" *Electronics Letters*, vol. 44, no. 13, pp. 800-801, Jun. 2008.",
    # --- related to the base paper's cloud setting
    "C. Gentry, \"Fully homomorphic encryption using ideal lattices,\" in *Proc. 41st ACM Symp. Theory of Computing (STOC)*, 2009, pp. 169-178.",
    "V. Costan and S. Devadas, \"Intel SGX explained,\" IACR Cryptology ePrint Archive, Report 2016/086, 2016.",
]

# key -> reference number (stable: do not reorder REFS)
CITE = {
    "base": 1, "memr": 2, "screed": 3, "s_triple": 4, "s_object": 5, "s_chaos": 6, "s_dwt": 7,
    "fridrich": 8, "cox": 9, "provos": 10, "chan": 11, "mielikainen": 12, "stc": 13, "cachin": 14,
    "westfeld": 15, "rs": 16, "spa": 17, "ws": 18, "wsrev": 19,
    "aes": 20, "gcm": 21, "rsa": 22, "rfc8017": 23, "oaep": 24, "katz": 25, "ssim": 26, "psnr": 27,
    "gentry": 28, "sgx": 29,
}
assert len(REFS) == max(CITE.values()) == len(CITE)
