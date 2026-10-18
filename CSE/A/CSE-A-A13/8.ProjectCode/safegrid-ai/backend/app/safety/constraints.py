"""Configurable electrical constraints. Nothing here is hard-coded into the checks."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

# ---- violation codes -------------------------------------------------------
MALFORMED_ACTION = "MALFORMED_ACTION"
UNKNOWN_AGENT = "UNKNOWN_AGENT"
AGENT_NODE_MISMATCH = "AGENT_NODE_MISMATCH"
UNKNOWN_TARGET_NODE = "UNKNOWN_TARGET_NODE"
NEGATIVE_POWER = "NEGATIVE_POWER"
NON_FINITE_POWER = "NON_FINITE_POWER"
INVALID_NODE_STATE = "INVALID_NODE_STATE"
POWER_LIMIT_EXCEEDED = "POWER_LIMIT_EXCEEDED"
BATTERY_UNAVAILABLE = "BATTERY_UNAVAILABLE"
BATTERY_CHARGE_LIMIT = "BATTERY_CHARGE_LIMIT"
BATTERY_DISCHARGE_LIMIT = "BATTERY_DISCHARGE_LIMIT"
BATTERY_SOC_LIMIT = "BATTERY_SOC_LIMIT"
NODE_IMPORT_LIMIT = "NODE_IMPORT_LIMIT"
NODE_EXPORT_LIMIT = "NODE_EXPORT_LIMIT"
LOAD_SHIFT_LIMIT = "LOAD_SHIFT_LIMIT"
CURTAILMENT_EXCEEDS_GENERATION = "CURTAILMENT_EXCEEDS_GENERATION"
DIRECTION_UNATTAINABLE = "DIRECTION_UNATTAINABLE"
VOLTAGE_OVER = "VOLTAGE_OVER"
VOLTAGE_UNDER = "VOLTAGE_UNDER"
LINE_OVERLOAD = "LINE_OVERLOAD"
TRANSFORMER_OVERLOAD = "TRANSFORMER_OVERLOAD"
POWER_FLOW_FAILED = "POWER_FLOW_FAILED"
GRID_IMPORT_LIMIT = "GRID_IMPORT_LIMIT"
GRID_EXPORT_LIMIT = "GRID_EXPORT_LIMIT"
POWER_BALANCE_RESIDUAL = "POWER_BALANCE_RESIDUAL"

# violation code -> named check shown in the dashboard pipeline
CHECK_OF: dict[str, str] = {
    MALFORMED_ACTION: "STRUCTURE", UNKNOWN_AGENT: "STRUCTURE", AGENT_NODE_MISMATCH: "STRUCTURE",
    UNKNOWN_TARGET_NODE: "STRUCTURE", NEGATIVE_POWER: "STRUCTURE", NON_FINITE_POWER: "STRUCTURE",
    INVALID_NODE_STATE: "STRUCTURE", POWER_LIMIT_EXCEEDED: "POWER_LIMITS",
    NODE_IMPORT_LIMIT: "NODE_LIMITS", NODE_EXPORT_LIMIT: "NODE_LIMITS", LOAD_SHIFT_LIMIT: "NODE_LIMITS",
    BATTERY_UNAVAILABLE: "BATTERY", BATTERY_CHARGE_LIMIT: "BATTERY", BATTERY_DISCHARGE_LIMIT: "BATTERY",
    BATTERY_SOC_LIMIT: "BATTERY", CURTAILMENT_EXCEEDS_GENERATION: "POWER_BALANCE",
    DIRECTION_UNATTAINABLE: "POWER_BALANCE", POWER_BALANCE_RESIDUAL: "POWER_BALANCE",
    VOLTAGE_OVER: "VOLTAGE", VOLTAGE_UNDER: "VOLTAGE", LINE_OVERLOAD: "LINE_LOADING",
    TRANSFORMER_OVERLOAD: "TRANSFORMER", POWER_FLOW_FAILED: "POWER_FLOW",
    GRID_IMPORT_LIMIT: "GRID_LIMITS", GRID_EXPORT_LIMIT: "GRID_LIMITS",
}
CHECK_ORDER = ["STRUCTURE", "POWER_LIMITS", "BATTERY", "NODE_LIMITS", "POWER_BALANCE",
               "POWER_FLOW", "VOLTAGE", "LINE_LOADING", "TRANSFORMER", "GRID_LIMITS"]


@dataclass(frozen=True)
class NodeLimits:
    """Per-node configurable limits: generation, load, storage, import/export."""

    max_import_kw: float
    max_export_kw: float
    max_generation_kw: float
    max_load_kw: float
    storage_capacity_kwh: float = 0.0
    max_charge_kw: float = 0.0
    max_discharge_kw: float = 0.0
    soc_min: float = 0.10
    soc_max: float = 0.95
    charge_eff: float = 0.95
    discharge_eff: float = 0.95
    shiftable_fraction: float = 0.30

    def reference_power_kw(self) -> float:
        return max(self.max_import_kw, self.max_export_kw, self.max_generation_kw,
                   self.max_charge_kw, self.max_discharge_kw, 1.0)


@dataclass(frozen=True)
class ConstraintConfig:
    v_min: float = 0.95
    v_max: float = 1.05
    line_max_loading_pct: float = 100.0
    trafo_max_loading_pct: float = 100.0
    max_grid_import_kw: float = 200.0
    max_grid_export_kw: float = 200.0
    min_action_kw: float = 0.05  # projected actions smaller than this are treated as rejected
    implausible_factor: float = 5.0  # request > factor * node reference power => rejected outright
    balance_tol_kw: float = 0.05
    attribution_tol: float = 1e-4  # a pre-existing violation only blocks if the action makes it worse
    node_limits: dict[str, NodeLimits] = field(default_factory=dict)

    def with_overrides(self, overrides: dict[str, Any] | None) -> "ConstraintConfig":
        if not overrides:
            return self
        allowed = {k: v for k, v in overrides.items()
                   if k in self.__dataclass_fields__ and k != "node_limits"}
        cfg = replace(self, **allowed)
        nl = overrides.get("node_limits")
        if nl:
            merged = dict(cfg.node_limits)
            for node_id, vals in nl.items():
                if node_id in merged:
                    merged[node_id] = replace(merged[node_id], **vals)
            cfg = replace(cfg, node_limits=merged)
        return cfg

    def to_dict(self) -> dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)
