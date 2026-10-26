"""Chapters 9 and 10, implementation decisions, references and appendices for CropSight."""
from __future__ import annotations

from docx.shared import Inches

from doc_common import REFERENCES, ROOT, metrics
from rc_results import AP, DL, G, IO, P, Q, R, RF, RP, extra_block, pc

APP = ROOT / "backend" / "app"


def _grab(rel: str, marker: str, n: int) -> str:
    """n lines of a real source file, starting at the first line that contains `marker`."""
    lines = (APP / rel).read_text(encoding="utf-8").splitlines()
    i = next(k for k, ln in enumerate(lines) if marker in ln)
    return "\n".join(lines[i:i + n])


def sec_decisions(d):
    d.h2("Implementation Decisions and Reasoning")
    d.p("The table lists the main implementation decisions and the reason for each. Several of them are consequences of two constraints: the project had no real "
        "labelled data, and it had to run on one ordinary computer without a graphics card.")
    d.table([["Decision", "Why"],
             ["Classical machine learning (Random Forest [10], Gradient Boosting [11]) instead of a deep network", "No labelled image set existed, the machine has no GPU, and the 11 features are computed from real pixels, so the model stays small, trains in seconds and can be explained with SHAP. The batch abstract speaks of deep learning; the shipped grader is not one"],
             ["Hand-crafted computer-vision features (HSV colour with an Otsu threshold [17], GLCM texture [15], Canny edges [16], blemish and size)", "Each feature has a meaning the farmer can read in the radar and SHAP charts; extraction is deterministic and needs no training data"],
             ["Train on generated feature vectors with 6% label noise", "A real labelled set was not available; the noise stops the forest from memorising separable clusters. The cost, shown in Chapter 8, is that real photographs fall outside the profiles"],
             ["SHAP TreeExplainer for both models", "Exact, fast attributions for tree ensembles [13], [14]; the top six contributions are returned with every grade and price"],
             ["Quantile Gradient Boosting for the price band", "Two extra models (alpha 0.15 and 0.85) give a 70% band without distributional assumptions [11], [12]; the displayed band is clamped to contain the point estimate"],
             ["Forecast by walking a market context forward 30 days", "A feed of weather, demand and supply did not exist, so the context is generated deterministically from crop, region and date; the same inputs give the same forecast on a day"],
             ["Transparent weighted score for delivery, not a trained model", "No delivery history exists; weights 0.38 / 0.22 / 0.18 / 0.14 / 0.08 can be read and defended, and the ranking was shown to be stable"],
             ["Simulated sensor stream over a WebSocket", "No hardware; a seeded random walk with injected events exercises the real path (WebSocket, history table, alert banner)"],
             ["FastAPI and SQLAlchemy with SQLite; scikit-learn [18], scikit-image [19] and OpenCV [20] for the models and features", "Typed request and response models, automatic documentation, no database server to install; sufficient for a single-machine demonstration"],
             ["JWT bearer tokens and a role dependency on every route", "Stateless authentication [23]; bcrypt password hashes; each role can reach only its own routes, and admins cannot be created by sign-up"],
             ["Order state machine in one dictionary", "placed to confirmed to in-transit to delivered is checked in one place, and each transition is bound to the role that may perform it"],
             ["Vite proxy for /api, /uploads and /ws", "The browser talks to one origin, so no cross-origin configuration is needed during development; ports 8000 and 5190 are fixed"],
             ["Run the API without the auto-reload option", "Observed in this setup: reload left orphaned worker processes holding the port with stale code; restart manually after backend edits"],
             ["Models retrained at start-up if the artefact is missing", "A fresh checkout works after the seed script; artefacts, datasets, the database and uploads are not committed"],
             ["Admin page that states the training data", "The synthetic origin of both models is shown in the application itself, not hidden"]],
            "Implementation decisions", widths=[0.4, 0.6], font=9)


