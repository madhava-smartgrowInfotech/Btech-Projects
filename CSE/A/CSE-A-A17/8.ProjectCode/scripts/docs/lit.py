"""Literature rows shared by the report (Chapter 2), the decks and the paper:
(key, work, approach, data, reported result, limitation). Only facts checked against the paper, its arXiv abstract page or the base paper's own text."""

ROWS = [
    ("base", "Mishra et al. (base paper)", "LightGBM with four explainability levels (permutation importance, PDP, SHAP, ICE); 41 features; Optuna tuning",
     "UCI Online Retail II, 1.07 M transactions, 4,631 SKUs, one-day-ahead", "RMSE 33.71, R2 0.243; XGBoost 33.89, CatBoost 33.83; MASE 0.799",
     "One dataset and one market; no domain shift or new-product handling; one-step horizon; its own price feature leaks slightly (stated by the authors)"),
    ("xgb", "Chen and Guestrin", "XGBoost: regularised, sparsity-aware tree boosting with a weighted quantile sketch", "General tabular benchmarks",
     "Became the default tabular learner; accepts per-row sample weights", "Assumes training and test data come from one distribution"),
    ("m5", "Makridakis et al. (M5)", "Large retail forecasting competition; boosted trees with hand-built features among the best entries (as summarised in the base paper)", "Walmart item-level sales",
     "Gradient boosting matched or beat deep learning when given rich features", "One retailer; hierarchical sales, not new-market transfer"),
    ("shim", "Shimodaira", "Weights the training loss by the ratio of target to source input density under covariate shift", "Theory and simulations",
     "Weighted fitting is the consistent choice when the model is mis-specified", "Needs a density-ratio estimate; weights can become very large"),
    ("bickel", "Bickel et al.", "Learns the covariate-shift weights with a discriminative (logistic) source-versus-target classifier", "Benchmark classification tasks",
     "Avoids density estimation; the idea TrendCast implements", "Weights depend on classifier calibration and overlap between the domains"),
    ("sugi", "Sugiyama et al.", "Importance-weighted cross-validation for model selection under covariate shift", "Benchmark tasks",
     "Unbiased validation score under shift", "Needs the same density ratio; high variance when weights are extreme"),
    ("bendavid", "Ben-David et al.", "Bounds target error by source error plus a divergence between the domains", "Theory",
     "Explains why unrelated domains transfer badly", "Bound is loose and not directly computable on tabular demand"),
    ("dann", "Ganin et al. (DANN)", "Adversarial training makes neural features indistinguishable between domains", "Image benchmarks",
     "Strong image-domain results", "Neural and data-hungry; not tested on tabular retail demand here"),
    ("thom", "Thomassey", "Reviews clothing sales forecasting and proposes fuzzy, neural and data-mining models", "Real sourcing and forecasting data of a clothing supply chain",
     "Models judged by their effect on the bullwhip effect", "Pre-dates gradient-boosted tabular models; no domain adaptation"),
    ("ekam", "Ekambaram et al.", "Attention-based multi-modal encoder-decoder for new fashion products from images, attributes and external factors", "Large fashion dataset",
     "Better accuracy and interpretability than k-nearest-neighbour baselines", "Needs product images and a large history of other products"),
    ("singh", "Singh et al.", "Attribute-based demand forecasting for new fashion items with several neural and ML models", "Large-scale fashion sales data",
     "Identifies which attributes drive demand", "Attribute model only; no transfer across markets"),
    ("skend", "Skenderi et al. (VISUELLE)", "Image-based Google Trends fused with product images and metadata for new-item sales", "VISUELLE: 5,577 products sold 2016-2019",
     "Forecasts the whole horizon at once", "External signals and images are required"),
    ("muqar", "Papadopoulos et al. (MuQAR)", "Multimodal perceptron plus quasi-autoregressive network for the visual popularity of new fashion products", "Mallzee, SHIFT15m, VISUELLE and others",
     "Compared with prior work on VISUELLE", "Predicts popularity, not units sold"),
    ("cdlf", "Zhou et al. (CDLF)", "Conditional diffusion model for new-product life cycles from static descriptors and similar products", "Intel microprocessor SKU life cycles and open-model repositories",
     "More accurate point and probabilistic forecasts than classical baselines", "Not fashion-specific; heavy generative model"),
]
GAP = ("The surveyed work either applies gradient boosting with explainability to one retail market, or builds neural models for new fashion items. "
       "A gradient-boosted demand model that is moved from one retail context to a differently distributed one by a simple, inspectable adaptation step, "
       "and then checked against honest controls, is not reported.")


def rows():
    return [[w, a, d, r, l] for _, w, a, d, r, l in ROWS]
