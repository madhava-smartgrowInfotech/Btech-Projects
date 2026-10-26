"""Chapter 8: Results and output screens. Every number is read from facts.py (experiments/metrics.json, experiments/api_latency.json) or typed exactly as in docs/REPORT_FACTS.md."""
import json
import os
from collections import Counter

from . import facts as F
from .blocks import B, CODE, FIG, H1, H2, H3, P, PAIR, TAB
from .refs import N

SH = F.shot
CLS, FC, HL, AS, IMP = F.CLS, F.FC, F.HL, F.AS, F.IMP
BT = FC["demo_backtest"]
SEEDN = CLS["seed_examples"]


def S(name, caption, base=5.6, max_h=3.7):
    """Screenshot figure with a width that keeps the picture on one page."""
    return FIG(SH(name), caption, F.shot_w(SH(name), base, max_h))


REPORT_DROP = {"f03_per_category_prf.png", "f04_confidence_coverage.png", "f07_sim_mape_noise.png", "f10_health_distribution.png",
               "f11_api_latency.png", "f12_assistant_coverage.png", "f13_seed_distribution.png"}   # shown in the chapter document, not repeated in the full report


def G(name, caption, width=5.6):
    """Result figure from docs/figures; omitted if the file has not been produced (and, in the report variant, if it only repeats a table)."""
    path = F.fig(name)
    if F.REPORT and name in REPORT_DROP:
        return []
    return [FIG(path, caption, width)] if os.path.exists(path) else []


def _compact(blocks):
    """Report variant: drop the sub-headings and put the screenshots two per figure, each with its own caption."""
    out, pend = [], []
    for blk in blocks:
        if blk[0] == "h3":
            continue
        if blk[0] == "fig":
            pend.append((blk[1], blk[2]))
            if len(pend) == 2:
                out.append(PAIR(pend, 2.95))
                pend = []
        else:
            out.append(blk)
    if pend:
        out.append(FIG(pend[0][0], pend[0][1], 4.0))
    return out


REPORT_DROP_TABLES = ("Evidence gathered", "Tier-C accuracy after adding random corrections")


def _drop_tab(blocks):
    """Report variant: drop tables whose content is already in the text or in a chart shown in the report."""
    if not F.REPORT:
        return blocks
    return [b for b in blocks if not (b[0] == "tab" and b[1].startswith(REPORT_DROP_TABLES))]


def _counts(n_right, n):
    return f"{n_right}/{n}"


def _errors():
    errs = CLS["errors"]
    to_transport = sum(1 for e in errs if e["predicted"] == "Transport")
    tier = Counter(e["tier"] for e in errs)
    by_true = Counter(e["true"] for e in errs if e["predicted"] == "Transport")
    return errs, to_transport, tier, by_true


# ------------------------------------------------------------------------------------------ 8.1
def _setup():
    return _drop_tab(_setup_all())


def _setup_all():
    mach = F.LAT["machine"]
    return [H2("8.1 Experimental set-up"),
            P("FINJARVIS has no large training corpus, so this chapter reports what the running application shows (Section 8.2), how its three analytical modules behave when measured (Sections 8.3 to 8.5), "
              "how the assistant, the import pipeline and the API perform (Sections 8.6 and 8.7) and how the results compare with the base paper (Section 8.8). "
              "Every table and chart is drawn from `experiments/metrics.json` and `experiments/api_latency.json`, written by `scripts/run_experiments.py` and `scripts/measure_api.py`."),
            H3("8.1.1 The data"),
            P(f"The categoriser is trained on {SEEDN} short example descriptions in {CLS['seed_categories']} categories that are written into `ml/expense_classifier.py`; no public dataset was used. "
              "The application data are the fictional records of the demo account (`demo` / `Demo@1234`): 68 transactions over six months (May to October 2026), five budgets, "
              "three savings goals and four investment holdings, built from the 34-row file `data/sample_transactions.csv` (dates shifted to the current month) "
              "and three earlier synthetic months (seed 411, drift of about 4 % a month). **All of these data are fictional**: they show that the mechanisms work, not how a real household spends."),
            H3("8.1.2 The probe set"),
            P(f"Because the application has no train and test split of its own, the team wrote a probe set of {CLS['probe_examples']} descriptions before scoring (`scripts/probe_data.py`): 18 for each of the 11 categories, "
              "in three tiers of 6 per category. Tier A uses wording close to the seed list, tier B upper-case bank-statement strings that contain a seed keyword (for example `UPI-HOSPITAL-BILL`), "
              "and tier C merchants and phrases the model has never seen (for example `BigBasket delivery`, `Jio 599 plan`). The probe set was never used for training. "
              "It is **not an independent benchmark**: the same team wrote the seed list and the probe set."),
            H3("8.1.3 Machine and software"),
            P(f"All measurements were made on one machine: an Intel Core i5-12500 (6 cores, 12 threads) with 15.7 GB of memory, an Intel UHD 770 integrated GPU (not used), Windows 11 Pro and Python {mach['python']}, "
              f"with scikit-learn {CLS['sklearn_version']}. API timings use the backend on `127.0.0.1`, a throw-away SQLite file with the demo data, one client and a warm server."),
            TAB("Evidence gathered and the file it comes from.", ["Measurement", "What was done", "Stored in"],
                [["Categoriser", f"Accuracy, macro scores, confusion matrix, tiers, keyword baseline, leave-one-out, confidence and correction experiments on {CLS['probe_examples']} probe descriptions", "metrics.json: classifier"],
                 ["Forecast", "One-step-ahead rolling-origin backtest on the demo account; synthetic simulation of 2,000 users per setting", "metrics.json: forecast"],
                 ["Health score", "Sensitivity sweeps from a baseline profile; 5,000 random profiles", "metrics.json: health"],
                 ["Assistant", "26 team-written questions (20 answerable, 6 off-topic) asked of the rule layer", "metrics.json: assistant"],
                 ["Import", "1,000-row CSV with 84 injected bad rows", "metrics.json: import"],
                 ["API", "30 repetitions per endpoint (10 for reports and import preview)", "api_latency.json"],
                 ["Tests", f"{F.PYTEST_TOTAL} pytest tests and {F.SMOKE_TOTAL} smoke-test checks", "pytest and scripts/smoke_test.py output"]],
                widths=[1.2, 3.8, 1.5], align=["l", "l", "l"], size=9.5)]


