"""Seeded generator for a synthetic GST ecosystem with injected ITC-fraud patterns.

Creates taxpayers, B2B invoices and monthly returns (GSTR-1 reporting flag, GSTR-2B
available ITC, GSTR-3B claimed ITC and cash paid) for one financial year, then injects
four fraud patterns with ground-truth labels:

  * shell entities      - young look-alike firms sharing an address/contact, issuing
                          fake invoices and paying almost no tax in cash
  * fake invoices       - established businesses claiming ITC on invoices bought
                          from shell clusters (no goods moved)
  * circular trading    - rings of 3-5 firms passing the same value A->B->C->A
  * ITC spikes          - claims far above the credit available in GSTR-2B

Legitimate hard negatives are included on purpose: festival seasonality, one-off capital
purchases, new registrations, group companies at one address, late filers, prior-period
credit catch-ups and naturally reciprocal trade between services and manufacturers.

All output is synthetic sample data.

Usage:
    python scripts/generate_gst_data.py --seed 42 --taxpayers 600 --out data/generated
"""
import argparse
import csv
import json
import os
from datetime import date, timedelta

import numpy as np

N_MONTHS = 12
START_YEAR, START_MONTH = 2025, 4  # financial year 2025-26


def month_start(i):
    m = START_MONTH - 1 + i
    return date(START_YEAR + m // 12, m % 12 + 1, 1)


MONTHS = [month_start(i).strftime("%Y-%m") for i in range(N_MONTHS)]

SECTORS = {
    "raw_material": dict(share=0.10, rates=[5, 18], hsn=["2601", "5201", "3901", "7208", "2804"],
                         b2c=(0.0, 0.02), buy=(0.10, 0.20), goods=True),
    "manufacturer": dict(share=0.20, rates=[12, 18, 28], hsn=["8481", "7308", "3923", "6109", "8708"],
                         b2c=(0.0, 0.08), buy=(0.55, 0.75), goods=True),
    "wholesaler": dict(share=0.25, rates=[5, 12, 18], hsn=["1006", "3004", "8517", "6204", "2106"],
                       b2c=(0.05, 0.20), buy=(0.75, 0.88), goods=True),
    "retailer": dict(share=0.30, rates=[5, 12, 18], hsn=["1905", "3401", "6403", "8516", "9403"],
                     b2c=(0.85, 0.97), buy=(0.70, 0.85), goods=True),
    "services": dict(share=0.15, rates=[18], hsn=["9965", "9983", "9985", "9987", "9973"],
                     b2c=(0.05, 0.30), buy=(0.20, 0.35), goods=False),
}
SUPPLY_FROM = {
    "raw_material": [("services", 1.0)],
    "manufacturer": [("raw_material", 0.85), ("services", 0.15)],
    "wholesaler": [("manufacturer", 0.92), ("services", 0.08)],
    "retailer": [("wholesaler", 0.80), ("manufacturer", 0.12), ("services", 0.08)],
    "services": [("manufacturer", 0.50), ("wholesaler", 0.30), ("services", 0.20)],
}
# downstream first, so each tier knows its B2B sales before it buys
PROCESS_ORDER = ["retailer", "wholesaler", "services", "manufacturer", "raw_material"]

STATES = {"27": ("Maharashtra", ["Mumbai", "Pune", "Nagpur"]), "29": ("Karnataka", ["Bengaluru", "Mysuru"]),
          "33": ("Tamil Nadu", ["Chennai", "Coimbatore"]), "24": ("Gujarat", ["Ahmedabad", "Surat"]),
          "07": ("Delhi", ["New Delhi"]), "09": ("Uttar Pradesh", ["Noida", "Lucknow"]),
          "36": ("Telangana", ["Hyderabad"]), "19": ("West Bengal", ["Kolkata", "Howrah"])}
AREAS = ["Industrial Estate", "MIDC Phase II", "Market Yard", "Trade Centre", "Commercial Complex",
         "Business Park", "Transport Nagar", "Main Road", "Ring Road", "Station Road", "Sector 18", "GIDC"]
NAME_A = ["Shree", "Sai", "Om", "Maa", "Jai", "Sri", "Navkar", "Balaji", "Krishna", "Ganesh", "Laxmi", "Vinayak",
          "Surya", "Tirupati", "Siddhi", "Nandi", "Kaveri", "Ganga", "Aravali", "Sahyadri", "Deccan", "Coastal",
          "Eastern", "Western", "Pioneer", "Prime", "Apex", "Zenith", "Vertex", "Unity", "Global", "Metro",
          "Royal", "Star", "Delta", "Nova", "Orbit", "Crest", "Summit", "Harmony", "Bright", "Lotus"]
NAME_B = {"raw_material": ["Minerals", "Agro", "Polymers", "Metals", "Chemicals", "Cotton", "Steel"],
          "manufacturer": ["Industries", "Manufacturing", "Fabricators", "Engineering", "Textiles", "Plastics",
                           "Components"],
          "wholesaler": ["Traders", "Distributors", "Enterprises", "Trading Co", "Wholesale", "Agencies"],
          "retailer": ["Stores", "Mart", "Retail", "Emporium", "Supermarket", "Outlet"],
          "services": ["Logistics", "Consultants", "Solutions", "Services", "Infotech", "Transport"]}
CONSTITUTIONS = [("Private Limited", "Pvt Ltd", "C", 0.35), ("Proprietorship", "", "P", 0.35),
                 ("Partnership", "& Co", "F", 0.15), ("LLP", "LLP", "F", 0.15)]
GSTIN_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def gstin_checksum(s14):
    total = 0
    for i, c in enumerate(s14):
        p = GSTIN_CHARS.index(c) * (2 if i % 2 else 1)
        total += p // 36 + p % 36
    return GSTIN_CHARS[(36 - total % 36) % 36]


class Gen:
    def __init__(self, seed, n_taxpayers):
        self.rng = np.random.default_rng(seed)
        self.seed = seed
        self.n = n_taxpayers
        self.taxpayers = []
        self.invoices = []
        self.used_gstin = set()
        self.used_names = set()
        self.addr_seq = 0
        self.inv_seq = {}

    # ---------- helpers ----------
    def u(self, a, b):
        return float(self.rng.uniform(a, b))

    def choice(self, seq, p=None):
        return seq[int(self.rng.choice(len(seq), p=p))]

    def new_gstin(self, state, pan_type):
        while True:
            pan = "".join(self.choice(LETTERS) for _ in range(3)) + pan_type + self.choice(LETTERS)
            pan += "".join(str(int(self.rng.integers(10))) for _ in range(4)) + self.choice(LETTERS)
            s14 = state + pan + "1Z"
            g = s14 + gstin_checksum(s14)
            if g not in self.used_gstin:
                self.used_gstin.add(g)
                return g

    def new_name(self, sector, suffix):
        for _ in range(100):
            name = f"{self.choice(NAME_A)} {self.choice(NAME_B[sector])}"
            if suffix:
                name += f" {suffix}"
            if name not in self.used_names:
                self.used_names.add(name)
                return name
        name = f"{name} {len(self.used_names)}"
        self.used_names.add(name)
        return name

    def new_address(self, state):
        self.addr_seq += 1
        city = self.choice(STATES[state][1])
        return (f"ADDR-{self.addr_seq:05d}", f"{int(self.rng.integers(1, 400))}, {self.choice(AREAS)}, {city}",
                f"M-XXXXXX{int(self.rng.integers(1000, 9999))}")

    def add_taxpayer(self, sector, reg_month, role="", constitution=None, state=None, address=None):
        state = state or self.choice(list(STATES))
        if constitution is None:
            constitution = self.choice(CONSTITUTIONS, p=[c[3] for c in CONSTITUTIONS])
        if reg_month >= 0:
            reg = month_start(reg_month) + timedelta(days=int(self.rng.integers(0, 25)))
        elif reg_month > -12:
            reg = month_start(0) + timedelta(days=int(30 * reg_month) + int(self.rng.integers(0, 25)))
        else:
            reg = date(2017, 7, 1) + timedelta(days=int(self.rng.integers(0, 2700)))
        addr_id, addr, contact = address or self.new_address(state)
        cfg = SECTORS[sector]
        tp = dict(
            idx=len(self.taxpayers), gstin=self.new_gstin(state, constitution[2]),
            legal_name=self.new_name(sector, constitution[1]), constitution=constitution[0],
            state=STATES[state][0], sector=sector, registration_date=reg.isoformat(),
            active_from=max(0, reg_month if reg_month >= 0 else 0), active_to=N_MONTHS - 1,
            address_id=addr_id, address=addr, contact_id=contact,
            scale=float(self.rng.lognormal(np.log(1.6e6), 0.8)),
            b2c_share=self.u(*cfg["b2c"]), buy_ratio=self.u(*cfg["buy"]),
            rate=int(self.choice(cfg["rates"])), hsn=self.choice(cfg["hsn"]),
            roles=[role] if role else [], ring_id="", cluster_id="",
            late_filer=self.rng.random() < 0.08,
        )
        self.taxpayers.append(tp)
        return tp

    def active(self, tp, m):
        return tp["active_from"] <= m <= tp["active_to"]

    def add_invoice(self, seller, buyer, m, day, value, reported, eway=None, fraud="", chain=""):
        if value < 1000:
            return
        day = int(min(max(day, 1), 28))
        d = month_start(m) + timedelta(days=day - 1)
        key = (seller["idx"], m)
        self.inv_seq[key] = self.inv_seq.get(key, 0) + 1
        goods = SECTORS[seller["sector"]]["goods"]
        if eway is None:
            eway = goods and value >= 50000 and self.rng.random() < 0.97
        rate = seller["rate"]
        self.invoices.append(dict(
            invoice_no=f"{seller['gstin'][2:7]}/{MONTHS[m][2:4]}{MONTHS[m][5:]}/{self.inv_seq[key]:04d}",
            invoice_date=d.isoformat(), month=MONTHS[m], seller_gstin=seller["gstin"], buyer_gstin=buyer["gstin"],
            hsn=seller["hsn"], taxable_value=round(value, 2), gst_rate=rate, tax_amount=round(value * rate / 100, 2),
            eway_bill=int(bool(eway and goods and value >= 50000)), seller_reported=int(bool(reported)),
            is_fraud=int(bool(fraud)), fraud_type=fraud, chain_id=chain, _s=seller["idx"], _b=buyer["idx"], _m=m))

    def odd_value(self, v):
        # real invoices rarely land on round numbers
        return round(v) + self.u(0.01, 0.99) + (7 if round(v) % 1000 == 0 else 0)

    def round_value(self, v):
        step = 50000 if v > 200000 else 10000
        return float(max(step, round(v / step) * step))

    # ---------- legitimate ecosystem ----------
    def build_legit(self, n_legit):
        sectors = list(SECTORS)
        shares = np.array([SECTORS[s]["share"] for s in sectors])
        for _ in range(n_legit):
            sector = self.choice(sectors, p=shares / shares.sum())
            reg_month = int(self.rng.integers(1, 7)) if self.rng.random() < 0.05 else -99
            self.add_taxpayer(sector, reg_month)
        # group companies sharing one registered address (legitimate)
        legit = list(self.taxpayers)
        n_groups = max(2, int(0.015 * len(legit)))
        for _ in range(n_groups):
            size = int(self.rng.integers(2, 4))
            members = [legit[i] for i in self.rng.choice(len(legit), size, replace=False)]
            for t in members[1:]:
                t["address_id"], t["address"], t["contact_id"] = (members[0]["address_id"], members[0]["address"],
                                                                  members[0]["contact_id"])

        self.season = np.ones(N_MONTHS)
        self.season[6], self.season[7] = 1.55, 1.35  # Oct / Nov festival season
        self.season[11] = 1.15  # year-end push
        by_sector = {s: [t for t in self.taxpayers if t["sector"] == s] for s in sectors}
        # fixed supplier relationships
        for t in self.taxpayers:
            sup = []
            for src, w in SUPPLY_FROM[t["sector"]]:
                pool = [p for p in by_sector[src] if p["idx"] != t["idx"]]
                k = int(self.rng.integers(2, 7)) if w > 0.5 else int(self.rng.integers(1, 3))
                weights = np.array([p["scale"] ** 0.7 for p in pool])
                picks = self.rng.choice(len(pool), min(k, len(pool)), replace=False, p=weights / weights.sum())
                shares_ = self.rng.dirichlet(np.ones(len(picks)) * 2) * w
                sup += [(pool[i], float(s)) for i, s in zip(picks, shares_)]
            t["suppliers"] = sup
            t["b2c"] = [t["scale"] * t["b2c_share"] * self.season[m] * float(self.rng.lognormal(0, 0.15))
                        if t["sector"] in ("retailer", "wholesaler") else
                        t["scale"] * t["b2c_share"] * float(self.rng.lognormal(0, 0.15)) for m in range(N_MONTHS)]
            if t["sector"] == "retailer":
                t["b2c"] = [v / max(t["b2c_share"], 0.5) for v in t["b2c"]]
        self.b2b_sales = np.zeros((len(self.taxpayers), N_MONTHS))

        for sector in PROCESS_ORDER:
            for t in by_sector[sector]:
                for m in range(N_MONTHS):
                    if not self.active(t, m):
                        continue
                    if sector in ("services", "raw_material"):
                        outward = t["scale"] * (1 + 0.1 * np.sin(m))
                    else:
                        outward = self.b2b_sales[t["idx"], m] + t["b2c"][m]
                    purchases = outward * t["buy_ratio"] * float(self.rng.lognormal(0, 0.12))
                    live = [(s, w) for s, w in t["suppliers"] if self.active(s, m)]
                    tot_w = sum(w for _, w in live)
                    for s, w in live:
                        amt = purchases * w / tot_w * float(self.rng.lognormal(0, 0.2))
                        self._split_invoices(s, t, m, amt)
        # one-off capital purchases (legitimate ITC jumps backed by real invoices)
        mfg = by_sector["manufacturer"]
        for t in self.taxpayers:
            if t["sector"] != "services" and self.rng.random() < 0.03:
                m = int(self.rng.integers(max(t["active_from"], 2), N_MONTHS))
                seller = self.choice(mfg)
                if seller is not t and self.active(seller, m):
                    self._split_invoices(seller, t, m, t["scale"] * t["buy_ratio"] * self.u(2, 3), max_n=2)
                    t["capex_month"] = m

    def _split_invoices(self, seller, buyer, m, amount, max_n=8):
        n_inv = int(min(max_n, 1 + self.rng.poisson(amount / 400000)))
        for part in self.rng.dirichlet(np.ones(n_inv) * 3) * amount:
            v = self.odd_value(part)
            self.add_invoice(seller, buyer, m, int(self.rng.integers(1, 29)), v, self.rng.random() < 0.985)
            self.b2b_sales[seller["idx"], m] += v

    # ---------- fraud injection ----------
    def established(self, sectors, exclude_roles=True):
        return [t for t in self.taxpayers if t["sector"] in sectors and t["active_from"] == 0
                and not (exclude_roles and t["roles"]) and t["registration_date"] < "2024-01-01"]

    def inject_shells(self, n_shells):
        clusters = []
        sizes, rem = [], n_shells  # exact total: the last cluster absorbs any remainder
        while rem > 0:
            size = int(self.rng.integers(3, 6))
            size = rem if rem - size < 3 else size
            sizes.append(size)
            rem -= size
        for size in sizes:
            cid = f"SC-{len(clusters) + 1:02d}"
            state = self.choice(list(STATES))
            shared = self.new_address(state)
            reg_month = int(self.rng.integers(-3, 5))
            start = max(0, reg_month)
            end = min(N_MONTHS - 1, start + int(self.rng.integers(5, 10)))
            members = []
            for k in range(size):
                sector = "wholesaler" if self.rng.random() < 0.8 else "services"
                t = self.add_taxpayer(sector, reg_month, "shell_entity", CONSTITUTIONS[1], state, shared)
                if k > 0 and self.rng.random() < 0.3:  # some share only the contact number, not the address
                    own = self.new_address(state)
                    t["address_id"], t["address"] = own[0], own[1]
                t["active_to"], t["cluster_id"] = end, cid
                t["scale"] = self.u(2e5, 8e5)
                t["b2c"] = [0.0] * N_MONTHS
                t["suppliers"] = []
                t["late_filer"] = self.rng.random() < 0.4
                members.append(t)
            clusters.append(dict(id=cid, members=members, start=start, end=end))
        self.b2b_sales = np.vstack([self.b2b_sales, np.zeros((len(self.taxpayers) - len(self.b2b_sales), N_MONTHS))])

        pool = self.established(["manufacturer", "wholesaler", "retailer"])
        self.rng.shuffle(pool)
        for c in clusters:
            benefs = [pool.pop() for _ in range(int(self.rng.integers(2, 5)))]
            for b in benefs:
                b["roles"].append("fake_invoice_buyer")
                b["cluster_id"] = c["id"]
                months = [m for m in range(c["start"], c["end"] + 1)]
                chosen = sorted(self.rng.choice(months, min(len(months), int(self.rng.integers(3, 7))),
                                                replace=False))
                for m in chosen:
                    base = b["scale"] * b["buy_ratio"] * self.u(0.15, 0.45)
                    for _ in range(int(self.rng.integers(1, 3))):
                        s = self.choice(c["members"])
                        v = base / 1.5 * self.u(0.6, 1.4)
                        v = self.round_value(v) if self.rng.random() < 0.6 else self.odd_value(v)
                        self.add_invoice(s, b, m, int(self.rng.integers(1, 29)), v, self.rng.random() < 0.7,
                                         eway=self.rng.random() < 0.2, fraud="fake_invoice", chain=c["id"])
                        self.b2b_sales[s["idx"], m] += v
            # layering: shells buy fake invoices from each other to cover their own output tax
            for m in range(c["start"], c["end"] + 1):
                for s in c["members"]:
                    sales = self.b2b_sales[s["idx"], m]
                    others = [o for o in c["members"] if o is not s]
                    if sales <= 0 or not others:
                        continue
                    target = sales * self.u(0.85, 1.0)
                    for _ in range(int(self.rng.integers(1, 3))):
                        o = self.choice(others)
                        v = target / 1.5 * self.u(0.6, 1.4)
                        v = self.round_value(v) if self.rng.random() < 0.5 else self.odd_value(v)
                        self.add_invoice(o, s, m, int(self.rng.integers(1, 29)), v, self.rng.random() < 0.5,
                                         eway=self.rng.random() < 0.2, fraud="fake_invoice", chain=c["id"])
        return clusters

    def inject_rings(self, n_rings):
        pool = self.established(["wholesaler", "manufacturer"])
        self.rng.shuffle(pool)
        rings = []
        for r in range(n_rings):
            rid = f"RING-{r + 1:02d}"
            members = [pool.pop() for _ in range(int(self.rng.integers(3, 6)))]
            for t in members:
                t["roles"].append("circular_trading")
                t["ring_id"] = rid
            base = self.u(3e6, 1.2e7)
            start = int(self.rng.integers(0, 5))
            end = min(N_MONTHS - 1, start + int(self.rng.integers(5, 9)))
            markup = self.u(0.005, 0.02)
            for m in range(start, end + 1):
                day = int(self.rng.integers(1, 12))
                v = base * self.u(0.9, 1.1)
                for i, s in enumerate(members):
                    b = members[(i + 1) % len(members)]
                    day += int(self.rng.integers(1, 4))
                    hop_v = v * (1 + markup) ** i
                    parts = [hop_v] if self.rng.random() < 0.6 else [hop_v * 0.55, hop_v * 0.45]
                    for p in parts:
                        val = self.round_value(p) if self.rng.random() < 0.3 else self.odd_value(p)
                        self.add_invoice(s, b, m, day, val, self.rng.random() < 0.97, eway=self.rng.random() < 0.6,
                                         fraud="circular_trading", chain=rid)
                        self.b2b_sales[s["idx"], m] += val
            rings.append(dict(id=rid, members=[t["gstin"] for t in members], start=start, end=end))
        return rings

    def inject_spikes(self, n_spikes):
        pool = self.established(list(SECTORS))
        self.rng.shuffle(pool)
        for t in pool[:n_spikes]:
            t["roles"].append("itc_spike")
            m0 = int(self.rng.integers(3, 11))
            t["spike"] = {m: self.u(2.5, 6.0) for m in range(m0, min(N_MONTHS, m0 + int(self.rng.integers(1, 3))))}

    # ---------- returns ----------
    def build_returns(self):
        n = len(self.taxpayers)
        inv_out = np.zeros((n, N_MONTHS, 2))  # taxable, tax
        itc_all = np.zeros((n, N_MONTHS))
        itc_2b = np.zeros((n, N_MONTHS))
        for inv in self.invoices:
            s, b, m = inv["_s"], inv["_b"], inv["_m"]
            inv_out[s, m, 0] += inv["taxable_value"]
            inv_out[s, m, 1] += inv["tax_amount"]
            itc_all[b, m] += inv["tax_amount"]
            if inv["seller_reported"]:
                itc_2b[b, m] += inv["tax_amount"]
        rows = []
        for t in self.taxpayers:
            i = t["idx"]
            carry = 0.0
            catchup = int(self.rng.integers(2, N_MONTHS)) if (not t["roles"] and self.rng.random() < 0.06) else -1
            for m in range(N_MONTHS):
                if not self.active(t, m):
                    continue
                b2c = t["b2c"][m] if "shell_entity" not in t["roles"] else 0.0
                outward = inv_out[i, m, 0] + b2c
                output_tax = inv_out[i, m, 1] + b2c * t["rate"] / 100
                if "shell_entity" in t["roles"]:
                    claimed = max(itc_all[i, m], output_tax * self.u(0.93, 0.99))
                else:
                    claimed = itc_all[i, m] * self.u(0.98, 1.0)
                    if m == catchup:
                        claimed += itc_all[i, m] * self.u(0.10, 0.30)
                    if m in t.get("spike", {}):
                        claimed += max(itc_all[i, m], output_tax * 0.5) * t["spike"][m]
                available = itc_2b[i, m]
                pool = claimed + carry
                cash = max(0.0, output_tax - pool)
                carry = max(0.0, pool - output_tax)
                r = self.rng.random()
                if t["late_filer"]:
                    delay = int(self.rng.integers(5, 45))
                else:
                    delay = 0 if r < 0.8 else int(self.rng.integers(1, 11)) if r < 0.97 else int(self.rng.integers(10, 30))
                rows.append(dict(gstin=t["gstin"], month=MONTHS[m], outward_taxable=round(outward, 2),
                                 b2c_taxable=round(b2c, 2), output_tax=round(output_tax, 2),
                                 itc_available_2b=round(available, 2), itc_claimed_3b=round(claimed, 2),
                                 tax_paid_cash=round(cash, 2), filing_delay_days=delay))
        return rows

    def run(self):
        n_shells = max(6, round(0.045 * self.n))
        self.build_legit(self.n - n_shells)
        clusters = self.inject_shells(n_shells)
        rings = self.inject_rings(max(2, round(self.n / 130)))
        self.inject_spikes(max(3, round(0.02 * self.n)))
        returns = self.build_returns()
        return clusters, rings, returns


def generate(seed=42, n_taxpayers=600, out_dir="data/generated"):
    g = Gen(seed, n_taxpayers)
    clusters, rings, returns = g.run()
    os.makedirs(out_dir, exist_ok=True)
    tp_cols = ["gstin", "legal_name", "constitution", "state", "sector", "registration_date", "address_id",
               "address", "contact_id", "is_fraud", "fraud_roles", "ring_id", "cluster_id"]
    with open(os.path.join(out_dir, "taxpayers.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=tp_cols)
        w.writeheader()
        for t in g.taxpayers:
            w.writerow({**{k: t[k] for k in tp_cols if k in t}, "is_fraud": int(bool(t["roles"])),
                        "fraud_roles": ";".join(t["roles"])})
    inv_cols = ["invoice_no", "invoice_date", "month", "seller_gstin", "buyer_gstin", "hsn", "taxable_value",
                "gst_rate", "tax_amount", "eway_bill", "seller_reported", "is_fraud", "fraud_type", "chain_id"]
    g.invoices.sort(key=lambda r: (r["invoice_date"], r["invoice_no"]))
    with open(os.path.join(out_dir, "invoices.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=inv_cols, extrasaction="ignore")
        w.writeheader()
        for k, r in enumerate(g.invoices):
            r["invoice_id"] = k
            w.writerow(r)
    ret_cols = list(returns[0].keys())
    with open(os.path.join(out_dir, "returns.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ret_cols)
        w.writeheader()
        w.writerows(returns)
    roles = {}
    for t in g.taxpayers:
        for r in t["roles"]:
            roles[r] = roles.get(r, 0) + 1
    meta = dict(seed=seed, n_taxpayers=len(g.taxpayers), n_invoices=len(g.invoices), n_returns=len(returns),
                months=MONTHS, fraud_taxpayers=sum(1 for t in g.taxpayers if t["roles"]), fraud_roles=roles,
                fraud_invoices=sum(r["is_fraud"] for r in g.invoices),
                shell_clusters=[dict(id=c["id"], members=[t["gstin"] for t in c["members"]]) for c in clusters],
                rings=rings, note="Synthetic sample data generated by scripts/generate_gst_data.py")
    with open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    return meta


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--taxpayers", type=int, default=600)
    ap.add_argument("--out", default="data/generated")
    a = ap.parse_args()
    m = generate(a.seed, a.taxpayers, a.out)
    print(json.dumps({k: m[k] for k in ("seed", "n_taxpayers", "n_invoices", "n_returns", "fraud_taxpayers",
                                         "fraud_roles", "fraud_invoices")}, indent=2))
