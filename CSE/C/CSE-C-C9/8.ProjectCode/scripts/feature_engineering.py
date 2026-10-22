"""FinSight AI — feature engineering layer.

Dataset: UCI Adult / Census Income (see data/README.md).
Adapts raw demographic + financial fields into interpretable features.
"""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer

RANDOM_STATE = 42

COLUMN_NAMES = [
    "age", "workclass", "fnlwgt", "education", "education-num",
    "marital-status", "occupation", "relationship", "race", "sex",
    "capital-gain", "capital-loss", "hours-per-week", "native-country", "income",
]

TARGET_COL = "income"
POSITIVE_LABEL = ">50K"

# Raw fields expected from a user / row (fnlwgt is optional; defaults to median)
USER_FIELDS = [
    "age", "workclass", "education", "marital-status", "occupation",
    "relationship", "race", "sex", "capital-gain", "capital-loss",
    "hours-per-week", "native-country",
]

REGION_MAP = {
    "United-States": "North America",
    "Canada": "North America",
    "Mexico": "Latin America",
    "Puerto-Rico": "Latin America",
    "Cuba": "Latin America",
    "Jamaica": "Latin America",
    "Haiti": "Latin America",
    "Dominican-Republic": "Latin America",
    "Guatemala": "Latin America",
    "Nicaragua": "Latin America",
    "El-Salvador": "Latin America",
    "Honduras": "Latin America",
    "Colombia": "Latin America",
    "Ecuador": "Latin America",
    "Peru": "Latin America",
    "Trinadad&Tobago": "Latin America",
    "England": "Europe",
    "Germany": "Europe",
    "Italy": "Europe",
    "Poland": "Europe",
    "Portugal": "Europe",
    "France": "Europe",
    "Ireland": "Europe",
    "Scotland": "Europe",
    "Greece": "Europe",
    "Yugoslavia": "Europe",
    "Hungary": "Europe",
    "Holand-Netherlands": "Europe",
    "Russia": "Europe",
    "Ukraine": "Europe",
    "Lithuania": "Europe",
    "Croatia": "Europe",
    "Czech": "Europe",
    "India": "Asia",
    "China": "Asia",
    "Japan": "Asia",
    "Philippines": "Asia",
    "Vietnam": "Asia",
    "Laos": "Asia",
    "Thailand": "Asia",
    "Taiwan": "Asia",
    "Hong-Kong": "Asia",
    "Cambodia": "Asia",
    "Iran": "Middle East",
    "Iraq": "Middle East",
    "Turkey": "Middle East",
    "Israel": "Middle East",
    "Lebanon": "Middle East",
    "Jordan": "Middle East",
    "Saudi-Arabia": "Middle East",
    "Yemen": "Middle East",
    "Korea": "Asia",
    "South": "Other",
    "Outlying-US(Guam-USVI-etc)": "North America",
}


def _clean_token(v):
    if not isinstance(v, str):
        return v
    v = v.strip()
    if v == "?":
        return np.nan
    return v


