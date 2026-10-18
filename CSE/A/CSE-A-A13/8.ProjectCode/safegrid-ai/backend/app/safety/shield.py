"""Symbolic Safety Shield.

Deterministic, LLM-independent gate between a proposed EnergyAction and the simulated grid.
Every action is APPROVED, PROJECTED (scaled to the largest safe value) or REJECTED. The original
request is always preserved in the returned decision for auditing.

Only the fields of `EnergyAction` are read; the shield never sees prompts, model output text or code.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from app.models.actions import EnergyAction
from app.safety import constraints as C
from app.safety import projector, validator
from app.safety.models import GridTrial, NodeView, Setpoint, ShieldDecision, ShieldStatus, Violation

TrialFn = Callable[[Setpoint], GridTrial]


class SymbolicSafetyShield:
    def __init__(self, config: C.ConstraintConfig):
        self.cfg = config

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="milliseconds")

    def _checks(self, violations: list[Violation], grid_evaluated: bool) -> list[dict]:
        failed = {C.CHECK_OF.get(v.code, "STRUCTURE") for v in violations}
        out = []
        for name in C.CHECK_ORDER:
            if name in ("POWER_FLOW", "VOLTAGE", "LINE_LOADING", "TRANSFORMER", "GRID_LIMITS") and not grid_evaluated and name not in failed:
                out.append({"name": name, "passed": None})  # not evaluated (rejected earlier)
            else:
                out.append({"name": name, "passed": name not in failed})
        return out

    def _decision(self, status, action, validated, violations, corrections, sp, safe_kw,
                  before: GridTrial, after: GridTrial, grid_evaluated) -> ShieldDecision:
        return ShieldDecision(
            status=status,
            requested_action=action.model_dump(),
            validated_action=validated.model_dump() if validated is not None else None,
            violations=violations,
            corrections=corrections,
            checks=self._checks(violations, grid_evaluated),
            requested_power_kw=action.power_kw,
            safe_power_kw=safe_kw,
            setpoint=sp,
            grid_before=before.summary(),
            grid_after=after.summary(),
            after_trial=after,
            timestamp=self._now(),
        )

    # ------------------------------------------------------------------ public API
    def evaluate(self, action: EnergyAction, node: NodeView | None, *, trial: TrialFn, current: GridTrial,
                 dt_minutes: int, known_agents: set[str], known_nodes: set[str]) -> ShieldDecision:
        cfg = self.cfg
        dt_h = dt_minutes / 60.0
        lim = cfg.node_limits.get(node.node_id) if node is not None else None

        # 1. structural / sanity checks -> reject
        sv = validator.structural_violations(action, node, lim, cfg, known_agents, known_nodes)
        if sv:
            return self._decision(ShieldStatus.REJECTED, action, None, sv, [], Setpoint(), 0.0, current, current, False)

        # 2. idle is always safe (still recorded)
        if action.action_type == "idle" or action.power_kw <= validator.EPS:
            validated = action.model_copy(update={"duration_minutes": dt_minutes})
            corr = self._duration_correction(action, dt_minutes)
            return self._decision(ShieldStatus.APPROVED, action, validated, [], corr, Setpoint(), 0.0, current, current, False)

        sp_req = validator.resolve_setpoint(action.action_type, action.power_kw, node)
        base_local = validator.local_violations(Setpoint(), node, lim, dt_h)
        base_grid = validator.check_grid(current, cfg)

        def local_new(sp: Setpoint) -> list[Violation]:
            return validator.new_violations(validator.local_violations(sp, node, lim, dt_h), base_local, cfg.attribution_tol)

        def grid_new(t: GridTrial) -> list[Violation]:
            return validator.new_violations(validator.check_grid(t, cfg), base_grid, cfg.attribution_tol)

        # 3. evaluate the request exactly as proposed
        v_local = local_new(sp_req)
        v_grid: list[Violation] = []
        trial_req: GridTrial | None = None
        if not v_local:
            trial_req = trial(sp_req)
            v_grid = grid_new(trial_req)
        violations = v_local + v_grid
        grid_evaluated = trial_req is not None

        if not violations:
            validated = action.model_copy(update={"duration_minutes": dt_minutes})
            return self._decision(ShieldStatus.APPROVED, action, validated, [], self._duration_correction(action, dt_minutes),
                                  sp_req, action.power_kw, current, trial_req, True)

        # 4. projection: largest safe lam (local limits first - cheap - then power-flow limits)
        lam = projector.bisect_max(lambda l: not local_new(sp_req.scaled(l)), 1.0, 40)
        if lam > 0:
            def grid_ok(l: float) -> bool:
                return not grid_new(trial(sp_req.scaled(l)))
            if not grid_ok(lam):
                lam = projector.bisect_max(grid_ok, lam, 14)
                grid_evaluated = True

        final_action, final_trial, sp_final, safe_kw = None, None, Setpoint(), 0.0
        for _ in range(4):  # defensive: re-verify the exact, rounded action that would be executed
            if lam <= 0:
                break
            safe_kw = projector.floor_to(validator.projected_power_kw(action.action_type, action.power_kw, node, lam))
            cand = action.model_copy(update={"power_kw": safe_kw, "duration_minutes": dt_minutes})
            sp_c = validator.resolve_setpoint(cand.action_type, cand.power_kw, node)
            if local_new(sp_c):
                lam *= 0.999
                continue
            t_c = trial(sp_c)
            if grid_new(t_c):
                lam *= 0.999
                continue
            final_action, final_trial, sp_final = cand, t_c, sp_c
            grid_evaluated = True
            break

        rejected = (
            final_action is None
            or sp_final.magnitude() < cfg.min_action_kw
            or not self._direction_ok(action, node, sp_final)
        )
        if rejected:
            if final_action is not None and not self._direction_ok(action, node, sp_final):
                violations = violations + [Violation(C.DIRECTION_UNATTAINABLE, node.node_id, action.power_kw, 0.0, "kW",
                                                      "requested import/export direction cannot be reached safely", action.power_kw)]
            return self._decision(ShieldStatus.REJECTED, action, None, violations, [], Setpoint(), 0.0, current, current, grid_evaluated)

        corrections = [{"field": "power_kw", "from": action.power_kw, "to": safe_kw,
                        "reason": sorted({v.code for v in violations})}]
        corrections += self._duration_correction(action, dt_minutes)
        return self._decision(ShieldStatus.PROJECTED, action, final_action, violations, corrections,
                              sp_final, safe_kw, current, final_trial, True)

    # ------------------------------------------------------------------ internals
    @staticmethod
    def _duration_correction(action: EnergyAction, dt_minutes: int) -> list[dict]:
        if action.duration_minutes == dt_minutes:
            return []
        return [{"field": "duration_minutes", "from": action.duration_minutes, "to": dt_minutes,
                 "reason": ["DURATION_ALIGNED_TO_STEP"]}]

    @staticmethod
    def _direction_ok(action: EnergyAction, node: NodeView, sp: Setpoint) -> bool:
        """An import (export) target must still be an import (export) after projection."""
        if action.action_type not in ("import_power", "export_power"):
            return True
        e = validator.neutral_exchange_kw(node) + sp.storage_kw
        tol = 1e-6
        return e >= -tol if action.action_type == "import_power" else e <= tol
