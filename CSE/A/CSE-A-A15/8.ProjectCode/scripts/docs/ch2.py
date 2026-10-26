"""Chapter 2: Literature survey."""

from . import facts as F
from . import lit
from .blocks import B, H1, H2, H3, N, P, TAB
from .refs import CITE as R


def blocks():
    base = R["base"]
    sa = F.EX["steganalysis"]

    def c(*keys):
        return ", ".join(f"[{R[k]}]" for k in keys)

    out = [
        H1("CHAPTER 2: LITERATURE SURVEY"),
        H2("2.1 Overview"),
        P("The survey has four purposes: to understand the base paper in depth, to place it among the work on steganography, steganalysis and hybrid encryption-plus-hiding schemes, "
          "to identify the algorithms and measures worth reusing, and to find the gap CipherVeil fills. The base paper was read in full from the PDF kept in the batch folder, together with its "
          f"reference list. Two further papers archived with the batch were read from their PDFs: SCReedSolo {c('screed')}, a symmetric-cipher, Reed-Solomon and LSB framework, and a study of "
          f"memristive lightweight ciphers used for image steganography {c('memr')}. The batch literature survey names four more papers ({c('s_triple', 's_object', 's_chaos', 's_dwt')}); "
          "only their titles, years and sources are known, so they are described from their titles and nothing is claimed for them beyond that. The standards and classic papers cited for "
          "the cryptographic and steganalytic background are the usual primary sources."),
        H2("2.2 Base Paper Analysis"),
        P(f"**Title.** {lit.BASE_PAPER_TITLE}. **Authors and venue.** {lit.BASE_PAPER_VENUE}, pp. 14393-14409 (received October 2025, accepted January 2026), doi 10.1109/ACCESS.2026.3656995 {c('base')}. "
          "The authors work in the Secure and Correct Systems Laboratory of Johannes Kepler University Linz."),
        H3("2.2.1 Aim and approach"),
        P("The paper starts from the cloud-outsourcing problem: a client wants an untrusted provider to compute on sensitive data. Fully homomorphic encryption allows this but at a high computational cost "
          f"{c('gentry')}, and trusted execution environments depend on particular hardware and are exposed to side-channel attacks {c('sgx')}. The authors propose a third route, **provably secure homomorphic "
          "steganography (ProSt)**. The client hides secret bits in the least significant bits of cover images and sends the images to a provider that knows it is processing hidden data but not "
          "where the secret bits are. Steganography is therefore used not to hide that a message exists, which the scheme deliberately gives up, but to hide the location and meaning of the secret bits "
          "among a large number of decoy bits."),
        H3("2.2.2 Construction"),
        P("ProSt is a tuple of four algorithms. **LocGen** draws a secret position (row, column, colour channel) uniformly at random from the h x w x 3 possibilities; the position acts as a symmetric key shared by "
          "the sender and the intended recipient. **Emb** writes a secret bit into the LSB of the pixel value at that position and leaves every other LSB as an independent random decoy. **Comp** lets the provider "
          "evaluate a Boolean circuit built only from Fredkin gates pixel by pixel over all positions, so the secret and the decoys receive the same operation. **Ext** reads the result bit at the known position. "
          "The Fredkin gate F(c, x, y) swaps x and y when the control bit c is 1; it is reversible and universal, and it keeps the number of ones unchanged (the paper's Lemma 1), which preserves the statistics of the "
          "LSB plane through any number of gates. A small domain-specific language lets circuits be written with AND, OR and NOT and compiled to Fredkin gates."),
        H3("2.2.3 Threat model and security result"),
        P("The adversary is an honest-but-curious, computationally unbounded provider. It knows the cover images, the circuit, the prior distribution of the secret and the embedding method, but not the secret positions; "
          "active attacks and several stego images of the same secret are excluded. Theorem 1 shows that a secret bit hidden at a uniformly random position among n LSBs gives the adversary an advantage of order 1/n over its prior "
          "knowledge, and Corollary 1 shows that this is preserved over any number of Fredkin gates. The authors are careful about what \"negligible\" means here: 1/n is statistically small but not cryptographically negligible, "
          "so they recommend n of at least 2^20 (about one million) for an advantage below 10^-6; a single 1024 x 1024 x 3 image gives n of about 3.1 million and four such images about 12.6 million. "
          "Hiding of the circuit's logic is heuristic only, and the paper states that no formal circuit privacy is proved."),
        H3("2.2.4 Implementation and reported performance"),
        P("The implementation is a Python and NumPy program. On a 128 x 128 x 3 image (49,152 values) with a circuit of 17 gates and 61 wires, run on an HP EliteBook with an Intel Core i5-1135G7 and 16 GB of RAM, "
          "the provider's total gate-execution time was 8.38 seconds. The authors extrapolate about 16.5 seconds for 34 gates and about 33 seconds for a 256 x 256 x 3 image, and suggest GPU acceleration as a way to reach 1 to 2 seconds. "
          "Their comparison with other steganography and homomorphic-encryption works uses runtimes that they adjusted or estimated from published complexity; the paper reports no PSNR, SSIM, MSE or embedding-capacity figures, "
          "because its security goal is the location of the secret and not statistical undetectability."),
        TAB("The base paper and CipherVeil side by side", ["Aspect", "ProSt (base paper)", "CipherVeil (this project)"],
            [["Goal", "Compute on hidden bits in an untrusted cloud", "Move a confidential file from a sender to a receiver"],
             ["What is hidden", "A few secret bits among n random decoy LSBs", "A whole encrypted bundle, written sequentially from the first pixel"],
             ["Role of encryption", "None (the paper's footnote assumes steganography is not combined with encryption)", "AES-256-GCM for the data; RSA-OAEP wraps a fresh key per message"],
             ["Key", "Secret position (r, c, k), shared out of band", "Receiver's RSA keypair; only the public half is shared"],
             ["Security statement", "Adversary advantage of order 1/n (Theorem 1); heuristic circuit privacy", "Confidentiality and integrity from AES-GCM and RSA-OAEP; no proof of undetectability"],
             ["Quality measures", "Not reported", "PSNR, SSIM, MSE, histograms, bit planes for every operation"],
             ["Reported cost", "8.38 s for 17 gates on 128 x 128 x 3", "Median encrypt 0.15 ms, embed 0.25 ms, RSA-3072 unwrap and decrypt 86 ms"],
             ["Implementation", "Python and NumPy demonstration", "FastAPI and React application, 39 tests"]],
            widths=[1.2, 2.5, 2.7], align=["l", "l", "l"], size=9.5),
        H3("2.2.5 Limitations stated by the authors and observed here"),
        B("Circuit privacy is heuristic: the topology is known to the provider and statistical analysis of gate frequencies could leak information.",
          "The advantage 1/n is statistically negligible only for very large n; small images give weak security.",
          "Storage and transfer overhead is high because the demonstration allocates one image per wire; runtime scales with the number of gates and the image area.",
          "Only passive (honest-but-curious) adversaries and a single-shot model are covered; active attacks are future work.",
          "No imperceptibility or capacity evaluation is given, so a reader cannot judge visual quality or payload size from the paper."),
        H3("2.2.6 What CipherVeil adopts and what it changes"),
        P("CipherVeil adopts the paper's carrier (the LSB plane of an RGB image), its idea that decoy-like random bits are what makes the LSB plane safe to write, and its use of a key to be shared with the recipient. "
          f"One observation links the two works: the paper needs the surrounding bits to look like independent random decoys, and an AES-GCM ciphertext is exactly that kind of bit stream. In our measurement the embedded stream has a fraction of "
          "ones between 0.49 and 0.51 for encrypted bundles, against 0.42 to 0.46 for the plain files. CipherVeil does not use secret positions, Fredkin gates or any computation on hidden data, and it makes no claim of "
          "provable security. Its numbers therefore cannot be set beside the paper's runtime or its advantage bound; where conditions differ, Chapter 8 says so."),
        H3("2.2.7 Critical assessment"),
        P("The paper's strength is a clear security model and an argument that is easy to check: with n equally likely positions, the best the adversary can do is guess. Its weaknesses are the ones the authors list, plus two: "
          "the argument rests on the decoy bits being independent random values, which a natural image's LSB plane usually is not (in our chi-square tests the untouched LSB plane of most covers differs clearly from random), and the demonstration "
          "is a small proof of concept with no quality or capacity evaluation. These are not faults of the paper's aim, which is secure outsourcing, but they define the room left for a practical, measured hiding pipeline."),
        H2("2.3 Related Work by Theme"),
        P("The related work is grouped by the capability it supplies, mirroring the modules of CipherVeil: hiding data in images, detecting hidden data, the cryptographic building blocks, and schemes that combine encryption with hiding."),
        H3("2.3.1 Hiding data in images"),
        P(f"Fridrich's monograph {c('fridrich')} and the textbook of Cox et al. {c('cox')} set out the principles: capacity, distortion and detectability pull against one another. Provos and Honeyman {c('provos')} give an accessible "
          f"introduction to the methods and to their detection. Chan and Cheng {c('chan')} study simple LSB substitution and add a pixel-adjustment step that lowers the embedding error; Mielikainen {c('mielikainen')} revisits "
          "LSB matching, which changes pixel values by plus or minus one so that fewer values change than in plain replacement. Filler, Judas and Fridrich "
          f"{c('stc')} embed with syndrome-trellis codes that minimise a distortion cost, the basis of modern adaptive schemes. Cachin {c('cachin')} gives the information-theoretic definition of a secure steganographic "
          "system, in which the stego and cover distributions differ by a small relative entropy. CipherVeil sits at the simple end of this range: sequential substitution of one bit per colour value, chosen for "
          "its capacity (3 bits per pixel) and its transparency."),
        H3("2.3.2 Detecting hidden data"),
        P(f"Westfeld and Pfitzmann {c('westfeld')} showed that replacing least significant bits with random-looking bits equalises the frequencies of the value pairs (2k, 2k+1), which a chi-square test detects. "
          f"Fridrich, Goljan and Du {c('rs')} introduced RS analysis for colour and grayscale images, and Dumitrescu, Wu and Wang {c('spa')} sample pair analysis; both estimate the length of the hidden message. "
          f"Fridrich and Goljan {c('ws')} derived a weighted-stego estimator, which Ker and Bohme {c('wsrev')} refined with better weights. These methods are why a PSNR above 50 dB is not a security statement. "
          f"CipherVeil applies the chi-square test and an unweighted weighted-stego estimate to its own output (Chapter 8): the chi-square statistic flags the embedded region in {sa['chi2_total']} of {sa['chi2_total']} cases."),
        H3("2.3.3 Cryptographic building blocks"),
        P(f"AES is specified in FIPS 197 {c('aes')} and the Galois/Counter Mode in NIST SP 800-38D {c('gcm')}, which recommends a 96-bit nonce and produces an authentication tag together with the ciphertext. "
          f"RSA {c('rsa')} is used for key transport with OAEP padding, specified in PKCS #1 version 2.2 {c('rfc8017')} and introduced by Bellare and Rogaway {c('oaep')}. Katz and Lindell {c('katz')} give the "
          "security definitions behind the hybrid construction: an authenticated symmetric cipher for the bulk data and a public-key scheme for its key. CipherVeil uses these standard primitives as implemented in a widely "
          "reviewed library and designs none of its own."),
        H3("2.3.4 Schemes that combine encryption with hiding"),
        P(f"SCReedSolo {c('screed')} is the closest companion work. It shuffles the message randomly, encrypts it with the Fernet symmetric cipher, adds Reed-Solomon error-correction codes and hides the result by LSB "
          "substitution at 3 bits per pixel. It reports a PSNR of 51.774 dB and an SSIM of 0.996 for the complete works of Shakespeare (5,458,195 characters) hidden in a 14589 x 8423 x 3 telescope image, 57.653 dB and 0.936 for "
          "audio in a 21188 x 30328 x 3 image, and 52.888 dB and 0.996 for a 100 x 100 x 3 image hidden in a 512 x 512 test image. The error-correcting codes let it survive noise that alters no more than half of the "
          "correction bits, and the authors report that it is not flagged by the passive steganalysis tools they tried. Its limitation for a file-transfer setting is that the key is symmetric and must be shared beforehand. "
          f"The study of Fatemieh, Alizadeh and Zarezadeh {c('memr')} implements the stream ciphers Trivium and Grain-128a on memristive in-memory logic and reports up to 42 % and 44 % lower energy; it tests the circuits in an "
          "LSB application on five 256 x 256 grayscale images and quotes the usual rule that a PSNR above 30 dB is indistinguishable to the eye. It is hardware-level work and offers no file-transfer pipeline."),
        P(f"The batch survey lists four further papers {c('s_triple', 's_object', 's_chaos', 's_dwt')}. Their titles indicate, in order, a triple-layer data-hiding scheme using visual cryptography, a general paper on hiding data "
          "using an image object, a hybrid of chaotic encryption and a convolutional network for robust hiding, and AES encryption with a hybrid DWT-DCT transform. They show that the field mixes spatial-domain and "
          "transform-domain hiding with several encryption layers, but their authors, datasets and results could not be verified and are not quoted."),
        H3("2.3.5 Measuring the result"),
        P(f"PSNR, defined from the mean squared error between cover and stego image, is the standard imperceptibility measure; Huynh-Thu and Ghanbari {c('psnr')} discuss the scope within which it is valid. SSIM {c('ssim')} "
          "compares local luminance, contrast and structure and tracks perceived quality more closely. CipherVeil reports both, with the MSE, the largest change of any value, and the fraction of values changed."),
        H3("2.3.6 Synthesis"),
        P("Three observations follow. First, the field's tools are mature and standard: AES-GCM, RSA-OAEP, LSB substitution and the PSNR and SSIM measures. Second, the published combinations either share a symmetric key in advance "
          "(SCReedSolo) or address a different problem (ProSt computes on hidden bits; the memristive work is hardware), so a key-wrapped file pipeline measured end to end is a distinct and modest contribution. Third, hiding and "
          "detecting are studied by different papers; a hiding paper rarely reports how its own output fares under chi-square or weighted-stego analysis, which is the test CipherVeil adds."),
        TAB("Related work compared", ["Work", "Year", "Approach", "Finding / limitation"], lit.LIT_TABLE, widths=[1.5, 0.5, 2.2, 2.2], align=["l", "c", "l", "l"], size=9),
        H2("2.4 Datasets and Algorithms Used"),
        H3("2.4.1 Data"),
        P("CipherVeil does not train a model and needs no dataset. Its test material is six cover images and four payload files, all committed to the repository and regenerated by a seeded script. Five covers come from the "
          "scikit-image sample data (a NASA astronaut photograph in the public domain, a cat photograph, a coffee-cup photograph and a small crop of it, and a rocket photograph; the cat and coffee images are CC0) and one is a "
          "procedurally generated landscape. The payloads are a CSV file of 2,774 bytes, a 21,517-byte memo in PDF form, a 169-byte text file and a 99-byte JSON file, all synthetic and generated for the project. Any image "
          "or file uploaded at run time can be used instead, up to 25 MB."),
        H3("2.4.2 Algorithms"),
        B(f"**AES-256-GCM** {c('aes', 'gcm')}: authenticated encryption of the file with a fresh 256-bit key and a 96-bit random nonce; the magic bytes are bound as associated data.",
          f"**RSA-OAEP with SHA-256** {c('rsa', 'rfc8017')}: wraps the 32-byte session key for the receiver; key sizes of 2048, 3072 (default) and 4096 bits.",
          f"**LSB substitution** {c('provos', 'chan')}: one bit per colour value, row by row, preceded by a 32-bit length field; PNG output so that no lossy coding follows.",
          "**SHA-256**: a hash of the original file travels inside the encrypted header and is compared with the hash of the restored file.",
          f"**Chi-square and weighted-stego analysis** {c('westfeld', 'ws')}: used in the evaluation to measure detectability, not in the product's embedding path."),
        H3("2.4.3 Evaluation measures"),
        P("**PSNR** is 10 log10(255^2 / MSE) over all RGB values; **SSIM** is computed per colour channel and averaged; **capacity** is (width x height x 3 - 32) / 8 bytes, that is 3.0 bits per pixel; **fill ratio** is "
          "the share of capacity used. **Robustness** is a binary outcome per attack: after the attack, extraction and decryption are attempted with the real private key and the recovered file's SHA-256 is compared "
          "with the original; the LSB error rate is the share of the first bundle-length bits that differ. **Tamper evidence** counts single-bit flips that were refused. Chapter 6 gives the formulas."),
        H2("2.5 Strengths and Limitations of Existing Work"),
        TAB("Strengths and limitations of the main approaches", ["Approach", "Strengths", "Limitations"],
            [["Encryption only", "Strong confidentiality and integrity with AES-GCM and RSA-OAEP", "Ciphertext reveals that a secret exists"],
             ["Plain LSB hiding", "Simple, 3 bits per pixel, invisible to the eye", "Payload readable once found; flagged by chi-square and weighted-stego tests; lost on any lossy change"],
             ["Shared-key encryption + Reed-Solomon + LSB (SCReedSolo)", "Large payloads; survives some noise; high PSNR on large covers", "Symmetric key must be shared; more complex payload coding"],
             ["Provably secure homomorphic steganography (ProSt)", "Formal advantage bound; computation on hidden bits; hardware-independent", "Not a file-transfer tool; heuristic circuit privacy; no quality or capacity figures; slow in Python"],
             ["Adaptive embedding (syndrome-trellis codes)", "Lower detectability for the same payload", "Coding complexity; not evaluated here"],
             ["Transform-domain and learned hiding (survey titles)", "Possibly more robust to compression", "Details not verified"]],
            widths=[2.0, 2.2, 2.3], align=["l", "l", "l"], size=9.5),
        H2("2.6 Research Gap"),
        P("The surveyed work advances steganography and encryption independently, including provably secure constructions. The gap is a practical hybrid AES-RSA plus LSB pipeline evaluated end to end on capacity, "
          "imperceptibility and speed. Beyond that headline gap, four narrower gaps follow from the survey:"),
        N(*lit.GAPS[1:]),
        P("CipherVeil addresses the headline gap by building and testing the pipeline; the first narrow gap by measuring PSNR against the fill ratio for six covers and seven fill levels and comparing it with the closed-form "
          "floor; the second by reporting capacity, per-stage times and the cost of three RSA key sizes; the third by listing eighteen attacks and their outcomes; and the fourth by running two steganalysis tests "
          "against its own stego images and reporting the result even though it is unfavourable."),
        H2("2.7 Summary"),
        P("The base paper supplies the carrier idea, the role of random decoy bits and a formal way to think about hiding the location of a secret. The companion papers supply the combination of a cipher with LSB hiding and "
          "the habit of reporting PSNR and SSIM. The classical steganalysis papers supply the tests that show where plain LSB replacement is weak. What is missing, and what CipherVeil attempts, is one working "
          "pipeline in which a file is encrypted, wrapped for a receiver, hidden, recovered and verified, with every claim measured and every limit stated."),
    ]
    return out
