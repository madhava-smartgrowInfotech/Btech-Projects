"""Feature definitions shared by the training code (ml/) and the live risk engine.

Keeping one copy guarantees the sandbox computes features exactly the way the models
were trained. Nothing here touches the database or configuration.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

# ---------------------------------------------------------------------------
# M1 - behaviour model (trained on the Digital Payment Fraud Detection Benchmark)
# ---------------------------------------------------------------------------
# Only signals the sandbox can observe honestly. `merchant_risk_score` is fed from the
# payee trust score at run time; `is_international` is always 0 for domestic UPI.
M1_FEATURES = [
    "log_amount",
    "amount_deviation_from_user_mean",
    "avg_monthly_spend",
    "account_age_days",
    "txn_count_1h",
    "txn_count_24h",
    "failed_txn_count_24h",
    "geo_distance_from_last_txn",
    "merchant_risk_score",
    "is_international",
    "hour_sin",
    "hour_cos",
    "device_mobile",
    "device_desktop",
    "device_tablet",
]

M1_LABELS = {
    "log_amount": "Payment amount",
    "amount_deviation_from_user_mean": "Amount compared with your daily spending",
    "avg_monthly_spend": "Your usual monthly spending",
    "account_age_days": "Age of your account",
    "txn_count_1h": "Payments in the last hour",
    "txn_count_24h": "Payments in the last 24 hours",
    "failed_txn_count_24h": "Failed attempts in the last 24 hours",
    "geo_distance_from_last_txn": "Distance from your last payment location",
    "merchant_risk_score": "Receiver risk",
    "is_international": "International payment",
    "hour_sin": "Time of day",
    "hour_cos": "Time of day",
    "device_mobile": "Device type",
    "device_desktop": "Device type",
    "device_tablet": "Device type",
}

# Range seen in the benchmark; values outside are clipped so trees never extrapolate oddly.
ACCOUNT_AGE_RANGE = (30, 2000)


def merchant_risk_from_trust(trust: float) -> float:
    """Maps a 0-100 payee trust score onto the benchmark's merchant_risk_score scale (0-0.84)."""
    t = min(max(trust, 0.0), 100.0) / 100.0
    return round(0.05 + 0.75 * (1.0 - t) ** 1.5, 4)


def m1_row(
    *,
    amount: float,
    avg_monthly_spend: float,
    account_age_days: float,
    txn_count_1h: int,
    txn_count_24h: int,
    failed_txn_count_24h: int,
    geo_distance_km: float | None,
    merchant_risk_score: float,
    hour: float,
    device: str = "mobile",
    is_international: int = 0,
) -> dict[str, float]:
    angle = 2 * math.pi * (hour % 24) / 24
    device = device if device in ("mobile", "desktop", "tablet") else "mobile"
    return {
        "log_amount": math.log1p(max(amount, 0.0)),
        "amount_deviation_from_user_mean": amount - avg_monthly_spend / 30.0,
        "avg_monthly_spend": avg_monthly_spend,
        "account_age_days": float(min(max(account_age_days, ACCOUNT_AGE_RANGE[0]), ACCOUNT_AGE_RANGE[1])),
        "txn_count_1h": float(txn_count_1h),
        "txn_count_24h": float(txn_count_24h),
        "failed_txn_count_24h": float(failed_txn_count_24h),
        "geo_distance_from_last_txn": float("nan") if geo_distance_km is None else float(geo_distance_km),
        "merchant_risk_score": float(merchant_risk_score),
        "is_international": float(is_international),
        "hour_sin": math.sin(angle),
        "hour_cos": math.cos(angle),
        "device_mobile": float(device == "mobile"),
        "device_desktop": float(device == "desktop"),
        "device_tablet": float(device == "tablet"),
    }


