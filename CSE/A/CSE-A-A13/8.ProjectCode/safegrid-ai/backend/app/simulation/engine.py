"""SimulationEngine: one run of one scenario.

Per step:
  exogenous inputs -> agents perceive -> agents propose (LLM/mock/fallback) -> coordinator detects conflicts
  -> Symbolic Safety Shield validates each proposal sequentially against the cumulative grid state
  -> only validated setpoints are committed to the pandapower simulation -> events, metrics, persistence.

Agents never touch the grid. The shield never imports agents/LLM code.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from app.agents.explain import attach_safety, build_explanation
from app.agents.manager import AgentManager
from app.config import Settings, get_settings
from app.database.store import Store
from app.grid.network import NetworkSpec
from app.grid.simulator import GridSimulator
from app.llm.provider import build_provider
from app.models.schemas import RunConfig
from app.safety import ConstraintConfig, GridTrial, Setpoint, ShieldDecision, ShieldStatus, SymbolicSafetyShield
from app.safety import validator
from app.safety.events import GENESIS, SafetyEvent, fingerprint, verify_chain
from app.simulation import coordinator
from app.simulation.scenarios import ScenarioDef, get_scenario
from app.simulation.timestep import Profiles, build_timeline

Emit = Callable[[dict[str, Any]], Awaitable[None]]

EXPORT_CREDIT_RATIO = 0.6  # illustrative feed-in credit as a fraction of the import price


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def build_constraints(settings: Settings, spec: NetworkSpec, overrides: dict[str, Any] | None) -> ConstraintConfig:
    cfg = ConstraintConfig(
        v_min=settings.voltage_min, v_max=settings.voltage_max,
        line_max_loading_pct=settings.line_max_loading_pct, trafo_max_loading_pct=settings.trafo_max_loading_pct,
        node_limits={n.node_id: n.limits for n in spec.nodes})
    return cfg.with_overrides(overrides)


class SimulationEngine:
    def __init__(self, config: RunConfig, settings: Settings | None = None, store: Store | None = None,
                 run_id: str | None = None, emit: Emit | None = None):
        self.settings = settings or get_settings()
        self.config = config
        self.store = store
        self.emit = emit
        self.run_id = run_id or f"run_{uuid.uuid4().hex[:10]}"
        self.scenario: ScenarioDef = get_scenario(config.scenario_id)
        sc = self.scenario
        self.dt = config.time_step_minutes
        self.n_steps = config.steps or sc.n_steps

        socs = {**sc.initial_soc, **(config.initial_soc or {})}
        self.spec = NetworkSpec(line_length_scale=sc.line_length_scale, ext_grid_vm_pu=sc.ext_grid_vm_pu,
                                line_max_i_ka=dict(sc.line_max_i_ka)).with_initial_soc(socs)
        self.sim = GridSimulator(self.spec)
        self.sim.set_dt(self.dt)
        self.cfg = build_constraints(self.settings, self.spec, config.constraint_overrides)
        self.shield = SymbolicSafetyShield(self.cfg)

        self.timeline = build_timeline(sc.start_time, self.n_steps, self.dt)
        self.profiles = Profiles(config.seed, self.spec.nodes, self.timeline, sc.load_scale, sc.pv_scale,
                                 sc.price_scale, sc.ev_mode)
        unsafe = sc.unsafe_rate if config.unsafe_rate is None else config.unsafe_rate
        faults = list(sc.faults) if config.inject_faults else []
        self.provider = build_provider(config.provider, self.settings, config.seed, unsafe, faults)
        self.manager = AgentManager(self.spec.nodes, self.provider, self.settings.llm_timeout_s, config.agents)

        self.known_agents = {n.agent_id for n in self.spec.nodes}
        self.known_nodes = {n.node_id for n in self.spec.nodes}
        self.step_index = 0
        self.status = "idle"  # idle | running | paused | stopped | completed | failed
        self.rows: list[dict[str, Any]] = []
        self.safety_events: list[SafetyEvent] = []
        self.event_log: list[dict[str, Any]] = []
        self._stop = asyncio.Event()
        self._event_seq = 0
        self._prev_hash = GENESIS
        self._registered = False
        self.totals = self._fresh_totals()
        self.summary: dict[str, Any] | None = None

    # ------------------------------------------------------------------ bookkeeping
    @staticmethod
    def _fresh_totals() -> dict[str, Any]:
        return {"proposals": 0, "approved": 0, "projected": 0, "rejected": 0, "idle": 0,
                "unshielded_violation_steps": 0, "unshielded_violations": 0, "no_action_violation_steps": 0,
                "caused_violation_steps": 0, "caused_violations": 0,
                "executed_violation_steps": 0, "executed_violations": 0,
                "voltage_violation_steps": 0, "line_overload_events": 0, "trafo_overload_events": 0,
                "power_flow_failures": 0, "cost": 0.0, "import_kwh": 0.0, "export_kwh": 0.0,
                "pv_available_kwh": 0.0, "curtailed_kwh": 0.0, "charged_kwh": 0.0, "discharged_kwh": 0.0,
                "losses_kwh": 0.0, "fallbacks": 0, "llm_latency_ms_sum": 0.0, "decisions": 0,
                "conflicts": 0, "step_time_ms_sum": 0.0, "min_voltage": None, "max_voltage": None,
                "max_line_loading": 0.0}

    def register(self) -> None:
        if self._registered or self.store is None:
            return
        self.store.create_run(self.run_id, self.config.model_dump(), self.resolved())
        self._registered = True

    def resolved(self) -> dict[str, Any]:
        return {"scenario": self.scenario.to_dict(), "steps": self.n_steps, "time_step_minutes": self.dt,
                "seed": self.config.seed, "provider": self.provider.describe(),
                "constraints": self.cfg.to_dict(), "faults_injected": bool(self.config.inject_faults and self.scenario.faults)}

    async def _publish(self, event_type: str, data: dict[str, Any], persist: bool = True) -> None:
        ev = {"type": event_type, "run_id": self.run_id, "timestamp": _now(), "data": data}
        self.event_log.append(ev)
        if len(self.event_log) > 2000:
            self.event_log = self.event_log[-2000:]
        if persist and self.store is not None:
            self.store.add_event(self.run_id, {"step": data.get("step", self.step_index), "event_type": event_type, **ev})
        if self.emit is not None:
            try:
                await self.emit(ev)
            except Exception:  # a broken client must never break the simulation
                pass

    def _record_safety(self, step: int, sim_time: str, payload: dict[str, Any]) -> SafetyEvent:
        self._event_seq += 1
        ev = SafetyEvent.create(self._event_seq, self.run_id, step, sim_time, _now(), payload, self._prev_hash)
        self._prev_hash = ev.hash
        self.safety_events.append(ev)
        if self.store is not None:
            self.store.add_safety_event(self.run_id, {"step": step, "status": payload["status"], **ev.to_dict()})
        return ev

    # ------------------------------------------------------------------ observation
    def _observation(self, i: int, current: GridTrial, exo) -> dict[str, Any]:
        nodes = {}
        for nid, ns in self.sim.nodes.items():
            bus_name = self.sim.emap.bus_name[self.sim.emap.node_bus[nid]]
            nodes[nid] = {"load_kw": ns.load_kw, "pv_kw": ns.pv_kw, "soc": ns.soc, "storage_available": ns.storage_available,
                          "voltage_pu": current.bus_vm.get(bus_name, 1.0), "exchange_kw": current.node_exchange_kw.get(nid, 0.0)}
        return {"step": i, "time": self.timeline[i].label, "dt_minutes": self.dt, "nodes": nodes,
                "limits": self.cfg.node_limits, "constraints": self.cfg, "price": exo.price,
                "price_stats": self.profiles.price_stats, "weather": exo.weather, "trial_summary": current.summary()}

    def _violations_of(self, trial: GridTrial) -> list:
        if not trial.converged:
            return [None]
        return validator.check_grid(trial, self.cfg)

    def _validate_and_commit(self, decisions, ordered, current: GridTrial):
        """CPU-bound part of a step (shield + power flow + commit); runs in a worker thread."""
        # what would have happened WITHOUT the shield (counterfactual, for the evaluation only)
        raw_sp: dict[str, Setpoint] = {}
        for d in decisions:
            node = self.sim.node_view(d.node_id)
            raw_sp[d.node_id] = validator.resolve_setpoint(d.action.action_type, d.action.power_kw, node)
        raw_trial = self.sim.trial(raw_sp)
        raw_viol = self._violations_of(raw_trial)

        cumulative: dict[str, Setpoint] = {}
        trial_now = current
        results: dict[str, dict[str, Any]] = {}
        for d in ordered:
            node = self.sim.node_view(d.node_id)

            def trial_fn(sp: Setpoint, _nid=d.node_id) -> GridTrial:
                return self.sim.trial({**cumulative, _nid: sp})

            if self.config.shield_enabled:
                dec = self.shield.evaluate(d.action, node, trial=trial_fn, current=trial_now, dt_minutes=self.dt,
                                           known_agents=self.known_agents, known_nodes=self.known_nodes)
            else:  # ablation arm: proposal is applied as requested (no safety layer)
                dec = ShieldDecision(ShieldStatus.APPROVED, d.action.model_dump(), d.action.model_dump(), [], [],
                                     [], d.action.power_kw, d.action.power_kw, raw_sp[d.node_id], current.summary(),
                                     current.summary(), None, _now())
            if dec.status in (ShieldStatus.APPROVED, ShieldStatus.PROJECTED) and dec.setpoint.magnitude() > 0:
                cumulative[d.node_id] = dec.setpoint
                if dec.after_trial is not None and dec.after_trial.converged:
                    trial_now = dec.after_trial
            results[d.agent_id] = dec.to_dict()

        final_trial, stats = self.sim.commit(cumulative, self.dt)
        return results, raw_viol, final_trial, stats

    # ------------------------------------------------------------------ one step
    async def step(self) -> dict[str, Any]:
        import time as _time
        t0 = _time.perf_counter()
        i = self.step_index
        if i >= self.n_steps:
            raise RuntimeError("simulation already finished")
        ts = self.timeline[i]
        exo = self.profiles.at(i)
        self.sim.apply_exogenous(exo.load_kw, exo.pv_kw, exo.price, exo.storage_available)
        current = self.sim.trial({})
        obs = self._observation(i, current, exo)

        contexts = await self.manager.perceive_all(obs)
        decisions = await self.manager.decide_all(contexts)
        conflicts = coordinator.detect_conflicts(decisions)
        ordered = coordinator.order_decisions(decisions, i)

        results, raw_viol, final_trial, stats = await asyncio.to_thread(self._validate_and_commit, decisions, ordered, current)
        final_viol = self._violations_of(final_trial)
        snapshot = self.sim.snapshot()

        # ---- per-agent records + events
        agent_rows = []
        for d in decisions:
            sd = results[d.agent_id]
            expl = attach_safety(build_explanation(d.context, d.action, d.decision_source, d.fallback_reason), sd)
            executed = sd["validated_action"]["power_kw"] if sd["validated_action"] else 0.0
            self.manager.agents[d.agent_id].remember({
                "step": i, "action_type": d.action.action_type, "requested_kw": d.action.power_kw,
                "shield_status": sd["status"], "executed_kw": executed})
            row = {"agent_id": d.agent_id, "node_id": d.node_id, "proposal": d.action.model_dump(),
                   "decision_source": d.decision_source, "latency_ms": round(d.latency_ms, 2),
                   "fallback_reason": d.fallback_reason, "shield": sd, "explanation": expl,
                   "executed_action": sd["validated_action"], "executed_power_kw": executed}
            agent_rows.append(row)
            self.totals["proposals"] += 1
            self.totals[sd["status"]] += 1
            if d.action.action_type == "idle":
                self.totals["idle"] += 1
            self.totals["decisions"] += 1
            self.totals["llm_latency_ms_sum"] += d.latency_ms
            if d.decision_source == "fallback":
                self.totals["fallbacks"] += 1
            await self._publish("agent_action", {"step": i, "time": ts.label, "agent_id": d.agent_id, "node_id": d.node_id,
                                                 "proposal": row["proposal"], "decision_source": d.decision_source,
                                                 "latency_ms": row["latency_ms"], "shield_status": sd["status"],
                                                 "executed_power_kw": executed})
            if sd["status"] != "approved" or d.decision_source in ("fallback", "injected"):
                payload = {"event_type": "SAFETY_INTERVENTION" if sd["status"] != "approved" else "AGENT_ANOMALY",
                           "status": sd["status"], "agent_id": d.agent_id, "node_id": d.node_id,
                           "requested_action": sd["requested_action"], "validated_action": sd["validated_action"],
                           "violations": sd["violations"], "corrections": sd["corrections"], "checks": sd["checks"],
                           "decision_source": d.decision_source, "fallback_reason": d.fallback_reason,
                           "grid_state_before": sd["grid_state_before"], "grid_state_after": sd["grid_state_after"]}
                ev = self._record_safety(i, ts.label, payload)
                if sd["status"] != "approved":
                    await self._publish("safety_intervention", {"step": i, "time": ts.label, **ev.to_dict()}, persist=False)

        for c in conflicts:
            self.totals["conflicts"] += 1
            await self._publish("conflict_detected", {"step": i, "time": ts.label, **c})

        # ---- metrics
        tot = snapshot.get("totals", {})
        dt_h = self.dt / 60.0
        pf_ok = final_trial.converged
        if not pf_ok:
            self.totals["power_flow_failures"] += 1
        if raw_viol:
            self.totals["unshielded_violation_steps"] += 1
            self.totals["unshielded_violations"] += len(raw_viol)
        real_final = [v for v in final_viol if v is not None]
        base_viol = self._violations_of(current)
        if base_viol:
            self.totals["no_action_violation_steps"] += 1
        # violations attributable to the applied actions (new or worse than the no-action grid state)
        caused = [v for v in final_viol if v is None] if not pf_ok and current.converged else \
            validator.new_violations(real_final, [v for v in base_viol if v is not None], self.cfg.attribution_tol)
        if caused:
            self.totals["caused_violation_steps"] += 1
            self.totals["caused_violations"] += len(caused)
        if final_viol:
            self.totals["executed_violation_steps"] += 1
            self.totals["executed_violations"] += len(final_viol)
        if pf_ok:
            vm = [v for v in final_trial.bus_vm.values()]
            if any(v < self.cfg.v_min - 1e-9 or v > self.cfg.v_max + 1e-9 for v in vm):
                self.totals["voltage_violation_steps"] += 1
            self.totals["line_overload_events"] += sum(1 for x in final_trial.line_loading.values() if x > self.cfg.line_max_loading_pct + 1e-6)
            self.totals["trafo_overload_events"] += sum(1 for x in final_trial.trafo_loading.values() if x > self.cfg.trafo_max_loading_pct + 1e-6)
            mn, mx = min(vm), max(vm)
            self.totals["min_voltage"] = mn if self.totals["min_voltage"] is None else min(self.totals["min_voltage"], mn)
            self.totals["max_voltage"] = mx if self.totals["max_voltage"] is None else max(self.totals["max_voltage"], mx)
            self.totals["max_line_loading"] = max(self.totals["max_line_loading"], max(final_trial.line_loading.values(), default=0.0))
            ext = final_trial.ext_grid_kw
            imp, exp_ = max(ext, 0.0) * dt_h, max(-ext, 0.0) * dt_h
            self.totals["import_kwh"] += imp
            self.totals["export_kwh"] += exp_
            self.totals["cost"] += exo.price * imp - exo.price * EXPORT_CREDIT_RATIO * exp_
            self.totals["losses_kwh"] += final_trial.losses_kw * dt_h
        for k in ("pv_available_kwh", "curtailed_kwh", "charged_kwh", "discharged_kwh"):
            self.totals[k] += stats[k]

        step_ms = (_time.perf_counter() - t0) * 1000.0
        self.totals["step_time_ms_sum"] += step_ms
        row = {"step": i, "time": ts.label, "price": round(exo.price, 3), "weather": exo.weather,
               "grid": snapshot, "agents": agent_rows, "conflicts": conflicts,
               "counts": {"approved": sum(1 for a in agent_rows if a["shield"]["status"] == "approved"),
                          "projected": sum(1 for a in agent_rows if a["shield"]["status"] == "projected"),
                          "rejected": sum(1 for a in agent_rows if a["shield"]["status"] == "rejected")},
               "violations_without_shield": len(raw_viol), "violations_executed": len(real_final) + (0 if pf_ok else 1),
               "violations_caused": len(caused),
               "step_ms": round(step_ms, 2)}
        self.rows.append(row)
        if self.store is not None:
            self.store.add_step(self.run_id, i, row)
        await self._publish("grid_update", {"step": i, "time": ts.label, "price": row["price"], "grid": snapshot,
                                            "counts": row["counts"]}, persist=False)
        self.step_index += 1
        return row

    # ------------------------------------------------------------------ preview / dry-run (no commit)
    def preview(self) -> dict[str, Any]:
        """Grid snapshot for the current (not yet executed) step, so the dashboard has something to show at step 0."""
        if self.sim.snapshot():
            return self.sim.snapshot()
        i = min(self.step_index, self.n_steps - 1)
        exo = self.profiles.at(i)
        self.sim.apply_exogenous(exo.load_kw, exo.pv_kw, exo.price, exo.storage_available)
        self.sim.commit({}, self.dt)
        return self.sim.snapshot()

    async def dry_run(self, agent_id: str, action=None) -> dict[str, Any]:
        """Ask an agent for its current proposal (or take an operator-crafted one) and validate it against the current
        state WITHOUT executing it. Used by the API and the Safety Shield page."""
        if agent_id not in self.known_agents:
            raise KeyError(agent_id)
        i = min(self.step_index, self.n_steps - 1)
        exo = self.profiles.at(i)
        self.sim.apply_exogenous(exo.load_kw, exo.pv_kw, exo.price, exo.storage_available)
        current = await asyncio.to_thread(self.sim.trial, {})
        obs = self._observation(i, current, exo)
        agent = self.manager.agents[agent_id]
        ctx = await agent.perceive(obs)
        source, latency, reason = "operator", 0.0, None
        if action is None:
            d = await agent.decide(ctx)
            action, source, latency, reason = d.action, d.decision_source, d.latency_ms, d.fallback_reason
        node = self.sim.node_view(agent.node_id)
        dec = await asyncio.to_thread(
            self.shield.evaluate, action, node, trial=lambda sp: self.sim.trial({agent.node_id: sp}), current=current,
            dt_minutes=self.dt, known_agents=self.known_agents, known_nodes=self.known_nodes)
        sd = dec.to_dict()
        expl = attach_safety(build_explanation(ctx, action, source, reason), sd)
        return {"agent_id": agent_id, "step": i, "time": self.timeline[i].label, "proposal": action.model_dump(),
                "decision_source": source, "latency_ms": round(latency, 2), "fallback_reason": reason, "shield": sd,
                "explanation": expl, "executed": False, "note": "dry run - nothing was applied to the simulation"}

    # ------------------------------------------------------------------ run control
    def _summarise(self) -> dict[str, Any]:
        t = self.totals
        n = max(t["decisions"], 1)
        pv = t["pv_available_kwh"]
        cap = sum(x.limits.storage_capacity_kwh for x in self.spec.nodes)
        return {
            "steps_run": self.step_index, "proposals": t["proposals"], "approved": t["approved"], "projected": t["projected"],
            "rejected": t["rejected"], "idle": t["idle"], "intervention_rate": round((t["projected"] + t["rejected"]) / n, 4),
            "violations_without_shield": t["unshielded_violations"], "violation_steps_without_shield": t["unshielded_violation_steps"],
            "violations_executed": t["executed_violations"], "violation_steps_executed": t["executed_violation_steps"],
            "violation_steps_no_action": t["no_action_violation_steps"],
            "violations_caused_by_actions": t["caused_violations"], "violation_steps_caused_by_actions": t["caused_violation_steps"],
            "voltage_violation_steps": t["voltage_violation_steps"], "line_overload_events": t["line_overload_events"],
            "trafo_overload_events": t["trafo_overload_events"], "power_flow_failures": t["power_flow_failures"],
            "total_cost": round(t["cost"], 3), "import_kwh": round(t["import_kwh"], 3), "export_kwh": round(t["export_kwh"], 3),
            "pv_available_kwh": round(pv, 3), "curtailed_kwh": round(t["curtailed_kwh"], 3),
            "renewable_utilization": round(1.0 - t["curtailed_kwh"] / pv, 4) if pv > 1e-9 else None,
            "battery_throughput_kwh": round(t["charged_kwh"] + t["discharged_kwh"], 3),
            "battery_utilization": round((t["charged_kwh"] + t["discharged_kwh"]) / cap, 4) if cap else None,
            "losses_kwh": round(t["losses_kwh"], 3),
            "fallback_rate": round(t["fallbacks"] / n, 4), "avg_decision_latency_ms": round(t["llm_latency_ms_sum"] / n, 3),
            "avg_step_time_ms": round(t["step_time_ms_sum"] / max(self.step_index, 1), 3),
            "conflicts_detected": t["conflicts"],
            "min_voltage_pu": None if t["min_voltage"] is None else round(t["min_voltage"], 4),
            "max_voltage_pu": None if t["max_voltage"] is None else round(t["max_voltage"], 4),
            "max_line_loading_pct": round(t["max_line_loading"], 2),
            "safety_chain_valid": verify_chain(self.safety_events), "safety_events": len(self.safety_events),
        }

    def finish(self, status: str) -> dict[str, Any]:
        self.status = status
        self.summary = self._summarise()
        if self.store is not None and self._registered:
            self.store.finish_run(self.run_id, status, self.summary, fingerprint(self.safety_events))
        return self.summary

    def stop(self) -> None:
        self._stop.set()

    async def run(self, realtime: bool = False) -> dict[str, Any]:
        """Run remaining steps to completion (or until stop())."""
        self.register()
        self.status = "running"
        self._stop.clear()
        await self._publish("simulation_started", {"step": self.step_index, "config": self.config.model_dump(),
                                                   "steps": self.n_steps}, persist=False)
        try:
            while self.step_index < self.n_steps:
                if self._stop.is_set():
                    summary = self.finish("stopped")
                    await self._publish("simulation_stopped", {"step": self.step_index, "summary": summary}, persist=False)
                    return summary
                await self.step()
                if realtime and self.config.step_delay_s > 0:
                    await asyncio.sleep(self.config.step_delay_s)
            summary = self.finish("completed")
            await self._publish("simulation_complete", {"step": self.step_index, "summary": summary})
            return summary
        except Exception as e:  # surface failures instead of dying silently in a background task
            summary = self.finish("failed")
            summary["error"] = f"{type(e).__name__}: {e}"
            await self._publish("simulation_error", {"step": self.step_index, "error": summary["error"]}, persist=False)
            raise

    def reset_state(self) -> None:
        """Reset to step 0 (fresh grid, agents, counters) keeping the same configuration."""
        self.__init__(self.config, self.settings, self.store, None, self.emit)  # type: ignore[misc]
