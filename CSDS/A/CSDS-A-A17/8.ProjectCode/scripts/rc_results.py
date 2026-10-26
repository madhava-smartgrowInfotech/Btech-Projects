"""Chapter 8 content: output screens, measured results, comparison with the base paper, failure analysis, objectives.

Every figure is read from experiments/*/metrics.json (through doc_common.metrics) or from docs/REPORT_FACTS.md.
"""
from __future__ import annotations

import json

from doc_common import CHARTS, SAMPLES, SHOTS, metrics

Q, P, R, DL, IO, AP = (metrics(n) for n in ("quality", "price", "real_images", "delivery", "iot", "api_latency"))
RF, RP = Q["shipped_rf"], R["shipped_model_on_real_photos"]
G, SF = P["shipped_gbr"], P["served_forecast"]


def pc(x, n=1):
    return f"{x * 100:.{n}f}%"


# (file, caption, what it shows)
MAIN_SCREENS = [
    ("01_landing.png", "Landing page", "The public home page: the headline \"Move every harvest with certainty, not guesswork\", the line that CropSight grades quality from a photo, forecasts the price and says who to sell to and when, and the buttons Get started and Log in. The four counters under the headline (38,400+ crops graded, +17% average price uplift, 92% grading accuracy, 2,400+ farmers onboarded) are fixed marketing text in the page source; they are not measurements of this project, and the only measured accuracy figures are those in this chapter."),
    ("03_login_error.png", "Failure case: wrong password", "The log-in page after the farmer's e-mail was entered with a wrong password. The API answered HTTP 401 and the page shows the red message \"Couldn't sign in - Invalid email or password\". The panel on the right also lists the four demo accounts."),
    ("06_upload_preview.png", "Farmer dashboard with a real photograph selected", "The farmer chose the crop Tomato, a quantity of 620 kg and the real photograph tomato_1.jpg (from the public vegetable dataset); the photograph appears in the preview panel on the right. The four earlier listings of the farmer (two potato lots, an onion lot and the seeded tomato lot) are listed below with their grade, status and asking price."),
    ("07_grading_result.png", "Grading result", "Right after the upload the app opened the listing workspace: Tomato, 620 kg, Sunridge Valley, **Grade B with 70.1% confidence**. The radar chart summarises colour, texture, size, surface, blemish (inverted) and vibrancy; the bar chart \"What drove this grade\" shows the six largest SHAP contributions (colour uniformity, blemish ratio, texture homogeneity, edge density, saturation spread, mean value). The toast says \"Crop graded - Grade B, 70% confidence\"."),
    ("08_price_forecast.png", "Price forecast", "After pressing Forecast price: the current price **INR 2,272 per quintal** with the range INR 2,068 to 2,272, the 30-day curve with its confidence band (peak near 9 November) and the SHAP bars \"What's driving this price\" - crop type is the largest (negative) contributor, quality grade and regional factor push up. The range ends exactly at the current price, because the displayed band is clamped to include the point estimate."),
    ("09_delivery_planner.png", "Delivery planner", "After Plan delivery: four buyers ranked by match score - Harvest & Co. (Millstone Basin, 773.6 km, 2.5 days, INR 2,533, **67.7%** match), Coastal Fresh Distributors (60.9%), GreenMart Wholesale (60.1%) and Riverstone Foods (56.5%) - and the suggested route Sunridge Valley Market to Millstone Basin Market. The best sell day for the listing is 9 November. The buyer offers are simulated from a hash of the buyer and crop."),
    ("12_farmer_listings.png", "Listings after publishing", "The farmer's dashboard after the tomato lot was published at INR 2,250: Tomato 620 kg (Grade B, listed), Potato 640 kg (Grade B, listed), Potato 1,200 kg (Grade A, sold), Onion 900 kg (Grade B, sold) and the seeded Tomato 480 kg (Grade A, listed)."),
    ("13_marketplace.png", "Buyer marketplace", "The buyer (Riverstone Foods) sees the three listings that are still for sale with their photographs, grade badges, quantity and asking price: Tomato 620 kg at INR 2,250 (Grade B), Potato 640 kg at INR 1,180 (Grade B) and the seeded Tomato 480 kg at INR 1,950 (Grade A, no image). Filters for crop, region and grade sit above the cards."),
    ("14_listing_detail.png", "Listing detail", "The buyer's view of the tomato lot: photograph, Grade B, INR 2,250, 620 kg available, the quality breakdown radar with \"Confidence 70%\" and, below it, the market price trend (reference price for this crop, grade and region)."),
    ("15_place_order_dialog.png", "Place-order dialog", "The Place order dialog over the blurred listing: quantity 620 kg and agreed price INR 2,250 per quintal entered by the buyer, and the Confirm order button."),
    ("16_buyer_orders.png", "Buyer orders", "My orders for the buyer: Order #3, 620 kg at INR 2,250 per quintal, state **placed**, with a four-segment progress bar of which the first segment (placed) is filled."),
    ("18_farmer_orders_confirmed.png", "Farmer confirms an order", "The farmer's Orders page after pressing Confirm: Order #3 (620 kg, INR 2,250) and Order #2 (1,200 kg, INR 1,090) are confirmed, Order #1 (900 kg, INR 1,640) is still placed with its Confirm button; the toast reads \"Order confirmed\"."),
    ("19_distributor_deliveries.png", "Distributor: orders ready to ship", "Active deliveries for the distributor (Vikram Rao): the two confirmed orders, #3 and #2, each with a Start transit button."),
    ("20_distributor_in_transit.png", "Distributor: shipments in transit", "After Start transit on both orders: each row shows the badge \"in transit\", Live monitor and Mark delivered; the toast says \"Shipment started - live monitoring is now active\". Starting transit created a shipment record for each order."),
    ("22_live_monitoring.png", "Live shipment monitoring", "Shipment #1 about one minute after the page was opened: the Live indicator, and three trace panels for temperature (2.9 C), humidity (75.8%, after a step upwards) and shock (0.3 g). All values are inside the alarm band, so no banner is shown. The readings come from the simulated sensor stream over a WebSocket."),
    ("22b_live_alert.png", "Cold-chain alert toast", "44 seconds after the page was opened the simulator's first injected event arrived and the red toast \"Cold-chain alert - Sensor reading outside safe range\" appeared while the traces were still near normal (temperature 2.3 C, humidity 77.5%, shock 0.9 g)."),
    ("22c_live_alert_later.png", "Alert banner after drift", "215 seconds after opening the page the red banner \"Sensor readings are currently outside the safe range for this shipment\" is on: temperature 9.5 C and humidity 93.7% are highlighted in red. The temperature and humidity random walks had drifted out of the alarm band without any new event."),
    ("23_admin_overview.png", "Admin overview", "Platform overview: 5 listings (2 live, 3 sold), 3 orders, 1 farmer, 4 buyers, 1 distributor, 1 admin, and a gross transaction volume of INR 41,79,000. This volume is overstated by a factor of 100: the sum multiplies the price per quintal by the quantity in kilograms (see the section Success and Failure Analysis)."),
    ("24_model_insights.png", "Model insights: quality model", "The admin's transparency page: Random Forest classifier, the badge \"92.3% test accuracy\", the impurity importance of the 11 features (blemish ratio and colour uniformity largest, mean hue smallest) and the disclosure that the training data were synthetically generated and no real labelled image set was used."),
]
EXTRA_SCREENS = [
    ("02_login.png", "Log-in page", "The log-in form with the e-mail and password fields and the four demo-account shortcuts (farmer, buyer, distributor, admin).", None),
    ("04_signup.png", "Sign-up page", "The registration form with name, e-mail, password (minimum six characters), role (farmer, buyer or distributor), region and phone.", None),
    ("05_farmer_dashboard.png", "Farmer dashboard before an upload", "The Grade a new crop form with the default crop and quantity, the empty drop zone and photo preview, and the farmer's existing listings.", None),
    ("08b_price_forecast_scrolled.png", "Price forecast panel", "The forecast panel with the best-day line (\"Best day to sell within a safe window: Nov 9\"), followed by the Delivery planner and the List on the marketplace card with the asking-price field pre-filled with the forecast (2,272).", None),
    ("10_publish_listing.png", "Publishing a listing", "The asking price changed to INR 2,250 and the Publish listing button.", None),
    ("11_listing_published.png", "Listing published", "The forecast and the four ranked buyers after publishing; the toast says \"Listed on the marketplace - Tomato INR 2,250\".", None),
    ("17_farmer_orders_placed.png", "Farmer orders before confirming", "Orders #3 and #1 are placed and show Confirm buttons; Order #2 is already confirmed.", None),
    ("21_live_monitoring_start.png", "Live monitoring right after opening", "The page a few seconds after the WebSocket connected: the Live indicator and the three telemetry panels begin to fill.", None),
    ("24b_model_insights_scrolled.png", "Model insights: price model", "The price model card: Gradient Boosted Regression Trees with point estimate and quantile bands, the badge \"R2 0.992\", grouped importances (crop type largest; rainfall and average temperature almost zero) and the disclosure of synthetic training data.", None),
    ("07b_grading_full.png", "Listing workspace, full length", "The complete workspace after grading: quality card, the Forecast price and Plan delivery buttons and the List on the marketplace card.", 6.3),
    ("01b_landing_full.png", "Landing page, full length", "The whole landing page including the how-it-works, platform and intelligence sections.", 6.3),
]
KEY_SINGLE = {"07_grading_result.png", "08_price_forecast.png", "09_delivery_planner.png", "22c_live_alert_later.png"}
SCREENS = [(f, c, t) for f, c, t in MAIN_SCREENS] + [(f, c, t) for f, c, t, _ in EXTRA_SCREENS]


