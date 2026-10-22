"""Candidate classifiers for FinSight AI."""
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from xgboost import XGBClassifier

RANDOM_STATE = 42


def get_candidate_models():
    return {
        "logistic_regression": LogisticRegression(
            max_iter=2000, C=1.0, random_state=RANDOM_STATE
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=300, max_depth=None, min_samples_split=2,
            n_jobs=-1, random_state=RANDOM_STATE,
        ),
        "gradient_boosting": GradientBoostingClassifier(random_state=RANDOM_STATE),
        "xgboost": XGBClassifier(
            n_estimators=400, max_depth=6, learning_rate=0.05,
            subsample=0.9, colsample_bytree=0.9, reg_lambda=1.0,
            eval_metric="logloss", n_jobs=-1, random_state=RANDOM_STATE,
        ),
    }
