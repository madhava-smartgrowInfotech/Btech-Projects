"""Pure-Python traffic network simulator (SUMO-style system-level validation).

A grid of signalised junctions, each with four approaches (N, E, S, W) and a
two-phase signal (phase 0 = North-South green, phase 1 = East-West green).
Vehicles queue at stop lines, are discharged at saturation flow while green,
travel a link to the next junction, and finally leave the network.

Four controllers can be compared on *identical* traffic (same random demand):

* ``fixed``      - classic fixed-time signals (the "traditional" baseline).
* ``adaptive``   - queue-actuated timing (surveyed adaptive systems).
* ``emergency``  - adaptive + emergency pre-emption at ONE junction using
                   camera/light-bar range (the base paper's approach).
* ``advanced``   - this project: PCU-weighted pressure + ML queue forecast +
                   inter-junction communication (platoon look-ahead, spill-back
                   avoidance, emergency green-wave) + violation detection.
"""
from __future__ import annotations

import math
import random
import string
from collections import defaultdict, deque

import numpy as np

APPROACHES = ("N", "E", "S", "W")
AIDX = {a: i for i, a in enumerate(APPROACHES)}
PHASE_OF = {"N": 0, "S": 0, "E": 1, "W": 1}
PHASE_NAME = {0: "North-South", 1: "East-West"}
PCU = {"car": 1.0, "bike": 0.5, "bus": 3.0, "truck": 2.0, "ambulance": 1.0}
VTYPES = ["car", "bike", "bus", "truck"]
VPROB = [0.68, 0.13, 0.06, 0.13]

LINK_TIME = 12        # seconds to travel between junctions
CAP = 30              # vehicles that fit on an approach (spill-back limit)
SAT = 0.5             # saturation discharge rate (veh / s / lane)
STARTUP = 2           # start-up lost time after a green begins
CLEAR = 3             # yellow + all-red clearance
FIXED_GREEN = 30
MIN_GREEN = 15
MAX_GREEN = 60

CONTROLLERS = {
    "fixed": "Fixed-time (traditional)",
    "adaptive": "Adaptive (queue-actuated)",
    "emergency": "Emergency-aware adaptive (base paper)",
    "advanced": "Advanced coordinated AI (this project)",
}

# (d_row, d_col, receiving approach) for each way a vehicle can leave an approach
STRAIGHT = {"N": (1, 0, "N"), "S": (-1, 0, "S"), "W": (0, 1, "W"), "E": (0, -1, "E")}
TURNS = {
    "N": [(0, 1, "W"), (0, -1, "E")],
    "S": [(0, -1, "E"), (0, 1, "W")],
    "W": [(-1, 0, "S"), (1, 0, "N")],
    "E": [(1, 0, "N"), (-1, 0, "S")],
}
BASE_RATE = {"N": 0.15, "S": 0.15, "E": 0.10, "W": 0.10}  # veh/s per entry road
STATES = ["TS", "AP", "KA", "MH", "TN"]


def demand_profile(hour: float) -> float:
    """Morning and evening rush-hour multiplier."""
    return (0.7 + 0.5 * math.exp(-((hour - 8.5) / 0.9) ** 2)
            + 0.55 * math.exp(-((hour - 17.5) / 1.1) ** 2))


class Vehicle:
    __slots__ = ("id", "vtype", "t0", "wait", "emg", "red_runner", "u", "hop", "plate")

    def __init__(self, vid, vtype, t0, emg, red_runner, u, plate):
        self.id, self.vtype, self.t0 = vid, vtype, t0
        self.wait, self.emg, self.red_runner = 0, emg, red_runner
        self.u, self.hop, self.plate = u, 0, plate