def sec_screens(d, all_screens=False):
    d.h2("Output Screens")
    d.p("Every screen below is a real capture of CropSight running with real data on 26 October 2026: real photographs of a tomato, onions and "
        "potatoes from a public vegetable dataset, the models trained from the project's code, and orders that moved through the full "
        "farmer, buyer and distributor flow. The farmer, buyer and distributor steps of the featured tomato lot were performed in the browser; "
        "the extra onion and potato listings and their orders were created through the same API the browser uses. The captures are 1440 by 900 "
        "pixels.")
    pending = []

    def flush():
        for i in range(0, len(pending), 2):
            pair = pending[i:i + 2]
            d.figure_pair([(SHOTS / f, cap) for f, cap, _t in pair], width=3.15, max_h=2.2)
            for f, cap, text in pair:
                if getattr(d, "report", False):
                    cut = text.find(". ", 90)
                    text = text[:cut + 1] if cut > 0 else text
                d.p(f"**{cap}.** {text}", size=10.5, line=1.25)
        pending.clear()

    for f, cap, text in MAIN_SCREENS:
        if f in KEY_SINGLE:
            flush()
            d.figure(SHOTS / f, cap, width=4.4)
            d.p(text, size=10.5, line=1.3)
        else:
            pending.append((f, cap, text))
    flush()
    if all_screens:
        d.h3("Additional screens")
        extra_block(d)


