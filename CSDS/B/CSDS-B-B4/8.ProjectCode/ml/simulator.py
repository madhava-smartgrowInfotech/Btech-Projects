"""Seeded UPI payment-scenario simulator used to train M3 (the payment risk model).

No public dataset contains UPI-specific context such as "new payee", community scam reports,
a linked scam SMS or a collect request that pretends to be a refund. This simulator creates a
year of sandbox-style UPI activity in which:

* normal behaviour (amounts, hours, categories, weekend effect) follows UPI Transactions 2024;
* scam episodes follow twelve Indian scam typologies, with deliberate overlap and noise
  (scams through a friend's taken-over account, genuine large night payments to new payees,
  unrelated scam-SMS checks, legitimate collect requests between friends, label noise);
* every feature is computed with the same functions the live risk engine uses
  (backend/app/ml/features.py), and SMS / collect-note signals come from running the real
  M2 model on held-out messages it never saw in training.

The output is fully determined by the seed.
"""
from __future__ import annotations

import bisect
import heapq
import json
import math
from collections import defaultdict, deque
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from common import DATA_PROCESSED, DATA_RAW, MODELS
from app.ml.features import (  # noqa: E402
    M1_FEATURES,
    RISK_FEATURES,
    TrustInputs,
    m1_row,
    merchant_risk_from_trust,
    report_weight,
    risk_row,
    trust_score,
)

DAY = 86400.0
HOUR = 3600.0
YEAR_DAYS = 365

SCAM_MIX = {
    "kyc_fraud": 0.15,
    "refund_scam": 0.15,
    "lottery_prize": 0.08,
    "job_task": 0.11,
    "impersonation": 0.10,
    "qr_scam": 0.10,
    "bill_disconnection": 0.07,
    "loan_fee": 0.06,
    "courier_customs": 0.05,
    "wrong_transfer": 0.04,
    "investment": 0.05,
    "account_takeover": 0.04,
}
# How each scam type usually behaves: amount range (INR), payments per episode, night share, channel mix.
SCAM_SHAPE = {
    "kyc_fraud": dict(amount=(10, 5000), n=(1, 2), night=0.08, channels={"send": 0.7, "collect": 0.3}, sms=0.9, sms_cat="kyc_fraud"),
    "refund_scam": dict(amount=(1500, 25000), n=(1, 2), night=0.08, channels={"collect": 0.85, "send": 0.15}, sms=0.6, sms_cat="refund_scam"),
    "lottery_prize": dict(amount=(999, 15000), n=(1, 3), night=0.1, channels={"send": 1.0}, sms=0.9, sms_cat="lottery_prize"),
    "job_task": dict(amount=(200, 60000), n=(2, 5), night=0.22, channels={"send": 1.0}, sms=0.7, sms_cat="job_task", escalate=True),
    "impersonation": dict(amount=(3000, 30000), n=(1, 2), night=0.3, channels={"send": 1.0}, sms=0.5, sms_cat="impersonation"),
    "qr_scam": dict(amount=(1000, 10000), n=(1, 1), night=0.1, channels={"qr": 1.0}, sms=0.2, sms_cat="refund_scam"),
    "bill_disconnection": dict(amount=(10, 3000), n=(1, 1), night=0.35, channels={"send": 1.0}, sms=0.95, sms_cat="bill_disconnection"),
    "loan_fee": dict(amount=(999, 12000), n=(1, 2), night=0.1, channels={"send": 1.0}, sms=0.9, sms_cat="loan_fee"),
    "courier_customs": dict(amount=(49, 2500), n=(1, 1), night=0.08, channels={"send": 1.0}, sms=0.95, sms_cat="courier_customs"),
    "wrong_transfer": dict(amount=(1500, 12000), n=(1, 1), night=0.12, channels={"send": 1.0}, sms=0.7, sms_cat="wrong_transfer"),
    "investment": dict(amount=(2000, 100000), n=(1, 3), night=0.15, channels={"send": 1.0}, sms=0.6, sms_cat="investment", escalate=True),
    "account_takeover": dict(amount=(4000, 40000), n=(1, 2), night=0.4, channels={"send": 0.6, "collect": 0.4}, sms=0.0, sms_cat=None),
}
MERCHANT_CATEGORIES = ["Grocery", "Food", "Shopping", "Fuel", "Healthcare", "Transport", "Entertainment", "Education", "Utilities", "Other"]


