"""Chapter 7 content: system testing (CropSight). Counts come from backend/tests and the pytest run recorded in docs/REPORT_FACTS.md."""
from __future__ import annotations

from doc_common import metrics

AL = metrics("api_latency")
PR = metrics("price")
DL = metrics("delivery")
IO = metrics("iot")


def sec_test_strategy(d):
    d.h2("Testing Strategy")
    d.paras(
        "CropSight is checked at five levels: automated backend tests, measurement of the machine-learning components on their own data, a check of the grader against real "
        "photographs, measured API response times, and a scripted walk-through of the whole product in a real browser. The levels answer different questions. The automated tests ask "
        "whether the code behaves as designed, deterministically and without any external service. The measurements ask how accurate the models are on the data they were built from. "
        "The real-photo check asks whether the grader transfers beyond that data. The latency run asks whether the product is responsive, and the browser walk-through asks "
        "whether a person can use it from sign-up to delivery.",
        "The backend suite is written with pytest and FastAPI's test client. Each run uses a throw-away SQLite file selected through the `DATABASE_URL` setting, seeds the demo accounts, "
        "and builds its own photographs with Pillow (a plain red ellipse on a white table, and the same ellipse covered with dark spots), so no external file is required. The real "
        "feature extractor, the real Random Forest, SHAP and the real price models run in every test; nothing is mocked. The suite contains **39 tests: 36 pass and 3 are expected failures "
        "(xfail)** that assert the behaviour a hardened system should have and fail today, so that known gaps are reported rather than hidden. The full run takes about 30 seconds.")


def sec_unit(d):
    d.h2("Unit Testing")
    d.table([["Test", "What it checks"],
             ["test_feature_vector_contract", "The extractor returns exactly the 11 named features, in order, each in [0, 1]"],
             ["test_blemishes_raise_blemish_ratio_and_edges", "A photograph with dark spots has a higher blemish ratio and edge density than a clean one"],
             ["test_blank_image_does_not_crash", "A 64 x 64 image is graded without error and gives one of the four grades"],
             ["test_grading_is_deterministic", "Grading the same photograph twice gives the same class probabilities"],
             ["test_delivery_weights_sum_to_one", "The five delivery-score weights sum to 1.00"],
             ["test_simulator_is_deterministic_per_seed", "The same shipment seed reproduces the same sensor sequence and a different seed does not"],
             ["test_simulator_bounds_and_anomaly_flag", "Over 800 steps temperature stays in [-5, 35] C, humidity in [20, 98] %, shock is non-negative, and at least one anomaly is flagged"]],
            "Unit tests (7)", widths=[0.4, 0.6], font=9.5)
    d.p("These seven tests cover the pure logic that must be exact: the feature contract between the extractor and the classifier, the monotone effect of blemishes, robustness to degenerate "
        "images, repeatability, and the sensor simulator. Repeatability is checked to a tolerance of 1e-9 because the last binary digit of a floating-point probability can differ between calls.")


def sec_integration(d):
    d.h2("Integration Testing")
    d.p("The remaining 32 tests call the running application through its HTTP interface, so that routing, authentication, validation, the database and the machine-learning services are exercised together.")
    d.table([["Area", "Tests", "What is checked"],
             ["Health and authentication", "8", "Health endpoint; sign-up then log-in then `/auth/me`; duplicate e-mail rejected; the admin role cannot be requested at sign-up; invalid e-mail and short password give 422; wrong password gives 401; protected routes need a token; a tampered token is refused"],
             ["Role guards", "1", "A buyer cannot upload, a farmer cannot order, a non-admin cannot read the admin endpoints, a distributor cannot request delivery plans"],
             ["Listings and grading", "8", "Upload returns a grade among A, B, C, Reject with probabilities summing to 1, 11 features and 1 to 6 SHAP entries; a blemished photo grades no higher than a clean one; wrong content type and oversize files rejected; own listings; publish; foreign or unknown listings give 404"],
             ["Price", "5", "Option lists; response shape (31 forecast days, band contains the estimate, best day 0 to 14, SHAP list); A > B > C > Reject price; the listing's grade overrides the requested grade; unknown crop (xfail)"],
             ["Delivery", "2", "At most five buyers, sorted by a score between 0 and 100, best route equals the top buyer; a farmer cannot plan another farmer's listing"],
             ["Marketplace and orders", "5", "Filtered browsing; a complete order lifecycle (placed, confirmed, in transit, delivered) with every illegal or unauthorised move refused; an unpublished lot cannot be ordered; role-scoped order lists; non-positive quantity (xfail)"],
             ["IoT", "2", "A shipment created through the order flow streams three valid readings over the WebSocket and stores history; an unknown shipment gives 404"],
             ["Admin", "1", "Overview counts; model insights contain both models, 11 importances and the synthetic-data disclosure"]],
            "Integration tests (32 including the 3 expected failures)", widths=[0.2, 0.08, 0.72], font=9)
    d.table([["Group", "Tests", "Passed", "Expected failures"],
             ["Unit", "7", "7", "0"],
             ["Integration (HTTP)", "32", "29", "3"],
             ["**Total**", "**39**", "**36**", "**3**"]],
            "Backend test inventory (pytest, 26 October 2026)", widths=[0.4, 0.2, 0.2, 0.2], font=10, align=["l", "c", "c", "c"])
    d.p("The web application is exercised by the browser walk-through described under functional testing; it is not covered by automated front-end tests.")


