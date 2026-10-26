"""Unit tests for the Smart Availability Engine (app/engine.py) and the policy constants."""
from datetime import timedelta

import pytest

from app import config
from app.engine import (fee_multiplier, forecast_free, haversine_km, nearest_alternate, quote_fee,
                        record_checkout_trust, reset_buffers_if_due, suspension_block, utcnow)
from app.models import ParkingLocation, Reservation, TrustEvent, User


def _loc(db, name, cap, buf=1, lat=12.97, lon=77.59, price=4.0):
    loc = ParkingLocation(name=name, address="x", latitude=lat, longitude=lon, capacity=cap,
                          buffer_size=buf, price_per_hour=price)
    db.add(loc)
    db.commit()
    return loc


def _user(db, email, trust=3.0):
    u = User(name="T", email=email, password_hash="x", role="driver", trust_score=trust)
    db.add(u)
    db.commit()
    return u


def _book(db, loc, user, s, e, status="reserved"):
    r = Reservation(user_id=user.id, location_id=loc.id, start_time=s, end_time=e, status=status)
    db.add(r)
    db.commit()
    return r


# ---------------------------------------------------------------- haversine
def test_haversine_zero_distance():
    assert haversine_km(12.97, 77.59, 12.97, 77.59) == pytest.approx(0.0, abs=1e-9)


def test_haversine_known_distance():
    # London -> Paris is about 343.5 km along the great circle
    assert haversine_km(51.5074, -0.1278, 48.8566, 2.3522) == pytest.approx(343.5, abs=1.5)


def test_haversine_symmetric():
    a = haversine_km(12.9716, 77.5946, 12.9850, 77.6100)
    b = haversine_km(12.9850, 77.6100, 12.9716, 77.5946)
    assert a == pytest.approx(b)


# ---------------------------------------------------------------- fee multiplier
@pytest.mark.parametrize("score,mult", [(0, 1.75), (1, 1.5), (2, 1.25), (3, 1.0), (4, 0.95), (5, 0.9)])
def test_fee_multiplier_table(score, mult):
    assert fee_multiplier(score) == mult


def test_fee_multiplier_clamps_out_of_range():
    assert fee_multiplier(-3) == 1.75
    assert fee_multiplier(9) == 0.9


def test_quote_fee_hours_rate_multiplier(db):
    loc = _loc(db, "Fee Lot", 10, price=4.0)
    s = utcnow()
    assert quote_fee(loc, 3.0, s, s + timedelta(hours=2)) == (8.0, 1.0)
    assert quote_fee(loc, 5.0, s, s + timedelta(hours=2)) == (7.2, 0.9)


def test_quote_fee_minimum_quarter_hour(db):
    loc = _loc(db, "Min Lot", 10, price=4.0)
    s = utcnow()
    fee, _ = quote_fee(loc, 3.0, s, s + timedelta(minutes=1))
    assert fee == 1.0  # 0.25 h x 4.0


# ---------------------------------------------------------------- admission rule
def test_admission_rule_bookings_plus_buffer_below_capacity(db):
    loc = _loc(db, "Adm Lot", cap=3, buf=1)
    u = _user(db, "adm@t.io")
    s = utcnow() + timedelta(days=5)
    e = s + timedelta(hours=2)
    assert forecast_free(db, loc, s, e)            # 0 + 1 < 3
    _book(db, loc, u, s, e)
    assert forecast_free(db, loc, s, e)            # 1 + 1 < 3
    _book(db, loc, u, s, e)
    assert not forecast_free(db, loc, s, e)        # 2 + 1 < 3 is False


def test_admission_ignores_non_overlapping_and_cancelled(db):
    loc = _loc(db, "Win Lot", cap=2, buf=1)
    u = _user(db, "win@t.io")
    s = utcnow() + timedelta(days=6)
    e = s + timedelta(hours=2)
    _book(db, loc, u, s + timedelta(hours=3), e + timedelta(hours=3))      # later, no overlap
    _book(db, loc, u, s, e, status="cancelled")                            # cancelled
    assert forecast_free(db, loc, s, e)


def test_zero_buffer_allows_full_capacity(db):
    loc = _loc(db, "Zero Lot", cap=2, buf=0)
    u = _user(db, "zero@t.io")
    s = utcnow() + timedelta(days=7)
    e = s + timedelta(hours=1)
    _book(db, loc, u, s, e)
    assert forecast_free(db, loc, s, e)
    _book(db, loc, u, s, e)
    assert not forecast_free(db, loc, s, e)


