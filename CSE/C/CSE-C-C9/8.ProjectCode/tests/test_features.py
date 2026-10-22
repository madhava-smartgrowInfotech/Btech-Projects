import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from feature_engineering import clean_frame, add_derived_features, build_preprocessor


def test_derived_features_computable():
    df = pd.DataFrame([{
        "age": 40, "workclass": "Private", "fnlwgt": 200000,
        "education": "Bachelors", "education-num": 13,
        "marital-status": "Married-civ-spouse", "occupation": "Exec-managerial",
        "relationship": "Husband", "race": "White", "sex": "Male",
        "capital-gain": 5000, "capital-loss": 0, "hours-per-week": 45,
        "native-country": "United-States"}])
    out = add_derived_features(clean_frame(df))
    assert out.loc[0, "net-capital"] == 5000
    assert out.loc[0, "region"] == "North America"
    assert out.loc[0, "education-tier"] == "Tertiary"
    assert out.loc[0, "age-band"] == "36-50"
    assert out.loc[0, "employment-stability"] == "Stable-private"


def test_missing_values_handled_by_pipeline():
    df = pd.DataFrame([
        {"age": None, "workclass": "?", "fnlwgt": 200000, "education": "Bachelors",
         "education-num": 13, "marital-status": "?", "occupation": "?",
         "relationship": "Husband", "race": "White", "sex": "Male",
         "capital-gain": 0, "capital-loss": 0, "hours-per-week": 40,
         "native-country": "?"},
        {"age": 30, "workclass": "Private", "fnlwgt": 180000, "education": "HS-grad",
         "education-num": 9, "marital-status": "Never-married", "occupation": "Sales",
         "relationship": "Not-in-family", "race": "Black", "sex": "Female",
         "capital-gain": 0, "capital-loss": 0, "hours-per-week": 35,
         "native-country": "United-States"},
    ])
    df = add_derived_features(clean_frame(df))
    pre = build_preprocessor(scale_numeric=True)
    Xt = pre.fit_transform(df)
    assert Xt.shape[0] == 2
    assert pd.notna(Xt).all()