def sec_functional(d):
    d.h2("Functional Testing")
    d.p("The functional tests follow the golden path of the product and were run against the live application on 26 October 2026 in Chrome at 1440 x 900, using real tomato, onion and potato photographs and the "
        "demo accounts. The farmer, buyer, distributor and admin steps were driven through the browser interface (Playwright); the extra listings and orders that populate the lists were created "
        "through the same API the interface calls. The screenshots in Chapter 8 are the captures made during this run.")
    d.table([["No.", "Requirement", "Test performed", "Observed"],
             ["F1", "Sign-in with a role-based home", "Log in as farmer, buyer, distributor, admin", "Pass: each role lands on its own dashboard"],
             ["F2", "Reject bad credentials", "Log in with a wrong password", "Pass: the API returns 401 and the page reports it"],
             ["F3", "Grade a crop from a photograph", "Upload `tomato_1.jpg`, tomato, 620 kg", "Pass: grade B, confidence 70.1 %, radar and SHAP bars shown"],
             ["F4", "Forecast the price", "Press Forecast price", "Pass: INR 2,272 per quintal, range 2,068 to 2,272, curve, best day 9 Nov, SHAP drivers"],
             ["F5", "Plan delivery", "Press Plan delivery", "Pass: four buyers ranked, best 67.7 % match (Harvest & Co.), route and transit time"],
             ["F6", "Publish to the marketplace", "Enter 2,250 and publish", "Pass: listing visible to buyers with grade and price"],
             ["F7", "Buyer places an order", "Open listing, place order 620 kg at 2,250", "Pass: order placed, listing becomes sold"],
             ["F8", "Farmer confirms", "Confirm on the orders page", "Pass: status confirmed"],
             ["F9", "Distributor starts transit", "Start transit, open Live monitor", "Pass: shipment created, live traces appear"],
             ["F10", "Cold-chain alert", "Keep the monitor open", "Pass: alert toast at 44.2 s (an injected humidity spike); red banner on at 215 s with temperature 9.5 C and humidity 93.7 %"],
             ["F11", "Admin views", "Open overview and model insights", "Pass with a defect: gross volume is overstated 100 times (price per quintal multiplied by kilograms)"],
             ["F12", "Model transparency", "Open model insights", "Pass: grader shown as 92.3 % accuracy and the synthetic-training disclosure is displayed"]],
            "Functional test cases (live walk-through)", widths=[0.07, 0.25, 0.28, 0.4], font=8.5)
    d.p("Every functional step passed except where a defect is noted, and one observation deserves emphasis: the photographs used in the walk-through were all graded B or A by the shipped grader (every scanned tomato and onion was B, 39 of 40 potatoes B), "
        "which is consistent with the real-photo check of Chapter 6 and means the C and Reject paths were exercised by the automated tests, not by real photographs.")


def sec_security_test(d):
    d.h2("Security Testing")
    d.p("Security testing is limited to the automated tests and a review of the validation paths. The tests confirm that a missing, malformed or tampered token is refused (401); that a "
        "buyer, farmer or distributor cannot reach another role's endpoints (403); that the admin role cannot be created through sign-up; that passwords shorter than six characters and invalid "
        "e-mail addresses are refused (422); that a wrong password fails with a generic message; that duplicate e-mail addresses are refused; that a farmer cannot publish or plan "
        "another farmer's listing (404); and that the order state machine refuses skipped, repeated and unauthorised transitions.")
    d.p("**Findings from the review.** The default signing secret is committed in the configuration file; the sensor WebSocket and the shipment history need no token; any signed-in user can read "
        "any listing; any distributor can start transit on any confirmed order; there is no rate limiting. **Not tested:** penetration testing, token expiry behaviour, HTTPS deployment, cross-site "
        "scripting in the front end, and malicious image files beyond the content-type and size checks.")