def sec_conclusion_summary(d):
    d.h2("Summary of the Work")
    d.paras(
        "This project built CropSight, a full-stack platform for the stage after harvest. A farmer uploads a photograph of a crop; computer-vision features are extracted from its pixels "
        "(colour, texture, edges, blemishes, relative size) and a Random Forest assigns the grade A, B, C or Reject, explained with SHAP. A Gradient Boosting model with quantile bands "
        "gives the current price, a 30-day forecast and a best day to sell, again explained with SHAP. A transparent weighted score ranks buyers, a route and the spoilage risk. Farmers, "
        "buyers, distributors and an admin work through a marketplace with a checked order lifecycle, and a distributor can follow a shipment's temperature, humidity and shock on a live "
        "stream with alerts. The system has 21 interfaces (20 REST and one WebSocket), nine database tables, a React web application with four role dashboards and a pytest suite.",
        f"Because no real labelled crop images or market prices were available, both models were trained on synthetic data generated by the project's code, and the sensor stream and "
        f"buyer offers are simulated. On its own synthetic test set the grader reaches {pc(RF['test_accuracy'])} accuracy and the price model R2 {G['r2']:.3f} with MAPE {pc(G['mape'])}. A check on "
        f"3,200 real fruit photographs showed that the grader does not transfer (fresh versus rotten accuracy {pc(RP['mapped_binary_accuracy'])}), while the same features retrained on real labels reach "
        f"{pc(R['features_trained_on_real_labels']['five_fold_cv_accuracy_mean'])}. Thirty-six automated tests pass, three more document known gaps, and a photograph is graded in about 0.17 s.")


def sec_conclusion_objectives(d):
    d.h2("Objectives Achieved")
    d.p("Of the six objectives, three are achieved as stated and three only in part. Explaining grading and pricing with explainable AI (objective 4), connecting farmers, distributors and buyers "
        "through a marketplace (objective 6) and recommending buyers, routes and the best time to sell (objective 5, as a transparent heuristic with simulated offers) are in place and tested. "
        "Grading quality from images (objective 1) is implemented with classical machine learning rather than deep learning and works only on synthetic data; forecasting prices (objective 2) "
        "is implemented but trained and evaluated on synthetic data; and monitoring storage and transport (objective 3) is demonstrated with a simulated sensor stream. Chapter 8 gives the "
        "evidence for each.")


def sec_conclusion_findings(d):
    d.h2("Key Findings")
    d.numbered([
        f"**A high score on synthetic data is not evidence of quality.** The grader scores {pc(RF['test_accuracy'])} on its own generator and {pc(RP['mapped_binary_accuracy'])} (chance) on 3,200 real photographs; it grades "
        f"{pc(RP['predicted_grade_share_by_label']['rotten']['B'])} of rotten fruit as grade B.",
        f"**The features are sound; the training data are not.** The same 11 features retrained on real fresh and rotten labels give {pc(R['features_trained_on_real_labels']['five_fold_cv_accuracy_mean'])} (AUC "
        f"{R['features_trained_on_real_labels']['five_fold_cv_auc_mean']:.2f}), but only {pc(R['features_trained_on_real_labels']['leave_fruits_out_accuracy_mean'])} for unseen fruits, so grading must be trained per crop on real labels.",
        f"**The price model recovers its generator almost exactly.** MAPE {pc(G['mape'])} against a data noise floor of {pc(P['noise_floor']['generating_function_vs_observed']['mape'])}, and R2 {P['time_holdout']['r2']:.3f} on a 2024 hold-out; "
        "crop type explains 72% of its importance and weather essentially none.",
        f"**The \"best day to sell\" is an artefact.** Waiting is recommended in {pc(1 - P['served_forecast']['best_sell_day_zero_share'], 0)} of cases with a mean gain of {P['served_forecast']['mean_gain_pct_if_waiting_to_best_day']:.1f}%, produced by hash-generated daily noise; a real forecast needs real price series, for which time-series foundation models [6] are a promising baseline.",
        f"**The delivery ranking is robust but its inputs are simulated.** The top buyer survives {pc(DL['weight_perturbation']['top1_unchanged_mean'])} of random weight changes; offers are a hash of the buyer and crop.",
        f"**The sensor simulator needs a return to normal.** {pc(IO['share_of_flags_that_are_persistent_drift'])} of its alarm steps are persistent drift, so by step 400 every one of the 50 simulated shipments was in alarm.",
        "**Software defects were found by testing:** a 100-fold overstatement of the admin transaction volume (unit mix of quintal and kilogram), a server error and orphan record on a corrupt image, and unvalidated crop, region and order values.",
        "**Disclosure works.** Because the admin page and this report state the synthetic origin of the models, the limits above are visible rather than hidden.",
    ])


def sec_conclusion_applications(d):
    d.h2("Practical Applications")
    d.p("In its present form CropSight is a working prototype and a teaching and demonstration platform for a post-harvest marketplace; it should not be used to set real prices or grades. With real "
        "labelled images of the crops it targets, a real price series from mandi or exchange feeds, real cold-chain sensors and the security fixes listed in Chapter 10, the same structure could support "
        "four uses: a photograph-based first grade that a buyer can inspect and challenge; price and timing guidance for smallholders with an honest uncertainty band; matching of lots to nearby "
        "buyers; and cold-chain alerts during transport.")


