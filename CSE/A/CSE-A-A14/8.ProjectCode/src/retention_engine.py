"""
retention_engine.py
----------------------
A fully local, rule-based retention recommendation engine. No external
AI/LLM API is used -- recommendations come from simple, explainable
IF/THEN rules over the customer's attributes and churn risk, matching
the project's "no external AI service" requirement.

Every recommendation is phrased as a *suggestion*, never a guarantee.
"""

from __future__ import annotations
import pandas as pd


def _get(row, col, default=None):
    """Safe getter that tolerates missing columns across different
    uploaded datasets."""
    try:
        val = row[col]
        return val if pd.notna(val) else default
    except (KeyError, TypeError):
        return default


def generate_recommendations(row: pd.Series, churn_probability: float, risk_category: str) -> list:
    """Return a list of (reason, suggestion) tuples for a single
    customer, generated from simple explainable business rules.
    """
    recs = []
    high_risk = churn_probability >= 60  # High or Critical band by default thresholds

    contract = str(_get(row, "Contract", "")).lower()
    tech_support = str(_get(row, "TechSupport", "")).lower()
    online_security = str(_get(row, "OnlineSecurity", "")).lower()
    payment_method = str(_get(row, "PaymentMethod", "")).lower()
    monthly_charges = _get(row, "MonthlyCharges")
    tenure = _get(row, "tenure")
    internet_service = str(_get(row, "InternetService", "")).lower()
    streaming_tv = str(_get(row, "StreamingTV", "")).lower()
    streaming_movies = str(_get(row, "StreamingMovies", "")).lower()
    paperless = str(_get(row, "PaperlessBilling", "")).lower()

    if high_risk and "month-to-month" in contract:
        recs.append((
            "High churn risk on a month-to-month contract",
            "Consider offering a suitable longer-term contract option (e.g. one-year plan with an incentive)."
        ))

    if high_risk and tech_support == "no":
        recs.append((
            "High churn risk with no technical support add-on",
            "Consider proactive technical support outreach or a limited-time free trial of tech support."
        ))

    if high_risk and online_security == "no":
        recs.append((
            "High churn risk with no online security add-on",
            "Consider highlighting the online security add-on as part of a retention conversation."
        ))

    if monthly_charges is not None and monthly_charges >= 80 and high_risk:
        recs.append((
            "High monthly charges combined with high churn risk",
            "Review whether the customer's current plan matches their usage, and present available lower-cost alternatives."
        ))

    if payment_method == "electronic check" and high_risk:
        recs.append((
            "Electronic check payment method with high churn risk",
            "Review the customer's payment experience and consider offering a smoother automatic payment option."
        ))

    if tenure is not None and tenure <= 6 and high_risk:
        recs.append((
            "Very new customer (tenure <= 6 months) at high risk",
            "Consider an early-lifecycle onboarding check-in to address any early friction."
        ))

    if internet_service == "fiber optic" and high_risk:
        recs.append((
            "Fiber optic customer at elevated churn risk",
            "Consider a service-quality/satisfaction check-in, since fiber customers in this segment show elevated risk."
        ))

    if streaming_tv == "no" and streaming_movies == "no" and high_risk and internet_service != "no":
        recs.append((
            "Low engagement with entertainment add-ons",
            "Consider a promotional trial of streaming add-ons to increase engagement and perceived value."
        ))

    if paperless == "yes" and high_risk and payment_method == "electronic check":
        recs.append((
            "Paperless billing with a friction-prone payment method",
            "Consider a billing-experience review; combined with electronic check this pattern often co-occurs with higher churn."
        ))

    if risk_category == "Critical Risk":
        recs.append((
            "Overall churn probability is in the Critical band",
            "Consider prioritizing this customer for a direct retention conversation with a case-specific offer."
        ))

    if not recs:
        if churn_probability < 30:
            recs.append((
                "Low churn risk",
                "No urgent retention action suggested; continue standard engagement and periodic satisfaction checks."
            ))
        else:
            recs.append((
                "Moderate churn risk without a single dominant risk factor",
                "Consider a general satisfaction check-in and monitor the account for changes in usage or complaints."
            ))

    return recs


def recommendations_dataframe(risk_table: pd.DataFrame, raw_df: pd.DataFrame, id_col: str) -> pd.DataFrame:
    """Build a flattened dataframe of recommendations for every customer
    in risk_table, joined back to their raw attributes."""
    rows = []
    merged = risk_table.merge(
        raw_df, left_on="customerID", right_on=id_col, how="left", suffixes=("", "_raw")
    ) if id_col else risk_table

    for _, r in merged.iterrows():
        recs = generate_recommendations(r, r["churn_probability"], r["risk_category"])
        for reason, suggestion in recs:
            rows.append({
                "customerID": r["customerID"],
                "churn_probability": r["churn_probability"],
                "risk_category": r["risk_category"],
                "reason": reason,
                "suggested_action": suggestion,
            })
    return pd.DataFrame(rows)
