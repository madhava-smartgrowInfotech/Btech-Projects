"""Chapter 7: System Testing for CipherVault.

Numbers come from facts.py (docs/metrics/metrics.json, tests.json); the step lists of the end-to-end check and of the browser walk
are read from docs/metrics/smoke_output.txt (output of scripts/smoke_test.py), so nothing in the tables is typed from memory.
"""

import ast
import os
import re

from . import facts as F
from .blocks import B, FIG, H1, H2, P, TAB
from .refs import N as cite

OPS = ["metadata", "download", "update", "list_permissions", "share", "change_role", "revoke", "file_audit", "delete"]
OP_LABEL = {"metadata": "Read metadata", "download": "Download ciphertext", "update": "Replace content", "list_permissions": "List permissions",
            "share": "Share", "change_role": "Change role", "revoke": "Revoke access", "file_audit": "File history", "delete": "Delete file"}
TAMPER_LABEL = {"edit_details": "Change the details text of an entry", "edit_action": "Change the action name", "edit_success": "Flip the success flag",
                "edit_user": "Change the user id", "edit_hash": "Overwrite the stored hash", "delete_entry_middle": "Delete an entry from the middle",
                "swap_adjacent": "Swap two adjacent entries", "insert_forged_entry": "Insert a forged entry", "truncate_tail": "Remove the last entries (truncate the tail)"}


def _smoke():
    """Parse docs/metrics/smoke_output.txt: (api_lines, ui_steps, stored_plain, audit_actions, chain_n)."""
    path = os.path.join(F.METRICS_DIR, "smoke_output.txt")
    api, ui, stored, actions, chain = [], [], None, [], None
    if not os.path.exists(path):
        return api, ui, stored, actions, chain
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        m = re.match(r"\[PASS\] (.+) \((\d+(?:\.\d+)?)s\)$", line)
        if m:
            ui.append((m.group(1), m.group(2)))
            continue
        m = re.match(r"\[PASS\] (.+)$", line)
        if m:
            api.append(m.group(1))
            s = re.search(r"stored=(\d+)B plaintext=(\d+)B", line)
            if s:
                stored = (int(s.group(1)), int(s.group(2)))
            a = re.search(r"audit entries generated (\[.*\])", line)
            if a:
                actions = ast.literal_eval(a.group(1))
            c = re.search(r"audit chain valid (\d+) entries", line)
            if c:
                chain = int(c.group(1))
    return api, ui, stored, actions, chain


API_STEPS, UI_STEPS, STORED, ACTIONS, CHAIN_N = _smoke()


def _e2e_check_rows():
    """The 17 end-to-end checks with a plain description of what each proves."""
    names = {
        "register + login 3 users": "Three accounts (owner, editor, viewer) register with real RSA-2048 keys and sign in",
        "encrypted upload": "A 16,000-byte file is encrypted in the client and accepted by the server",
        "stored ciphertext object exists": "The ciphertext object exists in the storage folder",
        "server stores ciphertext, not plaintext": "The stored object is the ciphertext (plaintext size plus 16 bytes) and does not contain the plaintext",
        "file metadata in database": "The files row holds name, sizes, IV, wrapped key and digest",
        "owner download": "The owner downloads the ciphertext",
        "decrypt + SHA-256 verify": "The owner unwraps the key, decrypts and the digest matches",
        "share with editor": "Sharing with the editor stores a wrapped key",
        "editor download allowed": "The editor downloads",
        "editor delete denied (owner-only)": "The editor's delete is refused (HTTP 403)",
        "share with viewer": "Sharing with the viewer stores a wrapped key",
        "viewer download allowed": "The viewer downloads",
        "stranger access rejected": "A signed-in user without a role is refused",
        "owner delete": "The owner deletes the file",
        "deleted file rejected": "A later access to the deleted file is refused",
        "audit entries generated": "The audit log holds the expected event types",
        "audit chain valid": "The server verifies the whole hash chain",
    }
    rows = []
    for i, line in enumerate(API_STEPS, 1):
        key = next((k for k in names if line.startswith(k)), None)
        detail = names.get(key, line)
        if key == "server stores ciphertext, not plaintext" and STORED:
            detail += f" ({STORED[0]:,} bytes stored for {STORED[1]:,} bytes of plaintext)"
        if key == "audit entries generated" and ACTIONS:
            detail += f" ({len(ACTIONS)} distinct types)"
        if key == "audit chain valid" and CHAIN_N:
            detail += f" ({CHAIN_N} entries)"
        rows.append([str(i), detail, "Pass"])
    return rows


