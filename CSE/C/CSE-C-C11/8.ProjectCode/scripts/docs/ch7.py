"""Chapter 7: System Testing for FINJARVIS. Numbers come from facts.py (experiments/*.json) and docs/REPORT_FACTS.md sections 5-8."""
import os

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, P, TAB
from .refs import N as cite


def _lat_rows():
    rows = []
    for k, v in F.LAT.items():
        if isinstance(v, dict) and "median_ms" in v:
            rows.append([f"`{k}`" if k.startswith(("GET", "POST")) else k, str(v["n"]), f"{v['median_ms']:.1f}", f"{v['p95_ms']:.1f}", f"{v['max_ms']:.1f}"])
    return rows


def blocks():
    c, fc, hl, a, imp = F.CLS, F.FC, F.HL, F.AS, F.IMP
    bt = fc["demo_backtest"]
    b = [H1("CHAPTER 7: SYSTEM TESTING")]

    # ------------------------------------------------------------------ 7.1
    b += [H2("7.1 Testing strategy"),
          P("FINJARVIS was handed over as a working Streamlit application with a small pytest suite and no end-to-end test. The documentation run kept that suite, added a smoke script that walks the web API from sign-up to report download, "
            "and added measurement scripts that probe the three algorithms (Chapter 8). The strategy follows the structure of the code. The service layer and the ML modules are plain functions with checkable results, so they are unit-tested against a temporary SQLite file that every test receives through an automatic fixture; "
            f"the {F.N_ROUTES} FastAPI routes are tested end to end by a script that starts the real server on a spare port against a throw-away database; and the quality of the models is measured offline on data written for the purpose instead of being asserted."),
          TAB("Test levels, tools and results.",
              ["Level", "Tool and scope", "Count", "Result"],
              [["Unit", "pytest in `tests/`: password hashing and authentication, transactions and user isolation, budgets and alerts, the health score, the categoriser and the forecast", f"{F.PYTEST_TOTAL} tests", f"{F.PYTEST_PASSED} passed, 0 failed, 11.5 s"],
               ["Functional / integration", "`scripts/smoke_test.py`: starts the backend, then exercises auth, transactions, import, budgets, goals, investments, analytics, assistant, reports and profile through HTTP", f"{F.SMOKE_TOTAL} checks", f"{F.SMOKE_PASSED} of {F.SMOKE_TOTAL} passed"],
               ["Model evaluation", "`scripts/run_experiments.py` on the probe set, the demo account, 2,000-user simulations, 5,000 random profiles and 26 assistant questions", "6 studies", "Results in Chapter 8 (not pass or fail tests)"],
               ["Performance", "`scripts/measure_api.py`: latency of 19 request types on 127.0.0.1", "30 or 10 repetitions each", "Table in Section 7.7"],
               ["Screens", "Playwright walk of the React console on the demo account (`scripts/capture_screens.py`)", "19 screenshots", "Captured and inspected by eye; not an automated UI test"]],
              widths=[1.1, 3.1, 0.9, 1.4], align=["l", "l", "c", "l"], size=9),
          P("Unit tests use tiny, hand-checkable inputs (a four-month series rising by 100 per month, a user with a 20 % savings rate) so that a failure points at one rule; "
            "the smoke script uses a brand-new user with exact amounts (a 450 expense that becomes 500, a transport budget of 200 overspent by 220). "
            "Neither level uses the demo account's totals as expected values, because those depend on today's date.")]

    # ------------------------------------------------------------------ 7.2
    b += [H2("7.2 Unit testing"),
          P(f"The pytest suite has {F.PYTEST_TOTAL} tests in five files. The fixture in `tests/conftest.py` creates a fresh SQLite file for every test function, rebinds the application's engine and session factory to it, and deletes it afterwards (after disposing the engine, which Windows requires). "
            "No test touches the real `finjarvis.db`."),
          TAB("Unit tests by file.",
              ["File", "Tests", "What is checked"],
              [["`test_auth.py`", "9", "A bcrypt hash differs from the password and verifies only the right one; sign-up succeeds; a weak password, mismatched passwords and a duplicate e-mail are refused; login works with a username and with an e-mail; a wrong password and an unknown user are refused"],
               ["`test_transactions.py`", "8", "Add creates a row; a negative amount and an invalid type raise `ValueError`; update; delete and delete of a missing id returns false; **user isolation** (one user's rows are invisible to another); filter by category and type"],
               ["`test_budget.py`", "6", "Set and read status; a non-positive amount is rejected; setting again updates the same budget; delete; an overrun raises an alert notification; no alert under the threshold"],
               ["`test_financial_health.py`", "6", "Savings-rate and expense-ratio bounds; a healthy profile scores well and a struggling one poorly; the score stays within 0-100; the result carries an explanation and the weakest area"],
               ["`test_ml.py`", "9", "'Swiggy order' is Food, 'Uber ride' Transport, 'Netflix subscription' Entertainment; an empty description gives 'Other'; nonsense text returns a string without crashing; the forecast refuses fewer than three months; works with four; never returns a negative value on a falling series; the category forecast declines on an empty frame"],
               ["**Total**", f"**{F.PYTEST_TOTAL}**", f"**{F.PYTEST_PASSED} passed**; 16 warnings, all the scikit-learn pickle-version notice"]],
              widths=[1.5, 0.6, 4.3], align=["l", "c", "l"], size=9),
          P("Three of these tests are weaker than they look. The categoriser tests use phrases that are in the seed list, so they confirm that the model reproduces its training data, not that it generalises. "
            "The nonsense-text test asserts only that a non-empty string comes back (Chapter 8 shows it is 'Transport'). "
            "And no unit test checks the exact value of the health score or the forecast, only their bounds; the experiment scripts cover the numbers.")]

    # ------------------------------------------------------------------ 7.3
    b += [H2("7.3 Integration and functional testing"),
          P(f"`scripts/smoke_test.py` copies nothing from the product's own database: it sets `FINJARVIS_DB` to a temporary file, starts uvicorn on a free port with the same `backend.main:app`, waits for `/api/health` and runs {F.SMOKE_TOTAL} checks with the `requests` library. "
            f"All {F.SMOKE_PASSED} passed. The checks are grouped below; the first column is the user-visible feature."),
          TAB("Smoke-test checks by feature.",
              ["Feature", "Checks", "Representative assertions"],
              [["Authentication", "5", "health endpoint; a protected route without a token answers 401; the demo account logs in; a wrong password is rejected; a weak password is rejected at sign-up (400)"],
               ["Demo data", "4", "the demo dashboard has current-month income; the health score is between 0 and 100; all chart datasets are returned; the public showcase works without login"],
               ["Sign-up and isolation", "3", "sign-up returns 201; a duplicate answers 409; a new user starts with no transactions"],
               ["Transactions", "10", "'Swiggy order' is auto-categorised as Food; income is accepted; amount 0 is rejected (400); search finds the expense; edit; another user's edit and delete answer 404; delete; a second delete answers 404"],
               ["Import", "4", "preview of three rows gives 2 valid and 1 warning; a blank category is filled (Transport); commit imports 2; a file with missing columns answers 400 with 'Missing required column(s)'"],
               ["Budgets and alerts", "5", "a budget saves (201); spending 220 against 200 shows 100 % or more; an alert notification appears; mark-all-read clears the unread count; delete"],
               ["Goals", "3", "17 % complete and a positive required monthly saving; a goal completes at its target; delete"],
               ["Investments", "3", "profit and loss of 200 (20 %); refresh with no symbol returns a failure message, not an error; delete"],
               ["Analytics and assistant", "5", "the demo user gets a forecast above zero; a one-month user is refused; a reversed date range answers 400; the assistant answers 'biggest spending category' with the disclaimer; insights are returned"],
               ["Reports", "3", "PDF starts with `%PDF`, Excel is a zip (`PK`), CSV starts with `id,date`"],
               ["Profile and security", "4", "profile update persists; a duplicate e-mail is refused; the demo-data loader inserts transactions; a token with a changed signature answers 401"]],
              widths=[1.4, 0.6, 4.4], align=["l", "c", "l"], size=9),
          P("The script has two known weaknesses: the check 'edit persisted' accepts either of two amounts because list order is not guaranteed, so it would also pass if the edit were lost; "
            "and it is a single linear walk, so one early failure can make later checks fail for the same reason.")]

    # ------------------------------------------------------------------ 7.4
    b += [H2("7.4 Security testing"),
          P("The security checks that were run are those in the unit and smoke tests above; no penetration test or automated scanner was used. What was verified, and how:"),
          TAB("Security checks that were run.",
              ["Check", "Result", "Where"],
              [["Password rules: 'abc' refused; mismatched passwords refused", "Passed (HTTP 400)", "`test_auth.py`, smoke"],
               ["Hash is not the plain password and verifies only the right one", "Passed", "`test_auth.py`"],
               ["Protected route without a token", "401", "smoke"],
               ["Token with a changed signature", "401", "smoke"],
               ["Another user edits or deletes a transaction", "404; the data is unchanged", "smoke, `test_transactions.py` isolation"],
               ["Duplicate e-mail on sign-up and on profile update", "409 on both", "smoke"],
               ["Wrong password versus unknown user", "Both refused; the code returns the same message for both (`Invalid username/email or password.`)", "`test_auth.py` (refusal), `auth/authentication.py` (message)"]],
              widths=[3.4, 1.8, 1.2], align=["l", "l", "l"], size=9),
          P("Several properties were **not tested** (Chapter 6 explains why each is a weakness): brute-force protection (the code has no rate limit or lockout), token expiry (the seven-day lifetime was not simulated), "
            "the default secret (`finjarvis-dev-secret` is used if `APP_SECRET_KEY` is unset, so anyone who knows it can forge a token), SQL-injection payloads (the ORM binds parameters; not probed), cross-site scripting (the token is in local storage), "
            "and the shared categoriser file. The product suits a demonstration on a trusted machine and is not hardened.")]

    # ------------------------------------------------------------------ 7.5
    b += [H2("7.5 Validation and edge cases"),
          P("The table lists the edge cases exercised by the tests, the smoke script and the experiment scripts; a defect or gap is marked as such."),
          TAB("Edge cases and observed behaviour.",
              ["Input or situation", "Observed behaviour", "Verdict"],
              [["Transaction with amount 0 or a negative amount", "HTTP 400 from the route; `ValueError` from the service", "Correct"],
               ["Empty description sent to the categoriser", "Returns 'Other' without calling the model", "Correct"],
               ["Description with no known word (`xyzabc123 qqq`)", f"Labelled **{c['unseen_text_prediction']['predicted']}** (the highest intercept), top probability {max(c['unseen_text_prediction']['probabilities'].values()):.3f}; no warning, no abstention", "Gap: silent wrong label"],
               ["Fewer than three months of history", "Forecast refuses: 'Need at least 3 months of transaction history for a reliable prediction (currently have n).'", "Correct; threshold is low for the method (Chapter 8)"],
               ["Falling expense series", "Prediction is clipped at 0, never negative", "Correct"],
               ["Reversed analytics date range", "HTTP 400, \"'From' must be on or before 'To'.\"", "Correct"],
               ["CSV without the required columns", "HTTP 400 with the names of the missing columns", "Correct"],
               [f"{imp['rows_in_file']:,}-row import with {imp['injected_bad_total']} injected bad rows (dates, amounts, blank descriptions)", f"{imp['rows_skipped']} skipped (exact), {imp['rows_imported']} imported, all {imp['blank_category_rows_auto_labelled']} blank categories labelled", "Correct"],
               ["Investment refresh with no symbol or no market data", "Returns a failure message and keeps the entered price", "Correct"],
               ["Budget re-crossing a threshold in a later month", "No new notification (de-duplicated by message text only)", "Gap"],
               ["Question outside the assistant's patterns", f"{a['answerable'] - a['answerable_handled_by_analytics']} of {a['answerable']} answerable questions fell to the fixed help text; {a['unanswerable_correctly_declined']} of {a['not_answerable']} off-topic questions were declined", "Partial (Chapter 8)"],
               ["'Am I overspending on shopping?'", "Answered with the Shopping total, not a budget comparison", "Gap"],
               ["Random financial profiles (5,000)", f"Score always between {hl['score_min']} and {hl['score_max']}; raising the savings rate by five points never lowered the score ({hl['monotonic_violations_when_savings_rate_plus5']} violations)", "Correct"]],
              widths=[2.4, 3.1, 1.0], align=["l", "l", "l"], size=8.5)]

    # ------------------------------------------------------------------ 7.6
    b += [H2("7.6 Model validation as testing"),
          P("The three algorithms are tested by measurement; the full results are in Chapter 8 and are summarised here."),
          B(f"**Categoriser.** Accuracy {c['tfidf_lr']['accuracy'] * 100:.1f} % on the probe set (macro-F1 {c['tfidf_lr']['macro_f1']:.3f}), but {c['tfidf_lr']['accuracy_by_tier']['A'] * 100:.0f} % and {c['tfidf_lr']['accuracy_by_tier']['B'] * 100:.0f} % on the seed-like and statement-style tiers and only {c['tfidf_lr']['accuracy_by_tier']['C'] * 100:.1f} % on unseen merchants; leave-one-out accuracy on the seed is {c['loo_cv_accuracy_on_seed'] * 100:.1f} %.",
            f"**Forecast.** On the demo account's three test points the line's MAPE was {bt['mape_pct']['linear_trend (app)']:.1f} % against {bt['mape_pct']['mean_of_all']:.1f} % for the mean of all history; in 2,000-user simulations a plain three-month mean was at least as good as the line in every setting.",
            f"**Health score.** Bounded, monotone in the savings rate on 5,000 random profiles, with a demo-account score of 90.4 (Excellent) whose weakest component is goal progress.",
            f"**Assistant.** {a['answerable_handled_by_analytics']} of {a['answerable']} answerable questions answered from the user's data; the two numeric answers checked (Food total INR {a['numeric_check_food_truth']:,.0f}; top category Rent) matched direct sums."),
          P("These are validation results on data written by the team, not field trials.")]

    # ------------------------------------------------------------------ 7.7
    m = "Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB RAM, no discrete GPU, Windows 11 Pro, Python 3.11.9"
    b += [H2("7.7 Performance testing"),
          P(f"`scripts/measure_api.py` starts the backend on a temporary database that holds the demo account, logs in once, and times each request type 30 times (10 times for the report downloads and the import preview) with `requests` against `127.0.0.1`. "
            f"The machine was {m}. Calls to `localhost` added about two seconds each here because of an IPv6 fallback, so every figure uses the numeric address. "
            "All figures are single-user, single-process and warm; no load or concurrency test was run."),
          TAB("API latency (milliseconds).", ["Request", "Runs", "Median", "p95", "Max"], _lat_rows(), widths=[3.4, 0.6, 0.8, 0.8, 0.8], align=["l", "c", "r", "r", "r"], size=9),
          P(f"Every data route answers in under 135 ms at the 95th percentile except four: login (median {F.lat('login'):.0f} ms, which is the cost of the bcrypt verification and is intentional), the PDF report (median {F.lat('GET /reports/pdf'):.0f} ms), the Excel report (median {F.lat('GET /reports/excel'):.0f} ms) and the import preview "
            f"(median {F.lat('POST /transactions/import/preview'):.0f} ms for 100 rows, about {F.lat('POST /transactions/import/preview') / 100:.1f} ms per row). The dashboard, which recomputes the metrics, budgets, health score and six chart datasets in one call, takes a median of {F.lat('GET /dashboard'):.0f} ms, "
            f"and a categorisation request takes {F.lat('POST /transactions/predict-category'):.1f} ms. For one user on a local machine every interactive route answers well inside a second."),
          P(f"The import commit is slower: a {imp['rows_in_file']:,}-row file took {imp['clean_and_categorise_s']:.1f} s to clean and label and {imp['commit_s']:.1f} s to insert ({imp['rows_per_second_commit']:.1f} rows per second), because `commit_import` opens one database session per row. "
            "A monthly statement of a few hundred rows takes seconds.")]

    # ------------------------------------------------------------------ 7.8
    b += [H2("7.8 User acceptance testing"),
          P("**No user acceptance test was carried out.** The product was used only by the project team. There was no questionnaire, no usability session, no task-completion timing and no comparison with another finance application, so no claim about ease of use, satisfaction or financial-behaviour change is made. "
            "The Mabu app study " + cite("to") + " shows what such a study looks like (interviews, survey, card sorting, think-aloud sessions and a usability questionnaire); it is listed as future work in Chapter 10."),
          P("The nearest substitute is the screen walk: all 13 pages were opened with the demo account at 1440 x 900 and checked by eye for layout, empty states and obvious errors (the screenshots in Chapter 8). "
            "That finds visible defects; it does not show that a person can complete a task.")]

    # ------------------------------------------------------------------ 7.9
    b += [H2("7.9 Limits of the testing done"),
          P("The testing supports the statement that the product's rules do what the code says and that its routes work together on one machine. It does not support stronger statements. The limits are:"),
          B("**Small, self-written data.** The categoriser was scored on 198 descriptions written by the team that wrote the 51-example seed; the forecast was backtested on six months of fictional data (three test points); the assistant on 26 questions. None is an independent benchmark.",
            "**No coverage measurement.** The share of lines executed by the tests was not measured; the route layer is reached only through the smoke script.",
            "**No browser-level tests.** The React console has no automated test; type checking (`tsc -b`) runs in the build.",
            "**No concurrency, soak or load test.** SQLite serialises writes and the shared model file is rewritten on a correction; neither was exercised with two simultaneous users.",
            "**No security assessment.** Section 7.4 lists what was and was not checked.",
            "**Unexercised integrations.** The optional language-model layer and the live price refresh need an API key and internet access and were not run; their failure paths (fall back to rules, return a message) are read from the code, not observed.",
            "**One machine, one run.** Accuracy figures are deterministic, but latency and import times shift by a few tens of percent between runs.",
            "**Experiments are not regression tests.** The measurement scripts write JSON; they do not fail when a number gets worse."),
          P("In summary, 38 unit tests and 49 end-to-end checks pass and the measurements show where the simple models are weak; the testing cannot show how the product behaves with real users, real statements or a hostile network.")]
    return b
