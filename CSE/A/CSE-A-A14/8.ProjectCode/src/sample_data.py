"""
sample_data.py
--------------
Generates a small synthetic telecom customer churn dataset so the
application can be demonstrated even when the user has not uploaded a
CSV file yet. The generated data mimics the structure of the widely
used "Telco Customer Churn" dataset (IBM sample dataset), with the
same column names, so it is compatible with the rest of the pipeline.
"""

import numpy as np
import pandas as pd


def generate_sample_churn_data(n_customers: int = 1000, random_state: int = 42) -> pd.DataFrame:
    """Create a synthetic telecom churn dataset with realistic-looking
    relationships between features and churn (so that the trained
    models produce meaningful, explainable results rather than noise).
    """
    rng = np.random.default_rng(random_state)

    customer_id = [f"CUST-{1000 + i}" for i in range(n_customers)]
    gender = rng.choice(["Male", "Female"], n_customers)
    senior_citizen = rng.choice([0, 1], n_customers, p=[0.84, 0.16])
    partner = rng.choice(["Yes", "No"], n_customers, p=[0.48, 0.52])
    dependents = rng.choice(["Yes", "No"], n_customers, p=[0.3, 0.7])
    tenure = rng.integers(0, 73, n_customers)

    phone_service = rng.choice(["Yes", "No"], n_customers, p=[0.9, 0.1])
    multiple_lines = np.where(
        phone_service == "No", "No phone service",
        rng.choice(["Yes", "No"], n_customers)
    )
    internet_service = rng.choice(["DSL", "Fiber optic", "No"], n_customers, p=[0.35, 0.44, 0.21])

    def dependent_service(has_internet, p_yes=0.4):
        out = []
        for has_net in has_internet:
            if has_net == "No":
                out.append("No internet service")
            else:
                out.append(rng.choice(["Yes", "No"], p=[p_yes, 1 - p_yes]))
        return np.array(out)

    online_security = dependent_service(internet_service, 0.35)
    online_backup = dependent_service(internet_service, 0.38)
    device_protection = dependent_service(internet_service, 0.38)
    tech_support = dependent_service(internet_service, 0.35)
    streaming_tv = dependent_service(internet_service, 0.45)
    streaming_movies = dependent_service(internet_service, 0.45)

    contract = rng.choice(
        ["Month-to-month", "One year", "Two year"], n_customers, p=[0.55, 0.24, 0.21]
    )
    paperless_billing = rng.choice(["Yes", "No"], n_customers, p=[0.59, 0.41])
    payment_method = rng.choice(
        ["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"],
        n_customers, p=[0.34, 0.23, 0.22, 0.21]
    )

    base_charge = np.where(internet_service == "Fiber optic", 70, np.where(internet_service == "DSL", 45, 20))
    extras = (
        (online_security == "Yes").astype(int) + (online_backup == "Yes").astype(int)
        + (device_protection == "Yes").astype(int) + (tech_support == "Yes").astype(int)
        + (streaming_tv == "Yes").astype(int) + (streaming_movies == "Yes").astype(int)
    )
    monthly_charges = np.round(base_charge + extras * 4.5 + rng.normal(0, 5, n_customers), 2)
    monthly_charges = np.clip(monthly_charges, 18.0, 120.0)
    total_charges = np.round(monthly_charges * np.maximum(tenure, 1) + rng.normal(0, 20, n_customers), 2)
    total_charges = np.clip(total_charges, 0, None)

    # ---- Construct a latent churn "risk score" driving the label ----
    # Intercept is tuned negative so the overall churn rate lands near the
    # ~26-27% typically seen in the public Telco churn dataset.
    risk = np.full(n_customers, -2.1)
    risk += (contract == "Month-to-month") * 1.3
    risk += (contract == "One year") * 0.25
    risk += (payment_method == "Electronic check") * 0.6
    risk += (tech_support == "No") * 0.45
    risk += (online_security == "No") * 0.35
    risk += (internet_service == "Fiber optic") * 0.35
    risk += (senior_citizen == 1) * 0.3
    risk += (partner == "No") * 0.15
    risk -= (tenure / 72.0) * 1.6
    risk += ((monthly_charges - 60) / 60.0) * 0.5
    risk += rng.normal(0, 0.55, n_customers)

    churn_prob = 1 / (1 + np.exp(-risk))
    churn = (rng.random(n_customers) < churn_prob).astype(int)
    churn_labels = np.where(churn == 1, "Yes", "No")

    df = pd.DataFrame({
        "customerID": customer_id,
        "gender": gender,
        "SeniorCitizen": senior_citizen,
        "Partner": partner,
        "Dependents": dependents,
        "tenure": tenure,
        "PhoneService": phone_service,
        "MultipleLines": multiple_lines,
        "InternetService": internet_service,
        "OnlineSecurity": online_security,
        "OnlineBackup": online_backup,
        "DeviceProtection": device_protection,
        "TechSupport": tech_support,
        "StreamingTV": streaming_tv,
        "StreamingMovies": streaming_movies,
        "Contract": contract,
        "PaperlessBilling": paperless_billing,
        "PaymentMethod": payment_method,
        "MonthlyCharges": monthly_charges,
        "TotalCharges": total_charges,
        "Churn": churn_labels,
    })
    return df


if __name__ == "__main__":
    generate_sample_churn_data().to_csv("data/customer_churn.csv", index=False)
    print("Sample dataset written to data/customer_churn.csv")