def sec_conclusion_limits(d):
    d.h2("Known Limitations")
    d.bullets([
        "Both models are trained on synthetic data; the grader fails on real photographs and the price forecast uses generated market context.",
        "The grader is classical machine learning on 11 hand-crafted features, not a deep network, and was never evaluated on A, B, C and Reject labels given by real graders.",
        "The sensor stream, the buyer offers and the buyer reliability scores are simulated or seeded; the alarm rarely returns to normal once the readings have drifted.",
        "Input validation, authorisation and the WebSocket are not hardened; the default signing key is in the source; the admin volume figure is wrong by a factor of 100.",
        "Single-process SQLite on one machine, no load test, no payment, no user study.",
        "The landing page shows fixed marketing counters that are not measurements.",
    ])


def sec_future_improvements(d):
    d.h2("Improvements")
    d.bullets([
        "**Retrain the grader on real labelled images** of each crop, starting with the Fresh and Rotten Fruits set [8] and the bruised-vegetable set of the same collection, with grades assigned by trained graders; report per-grade accuracy on held-out farms.",
        "**Replace the synthetic price series** with real mandi or exchange prices and compare the boosted model with a seasonal baseline and a time-series foundation model, as in [6], using a rolling-origin evaluation.",
        "**Calibrate the price band** so that it is not clamped to the point estimate, and report its coverage on real data.",
        "**Fix the known defects:** the admin volume units, a transactional upload that does not leave an orphan listing, and a return-to-normal rule with hysteresis for the sensor alarm.",
        "**Validate inputs and authorisation:** catalogue checks for crop and region, positive quantities limited to the lot, ownership checks on listing and order detail, and an authenticated WebSocket.",
    ])


def sec_future_features(d):
    d.h2("Additional Features")
    d.bullets([
        "Regional-language interface and voice input for farmers; photographs taken in the app with a guide for background and light.",
        "Multiple photographs per lot and a size reference object, so that size and surface are measured rather than inferred from the mask.",
        "Buyer bids and counter-offers instead of a single agreed price, delivery-partner assignment and proof of delivery.",
        "Disease and pest recognition for leaves, in the direction of [2], and storage-life estimates from the sensor history.",
        "Notifications by SMS or messaging application for orders and cold-chain alerts.",
    ])


def sec_future_deploy(d):
    d.h2("Scalability and Deployment")
    d.p("The next step is a hosted deployment: a managed database in place of SQLite, object storage for photographs, HTTPS, a strong secret key from the environment, rate limiting, a background "
        "worker for grading, and a process manager. The model artefacts should be versioned and monitored (grade distribution, confidence, drift of the feature means against training). A load test "
        "with concurrent users, a measured memory profile and a continuous-integration run of the 39 tests would turn the single-machine timings of this report into capacity figures.")


def sec_future_research(d):
    d.h2("Further Research")
    d.bullets([
        "How far hand-crafted features go against a small convolutional network or a vision transformer fine-tuned on a few thousand real photographs per crop, and how much SHAP-style explanations lose or gain.",
        "Domain shift in produce photography: backgrounds, lighting and cameras, and how much augmentation or colour calibration closes the gap seen in Chapter 8.",
        "Uncertainty for farmers: conformal intervals for price and a calibrated confidence for grades, so that low-confidence grades are sent for human inspection.",
        "Joint optimisation of timing, buyer and route under spoilage, with the price forecast and the cold-chain state as inputs rather than a fixed weighted score.",
        "A user study with smallholders and buyers to learn whether explanations change trust and decisions.",
    ])


def sec_references(d, heading=True):
    if heading:
        d.h2("References")
    for i, ref in enumerate(REFERENCES, 1):
        p = d.p(f"[{i}]\t{ref}", align="left", size=11, line=1.2, space_after=4)
        p.paragraph_format.left_indent = Inches(0.45)
        p.paragraph_format.first_line_indent = Inches(-0.45)


