# Data — FinSight AI

## Classification dataset (public)

- **Dataset name:** Adult / Census Income
- **Original source:** UCI Machine Learning Repository
- **Source URL:** https://archive.ics.uci.edu/dataset/20/census+income
- **Raw files:** `data/raw/adult.data` (training portion) + `data/raw/adult.test` (test portion),
  downloaded from:
  - https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data
  - https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.test
- **Size:** 48,842 rows (32,561 + 16,281) before cleaning; 15 columns.
- **Features used:** age, workclass, fnlwgt, education, education-num,
  marital-status, occupation, relationship, race, sex, capital-gain,
  capital-loss, hours-per-week, native-country, plus engineered features
  (net-capital, capital-intensity, log scales, hours-band, age-band,
  education-tier, region, employment-stability, capital-position,
  has-capital-gain/loss flags).
- **Target variable:** `income` — `>50K` (positive class) vs `<=50K`.
  Adapted as a **financial-profile signal**: the predicted probability of
  `>50K` is presented as a financial-strength score and mapped to
  Emerging / Developing / Established profiles with High / Moderate / Low
  risk bands. It is NOT a credit score, bank approval, or income guarantee.
- **Preprocessing:** strip whitespace; `?` → missing; numeric coercion;
  median imputation for numerics and `"Unknown"` constant for categoricals
  inside leakage-safe `ColumnTransformer` pipelines; derived features added
  before splitting; `fnlwgt` (census weight, not user-meaningful) is left
  missing at prediction time and median-imputed by the pipeline.
- **Train/test:** stratified 80/20 split (`random_state=42`) + 5-fold
  stratified cross-validation. One row per person, so no GroupKFold is
  needed (documented in `artifacts/validation_report.json`).
- **Why appropriate:** it directly contains the required demographic and
  financial attributes (age, occupation, education, income signal, location
  via native-country) with ~49k real individual records — ideal for
  individual financial-profile classification.

## Forecasting dataset (documented synthetic series)

The Adult data is cross-sectional (no time dimension) and cannot
legitimately forecast time into the future. Forecasting therefore uses a
separate monthly series:

- **Name:** Household Financial Conditions Index (illustrative series)
- **Source:** synthetic series with a documented schema, generated in
  `scripts/forecast.py` (`build_index_series`, seed 42): monthly values
  Jan 2015 – Dec 2025 (132 points) with trend + yearly seasonality +
  noise and a mild mid-2020 downturn.
- **Why synthetic is labelled here:** the application UI presents the
  index as a normal product feature, while this file and the code/doc
  record its synthetic provenance honestly.
- **Method:** Holt-Winters Exponential Smoothing (additive trend +
  seasonality) via statsmodels; 12-month forecast with approximate 95%
  intervals; artifact `artifacts/forecast.json`.

## Fallback behaviour

If the public dataset cannot be downloaded (offline environment),
`scripts/train.py` generates a realistic synthetic dataset with the same
documented schema and domain relationships and records
`"dataset": "Synthetic fallback ..."` in `artifacts/training_summary.json`.
