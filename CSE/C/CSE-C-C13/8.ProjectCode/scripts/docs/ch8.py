"""Chapter 8: Results and output screens for CipherVault. Every number is read from facts.py (docs/metrics/metrics.json, tests.json) or comes from the real screenshots in docs/screenshots."""
import os

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, P, PAIR, TAB
from .refs import N

SH = F.shot
SZ = {"1024": "1 KiB", "65536": "64 KiB", "1048576": "1 MiB", "10485760": "10 MiB", "26214400": "25 MiB"}


def S(path, caption, base=5.6, max_h=3.7):
    """Screenshot figure with a width that keeps the picture on one page."""
    return FIG(path, caption, F.shot_w(path, base, max_h))


def G(name, caption, width=5.4, doc_only=False):
    """Result figure from docs/figures; omitted if the file is missing, or (doc_only) in the compact report variant."""
    path = F.fig(name)
    if doc_only and F.REPORT:
        return []
    return [FIG(path, caption, width)] if os.path.exists(path) else []


def full(*blocks):
    """Blocks that appear only in the stand-alone Results document, not in the compact report chapter."""
    return [] if F.REPORT else list(blocks)


def _crop(name, out, box):
    """Crop of a tall screenshot (written once to docs/figures) so that the useful part is legible at page width."""
    dst = F.fig(out)
    if not os.path.exists(dst):
        from PIL import Image

        os.makedirs(F.FIGS, exist_ok=True)
        with Image.open(SH(name)) as im:
            im.crop(box).save(dst)
    return dst


def _compact(blocks):
    """Report variant: drop the sub-headings and put the screenshots two per figure, each with its own caption."""
    out, pend = [], []
    for blk in blocks:
        if blk[0] == "h3":
            continue
        if blk[0] == "fig":
            pend.append((blk[1], blk[2]))
            if len(pend) == 2:
                out.append(PAIR(pend, 2.95))
                pend = []
        else:
            out.append(blk)
    if pend:
        out.append(FIG(pend[0][0], pend[0][1], 4.0))
    return out


def _m(d):
    """median / p95 pair as text."""
    return f"{F.ms(d['median'])} / {F.ms(d['p95'])}"


# ----------------------------------------------------------------------------------------------- 8.1
def _setup():
    e = F.ENV
    return [H2("8.1 Experimental set-up"),
            P(f"All measurements in this chapter were made on one desktop computer: {e['cpu']}, {e['ram_gb']} GB of memory, Windows 11, Python {e['python']} for the server and the measurement scripts, "
              f"and Google Chrome {F.BR['browser_version']} (headless) for everything that runs in the browser. Client and server communicated over the loopback address {e['loopback']}, so the figures contain no network latency. "
              "Other programs, including other automated sessions, were using the processor during the runs; absolute timings are therefore indicative, and repeated runs of the 10 MiB cases differed by up to about a factor of three. "
              "CipherVault trains nothing and uses no dataset: there is no accuracy, precision or F1-score to report. What can be measured, and what this chapter reports, is the cost of the cryptography, the latency of the server, "
              "whether the access rules give the expected answer for every combination of user and operation, and whether tampering is detected."),
            *full(TAB("Experiments and what each measured.", ["Experiment", "Set-up", "Quantity measured"],
                [["Browser cryptography (8.3)", f"Web Crypto in headless Chrome; AES-256-GCM and SHA-256 on random data of 1 KiB, 64 KiB, 1 MiB, 10 MiB and 25 MiB (50, 50, 20, 8 and 4 repetitions); RSA-2048 key generation 12 times; wrap and unwrap 40 times; PBKDF2 12 times",
                  "Median, 95th percentile (p95), ciphertext overhead"],
                 ["End-to-end pipeline (8.4)", "In the browser: generate file key, encrypt, hash, wrap, upload, download, unwrap, decrypt, verify; same endpoint with an unencrypted payload as baseline; 30, 20 and 15 repetitions for 1 KiB, 1 MiB, 10 MiB", "Time per complete upload and download"],
                 ["Server API (8.5)", "Python HTTP client against a throw-away server and database, 1 to 60 repetitions per call", "Latency per endpoint, upload and download of 1 KiB to 25 MiB"],
                 ["Access control (8.6)", "Four principals (owner, editor, viewer, stranger) times nine operations on one shared file, plus unauthenticated and forged tokens", "Observed HTTP status against the expected allow or deny"],
                 ["Integrity and audit (8.7)", "2,000 random bit flips in an AES-GCM ciphertext; nine kinds of manipulation applied to a copy of the real audit log, about 200 trials each; chain verification at five log sizes; 100 concurrent logins", "Detection rate, verification time, chain validity"],
                 ["Automated tests (8.8)", "pytest suite, API end-to-end script, browser walk-through, evaluation script", "Checks passed"]],
                widths=[1.4, 3.3, 1.8], align=["l", "l", "l"], size=9.5)),
            P("Timings are the median with the 95th percentile (p95), because a few slow runs dominate the mean on a shared machine. "
              "Chrome rounds its clock to 0.1 ms, so operations on 1 KiB and 64 KiB were timed in batches of 200 and divided. The scripts are `scripts/measure_metrics.py`, `scripts/evaluate.py`, `scripts/e2e_check.py` and `scripts/smoke_test.py`; "
              "the raw figures are in `docs/metrics/metrics.json`.")]


