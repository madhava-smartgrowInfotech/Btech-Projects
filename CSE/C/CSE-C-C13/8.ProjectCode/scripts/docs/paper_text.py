"""Text of 19.IEEE_Paper.docx (CipherVault). Every number is read from facts.py (docs/metrics/*.json); citations are {r:key} and are numbered by first appearance."""

import os

from PIL import Image, ImageChops

from . import facts as F
from . import paper_figs
from .paper import Paper

AES, E2E, API, CRY = F.AES, F.E2E, F.API, F.CRY
KB, MB, MB10, MB25 = "1024", "1048576", "10485760", "26214400"
UP25 = "26212352"


def _med(d, size, op, stat="median"):
    return d[size][op][stat]


def ms(x):
    return F.ms(x)


def _crop(path, name):
    """Trim the white margin of a figure (the flow diagram has blank space at the bottom)."""
    im = Image.open(path).convert("RGB")
    bbox = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    if bbox:
        pad = 6
        im = im.crop((max(bbox[0] - pad, 0), max(bbox[1] - pad, 0), min(bbox[2] + pad, im.size[0]), min(bbox[3] + pad, im.size[1])))
    out = os.path.join(F.FIGS, name)
    im.save(out)
    return out


def build(path):
    figp = {k: os.path.join(F.FIGS, v) for k, v in
            dict(arch="paper_arch.png", flow="paper_flow.png", results="paper_fig3.png", tamper="paper_tamper.png",
                 share="paper_shot_share.png", audit="paper_shot_audit.png").items()}
    if not all(os.path.exists(p) for p in figp.values()):
        figp = paper_figs.make()
    flow = _crop(figp["flow"], "paper_flow_crop.png")

    # ------------------------------------------------------------------ numbers
    enc10, dec10, sha10 = (_med(AES, MB10, k) for k in ("encrypt", "decrypt", "sha256"))
    enc1, dec1 = _med(AES, MB, "encrypt"), _med(AES, MB, "decrypt")
    enc25, dec25 = _med(AES, MB25, "encrypt"), _med(AES, MB25, "decrypt")
    up_e10, up_p10 = E2E[MB10]["encrypted_up"]["median"], E2E[MB10]["plain_up"]["median"]
    dn_e10, dn_p10 = E2E[MB10]["encrypted_down"]["median"], E2E[MB10]["plain_down"]["median"]
    up_e1, up_p1 = E2E[MB]["encrypted_up"]["median"], E2E[MB]["plain_up"]["median"]
    dn_e1, dn_p1 = E2E[MB]["encrypted_down"]["median"], E2E[MB]["plain_down"]["median"]
    kg, wrap, unwrap, pb = (CRY[k]["median"] for k in ("rsa_keygen", "rsa_wrap", "rsa_unwrap", "pbkdf2_120k"))
    at = F.TAMPER["audit_tamper"]
    caught = [k for k, v in at.items() if v["detected"] == v["trials"]]
    n_cls = len(at)
    flips = F.TAMPER["ciphertext_bitflip"]
    tr = at["truncate_tail"]
    conc = F.CONC["4_workers"]
    wr = F.M["audit_write_ms"]
    sc = F.SCALE
    login, me, lst = API["login_ms"]["median"], API["me_ms"]["median"], API["list_files_ms"]["median"]
    upl10, dnl10 = API["upload_ms"][MB10]["median"], API["download_ms"][MB10]["median"]
    upl25, dnl25 = API["upload_ms"][UP25]["median"], API["download_ms"][UP25]["median"]
    ovh10, ovh1 = up_e10 - up_p10, up_e1 - up_p1
    base_num = __import__("scripts.docs.lit", fromlist=["BASE_ANALYSIS"]).BASE_ANALYSIS["numbers"]

    cells = F.RBAC["cells"]
    n_allow = sum(1 for c in cells if c["expected_allowed"])
    n_deny = len(cells) - n_allow
    P = Paper()

    authors = [[n.upper(), f"Roll No. {r}", "Dept. of Computer Science and Engineering", F.COLLEGE_SHORT, "Hyderabad, India", "[EMAIL]"] for n, r in F.STUDENTS]
    authors.append([F.GUIDE.upper(), f"{F.GUIDE_DESIGNATION} (project guide)", "Dept. of Computer Science and Engineering", F.COLLEGE_SHORT, "Hyderabad, India", "[EMAIL]"])
    P.title_block("CipherVault: Secure File Storage with Client-Side Encryption and Role-Based Access Control", authors)
    P.begin_two_columns()

    P.abstract(
        "Files kept on third-party storage are exposed to the provider, to insiders and to anyone who obtains a database backup, and access rules and audit trails kept on the same server are only as "
        "trustworthy as that server. CipherVault is a runnable web application that encrypts every file in the browser with AES-256-GCM before upload, wraps the per-file key for each recipient with "
        "RSA-2048-OAEP, enforces Owner, Editor and Viewer roles on the server, checks a SHA-256 digest on every download and records every sensitive action in a hash-chained audit log. "
        f"We measured each layer on one desktop computer. Browser AES-GCM took {ms(enc10)} ms for 10 MiB; an encrypted 10 MiB upload took {ms(up_e10)} ms against {ms(up_p10)} ms unencrypted; "
        f"a role matrix of {F.RBAC['total']} cells matched in {F.RBAC['matched']}; and {flips['detected']:,} of {flips['trials']:,} ciphertext bit flips were rejected. "
        f"The audit chain caught {len(caught)} of {n_cls} classes of tampering but missed truncation of its tail, and concurrent writers corrupted it. We report these limits and the fixes they suggest.",
        ["access control", "AES-GCM", "audit log", "client-side encryption", "key wrapping", "RBAC", "secure file storage"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para("Organisations keep sensitive documents on storage they do not control. At such a service the provider, its administrators and anyone holding a stolen backup can all read plaintext, "
           "and a network attacker can alter what is stored. Encrypting a file before it leaves the owner's machine removes the provider from the circle of trust, but implementations are easy to get wrong: "
           "the attacks on the deployed MEGA service showed that malleable key handling undoes end-to-end encryption in practice {r:mega}. "
           "Fine-grained alternatives such as attribute-based encryption {r:cpabe} move the policy into the ciphertext but are computationally heavy, "
           "and a small team sharing documents seldom needs more than three levels of access: read, write and manage.")
    P.para("Published designs for this problem leave a measurement gap. The declared base paper of this work {r:base} proposes attribute-based encryption with a blockchain for health records "
           "and evaluates it by calculation from primitive timings, not by running a system. The closest file-storage architecture {r:ijedr} reports +320 ms for a 10 MB upload, 98.6% access-control accuracy "
           "and 100% audit-tamper detection, but publishes no hardware, per-operation timings or tamper methods. What is missing is a runnable, general-purpose file store that is measured layer by layer, "
           "including where it fails.")
    P.para("CipherVault is such a store. Its contributions are: (1) a working web application in which the browser performs all file cryptography with the Web Crypto API {r:webcrypto}, "
           "so the server holds only ciphertext, wrapped keys, password hashes and metadata; "
           "(2) per-recipient key wrapping that lets an owner share, re-role and revoke access without ever sending a file key to the server in the clear; "
           f"(3) a server-enforced Owner / Editor / Viewer model checked on every request, tested exhaustively over {F.RBAC['total']} principal-operation cells; and "
           "(4) a hash-chained audit log together with a tamper study that states what the chain does and does not detect. "
           "Section II surveys related work, Section III describes the method, Section IV gives measurements and Section V concludes.")
    P.sub("A", "System Hardware")
    P.para(f"All measurements were taken on one desktop: Intel Core i5-12500 (6 cores, 12 threads), {F.ENV['ram_gb']} GB RAM, Windows 11, no GPU. Browser cryptography ran in Chrome {F.BR['browser_version']} (headless); "
           "API timings used the loopback interface. Other jobs shared the processor during the runs, so timings are indicative and varied by up to about three times between runs at 10 MiB.")
    P.sub("B", "Software Requirements")
    P.para(f"Python {F.ENV['python']} with FastAPI, SQLAlchemy 2, PyJWT, bcrypt and cryptography; SQLite by default and PostgreSQL through Docker; React 19 and Vite 8 for the interface, "
           f"with the Web Crypto API for all browser cryptography; pytest and Playwright for tests. The code base is {F.LOC['backend_py']['lines']:,} lines of backend Python and {F.LOC['frontend_src']['lines']:,} lines of front end.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para("**Base paper.** Nekouie et al. {r:base} propose sharing electronic health records through a semi-trusted cloud. ClinicalBERT extracts data attributes from clinical notes, and an elliptic-curve "
           "ciphertext-policy attribute-based scheme in the style of Bethencourt et al. {r:cpabe} encrypts each record under a policy over both user and data attributes. Several key-generation centres issue partial keys, "
           "so no authority holds a user's full key, and a private Hyperledger Fabric ledger {r:fabric} stores attribute public keys and policies. The design has 23 phases and a fixed 160-bit key length. "
           f"Its evaluation is analytic: total cost is calculated from operation counts and OpenSSL primitive timings taken on an HPE server (6-core E5-2620 v3, 32 GB) and a Raspberry Pi 3 B+, giving "
           f"about {base_num['proposed_us']['total_x5']:,} µs for five attributes against {min(base_num['compared_totals_us']):,} to {max(base_num['compared_totals_us']):,} µs for ten compared schemes. "
           "No dataset, extraction accuracy, end-to-end upload time or role check is reported, and it is not a file-storage product. CipherVault adopts its trust model (an untrusted store that sees only ciphertext) and its "
           "plaintext-hash check, but not attribute-based encryption, the language model or the blockchain.")
    P.para("**Related work.** Storage systems for untrusted servers date from SiRiUS {r:sirius}, which adds cryptographic read and write control over network file systems, Plutus {r:plutus}, which groups files to cut key distribution, "
           "and Tahoe-LAFS {r:tahoe}, which combines capabilities with erasure coding; none of their abstracts describes a tamper-evident audit log. Recent papers use commodity primitives: a hybrid AES-256, RSA and SHA-256 store {r:sagi}, "
           "Geocrypt, which adds location and time gating and Ethereum contracts {r:geo}, and the IJEDR architecture with browser-side AES-256-GCM, RSA-2048 wrapping, three roles, a chained audit log with ECDSA signatures, "
           "multi-factor sign-in and 4 MB chunking {r:ijedr}. For access models, role-based control {r:rbac01} grants permissions to roles rather than to users. For logs, Schneier and Kelsey {r:audit99} showed how hash linking "
           "makes earlier entries impossible to alter undetectably on a machine that is later compromised, and Crosby and Wallach {r:tamper09} gave Merkle-tree logs with logarithmic proofs.")
    P.table("Related work compared", ["Work", "Approach", "Data", "Reported result", "Limitation"],
            [["Base paper {r:base}", "EC CP-ABE, ClinicalBERT, Fabric", "None; HPE and Pi timings", "~8,506 µs, 5 attributes (calculated)", "No file store; not measured end to end"],
             ["IJEDR {r:ijedr}", "AES-GCM, RSA, RBAC, signed chain", "50 users, 900 attempts", "+320 ms/10 MB; 98.6%; 50/50 tamper", "No hardware or method given"],
             ["Geocrypt {r:geo}", "RSA, location, Ethereum", "Abstract only", "Qualitative", "Spoofable location; latency"],
             ["Hybrid store {r:sagi}", "AES-256, RSA, SHA-256", "Abstract only", "No figures", "No roles or audit trail"],
             ["MEGA attacks {r:mega}", "Cryptanalysis of key hierarchy", "Deployed service", "Full file compromise", "A lesson, not a system"],
             ["SiRiUS {r:sirius}", "Crypto access over NFS/CIFS", "Prototype", "File-level sharing", "Not a web app; no audit log described"],
             ["Plutus {r:plutus}", "Filegroups, efficient revocation", "OpenAFS prototype", "Overhead near network-encryption systems", "No audit log described"],
             ["Tahoe-LAFS {r:tahoe}", "Capabilities, erasure coding", "Grid design", "Provider-blind", "No roles or audit log described"],
             ["Schneier-Kelsey {r:audit99}", "Forward-secure hash chain", "Protocol", "Past entries unalterable", "Needs secure verifier"],
             ["Crosby-Wallach {r:tamper09}", "Merkle log, log-size proofs", "Prototype", "Log-size proofs", "Needs published commitments"]],
            [0.62, 0.7, 0.55, 0.8, 0.73], size=5.6, align=["l", "l", "l", "l", "l"])
    P.para("**Strengths and weaknesses.** The attribute-based and blockchain designs offer fine-grained policy and no single key authority, at the cost of pairing or elliptic-curve work per record and heavy infrastructure; "
           "the capability and filegroup systems show that per-file keys scale, but they target file-system clients rather than browsers; the recent file-storage papers are the closest in aim and the weakest in evidence, since "
           "the quantities that would let a reader reproduce their results are not given. The cryptanalysis of MEGA {r:mega} is the strongest argument for measuring and testing a design before trusting it, and it motivates the bit-flip and "
           "token-forgery tests reported here.")
    P.para("**Research gap.** The surveyed work splits into attribute-based schemes evaluated by calculation, cryptographic file systems built as prototypes, role models stated as standards, and a few "
           "recent papers that report headline outcomes without their conditions. None provides a general, runnable file store that joins browser-side AES-256-GCM, per-recipient RSA key wrapping, server-enforced roles, "
           "a plaintext-hash check and a hash-chained audit log, measures each layer on one machine and reports its own weaknesses. This paper fills that gap.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.sub("A", "Design and Trust Model")
    P.para("CipherVault has no machine-learning component and no trained dataset: it is cryptographic and access-control software, and its data are fictional demonstration files and measurement workloads. "
           "The browser is the trusted endpoint; the FastAPI server is treated as honest-but-curious for confidentiality and trusted for access decisions and logging (Fig. 1). "
           "The server therefore stores ciphertext under random 32-hex file names, public keys, bcrypt password hashes, wrapped keys and a SQL metadata and audit schema of four tables, but never plaintext or a private key.")
    P.figure(figp["arch"], "System architecture of CipherVault: browser-side cryptography, FastAPI service with 24 endpoints, SQL database and a ciphertext-only store.")
    P.sub("B", "Key Hierarchy and File Encryption")
    P.para(f"At registration the browser generates an RSA-2048 key pair, derives a key-encryption key from the password with PBKDF2-HMAC-SHA-256 {{r:pbkdf2}} ({F.PBKDF2_ITER:,} iterations, 16-byte random salt) and uses it to encrypt the private key with AES-GCM {{r:gcm}}; "
           "only the encrypted bundle and the public key are sent to the server. Each file M receives a fresh random 256-bit file key FEK and a 12-byte random IV, is encrypted in memory, and the FEK is wrapped under the owner's public key "
           "with RSA-OAEP {r:oaep}:")
    P.eq("(C, T) = AES-GCM_enc(FEK, IV, M),    h = SHA-256(M)")
    P.eq("W = RSA-OAEP_pk(FEK)")
    P.para(f"The primitives follow from the threat model. GCM {{r:gcm}} gives confidentiality and integrity in one pass, which a plain CBC mode would not; its security needs a fresh nonce under each key, and for that reason every upload and every "
           f"replacement draws a new random 96-bit IV, a practice whose failure mode is documented for GCM in TLS {{r:boeck}}. RSA-OAEP is chosen over attribute-based encryption because a handful of roles needs per-recipient keys, not policies over attributes, "
           f"and the wrapped key is only 256 bytes. The {F.PBKDF2_ITER:,}-iteration derivation costs {ms(pb)} ms here; the cost is linear in the iteration count, so the {310000:,} iterations of {{r:ijedr}} would take about {ms(pb * 310000 / F.PBKDF2_ITER)} ms by proportion, "
           "a calculation and not a measurement. A larger count would slow brute-force guessing of a stolen key bundle and is the first parameter we would raise.")
    P.para(f"The upload carries C with its 16-byte tag T, the IV, the wrapped key W and h. To share, the owner's browser unwraps the FEK with the private key and re-wraps it under the recipient's public key, so the server stores one 256-byte wrapped key per recipient. "
           "On download the browser unwraps its own copy, decrypts, rejects the file if the GCM tag fails and then compares SHA-256 of the plaintext with h. "
           f"The server accepts at most {F.UPLOAD_LIMIT_MB} MB per file, a 12-byte IV, a 64-hex digest and a 256-byte wrapped key on share; logins pass a bcrypt {{r:bcrypt}} (cost {F.BCRYPT_COST}) check and receive an HS256 JSON Web Token {{r:jwt}} "
           f"valid for {F.JWT_MINUTES} min, with an in-memory limit of {F.LOGIN_LIMIT[0]} attempts per {F.LOGIN_LIMIT[1]} s per address and email.")
    P.para("The private key is decrypted only in browser memory after the user enters the password on the unlock screen; a page reload locks the vault again, and a wrong password makes the GCM check on the key bundle fail, "
           "so no server round trip can confirm or deny a guess. When an owner or editor replaces a file's content, the browser decrypts the old key copy, encrypts the new bytes under the same FEK with a fresh IV and uploads them, "
           "so every existing wrapped key stays valid and nobody has to be re-shared. The server never learns the FEK, so it cannot check that a replacement was encrypted under it; the next downloader detects a mismatch through the tag and the digest.")
    P.figure(flow, "Main flow: encrypt-and-share on the left, download-decrypt-verify on the right.")
    P.sub("C", "Role-Based Access Control")
    P.para("Every file request resolves the caller's effective role as owner, editor, viewer or none. Owner may read, replace content, delete, share, change a role, revoke and read the file's history; "
           "editor may read and replace content; viewer may read; a stranger has no access, and each refusal writes an unauthorized_access event. The check is a server-side function on every route (complete mediation), "
           "following the role model of {r:rbac01}; the global account role column exists but plays no part in decisions.")
    P.para("The permitted-operation matrix (Table III) is derived from three predicates in the permission service: can_read for owner, editor and viewer, can_write for owner and editor, and an owner-only test for delete, share, "
           "role change, revoke and the per-file history. Listing a file's access list is open to anyone who has access. Roles are per file: the same account can own one file, edit a second and merely view a third.")
    P.sub("D", "Hash-Chained Audit Log")
    P.para("Each sensitive action (register, login, upload, download, update, share, role change, revoke, delete, denial, verification) appends a row whose hash binds the previous hash to the event:")
    P.eq("h_n = SHA-256( h_prev | t_n | u_n | f_n | a_n | s_n | d_n )")
    P.para("where t is the timestamp, u the user, f the file, a the action, s the success flag, d the details and h_prev of the first entry is the string GENESIS. "
           "The verify route recomputes the chain from the oldest entry. Unlike the signed or Merkle-tree logs of {r:audit99} and {r:tamper09}, the chain has no secret key and no external anchor, which Section IV measures. The threats addressed are a curious or compromised database or disk (only ciphertext and wrapped keys are exposed), an unauthorised account (denied and logged), "
           "a modified ciphertext (rejected by the tag and digest) and casual edits to the log. Not addressed are a malicious server that ships altered JavaScript, a compromised client device, loss of the password and an attacker with write access to the whole database.")
    P.sub("E", "Implementation")
    P.para(f"The backend exposes 24 REST endpoints in five routers (authentication, users, files, sharing, audit) over four tables: users, files, file_permissions with a unique pair of file and user, and audit_logs. "
           f"Uploads are multipart forms; downloads return the ciphertext as a stream with the IV, wrapped key and digest in response headers, so the browser needs one request to decrypt. "
           f"The interface has landing, sign-in, dashboard, file list, file detail with history, sharing dialog, audit, security and unlock screens, built to work down to a 360 px width. "
           f"Demonstration accounts for the three roles seed fictional files on first use.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.sub("A", "Test Conditions")
    P.para(f"Measurements ran on {F.ENV['date']} on the machine of Section I-A. Sizes up to 1 MiB used 15 to 50 repetitions (1 KiB and 64 KiB operations were timed in batches because Chrome's clock resolves 0.1 ms), 10 MiB used 6 to 15 and 25 MiB used 3 to 4. "
           f"The suite also ran {F.PYTEST_PASSED} of {F.PYTEST_TOTAL} pytest tests ({F.PYTEST_SECONDS:.0f} s), {F.E2E_PASSED} of {F.E2E_TOTAL} API end-to-end checks and a browser walk of {F.UI_PASSED} of {F.UI_TOTAL} steps; all passed. "
           "Medians are reported unless stated. The browser timings run the same primitives and parameters as the interface's crypto module in headless Chrome, the transfer timings drive the real upload and download routes with a bearer token, "
           "the role matrix registers fresh accounts and shares a real file, and the tamper study edits copies of the real audit rows and checks them with the verifier's hash rule copied into the script.")
    P.table("Measured results (median ms unless stated)", ["Measurement", "Result"],
            [["AES-256-GCM encrypt / decrypt, 1 MiB", f"{ms(enc1)} / {ms(dec1)}"],
             ["AES-256-GCM encrypt / decrypt, 10 MiB", f"{ms(enc10)} / {ms(dec10)}"],
             ["AES-256-GCM encrypt / decrypt, 25 MiB", f"{ms(enc25)} / {ms(dec25)}"],
             ["SHA-256, 10 MiB", f"{ms(sha10)}"],
             ["RSA-2048 key generation / wrap / unwrap", f"{ms(kg)} / {ms(wrap)} / {ms(unwrap)}"],
             [f"PBKDF2, {F.PBKDF2_ITER // 1000}k iterations", f"{ms(pb)}"],
             ["Encrypted / plain upload, 1 MiB", f"{ms(up_e1)} / {ms(up_p1)}"],
             ["Encrypted / plain upload, 10 MiB", f"{ms(up_e10)} / {ms(up_p10)}"],
             ["Decrypted / plain download, 10 MiB", f"{ms(dn_e10)} / {ms(dn_p10)}"],
             ["API upload / download, 10 MiB", f"{ms(upl10)} / {ms(dnl10)}"],
             ["API upload / download, 25 MiB", f"{ms(upl25)} / {ms(dnl25)}"],
             ["Login (bcrypt) / GET me / list files", f"{ms(login)} / {ms(me)} / {ms(lst)}"],
             ["Share / change role / revoke", f"{ms(API['share_ms'])} / {ms(API['change_role_ms'])} / {ms(API['revoke_ms'])} (1 run)"],
             ["Audit-event write (p95)", f"{ms(wr['median'])} ({ms(wr['p95'])})"],
             ["Role matrix cells matched", f"{F.RBAC['matched']} of {F.RBAC['total']}"],
             ["Ciphertext bit flips rejected", f"{flips['detected']:,} of {flips['trials']:,}"],
             ["Audit-tamper classes caught", f"{len(caught)} of {n_cls}"]],
            [2.4, 1.0], size=6.3, align=["l", "c"])
    P.sub("B", "Cryptographic and Transfer Cost")
    P.para(f"Browser AES-256-GCM is fast: {ms(enc10)} ms to encrypt and {ms(dec10)} ms to decrypt 10 MiB, {ms(enc25)} and {ms(dec25)} ms at 25 MiB, growing close to linearly with size (Fig. 3a); "
           f"SHA-256 is about twice as fast. Ciphertext is exactly 16 bytes longer than plaintext. Asymmetric work is paid once per file or user: key generation takes {ms(kg)} ms, wrapping {ms(wrap)} ms, unwrapping {ms(unwrap)} ms, "
           f"and the {F.PBKDF2_ITER // 1000}k-iteration key derivation {ms(pb)} ms. End to end through the real server, encryption added {ms(ovh1)} ms to a 1 MiB upload ({ms(up_e1)} against {ms(up_p1)} ms) "
           f"and {ms(ovh10)} ms to a 10 MiB upload ({ms(up_e10)} against {ms(up_p10)} ms); decrypting and verifying a 10 MiB download took {ms(dn_e10)} against {ms(dn_p10)} ms plain (Fig. 3b). "
           f"The overhead is a small part of the transfer but of the same size as the run-to-run spread of the shared host, so we read it as roughly {ms(ovh1)} to {ms(ovh10)} ms, not as a precise figure. A 25 MiB upload through the API took {ms(upl25)} ms and the download {ms(dnl25)} ms; "
           f"a request above the limit received HTTP {API['upload_limit_check']['over_25MB_status']}.")
    P.para(f"The remaining server routes are light. A login costs {ms(login)} ms at the median and a failed login {ms(API['login_fail_ms']['median'])} ms, almost all of it the deliberately slow bcrypt hash; "
           f"authenticated metadata calls take {ms(me)} ms, the health route {ms(API['health_ms']['median'])} ms, listing 65 owned files {ms(lst)} ms, sharing {ms(API['share_ms'])} ms, a role change {ms(API['change_role_ms'])} ms "
           f"and a revoke {ms(API['revoke_ms'])} ms, each a single run. Writing one audit event took {ms(wr['median'])} ms at the median and {ms(wr['p95'])} ms at p95, which is the price of the read-then-insert hash step on every request that is logged. "
           f"API upload and download time grew about linearly with size, from {ms(API['upload_ms'][KB]['median'])} and {ms(API['download_ms'][KB]['median'])} ms at 1 KiB.")
    P.figure(figp["results"], "Median latency: (a) AES-256-GCM and SHA-256 in the browser against plaintext size; (b) encrypted and plain transfers through the server.")
    P.sub("C", "Output Screens")
    P.para("Fig. 4 shows the sharing dialog of a demonstration owner with an editor and a viewer listed; the text states that the file key is re-wrapped in the browser and never sent in plaintext. "
           f"Fig. 5 shows the audit page after the verify button was pressed: the chain was valid over 226 entries at that moment (a later verification of the measurement database covered {F.M['audit_live_verify']['checked']:,} valid entries).")
    P.figure(figp["share"], "Share dialog (real capture, 1440x900 page): per-file roles and the key re-wrap notice.", width=1.9)
    P.figure(figp["audit"], "Audit page after chain verification: 226 entries valid, with the hash column (crop of a real capture).")
    P.sub("D", "Access Control and Integrity")
    P.para(f"A live test of four principals (owner, editor, viewer and an unrelated user) against nine operations (metadata, download, update, list access, share, change role, revoke, file history, delete) expected {n_allow} allowed and {n_deny} denied cells and observed exactly those: {F.RBAC['matched']} of {F.RBAC['total']}; unauthenticated requests received HTTP 401, as did forged, expired, "
           f"wrong-secret and alg=none tokens; after a revoke the same user's download returned HTTP {API['download_after_revoke_status']}. This is exhaustive over the implemented operations on one file, not a user study, "
           f"so the 98.6% of {{r:ijedr}} (13 errors in 900 attempts by 50 users) is a different experiment. All {flips['trials']:,} random single-bit changes to a 4 KiB AES-256-GCM ciphertext were rejected (tested with the Python cryptography library, the same algorithm as the browser), and a wrong key was refused.")
    P.table("Permitted operations per role (observed live)", ["Role", "Read, list", "Replace", "Delete", "Share, role, revoke, history"],
            [["Owner", "yes", "yes", "yes", "yes"], ["Editor", "yes", "yes", "no", "no"], ["Viewer", "yes", "no", "no", "no"], ["No role", "no", "no", "no", "no"]],
            [0.7, 0.7, 0.6, 0.6, 0.8], size=6.3, align=["l", "c", "c", "c", "c"])
    P.para(f"We then edited an unmodified chain of {F.TAMPER['audit_entries_available']} entries in nine ways (Fig. 6). Editing any field or the stored hash, deleting a middle entry, swapping neighbours and inserting a forged entry "
           f"were detected in every trial ({len(caught)} of {n_cls} classes). Removing entries from the tail was not detected in any of {tr['trials']} trials, and rewriting an edited entry together with every later hash passed verification, "
           "because the verifier checks only internal consistency and the chain has no signature or external anchor. A fully compromised database could therefore hide its tracks.")
    P.figure(figp["tamper"], "Share of trials in which each audit or ciphertext tampering was detected (per-class counts shown).")
    P.para(f"Observed against the objectives, the encryption and hash checks cost little, the role check is exact over the operations tested, and the audit log needs work. Three remedies follow from the measurements. "
           "First, serialise the read-then-insert step of the audit writer, for example with a database transaction that locks the last row, so concurrent requests cannot fork the chain. "
           "Second, sign the chain head or write it to a store the application cannot modify, which would expose both tail truncation and a recomputed rewrite, as the designs of {r:audit99} and {r:tamper09} do. "
           "Third, make verification incremental from a trusted checkpoint, because a full walk grows linearly and reached "
           f"{ms(sc['5000']['verify_ms_median'])} ms at 5,000 entries.")
    P.sub("E", "Comparison with the Base Paper")
    P.para(f"The base paper's {base_num['proposed_us']['total_x5']:,} µs per record is a calculation of attribute-based encryption from OpenSSL timings on a Raspberry Pi; CipherVault's {ms(enc10)} ms is a measured AES-GCM operation over a 10 MiB file in a browser. "
           "The workloads, hardware and metrics differ, so the figures cannot be ranked. Against the IJEDR paper {r:ijedr}, which reports +320 ms for a 10 MB upload, we measured about "
           f"{ms(ovh10)} ms of end-to-end overhead for 10 MiB, but its hardware, network and chunked, signed pipeline are undisclosed; likewise its 100% tamper detection covers 50 events and ours covers nine classes, one of which fails. "
           f"Two design differences are certain: CipherVault uses {F.PBKDF2_ITER:,} PBKDF2 iterations against 310,000, and has no multi-factor sign-in, chunking or ECDSA-signed log entries.")
    P.sub("F", "Failure Cases and Limits")
    P.para(f"Besides the unmasked tail truncation, 100 concurrent failed logins across four workers left the chain invalid at entry {conc['failure_at']:,} of {conc['checked']:,}, because the writer reads the last hash and commits without a lock. "
           f"Verification time grows linearly: {ms(sc['461']['verify_ms_median'])} ms for 461 entries and {ms(sc['5000']['verify_ms_median'])} ms for 5,000. "
           "Revocation deletes the server's wrapped key but cannot recall a key or ciphertext already downloaded, and there is no re-keying. Replacing content reuses the same file key with a fresh random 96-bit IV, so the nonce-collision bound applies after very many updates {r:boeck}. "
           "The server delivers the JavaScript that performs the cryptography, file names, sizes and owners are plaintext metadata, a lost password means lost data, the token lives in sessionStorage, "
           "the audit list is visible to any signed-in user, and files above 25 MB are not supported because encryption is whole-file in memory. "
           "Firefox, Safari, PostgreSQL, multi-user load and assistive-technology audits were not tested.")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion and Future Scope")
    P.para(f"CipherVault meets its six objectives: registration with bcrypt and JWT, AES-256-GCM encryption before upload, owner-and-role access control, SHA-256 verification on download, an audit log of uploads, downloads, deletions "
           f"and denials, and a measured evaluation. Encryption cost is small next to the transfer itself ({ms(enc10)} ms for 10 MiB), the role model matched in all {F.RBAC['total']} cells, and all 2,000 random bit flips in a test ciphertext were rejected. "
           "The main finding is about the audit trail: a plain hash chain detects edits, deletions and reordering but not truncation or a recomputed rewrite, and it breaks under concurrent writers. "
           "Limits are the shared measurement host, one browser, a 25 MB cap, no user study and the trust placed in the server's JavaScript. "
           "Future work in order of value: serialise audit writes and sign or externally anchor the chain head; chunked streaming for large files; key rotation on revoke; multi-factor sign-in; "
           "restricting the global audit list to the caller's own files; and testing on more browsers and under multi-user load.")
    P.references()
    P.save(path)
    return P
