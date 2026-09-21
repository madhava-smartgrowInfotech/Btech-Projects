"""
Preprocessing pipeline replicating paper Sec III-A:
- One-Hot Encoding for categorical
- Z-Score normalization for numerical (Gaussian for GRBM)
- Correlation filtering
- CatBoost-like feature importance (fallback to RandomForest if catboost not available)
- Balancing: SMOTE, Tomek, Manual Undersampling
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

try:
    from catboost import CatBoostClassifier
    HAS_CATBOOST = True
except:
    HAS_CATBOOST = False

try:
    from imblearn.over_sampling import SMOTE
    from imblearn.under_sampling import TomekLinks, RandomUnderSampler
    HAS_IMBLEARN = True
except:
    HAS_IMBLEARN = False

NUMERICAL_COLS = ['Amount','Time'] + [f'V{i}' for i in range(1,23)]
CATEGORICAL_COLS = ['Merchant_Category','Transaction_Type']
BINARY_COLS = ['Card_Present','Country_Match']

def zscore_normalize(df, cols):
    scaler = StandardScaler()
    df[cols] = scaler.fit_transform(df[cols])
    return df, scaler

def one_hot_encode(df):
    return pd.get_dummies(df, columns=CATEGORICAL_COLS, drop_first=False, dtype=float)

def correlation_filter(df, threshold=0.95):
    corr = df.corr(numeric_only=True).abs()
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    to_drop = [column for column in upper.columns if any(upper[column] > threshold)]
    return df.drop(columns=to_drop), to_drop

def feature_importance_filter(df, y, top_k=20):
    X = df.drop(columns=['Class']) if 'Class' in df.columns else df
    y_series = y
    if HAS_CATBOOST:
        model = CatBoostClassifier(iterations=200, depth=6, verbose=False, random_seed=42, loss_function='Logloss')
        model.fit(X, y_series)
        importances = model.get_feature_importance()
        feat_imp = dict(zip(X.columns, importances))
    else:
        rf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
        rf.fit(X, y_series)
        feat_imp = dict(zip(X.columns, rf.feature_importances_))
    sorted_feats = sorted(feat_imp.items(), key=lambda x: x[1], reverse=True)
    keep = [f for f,_ in sorted_feats[:top_k]]
    if 'Class' in df.columns:
        keep_cols = keep + ['Class']
        # but keep may not include all; ensure we keep top_k features
        filtered = df[keep_cols] if all(c in df.columns for c in keep_cols) else df[keep + ['Class']]
        # fallback if mismatch
        available_keep = [c for c in keep if c in df.columns]
        filtered = df[available_keep + ['Class']]
    else:
        filtered = df[[c for c in keep if c in df.columns]]
    return filtered, dict(sorted_feats)

def balancing_manual_undersampling(df):
    fraud = df[df['Class']==1]
    legit = df[df['Class']==0]
    n = min(len(fraud), len(legit))
    legit_sample = legit.sample(n=n, random_state=42)
    balanced = pd.concat([fraud, legit_sample]).sample(frac=1, random_state=42)
    return balanced

def balancing_smote(df):
    if not HAS_IMBLEARN:
        return balancing_manual_undersampling(df)
    X = df.drop(columns=['Class'])
    y = df['Class']
    try:
        sm = SMOTE(random_state=42)
        X_res, y_res = sm.fit_resample(X, y)
        df_res = pd.DataFrame(X_res, columns=X.columns)
        df_res['Class'] = y_res
        return df_res
    except:
        return balancing_manual_undersampling(df)

def balancing_tomek(df):
    if not HAS_IMBLEARN:
        return balancing_manual_undersampling(df)
    try:
        tl = TomekLinks()
        X = df.drop(columns=['Class'])
        y = df['Class']
        X_res, y_res = tl.fit_resample(X, y)
        df_res = pd.DataFrame(X_res, columns=X.columns)
        df_res['Class'] = y_res
        # Tomek may produce tiny set -> fallback to manual
        if len(df_res) < 1000:
            return balancing_manual_undersampling(df)
        return df_res
    except:
        return balancing_manual_undersampling(df)

def full_pipeline(df, method='manual', top_k=22, corr_threshold=0.95):
    """
    Apply full pipeline and return X_train, X_test, y_train, y_test, scaler, feature_importance, dropped_cols
    """
    # One-hot
    df_enc = one_hot_encode(df.copy())
    # Z-score for numeric (after one-hot numeric still there)
    numeric_after = [c for c in NUMERICAL_COLS if c in df_enc.columns]
    # also include binary? keep as is but scaler handles
    df_enc, scaler = zscore_normalize(df_enc, numeric_after)
    # Correlation filter (exclude Class)
    feature_cols = [c for c in df_enc.columns if c != 'Class']
    df_features = df_enc[feature_cols]
    df_filtered, dropped = correlation_filter(df_features, threshold=corr_threshold)
    df_filtered['Class'] = df_enc['Class'].values

    # Balancing BEFORE split? Paper balances then splits 80-20
    if method == 'smote':
        df_balanced = balancing_smote(df_filtered)
    elif method == 'tomek':
        df_balanced = balancing_tomek(df_filtered)
    elif method == 'manual':
        df_balanced = balancing_manual_undersampling(df_filtered)
    else:
        df_balanced = df_filtered

    # Feature importance filtering
    y = df_balanced['Class']
    df_final, feat_imp = feature_importance_filter(df_balanced, y, top_k=top_k)

    X = df_final.drop(columns=['Class']).astype(float)
    y = df_final['Class'].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    return {
        'X_train': X_train, 'X_test': X_test, 'y_train': y_train, 'y_test': y_test,
        'scaler': scaler, 'feature_importance': feat_imp, 'dropped_corr': dropped,
        'columns': list(X.columns), 'df_processed': df_final
    }

if __name__ == "__main__":
    from synthetic_data import generate_synthetic_transactions
    df = generate_synthetic_transactions(n_fraud=5000, n_legit=5000)
    res = full_pipeline(df, method='manual', top_k=18)
    print("Columns:", res['columns'])
    print("Train:", res['X_train'].shape, "Test:", res['X_test'].shape)
    print(list(res['feature_importance'].items())[:5])