# ----------------------------------------------------------------------------------------------- 8.2
def _screens():
    crop = _crop("08_file-detail.png", "r08_file_detail_crop.png", (0, 0, 1440, 1130))
    b = [H2("8.2 Output screens"),
         P("The screens below were captured from the running application at 1440 by 900 pixels (one is cropped) with the demonstration data that the demo login creates: five fictional text files owned by Olivia Owner, "
           "shared with an editor (Eddie Editor) and a viewer (Vera Viewer). The vault was unlocked, the audit log held more than two hundred real events, and no screen is empty or a mock-up. The landing, sign-in and registration pages and the mobile layouts are in Appendix C.")]
    b += [H3("8.2.1 Dashboard and file list"),
          S(SH("06_dashboard.png"), "Dashboard of the owner: four counters (5 files can be opened, 5 are owned, 0 shared with the user, 706 B of plaintext stored), a chart of vault-wide audit events per day, the donut of access by role (all five files owned), the security-status chips *Encrypted before upload*, *Ciphertext-only storage*, *Role-based access* and *AES-256-GCM, RSA-2048, SHA-256*, and the recent-activity list. The event chart is flat before 22 October because all events were generated on that day."),
          S(SH("07_my-files.png"), "My files: the drop zone (any file type up to 25 MB, encrypted with AES-256-GCM before it leaves the tab) and the list of the five encrypted files with name, MIME type, plaintext size, role, last update and the download, open, share and delete buttons; the table can be searched, sorted and filtered by role.")]
    b += [H3("8.2.2 File details and sharing"),
          S(crop, "File details for *Q3-board-memo.txt*: 165 B of plaintext stored as 181 B of ciphertext, the SHA-256 of the plaintext and the AES-GCM initialisation vector, the access list (owner, editor, viewer) and the owner-only file history. "
                  "The history, newest first, shows five downloads by the viewer and the red *Access denied* entry for the viewer's delete attempt (*delete denied (owner only)*); the older entries (editor's content replacement, two shares, upload) lie below the crop.", 5.6, 4.3),
          S(SH("09_share-access.png"), "Share dialog: recipient e-mail, role (Viewer, read and download; Editor), the *Grant access* button and the statement that the file key is unwrapped and re-wrapped for the recipient in this browser and never sent in plaintext; below, the current access list with a role selector and a remove button for each collaborator.")]
    b += [H3("8.2.3 Audit log"),
          S(SH("10_audit-log.png"), "Audit log after *Verify audit chain*: the message *Audit chain valid. 226 entries checked.* above the event table (number, time, action, user, file, result, details and a shortened SHA-256) with search and action and result filters; the newest entries are sign-ins and a ciphertext download by the viewer.")]
    b += [H3("8.2.4 Security profile and vault lock"),
          S(SH("11_security.png"), "Security profile: account data, the key status (public key registered, encrypted private key stored, this session unlocked in memory), the *Lock vault now* button and the five protection statements."),
          S(SH("12_unlock-vault.png"), "Unlock dialog shown after the vault was locked: the private key was cleared from browser memory (toast *Vault locked*) and is decrypted again only after the password is entered; a page reload locks the vault in the same way.")]
    return _compact(b) if F.REPORT else b


# ----------------------------------------------------------------------------------------------- 8.3
def _browser_crypto():
    A = F.AES
    rows = []
    for k, lab in SZ.items():
        a = A[k]
        thr = "-"
        if int(k) >= 1048576:
            thr = f"{int(k) / 1048576 / (a['encrypt']['median'] / 1000):.0f}"
        rows.append([lab, _m(a["encrypt"]), _m(a["decrypt"]), _m(a["sha256"]), str(a["overhead"]), thr])
    c = F.CRY
    prim = [["RSA-2048 key pair generation (once per account)", str(c["rsa_keygen"]["n"]), f"{F.ms(c['rsa_keygen']['median'])} / {F.ms(c['rsa_keygen']['p95'])}"],
            ["PBKDF2-HMAC-SHA-256, 120,000 iterations (each unlock)", str(c["pbkdf2_120k"]["n"]), _m(c["pbkdf2_120k"])],
            ["RSA-OAEP wrap of the file key (per share and per upload)", str(c["rsa_wrap"]["n"]), f"{F.ms(c['rsa_wrap']['median'])} / {F.ms(c['rsa_wrap']['p95'])}"],
            ["RSA-OAEP unwrap of the file key (per download)", str(c["rsa_unwrap"]["n"]), f"{F.ms(c['rsa_unwrap']['median'])} / {F.ms(c['rsa_unwrap']['p95'])}"]]
    one_mib = A["1048576"]
    est = one_mib["encrypt"]["median"] + one_mib["sha256"]["median"] + c["rsa_wrap"]["median"]
    b = [H2("8.3 Cryptographic cost in the browser"),
         P("Every file is encrypted and hashed in the browser before the first byte is sent, so the first question is what that costs. The first table below gives the median and p95 of one AES-256-GCM encryption, one decryption and one SHA-256 digest at five file sizes, "
           f"with the added length and the encryption throughput where the call overhead no longer dominates. The use of AES-GCM follows {N('gcm')} and the digest {N('sha')}."),
         TAB("Web Crypto timings in headless Chrome (median / p95, ms).", ["Plaintext size", "AES-GCM encrypt", "AES-GCM decrypt", "SHA-256", "Added bytes", "Encrypt MiB/s"], rows,
             widths=[1.0, 1.25, 1.25, 1.1, 0.8, 1.1], align=["l", "c", "c", "c", "c", "c"], size=10),
         P(f"Encryption of a 25 MiB file takes {F.ms(A['26214400']['encrypt']['median'])} ms and decryption {F.ms(A['26214400']['decrypt']['median'])} ms, a throughput of roughly 420 to 465 MiB/s; the cost grows linearly with size, as the first chart below shows on logarithmic axes. "
           "The ciphertext is always exactly 16 bytes longer than the plaintext, the length of the GCM authentication tag, so storage overhead is negligible. "
           f"Hashing costs about half as much as encryption. For a 1 MiB file the file-level cryptography (encryption, digest and key wrapping, summed from separately measured medians) is about {est:.1f} ms."),
         *G("f01_aes_latency_vs_size.png", f"AES-256-GCM encryption, decryption and SHA-256 time against file size (median, log-log): {F.ms(F.AES['26214400']['encrypt']['median'])} ms to encrypt 25 MiB.", 5.0),
         TAB("Key-management primitives in the browser (n = repetitions; median / p95, ms).", ["Operation", "n", "Median / p95"], prim, widths=[4.0, 0.6, 1.5], align=["l", "c", "c"], size=10),
         P(f"Key management is the other cost. Generating the RSA-2048 key pair takes about {F.ms(c['rsa_keygen']['median'])} ms once, at registration. Deriving the key-encryption key from the password with PBKDF2 takes {F.ms(c['pbkdf2_120k']['median'])} ms on this machine; "
           f"this is deliberately the slowest step of an unlock. Wrapping the file key for a recipient takes {F.ms(c['rsa_wrap']['median'])} ms and unwrapping it {F.ms(c['rsa_unwrap']['median'])} ms, and a wrapped key is always {c['rsa_wrapped_bytes']} bytes. "
           f"The iteration count of 120,000 is below the 310,000 reported by {N('ijedr')}; the time an attacker needs per guess scales with this count (Section 8.12)."),
         *G("f08_crypto_primitives.png", "Key-management primitives in the browser (median, log scale): key generation, PBKDF2, wrap and unwrap.", 4.6, doc_only=True)]
    return b