def clean_frame(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].map(_clean_token)
    for c in ["age", "fnlwgt", "education-num", "capital-gain", "capital-loss", "hours-per-week"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    if TARGET_COL in df.columns:
        df[TARGET_COL] = df[TARGET_COL].astype(str).str.strip().str.replace(".", "", regex=False)
    return df


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add interpretable derived financial-health features.

    Every derived column is computable from available raw fields only.
    """
    df = df.copy()
    age = pd.to_numeric(df.get("age"), errors="coerce")
    gain = pd.to_numeric(df.get("capital-gain"), errors="coerce").fillna(0)
    loss = pd.to_numeric(df.get("capital-loss"), errors="coerce").fillna(0)
    hours = pd.to_numeric(df.get("hours-per-week"), errors="coerce")
    edu_num = pd.to_numeric(df.get("education-num"), errors="coerce")

    df["net-capital"] = gain - loss
    df["capital-intensity"] = (gain + loss).clip(lower=0)

    # Capital gains/losses are highly skewed; log-scale them for linear models
    # (tree models are unaffected by monotonic transforms of single columns).
    df["log-capital-gain"] = np.log1p(gain.clip(lower=0))
    df["log-capital-loss"] = np.log1p(loss.clip(lower=0))

    # Earnings-effort proxy: hours worked per week, banded.
    df["hours-band"] = pd.cut(
        hours,
        bins=[-0.1, 29, 40, 60, 200],
        labels=["Part-time", "Full-time", "Extended", "Very-long"],
    ).astype(object)

    # Has any investment gain / loss flags (interpretable financial indicators).
    df["has-capital-gain"] = (gain > 0).astype(int).astype(str)
    df["has-capital-loss"] = (loss > 0).astype(int).astype(str)

    # Age bands.
    df["age-band"] = pd.cut(
        age,
        bins=[-0.1, 25, 35, 50, 65, 200],
        labels=["18-25", "26-35", "36-50", "51-65", "65+"],
    ).astype(object)

    # Education grouped into 3 tiers.
    def edu_tier(n):
        try:
            n = float(n)
        except (TypeError, ValueError):
            return np.nan
        if n <= 9:
            return "Secondary-or-below"
        if n <= 12:
            return "Higher-secondary"
        return "Tertiary"
    df["education-tier"] = edu_num.map(edu_tier)

    # Regional economic category derived from native-country.
    if "native-country" in df.columns:
        df["region"] = df["native-country"].map(REGION_MAP).fillna("Other")
    else:
        df["region"] = "Other"

    # Employment stability category derived from workclass + hours.
    def stability(row):
        wc = str(row.get("workclass", ""))
        h = row.get("hours-per-week", np.nan)
        try:
            h = float(h)
        except (TypeError, ValueError):
            h = np.nan
        if wc in ("Federal-gov", "State-gov", "Local-gov"):
            return "Stable-public"
        if wc == "Self-emp-inc":
            return "Business-owner"
        if wc in ("Self-emp-not-inc",):
            return "Self-employed"
        if wc == "Private":
            if pd.notna(h) and h >= 35:
                return "Stable-private"
            return "Variable-private"
        if wc in ("Without-pay", "Never-worked"):
            return "Not-employed"
        return "Other"
    df["employment-stability"] = df.apply(stability, axis=1)

    # Net-capital position category.
    df["capital-position"] = pd.cut(
        df["net-capital"],
        bins=[-10**9, -1, 0, 4999, 10**9],
        labels=["Net-loss", "No-capital", "Moderate-gain", "High-gain"],
    ).astype(object)

    return df


NUMERIC_FEATURES = [
    "age", "fnlwgt", "education-num", "capital-gain", "capital-loss",
    "hours-per-week", "net-capital", "capital-intensity",
    "log-capital-gain", "log-capital-loss",
]

CATEGORICAL_FEATURES = [
    "workclass", "education", "marital-status", "occupation",
    "relationship", "race", "sex", "native-country",
    "hours-band", "has-capital-gain", "has-capital-loss",
    "age-band", "education-tier", "region",
    "employment-stability", "capital-position",
]


def _onehot():
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:  # older sklearn
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def build_preprocessor(scale_numeric: bool) -> ColumnTransformer:
    """Build a leakage-safe ColumnTransformer.

    scale_numeric=True for the Logistic Regression pipeline;
    tree pipelines use scale_numeric=False.
    """
    if scale_numeric:
        num_pipe = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ])
    else:
        num_pipe = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
        ])
    cat_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
        ("onehot", _onehot()),
    ])
    return ColumnTransformer([
        ("num", num_pipe, NUMERIC_FEATURES),
        ("cat", cat_pipe, CATEGORICAL_FEATURES),
    ])


def get_output_feature_names(preprocessor: ColumnTransformer) -> list:
    """Return output feature names after fitting."""
    names = []
    for name, trans, cols in preprocessor.transformers_:
        if name == "num":
            names.extend(list(cols))
        elif name == "cat":
            ohe = trans.named_steps["onehot"]
            try:
                fn = ohe.get_feature_names_out(cols)
            except Exception:
                fn = [f"{c}_{i}" for c in cols for i in range(2)]
            names.extend(list(fn))
    return names


HUMAN_LABELS = {
    "age": "Age",
    "education-num": "Years of education",
    "capital-gain": "Investment gains",
    "capital-loss": "Investment losses",
    "hours-per-week": "Hours worked per week",
    "net-capital": "Net investment position (gains minus losses)",
    "capital-intensity": "Overall investment activity",
    "log-capital-gain": "Investment gains (log scale)",
    "log-capital-loss": "Investment losses (log scale)",
    "fnlwgt": "Census sampling weight",
}


def human_label(feature: str) -> str:
    if feature in HUMAN_LABELS:
        return HUMAN_LABELS[feature]
    if "__" in feature:
        feature = feature.split("__", 1)[1]
    # One-hot names look like "occupation_Exec-managerial"
    if "_" in feature:
        col, _, val = feature.partition("_")
        pretty_col = col.replace("-", " ")
        return f"{pretty_col} = {val}"
    return feature.replace("-", " ")
