"""Chapter 1: Introduction."""

from . import facts as F
from . import lit
from .blocks import B, FIG, H1, H2, N, P, TAB
from .refs import CITE as R


def _n(*keys):
    return ", ".join(f"[{R[k]}]" for k in keys)


def blocks():
    S = F.S
    ex = F.EX
    fs = ex["fill_study"]
    tam = ex["tamper_study"]
    sa = ex["steganalysis"]
    ro = F.EV["robustness"]
    survived_core = sum(1 for r in ro if r["recovered"] == 6)            # lossless re-save and bottom crop
    survived_extra = sum(1 for r in ex["extra_attacks"] if r["recovered"] == r["of"])
    n_attacks = len(ro) + len(ex["extra_attacks"])
    n_survive = survived_core + survived_extra
    base = R["base"]
    out = [
        H1("CHAPTER 1: INTRODUCTION"),
        H2("1.1 Domain Overview"),
        P("This project belongs to cyber security and information security. Two older disciplines meet in it. **Cryptography** makes the content of a message unreadable to anyone "
          f"without the key; its standard tools are the symmetric cipher AES {_n('aes')}, used in the authenticated Galois/Counter mode {_n('gcm')}, and the public-key system RSA {_n('rsa')} "
          f"with OAEP padding {_n('rfc8017', 'oaep')}. **Steganography** hides the fact that a message exists by placing it inside an ordinary carrier such as a photograph {_n('fridrich', 'cox')}. "
          "A cryptographic message is obviously secret, however well protected; a steganographic message looks ordinary, however easily read once found. The two protect different things, which is why "
          "combining them is an old and natural idea."),
        P(f"The simplest carrier is a digital image and the simplest hiding method is **least-significant-bit (LSB) substitution** {_n('provos', 'chan')}: each colour value of a pixel is a number from 0 to 255, and "
          "replacing its lowest bit changes the value by at most one, a difference the eye cannot see. A 512 x 512 colour image therefore offers 786,432 value positions, each able to carry one bit. "
          "The price is fragility and detectability: LSB data lives only in the exact pixel values, and statistical tests can notice that the lowest bit plane has been overwritten by random-looking bits "
          f"{_n('westfeld', 'rs', 'spa')}. Image quality after hiding is measured by the **peak signal-to-noise ratio (PSNR)** and the **structural similarity index (SSIM)** {_n('psnr', 'ssim')}."),
        P("Terms used throughout: the **cover** is the original image and the **stego image** the one carrying data; the **bundle** is the byte string that CipherVeil hides (a magic marker, the RSA-wrapped "
          "session key, a nonce, and the AES-GCM ciphertext with its tag); **capacity** is the number of bundle bytes a cover can hold; and **fill ratio** is the share of that capacity actually used."),
        H2("1.2 Background and Motivation"),
        P("Sensitive information is exchanged over the Internet constantly, and interception is a standing risk. Encryption protects the content of a message but reveals that a secret message exists: "
          "an encrypted attachment is an invitation to attack, to surveillance of who talks to whom or to legal pressure to hand over the key. Steganography hides the existence of the message, but a hiding method "
          "on its own offers no protection once the payload is discovered, because a plain message is readable by whoever finds it. Using both together gives two independent layers: an observer must first suspect "
          "and find the hidden data, and then break the encryption."),
        P("Hybrid encryption removes the key-distribution weakness of a purely symmetric scheme. A fast symmetric cipher encrypts the bulk data under a fresh random key, and a public-key system encrypts only "
          f"that key for the receiver {_n('katz')}. The sender needs nothing but the receiver's public key, so no secret has to be shared in advance. AES-GCM adds authentication: any change to the "
          "ciphertext is detected before a single byte is released. Hiding the resulting bundle in a PNG image, which is lossless, makes the transfer look like the sending of an ordinary picture."),
        P(f"The base paper of this batch, ProSt by Ahmad and Rass {_n('base')}, shows how far the LSB idea can be pushed theoretically: it hides secret bits at a secret position among random decoy bits "
          "and lets an untrusted cloud compute on them with reversible Fredkin gates, with a security argument about the adversary's advantage. It is not a file-transfer tool and it reports no PSNR, SSIM or capacity. "
          "The gap the batch identifies is the practical counterpart: a hybrid AES-RSA plus LSB pipeline that is built as a working application and evaluated end to end on capacity, imperceptibility and speed. "
          "That is the motivation for CipherVeil."),
        H2("1.3 Problem Statement"),
        P("Encryption alone signals that sensitive data is being transmitted, inviting attack. Steganography alone offers no protection once the hidden payload is discovered. Symmetric encryption is fast but its "
          "key exchange remains the weak point. Naive LSB embedding degrades the cover image and is detectable by steganalysis."),
        P("**The problem addressed in this report** is to design, build and evaluate a two-layer data-protection system that encrypts a file with hybrid AES-RSA encryption, hides the result imperceptibly inside a "
          "cover image, recovers the file byte for byte at the receiver, and states with measurements how much of the claimed protection survives imperceptibility tests, capacity limits, lossy handling "
          "of the image and statistical steganalysis."),
        P("The problem is broken into five questions that the later chapters answer with measurements:"),
        N("How invisible is the hidden data? How does the PSNR depend on how full the cover is, and is there a floor?",
          "How much can a cover hold, and what does the key-wrapping step cost in bytes and in time?",
          "Is the combined scheme tamper-evident: does any change to the stego image, the key or the length field prevent the file from being released?",
          "Which kinds of image handling destroy the payload, and which leave it intact?",
          "Is the hidden payload invisible to a statistical test, or only to the eye?"),
        H2("1.4 Need for the Project"),
        B("**A single layer is not enough.** Encryption without hiding announces a secret; hiding without encryption leaves the secret readable once found. The project builds and measures both layers together.",
          "**Key exchange must not need a shared secret.** A fresh AES session key per message, wrapped by the receiver's RSA public key, means the sender needs only a public key and one leaked message key never opens another message.",
          "**Imperceptibility has to be measured, not assumed.** PSNR and SSIM against the original cover, and bit planes and histograms, show where the change lives and how large it is.",
          "**Robustness claims must be tested.** Whether a hidden payload survives re-saving, JPEG, noise, resizing and cropping is an experimental question; the project answers it for eighteen cases.",
          "**Users need a tool, not a script.** A sender and a receiver need key management, a capacity check before embedding, a download of the stego PNG and a verifiable result, which is why the project ships a web application."),
        H2("1.5 Objectives"),
        P("The objectives come from two batch documents: the six objectives of the batch objectives sheet and the seven in the project documentary. The table below lists the six and records "
          "where each stands at the end of the project; the documentary objectives are covered in the paragraph after the table."),
        TAB("Objectives of the batch objectives sheet and their status", ["No.", "Objective", "Status at the end of the project"],
            [["1", lit.OBJECTIVES[0], "Met: AES-256-GCM for the payload, RSA-OAEP (SHA-256) for the session key"],
             ["2", lit.OBJECTIVES[1], "Met in part: RSA 2048/3072/4096 keypairs, PEM import and export, fingerprints; no key-agreement protocol or identity check"],
             ["3", lit.OBJECTIVES[2], f"Met: 1 bit per colour value, {S['max_capacity_bits_per_pixel']} bits per pixel, capacity check before embedding"],
             ["4", lit.OBJECTIVES[3], f"Met: {S['runs']} of {S['runs']} round trips byte-exact; wrong key, flipped bit or missing payload is refused"],
             ["5", lit.OBJECTIVES[4], f"Met: PSNR {S['psnr_db_min']:.1f} to 74.6 dB up to 73 % fill and 51.1 dB at full capacity; SSIM {S['ssim_min']:.4f} to 0.99999 in the core evaluation"],
             ["6", lit.OBJECTIVES[5], f"Met with stated limits: capacity and timings measured; only lossless handling preserves the payload; chi-square flags {sa['chi2_total']} of {sa['chi2_total']} test cases"]],
            widths=[0.5, 2.7, 3.1], align=["c", "l", "l"], size=10),
        P("Of the seven documentary objectives, the first to fifth (a hybrid-encryption system, AES for the data, RSA for the key, LSB hiding, extraction and decryption) are implemented and tested. The sixth "
          "(better confidentiality and secure communication) is supported by the tamper results but is a property of the scheme under the stated assumptions, not a separate measurement. The seventh "
          "(PSNR, MSE and embedding capacity) is met: all three are computed for every operation and reported in Chapter 8."),
        H2("1.6 Scope"),
        P("The system covers one workflow from a sender to a receiver. The receiver generates or imports an RSA keypair and gives the public half to the sender. The sender chooses a file (up to 25 MB) and a cover "
          "image, and the system encrypts, checks capacity, embeds and returns a PNG. The receiver extracts, unwraps the key, verifies the GCM tag and the stored SHA-256 and obtains the file back. An analysis page "
          "reports PSNR, SSIM, MSE, histograms and bit planes; a robustness page attacks the stego image; a benchmark page measures capacity and speed across covers; and a log records every operation without secrets. "
          "A FastAPI service and a React console tie the parts together; Chapters 5 and 6 give the design and implementation."),
        FIG(F.diag("02_high_level_workflow.png"), "High-level workflow of CipherVeil: key exchange, encrypt, wrap, embed at the sender, and extract, unwrap, decrypt, verify at the receiver.", 5.2),
        P("Out of scope are audio and video carriers, adaptive (edge-aware) or key-driven embedding, error-correcting codes, digital signatures and sender authentication, hardware key storage, the provable-security "
          "and homomorphic-computation parts of the base paper, and any formal security proof. Section 1.8 and Chapter 9 return to these."),
        H2("1.7 Contributions"),
        N("**An authenticated bundle format (CVL1).** The file name, size and SHA-256 travel inside the AES-GCM layer and the four-byte magic is used as associated data, so a modified bundle, a wrong key or a different file is refused before anything is released.",
          f"**A hybrid pipeline with a fresh key per message.** A new AES-256-GCM key and nonce are generated for every message and wrapped with RSA-OAEP-SHA256. The pipeline is byte-exact in {S['runs']} of {S['runs']} evaluation runs and tamper-evident in {tam['trials'] - tam['accepted_with_wrong_data']} of {tam['trials']} single-bit flips.",
          f"**A capacity-aware 1-bit LSB embedder with a closed-form quality model.** Capacity is {S['max_capacity_bits_per_pixel']} bits per pixel; the closed-form PSNR for the number of embedded bits matches the measurement within {fs['max_abs_dev_vs_theory_db']} dB over 6 covers, 7 fill levels and 5 payload seeds, and the PSNR never falls below 51.1 dB at any fill.",
          f"**An honest evaluation.** Of {n_attacks} attacks tried, {n_survive} leave the payload intact (lossless re-encodings and a crop of the bottom rows); every lossy or geometric change destroys it. A chi-square test flags the embedded region in {sa['chi2_total']} of {sa['chi2_total']} cases and a weighted-stego estimate follows the fill ratio, so hidden from the eye is not hidden from statistics.",
          f"**A full-stack tool.** A FastAPI and React application with key management, send, receive, analysis, robustness and benchmark views and an operation log that never records secrets, checked by {F.PYTEST_TOTAL} pytest tests and {F.SMOKE_TOTAL} smoke checks."),
        P("The novelty is integration and evaluation, not new primitives: AES-GCM, RSA-OAEP and LSB substitution are standard. What is new here is the combination in one authenticated format, the closed-form "
          "quality model checked against measurement, and a candid account of what the scheme does and does not survive."),
        P(f"The headline measurements are these. In the core evaluation (6 covers, payloads of 1 to 128 KiB, RSA-3072) {S['runs']} runs fit and {S['runs_skipped_too_large']} are blocked by the capacity check. "
          f"PSNR is {S['psnr_db_min']:.1f} dB at the minimum and {S['psnr_db_mean']:.1f} dB on average, SSIM {S['ssim_min']:.4f} at the minimum. Median times are {S['median_encrypt_ms']} ms to encrypt, "
          f"{S['median_embed_ms']} ms to embed, {S['median_extract_ms']} ms to extract and {S['median_decrypt_ms']} ms to unwrap the key and decrypt: the cost of the scheme is the RSA private-key operation, not the hiding. "
          "These figures are examined in Chapter 8."),
        P(f"Against the base paper {_n('base')} the contribution is a different and complementary one. ProSt gives a theoretical security argument for computing on hidden bits; CipherVeil gives a measured, working "
          "file-transfer pipeline. The two cannot be compared on speed or security: ProSt reports 8.38 seconds for a 17-gate circuit on a 128 x 128 x 3 image, a different task from moving a file, and no PSNR, SSIM or capacity."),
        H2("1.8 Limitations and Assumptions"),
        B("**LSB data survives only lossless handling.** One JPEG pass (even at quality 100), noise, resizing, rotation, flipping or colour reduction destroys the payload; there is no error correction. The stego image must travel as a PNG file.",
          f"**The hiding is detectable by statistics.** Embedding is sequential from the first pixel and independent of any key; chi-square analysis flags {sa['chi2_total']} of {sa['chi2_total']} test cases and weighted-stego analysis estimates the embedded fraction. Low fill ratios are safer, not safe.",
          "**Private keys are stored unencrypted** in the local SQLite database; the JWT signing secret ships as a placeholder; there is no login rate limit.",
          "**No sender authentication.** Anyone who has the public key can send; the receiver cannot tell who. There is no signature, certificate or identity check.",
          "**Only image carriers** (PNG, RGB, alpha dropped), a 25 MB upload cap, and six committed cover images with four small synthetic payloads; no camera photographs and no large corpus.",
          "**One machine.** Everything was measured on an Intel Core i5-12500 with 15.7 GB of RAM and no GPU; absolute milliseconds vary by roughly 10 to 30 % between runs.",
          "**Assumed:** the receiver's private key is kept secret and the receiver's public key is obtained over a channel the sender trusts; the stego image is delivered as an unmodified PNG file; the attacker has not been given the private key."),
        H2("1.9 Organisation of the Report"),
        P("**Chapter 2** surveys the literature, analyses the base paper in depth and states the research gap. **Chapter 3** studies the technical, economic, operational and schedule feasibility. "
          "**Chapter 4** sets out the existing and proposed systems and the requirements. **Chapter 5** presents the design: architecture, workflow, data-flow diagrams, UML, the data model, "
          "modules and screens. **Chapter 6** describes the methodology and implementation, including the algorithms, the equations, the API and installation. **Chapter 7** reports the testing. "
          "**Chapter 8** presents the results and output screens, the comparison with the base paper and the objectives against outcomes. **Chapter 9** concludes and **Chapter 10** gives the future scope. "
          "The references and three appendices (important code, installation and user guide, additional screens) follow."),
    ]
    return out