def extra_block(d):
    """Additional screens in side-by-side pairs, each pair followed by one line per screen."""
    small = [e for e in EXTRA_SCREENS if e[3] is None and not (getattr(d, 'report', False) and e[0] in ('08b_price_forecast_scrolled.png', '11_listing_published.png', '10_publish_listing.png'))]
    tall = [e for e in EXTRA_SCREENS if e[3] is not None] if not getattr(d, 'report', False) else []
    for group, width, mh in ((small, 3.15, 2.2), (tall, 2.9, 6.3)):
        for i in range(0, len(group), 2):
            pair = group[i:i + 2]
            d.figure_pair([(SHOTS / f, cap) for f, cap, _t, _m in pair], width=width, max_h=mh)
            for f, cap, text, _m in pair:
                d.p(f"**{cap}.** {text}", size=10.5, line=1.25)


def sec_engine_results(d):
    d.h2("Model Performance")
    d.p("CropSight contains two trained models, a Random Forest that grades a crop photograph and a Gradient Boosting model that prices it, "
        "and two rule-based parts, the delivery score and the sensor simulator. No real labelled crop-image set and no real market-price series "
        "were available to the project, so both models were trained on **synthetic data generated by the project's own code**. The admin screen "
        "says so. This has a consequence for how every figure in this section must be read: a score on a synthetic test set measures how well a "
        "model recovers the generator that produced its training data, not how it performs on a farm or in a market. To go beyond that, the "
        "grader was also run on 3,200 real photographs (see the subsection on real photographs below). All figures come from `experiments/*/metrics.json` and were produced on an "
        "Intel Core i5-12500 with 15.7 GB RAM and no GPU.")
    d.table([["Measure", "Result", "Data"],
             ["Quality grader accuracy (shipped split, 1,200 rows)", f"**{pc(RF['test_accuracy'])}**, macro F1 {RF['macro_f1']:.3f}", "synthetic"],
             ["Quality grader accuracy, five seeds", f"{pc(Q['seed_study']['accuracy_mean'])} +- {Q['seed_study']['accuracy_std'] * 100:.1f}", "synthetic"],
             ["Quality grader on real fruit photographs (fresh vs rotten)", f"**{pc(RP['mapped_binary_accuracy'])}** (chance 50%), AUC {RP['auc_fresh_vs_rotten_using_pA_plus_pB']:.3f}", "3,200 real photos"],
             ["Same 11 features retrained on real labels, 5-fold CV", f"**{pc(R['features_trained_on_real_labels']['five_fold_cv_accuracy_mean'])}**, AUC {R['features_trained_on_real_labels']['five_fold_cv_auc_mean']:.3f}", "3,200 real photos"],
             ["Price model MAE / RMSE (INR per quintal)", f"**{G['mae']:.1f}** / {G['rmse']:.1f}", "synthetic"],
             ["Price model R2 / MAPE", f"**{G['r2']:.4f}** / {pc(G['mape'])} (noise floor {pc(P['noise_floor']['generating_function_vs_observed']['mape'])})", "synthetic"],
             ["15-85% price band coverage (nominal 70%)", pc(G["band_empirical_coverage"]), "synthetic"],
             ["Delivery ranking: top buyer unchanged under weight changes", pc(DL["weight_perturbation"]["top1_unchanged_mean"]), "256 cases, 4 buyers"],
             ["Automated tests", "36 passed, 3 expected failures", "pytest"],
             ["Upload-and-grade response time (median / 95th percentile)", f"{AP['upload_and_grade']['median_ms']:.0f} ms / {AP['upload_and_grade']['p95_ms']:.0f} ms", "live API"]],
            "Headline results", widths=[0.5, 0.33, 0.17], font=9.5)

    d.h3("Quality grader on its synthetic test set")
    per = RF["per_class"]
    rows = [["Grade", "Precision", "Recall", "F1", "Support"]] + [[g, f"{per[g]['precision']:.3f}", f"{per[g]['recall']:.3f}", f"{per[g]['f1-score']:.3f}", f"{int(per[g]['support'])}"] for g in RF["labels"]]
    d.table(rows, "Per-grade results of the Random Forest (1,200 synthetic test rows)", widths=[0.2, 0.2, 0.2, 0.2, 0.2], font=10, align=["l", "c", "c", "c", "c"])
    d.figure(CHARTS / "01_quality_confusion_matrix.png", "Confusion matrix of the quality grader on the synthetic test set", width=3.0)
    d.p(f"Accuracy is {pc(RF['test_accuracy'])} and macro F1 {RF['macro_f1']:.3f} (train accuracy {pc(RF['train_accuracy'])}). Of the {RF['errors']} errors, "
        f"all are between neighbouring grades: none confuses A with C or Reject, or B with Reject. The model is a little less confident when it is wrong "
        f"(mean top probability {RF['mean_confidence_wrong']:.2f} against {RF['mean_confidence_correct']:.2f} when right). Over five different splits and forest seeds the "
        f"accuracy is {pc(Q['seed_study']['accuracy_mean'])} with a standard deviation of {Q['seed_study']['accuracy_std'] * 100:.1f} points (range "
        f"{pc(Q['seed_study']['accuracy_min'])} to {pc(Q['seed_study']['accuracy_max'])}).")
    d.p(f"**What the number means.** The training data contain 6% label noise (360 of 6,000 labels moved to a neighbouring grade), so the best a model "
        f"can do on the noisy test labels is about {pc(RF['max_possible_accuracy_if_noise_unlearnable'])}. Scored against the clean labels of the same test rows the forest "
        f"reaches {pc(RF['accuracy_vs_clean_labels_on_same_test_rows'])}, and trained and tested on clean labels {pc(Q['clean_label_reference']['accuracy_trained_and_tested_on_clean_labels'])}. "
        "The grader has therefore learned the generator's grade profiles almost completely; that is the ceiling of this experiment.")
    b = Q["baselines"]
    d.table([["Model (same split)", "Accuracy", "Macro F1"]] + [[n, f"{b[k]['accuracy']:.3f}", f"{b[k]['macro_f1']:.3f}"] for n, k in
            [("Majority class", "majority_class"), ("Decision tree (depth 9)", "decision_tree_depth9"), ("Histogram gradient boosting", "hist_gradient_boosting"),
             ("Random Forest (shipped)", "random_forest_shipped"), ("k-nearest neighbours (k = 15)", "knn_k15"), ("Logistic regression", "logistic_regression")]],
            "Baselines on the same synthetic split", widths=[0.5, 0.25, 0.25], font=10, align=["l", "c", "c"])
    if not getattr(d, "report", False):
        d.figure(CHARTS / "03_quality_baselines_seeds.png", "Baselines and the five-seed study", width=5.0)
    d.p("A linear model (0.931) and k-nearest neighbours (0.930) match the forest (0.923): the synthetic grade classes are close to linearly separable, "
        "so the choice of forest over a simpler model is not justified by accuracy on this data. It is justified by the tree-based SHAP explanations and by "
        "the expectation that real data will not be separable linearly.")
    d.figure_pair([(CHARTS / "02_quality_feature_importance.png", "Impurity and permutation importance of the 11 features"), (CHARTS / "04_quality_ablation.png", "Feature-group ablation: one group alone against all but one group")], width=3.15, max_h=2.6)
    ab, on = Q["ablation_drop_group"], Q["ablation_only_group"]
    d.p(f"Blemish ratio (impurity importance 0.241) and colour uniformity (0.239) matter most; mean hue matters least (0.004). Removing any single "
        f"group costs at most {(RF['test_accuracy'] - min(a['accuracy'] for a in ab.values())) * 100:.1f} points because the groups carry overlapping information; each group alone "
        f"gives {pc(min(a['accuracy'] for a in on.values()), 0)} (size score) to {pc(max(a['accuracy'] for a in on.values()), 0)} (colour).")

    d.h3("Quality grader on real photographs")
    di = R["dataset"]
    d.p(f"To test the grader outside its own generator, the real feature extractor and the shipped model were run on all {di['images_used']:,} images of the Fresh and "
        f"Rotten Fruits dataset [8] (CC BY 4.0): {di['fresh']:,} fresh and {di['rotten']:,} rotten photographs of eight fruits, 200 of each state per fruit. The dataset "
        "labels are fresh or rotten, not A, B, C or Reject, so the check maps fresh to {A, B} and rotten to {C, Reject}; this mapping is an assumption of the "
        "check, and the fruits are not CropSight's crops, but a grader that sees quality in a photograph should still rank a rotten fruit below a fresh one.")
    sh = RP["predicted_grade_share_by_label"]
    d.table([["True state", "Grade A", "Grade B", "Grade C", "Reject"]] + [[s.capitalize()] + [pc(sh[s][g], 2) for g in ("A", "B", "C", "Reject")] for s in ("fresh", "rotten")],
            "Grades predicted by the shipped model for 3,200 real fruit photographs", widths=[0.28, 0.18, 0.18, 0.18, 0.18], font=10, align=["l", "c", "c", "c", "c"])
    d.figure(CHARTS / "05_real_photos_grade_share.png", "Predicted grade share for fresh and rotten photographs", width=3.5)
    f = R["features_trained_on_real_labels"]
    d.p(f"**The shipped grader does not transfer.** It calls {pc(sh['fresh']['B'])} of the fresh and {pc(sh['rotten']['B'])} of the rotten photographs grade B; the mapped "
        f"fresh-or-rotten accuracy is {pc(RP['mapped_binary_accuracy'])} (chance is 50%) and the area under the ROC curve of P(A)+P(B) is {RP['auc_fresh_vs_rotten_using_pA_plus_pB']:.3f}. "
        f"Per fruit the AUC ranges from {min(v['auc'] for v in R['shipped_model_per_fruit'].values()):.2f} (jujube, i.e. inverted) to {max(v['auc'] for v in R['shipped_model_per_fruit'].values()):.2f} (strawberry). "
        f"{pc(R['share_real_images_outside_every_synthetic_profile_3sd'])} of the real images lie outside the three-standard-deviation envelope of every synthetic grade profile.")
    d.figure(CHARTS / "06_real_photos_auc_per_fruit.png", "Fresh-versus-rotten AUC of the shipped model for each fruit", width=3.8)
    d.figure(CHARTS / "07_real_vs_synthetic_features.png", "Mean feature values of the synthetic grade profiles and of the real photographs", width=5.6)
    d.p("The reason is visible in the feature means: real photographs have mean hue 0.14 (synthetic grades 0.24-0.28), texture contrast 0.02 (synthetic 0.18-0.64), blemish ratio "
        "0.14 for both fresh and rotten fruit and colour uniformity 0.70-0.72. The synthetic profiles were written by hand around plausible values, and real images fall "
        "in none of them; the classifier maps all of them to the middle grade.")
    d.figure(CHARTS / "08_real_label_retrain.png", "Fresh-versus-rotten accuracy: shipped model, retrained on real labels, and retrained on unseen fruits", width=3.8)
    d.p(f"The extractor itself is not the problem. The same 11 features, with a Random Forest of the same size trained on the real labels, reach {pc(f['five_fold_cv_accuracy_mean'])} accuracy "
        f"(AUC {f['five_fold_cv_auc_mean']:.3f}) in five-fold cross-validation. When whole fruit types are held out the accuracy falls to {pc(f['leave_fruits_out_accuracy_mean'])} (AUC "
        f"{f['leave_fruits_out_auc_mean']:.3f}), so the features are fruit-specific. The most important real-label features are mean hue ({f['importance'][0]['importance']:.2f}) and mean saturation "
        f"({f['importance'][1]['importance']:.2f}), the opposite order to the synthetic model. The practical conclusion is that the grader must be retrained on real labelled images of "
        "the crops it is meant to grade before its grades can be trusted.")

    d.h3("Price model")
    nf = P["noise_floor"]
    d.table([["Measure", "Value"],
             ["Test MAE / RMSE (3,504 rows, INR per quintal)", f"{G['mae']:.1f} / {G['rmse']:.1f}"],
             ["R2 / MAPE", f"{G['r2']:.4f} / {pc(G['mape'], 2)}"],
             ["Noise floor (noise-free generating formula against the observed price)", f"MAE {nf['generating_function_vs_observed']['mae']:.1f}, MAPE {pc(nf['generating_function_vs_observed']['mape'], 2)}"],
             ["Model against the noise-free formula", f"MAE {nf['model_vs_noise_free_truth']['mae']:.1f}, MAPE {pc(nf['model_vs_noise_free_truth']['mape'], 2)}"],
             ["Five seeds, MAE / R2", f"{P['seed_study']['mae_mean']:.1f} +- {P['seed_study']['mae_std']:.1f} / {P['seed_study']['r2_mean']:.4f} +- {P['seed_study']['r2_std']:.4f}"],
             ["Time hold-out (train 2022-23, test 2024), MAE / R2 / MAPE", f"{P['time_holdout']['mae']:.1f} / {P['time_holdout']['r2']:.3f} / {pc(P['time_holdout']['mape'])}"],
             ["15-85% band: empirical coverage, mean width", f"{pc(G['band_empirical_coverage'])} (nominal 70%), {pc(G['band_width_pct_of_price'])} of the price"],
             ["Test rows where the lower quantile model exceeds the upper one", f"{G['band_crossing_rows']} of {G['test_rows']:,}"]],
            "Price model results on the synthetic series", widths=[0.62, 0.38], font=9.5)
    bl = P["baselines"]
    d.table([["Model", "MAE", "R2", "MAPE"]] + [[n, f"{bl[k]['mae']:.0f}", f"{bl[k]['r2']:.3f}", pc(bl[k]["mape"])] for n, k in
            [("Crop mean", "crop_mean"), ("Crop x grade mean", "crop_x_grade_mean"), ("Linear regression", "linear_regression"), ("Random Forest (200 trees)", "random_forest_200"), ("Gradient boosting (shipped)", "gradient_boosting_shipped")]],
            "Price baselines on the same split", widths=[0.46, 0.18, 0.18, 0.18], font=10, align=["l", "c", "c", "c"])
    d.figure_pair([(CHARTS / "10_price_baselines_importance.png", "Price baselines and grouped feature importance"), (CHARTS / "09_price_scatter.png", "Observed against predicted price on the synthetic test set")], width=3.15, max_h=2.6)
    d.p(f"The boosted model clearly beats every baseline and sits close to the noise floor of its data (MAPE {pc(G['mape'])} against {pc(nf['generating_function_vs_observed']['mape'])}). "
        f"The 2024 hold-out is only slightly worse (R2 {P['time_holdout']['r2']:.3f}) even though the trend feature leaves its training range. The error is largest for the Reject grade "
        f"(MAPE {pc(P['per_grade']['Reject']['mape'])}, against 4.2% for grades A and B) and for the dearest crop, cotton (MAE {P['per_crop']['Cotton']['mae']:.0f}). "
        f"The 70% band covers {pc(G['band_empirical_coverage'])} of the observed prices, so it is well calibrated on this data.")
    fi = P["feature_importance_grouped"]
    d.p(f"**What the model learned.** Crop type carries {pc(fi[0]['importance'], 0)} of the importance, quality grade {pc(fi[1]['importance'], 0)}, market supply {pc(fi[2]['importance'], 0)} and demand "
        f"{pc(fi[3]['importance'], 0)}; rainfall and average temperature are almost zero ({fi[-2]['importance']:.5f} and {fi[-1]['importance']:.5f}). The generator uses temperature not at all and rainfall only "
        "above 150 mm, which almost never occurs, so a model that ignores weather is correct for this data - and a reminder that weather, one of the inputs the project "
        "set out to use, plays no real role here.")
    d.p(f"**Behaviour of the served forecast.** The forecast shown to the farmer evaluates the point model on 31 successive daily market contexts that are generated from a hash of crop, region "
        f"and date (not from a weather or demand feed). Over all {SF['combinations']} crop, region and grade combinations the recommended best day is today in {pc(SF['best_sell_day_zero_share'])} of cases, "
        f"on average day {SF['best_sell_day_mean']:.1f}, and waiting for it would raise the price by {SF['mean_gain_pct_if_waiting_to_best_day']:.1f}% on average (median {SF['median_gain_pct']:.1f}%, largest "
        f"{SF['max_gain_pct']:.0f}%); the mean spread between the highest and lowest price over 30 days is {SF['mean_30d_range_pct']:.1f}% of the mean. These swings come from the hashed daily noise in demand and "
        "supply, so the sell-day advice is an illustration of the interface, not market information. The price order A > B > C > Reject holds for all 64 crop-region pairs.")
    d.figure(CHARTS / "11_best_sell_day_hist.png", "Distribution of the recommended best sell day over 256 combinations", width=3.8)

    d.h3("Delivery recommendation")
    d.p(f"The delivery engine is a weighted score, not a trained model: 0.38 price, 0.22 distance, 0.18 quality fit, 0.14 reliability and 0.08 low spoilage risk (the weights sum to 1.00). "
        f"For all {DL['combinations']} crop, region and grade combinations an independent re-computation reproduced the served top buyer in {DL['replica_matches_served_top1']} cases. When every weight was "
        f"multiplied by a random factor between 0.5 and 1.5 (100 trials per case) the top buyer stayed the same {pc(DL['weight_perturbation']['top1_unchanged_mean'])} of the time (worst case "
        f"{pc(DL['weight_perturbation']['top1_unchanged_min'], 0)}) and the full ranking correlated at {DL['weight_perturbation']['rank_correlation_mean']:.2f} with the original, so the ranking is stable. "
        "Across the four buyers distance separates them most, then price; quality fit does not differ between buyers at all, because it is a property of the lot. The offered prices are the "
        "model price times a hash-derived factor between 0.90 and 1.18, so they are simulated, not quotes.")
    if not getattr(d, "report", False):
        d.figure(CHARTS / "13_delivery_weights.png", "Scoring weights and the spread each term creates between buyers", width=4.2)

    d.h3("Sensor stream and alerts")
    d.p(f"The sensor stream is simulated (no hardware exists). Over 50 simulated shipments of 1,200 steps the first alert came after a median of {IO['median_first_flag_step']:.0f} steps "
        f"({IO['median_first_flag_minutes']:.1f} minutes at 1.4 s per step). The temperature and humidity are random walks without a pull back to normal, so shipments drift out of the alarm band: 28% were in alarm by "
        f"step 50, 58% by step 100 and all 50 by step 400, and {pc(IO['share_of_flags_that_are_persistent_drift'])} of all flagged steps were persistent drift rather than injected events. "
        f"The median longest uninterrupted alarm lasted {IO['median_longest_alarm_run_steps']:.0f} of the 1,200 steps. The live run reproduced this: the first alert after 44 s and a persistent banner at 215 s.")
    d.figure(CHARTS / "12_iot_alarm_behaviour.png", "Share of simulated shipments in alarm (left) and one simulated trajectory, the demo shipment of order 3, seed 304 (right)", width=5.6)

    d.h3("Response time")
    keys = [("login", "Log in (bcrypt)"), ("health", "Health check"), ("upload_and_grade", "Upload and grade a 900 x 675 photograph"), ("price_predict", "Price forecast with SHAP"),
            ("delivery_recommend", "Delivery recommendation"), ("marketplace_listings", "Marketplace listings"), ("admin_overview", "Admin overview"), ("admin_model_insights", "Admin model insights")]
    d.table([["Endpoint", "n", "Median (ms)", "95th percentile (ms)"]] + [[n, str(AP[k]["n"]), f"{AP[k]['median_ms']:.1f}", f"{AP[k]['p95_ms']:.1f}"] for k, n in keys],
            "API response times (live server on 127.0.0.1, same machine, other jobs running)", widths=[0.5, 0.1, 0.18, 0.22], font=10, align=["l", "c", "c", "c"])
    if not getattr(d, "report", False):
        d.figure(CHARTS / "14_api_latency.png", "Median and 95th-percentile response time per endpoint", width=4.6)
    d.p("Grading a photograph, including feature extraction, the forest, SHAP and the database write, takes about 0.17 s; the slowest call is the bcrypt log-in at about 0.33 s, which is "
        "intended. No load test with many concurrent users was run.")


