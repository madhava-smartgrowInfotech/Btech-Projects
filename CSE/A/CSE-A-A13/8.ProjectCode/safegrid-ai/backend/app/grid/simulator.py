"""GridSimulator: owns the pandapower net and node states. The only place the net is mutated.

trial()  -> evaluate a hypothetical set of setpoints, leave the committed state untouched
commit() -> apply validated setpoints, run power flow, integrate battery energy, cache a snapshot
"""
from __future__ import annotations

import math
import threading
from typing import Any

from app.grid import power_flow as pf
from app.grid.network import LINES, NetworkSpec, create_network
from app.grid.state import NodeState
from app.safety.models import GridTrial, Setpoint

ZERO = Setpoint()


class GridSimulator:
    def __init__(self, spec: NetworkSpec | None = None):
        self.spec = spec or NetworkSpec()
        self.net, self.emap = create_network(self.spec)
        self.nodes: dict[str, NodeState] = {
            n.node_id: NodeState(n, n.initial_soc, n.base_load_kw, 0.0, n.base_load_kw) for n in self.spec.nodes}
        self._tan = ((1.0 / self.spec.load_power_factor**2) - 1.0) ** 0.5
        self._committed: dict[str, Setpoint] = {}
        self._snapshot: dict[str, Any] = {}
        self.price = 0.0
        self._lock = threading.RLock()  # the net is shared between the worker thread and API dry-runs

    # ---- exogenous inputs -------------------------------------------------------
    def apply_exogenous(self, load_kw: dict[str, float], pv_kw: dict[str, float], price: float,
                        storage_available: dict[str, bool] | None = None) -> None:
        with self._lock:
            self._apply_exogenous(load_kw, pv_kw, price, storage_available)

    def _apply_exogenous(self, load_kw, pv_kw, price, storage_available) -> None:
        for nid, ns in self.nodes.items():
            ns.base_load_kw = float(load_kw.get(nid, ns.spec.base_load_kw))
            ns.rebound_kw = min(ns.deferred_kwh / max(self._dt_h_hint, 1e-9), 0.5 * ns.base_load_kw) if ns.deferred_kwh > 0 else 0.0
            ns.load_kw = ns.base_load_kw + ns.rebound_kw
            ns.pv_kw = float(pv_kw.get(nid, 0.0))
            if storage_available is not None:
                ns.storage_available = bool(storage_available.get(nid, True))
        self.price = float(price)

    _dt_h_hint = 0.25

    def set_dt(self, dt_minutes: int) -> None:
        self._dt_h_hint = dt_minutes / 60.0

    # ---- writing setpoints into the net -----------------------------------------------
    def _write(self, setpoints: dict[str, Setpoint]) -> None:
        net, e = self.net, self.emap
        for nid, ns in self.nodes.items():
            sp = setpoints.get(nid, ZERO)
            load = max(0.0, ns.load_kw - sp.shift_kw)
            pv = max(0.0, ns.pv_kw - sp.curtail_kw)
            s = sp.storage_kw if ns.storage_available else 0.0
            net.load.at[e.load_idx[nid], "p_mw"] = load / 1000.0
            net.load.at[e.load_idx[nid], "q_mvar"] = load / 1000.0 * self._tan
            net.sgen.at[e.sgen_idx[nid], "p_mw"] = pv / 1000.0
            net.storage.at[e.storage_idx[nid], "p_mw"] = s / 1000.0

    def trial(self, setpoints: dict[str, Setpoint]) -> GridTrial:
        """Hypothetical power flow. Restores the committed state afterwards."""
        with self._lock:
            try:
                self._write(setpoints)
                ok = pf.run_power_flow(self.net)
                return pf.build_trial(self.net, ok, self.emap)
            finally:
                self._write(self._committed)

    # ---- commit -----------------------------------------------------------------------------
    def commit(self, setpoints: dict[str, Setpoint], dt_minutes: int) -> tuple[GridTrial, dict[str, float]]:
        with self._lock:
            return self._commit(setpoints, dt_minutes)

    def _commit(self, setpoints: dict[str, Setpoint], dt_minutes: int) -> tuple[GridTrial, dict[str, float]]:
        """Apply validated setpoints for one step. Returns the power-flow result and step energy stats."""
        dt_h = dt_minutes / 60.0
        self._committed = {k: v for k, v in setpoints.items()}
        self._write(self._committed)
        ok = pf.run_power_flow(self.net)
        trial = pf.build_trial(self.net, ok, self.emap)
        stats = {"charged_kwh": 0.0, "discharged_kwh": 0.0, "curtailed_kwh": 0.0, "pv_available_kwh": 0.0, "shifted_kwh": 0.0}
        for nid, ns in self.nodes.items():
            sp = setpoints.get(nid, ZERO)
            lim = ns.spec.limits
            s = sp.storage_kw if ns.storage_available else 0.0
            cap = lim.storage_capacity_kwh
            if dt_h > 0 and cap > 0 and abs(s) > 0:
                if s > 0:
                    ns.soc += s * dt_h * lim.charge_eff / cap
                    stats["charged_kwh"] += s * dt_h
                else:
                    ns.soc += s * dt_h / lim.discharge_eff / cap
                    stats["discharged_kwh"] += -s * dt_h
                ns.soc = min(1.0, max(0.0, ns.soc))
                self.net.storage.at[self.emap.storage_idx[nid], "soc_percent"] = ns.soc * 100.0
            if dt_h > 0:
                stats["curtailed_kwh"] += min(sp.curtail_kw, ns.pv_kw) * dt_h
                stats["pv_available_kwh"] += ns.pv_kw * dt_h
                stats["shifted_kwh"] += sp.shift_kw * dt_h
                ns.deferred_kwh = max(0.0, ns.deferred_kwh + sp.shift_kw * dt_h - ns.rebound_kw * dt_h)
            ns.last_setpoint = sp
        self._snapshot = self._build_snapshot(trial, ok)
        return trial, stats

    # ---- views --------------------------------------------------------------------------------
    def node_view(self, node_id: str):
        return self.nodes[node_id].view()

    def snapshot(self) -> dict[str, Any]:
        return self._snapshot

    def _build_snapshot(self, trial: GridTrial, ok: bool) -> dict[str, Any]:
        if not ok:
            return {"converged": False, "buses": [], "lines": [], "trafos": [], "nodes": [], "totals": {}, "price": self.price}
        buses = pf.get_bus_results(self.net)
        vm_by_bus = {b["bus"]: b["vm_pu"] for b in buses}
        nodes = []
        for nid, ns in self.nodes.items():
            sp = ns.last_setpoint
            s = sp.storage_kw if ns.storage_available else 0.0
            d = ns.to_dict()
            d.update({"load_kw": round(max(0.0, ns.load_kw - sp.shift_kw), 3), "pv_kw": round(max(0.0, ns.pv_kw - sp.curtail_kw), 3),
                      "pv_available_kw": round(ns.pv_kw, 3), "battery_kw": round(s, 3),
                      "exchange_kw": round(trial.node_exchange_kw.get(nid, 0.0), 3),
                      "voltage_pu": round(vm_by_bus[self.emap.node_bus[nid]], 4), "deferred_kwh": round(ns.deferred_kwh, 3)})
            nodes.append(d)
        lines = [{**l, "p_from_kw": round(l["p_from_kw"], 3), "loading_percent": round(l["loading_percent"], 2)}
                 for l in pf.get_line_results(self.net)]
        trafos = pf.get_trafo_results(self.net)
        vm = [b["vm_pu"] for b in buses if b["vn_kv"] < 1.0]
        gen = sum(n["pv_kw"] for n in nodes)
        load = sum(n["load_kw"] for n in nodes)
        batt = sum(n["battery_kw"] for n in nodes)
        totals = {
            "generation_kw": round(gen, 3), "load_kw": round(load, 3), "battery_charge_kw": round(max(batt, 0.0), 3),
            "battery_discharge_kw": round(max(-batt, 0.0), 3), "battery_net_kw": round(batt, 3),
            "ext_grid_kw": round(trial.ext_grid_kw, 3), "import_kw": round(max(trial.ext_grid_kw, 0.0), 3),
            "export_kw": round(max(-trial.ext_grid_kw, 0.0), 3), "losses_kw": round(trial.losses_kw, 3),
            "avg_voltage_pu": round(sum(vm) / len(vm), 4), "min_voltage_pu": round(min(vm), 4),
            "max_voltage_pu": round(max(vm), 4),
            "max_line_loading_pct": round(max((l["loading_percent"] for l in lines), default=0.0), 2),
            "trafo_loading_pct": round(max((t["loading_percent"] for t in trafos), default=0.0), 2),
        }
        return {"converged": True, "buses": buses, "lines": lines, "trafos": trafos, "nodes": nodes,
                "ext_grid": {"p_kw": totals["ext_grid_kw"]}, "totals": totals, "price": round(self.price, 3)}

    def topology(self) -> dict[str, Any]:
        pos = {"ext": (70, 210), "B0": (230, 210), "B1": (430, 110), "B2": (430, 310), "B3": (630, 110)}
        nodes = [{"id": "ext", "label": "External grid", "type": "grid", "x": pos["ext"][0], "y": pos["ext"][1]}]
        for i, b in enumerate(self.emap.lv_buses):
            nm = self.emap.bus_name[b]
            nodes.append({"id": nm, "label": f"Bus {i}", "type": "bus", "x": pos[nm][0], "y": pos[nm][1]})
        edges = [{"id": "T0", "source": "ext", "target": "B0", "kind": "trafo", "label": "T0 20/0.4 kV"}]
        for name, a, b, _km in LINES:
            edges.append({"id": name, "source": f"B{a}", "target": f"B{b}", "kind": "line", "label": name})
        devices = [{"node_id": n.node_id, "bus": f"B{n.bus}", "label": n.label, "role": n.role, "devices": list(n.devices)}
                   for n in self.spec.nodes]
        return {"nodes": nodes, "edges": edges, "devices": devices}
