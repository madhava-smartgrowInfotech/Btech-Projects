"""Synthetic grid used to unit-test the shield without pandapower.

Model: node exchange E [kW] -> bus voltage 1.0 - kv*E, line loading = |E| * kl [%], ext grid = E.
"""
from app.models.actions import EnergyAction
from app.safety import ConstraintConfig, GridTrial, NodeLimits, NodeView, Setpoint, SymbolicSafetyShield


def limits(**kw):
    base = dict(max_import_kw=15, max_export_kw=8, max_generation_kw=10, max_load_kw=20,
                storage_capacity_kwh=10, max_charge_kw=5, max_discharge_kw=5)
    base.update(kw)
    return NodeLimits(**base)


def make_cfg(lim=None, **kw):
    return ConstraintConfig(node_limits={"node_1": lim or limits()}, max_grid_import_kw=200, max_grid_export_kw=200, **kw)


def make_node(load=2.0, pv=0.0, soc=0.5, available=True):
    return NodeView("node_1", "prosumer_01", load, pv, soc, available)


class FakeGrid:
    def __init__(self, node, kv=0.004, kl=4.0, converged=True):
        self.node, self.kv, self.kl, self.converged = node, kv, kl, converged
        self.calls = 0

    def trial(self, sp: Setpoint) -> GridTrial:
        self.calls += 1
        e = (self.node.load_kw - sp.shift_kw) + sp.storage_kw - (self.node.pv_kw - sp.curtail_kw)
        return GridTrial(self.converged, {"bus_1": 1.0 - self.kv * e}, {"L01": abs(e) * self.kl}, {"T0": abs(e)},
                         ext_grid_kw=e, node_exchange_kw={"node_1": e})


def action(kind="charge_battery", kw=2.0, dur=15, target=None, conf=0.9, agent="prosumer_01", reasons=None):
    return EnergyAction(agent_id=agent, action_type=kind, power_kw=kw, duration_minutes=dur,
                        target_node=target, reason_codes=reasons or ["TEST"], confidence=conf)


def run(act, node=None, cfg=None, grid=None, dt=15):
    node = node or make_node()
    cfg = cfg or make_cfg()
    grid = grid or FakeGrid(node)
    shield = SymbolicSafetyShield(cfg)
    return shield.evaluate(act, node, trial=grid.trial, current=grid.trial(Setpoint()), dt_minutes=dt,
                           known_agents={"prosumer_01"}, known_nodes={"node_1", "node_2"})
