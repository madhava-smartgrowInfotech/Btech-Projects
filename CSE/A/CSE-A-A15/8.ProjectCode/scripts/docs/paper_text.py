"""Text of 19.IEEE_Paper.docx (CipherVeil). Every number is read from facts.py (experiments/**/metrics.json) or typed from docs/REPORT_FACTS.md.

Citations are written {r:N} with the global reference numbers of refs.py; Paper.expand renumbers them in order of first appearance.
"""
import statistics

from . import facts as F
from . import paper_figs
from .paper import Paper
from .refs import CITE


def c(*keys):
    return "{r:" + ",".join(str(CITE[k]) for k in keys) + "}"


def build(path):
    figs = paper_figs.make()
    P = Paper()
    S, EX, API = F.S, F.EX, F.API
    rsa = {r["rsa_bits"]: r for r in EX["rsa_study"]}
    fs = EX["fill_study"]
    frows = fs["rows"]

    def fill_mean(f, key):
        return statistics.mean(r[key] for r in frows if r["fill"] == f)

    full_lo = min(r["psnr_mean"] for r in frows if r["fill"] == 1.0)
    full_hi = max(r["psnr_mean"] for r in frows if r["fill"] == 1.0)
    ssim_floor = min(r["ssim_mean"] for r in frows)
    sa = EX["steganalysis"]
    chi_min = min(r["chi2_p_stego_prefix"] for r in sa["rows"])
    ws_clean = sorted({r["ws_estimate_cover"] for r in sa["rows"]})
    ws10 = [r["ws_estimate_stego"] for r in sa["rows"] if r["fill"] == 0.10]
    pe = EX["plain_vs_encrypted"]["rows"]
    ones_plain = [r["ones_fraction"] for r in pe if r["kind"] == "plain"]
    ones_enc = [r["ones_fraction"] for r in pe if r["kind"] == "encrypted"]
    tam = EX["tamper_study"]
    ex_att = {r["attack"]: r for r in EX["extra_attacks"]}
    rob = {r["attack"]: r for r in F.EV["robustness"]}
    a = lambda k: API[k]["median_ms"]  # noqa: E731
    send512 = a("send (21 KiB memo, 512x512 cover, RSA-3072)")
    send720 = a("send (21 KiB memo, 1280x720 cover)")
    recv = a("receive (RSA-3072)")
    cap = F.EV["capacity"]
    cap_lo, cap_hi = min(x["max_bundle_kib"] for x in cap), max(x["max_bundle_kib"] for x in cap)
    psnr_hi = max(r["psnr_db"] for r in F.EV["quality_and_speed"] if r["fits"])

    sixteen = [r for r in F.EV["quality_and_speed"] if r["payload_bytes"] == 16384 and r["fits"]]
    s16_psnr = ", ".join(f"{r['psnr_db']:.1f}" for r in sixteen)
    s16_names = ", ".join(r["cover"].split("_")[0] + " " + r["cover"].split("_")[-1].replace(".png", "") for r in sixteen)
    s16_used = ", ".join(f"{r['used_pct']:.0f}" for r in sixteen)
    memo = {r["kind"]: r["bytes"] for r in pe if r["payload"] == "confidential_memo.pdf"}
    pe_memo = {"plain": memo["plain"], "enc": memo["encrypted"]}

    authors = [[n, f"Roll No. {r}", "Dept. of Computer Science and Engineering", F.COLLEGE_SHORT, "[CITY], India", "[EMAIL]"] for n, r in F.STUDENTS_UPPER]
    authors.append([F.GUIDE.upper(), f"{F.GUIDE_DESIGNATION} (project guide)", "Dept. of Computer Science and Engineering", F.COLLEGE_SHORT, "[CITY], India", "[EMAIL]"])
    P.title_block("CipherVeil: Data Protection Using Hybrid AES-RSA Encryption and LSB Steganography", authors)
    P.begin_two_columns()

    P.abstract(
        "Encryption protects a message but shows that a secret exists; hiding alone protects nothing once the carrier is examined. This paper presents CipherVeil, "
        "a working web tool that applies both layers: a file is encrypted with AES-256-GCM under a fresh key, the key is wrapped with the receiver's RSA-OAEP public key, "
        "and the authenticated bundle is hidden in the least significant bits of a PNG image. On six cover images and four payloads, "
        f"all {S['runs']} runs that fit were restored byte for byte, PSNR ranged from {S['psnr_db_min']:.1f} to {psnr_hi:.1f} dB ({full_lo:.1f} dB at full capacity, within "
        f"{fs['max_abs_dev_vs_theory_db']:.3f} dB of a closed-form model), SSIM stayed at or above {ssim_floor:.4f}, capacity was {S['max_capacity_bits_per_pixel']:.1f} bits per pixel, "
        f"and all {tam['trials']} single-bit tampering trials were rejected. The same tests show the limits: only lossless handling preserves the payload, JPEG, noise, "
        "resizing and rotation destroy it, and a chi-square test flagged every embedded image. The scheme is invisible to the eye but not to statistics. "
        "The paper reports the design, the measurements and these limits, and compares them with the base paper, which addresses a different problem.",
        ["Hybrid encryption", "AES-GCM", "RSA-OAEP", "Image steganography", "LSB", "PSNR", "Cyber security"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para("Sensitive files travel over networks that the sender does not control. Encryption keeps the content unreadable but marks the transfer as worth attacking; "
           f"steganography hides the existence of the transfer but gives no protection once the carrier is suspected {c('fridrich', 'provos')}. "
           "Symmetric ciphers are fast, yet sharing their key is the weak point, and plain least-significant-bit (LSB) substitution can degrade the cover image "
           f"and be found by statistical tests {c('westfeld', 'rs')}. In practice a team encrypts a file with one tool and hopes the attachment is not noticed, or hides "
           "unencrypted data and relies on secrecy of the method; neither gives two independent layers.")
    P.para("A typical use is a small organisation that must send an account list or a signed memo to a partner over e-mail or a shared drive that it does not trust. "
           "The receiver publishes a public key; the sender picks the file, the key and an ordinary-looking picture, and sends back a PNG that looks like any other picture. "
           "Only the holder of the private key can open it, and any modification of the picture in transit is detected rather than silently accepted.")
    P.para("The base paper of this work, ProSt " + c("base") + ", advances steganography and encryption in a provably secure form for an untrusted cloud that computes on hidden bits, "
           "but reports no imperceptibility or capacity figures. Work on combined schemes " + c("screed", "memr") + " is mostly symmetric-only or hardware oriented. "
           "The gap is a practical hybrid AES-RSA plus LSB pipeline, evaluated end to end on capacity, imperceptibility, speed, robustness and detectability, with a tool a person can run. "
           "CipherVeil fills that gap. Its contributions are:")
    P.para("1) an authenticated bundle format (CVL1) that carries the file name, size and SHA-256 inside the AES-GCM layer, with the magic bytes as associated data; "
           f"2) a hybrid pipeline with a fresh AES-256-GCM key and nonce per message wrapped by RSA-OAEP-SHA256, byte-exact in {S['runs']} of {S['runs']} runs and tamper-evident in {tam['trials']} of {tam['trials']} bit flips; "
           f"3) a capacity-aware 1-bit LSB embedder at {S['max_capacity_bits_per_pixel']:.1f} bits per pixel whose closed-form PSNR model matches measurement within {fs['max_abs_dev_vs_theory_db']:.3f} dB, with PSNR never below {full_lo:.1f} dB at any fill; "
           "4) an honest evaluation in which only lossless handling survives 18 attacks and a chi-square test flags 30 of 30 embedded images; "
           f"5) a full-stack tool (FastAPI and React) with key management, analysis and robustness views and a secret-free log, covered by {F.PYTEST_TOTAL} automated tests and {F.SMOKE_TOTAL} smoke checks. "
           "The novelty is integration and evaluation, not new primitives.", indent=0)
    P.para("Section II surveys related work, Section III describes the method, Section IV reports measurements, and Section V concludes.")
    P.sub("A", "System Hardware")
    P.para("All numbers were measured on one PC: Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB RAM, Windows 11 Pro, CPU only. Other jobs shared the machine, so "
           "absolute times vary by roughly 10-30 % between runs.")
    P.sub("B", "Software Requirements")
    P.para("Python 3.11.9 with FastAPI 0.115.6, SQLAlchemy 2.0.36 (SQLite), cryptography 44.0.0, Pillow 11.0.0, NumPy 2.1.3, scikit-image 0.24.0 and matplotlib 3.9.3; "
           "React 18.3.1, Vite 6.0.3 and Tailwind CSS on Node 24.19.0; pytest for tests. No dataset, GPU or external service is needed.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para("**Base paper.** ProSt " + c("base") + " (Ahmad and Rass, IEEE Access, 2026) introduces provably secure homomorphic steganography. A client hides secret bits in the LSBs of cover images "
           "at a secret position among random decoy bits; an honest-but-curious cloud then evaluates a Boolean circuit made only of Fredkin gates on every pixel without learning "
           "which pixels carry secrets. Theorem 1 gives an adversary advantage of order 1/n in the number n of positions, so n of about 10^6 or more is recommended. "
           "The reported experiment is a circuit of 17 gates and 61 wires on a 128x128x3 image, evaluated in 8.38 s on an i5-1135G7 laptop. The paper reports no PSNR, SSIM or capacity, "
           "and the receiver is a computing server, not a person who must recover a file.")
    P.para("The security model of ProSt differs from the one used here. ProSt assumes that the cloud knows the data is present and protects its location and the circuit; "
           "traditional steganography, and this work, assume the opposite and try to hide the existence of the message. Consequently the metrics also differ: ProSt studies the "
           "adversary's advantage, while a steganographic transfer is judged by imperceptibility, capacity and detectability.")
    P.para("**Embedding.** Simple LSB substitution " + c("chan") + " is the standard baseline; LSB matching " + c("mielikainen") + " changes values by plus or minus one and lowers "
           "the number of changes, and syndrome-trellis codes " + c("stc") + " minimise a distortion cost. Textbooks " + c("fridrich") + " and surveys " + c("provos") +
           " cover the field. CipherVeil keeps plain sequential substitution because it is transparent and measurable.")
    P.para("**Combined schemes.** SCReedSolo " + c("screed") + " shuffles the message, encrypts it with Fernet, adds Reed-Solomon codes and embeds it at 3 bits per pixel; it is symmetric-only. "
           "Fatemieh et al. " + c("memr") + " implement the lightweight stream ciphers Trivium and Grain-128a in memristive IMPLY logic and demonstrate them in LSB steganography. "
           "The batch survey also lists four 2024-2025 works on triple-layer visual cryptography, image-object hiding, chaotic encryption with a CNN, and AES with DWT-DCT "
           + c("s_triple", "s_object", "s_chaos", "s_dwt") + "; only their titles are available here, so no result is quoted.")
    P.para("**Steganalysis.** The chi-square attack " + c("westfeld") + " detects equalised value pairs, RS analysis " + c("rs") + " and weighted-stego estimation " + c("ws") +
           " estimate the embedded length of LSB replacement. They set the bar for the detectability test in Section IV.")
    P.para("**Standards and measures.** AES " + c("aes") + " in Galois/Counter Mode " + c("gcm") + " gives authenticated encryption; RSA-OAEP follows PKCS #1 " + c("rfc8017") +
           ". Image quality is reported by SSIM " + c("ssim") + " and PSNR " + c("psnr") + ".")
    P.table("Selected related work", ["Work", "Approach", "Data", "Reported result", "Limitation"],
            [["ProSt " + c("base"), "LSB bits among decoys, Fredkin gates", "128x128x3, 17 gates", "8.38 s; advantage order 1/n; no PSNR", "cloud compute, not file transfer"],
             ["SCReedSolo " + c("screed"), "shuffle, Fernet, Reed-Solomon, LSB", "text, audio, image; 512x512 to 21188x30328", "3 bpp; PSNR 51.8-57.7 dB", "symmetric key only"],
             ["Memristive " + c("memr"), "Trivium, Grain-128a in IMPLY logic", "five 256x256 grayscale", "energy down by up to 42 % and 44 %", "hardware design"],
             ["Simple LSB " + c("chan"), "substitution", "test images", "baseline", "fragile, detectable"],
             ["LSB matching " + c("mielikainen"), "plus or minus 1 changes", "test images", "fewer changes per bit", "not tested here"],
             ["Chi-square, RS, WS " + c("westfeld", "rs", "ws"), "steganalysis of LSB", "natural images", "estimate embedded length", "attacks, not designs"],
             ["Survey works " + c("s_triple", "s_object", "s_chaos", "s_dwt"), "visual crypto, chaos + CNN, AES + DWT-DCT", "n/a", "titles only", "not verified"]],
            [0.62, 0.78, 0.68, 0.72, 0.6], size=5.6, align=["l"] * 5)
    P.para("**Positioning.** Read together, the works split into three groups: embedding designs that lower the visible or statistical footprint of the change "
           f"{c('chan', 'mielikainen', 'stc')}, combined schemes that add a cipher or an error-correcting code in front of the embedder {c('screed', 'memr')}, and a provably secure "
           f"construction for a different use {c('base')}. None of them pairs a public-key key transport with an LSB carrier and then measures what an attacker, a lossy channel and a bit flip do to it. "
           "That measurement, rather than a new embedder, is the aim of this work.")
    P.para("**Research gap.** The surveyed work advances steganography and encryption mostly separately, including provably secure constructions. What is missing is a practical hybrid "
           "AES-RSA plus LSB pipeline, with a public-key step so that sender and receiver share no secret beforehand, measured end to end on capacity, imperceptibility, speed, "
           "robustness and detectability, and offered as a tool. CipherVeil addresses that and does not claim provable security.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.sub("A", "Architecture and Main Flow")
    P.para(f"CipherVeil is a three-tier web application (Fig. 1). A React console on port {F.WEB_PORT} calls a FastAPI service on port {F.API_PORT} with 24 endpoints; the services crypto, lsb, "
           "metrics, pipeline, plots, robustness and benchmark do the work; SQLite holds three tables (users, keypairs, oplog) and the covers, payloads and PNG outputs are files. "
           "Passwords are hashed with bcrypt, sessions use a 12-hour JWT, every key and operation is checked for ownership, uploads are capped at 25 MB, and the log never receives keys or file contents.")
    P.figure(figs["arch"], "Architecture of CipherVeil: console, API, services, storage.", 3.4)
    P.para("The main flow (Fig. 2) has a send path and a receive path. The receiver first generates an RSA keypair (2048, 3072 or 4096 bits) and gives the public PEM to the sender.")
    P.figure(figs["flow"], "Main flow: encrypt, wrap the key, check capacity, embed; extract, unwrap, verify.", 3.4)
    P.sub("B", "Hybrid Encryption and Bundle")
    P.para("The sender builds a header with the file name, size and SHA-256. A fresh 256-bit AES key and a fresh 96-bit nonce encrypt header and file with AES-256-GCM "
           "using the magic bytes CVL1 as associated data. The AES key is wrapped with the receiver's public key by RSA-OAEP with SHA-256 and MGF1-SHA-256. "
           "Keys below 2048 bits are refused. The bundle is CVL1 | wrapped-key length (2 B) | wrapped key | nonce (12 B) | ciphertext and tag. "
           f"For a short file name its overhead is {rsa[2048]['overhead_bytes']}, {rsa[3072]['overhead_bytes']} and {rsa[4096]['overhead_bytes']} bytes for RSA-2048, 3072 and 4096. "
           "Because the key and nonce are new for every message, the compromise of one message key exposes no other message.")
    P.para("Three choices follow from the problem. GCM is used instead of a plain block-cipher mode because the receiver must be able to tell a modified bundle from a good one: "
           "an LSB channel is fragile, and a silent bit error would otherwise yield wrong data. OAEP is used instead of textbook RSA because the wrapped value is a short random key and "
           "padding must be randomised and checked. A new key per message is cheap, since the public-key step costs well under a millisecond on the sender's side (Section IV-B), "
           "and it removes any need to share a secret before the first message.")
    P.sub("C", "LSB Embedding and Capacity")
    P.para("The image is read as RGB (any alpha channel is dropped). The bundle length (32 bits) and the bundle are written, most significant bit first, into the lowest bit of each R, G and B "
           "value, row by row from the first pixel; the result is saved as PNG. For a W x H image the largest bundle is")
    P.eq("C = (3WH - 32) / 8   bytes,")
    P.para(f"that is {S['max_capacity_bits_per_pixel']:.1f} bits per pixel. A larger bundle is rejected before embedding. Extraction reads the length, checks that it is plausible, and returns the bits.")
    P.sub("D", "Imperceptibility Model")
    P.para("With MSE the mean squared difference over all 3WH values, PSNR is")
    P.eq("PSNR = 10 log_10 (255^2 / MSE).")
    P.para("SSIM " + c("ssim") + " is computed per colour channel and averaged. Encrypted bits are close to uniformly random, so each embedded bit flips its value with probability 1/2 and changes it by exactly one. "
           "For n embedded bits the expected MSE is n / (6WH), and")
    P.eq("PSNR = 10 log_10 (255^2 x 6WH / n).")
    P.para("At full capacity n = 3WH and the floor is 51.14 dB. The model depends on the number of bits only, not on the cover, which is what Section IV tests.")
    P.sub("E", "Extraction and Verification")
    P.para("The receiver reads the length and the bits, checks the magic and the wrapped-key length, unwraps the AES key with the private key, decrypts with AES-GCM and compares the SHA-256 "
           "in the header with the hash of the restored file. A wrong key, a flipped bit, a truncated bundle or an image without payload fails a check and releases nothing.")
    P.sub("F", "Evaluation Protocol")
    P.para(f"Core evaluation: six covers (200x200 to 1280x720), payloads of 1, 4, 16, 64 and 128 KiB, RSA-3072, three repeats, medians. Fill study: 7 fill levels x 6 covers x 5 random payloads, RSA-2048. "
           f"Robustness: nine attacks in the application and nine more (lossless re-encodings, WebP, grayscale, rotation, flip, palette) on all six covers, each ending in a real decryption and a hash comparison. "
           f"Detectability: the chi-square test {c('westfeld')} on the known embedded prefix and the weighted-stego estimate {c('ws')} over the whole image, at 10 to 100 % fill. "
           f"Tamper study: {tam['trials']} single-bit flips of the stego LSBs, 40 per field of the bundle. Freshness: 50 encryptions of one file. "
           f"Tests: {F.PYTEST_TOTAL} pytest tests and {F.SMOKE_TOTAL} smoke checks against the running backend.")

    P.sub("G", "Threat Model and Security Argument")
    P.para("The attacker may read and copy the PNG, run statistical tests on it, modify it, and try keys, but cannot read the receiver's private key. "
           "Confidentiality rests on AES-256 and on the RSA-OAEP wrapping of the session key; integrity and authenticity of the content rest on the GCM tag, "
           "which covers the header, the file and the magic bytes; the SHA-256 in the header gives an end-to-end check of the restored file. The hiding layer adds a second barrier: "
           "an observer must first suspect the picture and then locate and decode the bundle. That barrier is weak by design, because the embedding order is fixed and public, so security does not depend on it. "
           "Out of scope are sender authentication (anyone with the public key can send), metadata analysis, compromise of the machine that holds the database, and a quantum adversary against RSA.")
    P.sub("H", "Implementation and Tests")
    P.para(f"The services are about 470 lines of Python in seven modules; the five route modules add about 400 lines. The {F.PYTEST_TOTAL} pytest tests cover the cipher ({F.PYTEST_CRYPTO}), the embedder ({F.PYTEST_LSB}), "
           f"metrics, pipeline and attacks ({F.PYTEST_METRICS}) and the API ({F.PYTEST_API}); they include exact-fit, oversize, empty-file, non-image, alpha, wrong-key, wrong-size, truncated-bundle and path-traversal cases. "
           f"The {F.SMOKE_TOTAL}-check smoke script drives the running backend through key generation, send, analysis, receive, wrong key, robustness and the log.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.sub("A", "Imperceptibility and Capacity")
    P.para(f"Of 30 cover-payload pairs, {S['runs']} fit and {S['runs_skipped_too_large']} were blocked by the capacity check; all {S['runs']} were restored byte for byte. "
           f"PSNR was between {S['psnr_db_min']:.1f} and {psnr_hi:.1f} dB (mean {S['psnr_db_mean']:.1f}) and SSIM between {S['ssim_min']:.4f} and 0.9999 (mean {S['ssim_mean']:.4f}). "
           f"The fill study (Fig. 3a) gives mean PSNR of {fill_mean(0.01, 'psnr_mean'):.1f}, {fill_mean(0.10, 'psnr_mean'):.1f}, {fill_mean(0.50, 'psnr_mean'):.1f} and {fill_mean(1.0, 'psnr_mean'):.2f} dB at 1, 10, 50 and 100 % "
           f"of capacity. The measured values stay within {fs['max_abs_dev_vs_theory_db']:.3f} dB of the closed form of Section III-D, the standard deviation over five payloads is at most {fs['max_psnr_std_db']:.2f} dB, "
           f"and SSIM stays at or above {ssim_floor:.4f}, the lowest value occurring on the 1280x720 cover at full capacity. PSNR is therefore above 50 dB at every fill level. "
           f"Capacity is {S['max_capacity_bits_per_pixel']:.1f} bits per pixel, from {cap_lo} KiB (200x200) to {cap_hi} KiB (1280x720). "
           f"Compared with plain files, encrypted bundles keep PSNR unchanged (about 50 % of embedded bits flip a value either way) but are balanced: the fraction of one-bits is {min(ones_enc):.2f}-{max(ones_enc):.2f} against {min(ones_plain):.2f}-{max(ones_plain):.2f}.")
    P.para(f"Per cover, a 16 KiB payload gives {s16_psnr} dB on the {s16_names} covers "
           f"({s16_used} % used): the lower the share of capacity used, the higher the PSNR, whatever the picture. "
           f"The bundle is slightly larger than the file: a {pe_memo['plain']} byte memo becomes {pe_memo['enc']} bytes ({100 * (pe_memo['enc'] - pe_memo['plain']) / pe_memo['plain']:.1f} % more with RSA-2048).")
    P.para("For the 21 KiB memo hidden in the 512x512 photograph of Fig. 4, the analysis screen reports a largest change of 1 of 255 per colour value and 88,010 of 786,432 values changed (11.1911 %), "
           "which is about half of the 22.445 % of the capacity used, as the model predicts; the bit-plane view shows that only the lowest plane differs from the cover.")
    P.table("Measured results (six covers, four payloads)", ["Measure", "Result"],
            [["Byte-exact round trips", f"{S['runs']} of {S['runs']} ({S['runs_skipped_too_large']} blocked: too large)"],
             ["PSNR, core runs (min / mean)", f"{S['psnr_db_min']:.1f} / {S['psnr_db_mean']:.1f} dB"],
             ["PSNR at full capacity", f"{full_lo:.2f}-{full_hi:.2f} dB (floor 51.14)"],
             ["SSIM, core runs (min / mean)", f"{S['ssim_min']:.4f} / {S['ssim_mean']:.4f}"],
             ["SSIM, lowest at full capacity", f"{ssim_floor:.4f}"],
             ["Capacity", f"{S['max_capacity_bits_per_pixel']:.1f} bpp; {cap_lo}-{cap_hi} KiB"],
             ["Encrypt / embed / extract (median)", f"{S['median_encrypt_ms']} / {S['median_embed_ms']} / {S['median_extract_ms']} ms"],
             ["RSA unwrap + decrypt, 2048 / 3072 / 4096", f"{rsa[2048]['unwrap_decrypt_ms_median']:.0f} / {rsa[3072]['unwrap_decrypt_ms_median']:.0f} / {rsa[4096]['unwrap_decrypt_ms_median']:.0f} ms"],
             ["Key generation, 2048 / 3072 / 4096", f"{rsa[2048]['keygen_ms_median']:.0f} / {rsa[3072]['keygen_ms_median']:.0f} / {rsa[4096]['keygen_ms_median']:.0f} ms"],
             ["PNG re-save, WebP lossless, bottom crop 10 %", "recovered 6 / 6 each"],
             ["JPEG q50-q100, noise, resize, left crop, rotate, flip", "recovered 0 / 6 each"],
             ["Chi-square, stego prefix p-value", f"{chi_min:.2f}-1.00 (30 of 30)"],
             ["Tampered bundles rejected", f"{tam['trials']} of {tam['trials']}"],
             ["API send / receive, 512x512, RSA-3072", f"{send512 / 1000:.2f} s / {recv / 1000:.2f} s"]],
            [1.95, 1.35], size=6.2, align=["l", "c"])
    P.figure(figs["results"], "(a) PSNR against capacity used: mean over six covers, worst cover and closed form. (b) Weighted-stego estimate of the embedded fraction against the true fraction.", 3.4)
    P.sub("B", "Speed")
    P.para(f"Cryptography is cheap: median encryption takes {S['median_encrypt_ms']} ms, embedding {S['median_embed_ms']} ms and extraction {S['median_extract_ms']} ms. "
           f"RSA private-key operations dominate: unwrap plus decrypt takes {rsa[2048]['unwrap_decrypt_ms_median']:.0f}, {rsa[3072]['unwrap_decrypt_ms_median']:.0f} and {rsa[4096]['unwrap_decrypt_ms_median']:.0f} ms for 2048, 3072 and 4096 bits, "
           f"and key generation takes {rsa[2048]['keygen_ms_median']:.0f}, {rsa[3072]['keygen_ms_median']:.0f} and {rsa[4096]['keygen_ms_median']:.0f} ms (median; the 4096-bit range was {rsa[4096]['keygen_ms_min']:.0f}-{rsa[4096]['keygen_ms_max']:.0f} ms). "
           f"An API send takes {send512:.0f} ms on a 512x512 cover and {send720 / 1000:.1f} s on 1280x720, a receive {recv:.0f} ms, because SSIM, PSNR and PNG encoding, not the cipher, take most of the time. "
           f"Other calls are cheap: login {a('login'):.0f} ms (bcrypt), key generation through the API {a('keys/generate 2048'):.0f}, {a('keys/generate 3072'):.0f} and {a('keys/generate 4096'):.0f} ms, "
           f"the nine robustness attacks {a('robustness (9 attacks)'):.0f} ms, the first render of the histogram and bit-plane plots {a('histogram + bit planes, first render'):.0f} ms, and the full benchmark over six covers "
           f"{a('benchmark/run (6 covers x 3 sizes, RSA-2048)') / 1000:.0f} s.")
    P.sub("C", "Robustness and Failure Cases")
    P.para(f"Only lossless handling keeps the payload. Of the nine application attacks, a lossless PNG re-save and a bottom crop of 10 % are recovered on all six covers (the crop works only while the bundle lies in the rows that remain); "
           f"JPEG at quality 95, 75 and 50, Gaussian noise of sigma 1 and 3, resizing to 90 % and a left crop each recover 0 of 6, with LSB error rates of {min(r['mean_bit_error_rate'] for k, r in rob.items() if k not in ('png_resave', 'crop_bottom_10')):.2f}-{max(r['mean_bit_error_rate'] for r in rob.values()):.2f}, that is, no better than chance. "
           f"The extra attacks agree: PNG compression level 9, an added alpha channel and WebP lossless recover {ex_att['PNG re-save, compression 9']['recovered']} of 6; JPEG quality 100, lossy WebP, grayscale conversion, rotation, flip and a 256-colour palette recover 0 of 6. "
           "The reasons are mechanical: JPEG quantises every 8x8 block and rewrites the lowest bits even at quality 100, noise of one grey level flips about half of the lowest bits, and resizing, rotation, flipping "
           "and cropping from the left move every later bit to a wrong position. Images must therefore travel as PNG files, not through messengers or sites that re-encode.")
    P.sub("D", "Detectability")
    P.para(f"The chi-square test on the known embedded prefix gave a stego p-value of at least {chi_min:.2f} in all 30 cases (cover prefix below 0.5 in 27); in three cases the clean cover already looked equalised, so the test did not separate the two. "
           f"The blind weighted-stego estimate (Fig. 3b) follows the true embedded fraction, for example {statistics.mean(r['ws_estimate_stego'] for r in sa['rows'] if r['fill'] == 0.5):.2f} for a true {statistics.mean(r['true_fraction_of_samples'] for r in sa['rows'] if r['fill'] == 0.5):.2f}, "
           f"but clean covers already read {min(v for v in ws_clean if v > 0.05):.2f} to {max(ws_clean):.2f} on four of six images, so low fill levels are noisy ({min(ws10):.2f}-{max(ws10):.2f} at 10 %). "
           "Sequential, key-independent embedding is detectable at medium and high fill; low fill is safer, not safe.")
    P.sub("E", "Tamper Resistance")
    P.para(f"All {tam['trials']} single-bit flips (40 in each of the length, magic, key-length, wrapped-key, nonce and ciphertext fields) were rejected, none produced wrong data: "
           "flips in the wrapped key failed RSA unwrapping, in the nonce or ciphertext failed the GCM tag, and in the length header 13 of 40 were stopped as an invalid header and 27 by the tag. "
           f"Fifty encryptions of one file gave 50 different nonces and wrapped keys, with {EX['freshness']['mean_bit_difference_between_bundles']:.2f} of the bits differing between bundles.")
    P.sub("F", "Comparison with the Base and Supporting Papers")
    P.para("The comparison is indicative only, because goals, data and conditions differ. ProSt " + c("base") + " reports no PSNR, SSIM or capacity, so there is nothing to compare these against; its 8.38 s is "
           "the time of a 17-gate homomorphic circuit on 128x128x3, whereas CipherVeil transfers a whole file in milliseconds to a second. "
           "CipherVeil takes ProSt's LSB carrier and key-exchange framing but does not implement homomorphic computation, decoy-bit location hiding or a security proof. "
           f"SCReedSolo " + c("screed") + " reports PSNR of 51.8, 57.7 and 52.9 dB for a text, an audio and an image payload on very different covers at 3 bits per pixel; "
           f"CipherVeil's {S['psnr_db_min']:.1f}-{psnr_hi:.1f} dB up to 73 % fill and {full_lo:.1f} dB at full capacity are of the same order. "
           "SCReedSolo adds shuffling and error correction, which CipherVeil lacks; CipherVeil adds public-key key transport and authentication, which SCReedSolo lacks.")
    P.sub("G", "Output Screens")
    P.figure(figs["send"], "Send screen: stego image, PSNR 57.642 dB, SSIM 0.999054, 22.445 % capacity used, SHA-256 of the file and stage timings.", 3.3)
    P.figure(figs["receive"], "Receive screen: file restored byte for byte, hashes equal (top); wrong key rejected at RSA unwrap (bottom).", 3.3)
    P.para("Fig. 4 shows a 21 KiB memo hidden in a 512x512 photograph; Fig. 5 shows the restored file with equal SHA-256 values, and the refusal when the wrong keypair is chosen.")
    P.sub("H", "Practical Guidance from the Measurements")
    P.para(f"Three rules follow. First, choose a cover whose capacity is several times the bundle: at about 10 % of capacity PSNR is near {fill_mean(0.10, 'psnr_mean'):.0f} dB, at 50 % it is near {fill_mean(0.50, 'psnr_mean'):.0f} dB, "
           f"and the weighted-stego estimate rises with the fill. Second, send the file as a PNG attachment and avoid any service that re-encodes pictures; a single JPEG pass loses the whole payload. "
           f"Third, prefer RSA-3072: it adds {rsa[3072]['overhead_bytes'] - rsa[2048]['overhead_bytes']} bytes of overhead over RSA-2048 and about {rsa[3072]['unwrap_decrypt_ms_median'] - rsa[2048]['unwrap_decrypt_ms_median']:.0f} ms to the receiver, "
           f"while RSA-4096 more than doubles the receiver's time again ({rsa[4096]['unwrap_decrypt_ms_median']:.0f} ms). The chi-square result also shows that the equalisation of value pairs, "
           f"not the visible change, is what gives the embedding away: the mean p-value of the clean prefix falls from {statistics.mean(r['chi2_p_cover_prefix'] for r in sa['rows'] if r['fill'] == 0.10):.2f} at 10 % fill "
           f"to {statistics.mean(r['chi2_p_cover_prefix'] for r in sa['rows'] if r['fill'] == 1.0):.3f} at 100 %, while the stego prefix stays at {chi_min:.2f} or above.")
    P.sub("I", "Observed Limits")
    P.para("Six committed images and four small synthetic payloads were used, with no camera photographs, one machine and one operating system. Private keys are stored unencrypted in the local database, "
           "the JWT secret ships as a placeholder, login has no rate limit, there is no sender signature, and the Send page crashed for an account with no keys because of a missing icon import (found while testing and not fixed).")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion and Future Scope")
    P.para(f"CipherVeil meets its six objectives: a hybrid AES-256-GCM and RSA-OAEP pipeline with key generation and exchange, LSB embedding with a capacity check, exact extraction and decryption, and measured PSNR, SSIM, capacity, speed and robustness. "
           f"All {S['runs']} runs were byte-exact, PSNR never fell below {full_lo:.1f} dB at any fill, and {tam['trials']} of {tam['trials']} tampered bundles were rejected. "
           "The key finding is the gap between the two layers: the encryption layer is strong and authenticated, while the hiding layer is invisible to the eye but detectable by simple statistics and destroyed by any lossy step. "
           "The limits are those of Section IV-I: plain sequential embedding, six covers, unencrypted key storage and no sender authentication.")
    P.para("Against the stated objectives, the pipeline, the key mechanism, the embedder, the extraction path and the PSNR and SSIM measurements are met in full; the capacity, time and robustness "
           "objective is met as a measurement, and the measurement is unfavourable for robustness and detectability. The work does not claim provable security, resistance to modern steganalysers or a gain over the base paper, "
           "which solves a different problem.")
    P.para("For a user the outcome is a tool that is safe to use when two conditions hold: the picture travels as a lossless file, and the adversary is not running statistical steganalysis on it. "
           "If either condition fails, the AES-GCM and RSA-OAEP layer still protects the content, but the claim of hiding does not hold; the tool says so in its robustness view instead of hiding the fact.")
    P.para("Future work: a key-dependent pixel permutation and LSB matching or adaptive embedding to lower detectability, Reed-Solomon coding for mild channel noise, signed messages and an encrypted key store, "
           "and testing against stronger steganalysers on camera photographs.")

    P.references()
    P.save(path)
    return path
