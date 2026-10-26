"""Chapter 7: System Testing (VeriVision AI). Facts: tests/test_verivision.py, tests/test_api.py, scripts/smoke_test.py,
docs/metrics/{tests,latency,edge_cases}.json."""

import json
import os

from . import facts as F
from .blocks import B, H1, H2, H3, P, TAB


def _edge():
    path = os.path.join(F.METRICS_DIR, "edge_cases.json")
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else None


def _ms(key, sub="median"):
    v = F.LATENCY.get(key, {}).get(sub)
    return "n/a" if v is None else f"{v * 1000:,.0f} ms"


def _s(key, sub="median"):
    v = F.LATENCY.get(key, {}).get(sub)
    return "n/a" if v is None else f"{v:.2f} s"


def _edge_rows():
    e = _edge()
    if not e:
        return []
    rows = []
    for r in e["cases"]:
        if r["status"] == 200:
            res = f"Analysed: {r['verdict']} ({r['confidence_pct']:.1f} %), robustness {r['consistency']}, Grad-CAM {'ok' if r['cams_ok'] else 'missing'}"
        else:
            res = (r.get("error") or "").strip() or "refused"
        rows.append([r["case"], str(r["status"]), res])
    return rows


def blocks():
    pt, pp, ps = F.PYTEST_TOTAL, F.PYTEST_PASSED, F.PYTEST_SECONDS
    st, sp = F.SMOKE_TOTAL, F.SMOKE_PASSED
    out = [
        H1("CHAPTER 7: SYSTEM TESTING"),
        P("This chapter describes how VeriVision AI was tested, what each test really asserts, and what the testing does not cover. Model quality (accuracy, robustness, transfer) is measured on "
          "held-out data and is reported in Chapter 8; this chapter is about whether the software around the models behaves correctly."),

        H2("7.1 Testing Strategy"),
        P(f"Three layers of automated testing were used. The first is a pytest suite of {pt} tests ({pp} passed in {ps:.0f} s on the development PC) that checks the pure logic (upload validation, weight "
          "normalisation, logit fusion and the two gates) and the Flask routes through the test client. The second is an end-to-end smoke script, scripts/smoke_test.py, that runs against the live API "
          f"and the Vite proxy with the real trained models and passed {sp} of {st} checks. The third is a browser walk-through, scripts/capture_screens.py, which drives every screen in Chrome with real "
          "data and records the console and network errors; it finished with none. A small script, scripts/edge_cases.py, was added for this report to exercise unusual uploads and the security checks "
          "against the real models."),
        P("A test passes when the observed status code, response fields or numerical result equal the expected ones; there are no tolerance bands except for floating-point comparisons. The pytest suite "
          "does not need trained models: the one test that runs the full prediction path builds the four architectures with random weights, so it checks the structure of the response and not the quality of the verdict."),
        TAB("Testing environment", ["Item", "Value"], [
            ["Machine", "Intel Core i5-12500 (6 cores / 12 threads), 15.7 GB memory, no GPU, Windows 11"],
            ["Software", "Python 3.11.9, PyTorch 2.14.1 (CPU), torchvision 0.29.1, Flask 3.1.3, pytest 9.1.1, Node 24 for the front end"],
            ["Models under test", "The four CIFAKE-trained checkpoints installed in models/"],
            ["Servers (smoke test)", f"API on 127.0.0.1:{F.API_PORT}, Vite proxy on {F.WEB_PORT}"],
        ], widths=[1.6, 4.7], size=9.5, align=["l", "l"]),

        H2("7.2 Unit Testing"),
        P("tests/test_verivision.py holds nine unit tests of the logic and two route tests. Each test builds its own inputs, so the gates and the fusion are tested with hand-chosen logits whose "
          "correct outcome can be worked out on paper."),
        TAB("Unit tests of the application logic", ["ID", "Test", "What it asserts", "Result"], [
            ["U1", "preprocessing: valid image", "A 64 x 64 PNG decodes to an RGB image of the same size; 'photo.JPG' has an allowed extension", "Pass"],
            ["U2", "preprocessing: unsupported and corrupt", "'notes.txt' and a name without extension are not allowed; validate_upload and decode_image raise PreprocessingError for a .txt upload and for bytes that are not an image", "Pass"],
            ["U3", "weight normalisation", "The default weights sum to 1; the weights 7 and 3 become 0.7 and 0.3", "Pass"],
            ["U4", "logit fusion uses the weights", "Equal logits stay unchanged under equal weights; with weights 0.75 / 0.25 the fused value is 3.0", "Pass"],
            ["U5", "Gate 1 excludes an outlier", "B at (0, 5) against three routes pointing REAL: B is excluded and removed from the active weights", "Pass"],
            ["U6", "Gate 1 keeps an agreeing B", "When all four routes agree, nothing is excluded and all four weights stay", "Pass"],
            ["U7", "Gate 2 corrects", "Fused logits (4, 0) pointing REAL while B and C strongly say fake: the correction is applied and the fake logit rises", "Pass"],
            ["U8", "Gate 2 without consensus", "When C disagrees with B, the logits are returned unchanged and applied is false", "Pass"],
            ["U9", "response structure", "With random-weight fixture checkpoints the full prediction returns a valid label, probabilities in [0, 1] that sum to 1, and a label for each of the four routes", "Pass"],
            ["U10", "health route", "GET /health returns 200 or 503 and a status field", "Pass"],
            ["U11", "classic predict route, bad file", "POST /predict with a .txt upload returns 400 (or 503 if models are missing)", "Pass"],
        ], widths=[0.4, 1.5, 3.8, 0.6], size=9, align=["c", "l", "l", "c"]),

        H2("7.3 Integration Testing"),
        P("tests/test_api.py tests the JSON API that the React application uses, through the Flask test client, so the blueprints, the token handling, the upload guards and the error handler are exercised together."),
        TAB("Integration tests of the JSON API", ["ID", "Test", "What it asserts", "Result"], [
            ["I1", "wrong password", "POST /api/auth/login with a wrong password returns 401 and an error message", "Pass"],
            ["I2", "missing body", "Login with no JSON body returns 401", "Pass"],
            ["I3", "login and /auth/me", "The demo login returns a token; /auth/me with it returns the demo e-mail; without a token or with 'Bearer garbage' it returns 401", "Pass"],
            ["I4", "config describes the ensemble", "/api/config lists the routes a1, a2, b, c in order, the upload limit and the three gate settings", "Pass"],
            ["I5", "insights shape", "/api/insights has available and confusion_exists; when available, accuracy lies in [0, 1]", "Pass"],
            ["I6", "analyze requires login", "POST /api/analyze without a token returns 401", "Pass"],
            ["I7", "bad upload", "A .txt upload with a valid token returns 400 (or 503) with a JSON error", "Pass"],
            ["I8", "oversize upload", "A body of 10 MB + 1 KB returns 413 with a JSON message that mentions MB", "Pass"],
        ], widths=[0.4, 1.5, 3.8, 0.6], size=9, align=["c", "l", "l", "c"]),
        P("The integration of the front end with the API was tested by the smoke script, which also requests /health and /api/config through the Vite proxy on port " + str(F.WEB_PORT) + " and checks that the application shell is served."),

        H2("7.4 Functional Testing"),
        P(f"The smoke test covers the main user flow with the real models and the real front-end proxy. Its {st} checks fall into six groups, and all {sp} passed."),
        TAB("Groups of the smoke test (scripts/smoke_test.py)", ["Group", "Checks", "Examples of what is verified"], [
            ["Health and public JSON", "5", "Models loaded; four routes and upload limits in /api/config; demo account exposed; insights contain ensemble, model and robustness metrics; confusion matrix served"],
            ["Authentication", "4", "Wrong password gives 401; demo login returns a token; the token resolves to the demo user; analyze without a token gives 401"],
            ["Main flow, run for one AI-generated and one real test image", "12", "Status 200; verdict and probabilities consistent (sum to 1); four votes with active weights summing to 1; Grad-CAM overlays for a1, b and c; robustness outcomes for original, jpeg, resize and blur with a consistency string; original image echoed back"],
            ["Validation errors", "3", "Unsupported type gives 400 'Unsupported'; corrupt PNG gives 400 'decoded'; no file gives 400"],
            ["Original surface", "3", "/api/predict keeps its JSON contract; classic pages / and /insights render; classic /predict still shows its error page"],
            ["Front end and proxy", "2", "The shell with the root element is served; /health and /api/config work through the proxy"],
        ], widths=[1.7, 0.6, 4.0], size=9, align=["l", "c", "l"]),
        P("These are functional tests of behaviour, not of accuracy: the smoke test confirms that a verdict is produced and is well-formed, not that it is correct. The two test images are the first fake and the "
          "first real file of the test folder."),

        H2("7.5 Security Testing"),
        P("The security checks that exist are the ones in the pytest and smoke suites plus those added in scripts/edge_cases.py. They confirm that analysis cannot be reached without a valid token, that a token with "
          "an altered signature is refused, that a wrong password is refused (the code gives the same message for a wrong e-mail, which no test separately checks), that unsupported extensions, empty and undecodable files and over-size bodies are "
          "refused before inference, and that errors are returned as JSON without a stack trace. No penetration test, fuzzing, dependency audit or test of the default secret key was done, and the demo account "
          "and its password are deliberately exposed by /api/config (Section 6.11)."),
    ]
    rows = _edge_rows()
    e = _edge()
    out += [H2("7.6 Validation and Edge Cases")]
    if rows:
        det = e["determinism"]
        out += [
            P("Unusual uploads were sent to POST /api/analyze with the demo token and the real models through the Flask test client. The table gives the HTTP status and what the application answered."),
            TAB("Edge-case uploads to /api/analyze", ["Case", "Status", "Result"], rows, widths=[2.4, 0.6, 3.3], size=8.5, align=["l", "c", "l"]),
            P("The same image sent twice returned " + ("an identical" if det["same_image_twice_identical_probability"] else "a different") + f" fused probability ({det['prob_fake_first']:.6f} and {det['prob_fake_second']:.6f}), "
              "so the analysis is deterministic. Grayscale, transparent and WebP images are converted to RGB before inference, and the file type is decided by the content of the file and by the extension together: "
              "the extension must be on the allowed list, but the bytes are decoded by their real format. The images in the table that are random noise (grayscale, RGBA, WebP and 8 x 8) have no real-world "
              "origin, so their verdicts mean nothing; they are included because they show the robustness check at work. The grayscale noise image was called REAL with 100.0 % confidence but kept that verdict in only "
              "one of the four variants (consistency 1/4), which is the situation the check is meant to expose: a high confidence does not mean a stable answer.")]
    else:
        out += [P("Edge-case results were not recorded in this build.")]
    out += [
        H2("7.7 Performance Testing"),
        P("Response times were measured against the running API on 127.0.0.1 with scripts/measure_latency.py, eight runs per endpoint, on an otherwise idle machine after the models had loaded. "
          "(The address 127.0.0.1 is used because on this PC the name localhost adds about two seconds through an IPv6 fall-back.)"),
        TAB("Response times of the API (median of 8 runs; minimum to maximum)", ["Endpoint and input", "Median", "Minimum", "Maximum"], [
            ["GET /health", _ms("health"), _ms("health", "min"), _ms("health", "max")],
            ["GET /api/insights", _ms("insights"), _ms("insights", "min"), _ms("insights", "max")],
            ["POST /api/predict, 32 x 32 image (four routes and fusion)", _s("predict_cifake_32px"), _s("predict_cifake_32px", "min"), _s("predict_cifake_32px", "max")],
            ["POST /api/predict, 1,024 x 1,024 image", _s("predict_photo_1024px"), _s("predict_photo_1024px", "min"), _s("predict_photo_1024px", "max")],
            ["POST /api/analyze, 32 x 32 image (adds Grad-CAM and robustness)", _s("analyze_cifake_32px"), _s("analyze_cifake_32px", "min"), _s("analyze_cifake_32px", "max")],
            ["POST /api/analyze, 1,024 x 1,024 image", _s("analyze_photo_1024px"), _s("analyze_photo_1024px", "min"), _s("analyze_photo_1024px", "max")],
        ], widths=[3.4, 0.9, 0.9, 1.1], size=9, align=["l", "c", "c", "c"]),
        P("The full analysis takes about two seconds on this CPU, of which the four-route prediction is about a quarter of a second; the rest is the three Grad-CAM overlays and the three re-runs of the prediction for "
          "the robustness check. Image size matters little because every image is resized to 224 or 320 pixels first. In the offline evaluation, batched inference of all four routes took "
          f"{F.M.get('inference_seconds_per_image_batched', 0) * 1000:.0f} ms per image. Model loading happens once at start and was not timed. The earlier README estimate of 10 to 60 s per image was pessimistic for this machine."),

        H2("7.8 User Acceptance Testing"),
        P("No user study was carried out: no participant outside the project team used the application, and no usability score, task-completion time or satisfaction rating was collected. What was done is a "
          "walk-through by the team of every screen with real data (the 19 screenshots in Chapter 8 and Appendix C were captured this way), checking that the pages load, the demo login works, an upload "
          "produces a result, the heat-map tabs switch, and the page works in the light and the dark theme. This shows that the flow is complete, not that users understand or trust the verdict."),

        H2("7.9 Summary of Results and Findings"),
        TAB("Summary of the test runs", ["Suite", "Run", "Passed", "Notes"], [
            ["pytest (tests/test_verivision.py, tests/test_api.py)", str(pt), str(pp), f"{ps:.0f} s; 11 + 8 tests; random-weight fixtures for the prediction path"],
            ["Smoke test (scripts/smoke_test.py)", str(st), str(sp), "Live API, real models, Vite proxy"],
            ["Edge-case script (scripts/edge_cases.py)", str(len(e["cases"]) + 1) if e else "n/a", str(len(e["cases"]) + 1) if e else "n/a", "14 upload cases, the oversize body, 2 token cases and the determinism check; every case behaved as the code specifies"],
            ["Browser walk-through (scripts/capture_screens.py)", "all screens", "all screens", "No console errors and no failed requests"],
        ], widths=[2.4, 0.6, 0.7, 2.6], size=9, align=["l", "c", "c", "l"]),
        P("Four findings come from the testing rather than from the pass counts. First, the pytest suite passes with untrained weights, so it protects the plumbing and would not notice a model that is wrong; "
          "the earlier shipped models, trained on synthetic data, also passed every test while scoring a meaningless 100 %, which is why Chapter 8 relies on a held-out evaluation. Second, the gate unit tests use hand-made "
          "logits that make a gate fire, and they prove that the rules are coded as specified; on the 2,000 real test images Gate 1 fired seven times and Gate 2 never, so the rules that the tests exercise are almost "
          "never exercised in use. Third, confidence is not stability (Section 7.6). Fourth, the full analysis is cheap enough on a CPU (about two seconds) that no queue or background job was needed."),
        TAB("Objectives and the tests that cover them", ["Objective (batch document 6)", "Covered by", "Status"], [
            ["2. Preprocess and augment images", "U1, U2 (validation and decoding); augmentation is exercised by training, not by unit tests", "Partly tested"],
            ["3. Train a CNN classifier", "Held-out evaluation (Chapter 8); pytest only checks the response structure", "Measured, not unit-tested"],
            ["4. Evaluate cross-generator performance", "Cross-domain probe (Chapter 8); no software test", "Measured; not achieved"],
            ["5. Apply Grad-CAM", "Smoke test: overlays for a1, b and c present; edge cases: overlays for every analysed image", "Output tested, faithfulness not"],
            ["6. Deploy an interface returning verdict, confidence and explanation", "I1-I8, smoke test main flow, browser walk-through", "Tested"],
        ], widths=[2.3, 3.0, 1.0], size=9, align=["l", "l", "l"]),

        H2("7.10 Limits of the Testing Done"),
        B("The model tests in pytest use random weights; verdict correctness is tested only by the held-out evaluation of Chapter 8, not by unit tests.",
          "There are no unit tests of app/explainability.py and app/robustness.py; they are covered only by the smoke test and the edge cases, which check that overlays and variants are produced, not that a heat map is faithful.",
          "No load or concurrency test was run; the service was exercised by one client at a time, and model loading uses a lock but this was not stress-tested.",
          "No test on a GPU, on Linux or macOS, or inside the Docker containers was recorded.",
          "No adversarial test was made: nothing shows how the models behave against images edited to fool them.",
          "The smoke test uses two images, and the edge-case set is small; they show that the paths work, not that every file in the wild is handled.",
          "No user study was carried out (Section 7.8)."),
    ]
    return out
