"""Chapters 9 (Conclusion) and 10 (Future scope), plus the shared helper block lists used by documents 9, 10, 12 and 15."""
import glob
import os

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, N, P, TAB
from .refs import CITE as R

S_ = F.S


def src(rel, a, b):
    """Lines a..b (1-based, inclusive) of a repository file, exactly as they stand in 8.ProjectCode."""
    with open(os.path.join(F.CODE, rel), encoding="utf-8") as f:
        lines = f.read().split("\n")
    return "\n".join(lines[a - 1:b])


def FG(prefix, caption, width=5.4):
    hits = sorted(glob.glob(os.path.join(F.FIGS, prefix + "*.png")))
    if not hits:
        return P(f"[figure {prefix} not yet produced: {caption}]")
    return FIG(hits[0], caption, width)


CRY = "backend/app/services/crypto.py"
LSB = "backend/app/services/lsb.py"
PIPE = "backend/app/services/pipeline.py"
ROB = "backend/app/services/robustness.py"
OPS = "backend/app/routes/ops.py"


# ---------------------------------------------------------------------------- novelty / contributions
def novelty_blocks():
    return [
        H2("What the base paper contributes"),
        P(f"The base paper [{R['base']}] introduces Provably Secure Homomorphic Steganography (ProSt). A client hides secret bits in the least significant bits of cover images at a secret position (r, c, k), "
          "leaving every other least significant bit as an independent random decoy. An honest-but-curious cloud provider then evaluates a Boolean circuit built only from Fredkin gates on every pixel of the images "
          "without knowing which bits are secret, and the client reads the result at the secret position of the output image. Theorem 1 of the paper shows that the adversary's advantage in learning the secret bit is of order 1/n "
          "in the number n of positions, and the authors recommend n of at least 2^20 (about 10^6). The paper reports no PSNR, SSIM or capacity, because its goal is private computation and not transmission; "
          "the only runtime given is 8.38 s for a 17-gate circuit on a 128 x 128 x 3 image."),
        H2("What is new in CipherVeil"),
        B("**An authenticated bundle format.** The `CVL1` bundle carries the file name, size and SHA-256 inside the AES-GCM layer and uses the four magic bytes as associated data, so a bundle cannot be reinterpreted as another format and the receiver can verify the restored file against the sender's hash.",
          "**A complete hybrid pipeline.** A fresh AES-256-GCM key and nonce are made for every message, the key is wrapped with the receiver's RSA public key (OAEP, SHA-256), and the bundle is hidden in a PNG. The base paper leaves key exchange as a remark; CipherVeil implements it end to end.",
          "**A measured embedder.** The 1-bit LSB embedder is capacity-aware (3.0 bits per pixel) and its imperceptibility is predicted by a closed-form model that matches measurement within 0.053 dB, which lets a user know the PSNR before sending.",
          "**An honest evaluation.** The scheme was tried against 18 attacks, two classical steganalysis detectors and 240 single-bit tamper trials, and the report states what fails: lossy handling and statistical detection.",
          "**A usable tool.** A FastAPI and React application with key management, analysis views, robustness and benchmark pages and a log that holds no secrets, backed by 39 tests."),
        H2("What is standard"),
        P(f"AES in Galois/Counter mode [{R['aes']}], [{R['gcm']}], RSA [{R['rsa']}] with OAEP padding [{R['rfc8017']}], [{R['oaep']}], least significant bit replacement [{R['chan']}], PSNR [{R['psnr']}] and SSIM [{R['ssim']}] "
          f"are established techniques used as they are. The chi-square and weighted-stego detectors [{R['westfeld']}], [{R['ws']}] are published methods applied here as attackers. None of the primitives was invented in this project; "
          "the novelty is the integration, the bundle format, the closed-form check and the evaluation."),
        H2("What is weaker than the base paper"),
        B("**No provable security.** ProSt proves a bound on the adversary's advantage for locating the secret bit. CipherVeil's security rests on AES-GCM and RSA-OAEP; the hiding layer is not provably secure and is detected by chi-square at the fill levels tested.",
          "**No hidden location.** ProSt keeps the position of the secret bit secret. CipherVeil writes from the first pixel in raster order, so anyone who knows the algorithm knows where to read; only the encryption protects the content.",
          "**No computation on hidden data.** Homomorphic evaluation with Fredkin gates is outside the scope of this project.",
          f"**Weaker than the supporting paper on robustness.** SCReedSolo [{R['screed']}] adds Reed-Solomon coding against bit corruption; CipherVeil has no error correction and loses the payload to any lossy change."),
    ]