# ------------------------------------------------------------------------------------------ 8.2
def _screens():
    b = [H2("8.2 Output screens"),
         P("The screens below were captured from the running application with Playwright at 1440 by 900 pixels, logged in as the demo account; none is a mock-up. "
           "Every amount on them belongs to the fictional demo records (Section 8.1.1). The light-theme landing page, the sign-up page and the light-theme dashboard are in Appendix C.")]
    b += [H3("8.2.1 Landing and login"),
          S("01_landing-dark.png", "Landing page (dark theme): the hero card shows the demo account for October 2026 with health score 90 (Excellent), income INR 65K, spent INR 30.1K and 54 % saved; the strip below lists what the product does."),
          S("03_login.png", "Login page: username or e-mail, password, a Try the demo account button and the demo credentials.")]
    b += [H3("8.2.2 Dashboard"),
          S("05_dashboard.png", "Dashboard for October 2026: balance INR 1,98,382, income INR 65,000, expenses INR 30,080, savings INR 34,920 (53.7 %), investments INR 84,250, net worth INR 2,82,632, average budget usage 44 %. The health card shows 90 (Excellent), component scores 100, 100, 100, 100, 80 and 24, and names Goal Progress as the area to focus on."),
          S("06_dashboard-charts.png", "Dashboard charts: income against expenses, spending by category (led by Rent), the six-month trend and the allocation of the four holdings.")]
    b += [H3("8.2.3 Transactions"),
          S("07_transactions-add.png", "Add a transaction: type, date, amount, description, a category that defaults to Auto-detect (AI), payment method and notes; a manual category that differs teaches the model."),
          S("08_transactions-manage.png", "View and manage: 68 transactions, income INR 3,90,000 and expenses INR 1,91,618 for the six months, with filters, search, sort and edit and delete icons."),
          S("09_transactions-import.png", "Import from CSV or Excel: the preview reports Row 6 as skipped and lists the four valid rows with categories the AI filled in; nothing is saved until the preview is confirmed.")]
    b += [H3("8.2.4 Analytics and forecast"),
          S("10_analytics.png", "Analytics for 24 July to 22 October 2026: income INR 1,95,000, expenses INR 1,14,194, savings rate 41.4 %, daily average INR 1,359 and largest expense INR 18,000 (rent); the category chart is led by Rent, Investments and Shopping."),
          S("11_analytics-prediction.png", "Spending trend and prediction: the expense curve for May to October 2026 and the prediction card: next month INR 39,471 from six months, recent three-month average INR 36,592, trend Increasing.")]
    b += [H3("8.2.5 Budgets, goals and investments"),
          S("12_budgets.png", "Budgets for October 2026: Food 15 %, Transport 9 %, Entertainment INR 2,200 of 2,500 (88 %, Getting close), Shopping 45 % and Bills 65 %, each with a progress bar; warnings are promised at 75, 90 and 100 %."),
          S("13_goals.png", "Financial goals: Emergency Fund 32 %, New Laptop 19 % and Vacation 20 %, each with the suggested monthly saving and an update field."),
          S("14_investments.png", "Investments: invested INR 77,860, value INR 84,250, profit INR 6,390 (8.21 %) over four holdings, with an allocation donut and profit and loss by asset.")]
    b += [H3("8.2.6 Assistant, reports, notifications and profile"),
          S("15_assistant.png", "AI assistant: two questions answered from the user's own data (Rent at INR 108,000 is the top category; health 90.4, Excellent, weakest area goal progress). A banner notes that free-form answers are off because no AI_API_KEY is set."),
          S("16_reports.png", "Financial reports: month and year selectors and three downloads, a PDF summary, an Excel workbook and a CSV of every transaction."),
          S("17_notifications.png", "Notifications: one unread alert, Your Entertainment budget is 75% used, created when spending crossed the 75 % threshold."),
          S("18_profile.png", "Profile: name, e-mail, currency INR, monthly income INR 65,000, savings target INR 20,000, risk preference Moderate and a card that loads the fictional demo data.")]
    return _compact(b) if F.REPORT else b


# ------------------------------------------------------------------------------------------ 8.3
def _classifier():
    return _drop_tab(_classifier_all())


