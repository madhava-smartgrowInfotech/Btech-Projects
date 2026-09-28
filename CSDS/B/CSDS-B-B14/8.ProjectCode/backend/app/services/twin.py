"""Digital twin of the city distribution network, built and simulated with WNTR (EPANET engine).

The network is a looped grid of 48 junctions in 5 zones, fed by a treatment-plant reservoir through a
pump, with an elevated service tank. Demands are pressure-driven (PDD) and every junction carries a
small background-leakage emitter so non-revenue water responds to pressure like a real system.
"""
import copy
import json
import math
import tempfile
import threading
import uuid
from pathlib import Path

import numpy as np
import wntr

from ..config import CITY_LAT, CITY_LON, DATA

NET_DIR = DATA / "network"
INP_PATH = NET_DIR / "city.inp"
LAYOUT_PATH = NET_DIR / "layout.json"

ROWS, COLS, SPACING = 6, 8, 500.0  # grid of junctions, metres between them
ZONES = ["Z1", "Z2", "Z3", "Z4", "Z5"]
ZONE_NAMES = {"Z1": "Zone 1 - Old City West", "Z2": "Zone 2 - Central", "Z3": "Zone 3 - East Hills",
              "Z4": "Zone 4 - South West", "Z5": "Zone 5 - South Central"}
# average billed consumption per zone (m3/day); the consumption history generator uses the same values
ZONE_BASE_M3_DAY = {"Z1": 2300.0, "Z2": 2500.0, "Z3": 3100.0, "Z4": 1900.0, "Z5": 2200.0}
# hourly demand multipliers (mean = 1)
DIURNAL = [0.45, 0.4, 0.38, 0.38, 0.45, 0.75, 1.3, 1.75, 1.7, 1.4, 1.15, 1.05,
           1.0, 0.95, 0.9, 0.95, 1.1, 1.35, 1.6, 1.55, 1.3, 1.0, 0.75, 0.55]
_m = sum(DIURNAL) / 24
DIURNAL = [round(v / _m, 4) for v in DIURNAL]
BG_LEAK_FRACTION = 0.10       # background leakage ~10% of average demand at ~35 m pressure
REQUIRED_PRESSURE = 20.0      # m, full service
MINIMUM_PRESSURE = 3.0        # m, no service
NIGHT_HOUR = 3                # minimum-night-flow analysis window
SENSORS = ["J01", "J04", "J07", "J12", "J15", "J21", "J26", "J27", "J32", "J35",
           "J37", "J41", "J44", "J52", "J55", "J57"]

_lock = threading.Lock()
_tmp = Path(tempfile.gettempdir()) / "aquavision_sim"
_tmp.mkdir(exist_ok=True)


def zone_of(r, c):
    if c >= 6:
        return "Z3"
    if r <= 2:
        return "Z1" if c <= 2 else "Z2"
    return "Z4" if c <= 2 else "Z5"


