"""Chapter 7: System testing. Counts and timings are read from experiments/tests/test_run.json, experiments/api_latency and experiments/cew_ear."""

from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import n
from . import facts as F

FRAME_KEY = "POST frame (real face JPEG 640x480, monitoring on)"
TICK_KEY = "POST tick (simulation, monitoring on)"


def blocks():
    t = F.TESTS or {}
    ut = t.get("unittest", {})
    sm = t.get("web_smoke", {})
    api = F.API_LAT or {}
    fr = api.get(FRAME_KEY, {})
    tk = api.get(TICK_KEY, {})
    hs = api.get("GET /api/history (limit 500)", {})
    hl = api.get("GET /api/health", {})
    cew = F.CEW or {}
    vl = cew.get("latency_ms_vision_process_640x480", {})
    ec = (F.RULES or {}).get("engine_cost", {})
    rob = (F.ROB or {}).get("conditions", [])
    hw = F.HW

    out = [
        H1("CHAPTER 7: SYSTEM TESTING"),
        H2("7.1 Testing strategy"),
        P("Testing follows the structure of the system. The decision logic (`core.py`) is a set of small deterministic functions, so it is covered by unit tests that feed it "
          "scripted measurements and check the verdict. The web layer is exercised end to end by an API smoke test that drives a whole session in temporary storage. The vision "
          "component, which cannot be unit-tested with scripted numbers, is measured on real face images (public CEW data and degraded copies of it) and its behaviour is reported in "
          "Chapter 8. Every automated test uses a throw-away database and settings folder, so a test run never touches the real event history."),
        TAB("Test layers", ["Layer", "Tool", "What it checks", "Count"], [
            ["Unit", "`unittest` (`tests/test_system.py`)", "Eye aspect ratio, head roll, rule engine, calibration, settings bounds, SQLite and CSV, research pipeline", f"{ut.get('tests', 20)} tests"],
            ["Integration", "`scripts/smoke_test.py` (FastAPI `TestClient`)", "Login, 401 and 409 guards, simulation and camera sources, history and CSV export, thresholds, research route", f"{sm.get('checks', 34)} checks"],
            ["Component measurement", "`scripts/measure_cew.py`", "The shipped `Vision` pipeline on 2,423 public face images and on degraded copies", f"{cew.get('images_total', 2423):,} images"],
            ["Rule behaviour", "`scripts/measure_rules.py`", "Warning latency, false warnings and parameter trade-off on scripted streams", "seeded"],
            ["Performance", "`scripts/measure_api.py`", "HTTP latency on 127.0.0.1 with a real face frame", f"{fr.get('n', 150)} frames"],
            ["Earlier records", "`VERIFICATION.md` (23 Sep 2026)", "Tk desktop smoke test, bounded webcam diagnostic, `pip check`", "passed"],
        ], widths=[1.2, 1.9, 2.6, 0.9], size=9.5, align=["l", "l", "l", "c"]),
        P(f"The automated suites contain **{ut.get('tests', 20)} unit tests** and **{sm.get('checks', 34)} smoke checks**; all of them passed in the final run on "
          f"{t.get('run_date', '26 October 2026')} ({ut.get('seconds', 0.574):.2f} s for the unit tests). The measurement scripts are not pass/fail tests: they produce the numbers reported "
          "in Chapter 8, including the unflattering ones."),
        H2("7.2 Unit tests"),
        P("The 20 unit tests live in one file and fall into five groups. Synthetic fixtures are used only to check software behaviour; the tests make no claim about "
          "accuracy on people."),
        TAB("Unit tests by group", ["Group", "Tests", "What they check"], [
            ["Features", "3", "EAR on a known eye shape (0.5) and invariance to scale; degenerate or non-finite eye points raise an error; head-roll units (45 degrees and 0 degrees)"],
            ["Rule engine", "10", "Two-second warm-up before *Normal*; one bad frame cannot warn; sustained closure raises a warning and exactly one alert (cooldown); four unreliable conditions give *Unable to assess* and require re-warm-up; timing gaps and NaN are rejected; blink rate uses a 60-second denominator (12 per minute within one); head tilt warns only together with a low EAR; the alert cooldown survives signal loss; the four simulation scenarios give the expected verdicts; settings bounds"],
            ["Calibration", "2", "A steady open-eye stream gives the threshold 0.216 (0.72 x 0.30); poor-quality frames make calibration fail with an explanatory error"],
            ["Persistence", "1", "A SQLite event round-trips to CSV with its source label; settings save and load; a corrupt settings file falls back to safe defaults"],
            ["Research pipeline", "4", "Subject separation in the held-out split and creation of the artefacts; consent and empty-data rejection; known confusion-matrix counts, precision and false-alarm rate; unknown held-out subject rejected"],
        ], widths=[1.3, 0.6, 4.4], size=9.5, align=["l", "c", "l"]),
        H2("7.3 Integration tests"),
        P(f"`scripts/smoke_test.py` runs {sm.get('checks', 34)} checks against the FastAPI application in-process with a temporary data folder. They are listed below by group; the "
          "camera path is driven with a blank frame (which must be answered with *Poor lighting*) and a corrupt frame (which must be refused), because no person is available to a script. "
          "Real faces are covered by the CEW measurements and by the live-camera screenshot."),
        TAB("API smoke checks by group", ["Group", "Checks", "Examples"], [
            ["Public routes and login", "7", "`/api/health` public; four scenarios in `/api/config`; protected route returns 401; wrong password rejected; token accepted by `/api/auth/me`; default threshold 0.21 and not calibrated"],
            ["Session guards and simulation", "9", "Monitoring without a source returns 409; calibration refused without a camera and in simulation; simulation source set; metrics block present; verdict is one of the three outputs; scenario switch keeps the session; *Missing face* gives *Unable to assess*"],
            ["Camera path", "5", "Landmark model loads; blank frame gives *Poor lighting* plus a preview; garbage frame gives 422; calibration can start; monitoring is blocked while calibrating"],
            ["History and export", "3", "Events and summary present; simulation events carry the SIMULATION label; CSV export"],
            ["Thresholds", "3", "Out-of-range value gives 422; valid values saved; saved values persist"],
            ["Research route", "6", "Starts as *Model not trained*; evaluation without subjects gives 422; bad CSV gives 422 with the reason; synthetic evaluation trains; report flagged synthetic; confusion-matrix PNG served"],
            ["Cleanup", "1", "Session closed"],
        ], widths=[1.6, 0.7, 4.0], size=9.5, align=["l", "c", "l"]),
        H2("7.4 Functional testing"),
        P("Functional behaviour of the interface was checked by walking every screen with `scripts/capture_screens.py` (Playwright), which drives the demo login, the four simulation "
          "scenarios, the camera path with a looping video of one public-domain portrait, calibration, the threshold form (including a rejected value, screen 09) and the research "
          "screen, and fails on a console error or a wrong verdict. Its output is the set of screenshots in Chapter 8. `scripts/check_layout.py` checks the layout at 360, 768 and 1440 pixels "
          "in light and dark themes for overflow and console errors. The functional scenarios are summarised below."),
        TAB("Functional scenarios", ["Scenario", "Expected result", "Evidence"], [
            ["Sign in with the demo account", "Monitor opens; wrong password refused with a message", "Screen 03; smoke checks"],
            ["Simulation: Prolonged eye closure", "Warning after about 6 s with the reason \"Continuous eye closure\"", "Screen 04; unit test; Section 8.2"],
            ["Simulation: Missing face / Poor lighting", "*Unable to assess* with the reason, never a warning", "Unit test; smoke check"],
            ["Camera on a real face, calibrate, monitor", "Landmarks drawn on both eyes; calibrated threshold saved; *Normal* with EAR shown", "Screens 05 and 06"],
            ["Edit thresholds with an invalid value", "Field error \"Must be between 0.5 and 5\"; nothing saved", "Screen 09"],
            ["Export history", "CSV with source, UTC time, state, quality, reason and measurements", "Smoke check; screen 08"],
            ["Research screen before data", "\"Model not trained\"", "Screen 11"],
            ["Research screen with the synthetic sample", "Report flagged **Synthetic data**", "Screen 12"],
            ["Phone-width layout", "No horizontal overflow", "Mobile screens; `check_layout.py`"],
        ], widths=[2.0, 2.7, 1.6], size=9.5),
        H2("7.5 Security tests"),
        P("The product is a local demonstration with a single demo account, so security testing covers the controls that exist, not those of a production service."),
        TAB("Security checks", ["Check", "Expected", "Where tested"], [
            ["Protected route without a token", "401", "Smoke check \"protected route needs login\""],
            ["Wrong password", "401 with a message", "Smoke check \"wrong password rejected\""],
            ["Token integrity", "HMAC-SHA256 signature checked with `hmac.compare_digest`; expiry (12 h) enforced; malformed token gives 401", "Code review of `backend/main.py` (`current_user`); no separate automated test"],
            ["Invalid threshold values", "422 and nothing saved", "Smoke check \"invalid threshold -> 422\"; unit test of bounds"],
            ["Garbage image upload", "422", "Smoke check \"garbage frame -> 422\""],
            ["Bad research CSV / no consent flag", "422 with the reason; nothing trained", "Smoke check; unit test of consent validation"],
            ["Image persistence", "No frame or face image is written to disk; only numeric events", "Code review of `session.py` and `storage.py`; the data folder holds SQLite and JSON only"],
            ["SQL injection", "Bound parameters only (`?`)", "Code review of `storage.py`"],
        ], widths=[2.2, 2.4, 1.7], size=9.5),
        P("Known weaknesses are stated, not hidden: the demo credentials are shown on the login page by design, CORS is open to all origins for local use, the default `AUTH_SECRET` is a "
          "placeholder, and no penetration test or dependency audit was performed."),
        H2("7.6 Validation and edge cases"),
        B("No face, more than one face, eyes out of view, eyes smaller than 14 pixels, hidden or badly lit eyes, inconsistent eye geometry: each returns *Unable to assess* and clears the evidence timer.",
          "Dark or over-exposed frames, blurred frames and large frame-to-frame motion are rejected before landmarking.",
          "A time gap above 0.5 s, a non-increasing timestamp, NaN or an out-of-range EAR resets the engine instead of guessing.",
          "A closure shorter than 0.08 s or longer than 0.8 s is not counted as a blink; closures of 0.5 to 2.4 s never raise a warning with the default rules (Section 8.2).",
          "Head tilt alone never warns; it counts only together with a low EAR.",
          "Calibration fails, and the previous threshold is retained, when fewer than 40 usable frames or 70 % acceptance are reached in 15 s.",
          "Threshold edits outside the documented bounds are refused; a corrupt `settings.json` falls back to safe defaults.",
          "Research input without `consent=yes`, with duplicate timestamps or with an unsuitable held-out split is refused."),
        P("**Degraded-condition test.** To probe the quality gates, 272 open-eye faces were degraded in software and passed through the shipped `Vision` pipeline (table below). "
          "The gates fail safe, in that they return no verdict instead of a guess, but they are strict."),
    ]
    rows = []
    for c in rob:
        fc = c["false_closure_rate_among_good"]
        rows.append([c["condition"], f"{c['good']} ({F.pct(c['good_rate'])})", str(c["n"] - c["good"]), "-" if fc is None else F.pct(fc)])
    out += [
        TAB("Quality gating under degraded conditions (open-eye faces)", ["Condition", "Assessed", "Unable to assess", "False closed among assessed"], rows,
            widths=[2.7, 1.2, 1.1, 1.3], size=9.5, align=["l", "c", "c", "c"]),
        FIG(F.fig("robustness.png"), "Share of degraded open-eye faces that were assessed or refused by the quality gates", 5.6),
        P("Two cautions apply. The 100-pixel source crops are soft to begin with, so the sharpness gate sits close to their natural value and absolute rates would differ for webcam frames. "
          "And because `Vision` runs MediaPipe in video mode, an unrelated still can inherit tracking state from the previous one: the unmodified baseline row assessed 267 of 272 faces although all "
          "272 had been assessed in the first pass, so figures carry roughly two percentage points of run-to-run noise."),
        H2("7.7 Performance testing"),
        P(f"All timings were taken on {hw['cpu']}, {hw['ram']} of memory, {hw['gpu']}, {hw['os']}, Python {hw['python']} and MediaPipe {hw['mediapipe']}, on the CPU. "
          f"`Vision.process` on a 640 x 480 frame (quality checks and landmarking) took {vl.get('mean', 0):.1f} ms on average, {vl.get('p50', 0):.1f} ms at the median and "
          f"{vl.get('p95', 0):.1f} ms at the 95th percentile over {vl.get('n', 0):,} images (maximum {vl.get('max', 0):.1f} ms). The rule engine itself costs {ec.get('microseconds_per_update', 0):.1f} "
          f"microseconds per observation ({ec.get('updates', 0):,} updates), which is negligible."),
        P(f"The API was measured over HTTP on `127.0.0.1` in its own server process with temporary storage. A camera frame (a real face as a {api.get('frame_jpeg_bytes', 0):,}-byte JPEG) "
          f"took {fr.get('mean_ms', 0):.1f} ms on average, {fr.get('p50_ms', 0):.1f} ms at the median, {fr.get('p95_ms', 0):.1f} ms at the 95th percentile and {fr.get('max_ms', 0):.1f} ms at most "
          f"({fr.get('n', 0)} frames, monitoring on). That covers HTTP, JPEG decoding, landmarking, quality gates, the rule engine, the SQLite write and the annotated JPEG reply, and corresponds to roughly "
          f"{1000 / fr.get('p50_ms', 31):.0f} frames per second through one session. Simulation ticks took {tk.get('p50_ms', 0):.1f} ms and the history route (500 rows) {hs.get('p50_ms', 0):.1f} ms at the median; "
          f"starting the camera source, which loads the landmark model, took {api.get('camera source start_ms (loads MediaPipe model)', 0):.0f} ms. Addresses of the form `localhost` were not used for timing, because "
          "name resolution on this machine adds about two seconds per call."),
        TAB("API latency on 127.0.0.1", ["Route", "n", "Median (ms)", "95th percentile (ms)", "Maximum (ms)"], [
            ["GET /api/health", str(hl.get("n", 0)), f"{hl.get('p50_ms', 0):.1f}", f"{hl.get('p95_ms', 0):.1f}", f"{hl.get('max_ms', 0):.1f}"],
            ["POST tick (simulation)", str(tk.get("n", 0)), f"{tk.get('p50_ms', 0):.1f}", f"{tk.get('p95_ms', 0):.1f}", f"{tk.get('max_ms', 0):.1f}"],
            ["GET /api/history (limit 500)", str(hs.get("n", 0)), f"{hs.get('p50_ms', 0):.1f}", f"{hs.get('p95_ms', 0):.1f}", f"{hs.get('max_ms', 0):.1f}"],
            ["POST frame (real face JPEG)", str(fr.get("n", 0)), f"{fr.get('p50_ms', 0):.1f}", f"{fr.get('p95_ms', 0):.1f}", f"{fr.get('max_ms', 0):.1f}"],
        ], widths=[2.4, 0.6, 1.1, 1.3, 1.0], size=10, align=["l", "c", "c", "c", "c"]),
        FIG(F.fig("api_latency.png"), "Median and 95th-percentile latency of the API routes", 5.0),
        P(f"The base paper reports 25 frames per second on an NVIDIA Jetson Orin Nano {n(1)}; this prototype's vision path runs at about the same rate or faster on a laptop CPU, but the "
          "pipelines and hardware differ, so this is context, not a comparison. No load, concurrency or long-duration test was run."),
        H2("7.8 User acceptance"),
        P("No user study was run, and this report does not claim one. The product was demonstrated by the project team to the project guide in the form of the scripted simulation scenarios and the "
          "live-camera path; no questionnaire, rider trial or recorded feedback exists. What can be offered instead is requirement traceability, summarised below."),
        TAB("Requirement traceability", ["Requirement", "Evidence"], [
            ["Capture video and find landmarks in real time", "Camera path, screen 06; 31 ms median per frame; CEW measurements"],
            ["Extract eye closure, blink rate, head movement", "EAR, closure, blink rate, closed fraction and roll shown on screens 04 and 06; unit tests"],
            ["Raise an alert when the impairment score crosses a threshold", "Rule engine, on-screen warning and optional bell (screen 04); unit tests; Section 8.2"],
            ["Explain every verdict", "Reason string on every decision; quality status shown beside the preview"],
            ["Refuse to guess when the signal is poor", "Quality gates; Section 7.6"],
            ["Personal calibration", "Calibration screen 05; unit tests; calibrated threshold 0.183 visible in screens 06 and 09"],
            ["Log events without images", "SQLite events, CSV export; screen 08"],
            ["Not an alcohol result", "Disclaimers on every screen; *Possible impairment or drowsiness* wording"],
            ["Train a deep-learning sober/intoxicated classifier", "**Not met**: no dataset; see Section 8.11"],
            ["Prevention action (ignition warning, contact notification)", "**Not met**: on-screen warning and bell only"],
        ], widths=[2.8, 3.5], size=9.5),
        H2("7.9 Limits of the testing done"),
        B("The tests show that the software behaves as specified, not that it detects impairment, and certainly not alcohol: no intoxicated person and no rider took part in any test.",
          "The vision component was measured on one public still-image dataset (CEW) and on software-degraded copies; no helmet, visor, glasses-in-motion, vibration, night or demographic study exists.",
          "Rule-engine results (Section 8.2) use scripted streams generated by `scripts/measure_rules.py`; they describe the rules, not human behaviour.",
          "The live-camera screenshot and API timing use one public-domain portrait, so they say nothing about different faces or skin tones.",
          "The user-interface checks run in Chromium only; there is no load, concurrency or soak test and no penetration test.",
          "The Tk desktop smoke test and webcam diagnostic date from 23 September 2026 and were not repeated in the final run."),
    ]
    return out
