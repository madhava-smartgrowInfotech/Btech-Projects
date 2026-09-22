"""Clearly labelled sample activity for the sandbox (history, community reports, held payments, SMS checks).

Every sample payment is scored by the real risk engine at its own point in time, in
chronological order, so history screens and analytics show genuine model output. The random
generator is seeded, so each fresh install gets the same sample story.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models import IST, CollectRequest, Hold, IntentCheck, ScamReport, SmsCheck, User, utcnow
from app.services.payments import create_assessed_payment
from app.services.sms_service import analyze_and_store

log = get_logger("upi_guardian.sample")
SEED = 2026

SCAM_SMS = [
    "Dear customer, your Kaveri Gramin Bank KYC expires today. Your account will be blocked. Update KYC now: http://kyc-verify-now.top/a4471",
    "Congratulations! Your number won Rs 5,00,000 in the Mega Lucky Draw. Pay processing fee of Rs 4,999 to luckydraw.winner@upg to claim now.",
    "आपका UPI खाता ब्लॉक होने वाला है। KYC सत्यापन के लिए अभी इस लिंक पर क्लिक करें http://acct-help-india.site/2231",
    "Your refund of Rs 4,999 from ShopKart is ready. Approve the UPI request from refund.desk@upg and enter your PIN to receive it.",
    "Part-time job: earn Rs 3,000-8,000 daily by liking videos. Join now https://bit-link.cc/8812. Registration fee Rs 199 only.",
    "ప్రియమైన వినియోగదారు, గత నెల బిల్ అప్‌డేట్ కాలేదు కాబట్టి ఈ రాత్రి 9:30కి మీ కరెంట్ కట్ చేయబడుతుంది. వెంటనే అధికారికి 9123456780 కాల్ చేయండి.",
    "Pre-approved instant loan of Rs 2,50,000 without documents! Pay file charge Rs 2,999 to support.verify@upg and get money in 10 minutes.",
    "Swift Courier: Your parcel is held at customs. Pay clearance fee Rs 99 within 24 hours: http://parcel-track-in.info/t5521",
    "Hi Mom, this is my new number. My phone broke. I urgently need Rs 9,999, please send to cashback.offer@upg, will return tomorrow.",
    "Congrats! Cashback of Rs 7,500 credited to your RupeeGo wallet. To withdraw, scan the QR at https://reward-claim.online/c881 and enter UPI PIN.",
]
SAFE_SMS = [
    "Rs 450 debited from A/c XX4821 to Lakshmi General Stores via UPI. Ref 5521908812. Never share your OTP with anyone. -BUNB",
    "Your ShopKart order #88213 has been shipped and will arrive by 26-Sep.",
    "Hey, are we still meeting for lunch at 1?",
]


@dataclass(order=True)
class Planned:
    t: datetime
    payer: str = field(compare=False)
    payee: str = field(compare=False)
    amount: float = field(compare=False)
    channel: str = field(default="send", compare=False)
    note: str | None = field(default=None, compare=False)
    outcome: str = field(default="auto", compare=False)  # auto | hold_cancel | cancel_after_warning | hold_release
    purpose: str | None = field(default=None, compare=False)


def _at(rng: random.Random, day: datetime, start_hour: int = 8, end_hour: int = 21) -> datetime:
    """A time on `day` between the given India-time hours, returned in UTC."""
    local = day.astimezone(IST).replace(hour=rng.randint(start_hour, end_hour), minute=rng.randint(0, 59), second=rng.randint(0, 59), microsecond=0)
    return local.astimezone(utcnow().tzinfo)


def _plan(rng: random.Random, now: datetime) -> list[Planned]:
    plan: list[Planned] = []
    start = now - timedelta(days=180)
    day = start
    while day < now - timedelta(hours=6):
        d = (day - start).days
        # Meera - everyday life
        if rng.random() < 0.38:
            plan.append(Planned(_at(rng, day, 7, 10), "demo", "tea", rng.choice([20, 30, 40, 50, 60, 80])))
        if d % 4 == 0 or rng.random() < 0.08:
            plan.append(Planned(_at(rng, day, 10, 20), "demo", "grocery", float(rng.randint(15, 250) * 10)))
        if d % 30 == 3:
            plan.append(Planned(_at(rng, day, 10, 18), "demo", "power", float(rng.randint(90, 220) * 10)))
        if d % 30 == 12:
            plan.append(Planned(_at(rng, day, 11, 19), "demo", "pharmacy", float(rng.randint(20, 150) * 10)))
        if rng.random() < 0.1:
            plan.append(Planned(_at(rng, day, 12, 21), "demo", "ravi", float(rng.randint(20, 150) * 10)))
        if d % 30 == 20:
            plan.append(Planned(_at(rng, day, 9, 20), "demo", "priya", float(rng.randint(10, 50) * 100)))
        if d % 45 == 8:
            plan.append(Planned(_at(rng, day, 9, 20), "demo", "family", float(rng.randint(10, 30) * 100)))
        # Arjun (family member / trusted contact)
        if rng.random() < 0.2:
            plan.append(Planned(_at(rng, day, 9, 22), "family", rng.choice(["grocery", "tea", "pharmacy"]), float(rng.randint(5, 120) * 10)))
        if d % 30 == 1:
            plan.append(Planned(_at(rng, day, 9, 12), "family", "demo", 15000.0))
        # Community users, last two months
        if d >= 120:
            for i in range(1, 13):
                if rng.random() < 0.18:
                    payee = rng.choice(["grocery", "tea", "pharmacy", "power", f"community{rng.randint(1, 12)}"])
                    if payee != f"community{i}":
                        plan.append(Planned(_at(rng, day), f"community{i}", payee, float(rng.randint(3, 180) * 10)))
        day += timedelta(days=1)

    # Vikram Rao - a new (not reported) account receiving a few first payments.
    for k, i in enumerate((3, 7)):
        plan.append(Planned(_at(rng, now - timedelta(days=5 - k * 2)), f"community{i}", "vikram", float(rng.randint(5, 20) * 100)))

    # Scam accounts and what happened to the people they targeted (all sample data).
    plan += [
        Planned(now - timedelta(days=1, hours=20), "community2", "kyc", 4999.0, outcome="hold_cancel", purpose="kyc"),
        Planned(now - timedelta(days=1, hours=9), "community5", "kyc", 1999.0, outcome="hold_cancel", purpose="kyc"),
        Planned(now - timedelta(hours=30), "community11", "kyc", 999.0, outcome="cancel_after_warning", purpose="kyc"),
        Planned(now - timedelta(days=3, hours=4), "community4", "refund", 4999.0, "collect", "Refund for order #48213 - approve to receive Rs 4,999", outcome="hold_cancel", purpose="refund"),
        Planned(now - timedelta(days=2, hours=11), "community9", "refund", 7500.0, "collect", "Cashback reward Rs 7,500 - accept to get credited", outcome="hold_cancel", purpose="refund"),
        Planned(now - timedelta(hours=22), "community6", "lucky", 4999.0, outcome="cancel_after_warning", purpose="prize"),
        Planned(now - timedelta(hours=14), "community8", "lucky", 2999.0, outcome="auto", purpose="prize"),
        Planned(now - timedelta(days=2, hours=2), "community10", "cashback", 5000.0, "qr", None, outcome="cancel_after_warning", purpose="refund"),
        Planned(now - timedelta(days=9), "community12", "priya", 1200.0, outcome="auto"),
    ]
    return sorted(p for p in plan if p.t < now - timedelta(minutes=5))


def _reports(db: Session, users: dict[str, User], now: datetime) -> list[tuple[datetime, str, str, str]]:
    return [
        (now - timedelta(days=1, hours=18), "community2", "kyc.helpdesk@upg", "kyc_fraud"),
        (now - timedelta(days=1, hours=6), "community5", "kyc.helpdesk@upg", "kyc_fraud"),
        (now - timedelta(hours=26), "community11", "kyc.helpdesk@upg", "kyc_fraud"),
        (now - timedelta(hours=20), "community1", "kyc.helpdesk@upg", "kyc_fraud"),
        (now - timedelta(days=2, hours=20), "community4", "refund.desk@upg", "refund_scam"),
        (now - timedelta(days=2, hours=9), "community9", "refund.desk@upg", "refund_scam"),
        (now - timedelta(hours=21), "community6", "luckydraw.winner@upg", "lottery_prize"),
        (now - timedelta(hours=19), "community3", "luckydraw.winner@upg", "lottery_prize"),
        (now - timedelta(hours=17), "community7", "luckydraw.winner@upg", "lottery_prize"),
        (now - timedelta(days=2), "community10", "cashback.offer@upg", "qr_scam"),
    ]


def generate_sample_activity(db: Session, users: dict[str, User]) -> None:
    rng = random.Random(SEED)
    now = utcnow()
    plan = _plan(rng, now)
    reports = sorted(_reports(db, users, now))
    sms_plan = sorted(
        [(now - timedelta(days=rng.randint(1, 28), hours=rng.randint(0, 20)), f"community{rng.randint(1, 12)}", text) for text in SCAM_SMS + SCAM_SMS[:6]]
        + [(now - timedelta(days=rng.randint(1, 28), hours=rng.randint(0, 20)), f"community{rng.randint(1, 12)}", text) for text in SAFE_SMS]
    )
    ri = si = 0
    counts = {"payments": 0, "held": 0, "cancelled": 0, "blocked": 0}
    for p in plan:
        # Reports and SMS checks that happened before this payment become visible first.
        while ri < len(reports) and reports[ri][0] <= p.t:
            t, who, upi, cat = reports[ri]
            db.add(ScamReport(reporter_user_id=users[who].id, upi_id=upi, category=cat, source="payment", created_at=t))
            ri += 1
        while si < len(sms_plan) and sms_plan[si][0] <= p.t:
            t, who, text = sms_plan[si]
            analyze_and_store(db, users[who], text, now=t)
            si += 1
        db.flush()
        payer, payee = users[p.payer], users[p.payee]
        collect = None
        if p.channel == "collect":
            collect = CollectRequest(
                requester_wallet_id=payee.wallet.id, payer_wallet_id=payer.wallet.id, amount_paise=int(p.amount * 100),
                note=p.note, status="pending", expires_at=p.t + timedelta(days=2), created_at=p.t - timedelta(minutes=20),
            )
            db.add(collect)
            db.flush()
        qr = None
        if p.channel == "qr":
            from app.services.guard import build_upi_uri

            qr = build_upi_uri(payee.wallet.upi_id, "Cashback Offers", p.amount, "Scan to receive cashback")
        txn, assessment, _ = create_assessed_payment(db, payer, payee.wallet, p.amount, note=p.note, channel=p.channel, qr_payload=qr, collect=collect, now=p.t)
        counts["payments"] += 1
        level = assessment.level
        if level != "low" or p.purpose:
            purpose = p.purpose or rng.choice(["shopping", "family_friend", "bill"])
            db.add(IntentCheck(transaction_id=txn.id, purpose=purpose, answers={"purpose": purpose, "asked_by_someone": p.purpose is not None}, matched_scam_type=None, escalated=False, created_at=p.t))
        done = p.t + timedelta(seconds=rng.randint(20, 90))
        outcome = p.outcome
        if assessment.action == "block":
            txn.status, txn.status_reason, txn.completed_at = "blocked", "reported_scam_account", done
            counts["blocked"] += 1
        elif outcome == "cancel_after_warning":
            txn.status, txn.status_reason, txn.completed_at = "cancelled", "cancelled_after_warning", done
            counts["cancelled"] += 1
        elif level == "high" or outcome in ("hold_cancel", "hold_release"):
            minutes = 30
            cancelled = outcome == "hold_cancel"
            db.add(
                Hold(
                    transaction_id=txn.id, status="cancelled" if cancelled else "released", hold_minutes=minutes,
                    hold_until=done + timedelta(minutes=minutes), decided_at=done + timedelta(minutes=rng.randint(2, 25) if cancelled else minutes), created_at=done,
                )
            )
            txn.status = "cancelled" if cancelled else "completed"
            txn.status_reason = "cancelled_during_hold" if cancelled else "released_after_hold"
            txn.completed_at = done + timedelta(minutes=minutes if not cancelled else 5)
            counts["held"] += 1
        else:
            txn.status, txn.completed_at = "completed", done
        if collect:
            collect.status = {"cancelled": "cancelled", "completed": "approved"}.get(txn.status, "declined")
        db.flush()

    while ri < len(reports):
        t, who, upi, cat = reports[ri]
        db.add(ScamReport(reporter_user_id=users[who].id, upi_id=upi, category=cat, source="payment", created_at=t))
        ri += 1
    while si < len(sms_plan):
        t, who, text = sms_plan[si]
        analyze_and_store(db, users[who], text, now=t)
        si += 1

    # Requests waiting for the demo user: one genuine, one disguised refund (sandbox scenario 4).
    db.add(CollectRequest(requester_wallet_id=users["priya"].wallet.id, payer_wallet_id=users["demo"].wallet.id, amount_paise=65000, note="Dinner split", status="pending", expires_at=now + timedelta(days=7), created_at=now - timedelta(hours=3)))
    db.add(CollectRequest(requester_wallet_id=users["refund"].wallet.id, payer_wallet_id=users["demo"].wallet.id, amount_paise=499900, note="Refund for order #48213 - approve to receive Rs 4,999", status="pending", expires_at=now + timedelta(days=7), created_at=now - timedelta(minutes=40)))
    db.flush()
    log.info("sample activity created", extra=counts)
