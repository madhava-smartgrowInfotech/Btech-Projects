"""13.Review_2_PPT.pptx: 20 slides, design, methodology and progress. Built from D:\\abstracts\\Templates\\Review_2_PPT.pptx."""

import os

from pptx import Presentation

from . import content_shared as C
from . import facts as F
from . import pptkit as K
from .deck_review1 import agenda, is_ph, patch_theme, prepare, set_title, thank_you, title_slide, wipe

TEMPLATE = r"D:\abstracts\Templates\Review_2_PPT.pptx"

CHECKS = [
    ("STRUCTURE", "schema, known agent and node, finite non-negative power"),
    ("POWER_LIMITS", "request not implausibly large for the node"),
    ("BATTERY", "charge and discharge rating, configured state-of-charge window"),
    ("NODE_LIMITS", "node import and export limits, shiftable load share"),
    ("POWER_BALANCE", "curtailment within generation, reachable direction"),
    ("POWER_FLOW", "trial AC power flow converges"),
    ("VOLTAGE", "every bus between 0.95 and 1.05 pu"),
    ("LINE_LOADING", "every line at or below 100 %"),
    ("TRANSFORMER", "transformer at or below 100 %"),
    ("GRID_LIMITS", "external grid import and export up to 200 kW"),
]


def build(out_path):
    prs = Presentation(TEMPLATE)
    prepare(prs, "Review 2")
    S = list(prs.slides)
    assert len(S) == 20, len(S)
    notes = {}
    T = F.TESTS
    shield_total = F.PROPOSALS

    # ---- 1 title
    title_slide(S[0], "Design, methodology and progress: three agents on a simulated feeder, a Symbolic Safety Shield, and the first full measurements",
                "REVIEW 2  ·  DESIGN, METHODOLOGY AND PROGRESS")
    notes[1] = "This review shows how the system is designed and built, what is implemented, the first measured results and the open items."

    # ---- 2 contents
    s = S[1]
    set_title(s, "Contents")
    wipe(s)
    agenda(s, [("01", "Recap and architecture"), ("02", "Methodology, scenarios and context"), ("03", "Agent and shield design"), ("04", "Experiment protocol and decision logic"),
               ("05", "Data flow, database and use cases"), ("06", "Technology stack"), ("07", "Implementation progress and results"),
               ("08", "Output screens and testing"), ("09", "Challenges and next steps")],
           [K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE, K.BLUE, K.GREEN, K.PURPLE, K.ORANGE])
    notes[2] = "Agenda for the design and progress review."

    # ---- 3 recap
    s = S[2]
    set_title(s, "Recap: problem and proposed system")
    wipe(s)
    W = 3.85
    for i, (t, b_, col, gl) in enumerate([
        ("Problem", "Language-model agents can plan power routing, but a non-deterministic model that commands physical equipment can issue an unsafe set-point, and operators need to see why each decision was made.", K.ORANGE, "!"),
        ("Proposed system", "Agents propose one action each; a deterministic Symbolic Safety Shield approves it, scales it down by bisection or rejects it, and only the validated set-point is executed and logged.", K.BLUE, "i"),
        ("Base paper link", "Keeps role-based agents and scenario-based evaluation from the DC-microgrid base paper; adds a model-driven proposer, an independent shield, explanations and an audit log. Its MATLAB/Simulink system is not reproduced.", K.GREEN, "B"),
    ]):
        K.card(s, 0.6 + i * (W + 0.29), 1.5, W, 4.7, t, b_, col, gl, body_size=15)
    notes[3] = "One-minute recap of Review 1. The base paper is a rule-based DC-microgrid study; our system is a different, AC low-voltage simulation, so we compare ideas, not numbers."

    # ---- 4 architecture
    s = S[3]
    set_title(s, "System architecture")
    wipe(s)
    K.picture(s, F.diag("01_system_architecture.png"), 0.6, 1.3, 7.6, 5.45)
    K.text(s, 8.5, 1.5, 4.2, 5.2, [
        ("**Four tiers**", {"space_after": 8}),
        ("Presentation: React dashboard on port 5313 with a three.js landing page.", {"bullet": True}),
        ("Application: FastAPI on port 8313, REST routers plus the /ws/simulation WebSocket.", {"bullet": True}),
        ("Core: engine, three agents, coordinator, shield and a pandapower simulator.", {"bullet": True}),
        ("Data: SQLite store and a SHA-256 hash-chained safety log.", {"bullet": True}),
        ("The LLM provider is the only untrusted component.", {"bullet": True}),
    ], size=15, color=K.INK)
    notes[4] = "Follow the tiers left to right. The shield imports nothing from the language-model, agent, simulation or grid packages, and a test enforces that."

    # ---- 5 methodology workflow
    s = S[4]
    set_title(s, "Methodology: one simulation step")
    wipe(s)
    K.flow(s, 0.6, 1.5, 12.13, 1.35, [("Seeded PV, load, price", K.NAVY), ("No-action power flow", K.NAVY), ("Agents perceive", K.PURPLE), ("Agents propose", K.PURPLE),
                                      ("Coordinator orders", K.GREEN), ("Shield validates", K.ORANGE), ("Commit and log", K.BLUE)], size=13, gap=0.22)
    for i, (t, b_) in enumerate([("Counterfactual", "The raw proposals are also trial-run, so each step records what would have happened without the shield."),
                                 ("Fair attribution", "Only violations that are new or worse than the no-action grid are blamed on an action; pre-existing stress is reported separately."),
                                 ("Reproducible", "Everything is seeded; the same seed gives the same profiles, proposals and results.")]):
        x = 0.6 + i * 4.14
        K.box(s, x, 3.3, 3.85, 3.0)
        K.text(s, x + 0.25, 3.45, 3.4, 0.5, t, size=18, color=K.INK, bold=True)
        K.text(s, x + 0.25, 4.05, 3.4, 2.1, b_, size=15, color=K.TXT)
    notes[5] = "A step is 15 simulated minutes. The shield validates the agents one after another against the cumulative grid state, relief actions first."

    # ---- 6 scenarios and inputs
    s = S[5]
    set_title(s, "Scenarios and inputs (no external dataset)")
    wipe(s)
    for i, (v, l, c) in enumerate([("7", "seeded scenarios", K.BLUE), ("3", "agents on 3 nodes", K.GREEN), ("15 min", "control step", K.ORANGE), ("No dataset", "inputs generated from a seed", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.1, 1.45, 2.9, 1.25, v, l, c, vsize=26, lsize=12)
    K.bar_chart(s, 0.6, 2.95, 6.8, 3.9, [sc.replace("_", " ") for sc in F.SCENARIOS], [("Native length (steps)", [F.SCEN_STEPS[sc] for sc in F.SCENARIOS])],
                colors=[K.BLUE], number_format="0", font_size=11, max_value=40)
    K.text(s, 7.7, 3.0, 5.0, 3.9, [
        ("Solar follows a daylight curve scaled by a seeded cloud factor; household load has morning and evening peaks with 5 % noise.", {"bullet": True}),
        ("Tariff is an illustrative time-of-use table in INR; export is credited at 60 % of the price.", {"bullet": True}),
        ("No train, validation or test split exists, so no accuracy or F1 is reported anywhere.", {"bullet": True}),
        ("The evaluation runs every scenario for 24 steps.", {"bullet": True}),
    ], size=14, color=K.INK)
    notes[6] = "There is no dataset. Profiles are generated at run time from a seed, so every number is reproducible. The chart shows each scenario's native length; the evaluation uses 24 steps for all."

    # ---- 7 perception and context
    s = S[6]
    set_title(s, "Perception: what each agent sees")
    wipe(s)
    for i, (t, b_, col, gl) in enumerate([
        ("Own node", "Load, solar output, battery state of charge and rating, local voltage, net exchange, price and weather.", K.BLUE, "1"),
        ("Neighbours and limits", "Net exchange, state of charge and voltage of the other nodes, plus the voltage band, line and import limits.", K.GREEN, "2"),
        ("Memory and output", "The previous action and its shield result. The agent returns one schema-checked action; anything else becomes a labelled fallback.", K.ORANGE, "3")]):
        K.card(s, 0.6 + i * 4.14, 1.5, 3.85, 3.3, t, b_, col, gl, body_size=16)
    K.box(s, 0.6, 5.05, 12.13, 1.5)
    K.text(s, 0.9, 5.2, 11.5, 1.2, "The shield never sees this context, any prompt or any model text. It reads only the fields of the proposed action: agent, action type, power, duration, target node, reason codes and confidence.", size=16, color=K.INK, anchor="m")
    notes[7] = "The context is structured data, not free text. The shield never sees this context or any model text; it reads only the action fields."

    # ---- 8 agent and shield design
    s = S[7]
    set_title(s, "Agent and shield design")
    wipe(s)
    K.picture(s, F.diag("11_feeder_topology.png"), 0.6, 1.35, 5.6, 3.0)
    K.text(s, 0.6, 4.5, 5.6, 2.3, [
        ("**prosumer_01** (node 1): 6 kWp PV, 10 kWh battery.", {"bullet": True}),
        ("**ev_01** (node 2): 40 kWh EV, charge only, 7.4 kW.", {"bullet": True}),
        ("**renewable_01** (node 3): 20 kWp PV, 30 kWh battery.", {"bullet": True}),
    ], size=14, color=K.INK)
    rows = [["Shield check", "What it tests"]] + [[a, b_] for a, b_ in CHECKS]
    K.table(s, 6.5, 1.4, [1.9, 4.33], rows, font_size=10.5, row_h=0.5, first_bold=True)
    notes[8] = "The feeder and the three agents on the left; the ten ordered checks on the right. 25 violation codes map onto these ten named checks."

    # ---- 9 experiment protocol
    s = S[8]
    set_title(s, "Experiment protocol")
    wipe(s)
    rows = [["Setting", "Value"],
            ["Scenarios x strategies x seeds", "7 x 3 x 3 = 63 simulation runs"],
            ["Strategies", "rule baseline, agents without shield, SafeGrid-AI (agents + shield)"],
            ["Steps per run", "24 steps of 15 simulated minutes"],
            ["Seeds", "0, 1, 2 (results are means over 21 runs per strategy)"],
            ["Language model", "deterministic mock provider; no live model"],
            ["Machine", "Intel Core i5-12500, 15.7 GB RAM, no GPU"],
            ["Wall time", "about 10 minutes for all 63 runs"]]
    K.table(s, 0.6, 1.4, [3.0, 5.0], rows, font_size=12.5, row_h=0.6, first_bold=True)
    K.picture(s, F.diag("02_high_level_workflow.png"), 8.8, 1.4, 4.0, 2.4)
    K.card(s, 8.8, 4.0, 3.93, 2.7, "Honest limits", "Three seeds, a synthetic three-node feeder, an illustrative tariff and a mock model. Results are simulation evidence only.", K.ORANGE, "!", body_size=13)
    notes[9] = "Every number later in the deck comes from this protocol, saved as docs/results/experiment_3seeds_24steps.json."

    # ---- 10 decision logic
    s = S[9]
    set_title(s, "Decision logic of the shield")
    wipe(s)
    K.picture(s, F.diag("10_core_algorithm_flowchart.png"), 0.6, 1.3, 5.2, 5.6)
    K.text(s, 6.2, 1.5, 6.5, 5.3, [
        ("**Reject** structurally invalid actions at once; **approve** idle actions.", {"bullet": True, "space_after": 10}),
        ("**Trial power flow** of the request; only violations that are new or worse than the no-action grid count.", {"bullet": True, "space_after": 10}),
        ("**Project** by bisection to the largest safe scale (40 iterations on local limits, 14 on power-flow limits), re-verify the rounded action, reject below 0.05 kW.", {"bullet": True, "space_after": 10}),
        ("**Record** every non-approved decision as a hash-chained safety event.", {"bullet": True}),
    ], size=15, color=K.INK)
    notes[10] = "This is the evaluate() function of the shield. The guarantee is relative to the simulated model: no new or worse violation of the configured limits."

    # ---- 11 data flow and modules
    s = S[10]
    set_title(s, "Data flow and modules")
    wipe(s)
    K.picture(s, F.diag("04_dfd_level1.png"), 0.6, 1.3, 7.3, 5.5)
    rows = [["Module", "Role"], ["safety/shield.py", "approve, project, reject"], ["safety/validator.py", "checks and attribution"], ["simulation/engine.py", "one run, one step"],
            ["simulation/coordinator.py", "conflicts, ordering"], ["agents/manager.py", "perceive and decide"], ["llm/provider.py", "mock, api, baseline"], ["grid/simulator.py", "pandapower trial, commit"],
            ["database/store.py", "SQLite store"]]
    K.table(s, 8.1, 1.4, [2.55, 2.08], rows, font_size=11, row_h=0.5)
    notes[11] = "Level-1 data flow with six processes. Levels 0 and 2 are in the report."

    # ---- 12 database and use cases
    s = S[11]
    set_title(s, "Database design and use cases")
    wipe(s)
    rows = [["Table", "Content"], ["runs", "configuration, summary, chain fingerprint"], ["events", "stream events per run and step"], ["safety_events", "hash-chained interventions"], ["steps", "full step record (run_id, step)"], ["experiments", "specification and results of a comparison"]]
    K.table(s, 0.6, 1.5, [1.8, 3.7], rows, font_size=12.5, row_h=0.62, first_bold=True)
    K.text(s, 0.6, 5.4, 5.5, 1.4, "SQLite from the Python standard library; JSON text columns, indexes on (run_id, event_type) and (run_id, status).", size=13, color=K.TXT, italic=True)
    K.picture(s, F.diag("08_use_case_diagram.png"), 6.5, 1.35, 6.2, 5.4)
    notes[12] = "Five tables. The use-case diagram shows the operator, the optional language-model provider and the experiment job."

    # ---- 13 technology stack
    s = S[12]
    set_title(s, "Technology stack")
    wipe(s)
    stack = [("Simulation", "pandapower 3.5.6 (AC power flow), numpy 2.4.6, pandas 2.3.3, scipy 1.17.1", K.BLUE, "S"),
             ("Service", "Python 3.11.9, FastAPI 0.143.3, Uvicorn 0.54.0, pydantic 2.14.1, httpx", K.GREEN, "A"),
             ("Storage", "SQLite (standard library) with a SHA-256 hash-chained safety log", K.ORANGE, "D"),
             ("Dashboard", "React 18, Vite 5, React Router, Recharts, three.js with react-three-fiber", K.PURPLE, "U"),
             ("Language-model layer", "Provider interface: mock, rule-based, failing, and an API provider (Anthropic or OpenAI wire format)", K.BLUE, "L"),
             ("Quality", "pytest 9.1.1, a 20-check smoke test, Playwright browser walk", K.GREEN, "Q")]
    for i, (t, b_, col, gl) in enumerate(stack):
        r, c = divmod(i, 3)
        K.card(s, 0.6 + c * 4.14, 1.5 + r * 2.7, 3.85, 2.5, t, b_, col, gl, body_size=16)
    notes[13] = "Everything is open source. The API provider is implemented but was not exercised against a live model."

    # ---- 14 implementation progress
    s = S[13]
    set_title(s, "Implementation progress")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{F.LOC['backend']:,}", "lines of backend code", K.BLUE), (f"{F.LOC['tests']:,}", "lines of tests (55 tests)", K.GREEN), (f"{F.LOC['frontend']:,}", "lines of dashboard code", K.ORANGE)]):
        K.tile(s, 0.6 + i * 4.14, 1.4, 3.85, 1.15, v, l, c, vsize=26, lsize=12)
    rows = [["Component", "Status", "Evidence"],
            ["Grid model, simulator, trial power flow", "Done", "pandapower 3-node feeder, 7 scenarios"],
            ["Agents, coordinator, mock provider", "Done", "3 agents, 3 conflict types"],
            ["Symbolic Safety Shield, audit log", "Done", "0 violations caused in 504 shielded steps"],
            ["REST and WebSocket service", "Done", "smoke test 20 of 20"],
            ["Dashboard (7 screens)", "Done", "11 real screenshots"],
            ["Real LLM provider", "Implemented, not run", "no API key; mock used for all results"],
            ["Violation-resolution rate", "Not measured", "project measures violations prevented"]]
    K.table(s, 0.6, 2.8, [4.6, 2.3, 5.23], rows, font_size=12, row_h=0.5)
    notes[14] = "State of the code base. The two honest gaps are the live language model and the resolution-rate metric."

    # ---- 15 preliminary results
    s = S[14]
    set_title(s, "Preliminary results: violations caused by actions")
    wipe(s)
    for i, (v, l, c) in enumerate([("0 of 504", "shielded steps with a violation caused", K.GREEN), (f"{F.UNSHIELDED_CAUSED_STEPS} steps", f"without shield ({F.UNSHIELDED_CAUSED} violations)", K.ORANGE),
                                   (F.pct(F.APPROVED / F.PROPOSALS), f"of {F.PROPOSALS:,} proposals approved as asked", K.BLUE)]):
        K.tile(s, 8.3, 1.45 + i * 1.5, 4.43, 1.3, v, l, c, vsize=26, lsize=12)
    cats = [sc.replace("_", " ") for sc in F.SCENARIOS]
    K.bar_chart(s, 0.6, 1.4, 7.5, 5.0, cats, [(F.ARM_LABEL[a], [round(F.sc_mean(sc, a, "violation_steps_caused_by_actions"), 2) for sc in F.SCENARIOS]) for a in F.ARMS],
                colors=[K.TXT, K.ORANGE, K.GREEN], number_format="0.0", font_size=10, max_value=14, label_size=8)
    K.text(s, 0.6, 6.5, 7.5, 0.4, "Steps of 24 with violations caused by actions, mean of 3 seeds; mock provider, synthetic feeder.", size=11, color=K.TXT, italic=True)
    K.text(s, 8.3, 5.95, 4.43, 0.9, "Pre-existing grid stress is not removed by design: any violation after execution drops from 6.05 (rule) and 6.38 (no shield) to 2.48 steps.", size=12, color=K.TXT)
    notes[15] = ("Real measurements from 63 runs. The shield column is zero in every scenario by construction of the metric: violations new or worse than the no-action grid. "
                 "Steps with any violation are also reduced but not to zero. The rule baseline itself causes violations in peak demand and line congestion.")

    # ---- 16 output screens
    s = S[15]
    set_title(s, "Output screens")
    wipe(s)
    K.picture(s, F.shot("04_dashboard.png"), 0.6, 1.4, 6.0, 3.75, border=True)
    K.picture(s, F.shot("07_safety_shield.png"), 6.75, 1.4, 6.0, 3.75, border=True)
    K.text(s, 0.6, 5.3, 6.0, 1.3, "Dashboard after a finished run of the unsafe_ai_action scenario: 12 interventions in 36 proposals, 0 violations caused.", size=13, color=K.TXT, align="c")
    K.text(s, 6.75, 5.3, 6.0, 1.3, "Safety shield view: event table, a dry-run rejection of a 1000 kW export, and the active constraints.", size=13, color=K.TXT, align="c")
    notes[16] = "Real screenshots from the running dashboard (scenario unsafe_ai_action, mock provider, seed 42). The remaining screens are in the report."

    # ---- 17 testing
    s = S[16]
    set_title(s, "Initial testing and observations")
    wipe(s)
    for i, (v, l, c) in enumerate([(f"{T['passed']} of {T['total']}", "pytest tests passed", K.GREEN), ("20 of 20", "live smoke-test checks", K.BLUE), (str(T["failed"]), "tests fail on numeric tolerances", K.ORANGE), (str(T["hung"]), "WebSocket test hangs", K.PURPLE)]):
        K.tile(s, 0.6 + i * 3.1, 1.45, 2.9, 1.25, v, l, c, vsize=26, lsize=12)
    rows = [["Observation", "Action"],
            ["test_power_flow_converges_and_balances: 10.995 kW against 10.0 +/- 0.5", "Tolerance was set for an older pandapower; power flow converges. Left unchanged, reported."],
            ["test_trial_does_not_change_committed_state: -3.12314 against -3.123 +/- 1e-6", "Same cause. Left unchanged, reported."],
            ["test_websocket_receives_events hangs under the installed Starlette test client", "Excluded from the run; the live WebSocket works in the dashboard."]]
    K.table(s, 0.6, 3.1, [6.2, 5.93], rows, font_size=12, row_h=0.85)
    notes[17] = "55 test functions: safety 22, agents 12, simulation 11, grid 6, API 4. The three problems existed before this documentation work; we report them instead of hiding them."

    # ---- 18 challenges
    s = S[17]
    set_title(s, "Challenges and corrective actions")
    wipe(s)
    ch = [("Pre-existing grid stress", "Some scenarios break limits even with every agent idle (6.33 steps per run). Reported separately; the shield blocks only what actions add.", K.ORANGE, "1"),
          ("Mock language model", "Results use a deterministic mock, so model reasoning quality is unmeasured. Provider interface is ready for a live model.", K.BLUE, "2"),
          ("Cost of validation", f"Trial power flows raise step time from about 107 ms to {F.mean('safegrid_shielded', 'avg_step_time_ms'):.0f} ms.", K.PURPLE, "3"),
          ("Failing tolerance tests", "Two grid tests use tolerances tied to an older pandapower; documented, not hidden.", K.GREEN, "4"),
          ("Hanging WebSocket test", "Blocks under the installed Starlette test client; excluded and flagged.", K.ORANGE, "5"),
          ("Strong wording in the abstract", "'Mathematically guaranteeing zero violations' is stronger than a model-relative guarantee; the documents say so.", K.BLUE, "6")]
    for i, (t, b_, col, gl) in enumerate(ch):
        r, c = divmod(i, 3)
        K.card(s, 0.6 + c * 4.14, 1.5 + r * 2.7, 3.85, 2.5, t, b_, col, gl, body_size=14)
    notes[18] = "Each challenge is either handled in the code or stated plainly in the documents."

    # ---- 19 next steps
    s = S[18]
    set_title(s, "Next steps")
    wipe(s)
    for i, (t, b_, col, gl) in enumerate([
        ("Evaluate", "Report the full 63-run results with per-scenario tables and traces.", K.BLUE, "1"),
        ("Compare", "Set the work against the base paper qualitatively, stating the differences.", K.GREEN, "2"),
        ("Document", "Final report, paper and deck with every figure regenerated from the saved results.", K.ORANGE, "3"),
        ("Extend (future)", "Live language-model runs, a violation-resolution metric, larger feeders, field data.", K.PURPLE, "4")]):
        K.card(s, 0.6 + i * 3.1, 1.6, 2.9, 4.4, t, b_, col, gl, body_size=18)
    notes[19] = "Plan to the final review. The extensions on the right are out of scope for this submission."

    # ---- 20 thank you
    thank_you(S[19], "Questions and suggestions are welcome.")
    notes[20] = "Likely questions: why a mock model; what the guarantee means; why zero shielded violations while some steps still violate (pre-existing stress)."

    for i, sl in enumerate(S, 1):
        K.set_notes(sl, notes[i])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)
    patch_theme(out_path)
    return out_path


if __name__ == "__main__":
    print(build(os.path.join(F.BATCH, "13.Review_2_PPT.pptx")))