def sec_validation(d):
    d.h2("Validation and Edge Cases")
    d.table([["Case", "Behaviour observed", "Result"],
             ["Upload with a text content type", "HTTP 400 `Upload a JPEG, PNG or WEBP image`", "Pass"],
             ["Upload larger than 8 MB", "HTTP 400 `Image too large (max 8MB)`", "Pass"],
             ["Corrupt file sent as `image/jpeg`", "Grader raises, HTTP 500, and a gradeless draft listing remains in the database", "Gap (xfail); later tests found the orphan listing"],
             ["Blank or very small image (64 x 64)", "Foreground mask falls back to the whole image; a valid grade is returned", "Pass"],
             ["Unknown crop or region in a price request", "Priced from an all-zero crop encoding with no error", "Gap (xfail)"],
             ["Order with quantity -50 and price 0", "Accepted; the listing becomes sold", "Gap (xfail)"],
             ["Second order on a sold listing", "HTTP 400 `Listing is not available`", "Pass"],
             ["Order on an unpublished (draft) listing", "HTTP 400", "Pass"],
             ["Skipping a stage (placed to delivered)", "HTTP 400 with the current and requested status", "Pass"],
             ["Reopening a finished shipment", "A new WebSocket restarts the simulator from its seed and writes duplicate history rows", "Observed by design review"],
             ["Unknown shipment history", "HTTP 404", "Pass"]],
            "Validation and edge cases", widths=[0.34, 0.46, 0.2], font=9)
    d.p("The three expected failures are the same three gaps listed in Chapter 6: unvalidated catalogue values, unvalidated order quantity and price, and an unhandled corrupt image. They are kept in the suite "
        "as tests of the desired behaviour, so that fixing the code turns them into passes.")


def sec_performance(d):
    d.h2("Performance Testing")
    d.p("Response times were measured against a live server on the same machine over 127.0.0.1 (an Intel Core i5-12500 with 6 cores and 12 threads, 15.7 GB of memory, no discrete GPU, "
        "Windows 11) while other jobs were running, so the figures are indicative rather than a benchmark. Each request type was repeated 20 to 30 times with real tomato photographs.")
    keys = [("health", "Health check"), ("marketplace_listings", "Marketplace listings"), ("admin_overview", "Admin overview"), ("price_predict", "Price forecast (31 days, band, SHAP)"),
            ("delivery_recommend", "Delivery recommendation"), ("admin_model_insights", "Admin model insights"), ("upload_and_grade", "Upload and grade (photo, features, forest, SHAP, database)"),
            ("login", "Log in (bcrypt verification)")]
    d.table([["Request", "Runs", "Median (ms)", "95th percentile (ms)", "Max (ms)"]] + [[n, str(AL[k]["n"]), f"{AL[k]['median_ms']:.1f}", f"{AL[k]['p95_ms']:.1f}", f"{AL[k]['max_ms']:.1f}"] for k, n in keys],
            "API response times (live server)", widths=[0.42, 0.1, 0.15, 0.19, 0.14], font=9.5, align=["l", "c", "c", "c", "c"])
    sf = PR["served_forecast"]
    d.p(f"Measured inside the process, the price model takes a median of {sf['latency_ms_median']:.1f} ms (95th percentile {sf['latency_ms_p95']:.1f} ms, maximum {sf['latency_ms_max']:.1f} ms) over 256 crop, region and grade "
        f"combinations, and the delivery recommendation a median of {DL['latency_ms_median']:.1f} ms (95th percentile {DL['latency_ms_p95']:.1f} ms). Grading a photograph, the heaviest request, takes about 0.17 s at the median; "
        "log-in is the slowest request at about 0.33 s because bcrypt is deliberately slow. Extracting features from 3,200 full-size fruit photographs and classifying them took about ten minutes (about 0.19 s each, including "
        "decoding), measured while other jobs ran. Both models train in seconds, and the whole backend suite runs in about 30 seconds.")
    d.p("**Not measured:** concurrent users, memory use under load, behaviour with a large database, the front end's load time, and other hardware.")


def sec_uat(d):
    d.h2("User Acceptance Testing")
    d.p("No user-acceptance test with farmers, buyers or distributors was carried out. The walk-through of the previous section was run by the project team and is a functional acceptance run, "
        "not a user study; it shows that the intended flow works, not that real users find it understandable or useful. A pilot in which farmers photograph their own produce and compare the "
        "grade with a trader's, and in which buyers judge the delivery ranking, is the most important piece of future work, and it needs real-labelled data first.")


def sec_test_limits(d):
    d.h2("Limits of the Testing Done")
    d.bullets([
        "The machine-learning results (grader accuracy 92.3 %, price R2 0.992) measure agreement with the synthetic generators that produced the data; the only evidence about real images is the single check on 3,200 fruit photographs, which showed chance-level transfer (accuracy 50.4 %, AUC 0.571).",
        "The real-photo check uses fruits and a binary fresh/rotten label, not the application's crops and A/B/C/Reject grades, and the mapping between them is an assumption.",
        "The price 'forecast' and the buyer offers are generated from hashed values, not market data, and the sensor stream is a simulator; testing shows that the mechanisms work, not that their numbers match reality.",
        "The 39 backend tests use synthetic photographs and a temporary database; there are no automated front-end tests, no load or concurrency tests, no penetration tests and no browser compatibility matrix (Chrome only).",
        "All timing figures come from one machine that was running other jobs, so they vary between runs.",
        "No user study was carried out. Three gaps are known and recorded as expected failures; five further weaknesses (default secret, open WebSocket, broad read access, no rate limiting, the volume-unit error) were found by review rather than by tests.",
    ])