def m1_frame_from_benchmark(df):
    """Builds the M1 feature table from the raw benchmark CSV columns."""
    import pandas as pd

    hours = df["transaction_time"].dt.hour + df["transaction_time"].dt.minute / 60.0
    angle = 2 * np.pi * hours / 24
    out = pd.DataFrame(
        {
            "log_amount": np.log1p(df["transaction_amount"].clip(lower=0)),
            "amount_deviation_from_user_mean": df["amount_deviation_from_user_mean"],
            "avg_monthly_spend": df["avg_monthly_spend"],
            "account_age_days": df["account_age_days"].clip(*ACCOUNT_AGE_RANGE).astype(float),
            "txn_count_1h": df["txn_count_1h"].astype(float),
            "txn_count_24h": df["txn_count_24h"].astype(float),
            "failed_txn_count_24h": df["failed_txn_count_24h"].astype(float),
            "geo_distance_from_last_txn": df["geo_distance_from_last_txn"].astype(float),
            "merchant_risk_score": df["merchant_risk_score"].astype(float),
            "is_international": df["is_international"].astype(float),
            "hour_sin": np.sin(angle),
            "hour_cos": np.cos(angle),
            "device_mobile": (df["device_type"] == "mobile").astype(float),
            "device_desktop": (df["device_type"] == "desktop").astype(float),
            "device_tablet": (df["device_type"] == "tablet").astype(float),
        }
    )
    return out[M1_FEATURES]


# ---------------------------------------------------------------------------
# F3 - payee trust score (transparent formula, shown to users with its parts)
# ---------------------------------------------------------------------------
@dataclass
class TrustInputs:
    account_age_days: float
    report_score: float  # weighted, decayed community reports
    distinct_payers_24h: int
    distinct_payers_7d: int
    new_payer_share_7d: float  # share of 7-day inbound payments that came from first-time payers
    inbound_count_90d: int
    distinct_payers_90d: int
    collect_targets_7d: int  # distinct people this payee sent collect requests to in 7 days
    is_merchant: bool


def trust_score(t: TrustInputs) -> tuple[int, list[dict]]:
    """Returns (score 0-100, component list). Start neutral at 60 and adjust for evidence."""
    parts: list[dict] = []

    def add(code: str, delta: float) -> None:
        if abs(delta) >= 0.5:
            parts.append({"code": code, "delta": round(delta)})

    score = 60.0
    age = t.account_age_days
    if age < 7:
        d = -25
    elif age < 30:
        d = -14
    elif age < 180:
        d = -4
    elif age >= 365:
        d = 10
    else:
        d = 4
    add("account_age", d)
    score += d

    d = -min(45.0, 16.0 * t.report_score)
    add("community_reports", d)
    score += d

    if t.distinct_payers_7d >= 4 and t.new_payer_share_7d >= 0.6 and not t.is_merchant:
        d = -8 - 10 * (t.new_payer_share_7d - 0.6) / 0.4 - min(6, t.distinct_payers_24h)
        add("many_new_payers", d)
        score += d

    if t.collect_targets_7d >= 3:
        d = -min(12.0, 3.0 * t.collect_targets_7d)
        add("mass_collect_requests", d)
        score += d

    if t.distinct_payers_90d >= 5 and t.report_score < 0.5 and age >= 90:
        d = min(12.0, 2.0 + t.distinct_payers_90d / 5)
        add("steady_history", d)
        score += d

    if t.is_merchant and age >= 90:
        add("registered_merchant", 6)
        score += 6

    return int(round(min(100.0, max(0.0, score)))), parts


def trust_band(score: int) -> str:
    return "trusted" if score >= 70 else "caution" if score >= 40 else "risky"


# ---------------------------------------------------------------------------
# M3 - payment risk model (the score users see)
# ---------------------------------------------------------------------------
RISK_FEATURES = [
    "behaviour_score",
    "amount_log",
    "amount_to_median",
    "amount_to_max",
    "is_new_payee",
    "payee_times_paid",
    "is_saved_contact",
    "is_night",
    "hour_share",
    "txn_count_1h",
    "txn_count_24h",
    "failed_24h",
    "payee_account_age_days",
    "payee_reports",
    "payee_distinct_payers_24h",
    "payee_new_payer_share_7d",
    "payee_collects_7d",
    "payee_is_merchant",
    "sms_scam_prob",
    "sms_recent_scam",
    "channel_qr",
    "channel_collect",
    "collect_note_score",
    "qr_flag",
    "payer_account_age_days",
]