# ---------------------------------------------------------------- nearest alternate
def test_nearest_alternate_skips_locations_without_forecast_space(db):
    origin = _loc(db, "Skip Origin", 5, lat=40.0, lon=10.0)
    _loc(db, "Skip Full", 1, buf=1, lat=40.001, lon=10.0)   # 0 + 1 < 1 is False: never admissible
    ok = _loc(db, "Skip OK", 5, lat=40.5, lon=10.0)
    s = utcnow() + timedelta(days=9)
    alt, km = nearest_alternate(db, origin, s, s + timedelta(hours=1))
    assert alt is not None and alt.id == ok.id
    assert km == pytest.approx(haversine_km(40.0, 10.0, 40.5, 10.0))


def test_nearest_alternate_picks_the_closer_of_two(db):
    origin = _loc(db, "Pick Origin", 5, lat=-10.0, lon=50.0)
    near = _loc(db, "Pick Near", 5, lat=-10.02, lon=50.0)
    _loc(db, "Pick Far", 5, lat=-10.20, lon=50.0)
    s = utcnow() + timedelta(days=9)
    alt, _ = nearest_alternate(db, origin, s, s + timedelta(hours=1))
    assert alt.id == near.id


def test_nearest_alternate_none_when_all_excluded(db):
    origin = _loc(db, "Iso Origin", 5, lat=-30.0, lon=100.0)
    others = {l.id for l in db.query(ParkingLocation).all() if l.id != origin.id}
    s = utcnow() + timedelta(days=10)
    alt, km = nearest_alternate(db, origin, s, s + timedelta(hours=1), exclude_ids=others)
    assert alt is None and km == 0.0


# ---------------------------------------------------------------- trust score
def test_three_on_time_checkouts_raise_trust_by_one(db):
    u = _user(db, "t3@t.io", trust=3.0)
    for _ in range(config.BENEFIT_STREAK_FOR_REWARD):
        record_checkout_trust(db, u, True)
    assert u.trust_score == 4.0 and u.benefit_streak == 0
    kinds = [e.kind for e in db.query(TrustEvent).filter(TrustEvent.user_id == u.id)]
    assert kinds.count("benefit") == 3 and kinds.count("reward") == 1


def test_trust_is_capped_at_five(db):
    u = _user(db, "cap@t.io", trust=5.0)
    for _ in range(6):
        record_checkout_trust(db, u, True)
    assert u.trust_score == 5.0


def test_two_late_checkouts_lower_trust_by_one(db):
    u = _user(db, "late@t.io", trust=3.0)
    record_checkout_trust(db, u, False)
    assert u.trust_score == 3.0 and u.warning_count == 1
    record_checkout_trust(db, u, False)
    assert u.trust_score == 2.0 and u.warning_count == 0


def test_trust_floor_is_zero(db):
    u = _user(db, "floor@t.io", trust=0.0)
    for _ in range(4):
        record_checkout_trust(db, u, False)
    assert u.trust_score == 0.0


def test_late_checkout_resets_benefit_streak(db):
    u = _user(db, "streak@t.io", trust=3.0)
    record_checkout_trust(db, u, True)
    record_checkout_trust(db, u, True)
    record_checkout_trust(db, u, False)
    assert u.benefit_streak == 0


# ---------------------------------------------------------------- suspension
def test_no_suspension_for_good_standing(db):
    u = _user(db, "good@t.io", trust=4.0)
    assert suspension_block(db, u) is None


def test_low_trust_without_recent_violation_is_not_suspended(db):
    u = _user(db, "lowclean@t.io", trust=1.0)
    assert suspension_block(db, u) is None


def test_low_trust_with_recent_warning_is_suspended_and_cooled_down(db):
    u = _user(db, "lowbad@t.io", trust=1.0)
    db.add(TrustEvent(user_id=u.id, kind="warning", detail="late"))
    db.commit()
    msg = suspension_block(db, u)
    assert msg and "paused" in msg.lower()
    assert u.suspended_until is not None
    assert suspension_block(db, u)      # the cooldown keeps blocking until it expires


# ---------------------------------------------------------------- buffer reset job
def test_buffer_reset_after_24h(db):
    loc = _loc(db, "Reset Lot", 10, buf=4)
    loc.last_buffer_reset = utcnow() - timedelta(hours=25)
    db.commit()
    n = reset_buffers_if_due(db)
    db.refresh(loc)
    assert n >= 1 and loc.buffer_size == config.BUFFER_INIT


def test_buffer_not_reset_inside_window(db):
    loc = _loc(db, "Fresh Lot", 10, buf=4)
    loc.last_buffer_reset = utcnow() - timedelta(hours=3)
    db.commit()
    reset_buffers_if_due(db)
    db.refresh(loc)
    assert loc.buffer_size == 4


def test_policy_constants_match_documented_values():
    assert (config.BUFFER_INIT, config.BUFFER_MAX, config.BUFFER_RESET_HOURS) == (1, 5, 24)
    assert (config.BENEFIT_STREAK_FOR_REWARD, config.WARNINGS_FOR_PENALTY) == (3, 2)
    assert config.TRUST_START == 3.0 and config.TRUST_SUSPEND_THRESHOLD == 1.5