# ----------------------------------------------------------------------------------------------- 8.4
def _e2e():
    E = F.E2E
    rows = []
    for k in ("1024", "1048576", "10485760"):
        e = E[k]
        du = e["encrypted_up"]["median"] - e["plain_up"]["median"]
        dd = e["encrypted_down"]["median"] - e["plain_down"]["median"]
        rows.append([SZ[k], _m(e["encrypted_up"]), _m(e["plain_up"]), f"{du:+.1f}", _m(e["encrypted_down"]), _m(e["plain_down"]), f"{dd:+.1f}"])
    e10 = E["10485760"]
    e1 = E["1048576"]
    return [H2("8.4 End-to-end upload and download"),
            P("The next experiment times the whole user-visible operation in the browser. An encrypted upload generates the file key, encrypts, hashes, wraps the key with the owner's public key and posts the multipart request; an encrypted download fetches the ciphertext, unwraps the key, decrypts and compares the SHA-256. "
              "The baseline sends the same bytes unencrypted to the same endpoint (with the digest and a wrapped key left over from the encrypted run, so that the server's validation passes) and fetches them back without decryption. The table below gives the medians and the difference of the medians."),
            TAB("Browser upload and download with and without encryption (median / p95, ms; difference = encrypted minus plain, medians).",
                ["Size", "Encrypted upload", "Plain upload", "Diff.", "Encrypted download + verify", "Plain download", "Diff."], rows,
                widths=[0.7, 1.1, 1.0, 0.55, 1.4, 1.1, 0.55], align=["l", "c", "c", "c", "c", "c", "c"], size=9.5),
            P(f"For 10 MiB the encrypted upload took {F.ms(e10['encrypted_up']['median'])} ms against {F.ms(e10['plain_up']['median'])} ms for the unencrypted one, and the encrypted download with decryption and digest check {F.ms(e10['encrypted_down']['median'])} ms against {F.ms(e10['plain_down']['median'])} ms. "
              f"The difference of the medians is therefore {e10['encrypted_up']['median'] - e10['plain_up']['median']:.0f} ms for the upload and {e10['encrypted_down']['median'] - e10['plain_down']['median']:.0f} ms for the download. "
              f"The 95th-percentile ranges of the two variants overlap at every size and the spread between repetitions is larger than some of the differences (at 1 KiB the difference is smaller than the noise), so these differences should be read as estimates of the order of magnitude, not as resolved values. "
              + ("" if F.REPORT else f" The time spent only in the encryption call is {F.ms(e1['enc_only']['median'])} ms for 1 MiB and {F.ms(e10['enc_only']['median'])} ms for 10 MiB, which is consistent with the browser timings of Section 8.3.")),
            *G("f02_e2e_overhead.png", f"Encrypted against plain transfer in the browser (median, whisker to p95): at 10 MiB the encrypted upload takes {F.ms(e10['encrypted_up']['median'])} ms and the plain one {F.ms(e10['plain_up']['median'])} ms.", 5.0, doc_only=True)]


