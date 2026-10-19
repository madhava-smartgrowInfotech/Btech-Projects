"""Chapter 7: System testing. Counts are read from experiments/test_run.json (written by scripts/run_all_tests.py)."""

from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import n
from . import facts as F


def _t():
    t = F.TESTS or {}
    return t


def blocks():
    t = _t()
    py = t.get("pytest", {})
    sm = t.get("smoke", {})
    ui = t.get("ui", {})
    per = py.get("per_file", {})
    total = py.get("passed", 0)
    lat = F.API_LAT or {}
    e = F.DEPLOYED or {}
    lm = e.get("latency_ms_mean_cpu", {})
    out = [
        H1("CHAPTER 7: SYSTEM TESTING"),
        H2("7.1 Testing strategy"),
        P("Testing follows the structure of the system. Small, deterministic functions are covered by unit tests; the API is exercised end to end with the real model, a throw-away "
          "database and throw-away image folders; the original Flask pages have functional tests; the running stack is checked by a smoke test and by browser-driven "
          "verification of the interface. Every test starts from a clean temporary database, so tests cannot affect each other or the real history."),
        TAB("Test layers", ["Layer", "Tool", "What it checks", "Count"], [
            ["Unit", "pytest", "Preprocessing, network builder, Grad-CAM, database layer, session tokens", f"{per.get('tests/test_preprocess.py', 0) + per.get('tests/test_model_gradcam.py', 0) + per.get('tests/test_database.py', 0) + per.get('tests/test_auth_tokens.py', 0)}"],
            ["Integration", "pytest + FastAPI TestClient", "Authentication, validation, prediction, history, statistics, file serving through the real model", f"{per.get('tests/test_api.py', 0)}"],
            ["Functional (original UI)", "pytest + Flask test client", "Upload form, result page, history, error messages", f"{per.get('tests/test_flask_app.py', 0)}"],
            ["System smoke", "scripts/smoke_test.py (standard library only)", "The running servers: login, 401s, validation, four real predictions, images, history, statistics, 404, delete, logout", f"{sm.get('checks', 0)} checks"],
            ["User interface", "scripts/verify_ui.py (Playwright)", "Overflow and console errors at 360, 768 and 1440 px in light and dark; drawer, dialog, focus, theme persistence, reduced motion", f"{ui.get('configurations', 0)} configurations"],
        ], widths=[1.3, 1.6, 2.7, 0.8], size=9.5, align=["l", "l", "l", "c"]),
        P(f"The automated suite contains **{total} pytest tests**, all of which passed in the final run ({py.get('seconds', 0):.0f} s)." if py else ""),
        H2("7.2 Unit tests"),
        TAB("Unit tests", ["File", "Tests", "Examples"], [
            ["`tests/test_preprocess.py`", per.get("tests/test_preprocess.py", 0), "Output is 224 x 224 x 3 float32 in [0, 1]; channels identical; bytes and path give the same tensor; CLAHE raises the contrast of a flat image; unreadable input raises `ValueError`"],
            ["`tests/test_model_gradcam.py`", per.get("tests/test_model_gradcam.py", 0), "Network output is a probability vector; last convolution layer found; Grad-CAM map normalised to [0, 1]; overlay keeps size and dtype; alpha 0 returns the original"],
            ["`tests/test_database.py`", per.get("tests/test_database.py", 0), "Initialisation is idempotent; ids increment; round trip of a record; newest-first order; limit; schema columns"],
            ["`tests/test_auth_tokens.py`", per.get("tests/test_auth_tokens.py", 0), "Token round trip; tampered payload; tampered signature; expired token; malformed tokens"],
        ], widths=[1.9, 0.6, 3.8], size=9.5, align=["l", "c", "l"]),
        H2("7.3 Integration tests"),
        P(f"`tests/test_api.py` ({per.get('tests/test_api.py', 0)} tests) drives the FastAPI application in-process. It signs in, uploads the three public sample radiographs and checks the complete "
          "record: probabilities for the three classes sum to one, the label is the arg-max, the confidence equals the largest probability, both image URLs are served as images, the same "
          "image gives the same probabilities twice, uppercase `.PNG` uploads are accepted, history is newest first, statistics agree with history, and deleting a scan removes it."),
        H2("7.4 Functional tests"),
        P(f"`tests/test_flask_app.py` ({per.get('tests/test_flask_app.py', 0)} tests) covers the original interface: the home page has the upload field, about and history render, an unknown result "
          "redirects home, a post without a file shows \"No file part\", a `.gif` is rejected, a valid upload redirects to a result page that shows the prediction and the Grad-CAM image and then appears in "
          "the history, and an oversize body is refused with 413."),
        P(f"`scripts/smoke_test.py` runs {sm.get('checks', 0)} checks against the live servers (through the Vite proxy when given the front-end address) and `scripts/capture_screens.py` walks every screen "
          "with real uploads, failing on any console error or HTTP 4xx/5xx; its output is the set of screenshots in Chapter 8."),
        H2("7.5 Security tests"),
        TAB("Security checks", ["Check", "Expected", "Test"], [
            ["Protected routes without a session (6 routes)", "401", "`test_protected_routes_need_a_session`"],
            ["Forged cookie `abc.def`", "401", "`test_forged_cookie_is_rejected`"],
            ["Tampered payload or signature, expired token", "Rejected", "`tests/test_auth_tokens.py`"],
            ["Wrong password, wrong email", "401", "`test_login_rejects_*`"],
            ["Session cookie attributes", "HttpOnly present", "`test_login_sets_httponly_cookie`"],
            ["Path traversal (`..%2Fapp.py`, `..%5Capp.py`), unknown folder, missing file", "404", "`test_files_route_blocks_missing_and_traversal`"],
            ["Corrupt image", "400 and the saved file removed", "`test_predict_rejects_corrupt_image_and_cleans_up`"],
            ["Upload larger than 8 MB", "413", "`test_predict_rejects_oversize_upload`"],
        ], widths=[2.8, 1.5, 2.0], size=9.5),
        H2("7.6 Validation and edge cases"),
        B("No file part, empty file name, extension missing, extension not allowed (`.gif`), uppercase extension.",
          "Unreadable image content with a valid extension.",
          "Eight-megabyte boundary: the server reads at most 8 MB + 1 byte before deciding.",
          "`limit=0` on the history route is clamped to one record.",
          "Unknown prediction id on read and on delete returns JSON 404, and the interface shows a not-found state.",
          "Statistics on an empty history return zero totals, a null average confidence and a seven-day series of zeros.",
          "Same image twice gives the same probabilities (deterministic inference)."),
        H2("7.7 Performance testing"),
    ]
    if lm:
        out += [
            P(f"Latency was measured on the development machine (Intel Core i5-12500, no GPU) for the deployed model. Over {lm.get('images_timed', 60)} test images, one image at a time, "
              f"preprocessing takes {lm['preprocess']:.0f} ms on average, the network forward pass {lm['predict']:.0f} ms and Grad-CAM with the overlay "
              f"{lm['gradcam_overlay']:.0f} ms, so the model-side pipeline takes about {lm['total_pipeline']:.0f} ms per image. These are means over 60 images after three warm-up calls."),
        ]
    if lat:
        out += [
            P(f"The end-to-end time of `POST /api/predict` through the running API (upload, validation, preprocessing, inference, Grad-CAM, two file writes and a database insert) was measured with "
              f"{lat['requests']} requests: mean {lat['mean_ms']:.0f} ms, median {lat['median_ms']:.0f} ms, 95th percentile {lat['p95_ms']:.0f} ms and maximum {lat['max_ms']:.0f} ms. "
              f"Reading the history ({lat['history_calls']} calls) took {lat['history_mean_ms']:.0f} ms on average and a result record {lat['record_mean_ms']:.0f} ms."),
        ]
    out += [
        H2("7.8 User acceptance"),
        P("No formal acceptance test with clinicians or external users was carried out, and this report does not claim one. What was done instead is a requirements walk-through: "
          "every functional requirement of Section 4.3 was exercised by an automated check or by the screenshot walk, and the traceability is summarised below."),
        TAB("Requirement traceability", ["Requirement", "Evidence"], [
            ["FR1 sign in / out", "`test_login_*`, `test_logout_clears_session`, screen 03"],
            ["FR2, FR3 upload and validation", "`test_predict_rejects_*`, client-side checks on screens 04 and 05"],
            ["FR4 preview", "Screen 05"],
            ["FR5, FR6 classification and Grad-CAM", "`test_predict_returns_a_complete_record`, `test_gradcam_*`, screen 06"],
            ["FR7 result display", "Screens 06, 07, 08"],
            ["FR8 storage", "`test_predict_saves_both_images_and_serves_them`, `test_history_*`"],
            ["FR9, FR10 history and export", "Screen 11, smoke test"],
            ["FR11 delete", "`test_delete_removes_the_record`, dialog check in `verify_ui.py`"],
            ["FR12 dashboard", "`test_stats_*`, screens 09 and 10"],
            ["FR13 print and download", "Result screen actions (print stylesheet; download link)"],
            ["FR14 Demo Mode warning", "Present when no trained weights exist (shown in the first release of the interface)"],
            ["FR15 not found", "`test_unknown_prediction_is_404_json`, screen 13"],
            ["FR16, FR17 about and disclaimer", "Screens 01 and 12"],
            ["FR18 themes", "Theme persistence check in `verify_ui.py`; screens 02, 08, 10"],
        ], widths=[2.3, 4.0], size=9.5),
        H2("7.9 Limits of the testing done"),
        B("The tests prove that the software behaves as specified, not that the model is clinically useful; model quality is measured separately in Chapter 8 and only on one public data source.",
          "There is no load or concurrency test beyond the single-inference lock, and no long-running soak test.",
          "The user-interface checks run in one browser engine (Chromium); other browsers and assistive technologies were not tested.",
          "No penetration test or dependency audit was performed; the security tests cover the controls listed in Section 6.9 only.",
          "The tests run on Windows with the development Python environment; the freshly built `.venv` from `requirements.txt` was verified with the smoke test, not with the full pytest suite."),
    ]
    return out