def sec_product_results(d):
    d.h2("Software Verification Results")
    d.p("The backend has a pytest suite (`backend/tests`) that uses a throw-away SQLite database. **36 tests pass and 3 are expected failures** (about 30 s). The three expected failures "
        "are tests that assert the behaviour a hardened system should have and fail on the shipped code; they are kept visible rather than deleted.")
    d.table([["Group", "Tests", "What is checked"],
             ["Health and authentication", "8", "sign-up and log-in round trip, duplicate e-mail, no admin self-sign-up, validation errors, wrong password, token required, tampered token rejected"],
             ["Role guards", "1", "a buyer cannot upload, a farmer cannot order, non-admins cannot read admin routes, a distributor cannot ask for a delivery plan"],
             ["Listings, grading and CV features", "12", "grade, probabilities and 11 features returned; blemished photo not graded above a clean one; non-image and oversize uploads rejected; feature vector contract; deterministic grading; foreign listings are 404"],
             ["Price intelligence", "5", "response shape (31 days, band contains the price, best day 0-14), A > B > C > Reject, listing grade is used"],
             ["Delivery", "3", "top five sorted by score within 0-100, weights sum to 1, foreign listing is 404"],
             ["Marketplace and orders", "5", "browse and filter, full lifecycle placed to delivered with every guard, unlisted listing cannot be ordered, role-scoped order lists"],
             ["IoT and simulator", "4", "WebSocket delivers three readings, history stored, unknown shipment 404, simulator deterministic per seed and bounded"],
             ["Admin", "1", "overview counts, both models' transparency cards"],
             ["Expected failures", "3", "corrupt image returns HTTP 500 and leaves a gradeless draft listing; unknown crop is accepted; non-positive order quantity is accepted"]],
            "Automated test results", widths=[0.24, 0.08, 0.68], font=9)
    d.p("The end-to-end flow was also executed in the browser: a farmer graded, forecast, planned and published a tomato lot; a buyer ordered it; the farmer confirmed; a distributor started transit, "
        "watched the live stream and could mark the order delivered. Every state change was refused when attempted by the wrong role or out of order (tested in the suite).")