# ----------------------------------------------------------------------------------------------- 8.5
def _api():
    A = F.API
    rows = [["Health check (`GET /api/health`)", str(A["health_ms"]["n"]), _m(A["health_ms"])],
            ["Current user (`GET /api/auth/me`, JWT check and one query)", str(A["me_ms"]["n"]), _m(A["me_ms"])],
            ["Login, correct password (bcrypt cost 12, JWT, audit entry)", str(A["login_ms"]["n"]), _m(A["login_ms"])],
            ["Login, wrong password of an existing account", str(A["login_fail_ms"]["n"]), _m(A["login_fail_ms"])],
            ["Failed login of an unknown e-mail (one audit entry written)", str(F.M["audit_write_ms"]["n"]), _m(F.M["audit_write_ms"])],
            ["List the user's own files", str(A["list_files_ms"]["n"]), _m(A["list_files_ms"])],
            ["Share a file (one run)", "1", F.ms(A["share_ms"])],
            ["Change a role (one run)", "1", F.ms(A["change_role_ms"])],
            ["Revoke access (one run)", "1", F.ms(A["revoke_ms"])],
            [f"Download after revoke (one run, HTTP {A['download_after_revoke_status']})", "1", F.ms(A["download_after_revoke_ms"])]]
    xs = []
    for k, lab in SZ.items():
        kk = "26212352" if k == "26214400" else k
        xs.append([lab if k != "26214400" else "about 25 MiB", str(A["upload_ms"][kk]["n"]), _m(A["upload_ms"][kk]), _m(A["download_ms"][kk])])
    return [H2("8.5 Server API latency"),
            P("The server was measured separately with a Python client over loopback, so that the cost of the FastAPI application, the database and the file store is visible without the browser. The ciphertexts used here were produced with AES-GCM in Python, since the server cannot tell the difference. "
              "The first table lists the control-plane calls; the second gives upload and download of ciphertext objects of increasing size."),
            TAB("Latency of the API calls (median / p95, ms).", ["Call", "n", "Median / p95"], rows, widths=[4.3, 0.5, 1.6], align=["l", "c", "c"], size=9.5),
            P(f"Calls that do little work return in a few milliseconds ({F.ms(A['health_ms']['median'])} ms for the health check). Login is dominated by bcrypt at cost 12, about {F.ms(A['login_ms']['median'])} ms, which is the intended price of slowing down password guessing {N('bcrypt')}. "
              f"A wrong password costs the same, as it should. A failed login for an e-mail that does not exist, however, takes only {F.ms(F.M['audit_write_ms']['median'])} ms: the code skips the bcrypt comparison when no account is found, so response time tells an attacker whether an account exists (Section 8.11). "
              f"This call also measures one audit write, because every failed login adds an audit entry." if not F.REPORT else ""),
            TAB("Upload and download of ciphertext through the API (median / p95, ms).", ["Object size", "n", "Upload", "Download"], xs, widths=[1.5, 0.6, 1.9, 1.9], align=["l", "c", "c", "c"], size=10),
            P(f"A 25 MiB object, the largest the server accepts, uploads in {F.ms(A['upload_ms']['26212352']['median'])} ms and downloads in {F.ms(A['download_ms']['26212352']['median'])} ms, based on only three runs. "
              f"An upload larger than the 25 MB limit was rejected with HTTP {A['upload_limit_check']['over_25MB_status']}. Both directions grow roughly linearly with size."),
            *G("f03_api_latency.png", f"API latency over loopback (median, marker at p95): login {F.ms(A['login_ms']['median'])} ms (bcrypt), health check {F.ms(A['health_ms']['median'])} ms.", 4.8, doc_only=True),
            *G("f04_api_transfer_scaling.png", "Upload and download of ciphertext against object size (median, shaded to p95).", 4.6, doc_only=True)]


# ----------------------------------------------------------------------------------------------- 8.6
def _rbac():
    cells = F.RBAC["cells"]
    ops = []
    for c in cells:
        if c["operation"] not in ops:
            ops.append(c["operation"])
    label = {"metadata": "View metadata (`GET /api/files/{id}`)", "download": "Download ciphertext", "update": "Replace content (`PUT`)",
             "list_permissions": "List permissions", "share": "Share a file", "change_role": "Change a role", "revoke": "Revoke access",
             "file_audit": "View the file's audit history", "delete": "Delete the file"}
    rows = []
    for op in ops:
        r = [label[op]]
        for p in ("owner", "editor", "viewer", "stranger"):
            c = next(x for x in cells if x["principal"] == p and x["operation"] == op)
            r.append(f"{c['status']}" + ("" if c["match"] else " (!)"))
        rows.append(r)
    R = F.RBAC
    return [H2("8.6 Access-control correctness"),
            P(f"Role-based access control is checked on the server for every request. To test it exhaustively, one file was shared with an editor and a viewer, and each of four principals (the owner, the editor, the viewer and a registered user with no access) attempted each of the nine operations on it. "
              f"The table below shows the HTTP status observed; 200 means allowed and 403 means denied. All {R['total']} cells matched the rule table of the design (owner: everything; editor: read and replace content; viewer: read; stranger: nothing), an agreement of {R['accuracy'] * 100:.0f} per cent."),
            TAB("Observed HTTP status for every principal and operation (36 cells, all as expected).", ["Operation", "Owner", "Editor", "Viewer", "Stranger"], rows, widths=[2.9, 0.8, 0.8, 0.8, 0.9], align=["l", "c", "c", "c", "c"], size=10),
            P(f"Requests without a token were answered with HTTP 401 in all {len(R['unauthenticated_statuses'])} cases, and four invalid tokens (forged signature, expired, signed with the wrong secret, and one with the algorithm set to `none`) were all rejected with HTTP {R['forged_token_status']}. "
              f"After the owner revoked the editor's access, the editor's next download returned HTTP {F.API['download_after_revoke_status']} in {F.ms(F.API['download_after_revoke_ms'])} ms. "
              "The experiment is exhaustive over the implemented operations on one file; it is a correctness check of the rule table, not a user study, and it does not measure access-control accuracy in the sense of a classifier."),
            *G("f05_rbac_matrix.png", "Access-control matrix on the live API: observed status for four principals and nine operations; 36 of 36 matched the expected decision.", 4.6, doc_only=True)]


