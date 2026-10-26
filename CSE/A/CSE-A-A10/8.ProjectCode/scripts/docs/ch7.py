"""Chapter 7: System Testing for FlowSense. Numbers come from facts.py (experiments/**/metrics.json) and the recorded test runs (docs/REPORT_FACTS.md section 11)."""

from . import facts as F
from .blocks import B, H1, H2, H3, P, TAB

_KEEP = ("health", "live snapshot", "live step 2 s", "live step 60 s", "live step 300 s", "prediction:", "violations", "vision synthetic", "vision sample", "POST /api/benchmark")


def _lat_rows():
    rows = []
    for r in F.API["results"]:
        name = r["endpoint"]
        if not any(name.startswith(k) for k in _KEEP):
            continue
        p95 = f"{r['p95_ms']:.1f}" if "p95_ms" in r else "-"
        rows.append([name.replace("POST /api/benchmark (4 ctrl x 3 seeds x 1800 s, first call)", "Benchmark, 4 controllers x 3 seeds x 1,800 s (first call)")
                     .replace("POST /api/benchmark (cached)", "Benchmark, same settings (cached)")
                     .replace("POST /api/benchmark/sweep (5 demand levels x 4 ctrl)", "Demand sweep, 5 levels x 4 controllers")
                     .replace("vision sample (YOLOv8): ", "YOLOv8n sample photo: ").replace("vision synthetic: ", "Synthetic scene: ")
                     .replace("live step", "Live step").replace("live snapshot", "Live snapshot").replace("prediction:", "Prediction:")
                     .replace("violations:", "Violations:").replace("health:", "Health:"),
                     f"{r['mean_ms']:.1f}", p95, str(r["n"])])
    return rows


