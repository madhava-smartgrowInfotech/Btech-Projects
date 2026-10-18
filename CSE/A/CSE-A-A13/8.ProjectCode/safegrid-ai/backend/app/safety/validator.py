"""Pure, deterministic constraint checks. No I/O, no randomness, no LLM."""
from __future__ import annotations

import math

from app.models.actions import ACTION_TYPES, EnergyAction
from app.safety import constraints as C
from app.safety.models import GridTrial, NodeView, Setpoint, Violation

EPS = 1e-6


def _v(code, comp, requested, allowed, unit, msg, excess=None) -> Violation:
    return Violation(code, comp, float(requested), float(allowed), unit, msg,
                     float(excess if excess is not None else abs(requested - allowed)))


def neutral_exchange_kw(node: NodeView) -> float:
    """Net grid exchange of a node if no action is taken (+ import)."""
    return node.load_kw - node.pv_kw


def resolve_setpoint(action_type: str, power_kw: float, node: NodeView) -> Setpoint:
    """Single source of truth mapping an action to its physical effect.

    import_power / export_power are *net exchange targets*: the node aims to import (export)
    power_kw at its connection point and the storage covers the difference.
    """
    p = float(power_kw)
    if action_type == "charge_battery":
        return Setpoint(storage_kw=p)
    if action_type == "discharge_battery":
        return Setpoint(storage_kw=-p)
    if action_type == "curtail_generation":
        return Setpoint(curtail_kw=p)
    if action_type == "shift_load":
        return Setpoint(shift_kw=p)
    if action_type == "import_power":
        return Setpoint(storage_kw=p - neutral_exchange_kw(node))
    if action_type == "export_power":
        return Setpoint(storage_kw=-p - neutral_exchange_kw(node))
    return Setpoint()


def projected_power_kw(action_type: str, requested_kw: float, node: NodeView, lam: float) -> float:
    """Power value of the action after scaling its physical effect by lam in [0,1]."""
    if action_type in ("import_power", "export_power"):
        e0 = neutral_exchange_kw(node)
        e_req = requested_kw if action_type == "import_power" else -requested_kw
        return abs(e0 + lam * (e_req - e0))
    return requested_kw * lam


def structural_violations(action: EnergyAction, node: NodeView | None, limits, cfg: C.ConstraintConfig,
                          known_agents: set[str], known_nodes: set[str]) -> list[Violation]:
    out: list[Violation] = []
    a = action
    if a.action_type not in ACTION_TYPES:
        out.append(_v(C.MALFORMED_ACTION, a.agent_id, 0, 0, "", f"action_type {a.action_type!r} not allow-listed", 1))
    if a.agent_id not in known_agents:
        out.append(_v(C.UNKNOWN_AGENT, a.agent_id, 0, 0, "", "agent is not registered", 1))
    if node is None or limits is None:
        return out
    if node.agent_id != a.agent_id:
        out.append(_v(C.AGENT_NODE_MISMATCH, node.node_id, 0, 0, "", "agent does not own this node", 1))
    if a.target_node is not None and a.target_node not in known_nodes:
        out.append(_v(C.UNKNOWN_TARGET_NODE, str(a.target_node), 0, 0, "", "target node is not part of the grid", 1))
    if not math.isfinite(a.power_kw):
        out.append(_v(C.NON_FINITE_POWER, node.node_id, 0, 0, "kW", "power is NaN/inf", 1))
        return out
    if a.power_kw < 0:
        out.append(_v(C.NEGATIVE_POWER, node.node_id, a.power_kw, 0, "kW", "power must be >= 0", -a.power_kw))
    state_ok = all(math.isfinite(x) for x in (node.load_kw, node.pv_kw, node.soc)) and 0.0 <= node.soc <= 1.0
    if not state_ok:
        out.append(_v(C.INVALID_NODE_STATE, node.node_id, node.soc, 0.0, "pu", "node state invalid (SOC outside [0,1] or NaN)", 1))
    cap = cfg.implausible_factor * limits.reference_power_kw()
    if a.power_kw > cap:
        out.append(_v(C.POWER_LIMIT_EXCEEDED, node.node_id, a.power_kw, cap, "kW",
                      "requested power is implausibly large for this node", a.power_kw - cap))
    return out


