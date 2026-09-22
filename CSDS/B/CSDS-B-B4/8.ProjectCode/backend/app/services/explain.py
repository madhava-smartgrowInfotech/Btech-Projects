"""F7 - turns SHAP contributions into plain-language reasons (English, Hindi, Telugu).

A reason is only shown when its sentence is actually true for this payment (for example
"8 times more than usual" needs a ratio of at least 2), so explanations never overstate.
"""
from __future__ import annotations

from typing import Any

from app.i18n.messages import reason_texts

M1_REASON = {
    "txn_count_24h": "BEHAVIOUR_VELOCITY",
    "txn_count_1h": "BEHAVIOUR_VELOCITY",
    "failed_txn_count_24h": "BEHAVIOUR_FAILED",
    "merchant_risk_score": "BEHAVIOUR_RECEIVER",
    "log_amount": "BEHAVIOUR_AMOUNT",
    "amount_deviation_from_user_mean": "BEHAVIOUR_AMOUNT",
    "avg_monthly_spend": "BEHAVIOUR_AMOUNT",
}


def _fmt_ratio(x: float) -> str:
    return f"{x:.0f}" if x >= 10 else f"{x:.1f}".rstrip("0").rstrip(".")


def _risk_reason(feature: str, f: dict[str, float], ctx: dict[str, Any]) -> tuple[str, dict] | None:
    payee = ctx["payee_name"]
    if feature == "is_new_payee" and f[feature] >= 1:
        return "NEW_PAYEE", {"payee": payee}
    if feature == "is_saved_contact" and f[feature] < 1 and f["is_new_payee"] < 1:
        return "NOT_SAVED", {"payee": payee}
    if feature == "amount_to_median" and f[feature] >= 2:
        if ctx["has_history"]:
            return "AMOUNT_UNUSUAL", {"ratio": _fmt_ratio(f[feature])}
        if ctx["amount"] >= 5000:
            return "AMOUNT_LARGE", {"amount_value": ctx["amount"]}
        return None
    if feature == "amount_to_max" and f[feature] > 1 and ctx["has_history"]:
        return "AMOUNT_HIGHEST", {}
    if feature == "amount_log" and ctx["amount"] >= 5000:
        return "AMOUNT_LARGE", {"amount_value": ctx["amount"]}
    if feature == "is_night" and f[feature] >= 1:
        return "NIGHT", {"time": ctx["local_time"]}
    if feature == "hour_share" and f[feature] < 0.1 and ctx["has_history"]:
        return "UNUSUAL_TIME", {}
    if feature == "txn_count_1h" and f[feature] >= 2:
        return "RAPID_PAYMENTS", {"n": int(f[feature])}
    if feature == "txn_count_24h" and f[feature] >= 4:
        return "MANY_PAYMENTS", {"n": int(f[feature])}
    if feature == "failed_24h" and f[feature] >= 1:
        return "FAILED_ATTEMPTS", {"n": int(f[feature])}
    if feature == "payee_account_age_days" and f[feature] < 90:
        return "NEW_ACCOUNT", {"payee": payee, "days": max(1, int(f[feature]))}
    if feature == "payee_reports" and ctx["report_count"] >= 1:
        return "REPORTED", {"n": ctx["report_count"]}
    if feature in ("payee_distinct_payers_24h", "payee_new_payer_share_7d") and f["payee_new_payer_share_7d"] >= 0.5 and f["payee_distinct_payers_24h"] >= 2:
        return "MANY_NEW_PAYERS", {}
    if feature == "payee_collects_7d" and f[feature] >= 2:
        return "MASS_COLLECT", {"n": int(f[feature])}
    if feature == "sms_scam_prob" and f[feature] >= 0.4:
        return "SCAM_SMS_LINKED", {}
    if feature == "sms_recent_scam" and f[feature] >= 1:
        return "RECENT_SCAM_SMS", {}
    if feature == "channel_collect" and f[feature] >= 1:
        return "COLLECT_DEBIT", {"amount_value": ctx["amount"]}
    if feature == "collect_note_score" and f[feature] >= 0.5:
        return "DECEPTIVE_NOTE", {}
    if feature in ("qr_flag", "channel_qr") and f["qr_flag"] >= 0.5:
        return "QR_TRICK", {}
    if feature == "behaviour_score" and f[feature] >= 0.02:
        return M1_REASON.get(ctx.get("m1_top") or "", "BEHAVIOUR_GENERAL"), {}
    if feature == "payer_account_age_days" and f[feature] < 30:
        return "NEW_USER", {}
    return None


def _safe_reason(feature: str, f: dict[str, float], ctx: dict[str, Any]) -> tuple[str, dict] | None:
    payee = ctx["payee_name"]
    if feature == "payee_times_paid" and f[feature] >= 1:
        return "KNOWN_PAYEE", {"payee": payee, "n": int(f[feature])}
    if feature == "is_saved_contact" and f[feature] >= 1:
        return "SAVED_CONTACT", {"payee": payee}
    if feature == "payee_account_age_days" and f[feature] >= 365 and ctx["report_count"] == 0:
        return "TRUSTED_PAYEE", {"payee": payee}
    if feature == "amount_to_median" and f[feature] <= 1.5 and ctx["has_history"]:
        return "USUAL_AMOUNT", {}
    if feature == "hour_share" and f[feature] >= 0.2 and ctx["has_history"]:
        return "USUAL_TIME", {}
    return None


def build_reasons(features: dict[str, float], contributions: dict[str, float], ctx: dict[str, Any], top: int = 4) -> tuple[list[dict], list[dict]]:
    """Returns (risk reasons, reassuring reasons), each item {code, params, contribution, text{en,hi,te}}."""
    risk, safe, seen = [], [], set()
    guard_codes = []
    if features.get("channel_collect", 0) >= 1:
        guard_codes.append(("COLLECT_DEBIT", {"amount_value": ctx["amount"]}, "channel_collect"))
    if features.get("qr_flag", 0) >= 0.5:
        guard_codes.append(("QR_TRICK", {}, "qr_flag"))
    for code, params, feat in guard_codes:
        risk.append({"code": code, "params": params, "feature": feat, "contribution": round(float(contributions.get(feat, 0.0)), 4), "kind": "guard"})
        seen.add(code)

    for feature, value in sorted(contributions.items(), key=lambda kv: -kv[1]):
        if value <= 0.02 or len(risk) >= top + len(guard_codes):
            break
        hit = _risk_reason(feature, features, ctx)
        if hit and hit[0] not in seen:
            seen.add(hit[0])
            risk.append({"code": hit[0], "params": hit[1], "feature": feature, "contribution": round(float(value), 4), "kind": "model"})

    for feature, value in sorted(contributions.items(), key=lambda kv: kv[1]):
        if value >= -0.02 or len(safe) >= 3:
            break
        hit = _safe_reason(feature, features, ctx)
        if hit and hit[0] not in seen:
            seen.add(hit[0])
            safe.append({"code": hit[0], "params": hit[1], "feature": feature, "contribution": round(float(value), 4), "kind": "model"})

    for item in risk + safe:
        item["text"] = reason_texts(item["code"], item["params"])
        item["params"] = {k: v for k, v in item["params"].items() if k != "amount_value"} | (
            {"amount": ctx["amount"]} if "amount_value" in item["params"] else {}
        )
    return risk, safe
