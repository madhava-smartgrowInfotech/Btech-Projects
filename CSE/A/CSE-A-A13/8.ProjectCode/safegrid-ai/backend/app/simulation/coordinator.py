"""Decentralised coordination: agents only propose; the coordinator detects conflicts and fixes the
order in which proposals are validated against the *cumulative* grid state. It never edits an action."""
from __future__ import annotations

from collections import defaultdict
from typing import Any

FEEDER_SHARED = [("node_1", "node_3", "L0_1")]  # node_3 hangs off node_1's feeder segment
RELIEF = {"idle", "curtail_generation", "shift_load"}


def net_effect_kw(action) -> float:
    """Approximate signed effect on the node's grid exchange (+ = more import)."""
    t, p = action.action_type, action.power_kw
    return {"charge_battery": p, "import_power": p, "discharge_battery": -p, "export_power": -p,
            "curtail_generation": p, "shift_load": -p}.get(t, 0.0)


def detect_conflicts(decisions) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    exports = [d for d in decisions if d.action.action_type == "export_power" and d.action.power_kw > 0]
    imports = [d for d in decisions if d.action.action_type == "import_power" and d.action.power_kw > 0]
    ex_kw, im_kw = sum(d.action.power_kw for d in exports), sum(d.action.power_kw for d in imports)
    if exports and imports and abs(ex_kw - im_kw) > 0.5:
        out.append({"type": "PEER_MISMATCH", "agents": [d.agent_id for d in exports + imports],
                    "detail": f"proposed exports {ex_kw:.2f} kW vs imports {im_kw:.2f} kW do not match",
                    "resolution": "Residual is exchanged with the external grid; each proposal is validated against cumulative network state."})
    by_target = defaultdict(list)
    for d in decisions:
        if d.action.target_node:
            by_target[d.action.target_node].append(d)
    for tgt, ds in by_target.items():
        if len(ds) > 1:
            out.append({"type": "TARGET_CONTENTION", "agents": [d.agent_id for d in ds], "detail": f"{len(ds)} agents target {tgt}",
                        "resolution": "Proposals are validated sequentially; later ones see the effect of earlier ones."})
    by_node = {d.node_id: d for d in decisions}
    for a, b, line in FEEDER_SHARED:
        if a in by_node and b in by_node:
            ea, eb = net_effect_kw(by_node[a].action), net_effect_kw(by_node[b].action)
            if ea * eb > 0 and min(abs(ea), abs(eb)) > 0.5:
                out.append({"type": "SHARED_FEEDER", "agents": [by_node[a].agent_id, by_node[b].agent_id],
                            "detail": f"both proposals push flow the same way over {line}",
                            "resolution": "Joint effect is checked by cumulative power flow; the later proposal may be projected."})
    return out


def order_decisions(decisions, step: int):
    """Relief actions first (they can only help), then rotate the rest for fairness."""
    ds = list(decisions)
    if ds:
        k = step % len(ds)
        ds = ds[k:] + ds[:k]
    return sorted(ds, key=lambda d: 0 if d.action.action_type in RELIEF else 1)
