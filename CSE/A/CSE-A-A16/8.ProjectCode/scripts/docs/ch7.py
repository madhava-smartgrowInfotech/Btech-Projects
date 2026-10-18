"""Chapter 7: System Testing."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, P, TAB


def latency_rows():
    L = F.LAT
    rows = []
    for label, key in (("JPEG decode 960x540", "jpeg_decode_960x540"), ("ROI crop + segmentation + normalise", "roi_crop_and_segmentation_and_normalisation"),
                       ("CNN forward pass, batch 1 (`model.predict`)", "cnn_forward_batch1"), ("Server total per frame", "server_side_total_per_frame"),
                       ("HTTP `/recognize/frame` round trip (localhost)", "http_recognize_frame_round_trip"), ("HTTP `/health`", "http_health")):
        r = L[key]
        rows.append([label, f"{r['median_ms']:.2f}", f"{r['mean_ms']:.2f}", f"{r['p95_ms']:.2f}", str(r["n"])])
    return rows


def blocks():
    b = [H1("CHAPTER 7: SYSTEM TESTING")]
    b += [H2("7.1 Testing strategy"),
          P("Testing covers four layers. Small functions and the smoothing logic are tested in isolation; the API is tested in-process against the real application object; the whole stack is run in a "
            "throw-away copy with synthetic frames; and the web interface is walked in a real browser. All automated tests are in the repository (`tests/`, `scripts/smoke_test.py`) and can be re-run with one command. "
            "Before this documentation work the project had no automated tests; the 52 tests below were written for it. They test behaviour, not recognition quality: recognition quality is measured separately "
            "on held-out images (Chapter 8)."),
          TAB("Test layers and results", ["Layer", "What it covers", "How", "Result"],
              [["Unit: preprocessing", "ROI box, crop, blur, Otsu mask, morphology, normalisation, skin mode", "pytest, synthetic images", f"{F.PYTEST_PRE} passed"],
               ["Unit: recogniser", "Confidence threshold, majority vote, stable count, auto-commit, repeat guard", "pytest, stub model", f"{F.PYTEST_REC} passed"],
               ["Unit: dataset and model", "Class counts, 70/15/15 stratified split, reproducibility, label file, CNN shape and structure", "pytest, temp folders", f"{F.PYTEST_DS} passed"],
               ["Integration: API", "All endpoints, validation errors, collection, training validation, recognition flow", "pytest + FastAPI TestClient", f"{F.PYTEST_API} passed"],
               ["Functional: smoke test", "Collect 80 images, long run stopped early, 3-epoch training, model report, live recognition, bad inputs", "`scripts/smoke_test.py`, own server on port 8399", f"{F.SMOKE_TOTAL} of {F.SMOKE_TOTAL} checks pass"],
               ["Browser walk", "Every screen at 360 / 768 / 1440 px, light and dark, reduced motion at 360 px; console, network and 404s", "Playwright + Chromium, fake camera fed with real ASL photos", "Clean (details below)"],
               ["Build", "TypeScript type-check and production bundle", "`npm run build`", "Passes"]],
              widths=[1.35, 2.5, 1.7, 1.05], align=["l", "l", "l", "c"], size=9.5),
          P(f"In total **{F.PYTEST_TOTAL} pytest tests pass** (about four seconds) and **{F.SMOKE_TOTAL} of {F.SMOKE_TOTAL}** smoke-test checks pass.")]

    b += [H2("7.2 Unit testing"),
          P("The most important unit tests are those of the temporal logic, because it decides what is typed. They use a stub model that returns a fixed probability vector, so they need no trained weights and no TensorFlow inference."),
          TAB("Selected unit test cases", ["ID", "Test", "Input", "Expected result", "Result"],
              [["U1", "Commit after stability", "Letter A at 0.95 confidence for 28 frames", "`A` committed exactly once, at frame 18", "Pass"],
               ["U2", "No early commit", "Letter B at 0.95 for 17 frames", "No letter committed", "Pass"],
               ["U3", "Low confidence ignored", "Letter A at confidence 0.65 for 40 frames", "Nothing committed; stable label is `nothing`", "Pass"],
               ["U4", "Repeat guard", "Letter A held 40 frames, held 40 more, then a `nothing` pause, then A again", "No second commit without the pause; one commit after it", "Pass"],
               ["U5", "Control labels", "`space` and `del` held steadily", "Committed like letters", "Pass"],
               ["U6", "Noise tolerance", "One wrong frame inside a steady run", "Stable label unchanged", "Pass"],
               ["U7", "Not loaded", "`predict_frame` before a model is loaded", "Returns `None`", "Pass"],
               ["U8", "ROI box", "Default 960x540 frame; small frame", "(620, 90, 920, 390); box stays inside the frame", "Pass"],
               ["U9", "Mask polarity", "Bright hand on dark and dark hand on bright background", "Hand is the white minority region, corner is black, in both cases", "Pass"],
               ["U10", "Flat image", "Uniform grey crop", "No crash", "Pass"],
               ["U11", "Normalisation", "Any mask", "Shape (64, 64, 1), values in [0, 1]", "Pass"],
               ["U12", "Split", "Two classes of 40 images", "56 / 12 / 12 images, equal class counts per part, identical test part on a second call (seed 42)", "Pass"],
               ["U13", "Network", "Build for 29 classes", "Softmax output of shape (1, 29) summing to 1; three convolution layers", "Pass"],
               ["U14", "No data", "`load_dataset` with empty `data/`", "Raises an error with a clear message", "Pass"]],
              widths=[0.4, 1.3, 1.9, 2.4, 0.6], align=["c", "l", "l", "l", "c"], size=9)]

    b += [H2("7.3 Integration testing"),
          P("The 27 API tests call the real FastAPI application in-process. Collection tests redirect the data folder to a temporary directory by patching `config.DATA_DIR`, so the real `data/` is never touched. The tests check status "
            "codes and the shape of responses for every endpoint family."),
          TAB("Selected integration test cases", ["ID", "Test", "Input", "Expected result", "Result"],
              [["I1", "Health", "GET /api/health", "200, status ok", "Pass"],
               ["I2", "Config", "GET /api/config", "29 classes, image size 64, ROI (620, 90, 920, 390), stable frames from `config`", "Pass"],
               ["I3", "Unknown class", "GET /api/dataset/Z9/images; POST /api/collect/Z9", "404 for both", "Pass"],
               ["I4", "Hostile image names", "`..%2F..%2Fsecret.png`, `a.txt`, `x y.exe`", "400 or 404, no file read", "Pass"],
               ["I5", "Collect", "POST a 960x540 frame to /api/collect/A", "200, count 1, a 200x200 PNG on disk, listed and fetchable", "Pass"],
               ["I6", "Preview", "POST a frame to /api/preview", "200, PNG data URL", "Pass"],
               ["I7", "Bad frames", "Empty body; text instead of an image", "400", "Pass"],
               ["I8", "Odd frame size", "120x200 image", "200 (resized, not rejected)", "Pass"],
               ["I9", "Missing field", "POST /api/preview with no frame", "422", "Pass"],
               ["I10", "Unknown session", "POST /api/recognize/frame, session `nope`", "404 or 409", "Pass"],
               ["I11", "Hyper-parameter limits", "epochs 0 or 501; batch 0 or 2,000; learning rate 0 or 2", "400 for each of the six", "Pass"],
               ["I12", "Too few classes", "POST /api/train/start with an empty data folder", "409", "Pass"],
               ["I13", "Speech limits", "Empty, blank and 2,001-character text", "400 for each", "Pass"],
               ["I14", "Model report", "GET /api/model", "`trained`; if true 29 labels and accuracy in (0, 1]", "Pass"],
               ["I15", "Recognition flow", "Reload model, open session, post a frame", "200; label in the 29 classes; confidence in [0, 1]; mask data URL", "Pass"]],
              widths=[0.4, 1.3, 1.9, 2.4, 0.6], align=["c", "l", "l", "l", "c"], size=9)]

    b += [H2("7.4 Functional testing: the smoke test"),
          P("`scripts/smoke_test.py` copies the application into a temporary folder, starts its own server on port 8399 and drives the full user flow with synthetic frames (a bright disc for class A, a square for class B). "
            "It checks 26 things: health, config, about; empty dataset and untrained model states; the 409 and 400 refusals (too few classes, bad hyper-parameters, unknown class, bad frame, empty speech, "
            "recognition without a model); collecting 40 images for each of two classes; listing and fetching images; the preview mask; a long training run that is stopped early (it stopped at epoch 2) and a second start "
            "that is refused while it runs; a three-epoch training that finishes; the training history and summary; the model report with per-class rows and the confusion matrix; automatic loading of the new model; "
            "recognition of frames with the smoothing fields present; and an unknown session. All 26 pass. The smoke test proves that the pieces are wired together; because its frames are synthetic it says nothing about recognition quality.")]

    b += [H2("7.5 Security and validation testing"),
          P("Security testing is limited to input validation, because the application is a single-user local tool: hostile file names (I4), unknown classes (I3), oversized speech text (I13), "
            "out-of-range training parameters (I11), undecodable and empty frames (I7), and concurrent access. A frame that is not 16:9 is resized and processed, not rejected (I8). Concurrency is handled by locks "
            "(one model lock, one collection lock) and by refusing a second training start (smoke test). No penetration test, dependency audit or authentication test was done, and the API has no authentication by design.")]

    b += [H2("7.6 Performance testing"),
          P(f"Latency was measured on the development PC ({F.ENV['cpu']}, {F.ENV['ram_gb']} GB RAM, no GPU) with a throw-away server, over 300 frames after warm-up. The table gives the median, mean and 95th percentile of each stage."),
          TAB("Latency per frame (milliseconds, 300 frames)", ["Stage", "Median", "Mean", "p95", "n"], latency_rows(), widths=[3.1, 0.8, 0.8, 0.8, 0.6], align=["l", "c", "c", "c", "c"], size=10),
          FIG(F.fig("f07_latency.png"), "Median latency of each stage of one recognition request.", 5.0),
          P(f"The server needs {F.LAT['server_side_total_per_frame']['median_ms']:.1f} ms per frame (a ceiling of about {F.LAT['max_fps_server_side']} frames per second) and a full HTTP round trip takes "
            f"{F.LAT['http_recognize_frame_round_trip']['median_ms']:.1f} ms, which gives about {F.LAT['http_round_trip_fps_sequential']} frames per second with one request at a time. The convolutional network dominates: "
            f"{F.LAT['cnn_forward_batch1']['median_ms']:.1f} ms of the {F.LAT['server_side_total_per_frame']['median_ms']:.1f} ms, whereas decoding and preprocessing together take about 2.5 ms. The cost is that of calling "
            "`model.predict` on a single image, which carries per-call overhead; calling the model directly, exporting it or quantising it would likely lower it, but none of that was tried. "
            f"The JPEG payload averages {F.LAT['jpeg_payload_kb_mean']:.0f} KB per frame. These figures are for one CPU and one client and are not a load test."),
          H3("7.6.1 Robustness to image changes"),
          P(f"Robustness was tested by perturbing {F.M['robustness']['n']} held-out photos (20 per class) and re-classifying them. Brightness, noise and blur change accuracy little, except for brighter images; "
            f"a rotation of 10 degrees in either direction costs about 17 points."),
          FIG(F.fig("f06_robustness.png"), "Accuracy under brightness, noise, blur and rotation changes (580 photos).", 5.2),
          TAB("Accuracy under perturbation", ["Condition", "Accuracy"], [[k, F.pct(v)] for k, v in F.ROB.items()], widths=[3.0, 1.2], align=["l", "c"], size=10),
          P("The sensitivity to rotation is a real weakness: the training augmentation rotates by up to 12 degrees, yet 10 degrees of rotation of a held-out photo still reduces accuracy from 85.0 % to about 68 %. A signer who "
            "tilts the hand will be read less accurately.")]

    b += [H2("7.7 User interface testing"),
          P("A browser walk was run with Playwright and Chromium, using Chromium's fake camera fed with a clip assembled from real held-out ASL photos (there is no physical webcam on the build machine). Every screen was opened at 360, 768 and 1440 px "
            "in light and dark themes, and at 360 px with reduced motion. The console, the network log and 404 responses were clean; the navigation drawer closed with the Escape key; form validation (for example a hyper-parameter out of range) "
            "showed its message. The phone-width captures in Chapter 8 are from this walk."),
          H3("7.7.1 Browser matrix and what was not covered"),
          P("Only Chromium was used. Firefox and Safari, a physical webcam in varied rooms, screen readers and a keyboard-only pass beyond the drawer and focus checks were not tested.")]

    b += [H2("7.8 User acceptance testing"),
          P("No user study was carried out. Members of the project team used the application during development, but no test with deaf or hearing signers, and no usability questionnaire, was run, so we make no claim "
            "about acceptance. This is listed with the limitations in Chapter 8.")]

    b += [H2("7.9 Limits of the testing done"),
          B("The held-out test images come from the same recordings as the training images (Chapter 6), so accuracy on a new signer or room is not measured.",
            "Recognition through the browser was tested with a fake camera, not a physical webcam; the camera hook was not tested against real hardware variation.",
            "There are no unit tests of the React components, no load or stress tests, and no security audit beyond input validation.",
            "Timing figures are for one machine and one client; they were measured on an otherwise idle PC and vary a little between runs.")]
    return b