def build_network(seed=7):
    """Build the twin from scratch (used by scripts/generate_network.py)."""
    rng = np.random.default_rng(seed)
    wn = wntr.network.WaterNetworkModel()
    wn.add_pattern("diurnal", DIURNAL)
    zones = {}
    zone_nodes = {z: [(r, c) for r in range(ROWS) for c in range(COLS) if zone_of(r, c) == z] for z in ZONES}
    for r in range(ROWS):
        for c in range(COLS):
            z = zone_of(r, c)
            name = f"J{r}{c}"
            share = ZONE_BASE_M3_DAY[z] / len(zone_nodes[z])
            base = share * rng.uniform(0.7, 1.3) / 86400.0  # m3/s
            elev = 4.0 + 2.2 * c + 1.2 * r + (9.0 if c >= 6 else 0.0) + rng.uniform(-1, 1)
            wn.add_junction(name, base_demand=base, demand_pattern="diurnal", elevation=round(elev, 2),
                            coordinates=(c * SPACING, (ROWS - 1 - r) * SPACING))
            zones[name] = z
    wn.add_reservoir("PLANT", base_head=12.0, coordinates=(-1.6 * SPACING, 2.5 * SPACING))
    wn.add_junction("PLANT_OUT", base_demand=0.0, elevation=2.0, coordinates=(-1.0 * SPACING, 2.5 * SPACING))
    wn.add_curve("PUMP_CURVE", "HEAD", [(0.16, 47.0)])
    wn.add_pump("PUMP1", "PLANT", "PLANT_OUT", pump_type="HEAD", pump_parameter="PUMP_CURVE")
    wn.add_tank("TANK1", elevation=48.0, init_level=3.0, min_level=0.5, max_level=6.0, diameter=28.0,
                coordinates=(3.5 * SPACING, (ROWS + 0.6) * SPACING))
    links = []

    def pipe(a, b, d, length=SPACING):
        name = f"P{len(links) + 1:02d}"
        wn.add_pipe(name, a, b, length=length, diameter=d, roughness=110, minor_loss=0.0)
        links.append(name)

    pipe("PLANT_OUT", "J20", 0.45, 600)
    pipe("PLANT_OUT", "J30", 0.45, 600)
    pipe("TANK1", "J03", 0.35, 400)
    for r in range(ROWS):
        for c in range(COLS - 1):
            d = 0.35 if r in (2, 3) else 0.2
            pipe(f"J{r}{c}", f"J{r}{c + 1}", d)
    for r in range(ROWS - 1):
        for c in range(COLS):
            d = 0.3 if c in (0, 3) else 0.15
            pipe(f"J{r}{c}", f"J{r + 1}{c}", d)
    opts = wn.options
    opts.time.duration = 24 * 3600
    opts.time.hydraulic_timestep = 3600
    opts.time.pattern_timestep = 3600
    opts.time.report_timestep = 3600
    opts.hydraulic.demand_model = "PDD"
    opts.hydraulic.required_pressure = REQUIRED_PRESSURE
    opts.hydraulic.minimum_pressure = MINIMUM_PRESSURE
    opts.hydraulic.pressure_exponent = 0.5
    opts.hydraulic.emitter_exponent = 0.5
    # background leakage emitters: q = C * sqrt(p)
    for name, z in zones.items():
        j = wn.get_node(name)
        avg = j.demand_timeseries_list[0].base_value
        j.emitter_coefficient = BG_LEAK_FRACTION * avg / math.sqrt(35.0)
    return wn, zones


def to_latlon(x, y):
    lat0, lon0 = CITY_LAT - 0.006, CITY_LON - 0.018
    return lat0 + y / 111320.0, lon0 + x / (111320.0 * math.cos(math.radians(CITY_LAT)))


def save_network(wn, zones):
    NET_DIR.mkdir(parents=True, exist_ok=True)
    wntr.network.write_inpfile(wn, str(INP_PATH), units="CMH")
    layout = {"zones": zones, "sensors": SENSORS}
    pipe_zone = {}
    for name, link in wn.links():
        a, b = link.start_node_name, link.end_node_name
        pipe_zone[name] = zones.get(a) or zones.get(b) or "SRC"
    layout["pipe_zone"] = pipe_zone
    LAYOUT_PATH.write_text(json.dumps(layout, indent=1))


_base = None
_layout = None


def base_network():
    global _base, _layout
    if _base is None:
        wn = wntr.network.WaterNetworkModel(str(INP_PATH))
        # INP round trip keeps PDD settings; make sure they are set
        wn.options.hydraulic.demand_model = "PDD"
        wn.options.hydraulic.required_pressure = REQUIRED_PRESSURE
        wn.options.hydraulic.minimum_pressure = MINIMUM_PRESSURE
        _base = wn
        _layout = json.loads(LAYOUT_PATH.read_text())
    return _base


def layout():
    base_network()
    return _layout


def zones_map():
    return layout()["zones"]


def pipe_zone():
    return layout()["pipe_zone"]


def candidate_pipes():
    """Distribution pipes where a leak can be injected/located (trunk mains from plant and tank excluded)."""
    return [p for p, z in pipe_zone().items() if z in ZONES and p not in ("P01", "P02", "P03")]


def copy_network():
    return copy.deepcopy(base_network())


def add_leak(wn, pipe, leak_lps, ref_pressure=35.0):
    """Split `pipe` at its midpoint and attach an emitter that discharges ~leak_lps at ref pressure."""
    node = f"LEAK_{pipe}"
    wntr.morph.split_pipe(wn, pipe, f"{pipe}_B", node, split_at_point=0.5, return_copy=False)
    a = wn.get_link(pipe).start_node
    b = wn.get_link(f"{pipe}_B").end_node
    j = wn.get_node(node)
    j.elevation = (a.elevation + b.elevation) / 2 if hasattr(b, "elevation") and hasattr(a, "elevation") else j.elevation
    j.emitter_coefficient = (leak_lps / 1000.0) / math.sqrt(ref_pressure)
    return node