def _classifier_all():
    t, k, m = CLS["tfidf_lr"], CLS["keyword_table"], CLS["majority_class"]
    errs, to_tr, tier, by_true = _errors()
    cm = CLS["confusion_matrix"]
    diag = sum(cm[i][i] for i in range(len(cm)))
    cc = {c["threshold"]: c for c in CLS["confidence_curve"]}
    pc = CLS["per_category"]
    rows_pc = [[n, f"{v['precision']:.3f}", f"{v['recall']:.3f}", f"{v['f1']:.3f}", f"{round(v['recall'] * v['support'])}/{v['support']}"] for n, v in pc.items()]
    lc = CLS["learning_from_corrections"]
    rm = CLS["repeat_merchant_learning"]
    up = CLS["unseen_text_prediction"]
    top3 = sorted(up["probabilities"].items(), key=lambda kv: -kv[1])[:3]
    return ([H2("8.3 Expense categoriser"),
             H3("8.3.1 Accuracy on the probe set"),
             P(f"The shipped model (TF-IDF with word unigrams and bigrams followed by logistic regression) labels {diag} of the {CLS['probe_examples']} probe descriptions correctly, an accuracy of **{t['accuracy']:.4f}** "
               f"(macro precision {t['macro_precision']:.4f}, macro recall {t['macro_recall']:.4f}, macro F1 **{t['macro_f1']:.4f}**). The headline hides a sharp split between the tiers: "
               f"{t['accuracy_by_tier']['A'] * 100:.1f} % on wording close to the seed list ({_counts(round(t['accuracy_by_tier']['A'] * 66), 66)}), {t['accuracy_by_tier']['B'] * 100:.1f} % on upper-case statement strings that contain a seed keyword ({_counts(round(t['accuracy_by_tier']['B'] * 66), 66)}), "
               f"and only **{t['accuracy_by_tier']['C'] * 100:.1f} %** on merchants it has never seen ({_counts(round(t['accuracy_by_tier']['C'] * 66), 66)}). "
               f"On the same 198 descriptions the fallback keyword table scores {k['accuracy']:.4f} (macro F1 {k['macro_f1']:.4f}) and always answering {CLS['majority_label']} scores {m['accuracy']:.4f}; "
               "the learned model beats the table on every tier, but almost entirely in tiers A and B."),
             TAB("Categoriser on the 198-description probe set.", ["Model", "Accuracy", "Macro P", "Macro R", "Macro F1", "Tier A", "Tier B", "Tier C"],
                 [["TF-IDF + logistic regression (shipped)", f"{t['accuracy']:.4f}", f"{t['macro_precision']:.4f}", f"{t['macro_recall']:.4f}", f"{t['macro_f1']:.4f}", f"{t['accuracy_by_tier']['A']:.3f}", f"{t['accuracy_by_tier']['B']:.3f}", f"{t['accuracy_by_tier']['C']:.3f}"],
                  ["Keyword table (fallback)", f"{k['accuracy']:.4f}", f"{k['macro_precision']:.4f}", f"{k['macro_recall']:.4f}", f"{k['macro_f1']:.4f}", f"{k['accuracy_by_tier']['A']:.3f}", f"{k['accuracy_by_tier']['B']:.3f}", f"{k['accuracy_by_tier']['C']:.3f}"],
                  [f"Majority class ({CLS['majority_label']})", f"{m['accuracy']:.4f}", f"{m['macro_precision']:.4f}", f"{m['macro_recall']:.4f}", f"{m['macro_f1']:.4f}", f"{m['accuracy_by_tier']['A']:.3f}", f"{m['accuracy_by_tier']['B']:.3f}", f"{m['accuracy_by_tier']['C']:.3f}"]],
                 widths=[2.0, 0.7, 0.65, 0.65, 0.65, 0.55, 0.55, 0.55], align=["l"] + ["c"] * 7, size=8.5),
             ] + G("f01_classifier_tiers.png", "Accuracy of the three models on each probe tier; the shipped model falls from near 100 % to 18 % on unseen merchants.", 5.4) +
            [P(f"On the 34-row bundled sample file the model labels all {CLS['sample_csv_rows']} rows as the file does (accuracy {CLS['sample_csv_accuracy']:.3f}), but its vocabulary overlaps the seed list, so that figure is optimistic. "
               f"Leave-one-out validation on the {CLS['loo_n']} seed pairs gives only **{CLS['loo_cv_accuracy_on_seed'] * 100:.1f} %** ({round(CLS['loo_cv_accuracy_on_seed'] * CLS['loo_n'])}/{CLS['loo_n']}): each seed phrase has three to six siblings that hardly share words with it, "
               "so a held-out phrase cannot be recognised. This shows how small the seed list is and agrees with tier C."),
             H3("8.3.2 Confusion matrix and per-category scores"),
             P(f"The confusion matrix of the probe set is shown below. The diagonal holds {diag} of 198 items. Almost all of the {len(errs)} errors fall in one column: **{to_tr} descriptions were labelled Transport**, "
               f"{tier['C']} of the {len(errs)} errors belong to tier C and only {tier['B']} to tier B (`UPI-AMAZON-PAY-8821` labelled Entertainment, because the seed list has `amazon prime video`, and `UPI-HOSPITAL-BILL` labelled Bills). "
               f"The cause is mechanical: a description made only of unseen words gives an all-zero TF-IDF vector, so the decision comes from the intercepts alone and Transport has the largest: for the nonsense text `{up['text']}` the model returns {up['predicted']} with probability "
               f"{up['probabilities']['Transport']:.3f}, against {top3[1][1]:.3f} for {top3[1][0]} and {top3[2][1]:.3f} for {top3[2][0]}. The model never outputs Other, so an unseen merchant is silently given a category.")]
            + G("f02_confusion_matrix.png", "Confusion matrix on the probe set (rows are true categories, 18 descriptions each); the Transport column collects the unseen-merchant errors.", 4.7) +
            [TAB("Per-category scores on the probe set (18 descriptions per category).", ["Category", "Precision", "Recall", "F1", "Correct"], rows_pc,
                 widths=[1.7, 1.0, 1.0, 1.0, 1.0], align=["l", "c", "c", "c", "c"], size=9.5),
             P(f"Precision is 1.000 for Healthcare, Rent, Travel, Investments and Salary; Transport's recall is {pc['Transport']['recall']:.3f} "
               f"but its precision only **{pc['Transport']['precision']:.3f}**: it is the dump class."),
             ] + G("f03_per_category_prf.png", "Precision, recall and F1 per category on the probe set; Transport recalls everything and is right on 27 % of what it claims.", 5.4) +
            [H3("8.3.3 Confidence and abstaining"),
             P(f"The model's probabilities are low in absolute terms (eleven classes, {SEEDN} examples) but informative: the mean top probability is {CLS['mean_confidence_correct']:.3f} when the label is right and {CLS['mean_confidence_wrong']:.3f} when it is wrong. "
               f"Withholding predictions below 0.15 would still label {cc[0.15]['coverage'] * 100:.1f} % of the items at {cc[0.15]['accuracy_on_kept'] * 100:.1f} % accuracy; at 0.20 it would keep {cc[0.2]['coverage'] * 100:.1f} % at {cc[0.2]['accuracy_on_kept'] * 100:.1f} %, "
               f"and at 0.25 {cc[0.25]['coverage'] * 100:.1f} % at {cc[0.25]['accuracy_on_kept'] * 100:.0f} %. **The application applies no such threshold.** Asking the user when the model is unsure would turn the Transport dump into a prompt for a correction, the cheapest improvement available."),
             ] + G("f04_confidence_coverage.png", "Accuracy on kept predictions and share of items kept as the minimum probability rises (computed offline; not part of the application).", 4.8) +
            [H3("8.3.4 Learning from corrections"),
             P("When a user picks a category that differs from the prediction, the application retrains on the seed list, the user's history and the correction. Two experiments measure what that buys. "
               f"In the first, k random tier-C items were added as corrections (30 draws per k) and accuracy was measured on the rest of tier C: it moved from {lc[0]['tier_C_accuracy_mean'] * 100:.1f} % with no corrections to {lc[-1]['tier_C_accuracy_mean'] * 100:.1f} % with {lc[-1]['corrections']}, "
               "so teaching the model some merchants hardly helps with others. "
               f"In the second, one unseen merchant was corrected and then narrated three other ways (`UPI-X-4412`, `POS X`, `X 2`; {rm['tests']} tests over {rm['items']} merchants): accuracy rose from {rm['accuracy_before_correction'] * 100:.1f} % to **{rm['accuracy_after_one_correction'] * 100:.1f} %**. "
               "A correction fixes that merchant for good but does not generalise; the second test is easy by construction, because the variants share the corrected words."),
             TAB("Tier-C accuracy after adding random corrections (mean and standard deviation over 30 draws).", ["Corrections added", "Mean accuracy", "Std"],
                 [[str(d["corrections"]), f"{d['tier_C_accuracy_mean'] * 100:.1f} %", f"{d['tier_C_accuracy_sd'] * 100:.1f}"] for d in lc],
                 widths=[1.6, 1.5, 1.0], align=["c", "c", "c"], size=9.5),
             ] + G("f05_learning_from_corrections.png", "(a) Tier-C accuracy against the number of corrections; (b) accuracy on the same merchant written three other ways, before and after one correction.", 5.8) +
            G("f13_seed_distribution.png", f"The complete training set: {SEEDN} descriptions, between 3 (Rent, Investments, Salary) and 6 (Food, Transport, Entertainment) per category.", 4.8) +
            [P(f"One prediction takes {CLS['predict_ms_per_description']} ms in process and retraining from the seed list {CLS['retrain_ms_seed_only']} ms. "
               "The pickled model in `ml/` was trained under scikit-learn 1.5.0 and loads under 1.9.1 with an `InconsistentVersionWarning`; retraining removes it.")])


