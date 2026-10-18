"""Mutable per-node state held by the simulator."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.grid.network import NodeSpec
from app.safety.models import NodeView, Setpoint


@dataclass
class NodeState:
    spec: NodeSpec
    soc: float
    load_kw: float = 0.0
    pv_kw: float = 0.0
    base_load_kw: float = 0.0
    rebound_kw: float = 0.0  # deferred load returning
    deferred_kwh: float = 0.0
    storage_available: bool = True
    last_setpoint: Setpoint = field(default_factory=Setpoint)

    @property
    def node_id(self) -> str:
        return self.spec.node_id

    def view(self) -> NodeView:
        return NodeView(self.spec.node_id, self.spec.agent_id, self.load_kw, self.pv_kw, self.soc, self.storage_available)

    def to_dict(self) -> dict:
        s = self.spec
        return {"node_id": s.node_id, "agent_id": s.agent_id, "role": s.role, "label": s.label, "bus": s.bus,
                "devices": list(s.devices), "capacity_kwh": s.limits.storage_capacity_kwh,
                "max_charge_kw": s.limits.max_charge_kw if self.storage_available else 0.0,
                "max_discharge_kw": s.limits.max_discharge_kw if self.storage_available else 0.0,
                "soc": self.soc, "storage_available": self.storage_available}
