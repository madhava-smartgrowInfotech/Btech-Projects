"""Classical baseline forecasting layer: ARIMA, SARIMAX, Prophet, RF, SVR.

All baselines use an 80/20 chronological train-test split on the Close series
(RF/SVR use lag-20 features). Metrics: MAE, MSE, R2, directional accuracy.
Prophet is optional — if the package is unavailable the tier is skipped and
reported as such (documented substitution path).
"""
from __future__ import annotations
import warnings
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from . import config

warnings.filterwarnings("ignore")


def _metrics(y_true, y_pred) -> dict:
    y_true = np.asarray(y_true, float); y_pred = np.asarray(y_pred, float)
    mae = float(mean_absolute_error(y_true, y_pred))
    mse = float(mean_squared_error(y_true, y_pred))
    try:
        r2 = float(r2_score(y_true, y_pred))
    except Exception:
        r2 = 0.0
    dt = np.diff(y_true) > 0
    dp = np.diff(y_pred) > 0
    # directional accuracy vs previous ACTUAL value (standard): sign(actual_t - actual_{t-1}) == sign(pred_t - actual_{t-1})
    dp2 = (y_pred[1:] - y_true[:-1]) > 0
    da = float((dt == dp2).mean()) if len(dt) else 0.0
    return {"mae": mae, "mse": mse, "rmse": float(np.sqrt(mse)), "r2": r2, "directional_accuracy": da,
            "n_test": int(len(y_true))}


def _split(close: np.ndarray):
    n = len(close); k = int(n * config.TRAIN_SPLIT)
    return close[:k], close[k:]


def run_arima(close: np.ndarray) -> dict:
    from statsmodels.tsa.arima.model import ARIMA
    tr, te = _split(close)
    fit = ARIMA(tr, order=(5, 1, 0)).fit()
    pred = np.asarray(fit.forecast(steps=len(te)), float)
    return {"metrics": _metrics(te, pred), "pred": pred}


def run_sarimax(close: np.ndarray) -> dict:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    tr, te = _split(close)
    fit = SARIMAX(tr, order=(1, 1, 1), seasonal_order=(1, 1, 1, 5),
                  enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)
    pred = np.asarray(fit.forecast(steps=len(te)), float)
    return {"metrics": _metrics(te, pred), "pred": pred}


def run_prophet(dates, close: np.ndarray) -> dict:
    try:
        from prophet import Prophet
    except Exception as e:
        return {"metrics": None, "pred": None, "skipped": f"prophet unavailable: {e}"}
    import pandas as pd
    tr, te = _split(close)
    dtr, dte = dates[:len(tr)], dates[len(tr):]
    df = pd.DataFrame({"ds": pd.to_datetime(dtr), "y": tr})
    m = Prophet(daily_seasonality=True, weekly_seasonality=True, yearly_seasonality=False)
    m.fit(df)
    fut = pd.DataFrame({"ds": pd.to_datetime(dte)})
    pred = np.asarray(m.predict(fut)["yhat"], float)
    return {"metrics": _metrics(te, pred), "pred": pred}


def _lag_xy(close: np.ndarray, lags: int = 20):
    X, y = [], []
    for i in range(lags, len(close)):
        X.append(close[i - lags:i]); y.append(close[i])
    return np.array(X), np.array(y)


def run_rf(close: np.ndarray) -> dict:
    tr, te = _split(close)
    Xtr, ytr = _lag_xy(tr); Xte, yte = _lag_xy(np.concatenate([tr[-20:], te]))
    m = RandomForestRegressor(n_estimators=200, random_state=config.RANDOM_STATE, n_jobs=-1)
    m.fit(Xtr, ytr)
    return {"metrics": _metrics(yte, m.predict(Xte)), "pred": m.predict(Xte)}


def run_svr(close: np.ndarray) -> dict:
    from sklearn.preprocessing import StandardScaler
    tr, te = _split(close)
    Xtr, ytr = _lag_xy(tr); Xte, yte = _lag_xy(np.concatenate([tr[-20:], te]))
    sc = StandardScaler().fit(Xtr)
    m = SVR(kernel="rbf", C=10.0, epsilon=0.5)
    m.fit(sc.transform(Xtr), ytr)
    return {"metrics": _metrics(yte, m.predict(sc.transform(Xte))), "pred": m.predict(sc.transform(Xte))}


def run_all(dates, close: np.ndarray) -> dict:
    out = {}
    for name, fn in [("arima", lambda: run_arima(close)),
                     ("sarimax", lambda: run_sarimax(close)),
                     ("prophet", lambda: run_prophet(dates, close)),
                     ("random_forest", lambda: run_rf(close)),
                     ("svr", lambda: run_svr(close))]:
        try:
            out[name] = fn()
            for k in ("pred",):
                out[name].pop(k, None)
        except Exception as e:
            out[name] = {"metrics": None, "error": str(e)[:300]}
    return out