def run(wn, snapshot_hour=None):
    """Run EPANET. snapshot_hour -> single steady state at that hour, else 24h extended period."""
    if snapshot_hour is not None:
        wn.options.time.duration = 0
        wn.options.time.pattern_start = snapshot_hour * 3600
    prefix = str(_tmp / uuid.uuid4().hex[:10])
    with _lock:
        res = wntr.sim.EpanetSimulator(wn).run_sim(file_prefix=prefix)
    for ext in (".inp", ".rpt", ".bin"):
        try:
            Path(prefix + ext).unlink()
        except OSError:
            pass
    return res


def scale_demands(wn, factors):
    """factors: dict junction -> multiplier on its base demand."""
    for name, f in factors.items():
        j = wn.get_node(name)
        ts = j.demand_timeseries_list[0]
        ts.base_value = ts.base_value * f


def emitter_flow(wn, pressure):
    """Emitter (leakage) outflow per node in m3/s given a pressure Series/DataFrame."""
    out = {}
    for name, j in wn.junctions():
        c = j.emitter_coefficient or 0.0
        if c > 0 and name in pressure:
            out[name] = c * np.sqrt(np.clip(pressure[name], 0, None))
    return out


def summarize_eps(wn, res, zones=None):
    """Per-zone and system KPIs from a 24h extended-period run (hours 0-23)."""
    zones = zones or dict(zones_map())
    for name in wn.junction_name_list:
        if name.startswith("LEAK_"):
            zones[name] = pipe_zone()[name[5:]]
    p = res.node["pressure"].iloc[:24]
    d = res.node["demand"].iloc[:24]
    em = emitter_flow(wn, p)
    mult = np.array([DIURNAL[int(t // 3600) % 24] for t in d.index])
    dt = 3600.0
    per_zone = {}
    for z in ZONES:
        nodes = [n for n, zz in zones.items() if zz == z]
        consumer = [n for n in nodes if not n.startswith("LEAK_")]
        req = float(sum(wn.get_node(n).demand_timeseries_list[0].base_value * mult.sum() for n in consumer)) * dt
        inflow = float(sum(d[n].clip(lower=0).sum() for n in nodes)) * dt
        leak = float(sum(np.asarray(em[n]).sum() for n in nodes if n in em)) * dt
        delivered = inflow - leak
        zp = p[consumer]
        per_zone[z] = {
            "zone": z, "name": ZONE_NAMES[z],
            "demand_m3": round(req, 1),
            "delivered_m3": round(delivered, 1),
            "supply_m3": round(inflow, 1),
            "losses_m3": round(leak, 1),
            "service_ratio": round(delivered / req, 4) if req else 1.0,
            "pressure_adequacy": round(float((zp.values >= REQUIRED_PRESSURE).mean()), 4),
            "avg_pressure": round(float(zp.values.mean()), 2),
            "min_pressure": round(float(zp.values.min()), 2),
            "low_pressure_hours": int((zp.min(axis=1) < REQUIRED_PRESSURE).sum()),
        }
    supply = sum(v["supply_m3"] for v in per_zone.values())
    delivered = sum(v["delivered_m3"] for v in per_zone.values())
    demand = sum(v["demand_m3"] for v in per_zone.values())
    # equity: service level (pressure adequacy x delivered share) of worst zone relative to best zone
    service = [v["pressure_adequacy"] * min(1.0, v["service_ratio"]) for v in per_zone.values()]
    equity = 100.0 * min(service) / max(service) if max(service) > 0 else 0.0
    junc = [n for n in zones if not n.startswith("LEAK_")]
    pump_flow = res.link["flowrate"]["PUMP1"].iloc[:24]
    return {
        "zones": per_zone,
        "system_input_m3": round(supply, 1),
        "billed_m3": round(delivered, 1),
        "demand_m3": round(demand, 1),
        "nrw_pct": round(100 * (supply - delivered) / supply, 2) if supply else 0.0,
        "avg_pressure": round(float(p[junc].values.mean()), 2),
        "min_pressure": round(float(p[junc].values.min()), 2),
        "equity_score": round(equity, 1),
        "pump_m3": round(float(pump_flow.clip(lower=0).sum() * dt), 1),
        "tank_level": [round(float(v), 2) for v in res.node["pressure"]["TANK1"].iloc[:24].values],
        "hourly_pressure": [round(float(v), 2) for v in p[junc].mean(axis=1).values],
        "hourly_supply_lps": [round(float(v) * 1000, 2) for v in d[list(zones)].clip(lower=0).sum(axis=1).values],
    }


def sensor_readings(wn, res, zones=None):
    """Logger readings from a snapshot: pressure at sensor nodes and DMA inflow per zone (L/s)."""
    zones = zones or dict(zones_map())
    for name in wn.junction_name_list:
        if name.startswith("LEAK_"):
            zones[name] = pipe_zone()[name[5:]]
    p = res.node["pressure"].iloc[0]
    d = res.node["demand"].iloc[0]
    vals = [float(p[s]) for s in SENSORS]
    for z in ZONES:
        vals.append(1000.0 * float(sum(max(d[n], 0) for n, zz in zones.items() if zz == z)))
    return np.array(vals)


FEATURES = [f"p_{s}" for s in SENSORS] + [f"q_{z}" for z in ZONES]
NOISE_STD = np.array([0.05] * len(SENSORS) + [0.35] * len(ZONES))


def observe(pipe=None, leak_lps=0.0, rng=None, demand_sigma=0.03):
    """Simulate what the field loggers would report at the night window, optionally with a leak."""
    rng = rng or np.random.default_rng()
    wn = copy_network()
    zones = zones_map()
    zf = {z: rng.normal(1.0, demand_sigma) for z in ZONES}
    scale_demands(wn, {n: zf[zones[n]] * rng.normal(1.0, 0.04) for n in zones})
    if pipe:
        add_leak(wn, pipe, leak_lps)
    res = run(wn, snapshot_hour=NIGHT_HOUR)
    return sensor_readings(wn, res) + rng.normal(0, 1, len(NOISE_STD)) * NOISE_STD


_baseline = None


def baseline_readings():
    """What the twin expects the loggers to read with no new leak (forecast demands)."""
    global _baseline
    if _baseline is None:
        wn = copy_network()
        _baseline = sensor_readings(wn, run(wn, snapshot_hour=NIGHT_HOUR))
    return _baseline


def residuals(observed):
    return observed - baseline_readings()


def simulate_state(leaks=(), pump_speed=1.0, throttle=None):
    """24h run of the twin with active leaks [(pipe, lps)], pump speed and optional zone-inlet throttling."""
    wn = copy_network()
    for pipe, lps in leaks:
        add_leak(wn, pipe, lps)
    wn.get_link("PUMP1").base_speed = pump_speed
    if throttle:
        for pipe_name, k in throttle.items():
            wn.get_link(pipe_name).minor_loss = k
    res = run(wn)
    return wn, res


def network_geo(res=None, wn=None):
    """Nodes and links with lat/lon for the map, plus latest simulated pressures/flows if given."""
    wn = wn or base_network()
    zones = zones_map()
    pz = pipe_zone()
    nodes = []
    peak = 8  # 08:00 report
    pr = res.node["pressure"].iloc[peak] if res is not None else None
    for name, n in wn.nodes():
        if name.startswith("LEAK_"):
            continue
        lat, lon = to_latlon(*n.coordinates)
        nodes.append({
            "id": name, "type": n.node_type, "lat": lat, "lon": lon,
            "zone": zones.get(name, "SRC"), "sensor": name in SENSORS,
            "elevation": round(getattr(n, "elevation", 0) or 0, 1),
            "pressure": round(float(pr[name]), 2) if pr is not None else None,
        })
    links = []
    fl = res.link["flowrate"].iloc[peak] if res is not None else None
    base = base_network()
    for name, l in base.links():
        a, b = base.get_node(l.start_node_name), base.get_node(l.end_node_name)
        f = None
        if fl is not None:
            f = float(fl[name]) if name in fl else None
        links.append({
            "id": name, "type": l.link_type, "from": l.start_node_name, "to": l.end_node_name,
            "zone": pz.get(name, "SRC"),
            "diameter_mm": round(getattr(l, "diameter", 0) * 1000) if l.link_type == "Pipe" else None,
            "length_m": round(getattr(l, "length", 0)) if l.link_type == "Pipe" else None,
            "coords": [list(to_latlon(*a.coordinates)), list(to_latlon(*b.coordinates))],
            "flow_lps": round(f * 1000, 2) if f is not None else None,
        })
    return {"nodes": nodes, "links": links, "zones": [{"id": z, "name": ZONE_NAMES[z]} for z in ZONES],
            "sensors": SENSORS}
