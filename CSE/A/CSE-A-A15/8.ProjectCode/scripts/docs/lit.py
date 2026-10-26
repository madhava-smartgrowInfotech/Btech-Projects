"""Literature and framing data for the chapters, the decks and the IEEE paper (CipherVeil).

Every literature fact traces to the base-paper PDF (Documentary/), the two arXiv PDFs in archived_base_papers/, the reference notes in refs.py
or the batch documents. The four batch-survey items [4]-[7] could not be verified beyond their titles and are never quoted for numbers.
Reference numbers match scripts/docs/refs.py (CITE keys).
"""
from . import facts as F
from .refs import CITE as R

BASE_PAPER_TITLE = "ProSt: Provably Secure Homomorphic Steganography"
BASE_PAPER_VENUE = "S. Ahmad and S. Rass - IEEE Access, vol. 14, 2026"

# [work, year, approach, finding / limitation]   (each cell kept short)
LIT_TABLE = [
    [f"Ahmad, Rass [{R['base']}] (base paper)", "2026",
     "LSB secret bit at a secret position among random decoy LSBs; Fredkin-gate circuits evaluated on all pixels by an untrusted cloud",
     "Advantage of order 1/n; 8.38 s for 17 gates on 128x128x3; no PSNR, SSIM or capacity reported"],
    [f"Raiyan, Kabir (SCReedSolo) [{R['screed']}]", "2025",
     "Random shuffle + Fernet + Reed-Solomon codes + LSB, 3 bits per pixel",
     "PSNR 51.77-57.65 dB on very large covers; error correction helps against noise; text, audio and image payloads"],
    [f"Fatemieh et al. [{R['memr']}]", "2026",
     "Trivium and Grain-128a stream ciphers on memristive IMPLY logic, tested in an LSB application",
     "Up to 42 % and 44 % lower energy; hardware-level, no file-transfer pipeline"],
    [f"Fridrich [{R['fridrich']}]; Cox et al. [{R['cox']}]", "2008-09",
     "Textbooks on steganography, watermarking and steganalysis", "Foundations: capacity, distortion, detectability"],
    [f"Chan, Cheng [{R['chan']}]; Mielikainen [{R['mielikainen']}]", "2004-06",
     "Simple LSB substitution with a pixel-adjustment step; LSB matching (+/-1)", "Lower distortion than plain replacement; payload not encrypted"],
    [f"Filler et al. [{R['stc']}]", "2011", "Syndrome-trellis codes: embedding that minimises a distortion cost", "Adaptive embedding; more complex than sequential LSB"],
    [f"Westfeld, Pfitzmann [{R['westfeld']}]", "2000", "Chi-square attack on pairs of values after LSB replacement", "Detects sequential replacement of random-looking bits"],
    [f"Fridrich et al. [{R['rs']}]; Dumitrescu et al. [{R['spa']}]", "2001-03", "RS analysis; sample pair analysis (message-length estimates)", "Detects LSB replacement at low embedding rates"],
    [f"Fridrich, Goljan [{R['ws']}]; Ker, Bohme [{R['wsrev']}]", "2004-08", "Weighted-stego estimator and its refinement", "Blind estimate of the embedded fraction"],
    [f"Batch survey items [{R['s_triple']}]-[{R['s_dwt']}]", "2024-25",
     "Triple-layer visual cryptography; image-object hiding; chaotic encryption with a CNN; AES with hybrid DWT-DCT (titles only)",
     "Authors, data and results not verified; not quoted for numbers"],
]

# [work, approach, data, reported result, limitation]  - short cells for the IEEE paper's TABLE I
PAPER_TABLE = [
    [f"ProSt [{R['base']}]", "Decoy-LSB hiding + Fredkin gates", "Random bits in a 128x128x3 image", "8.38 s, 17 gates; advantage O(1/n)", "No PSNR, SSIM, capacity"],
    [f"SCReedSolo [{R['screed']}]", "Shuffle, Fernet, Reed-Solomon, LSB", "Text, audio, image into large covers", "PSNR 51.8-57.7 dB; 3 bpp", "Symmetric key only"],
    [f"Memristive [{R['memr']}]", "Trivium, Grain-128a in IMPLY logic", "Five 256x256 grayscale images", "Energy -42 % and -44 %", "Hardware study"],
    [f"Chan, Cheng [{R['chan']}]", "LSB substitution, pixel adjustment", "Grayscale images", "Lower error than plain LSB", "Plaintext payload"],
    [f"Mielikainen [{R['mielikainen']}]", "LSB matching", "Images (not reproduced here)", "Fewer changed pixels", "Plaintext payload"],
    [f"Filler et al. [{R['stc']}]", "Syndrome-trellis codes", "Image benchmarks (not reproduced here)", "Lower detectability", "Complex coding"],
    [f"Westfeld, Pfitzmann [{R['westfeld']}]", "Chi-square attack", "LSB-embedded images", "Flags LSB replacement", "Attack, not a hiding scheme"],
    [f"Fridrich et al. [{R['rs']}]", "RS analysis", "Colour, grayscale images", "Estimates message length", "Attack, not a hiding scheme"],
    [f"Survey [{R['s_triple']}]-[{R['s_dwt']}]", "Visual crypto; chaos + CNN; AES + DWT-DCT", "Not verified", "Not verified", "Details unverified"],
]