def _ui_rows():
    return [[str(i), name, "Pass", f"{t}"] for i, (name, t) in enumerate(UI_STEPS, 1)]


def _rbac_rows():
    cells = {(c["principal"], c["operation"]): c for c in F.RBAC["cells"]}
    rows = []
    for op in OPS:
        row = [OP_LABEL[op]]
        for p in ("owner", "editor", "viewer", "stranger"):
            c = cells[(p, op)]
            row.append(f"{c['status']} ({'allow' if c['expected_allowed'] else 'deny'}){'' if c['match'] else ' MISMATCH'}")
        rows.append(row)
    return rows


def _tamper_rows():
    rows = []
    for k, lab in TAMPER_LABEL.items():
        t = F.TAMPER["audit_tamper"][k]
        rows.append([lab, str(t["trials"]), str(t["detected"]), F.pct(t["detected"] / t["trials"], 0)])
    return rows


def _scale_rows():
    return [[str(n), str(v["checked"]), F.ms(v["verify_ms_median"])] for n, v in sorted(F.SCALE.items(), key=lambda kv: int(kv[0]))]


def _lat_rows():
    api = F.API
    aw = F.M["audit_write_ms"]

    def r(lab, d):
        return [lab, str(d["n"]), F.ms(d["median"]), F.ms(d["p95"]), F.ms(d["max"])]

    return [r("GET /api/health", api["health_ms"]), r("GET /api/auth/me (JWT check, one query)", api["me_ms"]),
            r("POST /api/auth/login (correct password, bcrypt cost 12)", api["login_ms"]), r("POST /api/auth/login (wrong password)", api["login_fail_ms"]),
            r("GET /api/files (65 owned files)", api["list_files_ms"]), r("Audit write (one failed login of an unknown user)", aw)]


def _size_label(k):
    n = int(k)
    return {1024: "1 KiB", 65536: "64 KiB", 1048576: "1 MiB", 10485760: "10 MiB", 26212352: "about 25 MiB"}.get(n, str(n))


def _transfer_rows():
    rows = []
    for k in F.API["upload_ms"]:
        u, d = F.API["upload_ms"][k], F.API["download_ms"][k]
        rows.append([_size_label(k), str(u["n"]), f"{F.ms(u['median'])} ({F.ms(u['p95'])})", f"{F.ms(d['median'])} ({F.ms(d['p95'])})"])
    return rows


def _e2e_rows():
    rows = []
    for k, e in F.E2E.items():
        eu, pu, ed, pd = (e[x]["median"] for x in ("encrypted_up", "plain_up", "encrypted_down", "plain_down"))
        rows.append([_size_label(k), f"{F.ms(eu)} / {F.ms(pu)}", f"{(eu - pu) / pu * 100:+.0f}%", f"{F.ms(ed)} / {F.ms(pd)}", f"{(ed - pd) / pd * 100:+.0f}%"])
    return rows


def blocks():
    b = _blocks()
    return _trim_report(b) if F.REPORT else b


_DROP_TAB = ("Access-control matrix", "Tamper tests on", "Latency of repeated API calls", "Upload and download of ciphertext",
             "The whole pipeline in the browser", "Time to verify the whole audit chain")


