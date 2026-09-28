"""Load a generated GST ecosystem and build the three feature layers.

Every active taxpayer-month gets one vector made of:
  * invoice layer   - what the month's invoices look like (matching, e-way bills, round values, young suppliers)
  * behaviour layer - what the GSTR-3B return says (turnover, ITC, mismatch with GSTR-2B, cash paid, filing)
  * network layer   - who the taxpayer trades with (partner counts, new partners, reciprocity, concentration)
"""
import csv
import json
import math
import os
from collections import defaultdict
from datetime import date

import numpy as np

FEATURE_GROUPS = {
    "invoice": ["purchase_invoices", "sales_invoices", "unmatched_share", "no_eway_share", "round_share",
                "young_supplier_share"],
    "behaviour": ["outward_log", "itc_claimed_log", "itc_to_output", "itc_mismatch", "cash_ratio",
                  "filing_delay", "age_log"],
    "network": ["suppliers", "buyers", "new_partner_share", "reciprocal_share", "top_buyer_share", "value_add"],
}
FEATURE_NAMES = [f for g in FEATURE_GROUPS.values() for f in g]
GROUP_INDEX = {g: [FEATURE_NAMES.index(f) for f in fs] for g, fs in FEATURE_GROUPS.items()}
FEATURE_LABELS = {
    "purchase_invoices": "purchase invoices (log count)", "sales_invoices": "sales invoices (log count)",
    "unmatched_share": "share of purchases not reported by suppliers", "no_eway_share": "goods invoices without e-way bill",
    "round_share": "round-value invoices", "young_supplier_share": "purchases from suppliers under 6 months old",
    "outward_log": "outward turnover", "itc_claimed_log": "ITC claimed", "itc_to_output": "ITC claimed / output tax",
    "itc_mismatch": "ITC claimed above GSTR-2B", "cash_ratio": "output tax paid in cash",
    "filing_delay": "filing delay", "age_log": "registration age", "suppliers": "number of suppliers",
    "buyers": "number of buyers", "new_partner_share": "share of new trading partners",
    "reciprocal_share": "sales to parties that also supply it", "top_buyer_share": "largest buyer's share of sales",
    "value_add": "value added (sales vs purchases)",
}
GOODS_SECTORS = {"raw_material", "manufacturer", "wholesaler", "retailer"}


def _d(s):
    return date.fromisoformat(s)