def sec_comparison(d):
    d.h2("Comparison with the Base Paper")
    d.p("The base paper [1] builds an AI-driven smart-agriculture system for the pre-harvest stage: IoT soil sensors and a weather API feed deep tabular models for irrigation advice (Transformer-based "
        "tabular learning, accuracy 99.13%), soil analysis (TabNet regressor, RMSE 1.51, R2 98.7%), crop recommendation (SwiFT, 98.75%) and fertiliser recommendation (TabNet classifier, 99.3%), "
        "with explainable-AI techniques (LIME [21] and TabNet [22] among them) and a chatbot. CropSight takes the same idea of IoT, learning and explanation into the post-harvest stage. **The two works differ in task, data, model family "
        "and metric, and CropSight's data are synthetic, so the figures cannot be compared and no head-to-head claim is made.** What can be compared is capability.")
    d.table([["Aspect", "Base paper [1]", "CropSight"],
             ["Stage of the farm cycle", "Before harvest: soil, irrigation, crop and fertiliser choice", "After harvest: quality grading, price, delivery, marketplace"],
             ["Input data", "Tabular soil, weather and crop records; IoT sensor readings", "Crop photographs; synthetic market series; simulated sensor stream"],
             ["Models", "Transformer-based tabular learning, TabNet, SwiFT (deep)", "Random Forest, Gradient Boosting with quantile bands (classical), weighted scoring"],
             ["Explainability", "XAI techniques applied to TabNet predictions", "SHAP for both models, shown to the farmer; feature importance for the admin"],
             ["IoT", "Soil sensors for real-time analysis", "Simulated cold-chain stream over WebSocket with alerts; no hardware"],
             ["Reported results", "99.13% (irrigation), RMSE 1.51 / R2 98.7% (soil), 98.75% (crop), 99.3% (fertiliser)", f"{pc(RF['test_accuracy'])} grading and R2 {G['r2']:.3f} pricing on synthetic data; chance level on real photographs"],
             ["Marketplace and delivery", "Not part of the system", "Farmer, buyer and distributor marketplace with order states; delivery ranking"],
             ["User interface", "Chatbot interface for farmers", "React web app with four role dashboards"]],
            "CropSight and the base paper", widths=[0.2, 0.4, 0.4], font=9)
    d.p("The batch literature survey also lists [3] (image-based quality inspection and e-commerce grading), [4] and [5] (crop price prediction with machine learning). These three could not be "
        "retrieved, so no result from them is used here.")
    d.p("Two other works that were read support the direction. The foundation-model study [6] shows on real USDA price data that modern time-series models beat classical, machine-learning and deep-learning "
        "forecasters; CropSight's price model uses none of that and is trained on synthetic data, so it is the first thing to replace. The crop-image recognition study [7] reports an accuracy of 0.982 for a "
        "ConvLSTM-based model on real crop images; again a different task and data.")


