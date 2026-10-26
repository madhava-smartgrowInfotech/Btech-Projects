"""Chapter 2: Literature survey."""

from . import facts as F
from . import lit
from .blocks import B, H1, H2, N, P, TAB
from .refs import N as C


def blocks():
    out = _blocks()
    if F.REPORT:   # compact report variant
        from .ch1 import trim
        out = trim(out, drop=("Forecast error needs care.", "The four remaining titles of the batch survey", "Put as questions this project can answer",
                              "The H&M release", "Security"),
                   drop_sections=("2.7 Datasets",),
                   replace={"Comparison of the surveyed work": ("tab", "Comparison of the surveyed work", ["Work", "Approach", "Reported result", "Limitation"],
                                                               [[r[0], r[1], r[3], r[4]] for k, r in zip([x[0] for x in lit.ROWS], lit.rows()) if k not in ("sugi", "dann", "singh", "muqar", "skend")],
                                                               [1.1, 2.3, 1.6, 1.5], ["l", "l", "l", "l"], 8.5)})
        out.insert(len(out) - 2, P("The four remaining titles of the batch survey (references " + C('s2', 's3', 's4', 's5') + ") were not locatable online and are listed in the reference list without any claim about their content. "
                                   "The H&M release used here contains transactions, articles and customers tables " + C('hm') + "."))
    return out