def appendix_a(d):
    d.p("The listings below are extracted from the source files when this report is built, so they match the code that produced the results.")
    d.h2("Foreground Mask and Blemish Features")
    d.code(_grab("ml/quality/feature_extraction.py", "def _foreground_mask", 15) + "\n    ...\n" + _grab("ml/quality/feature_extraction.py", "edges = cv2.Canny", 11),
           "_foreground_mask() and the edge and blemish features in ml/quality/feature_extraction.py")
    d.h2("Random Forest Training")
    d.code(_grab("ml/quality/train_model.py", "X = df[FEATURE_NAMES]", 22), "Training of the quality grader in ml/quality/train_model.py")
    if getattr(d, "report", False):
        d.p("The listings of the price forecast walk, the delivery score, the order state machine, the role guard and the sensor simulator step are given in section 6.8 and are not repeated here.")
        return
    d.h2("Price Forecast Walk")
    d.code(_grab("ml/price/infer.py", "forecast: dict[int, float]", 16), "Forecast loop and best sell day in ml/price/infer.py")
    d.h2("Delivery Score")
    d.code(_grab("ml/delivery/recommend.py", "price_norm =", 18), "Weighted score of one buyer in ml/delivery/recommend.py")
    d.h2("Order State Machine and Role Guard")
    d.code(_grab("api/marketplace.py", "VALID_TRANSITIONS = {", 5) + "\n    ...\n" + _grab("core/security.py", "def require_roles", 6), "VALID_TRANSITIONS in api/marketplace.py and require_roles() in core/security.py")
    d.h2("Sensor Simulator Step")
    d.code(_grab("ml/iot/simulate.py", "def step(self)", 24), "ShipmentSensorState.step() in ml/iot/simulate.py")


def appendix_b(d):
    d.h2("Installation Guide")
    d.p("CropSight runs on Windows, macOS or Linux with Python 3.11 and Node.js. The commands below are those of the project README; the port numbers are fixed in the code.")
    d.numbered([
        "Backend: `cd backend`, `python -m venv venv`, activate it (`venv\\Scripts\\activate` on Windows) and run `pip install -r requirements.txt`.",
        "Train both models (about 20 s on the machine of this report): `python -m app.ml.quality.train_model` and `python -m app.ml.price.train_model`. They write `.joblib` artefacts and CSV datasets to `backend/app/data/`.",
        "Seed the demo accounts, eight towns and one sample listing: `python scripts/seed_db.py`.",
        "Start the API on port 8000: `python -m uvicorn app.main:app --port 8000` (do not use `--reload` on Windows in this setup). Interactive documentation is at `/docs`.",
        "Frontend: `cd frontend`, `npm install`, `npm run dev`. The web app is served at http://127.0.0.1:5190 and proxies `/api`, `/uploads` and `/ws` to port 8000.",
        "Tests (optional): `pip install pytest httpx`, then `cd backend` and `python -m pytest tests -q`; the suite uses its own temporary database.",
    ])
    d.table([["Role", "E-mail", "Password"],
             ["Farmer", "farmer@cropsight.dev", "cropsight123"],
             ["Buyer", "buyer1@cropsight.dev (also buyer2, buyer3, buyer4)", "cropsight123"],
             ["Distributor", "distributor@cropsight.dev", "cropsight123"],
             ["Admin", "admin@cropsight.dev", "cropsight123"]],
            "Demo accounts created by the seed script", widths=[0.2, 0.55, 0.25], font=10)
    d.h2("User Guide")
    d.table([["Task", "How"],
             ["Grade a crop (farmer)", "Dashboard, choose the crop and quantity, drop or select a JPEG, PNG or WEBP photograph of at most 8 MB, press Grade this crop; the workspace opens with grade, confidence and the explanation"],
             ["Forecast the price (farmer)", "In the workspace press Forecast price: current price, 30-day curve with band, best day to sell and the drivers"],
             ["Plan delivery (farmer)", "Press Plan delivery: the top buyers with offer, distance, transit time and match score, and the suggested route"],
             ["Publish a listing (farmer)", "Enter the asking price per quintal and press Publish listing; the lot appears in the marketplace"],
             ["Confirm an order (farmer)", "Orders, press Confirm on a placed order"],
             ["Buy (buyer)", "Marketplace, filter by crop, region and grade, open a listing, Place order, enter quantity and agreed price; My orders shows the progress"],
             ["Ship (distributor)", "Active deliveries, Start transit on a confirmed order, Live monitor for the sensor stream, Mark delivered at the end"],
             ["Review the platform (admin)", "Overview for users, listings, orders and volume; Model insights for the algorithms, accuracy and training-data notes"]],
            "User guide", widths=[0.26, 0.74], font=10)
    d.p("CropSight is a prototype: grades, prices and alerts shown by the application are produced by models trained on synthetic data and by simulators, and must not be used for real transactions.")


def appendix_c(d):
    d.p("Additional captures of the running application (26 October 2026, 1440 by 900 pixels).")
    extra_block(d)
