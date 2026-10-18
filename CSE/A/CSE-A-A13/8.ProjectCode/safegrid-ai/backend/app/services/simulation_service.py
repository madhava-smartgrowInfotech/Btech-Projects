"""SimulationService: owns the current engine, background run task, experiments and the WebSocket hub.

Single-process, single-active-run design (documented limitation): suitable for a research demo, not multi-tenant use.
"""
from __future__ import annotations

import asyncio
import uuid
from typing import Any

from app.config import Settings, get_settings
from app.database.store import SQLiteStore, Store
from app.models.schemas import ExperimentRequest, RunConfig
from app.services.hub import ConnectionHub
from app.simulation.engine import SimulationEngine
from app.simulation.experiment import run_experiment
from app.simulation.scenarios import SCENARIOS


class SimulationService:
    def __init__(self, settings: Settings | None = None, store: Store | None = None):
        self.settings = settings or get_settings()
        self.store: Store = store or SQLiteStore(self.settings.database_url)
        self.hub = ConnectionHub()
        self.engine: SimulationEngine | None = None
        self.task: asyncio.Task | None = None
        self.jobs: dict[str, dict[str, Any]] = {}
        self._job_tasks: set[asyncio.Task] = set()

    # ---- engine lifecycle ----------------------------------------------------------------
    def default_config(self, **kw: Any) -> RunConfig:
        return RunConfig(seed=self.settings.default_seed, time_step_minutes=self.settings.default_time_step_minutes,
                         provider=self.settings.llm_provider if self.settings.llm_provider in ("mock", "api", "failing", "baseline") else "mock",
                         **kw)

    def _new_engine(self, config: RunConfig) -> SimulationEngine:
        return SimulationEngine(config, self.settings, self.store, emit=self.hub.broadcast)

    def ensure_engine(self) -> SimulationEngine:
        if self.engine is None:
            self.engine = self._new_engine(self.default_config())
        return self.engine

    @property
    def running(self) -> bool:
        return self.task is not None and not self.task.done()

    async def _cancel_task(self) -> None:
        if self.engine is not None:
            self.engine.stop()
        if self.task is not None and not self.task.done():
            try:
                await asyncio.wait_for(self.task, timeout=30)
            except (asyncio.TimeoutError, Exception):
                self.task.cancel()
        self.task = None

    async def start(self, config: RunConfig | None = None, resume: bool = False) -> SimulationEngine:
        if self.running:
            raise RuntimeError("a simulation is already running")
        if resume and self.engine is not None and self.engine.step_index < self.engine.n_steps:
            eng = self.engine
        else:
            eng = self._new_engine(config or self.default_config())
            self.engine = eng
        self.task = asyncio.create_task(self._run_guarded(eng))
        return eng

    async def _run_guarded(self, eng: SimulationEngine) -> None:
        try:
            await eng.run(realtime=True)
        except Exception:
            pass  # engine already published simulation_error

    async def stop(self) -> dict[str, Any]:
        await self._cancel_task()
        eng = self.ensure_engine()
        return self.status()

    async def reset(self, config: RunConfig | None = None) -> SimulationEngine:
        await self._cancel_task()
        cfg = config or (self.engine.config if self.engine else self.default_config())
        self.engine = self._new_engine(cfg)
        return self.engine

    async def step_once(self) -> dict[str, Any]:
        if self.running:
            raise RuntimeError("simulation is running; stop it before stepping manually")
        eng = self.ensure_engine()
        if eng.step_index >= eng.n_steps:
            raise IndexError("simulation finished; reset to run again")
        eng.register()
        eng.status = "paused"
        row = await eng.step()
        if eng.step_index >= eng.n_steps:
            summary = eng.finish("completed")
            await eng._publish("simulation_complete", {"step": eng.step_index, "summary": summary})
        return row

    async def run_scenario(self, scenario_id: str, config: RunConfig | None = None) -> dict[str, Any]:
        """Run a scenario to completion immediately (no playback delay) and make it the current run."""
        if scenario_id not in SCENARIOS:
            raise KeyError(scenario_id)
        if self.running:
            raise RuntimeError("a simulation is already running")
        base = config.model_dump() if config else self.default_config().model_dump()
        base["scenario_id"] = scenario_id
        base["step_delay_s"] = 0.0
        eng = self._new_engine(RunConfig(**base))
        self.engine = eng
        summary = await eng.run(realtime=False)
        return {"run_id": eng.run_id, "scenario_id": scenario_id, "summary": summary}

    def status(self) -> dict[str, Any]:
        eng = self.ensure_engine()
        return {"run_id": eng.run_id, "status": "running" if self.running else eng.status, "step": eng.step_index,
                "total_steps": eng.n_steps, "time": eng.timeline[min(eng.step_index, eng.n_steps - 1)].label,
                "scenario_id": eng.scenario.id, "seed": eng.config.seed, "provider": eng.provider.describe(),
                "shield_enabled": eng.config.shield_enabled, "ws_clients": self.hub.count,
                "summary": eng.summary or eng._summarise()}

    # ---- experiments --------------------------------------------------------------------------
    async def start_experiment(self, req: ExperimentRequest) -> dict[str, Any]:
        exp_id = f"exp_{uuid.uuid4().hex[:8]}"
        spec = req.model_dump()
        self.jobs[exp_id] = {"exp_id": exp_id, "status": "running", "spec": spec, "error": None}

        async def job() -> None:
            try:
                res = await run_experiment(req.scenarios, req.seeds, req.steps, req.arms, req.time_step_minutes, self.settings)
                self.store.save_experiment(exp_id, spec, res)
                self.jobs[exp_id]["status"] = "completed"
            except Exception as e:
                self.jobs[exp_id].update(status="failed", error=f"{type(e).__name__}: {e}")

        t = asyncio.create_task(job())
        self._job_tasks.add(t)
        t.add_done_callback(self._job_tasks.discard)
        return self.jobs[exp_id]
