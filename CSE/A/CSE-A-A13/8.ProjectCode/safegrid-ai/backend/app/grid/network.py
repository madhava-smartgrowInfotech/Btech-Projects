"""Programmatic pandapower network. No external files are needed.

        HV(20kV) --T0-- B0(0.4kV) --L0_1-- B1 --L1_3-- B3
                           \\--L0_2-- B2
   node_1 (home: load+PV+battery) @B1, node_2 (EV/storage) @B2, node_3 (renewable prosumer) @B3
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

import pandapower as pp

from app.safety.constraints import NodeLimits


@dataclass(frozen=True)
class NodeSpec:
    node_id: str
    agent_id: str
    role: str  # residential_prosumer | ev_storage | renewable_prosumer
    bus: int
    label: str
    pv_kwp: float
    base_load_kw: float
    initial_soc: float
    limits: NodeLimits
    devices: tuple[str, ...] = ("load",)


DEFAULT_NODES: tuple[NodeSpec, ...] = (
    NodeSpec("node_1", "prosumer_01", "residential_prosumer", 1, "Residential prosumer", 6.0, 3.0, 0.50,
             NodeLimits(max_import_kw=12, max_export_kw=6, max_generation_kw=6.5, max_load_kw=15,
                        storage_capacity_kwh=10, max_charge_kw=5, max_discharge_kw=5),
             ("load", "solar", "battery")),
    NodeSpec("node_2", "ev_01", "ev_storage", 2, "EV / storage node", 0.0, 0.8, 0.40,
             NodeLimits(max_import_kw=10, max_export_kw=0.0, max_generation_kw=0.0, max_load_kw=12,
                        storage_capacity_kwh=40, max_charge_kw=7.4, max_discharge_kw=0.0,
                        soc_min=0.20, soc_max=0.95),
             ("load", "ev")),
    NodeSpec("node_3", "renewable_01", "renewable_prosumer", 3, "Renewable prosumer", 20.0, 6.0, 0.50,
             NodeLimits(max_import_kw=15, max_export_kw=12, max_generation_kw=22, max_load_kw=20,
                        storage_capacity_kwh=30, max_charge_kw=10, max_discharge_kw=10),
             ("load", "solar", "battery")),
)

# (name, from_bus, to_bus, length_km)
LINES = (("L0_1", 0, 1, 0.30), ("L0_2", 0, 2, 0.25), ("L1_3", 1, 3, 0.45))
LINE_STD_TYPE = "NAYY 4x50 SE"
TRAFO_STD_TYPE = "0.25 MVA 20/0.4 kV"


@dataclass
class NetworkSpec:
    nodes: tuple[NodeSpec, ...] = DEFAULT_NODES
    ext_grid_vm_pu: float = 1.0
    line_length_scale: float = 1.0
    line_max_i_ka: dict[str, float] = field(default_factory=dict)  # per-line ampacity overrides
    load_power_factor: float = 0.95

    def with_initial_soc(self, socs: dict[str, float] | None) -> "NetworkSpec":
        if not socs:
            return self
        nodes = tuple(replace(n, initial_soc=socs.get(n.node_id, n.initial_soc)) for n in self.nodes)
        return replace(self, nodes=nodes)


@dataclass
class ElementMap:
    hv_bus: int
    lv_buses: list[int]
    load_idx: dict[str, int]
    sgen_idx: dict[str, int]
    storage_idx: dict[str, int]
    bus_name: dict[int, str]
    line_name: dict[int, str]
    trafo_name: dict[int, str]
    node_bus: dict[str, int]


def create_network(spec: NetworkSpec | None = None) -> tuple[Any, ElementMap]:
    spec = spec or NetworkSpec()
    net = pp.create_empty_network(name="safegrid-lv-feeder", f_hz=50.0)
    hv = pp.create_bus(net, vn_kv=20.0, name="HV")
    lv = [pp.create_bus(net, vn_kv=0.4, name=f"B{i}") for i in range(4)]
    pp.create_ext_grid(net, bus=hv, vm_pu=spec.ext_grid_vm_pu, name="ExternalGrid")
    pp.create_transformer(net, hv_bus=hv, lv_bus=lv[0], std_type=TRAFO_STD_TYPE, name="T0")
    for name, a, b, km in LINES:
        idx = pp.create_line(net, from_bus=lv[a], to_bus=lv[b], length_km=km * spec.line_length_scale,
                             std_type=LINE_STD_TYPE, name=name)
        if name in spec.line_max_i_ka:
            net.line.at[idx, "max_i_ka"] = float(spec.line_max_i_ka[name])

    tan_phi = ((1.0 / spec.load_power_factor**2) - 1.0) ** 0.5
    load_idx, sgen_idx, storage_idx, node_bus = {}, {}, {}, {}
    for n in spec.nodes:
        bus = lv[n.bus]
        node_bus[n.node_id] = bus
        p = n.base_load_kw / 1000.0
        load_idx[n.node_id] = pp.create_load(net, bus=bus, p_mw=p, q_mvar=p * tan_phi, name=f"load_{n.node_id}")
        sgen_idx[n.node_id] = pp.create_sgen(net, bus=bus, p_mw=0.0, q_mvar=0.0, name=f"pv_{n.node_id}", type="PV")
        cap_mwh = max(n.limits.storage_capacity_kwh, 1e-6) / 1000.0
        storage_idx[n.node_id] = pp.create_storage(net, bus=bus, p_mw=0.0, max_e_mwh=cap_mwh,
                                                   soc_percent=n.initial_soc * 100.0, name=f"storage_{n.node_id}")
    emap = ElementMap(
        hv_bus=hv, lv_buses=lv, load_idx=load_idx, sgen_idx=sgen_idx, storage_idx=storage_idx,
        bus_name={int(i): str(nm) for i, nm in net.bus["name"].items()},
        line_name={int(i): str(nm) for i, nm in net.line["name"].items()},
        trafo_name={int(i): str(nm) for i, nm in net.trafo["name"].items()},
        node_bus=node_bus,
    )
    return net, emap