# +1: more of this can only raise risk, -1: can only lower it, 0: learned freely.
RISK_MONOTONE = {
    "behaviour_score": 1,
    "amount_log": 0,
    "amount_to_median": 1,
    "amount_to_max": 1,
    "is_new_payee": 1,
    "payee_times_paid": -1,
    "is_saved_contact": -1,
    "is_night": 1,
    "hour_share": -1,
    "txn_count_1h": 0,
    "txn_count_24h": 0,
    "failed_24h": 1,
    "payee_account_age_days": -1,
    "payee_reports": 1,
    "payee_distinct_payers_24h": 0,
    "payee_new_payer_share_7d": 1,
    "payee_collects_7d": 1,
    "payee_is_merchant": 0,
    "sms_scam_prob": 1,
    "sms_recent_scam": 0,
    "channel_qr": 0,
    "channel_collect": 0,
    "collect_note_score": 1,
    "qr_flag": 1,
    "payer_account_age_days": 0,
}

# Population defaults used when a payer has no history yet (from UPI Transactions 2024).
POPULATION_MEDIAN_AMOUNT = 630.0
POPULATION_P90_AMOUNT = 3200.0


def is_night_hour(hour: float) -> int:
    h = int(hour) % 24
    return int(h >= 23 or h < 5)


def hour_share(past_hours: list[float], hour: float, default: float) -> float:
    """Share of past payments made within +/-1 hour of this hour (circular clock)."""
    if len(past_hours) < 5:
        return default
    arr = np.asarray(past_hours, dtype=float)
    diff = np.abs((arr - hour + 12) % 24 - 12)
    return float(np.mean(diff <= 1.0))


def risk_row(
    *,
    behaviour_score: float,
    amount: float,
    past_amounts: list[float],
    is_new_payee: bool,
    payee_times_paid: int,
    is_saved_contact: bool,
    hour: float,
    past_hours: list[float],
    hour_prior: float,
    txn_count_1h: int,
    txn_count_24h: int,
    failed_24h: int,
    payee_account_age_days: float,
    payee_reports: float,
    payee_distinct_payers_24h: int,
    payee_new_payer_share_7d: float,
    payee_collects_7d: int,
    payee_is_merchant: bool,
    sms_scam_prob: float,
    sms_recent_scam: bool,
    channel: str,
    collect_note_score: float,
    qr_flag: float,
    payer_account_age_days: float,
) -> dict[str, float]:
    if len(past_amounts) >= 3:
        median = float(np.median(past_amounts))
        biggest = float(np.max(past_amounts))
    else:
        median = POPULATION_MEDIAN_AMOUNT
        biggest = POPULATION_P90_AMOUNT
    return {
        "behaviour_score": float(behaviour_score),
        "amount_log": math.log1p(max(amount, 0.0)),
        "amount_to_median": min(200.0, amount / max(median, 1.0)),
        "amount_to_max": min(200.0, amount / max(biggest, 1.0)),
        "is_new_payee": float(is_new_payee),
        "payee_times_paid": float(min(payee_times_paid, 50)),
        "is_saved_contact": float(is_saved_contact),
        "is_night": float(is_night_hour(hour)),
        "hour_share": hour_share(past_hours, hour, hour_prior),
        "txn_count_1h": float(txn_count_1h),
        "txn_count_24h": float(txn_count_24h),
        "failed_24h": float(failed_24h),
        "payee_account_age_days": float(min(payee_account_age_days, 3650)),
        "payee_reports": float(payee_reports),
        "payee_distinct_payers_24h": float(payee_distinct_payers_24h),
        "payee_new_payer_share_7d": float(payee_new_payer_share_7d),
        "payee_collects_7d": float(payee_collects_7d),
        "payee_is_merchant": float(payee_is_merchant),
        "sms_scam_prob": float(sms_scam_prob),
        "sms_recent_scam": float(sms_recent_scam),
        "channel_qr": float(channel == "qr"),
        "channel_collect": float(channel == "collect"),
        "collect_note_score": float(collect_note_score),
        "qr_flag": float(qr_flag),
        "payer_account_age_days": float(min(payer_account_age_days, 3650)),
    }


def report_weight(reporter_account_age_days: float, report_age_days: float) -> float:
    """Reports from brand-new accounts count less, and every report fades over about a month."""
    return min(1.0, max(reporter_account_age_days, 0.0) / 30.0) * math.exp(-max(report_age_days, 0.0) / 30.0)
