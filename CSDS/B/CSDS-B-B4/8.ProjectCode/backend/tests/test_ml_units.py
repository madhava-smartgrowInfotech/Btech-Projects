"""Unit tests for the shared features, SMS rules, trust score and score mapping."""
from __future__ import annotations

import math

from app.ml.features import M1_FEATURES, RISK_FEATURES, TrustInputs, m1_row, merchant_risk_from_trust, risk_row, trust_score
from app.ml.registry import registry
from app.ml.sms import analyze
from app.services.risk import score_from_probability
from app.services.sms_rules import detect_language, extract_entities, match_rules


def test_m1_row_has_every_feature_and_clips_account_age():
    row = m1_row(amount=500, avg_monthly_spend=3000, account_age_days=2, txn_count_1h=0, txn_count_24h=1, failed_txn_count_24h=0, geo_distance_km=None, merchant_risk_score=0.2, hour=13.5)
    assert list(row) == M1_FEATURES
    assert row["account_age_days"] == 30 and math.isnan(row["geo_distance_from_last_txn"])
    assert abs(row["hour_sin"] ** 2 + row["hour_cos"] ** 2 - 1) < 1e-9


def test_risk_row_uses_population_defaults_without_history():
    row = risk_row(
        behaviour_score=0.01, amount=6300, past_amounts=[], is_new_payee=True, payee_times_paid=0, is_saved_contact=False, hour=1.5,
        past_hours=[], hour_prior=0.02, txn_count_1h=0, txn_count_24h=0, failed_24h=0, payee_account_age_days=5, payee_reports=0,
        payee_distinct_payers_24h=0, payee_new_payer_share_7d=0, payee_collects_7d=0, payee_is_merchant=False, sms_scam_prob=0,
        sms_recent_scam=False, channel="send", collect_note_score=0, qr_flag=0, payer_account_age_days=400,
    )
    assert list(row) == RISK_FEATURES
    assert row["amount_to_median"] == 10.0 and row["is_night"] == 1.0 and row["hour_share"] == 0.02


def test_trust_score_rewards_history_and_punishes_reports():
    good, _ = trust_score(TrustInputs(900, 0, 1, 3, 0.1, 40, 12, 0, True))
    bad, parts = trust_score(TrustInputs(2, 2.5, 5, 6, 1.0, 6, 6, 5, False))
    assert good >= 80 and bad <= 10
    assert {p["code"] for p in parts} >= {"account_age", "community_reports", "many_new_payers", "mass_collect_requests"}
    assert merchant_risk_from_trust(100) < merchant_risk_from_trust(50) < merchant_risk_from_trust(0)


def test_score_mapping_is_monotonic_and_anchored():
    anchors = {"t_medium": 0.01, "t_high": 0.05, "medium_score": 35, "high_score": 70}
    scores = [score_from_probability(p, anchors) for p in (0, 0.005, 0.01, 0.03, 0.05, 0.5, 1.0)]
    assert scores == sorted(scores) and scores[2] == 35 and scores[4] == 70 and scores[-1] == 100


def test_genuine_otp_advice_is_not_an_otp_request():
    hits = {h["rule"] for h in match_rules("123456 is your OTP. Never share your OTP with anyone, including bank staff.")}
    assert "share_otp_pin" not in hits
    assert "share_otp_pin" in {h["rule"] for h in match_rules("Share the OTP you just received with our officer to secure your account.")}


def test_language_detection_and_entities():
    assert detect_language("आपका खाता बंद हो जाएगा") == ("hi", "native")
    assert detect_language("మీ ఖాతా బ్లాక్ అవుతుంది") == ("te", "native")
    assert detect_language("Aapka account band ho jayega, turant KYC karein") == ("hi", "latin")
    ent = extract_entities("Pay Rs 4,999 to kyc.helpdesk@upg or call 9123456780, mail help@bank.com http://x.top/1")
    assert ent["upi_ids"] == ["kyc.helpdesk@upg"] and ent["phones"] == ["9123456780"] and ent["amounts"] == [4999.0] and ent["urls"]


def test_sms_model_in_three_languages():
    registry.load()
    bundle = registry.bundles["sms"]
    assert analyze(bundle, "आपका KYC आज समाप्त हो रहा है, खाता बंद हो जाएगा। तुरंत लिंक पर क्लिक करें")["verdict"] == "scam"
    assert analyze(bundle, "మీ ఖాతా బ్లాక్ అవుతుంది, వెంటనే KYC అప్‌డేట్ చేయండి")["verdict"] == "scam"
    assert analyze(bundle, "Hey, are we still meeting for lunch at 1?")["verdict"] == "safe"
