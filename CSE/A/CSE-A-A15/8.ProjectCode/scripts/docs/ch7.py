"""Chapter 7: System Testing for CipherVeil. Numbers come from facts.py (experiments/**) and the recorded test runs (docs/REPORT_FACTS.md section 8)."""

from . import facts as F
from .blocks import B, FIG, H1, H2, N, P, TAB

_LAT = ["login", "keys/generate 2048", "keys/generate 3072", "keys/generate 4096",
        "send (21 KiB memo, 512x512 cover, RSA-3072)", "send (21 KiB memo, 1280x720 cover)", "receive (RSA-3072)",
        "analysis metrics", "histogram + bit planes, first render", "robustness (9 attacks)",
        "benchmark/run (6 covers x 3 sizes, RSA-2048)", "log (100 rows)", "health"]


def _lat_rows():
    rows = []
    for k in _LAT:
        v = F.API.get(k)
        if v:
            tail = v.get("p95_ms", v.get("max_ms"))
            rows.append([k.replace("benchmark/run", "benchmark run"), str(v["n"]), f"{v['median_ms']:,.1f}", f"{tail:,.1f}"])
    return rows


def _rsa_rows():
    return [[str(r["rsa_bits"]), f"{r['keygen_ms_median']:.1f} ({r['keygen_ms_min']:.1f}-{r['keygen_ms_max']:.1f})",
             f"{r['encrypt_wrap_ms_median']:.3f}", f"{r['unwrap_decrypt_ms_median']:.1f}", str(r["wrapped_key_bytes"]), str(r["overhead_bytes"])]
            for r in F.EX["rsa_study"]]


def _tamper_rows():
    t = F.EX["tamper_study"]["by_field"]
    out = []
    for fld, d in t.items():
        res = "; ".join(f"{k.replace('rejected: ', '')} x{v}" for k, v in d.items())
        out.append([fld, str(sum(d.values())), res])
    return out


