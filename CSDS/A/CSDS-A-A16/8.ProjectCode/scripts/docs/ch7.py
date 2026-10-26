"""Chapter 7: System Testing for Mosaic. Counts come from the recorded pytest run (experiments/pytest_results.xml via F.TESTS);
timings and probes from F.APIM (scripts/measure_api.py); the Haar study from F.DET (scripts/run_experiments.py)."""
import os

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, P, TAB
from .refs import CITE as C

T, A, D = F.TESTS, F.APIM, F.DET

# ----------------------------------------------------------------------------- grouping of the 28 pytest cases
_GROUPS = [
    ("Taxonomy", "test_units", ["test_taxonomy_counts_and_order", "test_every_compound_has_two_distinct_basic_components", "test_compound_pairs_are_unique", "test_display_label"],
     "7 basic + 11 compound = 18 unique labels in a fixed order; every compound has two distinct valid components; no two compounds share a pair; `display_label` title-cases keys."),
    ("Security primitives", "test_units", ["test_password_hash_roundtrip", "test_token_roundtrip_and_tamper", "test_expired_token_rejected", "test_token_signed_with_other_key_rejected"],
     "bcrypt hash differs from the password and verifies only the right one; a JWT round-trips; a tampered, expired or wrongly signed token decodes to nothing."),
    ("Model and pre-processing", "test_units", ["test_class_weights_inverse_frequency", "test_cnn_output_shapes", "test_gan_shapes", "test_preprocess_range_and_shape",
                                                 "test_no_face_in_flat_image", "test_synthesised_compound_labels_have_three_bits"],
     "Rarer classes get larger loss weights; the CNN returns (N, 7) and (N, 18); the generator returns 1x64x64 images in [-1, 1] and the discriminator one logit; a white face scales to +1.0; a flat grey image has no face; "
     "synthesised compound targets have exactly three bits set (two basic, one compound)."),
    ("Service and accounts", "test_api", ["test_health", "test_health_reports_model_loaded", "test_register_login_me", "test_duplicate_email_conflict", "test_short_password_rejected",
                                          "test_bad_login", "test_me_requires_token", "test_history_requires_token"],
     "Health, registration, login and `/me`; 409 on a duplicate e-mail; 422 on a five-character password; 401 on a wrong password, a missing or a junk token; history needs a token."),
    ("Analysis and history", "test_api", ["test_analyze_anonymous_not_persisted", "test_analyze_persists_and_history_roundtrip", "test_history_is_private_per_user",
                                          "test_no_face_returns_200_with_empty_result", "test_missing_file_field_is_422", "test_non_image_upload_is_unhandled_500"],
     "An anonymous analysis returns 7 + 11 sorted scores and is not stored; a signed-in one is stored with a thumbnail, listed, read and deleted; another user gets 404; "
     "a flat image returns 200 with `face_detected` false; a missing file field is 422; an undecodable file is HTTP 500 (a characterised defect)."),
]
_all = {n for _, _, ns, _ in _GROUPS for n in ns}
assert len(_all) == T["tests"] == sum(len(ns) for _, _, ns, _ in _GROUPS), (len(_all), T["tests"])
assert _all == {n for _, n in T["cases"]}


def _count(prefix):
    return sum(1 for c, _ in T["cases"] if c == prefix)


def _probe_rows():
    rows = []
    for p in A["probes"]:
        exp = "/".join(str(e) for e in p["expected"])
        note = "as expected"
        if p["status"] == 500:
            note = "DEFECT: unhandled exception"
        elif "not-an-email" in p["name"]:
            note = "DEFECT: e-mail not validated"
        elif "limit=-5" in p["name"]:
            note = "accepted (SQLite treats a negative limit as no limit)"
        elif "6000x6000" in p["name"]:
            note = "accepted: no size limit"
        rows.append([p["name"], exp, str(p["status"]), note])
    return rows


def _lat_rows():
    return [[l["label"], str(l["n"]), f"{l['p50_ms']:.1f}", f"{l['p95_ms']:.1f}", f"{l['max_ms']:.1f}"] for l in A["latency"]]


def _lat(label_part):
    return next(l for l in A["latency"] if label_part in l["label"])


def pc(x, d=1):
    return f"{x * 100:.{d}f} %"