def sec_samples(d):
    d.h2("Sample Inputs and Outputs")
    ch = json.loads((SAMPLES / "_chosen.json").read_text(encoding="utf-8"))
    rows = [["Photograph", "Crop", "Photos scanned", "Grade", "Confidence"]]
    for crop in ("Tomato", "Onion", "Potato"):
        for k in ch[crop]["kept"]:
            gc = ch[crop]["grade_counts"]
            rows.append([k["file"], crop, f"{ch[crop]['scanned']} (A {gc['A']}, B {gc['B']}, C {gc['C']}, Reject {gc['Reject']})", k["grade"], f"{k['confidence']:.3f}"])
    d.table(rows, "Real sample photographs and the grades the shipped model gave them", widths=[0.2, 0.12, 0.38, 0.12, 0.18], font=9.5)
    d.figure_pair([(SAMPLES / "tomato_1.jpg", "tomato_1.jpg, graded B (0.701)"), (SAMPLES / "potato_2.jpg", "potato_2.jpg, graded A (0.834)")], width=3.0, max_h=2.4)
    d.p("The photographs come from the public vegetable dataset [9]. Forty photographs of each crop were graded and the examples were chosen so that the screens show more than one grade; this selection "
        "is not a test. All 40 tomatoes and all 40 onions were graded B and 39 of 40 potatoes were graded B, which is consistent with the real-photograph finding that the grader gives B to almost everything.")
    d.table([["Input", "Output"],
             ["Photograph tomato_1.jpg, Tomato, 620 kg, Sunridge Valley (farmer)", "Grade B, confidence 70.1%; top SHAP features colour uniformity, blemish ratio, texture homogeneity; stored as a draft listing"],
             ["Forecast for the graded lot", "Current price INR 2,272 per quintal, range 2,068 to 2,272, 30-day curve, best day to sell 9 November"],
             ["Delivery plan for the lot", "1 Harvest & Co. 67.7% (INR 2,533, 773.6 km, 2.5 days); 2 Coastal Fresh Distributors 60.9%; 3 GreenMart Wholesale 60.1%; 4 Riverstone Foods 56.5%"],
             ["Publish at INR 2,250; buyer orders 620 kg at INR 2,250", "Listing becomes sold; Order #3 placed; farmer confirms; distributor starts transit; shipment #1 opens the live stream"],
             ["Wrong password for the farmer account", "HTTP 401, message \"Invalid email or password\""],
             ["Admin overview after the demo", "5 listings (2 live, 3 sold), 3 orders, 7 users (1 farmer, 4 buyers, 1 distributor, 1 admin); displayed volume INR 41,79,000"]],
            "Sample inputs and outputs (live run, 26 October 2026)", widths=[0.4, 0.6], font=9)