def blocks():
    th, vy, vr = F.TH, F.VY, F.VR
    b = [H1("CHAPTER 7: SYSTEM TESTING")]

    # ------------------------------------------------------------------ 7.1
    b += [H2("7.1 Testing strategy"),
          P("FlowSense was first delivered with one end-to-end smoke script and a screenshot walk. The documentation run added an automated test suite and measurement scripts. "
            "The engine (`smart_traffic/`) is deterministic once seeded, so it is tested at unit level with exact assertions on controller behaviour, demand fairness and the vision rules. "
            "The two statistical components, the queue forecaster and the vision layer, are tested twice: their software behaviour (shapes, clipping, thresholds, blank input) by unit tests, and their predictive quality by the multi-seed and real-image experiments of Chapter 8. "
            "The API is tested through FastAPI's test client and through a smoke script against a running server, and the screens by walking every route of the console with real data."),
          TAB("Test levels, tools and results.",
              ["Level", "Tool and scope", "Count", "Result"],
              [["Unit", "pytest: tests/test_engine.py (simulator, controllers, forecaster, vision rules)", f"{F.PYTEST_ENGINE} tests", "All passed"],
               ["API / component", "pytest with FastAPI TestClient: tests/test_api.py", f"{F.PYTEST_API} tests", "All passed"],
               ["Integration", f"scripts/smoke_test.py against the running API (127.0.0.1:{F.API_PORT})", f"{F.SMOKE_TOTAL} checks", f"{F.SMOKE_PASSED} of {F.SMOKE_TOTAL} passed"],
               ["Functional / screens", "Playwright walk of the console, screenshots 01-19; scripts/check_ui.py responsive checks", "19 captures", "Rendered with real data"],
               ["Performance", "scripts/measure_api.py, scripts/run_experiments.py (throughput)", "API routes; 4 simulator runs", "Section 7.7"],
               ["Model validation", "scripts/run_experiments.py, scripts/eval_real_vision.py", "5 seeds; 6 held-out runs; 893 real images", "Chapter 8"]],
              widths=[1.3, 3.2, 1.2, 1.0], align=["l", "l", "l", "l"], size=9.5),
          P(f"All tests ran on one machine: Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB RAM shared with other programs, Windows 11, Python 3.11.9, PyTorch 2.14.1 (CPU), scikit-learn 1.5.0, Ultralytics 8.4.186. "
            f"The pytest suite finished in about {F.PYTEST_SECONDS} s. Timings in Section 7.7 are means of repeated calls on this shared machine and are indicative.")]

    # ------------------------------------------------------------------ 7.2
    b += [H2("7.2 Unit testing"),
          P(f"The pytest suite has **{F.PYTEST_TOTAL} tests in two files, and all {F.PYTEST_PASSED} passed**. `tests/conftest.py` imports PyTorch before anything else, because on the test machine PyTorch's DLLs fail to initialise if NumPy or OpenCV are loaded first."),
          TAB("Unit tests of the engine, forecaster and vision layer, grouped (tests/test_engine.py).",
              ["Group (tests)", "What is asserted"],
              [["Determinism and fairness (same seed, different seed, demand independent of controller, rush-hour profile)",
                "Equal seeds give identical summaries; different seeds differ; all four controllers receive the same number of ambulances for one seed, so comparisons are like-for-like; the profile peaks at 08:30 and 17:30"],
               ["Signal and network rules (phases, fixed cycle, spill-back, PCU weights, feature matrix)",
                "Phases are 0 or 1 and no fixed-time green is shorter than 30 s; internal approach queues stay within capacity plus a margin for vehicles in flight; PCU weights bus 3, bike 0.5, car 1; the feature matrix is 16 x 11 on 2 x 2"],
               ["Violations and summary (violations off, log fields, summary keys)",
                "With violations disabled the log is empty; logged rows carry time, junction, approach, kind, plate, vehicle and a confidence of 0.86-0.99; CO2 equals 2.31 x fuel"],
               ["Controller behaviour (emergency served faster, ambulance not ignored, advanced beats fixed on three seeds, controllers registered)",
                "Over three seeds the emergency-aware controller halves ambulance delay against fixed-time; an injected ambulance is served and a pre-emption counted; advanced mean delay is below fixed-time"],
               ["Forecaster (beats persistence, output clipped)",
                "MAE below persistence; more than 20,000 training rows; importance for all 11 features; absurd inputs give outputs within 0-40"],
               ["Vision rules (ambulance flagged, not flagged, blank frame, density levels, light-bar rule, annotate, YOLO sample)",
                "A scene with an ambulance has a light-bar cluster, an `ambulance` detection and a 12 s green; none without; a uniform frame gives nothing; 2, 7, 11 and 20 cars map to LOW to JAMMED with greens clamped to 15-60 s; red alone is no light bar, red touching blue is; annotation works on a copy; YOLOv8n finds the bus in the bundled photograph"]],
              widths=[2.7, 3.8], align=["l", "l"], size=9),
          P("The fourteen API tests drive the real FastAPI application and engine through `TestClient`. They check that health is public; that protected routes answer 401 without a token; that a wrong password and a malformed login give readable messages (401 and 422); "
            "that tokens round-trip, reject a changed signature and expire; that the live simulation resets, accepts a configuration and advances 120 s; that an out-of-range step, an unknown controller and a demand of 9 are refused with 422; "
            "that an ambulance raises a pre-emption banner which the fixed controller turns into an \"ignored\" banner; that a 3 x 3 grid restarts the simulation with nine junctions; "
            "that a benchmark returns four rows with a positive reduction against fixed-time and a 10-second benchmark is refused; and that the prediction, synthetic-vision and violation routes answer correctly and a non-image upload is rejected.")]

    # ------------------------------------------------------------------ 7.3
    b += [H2("7.3 Integration testing"),
          P(f"`scripts/smoke_test.py` drives the running API over HTTP with no mocks; it finished with **{F.SMOKE_PASSED} of {F.SMOKE_TOTAL} checks passed and none failed**. It waits for the forecaster to finish training, so the first start is covered. "
            "The checks cover start-up and authentication (health, predictor ready, anonymous refusal, bad and demo login), the public landing pulse and four listed controllers, live control (reset, configuration, 2 s steps, a 300 s skip, map with 4 roads and 16 signals, ambulance banner, fixed controller ignoring it, demand 9 refused, 3 x 3 restart), "
            "violations and prediction (log rows with plate and kind, forecaster beating persistence, live forecast), the benchmark and demand sweep (four controllers, advanced beating fixed-time, out-of-range settings refused), "
            "and vision (synthetic ambulance flagged, YOLOv8n on the sample photograph, blank upload giving zero vehicles, a non-image upload refused with a message).")]

    # ------------------------------------------------------------------ 7.4
    b += [H2("7.4 Functional testing of the screens"),
          P("`scripts/capture_screens.py` walks every screen of the console in a real Chrome browser, puts real data on it (a 16-minute congested run for the violation log, a benchmark, a forecast, the YOLOv8 sample photograph) and saves nineteen 1440 x 900 screenshots (Chapter 8 and Appendix C). "
            "`scripts/check_ui.py` repeats the pages at 360, 768 and 1440 px, in light and dark themes, with keyboard navigation and reduced motion. These checks show that the screens render and respond with real data; the React components have no unit tests of their own."),
          TAB("Functional scenarios covered by the screen walk.",
              ["Scenario", "Expected", "Observed"],
              [["Run the live simulation 60 s, then skip 5 min", "Queues, KPIs and map update", "As expected"],
               ["Switch the controller while an ambulance is queued", "Banner changes between pre-empting and ignored", "As expected"],
               ["30 min benchmark at demand x1.2, 3 seeds", "KPI tiles and four-controller charts", "Fixed 73.0 s, adaptive 48.5 s, emergency-aware 51.2 s, advanced 45.4 s"],
               ["Vision: synthetic scene; YOLOv8n sample photograph", "Boxes and a light-bar cluster; a bus box", "As expected; bus 0.87"],
               ["Prediction screen", "KPIs, scatter, importance, model table", "MAE 1.64, R² 0.961, 26,988 samples"],
               ["Violations after 16 simulated minutes", "Counts, charts and an evidence log", "11 violations (8 red-light, 3 wrong-way)"]],
              widths=[2.4, 2.0, 2.0], align=["l", "l", "l"], size=9.5)]

    # ------------------------------------------------------------------ 7.5
    b += [H2("7.5 Security testing"),
          P("Security testing is limited to what a demonstration console needs. The API tests and smoke checks confirm that protected routes reject anonymous requests with 401; that a wrong password is refused with a message that does not say whether the e-mail exists; "
            "that a token with a modified signature or a past expiry is rejected; that over-range inputs are refused with 422; that an oversized or non-image upload is refused with 413 or 415; and that errors carry a message and a hint but no stack trace."),
          P("**Not tested:** brute-force protection (none exists), transport security (HTTP on localhost), the strength of the development signing key (a fixed key is used when `JWT_SECRET` is missing or a placeholder), cross-site scripting beyond React's default escaping, "
            "dependency vulnerabilities, and any penetration test. The product has one demonstration account and no personal data, which bounds the risk but is not a defence.")]

    # ------------------------------------------------------------------ 7.6
    pr = F.PR
    gb = pr["leave_one_simulation_out"]["Gradient Boosting (used)"]["mae_per_fold"]
    ps = pr["leave_one_simulation_out"]["Persistence"]["mae_per_fold"]
    m = vr["mixed_traffic"]["per_class"]
    a = vr["ambulance_classification"]
    b += [H2("7.6 Validation and edge cases"),
          H3("7.6.1 Validity of the comparison"),
          P(f"The controller comparison is only meaningful if the controllers face identical traffic. The unit test `test_demand_is_controller_independent` checks this, and the experiment tables confirm it: for each grid all four controllers spawned the same number of ambulances "
            f"({F.C2['results']['fixed']['emergency_spawned']} over five seeds on 2 x 2, {F.C3['results']['fixed']['emergency_spawned']} on 3 x 3). Runs are deterministic, and the Benchmark screen reproduces the first three seeds of the 2 x 2 table (73.0, 48.5, 51.2 and 45.4 s)."),
          H3("7.6.2 Validation of the forecaster"),
          P(f"A random split gives MAE {pr['random_split_5x']['Gradient Boosting (used)']['mae_mean']:.2f} and R² {pr['random_split_5x']['Gradient Boosting (used)']['r2_mean']:.3f}, but rows from the same run sit on both sides of that split. Holding out each of the six training runs in turn, "
            f"gradient boosting beats persistence in five runs (for example {gb[0]:.2f} against {ps[0]:.2f} vehicles) and fails in the congested 3 x 3 run ({gb[3]:.2f} against {ps[3]:.2f}), whose queues are far outside the range of the other five. The output clip of 0-40 and the tree model's inability to extrapolate make the forecaster unreliable under heavier congestion than it was trained on; no unit test catches this."),
          H3("7.6.3 Validation of the vision layer"),
          P(f"The classical detector scores recall {F.VS['results']['clean']['recall']:.3f} and precision {F.VS['results']['clean']['precision']:.3f} on 300 synthetic scenes from the same author's renderer, but Gaussian noise of σ = 10 gives no detections, "
            f"a brightness factor of 0.6 loses every light bar, and a 7 x 7 blur leaves light-bar recall at {F.VS['results']['gaussian_blur_7x7']['ambulance_recall']:.3f}. On real photographs YOLOv8n reaches recall {m['4-wheeler']['recall']:.3f} and precision {m['4-wheeler']['precision']:.3f} for four-wheelers, "
            f"recall {m['2-wheeler']['recall']:.3f} for two-wheelers and 0 for auto-rickshaws (COCO has no such class), and the light-bar rule flags {a['lightbar_cluster_any']['tp']} of 300 real ambulance photographs with {a['lightbar_cluster_any']['fp']} false alarm in 300 others; "
            "on inspection those few hits sit on red and blue livery, a flag graphic and a star-of-life rather than on roof lights. These numbers come from one run with the application's default settings; Chapter 8 discusses them."),
          H3("7.6.4 Edge cases exercised"),
          TAB("Edge cases and their handling.",
              ["Case", "Handling", "Tested by"],
              [["Blank or uniform image", "No detections, no light bar, density LOW", "Unit test; smoke check"],
               ["File that is not an image", "415 with a hint", "API test; smoke check"],
               ["Image above 12 MB; Ultralytics missing; forecaster still training", "413, 503 with the install command, 503 with a retry hint", "Code paths; not exercised by an automated test"],
               ["Step of 0 or more than 900 s, unknown grid or controller", "422 naming the allowed values", "API test; smoke check"],
               ["Controller switched while an ambulance is present; grid changed mid-run", "Banner switches; simulation restarts at t = 0", "API tests; smoke check"],
               ["Very low (x0.6) and very high (x1.8) demand", "Runs complete; advanced is worse than adaptive at x0.6", "Demand sweep experiment"],
               ["Spill-back on a full receiving queue", "Release blocked; vehicles wait", "test_spillback_limit_on_internal_links"]],
              widths=[2.3, 2.2, 1.9], align=["l", "l", "l"], size=9.5)]

    # ------------------------------------------------------------------ 7.7
    b += [H2("7.7 Performance testing"),
          P("`scripts/measure_api.py` calls each endpoint repeatedly against `http://127.0.0.1:8310` (the numeric address, because `localhost` added about two seconds per call on this machine) and records mean and 95th-percentile response times."),
          TAB("API response times (milliseconds, 127.0.0.1).",
              ["Endpoint", "Mean", "p95", "Calls"], _lat_rows(), widths=[3.9, 0.8, 0.8, 0.8], align=["l", "r", "r", "r"], size=9),
          P(f"Every interactive route except the YOLOv8 one answers in about 30 ms or less on average. The first YOLOv8 call includes loading the weights, which is why that route's mean is 503 ms and its 95th percentile more than three seconds; an earlier run against a warmed server measured about 150 ms. "
            f"A 30-minute, four-controller, three-seed benchmark takes about {F.API['results'][-3]['mean_ms'] / 1000:.1f} s the first time, which is why the console caches it."),
          TAB("Simulator and model speed.",
              ["Measurement", "Result"],
              [[f"Simulate 1,800 s, {k.replace('/', ', ')}", f"{v['wall_s']:.2f} s ({v['speedup']:,.0f} x real time)"] for k, v in th.items() if isinstance(v, dict)] +
              [["Forecaster prediction for 16 rows", f"{th['predictor_batch16_ms']:.2f} ms"],
               ["Forecaster training (application start)", f"{pr['shipped_fit']['fit_seconds']:.1f} s"],
               ["YOLOv8n, bundled photograph, CPU (20 runs)", f"{vy['sample_photo']['latency_ms_mean']:.1f} ms mean, {vy['sample_photo']['latency_ms_median']:.1f} ms median"],
               ["YOLOv8n, 293 dashcam frames, CPU", f"{vr['mixed_traffic']['latency_ms_mean']:.1f} ms mean per 640 x 480 frame"]],
              widths=[3.8, 2.6], align=["l", "l"], size=10),
          P("The base paper reports 11.45 to 13.89 ms per frame for its YOLO26m detector on an NVIDIA T4 GPU; FlowSense's 32 to 51 ms per frame is measured on a CPU with a smaller model, so the two are not comparable as speeds of the same thing. "
            "No load test with many simultaneous users was run: the live simulation is one shared object guarded by a lock, so concurrent operators would interfere with each other.")]

    # ------------------------------------------------------------------ 7.8
    b += [H2("7.8 User acceptance"),
          P("**No formal user-acceptance test was carried out.** There was no panel of traffic engineers or control-room operators, no questionnaire and no usability metric. What exists is a repeatable demonstration walkthrough: "
            "sign in; run the live simulation under fixed-time control and watch queues build; switch to the advanced controller; send an ambulance and watch the pre-emption banner; run the benchmark; analyse the synthetic scene and the sample photograph; compare forecast and queue; and read the violation log. "
            "Each step was executed by the screen-capture script with real data, so it is known to work, but whether an operator would find the console clear, or trust a simulated violation log, was not asked.")]

    # ------------------------------------------------------------------ 7.9
    b += [H2("7.9 Findings from testing"),
          P("Writing the tests and running the experiments produced findings that are recorded rather than hidden. None made a test fail, but several change how the product should be described."),
          B("**The forecaster does not generalise to unseen congestion** (Section 7.6.2): the random-split R² of 0.96 is optimistic; leave-one-simulation-out R² averages about 0.04.",
            "**The light-bar rule does not transfer to real photographs** (Section 7.6.3): 4 of 300 real ambulance photographs trigger a cluster, and those hits are livery colours, against all synthetic ones.",
            "**The advanced controller loses to plain adaptive control at the lowest demand** (26.4 s against 20.6 s at x0.6) and gains only 4 to 5 % at the benchmark demand, within one standard deviation.",
            "**Violations are simulated events.** The test that checks the log verifies its fields and range, not detection quality, because there is no detector to test.",
            "**The ambulance button is not seeded**, so the live demonstration is not exactly repeatable even though every experiment is; and **the pressure and forecast parameters (0.7, 8 s, 15 s, 12, 0.3) were set by hand**, varied only through the ablation.")]

    # ------------------------------------------------------------------ 7.10
    b += [H2("7.10 Limits of the testing done"),
          B("**Everything is simulated.** No camera, signal controller or real junction was involved; the base paper's SUMO roundabout and real traffic data were not available.",
            "**The unit tests assert behaviour the author expected.** They catch a regression but not a wrong modelling assumption such as the saturation flow or the link time; the React components were checked only by the screen walk.",
            "**Statistical power is small.** Five seeds per setting and standard deviations of 3 to 11 s mean that differences of a few percent (advanced against adaptive) cannot be called significant.",
            "**Real-image evaluation used 293 frames and 600 photographs** from two public sets unlike a fixed junction camera; the first 300 files of each ambulance folder were used, not a random sample.",
            "**No concurrency, load, endurance or security audit** was run.")]
    return b