class Sim:
    def __init__(self, rows=2, cols=2, controller="advanced", demand=1.0, seed=0,
                 start_hour=8.0, predictor=None, emergencies=True, emg_rate=1 / 150,
                 violations=True):
        self.rows, self.cols, self.n = rows, cols, rows * cols
        self.controller, self.demand, self.start_hour = controller, demand, start_hour
        self.predictor, self.emergencies, self.emg_rate = predictor, emergencies, emg_rate
        self.violations = violations
        self.arr_rng = np.random.default_rng(seed)       # demand (controller independent)
        self.aux_rng = random.Random(seed + 991)          # plates, confidences
        self.t = 0
        self._vid = 0
        self.q = [[deque() for _ in APPROACHES] for _ in range(self.n)]
        self.phase = [0] * self.n
        self.timer = [0] * self.n
        self.clear = [0] * self.n
        self.nxt = [0] * self.n
        self.credit = [[0.0] * 4 for _ in range(self.n)]
        self.transit = defaultdict(list)                  # arrive_t -> [(veh, j, a, depart_t, src)]
        self.entries = []
        for r in range(rows):
            for c in range(cols):
                j = r * cols + c
                for a in APPROACHES:
                    dr, dc, _ = STRAIGHT[a]
                    # approach `a` is fed from outside if the upstream cell is off-grid
                    if not (0 <= r - dr < rows and 0 <= c - dc < cols):
                        self.entries.append((j, AIDX[a]))
        self.pred = np.zeros((self.n, 4))
        self._inbound = np.zeros((self.n, 4))
        self._emg_in = {}
        self.qhist, self.arrhist = [], []
        self.qtot, self.phases_log = [], []
        self.done_delays, self.emg_log, self.viol_log = [], [], []
        self.active_emg = {}
        self.spawned = 0
        self.preemptions = 0
        self._preempt_active = [False] * self.n

    # ------------------------------------------------------------------ helpers
    def jrc(self, j):
        return divmod(j, self.cols)

    def hour(self):
        return (self.start_hour + self.t / 3600.0) % 24

    def wq(self, j, a):
        return sum(PCU[v.vtype] for v in self.q[j][a])

    def _next_hop(self, v, j, a):
        """Return (next_junction, next_approach) or None if the vehicle leaves."""
        name = APPROACHES[a]
        u = v.u[v.hop % len(v.u)]
        if v.emg or u < 0.78:
            dr, dc, na = STRAIGHT[name]
        else:
            dr, dc, na = TURNS[name][0 if u < 0.89 else 1]
        r, c = self.jrc(j)
        nr, nc = r + dr, c + dc
        if 0 <= nr < self.rows and 0 <= nc < self.cols:
            return nr * self.cols + nc, AIDX[na]
        return None

    def _new_vehicle(self, emg=False):
        self._vid += 1
        rng = self.arr_rng
        vt = "ambulance" if emg else VTYPES[int(rng.choice(4, p=VPROB))]
        red_runner = (not emg) and rng.random() < 0.05
        u = [float(x) for x in rng.random(10)]
        plate = "%s%02d%s%04d" % (
            STATES[int(rng.integers(len(STATES)))], int(rng.integers(1, 40)),
            "".join(string.ascii_uppercase[int(x)] for x in rng.integers(0, 26, 2)),
            int(rng.integers(1000, 9999)))
        return Vehicle(self._vid, vt, self.t, emg, red_runner, u, plate)

    def _log_violation(self, kind, j, a, v):
        conf = 0.86 + 0.13 * self.aux_rng.random()
        self.viol_log.append(dict(t=self.t, junction=j, approach=APPROACHES[a], kind=kind,
                                  plate=v.plate, vehicle=v.vtype, confidence=round(conf, 2)))

    # ---------------------------------------------------------------- simulation
    def step(self):
        self._arrivals()
        self._transit_arrivals()
        self._signals()
        self._discharge()
        self._record()
        self.t += 1

    def run(self, seconds):
        for _ in range(int(seconds)):
            self.step()
        return self

    def _arrivals(self):
        mult = self.demand * demand_profile(self.hour())
        arr = np.zeros((self.n, 4))
        for j, a in self.entries:
            lam = BASE_RATE[APPROACHES[a]] * mult
            for _ in range(int(self.arr_rng.poisson(lam))):
                v = self._new_vehicle()
                self.q[j][a].append(v)
                arr[j, a] += 1
            if self.violations and self.arr_rng.random() < 0.0003:   # wrong-way driver
                v = self._new_vehicle()
                self._log_violation("Wrong-way driving", j, a, v)
        self._arr_now = arr
        # emergency vehicle enters at a random entry road
        e_roll, e_pick = self.arr_rng.random(), int(self.arr_rng.integers(len(self.entries)))
        if self.emergencies and e_roll < self.emg_rate:
            j, a = self.entries[e_pick]
            v = self._new_vehicle(emg=True)
            self.q[j][a].append(v)
            self.active_emg[v.id] = v
            self.spawned += 1
            arr[j, a] += 1

    def _transit_arrivals(self):
        for v, j, a, _dep, _src in self.transit.pop(self.t, []):
            self.q[j][a].append(v)
            self._arr_now[j, a] += 1

    # ----------------------------------------------------------------- signals
    def _scan_upstream(self, lookahead_pcu, lookahead_emg):
        self._inbound[:] = 0
        self._emg_in = {}
        for dt in range(1, max(lookahead_pcu, lookahead_emg) + 1):
            for v, j, a, _d, _s in self.transit.get(self.t + dt, ()):
                if dt <= lookahead_pcu:
                    self._inbound[j, a] += PCU[v.vtype]
                if v.emg and dt <= lookahead_emg:
                    self._emg_in[(j, a)] = min(dt, self._emg_in.get((j, a), 99))

    def _signals(self):
        ctrl = self.controller
        if ctrl == "advanced":
            self._scan_upstream(8, 15)
            if self.t % 10 == 0 and self.predictor is not None and self.t >= 30:
                self.pred = self.predictor.predict(self.feature_matrix()).reshape(self.n, 4)
        elif ctrl == "emergency":
            self._scan_upstream(0, 5)
        for j in range(self.n):
            if self.clear[j] > 0:
                self.clear[j] -= 1
                if self.clear[j] == 0:
                    self.phase[j], self.timer[j] = self.nxt[j], 0
                continue
            self.timer[j] += 1
            want = self._decide(j)
            if want != self.phase[j]:
                self.clear[j], self.nxt[j] = CLEAR, want

    def _decide(self, j):
        ph, tm, ctrl = self.phase[j], self.timer[j], self.controller
        if ctrl == "fixed":
            return 1 - ph if tm >= FIXED_GREEN else ph
        if ctrl in ("emergency", "advanced"):
            target = self._emergency_target(j)
            if target is not None:
                if target != ph and tm >= 2:
                    self.preemptions += 0 if self._preempt_active[j] else 1
                    self._preempt_active[j] = True
                    return target
                self._preempt_active[j] = target == ph
                return ph
            self._preempt_active[j] = False
        adv = ctrl == "advanced"
        cur, oth = self._pressure(j, ph, adv), self._pressure(j, 1 - ph, adv)
        min_g, max_g = (13, 60) if adv else (MIN_GREEN, MAX_GREEN)
        if tm < min_g:
            return ph
        if tm >= max_g:
            return 1 - ph if oth > 0 else ph
        if cur <= 0.01 and oth > 0:
            return 1 - ph
        if oth > 2.0 * cur + 4:
            return 1 - ph
        return ph

    def _emergency_target(self, j):
        best_dt, best_ph = 99, None
        for a in range(4):
            if any(v.emg for v in self.q[j][a]):
                dt = 0
            else:
                dt = self._emg_in.get((j, a), 99)
            if dt < best_dt:
                best_dt, best_ph = dt, PHASE_OF[APPROACHES[a]]
        return best_ph

    def _pressure(self, j, phase, adv):
        total = 0.0
        for a, name in enumerate(APPROACHES):
            if PHASE_OF[name] != phase:
                continue
            qq = self.q[j][a]
            w = self.wq(j, a)
            if adv:
                w += 0.7 * max(float(self.pred[j, a]) - len(qq), 0.0)     # ML forecast
                w += float(self._inbound[j, a])                           # arriving platoon
                if qq:
                    w += qq[0].wait / 12.0                                # fairness
                nh = self._next_hop_of_straight(j, a)
                if nh is not None and len(self.q[nh[0]][nh[1]]) >= CAP - 4:
                    w *= 0.3                                              # downstream full
            total += w
        return total

    def _next_hop_of_straight(self, j, a):
        dr, dc, na = STRAIGHT[APPROACHES[a]]
        r, c = self.jrc(j)
        nr, nc = r + dr, c + dc
        if 0 <= nr < self.rows and 0 <= nc < self.cols:
            return nr * self.cols + nc, AIDX[na]
        return None

    # --------------------------------------------------------------- discharge
    def _release(self, v, j, a):
        nh = self._next_hop(v, j, a)
        if nh is not None:
            nj, na = nh
            if len(self.q[nj][na]) >= CAP:
                return False                           # spill-back: cannot enter
            v.hop += 1
            self.transit[self.t + LINK_TIME].append((v, nj, na, self.t, j))
            return True
        v.hop += 1
        self.done_delays.append(v.wait)
        if v.emg:
            self.emg_log.append(dict(id=v.id, delay=v.wait, travel=self.t - v.t0))
            self.active_emg.pop(v.id, None)
        return True

    def _discharge(self):
        for j in range(self.n):
            if self.clear[j] > 0:
                continue
            ph, tm = self.phase[j], self.timer[j]
            for a, name in enumerate(APPROACHES):
                qq = self.q[j][a]
                if not qq:
                    self.credit[j][a] = min(self.credit[j][a], 0.9)
                    continue
                if PHASE_OF[name] == ph:
                    if tm <= STARTUP:
                        continue
                    for i, v in enumerate(qq):            # sirens clear the lane
                        if v.emg:
                            if i:
                                del qq[i]
                                qq.appendleft(v)
                            break
                    self.credit[j][a] += SAT
                    while self.credit[j][a] >= 1 and qq:
                        if not self._release(qq[0], j, a):
                            break
                        qq.popleft()
                        self.credit[j][a] -= 1
                else:
                    self.credit[j][a] = 0.0
                    v = qq[0]
                    if self.violations and v.red_runner and v.wait >= 25 and not v.emg:
                        if self._release(v, j, a):
                            qq.popleft()
                            self._log_violation("Red-light jumping", j, a, v)

    def _record(self):
        qs = np.zeros((self.n, 4))
        for j in range(self.n):
            for a in range(4):
                qq = self.q[j][a]
                qs[j, a] = len(qq)
                for v in qq:
                    v.wait += 1
        self.qhist.append(qs)
        self.arrhist.append(self._arr_now)
        self.qtot.append(float(qs.sum()))
        self.phases_log.append(list(self.phase))

    # ----------------------------------------------------------- ML features
    FEATURES = ["queue", "pcu_queue", "queue_lag10", "queue_lag30", "inflow_30s",
                "inbound_15s", "is_green", "green_time", "is_entry", "sin_day", "cos_day"]

    def feature_matrix(self):
        t = len(self.qhist)
        cur = self.qhist[-1]
        lag10 = self.qhist[max(t - 11, 0)]
        lag30 = self.qhist[max(t - 31, 0)]
        inflow = np.sum(self.arrhist[-30:], axis=0)
        inbound = np.zeros((self.n, 4))
        for dt in range(1, 16):
            for _v, j, a, _d, _s in self.transit.get(self.t + dt, ()):
                inbound[j, a] += 1
        ang = 2 * math.pi * self.hour() / 24
        entry = set(self.entries)
        rows = []
        for j in range(self.n):
            for a, name in enumerate(APPROACHES):
                green = float(PHASE_OF[name] == self.phase[j] and self.clear[j] == 0)
                rows.append([cur[j, a], self.wq(j, a), lag10[j, a], lag30[j, a], inflow[j, a],
                             inbound[j, a], green, self.timer[j], float((j, a) in entry),
                             math.sin(ang), math.cos(ang)])
        return np.array(rows, dtype=float)

    # ------------------------------------------------------------------ results
    def summary(self):
        idle = float(sum(self.qtot))
        fuel = idle * 0.6 / 3600.0
        emg = [e["delay"] for e in self.emg_log]
        red = sum(1 for x in self.viol_log if x["kind"] == "Red-light jumping")
        return {
            "Avg delay / vehicle (s)": float(np.mean(self.done_delays)) if self.done_delays else 0.0,
            "Avg queue (veh)": float(np.mean(self.qtot)) if self.qtot else 0.0,
            "Max approach queue": float(max((q.max() for q in self.qhist), default=0)),
            "Throughput (veh)": len(self.done_delays),
            "Emergency delay (s)": float(np.mean(emg)) if emg else 0.0,
            "Emergency max (s)": float(max(emg)) if emg else 0.0,
            "Emergency served": len(emg),
            "Red-light violations": red,
            "Wrong-way violations": len(self.viol_log) - red,
            "Fuel wasted idling (L)": fuel,
            "CO2 (kg)": fuel * 2.31,
        }

    def in_network(self):
        return sum(len(q) for row in self.q for q in row) + sum(len(x) for x in self.transit.values())


def run_benchmark(rows, cols, seconds, demand, seeds, controllers, predictor, start_hour=8.0):
    out = {}
    for c in controllers:
        runs = []
        for s in seeds:
            sim = Sim(rows, cols, c, demand, seed=s, start_hour=start_hour, predictor=predictor)
            sim.run(seconds)
            runs.append(sim)
        out[c] = runs
    return out