def load_dataset(data_dir):
    def read(name):
        with open(os.path.join(data_dir, name), newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    with open(os.path.join(data_dir, "meta.json"), encoding="utf-8") as f:
        meta = json.load(f)
    taxpayers = read("taxpayers.csv")
    for t in taxpayers:
        t["is_fraud"] = int(t["is_fraud"])
        t["fraud_roles"] = [r for r in t["fraud_roles"].split(";") if r]
    invoices = read("invoices.csv")
    for k, r in enumerate(invoices):
        r["id"] = k
        for c in ("taxable_value", "tax_amount"):
            r[c] = float(r[c])
        for c in ("gst_rate", "eway_bill", "seller_reported", "is_fraud"):
            r[c] = int(r[c])
    returns = read("returns.csv")
    for r in returns:
        for c in ("outward_taxable", "b2c_taxable", "output_tax", "itc_available_2b", "itc_claimed_3b",
                  "tax_paid_cash"):
            r[c] = float(r[c])
        r["filing_delay_days"] = int(r["filing_delay_days"])
    months = meta["months"]
    idx = {t["gstin"]: i for i, t in enumerate(taxpayers)}
    midx = {m: i for i, m in enumerate(months)}
    for r in invoices:
        r["_s"], r["_b"], r["_m"] = idx[r["seller_gstin"]], idx[r["buyer_gstin"]], midx[r["month"]]
    return dict(meta=meta, months=months, taxpayers=taxpayers, invoices=invoices, returns=returns, idx=idx,
                midx=midx)


def build_features(ds):
    """Returns raw feature tensor X (n, months, D), presence mask (n, months) and helper aggregates."""
    tps, months = ds["taxpayers"], ds["months"]
    n, T, D = len(tps), len(months), len(FEATURE_NAMES)
    fi = {f: i for i, f in enumerate(FEATURE_NAMES)}
    reg = [_d(t["registration_date"]) for t in tps]
    goods = [t["sector"] in GOODS_SECTORS for t in tps]

    purch_n = np.zeros((n, T)); sales_n = np.zeros((n, T))
    purch_v = np.zeros((n, T)); sales_v = np.zeros((n, T))
    unmatched_v = np.zeros((n, T)); eway_req = np.zeros((n, T)); eway_miss = np.zeros((n, T))
    round_n = np.zeros((n, T)); young_v = np.zeros((n, T))
    sup_m = defaultdict(set); buy_m = defaultdict(lambda: defaultdict(float))
    suppliers_all = defaultdict(set); first_seen = {}
    for r in ds["invoices"]:
        s, b, m, v = r["_s"], r["_b"], r["_m"], r["taxable_value"]
        purch_n[b, m] += 1; sales_n[s, m] += 1
        purch_v[b, m] += v; sales_v[s, m] += v
        if not r["seller_reported"]:
            unmatched_v[b, m] += v
        if goods[s] and v >= 50000:
            eway_req[b, m] += 1
            eway_miss[b, m] += 1 - r["eway_bill"]
        if v % 10000 == 0:
            round_n[b, m] += 1
        if (_d(r["invoice_date"]) - reg[s]).days < 180:
            young_v[b, m] += v
        sup_m[(b, m)].add(s); buy_m[(s, m)][b] += v
        suppliers_all[b].add(s)
        for key in ((b, s), (s, b)):
            first_seen[key] = min(first_seen.get(key, m), m)

    ret = {(ds["idx"][r["gstin"]], ds["midx"][r["month"]]): r for r in ds["returns"]}
    X = np.zeros((n, T, D), dtype=np.float32)
    present = np.zeros((n, T), dtype=bool)
    for i in range(n):
        for m in range(T):
            r = ret.get((i, m))
            if r is None:
                continue
            present[i, m] = True
            x = X[i, m]
            x[fi["purchase_invoices"]] = math.log1p(purch_n[i, m])
            x[fi["sales_invoices"]] = math.log1p(sales_n[i, m])
            pv = purch_v[i, m]
            x[fi["unmatched_share"]] = unmatched_v[i, m] / pv if pv else 0
            x[fi["no_eway_share"]] = eway_miss[i, m] / eway_req[i, m] if eway_req[i, m] else 0
            x[fi["round_share"]] = round_n[i, m] / purch_n[i, m] if purch_n[i, m] else 0
            x[fi["young_supplier_share"]] = young_v[i, m] / pv if pv else 0
            out_tax, claimed, avail = r["output_tax"], r["itc_claimed_3b"], r["itc_available_2b"]
            x[fi["outward_log"]] = math.log1p(r["outward_taxable"])
            x[fi["itc_claimed_log"]] = math.log1p(claimed)
            x[fi["itc_to_output"]] = min(claimed / (out_tax + 1), 5)
            mm = (claimed - avail) / (avail + 10000)
            x[fi["itc_mismatch"]] = math.copysign(math.log1p(abs(mm)), mm)
            x[fi["cash_ratio"]] = min(r["tax_paid_cash"] / (out_tax + 1), 1)
            x[fi["filing_delay"]] = r["filing_delay_days"] / 30
            month_start = date.fromisoformat(months[m] + "-01")
            x[fi["age_log"]] = math.log1p(max(0, (month_start - reg[i]).days) / 30)
            sups, buys = sup_m.get((i, m), set()), buy_m.get((i, m), {})
            x[fi["suppliers"]] = math.log1p(len(sups))
            x[fi["buyers"]] = math.log1p(len(buys))
            partners = [(i, s) for s in sups] + [(i, b) for b in buys]
            x[fi["new_partner_share"]] = (sum(first_seen[p] == m for p in partners) / len(partners)
                                          if partners and m > 0 else 0)
            sv = sales_v[i, m]
            x[fi["reciprocal_share"]] = (sum(v for b, v in buys.items() if b in suppliers_all[i]) / sv) if sv else 0
            x[fi["top_buyer_share"]] = max(buys.values()) / sv if sv else 0
            outward = r["outward_taxable"]
            x[fi["value_add"]] = (outward - pv) / (outward + pv + 1)
    return dict(X=X, present=present, purch_v=purch_v, sales_v=sales_v, returns=ret)


class RobustScaler:
    def __init__(self, median=None, scale=None):
        self.median, self.scale = median, scale

    def fit(self, X2d):
        q25, med, q75 = np.percentile(X2d, [25, 50, 75], axis=0)
        self.median = med.astype(np.float32)
        self.scale = np.maximum.reduce([(q75 - q25) / 1.349, 0.5 * X2d.std(axis=0),
                                        np.full(X2d.shape[1], 1e-3)]).astype(np.float32)
        return self

    def transform(self, X):
        return np.clip((X - self.median) / self.scale, -10, 10).astype(np.float32)

    def to_dict(self):
        return {"median": self.median.tolist(), "scale": self.scale.tolist()}

    @classmethod
    def from_dict(cls, d):
        return cls(np.array(d["median"], dtype=np.float32), np.array(d["scale"], dtype=np.float32))
