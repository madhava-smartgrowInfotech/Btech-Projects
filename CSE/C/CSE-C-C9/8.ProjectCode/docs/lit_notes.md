# Literature notes (verified facts only - use nothing else about these works)

1. BASE (IEEE Access 2026, Kim & Sun) - in Documentary/ PDF; see REPORT_FACTS.md section 4 and the PDF text. Four-stage framework (domain-adaptive
   feature engineering, multi-model training, SHAP global/local interpretation, domain-specific validation); 165 Korean hospitals, 825 hospital-year rows 2019-2023,
   236 line items -> 11 features; target deficit (net income<0), 41.2% positive; XGBoost AUC 0.842 under hospital-level Group K-Fold, GB 0.840, RF 0.831, LR 0.776,
   MLP 0.772; temporal 2019-22 -> 2023 AUC 0.780; Altman Z'' 0.680; SHAP: material cost ratio 0.777, labor cost ratio 0.729; counterfactual subsidy analysis (57.5 pp gap);
   fixed-effects regression (28.9 pp, p<0.001); DeLong tests - ensembles not significantly different; hyperparameters at defaults; limits: SHAP is associational, compositional collinearity.
2. abid (JRFM 18(6):300, 2025, Amira Abid) - forecasts CDS-based implied default probabilities of Egypt, Morocco, Saudi Arabia during political crises; compares five ML models
   (linear, ridge, lasso, XGBoost, kernel ridge) and four DL models (RNN, LSTM, BiLSTM, GRU); linear regression performed best, RNN and GRU competitive; maps to implied ratings. (abstract only verified)
3. maurino (ICAIF 2025 workshop, Andrea Maurino, Univ. Milano-Bicocca) - effect of missing values, noise, outliers, label errors on 10 models (RF, SVM, LR ...) for credit risk using an
   open-source dataset and the Pucktrick corruption library; certain errors (outliers, missing values, duplicates) can sometimes help (up to 17% F1 gain for specific models), noise and mislabeling
   generally hurt; effect depends on feature, model, error type; future: multiclass, other datasets, fairness.
4. zhang (arXiv 2606.10333, Zhang, Xu, He, Fang, Jun 2026) - PrivacyCredit: privacy-preserving credit risk prediction with alternative data (vertical federated learning); privacy-preserving,
   model-confidential, lossless constraints; same predictive performance as plaintext combination; notes XGBoost widely used for credit risk for interpretability and performance.
5. survey1/2/3 - batch survey entries (title/year only); NOT verified; never cite for facts.
6. Classical works summarised by the base paper's related-work section: Altman Z-score (linear discriminant, five ratios) and Ohlson logit; Breiman RF; Friedman GBM; Chen&Guestrin XGBoost;
   Barboza et al. (ensembles outperform traditional statistical models for bankruptcy prediction); Zieba et al. (ensemble boosted trees with synthetic features); Mai et al. (RNN on textual
   disclosures); Moscatelli et al. (ML + financial features for corporate default forecasting); Lundberg&Lee SHAP; Lundberg et al. TreeExplainer; Ribeiro LIME; Cerneviciene&Kabasinskas
   (XAI in finance review: SHAP most widely adopted, few end-to-end frameworks); Bussmann et al. (Shapley values for SME credit risk); Gramegna&Giudici (SHAP vs LIME in credit risk);
   Grinsztajn et al. (trees beat deep learning on typical tabular data).
7. Adult dataset: Kohavi 1996 (the dataset's origin paper); UCI page. Holt-Winters: Winters 1960, Holt 2004 (reprint). Hyndman & Koehler 2006 on forecast accuracy measures.
