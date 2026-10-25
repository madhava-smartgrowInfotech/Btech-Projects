"""Chapter 7: System Testing (ResQAI). Every number is read from facts.py (experiments/resqai_eval/*.json)."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, P, TAB
from .refs import CITE as R

RES = F.TESTS["results"]
GRP = F.TESTS["by_group"]


def c(*keys):
    return "[" + ", ".join(str(R[k]) for k in keys) + "]"


def _grp(name):
    return [r for r in RES if r["group"] == name]


def _ok(r):
    return "Pass" if r["passed"] else "**Fail**"


def _short(name, n=88):
    return name if len(name) <= n else name[: n - 1] + "..."


# What each failing edge case means. Keys are substrings of the test name written by scripts/run_tests.py.
FINDINGS = [
    ("non-numeric field gives a client error", "POST /api/predict with {\"acc_x\": \"abc\"}", "HTTP 500 (an unhandled ValueError in float())",
     "A malformed field from a faulty client crashes the request instead of returning 400; the React app never sends one, so the screens are not affected.", "Wrap the conversion and answer 400 with the field name."),
    ("JSON array body gives a client error", "POST /api/predict with [1, 2, 3]", "HTTP 500 (the array has no .get)",
     "Same class of fault: the body is assumed to be an object.", "Reject non-object bodies with 400."),
    ("non-numeric lat gives a client error", "GET /api/hospitals?lat=abc", "HTTP 500",
     "A hand-typed URL can crash the request.", "Parse with error handling; answer 400."),
    ("k=-1", "GET /api/hospitals?k=-1", "HTTP 200 with 9 of 10 hospitals (the Python slice [:-1])",
     "Wrong, not harmful: a negative count is accepted and silently means 'all but the last'.", "Clamp k to 1..10."),
    ("out-of-range coordinates", "GET /api/hospitals?lat=999&lon=999", "HTTP 200, hospitals ranked from an impossible point",
     "No range check, so nonsense input gives nonsense output without a warning.", "Check |lat| <= 90 and |lon| <= 180."),
    ("non-numeric confidence", "POST /api/emergency with {\"confidence\": \"abc\"}", "HTTP 500",
     "The dispatch route crashes on a bad number; the React app always sends a float.", "Validate and answer 400."),
    ("severity_label is validated", "POST /api/emergency with a free-text severity_label containing a line break", "HTTP 200, the text is copied into the dispatch message",
     "The message could carry arbitrary text supplied by the caller. The React app sends only the four labels, and the message is shown as plain text, so the effect on the screens is nil, but a future SMS gateway would forward it.", "Accept only None / Minor / Moderate / Severe."),
    ("same second", "Two POST /api/emergency calls within one second", "Both return the same alert id (RQ-<unix seconds>)",
     "Two genuine alerts in one second would be indistinguishable and could overwrite each other once alerts are stored.", "Use a UUID or a counter."),
]


def blocks():
    sm_t, sm_p = F.SMOKE_TOTAL, F.SMOKE_PASSED
    e = F.ENDPOINTS
    ap = F.ALERT_PATH
    fails = [r for r in RES if not r["passed"]]
    u, ed, sc = GRP["unit"], GRP["edge"], GRP["security"]
    b = [H1("CHAPTER 7: SYSTEM TESTING")]

    # ------------------------------------------------------------------------------------------ 7.1
    b += [H2("7.1 Testing Strategy"),
          P("ResQAI was tested in five layers. Single functions of the backend (distance calculation, feature-vector construction, the rule-based fallback, the simulator) are tested in isolation; "
            "the API is exercised over HTTP against a running server; the whole stack, including the React web server and its proxy, is driven by the smoke test that ships with the application; "
            "security and input validation were probed with a second script written for this report; and the two classifiers were measured on held-out events, which Chapter 8 reports. "
            f"Every screen was also walked in a real browser while the screenshots of Chapter 8 were captured; that script stops with an error if the browser console shows an error or a failed request."),
          P(f"The automated checks are {sm_t} in scripts/smoke_test.py (shipped with the application) and {F.TEST_TOTAL} in scripts/run_tests.py (unit, edge-case and security checks). "
            f"{F.TEST_PASSED} of the {F.TEST_TOTAL} pass. The {len(fails)} that fail are not hidden or fixed away: they are recorded in Section 7.6 as findings, because a test script that was edited until it passed would say nothing about the application."),
          P("What the tests establish is that the code behaves as designed on the cases tried. They do not establish that the system would detect real crashes on real roads: the models were trained and tested on synthetic events, "
            "no phone was attached, and no user study was run. Section 7.10 states the limits plainly."),
          TAB("Test layers and results", ["Layer", "What it covers", "How", "Result"], [
              ["Unit", "haversine distance, nearest-hospital ranking, feature-vector derivation, rule-based fallback, health route, simulator-to-model consistency", "scripts/run_tests.py, in-process (Flask test client)", f"{u['passed']} of {u['total']} pass"],
              ["Integration", "accounts and login, every simulated scenario through /api/predict, hospitals, emergency, front-end shell served through the Vite proxy", "scripts/smoke_test.py over HTTP on port 5302", f"{sm_p} of {sm_t} pass"],
              ["Functional", "five scenarios, manual override, 15-second countdown, cancel, dispatch, map, theme, sign-out", "scripts/capture_screens.py and capture_extra_screens.py (Playwright, real Chrome)", "All screens reached; no console errors in the main run"],
              ["Security", "token guard with REQUIRE_AUTH=1, tampered token, lock-out after five failures, hash storage, ignored secret files", "scripts/run_tests.py against a second server on port 8399", f"{sc['passed']} of {sc['total']} pass"],
              ["Validation and edge cases", "empty, malformed, non-numeric, NaN, huge and out-of-range input; id uniqueness", "scripts/run_tests.py against port 8302", f"{ed['passed']} of {ed['total']} pass; {ed['total'] - ed['passed']} findings"],
              ["Performance", "latency per endpoint, alert path, new connections, single-client throughput, in-process model call", "scripts/measure_api.py, scripts/measure_metrics.py", "Measured (Section 7.7)"],
          ], widths=[1.1, 2.5, 1.7, 1.2], align=["l", "l", "l", "l"], size=9)]

    # ------------------------------------------------------------------------------------------ 7.2
    rows = [[str(i), _short(r["name"], 92), _ok(r)] for i, r in enumerate(_grp("unit"), 1)]
    b += [H2("7.2 Unit Testing"),
          P(f"The unit group has {u['total']} checks and all pass. They import app.py directly and call its helper functions or its routes through Flask's test client, so no server is needed. "
            "The distance function is checked for the zero case, for symmetry and against a known pair of cities: London to Paris comes out at "
            "343.6 km, which agrees with the published great-circle distance of about 343 km. The nearest-hospital ranking is compared with a brute-force sort on 500 random points around the default location; "
            "the top three distances match every time (the comparison is at the two-decimal precision at which the application sorts, because rounding can swap two hospitals that are a few metres apart)."),
          P("The feature-vector builder is checked on three inputs: a payload of (3, 4, 0) must give an acceleration magnitude of exactly 5; a negative jerk must be stored as its absolute value; and an empty payload must default to a stationary reading of 1 g (9.81 m/s2) "
            "with a vector of 11 values in the order the models were trained on. The rule-based fallback is checked at four magnitudes (10, 20, 30 and 60 m/s2), which must give None, Minor, Moderate and Severe."),
          P(f"The last five checks tie the simulator to the models. For each of the five scenarios, 60 readings are drawn from /api/simulate and sent to /api/predict; all 60 are rated as the scenario they were generated as. "
            "This is a consistency check between the generator in app.py and the one in train_models.py, not an accuracy measurement on independent data; it passes because the two generators use the same parameters."),
          TAB("Unit checks (scripts/run_tests.py, group 'unit')", ["No.", "Check", "Result"], rows, widths=[0.4, 5.0, 0.7], align=["c", "l", "c"], size=9)]

    # ------------------------------------------------------------------------------------------ 7.3
    b += [H2("7.3 Integration Testing"),
          P(f"The smoke test (scripts/smoke_test.py) is the integration test of the application. It runs against the Vite server on port 5302, which proxies /api to the Flask server on 8302, so a pass proves the front-end wiring as well as the API. "
            f"It makes {sm_t} checks and all {sm_p} pass (output saved in experiments/resqai_eval/smoke_test.txt)."),
          B("**Health (1 check).** /api/health reports status ok and models_loaded."),
          B("**Accounts (8 checks).** A short password and a malformed e-mail are rejected with HTTP 400 and the offending field name; a valid registration returns 201 and a token; a duplicate e-mail is refused with 409; a wrong password gives 401; login returns a token; /me returns the signed-in user; a garbage token is refused."),
          B("**Detection (15 checks).** For each of the five scenarios the reading carries all four derived keys, and the prediction has the full response shape. Normal driving is not an accident and a severe crash is detected as Moderate or Severe. "
            "Then 40 more readings of each crash scenario are generated and each scenario must be rated as its own severity in at least 36 of 40 cases; the observed result was 40 of 40 for Minor, Moderate and Severe."),
          B("**Manual input (1 check).** The payload that the Manual override screen builds, with a calm reading, predicts no accident."),
          B("**Response (6 checks).** The hospital list returns five entries sorted by distance; the emergency route dispatches with an id that starts with RQ-, lists three hospitals, names the severity in the message and carries 112 and 108; a call without coordinates falls back to a server-side location."),
          B("**Front end (1 check).** The Vite server serves the application shell (the page that holds the React root)."),
          P("The smoke test also passes when the server is started with REQUIRE_AUTH=1, because it sends its token on every call; it detects that mode from /api/auth/status and adds one extra check that an unauthenticated call is refused.")]

    # ------------------------------------------------------------------------------------------ 7.4
    pk = F.SHIP["per_event_kind"]
    b += [H2("7.4 Functional Testing"),
          P("Functional testing followed the use cases of Chapter 5. The Playwright script signs in through the real login form (creating the demo account on the first run), then presses every scenario button, starts and stops live monitoring, "
            "lets the 15-second dialog run for three seconds and presses Send alert now, opens the response map, types values on the manual override screen, switches the theme, reloads the response page and finally signs out, "
            "after which it checks that /response redirects back to the login form. It fails if the browser console shows an error, a page error or a failed request (HTTP 401 and 409 from the auth form and map tiles are excluded, because they are the designed error path or a third-party service)."),
          TAB("Functional cases and observed behaviour", ["Case", "Action", "Observed"], [
              ["Calm drive", "Press Normal driving", "Result 'No accident', severity None, probability 0 %; no dialog"],
              ["Hard braking", "Press Harsh brake", f"'No accident' (0 of {pk['harsh_brake']['n']} held-out braking events were flagged in the batch test)"],
              ["Minor crash", "Press Minor crash", "'Accident detected', severity Minor; logged in the event log; no countdown (screen 16)"],
              ["Moderate crash", "Press Moderate crash", "Dialog 'Possible accident detected'; live monitoring pauses; cancelling logs 'User confirmed they are OK. Alert cancelled.' (screen 17)"],
              ["Severe crash, send now", "Press Severe crash, then Send alert now", "Alert id RQ-..., dispatch dialog, map with accident and hospital markers (screens 09-11)"],
              ["Countdown expiry", "Leave the dialog alone for 15 s", "The alert is sent automatically at 0 s (code path in MonitorContext; the screenshot run presses the button instead of waiting)"],
              ["Cancel by keyboard", "Press Escape during the countdown", "Counted as a response and cancels the alert (the dialog states this)"],
              ["Manual values", "acc_x 32, acc_y 18, speed change -45, jerk 40", "Derived magnitude 38.00 m/s2, result Moderate (screen 12)"],
              ["Live monitoring", "Start live monitoring for 7 s", "One reading every 1.5 s, sensor trace fills; a Moderate or Severe draw pauses monitoring and opens the dialog"],
              ["Sign-out and guard", "Sign out, then open /response", "Redirected to /login; the console is locked again"],
              ["Unknown route", "Open /no-such-page", "The 404 page (screen 18)"],
          ], widths=[1.3, 2.0, 3.0], align=["l", "l", "l"], size=9),
          P("One behaviour is worth noting because it is easy to misread in a demonstration: closing the dialog with the cross, or pressing Escape, cancels the alert in the same way as the cancel button, while a click outside the dialog does not close it; "
            "and only Moderate and Severe events open it. A Minor crash is flagged as an accident but, by design, never contacts anyone.")]

    # ------------------------------------------------------------------------------------------ 7.5
    srows = [[str(i), _short(r["name"], 96), _ok(r)] for i, r in enumerate(_grp("security"), 1)]
    b += [H2("7.5 Security Testing"),
          P(f"Security checks ran against a second backend started with REQUIRE_AUTH=1 on port 8399. All {sc['total']} checks pass. With the guard on, /api/predict, /api/simulate, /api/hospitals and /api/emergency each answer 401 without a token while /api/health stays public; "
            "a valid token opens them; a token whose signature has been altered and an Authorization header that is not a Bearer token are both refused."),
          P(f"Account handling behaves as designed. A registration never echoes the password or its hash; /me never exposes the hash; a one-character name and a 200-character password are rejected; the same e-mail in capitals is treated as a duplicate (409). "
            f"Five wrong passwords in a row each return 401, and the sixth attempt with the *correct* password is refused with 429 for five minutes, so a guessing attack is slowed. Stored passwords begin with scrypt:32768:8:1, the scrypt key-derivation function {c('scrypt')}, "
            "with a per-user salt. The signing key comes from SECRET_KEY or from data/.secret, and .env, data/users.json and data/.secret are in .gitignore."),
          TAB("Security checks (scripts/run_tests.py, group 'security')", ["No.", "Check", "Result"], srows, widths=[0.4, 5.0, 0.7], align=["c", "l", "c"], size=9),
          P("These results show that the access-control logic works as coded. They are not a penetration test: transport encryption is out of scope for a loopback demonstration, the lock-out counter is kept in the memory of one process, "
            "tokens are valid for 12 hours with no revocation list, and the default setting (REQUIRE_AUTH=0) leaves the API open so that the original Flask page keeps working. "
            "Anyone deploying the system would have to turn the guard on and put it behind HTTPS.")]

    # ------------------------------------------------------------------------------------------ 7.6
    frows = []
    for key, req, obs, cons, fix in FINDINGS:
        hit = next((r for r in fails if key in r["name"]), None)
        frows.append([req, obs, cons, fix])
    assert len(frows) == len(fails), (len(frows), len(fails))
    passed_edge = [r for r in _grp("edge") if r["passed"]]
    b += [H2("7.6 Validation and Edge Cases"),
          P(f"The edge-case group sends {ed['total']} unusual requests to the open API. {ed['passed']} are handled acceptably and {ed['total'] - ed['passed']} are not. "
            "Handled acceptably: an empty object defaults to a calm reading and predicts no accident; malformed JSON gives HTTP 400; NaN is answered without a crash (no accident, probability 0); absurdly large values (1e9 on three axes) and a negative speed are still answered; "
            "a GET on a POST-only route gives 405; an unknown scenario falls back to a random one; k = 0 returns an empty list and k = 1000 is capped at the ten hospitals in the directory; "
            "an emergency call with no body falls back to the default area and dispatches; the dispatch message carries a map link and lists the nearest hospital first; and alert ids raised a second apart differ."),
          P("The eight failures are all input-validation gaps in app.py. They were found by the test script, not fixed, because this stage of the work documents the system as built. None of them can be triggered from the React screens, "
            "which send well-formed numbers and one of four fixed labels, but each is reachable by anyone who calls the API directly."),
          TAB("Findings from the edge-case checks", ["Request", "Observed", "Consequence", "Suggested fix"], frows, widths=[1.5, 1.4, 2.3, 1.2], align=["l", "l", "l", "l"], size=8.5),
          P("The large-value case deserves a remark of its own. With acceleration of 1e9 m/s2 the classifier answers 'Minor', not 'Severe', because the values lie far outside the range the forests have seen and tree models extrapolate flat; "
            "the answer is not an error, but it shows that an absurd reading is not recognised as absurd. A plausibility check on the physical range of a phone accelerometer (a few tens of m/s2) would catch it before the model.")]

    # ------------------------------------------------------------------------------------------ 7.7
    b += [H2("7.7 Performance Testing"),
          P(f"Latency was measured on 127.0.0.1 (using 'localhost' adds about two seconds per call on this Windows machine because of an IPv6 fall-back) against the Flask development server, one process, debug mode on, from a single Python client with a persistent connection. "
            "The machine was an Intel Core i5-12500 with no GPU and 15.7 GB of RAM, and during the measurements other programs held most of the memory, so the figures are conservative rather than best-case. "
            f"Each endpoint was called {e['POST /api/predict']['n']} times after a 20-call warm-up."),
          TAB("API latency in milliseconds (loopback)", ["Endpoint", "Mean", "Median", "95th pct", "99th pct", "Max"], [
              [k.replace("?k=3", " (k = 3)"), f"{v['mean']:.2f}", f"{v['p50']:.2f}", f"{v['p95']:.2f}", f"{v['p99']:.2f}", f"{v['max']:.2f}"] for k, v in e.items()
          ] + [[f"Alert path: simulate + predict + emergency (n = {ap['n']})", f"{ap['mean']:.2f}", f"{ap['p50']:.2f}", f"{ap['p95']:.2f}", f"{ap['p99']:.2f}", f"{ap['max']:.2f}"],
               [f"POST /api/predict on a new connection (n = {F.LAT['predict_new_connection_ms']['n']})", f"{F.LAT['predict_new_connection_ms']['mean']:.2f}", f"{F.LAT['predict_new_connection_ms']['p50']:.2f}", f"{F.LAT['predict_new_connection_ms']['p95']:.2f}", f"{F.LAT['predict_new_connection_ms']['p99']:.2f}", f"{F.LAT['predict_new_connection_ms']['max']:.2f}"]],
              widths=[2.7, 0.65, 0.7, 0.75, 0.75, 0.65], align=["l", "r", "r", "r", "r", "r"], size=9),
          FIG(F.fig("f08_api_latency.png"), "Mean and 95th-percentile latency of each endpoint and of the three-call alert path.", 5.0),
          P(f"Calling the two forests directly in the same process takes {F.INF['mean']:.2f} ms on average (median {F.INF['p50']:.2f}, 95th percentile {F.INF['p95']:.2f}, 99th {F.INF['p99']:.2f} ms; {F.INF['n']} calls), "
            f"so about half of the {e['POST /api/predict']['mean']:.1f} ms that /api/predict takes over HTTP is model evaluation and the rest is the web server and JSON handling. "
            f"The three calls of one alert (reading, prediction, dispatch) take {ap['mean']:.1f} ms on average. A single client sustains {F.LAT['predict_throughput_req_per_s_single_client']} prediction requests per second. "
            "The pickled models are small (the detector 385.5 KB, the severity model 2,608.2 KB), so start-up is quick and memory use is low."),
          P("Three cautions apply. The latency of the alert path excludes the deliberate 15-second confirmation window, which dominates the time to an alert by three orders of magnitude, and it excludes the time to deliver a real message, which is not measured because nothing is sent. "
            "The timings show steps of about 15 ms because of the operating-system timer, so differences of a few milliseconds are not meaningful. And no load or concurrency test was run: the development server is single-process and was not designed for many simultaneous users.")]

    # ------------------------------------------------------------------------------------------ 7.8
    nz = {r["noise_sd_fraction_of_feature_sd"]: r for r in F.NOISE}
    b += [H2("7.8 Robustness Testing"),
          P("Two further tests probe behaviour outside the clean test split; Chapter 8 analyses them in detail. In the noise test the nine raw sensor channels of the 2,400 test events are perturbed with zero-mean Gaussian noise whose standard deviation is a fraction of each feature's own standard deviation. "
            f"Up to 10 % the detector is unaffected (false-alarm rate {F.pct(nz[0.1]['det_false_alarm'])}); at 25 % it begins to fail ({F.pct(nz[0.25]['det_false_alarm'])} false alarms); at 50 % it raises {F.pct(nz[0.5]['det_false_alarm'])}; at 100 % it is wrong more often than right (detector accuracy {F.pct(nz[1.0]['det_accuracy'])}). "
            "The models were never trained with noise, so this is a measure of how far the synthetic separation can be trusted, not of a tuned system."),
          P(f"In the road-surface probe, 1,000 pothole-like and 1,000 speed-breaker-like events that the training generator never produces were sent through the models. The detector flags {F.pct(F.OOD['pothole']['predicted_accident_rate'])} of the pothole-like and {F.pct(F.OOD['speed_breaker']['predicted_accident_rate'])} of the speed-breaker-like events as accidents, "
            f"but none ({F.pct(F.OOD['pothole']['alert_trigger_rate'])} and {F.pct(F.OOD['speed_breaker']['alert_trigger_rate'])}) is graded Moderate or Severe, so none would start the countdown. The events were constructed for this report from our own parameter choices; they are not real recordings."),
          FIG(F.fig("f05_noise_robustness.png"), "Detector F1, severity macro-F1 and detector false-alarm rate as sensor noise grows.", 5.0)]

    # ------------------------------------------------------------------------------------------ 7.9
    b += [H2("7.9 User Acceptance Testing"),
          P("No user acceptance test was carried out. No driver, rider, paramedic or hospital staff member used the system, no questionnaire was issued and no usability metric (task time, error rate, satisfaction) was collected. "
            "The only people who operated the application were the project team, and they wrote it; their walk-through is useful for finding defects, as Section 7.4 shows, but it is not acceptance testing."),
          P("What a real acceptance test would need is described in Chapter 10: a phone application that records genuine motion data, a protocol for staged low-speed impacts and for ordinary rough roads, "
            "agreement with a responsible emergency service about receiving automated alerts, and a trial in which volunteers press (or fail to press) the cancel button under realistic stress. "
            "Until that is done the confirmation window of 15 seconds is a design choice taken from the project brief, not a value validated with users.")]

    # ------------------------------------------------------------------------------------------ 7.10
    b += [H2("7.10 Limits of the Testing Done"),
          B("**Synthetic data throughout.** The classifiers were tested on events drawn from the same generator that trained them, so the scores in Chapter 8 measure separability by construction. There are no real phone recordings, and no crash, pothole or speed-breaker data from a vehicle."),
          B("**Simulated sensors and location.** The readings come from /api/simulate, and the position comes from the browser or, if it is refused, from a random point near the default location. No GPS accuracy was tested."),
          B("**No delivery.** Nothing is sent to a phone, a hospital or an ambulance service, so alert delivery and end-to-end time to help were not and could not be measured."),
          B("**No concurrency, endurance or battery tests.** One client was used; the server was the development server; no long-running monitoring, mobile CPU or battery measurement was made."),
          B("**Input validation gaps remain.** Eight edge cases fail (Section 7.6); the checks were not extended to every parameter of every route."),
          B("**Small, self-written suites.** The 55 checks of run_tests.py and the 33 of the smoke test were written by the project team for this application; they are not an independent audit, and there is no coverage measurement."),
          B("**Single environment.** All runs were on one Windows 11 machine with scikit-learn 1.5.0 loading pickles that were written by version 1.9.0. A fresh retraining with the same seed agrees with the shipped models on every one of the 2,400 test events, which removes the main worry, but other platforms were not tried.")]
    return b
