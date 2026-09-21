"""
Synthetic dataset generator mimicking Stone fintech dataset (145M -> balanced 39k).
Generates realistic credit card transaction features with severe imbalance then balances.
"""
import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

def generate_synthetic_transactions(n_fraud=19500, n_legit=80000, n_features=30, balanced_output=False):
    """
    Generate synthetic transactions.
    Default mirrors paper: raw imbalanced then manual undersampling to 39k balanced.
    For demo we directly generate balanced-ish dataset to keep training fast.
    """
    def gen_legit(n):
        data = {}
        data['Amount'] = np.abs(RNG.normal(80, 60, n))  # mean 80
        data['Time'] = RNG.integers(0, 86400*90, n)  # 3 months seconds
        data['Merchant_Category'] = RNG.choice(['Grocery','Fuel','Restaurant','Travel','Electronics','Health','Online'], n, p=[0.25,0.15,0.2,0.08,0.1,0.07,0.15])
        data['Transaction_Type'] = RNG.choice(['Chip','Contactless','Online','Swipe'], n, p=[0.4,0.3,0.2,0.1])
        data['Card_Present'] = RNG.choice([0,1], n, p=[0.2,0.8])
        data['Country_Match'] = RNG.choice([0,1], n, p=[0.05,0.95])
        # PCA-like anonymized features V1-V22
        for i in range(1, 23):
            data[f'V{i}'] = RNG.normal(0, 1, n)
        # Slight structure: amount higher variance for legit
        data['V1'] += 0.1 * (data['Amount']/100)
        df = pd.DataFrame(data)
        df['Class'] = 0
        return df

    def gen_fraud(n):
        data = {}
        data['Amount'] = np.abs(RNG.normal(350, 250, n))  # larger amounts
        data['Time'] = RNG.integers(0, 86400*90, n)
        # fraudulent patterns: more online, less country match
        data['Merchant_Category'] = RNG.choice(['Grocery','Fuel','Restaurant','Travel','Electronics','Health','Online'], n, p=[0.05,0.05,0.1,0.15,0.25,0.05,0.35])
        data['Transaction_Type'] = RNG.choice(['Chip','Contactless','Online','Swipe'], n, p=[0.1,0.15,0.6,0.15])
        data['Card_Present'] = RNG.choice([0,1], n, p=[0.7,0.3])
        data['Country_Match'] = RNG.choice([0,1], n, p=[0.4,0.6])
        for i in range(1, 23):
            data[f'V{i}'] = RNG.normal(0, 1, n)
        # fraud shifts
        data['V3'] += RNG.normal(1.5, 0.8, n)
        data['V7'] += RNG.normal(-1.2, 0.9, n)
        data['V10'] += RNG.normal(1.0, 0.7, n)
        data['V14'] += RNG.normal(-0.8, 0.6, n)
        data['V17'] += RNG.normal(1.3, 0.5, n)
        df = pd.DataFrame(data)
        df['Class'] = 1
        return df

    df_legit = gen_legit(n_legit)
    df_fraud = gen_fraud(n_fraud)
    df = pd.concat([df_legit, df_fraud], ignore_index=True)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    return df

def create_balanced_39k():
    """Reproduce paper's manual undersampling: 39k with 50-50 split"""
    df = generate_synthetic_transactions(n_fraud=19500, n_legit=19500, balanced_output=True)
    return df

def save_default_csv(path="data/creditcard_synthetic.csv"):
    df = create_balanced_39k()
    df.to_csv(path, index=False)
    return path, df

if __name__ == "__main__":
    import pathlib
    p = pathlib.Path(__file__).parent.parent / "data" / "creditcard_synthetic.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    _, df = save_default_csv(str(p))
    print(f"Generated {len(df)} rows -> {p}")
    print(df['Class'].value_counts())