def _trim_report(bl):
    """Report variant: the measured tables of 7.5 and 7.7 are printed once, in Chapter 8; here only the test design stays."""
    out = []
    for x in bl:
        if x[0] == "tab" and x[1].startswith(_DROP_TAB):
            continue
        if x[0] == "fig" and x[2].startswith("Automated checks that were run"):
            continue
        if x[0] == "p":
            x = ("p", x[1].replace("The observed HTTP status of each cell follows.", "The observed status of every cell is tabulated in Section 8.6.")
                 .replace("this section lists the numbers that belong to the test record.", "the measured tables are printed once, in Sections 8.3 to 8.7."))
        out.append(x)
    return out


def _blocks():
    api, rb, tp = F.API, F.RBAC, F.TAMPER
    det = [(t["trials"], t["detected"]) for k, t in tp["audit_tamper"].items() if k != "truncate_tail"]
    det_trials, det_ok = sum(a for a, _ in det), sum(b for _, b in det)
    trunc = tp["audit_tamper"]["truncate_tail"]
    first_bad, checked = F.CONC["4_workers"]["failure_at"], F.CONC["4_workers"]["checked"]
    b = [H1("CHAPTER 7: SYSTEM TESTING")]

    # ------------------------------------------------------------------ 7.1
    b += [H2("7.1 Testing strategy"),
          P("CipherVault is software whose correctness is largely a matter of exact, checkable rules: a ciphertext must authenticate or be rejected, a role must allow or refuse each operation, a hash chain must verify or fail, and a request must be answered with the right status code. "
            "The strategy follows from that. Rules with exact answers are tested by automated tests that need no judgement; rules that depend on the browser's cryptography or on the whole system are tested by scripts that drive the real application; and the cost and the failure modes of the design are measured rather than asserted (Chapter 8). "
            "Three principles were applied. The tests run against the real code and a real database (SQLite in a temporary directory) and never replace the access-control or audit logic. Every security claim in this report has at least one test or measurement that could have contradicted it. And a result that contradicts the design is reported as such: the audit-chain tests were written to find weaknesses, and they found three."),
          TAB("Test levels, tools and results.",
              ["Level", "Tool and scope", "Count", "Result"],
              [["Unit and API", "pytest with the FastAPI TestClient: tests/test_auth.py, test_crypto.py, test_files.py, test_rbac.py, test_audit.py on a scratch database", f"{F.PYTEST_TOTAL} tests", f"{F.PYTEST_PASSED} passed in {F.PYTEST_SECONDS:.0f} s"],
               ["Integration (live server)", f"scripts/e2e_check.py against a running server on port {F.API_PORT}: register, encrypt, upload, share, download, decrypt, delete, audit, with real RSA and AES in Python", f"{F.E2E_TOTAL} checks", f"{F.E2E_PASSED} passed"],
               ["Library checks", "scripts/evaluate.py: primitive round trips, access refusals, forged token, tamper detection", f"{F.EVAL_TOTAL} checks", f"{F.EVAL_PASSED} passed"],
               ["Functional (real browser)", f"scripts/smoke_test.py: Playwright drives Chrome through the interface against the API on {F.API_PORT} and Vite on {F.WEB_PORT}, using the real Web Crypto code", f"{F.UI_TOTAL} steps", f"{F.UI_PASSED} passed"],
               ["Security and tamper study", "scripts/measure_metrics.py: access matrix on the live API, token forgery, 2,000 ciphertext bit flips, nine audit-tamper classes, concurrent writers", f"{rb['total']} matrix cells, 9 tamper classes", f"{rb['matched']} of {rb['total']} cells matched; 8 of 9 tamper classes detected"],
               ["Performance", "scripts/measure_metrics.py: browser primitive timings, end-to-end pipeline, API latency, chain verification", "see Section 7.7", "Measured"]],
              widths=[1.3, 3.1, 1.1, 1.0], align=["l", "l", "l", "l"], size=9),
          P(f"All tests ran on one machine: {F.ENV['cpu']}, {F.ENV['ram_gb']} GB RAM, Windows 11, Python {F.ENV['python']}, Chrome {F.BR['browser_version']}, loopback address {F.ENV['loopback']}. "
            "Other jobs were using the machine during the measurements, so timing figures are indicative; pass and fail results do not depend on timing. "
            f"The measurements and the test runs are dated {F.ENV['date']}. The measurement server used a scratch database and storage folder, a throw-away JWT secret and a raised login-throttle limit so that the 25 and more logins of a timing run were not refused; the shipped throttle was therefore not exercised by any run."),
          *([FIG(F.fig("f09_test_summary.png"), "Automated checks that were run and passed.", 4.8)] if os.path.exists(F.fig("f09_test_summary.png")) else [])]

    # ------------------------------------------------------------------ 7.2
    b += [H2("7.2 Unit testing"),
          P(f"The pytest suite holds **{F.PYTEST_TOTAL} tests and all of them passed in {F.PYTEST_SECONDS:.0f} seconds**. They sit in five files, each with one theme, and use a fixture that builds a clean SQLite database and ciphertext folder per run, registers uniquely named users and logs them in, so the tests are independent of each other. "
            "Two limits of the suite should be read before its results: the API tests upload a fixed 32-byte block of dummy bytes and placeholder keys, because the server cannot tell ciphertext from any other bytes, so they test the rules of the server and not the cryptography; "
            "and the cryptographic tests run the Python `cryptography` library, the same algorithms as the browser but not the JavaScript code of the application."),
          TAB("Automated tests by file.",
              ["File (tests)", "What each test asserts"],
              [["test_auth.py (6)", "Register and log in returns a token; duplicate registration is refused (HTTP 400); a wrong password is refused (401); protected routes refuse a request without a token; a malformed token is refused (401); the password and its hash are never returned by `/api/auth/me`"],
               ["test_crypto.py (5)", "AES-256-GCM round trip; two keys give different ciphertext for the same plaintext and IV; a corrupted ciphertext fails authentication; SHA-256 matches for equal data and differs for altered data; RSA-2048-OAEP wrap and unwrap of a 256-bit key gives a 256-byte value and the original key"],
               ["test_files.py (3)", "Upload, list, download (headers `X-CipherVault-SHA256` and `X-CipherVault-IV` present) and delete, after which the file is not found (404); a malformed upload (invalid base64 IV, invalid digest) is refused (400); a file shared as viewer appears in the recipient's shared list with the role viewer"],
               ["test_rbac.py (5)", "Owner reads and downloads; viewer reads and downloads but cannot delete (403) or change a role (403); editor replaces content but cannot delete (403); a user without a role is refused on metadata and download (403) and the refusal appears in the audit log as `unauthorized_access`; the owner changes a role and revokes, after which the former recipient is refused"],
               ["test_audit.py (2)", "An upload creates audit entries with a hash and a previous hash, and `/api/audit/verify` reports a valid chain; editing the details of the first entry makes `verify_chain` fail and name that entry"]],
              widths=[1.3, 5.2], align=["l", "l"], size=9.5),
          P("One test deserves a note on its name. `test_expired_or_invalid_jwt_rejected` sends a string that is not a token at all; it does not construct an expired token. Token expiry, a token signed with a different secret and an unsigned token (`alg=none`) were therefore checked separately, by the security run of Section 7.5, where each is refused with HTTP 401. "
            "Likewise `test_protected_route_without_jwt` accepts either 401 or 403, while the live run shows 401 in all five cases.")]

    # ------------------------------------------------------------------ 7.3
    b += [H2("7.3 Integration testing"),
          P(f"`scripts/e2e_check.py` follows the whole workflow against a running server, with the client steps done in Python using the same algorithms as the browser (AES-256-GCM, RSA-2048-OAEP with SHA-256, SHA-256). It also opens the database file and the storage folder directly, which no browser test can do, to confirm what is at rest. **All {F.E2E_TOTAL} checks passed.**"),
          TAB("The end-to-end checks.",
              ["No.", "What is checked", "Result"], _e2e_check_rows(),
              widths=[0.5, 5.2, 0.8], align=["c", "l", "c"], size=9.5),
          P((f"The fourth check carries the confidentiality claim: the object on disk is {STORED[0]:,} bytes for a {STORED[1]:,}-byte file, which is the plaintext size plus the 16-byte tag, and it does not contain the plaintext. " if STORED else "")
            + (f"The audit step shows that a single workflow of this kind writes events of {len(ACTIONS)} different types ({', '.join(ACTIONS)})." if ACTIONS else "")),
          P(f"`scripts/evaluate.py` adds {F.EVAL_TOTAL} checks that run in one process: the AES-GCM round trip at 1 KiB, 64 KiB and 1 MiB, the SHA-256 check, the RSA wrap and unwrap, a duplicate registration, a wrong password, a protected route without a token, a forged token, an encrypted upload, the ciphertext-not-plaintext check, an allowed and a refused download, decrypt and verify, a tampered ciphertext, a valid audit chain of 14 entries and a detected edit of the chain. "
            "All passed. This script also prints timings labelled `browser_*`; they were taken with the Python library and not in a browser, so this report uses the measurements of Section 7.7 instead.")]

    # ------------------------------------------------------------------ 7.4
    b += [H2("7.4 Functional testing"),
          P(f"`scripts/smoke_test.py` is the functional test of the interface. Its second part starts headless Chrome at 1440 by 900 pixels, registers a new user in the real registration form, and then performs the actions of a user in order, checking the visible result of each step, and recording page errors and console errors. "
            f"The first part repeats the API workflow of Section 7.3. **All {F.UI_TOTAL} browser steps passed**, with no page error and no unexpected console error. The times in the last column are the wall-clock time of each step including the waits that the script inserts; they are not response times."),
          TAB("The browser walk (scripts/smoke_test.py, part 2).",
              ["No.", "Step", "Result", "Time (s)"], _ui_rows(),
              widths=[0.5, 4.5, 0.7, 0.8], align=["c", "l", "c", "c"], size=9.5),
          P("Several of these steps exercise code that no other test touches: the key generation and sealing at registration, the encryption and the SHA-256 in `vaultCrypto.js` (steps 4, 5 and 7), the decryption failure path when the password is wrong (step 12 and 16) and the lock on reload (step 14). "
            "The final step of the walk, no horizontal overflow at 360 and 768 pixels, is the only responsive-layout check that was automated. The walk uses fictional accounts and files from the demonstration mode as well as one registered account.")]

    # ------------------------------------------------------------------ 7.5
    b += [H2("7.5 Security testing"),
          P("The security tests were written as attacks on the claims of Chapter 6: that access is decided by role on the server, that a token cannot be forged, that stored ciphertext cannot be altered unnoticed, and that the audit trail is tamper-evident. They ran on the live API with a scratch database; none is a substitute for a penetration test."),
          P(f"**Access control.** One file and four principals (the owner, an editor and a viewer, each given their role by the owner, and a stranger who holds none) were tested against the nine operations that touch a file, giving {rb['total']} cells. The expected decision was written down from the permission rules before the run. "
            f"**{rb['matched']} of {rb['total']} cells matched ({F.pct(rb['accuracy'])}).** The observed HTTP status of each cell follows."),
          TAB("Access-control matrix: observed HTTP status (expected decision in brackets).",
              ["Operation", "Owner", "Editor", "Viewer", "Stranger"], _rbac_rows(),
              widths=[1.7, 1.2, 1.2, 1.2, 1.2], align=["l", "c", "c", "c", "c"], size=9.5),
          P("The matrix is exhaustive over the implemented operations on one file; it is not a user study and not a statistical accuracy. The access-control accuracy of 98.6 % reported by Sowmiya et al. " + cite("ijedr") + " comes from 900 access attempts in an evaluation with 50 users, and is a different experiment; the two figures are not comparable. "
            "Two features of the matrix are worth noting. A viewer and an editor may list the permissions of a file (200), which shows them the e-mail addresses of the other people with access, and they are refused only its history. And the stranger's refusals are written to the audit log, which is why the log shows `unauthorized_access` events."),
          P(f"**Authentication.** A request with no token was refused with HTTP 401 on all five protected routes tried ({', '.join(str(x) for x in rb['unauthenticated_statuses'])}). A malformed token ({rb['forged_token_status']}), a correctly formed token that had expired a minute earlier ({rb['expired_token_status']}), a token signed with a different secret ({rb['wrong_secret_token_status']}) and an unsigned token with the header `alg=none` ({rb['alg_none_token_status']}) were all refused. "
            "Brute-force login throttling (HTTP 429) was not tested, because the measurement server raised its limit; the code path is short, but it has no test."),
          TAB("Tamper tests on stored data and on the audit log.",
              ["Attack", "Trials", "Detected", "Rate"],
              [["Flip one random bit of a stored ciphertext (4 KiB object)", str(tp["ciphertext_bitflip"]["trials"]), str(tp["ciphertext_bitflip"]["detected"]), F.pct(tp["ciphertext_bitflip"]["detected"] / tp["ciphertext_bitflip"]["trials"], 0)],
               ["Decrypt with a different key", "1", "1" if tp["wrong_key_rejected"] else "0", "100%" if tp["wrong_key_rejected"] else "0%"]] + _tamper_rows(),
              widths=[3.9, 0.8, 0.9, 0.9], align=["l", "c", "c", "c"], size=9.5),
          P(f"The ciphertext tests used the same AES-256-GCM primitive in Python; in the application the check is made in the recipient's browser, so the server itself never detects an altered stored object, which is by design. "
            f"The audit tests copied the {tp['audit_entries_available']} entries of the measurement database, applied one change at a time at random positions and ran the same recomputation as `verify_chain`; the untouched chain verified. "
            f"**Eight of the nine classes were detected in every trial ({det_ok} of {det_trials} trials).** The ninth was not: **removing the last entries was detected in {trunc['detected']} of {trunc['trials']} trials**, because the verifier checks that the entries present are consistent with each other and has nowhere to learn how many there should be. "
            f"A stronger attacker with write access who edits an entry **and recomputes the hashes of all later entries** is also not detected ({'not detected' if not tp['audit_rechain_attack_detected'] else 'detected'}): the chain has no secret key and no external anchor. "
            "These results are the honest bound of the claim 'tamper-evident': the chain detects accidental damage and naive edits, not a determined insider with database access. The IJEDR paper reports 100 % detection of 50 simulated tamper events " + cite("ijedr") + "; the tamper methods are not listed, so the figures are not comparable."),
          P(f"**Concurrency defect.** The last test asked whether the chain stays valid when several requests write at once. Before the test the chain was valid. After {F.CONC['4_workers']['requests']} failed logins sent by 4 concurrent workers in {F.CONC['4_workers']['seconds']} seconds (all answered 401 as expected), "
            f"**the chain was invalid, with the first broken link at entry {first_bad} of {checked}.** The cause is in `record_event`: it reads the last hash and commits a new entry in two steps with no lock, so two requests can read the same last hash and both write an entry that claims it as predecessor. "
            "The audit entries themselves are all present, but the chain is no longer a single line, and the verifier, correctly, reports a failure. The defect was documented and not fixed in the product during this work; a lock around the read and write, or a unique constraint on the previous hash with a retry, would remove it (Chapter 10).")]

    # ------------------------------------------------------------------ 7.6
    b += [H2("7.6 Validation and edge cases"),
          P("The table lists the cases exercised, with the source of each result. Cases marked *code only* are read from the code and were not run."),
          TAB("Edge cases, expected behaviour and observed result.",
              ["Case", "Expected behaviour", "Observed (source)"],
              [["Ciphertext larger than 25 MB", "Refused with HTTP 413 before anything is stored", f"HTTP {api['upload_limit_check']['over_25MB_status']} for a 25 MB object plus 5,000 bytes (measurement run)"],
               ["Invalid IV (not base64) and invalid digest", "HTTP 400", "HTTP 400 (test_files.py)"],
               ["Duplicate e-mail at registration", "HTTP 400, a failed `register` event", "Passed (test_auth.py)"],
               ["Wrong password", "HTTP 401, a `login_failure` event", "Passed (test_auth.py, e2e)"],
               ["Download after revocation", "HTTP 403", f"HTTP {api['download_after_revoke_status']} in {F.ms(api['download_after_revoke_ms'])} ms (measurement run; test_rbac.py)"],
               ["Access to a deleted file", "HTTP 404", "Passed (test_files.py, e2e)"],
               ["Altered stored ciphertext", "Decryption fails; no file is saved", "2,000 of 2,000 bit flips detected at primitive level; the browser shows the message of `fetchAndDecrypt` (code, UI walk covers only the wrong-password case)"],
               ["Wrong password at unlock", "Error message; vault stays locked", "Passed (UI walk, step 12)"],
               ["Page reload while unlocked", "Private key is gone; the next action asks for the password", "Passed (UI walk, step 14)"],
               ["Empty file selected for upload", "Refused in the browser with a message", "*Code only* (`uploadFile`); not run"],
               ["Sharing with the owner or a user who already has access", "HTTP 400 / HTTP 409", "*Code only*; not run"],
               ["More than 20 logins in 300 seconds", "HTTP 429", "*Code only*; not run (limit raised for the measurements)"],
               ["PostgreSQL database; Docker build", "Same behaviour as SQLite", "Not run"],
               ["File just under 25 MB (26,212,352 bytes, the largest measured)", "Accepted", f"Accepted; upload {F.ms(api['upload_ms']['26212352']['median'])} ms, download {F.ms(api['download_ms']['26212352']['median'])} ms (3 runs)"]],
              widths=[2.0, 2.0, 2.5], align=["l", "l", "l"], size=9),
          P("Several of the 'code only' rows are short branches (a status code and a message); their absence from the test suite is a gap in coverage and not evidence of a fault, but it is stated so that the reported coverage is not read as complete.")]

    # ------------------------------------------------------------------ 7.7
    b += [H2("7.7 Performance testing"),
          P(f"Performance was measured in the browser (Web Crypto and the whole encrypted pipeline) and over loopback on the API, on the machine of Section 7.1 with other jobs running. Medians are reported with the 95th percentile because single runs varied by up to three times at 10 MiB. "
            "Chapter 8 discusses the results; this section lists the numbers that belong to the test record."),
          TAB("Latency of repeated API calls (milliseconds).",
              ["Call", "Runs", "Median", "95th percentile", "Maximum"], _lat_rows(),
              widths=[3.0, 0.6, 0.8, 1.2, 0.9], align=["l", "c", "c", "c", "c"], size=9.5),
          TAB("Upload and download of ciphertext through the API (median, 95th percentile in brackets, milliseconds).",
              ["Object size", "Runs", "Upload", "Download"], _transfer_rows(),
              widths=[1.6, 0.8, 2.0, 2.0], align=["l", "c", "c", "c"], size=9.5),
          TAB("The whole pipeline in the browser, encrypted against plain transfer to the same endpoint (median, milliseconds).",
              ["Size", "Upload: encrypted / plain", "Difference", "Download: decrypt and verify / plain", "Difference"], _e2e_rows(),
              widths=[1.0, 1.6, 0.9, 2.1, 0.9], align=["l", "c", "c", "c", "c"], size=9.5),
          P(f"Encryption adds little to the cost of a transfer: at 10 MiB the encrypted upload took {F.ms(F.E2E['10485760']['encrypted_up']['median'])} ms against {F.ms(F.E2E['10485760']['plain_up']['median'])} ms for the same bytes sent in plain, and the cryptography alone (AES-GCM encrypt plus the digest) accounts for part of that. "
            "The differences at 1 KiB are smaller than the run-to-run spread and should not be read as a cost. Sowmiya et al. report +320 ms for a 10 MB upload " + cite("ijedr") + "; their hardware, network and method are not stated, so that figure cannot be compared with these."),
          TAB("Time to verify the whole audit chain against its length (median, milliseconds).",
              ["Entries written for the test", "Entries checked", "Verification time"], _scale_rows(),
              widths=[2.0, 1.6, 1.6], align=["c", "c", "c"], size=9.5),
          P("Verification is linear in the number of entries, as the algorithm predicts, with scatter from the shared machine (500 entries took less time than 461). At 5,000 entries one verification takes about 0.4 s, and it reads every row each time, so a vault with a long history would need an incremental or periodic verification; the dashboard and the audit page both call the full check on demand.")]

    # ------------------------------------------------------------------ 7.8
    b += [H2("7.8 User acceptance and the browser walk-through"),
          P("**No user study was run.** Nobody outside the project team used CipherVault under observation, so there are no task times, ratings or satisfaction scores, and none is claimed. The usability objectives of the project are therefore judged only by the team's own use and by the scripted walk of Section 7.4."),
          P("What was done instead is a scripted walk of the interface that a user would follow, and a capture of every screen with real data. `scripts/capture_screens.py` signs in as the demonstration owner and visits the landing page in the dark and light themes, the sign-in and registration pages, the dashboard, the file list, the file detail page with its access list and history, the sharing dialog, the audit log, the security page, the unlock dialog, the list of files shared with the viewer, and the dashboard at a phone width of 360 pixels with its navigation drawer, saving 17 screenshots (Chapter 8 and Appendix C). "
            "The screens show real data: five encrypted files, three accounts in the three roles, and hundreds of audit entries from the test runs. The demonstration mode uses the same API and the same browser encryption as a registered account, so a screenshot is evidence of the working system and not of a mock-up."),
          P("The walk is also evidence for a point that tests cannot make: the interface says what has happened. A failed decryption or a digest mismatch is shown as an error and the file is not saved; a refusal appears in the file history as *Access denied*; the vault status in the top bar shows when the key is locked. "
            "Accessibility was not audited beyond the overflow check, the use of semantic controls and the reduced-motion setting the interface honours; no screen-reader test was made.")]

    # ------------------------------------------------------------------ 7.9
    b += [H2("7.9 Limits of the testing done"),
          B("**The server tests do not test the browser code.** The pytest suite and the end-to-end script run the cryptography in Python, and the JavaScript `vaultCrypto.js` has no unit tests of its own; it is covered by the 18 steps of the browser walk and by the primitive timings, which are real browser runs but check only a few properties.",
            "**The API tests use dummy ciphertext.** The server cannot tell it from real data, so these tests prove the rules and not the cryptography; the cryptography is proved by the round trips of Section 7.3 and 7.4.",
            "**The security study is bounded.** One file, three roles and a handful of attack classes were tested. SQL injection, malformed multipart bodies, request smuggling, cross-site scripting through file names, and timing differences (an unknown e-mail skips the bcrypt step and so answers faster than a known one, which was not measured) were not tested.",
            "**Small samples and one machine.** Between 3 and 60 repetitions per timing, one desktop with a shared CPU, Windows 11, Chrome only. Medians are stable between runs of the same script; differences of a few milliseconds are not.",
            "**Not tested at all:** more than one user at a time (load), files above 25 MB, Firefox and Safari (the guide lists Firefox as supported), the PostgreSQL path, the Docker image, a screen reader, backup and restore, and clock changes (the hash chain uses the server's clock).",
            "**Defects found and left as found.** Concurrent writers fork the audit chain; truncation and a complete re-hash of the chain are not detected; `GET /api/audit` lists the vault-wide events to every signed-in user; the test named for expired tokens does not use one; `evaluate.py` labels Python timings as browser timings."),
          P(f"In short: the rules of the server are covered by {F.PYTEST_TOTAL} passing automated tests and {F.E2E_TOTAL} end-to-end checks; the application works through the real browser in {F.UI_TOTAL} scripted steps; the access matrix matched in {rb['matched']} of {rb['total']} cells; and the tamper study found that the audit chain detects eight of nine classes of edit but has two real gaps and one concurrency defect. "
            "The results support the confidentiality and access-control claims within the stated bounds and do not support a claim of a tamper-proof log.")]
    return b