# ----------------------------------------------------------------------------------------------- 8.7
def _integrity():
    T = F.TAMPER
    kinds = [("edit_details", "Edit the details text of an entry"), ("edit_action", "Change the action of an entry"), ("edit_success", "Flip the success flag"),
             ("edit_user", "Change the user of an entry"), ("edit_hash", "Overwrite the stored hash"), ("delete_entry_middle", "Delete an entry in the middle"),
             ("swap_adjacent", "Swap two adjacent entries"), ("insert_forged_entry", "Insert a forged entry"), ("truncate_tail", "Cut off the newest entries")]
    rows = []
    for k, lab in kinds:
        a = T["audit_tamper"][k]
        rows.append([lab, str(a["trials"]), str(a["detected"]), F.pct(a["detected"] / a["trials"], 0)])
    rows.append(["Rewrite one entry and recompute every later hash", "1", "0" if not T["audit_rechain_attack_detected"] else "1", "not detected" if not T["audit_rechain_attack_detected"] else "detected"])
    S_ = F.SCALE
    keys = sorted(S_, key=int)
    srows = [[str(S_[k]["checked"]), F.ms(S_[k]["verify_ms_median"])] for k in keys]
    C = F.CONC["4_workers"]
    return [H2("8.7 Integrity and tamper evidence"),
            P(f"Two mechanisms detect tampering. For file contents, AES-GCM authenticates the ciphertext and the browser compares the SHA-256 of the decrypted bytes with the stored digest. "
              f"In {T['ciphertext_bitflip']['trials']:,} trials with one random bit changed in an AES-GCM ciphertext, decryption failed in {T['ciphertext_bitflip']['detected']:,}; a wrong key was rejected as well. "
              "This test used the Python implementation of the same primitive on a 4 KiB message, not the browser. "
              f"For the audit log, each entry stores the SHA-256 of the previous hash and its own fields, and `verify_chain` recomputes the chain {N('audit99')}, {N('tamper09')}. Nine manipulations were applied to an in-memory copy of the {T['audit_entries_available']} real entries of the measurement run, "
              "with a verifier equal to the server's. The table below gives the result."),
            TAB("Detection of manipulations of the audit log (copy of a real log).", ["Manipulation", "Trials", "Detected", "Rate"], rows, widths=[3.6, 0.8, 0.8, 1.0], align=["l", "c", "c", "c"], size=10),
            P("Eight of the nine classes were detected in every trial. Two weaknesses are real and are stated here as findings. **Truncating the newest entries was never detected (0 of "
              f"{T['audit_tamper']['truncate_tail']['trials']}):** the remaining prefix is still a valid chain, and nothing outside the database records how long the chain should be. **An attacker who rewrites an entry and recomputes all later hashes is not detected either,** because the chain uses no secret key and has no external anchor. "
              "Detection therefore holds against careless or partial edits, not against an adversary with write access to the whole table."),
            *G("f06_tamper_detection.png", "Detection rate per manipulation class: eight classes at 100 per cent, tail truncation at 0 per cent; 2,000 of 2,000 ciphertext bit flips were rejected.", 4.8),
            P((f"Verification time grows with the log: {srows[0][1]} ms for {srows[0][0]} entries and {srows[-1][1]} ms for {srows[-1][0]} entries, with scatter caused by other processes (median of three runs); the verifier reads the whole table, so the cost is linear in the log length. " if not F.REPORT else "")
              + f"The most serious defect appeared in the concurrency check. {C['requests']} failed logins were sent through {4} parallel workers in {C['seconds']} s; the chain had been valid before and was **invalid afterwards, with the first broken link at entry {C['failure_at']} of {C['checked']}**. "
              "`record_event` reads the last hash, computes the next one and commits without a lock, so two simultaneous requests chain to the same predecessor and the log forks. A single-writer assumption is built in; the defect is documented here and was not fixed."),
            *G("f07_chain_verify_scaling.png", "Time to verify the audit chain against its length (median of three runs).", 4.4, doc_only=True),
            *G("f10_audit_concurrency.png", f"Audit chain before and after {C['requests']} concurrent failed logins: valid before, first broken link at entry {C['failure_at']} afterwards.", 4.4, doc_only=True)]


# ----------------------------------------------------------------------------------------------- 8.8
def _tests():
    rows = [["pytest suite (`tests/`: authentication 6, crypto 5, files 3, RBAC 5, audit 2)", f"{F.PYTEST_PASSED} / {F.PYTEST_TOTAL}", f"{F.PYTEST_SECONDS:.0f} s"],
            ["API end-to-end script (`scripts/e2e_check.py`)", f"{F.E2E_PASSED} / {F.E2E_TOTAL}", "register to delete, 285 audit entries verified"],
            ["Browser walk-through (`scripts/smoke_test.py`, Chrome)", f"{F.UI_PASSED} / {F.UI_TOTAL}", "register, upload, download, share, revoke, audit, lock, 360 / 768 px"],
            ["Evaluation script (`scripts/evaluate.py`)", f"{F.EVAL_PASSED} / {F.EVAL_TOTAL}", "primitives, authorisation, tamper checks"]]
    return [H2("8.8 Automated tests"),
            TAB("Automated checks and their outcome.", ["Check", "Passed", "Remark"], rows, widths=[3.5, 0.9, 2.1], align=["l", "c", "l"], size=10),
            P("All four sets passed on the code as measured. The evaluation script times a *Python* implementation under the name *browser_encrypt*; those timings are not browser timings and are superseded by Section 8.3. "
              "What was **not** tested: many simultaneous users, files above 25 MB, browsers other than Chrome, the PostgreSQL configuration, the Docker build, and an accessibility audit with a screen reader."),
            *G("f09_test_summary.png", "Automated checks passed: 21 of 21 pytest tests, 17 of 17 API checks, 18 of 18 browser steps, 17 of 17 evaluation checks.", 4.4, doc_only=True)]


