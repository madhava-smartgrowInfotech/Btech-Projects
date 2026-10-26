"""Chapter 7: System Testing. Counts and timings come from facts.py (docs/metrics/edge_tests.json, experiments/plantdoc/latency.json)."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, TAB

LAT = F.LAT
EDGE = F.EDGE
ROWS = EDGE["rows"]          # [group, status, label]
DC, DS = LAT["detect_client_ms"], LAT["detect_server_ms"]


def _n(group, status):
    return sum(1 for g, s, _ in ROWS if g == group and s == status)


def _row_text(group, startswith):
    for g, s, label in ROWS:
        if g == group and label.startswith(startswith):
            return s
    raise KeyError(startswith)


# the 39 checks of scripts/smoke_test.py, grouped as they appear in the script
SMOKE_GROUPS = [
    ("Public endpoints and knowledge base", 6, "health reports 38 classes and names the engine; the disease guide lists 38 entries, each with chemical, organic and cultural treatments; detail by class name; an unknown disease is 404"),
    ("Accounts and profile", 10, "history needs sign-in (401); wrong password 401; demo login; /auth/me; register; duplicate email 409; invalid email 400; short password 400; profile update saves language and crops; unsupported language 400"),
    ("Detection upload", 6, "detect needs sign-in; a .txt file is rejected; a corrupt image is rejected cleanly; a valid photo returns a result with top-3; confidence in (0, 1] and a valid severity; three treatments returned"),
    ("Result detail and ownership", 4, "result detail loads; it holds top-3 and the crop; the stored leaf image is served; another user cannot open the result (404)"),
    ("History search and filters", 4, "the new scan is listed; a search with no match is empty; a search by disease name finds it; healthy plus diseased filters add up to all scans"),
    ("Exports", 3, "single-record CSV; single-record PDF (%PDF header); all-history CSV"),
    ("Dashboard and analytics", 3, "analytics totals equal the history count and the severity counts add up; the timeline adds up; dashboard totals and recent list"),
    ("Deletion", 3, "another user cannot delete the result (404); delete removes the record; the deleted result is gone"),
]


def blocks():
    n_pass_unit, n_def_unit = _n("unit", "PASS"), _n("unit", "DEFECT")
    n_pass_api, n_def_api = _n("api", "PASS"), _n("api", "DEFECT")
    sm_total = sum(c for _, c, _ in SMOKE_GROUPS)
    assert sm_total == F.N_SMOKE, sm_total

    out = [
        H1("CHAPTER 7: SYSTEM TESTING"),
        P("This chapter describes how AgriVision was tested, what the tests found and what they did not cover. Two kinds of testing are kept apart. Software testing asks whether the application "
          "does what its interface promises (accounts, upload, history, exports, security of the API). Model testing asks whether the diagnosis is right; that is measured on the PlantDoc test "
          "photographs and reported in Chapter 8. Every count in this chapter was produced by a script in `8.ProjectCode/scripts/` that can be run again."),
        H2("7.1 Testing strategy"),
        P(f"The application has three layers (Chapter 5): a React interface, a FastAPI service and the original Flask product modules `inference.py` and `disease_db.py` over one SQLite database. "
          f"The tests follow the same layers. Unit-level checks call the Python modules directly. Integration and security checks start a private copy of the API on its own port with a throw-away "
          f"database and upload folder, so the real demo account in `agrivision/agrivision.db` is never touched. Browser checks drive the built interface in headless Chrome. All three kinds were "
          f"written for this project; no third-party test framework such as pytest was used, each script prints PASS or FAIL per check and exits non-zero if any check fails."),
        TAB("Test scripts and what each one counts", ["Script", "Layer", "Checks", "Result"],
            [["`scripts/edge_tests.py` (part 1)", "Python modules, in process", str(F.N_UNIT), f"{n_pass_unit} pass, {n_def_unit} reproduce a defect"],
             ["`scripts/smoke_test.py`", "FastAPI service, own server on port 18416", str(F.N_SMOKE), f"{F.N_SMOKE} pass"],
             ["`scripts/edge_tests.py` (part 2)", "FastAPI service, own server on port 18417", str(F.N_API), f"{n_pass_api} pass, {n_def_api} reproduce a defect"],
             ["`scripts/ui_checks.py`", "Built React interface in Chrome", str(F.N_UI), f"{F.N_UI} passed at the end of the frontend session; not re-run for this report"],
             ["`scripts/measure_api.py`", "Latency on 127.0.0.1", "-", "100 detect calls and 40 calls per other endpoint"],
             ["`scripts/run_experiments.py`", "Model accuracy (Chapter 8)", "-", "5 hash seeds for the heuristic, 3 training seeds for each network"]],
            widths=[2.1, 2.1, 0.7, 1.9], align=["l", "l", "c", "l"], size=9.5),
        P(f"A check that exposes a defect of the product is reported as DEFECT, not as PASS and not hidden: {F.N_EDGE_DEFECT} of the {F.N_EDGE} checks of `edge_tests.py` do so (Section 7.8)."),

        H2("7.2 Unit testing"),
        P(f"The unit part of `edge_tests.py` imports `disease_db.py` and `inference.py` and runs {F.N_UNIT} checks. They fall into three groups."),
        B("**Knowledge base** (7 checks): there are exactly 38 distinct classes; `get_disease_info` returns the requested class and falls back to Tomato healthy for an unknown label; every card has all eight fields "
          "(name, crop, severity, symptoms, treatments, prevention, lifecycle, urgent); healthy classes have severity none and are flagged healthy; diseased classes are not; the urgent flag equals severity high.",
          "**Label mapping and crop hints** (6 checks): all 28 PlantDoc folder names map onto canonical classes one-to-one; every crop option has at least one candidate class; the hint 'general' or an empty hint keeps all 38 "
          "classes; the hint is tolerant of case and spaces; 'maize' and 'corn' give the same candidates.",
          "**Heuristic engine** (8 checks): the same image gives the same output in the same process; the confidence floor of 0.62 holds; a plain green image is called healthy with confidence above 0.9; a 12-megapixel image is "
          "analysed in under 5 s; an RGBA PNG is accepted; garbage bytes raise an exception that the API turns into an error answer; two checks that fail by design are described below."),
        P(f"Of the {F.N_UNIT} unit checks, {n_pass_unit} pass and {n_def_unit} reproduce defects. The first is **D2**: the three scores shown for a photograph are meant to be class probabilities but add up to more than "
          f"102 % on {F.pct(F.HCONF['share_sum_over_102'], 0)} of the {F.HCONF['n']} test photographs the heuristic can answer, with a maximum of {F.pct(F.HCONF['max_sum'], 0)}. (The edge test, which samples every fourth test photograph "
          "of all crops, found 92 % of 59 photographs above 102 %; the larger sample in Chapter 8 is the one used throughout the report.) The second is **D1**: for every crop option that leaves fewer than three "
          "candidate classes the engine raises `IndexError` (Section 7.6)."),

        H2("7.3 Integration testing"),
        P(f"`smoke_test.py` walks one user through the whole API on a private server: it logs in as the demo farmer, registers a second user, uploads a real PlantDoc photograph (Tomato late blight, or a synthetic "
          f"leaf if the dataset is absent), reads, filters, exports and deletes the result, and checks that a second user can neither read nor delete it. It contains {F.N_SMOKE} checks and all of them pass."),
        TAB("The 39 integration checks of smoke_test.py by group", ["Group", "Checks", "What is verified"], [[g, str(c), t] for g, c, t in SMOKE_GROUPS] + [["Total", str(sm_total), "all pass"]],
            widths=[1.8, 0.7, 4.3], align=["l", "c", "l"], size=9),
        P("Because the script exercises the real FastAPI routes, the real SQLite file and the real upload folder, it also covers the contract between the new FastAPI layer and the unchanged Flask modules "
          "(`init_db`, `get_disease_info`, `predict`) described in Chapter 5. It does not exercise the Flask pages on port 5000, which remain as shipped."),

        H2("7.4 Functional testing"),
        P(f"Functional behaviour of the screens was tested with `ui_checks.py`, a Playwright script with {F.N_UI} checks run against the production build of the interface (`vite preview`). It seeds three scans through the API, "
          "runs each section in a fresh headless Chrome and removes the scans afterwards. The script covers:"),
        B("**Layout**: no sideways scroll on 10 routes (landing, disease guide, disease detail, dashboard, detect, history, analytics, profile, a result page and the not-found page) at 360, 768 and 1440 px, the last in light theme; "
          "the public login and register pages at 360 and 768 px.",
          "**Navigation at phone width**: the sidebar is hidden, the menu button opens a drawer, Escape closes it, the bottom quick-navigation bar is visible.",
          "**History**: it lists the seeded scans; a search with no match shows an empty state with a clear-filters action; clearing the filters brings the cards back; the healthy/diseased segments change the list; "
          "the delete dialog is cancelled by Escape and confirming removes exactly one record.",
          "**Preferences**: the light and dark theme choices persist after a reload; the Hindi switch translates the page title and switching back to English works; saving the profile shows success feedback.",
          "**Input and access**: the first Tab stop is the skip link; a .txt file is rejected and the Diagnose button stays disabled; a signed-out visitor is sent to the login page; a wrong password shows the API's message; "
          "after signing in the user returns to the page they wanted.",
          "**Console**: no console errors, page errors or failed requests during the whole walk."),
        P(f"All {F.N_UI} checks passed when the script was last run, at the end of the interface build (25 October 2026). It needs both servers and a slow software-rendered browser, so it was **not re-run** while this report "
          "was written; the figure is quoted as a result of that earlier run. The screenshots in Chapter 8 were captured in a separate run of the same interface and show the same behaviour."),
        P("The functional requirements of Chapter 4 map onto the tests as follows."),
        TAB("Functional requirements and the checks that cover them", ["Requirement", "Covered by"],
            [["Register, sign in, stay signed in for seven days, sign out", "smoke_test (accounts); edge_tests (forged, malformed and expired tokens); ui_checks (login redirect)"],
             ["Upload a leaf photo with a crop, receive top-3, severity and treatments", "smoke_test (detection); edge_tests (formats, sizes, crop hints); ui_checks (rejects a .txt file)"],
             ["Browse the 38-disease guide without signing in", "smoke_test (public endpoints); ui_checks (overflow on /encyclopedia and /disease)"],
             ["Search, filter, delete and export scans", "smoke_test (history, exports, deletion); ui_checks (empty state, filters, delete dialog)"],
             ["Dashboard and analytics", "smoke_test (totals and timeline add up); ui_checks (overflow on both pages)"],
             ["Profile, language (en, hi, mr) and theme", "smoke_test (profile update); ui_checks (language and theme)"],
             ["Fertiliser, yield and weather advice, voice input, administrator dashboard", "not implemented, so not tested (Chapter 10)"]],
            widths=[3.2, 3.6], align=["l", "l"], size=9.5),

        H2("7.5 Security testing"),
        P(f"The API part of `edge_tests.py` ({F.N_API} checks) probes authentication, upload handling, injection-style input and cross-origin access. {n_pass_api} pass and {n_def_api} reproduce a defect."),
        TAB("Security and robustness checks of the API", ["Area", "Checks", "Outcome"],
            [["Token handling", "forged signature; malformed token; non-bearer header; validly signed but expired token", "all refused with 401"],
             ["Token secret", "token signed with the default development secret", "**accepted** (defect D3)"],
             ["Upload validation", ".JPG and .webp accepted; empty file 400; no extension 400; 11 MB file 413; '../../evil.jpg' stays inside the upload folder", "all as intended"],
             ["Injection-style input", "SQL text in `crop_type` and in the history search box", "stored or matched as plain data; the results table keeps working"],
             ["Input validation", "limit 0, limit 101 and offset -1 on /history; login and register with no body", "422 / 401 / 400 as intended"],
             ["File serving", "path traversal in /uploads/; a missing upload", "404 in both cases; stored images are served without a token (the random file name is the capability)"],
             ["Cross-origin access", "origin http://localhost:5416 and a foreign origin", "local origin allowed, foreign origin not"],
             ["Passwords", "database column of the demo user", "salted scrypt hash, not the clear text"],
             ["Brute force", "8 wrong passwords in a row", "all answered in 2.8 s: **no rate limiting** (defect D4)"]],
            widths=[1.3, 3.4, 2.1], align=["l", "l", "l"], size=9),
        P("Two security properties deserve a plain statement. First, the session token is an HMAC-SHA256-signed payload (user id and expiry) kept in the browser's local storage, not an industry-standard JSON Web Token library; "
          "it is checked with a constant-time comparison. Its secret defaults to the string `agrivision-dev-secret-change-me` in `config.py`, which is public, so anyone who knows a user id can forge a valid token unless the "
          "environment variable `AGRIVISION_SECRET` is set (**D3**). Second, there is no limit on login attempts (**D4**). Neither matters for a single-PC demonstration, both must be fixed before the system is exposed on a network."),

        H2("7.6 Validation and edge cases"),
        P("Validation tests ask what happens at the borders of the input. The behaviours found are listed below."),
        B("**Image formats and size.** JPG, JPEG, PNG and WEBP up to 10 MB are accepted; the extension check is case-insensitive; a file named `notes.txt`, a file with no extension and an empty file are refused with 400; a "
          "corrupt image with a good extension is refused with 400; an 11 MB upload is refused with 413. A WEBP upload is saved with a .png extension although its bytes are not converted.",
          "**Unusual images.** An RGBA PNG and a 12-megapixel JPEG are analysed without error (the latter in under 5 s). A plain green square is called healthy with a displayed confidence above 90 %, which shows that the "
          "displayed confidence is a property of the colour statistics and not of the evidence for a disease.",
          "**Crop options (defect D1).** The engine accepts 19 crop keys (the web form offers 18 of them, without 'citrus'). For ten of them (blueberry, cherry, orange, citrus, peach, bell pepper, raspberry, soybean, squash, strawberry) the knowledge base has fewer "
          "than three classes, so the code that fills the top-3 list raises `IndexError`; the API catches every exception and answers HTTP 400 `UNREADABLE_IMAGE`, 'That file could not be read as an image', for a perfectly "
          f"valid photograph (screenshot 16 in Chapter 8). On the PlantDoc test split this affects {F.pct(F.HC['failed_share']['mean'])} of the photographs when the right crop is chosen. Choosing 'general' avoids the error.",
          "**Unknown crop text.** A crop value that is not in the alias table (including SQL text) falls back to all 38 classes and is stored as data.",
          "**Empty crop list in the profile.** It falls back to tomato, the same default as the original Flask form.",
          "**Other users' data.** Another user's result id gives 404 for read, delete and export."),
        FIG(F.fig("f06_crop_candidates.png"), "Candidate classes per crop option; crops under the dashed line of three make the heuristic raise an error (defect D1).", 4.8),

        H2("7.7 Performance testing"),
        P(f"`measure_api.py` starts its own server on 127.0.0.1 (using the loopback address matters on this PC, where the name 'localhost' adds about two seconds per call), warms it up with five uploads and then "
          f"times 100 real PlantDoc photographs (median size {LAT['upload_kb']['median']:.0f} KB, 95th percentile {LAT['upload_kb']['p95']:.0f} KB) and 40 calls to each read endpoint. Start-up to the first "
          f"answer of `/api/health` took {LAT['startup_s']:.1f} s. The machine is {F.HARDWARE}."),
        TAB("Response times on 127.0.0.1 (milliseconds)", ["Call", "Samples", "Median", "Mean", "95th percentile", "Maximum"],
            [["POST detect/upload (client round trip)", "100", f"{DC['median']:.0f}", f"{DC['mean']:.0f}", f"{DC['p95']:.0f}", f"{DC['max']:.0f}"],
             ["POST detect/upload (server-reported `processing_time_ms`)", "100", f"{DS['median']:.0f}", f"{DS['mean']:.0f}", f"{DS['p95']:.0f}", f"{DS['max']:.0f}"]]
            + [[nm, "40", f"{LAT[k]['median']:.0f}", f"{LAT[k]['mean']:.0f}", f"{LAT[k]['p95']:.0f}", f"{LAT[k]['max']:.0f}"]
               for nm, k in (("GET health", "get_health_ms"), ("GET diseases (38 cards)", "get_diseases_ms"), ("GET dashboard", "get_dashboard_ms"), ("GET history (20 rows)", "get_history_ms"),
                             ("GET analytics", "get_analytics_ms"))],
            widths=[2.9, 0.7, 0.7, 0.6, 1.1, 0.8], align=["l", "c", "c", "c", "c", "c"], size=9),
        P(f"A diagnosis takes a median of {DC['median']:.0f} ms from the client's point of view. The server-reported time is larger ({DS['median']:.0f} ms median) than the full round trip, which is only possible because `predict()` "
          "adds a constant 40 ms to the measured heuristic time (**D7**); the real engine time is therefore about 7 ms. The application feels instant on one machine. This says nothing about the cost of a trained network: "
          f"the compact CNN needs a median of {F.C['latency_ms_median']['mean']:.0f} ms per photograph on this CPU and MobileNetV2 {F.MB['latency_ms_median']['mean']:.0f} ms (Chapter 8), which would still be acceptable."),
        FIG(F.fig("f08_api_latency.png"), "Median and 95th-percentile response time of the API on 127.0.0.1.", 5.0),
        P("No load test was run: concurrent users, large histories (the history route reads all rows of a user and filters them in Python), memory growth and behaviour under a slow network were not measured."),

        H2("7.8 Defects found"),
        P("The tests and the model experiments together found seven defects in the product as delivered. They are reported here with the identifiers used in the rest of the report; none was fixed during the documentation work, "
          "so that the documents describe the code that was measured."),
        TAB("Defect register", ["ID", "Defect", "How it was found", "Effect"],
            [["D1", "Ten of the engine's 19 crop keys (nine of the 18 offered in the web form) leave fewer than three candidate classes and make the heuristic raise IndexError", "edge_tests (unit and API), run_experiments", f"HTTP 400 'unreadable image' for valid photos; {F.pct(F.HC['failed_share']['mean'])} of test photos unanswered"],
             ["D2", "The three displayed scores are not probabilities: they add up to more than 100 % (maximum 112 %) and the top score sits near 97 % for most photos", "edge_tests, Chapter 8 confidence analysis", "The shown confidence misleads the farmer"],
             ["D3", "Default token-signing secret is a public string", "edge_tests (API)", "A forged token is accepted unless AGRIVISION_SECRET is set"],
             ["D4", "No rate limiting on login", "edge_tests (API)", "Unlimited password guessing"],
             ["D5", "`train.py` uses the test folder as validation data and evaluates it with 27 class names against a 28-class model, so the two grape labels are shifted by one", "Reading the script and listing the folders", "Reported test accuracy of that script is not trustworthy; checkpoints are selected on the test data"],
             ["D6", f"`train.py` docstring says about 1.1M parameters; the model has {F.C['params']['mean']:,.0f}", "run_experiments (count_params)", "Misleading documentation"],
             ["D7", "`predict()` adds a constant 40 ms to the reported latency of the heuristic", "Server-reported time larger than the client round trip", "Latency shown to the user is inflated"]],
            widths=[0.4, 2.9, 1.7, 1.8], align=["c", "l", "l", "l"], size=9),

        H2("7.9 User acceptance"),
        P("No user study was carried out. No farmer, agricultural officer or student outside the project team used the application, so there is no measured evidence of acceptance, usability or trust. "
          "What exists is a walkthrough of the demonstration account by the project team: sign in, choose a crop, upload a photograph, read the result, filter the history, export a PDF, change the language and the theme. "
          "The walkthrough is the basis of the captured screens in Chapter 8. Judged by this walkthrough alone, the interface works as designed on a laptop and on a phone-width screen; judged by the accuracy figures of "
          "Chapter 8, the diagnosis would not be acceptable to a farmer, and the interface would mislead by showing a 97 % score on most photographs. A real acceptance test needs photographs taken by farmers, an agronomist's "
          "reading of the advice and a trained model; none of these exists yet."),

        H2("7.10 Limits of the testing done"),
        B(f"The browser checks ({F.N_UI}) were not repeated for this report; they describe the interface as it was at the end of the interface build.",
          "No accessibility audit was done beyond the checks listed in Section 7.4 (skip link, reachable drawer, Escape handling); there was no screen-reader test and no colour-contrast measurement.",
          "No load, stress or endurance test was run, and only one machine was used.",
          "No field trial: all photographs are PlantDoc web images, not photographs taken with a phone in a field, and no photograph of the project team was used.",
          "The security tests are a short list of hand-written probes; there was no external penetration test, dependency audit or review of the Flask pages.",
          f"The edge tests that depend on random images used a small sample (the confidence-sum check used 59 photographs). The model results use five hash seeds for the heuristic and three training seeds for each network, with no significance test.",
          "The Flask pages on port 5000, the PDF layout and the printed result page were not tested beyond the single-record PDF check that looks for the PDF header.",
          "The advice itself (doses, products, prices) was not checked by an agronomist, so the correctness of the recommendations is untested."),
    ]
    return out
