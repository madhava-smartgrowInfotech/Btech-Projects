"""Chapter 7: System testing."""

from . import facts as F
from .blocks import B, CODE, H1, H2, P, TAB


def blocks():
    return [
        H1("CHAPTER 7: SYSTEM TESTING"),
        H2("7.1 Test Strategy"),
        P("Testing has four layers, from the smallest unit to the user-visible behaviour. Each layer was run on the final code and its output is kept in `experiments/churn_synthetic/` so that the figures below can be re-checked."),
        TAB("Test layers", ["Layer", "What it covers", "Tool", "Result"],
            [["Unit tests", "The pure-Python core in src/ and the token functions", "pytest 9.1.1, `tests/test_core.py`", f"{F.TESTS['pytest']} passed on pandas 3.0.6 / scikit-learn 1.9.1 and {F.TESTS['pytest']} passed on pandas 2.2.1 / scikit-learn 1.5.0"],
             ["API end-to-end", "Every route group, including error paths, against the running service", "`scripts/smoke_test.py` (standard library only)", f"{F.TESTS['smoke']} checks passed, 0 failed"],
             ["Build", "The React interface compiles", "`npm run build` (Vite 8)", "Passes"],
             ["Interface walk", "All sixteen screens render with real data; no console errors or failed requests", "Playwright with Chrome, `scripts/capture_screens.py`", "16 screens captured; console clean"],
             ["Responsive and theme", "Layout at 360, 768 and 1440 px in light and dark themes; reduced motion; keyboard use", "Playwright, checked manually during the build", "No horizontal overflow found; no automated accessibility audit was run"]],
            widths=[1.0, 2.0, 1.6, 1.4], size=9),
        H2("7.2 Unit Tests"),
        P(f"The {F.TESTS['pytest']} unit tests were written for this report. They run in about 15 seconds, use the synthetic sample and a throw-away models folder, and do not touch the real saved model. They are grouped by the part of the pipeline they protect."),
        TAB("Unit tests by topic", ["Topic", "Tests", "Examples of what is asserted"],
            [["Sample data and loading", "10", "21 columns, 1,000 rows, reproducible for a seed, churn rate in a sane range; target and ID detected; Yes/No, 1/0, True/False and Churned/Retained labels normalised; blank TotalCharges converted; validation messages"],
             ["Preprocessing", "6", "Duplicates removed; encoded width is 45; split is stratified 80/20; unseen category is ignored, not fatal; SMOTE balances the training split; class distribution"],
             ["Training and metrics", "6", "Registry holds the required models; three models give valid metrics; confusion matrix sums to the test size; best model follows the requested metric; class weights raise recall over no handling; scores are percentages"],
             ["Risk segmentation", "11", "Band boundaries at 0, 29.99, 30, 59.9, 60, 79.9, 80 and 100; custom thresholds move the bands; tenure groups; risk table sorted and summary adds up"],
             ["Batch prediction", "2", "Output columns and the 50% churn cut-off; missing columns are named"],
             ["Retention rules", "4", "Month-to-month high-risk customer gets a contract offer; new-customer and Critical rules fire; low-risk gets no urgent action and the list is never empty; no rule fires below 60%"],
             ["Explainability", "2", "Local explanation falls back without SHAP; feature labels are cleaned"],
             ["Persistence", "1", "Save and load round-trip returns an identical model"],
             ["Authentication", "2", "Token round-trip, tampering and expiry are detected; wrong credentials rejected"]],
            widths=[1.4, 0.5, 4.1], align=["l", "c", "l"], size=9),
        CODE("""def test_default_risk_band_boundaries(p, band):
    assert assign_risk_category(p) == band      # 0, 29.99, 30, 59.9, 60, 79.9, 80, 100

def test_class_weights_raise_recall_over_no_handling(fitted):
    ...                                          # recall(class_weight) > recall(none)

def test_token_roundtrip_tamper_and_expiry(monkeypatch):
    ...                                          # a modified signature or an old exp is rejected""", 8.5),
        H2("7.3 API End-to-End Test"),
        P(f"`scripts/smoke_test.py` drives a running service through the whole workflow with the standard library only. It logs in, loads the sample, prepares it, explores, trains, saves, scores, explains, runs a what-if, generates retention actions, "
          f"scores a batch and checks drift, and it deliberately sends bad requests. All {F.TESTS['smoke']} checks pass. The table lists the error-path cases, which are as important as the successful ones."),
        TAB("Error and gating cases checked by the end-to-end test", ["Case", "Expected", "Result"],
            [["Protected route without a token", "401", "Pass"],
             ["Wrong password", "401", "Pass"],
             ["Exploration before any data is loaded", "409 (not ready)", "Pass"],
             ["Training with no model selected", "422", "Pass"],
             ["Risk thresholds out of order", "422", "Pass"],
             ["Unknown customer ID", "404", "Pass"],
             ["Batch file with missing columns", "422, columns named", "Pass"],
             ["Uploading a file that is not CSV", "422", "Pass"]],
            widths=[3.0, 1.8, 1.2], align=["l", "c", "c"], size=10),
        P("The successful path is covered by the other checks: every route returns 200 with the expected content (for example the training response contains three models, the evaluation response contains curves and a confusion matrix, the customer profile is complete, the what-if response contains a score change, and the batch response scores the 25 template rows)."),
        H2("7.4 Interface Testing"),
        P("The Playwright walk signs in with the demo account, loads the sample, trains three models, saves the Logistic Regression model and visits every page, capturing a 1440 x 900 screenshot of each. The run produced sixteen screenshots with real data and no console errors or failed network requests. "
          "Layouts were also checked at 360 px (phone), 768 px (tablet) and 1440 px (desktop) in both themes, and the keyboard path (skip link, visible focus, Escape closes overlays) and the reduced-motion setting were exercised. "
          "These checks were done by script and by inspection; no automated accessibility tool was run, and only Chrome was used."),
        H2("7.5 Performance Tests"),
        P("Response times were measured against the running API over `127.0.0.1` with `scripts/measure_api_latency.py` (10 repetitions per endpoint, 5 for batch). Section 8.11 gives the figures. No load or concurrency test was run: the service is single-user by design."),
        H2("7.6 Defects Found and Fixed"),
        P("Writing the tests exposed a real defect, and measuring the API exposed a platform quirk."),
        TAB("Defects and findings", ["Finding", "Cause", "Action"],
            [["Blank `TotalCharges` strings were not converted to numbers, and labels such as Churned / Retained were mishandled, under pandas 3", "`src/data_loader.py` tested `dtype == object` in three places; pandas 3 gives text columns a `str` dtype, so the test is false", "Added `_is_text()` that accepts object and string dtypes; two regression tests now pass on pandas 2 and 3. The sample data and Yes/No labels were never affected"],
             ["Every request through `http://localhost:8314` took about 2.04 s more than through `127.0.0.1`", "On this Windows machine `localhost` is tried over IPv6 first and the server listens on IPv4 only", "Not a product defect: the web interface uses the Vite proxy to 127.0.0.1. The smoke test's default base URL is `localhost`, so it takes about 95 s there; this is documented and was not changed"],
             ["Tree-ensemble scores on the 200-row split differ between scikit-learn versions", "Random Forest on 800 training rows is version-sensitive; Logistic Regression is identical", "The environment of record is stated; the other environment's metrics are archived and reported (Section 8.3)"]],
            widths=[2.2, 2.0, 1.8], size=8.5),
        H2("7.7 What Was Not Tested"),
        B("No load, stress or concurrency test: the in-memory single-user design does not support it.",
          "No penetration test and no review of the demo login beyond the unit tests of the token.",
          "No user-acceptance study with real analysts.",
          "No browser other than Chrome.",
          "No test of the SHAP code path, because SHAP is not installed.",
          "No test on real operator data or on a file with a different schema."),
        H2("7.8 Conclusion on Testing"),
        P("The tests show that the pipeline does what it is specified to do on the data it was built for, that invalid input is refused with clear messages, and that the interface renders every page with real data. "
          "They do not show that the models would perform the same way on real data, which is a matter of evidence (Chapter 8) and not of correctness."),
    ]
