import asyncio
from dataclasses import replace

import pytest

from app.agents.explain import attach_safety, build_explanation
from app.agents.storage_agent import StorageAgent
from app.agents.prosumer_agent import ProsumerAgent
from app.config import get_settings
from app.llm.api_provider import APILLMProvider
from app.llm.base import LLMOutputError, LLMProvider, LLMUnavailableError
from app.llm.mock_provider import FailingProvider, FaultInjectingProvider, MockLLMProvider, RuleBasedProvider
from app.llm.provider import build_provider
from app.models.actions import EnergyAction
from app.safety import ConstraintConfig, ShieldStatus
from tests.helpers import FakeGrid, action, limits, make_cfg, make_node, run


def make_obs(step=0, solar=4.8, load=2.1, soc=0.42, price=5.2, role="residential_prosumer", avail=True):
    lim = limits()
    node = {"load_kw": load, "pv_kw": solar, "soc": soc, "storage_available": avail, "voltage_pu": 1.0, "exchange_kw": load - solar}
    other = {"load_kw": 1, "pv_kw": 0, "soc": 0.5, "storage_available": True, "voltage_pu": 1.0, "exchange_kw": 1.0}
    return {"step": step, "time": "12:30", "dt_minutes": 15, "price": price,
            "price_stats": {"min": 3.8, "max": 9.0, "avg": 5.6}, "weather": {"cloud_factor": 0.9, "temp_c": 30},
            "nodes": {"node_1": node, "node_2": other}, "limits": {"node_1": lim, "node_2": lim},
            "constraints": ConstraintConfig(), "trial_summary": {"max_line_loading_pct": 20.0, "trafo_loading_pct": 10.0}}


def agent(provider, cls=ProsumerAgent, **kw):
    return cls("prosumer_01", "node_1", provider, **kw)


def decide(a, obs=None):
    async def go():
        ctx = await a.perceive(obs or make_obs())
        return ctx, await a.decide(ctx)
    return asyncio.run(go())


def test_context_is_structured():
    ctx, _ = decide(agent(MockLLMProvider(seed=1, unsafe_rate=0)))
    for key in ("load_kw", "solar_kw", "battery", "electricity_price", "neighboring_nodes", "grid_constraints", "time"):
        assert key in ctx
    assert ctx["battery"]["soc"] == 0.42 and "node_2" in ctx["neighboring_nodes"]


def test_mock_provider_returns_valid_schema_and_is_reproducible():
    _, d1 = decide(agent(MockLLMProvider(seed=7, unsafe_rate=0.5)))
    _, d2 = decide(agent(MockLLMProvider(seed=7, unsafe_rate=0.5)))
    assert isinstance(d1.action, EnergyAction) and d1.decision_source == "mock"
    assert d1.action == d2.action if hasattr(d1.action, "__eq__") and False else d1.action.model_dump() == d2.action.model_dump()


def test_surplus_solar_prefers_charging_the_battery():
    _, d = decide(agent(MockLLMProvider(seed=1, unsafe_rate=0)))
    assert d.action.action_type == "charge_battery" and "HIGH_SOLAR_GENERATION" in d.action.reason_codes


# --- spec test 7: LLM API failure -> labelled fallback ---------------------------------------------
def test_llm_failure_uses_labelled_fallback():
    _, d = decide(agent(FailingProvider()))
    assert d.decision_source == "fallback"
    assert "LLMUnavailableError" in d.fallback_reason
    assert isinstance(d.action, EnergyAction)


def test_malformed_llm_output_uses_fallback():
    faults = [{"agent_id": "prosumer_01", "from_step": 0, "to_step": 5, "kind": "malformed"}]
    _, d = decide(agent(FaultInjectingProvider(MockLLMProvider(), faults)))
    assert d.decision_source == "fallback" and "LLMOutputError" in d.fallback_reason


