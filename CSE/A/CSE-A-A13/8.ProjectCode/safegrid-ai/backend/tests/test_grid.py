"""Grid layer tests. Require pandapower (skipped otherwise)."""
import pytest

pytest.importorskip("pandapower")

from app.grid.network import DEFAULT_NODES, NetworkSpec, create_network  # noqa: E402
from app.grid.simulator import GridSimulator  # noqa: E402
from app.safety import Setpoint  # noqa: E402


def test_network_structure():
    net, emap = create_network(NetworkSpec())
    assert len(net.bus) == 5 and len(net.line) == 3 and len(net.trafo) == 1
    assert set(emap.load_idx) == {n.node_id for n in DEFAULT_NODES}
    assert set(emap.storage_idx) == set(emap.sgen_idx) == set(emap.load_idx)


def test_power_flow_converges_and_balances():
    sim = GridSimulator()
    sim.apply_exogenous({"node_1": 3, "node_2": 1, "node_3": 6}, {"node_1": 0, "node_2": 0, "node_3": 0}, 5.0)
    trial, _ = sim.commit({}, 15)
    assert trial.converged
    # import from the external grid covers the load (plus small losses)
    assert trial.ext_grid_kw == pytest.approx(10.0, abs=0.5)
    assert all(0.9 < v < 1.1 for v in trial.bus_vm.values())
    assert abs(trial.balance_residual_kw) < 0.5


def test_trial_does_not_change_committed_state():
    sim = GridSimulator()
    sim.apply_exogenous({"node_1": 3, "node_2": 1, "node_3": 6}, {"node_1": 4, "node_2": 0, "node_3": 10}, 5.0)
    sim.commit({}, 15)
    before = sim.snapshot()["totals"]["ext_grid_kw"]
    t = sim.trial({"node_3": Setpoint(storage_kw=10.0)})
    assert t.ext_grid_kw > before + 5
    again = sim.trial({})
    assert again.ext_grid_kw == pytest.approx(before, abs=1e-6)


def test_battery_soc_integration_respects_efficiency():
    sim = GridSimulator()
    sim.apply_exogenous({"node_1": 3, "node_2": 1, "node_3": 6}, {"node_1": 0, "node_2": 0, "node_3": 0}, 5.0)
    soc0 = sim.nodes["node_1"].soc
    sim.commit({"node_1": Setpoint(storage_kw=4.0)}, 60)
    gained_kwh = (sim.nodes["node_1"].soc - soc0) * 10.0
    assert 0 < gained_kwh <= 4.0  # efficiency losses: never more than the energy delivered


def test_reduced_ampacity_overloads_line():
    spec = NetworkSpec(line_max_i_ka={"L0_2": 0.009})
    sim = GridSimulator(spec)
    sim.apply_exogenous({"node_1": 3, "node_2": 1, "node_3": 6}, {"node_1": 0, "node_2": 0, "node_3": 0}, 5.0)
    trial, _ = sim.commit({"node_2": Setpoint(storage_kw=7.4)}, 15)
    assert trial.line_loading["L0_2"] > 100.0


def test_topology_has_all_nodes_and_edges():
    topo = GridSimulator().topology()
    assert {e["id"] for e in topo["edges"]} == {"T0", "L0_1", "L0_2", "L1_3"}
    assert len(topo["devices"]) == 3