def blocks():
    s, ex = F.S, F.EX
    tam = ex["tamper_study"]
    b = [H1("CHAPTER 7: SYSTEM TESTING")]

    # ------------------------------------------------------------------ 7.1
    b += [H2("7.1 Testing strategy"),
          P("CipherVeil was delivered with a single end-to-end smoke script and an evaluation script. The documentation run added an automated test suite, a tamper study and the measurement scripts. "
            "The cryptographic and steganographic services are deterministic functions of their inputs (apart from the random session key and nonce), so they are tested at unit level with exact assertions: "
            "a round trip must return the original bytes, a flipped bit must be rejected, and the PSNR of a known change must equal its closed-form value. "
            "The API is tested through FastAPI's test client against a scratch database and a scratch output folder, so tests never touch the user's data, and through a smoke script against a running server. "
            "The screens were walked with real data and captured by a Playwright script; that walk is evidence that the screens work, not an automated assertion suite."),
          TAB("Test levels, tools and results.",
              ["Level", "Tool and scope", "Count", "Result"],
              [["Unit", "pytest: tests/test_crypto.py, test_lsb.py, test_metrics_pipeline.py", f"{F.PYTEST_CRYPTO + F.PYTEST_LSB + F.PYTEST_METRICS} tests", "All passed"],
               ["API and component", "pytest with FastAPI TestClient: tests/test_api.py", f"{F.PYTEST_API} tests", "All passed"],
               ["Integration", f"scripts/smoke_test.py against the running API (127.0.0.1:{F.API_PORT})", f"{F.SMOKE_TOTAL} checks", f"{F.SMOKE_PASSED} of {F.SMOKE_TOTAL} passed"],
               ["Round-trip evaluation", "ml/eval.py: 6 covers x 5 payload sizes", "22 runs (8 blocked by capacity)", "22 of 22 byte-exact"],
               ["Security", "Tamper study: one flipped stego LSB, 6 bundle fields", f"{tam['trials']} trials", f"{tam['trials']} of {tam['trials']} rejected"],
               ["Robustness", "Nine attacks x 6 covers, plus nine more channel changes", "54 + 54 attempts", "Only lossless handling survives (Chapter 8)"],
               ["Performance", "Median timings of services and of the API", "see Section 7.7", "Measured"],
               ["Screens", "Playwright walk of all eight screens, 18 captures", "18 screens", "All rendered with real data"]],
              widths=[1.1, 3.1, 1.3, 1.5], align=["l", "l", "c", "l"], size=9.5),
          P(f"All {F.PYTEST_TOTAL} automated tests pass in about 8 to 12 seconds on the measurement machine. Test files and scripts are part of the repository (`tests/`, `scripts/smoke_test.py`, `scripts/run_experiments.py`), "
            "so every result in this chapter can be reproduced with one command.")]

    # ------------------------------------------------------------------ 7.2
    b += [H2("7.2 Unit tests"),
          P(f"The {F.PYTEST_CRYPTO + F.PYTEST_LSB + F.PYTEST_METRICS} unit tests are split by module. The table lists each file and what its tests assert; a parametrised test counts once per parameter."),
          TAB("Unit tests by file.",
              ["File", "Tests", "What is asserted"],
              [["test_crypto.py", str(F.PYTEST_CRYPTO),
                "Round trip with path stripped from the stored name; overhead matches the bundle layout; a fresh key and nonce per message (two encryptions of the same data differ); wrong private key rejected; "
                "key-size mismatch rejected before any private-key operation; tampered ciphertext, nonce or tag rejected (three positions); tampered wrapped key rejected; truncated, foreign-magic and empty bundles rejected; "
                "key sizes below the policy rejected; fingerprint stable; public key derivable from private key"],
               ["test_lsb.py", str(F.PYTEST_LSB),
                "Capacity equals (3WH - 32) / 8; exact round trip for 1 byte, 17, 1,000 bytes and a payload that fills the cover exactly; only the lowest bit plane changes and by at most 1; values after the payload are untouched; "
                "oversize payload rejected; a clean cover yields no decryptable bundle; PNG encoding is lossless; alpha channel dropped; a non-image is rejected"],
               ["test_metrics_pipeline.py", str(F.PYTEST_METRICS),
                "Identical images give undefined PSNR and SSIM 1; PSNR of exactly 1,000 changed values equals the closed form within 0.01 dB; pipeline round trip with PSNR above 50 dB and largest change 1; "
                "a full cover gives 50.9 to 51.5 dB (the theoretical floor); lossless attacks recover and the seven destructive ones do not, with error rates between 0.3 and 0.7; the benchmark marks oversize rows; capacity table gives 3.0 bits per pixel"]],
              widths=[1.4, 0.6, 4.7], align=["l", "c", "l"], size=9.5),
          P("Two of these tests deserve a remark. The closed-form PSNR test is a check of the specification as well as the code: it fails if the metric is computed over a different set of values or with a different data range. "
            "The floor test embeds a random payload that fills the cover and requires a PSNR between 50.9 and 51.5 dB; it would fail if the embedding wrote more than one bit per value or changed values by more than one.")]

    # ------------------------------------------------------------------ 7.3
    b += [H2("7.3 Integration testing"),
          P(f"`scripts/smoke_test.py` drives a running backend over HTTP using only the standard library, in the order a user would: {F.SMOKE_TOTAL} checks, all of which pass. "
            "It logs in as the demo user, generates an RSA-3072 and an RSA-2048 keypair, sends the sample memo into the astronaut cover, reads the metrics (PSNR above 50 dB, SSIM above 0.999, no value moved by more than 1, input hash recorded), "
            "fetches the histogram and bit-plane images, downloads the stego PNG and submits it as a fresh upload, and requires the restored file to be byte-identical with equal hashes."),
          B("**Rejections:** the second keypair is refused as a wrong private key; the original cover is refused as an image with no payload.",
            "**Robustness:** a lossless re-save survives; JPEG at quality 95 and 50, noise and the left crop destroy the payload.",
            "**Capacity:** the same memo into the 200 x 200 cover is blocked with the capacity message.",
            "**Housekeeping:** the capacity table lists six covers; the log contains the key, send, receive and robustness operations and contains no key material.")]

    # ------------------------------------------------------------------ 7.4
    b += [H2("7.4 Functional testing"),
          P("Each feature of the application was exercised on the running system with real data. The table maps the seven features to the evidence."),
          TAB("Functional test cases.",
              ["#", "Feature", "Action and expected result", "Evidence", "Result"],
              [["F1", "Keys", "Generate RSA-3072 and RSA-2048 keypairs; import a public-only key; fingerprints shown", "test_key_lifecycle; screen 04", "Passed"],
               ["F2", "Send", "Encrypt the memo into the astronaut cover; stego PNG, PSNR 57.642 dB, SSIM 0.9991, 22.445 % used", "test_send_receive_end_to_end; screens 05-06", "Passed"],
               ["F2", "Send (capacity)", "A 22,063-byte bundle into a 14,996-byte cover is blocked with the sizes in the message", "test_capacity_check_blocks_oversize; screen 07", "Passed"],
               ["F3", "Receive", "Extract and decrypt; both SHA-256 values equal; file downloadable", "test_send_receive_end_to_end; screen 11", "Passed"],
               ["F3", "Receive (wrong key)", "A same-size wrong keypair fails with the RSA unwrap message and releases nothing", "test_receive_failure_paths; screen 12", "Passed"],
               ["F4", "Analysis", "PSNR, SSIM, MSE, histograms and bit planes of a send", "test_analysis_images_and_robustness; screens 08-10", "Passed"],
               ["F5", "Capacity and timings", "Capacity per cover; timings per stage; benchmark rows with blocked rows marked", "smoke test; screens 15-16", "Passed"],
               ["F6", "Robustness", "Nine attacks; two survive, seven lose the payload; verdict shown", "test_robustness_lossless_survives_lossy_destroys; screens 13-14", "Passed"],
               ["F7", "Log", "Operations with sizes, timings, metrics; failures visible; no secrets", "test_log_never_contains_key_material; screens 17-18", "Passed"]],
              widths=[0.4, 1.1, 2.8, 1.8, 0.7], align=["c", "l", "l", "l", "c"], size=9),
          P("Registration and login validation (user name length, password length, duplicate user, wrong password) is covered by test_register_login_validation.")]

    # ------------------------------------------------------------------ 7.5
    b += [H2("7.5 Security testing"),
          P(f"The central security claim of the hybrid scheme is that nothing is released unless the key is right and the data is untouched. It was tested directly. "
            f"The tamper study takes a stego image of the astronaut cover holding a 4 KiB random payload (RSA-2048), flips exactly one least significant bit at a random position inside each of six regions of the embedded bundle, "
            f"and runs the real extract-and-decrypt path. Forty flips per region, {tam['trials']} in all: **{tam['accepted_with_wrong_data']} were accepted with wrong data**, and every flip was rejected."),
          TAB("Tamper study: one flipped LSB in each region of the bundle.",
              ["Region of the bundle", "Flips", "How it was rejected"],
              _tamper_rows(), widths=[1.8, 0.6, 4.3], align=["l", "c", "l"], size=9.5),
          FIG(F.fig("f09_tamper_outcomes.png"), "Outcome of the 240 single-bit tamper trials by region of the bundle.", 5.0),
          P("A flip in the length prefix is caught in one of two ways: 13 of the 40 produce an implausible length and are refused at extraction, and the other 27 change the number of bytes read, so the tag check fails. "
            "The other checks are:"),
          B("**Wrong key, same size:** RSA-OAEP decryption fails and the message names the key as the cause (test_wrong_private_key_rejected; test_receive_failure_paths).",
            "**Wrong key size:** rejected from the wrapped-key length before any RSA operation (test_key_size_mismatch_rejected).",
            "**Truncated, foreign and empty bundles:** rejected (test_truncated_and_foreign_bundles).",
            "**Path traversal:** requests for `..%2F..%2F.env` and `..%5C..%5C.env` as sample names return 404 (test_sample_names_cannot_escape_folder).",
            "**Secrets in the log:** a search of 500 log entries for `BEGIN` and `PRIVATE` finds nothing (test_log_never_contains_key_material).",
            "**Key policy:** generating a 1,024-bit key is refused (test_key_lifecycle); a public key imported as recipient cannot export a private part.",
            f"**Freshness:** 50 encryptions of one file under one key gave {ex['freshness']['distinct_nonces']} distinct nonces and {ex['freshness']['distinct_wrapped_keys']} distinct wrapped keys; the mean bit difference between two bundles was {ex['freshness']['mean_bit_difference_between_bundles']:.4f}, as expected for independent random keys."),
          P("What was not tested is as important. The ownership checks that stop one user opening another's key or operation are in the code but no test logs in as a second user to try it. "
            "The 25 MB upload cap is in the code but no test sends 25 MB. No penetration test, fuzzing campaign or timing-side-channel analysis was done, and the application inherits the properties of the `cryptography` library rather than proving them.")]

    # ------------------------------------------------------------------ 7.6
    b += [H2("7.6 Validation and edge cases"),
          TAB("Edge cases and their outcomes.",
              ["Case", "Expected", "Outcome", "Where checked"],
              [["Payload fills the cover exactly", "Embeds and extracts", "Byte-exact", "test_round_trip_exact"],
               ["One byte over capacity", "Rejected with sizes", "Rejected: payload needs N bytes, cover holds only C", "test_oversize_rejected"],
               ["One-byte payload", "Works", "Byte-exact", "test_round_trip_exact"],
               ["Empty file", "Rejected", "400", "test_empty_upload_rejected"],
               ["Upload that is not an image", "Rejected", "400: could not read as an image", "test_non_image_rejected"],
               ["Cover with an alpha channel", "Accepted, alpha dropped", "Shape (H, W, 3); PNG with alpha also survives re-save", "test_alpha_channel_dropped; extra attack grid"],
               ["Image with no payload", "No plausible bundle", "Rejected, never decrypts", "test_clean_cover_has_no_decryptable_payload"],
               ["Smallest cover (200 x 200) with the memo", "Blocked", "Blocked by the capacity check", "smoke test; screen 07"],
               ["PNG re-saved at compression 9, with alpha, or as lossless WebP", "Payload survives", "6 of 6 covers each", "run_experiments, group G"],
               ["JPEG quality 100, lossy WebP q90, grayscale, rotate 90, flip, 256-colour palette", "Payload lost", "0 of 6 covers each", "run_experiments, group G"],
               ["Crop bottom 10 % / crop left 10 %", "Survives / lost", "6 of 6 / 0 of 6", "ml/eval.py"]],
              widths=[2.3, 1.2, 1.9, 1.3], align=["l", "l", "l", "l"], size=9),
          P("The two rows at the bottom of the table show why robustness results must be read with the embedding layout in mind. A crop of the bottom rows leaves the payload intact because the bits are stored from the top row downwards "
            "and the payload ends before the cut; a crop of the left columns changes the row width, so every later bit lands in the wrong place.")]

    # ------------------------------------------------------------------ 7.7
    b += [H2("7.7 Performance testing"),
          P(f"All timings were taken on one machine (Intel Core i5-12500, 6 cores, 15.7 GB, Windows 11, CPU only). Other work ran on the same machine at times, so absolute milliseconds vary by roughly 10 to 30 % between runs "
            f"(for example, the RSA-3072 unwrap median is {s['median_decrypt_ms']} ms in `ml/eval.py` and 93.7 ms in the extra experiments); the ordering of the costs does not change."),
          P(f"**Service level.** Over the 22 evaluated runs the median times are {s['median_encrypt_ms']} ms to encrypt and wrap, {s['median_embed_ms']} ms to embed and {s['median_extract_ms']} ms to extract; "
            f"the largest embedding, 131,072 bytes into the 1280 x 720 cover, took 1.674 ms. The only noticeable cost is the RSA private-key operation, median {s['median_decrypt_ms']} ms at 3072 bits."),
          FIG(F.fig("f04_stage_timings.png"), "Median time of each stage of the pipeline for the evaluated payload sizes.", 5.0),
          TAB("RSA key size: time and overhead (median of 30 operations on a 4 KiB payload; key generation median of 5, with range).",
              ["RSA bits", "Key generation (ms)", "Encrypt + wrap (ms)", "Unwrap + decrypt (ms)", "Wrapped key (B)", "Overhead (B)"],
              _rsa_rows(), widths=[0.8, 1.9, 1.1, 1.2, 0.9, 0.8], align=["c", "c", "c", "c", "c", "c"], size=9.5),
          FIG(F.fig("f05_rsa_key_size.png"), "Key generation and private-key operation time at 2048, 3072 and 4096 bits.", 4.8),
          P("Wrapping is cheap at every size because the public exponent is small; unwrapping and key generation grow steeply (roughly seven times from 2048 to 4096 bits for unwrapping). The overhead grows only by 128 bytes per step. "
            "Key generation is also highly variable (the 4096-bit range is 97 to 541 ms) because it searches for random primes."),
          P("**API level.** The table gives end-to-end latency through HTTP on 127.0.0.1 with the demo user. A send costs 0.4 s on a 512 x 512 cover and 1.9 s on 1280 x 720, although encryption and embedding together take well under a millisecond: "
            "the time goes to PNG encoding (100 to 190 ms in the log) and to the SSIM computation (about 300 ms), both of which are measurements and not part of the protection. Login costs 0.29 s because bcrypt is deliberately slow."),
          TAB("API latency (median and 95th percentile or maximum, ms).",
              ["Call", "Runs", "Median", "p95 / max"],
              _lat_rows(), widths=[3.9, 0.7, 1.0, 1.1], align=["l", "c", "r", "r"], size=9.5),
          FIG(F.fig("f10_api_latency.png"), "Median API latency of the main calls.", 5.0),
          P("No load or concurrency test was run: every figure is for one user at a time.")]

    # ------------------------------------------------------------------ 7.8
    b += [H2("7.8 User acceptance"),
          P("No formal user-acceptance test with outside users was carried out, and this chapter does not claim one. The acceptance evidence is a structured walk of the console by the team on a fresh database: sign in, generate two RSA-3072 keys and import a public key, "
            "send four files into four covers, try one send that the capacity check blocks, analyse the first message, receive it with the right key and fail with the wrong one, run the nine attacks, run the benchmark, and read the log. "
            "Each step worked as the screen text described, and the 18 screens captured in that session are shown in Chapter 8 and Appendix C."),
          P("The walk also found one defect that the unit tests could not: the Send screen refers to an icon it does not import, so an account with no keys sees a crash instead of the empty-state message (`KeyRound is not defined`, reproduced with a freshly "
            "registered account). The Receive screen imports the icon and is not affected. The defect is recorded, not fixed, in the code that was submitted; the one-line fix is to import `KeyRound` from `lucide-react` in `Send.jsx`.")]

    # ------------------------------------------------------------------ 7.9
    b += [H2("7.9 Limits of the testing done"),
          P("The results above support the claims made for CipherVeil and no more. The following were not done and should be read as open items."),
          B("**No browser test suite.** The screens were driven and captured by a script but not asserted, so a visual regression would not be caught automatically.",
            "**No load, concurrency or soak test.** Latency is for a single user; a shared database file and a single worker process were not stressed.",
            "**No external security audit, fuzzing or side-channel analysis.** The tamper study covers single-bit flips only, not structured attacks on the bundle format.",
            "**No cross-user authorisation test and no 25 MB upload test**, although the checks exist in the code.",
            "**Six covers and four small payloads.** All covers are the committed library images; no camera photographs, no large files, no images produced by social-media pipelines.",
            "**One machine.** All timings come from one Windows PC; other hardware was not tried.",
            "**Statistical detection is assessed with two classical detectors only.** The chi-square and weighted-stego tests were implemented here; RS analysis, sample-pair analysis and learned detectors were not run, so the detection results are a lower bound on what an attacker could do.",
            "**No comparison run against the base paper.** Its code was not executed; the comparison in Chapter 8 uses its published numbers and says where the conditions differ.")]
    return b