def test_slow_llm_times_out_into_fallback():
    class Slow(LLMProvider):
        async def generate_action(self, context):
            await asyncio.sleep(2)
    _, d = decide(agent(Slow(), timeout_s=0.05))
    assert d.decision_source == "fallback" and "Timeout" in d.fallback_reason


def test_unconfigured_api_provider_is_unavailable_and_falls_back():
    s = replace(get_settings(), llm_api_key="", llm_model="")
    p = APILLMProvider(s)
    with pytest.raises(LLMUnavailableError):
        asyncio.run(p.generate_action({"agent_id": "prosumer_01"}))
    _, d = decide(agent(p))
    assert d.decision_source == "fallback"


def test_api_output_is_untrusted_and_schema_validated():
    ok = APILLMProvider.validate_arguments(
        {"agent_id": "someone_else", "action_type": "idle", "power_kw": 0, "duration_minutes": 15, "reason_codes": [], "confidence": 0.5},
        "prosumer_01")
    assert ok.agent_id == "prosumer_01"  # the model cannot choose its identity
    for bad in ("os.system('id')", None, [], {"action_type": "run_shell", "power_kw": 1, "duration_minutes": 5, "confidence": 1},
                {"action_type": "idle", "power_kw": -5, "duration_minutes": 5, "confidence": 1, "reason_codes": []},
                {"action_type": "idle", "power_kw": 0, "duration_minutes": 5, "confidence": 1, "reason_codes": [], "code": "x"}):
        with pytest.raises(LLMOutputError):
            APILLMProvider.validate_arguments(bad, "prosumer_01")


def test_provider_factory_and_baseline_gets_no_faults():
    s = get_settings()
    faults = [{"agent_id": "x", "from_step": 0, "to_step": 1, "kind": "malformed"}]
    assert isinstance(build_provider("baseline", s, faults=faults), RuleBasedProvider)
    assert isinstance(build_provider("mock", s, faults=faults), FaultInjectingProvider)
    assert isinstance(build_provider("failing", s), FailingProvider)


def test_storage_agent_defers_when_ev_away():
    a = StorageAgent("ev_01", "node_1", MockLLMProvider(unsafe_rate=0))
    obs = make_obs(role="ev_storage", avail=False, solar=0)
    _, d = decide(a, obs)
    assert d.action.action_type == "idle" and "EV_NOT_CONNECTED" in d.action.reason_codes


# --- spec test 8: unsafe LLM proposal != executed action -----------------------------------------------
def test_unsafe_llm_proposal_never_equals_executed_action():
    faults = [{"agent_id": "prosumer_01", "from_step": 0, "to_step": 9, "kind": "action",
               "action_type": "export_power", "power_kw": 1000.0}]
    _, d = decide(agent(FaultInjectingProvider(MockLLMProvider(), faults)))
    assert d.decision_source == "injected" and d.action.power_kw == 1000.0
    node = make_node(load=2.0, pv=4.0)
    decision = run(d.action, node=node, cfg=make_cfg(limits(max_export_kw=5)), grid=FakeGrid(node))
    assert decision.status in (ShieldStatus.REJECTED, ShieldStatus.PROJECTED)
    assert decision.validated_action is None or decision.validated_action["power_kw"] != d.action.power_kw
    assert decision.setpoint.magnitude() <= 5.0 + 1e-6


def test_explanation_is_structured_and_has_no_chain_of_thought():
    ctx, d = decide(agent(MockLLMProvider(seed=1, unsafe_rate=0)))
    ex = build_explanation(ctx, d.action, d.decision_source)
    assert {"decision", "reason_codes", "context_used", "decision_factors", "safety_result"} <= set(ex)
    assert not any(k in ex for k in ("chain_of_thought", "reasoning", "thoughts", "scratchpad"))
    node = make_node(load=2.1, pv=4.8, soc=0.42)
    ex2 = attach_safety(ex, run(d.action, node=node).to_dict())
    assert ex2["safety_result"] in ("approved", "projected", "rejected")