# ------------------------------------------------------------------------------------------ 8.4
def _forecast():
    steps = BT["steps"]
    keys = [("linear_trend (app)", "Linear trend (app)"), ("mean_of_all", "Mean of all history"), ("mean_of_last_3", "Mean of last 3 months"), ("last_value", "Last value")]
    rows = [[lab, *[f"{s[k]:,.0f}" for s in steps], f"{BT['mae'][k]:,.0f}", f"{BT['mape_pct'][k]:.1f} %"] for k, lab in keys]
    sim_n = FC["sim_mape_by_noise_pct"]
    sim_h = FC["sim_mape_by_history_pct_noise_0.10"]
    app = BT["app_prediction_for_next_month"]
    cat = BT["category_prediction"]["predictions"]
    cat_sorted = sorted(cat.items(), key=lambda kv: -kv[1])
    hmap = {r["history_months"]: r for r in sim_h}
    act = ", ".join("{:,.0f}".format(s["actual"]) for s in steps)
    return ([H2("8.4 Spending forecast"),
             H3("8.4.1 Backtest on the demo account"),
             P(f"The forecast fits a straight line to the monthly expense totals and extends it one month. It was tested by rolling origin on the demo account's six monthly totals "
               f"({', '.join(f'{v:,.0f}' for v in BT['actual'])} INR for May to October 2026): months 4, 5 and 6 were each predicted from the months before them, so there are **only three test points**. "
               f"The linear trend followed the August to September rise but overshot October, when spending fell from {BT['actual'][4]:,.0f} to {BT['actual'][5]:,.0f}; its MAPE is **{BT['mape_pct']['linear_trend (app)']:.1f} %** "
               f"(MAE INR {BT['mae']['linear_trend (app)']:,.0f}). The mean of all history was better ({BT['mape_pct']['mean_of_all']:.1f} %, MAE INR {BT['mae']['mean_of_all']:,.0f}), and so was the mean of the last three months ({BT['mape_pct']['mean_of_last_3']:.1f} %). "
               "Three points cannot rank methods, but the trend model shows no demonstrated advantage here."),
             TAB("One-step-ahead forecasts for August, September and October 2026 (INR) and their errors.", ["Method", "Aug forecast", "Sep forecast", "Oct forecast", "MAE", "MAPE"], rows,
                 widths=[1.9, 0.9, 0.9, 0.9, 0.8, 0.7], align=["l", "c", "c", "c", "c", "c"], size=9.5),
             P(f"The actual values were {act} INR. On the full six months the application predicts INR **{app['predicted_next_month_expense']:,.0f}** for November (recent three-month average INR {app['recent_average']:,.0f}, trend {app['trend']}, "
               f"{app['months_used']} months used), as the Analytics page shows (Section 8.2.4). Per-category forecasts use the same fit: "
               + ", ".join(f"{c} {v:,.0f}" for c, v in cat_sorted) + " (INR); Rent equals its fixed INR 18,000, the one category where a straight line is exact."),
             ] + G("f06_forecast_backtest.png", "Actual monthly expenses against the four one-step-ahead forecasts for months 4 to 6 of the demo account.", 5.5) +
            [H3("8.4.2 Simulation: when does the trend help?"),
             P(f"To learn more than three points can tell, the team simulated {FC['sim_users_per_setting']:,} users per setting (seed 7): a level drawn between 20,000 and 60,000, a linear drift of N(0, 3 % a month), Gaussian noise and a 10 % chance of a 50 % spike. "
               "**These are synthetic data and say nothing about real households**; they show how the methods behave when the generating process is known. "
               f"At 5 % noise the trend gives a MAPE of {sim_n[0]['linear_trend (app)']:.1f} % against {sim_n[0]['mean_of_last_3']:.1f} % for the three-month mean; at 30 % noise {sim_n[-1]['linear_trend (app)']:.1f} % and {sim_n[-1]['mean_of_last_3']:.1f} %. "
               "The three-month mean was at least as good as the trend in every noise setting."),
             TAB("Simulated one-step-ahead MAPE (%) against noise (12-month histories).", ["Noise (sd / level)", "Linear trend (app)", "Mean of all", "Mean of last 3", "Last value"],
                 [[f"{r['noise_ratio']:.2f}", f"{r['linear_trend (app)']:.2f}", f"{r['mean_of_all']:.2f}", f"{r['mean_of_last_3']:.2f}", f"{r['last_value']:.2f}"] for r in sim_n],
                 widths=[1.3, 1.3, 1.1, 1.2, 1.0], align=["c"] * 5, size=9.5),
             ] + G("f07_sim_mape_noise.png", "Simulated MAPE of the four methods against noise.", 4.6) +
            [P(f"History length matters more than noise. At 10 % noise the trend needs about seven months before it overtakes a plain average: with 3 months its MAPE is {hmap[3]['linear_trend (app)']:.1f} % against {hmap[3]['mean_of_all']:.1f} % for the mean, "
               f"with 7 months {hmap[7]['linear_trend (app)']:.1f} % against {hmap[7]['mean_of_all']:.1f} %, and with 11 months {hmap[11]['linear_trend (app)']:.1f} % against {hmap[11]['mean_of_all']:.1f} %, because the mean of all history ignores the drift. "
               f"The three-month mean stays at least as good as the trend at every length ({hmap[11]['mean_of_last_3']:.1f} % at 11 months against {hmap[11]['linear_trend (app)']:.1f} %). "
               f"The application's minimum of {FC['min_months_required']} months is therefore too low: at that length the trend is the worst of the four."),
             ] + G("f08_sim_mape_history.png", "Simulated MAPE against months of history at 10 % noise; the dotted line marks the application's three-month minimum.", 4.6) +
            [P("The base paper's LSTM reports RMSE 137.2, MAE 89.5 and R-squared 0.63 on a synthetic savings series of unstated units " + N("base") + "; "
               "these cannot be compared with the errors above, since the series, target (savings, not expenses), units and validation differ.")])