def sec_success_failure(d):
    d.h2("Success and Failure Analysis")
    d.h3("Where it works")
    d.bullets([
        "The complete marketplace flow works end to end with four roles, JWT authentication and an order state machine that refuses wrong-role and out-of-order changes (36 passing tests).",
        "Grading, SHAP explanation, price forecast with a band, delivery ranking and the live sensor stream all respond quickly: 0.17 s to upload and grade, 55 ms median for a price forecast, 100 ms for a delivery plan.",
        "On its own generated data the grader reaches 92.3% and the price model R2 0.992, with errors only between neighbouring grades and a band that covers 69.3% against 70% nominal.",
        "The weighted delivery ranking is stable: the top buyer survives 97.7% of random weight changes.",
        "The admin transparency page discloses honestly that both models are trained on synthetic data.",
    ])
    d.h3("Where it fails or is weak")
    d.table([["Observation", "Cause", "Effect / handling"],
             ["Grader gives grade B to 99% of 3,200 real photographs and is at chance for fresh versus rotten (50.4%, AUC 0.57)", "Trained only on synthetic feature profiles that real images do not resemble", "Grades on real photographs are not trustworthy; retrain on real labelled images (future scope)"],
             ["A corrupt file sent as an image gives HTTP 500 and leaves a gradeless draft listing", "The listing row is saved before grading and grading is not guarded", "Expected-failure test; wrap grading and roll back the listing"],
             ["Admin gross volume INR 41,79,000 for three small orders", "Price per quintal multiplied by quantity in kilograms (100 times too large)", "Divide by 100; the correct figure for the demo orders is INR 41,790"],
             ["Sensor alarm drifts into permanent alarm; each connection restarts the stream from its seed", "Random walks without mean reversion; simulator state lives in the connection", "Add return-to-normal behaviour and hysteresis; keep state per shipment"],
             ["Order accepts zero, negative or larger-than-listing quantities", "No validation of quantity or price", "Expected-failure test; add schema constraints and a stock check"],
             ["Unknown crop or region is priced instead of rejected", "No catalogue check; unknown crop uses an all-zero one-hot", "Expected-failure test; validate against the catalogue"],
             ["Displayed price range ends exactly at the current price", "The band is clamped to include the point estimate", "Report the unclamped quantile band or recalibrate"],
             ["Landing page shows 38,400+ crops graded, +17% price uplift, 92% accuracy, 2,400+ farmers", "Fixed marketing numbers in the page source", "Remove or replace with real statistics"],
             ["\"Best day to sell\" suggests large gains (mean +14.6%)", "Hash-generated daily demand and supply noise, not a real forecast", "Treat as an illustration; replace with a real time-series model"]],
            "Failure and weakness analysis", widths=[0.34, 0.33, 0.33], font=8.5)


