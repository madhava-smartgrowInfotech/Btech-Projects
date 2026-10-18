"""Structured explanations. Only inputs, decision factors, action, safety checks and outcome are shown -
never model chain-of-thought."""
from __future__ import annotations

from typing import Any

from app.models.actions import EnergyAction

LABEL = {
    "charge_battery": "Charge battery", "discharge_battery": "Discharge battery", "import_power": "Import power from grid",
    "export_power": "Export power to grid", "curtail_generation": "Curtail generation", "shift_load": "Shift load",
    "idle": "Idle (no action)",
}
REASON_TEXT = {
    "HIGH_SOLAR_GENERATION": "Solar generation exceeds local demand", "LOW_LOCAL_LOAD": "Local load is low",
    "BATTERY_CAPACITY_AVAILABLE": "Battery has available capacity", "BATTERY_ENERGY_AVAILABLE": "Battery holds usable energy",
    "BATTERY_FULL": "Battery has no headroom", "BATTERY_LOW_SOC": "Battery state of charge is low",
    "HIGH_PRICE": "Electricity price is high", "LOW_PRICE": "Electricity price is low",
    "LOCAL_DEFICIT": "Local load exceeds local generation", "SOLAR_SURPLUS": "Surplus solar power is available",
    "VOLTAGE_HIGH_ABSORB": "Local voltage is near the upper limit - absorbing power",
    "VOLTAGE_HIGH_CURTAIL": "Local voltage is near the upper limit - reducing generation",
    "GRID_STRESS_SUPPORT": "Grid stress detected - supporting locally", "GRID_STRESS_HOLD": "Grid stress detected - holding position",
    "GRID_STRESS_REDUCE_RATE": "Grid stress detected - reducing charging rate", "EV_CHARGE_NEEDED": "EV has not reached its target SOC",
    "EV_NOT_CONNECTED": "EV is not connected", "EV_TARGET_REACHED": "EV target SOC reached", "DEFER_HIGH_PRICE": "Deferring charge during high price",
    "EV_ABOVE_CRITICAL_SOC": "EV is above its critical SOC", "V2G_SUPPORT": "Vehicle-to-grid support", "NO_BENEFICIAL_ACTION": "No cost-beneficial action found",
    "AGGRESSIVE_SIZING": "Request sized above the estimated safe range", "MAX_RATE_REQUEST": "Request uses the full power rating",
    "INJECTED_FAULT": "Scenario fault injection (intentionally unsafe proposal)",
}
SOURCE_TEXT = {"llm": "LLM agent", "mock": "Mock LLM provider", "fallback": "Deterministic fallback policy (LLM unavailable/invalid)",
               "baseline": "Non-LLM baseline controller", "injected": "Injected fault (test scenario)"}


def build_explanation(ctx: dict[str, Any], action: EnergyAction, source: str, fallback_reason: str | None = None) -> dict[str, Any]:
    gc = ctx["grid_constraints"]
    factors = [REASON_TEXT.get(c, c.replace("_", " ").capitalize()) for c in action.reason_codes]
    return {
        "agent_id": ctx["agent_id"], "node_id": ctx["node_id"], "time": ctx["time"], "step": ctx["step"],
        "decision": action.action_type, "decision_label": LABEL[action.action_type], "power_kw": action.power_kw,
        "reason_codes": list(action.reason_codes), "decision_factors": factors, "confidence": action.confidence,
        "context_used": {
            "solar_generation_kw": ctx["solar_kw"], "local_load_kw": ctx["load_kw"],
            "battery_soc": ctx["battery"]["soc"], "electricity_price": ctx["electricity_price"],
            "local_voltage_pu": gc["local_voltage_pu"], "worst_line_loading_pct": gc["worst_line_loading_pct"],
        },
        "decision_source": source, "decision_source_text": SOURCE_TEXT.get(source, source), "fallback_reason": fallback_reason,
        "safety_result": "pending", "shield_violations": [], "executed_power_kw": None,
    }


def attach_safety(explanation: dict[str, Any], shield: dict[str, Any]) -> dict[str, Any]:
    out = dict(explanation)
    out["safety_result"] = shield["status"]
    out["shield_violations"] = [{"code": v["code"], "component": v["component"], "requested": v["requested"], "allowed": v["allowed"]}
                                for v in shield["violations"]]
    va = shield.get("validated_action")
    out["executed_power_kw"] = va["power_kw"] if va else 0.0
    return out