# ------------------------------------------------------------------------------------------ 8.5
def _health():
    sw = HL["sweeps"]
    rc = HL["rating_counts"]
    bc = HL["baseline_components"]
    dem = [("Savings rate", 0.30, 100.0), ("Expense ratio", 0.20, 100.0), ("Budget adherence", 0.15, 100.0), ("Emergency fund", 0.15, 100.0), ("Investment diversification", 0.10, 80.0), ("Goal progress", 0.10, 24.0)]
    rows = [[n, f"{w:.2f}", f"{s:.0f}", f"{w * s:.1f}"] for n, w, s in dem]
    rows.append(["**Total**", "1.00", "", f"**{sum(w * s for _, w, s in dem):.1f}**"])
    return ([H2("8.5 Financial health score"),
             P("The score is a weighted sum of six components, each scaled to 0 to 100 (Chapter 6). It has no training data, so the results are about its behaviour, not its accuracy. "
               "The demo account scores **90.4 out of 100, Excellent**; its weakest component is goal progress (24)."),
             TAB("Components of the demo account's score (October 2026).", ["Component", "Weight", "Component score", "Contribution"], rows, widths=[2.4, 0.9, 1.3, 1.1], align=["l", "c", "c", "c"], size=9.5),
             H3("8.5.1 Sensitivity"),
             P(f"From a baseline profile (income INR 65,000, expenses INR 32,500, a savings rate of 20 %, a balance of INR 100,000, two budgets at 60 % and 90 %, two asset types and goals at 40 %) the score is {HL['baseline_profile_score']}. "
               f"Raising the savings rate from 0 % to 20 % lifts it from {sw['savings_rate'][1][1]} to {sw['savings_rate'][5][1]}, and no further (the component saturates at 20 %). "
               f"Raising monthly expenses from INR 20,000 to INR 75,000 lowers it from {sw['monthly_expenses'][0][1]} to {sw['monthly_expenses'][-1][1]}. A balance covering six months of expenses (INR 195,000 and above) lifts it to {sw['total_balance'][3][1]}, where it stops. "
               f"Goal progress from 0 % to 100 % adds {sw['goal_progress'][-1][1] - sw['goal_progress'][0][1]:.1f} points and each extra asset type 2 points up to five types. The curves are monotone and saturate where the formulas cap."),
             ] + G("f09_health_sensitivity.png", "Health-score sensitivity to each input, changed one at a time from the baseline profile.", 6.2) +
            [H3("8.5.2 Behaviour over 5,000 random profiles"),
             P(f"Over {HL['random_profiles']:,} random profiles the score ranged from {HL['score_min']} to {HL['score_max']} with a mean of {HL['score_mean']}; the ratings were Critical {rc['Critical']:,}, Needs Improvement {rc['Needs Improvement']:,}, Fair {rc['Fair']:,}, Good {rc['Good']:,} and Excellent {rc['Excellent']:,}. "
               f"Raising the savings rate by five points never lowered the score ({HL['monotonic_violations_when_savings_rate_plus5']} violations in {HL['random_profiles']:,} profiles). "
               "Two things limit what the score means. The savings rate and the expense ratio carry half of the weight and are strongly correlated (both derive from income minus expenses), so one habit is counted twice; "
               "and the weights are chosen by the team, not fitted to any outcome, with no user study. The score is a transparent summary, not a validated predictor of well-being."),
             ] + G("f10_health_distribution.png", "Ratings of 5,000 random profiles.", 4.2) +
            [])


