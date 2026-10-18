"""Chapter 8: Results and output screens. Every table value is read from facts.py (the real experiment JSON)."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .content_shared import BASE_COMPARE, GAPS, HEADLINE, OUTCOMES
from .refs import n

A = F.ARMS
SC = F.SCENARIOS


def nice(sc):
    return sc.replace("_", " ")


def mm(arm, key, d=2):
    r = F.OVERALL[arm].get(key)
    return "n/a" if not r else f"{r['mean']:.{d}f}"


def sm(sc, arm, key, d=2):
    r = F.BYSC[sc][arm].get(key)
    return "n/a" if not r else f"{r['mean']:.{d}f}"


def sv(sc, arm, key):
    r = F.BYSC[sc][arm].get(key)
    return None if not r else r["mean"]


def screen(name_literal_path, caption, width=5.7):
    return FIG(name_literal_path, caption, F.shot_w(name_literal_path, width, 3.7))


OVERALL_ROWS = [
    ("Steps with violations caused by actions (of 24)", "violation_steps_caused_by_actions", 2),
    ("Violations caused by actions", "violations_caused_by_actions", 2),
    ("Violations the raw proposals would cause", "violations_without_shield", 2),
    ("Steps with pre-existing stress (every agent idle)", "violation_steps_no_action", 2),
    ("Steps with any violation after execution", "violation_steps_executed", 2),
    ("Voltage violation steps (strict counter)", "voltage_violation_steps", 2),
    ("Line overload events (strict counter)", "line_overload_events", 2),
    ("Transformer overload events", "trafo_overload_events", 2),
    ("Energy cost per run, INR (illustrative tariff)", "total_cost", 1),
    ("Renewable utilisation", "renewable_utilization", 3),
    ("Battery utilisation (throughput / capacity)", "battery_utilization", 3),
    ("Shield intervention rate", "intervention_rate", 3),
    ("Fallback rate", "fallback_rate", 4),
    ("Mean decision latency, ms (mock provider)", "avg_decision_latency_ms", 3),
    ("Mean step time, ms", "avg_step_time_ms", 1),
]


def blocks():
    ov_rows = [[lab] + [mm(a, k, d) for a in A] for lab, k, d in OVERALL_ROWS]
    caused_rows = [[nice(s)] + [sm(s, a, "violation_steps_caused_by_actions") for a in A] for s in SC]
    caused_rows.append(["**all scenarios (mean)**"] + [f"**{mm(a, 'violation_steps_caused_by_actions')}**" for a in A])
    dec_rows = []
    for s in SC:
        dec_rows.append([nice(s), "72", sm(s, "safegrid_shielded", "approved", 1), sm(s, "safegrid_shielded", "projected", 1), sm(s, "safegrid_shielded", "rejected", 1),
                         sm(s, "safegrid_shielded", "violations_without_shield", 1), sm(s, "safegrid_shielded", "violation_steps_no_action", 1), sm(s, "safegrid_shielded", "total_cost", 1)])
    exec_rows = [[nice(s), sm(s, "safegrid_shielded", "violation_steps_no_action", 1)] + [sm(s, a, "violation_steps_executed", 1) for a in A] for s in SC]
    exec_rows.append(["**all scenarios (mean)**", f"**{mm('safegrid_shielded', 'violation_steps_no_action', 2)}**"] + [f"**{mm(a, 'violation_steps_executed')}**" for a in A])
    cost_rows = [[nice(s)] + [sm(s, a, "total_cost", 1) for a in A] + [sm(s, a, "renewable_utilization", 3) for a in A] for s in SC]

    hs = sv("high_solar", "safegrid_shielded", "renewable_utilization")
    hu = sv("high_solar", "agents_unshielded", "renewable_utilization")
    vs_ = sv("voltage_violation", "safegrid_shielded", "renewable_utilization")
    pk_b = sm("peak_demand", "baseline_rule", "violation_steps_executed")
    pk_s = sm("peak_demand", "safegrid_shielded", "violation_steps_executed")
    pk_u = sm("peak_demand", "agents_unshielded", "violation_steps_executed")
    ua_cost = sm("unsafe_ai_action", "agents_unshielded", "total_cost", 0)
    ua_bat = sm("unsafe_ai_action", "agents_unshielded", "battery_utilization", 1)

    p_dash = F.shot("04_dashboard.png")
    p_grid = F.shot("05_grid_view.png")
    p_agent = F.shot("06_agent_monitor.png")
    p_shield = F.shot("07_safety_shield.png")
    p_pf = F.shot("08_power_flow.png")
    p_scn = F.shot("09_scenarios.png")
    p_exp = F.shot("10_explainability.png")

    return [
        H1("CHAPTER 8: RESULTS AND OUTPUT SCREENS"),
        P("This chapter shows the console with real data (Section 8.1), reports the experiment that compares three control strategies on seven scenarios (8.2 to 8.7) and interprets it, "
          "including where the shield does not help (8.8 to 8.11). Every number was produced by running this repository; none is quoted from a paper."),
        H2("8.1 Application Output Screens"),
        P("All screens were captured from the running application at 1440 x 900 pixels in the dark theme and show one run: scenario `unsafe_ai_action`, agent brain *Mock LLM*, seed 42, instant playback, 12 of 12 steps. "
          "The scenario injects absurd and malformed proposals so that the shield has something to do."),
        screen(p_dash, "Dashboard after a completed run of the unsafe-action scenario"),
        P("The status reads *Completed 14:45* (*step 12 of 12*) and a badge reports *Audit chain valid, 13 events*. "
          "At the last step the tiles show generation 16.4 kW, load 5.3 kW, grid exchange -2.6 kW (a net export), voltage range 0.992 to 1.029 pu, worst line loading 12 %, "
          "**12 shield interventions out of 36 proposals**, **0 violations caused by actions** and renewable utilisation 100 %."),
        screen(p_grid, "Grid view: single-line diagram of the feeder"),
        P("The diagram is drawn from the live power-flow result: the external grid exports 2.6 kW, transformer T0 is 2 % loaded, buses B0, B1 and B3 are at 1.000, 1.013 and 1.029 pu, and lines L0_1, L1_3 and L0_2 are at 12 %, 9 % and 8 % loading. "
          "Rings and lines turn amber near a limit and red in violation; here all are green."),
        screen(p_agent, "Agent monitor: the three agents and the latest decision"),
        P("Each card reports node, state of charge, local voltage, exchange, latest proposal, shield result and decision source. "
          "`prosumer_01` proposed to export 2.16 kW and `renewable_01` 9.42 kW, both approved; `ev_01` (84 %, 0.992 pu) asked to charge at 11.10 kW and the shield marked it **Projected**, scaled down before execution. "
          "All three decisions came from the *Mock LLM* source."),
        screen(p_shield, "Safety shield: dry run of a 1,000 kW export, and the active constraints"),
        P("The left panel validates any crafted action against the current grid without applying it. `prosumer_01` is asked to *export power* 1,000 kW for 15 minutes and the shield answers **Rejected**: "
          "`POWER_LIMIT_EXCEEDED at node_1: requested power is implausibly large for this node (requested 1000.00 kW, allowed 60.00 kW)`, with 0.00 kW executed. "
          "The check chips show that the power-flow-based checks were not evaluated because rejection happened earlier. "
          "The right panel lists the enforced limits: 0.950 to 1.050 pu, 100 % line and transformer loading, 200 kW grid import and export, a 0.050 kW smallest useful action and per-node import, export and state-of-charge limits."),
        screen(p_pf, "Power flow: bus voltages and line loadings over the run"),
        P("The screen plots the AC power-flow results of the twelve steps (12:15 to 14:45): bus voltages stay between about 0.99 and 1.04 pu, inside the dashed 0.95 and 1.05 limits, "
          "and all line loadings stay below about 15 % against the 100 % limit. Six more charts follow below the capture."),
        screen(p_scn, "Scenarios: result of the strategy comparison"),
        P("This capture shows a short comparison with the screen's default settings (one seed, eight steps per run), so its numbers differ from the three-seed, 24-step experiment below. "
          "For the rule baseline, the agents without the shield and SafeGrid-AI it reports voltage violation steps 1, 3 and 0, line overload events 1, 1 and 0, and energy cost 103.7, 192.0 and 78.2 INR; "
          "SafeGrid-AI's shield intervention rate is 0.369. The chart shows no violations caused by actions for SafeGrid-AI."),
        screen(p_exp, "Explainability: proposal, shield decision and executed action for one agent"),
        P("For `prosumer_01` at 14:45 the screen shows the AI proposal (*export power* 2.16 kW, source *Mock LLM*, confidence 75 %), the shield decision (*Approved*, *No violations*) and the executed action (2.16 kW), "
          "ten green check chips, the factor *Surplus solar power is available* and the context the agent knew (for example solar 3.788 kW). No model chain-of-thought is requested or stored."),
        H2("8.2 Experimental Setup"),
        P("Three control strategies (arms) are compared on the three-node feeder of Chapter 5; all arms see identical inputs for a given scenario and seed."),
        TAB("Experimental setup", ["Item", "Value"],
            [["Scenarios", "7: normal, high solar, peak demand, battery stress, line congestion, voltage violation, unsafe AI action"],
             ["Seeds", "0, 1, 2 (three seeds per scenario and arm)"],
             ["Steps per run", "24 steps of 15 minutes (6 simulated hours) in every run"],
             ["Runs", f"{F.N_RUNS} = 7 scenarios x 3 arms x 3 seeds; 21 runs per arm; {F.SHIELDED_STEPS} steps per arm"],
             ["Arm 1: rule baseline", "Non-LLM time-of-use rules, no shield, no fault injection"],
             ["Arm 2: agents, no shield", "Agents with the mock provider and the scenario's injected faults; proposals applied exactly as requested"],
             ["Arm 3: SafeGrid-AI", "Same agents and faults, every proposal validated by the Symbolic Safety Shield"],
             ["Language model", "Deterministic seeded mock provider in every agent run; the real-model provider was not exercised"],
             ["Machine", F.MACHINE + "; the 63 runs took about ten minutes"],
             ["Tariff", "Illustrative time-of-use tariff of 3.8 to 9.0 INR per kWh; export credited at 60 % of the import price"]],
            widths=[1.8, 4.7], size=9.5),
        P("Two definitions matter. A violation is **caused by an action** when it is new, or worse than in the same step with every agent idle; this is what the shield is designed to prevent. "
          "A step has **pre-existing stress** when a limit is violated even with every agent idle; the shield is not designed to remove that. Results are means over seeds. "
          "Every run uses 24 steps, longer than the native length of the shorter scenarios (12 to 16 steps), whose injected faults occur early."),
        H2("8.3 Violations Caused by Executed Actions"),
        P(f"Over 21 runs of 24 steps, SafeGrid-AI caused **no** violation: 0 of {F.SHIELDED_STEPS} shielded steps. "
          f"The same agents without the shield caused {F.UNSHIELDED_CAUSED} violations in {F.UNSHIELDED_CAUSED_STEPS} steps; "
          f"the rule baseline, which has no safety layer either, caused {F.BASELINE_CAUSED} violations in {F.BASELINE_CAUSED_STEPS} steps, all in `line_congestion` and `peak_demand`."),
        TAB("Overall comparison of the three strategies (mean per run of 24 steps; 21 runs per strategy)", ["Metric", "Rule baseline", "Agents, no shield", "SafeGrid-AI"], ov_rows,
            widths=[3.1, 1.1, 1.2, 1.1], size=9, align=["l", "r", "r", "r"]),
        TAB("Steps with violations caused by actions, per scenario (mean of three seeds, of 24 steps)", ["Scenario", "Rule baseline", "Agents, no shield", "SafeGrid-AI"], caused_rows,
            widths=[2.0, 1.5, 1.6, 1.4], size=10, align=["l", "r", "r", "r"]),
        FIG(F.fig("fig_violations_by_scenario.png"), "Steps with violations caused by actions, per scenario and strategy (mean of three seeds)", 5.8),
        P("Without the shield the agents cause violations in every scenario, from 0.67 steps in `high_solar` to 11.33 in `line_congestion`; the injected faults of `unsafe_ai_action` give 4.33. "
          "The rule baseline is safe in five scenarios but fails in `line_congestion` (12.00 steps) and `peak_demand` (3.33): its rules charge the vehicle at the full available rate (`BASELINE_UNCONTROLLED_EV_CHARGING`) on a feeder with reduced ampacity. "
          "The shield brings the count to zero everywhere because it checks the consequences of an action, not its intention."),
        P("The strict counters in the overall table (voltage violation steps 3.14, line overload events 0.71) are not zero for SafeGrid-AI. They use a tighter tolerance than the shield (1e-9 pu against 1e-6 pu; 1e-6 % against 1e-4 %), "
          "and projection places a quantity exactly on its limit, so a step can be counted although the shield accepts it. The size of those excesses was not measured; the attribution counters are the primary evidence."),
        H2("8.4 What the Shield Decided"),
        P(HEADLINE + f" Across the 21 runs the shield also wrote {F.SAFETY_EVENTS} safety-log events, the coordinator reported {F.CONFLICTS} conflicts, and the hash chain verified in 21 of 21 runs."),
        TAB("Shield decisions per scenario, SafeGrid-AI arm (mean per run of three seeds)", ["Scenario", "Proposals", "Approved", "Projected", "Rejected", "Raw-proposal violations", "Pre-existing stress steps", "Cost (INR)"], dec_rows,
            widths=[1.3, 0.7, 0.75, 0.75, 0.7, 0.85, 0.85, 0.7], size=8.5, align=["l", "r", "r", "r", "r", "r", "r", "r"]),
        FIG(F.fig("fig_shield_decisions.png"), "Approved, projected and rejected proposals per run and scenario (SafeGrid-AI arm)", 5.8),
        P(f"The shield approved {F.pct(F.APPROVED / F.PROPOSALS)} of proposals, projected {F.pct(F.PROJECTED / F.PROPOSALS)} and rejected {F.pct(F.REJECTED / F.PROPOSALS)}; the intervention rate rises from 15.3 % in `peak_demand` to 36.6 % in `line_congestion`, "
          "where almost every EV charging request has to be scaled down. The same proposals would have caused 16.0 violations per run in `line_congestion` and 14.0 in `peak_demand` without the shield. "
          "Projection is more common than rejection (237 against 113), so the shield usually keeps the agent's intent and reduces its size."),
        H2("8.5 Pre-existing Grid Stress"),
        P("Some violations exist even when no agent acts. The shield does not repair them by design, but relief-first ordering and projection can reduce them; the table shows the steps that still carried any violation after execution."),
        TAB("Steps with any violation after execution, per scenario (mean of three seeds, of 24 steps)", ["Scenario", "Stress with every agent idle", "Rule baseline", "Agents, no shield", "SafeGrid-AI"], exec_rows,
            widths=[1.7, 1.4, 1.1, 1.2, 1.1], size=9.5, align=["l", "r", "r", "r", "r"]),
        FIG(F.fig("fig_preexisting_stress.png"), "Grid stress with every agent idle compared with violations after SafeGrid-AI actions", 5.7),
        FIG(F.fig("fig_executed_violations.png"), "Steps with any violation after execution, per scenario and strategy", 5.7),
        P(f"Averaged over scenarios, {mm('baseline_rule', 'violation_steps_executed')} steps per run carry a violation under the rule baseline, {mm('agents_unshielded', 'violation_steps_executed')} without the shield and **{mm('safegrid_shielded', 'violation_steps_executed')} with SafeGrid-AI**, "
          f"against {mm('safegrid_shielded', 'violation_steps_no_action', 2)} steps of stress with every agent idle. The reduction comes mostly from `high_solar` (20.0 stress steps with everyone idle, 1.7 after SafeGrid-AI), where the agents absorb surplus solar in their batteries; "
          "removing violations was not the shield's guarantee, and Section 8.8 shows where the gain does not appear."),
        H2("8.6 Cost of Safety"),
        P("A safety layer is not free; the table and figures show the trade-offs."),
        TAB("Energy cost per run (INR, illustrative tariff) and renewable utilisation, per scenario", ["Scenario", "Cost: rule", "Cost: no shield", "Cost: SafeGrid", "RU: rule", "RU: no shield", "RU: SafeGrid"], cost_rows,
            widths=[1.4, 0.9, 0.95, 0.95, 0.75, 0.85, 0.85], size=8.5, align=["l", "r", "r", "r", "r", "r", "r"]),
        P("RU is renewable utilisation (the share of available solar output that was used); it is not defined in `line_congestion`, which has no available solar generation, and is printed as n/a."),
        FIG(F.fig("fig_overall_metrics.png"), "Overall comparison: violations after execution, cost, renewable utilisation and step time", 5.9),
        FIG(F.fig("fig_cost_utilisation.png"), "Energy cost and renewable utilisation per scenario", 5.9),
        B(f"**Cost.** Mean cost per run is {mm('safegrid_shielded', 'total_cost', 1)} INR with the shield, {mm('agents_unshielded', 'total_cost', 1)} without it and {mm('baseline_rule', 'total_cost', 1)} for the rule baseline. "
          f"The unshielded agents are dear mainly because of `unsafe_ai_action`, where an injected 900 kW import raises the cost to about {ua_cost} INR per run against {sm('unsafe_ai_action', 'safegrid_shielded', 'total_cost', 1)} with the shield. "
          "SafeGrid-AI is slightly dearer than the rule baseline overall but cheaper in `peak_demand` and `line_congestion`.",
          f"**Renewable utilisation.** The rule baseline uses all available solar; the shielded arm uses {mm('safegrid_shielded', 'renewable_utilization', 3)}. The cost shows in `high_solar` ({hs:.3f}) and `voltage_violation` ({vs_:.3f}), where the shield limits export to protect voltage; "
          f"unshielded agents do worse in `high_solar` ({hu:.3f}).",
          f"**Battery use.** Throughput divided by capacity is {mm('safegrid_shielded', 'battery_utilization', 3)} with the shield, {mm('baseline_rule', 'battery_utilization', 3)} for the rule baseline and {mm('agents_unshielded', 'battery_utilization', 3)} for the unshielded agents, "
          f"dominated by `unsafe_ai_action` ({ua_bat} times capacity per run).",
          f"**Compute.** Mean step time rises from about {mm('agents_unshielded', 'avg_step_time_ms', 0)} ms to {mm('safegrid_shielded', 'avg_step_time_ms', 0)} ms, with {sm('line_congestion', 'safegrid_shielded', 'avg_step_time_ms', 0)} ms in `line_congestion`, where nearly every proposal needs bisection. "
          "The mock provider's 0.17 ms decision latency is meaningless for a real model."),
        H2("8.7 Single-Run Traces"),
        P("Three single runs (seed 42, native length, shield on and off) show what the averages hide."),
        FIG(F.fig("fig_timeseries.png"), "Single-run traces with and without the shield: line loading, highest bus voltage and lowest bus voltage", 6.0),
        TAB("Worst values in the three traced runs", ["Scenario", "Quantity", "Agents, no shield", "SafeGrid-AI", "Limit"],
            [["line congestion", "worst line loading", "137.7 %", "100.0 %", "100 %"],
             ["voltage violation", "highest bus voltage", "1.117 pu", "1.056 pu", "1.05 pu"],
             ["peak demand", "lowest bus voltage", "0.861 pu", "0.932 pu", "0.95 pu"]], widths=[1.4, 1.6, 1.3, 1.2, 0.8], size=10, align=["l", "l", "r", "r", "r"]),
        P("In `line_congestion` the unshielded agents drive the feeder to 137.7 % of its rating for eight steps; with the shield the loading is projected exactly onto the 100 % limit and never above it. "
          "In `voltage_violation` the voltage climbs to 1.117 pu without the shield and peaks at 1.056 pu with it, still above 1.05 pu because the scenario's weak feeder is already out of band when the agents are idle. "
          "In `peak_demand` the lowest voltage is 0.861 pu without the shield and 0.932 pu with it, still below 0.95 pu because the evening peak itself is the stressor. "
          "The shield removes the excess that actions add and leaves the stress that the scenario creates."),
        H2("8.8 Analysis of Successful and Failure Cases"),
        H3("Where the shield works"),
        B(f"**Agent faults.** In `unsafe_ai_action` the unshielded agents cause violations in {sm('unsafe_ai_action', 'agents_unshielded', 'violation_steps_caused_by_actions')} steps per run and the shielded agents in none. "
          "The 1,000 kW export and the 900 kW import are rejected; a malformed output becomes a labelled fallback decision that is shielded like any other.",
          f"**Congestion by a non-AI controller.** The rule baseline causes violations in {sm('line_congestion', 'baseline_rule', 'violation_steps_caused_by_actions')} of 24 steps in `line_congestion`. The shielded agents face the same congested feeder and cause none. "
          "No arm combines the rule controller with the shield, so that pairing is not claimed.",
          "**Plausible-but-oversized requests.** About one proposal in six is projected, not rejected: the agent wanted the right thing at the wrong size, and the shield returns the largest safe part of it."),
        H3("Where it does not help, or helps less"),
        B(f"**Pre-existing stress remains.** `high_solar` has 20.0 stress steps out of 24 with every agent idle, and `peak_demand` has 12.0; after SafeGrid-AI actions `peak_demand` still shows {pk_s} steps with a violation.",
          f"**A rule controller can leave fewer violations in peak demand.** Steps with any violation after execution in `peak_demand` are {pk_b} for the rule baseline, {pk_s} for SafeGrid-AI and {pk_u} without the shield. "
          "The shield prevents harm but does not search for relief; this is a real limitation of a veto-style layer and the reason future work proposes a planner rewarded for resolving violations.",
          f"**Renewable energy is sometimes given up.** Utilisation falls to {hs:.3f} in `high_solar` and {vs_:.3f} in `voltage_violation`.",
          "**Strict counters are not zero** (3.14 and 0.71), for the tolerance reason in Section 8.3, and **everything depends on the model**: the shield is only as good as the simulated grid it asks."),
        H2("8.9 Discussion of Limitations"),
        P("The results support one limited claim: in this simulator, under these scenarios, with a deterministic stand-in for a language model, validating every action with an AC power flow prevents all new or worsened limit violations, "
          "at the cost of some renewable energy and about three times the compute per step. The limits of the evidence are:"),
        B(*[g for g in GAPS]),
        P("Three seeds do not support confidence intervals, and means over scenarios mix very different situations, so the per-scenario tables are more informative than the overall one."),
        H2("8.10 Objectives versus Outcomes"),
        TAB("Objectives of the project and what was delivered", ["Objective", "Status", "Evidence"], [list(r) for r in OUTCOMES], widths=[1.5, 1.1, 3.9], size=9.5),
        H2("8.11 Comparison with the Base Paper"),
        P(f"The base paper {n(1)} designs a rule-based multi-agent energy management system for a DC microgrid and validates it in MATLAB/Simulink in eight scenarios. "
          "SafeGrid-AI differs in the system modelled, in how decisions are made and in what is measured, so **no numeric comparison is possible or attempted**. "
          f"Grid-Agent {n(2)} is closer in spirit, but its safety rests on sandboxed execution with rollback and its results are success rates on IEEE and CIGRE networks, on which this project did not run. The table compares design and evidence qualitatively."),
        TAB("SafeGrid-AI compared with the base paper (qualitative)", ["Aspect", "Base paper [1]", "SafeGrid-AI"], [list(r) for r in BASE_COMPARE], widths=[1.3, 2.4, 2.8], size=9.5),
        P("It supports the gap stated in the batch survey: an independent, deterministic safety layer with explanations and an audit trail is what this project adds and measures, within the limits above."),
    ]
