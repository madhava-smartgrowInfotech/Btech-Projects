"""Thin, typed wrappers around pandapower power flow and result tables."""
from __future__ import annotations

import math
from typing import Any

import pandapower as pp

from app.grid.network import ElementMap
from app.safety.models import GridTrial


def run_power_flow(net) -> bool:
    """Run AC power flow. Never raises; returns False on non-convergence or NaN results."""
    try:
        pp.runpp(net, numba=False)
    except Exception:
        return False
    if not bool(getattr(net, "converged", False)):
        return False
    return bool(net.res_bus["vm_pu"].notna().all())


def _f(x) -> float:
    x = float(x)
    return x if math.isfinite(x) else 0.0


def get_bus_results(net) -> list[dict[str, Any]]:
    return [{"bus": int(i), "name": str(net.bus.at[i, "name"]), "vn_kv": _f(net.bus.at[i, "vn_kv"]),
             "vm_pu": _f(r.vm_pu), "va_degree": _f(r.va_degree)} for i, r in net.res_bus.iterrows()]


def get_line_results(net) -> list[dict[str, Any]]:
    out = []
    for i, r in net.res_line.iterrows():
        out.append({"line": int(i), "name": str(net.line.at[i, "name"]),
                    "from_bus": int(net.line.at[i, "from_bus"]), "to_bus": int(net.line.at[i, "to_bus"]),
                    "p_from_kw": _f(r.p_from_mw) * 1000, "p_to_kw": _f(r.p_to_mw) * 1000,
                    "loss_kw": _f(r.pl_mw) * 1000, "i_ka": _f(r.i_ka), "max_i_ka": _f(net.line.at[i, "max_i_ka"]),
                    "loading_percent": _f(r.loading_percent)})
    return out


def get_trafo_results(net) -> list[dict[str, Any]]:
    return [{"trafo": int(i), "name": str(net.trafo.at[i, "name"]), "p_hv_kw": _f(r.p_hv_mw) * 1000,
             "p_lv_kw": _f(r.p_lv_mw) * 1000, "loss_kw": _f(r.pl_mw) * 1000,
             "loading_percent": _f(r.loading_percent)} for i, r in net.res_trafo.iterrows()]


def get_load_results(net) -> list[dict[str, Any]]:
    return [{"load": int(i), "name": str(net.load.at[i, "name"]), "bus": int(net.load.at[i, "bus"]),
             "p_kw": _f(r.p_mw) * 1000, "q_kvar": _f(r.q_mvar) * 1000} for i, r in net.res_load.iterrows()]


def get_generation_results(net) -> list[dict[str, Any]]:
    return [{"sgen": int(i), "name": str(net.sgen.at[i, "name"]), "bus": int(net.sgen.at[i, "bus"]),
             "p_kw": _f(r.p_mw) * 1000} for i, r in net.res_sgen.iterrows()]


def get_storage_results(net) -> list[dict[str, Any]]:
    return [{"storage": int(i), "name": str(net.storage.at[i, "name"]), "bus": int(net.storage.at[i, "bus"]),
             "p_kw": _f(r.p_mw) * 1000, "soc_percent": _f(net.storage.at[i, "soc_percent"])}
            for i, r in net.res_storage.iterrows()]


def get_ext_grid_kw(net) -> float:
    return _f(net.res_ext_grid["p_mw"].sum()) * 1000


def build_trial(net, ok: bool, emap: ElementMap) -> GridTrial:
    """Convert pandapower results into the shield's GridTrial."""
    if not ok:
        return GridTrial(converged=False)
    bus_vm = {emap.bus_name[b]: _f(net.res_bus.at[b, "vm_pu"]) for b in emap.lv_buses}
    line_loading = {emap.line_name[i]: _f(net.res_line.at[i, "loading_percent"]) for i in net.line.index}
    trafo_loading = {emap.trafo_name[i]: _f(net.res_trafo.at[i, "loading_percent"]) for i in net.trafo.index}
    ext = get_ext_grid_kw(net)
    losses = (_f(net.res_line["pl_mw"].sum()) + _f(net.res_trafo["pl_mw"].sum())) * 1000
    load = _f(net.res_load["p_mw"].sum()) * 1000
    stor = _f(net.res_storage["p_mw"].sum()) * 1000
    gen = _f(net.res_sgen["p_mw"].sum()) * 1000
    exchange = {}
    for node_id in emap.node_bus:
        exchange[node_id] = (_f(net.res_load.at[emap.load_idx[node_id], "p_mw"])
                             + _f(net.res_storage.at[emap.storage_idx[node_id], "p_mw"])
                             - _f(net.res_sgen.at[emap.sgen_idx[node_id], "p_mw"])) * 1000
    return GridTrial(True, bus_vm, line_loading, trafo_loading, ext, losses, ext + gen - load - stor - losses, exchange)