def sec_results_limits(d):
    d.h2("Limits of the Results")
    d.bullets([
        "**Synthetic data.** The accuracy of 92.3%, the R2 of 0.992 and the 70% band all describe recovery of the project's own generators. They say nothing about real farms or markets; the only real-image evidence is the negative result above.",
        "**Mapped labels.** The real-photograph check maps fresh and rotten to grades and uses fruits instead of the app's crops; it shows non-transfer clearly but cannot measure the accuracy of A, B, C and Reject grading.",
        "**Simulated sensors and offers.** The sensor stream, the buyer offers and the daily market context are generated, so the alert behaviour, the ranking and the sell-day advice illustrate the interface only.",
        "**Small, single-machine measurements.** Timings come from one desktop with other jobs running, 20 to 30 calls per endpoint, no concurrent load and no memory profile; no user study was carried out.",
        "**Chosen photographs.** The sample photographs on the output screens were picked from 40 scanned per crop to show more than one grade.",
        "**No numeric comparison with the base paper** is possible, as explained in the section Comparison with the Base Paper.",
    ])


def sec_objectives(d):
    d.h2("Objectives Against Outcomes")
    d.table([["Objective", "Outcome", "Evidence"],
             ["1. Grade crop quality automatically from images", "Partly achieved", f"Implemented as classical machine learning on 11 hand-crafted features, not a deep network; {pc(RF['test_accuracy'])} on synthetic data; at chance on 3,200 real photographs; retraining on real labels reaches {pc(f_acc())}"],
             ["2. Forecast crop prices from market, weather and demand data", "Partly achieved", f"Boosted model with a 70% band, R2 {G['r2']:.3f} on synthetic data; weather has almost no effect; the 30-day forecast uses generated context; no real price feed"],
             ["3. Monitor storage and transport with IoT sensors", "Demonstrated with simulation only", "WebSocket stream, stored readings and alert banner work end to end; no hardware, and the alarm drifts into permanent alarm"],
             ["4. Explain grading and pricing decisions with XAI", "Achieved", "SHAP top-six contributions for every grade and price, shown in the app; importance charts for the admin"],
             ["5. Recommend buyers, routes and the best time to sell", "Achieved as a heuristic", "Weighted ranking stable under weight changes (97.7%); route is the top buyer's town; offers and sell-day advice are simulated"],
             ["6. Connect farmers, distributors and buyers through a marketplace", "Achieved", "Four roles, listings, orders, state machine, shipments; 36 tests pass; 3 validation gaps documented"]],
            "Objectives against outcomes", widths=[0.34, 0.16, 0.5], font=9)


def f_acc():
    return R["features_trained_on_real_labels"]["five_fold_cv_accuracy_mean"]
