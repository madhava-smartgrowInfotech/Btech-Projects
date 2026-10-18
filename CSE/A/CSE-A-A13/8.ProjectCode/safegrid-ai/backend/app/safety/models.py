"""Plain data contracts used by the shield. No LLM, agent or simulator imports here."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ShieldStatus(str, Enum):
    APPROVED = "approved"
    PROJECTED = "projected"
    REJECTED = "rejected"


@dataclass(frozen=True)
class Violation:
    code: str
    component: str
    requested: float  # the offending metric value
    allowed: float  # the limit
    unit: str
    message: str
    excess: float = 0.0  # magnitude beyond the limit (>0 when violated)

    def key(self) -> tuple[str, str]:
        return (self.code, self.component)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Setpoint:
    """Physical effect of an action on one node. storage_kw > 0 means charging."""

    storage_kw: float = 0.0
    curtail_kw: float = 0.0
    shift_kw: float = 0.0

    def scaled(self, lam: float) -> "Setpoint":
        return Setpoint(self.storage_kw * lam, self.curtail_kw * lam, self.shift_kw * lam)

    def magnitude(self) -> float:
        return max(abs(self.storage_kw), abs(self.curtail_kw), abs(self.shift_kw))

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True)
class NodeView:
    """Read-only facts about a node at decision time."""

    node_id: str
    agent_id: str
    load_kw: float
    pv_kw: float
    soc: float
    storage_available: bool = True  # e.g. False when the EV is away


@dataclass
class GridTrial:
    """Result of a (trial) power flow, in the shield's own vocabulary."""

    converged: bool
    bus_vm: dict[str, float] = field(default_factory=dict)
    line_loading: dict[str, float] = field(default_factory=dict)
    trafo_loading: dict[str, float] = field(default_factory=dict)
    ext_grid_kw: float = 0.0  # + import from upstream grid
    losses_kw: float = 0.0
    balance_residual_kw: float = 0.0
    node_exchange_kw: dict[str, float] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        vm = list(self.bus_vm.values())
        return {
            "converged": self.converged,
            "min_voltage_pu": round(min(vm), 4) if vm else None,
            "max_voltage_pu": round(max(vm), 4) if vm else None,
            "max_line_loading_pct": round(max(self.line_loading.values()), 2) if self.line_loading else 0.0,
            "trafo_loading_pct": round(max(self.trafo_loading.values()), 2) if self.trafo_loading else 0.0,
            "ext_grid_kw": round(self.ext_grid_kw, 3),
            "losses_kw": round(self.losses_kw, 3),
            "node_exchange_kw": {k: round(v, 3) for k, v in self.node_exchange_kw.items()},
        }


@dataclass
class ShieldDecision:
    status: ShieldStatus
    requested_action: dict[str, Any]
    validated_action: dict[str, Any] | None
    violations: list[Violation]
    corrections: list[dict[str, Any]]
    checks: list[dict[str, Any]]
    requested_power_kw: float
    safe_power_kw: float
    setpoint: Setpoint
    grid_before: dict[str, Any]
    grid_after: dict[str, Any]
    after_trial: GridTrial | None = None
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "requested_power_kw": self.requested_power_kw,
            "safe_power_kw": self.safe_power_kw,
            "requested_action": self.requested_action,
            "validated_action": self.validated_action,
            "violations": [v.to_dict() for v in self.violations],
            "corrections": self.corrections,
            "checks": self.checks,
            "executed_setpoint": self.setpoint.to_dict(),
            "grid_state_before": self.grid_before,
            "grid_state_after": self.grid_after,
            "timestamp": self.timestamp,
        }