# ------------------------------------------------------------------------------------------ 8.6
def _assistant():
    det = AS["detail"]
    pick = [d for d in det if d["question"] in ("How much did I spend on Food?", "Can I save 5000 this month?", "How can I reduce my expenses?", "What is my financial health?", "How much did I spend on groceries?", "What is my biggest expense?", "Tell me a joke")]
    rows = []
    for d in pick:
        ans = d["answer"].replace("\n", " ")
        ans = ans if len(ans) <= 110 else ans[:107] + "..."
        rows.append([d["question"], "analytics" if d["source"] == "analytics" else "fixed help text", ans.replace("₹", "INR ")])
    missed = [d["question"] for d in det if d["answerable"] and d["source"] == "fallback"]
    return ([H2("8.6 AI assistant"),
             P(f"The assistant routes a question through five rule handlers (can I save, reduce expenses, financial health, where am I spending, spending on a named category) and, only if none matches and an `AI_API_KEY` is set, to an optional language model; "
               f"otherwise it replies with a fixed help text. **The language-model layer was not exercised in any measurement.** The team wrote 26 questions, {AS['answerable']} answerable from the user's data and {AS['not_answerable']} off-topic, and asked them of the demo account. "
               f"The rule layer answered **{AS['answerable_handled_by_analytics']} of {AS['answerable']} (70 %)** answerable questions and correctly declined {AS['unanswerable_correctly_declined']} of {AS['not_answerable']} off-topic ones, wrongly answering {AS['unanswerable_wrongly_answered']}. "
               f"The {AS['answerable'] - AS['answerable_handled_by_analytics']} misses all fell to the fixed help text: " + "; ".join(f"\"{q}\"" for q in missed) + ": phrasings the keyword routing does not recognise."),
             ] + G("f12_assistant_coverage.png", "Outcome of the 26 test questions for the rule layer.", 4.4) +
            [TAB("Sample questions and the assistant's answers (demo account).", ["Question", "Answered by", "Answer (shortened)"], rows, widths=[1.7, 1.0, 3.8], align=["l", "l", "l"], size=9),
             P(f"The numbers in the answers are correct: the Food answer is INR {AS['numeric_check_food_truth']:,.2f}, equal to a direct SUM over the same records, and the top category is {AS['numeric_check_top_category_truth']} at INR 108,000.00, as a group-by maximum gives. "
               "One quirk remains: Am I overspending on shopping? is answered with the Shopping total (INR 13,165), not a comparison with the budget.")])


# ------------------------------------------------------------------------------------------ 8.7
def _performance():
    rows = []
    for k, v in F.LAT.items():
        if isinstance(v, dict) and "median_ms" in v:
            rows.append([k, str(v["n"]), f"{v['median_ms']:.1f}", f"{v['p95_ms']:.1f}", f"{v['max_ms']:.1f}"])
    return ([H2("8.7 Import pipeline, API latency and tests"),
             H3("8.7.1 Statement import"),
             P(f"A 1,000-row CSV was prepared with all categories blank and {IMP['injected_bad_total']} injected bad rows ({IMP['injected_bad_rows']['bad_date']} unparsable dates, {IMP['injected_bad_rows']['negative_amount']} negative amounts, "
               f"{IMP['injected_bad_rows']['blank_description']} blank descriptions and {IMP['injected_bad_rows']['non_numeric_amount']} non-numeric amounts). The pipeline skipped exactly {IMP['rows_skipped']} rows, each with a Row n warning, and imported {IMP['rows_imported']}, "
               f"auto-labelling all of them ({IMP['blank_category_rows_auto_labelled']}). Cleaning and categorising took {IMP['clean_and_categorise_s']} s and committing {IMP['commit_s']} s, **{IMP['rows_per_second_commit']} rows per second**: the commit opens one database session per row, "
               "the slow part and the first thing to change for large statements. The auto-labels inherit the accuracy of Section 8.3; their correct share is unknown, as the generated file has no ground truth."),
             H3("8.7.2 API latency"),
             P(f"Reads are fast, with medians between {F.lat('GET /goals'):.1f} and {F.lat('GET /analytics'):.1f} ms. "
               f"Login takes {F.lat('login'):.0f} ms because bcrypt is deliberately slow; the heaviest calls are the Excel report ({F.lat('GET /reports/excel'):.0f} ms) and the 100-row import preview ({F.lat('POST /transactions/import/preview'):.0f} ms). "
               "Single user, single process: no load or concurrency test was run."),
             TAB("API latency in milliseconds (n = repetitions).", ["Endpoint", "n", "Median", "p95", "Max"], rows, widths=[3.2, 0.5, 0.8, 0.8, 0.8], align=["l", "c", "c", "c", "c"], size=8.5),
             ] + G("f11_api_latency.png", "Median and 95th-percentile latency per endpoint.", 5.2) +
            [H3("8.7.3 Tests"),
             P(f"`pytest` ran {F.PYTEST_TOTAL} tests and all {F.PYTEST_PASSED} passed (authentication {F.PYTEST_FILES['test_auth.py']}, budgets {F.PYTEST_FILES['test_budget.py']}, financial health {F.PYTEST_FILES['test_financial_health.py']}, "
               f"machine learning {F.PYTEST_FILES['test_ml.py']}, transactions {F.PYTEST_FILES['test_transactions.py']}) in 11.5 s, with 16 warnings from the scikit-learn pickle version. "
               f"The end-to-end smoke script, which starts its own backend and a throw-away database, passed {F.SMOKE_PASSED} of {F.SMOKE_TOTAL} checks (rejected weak passwords and tampered tokens, 401 on protected routes, per-user isolation, transactions, import, budgets, goals, investments, analytics, the assistant, the three downloads, profile and the demo-data loader). "
               "Not tested: browser-level UI tests (screens were captured by script and inspected by eye), concurrency, a security scan, accessibility, the language-model layer and the live price refresh.")])