# ----------------------------------------------------------------------------------------------- 8.9
def _samples():
    rows = [["Plaintext file", "`Q3-board-memo.txt`, text/plain, 165 B (after the editor replaced the original 217 B upload)"],
            ["Stored object", "181 B of ciphertext (165 B + 16 B tag) under a random 32-character hexadecimal name; the real file name appears only in the database"],
            ["SHA-256 of plaintext", "`652b4723fe9e13590fa166c7a87e90d74151048ee774c8b77a7aa719559fed96`"],
            ["AES-GCM IV", "`9FuZxp4z9WWxWTo8` (12 bytes in base64, a fresh random value for each encryption)"],
            ["Wrapped file key", "256 bytes (344 base64 characters) for each of the three principals; the owner's copy is stored with the file, the others in `file_permissions`"],
            ["API check run", "`e2e-report.txt`: 16,000 B of plaintext, 16,016 B stored; server holds ciphertext, not plaintext"]]
    ev = [["226", "4:27 PM", "Signed in", "owner@example.com", "-", "Success", "login: owner@example.com", "3ed4ed87...1551be"],
          ["225", "4:27 PM", "Signed in", "owner@example.com", "-", "Success", "login: owner@example.com", "06f35c02...01ecbf"],
          ["224", "4:26 PM", "File downloaded", "viewer@example.com", "#2", "Success", "ciphertext download by viewer@example.com", "e4520728...2b6988"],
          ["223", "4:26 PM", "Signed in", "viewer@example.com", "-", "Success", "login: viewer@example.com", "9c1704e2...f03e59"]]
    v = F.M["audit_live_verify"]
    return [H2("8.9 Sample inputs and outputs"),
            P("The following values are taken from the application's own screens and measurement runs, not constructed. The first table describes one stored file as the file-details screen shows it."),
            TAB("One stored file as shown on the details screen (file-details screen).", ["Item", "Value"], rows, widths=[1.5, 5.0], align=["l", "l"], size=9.5),
            P("The second table reproduces four consecutive entries of the audit log from the audit screen; the hash column is shortened by the interface to the first eight and last six characters."),
            TAB("Entries 223 to 226 of the audit log (audit-log screen).", ["#", "Time", "Action", "User", "File", "Result", "Details", "Hash"], ev, widths=[0.35, 0.55, 0.85, 1.15, 0.35, 0.55, 1.5, 1.2], align=["c", "c", "l", "l", "c", "c", "l", "l"], size=8),
            P(f"The chain verification endpoint returned `{{\"valid\": true, \"checked\": {v['checked']}, \"failure_at\": null, \"message\": \"{v['message']}\"}}` at the end of the measurement run, and the same endpoint after the concurrent logins returned a failure at entry {F.CONC['4_workers']['failure_at']} (Section 8.7). "
              "A request for a file without permission returns `{\"detail\": \"Access denied\"}` with status 403 and adds an `unauthorized_access` entry; an upload above the limit returns status 413.")]


# ----------------------------------------------------------------------------------------------- 8.10, 8.11
def _success():
    T = F.TAMPER
    return [H2("8.10 Success cases"),
            B(f"**The server never holds plaintext.** In the end-to-end check the stored object of a 16,000-byte file was 16,016 bytes of ciphertext, and the details screen shows the same 16-byte difference for a real file.",
              f"**Access rules behave exactly as specified:** {F.RBAC['matched']} of {F.RBAC['total']} operation and role combinations matched, and every missing or invalid token was refused.",
              f"**The cost of encryption is small next to the transfer.** Encrypting 25 MiB takes {F.ms(F.AES['26214400']['encrypt']['median'])} ms and a 10 MiB upload with all cryptography took {F.ms(F.E2E['10485760']['encrypted_up']['median'])} ms against {F.ms(F.E2E['10485760']['plain_up']['median'])} ms without.",
              f"**Tampering with a file is always noticed:** {T['ciphertext_bitflip']['detected']:,} of {T['ciphertext_bitflip']['trials']:,} bit flips were rejected, and a wrong key fails to decrypt.",
              "**Accidental or crude edits of the log are noticed:** eight of nine manipulation classes were detected in every trial, and the screen shows the verification result in one click.",
              "**Sharing needs no secret to travel.** The share dialog re-wraps the file key for the recipient in the browser; the server sees only a 256-byte value, and revocation takes effect on the next request (HTTP 403 in the measurement).")]