@dataclass
class Payer:
    idx: int
    created: float
    device: str
    elderly: bool
    rate: float
    scale: float
    hour_probs: np.ndarray
    friends: list[int]
    merchants: list[int]
    bills: list[int]
    saved: set[int] = field(default_factory=set)
    paid: dict[int, int] = field(default_factory=lambda: defaultdict(int))
    history: deque = field(default_factory=deque)  # (t, amount, hour)
    failed: deque = field(default_factory=deque)
    scam_sms_checks: deque = field(default_factory=deque)  # times the user checked a scam-verdict SMS
    linked: dict[int, tuple[float, float]] = field(default_factory=dict)  # payee -> (t, sms prob)


class Window:
    """Rolling window of (time, payer, first_time) with O(1) distinct-payer counts."""

    __slots__ = ("span", "items", "counts", "first")

    def __init__(self, span: float) -> None:
        self.span = span
        self.items: deque = deque()
        self.counts: dict[int, int] = {}
        self.first = 0

    def trim(self, t: float) -> None:
        while self.items and self.items[0][0] < t - self.span:
            _, payer, first = self.items.popleft()
            c = self.counts[payer] - 1
            if c:
                self.counts[payer] = c
            else:
                del self.counts[payer]
            self.first -= first

    def add(self, t: float, payer: int, first: bool) -> None:
        self.items.append((t, payer, first))
        self.counts[payer] = self.counts.get(payer, 0) + 1
        self.first += first


@dataclass
class Payee:
    created: float
    is_merchant: bool
    w24: Window = field(default_factory=lambda: Window(DAY))
    w7: Window = field(default_factory=lambda: Window(7 * DAY))
    w90: Window = field(default_factory=lambda: Window(90 * DAY))
    payers_all: set = field(default_factory=set)
    collects: deque = field(default_factory=deque)  # (t, target)
    reports: list = field(default_factory=list)  # (t, reporter_age_days)