def contribution_blocks():
    return [
        P("The contributions of the project, stated at the strength the evidence supports, are:"),
        N("**An authenticated bundle format (`CVL1`)** that carries the file name, size and SHA-256 inside the AES-GCM layer and uses the magic as associated data, so that the receiver can check the restored file and a bundle cannot be confused with another format.",
          f"**A hybrid pipeline with a fresh key per message**: AES-256-GCM with a new 256-bit key and 96-bit nonce for every message, wrapped by RSA-OAEP-SHA256 for the receiver. The file was restored byte for byte in {S_['runs']} of {S_['runs']} evaluation runs, and all 240 single-bit tamper trials were rejected.",
          f"**A capacity-aware 1-bit LSB embedder** at 3.0 bits per pixel whose closed-form PSNR model matches measurement within {F.EX['fill_study']['max_abs_dev_vs_theory_db']} dB; PSNR was never below 51.1 dB at any fill level on six covers.",
          f"**An honest evaluation**: of 18 attacks only the lossless ones survive (5 of 18), the chi-square test flags the embedded region in {F.EX['steganalysis']['chi2_total']} of {F.EX['steganalysis']['chi2_total']} cases, and the weighted-stego estimator tracks the fill; the report states these limits instead of claiming undetectability.",
          f"**A full-stack tool**: FastAPI and React with key management, send and receive, analysis, robustness and benchmark views and a secret-free log, tested by {F.PYTEST_PASSED} pytest tests and {F.SMOKE_PASSED} end-to-end smoke checks."),
        P("The novelty is the integration and the evaluation. No new cipher, embedding rule or detector is proposed."),
    ]


# ---------------------------------------------------------------------------- scope and limitations
def scope_blocks():
    return [
        H2("In scope"),
        B("**Hybrid encryption of a single file**: AES-256-GCM for the data and RSA-OAEP-SHA256 for the session key, with RSA keypairs of 2048, 3072 or 4096 bits.",
          "**Key management in the application**: generating keypairs, importing a public key (to send) or an unencrypted private key (to receive), exporting either half, and showing fingerprints.",
          "**LSB embedding in PNG covers**: one bit per R, G and B value, in raster order, with a 32-bit length header and a capacity check before embedding; files up to 25 MB can be uploaded.",
          "**Extraction and decryption**: format checks, RSA unwrap, tag verification and a SHA-256 comparison of the restored file.",
          "**Measurement**: PSNR, SSIM, MSE, capacity, bit planes, histograms and stage timings for every send; a robustness test with nine attacks; a benchmark across covers and payload sizes.",
          "**The application**: JWT sign-in, six working screens, an operation log, and a script-based evaluation (`ml/eval.py`, `scripts/run_experiments.py`) with 39 tests."),
        H2("Out of scope"),
        B("**Provable security and homomorphic computation** as in the base paper, and hiding the location of the payload.",
          "**Robustness engineering**: error-correcting codes, transform-domain (DCT or DWT) embedding or embedding that survives JPEG.",
          "**Adaptive and matching embedding** (LSB matching, syndrome-trellis codes) and resistance to modern steganalysis.",
          "**Authentication of the sender**: there are no signatures, certificates or identity checks; anyone with the public key can send.",
          "**Audio, video or document carriers**; images other than those Pillow can decode, and any transparency (the alpha channel is dropped).",
          "**Network delivery**: CipherVeil produces a PNG; how it is transported is left to the user.",
          "**Multi-user key sharing, key recovery and hardware key storage.**"),
    ]