def local_violations(sp: Setpoint, node: NodeView, lim: C.NodeLimits, dt_h: float) -> list[Violation]:
    """Battery, node and balance limits for one node (no power flow needed)."""
    out: list[Violation] = []
    n = node.node_id
    s = sp.storage_kw
    cap = lim.storage_capacity_kwh
    if abs(s) > EPS:
        if cap <= 0 or not node.storage_available:
            out.append(_v(C.BATTERY_UNAVAILABLE, n, abs(s), 0.0, "kW", "no usable storage at this node right now"))
        elif s > 0:
            max_c = lim.max_charge_kw
            if s > max_c + EPS:
                out.append(_v(C.BATTERY_CHARGE_LIMIT, n, s, max_c, "kW", "exceeds battery charge power rating"))
            headroom = max(0.0, lim.soc_max - node.soc) * cap / (dt_h * lim.charge_eff)
            if s > headroom + EPS:
                out.append(_v(C.BATTERY_SOC_LIMIT, n, s, headroom, "kW", f"would exceed SOC max {lim.soc_max:.2f}"))
        else:
            d = -s
            if d > lim.max_discharge_kw + EPS:
                out.append(_v(C.BATTERY_DISCHARGE_LIMIT, n, d, lim.max_discharge_kw, "kW", "exceeds battery discharge power rating"))
            avail = max(0.0, node.soc - lim.soc_min) * cap * lim.discharge_eff / dt_h
            if d > avail + EPS:
                out.append(_v(C.BATTERY_SOC_LIMIT, n, d, avail, "kW", f"would go below SOC min {lim.soc_min:.2f}"))
    if sp.curtail_kw > node.pv_kw + EPS:
        out.append(_v(C.CURTAILMENT_EXCEEDS_GENERATION, n, sp.curtail_kw, node.pv_kw, "kW", "cannot curtail more than is generated"))
    shiftable = max(0.0, node.load_kw) * lim.shiftable_fraction
    if sp.shift_kw > shiftable + EPS:
        out.append(_v(C.LOAD_SHIFT_LIMIT, n, sp.shift_kw, shiftable, "kW", "exceeds shiftable share of current load"))
    load_eff = node.load_kw - sp.shift_kw
    pv_eff = node.pv_kw - sp.curtail_kw
    e = load_eff + s - pv_eff
    if e > lim.max_import_kw + EPS:
        out.append(_v(C.NODE_IMPORT_LIMIT, n, e, lim.max_import_kw, "kW", "node import limit exceeded"))
    if -e > lim.max_export_kw + EPS:
        out.append(_v(C.NODE_EXPORT_LIMIT, n, -e, lim.max_export_kw, "kW", "node export limit exceeded"))
    return out


def check_grid(t: GridTrial, cfg: C.ConstraintConfig) -> list[Violation]:
    """Every violation present in a power-flow result."""
    if not t.converged:
        return [_v(C.POWER_FLOW_FAILED, "network", 1, 0, "", "power flow did not converge", 1)]
    out: list[Violation] = []
    for bus, vm in t.bus_vm.items():
        if vm > cfg.v_max + EPS:
            out.append(_v(C.VOLTAGE_OVER, bus, vm, cfg.v_max, "pu", "overvoltage", vm - cfg.v_max))
        elif vm < cfg.v_min - EPS:
            out.append(_v(C.VOLTAGE_UNDER, bus, vm, cfg.v_min, "pu", "undervoltage", cfg.v_min - vm))
    for line, pct in t.line_loading.items():
        if pct > cfg.line_max_loading_pct + 1e-4:
            out.append(_v(C.LINE_OVERLOAD, line, pct, cfg.line_max_loading_pct, "%", "line thermal limit exceeded", pct - cfg.line_max_loading_pct))
    for tr, pct in t.trafo_loading.items():
        if pct > cfg.trafo_max_loading_pct + 1e-4:
            out.append(_v(C.TRANSFORMER_OVERLOAD, tr, pct, cfg.trafo_max_loading_pct, "%", "transformer overloaded", pct - cfg.trafo_max_loading_pct))
    if t.ext_grid_kw > cfg.max_grid_import_kw:
        out.append(_v(C.GRID_IMPORT_LIMIT, "ext_grid", t.ext_grid_kw, cfg.max_grid_import_kw, "kW", "grid import limit exceeded", t.ext_grid_kw - cfg.max_grid_import_kw))
    if -t.ext_grid_kw > cfg.max_grid_export_kw:
        out.append(_v(C.GRID_EXPORT_LIMIT, "ext_grid", -t.ext_grid_kw, cfg.max_grid_export_kw, "kW", "grid export limit exceeded", -t.ext_grid_kw - cfg.max_grid_export_kw))
    if abs(t.balance_residual_kw) > cfg.balance_tol_kw:
        out.append(_v(C.POWER_BALANCE_RESIDUAL, "network", abs(t.balance_residual_kw), cfg.balance_tol_kw, "kW", "power balance residual too large", abs(t.balance_residual_kw) - cfg.balance_tol_kw))
    return out


def new_violations(after: list[Violation], before: list[Violation], tol: float = 1e-4) -> list[Violation]:
    """Violations attributable to the action: new, or pre-existing but made worse."""
    prior = {v.key(): v.excess for v in before}
    return [v for v in after if v.key() not in prior or v.excess > prior[v.key()] + tol]