class Simulator:
    def __init__(self, seed: int = 42, n_users: int = 3000, n_merchants: int = 900, sms_bundle=None, episode_rate: float = 0.55) -> None:
        self.rng = np.random.default_rng(seed)
        self.n_users = n_users
        self.n_merchants = n_merchants
        self.episode_rate = episode_rate
        self.profile = json.loads((MODELS / "behaviour_profile.json").read_text(encoding="utf-8"))
        self.hour_share = np.array([self.profile["hour_share"][str(h)] for h in range(24)], dtype=float)
        self.hour_share /= self.hour_share.sum()
        self.hour_window = {h: self.profile["hour_window_share"][str(h)] for h in range(24)}
        self._load_texts(sms_bundle)
        self.payees: dict[int, Payee] = {}
        self.payers: list[Payer] = []
        self.merchant_cat: dict[int, str] = {}

    # ------------------------------------------------------------------ texts
    def _load_texts(self, bundle) -> None:
        from app.ml.sms import batch_scores

        held = pd.read_csv(DATA_PROCESSED / "sms_heldout_for_simulation.csv")
        uci = pd.read_csv(DATA_RAW / "sms_spam_collection" / "spam.csv", encoding="latin-1")[["v1", "v2"]]
        texts = pd.concat([held.text, uci[uci.v1 == "ham"].v2.head(400)]).drop_duplicates().tolist()
        scores = dict(zip(texts, batch_scores(bundle, texts)))
        thr = bundle["thresholds"]["scam"]
        self.sms_scam_threshold = thr
        sms = held[held.kind == "sms"]
        self.scam_sms = {c: [scores[t] for t in g.text] for c, g in sms[sms.label == 1].groupby("category")}
        self.legit_sms_scores = [scores[t] for t in sms[sms.label == 0].text] + [scores[t] for t in uci[uci.v1 == "ham"].v2.head(400)]
        notes = held[held.kind == "collect_note"]
        self.scam_notes = [scores[t] for t in notes[notes.label == 1].text] or [0.9]
        self.legit_notes = [scores[t] for t in notes[notes.label == 0].text] or [0.05]

    # ------------------------------------------------------------------ world
    def _hour_profile(self) -> np.ndarray:
        shift = self.rng.normal(0, 1.2)
        idx = (np.arange(24) - shift) % 24
        probs = np.interp(idx, np.arange(24), self.hour_share, period=24) ** self.rng.uniform(0.9, 1.4)
        return probs / probs.sum()

    def build_world(self) -> None:
        rng = self.rng
        cat_share = self.profile["category_share"]
        cats = list(cat_share)
        probs = np.array([cat_share[c] for c in cats])
        for m in range(self.n_merchants):
            pid = 100000 + m
            age = rng.uniform(10, 90) if rng.random() < 0.06 else rng.uniform(90, 3000)
            self.payees[pid] = Payee(created=-age * DAY, is_merchant=True)
            self.merchant_cat[pid] = rng.choice(cats, p=probs / probs.sum())
        utilities = [p for p, c in self.merchant_cat.items() if c == "Utilities"] or [100000]
        popularity = 1.0 / np.arange(1, self.n_merchants + 1) ** 0.6
        popularity /= popularity.sum()
        for u in range(self.n_users):
            age = rng.uniform(0, 60) if rng.random() < 0.1 else rng.uniform(60, 2500)
            elderly = rng.random() < 0.18
            payer = Payer(
                idx=u,
                created=-age * DAY,
                device=rng.choice(["mobile", "desktop", "tablet"], p=[0.86, 0.11, 0.03]),
                elderly=elderly,
                rate=float(np.clip(rng.lognormal(math.log(0.55 if not elderly else 0.3), 0.5), 0.08, 3.0)),
                scale=float(rng.lognormal(0, 0.45)),
                hour_probs=self._hour_profile(),
                friends=[],
                merchants=list(rng.choice(np.arange(100000, 100000 + self.n_merchants), size=rng.integers(5, 13), replace=False, p=popularity)),
                bills=list(rng.choice(utilities, size=min(len(utilities), rng.integers(1, 3)), replace=False)),
            )
            self.payers.append(payer)
            self.payees[u] = Payee(created=payer.created, is_merchant=False)
        for payer in self.payers:
            k = rng.integers(3, 10)
            payer.friends = [int(f) for f in rng.choice(self.n_users, size=k, replace=False) if f != payer.idx]
            for f in payer.friends:
                if rng.random() < 0.8:
                    payer.saved.add(f)
            for m in payer.merchants:
                if rng.random() < 0.4:
                    payer.saved.add(int(m))
            for b in payer.bills:
                if rng.random() < 0.7:
                    payer.saved.add(int(b))
            # Earlier relationships: most regular payees were paid before the simulated year started.
            for p in payer.friends + [int(m) for m in payer.merchants] + [int(b) for b in payer.bills]:
                if rng.random() < 0.85:
                    payer.paid[p] = int(rng.integers(1, 12))
                    self.payees[p].payers_all.add(payer.idx)
        self.next_scammer = 200000

    def new_scammer(self, t: float, merchant_like: bool = False) -> int:
        """Receiving accounts are a mix of fresh accounts, older rented "mule" accounts and
        long-standing accounts that were compromised - so account age alone never gives a scam away."""
        pid = self.next_scammer
        self.next_scammer += 1
        r = self.rng.random()
        if merchant_like:
            age = self.rng.uniform(20, 400)
        elif r < 0.45:
            age = self.rng.exponential(6)
        elif r < 0.8:
            age = self.rng.uniform(20, 300)
        else:
            age = self.rng.uniform(300, 2000)
        self.payees[pid] = Payee(created=t - age * DAY, is_merchant=merchant_like and self.rng.random() < 0.5)
        return pid

    # ----------------------------------------------------------------- events
    def _hour(self, payer: Payer, night_share: float | None = None) -> float:
        if night_share is not None and self.rng.random() < night_share:
            h = self.rng.choice([23, 0, 1, 2, 3, 4])
        else:
            h = self.rng.choice(24, p=payer.hour_probs)
        return float(h) + self.rng.random()

    def _amount(self, category: str, scale: float, weekend: bool) -> float:
        prof = self.profile["amount_by_category"].get(category) or self.profile["overall_amount"]
        a = self.rng.lognormal(prof["mu"], prof["sigma"] * 0.8) * scale
        if weekend:
            a *= self.profile["weekend_amount_ratio"].get(category, 1.0)
        return float(np.clip(round(a), 10, 200000))

    def generate_events(self) -> list[tuple]:
        """Returns (t, payer, payee, amount, channel, label, scam_type, extras) sorted by time."""
        rng = self.rng
        events: list[tuple] = []
        for payer in self.payers:
            n = rng.poisson(payer.rate * YEAR_DAYS)
            days = np.sort(rng.uniform(0, YEAR_DAYS, size=n))
            for d in days:
                day0 = math.floor(d) * DAY
                weekend = (math.floor(d) % 7) in (5, 6)
                r = rng.random()
                extras: dict = {}
                if r < 0.27 and payer.friends:
                    payee = int(rng.choice(payer.friends))
                    amount = self._amount("Other", payer.scale * 0.9, weekend)
                    channel = "collect" if rng.random() < 0.08 else "send"
                    hour = self._hour(payer, 0.03)
                    if channel == "collect":
                        extras["note"] = float(rng.choice(self.legit_notes)) if rng.random() < 0.7 else 0.0
                elif r < 0.78:
                    payee = int(rng.choice(payer.merchants))
                    amount = self._amount(self.merchant_cat[payee], payer.scale, weekend)
                    channel = "qr" if rng.random() < 0.65 else "send"
                    hour = self._hour(payer, 0.03)
                    if channel == "qr":
                        extras["qr"] = 1.0 if rng.random() < 0.01 else 0.0
                elif r < 0.84 and payer.bills:
                    payee = int(rng.choice(payer.bills))
                    amount = self._amount("Utilities", payer.scale, False)
                    channel = "send"
                    hour = self._hour(payer)
                else:
                    # A payee the user has never paid: new shop, new person, occasional big genuine payment.
                    if rng.random() < 0.6:
                        payee = int(rng.integers(100000, 100000 + self.n_merchants))
                        amount = self._amount(self.merchant_cat[payee], payer.scale * 1.2, weekend)
                        channel = "qr" if rng.random() < 0.6 else "send"
                    else:
                        payee = int(rng.integers(0, self.n_users))
                        if payee == payer.idx:
                            continue
                        amount = self._amount("Other", payer.scale, weekend)
                        if rng.random() < 0.12:  # deposits, rent, second-hand purchase ...
                            amount = float(rng.choice([8000, 12000, 15000, 20000, 25000, 30000, 45000, 60000]))
                        channel = "send"
                    hour = self._hour(payer, 0.06)
                    if rng.random() < 0.5:
                        extras["becomes_regular"] = True
                t = day0 + hour * HOUR
                if rng.random() < 0.03:
                    extras["failed_before"] = int(rng.integers(1, 3))
                events.append((t, payer.idx, payee, amount, channel, 0, "none", extras))

            # Unrelated scam-SMS checks (the user spotted a scam and did not pay) - hard negatives.
            for d in rng.uniform(0, YEAR_DAYS, size=rng.poisson(1.5)):
                events.append((d * DAY + self._hour(payer) * HOUR, payer.idx, -1, 0.0, "sms_check", 0, "none", {"scam": rng.random() < 0.55}))

            # Scam episodes.
            rate = self.episode_rate * (1.9 if payer.elderly else 1.0) * (1.4 if payer.created > -60 * DAY else 1.0)
            for _ in range(rng.poisson(rate)):
                events.extend(self._episode(payer, rng.uniform(0, YEAR_DAYS) * DAY))
        events.sort(key=lambda e: e[0])
        return events

    def _episode(self, payer: Payer, t0: float) -> list[tuple]:
        rng = self.rng
        kinds = list(SCAM_MIX)
        kind = rng.choice(kinds, p=np.array([SCAM_MIX[k] for k in kinds]))
        shape = SCAM_SHAPE[kind]
        if kind == "account_takeover":
            if not payer.friends:
                return []
            payee = int(rng.choice(payer.friends))
        else:
            payee = self.new_scammer(t0, merchant_like=kind in ("qr_scam", "refund_scam") and rng.random() < 0.35)
        out: list[tuple] = []
        sms_prob = None
        if shape["sms_cat"] and rng.random() < shape["sms"]:
            checked = rng.random() < (0.25 if payer.elderly else 0.32)
            if checked:
                sms_prob = float(rng.choice(self.scam_sms.get(shape["sms_cat"], [0.9])))
                linked = rng.random() < 0.7
                out.append((t0 - rng.uniform(0.1, 20) * HOUR, payer.idx, payee if linked else -1, 0.0, "sms_check", 0, kind, {"scam_prob": sms_prob, "scam": sms_prob >= self.sms_scam_threshold}))
        n = int(rng.integers(shape["n"][0], shape["n"][1] + 1))
        lo, hi = shape["amount"]
        amount = float(np.exp(rng.uniform(math.log(lo), math.log(hi if not shape.get("escalate") else max(lo * 4, hi / 6)))))
        t = t0
        for i in range(n):
            channels = shape["channels"]
            channel = rng.choice(list(channels), p=list(channels.values()))
            hour = self._hour(payer, shape["night"])
            if i == 0:
                t = math.floor(t0 / DAY) * DAY + hour * HOUR
                if t < t0:
                    t += DAY
            else:
                t += rng.exponential(0.6 if kind == "job_task" else 18) * HOUR
            extras: dict = {}
            if channel == "collect":
                extras["note"] = float(rng.choice(self.scam_notes)) if rng.random() < 0.75 else float(rng.choice(self.legit_notes)) * 0.5
                extras["collect_from_payee"] = True
            if channel == "qr":
                extras["qr"] = 1.0 if rng.random() < 0.65 else 0.0
            if rng.random() < 0.2:
                extras["failed_before"] = int(rng.integers(1, 3))
            if rng.random() < 0.35 and kind != "account_takeover":
                extras["report_after"] = float(rng.exponential(2.0) * DAY + 0.5 * HOUR)
            out.append((t, payer.idx, payee, float(round(amount)), channel, 1, kind, extras))
            if shape.get("escalate"):
                amount = min(hi, amount * rng.uniform(1.6, 3.5))
        # Other people also report busy scam accounts.
        if kind != "account_takeover" and rng.random() < 0.5:
            for _ in range(rng.poisson(1.2)):
                out.append((t0 + rng.uniform(0.2, 6) * DAY, int(rng.integers(0, self.n_users)), payee, 0.0, "report", 0, kind, {}))
        # Scam accounts spray collect requests at many people.
        if kind in ("refund_scam", "kyc_fraud") and rng.random() < 0.6:
            for _ in range(rng.poisson(4)):
                out.append((t0 - rng.uniform(0, 3) * DAY, int(rng.integers(0, self.n_users)), payee, 0.0, "collect_sent", 0, kind, {}))
        return out

    # --------------------------------------------------------------- features
    def run(self) -> pd.DataFrame:
        self.build_world()
        events = self.generate_events()
        rng = self.rng
        pending_reports: list[tuple[float, int, int]] = []
        rows: list[dict] = []
        m1_rows: list[dict] = []
        for t, u, p, amount, channel, label, kind, extras in events:
            while pending_reports and pending_reports[0][0] <= t:
                rt, reporter, target = heapq.heappop(pending_reports)
                self.payees[target].reports.append((rt, (rt - self.payers[reporter].created) / DAY))
            payer = self.payers[u]
            if channel == "sms_check":
                if extras.get("scam"):
                    payer.scam_sms_checks.append(t)
                    if p >= 0:
                        payer.linked[p] = (t, extras.get("scam_prob", 0.9))
                continue
            if channel == "report":
                if p in self.payees:
                    self.payees[p].reports.append((t, (t - self.payers[u].created) / DAY))
                continue
            if channel == "collect_sent":
                if p in self.payees:
                    self.payees[p].collects.append((t, u))
                continue
            if p not in self.payees or p == u:
                continue
            payee = self.payees[p]
            if extras.get("collect_from_payee"):
                payee.collects.append((t - 60, u))

            # ---- payer state -------------------------------------------------
            while payer.history and payer.history[0][0] < t - 90 * DAY:
                payer.history.popleft()
            while payer.failed and payer.failed[0] < t - DAY:
                payer.failed.popleft()
            while payer.scam_sms_checks and payer.scam_sms_checks[0] < t - DAY:
                payer.scam_sms_checks.popleft()
            for _ in range(extras.get("failed_before", 0)):
                payer.failed.append(t - rng.uniform(30, 1800))
            hist_t = [h[0] for h in payer.history]
            c1 = len(hist_t) - bisect.bisect_left(hist_t, t - HOUR)
            c24 = len(hist_t) - bisect.bisect_left(hist_t, t - DAY)
            past_amounts = [h[1] for h in payer.history]
            past_hours = [h[2] for h in payer.history]
            age_days = (t - payer.created) / DAY
            months = max(1.0, min(90.0, max(age_days, 1.0)) / 30.0)
            avg_monthly = sum(past_amounts) / months if past_amounts else 0.0
            hour = (t % DAY) / HOUR

            # ---- payee state ---------------------------------------------------
            for w in (payee.w24, payee.w7, payee.w90):
                w.trim(t)
            while payee.collects and payee.collects[0][0] < t - 7 * DAY:
                payee.collects.popleft()
            n7 = len(payee.w7.items)
            new_share = payee.w7.first / n7 if n7 else 0.0
            reports = sum(report_weight(age, (t - rt) / DAY) for rt, age in payee.reports if rt <= t)
            payee_age = (t - payee.created) / DAY
            trust, _ = trust_score(
                TrustInputs(
                    account_age_days=payee_age,
                    report_score=reports,
                    distinct_payers_24h=len(payee.w24.counts),
                    distinct_payers_7d=len(payee.w7.counts),
                    new_payer_share_7d=new_share,
                    inbound_count_90d=len(payee.w90.items),
                    distinct_payers_90d=len(payee.w90.counts),
                    collect_targets_7d=len({c[1] for c in payee.collects}),
                    is_merchant=payee.is_merchant,
                )
            )
            times_paid = payer.paid.get(p, 0)
            link = payer.linked.get(p)
            sms_prob = link[1] if link and t - link[0] <= 2 * DAY else 0.0
            geo = None if rng.random() < 0.8 else float(rng.gamma(1.5, 6.0))
            m1_rows.append(
                m1_row(
                    amount=amount,
                    avg_monthly_spend=avg_monthly,
                    account_age_days=age_days,
                    txn_count_1h=c1,
                    txn_count_24h=c24,
                    failed_txn_count_24h=len(payer.failed),
                    geo_distance_km=geo,
                    merchant_risk_score=merchant_risk_from_trust(trust),
                    hour=hour,
                    device=payer.device,
                )
            )
            row = risk_row(
                behaviour_score=0.0,  # filled in after M1 scores every row
                amount=amount,
                past_amounts=past_amounts,
                is_new_payee=times_paid == 0,
                payee_times_paid=times_paid,
                is_saved_contact=p in payer.saved,
                hour=hour,
                past_hours=past_hours,
                hour_prior=self.hour_window[int(hour) % 24],
                txn_count_1h=c1,
                txn_count_24h=c24,
                failed_24h=len(payer.failed),
                payee_account_age_days=payee_age,
                payee_reports=reports,
                payee_distinct_payers_24h=len(payee.w24.counts),
                payee_new_payer_share_7d=new_share,
                payee_collects_7d=len({c[1] for c in payee.collects}),
                payee_is_merchant=payee.is_merchant,
                sms_scam_prob=sms_prob,
                sms_recent_scam=bool(payer.scam_sms_checks),
                channel=channel,
                collect_note_score=extras.get("note", 0.0) if channel == "collect" else 0.0,
                qr_flag=extras.get("qr", 0.0) if channel == "qr" else 0.0,
                payer_account_age_days=age_days,
            )
            row.update({"t": t, "payer": u, "payee": p, "amount": amount, "channel": channel, "label": label, "scam_type": kind, "payee_trust": trust})
            rows.append(row)

            # ---- update state (payment goes through in the simulated world) ------
            payer.history.append((t, amount, hour))
            payer.paid[p] = times_paid + 1
            if extras.get("becomes_regular") and p < 100000 + self.n_merchants:
                (payer.merchants if p >= 100000 else payer.friends).append(p)
            first_time = u not in payee.payers_all
            payee.payers_all.add(u)
            for w in (payee.w24, payee.w7, payee.w90):
                w.add(t, u, first_time)
            if "report_after" in extras:
                heapq.heappush(pending_reports, (t + extras["report_after"], u, p))

        df = pd.DataFrame(rows)
        m1 = pd.DataFrame(m1_rows)[M1_FEATURES]
        # Label noise, as in any real ledger: some scams are never reported (2%) and a handful of
        # genuine payments are wrongly reported as scams (0.02%).
        u = rng.random(len(df))
        flip = ((df.label == 1) & (u < 0.02)) | ((df.label == 0) & (u < 0.0002))
        df.loc[flip, "label"] = 1 - df.loc[flip, "label"]
        df["label_noise"] = flip.astype(int)
        return df, m1


def simulate(behaviour_bundle, sms_bundle, seed: int = 42, n_users: int = 3000) -> pd.DataFrame:
    sim = Simulator(seed=seed, n_users=n_users, sms_bundle=sms_bundle)
    df, m1 = sim.run()
    df["behaviour_score"] = behaviour_bundle["model"].predict_proba(m1)[:, 1]
    start = pd.Timestamp("2025-01-01")
    df.insert(0, "timestamp", start + pd.to_timedelta(df.pop("t"), unit="s"))
    cols = ["timestamp", "payer", "payee", "amount", "channel", "label", "scam_type", "label_noise", "payee_trust"] + RISK_FEATURES
    return df[cols].sort_values("timestamp").reset_index(drop=True)