def assumption_blocks():
    return [
        P("The results depend on the following assumptions, which are choices of the project and not findings:"),
        B("**Lossless channel.** The stego image reaches the receiver as a PNG file with pixel values unchanged. This is the only channel for which the scheme works.",
          "**Receiver's private key is safe.** The security of the content is the security of the RSA private key; here the key is kept unencrypted in the local database and the machine is assumed to be trusted.",
          "**Public keys are authentic.** The sender is assumed to hold the right public key, because there is no certificate or fingerprint-verification protocol; the application only shows the fingerprint.",
          "**Random sources are sound.** The AES key and nonce come from the operating system's random generator (`os.urandom` and the `cryptography` library).",
          "**Covers are ordinary images.** The six committed covers stand for 'ordinary-looking' images; no claim is made for images with large flat areas, saturated regions or previous JPEG compression.",
          "**Attacker model for the evaluation.** The robustness attacks are accidental or benign processing; the steganalysis is a passive attacker with a classical detector. An active attacker who rewrites the image can always destroy the payload.",
          "**Single user per run.** The measurements were taken with one user on one machine; no concurrency was tested."),
    ]


def limitation_blocks():
    fs = F.EX["fill_study"]
    return [
        P("The limitations below are properties of the delivered system and of the evidence, ordered by how much they affect the conclusions."),
        TAB("Limitations of CipherVeil and their effect", ["Limitation", "Evidence", "Effect on the conclusions"],
            [["Fragile to any lossy or geometric change", "JPEG q100, q95, q75, q50, lossy WebP, noise sigma 1, resize 90 %, grayscale, palette, rotation, flip: payload lost in every case; error rate 49-50 % where measured",
              "The stego image must travel as a PNG file; a messaging app that recompresses it destroys the message"],
             ["Detectable by statistics", "Chi-square p 0.97-1.00 on all 30 stego prefixes; weighted-stego estimate tracks the fill; sequential embedding from the first pixel",
              "Imperceptible to the eye is not undetectable; low fill is safer, not safe"],
             ["Location of the payload is public", "Raster order from pixel 0 with a 32-bit length header, no key-dependent permutation", "Secrecy rests on AES and RSA alone, not on hiding"],
             ["No sender authentication", "No signature in the bundle; any holder of the public key can send", "The receiver cannot tell who sent a message"],
             ["Unencrypted private keys at rest", "`keypairs.private_pem` is stored in clear in SQLite", "Anyone who can read `data/app.db` can open every message for that user"],
             ["Placeholder secrets and no rate limiting", "`.env` ships `JWT_SECRET=change-me-on-first-run`; no login throttle", "Acceptable for a local demo only"],
             ["Small, synthetic evaluation set", "Six covers, four small payloads, one machine", "Numbers show the behaviour of the method, not a field performance"],
             ["Capacity bounded by the image", "3.0 bits per pixel, minus a bundle overhead of 401-657 bytes", "A 200 x 200 cover holds 14.6 KiB; larger files need larger covers"],
             ["Send page crashes for an account with no keys", "`Send.jsx` uses the `KeyRound` icon without importing it (`KeyRound is not defined`, reproduced with a new account)", "A first-time user must open Keys before Send"]],
            widths=[1.6, 2.7, 2.2], align=["l", "l", "l"], size=9),
        P(f"One limitation is a strength of the evidence rather than of the system: the closed-form PSNR model matches measurement within {fs['max_abs_dev_vs_theory_db']} dB, so the imperceptibility result does not depend on which covers were chosen. "
          "The detectability and robustness results do depend on the covers, and six covers are few."),
    ]


def not_measured_blocks():
    return [
        P("The following were not measured, and nothing in the documents should be read as a result for them:"),
        B("Resistance to modern steganalysis: sample-pair, RS, rich-model or deep-learning detectors were not run; the chi-square test used the known payload length.",
          "Behaviour on camera photographs, on images that were JPEG-compressed before conversion to PNG, and on covers with flat or saturated regions.",
          "Transfer through real messaging or e-mail services, and what each of them does to a PNG.",
          "Performance with several simultaneous users, long-running stability and load behaviour of the API.",
          "Security testing of the web application: no penetration test, no review of the JWT in `localStorage`, no rate-limit test.",
          "Usability: no study with real users; the screens were exercised by a script.",
          "Energy use, memory use and mobile or embedded deployment.",
          "Any reproduction of the base paper's security proof or its homomorphic circuit evaluation."),
    ]


