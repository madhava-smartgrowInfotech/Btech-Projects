"""Chapter 7: System Testing. Numbers come from facts.py (experiments/**/metrics.json) and from the recorded test runs (docs/metrics/*.txt)."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, P, TAB

SIZES = ["1 KB", "10 KB", "100 KB", "1 MB", "5 MB"]


def _txt(blk):
    k = blk[0]
    if k in ("p", "eq", "h1", "h2", "h3", "code"):
        return blk[1]
    if k == "fig":
        return blk[2]
    if k == "tab":
        return blk[1]
    if k in ("b", "n"):
        return " ".join(blk[1])
    return ""


def _drop(b, *needles):
    """Report mode only: remove blocks whose text contains one of the needles (each must match something)."""
    out = list(b)
    for n in needles:
        hit = [x for x in out if n in _txt(x)]
        assert hit, f"ch7 trim needle not found: {n}"
        out = [x for x in out if n not in _txt(x)]
    return out


def _ms(x):
    return f"{x:.3f}" if x < 10 else f"{x:.1f}"


def crypto_rows():
    rows = []
    for s in SIZES:
        rows.append([s, _ms(F.crypto_row("sc", s, "encrypt")), _ms(F.crypto_row("sc", s, "decrypt")),
                     f"{_ms(F.crypto_row('aes', s, 'encrypt'))} / {_ms(F.crypto_row('aes', s, 'decrypt'))}",
                     f"{_ms(F.crypto_row('rsa2048', s, 'encrypt'))} / {_ms(F.crypto_row('rsa2048', s, 'decrypt'))}",
                     f"{_ms(F.crypto_row('rsa3072', s, 'encrypt'))} / {_ms(F.crypto_row('rsa3072', s, 'decrypt'))}"])
    return rows


def tamper_rows():
    T = F.CRY["tamper_tests"]
    out = []
    expect = {"untouched message accepted": "accepted", "ciphertext bit flipped": "rejected", "tag bit flipped": "rejected", "nonce bit flipped": "rejected",
              "ciphertext truncated by one byte": "rejected", "decrypted with another party's key": "rejected"}
    for k, v in T.items():
        out.append([k.capitalize(), expect[k], f"{v['as_expected']:,} of {v['trials']:,}", "Pass" if v["as_expected"] == v["trials"] else "FAIL"])
    return out


def api_rows():
    A = F.API
    names = [("health", "GET /api/health"), ("score_single", "POST /api/ids/score (one flow)"), ("encrypt_1kb_text", "POST /api/crypto/encrypt (1 KB text)"),
             ("decrypt_1kb_text", "POST /api/crypto/decrypt (1 KB text)"), ("score_batch_120_rows", "POST /api/ids/score-batch (120 rows)"),
             ("encrypt_file_1mb", "POST /api/crypto/encrypt-file (1 MB)"), ("protected_transfer_via_api_1kb", "Score + encrypt + decrypt, three calls (1 KB)")]
    return [[n, f"{A[k]['median_ms']:.2f}", f"{A[k]['p95_ms']:.2f}", f"{A[k]['n']}"] for k, n in names]


def blocks():
    ip, ap, O = F.IP, F.API, F.OFF
    share = ip["share_of_transfer_median"]
    rep = F.REPORT
    b = [H1("CHAPTER 7: SYSTEM TESTING")]

    # ------------------------------------------------------------------ 7.1
    b += [H2("7.1 Testing strategy"),
          P("The project had no separate test phase in its first delivery: it shipped with one end-to-end smoke script and a screenshot walk. The documentation run added an automated test suite and a set of measurement scripts, and this chapter reports what they show. "
            "The strategy follows the structure of the product. The cryptography is a small, deterministic component with a clear specification, so it is tested exhaustively at unit level and then attacked with systematic tampering. "
            "The intrusion detector is a statistical component, so it is tested in two different ways: its *software* behaviour (loading, shapes, probabilities, unseen categories) by unit tests, and its *predictive quality* by the multi-seed experiments of Chapter 8. "
            "The API ties the two together and is tested through FastAPI's test client and through a smoke script against a running server. Screens are checked by walking every route of the console with real data."),
          TAB("Test levels, tools and results.",
              ["Level", "Tool and scope", "Count", "Result"],
              [["Unit", "pytest: tests/test_crypto.py, tests/test_ids_engine.py", "16 tests", "All passed"],
               ["API / component", "pytest with FastAPI TestClient: tests/test_api.py", "10 tests", "All passed"],
               ["Integration", "scripts/smoke_test.py against the running backend (127.0.0.1:" + str(F.API_PORT) + ")", f"{F.SMOKE_TOTAL} checks", f"{F.SMOKE_PASSED} of {F.SMOKE_TOTAL} passed"],
               ["Functional / screens", "Playwright walk of the React console, screenshots 01 to 12", "12 screens", "All rendered with real data"],
               ["Security", "scripts/benchmark_crypto.py tamper and uniqueness tests", "6 cases x 1,000 trials; 20,000 encryptions", "As expected in every trial"],
               ["Performance", "scripts/benchmark_crypto.py and measure_pipeline.py", "5 payload sizes; 7 API calls", "Reported in Section 7.7"],
               ["Model validation", "scripts/run_experiments.py (5 + 10 seeds)", "15 runs on real data", "Reported in Chapter 8"]],
              widths=[1.3, 3.1, 1.3, 1.1], align=["l", "l", "l", "l"], size=9.5),
          P(f"All tests were run on one machine: Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB RAM shared with other running programs, Windows 11, Python 3.11.9, PyTorch {'2.14.1'} (CPU), XGBoost 2.0.3 and scikit-learn 1.5.0. "
            f"The pytest suite finished in {F.PYTEST_SECONDS} s. Timings in Section 7.7 are medians of repeated runs on this shared machine and should be read as indicative.")]

    # ------------------------------------------------------------------ 7.2
    b += [H2("7.2 Unit testing"),
          P(f"The pytest suite has **{F.PYTEST_TOTAL} tests in three files, and all {F.PYTEST_PASSED} passed**. The file `tests/conftest.py` imports PyTorch before anything else, because on the test machine PyTorch's DLLs fail to initialise if NumPy or pandas are loaded first."),
          H3("7.2.1 SecureChannel (tests/test_crypto.py, 10 tests)"),
          TAB("Unit tests of the cryptography.",
              ["Test", "What it asserts"],
              [["test_both_sides_derive_the_same_key", "ECDH from either side gives the same 32-byte key"],
               ["test_round_trip", "Decrypting an ephemeral-key envelope returns the plaintext; the ciphertext differs from the plaintext"],
               ["test_sizes_of_nonce_tag_and_point", "Nonce 12 bytes, tag 16 bytes, ephemeral public point 65 bytes, ciphertext as long as the plaintext (100 bytes)"],
               ["test_same_plaintext_gives_different_ciphertext", "Two encryptions of the same text differ in ciphertext, nonce and ephemeral key"],
               ["test_any_flipped_bit_is_rejected (3 cases)", "A flipped bit in the ciphertext, in the tag or in the nonce raises InvalidTag"],
               ["test_wrong_key_is_rejected", "A random 32-byte key cannot decrypt a valid envelope"],
               ["test_bad_parameter_lengths_are_refused", "A short key, an 11-byte nonce and a 15-byte tag raise ValueError"],
               ["test_empty_and_large_payloads", "Empty, one-byte and 5 MB payloads all round-trip"]],
              widths=[2.9, 3.9], align=["l", "l"], size=9.5),
          H3("7.2.2 ThreatSense Engine (tests/test_ids_engine.py, 6 tests)"),
          TAB("Unit tests of the detection engine (shipped bundle).",
              ["Test", "What it asserts"],
              [["test_engine_loads_all_artifacts", "Engine is loaded, uses the torch backend and has 70 input dimensions"],
               ["test_attack_and_normal_presets", "The attack preset is classified attack with severity medium, high or critical; the normal preset is normal with severity low"],
               ["test_scores_are_probabilities", "Confidence, XGBoost score and CNN score all lie in [0, 1]"],
               ["test_batch_matches_single", "A two-row batch gives the labels [attack, normal] and the same probability as the single-record call"],
               ["test_unseen_category_does_not_crash", "A never-seen protocol, service and state still gives a label"],
               ["test_shipped_metrics_file_is_consistent", "The confusion matrix of reports/metrics.json sums to the test size and reproduces the stored accuracy"]],
              widths=[2.9, 3.9], align=["l", "l"], size=9.5),
          H3("7.2.3 API (tests/test_api.py, 10 tests)"),
          TAB("Component tests of the HTTP API.",
              ["Test", "What it asserts"],
              [["test_health", "200, status ok, engine loaded"],
               ["test_metrics_endpoint", "200 and an accuracy between 0.5 and 1"],
               ["test_score_attack_raises_alert_and_normal_does_not", "Normal flow: label normal, no alert, alert list empty; attack flow: label attack, alert in the response, list holds one entry; DELETE clears it"],
               ["test_score_rejects_empty_payload", "An empty JSON object gives 400"],
               ["test_batch_scoring_and_validation", "The 120-row sample scores with attack plus normal counts equal to 120; a .txt upload and an empty CSV give 400"],
               ["test_encrypt_decrypt_round_trip", "Encrypt then decrypt returns the text with verified true"],
               ["test_decrypt_uses_cloud_private_key_when_cache_is_empty", "With the session-key cache cleared the real ECDH path still decrypts"],
               ["test_tampered_ciphertext_is_rejected", "One flipped ciphertext bit gives 400"],
               ["test_crypto_input_validation", "Empty plaintext, invalid base64 and a missing ephemeral key all give 400"],
               ["test_file_encryption_round_trip_and_limits", "A 21-byte file round-trips; an empty file and a file of 5 MB + 1 byte give 400"]],
              widths=[2.9, 3.9], align=["l", "l"], size=9.5)]

    # ------------------------------------------------------------------ 7.3
    smoke = [["1", "GET /api/health returns ok"], ["2", "Engine loaded with the installed scikit-learn"], ["3", "GET /api/metrics returns accuracy in (0.5, 1]"],
             ["4", "Attack preset scores as attack (severity high)"], ["5", "Normal preset scores as normal"], ["6", "Batch of the bundled sample scored (60 attacks / 60 normal)"],
             ["7", "Batch rejects a non-CSV upload with 400"], ["8", "Alert list has entries after scoring"], ["9", "DELETE /api/alerts empties the list"],
             ["10", "Encrypt returns a 12-byte nonce and a 16-byte tag"], ["11", "Decrypt round-trip returns the message, verified"], ["12", "Tampered ciphertext rejected with 400"],
             ["13", "Empty plaintext rejected with 400"], ["14", "File encryption returns the right original size"], ["15", "File decrypt round-trip returns the content"]]
    b += [H2("7.3 Integration testing"),
          P(f"`scripts/smoke_test.py` drives a running backend over HTTP exactly as the console does. It was run against the shipped bundle on port {F.API_PORT} and **all {F.SMOKE_PASSED} of {F.SMOKE_TOTAL} checks passed** (log in `docs/metrics/smoke_run.txt`). "
            "The checks cross the module boundaries: the API with the engine (checks 2 to 8), the API with the SecureChannel (10 to 15) and the alert log with the scorer (8 and 9). The script has a `--frontend` option that repeats the checks through the Vite proxy; "
            "that option was not run in the final pass because the React server was started separately for the screenshots."),
          TAB("The fifteen smoke checks.", ["No.", "Check"], smoke, widths=[0.6, 6.2], align=["c", "l"], size=9.5)]

    # ------------------------------------------------------------------ 7.4
    screens = [["01, 02", "Landing page, dark and light themes", "Page loads, live counters animate, terminal calls the API"],
               ["03", "Live scoring: attack preset", "Verdict ATTACK, severity HIGH, ensemble probability 0.84 (XGBoost 0.45, CNN 1.00)"],
               ["04, 05", "Batch scoring and session charts", "120-row sample scored; per-row table, attack-versus-normal chart"],
               ["06", "Secure transfer, verified", "Encrypt shows ciphertext, nonce, tag and ephemeral key; decrypt shows verified plaintext"],
               ["07", "Secure transfer, tampered", "After altering the ciphertext the decrypt is rejected (tag failure)"],
               ["08", "Alerts", "Alerts from the batch are listed with severity, confidence and scores"],
               ["09", "Model performance, shipped bundle", "97.33 % on synthetic data, banner \"synthetic demo data\", confusion matrix"],
               ["10", "Real flows, shipped model", "120 real UNSW-NB15 flows: the shipped model agrees with the labels on 78 of 120 (65.0 %)"],
               ["11", "Model performance, real-trained bundle", "88.79 % on the 82,332 official test flows, confusion matrix, 192 input dimensions"],
               ["12", "Real flows, real-trained bundle", "Same 120 flows: agreement 101 of 120 (84.2 %)"]]
    b += [H2("7.4 Functional testing"),
          P("Functional testing walked every route of the React console with real data, using Playwright with 1440 x 900 pixel windows (`scripts/capture_screens.py` for screens 01 to 09 and `scripts/capture_real_screens.py` for 10 to 12). "
            "The walk clicked the real buttons (Simulate attack, Use sample, Encrypt and transmit, Decrypt and verify, Tamper ciphertext), waited for the server's answers and saved a screenshot. It also collected browser console errors, page errors and failed requests; the only failed request is the intentional HTTP 400 of the tamper test. "
            "Screens 03 to 12 show states that can only occur if the corresponding API call succeeded, so the screenshots double as evidence of the functional test."),
          TAB("Functional checks by screen.", ["Screen", "Function", "Observed result"], screens, widths=[0.8, 2.3, 3.7], align=["c", "l", "l"], size=9.5)]
    if not rep:
        b += [FIG(F.shot("06_secure-transfer-verified.png"), "Secure transfer: the message was encrypted, sent to the mock cloud, decrypted and verified.", F.shot_w(F.shot("06_secure-transfer-verified.png"), 5.4)),
              FIG(F.shot("07_secure-transfer-tampered.png"), "The same envelope after one ciphertext byte was changed: the cloud rejects it.", F.shot_w(F.shot("07_secure-transfer-tampered.png"), 5.4))]

    # ------------------------------------------------------------------ 7.5
    u = F.CRY["uniqueness"]
    b += [H2("7.5 Security testing"),
          P("The security tests are attacks on the envelope that a network adversary or a faulty client could mount. Each was repeated 1,000 times with fresh messages and random positions (`tamper_tests` in `scripts/benchmark_crypto.py`), "
            "so that a position-dependent weakness would have shown up. The untouched message is the control: it must be accepted."),
          TAB("Tamper tests on the SecureChannel (1,000 trials each).", ["Case", "Expected", "Observed", "Result"], tamper_rows(), widths=[3.1, 0.9, 1.7, 1.1], align=["l", "c", "c", "c"], size=9.5),
          P(f"A second test checks for nonce reuse, which is the one way to break GCM badly: {u['encryptions']:,} encryptions of one identical plaintext produced {u['distinct_nonces']:,} distinct nonces and {u['distinct_ciphertexts_for_identical_plaintext']:,} distinct ciphertexts. "
            "Input validation was tested through the API: empty plaintext, empty file, a file of 5 MB + 1 byte, invalid base64, a missing ephemeral key, a non-CSV upload and an empty CSV all produced HTTP 400 and none produced a server error."),
          P("What the security testing does *not* establish matters as much. It does not show that the cryptography library is free of defects (it relies on the `cryptography` package), that the key derivation is used correctly beyond the tests above, "
            "or that the service is safe to expose: the API has no authentication, CORS is open (`*`), the transport is plain HTTP on the loopback interface, the cloud key pair and all session keys live in process memory, and no fuzzing, penetration test or dependency audit was run. "
            "The adversary model of the tests is the network attacker who modifies a message in transit; an adversary who can call the API, or read the process memory, is out of scope.")]

    # ------------------------------------------------------------------ 7.6
    b += [H2("7.6 Validation and edge cases"),
          P("Validation asks whether the system behaves sensibly at the edges of its input space. The table separates what was actually exercised from what the code promises but no test checks."),
          TAB("Edge cases and how they were checked.", ["Case", "Behaviour", "Checked by"],
              [["Category never seen in training (protocol, service, state)", "Scored without error; the one-hot block is all zeros", "test_unseen_category_does_not_crash"],
               ["Record with only a few features", "Missing features take the documented defaults", "Smoke and API tests (partial records)"],
               ["Empty JSON object", "400", "test_score_rejects_empty_payload"],
               ["Non-CSV or empty CSV upload", "400", "test_batch_scoring_and_validation; smoke check 7"],
               ["Empty plaintext, empty file", "400", "test_crypto_input_validation; test_file_encryption_...; smoke check 13"],
               ["File of 5 MB + 1 byte", "400", "test_file_encryption_round_trip_and_limits"],
               ["Payload of 5 MB, 1 byte, 0 bytes (library level)", "Round-trip succeeds", "test_empty_and_large_payloads"],
               ["Invalid base64, missing ephemeral key", "400", "test_crypto_input_validation"],
               ["Session-key cache empty", "Real ECDH with the cloud private key", "test_decrypt_uses_cloud_private_key_when_cache_is_empty"],
               ["Real flows instead of synthetic", "Scores, but quality depends on the training data (Chapter 8)", "Experiments; screens 10 to 12"],
               ["CSV with 10,001 rows, CSV above 10 MB, plaintext above 1 MB", "Specified as 400", "**Not tested** (limits are in the code only)"],
               ["Concurrent requests, very long sessions", "Not specified", "**Not tested**"]],
              widths=[2.5, 2.3, 2.0], align=["l", "l", "l"], size=9.3),
          P(f"Model validation, the other kind of validation, is done by repetition rather than by single runs. The official-partition experiment was run with five seeds and the base-paper protocol with ten, so that every reported metric has a standard deviation; "
            f"for example the stacked model's accuracy on the official test set is {F.mstd(F.OFFS, 'stack', 'accuracy')} and its ROC-AUC {F.mstd(F.OFFS, 'stack', 'roc_auc', 4)}. The test set is never used for fitting, early stopping or the meta-model. "
            "A deliberate weakness of the validation is that the threshold analysis of Chapter 8 was computed on the test set; it describes the trade-off and is not a tuned result.")]

    # ------------------------------------------------------------------ 7.7 performance
    b += [H2("7.7 Performance testing"),
          H3("7.7.1 Cryptography"),
          P("Each operation was timed with a high-resolution clock on payloads of 1 KB to 5 MB, 300 repetitions for payloads up to 100 KB and 40 or 15 for the larger ones; the table gives medians. "
            "*SecureChannel* includes everything the API does for one message: ephemeral key generation, ECDH, HKDF, AES-GCM and the base64 encoding that the API needs. The comparison columns are AES-256-GCM alone (no key agreement, no base64) and a classical RSA-OAEP key wrap plus AES-GCM, which the project did not adopt but measured as the baseline for objective 1."),
          TAB("Median encryption and decryption time in milliseconds by payload size.",
              ["Payload", "SecureChannel enc", "SecureChannel dec", "AES-GCM only enc / dec", "RSA-2048 + AES enc / dec", "RSA-3072 + AES enc / dec"],
              crypto_rows(), widths=[0.8, 1.1, 1.1, 1.3, 1.3, 1.3], align=["l", "r", "r", "r", "r", "r"], size=9.2),
          P(f"Three observations follow. First, for payloads up to 100 KB every SecureChannel operation takes well under one millisecond ({_ms(F.crypto_row('sc', '100 KB', 'encrypt'))} ms to encrypt 100 KB). Second, at 1 MB and above SecureChannel is several times slower than raw AES-GCM "
            f"({_ms(F.crypto_row('sc', '5 MB', 'encrypt'))} ms against {_ms(F.crypto_row('aes', '5 MB', 'encrypt'))} ms for 5 MB) because it also base64-encodes the data, a cost of the demonstration API format and not of the cipher; its throughput is about {F.CRY['secure_channel_ecdh_aesgcm']['5 MB']['encrypt_throughput_mb_s']:.0f} MB/s against "
            f"{F.CRY['aes256gcm_only']['5 MB']['throughput_mb_s']:,.0f} MB/s for AES-GCM alone. Third, the asymmetric step is cheap: ECDH key generation takes {F.CRY['key_setup']['ecdh_p256_keygen']['median_ms'] * 1000:.0f} microseconds and ECDH with HKDF {F.CRY['key_setup']['ecdh_exchange_plus_hkdf']['median_ms'] * 1000:.0f} microseconds, while one RSA-2048 key generation took {F.CRY['rsa2048_oaep_aesgcm']['keygen_ms_one_time']:.0f} ms and RSA-3072 {F.CRY['rsa3072_oaep_aesgcm']['keygen_ms_one_time']:.0f} ms (single samples, one-time cost). "
            f"RSA-OAEP encryption is cheaper than SecureChannel at small sizes, but RSA decryption costs {F.crypto_row('rsa2048', '1 KB', 'decrypt') / F.crypto_row('sc', '1 KB', 'decrypt'):.1f} times (2048 bits) and {F.crypto_row('rsa3072', '1 KB', 'decrypt') / F.crypto_row('sc', '1 KB', 'decrypt'):.1f} times (3072 bits) more at the cloud for a 1 KB message. "
            f"The fixed wire overhead of SecureChannel is {F.ENVELOPE_OVERHEAD_BYTES} bytes per message ({F.ENVELOPE_OVERHEAD_BYTES / 1024 * 100:.1f} % of a 1 KB message, under 0.1 % above 100 KB)."),
          FIG(F.fig("f09_crypto_latency.png"), "Median encryption and decryption time against payload size for SecureChannel, AES-GCM alone and two RSA hybrids (log scale).", 6.0),
          H3("7.7.2 Detection and the combined pipeline"),
          P(f"The in-process cost of one protected 100 KB transfer was timed over 200 repetitions: scoring one flow takes {ip['ids_score_single']['median_ms']:.2f} ms, encrypting 100 KB {ip['encrypt_100kb']['median_ms']:.2f} ms and decrypting it {ip['decrypt_100kb']['median_ms']:.2f} ms. "
            f"Measured end to end the three steps take **{ip['protected_transfer_100kb']['median_ms']:.2f} ms** (95th percentile {ip['protected_transfer_100kb']['p95_ms']:.2f} ms). The intrusion detector accounts for {share['ids'] * 100:.0f} % of that time, encryption for {share['encrypt'] * 100:.0f} % and decryption for {share['decrypt'] * 100:.0f} %: "
            f"it is the detection, not the encryption, that dominates the combined overhead. Batch scoring is far cheaper per flow: 120 rows take {ip['ids_batch_120_rows']['median_ms']:.1f} ms and 1,000 rows {ip['ids_batch_1000_rows']['median_ms']:.1f} ms. "
            f"Loading the models takes {ip['engine_load_ms']:.0f} ms. For the real-trained bundle (192 inputs) one flow takes {O['inference_timing_ms']['1']['median_ms']:.2f} ms, 100 flows {O['inference_timing_ms']['100']['median_ms']:.1f} ms and 1,000 flows {O['inference_timing_ms']['1000']['median_ms']:.1f} ms."),
          TAB("API latency over HTTP on 127.0.0.1 (milliseconds).", ["Call", "Median", "95th percentile", "Repetitions"], api_rows(), widths=[3.6, 1.0, 1.3, 0.9], align=["l", "r", "r", "r"], size=9.5),
          P("The three-call sequence of scoring a flow, encrypting 1 KB and decrypting it takes about 8 ms through HTTP, which is the figure that answers the gap named in the literature survey: the two protections can run together on one data path for a few milliseconds per message on a CPU-only laptop. "
            "What the measurements do not cover is throughput under concurrent load, network latency to a real cloud provider, and the memory footprint."),
          FIG(F.fig("f10_pipeline_latency.png"), "Time split of one protected transfer and median latency of the API calls.", 6.2)]

    # ------------------------------------------------------------------ 7.8
    b += [H2("7.8 User acceptance testing"),
          P("No formal user acceptance test was held: there was no test group, questionnaire or acceptance criteria agreed with a stakeholder, and this chapter does not claim one. "
            "What was done instead is a scripted walkthrough by the project team of the complete user journey on real data: start the application, score an attack and a normal record, upload a CSV, read the alerts, encrypt a message, decrypt it, tamper with it, and open the performance page. "
            "Every step produced the expected screen (Section 7.4). The walkthrough also exposed usability points that a formal acceptance test would be expected to find: the model-performance page of the shipped bundle shows 97.33 % beside a banner that says the data are synthetic, "
            "and a reader who skips the banner will over-trust the figure; and the text under the sample button describes the sample as real flows although it is synthetic.")]

    # ------------------------------------------------------------------ 7.9
    b += [H2("7.9 Defects and observations from testing"),
          TAB("Findings of the test and measurement runs.", ["No.", "Finding", "Consequence"],
              [["1", "Shipped model on real UNSW-NB15 flows: accuracy " + F.f3(F.SHIFT["shipped_on_real_official_test"]["stack"]["accuracy"]) + ", ROC-AUC " + F.f3(F.SHIFT["shipped_on_real_official_test"]["stack"]["roc_auc"]) + " (screen 10: 65 % agreement)",
                "The default model must not be presented as a real detector; a real-trained bundle was produced (screens 11, 12) and a switch to serve it was added"],
               ["2", "PyTorch fails to load (DLL error 1114) when NumPy or pandas are imported first on the test machine", "Launcher and tests import PyTorch first; documented in Section 6.10. The original `run.bat` environment was not re-run"],
               ["3", "README claims balanced loss weighting for the CNN; the PyTorch path trains with unweighted BCE", "Documented; CNN shows high recall and high false-positive rate on real data"],
               ["4", "UI text calls the bundled sample \"real flows\"; the sample is synthetic", "Documented; not changed"],
               ["5", "`attack_cat` of the synthetic data is drawn with an unseeded random call", "The generated CSV is not reproducible bit for bit; the shipped CSV is the reference"],
               ["6", "On real data the stack does not beat XGBoost alone (" + F.mstd(F.OFFS, "stack", "accuracy") + " against " + F.mstd(F.OFFS, "xgb", "accuracy") + ")", "Reported as a finding in Chapter 8; the design was not altered to hide it"],
               ["7", "Alerts live in memory and are lost on restart; the cloud key pair changes on restart", "Documented as a limitation; no persistence was added"]],
              widths=[0.5, 3.6, 2.7], align=["c", "l", "l"], size=9.2)]

    # ------------------------------------------------------------------ 7.10
    b += [H2("7.10 Limits of the testing done"),
          P("The results above support the claims of this report, but they have limits that the reader should know:"),
          B("**One machine, one operating system, one run per timing.** All timings come from a shared Intel i5-12500 machine running Windows 11; no other operating system, browser other than Chromium or Chrome, or Python version was tested.",
            "**Default settings only.** Docker, the TensorFlow code path and `run.bat` in a fresh environment were not exercised in the documentation run.",
            "**No load, soak or concurrency testing,** no memory or energy measurement, and no measurement against a real cloud provider or over a real network.",
            "**No adversarial testing of the detector.** The IDS was never attacked with crafted flows, and its dependence on the `sttl` feature suggests that it would be easy to evade.",
            "**No independent review of the cryptography.** The tamper tests show that the library behaves as specified in the cases tried; they are not a security audit.",
            "**Threshold analysis on the test set.** The threshold sweep of Chapter 8 uses the held-out data and is descriptive, not a tuned operating point.",
            "**Real-data results come from one dataset.** UNSW-NB15 is a testbed capture with known artefacts; the results say nothing about other networks, and the official test period is the only temporal shift examined.",
            "**Small automated suite.** Twenty-six tests and fifteen smoke checks cover the main routes and the cryptography; they do not cover the front-end components, and the React console was tested only by the screenshot walk.")]
    if rep:  # compact variant for the full report; the chapter documents never call blocks() with F.REPORT set
        b = _drop(b, "Component tests of the HTTP API", "The fifteen smoke checks", "Time split of one protected transfer")
        b = [x for x in b if not (x[0] == "tab" and x[1].startswith("Findings of the test"))] + []
        i = [k for k, x in enumerate(b) if x[0] == "h2" and x[1].startswith("7.10")][0]
        b.insert(i, _defects_compact())
        j = [k for k, x in enumerate(b) if x[0] == "h3" and x[1].startswith("7.2.3")][0]
        b.insert(j + 1, P("The ten API tests (`tests/test_api.py`, via FastAPI's TestClient) check health and metrics; that a normal flow raises no alert while an attack flow does and `DELETE` clears the list; "
                          "that an empty record, a non-CSV upload and an empty CSV give 400; the 120-row batch; the encrypt-decrypt round trip, including the path that re-derives the key with the cloud private key when the session-key cache is empty; "
                          "rejection of a tampered ciphertext; 400 for empty plaintext, invalid base64 and a missing ephemeral key; and the file round trip with an empty file and a file of 5 MB + 1 byte refused."))
        k2 = [k for k, x in enumerate(b) if x[0] == "h2" and x[1].startswith("7.3")][0]
        b.insert(k2 + 2, P("The fifteen checks are: health; engine loaded; metrics; attack preset scored attack; normal preset scored normal; the 120-row sample batch (60 attacks, 60 normal); non-CSV upload rejected; alerts present; alerts cleared; "
                           "encrypt with 12-byte nonce and 16-byte tag; decrypt round trip; tampered ciphertext rejected; empty plaintext rejected; file encryption size; file decrypt round trip."))
    return b


def _defects_compact():
    return P("Findings of the test and measurement runs: (1) the shipped model scores " + F.f3(F.SHIFT["shipped_on_real_official_test"]["stack"]["accuracy"]) + " accuracy and ROC-AUC " + F.f3(F.SHIFT["shipped_on_real_official_test"]["stack"]["roc_auc"])
             + " on real UNSW-NB15 flows (screen 10: 65 % agreement), so a real-trained bundle was produced and a switch to serve it was added; (2) PyTorch fails to load (DLL error 1114) when NumPy or pandas are imported first on the test machine, so the launcher and tests import it first (the original `run.bat` environment was not re-run); "
             "(3) the README claims balanced loss weighting for the CNN but the PyTorch path trains with unweighted BCE; (4) the UI text calls the bundled sample \"real flows\" although it is synthetic; (5) `attack_cat` of the synthetic data is drawn with an unseeded random call; "
             "(6) on real data the stack does not beat XGBoost alone (" + F.mstd(F.OFFS, "stack", "accuracy") + " against " + F.mstd(F.OFFS, "xgb", "accuracy") + "), which Chapter 8 reports as a finding; (7) alerts and the cloud key pair live in memory and are lost on restart. All were documented rather than hidden.")