# ------------------------------------------------------------------------------------------ 8.8
def _base():
    t = CLS["tfidf_lr"]
    return [H2("8.8 Comparison with the base paper"),
            P(f"The registered base paper {N('base')} (Kharat et al.) builds four models in a Streamlit assistant: a BERT expense categoriser over 50 categories, a Q-learning budget recommender, an LSTM savings forecaster and an Isolation Forest anomaly detector. "
              "FINJARVIS implements simpler versions of the first and third modules, a rule-based substitute for the second and nothing for the fourth. The reported numbers belong to different data, label sets and models, so **they are shown side by side but must not be ranked**."),
            TAB("Base paper against this work.", ["Module", "Base paper [1]", "FINJARVIS (this work)", "Comparable?"],
                [["Categorisation", "BERT (bert-base-uncased, 10 epochs), 50 categories, SMOTE, 80/20 split of own data: accuracy 92.3 %, precision 90.8 %, recall 91.5 %, F1 91.1 %",
                  f"TF-IDF + logistic regression, {CLS['seed_categories']} categories, {SEEDN} training examples; team-written probe set: accuracy {t['accuracy'] * 100:.1f} %, macro F1 {t['macro_f1'] * 100:.1f} %; unseen merchants {t['accuracy_by_tier']['C'] * 100:.1f} %", "No: different data, 50 against 11 labels, model size, split"],
                 ["Budget recommendation", "Q-learning; convergence after about 150-200 of 300 episodes; no numeric accuracy", "Budgets are set by the user; alerts at 75, 90 and 100 %; rule-based advice (top categories, trim 10-15 %)", "No: nothing is learned here"],
                 ["Forecasting", "LSTM on a synthetic savings series: RMSE 137.2, MAE 89.5, R-squared 0.63 (units not stated)",
                  f"Linear trend on monthly expense totals: MAPE {BT['mape_pct']['linear_trend (app)']:.1f} % (MAE INR {BT['mae']['linear_trend (app)']:,.0f}) on 3 backtest points; synthetic simulation in Section 8.4", "No: different target, units and series"],
                 ["Anomaly detection", "Isolation Forest: precision 93 %, recall 94 %, F1 94 %, on data with synthetic outliers", "**Not implemented**; the nearest feature is the largest expense in a date range", "Not applicable"],
                 ["Interface and delivery", "Streamlit dashboard; Flask API mentioned", "React 18 + FastAPI web app with 13 pages, 33 routes, SQLite; Streamlit original kept", "Qualitative only"],
                 ],
                widths=[1.0, 2.1, 2.5, 0.9], align=["l", "l", "l", "l"], size=8.5),
            P("This work goes beyond the base paper in the product, not the models: a runnable multi-user web application with accounts, imports, budgets with alerts, goals, a portfolio, reports and an explainable score, plus a measurement of where its simple models fail. "
              "It falls short in modelling: no deep categoriser, learned budget policy, sequence forecaster or anomaly detector. The batch abstract names Flask and MySQL; the shipped system uses FastAPI and SQLite, and the loan tracking in the abstract and periodic digest alerts were not built.")]


# ------------------------------------------------------------------------------------------ 8.9
def _samples():
    ps = BT["app_prediction_for_next_month"]
    up = CLS["unseen_text_prediction"]
    det = {d["question"]: d for d in AS["detail"]}
    dump = lambda o: json.dumps(o, indent=2)  # noqa: E731
    errs = CLS["errors"]
    err_rows = [[e["description"], e["true"], e["predicted"], e["tier"]] for e in errs[:4]] + [[e["description"], e["true"], e["predicted"], e["tier"]] for e in errs if e["tier"] == "B"]
    ans = lambda q: det[q]["answer"].replace("\n", " ").replace("₹", "INR ")  # noqa: E731
    return [H2("8.9 Sample inputs and outputs"),
            P("The samples are taken from the stored experiment files; the demo account is fictional."),
            H3("8.9.1 Forecast"),
            CODE("# predict_next_month_expense(df) for the demo account's six months (Section 8.4)\n" + dump(ps), 8) if not F.REPORT else
            P(f"`predict_next_month_expense` on the demo account's six months returns predicted_next_month_expense {ps['predicted_next_month_expense']:,.2f}, recent_average {ps['recent_average']:,.2f}, trend {ps['trend']} and months_used {ps['months_used']} (Section 8.4)."),
            H3("8.9.2 Categoriser"),
            TAB("Misclassified probe descriptions (first four tier-C errors and both tier-B errors).", ["Description", "True category", "Predicted", "Tier"], err_rows, widths=[2.6, 1.5, 1.4, 0.6], align=["l", "l", "l", "c"], size=9.5),
            CODE("# text with no known word (all-zero feature vector)\ninput:     " + up["text"] + "\npredicted: " + up["predicted"] + "\nprobabilities (top 3): " +
                 ", ".join(f"{k} {v:.4f}" for k, v in sorted(up["probabilities"].items(), key=lambda kv: -kv[1])[:3]), 8),
            H3("8.9.3 Assistant"),
            CODE("Q: How much did I spend on Food?\nA: " + ans("How much did I spend on Food?") +
                 "\n\nQ: What is my financial health?\nA: " + ans("What is my financial health?")[:230] + "\n\nQ: What is my biggest expense?   (not matched)\nA: " + ans("What is my biggest expense?")[:130] + "...", 8)]


# ------------------------------------------------------------------------------------------ 8.10
def _analysis():
    errs, to_tr, tier, by_true = _errors()
    return [H2("8.10 Success and failure analysis"),
            H3("8.10.1 Where the product succeeds"),
            B("Every screen of Section 8.2 works end to end on the demo data: sign-up, login, transactions with import, budgets with alerts, goals, a portfolio, analytics, the assistant, three report formats and notifications.",
              f"The rules are exact and tested: {F.PYTEST_TOTAL} unit tests and {F.SMOKE_TOTAL} smoke checks pass, the assistant's numbers equal direct SUMs, the import skips exactly the {IMP['rows_skipped']} bad rows, and the health score is monotone in the savings rate over {HL['random_profiles']:,} random profiles.",
              f"The categoriser is dependable inside its vocabulary ({CLS['tfidf_lr']['accuracy_by_tier']['A'] * 100:.0f} % on seed-like wording, {CLS['tfidf_lr']['accuracy_by_tier']['B'] * 100:.0f} % on statement strings with a known keyword), and one correction fixes a repeat merchant in all {CLS['repeat_merchant_learning']['tests']} test cases.",
              f"Reads answer in under {F.lat('GET /analytics'):.0f} ms at the median and a categorisation takes {CLS['predict_ms_per_description']} ms."),
            H3("8.10.2 Where it falls short"),
            B(f"**Unseen merchants are silently mislabelled.** {to_tr} of the {len(errs)} probe errors are labelled Transport, tier-C accuracy is {CLS['tfidf_lr']['accuracy_by_tier']['C'] * 100:.1f} % and the model never answers Other or asks.",
              f"**Corrections do not generalise.** After {CLS['learning_from_corrections'][-1]['corrections']} corrections tier-C accuracy is {CLS['learning_from_corrections'][-1]['tier_C_accuracy_mean'] * 100:.1f} %; only repeats of a corrected merchant are fixed.",
              "**The seed list is tiny** (51 pairs, 3 to 6 per class), so leave-one-out accuracy is 11.8 %.",
              "**The forecast is not better than an average with fewer than seven months of history**, and the three-month minimum lets it run in exactly that regime; the demo backtest has only three points.",
              "**The assistant misses natural phrasings** (6 of 20 answerable questions) and answers a budget question with a category total.",
              "**Anomaly detection, reinforcement-learning budgeting, a sequence forecaster and a language-model categoriser were not built**, so objective 4 is not met and objectives 3 and 5 only in simple form.",
              f"**Import commits one row at a time** ({IMP['rows_per_second_commit']} rows per second).",
              "**Budget alerts are de-duplicated by message text**, so a budget that crosses 75 % again in a later month raises no new alert; the screenshot in Section 8.2.6 shows a 75 % message while Entertainment stands at 88 %, because the 90 % message appears only above 90 %.",
              "**Tokens are home-made signed tokens** (HMAC-SHA256, 7 days, no revocation) with a default development secret when `APP_SECRET_KEY` is unset, and the database is one SQLite file without migrations.")]