# ---------------------------------------------------------------------------- design walk-throughs and decisions
def walkthrough_blocks():
    return [
        H2("Building the bundle (`crypto.encrypt_bundle`)"),
        P("The function builds the header, encrypts header and file together with a fresh key and nonce, wraps the key and concatenates the fields. The header is encrypted too, so the file name and hash are not visible to anyone who finds the bundle."),
        CODE(src(CRY, 87, 101), 8),
        P("`AESGCM.generate_key(256)` and `os.urandom(12)` are called for every message. The magic `CVL1` is passed as associated data, so it is authenticated without being encrypted. "
          "`_OAEP` is OAEP with SHA-256 for both the hash and the mask function. The returned `overhead_bytes` is the difference between bundle and file size, shown on the Send screen."),
        H2("Opening the bundle (`crypto.decrypt_bundle`)"),
        CODE(src(CRY, 104, 128), 8),
        P("Every failure maps to a specific `CryptoError`: no magic, wrong key size, failed RSA unwrap, failed tag. Nothing is returned until the GCM tag has verified, and the final dictionary reports whether the recorded hash equals the hash of the restored bytes."),
        H2("Embedding and extracting (`lsb.py`)"),
        CODE(src(LSB, 35, 55), 8),
        P("The bundle is prefixed with its 32-bit length, unpacked into bits and written into the lowest bit of the first `n` colour values with one vectorised mask (`& 0xFE`) and an OR. "
          "The capacity check comes first and produces the message shown on the Send screen. `extract` reads the length, rejects a zero or impossible length, and packs the following bits back into bytes."),
        H2("The pipeline (`pipeline.py`)"),
        CODE(src(PIPE, 13, 30) + "\n    ...\n" + src(PIPE, 47, 55), 8),
        P("`hide` times encryption, embedding, PNG encoding and the quality measures separately, which is why the log can show that PNG encoding and SSIM, not the cryptography, take most of a send. "
          "`reveal` returns the extraction and decryption times separately for the same reason. The API, the benchmark and `ml/eval.py` all call these two functions, so the same code produces the screens and the numbers."),
        H2("Attacking the image (`robustness.run_attacks`)"),
        CODE(src(ROB, 76, 106), 8),
        P("Each attack is a function from image to image; the result is decided by a real extraction, a real decryption and a hash comparison, not by a bit-error threshold. "
          "The bit error rate is computed against the unattacked LSB stream only for the report. Any exception while parsing a corrupted header is caught and reported as 'lost'."),
        H2("Serving a send request (`routes/ops.py`)"),
        CODE(src(OPS, 42, 82), 8),
        P("The route accepts an uploaded file or the name of a committed sample (resolved by directory listing, never by joining the name to a path), calls `pipeline.hide`, logs success or failure, and stores the cover and stego PNGs under the operation id. "
          "Errors from the library become HTTP 400 with the library's own message, and the same message is written to the log, which is what the Send and Log screens display."),
    ]


def decision_blocks():
    return [
        P("The table lists the main implementation decisions with the reason for each and the consequence that was observed."),
        TAB("Implementation decisions and their reasons", ["Decision", "Reason", "Consequence observed"],
            [["AES-256-GCM instead of AES-CBC or CTR", "Authenticated encryption detects tampering without a separate MAC", "All 240 bit flips rejected; one primitive provides secrecy and integrity"],
             ["A new session key and nonce for every message", "Removes nonce reuse, the main way GCM fails, and limits the damage of a leaked key to one message", "50 encryptions of one file gave 50 distinct nonces and wrapped keys"],
             ["RSA-OAEP with SHA-256 for the key, default 3072 bits", "OAEP is the recommended padding; 3072 bits balances security and speed", "Unwrap takes 94 ms (3072) against 31 ms (2048) and 221 ms (4096); overhead 529 B"],
             ["Magic as GCM associated data and header inside the encrypted part", "Authenticates the format and hides file name and hash", "Bundles are not confusable; the receiver can verify the file hash"],
             ["1 LSB per R, G and B value, sequential", "Simple, fast and predictable capacity (3.0 bits per pixel); PSNR can be computed in advance", "PSNR within 0.053 dB of the model; detectable by chi-square"],
             ["32-bit length header before the bundle", "Lets the receiver know how many bits to read without scanning", "A clean image is rejected (a random 32-bit value almost always exceeds the capacity); a wrong but plausible length is caught by the magic check"],
             ["PNG output only", "Lossless compression keeps every pixel value", "Payload survives re-save and WebP lossless, not JPEG"],
             ["Capacity check before embedding", "Fail early with exact numbers instead of truncating", "Eight of 30 evaluation combinations were refused with a clear message"],
             ["Measure PSNR, SSIM and MSE in the send path", "The user should see the cost of every message", "About 300 ms of each send is spent on the measures, more than all cryptography"],
             ["Resolve sample names by directory listing", "Blocks path traversal without a deny-list", "Traversal requests return 404 in the tests"],
             ["bcrypt for passwords and HS256 JWT for sessions", "Standard, slow hashing; stateless sessions", "Login takes 287 ms; the JWT is stored in the browser, which is acceptable for a local tool"],
             ["Store private keys in the database", "Keeps the demo to one component and lets the Receive screen work after a restart", "Convenient but unsafe at rest; listed as a limitation and as future work"],
             ["Run the evaluation on the same services as the API", "One code path for numbers and screens", "`ml/eval.py`, the benchmark page and the tests agree"]],
            widths=[1.8, 2.3, 2.4], align=["l", "l", "l"], size=9),
    ]