def _failure():
    A = F.API
    rows = [["Audit tail truncation is not detected", "0 of 199 trials; the remaining prefix is a valid chain and the log length is not recorded elsewhere"],
            ["A full rewrite with recomputed hashes is not detected", "The chain has no secret key and no external anchor; anyone able to write the table can re-chain it"],
            ["Concurrent writers fork the chain", f"{F.CONC['4_workers']['requests']} concurrent failed logins: chain invalid, first broken entry {F.CONC['4_workers']['failure_at']} of {F.CONC['4_workers']['checked']} (no lock around read-last-hash and insert)"],
            ["The server cannot tell ciphertext from plaintext", "The unencrypted baseline of Section 8.4 was accepted by the same upload endpoint; encryption is a property of the trusted client, not enforced by the server"],
            ["Login timing reveals whether an account exists", f"Unknown e-mail {F.ms(F.M['audit_write_ms']['median'])} ms against {F.ms(A['login_fail_ms']['median'])} ms for a wrong password; the register endpoint also names an existing e-mail"],
            ["Any signed-in user sees the global audit list", "`GET /api/audit` returns the latest events of all users (e-mail addresses, file numbers, IP addresses); only the per-file history is owner-only"],
            ["Revocation cannot recall what was already downloaded", "The server deletes the recipient's wrapped key and refuses further downloads (403), but a file key or ciphertext saved earlier stays usable; there is no re-keying"],
            ["Editor updates reuse the file key", "The new ciphertext uses a fresh random 96-bit IV under the same key; the server cannot verify the pairing, so the client's digest check is the only guard"],
            ["Deployment-level exposures", "The server delivers the JavaScript that performs the cryptography; the file name, size, type, owner and time are stored in clear; the token is kept in `sessionStorage`; the login throttle (20 attempts per 300 s) is in memory; there is no second factor; losing the password loses the data"]]
    return [H2("8.11 Failure cases and defects"),
            P("The experiments exposed the weaknesses in the table below. They are stated as measured; none has been fixed, and Chapter 10 ranks them."),
            TAB("Weaknesses found, with the evidence.", ["Finding", "Evidence"], rows, widths=[2.2, 4.3], align=["l", "l"], size=9),
            P("The first three concern the audit trail and weaken the claim of tamper evidence to *evidence of non-malicious or partial modification*. The fourth and the fifth follow from the design: a web server cannot inspect what it stores and still be blind to it. "
              "The remaining items are limits that every comparable browser-encryption service shares, the best-known being that the server supplies the code that does the encryption, which is the starting point of the attacks on MEGA " + N("mega") + ".")]


# ----------------------------------------------------------------------------------------------- 8.12
def _base():
    ba = __import__("scripts.docs.lit", fromlist=["BASE_ANALYSIS"]).BASE_ANALYSIS
    n = ba["numbers"]
    e10 = F.E2E["10485760"]
    rows = [["System", "Health records for a semi-trusted cloud; attribute-based encryption with a ledger", "Cloud file store with client-side encryption and RBAC", "General secure file store, local web application"],
            ["Cryptography", "ECC dual-attribute encryption (160-bit key), ClinicalBERT attribute extraction, multiple key-generation centres", "AES-256-GCM, RSA-2048 OAEP, PBKDF2 (310,000 iterations), TOTP, ECDSA-signed log entries", "AES-256-GCM, RSA-2048 OAEP, PBKDF2 (120,000 iterations), bcrypt, no second factor"],
            ["Access control", "Policy over user and data attributes, checked by decryption", "Owner, editor, viewer", "Owner, editor, viewer per file, enforced on the server"],
            ["Audit / integrity", "Hyperledger Fabric ledger of public keys and policies; hash of the record", "SHA-256 chained log with signatures", "SHA-256 chain in the database; digest check on download"],
            ["Evaluation", "Calculated from primitive timings and operation counts; no dataset or end-to-end run reported", "50 users, 3 roles; 900 access attempts; 50 simulated tamper events", "Measured on one machine: 36 access cells, about 1,800 audit-manipulation trials, 2,000 bit flips"],
            ["Hardware", "HPE server (E5-2620 v3) and Raspberry Pi 3 B+", "not stated", "Core i5-12500, 15.7 GB, shared with other jobs"],
            ["Reported cost", f"About {n['proposed_us']['total_x5']:,} microseconds in total at five attributes on the Raspberry Pi (other schemes {min(n['compared_totals_us']):,} to {max(n['compared_totals_us']):,})", "+320 ms for a 10 MB upload", f"Encrypted 10 MiB upload {F.ms(e10['encrypted_up']['median'])} ms against {F.ms(e10['plain_up']['median'])} ms plain (median)"],
            ["Reported correctness", "Security argued by proof sketches", "98.6 per cent access-control accuracy (13 of 900 attempts misclassified); 100 per cent of 50 tamper events detected; no exposure in 30 days", "36 of 36 cells; 8 of 9 audit manipulation classes detected, tail truncation and a full re-chain not detected"]]
    return [H2("8.12 Comparison with the base paper and the closest architecture"),
            P(f"The declared base paper {N('base')} designs a scheme for electronic health records. Its evaluation is a *calculation*: the cost of each phase is obtained from operation counts and the measured time of single primitives (OpenSSL) on a server and a Raspberry Pi, in microseconds, and no dataset or end-to-end run is reported. "
              f"CipherVault measures real requests in milliseconds on a different machine, with a different scheme (AES-256-GCM with per-user key wrapping against attribute-based encryption), so **the two sets of numbers must not be ranked against each other** and no ranking is claimed. "
              f"The paper that is closest in architecture, {N('ijedr')}, reports measurements, but states neither its hardware nor its test protocol, so its figures cannot be reproduced or compared like for like either. The table below sets side by side what each reports."),
            TAB("Base paper, closest architecture and CipherVault (what each reports; not a ranking).", ["Aspect", "Base paper [1]", "IJEDR paper [2]", "CipherVault"], rows,
                widths=[0.9, 1.9, 1.8, 1.9], align=["l", "l", "l", "l"], size=8.5),
            P("What is adopted from the base paper is its trust model (the store is untrusted and sees only ciphertext), the hash comparison after decryption, and the idea of treating revocation and the audit trail as part of the design; "
              "attribute-based encryption, ClinicalBERT, the key-generation centres and the blockchain are not adopted, because they would add cost and administration for a three-role file store. "
              "Against the closest architecture CipherVault lacks multi-factor authentication, chunked encryption, a stronger key-derivation setting and signed log entries, and says so; it adds a measured failure analysis of its own audit log, which that paper does not give. "
              f"Its single quantitative claim that can be set beside a CipherVault number is the extra time for a 10 MB upload, +320 ms against a measured difference of medians of about {e10['encrypted_up']['median'] - e10['plain_up']['median']:.0f} ms; the setups differ (client, network, whether the server is remote), so this is context, not a result.")]