def _blocks():
    ds = F.DS
    return [
        H1("CHAPTER 2: LITERATURE SURVEY"),
        H2("2.1 Overview"),
        P("The survey has four threads, because the project joins four bodies of work. The first is gradient-boosted forecasting of retail demand and the forecasting competitions that established it. "
          "The second is explainability of such models, which is the subject of the base paper. The third is covariate shift and domain adaptation, which is what the base paper does not do and what this project adds. "
          "The fourth is fashion forecasting and the new-product (cold-start) problem, which motivates why adaptation matters in fashion. "
          f"The base paper {C('base')} is analysed in depth in Section 2.2; every claim about it in this report was checked against the paper itself, which is in the batch folder. "
          "Claims about the other works come from their own abstracts or from the base paper's account of them, and are limited to what those sources state."),
        P("The batch literature survey (5.LITERATURE SURVEY.docx) lists five works: the base paper and four 2026 papers on AI-driven demand forecasting and inventory. "
          "We searched for the four by title and could not locate them online, so they are listed in the reference list as the batch gave them and are not described or used for any claim here."),
        H2("2.2 Base Paper Analysis"),
        P(f"**Reference.** L. N. Mishra, B. Senapati, S. K. Nayak and A. J. Rangari, \"Explainable retail demand forecasting: a hybrid LightGBM-SHAP framework for inventory optimization,\" IEEE Access, vol. 14, 2026, doi 10.1109/ACCESS.2026.3675540 {C('base')}."),
        P("**Problem.** Gradient-boosting models predict retail demand well, but inventory planners distrust predictions they cannot interpret and override them even when the model beats their heuristics. "
          "The authors build on an earlier LightGBM study that explained its model only with global methods (permutation importance and partial-dependence plots) and add two further levels, so that planners can see both why a specific forecast was made and whether an average effect hides different behaviour in different products."),
        P("**Method.** A seven-stage pipeline: preprocessing, feature engineering, LightGBM training with Optuna tuning under time-ordered cross-validation, and four explainability levels. "
          "Level 1 is permutation feature importance (a global ranking); level 2 is partial-dependence plots (marginal effects); level 3 is SHAP, specifically TreeSHAP, for instance-level attribution; "
          "level 4 is individual conditional expectation (ICE), whose crossing curves reveal products that react to a feature in opposite ways and so justify segment-specific inventory policies. "
          "The authors name this fourth level as their main extension."),
        P("**Data and preprocessing.** The UCI Online Retail II data: transactions of a UK-based online giftware retailer from December 2009 to December 2011, about 1.07 million rows and 4,631 products. "
          "Preprocessing removes rows with non-positive quantity, missing customer identifier or non-positive unit price, and cancelled invoices; aggregates quantity by product and date; keeps products with at least 1,000 units sold and 150 active days; "
          "and removes outliers per product by the interquartile-range rule. The target is daily demand per product, forecast one day ahead."),
        P("**Features.** 41 engineered features in five categories (temporal, lag, rolling and derived features among them). Temporal features include weekday, month, quarter and sine-cosine encodings of the cycles; "
          "lag features are demand 1, 7, 14 and 28 days earlier; rolling statistics use windows of 3, 7, 14 and 28 days. The authors state a temporal-integrity rule: every feature at time t uses only information from t-1 or earlier, "
          "and rolling statistics are shifted by one step so that the current day is excluded. TrendCast adopts the same rule."),
        TAB("Base paper at a glance", ["Aspect", "What the base paper reports"],
            [["Model", "LightGBM, Optuna Bayesian (TPE) tuning, 30 trials, 3-fold TimeSeriesSplit, about 2 minutes"],
             ["Baselines", "Naive lag-1; 7-day moving average; linear regression; random forest (100 trees, depth 10); XGBoost and CatBoost (30 Optuna trials each)"],
             ["Headline result", "RMSE 33.71 and R2 0.243 on daily product-level demand; MASE 0.799 (20.1 % better than naive)"],
             ["Against baselines", "CatBoost 33.83 RMSE (difference 0.12, p = 0.917, not significant); XGBoost 33.89; random forest 0.45 RMSE worse; moving average 2.86 worse; naive lag-1 14.06 worse"],
             ["Statistics", "Paired t-tests on per-sample absolute errors with Bonferroni correction; 1,000-resample bootstrap confidence intervals; Durbin-Watson 1.91 on the residuals"],
             ["Dominant features", "Permutation importance: rolling_mean_28 (191.23) and price_relative (168.83) far ahead of all others"],
             ["Ablation", "Removing rolling features costs the most (change in R2 of -0.064); rolling features alone reach R2 0.184, 76 % of the full model, with 17 of 41 features; removing derived features costs -0.036"]],
            widths=[1.5, 5.0], align=["l", "l"], size=10),
        P("**Interpretation by the authors.** The three boosting libraries converge to within 0.5 % RMSE, which matches what the M5 competition reported, so the choice among them is made on speed and categorical handling. "
          "The R2 of 0.243 is modest, and the authors explain it with three factors: demand for individual products is intermittent and 'lumpy'; no promotion, holiday, weather or economic features were used on purpose, to isolate the contribution of transaction-derived features; "
          "and the data are a wholesale-like market with extreme heterogeneity across 4,631 products."),
        P("**Limitations stated by the authors.** One data set from one market, so generalisation to brick-and-mortar or other retail formats is unproven; a stationarity assumption that retail dynamics often break, with a need for drift monitoring; "
          "no external factors; a price-relative feature that divides by the product's mean price over all time and so leaks a little future information; SHAP's cost at scale; and one-day-ahead forecasting only, so multi-step error accumulation is not examined."),
        P("**What this project takes and what it adds.** We keep the problem (daily product-level demand), the temporal-integrity rule, the lag and rolling feature families, time-ordered tuning, a naive and moving-average baseline, and the interest in explanation. "
          "We change the learner to XGBoost, work on the H&M fashion data, and add what the paper lists as missing: a test of moving the model across contexts (domain adaptation) and a multi-step forecast. "
          "We do not reproduce the four-level explanation pipeline inside the application: the application shows gain importance, and exact TreeSHAP is computed offline. The table below sets the two side by side."),
        TAB("Base paper and TrendCast compared", ["Aspect", "Base paper", "TrendCast"],
            [["Learner", "LightGBM (plus XGBoost, CatBoost, RF, linear baselines)", "XGBoost (plus LightGBM, RF and simple baselines as comparison)"],
             ["Data", "UCI Online Retail II, UK online giftware, 1.07 M rows, 4,631 products, 24 months", f"H&M, fashion, subset of {ds['raw_rows']:,} rows, {ds['articles']} articles, 107 days"],
             ["Horizon", "One day ahead", "One day ahead (evaluation) and recursive 7, 14 and 30 days (application)"],
             ["Features", "41, five categories, rolling dominant", f"{ds['feature_cols']}, calendar, price, attributes, lag and rolling; lag and rolling dominant"],
             ["Explanation", "PFI, PDP, SHAP, ICE", "Gain importance in the application; TreeSHAP offline"],
             ["Distribution shift", "Not treated; listed as a limitation", "Importance-weighted domain adaptation, 6 pairs x 5 seeds, four controls"],
             ["Tuning", "Optuna TPE, 30 trials", "RandomizedSearchCV, 10 iterations x 3 time-ordered folds"],
             ["Significance tests", "Paired t-test, bootstrap CI", "Five seeds with standard deviation; no significance tests"]],
            widths=[1.25, 2.6, 2.65], align=["l", "l", "l"], size=10),
        H2("2.3 Gradient Boosting and Forecasting Competitions"),
        P(f"Gradient boosting builds an additive ensemble of shallow trees, each fitted to the residual errors of the ensemble so far {C('gbm')}. "
          f"XGBoost {C('xgb')} added regularisation of the tree weights, sparsity-aware split finding and a parallel implementation, and became the default tool for tabular data; "
          f"LightGBM {C('lgbm')} sped up training with histogram-based splitting and leaf-wise growth. Random forests {C('rf')}, which average independent deep trees, are the usual non-boosted comparison."),
        P(f"For retail, the evidence is the M5 competition on Walmart item sales {C('m5')}. The base paper summarises it as showing that boosted trees with hand-made features matched or beat deep-learning models, "
          "and concludes that feature engineering is the main accuracy lever. That is the reason this project uses a tabular booster with lag, rolling and calendar features rather than a neural forecaster, and our ablation (Chapter 8) agrees: "
          "the lag and rolling features carry most of the accuracy."),
        P(f"Forecast error needs care. Percentage errors explode when actual demand is zero, which is common for single articles, so the application reports a safe MAPE that skips zero days and says how many it skipped. "
          f"Scaled errors such as MASE {C('mase')} compare a model with the naive forecast and are used by the base paper; we report WAPE, the sum of absolute errors over the sum of demand, for the same reason."),
        H2("2.4 Explainability of Forecasting Models"),
        P(f"SHAP assigns each feature a Shapley value, the average marginal contribution of the feature over all orders of adding features, so that the contributions add up exactly to the prediction minus a baseline {C('shap')}. "
          f"TreeSHAP computes these values exactly and quickly for tree ensembles {C('treeshap')}. XGBoost can output them directly (the pred_contribs option), which is how we compute them without a further library. "
          "The base paper layers permutation importance, partial dependence and ICE on top, for global ranking, marginal effects and heterogeneity. "
          "Its argument for ICE is that two products can respond to the same feature in opposite ways and a partial-dependence curve then averages to a misleading flat line."),
        P("Our measurement is a reminder that the choice of importance method matters. The built-in gain importance of the trained XGBoost ranks is_month_end, lag_1 and quarter highest, "
          f"whereas the exact SHAP attribution on the test rows ranks lag_1 first by a wide margin; the rank correlation between the two is only {F.EX['spearman_rank_corr_shap_vs_gain']:.2f}. "
          "Gain overstates features, especially calendar columns, that are split on often but contribute little to the prediction."),
        H2("2.5 Covariate Shift and Domain Adaptation"),
        P(f"When a model is trained on data from one distribution and applied to another, its error on the new data can be much higher than on held-out data from the old one. "
          f"The theory of learning from different domains {C('bendavid')} bounds the target error by the source error plus a measure of the divergence between the domains, which explains why unrelated domains transfer badly. "
          f"Surveys of transfer learning {C('pan')} group the remedies by what changes between domains."),
        P(f"Covariate shift is the case in which the distribution of the inputs differs but the relation of demand to inputs is the same. Shimodaira {C('shim')} showed that weighting each training example by the ratio of the target to the source input density "
          f"gives consistent fitting when the model is mis-specified. Sugiyama et al. {C('sugi')} applied the same weights to cross-validation. "
          f"Bickel et al. {C('bickel')} avoid estimating two densities by modelling the shift with a discriminative classifier that tells training inputs from test inputs; "
          "the ratio of its class probabilities gives the weight. This classifier route is the one TrendCast implements: the weight of a source row is p/(1-p), where p is the domain classifier's probability that the row belongs to the target."),
        P(f"Neural methods learn features that are the same in both domains, either adversarially {C('dann')} or by aligning second-order statistics {C('coral')}. They were developed and tested largely on images, need more data and training than a tabular model, "
          "and are outside the scope of this project; we list them as future work. Two practical weaknesses of importance weighting are known from the literature and are visible in our results: "
          "the weights become extreme when the domains barely overlap, and they depend on how well the classifier is calibrated."),
        H2("2.6 Fashion and New-Product Forecasting"),
        P(f"Fashion adds two difficulties to retail forecasting. Thomassey {C('thom')} reviews clothing sales forecasting and names volatile demand, strong seasonality, many short-lived items and scarce history as the main obstacles, "
          "and proposes fuzzy, neural and data-mining models whose value is judged by their effect on the bullwhip effect in the supply chain. "
          f"Recent work concentrates on items with no history. Ekambaram et al. {C('ekam')} predict a new product's sales from its images, attributes and external factors such as holidays, events, weather and discounts with an attention-based multi-modal encoder-decoder, and report better accuracy and interpretability than k-nearest-neighbour baselines. "
          f"Singh et al. {C('singh')} analyse large-scale fashion sales to find which attributes drive demand and forecast demand for new items from them. "
          f"Skenderi et al. {C('skend')} fuse image-based Google Trends with product images and metadata on VISUELLE, a public data set of 5,577 products sold from 2016 to 2019, and forecast the whole horizon at once; "
          f"Papadopoulos et al. {C('muqar')} predict the visual popularity of new fashion products with a multimodal and quasi-autoregressive network. "
          f"Outside fashion, Zhou et al. {C('cdlf')} forecast new-product life cycles from static descriptors and similar products with a conditional diffusion model, and report better point and probabilistic forecasts than classical baselines on Intel product life cycles."),
        P("These studies treat the cold start as the main problem and rely on images, text or external signals that the H&M files used here do not contain in usable form. "
          "TrendCast has no cold-start mode; Chapter 8 reports an offline test that shows how much (and how little) product attributes and the calendar can do for an unseen article."),
        P("The four remaining titles of the batch survey are, as listed there: *Impact of AI-driven demand forecasting on retail inventory efficiency* (2026); *Enhancing inventory planning in retail SMEs through data-driven demand forecasting* (2026); "
          "*Does the forecaster matter? A systematic evaluation of demand forecasting and inventory control policies across retail demand regimes* (2026); and *Predictive inventory management for retail distribution networks: reorder point optimization and machine learning demand forecasting* (2026). "
          f"They are cited as {C('s2', 's3', 's4', 's5')}. Their titles show the same interest in linking forecast error to inventory, which our offline inventory calculation addresses in a simple way; we make no claim about their content."),
        H2("2.7 Datasets and Algorithms Used in Related Work"),
        TAB("Data sets and algorithms in the surveyed work", ["Work", "Data set", "Algorithms"],
            [["Base paper", "UCI Online Retail II, 1.07 M transactions, 4,631 SKUs", "LightGBM, XGBoost, CatBoost, random forest, linear regression, moving average, naive; PFI, PDP, SHAP, ICE"],
             ["M5 (as summarised by the base paper)", "Walmart item sales", "Boosted trees with hand-made features; deep-learning entries"],
             ["Ekambaram et al.", "Large fashion data set of a retailer", "Attention-based multi-modal encoder-decoder; k-nearest-neighbour baselines"],
             ["Singh et al.", "Large-scale fashion sales", "Neural architectures, ML methods, several loss functions"],
             ["Skenderi et al.", "VISUELLE, 5,577 new products, 2016-2019", "Image-based Google Trends encoder, multimodal decoder"],
             ["Papadopoulos et al.", "Mallzee, SHIFT15m, VISUELLE and others", "Multimodal perceptron with quasi-autoregressive network"],
             ["Zhou et al.", "Intel microprocessor SKU life cycles; open-model repositories", "Conditional diffusion forecaster"],
             ["Shimodaira; Bickel; Sugiyama", "Theory and benchmark tasks", "Importance weighting; discriminative covariate-shift learning; weighted cross-validation"],
             ["This project", f"H&M subset: {ds['raw_rows']:,} rows, {ds['articles']} articles, 107 days", "Moving average, XGBoost, random forest, LightGBM; logistic domain classifier with importance weighting; TreeSHAP offline"]],
            widths=[1.6, 2.4, 2.5], align=["l", "l", "l"], size=10),
        P(f"The H&M release {C('hm')} contains the three tables used here: transactions (date, customer, article, price, sales channel), articles (names, product type and group, colour, department, section, garment group, description) and customers. "
          "Unlike the UCI data it covers a fashion retailer with a mass-market assortment and, unlike VISUELLE, it carries no sales-plan or image signals in the files we use."),
        H2("2.8 Strengths and Limitations of Existing Research"),
        P("The table below lists each surveyed work with its approach, data, reported result and limitation, using only what its paper or abstract states."),
        TAB("Comparison of the surveyed work", ["Work", "Approach", "Data", "Reported result", "Limitation"], lit.rows(),
            widths=[0.95, 1.65, 1.15, 1.35, 1.4], align=["l", "l", "l", "l", "l"], size=8.5),
        P("**Strengths.** Boosted trees on engineered lag and rolling features are accurate, fast and tabular-friendly; the base paper shows how to explain them at several levels and how to test differences statistically; "
          "the covariate-shift literature supplies a simple, theoretically grounded weighting scheme; the fashion literature identifies attributes, images and external signals as the way to forecast items without history."),
        P("**Limitations.** Retail forecasting studies, including the base paper, validate on one data set; explanation work stops at the model and rarely connects to the shift between contexts; "
          "importance weighting is known to be fragile when domains barely overlap, but retail applications seldom report the weights or compare against simple controls; "
          "and the cold-start methods need images or external signals. None of the works above reports a boosted-tree demand model moved across sales channels or product groups of one fashion retailer, with controls."),
        H2("2.9 Research Gap"),
        P(lit.GAP),
        P("Put as questions this project can answer with the data it has: does importance-weighted adaptation improve a boosted-tree demand forecaster on a differently distributed target domain of a real fashion retailer, "
          "compared with the same model without weights, with a model trained on the target alone, with unweighted pooling and with random weights? And is any improvement real, or does it come from how the experiment is arranged? "
          "Chapters 6 and 8 give the method and the answers."),
    ]
