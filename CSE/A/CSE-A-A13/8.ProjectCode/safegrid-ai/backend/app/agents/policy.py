"""Transparent, deterministic, cost-aware heuristics (NOT an optimiser - no global optimality is claimed).

Used (a) as the labelled fallback when the LLM fails, (b) as the base of the mock provider, and
(c) in a deliberately simpler form as the non-LLM baseline controller.
"""
from __future__ import annotations

from typing import Any


def _price_bands(ctx: dict[str, Any]) -> tuple[bool, bool]:
    ps, p = ctx["price_stats"], ctx["electricity_price"]
    span = max(ps["max"] - ps["min"], 1e-9)
    return p >= ps["min"] + 0.7 * span, p <= ps["min"] + 0.25 * span


def _rooms(ctx: dict[str, Any]) -> tuple[float, float]:
    b = ctx["battery"]
    if not b["available"] or b["capacity_kwh"] <= 0:
        return 0.0, 0.0
    dt_h = ctx["dt_minutes"] / 60.0
    up = min(b["max_charge_kw"], (min(b["soc_max"], 0.90) - b["soc"]) * b["capacity_kwh"] / (dt_h * 0.95))
    down = min(b["max_discharge_kw"], (b["soc"] - max(b["soc_min"], 0.20)) * b["capacity_kwh"] * 0.95 / dt_h)
    return max(up, 0.0), max(down, 0.0)


def _act(kind: str, kw: float, reasons: list[str], conf: float) -> dict[str, Any]:
    return {"action_type": kind, "power_kw": round(max(kw, 0.0), 3), "reason_codes": reasons, "confidence": conf}


def cost_aware_policy(ctx: dict[str, Any]) -> dict[str, Any]:
    load, solar = ctx["load_kw"], ctx["solar_kw"]
    surplus = solar - load
    hi, lo = _price_bands(ctx)
    up, down = _rooms(ctx)
    gc, b = ctx["grid_constraints"], ctx["battery"]
    v = gc["local_voltage_pu"]
    over = v >= gc["v_max"] - 0.008
    under = v <= gc["v_min"] + 0.008
    hot = gc["worst_line_loading_pct"] > 0.85 * gc["line_max_loading_pct"]

    if ctx["role"] == "ev_storage":
        ev = ctx["ev"]
        if not b["available"]:
            return _act("idle", 0, ["EV_NOT_CONNECTED"], 0.95)
        need_kw = max(ev["required_soc"] - b["soc"], 0.0) * b["capacity_kwh"] / (ctx["dt_minutes"] / 60.0 * 0.95)
        if need_kw > 0.1 and up > 0.1:
            if hi and b["soc"] >= ev["critical_soc"]:
                return _act("idle", 0, ["DEFER_HIGH_PRICE", "EV_ABOVE_CRITICAL_SOC"], 0.8)
            if under or hot:
                return _act("charge_battery", min(up, need_kw) * 0.5, ["GRID_STRESS_REDUCE_RATE", "EV_CHARGE_NEEDED"], 0.75)
            return _act("charge_battery", min(up, need_kw), ["EV_CHARGE_NEEDED"] + (["LOW_PRICE"] if lo else []), 0.85)
        if ev.get("v2g_enabled") and hi and down > 0.1 and b["soc"] > 0.7:
            return _act("discharge_battery", min(down, max(load - solar, 0.5)), ["HIGH_PRICE", "V2G_SUPPORT"], 0.6)
        return _act("idle", 0, ["EV_TARGET_REACHED"], 0.9)

    if over and solar > 0.2:
        if up > 0.1:
            return _act("charge_battery", min(up, max(surplus, 0.5 * up)), ["VOLTAGE_HIGH_ABSORB", "BATTERY_CAPACITY_AVAILABLE"], 0.85)
        return _act("curtail_generation", min(solar, max(surplus, 0.0)), ["VOLTAGE_HIGH_CURTAIL", "BATTERY_FULL"], 0.7)
    if under or hot:
        if down > 0.1 and load > solar:
            return _act("discharge_battery", min(down, load - solar), ["GRID_STRESS_SUPPORT", "BATTERY_ENERGY_AVAILABLE"], 0.8)
        return _act("idle", 0, ["GRID_STRESS_HOLD"], 0.8)
    if surplus > 0.2:
        if up > 0.1:
            r = ["HIGH_SOLAR_GENERATION", "BATTERY_CAPACITY_AVAILABLE"] + (["LOW_LOCAL_LOAD"] if load < 0.5 * solar else [])
            return _act("charge_battery", min(surplus, up), r, 0.9)
        return _act("export_power", surplus, ["SOLAR_SURPLUS", "BATTERY_FULL"], 0.75)
    if hi and down > 0.1 and load > solar:
        return _act("discharge_battery", min(down, load - solar), ["HIGH_PRICE", "LOCAL_DEFICIT", "BATTERY_ENERGY_AVAILABLE"], 0.85)
    if lo and b["available"] and b["soc"] < 0.5 and up > 0.1:
        return _act("import_power", max(load - solar, 0.0) + min(up, 0.5 * b["max_charge_kw"]), ["LOW_PRICE", "BATTERY_LOW_SOC"], 0.7)
    return _act("idle", 0, ["NO_BENEFICIAL_ACTION"], 0.7)


def baseline_policy(ctx: dict[str, Any]) -> dict[str, Any]:
    """Simple time-of-use rules, ignoring solar surplus and grid stress. Deterministic, no LLM."""
    hi, lo = _price_bands(ctx)
    up, down = _rooms(ctx)
    b = ctx["battery"]
    if ctx["role"] == "ev_storage":
        if b["available"] and b["soc"] < ctx["ev"]["required_soc"] and up > 0.1:
            return _act("charge_battery", up, ["BASELINE_UNCONTROLLED_EV_CHARGING"], 1.0)
        return _act("idle", 0, ["BASELINE_IDLE"], 1.0)
    if lo and up > 0.1:
        return _act("charge_battery", 0.5 * b["max_charge_kw"], ["BASELINE_LOW_PRICE_CHARGE"], 1.0)
    if hi and down > 0.1:
        return _act("discharge_battery", 0.5 * b["max_discharge_kw"], ["BASELINE_HIGH_PRICE_DISCHARGE"], 1.0)
    return _act("idle", 0, ["BASELINE_IDLE"], 1.0)