# the six objectives of 6.OBJECTIVES&PROBLEM STATEMENT.docx
OBJECTIVES = [
    "Implement AES encryption for the secret payload and RSA encryption for the AES key",
    "Build a secure key generation and exchange mechanism between sender and receiver",
    "Embed the encrypted payload into a cover image using LSB steganography",
    "Implement the extraction and decryption path to recover the original data",
    "Measure imperceptibility using PSNR and SSIM against the original cover image",
    "Evaluate embedding capacity, processing time and robustness of the combined scheme",
]

# the objectives of the batch documentary (Documentary/Batch_15_...docx)
OBJECTIVES_DOC = [
    "Develop a secure system for protecting confidential data using hybrid encryption techniques",
    "Implement AES to encrypt the secret data efficiently",
    "Implement RSA to securely encrypt and exchange the AES key",
    "Hide encrypted data inside digital images using LSB steganography",
    "Extract and decrypt hidden data to recover the original information",
    "Improve data confidentiality and secure communication over digital networks",
    "Evaluate system performance using metrics such as PSNR, MSE and embedding capacity",
]

PROBLEM_STATEMENT = [
    "Encryption alone signals that sensitive data is being transmitted, inviting attack",
    "Steganography alone offers no protection once the hidden payload is discovered",
    "Symmetric encryption is fast but its key exchange remains the weak point",
    "Naive LSB embedding degrades the cover image and is detectable by steganalysis",
    "Need: a two-layer scheme that encrypts data with hybrid AES-RSA and hides the result imperceptibly inside a cover image",
]

EXISTING_SYSTEM = [
    "Encryption-only transfer (AES or RSA files sent as they are): confidential, but the ciphertext announces that a secret exists [" + str(R["katz"]) + "]",
    "Plain LSB steganography tools: the message is hidden, but anyone who finds it can read it, and plaintext bits are not random-looking [" + str(R["chan"]) + "], [" + str(R["fridrich"]) + "]",
    "Shared-key hybrids with a symmetric cipher and error correction (for example SCReedSolo): robust to some noise, but the key must be shared in advance [" + str(R["screed"]) + "]",
    "Provably secure and homomorphic constructions (ProSt): strong theory for computing on hidden bits in the cloud, not a file-transfer tool [" + str(R["base"]) + "]",
    "Transform-domain and learned hiding (DWT-DCT, chaotic encryption with a CNN): the batch survey lists them by title only [" + str(R["s_chaos"]) + "], [" + str(R["s_dwt"]) + "]",
]

LIMITATIONS_OF_EXISTING = [
    "Encryption alone cannot hide that a secret message is being sent",
    "Steganography alone gives no protection after discovery: the payload is readable",
    "Symmetric-only schemes leave key distribution open",
    "Sequential LSB replacement is flagged by chi-square and weighted-stego analysis [" + str(R["westfeld"]) + "], [" + str(R["ws"]) + "] (30 of 30 cases in our own test)",
    "The base paper's security argument targets computation on hidden bits, and it reports no PSNR, SSIM or capacity [" + str(R["base"]) + "]",
    "Several surveyed systems are only described by title in the batch survey; their results could not be verified [" + str(R["s_triple"]) + "]-[" + str(R["s_dwt"]) + "]",
]

GAPS = [
    "The surveyed work advances steganography and encryption independently, including provably secure constructions; a practical hybrid AES-RSA plus LSB file pipeline is rarely evaluated end to end",
    "Imperceptibility is usually reported for a few payloads; the dependence of PSNR on the fill ratio, and its closed-form floor, is seldom shown against measurement",
    "Capacity, processing time and the cost of the key-wrapping step are rarely reported together with the quality measures",
    "Robustness is often asserted rather than tested: which handling (JPEG, noise, resize, crop, re-encoding) destroys the payload is seldom listed",
    "Statistical detectability of the finished stego image is seldom measured on the same pipeline that is advertised as concealment",
]