# ----------------------------------------------------------------------------------------------- 8.13
def _analysis():
    return [H2("8.13 Analysis and limits of these results"),
            B("**Cryptography is not the bottleneck.** Browser encryption of a file the server accepts costs tens of milliseconds at most; login (bcrypt) and PBKDF2 are the slowest operations a user sees, by design.",
              "**Correctness of access rules is the strongest result,** because it is exhaustive over the implemented operations; its weakness is that it covers one file and the rules as implemented, not rules that are missing (for example, no admin role exists and the global audit list is open to all users).",
              "**The audit trail is weaker than its interface suggests.** The screen says *Audit chain valid*; the measurements show that this statement is true for consistent logs and cannot be trusted against truncation, a re-chaining attacker or a concurrent burst.",
              "**Several guarantees depend on the client.** Encryption, the digest check and key wrapping all happen in code delivered by the server; the server cannot enforce them."),
            P("The results are limited in the following ways. All timings come from one shared machine over loopback, from headless Chrome only, with small repetition counts at large sizes (four runs at 25 MiB, three for the API). "
              "The audit-manipulation tests ran on a copy of one log of about 460 entries, not on the running server. "
              "The demonstration files are fictional and tiny (111 to 165 bytes), so large-file behaviour rests on the synthetic measurements only. "
              "No load test, independent penetration test or usability study was carried out, and the figures of the closest architecture could not be reproduced.")]


# ----------------------------------------------------------------------------------------------- 8.14
def _objectives():
    T = F.TAMPER
    rows = [["1. Registration and authentication with hashed credentials and JWT sessions", "Achieved, with gaps",
             f"bcrypt cost {F.BCRYPT_COST}, HS256 tokens valid for {F.JWT_MINUTES} min; {F.PYTEST_PASSED} of {F.PYTEST_TOTAL} tests pass; forged, expired and `none` tokens refused. Gaps: login timing reveals account existence, in-memory throttle, no second factor"],
            ["2. Encrypt every upload with AES-256-GCM before it reaches storage", "Achieved (client side)",
             "Browser encryption; stored objects are ciphertext (16 B longer). The server cannot verify that a client really encrypted: a plain payload was accepted"],
            ["3. Role-based access with ownership checks", "Achieved", f"{F.RBAC['matched']} of {F.RBAC['total']} cells as expected; unauthenticated and forged requests refused; revoke takes effect at once"],
            ["4. Verify integrity on download", "Achieved", f"AES-GCM tag plus SHA-256 comparison; {T['ciphertext_bitflip']['detected']:,} of {T['ciphertext_bitflip']['trials']:,} bit flips rejected (Python primitive)"],
            ["5. Structured audit log of uploads, downloads, deletes and denials", "Achieved, with defects", "All four kinds are logged and chained; tail truncation and re-chaining undetected; concurrent writers fork the chain; global list open to every user"],
            ["6. Evaluate encryption overhead, access-control correctness and integrity", "Achieved, within limits", "Sections 8.3 to 8.7; one shared machine, Chrome only, small repetition counts, no load test"]]
    return [H2("8.14 Objectives versus outcomes"),
            TAB("The six project objectives against what was measured.", ["Objective", "Status", "Evidence"], rows, widths=[2.2, 1.0, 3.3], align=["l", "l", "l"], size=9)]


def _summary():
    A = F.AES["26214400"]
    return [H2("8.15 Summary of findings"),
            B(f"AES-256-GCM encryption of 25 MiB takes {F.ms(A['encrypt']['median'])} ms in the browser, adds 16 bytes, and an encrypted 10 MiB upload took {F.ms(F.E2E['10485760']['encrypted_up']['median'])} ms against {F.ms(F.E2E['10485760']['plain_up']['median'])} ms unencrypted (medians, shared machine).",
              f"All {F.RBAC['total']} role and operation combinations gave the expected answer; invalid tokens were always refused.",
              "All 2,000 ciphertext bit flips and eight of nine audit manipulation classes were detected.",
              f"Tail truncation, a full re-chain and concurrent writers defeat the audit chain (0 of 199; not detected; first broken link at {F.CONC['4_workers']['failure_at']}).",
              "Login timing, the open global audit list, non-recallable revocation and the trust placed in the delivered JavaScript are documented limits.",
              f"{F.PYTEST_PASSED} of {F.PYTEST_TOTAL} unit tests, 17 of 17 API checks and 18 of 18 browser steps passed; load, other browsers, PostgreSQL and Docker were not tested.")]


def blocks():
    b = [H1("CHAPTER 8: RESULTS AND OUTPUT SCREENS")]
    b += (_setup() + _screens() + _browser_crypto() + _e2e() + _api() + _rbac() + _integrity() + _tests() + _samples()
          + _success() + _failure() + _base() + _analysis() + _objectives() + _summary())
    return b