# ---------------------------------------------------------------------------- chapter 9 and document 15 conclusion
def conclusion_blocks():
    return [
        H2("9.1 Summary of the work"),
        P(f"CipherVeil was built to show a two-layer protection for a confidential file: encryption that survives discovery of the payload, and hiding that does not announce that a secret is moving. "
          f"A file is encrypted with a fresh AES-256-GCM key, the key is wrapped with the receiver's RSA public key, and the resulting bundle is written into the least significant bits of a PNG. "
          f"The receiver extracts the bundle, unwraps the key, verifies the tag and the file hash, and obtains the original file. The work is grounded in the base paper [{R['base']}], whose LSB carrier and key-exchange framing it adopts, and not its homomorphic computation."),
        P(f"The system was evaluated and not only demonstrated. Over {S_['runs']} runs on six covers the file was restored byte for byte every time, PSNR was at least {S_['psnr_db_min']} dB (mean {S_['psnr_db_mean']} dB), "
          f"SSIM at least {S_['ssim_min']}, and capacity was 3.0 bits per pixel. A closed-form model reproduced measured PSNR within {F.EX['fill_study']['max_abs_dev_vs_theory_db']} dB, and the same measurement at full capacity gave 51.14-51.17 dB."),
        H2("9.2 Objectives achieved"),
        TAB("The six objectives and their status", ["Objective", "Status", "Headline evidence"],
            [["AES for the payload, RSA for the AES key", "Achieved", "AES-256-GCM + RSA-OAEP-SHA256; 240 of 240 tamper trials rejected"],
             ["Key generation and exchange", "Achieved for the keypair workflow", "2048, 3072, 4096-bit keys, PEM import and export; no identity check"],
             ["Embed by LSB", "Achieved", "1 bit per colour value, 3.0 bits per pixel, capacity check"],
             ["Extraction and decryption", "Achieved", "22 of 22 byte-exact restorations"],
             ["PSNR and SSIM", "Achieved", "PSNR 52.479-74.615 dB up to 73 % fill, 51.14 dB at 100 %; SSIM at least 0.9929"],
             ["Capacity, time and robustness", "Measured", "86 ms median unwrap; lossless handling only survives; detectable at medium and high fill"]],
            widths=[2.2, 1.5, 2.9], align=["l", "l", "l"], size=9.5),
        H2("9.3 Key findings"),
        N("**Encryption costs nothing in image quality.** Plain and encrypted payloads flip about 50 % of the embedded bits either way, so PSNR depends only on how many bits are embedded; encryption makes the stream balanced and unreadable.",
          "**Imperceptibility is predictable.** PSNR follows 10 log10(255^2 / (0.5 n / N)) within 0.053 dB, and never falls below 51.1 dB even at full capacity.",
          "**The scheme is robust to lossless handling only.** Of 18 attacks, 5 were survived; JPEG at quality 100 already loses the payload, and the error rate of 49-50 % leaves nothing for a correcting code to repair.",
          "**Hidden is not undetectable.** The chi-square test flagged all 30 embedded prefixes and the weighted-stego estimate followed the fill, because embedding is sequential and key-independent.",
          "**The cryptographic layer is cheap and strict.** AES-GCM takes 0.15 ms; the RSA unwrap (94 ms at 3072 bits) dominates; any single-bit change is rejected before data is released."),
        H2("9.4 Practical applications"),
        B("Sending a small confidential file (a few kilobytes to a few hundred kilobytes) as an ordinary-looking PNG over a channel that does not recompress images.",
          "A teaching tool that shows PSNR, SSIM, histograms and bit planes for real data, and what lossy processing does to a hidden payload."),
        H2("9.5 Known limitations"),
        P("The payload is lost to any lossy change and the images can be flagged statistically; the private keys are unencrypted at rest; there is no sender authentication; the evaluation uses six covers and four small synthetic payloads on one machine. "
          "These are listed with their evidence in Chapters 8 and 10."),
        H2("9.6 Lessons learned"),
        B("A closed-form model is worth deriving: it turned PSNR from a result into a check.",
          "Perceptual quality is the wrong proxy for security; the chi-square test found the data in images with PSNR above 57 dB.",
          "Measure the whole request: the cryptography took 0.15 ms and a send took 438 ms because of PNG encoding and SSIM."),
        H2("9.7 Concluding remarks"),
        P("CipherVeil delivers a working, tested, double-layer protection tool whose strengths and weaknesses are both measured. The honest reading is a sound hybrid encryption layer with a simple hiding layer on top: "
          "the content is protected by standard cryptography, the concealment is good to the eye and weak to statistics, and the image must stay a PNG."),
    ]