# ------------------------------------------------------------------------------------------ 8.11
def _limits():
    return [H2("8.11 Limitations of the evaluation"),
            B("All application data are fictional; no real person's transactions or bank API were involved.",
              f"The categoriser was scored on a {CLS['probe_examples']}-item probe set written by the team that wrote the seed list: a diagnostic, not a benchmark, whose tier proportions (one third unseen merchants) drive the headline accuracy.",
              "The forecast was backtested on three points of one fictional account; the simulation uses a generating process of the team's own choosing.",
              "The health-score weights are expert-chosen and not validated; no user study was run. The assistant was tested with 26 team-written questions and its language-model layer never ran.",
              "Latency was measured with one client over loopback on one machine; import speed shifts between runs when the machine is busy. Not exercised: live price refresh, concurrent users, mobile browsers, a security scan and accessibility testing.")]


# ------------------------------------------------------------------------------------------ 8.12
def _objectives():
    t = CLS["tfidf_lr"]
    rows = [["1. Secure user accounts with transaction import and manual entry", "Achieved",
             f"Sign-up and login with bcrypt hashes, password rules and signed tokens; per-user data scoping; manual entry and CSV or Excel import with preview (916 of 1,000 rows imported, 84 bad rows skipped); {F.PYTEST_TOTAL} tests and {F.SMOKE_TOTAL} smoke checks pass"],
            ["2. Categorise expenses automatically with text classification", "Partly achieved",
             f"TF-IDF + logistic regression labels with {t['accuracy'] * 100:.1f} % probe accuracy and {t['macro_f1'] * 100:.1f} % macro F1, but only {t['accuracy_by_tier']['C'] * 100:.1f} % on unseen merchants; 11 categories from {SEEDN} examples, no BERT"],
            ["3. Forecast upcoming expenses and savings with time-series models", "Partly achieved",
             f"A linear trend forecasts next month's expenses and per-category spend (INR {BT['app_prediction_for_next_month']['predicted_next_month_expense']:,.0f} for November on the demo); MAPE {BT['mape_pct']['linear_trend (app)']:.1f} % on three points, no better than a mean under seven months; savings are not forecast directly; no ARIMA or LSTM"],
            ["4. Detect anomalous transactions", "Not achieved", "No anomaly detector exists; only the largest expense in a date range is reported"],
            ["5. Personalised budget recommendations and alerts on threshold breaches", "Partly achieved",
             "Budgets are set by the user; alerts fire at 75, 90 and 100 % of a budget; advice is rule-based (top categories, a 10 to 15 % trim) and uses the user's own income and spending; no learned policy"],
            ["6. Visualise spending, category breakdown and forecasts on an interactive dashboard", "Achieved",
             "React dashboard, analytics, budgets, goals and investment pages with charts and a forecast card (Section 8.2); health score with six explained components; reports in PDF, Excel and CSV"]]
    return [H2("8.12 Objectives versus outcomes"),
            TAB("The six project objectives against what was measured.", ["Objective", "Status", "Evidence"], rows, widths=[2.0, 0.9, 3.6], align=["l", "l", "l"], size=9.5)]


# ------------------------------------------------------------------------------------------ 8.13
def _summary():
    t = CLS["tfidf_lr"]
    return [H2("8.13 Summary of findings"),
            B(f"FINJARVIS runs as a complete personal finance web application ({F.N_PAGES} pages, {F.N_ROUTES} routes, {F.N_TABLES} tables, {F.PYTEST_TOTAL} tests and {F.SMOKE_TOTAL} smoke checks passing); reads answer in under {F.lat('GET /analytics'):.0f} ms at the median.",
              f"The categoriser works on familiar wording ({t['accuracy_by_tier']['A'] * 100:.0f} % and {t['accuracy_by_tier']['B'] * 100:.0f} % on tiers A and B) but fails on unseen merchants ({t['accuracy_by_tier']['C'] * 100:.1f} %), mostly by answering Transport; a confidence threshold of 0.15 would keep {[c for c in CLS['confidence_curve'] if c['threshold'] == 0.15][0]['coverage'] * 100:.0f} % of items at {[c for c in CLS['confidence_curve'] if c['threshold'] == 0.15][0]['accuracy_on_kept'] * 100:.0f} % accuracy but is not applied.",
              "A correction fixes a repeated merchant completely, but 48 corrections lift accuracy on new merchants only from 18 % to 22 %.",
              f"The linear-trend forecast overshot October on the demo account (MAPE {BT['mape_pct']['linear_trend (app)']:.1f} % against {BT['mape_pct']['mean_of_all']:.1f} % for a plain mean) and, in simulation, needs about seven months of history to beat an average; the three-month minimum is too low.",
              f"The health score is explainable and monotone (demo account {90.4}, Excellent); its weights are not validated. The assistant answers {AS['answerable_handled_by_analytics']} of {AS['answerable']} answerable questions from the user's data and declines all off-topic ones; its language-model layer is untested.",
              "Anomaly detection, reinforcement-learning budgeting, an LSTM forecaster, a BERT categoriser, loan tracking and scheduled digests were not built; the base paper's four-model design is matched only partly, and its reported numbers are not comparable with these.",
              "Objectives 1 and 6 are met; objectives 2, 3 and 5 are met in simple form; objective 4 is not met.")]


def blocks():
    b = [H1("CHAPTER 8: RESULTS AND OUTPUT SCREENS")]
    b += (_setup() + _screens() + _classifier() + _forecast() + _health() + _assistant() + _performance() + _base() + _samples()
          + _analysis() + _limits() + _objectives() + _summary())
    return b