def blocks():
    n_def = sum(1 for p in A["probes"] if p["status"] == 500)
    la, lp, ln, lh, lg, ll = (_lat("anonymous"), _lat("authenticated"), _lat("no face"), _lat("health"), _lat("2000x1500"), _lat("login"))
    b = [H1("7. SYSTEM TESTING")]

    # ------------------------------------------------------------------ 7.1
    b += [H2("7.1 Testing strategy"),
          P("Mosaic was handed over without any automated test. The documentation run added four kinds of evidence, each answering a different question. (1) A pytest suite in `backend/tests` checks the code in isolation and through "
            f"FastAPI's `TestClient` against a temporary SQLite database ({T['tests']} tests). (2) `scripts/measure_api.py` sends {A['probes_total']} malformed or hostile requests to the running service over real HTTP and times the main endpoints. "
            "(3) `scripts/run_experiments.py` measures the model itself (Chapter 8), including a face-detector study and a seeded ablation. (4) `scripts/capture_screens.py` drives the production build of the Next.js console in Chrome with real "
            "FER2013 faces and photographs every screen."),
          P("The strategy follows the risk in the design. The model cannot be unit-tested for 'correct emotion', because the data has no compound ground truth, so model quality is treated as a measurement (Chapter 8) and testing concentrates on what "
            "can be checked exactly: label bookkeeping, tensor shapes, authentication, access control, the request/response contract and behaviour on bad input. Where a test exposed a defect the product was **not** changed; the test "
            "was written to describe the behaviour that exists (a *characterisation test*) and the defect is listed in Section 7.7 and in Chapter 8."),
          TAB("Test activities and where their evidence is recorded.",
              ["Activity", "Tool and location", "Volume", "Section"],
              [["Unit tests", "pytest, `backend/tests/test_units.py`", f"{_count('test_units')} tests", "7.3"],
               ["Integration tests (API + database + model)", "pytest + TestClient, `backend/tests/test_api.py`", f"{_count('test_api')} tests", "7.4"],
               ["Functional walk-through of the console", "Playwright + Chrome, `scripts/capture_screens.py`", "19 screen captures", "7.5"],
               ["Security and abuse probes", "`scripts/measure_api.py`", f"{A['probes_total']} probes", "7.6"],
               ["Validation and edge cases", "`scripts/run_experiments.py eval` (Haar study), probes", f"{D['n_images']:,} faces per scale", "7.7"],
               ["Performance", "`scripts/measure_api.py`", f"{len(A['latency'])} request types, 10-100 calls each", "7.8"]],
              widths=[1.9, 2.6, 1.3, 0.7], align=["l", "l", "l", "c"], size=10)]

    # ------------------------------------------------------------------ 7.2
    b += [H2("7.2 Test environment"),
          P("All tests ran on one Windows 11 Pro machine with an Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB of RAM and no GPU. Python was 3.11.9. The backend ran in a virtual environment that inherits the system packages "
            "(PyTorch 2.14.1 CPU, FastAPI 0.143.3, Pydantic 2.14.1, OpenCV 4.11, pytest 8.2.0) and pins `bcrypt==4.0.1`; these are newer than the versions in `requirements.txt` "
            "(FastAPI 0.115.0, PyTorch 2.4.1), so the suite doubles as a check that the code runs on current libraries. The pin on bcrypt matters: with the system's bcrypt 5.0.0 the first test run failed with five errors, because "
            "passlib 1.7.4 cannot hash with bcrypt 5. The front end was the production build (`next build`, then `next start` on port 3000) of Next.js 16.3.6, pointed at the API on port 8116 because port 8000 was occupied by another program."),
          P("Other programs kept the processor busy during the measurements, so every timing in Section 7.8 is an upper bound on what an idle machine would give. The checkpoint under test is `classifier_final.pt`, trained during "
            "the documentation run with the unchanged training script (it was missing from the delivered folder).")]

    # ------------------------------------------------------------------ 7.3
    rows = [[g, f"`{f}.py`", str(len(ns)), desc] for g, f, ns, desc in _GROUPS if f == "test_units"]
    b += [H2("7.3 Unit testing"),
          P(f"`test_units.py` holds {_count('test_units')} tests. They need no network, no database and (apart from one that builds a random generator) no trained weights, and they ran in a fraction of a second."),
          TAB("Unit tests by area.", ["Area", "File", "Tests", "What is checked"], rows, widths=[1.3, 1.1, 0.6, 3.6], align=["l", "l", "c", "l"], size=9.5),
          P("Two of these deserve a comment. The class-weight test confirms the inverse-frequency rule used by the stage-1 trainer: with 436 disgust and 7,215 happy training faces the weight of disgust is about "
            f"{F.DATA['n_train'] / (7 * F.DATA['class_counts']['train']['disgust']):.1f}, against {F.DATA['n_train'] / (7 * F.DATA['class_counts']['train']['happy']):.2f} for happy. "
            "The synthesis test pins down the labelling convention of the whole method: a synthetic 'happily surprised' face is trained with three positive outputs (happy, surprise and happily surprised), exactly as the base paper "
            f"[{C['base']}] gives each generated image two basic labels, with Mosaic adding a third bit for the compound class.")]

    # ------------------------------------------------------------------ 7.4
    rows = [[g, f"`{f}.py`", str(len(ns)), desc] for g, f, ns, desc in _GROUPS if f == "test_api"]
    b += [H2("7.4 Integration testing"),
          P(f"`test_api.py` holds {_count('test_api')} tests that start the real FastAPI application (including the start-up hook that loads the checkpoint) and replace only the database with a temporary file. They therefore exercise routers, dependencies, JWT handling, "
            "the ORM, the Haar detector, the CNN, the thumbnail writer and the pydantic response models together. The face fixture is a real FER2013 test image enlarged threefold, because the detector cannot see a native 48-pixel face (Section 7.7)."),
          TAB("Integration tests by area.", ["Area", "File", "Tests", "What is checked"], rows, widths=[1.3, 1.1, 0.6, 3.6], align=["l", "l", "c", "l"], size=9.5),
          P(f"All {T['tests']} tests passed in {T['seconds']:.1f} s ({T['failures']} failures, {T['errors']} errors, {T['skipped']} skipped). Two of them pass *because* the product misbehaves: `test_no_face_returns_200_with_empty_result` "
            "records that `API_CONTRACT.md` promises HTTP 422 for an image without a face while the code answers 200 with `face_detected: false`, and `test_non_image_upload_is_unhandled_500` records that an undecodable upload ends in an internal server error. "
            "If either defect is fixed, the corresponding test must be updated deliberately."),
          H3("7.4.1 A defect found by the first run"),
          P("The first execution of the suite used the system's bcrypt 5.0.0 and produced five failures (password hashing and every test that registers a user). The cause is the known incompatibility between passlib 1.7.4 and bcrypt 5. "
            "`requirements.txt` already pins `bcrypt==4.0.1` for this reason; the failure is therefore a reminder that the pin is load-bearing, not a code defect.")]

    # ------------------------------------------------------------------ 7.5
    b += [H2("7.5 Functional testing: a walk-through with real data"),
          P("The functional check is a scripted walk-through of the production console. The script registers a user, then uploads seven real FER2013 test faces (one per basic class, enlarged fivefold so that the Haar detector can find them) and two faces "
            "generated by the project's own cEmoGAN, uploads an un-enlarged 48-pixel face to provoke the no-face path, opens the history list and one history entry, and finally opens the Webcam tab. "
            "Every screen was captured at 1440 x 900 (Chapter 8 shows the key ones, Appendix C the rest)."),
          TAB("Functional test cases and observed behaviour.",
              ["No.", "Case", "Expected", "Observed"],
              [["F1", "Open the landing page", "Hero, features and how-it-works sections render", "Passed (screens 01-03)"],
               ["F2", "Register with name, e-mail, password", "Account created, redirect to `/app`", "Passed (screens 05-07)"],
               ["F3", "Log-in page renders", "E-mail and password fields", "Passed (screen 04)"],
               ["F4", "Upload a face photo", "Dominant card, basic chart, compound rows", "Passed for 7 of 7 basic-class faces and 2 of 2 generated faces (screens 08-15)"],
               ["F5", "Dominant label matches the face", "Same as the dataset label", "4 of the 7 real faces (happy, sad, angry, fear); neutral -> Fear, disgust -> Angry, surprise -> Fear. A sample of seven, not a statistic"],
               ["F6", "Face thumbnail on the result card", "Cropped face next to the label", "FAILED: broken image icon with alt text (the relative `/api/media/thumbs/...` URL resolves against the UI origin)"],
               ["F7", "Image without a detectable face", "Clear message", "Passed: 'No face was detected in that image' (screen 16)"],
               ["F8", "History list", "One row per analysis, newest first", "Passed (screen 17)"],
               ["F9", "Open a history entry", "Reachable from the list", "FAILED as a user path: the route exists but nothing links to it; opened by typing its address (screen 18)"],
               ["F10", "Webcam capture", "Camera frame analysed", "Not exercised: the headless browser has no camera; only the tab was opened (screen 19)"],
               ["F11", "Reload a protected page", "Stays signed in", "FAILED in development mode (redirect to `/login`); in the production build the page also redirected when opened by address, so the check was done through in-app navigation"],
               ["F12", "Delete a history entry", "Entry removed", "Passed through the API (integration test); not clicked in the UI walk-through"]],
              widths=[0.4, 1.6, 1.9, 2.6], align=["c", "l", "l", "l"], size=9),
          P("F6, F9 and F11 are front-end defects. They do not affect any measured number, but a user would notice the broken thumbnail on every result.")]

    # ------------------------------------------------------------------ 7.6
    b += [H2("7.6 Security testing"),
          P(f"`scripts/measure_api.py` sends {A['probes_total']} probes and then checks that the service still answers `/api/health` ({'it did' if A['healthy_after_probes'] else 'it did not'}). The probe table lists the tolerated outcomes; "
            f"for the three undecodable-upload probes and the e-mail probe the tolerated set deliberately included the defective answer, so the headline '{A['probes_ok']} of {A['probes_total']} as expected' means 'no crash and no surprise', not 'no defect'. "
            "The real findings are in the last column."),
          TAB("Probes sent to the running API (127.0.0.1) and what came back.", ["Probe", "Tolerated", "Status", "Verdict"], _probe_rows(), widths=[2.9, 0.9, 0.6, 2.2], align=["l", "c", "c", "l"], size=8.5),
          P("What the probes and the tests establish:"),
          B("**Passwords** are stored as bcrypt hashes and never returned; a SQL-looking e-mail is just an unknown user (401), because all queries go through the ORM.",
            "**Tokens**: a tampered token, an expired token and a token signed with another key are all rejected; a request without a token is rejected on every protected route.",
            "**Isolation**: user B reading or deleting user A's history entry gets 404, and A's history is empty for B.",
            f"**CORS**: the listed origin gets `Access-Control-Allow-Origin: {A['cors_listed_origin_allow_origin_header']}`; an unlisted origin is refused with 400 'Disallowed CORS origin'.",
            "**Path traversal** in the thumbnail route returns 404.",
            "**Weaknesses found**: e-mail addresses are not validated (any string registers); passwords need only six characters; there is no rate limit on login or on analysis; "
            "uploads have no size limit (a 6000 x 6000 JPEG is decoded in full); the JWT secret falls back to a fixed development string when `MOSAIC_SECRET_KEY` is not set; the token is kept in browser local storage; traffic is plain HTTP in development."),
          P("These are findings of a black-box probe and a code reading, not a penetration test. They are acceptable for a local demonstration and would have to be closed before a public deployment.")]

    # ------------------------------------------------------------------ 7.7
    b += [H2("7.7 Validation and edge cases"),
          H3("7.7.1 The face detector on FER2013 faces"),
          P(f"The product looks for a face with OpenCV's Haar cascade (scale factor 1.1, five neighbours, minimum size 40 x 40 pixels) [{C['viola']}]. FER2013 images are 48 x 48 pixels and already cropped, so a face fills almost the whole image and is barely larger than the minimum window. "
            f"On {D['n_images']:,} random test faces the detector found a face in {pc(D['haar_detection_rate_scale_1x'])} of the native images, {pc(D['haar_detection_rate_scale_2x'])} after a bicubic 2x enlargement, "
            f"{pc(D['haar_detection_rate_scale_3x'])} at 3x, {pc(D['haar_detection_rate_scale_4x'])} at 4x and {pc(D['haar_detection_rate_scale_6x'])} at 6x. More than four in ten faces are therefore never classified, whatever the scale, which is a property of the detector on this kind of image "
            "(low resolution, harsh crops, occlusions, strong expressions such as open mouths), not of the CNN."),
          FIG(F.fig("fig_detection.png"), "Haar detection rate against image size (left) and accuracy of the final model on the same faces through the product path and by direct resizing (right).", 5.4),
          P(f"The second panel measures a second effect. On the {D['detected_at_3x']} faces that were detected at 3x, the final classifier is {pc(D['accuracy_direct_64px_on_same_images'])} accurate when the 48-pixel image is simply resized to 64 x 64 (how it was trained) "
            f"but only {pc(D['accuracy_via_haar_crop_on_detected'])} accurate when the product's own path is used (Haar crop of the enlarged image, then resize). The Haar box cuts the face tighter than the dataset's crop, so the network sees a different framing from the one it learned. "
            "This train/serve mismatch costs about ten points of accuracy and is not visible in any number the training script prints."),
          H3("7.7.2 Other edge cases"),
          B("**No face**: the service answers 200 with `face_detected: false`, empty lists and `dominant: null`; for a signed-in user a history row is still written (without a thumbnail), so history lists such rows as 'No face detected'.",
            f"**Undecodable input**: a text file, an empty file and a truncated JPEG each end in HTTP 500 ({n_def} probes), because Pillow's exception is not caught.",
            "**Large input**: a 2000 x 1500 JPEG with no face takes about "
            f"{lg['p50_ms']:.0f} ms; a 6000 x 6000 JPEG is accepted.",
            "**Several faces**: only the largest detected box is analysed; the others are ignored (by design in `face.py`).",
            "**Model file missing**: `/api/health` reports `model_loaded: false` and an analysis that finds a face raises `FileNotFoundError` (HTTP 500); this is exactly the state the delivered folder was in.",
            "**Unused parameter**: `analyze_image_bytes` accepts a `threshold` argument that is never read."),
          ]

    # ------------------------------------------------------------------ 7.8
    b += [H2("7.8 Performance testing"),
          P("Latency was measured over real HTTP on 127.0.0.1 (the name `localhost` adds about two seconds per call on this machine because of an IPv6 fall-back). Each endpoint was called 10-100 times in sequence by a single client; "
            "there was no concurrent load, so these are service times, not capacity figures."),
          TAB("Latency of the Mosaic API (milliseconds).", ["Request", "n", "p50", "p95", "max"], _lat_rows(), widths=[3.4, 0.5, 0.7, 0.7, 0.7], align=["l", "c", "r", "r", "r"], size=9.5),
          FIG(F.fig("fig_latency.png"), "Median and 95th-percentile latency of each measured request (log scale).", 5.2),
          P(f"Classification is cheap: an anonymous analysis of a face takes {la['p50_ms']:.1f} ms at the median, and {lp['p50_ms']:.1f} ms when the user is signed in, the extra {lp['p50_ms'] - la['p50_ms']:.1f} ms being the database insert, the thumbnail write and the update. "
            f"A photo without a face is answered in {ln['p50_ms']:.1f} ms because the CNN is skipped, and the largest image tested ({lg['p50_ms']:.0f} ms) is dominated by decoding. Login costs {ll['p50_ms']:.0f} ms, which is bcrypt's deliberate work factor. "
            f"Health and `/me` take under {max(lh['p50_ms'], _lat('/me')['p50_ms']) + 1:.0f} ms. Model start-up (loading a {F.FIN['parameters']:,}-parameter network) happens once, when uvicorn starts."),
          P("Training cost is a different matter: on this CPU one 5-epoch classifier run took 8-9 minutes when the machine was shared "
            f"(mean {sum(v['config']['minutes'] for v in F.ABL.values()) / len(F.ABL):.1f} minutes over {len(F.ABL)} runs), and the shipped final-stage run took 10 minutes 37 seconds.")]

    # ------------------------------------------------------------------ 7.9
    b += [H2("7.9 User acceptance"),
          P("No user-acceptance test with real users was carried out. There was no pilot group, no questionnaire and no usability session, and no claim about satisfaction or usability is made anywhere in this report. "
            "The nearest substitute is the scripted walk-through of Section 7.5, which shows that a new user can register, upload a photo and read a result without any step that the interface does not offer, with the exceptions listed there.")]

    # ------------------------------------------------------------------ 7.10
    b += [H2("7.10 The limits of the testing done"),
          B("**One machine, one browser, one session**: Windows 11, Chrome (headless, 1440 x 900), a single sequential client. No mobile or tablet layouts, no other browsers, no accessibility audit.",
            "**No load or soak test**: concurrency, memory growth and SQLite locking under many users were not measured.",
            "**Front end**: there are no component or end-to-end test files in the repository; the evidence is the successful TypeScript compile in `next build` and the screen walk-through.",
            "**Webcam path** untested (no camera); the same upload route would be used, with a JPEG captured from the video element.",
            "**Model correctness** is measured, not tested: the 7,178 FER2013 test faces carry basic labels only, so the compound outputs have no real ground truth (Chapter 8).",
            "**Test data is the training distribution**: every face used in a test or screenshot comes from FER2013 or from the project's own generator; no photograph of a person outside the dataset was used.",
            "**Characterisation tests freeze defects**: two of the 28 tests pass only while two known defects remain.")]
    return b