def chapter9_blocks():
    from .blocks import renum
    return [H1("CHAPTER 9: CONCLUSION")] + renum(conclusion_blocks(), "9")


# ---------------------------------------------------------------------------- chapter 10 and document 15 future scope
def future_blocks():
    return [
        H2("10.1 Improvements to the existing system"),
        N("**Key-dependent pixel selection.** Derive a pseudo-random permutation of the embedding positions from a shared secret (or from the session key) so that the payload is no longer in raster order; this moves towards the location secrecy of the base paper and defeats the oracle chi-square test on the prefix.",
          f"**LSB matching and adaptive embedding.** Replace LSB replacement by +/-1 matching [{R['mielikainen']}] and by cost-based embedding with syndrome-trellis codes [{R['stc']}], which change fewer values and avoid the pair-equalisation signature of replacement.",
          f"**Error correction.** Add Reed-Solomon coding, as in SCReedSolo [{R['screed']}], so that mild bit corruption can be repaired; JPEG itself would still need transform-domain embedding.",
          "**Sender signatures.** Sign the bundle with Ed25519 or RSA-PSS so that the receiver learns who sent it and a message cannot be forged by anyone who holds the public key.",
          "**An encrypted key store.** Protect private keys at rest with a passphrase-derived key (scrypt or Argon2) or an operating-system store, and add rate limiting and a generated `JWT_SECRET`."),
        H2("10.2 Additional features"),
        B("**Compression before encryption** to increase the effective capacity, and a choice of fill levels with a warning when the estimated detectability is high.",
          "**Post-quantum key transport**: a KEM such as ML-KEM next to or instead of RSA-OAEP.",
          "**More carriers**: audio (WAV) and video frames, and JPEG-domain embedding for channels that recompress.",
          "**Multiple recipients**: wrap the same session key for several public keys in one bundle.",
          "**Fix the empty-key crash** on the Send page and add an assertion-based browser test suite."),
        H2("10.3 Scalability and deployment"),
        B("Move the quality measures (SSIM, PNG encoding) off the request path, since they cost about 300 ms of each send and cryptography costs 0.15 ms.",
          "Replace SQLite by a server database with row-level ownership, store the stego images in object storage and add a job queue for large covers.",
          "Package the backend and the console as containers and serve both behind TLS; the demonstration runs as two local processes."),
        H2("10.4 Further research"),
        B("Evaluate against stronger steganalysis (sample-pair, RS, rich-model and deep detectors) at several fill levels, and report detection error against fill as the base paper's security view would require.",
          "Bring the base paper's secret-position idea into the pipeline: hide the payload bits among decoys with a keyed location generator and measure the capacity cost of the added security.",
          "Run a formal usability study with real senders and receivers, including how they move PNG files through ordinary channels.",
          "Measure on a larger corpus of camera photographs, including previously compressed images."),
    ]


def chapter10_blocks():
    return [H1("CHAPTER 10: FUTURE SCOPE")] + future_blocks()
