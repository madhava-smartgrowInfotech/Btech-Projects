"""Chapters 9 and 10 plus the supporting blocks of the separate chapter documents (novelty, contributions, scope,
assumptions, limitations, not-measured, code walk-throughs, implementation decisions, conclusion, future scope)."""

from . import facts as F
from .blocks import B, CODE, H1, H2, H3, N, P, TAB
from .content_shared import GAPS, HEADLINE, OBJECTIVES, OUTCOMES
from .refs import n

PCT = lambda x: F.pct(x / F.PROPOSALS)  # noqa: E731


def _o(arm, key, d=2):
    return f"{F.mean(arm, key):.{d}f}"


# ------------------------------------------------------------------------------------------------ chapter 9
def chapter9_blocks():
    return [
        H1("CHAPTER 9: CONCLUSION"),
        H2("9.1 Summary of the Work"),
        P("SafeGrid-AI is a simulation-based system in which three agents (a residential prosumer, an electric-vehicle storage node and a renewable prosumer) propose one `EnergyAction` per 15-minute step for a small low-voltage feeder, "
          "and a deterministic Symbolic Safety Shield decides what reaches the grid. A coordinator orders the proposals, relief actions first, and the shield validates each one against the cumulative grid state with a real AC power flow (pandapower " + n(11) + "): "
          "approved, projected (scaled to the largest safe size by bisection) or rejected, with every non-approved decision entered in a SHA-256 hash-chained log. "
          "A FastAPI service and a React console expose run controls, a live single-line diagram, an agent monitor, a shield view with a dry-run tool, power-flow charts, a scenario runner and an explainability view."),
        P("The evaluation used seven scenarios, three seeds and three strategies, 63 runs of 24 steps. The language model in every run was a deterministic mock provider, which limits what the results can say."),
        H2("9.2 Objectives Achieved and Main Contributions"),
        P("Of the six objectives, four were achieved in full (multi-agent model, safety shield, explanations, scenarios), one with a mock model in place of a real one (the language-model planner) and one in part "
          "(evaluation: unsafe actions blocked and decision latency were measured, a violation-resolution rate was not). Section 8.10 gives the evidence."),
        P("The contributions beyond assembling known parts are modest and specific: a verdict that can reduce an action instead of only vetoing it; an attribution rule that separates violations caused by an action from pre-existing stress; "
          "a shield whose independence from the language-model code is enforced by a test; explanations built from structured data; a tamper-evident audit trail; and an evaluation that includes the counterfactual of what the raw proposals would have done."),
        H2("9.3 Key Findings"),
        N(f"{HEADLINE}",
          f"The rule-based baseline, which has no safety layer, also caused violations ({F.BASELINE_CAUSED} in {F.BASELINE_CAUSED_STEPS} steps), all in the congestion and peak-demand scenarios, so the failure is not specific to language-model agents.",
          f"The shield intervened on {F.PROJECTED + F.REJECTED} of {F.PROPOSALS:,} proposals ({PCT(F.PROJECTED + F.REJECTED)}): {F.PROJECTED} projected and {F.REJECTED} rejected, so the agent's intent is usually kept at a smaller size.",
          f"Steps with any violation after execution average {_o('baseline_rule', 'violation_steps_executed')} for the rule baseline, {_o('agents_unshielded', 'violation_steps_executed')} without the shield and {_o('safegrid_shielded', 'violation_steps_executed')} with it, "
          f"against {_o('safegrid_shielded', 'violation_steps_no_action')} steps of stress when every agent is idle. Not all stress is removed, and in `peak_demand` the rule baseline leaves fewer violations than the shielded agents.",
          f"Safety has a price: mean step time is {_o('safegrid_shielded', 'avg_step_time_ms', 1)} ms with the shield against about {_o('agents_unshielded', 'avg_step_time_ms', 0)} ms without it, and renewable utilisation is {_o('safegrid_shielded', 'renewable_utilization', 3)} against {_o('baseline_rule', 'renewable_utilization', 3)} for the rule baseline; "
          f"mean energy cost is {_o('safegrid_shielded', 'total_cost', 1)} INR against {_o('agents_unshielded', 'total_cost', 1)} without the shield.",
          "The audit chain verified in all 21 shielded runs, and a forged event is detected by the tests."),
        H2("9.4 Practical Applications"),
        P("The system is a research and teaching prototype, not a controller for a real network. Within that limit it serves four purposes."),
        B("**Teaching and demonstration.** Students can watch an agent propose an unsafe action, see which check stopped it and read why, with every number reproducible from a seed.",
          "**A test bench for agent controllers.** Any controller that can emit an `EnergyAction` can be dropped in behind the provider interface and compared on the same scenarios, with and without the shield.",
          "**A pattern for supervising AI agents on physical systems.** An independent, deterministic validator and a record of every decision apply to other domains with hard limits.",
          "**A starting point for operator-facing tools.** The dry-run view, decision lane and audit chain are the beginnings of a review interface."),
        H2("9.5 Known Limitations"),
        P("The conclusions hold only for the simulated three-node feeder, three seeds and the mock provider: no real language model was evaluated (reasoning quality and real latency are unknown); "
          "violation resolution was not measured; the guarantee is relative to the simulator and is not a formal proof; the comparison with the base paper is qualitative; two grid tests fail and one WebSocket test hangs; and no user study was done."),
    ]


# ------------------------------------------------------------------------------------------------ chapter 10
def chapter10_blocks():
    return [
        H1("CHAPTER 10: FUTURE SCOPE"),
        H2("10.1 Possible Improvements"),
        B("**Run a real language model.** Configure the existing API provider with a hosted model, repeat the 63-run experiment, and report decision latency, token cost, fallback rate and schema-invalid outputs. This is the most valuable next step, because every agent result here comes from a mock.",
          "**Repair the test suite.** Compute the expected values in the two grid tests instead of fixing them, and use an asynchronous client for the WebSocket test.",
          "**Measure resolution.** Add a metric for the share of pre-existing violation steps that are cleared, and a planner objective that rewards clearing them; `peak_demand` shows a veto-only layer can be out-performed by a controller that acts helpfully.",
          "**Reduce the cost of safety.** Use cached factorisations or sensitivity screening to avoid a full trial power flow for clearly safe proposals; the shield roughly triples the step time."),
        H2("10.2 Additional Features"),
        B("**Human-in-the-loop approval.** Hold projected or rejected actions for an operator to accept, edit or override, recorded in the same hash chain, in line with the human-oversight requirements discussed for grid studies " + n(3) + ".",
          "**Tool interface.** Expose the simulator and the shield through the Model Context Protocol " + n(3) + " so that external agents can call them as standard tools.",
          "**Forecast-aware agents.** Give the agents solar and load forecasts so that they can plan over several steps, with the shield still validating each step.",
          "**Authentication and roles.** Replace the browser-side demo gate with real accounts and keep the model API key on the server."),
        H2("10.3 Scalability and Deployment"),
        B("**Larger networks.** Repeat the study on benchmark feeders of the kind used in related work " + n(2) + "; trial power flows per step grow with the number of agents and the bisection depth, so scaling must be measured, not assumed.",
          "**Three-phase operation.** Move from the single-phase equivalent to a three-phase model, because low-voltage feeders are often unbalanced and voltage limits are phase-wise.",
          "**Operational packaging.** Containerise the services, move the store to a server database, add structured logging and run the experiment runner as a scheduled job.",
          "**Hardware in the loop.** Connect the shield to a real-time simulator before any field device, since the quasi-static 15-minute model hides fast dynamics and protection."),
        H2("10.4 Further Research Directions"),
        B("**Formal verification of the shield.** State the guarantee as a theorem about a stated model (monotone projection, the attribution rule, the tolerance) and check it with a verifier, in the spirit of shielding for safe learning " + n(12) + ".",
          "**Learning with a shield in the loop.** Train a policy by reinforcement learning or fine-tuning with the shield's corrections as part of the signal, so that agents propose actions that need less projection " + n(13) + ", " + n(14) + ".",
          "**Faithful explanations.** Compare structured explanations with model-written rationales for operator comprehension and faithfulness " + n(17) + ".",
          "**User study.** Test with students and operators whether the decision lane, dry run and audit view improve understanding, trust and error detection.",
          "**Adversarial evaluation.** Attack the provider with prompt injection and measure what reaches the grid; the schema and shield should make the answer 'nothing', but only synthetic faults were tested."),
    ]


# ------------------------------------------------------------------------------------------------ separate documents
def conclusion_blocks():
    return [
        H2("Summary"),
        P("This project set out to show that autonomous agents can be allowed to propose control actions for a power network without being allowed to execute them. "
          "The system that resulted, SafeGrid-AI, has three agents on a simulated three-node low-voltage feeder, a coordinator that detects conflicts and orders proposals, and a Symbolic Safety Shield that validates every proposal with an AC power flow and returns one of three verdicts: approved, projected (scaled to the largest safe size) or rejected. "
          "Only validated set-points are committed to the simulated grid. Each non-approved decision is written to a SHA-256 hash-chained log, and each decision carries a structured explanation. "
          "The system is served by a FastAPI interface with a WebSocket stream and a React console, and is evaluated with a three-strategy experiment on seven seeded scenarios."),
        H2("What the Measurements Show"),
        P(HEADLINE),
        P(f"The shield intervened on {PCT(F.PROJECTED + F.REJECTED)} of proposals, mostly by scaling them down rather than refusing them. The mean number of steps with any limit violation after execution fell from {_o('agents_unshielded', 'violation_steps_executed')} (agents without the shield) and {_o('baseline_rule', 'violation_steps_executed')} (rule baseline) to {_o('safegrid_shielded', 'violation_steps_executed')} with SafeGrid-AI, "
          f"although {_o('safegrid_shielded', 'violation_steps_no_action')} steps per run are stressed by the scenario even when every agent is idle. "
          f"The price is compute and some renewable energy: {_o('safegrid_shielded', 'avg_step_time_ms', 1)} ms per step against about {_o('agents_unshielded', 'avg_step_time_ms', 0)} ms, and renewable utilisation of {_o('safegrid_shielded', 'renewable_utilization', 3)} against {_o('agents_unshielded', 'renewable_utilization', 3)} without the shield."),
        P("Single-run traces make the same point visually: in the congestion scenario the unshielded agents push a line to 137.7 % of its rating, while with the shield it never exceeds 100.0 %; in the voltage scenario the highest voltage is 1.117 pu without the shield and 1.056 pu with it, which is still above 1.05 pu because the scenario already breaks the limit with every agent idle."),
        H2("Contributions"),
        P("The work contributes a verdict that can reduce a request instead of only vetoing it, an attribution rule that separates violations caused by an action from those already present, a shield whose independence from the language-model code is enforced by a test, structured explanations without stored chain-of-thought, a tamper-evident audit trail and a three-arm evaluation that includes the counterfactual of what the raw proposals would have done. "
          f"Measured against the six objectives of the batch, four were achieved, one was achieved with a mock model and one, violation resolution, was achieved in part."),
        H2("Limits of the Conclusion"),
        P("These conclusions are conditional. No real language model was evaluated; every agent decision came from a deterministic mock. The feeder is a three-node simulation with synthetic profiles and an illustrative tariff, and the experiment has three seeds. "
          "The safety guarantee is that executed actions do not create or worsen a violation of the configured limits in the simulated model; it is not a proof and it does not promise a violation-free grid. "
          "The comparison with the base paper " + n(1) + " is qualitative. Two grid unit tests fail on numeric tolerances, one WebSocket test hangs, and no user study was carried out."),
        H2("Closing Remark"),
        P("The practical lesson is architectural. A language model, or any other flexible proposer, is most useful when the system around it assumes that it will sometimes be wrong, and makes being wrong cheap: a narrow action schema, an independent deterministic validator, a clear record of what was changed and why, and an interface in which a person can check any decision. "
          "SafeGrid-AI is a small, honest demonstration of that pattern, together with a clear list of what remains to be shown."),
    ]


def future_blocks():
    return [
        H2("Evaluate with a Real Language Model"),
        P("Every agent result in this report comes from a deterministic mock provider, so the most valuable next step is to run the existing API provider against a hosted model and repeat the 63-run experiment. "
          "The report should then include decision latency (the mock's 0.1-0.2 ms is meaningless), token cost, the rate of outputs that fail schema validation, the fallback rate and a comparison of reasoning quality between models, as in the model-by-model success rates reported for Grid-Agent " + n(2) + "."),
        H2("Measure and Improve Resolution"),
        P("Objective 6 asked for a violation resolution rate, which was not measured. Add a metric for the share of pre-existing violation steps that are cleared, and give the planner an objective that rewards clearing them. "
          f"The `peak_demand` scenario shows why: the rule baseline leaves {F.BYSC['peak_demand']['baseline_rule']['violation_steps_executed']['mean']:.2f} steps with a violation, the shielded agents {F.BYSC['peak_demand']['safegrid_shielded']['violation_steps_executed']['mean']:.2f}, "
          "because a veto-only layer prevents harm but does not look for relief."),
        H2("Stronger Guarantees"),
        B("State the shield's guarantee as a theorem about an explicit model and check it with a verifier; the present claim is model-relative and rests on tests.",
          "Test the monotonicity assumption of the bisection (that a smaller action is never less safe) on more network types and on three-phase models.",
          "Add adversarial evaluation: prompt-injection attacks on a hosted model, measuring what reaches the grid."),
        H2("Realism and Scale"),
        B("Larger benchmark networks of the kind used in related work " + n(2) + ", with measured scaling of trial power flows per step.",
          "Three-phase unbalanced feeders, forecasts for solar and load, real tariffs and measured profiles in place of synthetic ones.",
          "Dynamics and protection through a real-time simulator or hardware in the loop before any field use."),
        H2("Operator-Facing Features"),
        B("Human-in-the-loop approval of projected and rejected actions, recorded in the same hash chain, following the human-oversight requirements discussed for agent-assisted grid studies " + n(3) + ".",
          "A Model Context Protocol tool interface for the simulator and the shield " + n(3) + ".",
          "Real authentication, roles and server-side key storage, replacing the browser-side demo gate.",
          "A user study of the decision lane, dry run and audit view with students and operators."),
        H2("Engineering Clean-up"),
        B("Repair the two failing grid tests (compute the expected value in the test instead of fixing 10.0 kW and -3.123 kW) and the hanging WebSocket test (use an asynchronous client).",
          "Reduce the roughly threefold step-time cost of the shield with sensitivity screening or cached factorisations.",
          "Containerise, add server-side persistence and run the experiment as a scheduled job with archived results."),
    ]


def novelty_blocks():
    return [
        H2("2.1 Positioning"),
        P(f"Three works frame the novelty claim. The base paper {n(1)} designs a rule-based multi-agent energy management system for a DC microgrid, regulates the bus voltage at 800 V in eight Simulink scenarios, and lists scalability, software integration, cybersecurity and the lack of experimental validation as open issues. "
          f"Grid-Agent {n(2)} uses a language-model planning agent and a validation agent that runs candidate actions in a sandbox with rollback on IEEE and CIGRE networks; its best configurations report a 100 % success rate and weaker ones 63 % and 44 %. "
          f"Picault and Goubet {n(3)} argue in a position paper for Model Context Protocol access to grid simulators under human oversight and set requirements such as traceability and human validation, without quantitative results."),
        P("SafeGrid-AI sits between these: it keeps the multi-agent structure of the first, the language-model proposer of the second and the traceability and oversight concern of the third, and it adds an independent safety layer with an explanation and audit interface. "
          "The claim is about the combination and the evaluation, not about a new learning algorithm."),
        H2("2.2 What Is New"),
        TAB("Novelty compared with the three framing papers", ["Element", "Base paper [1]", "Grid-Agent [2]", "MCP position paper [3]", "SafeGrid-AI"],
            [["Decision makers", "Rule-based agents", "LLM planner", "LLM agents via MCP tools", "Pluggable provider (mock measured), deterministic fallback"],
             ["Safety mechanism", "Control keeps bus voltage regulated", "Sandboxed trial with rollback", "Human validation (proposed)", "Deterministic shield: approve, project or reject before execution"],
             ["Action modification", "-", "Revise plan and retry", "-", "Largest safe scale found by bisection, original request preserved"],
             ["Attribution of violations", "-", "-", "-", "New-or-worse than the idle grid state"],
             ["Explanation", "-", "-", "Traceability as a requirement", "Structured explanation per decision, no stored chain-of-thought"],
             ["Audit", "-", "-", "Traceability as a requirement", "SHA-256 hash-chained safety log, verified in 21 of 21 runs"],
             ["Evidence", "8 Simulink scenarios", "IEEE/CIGRE benchmarks", "None (position paper)", "63 runs, 7 scenarios, 3 strategies, 3 seeds, counterfactual of raw proposals"]],
            widths=[1.0, 1.1, 1.2, 1.3, 1.9], size=8.5),
        P("Five elements are new in this project, in a modest sense of the word:"),
        N("**A verdict with three values.** A veto-only validator forces the agent to guess again. The shield returns the largest safe fraction of the request by bisection, so the agent's intent survives at a smaller size; of 1,512 proposals, 237 were handled this way. Projection of an unsafe action onto a safe set is a known idea in safe learning " + n(13) + ", applied here to a grid feeder with a full power flow in the loop.",
          "**Attribution against the idle baseline.** A violation is blamed on an action only if it is new or worse than the same step with every agent idle. This lets the evaluation separate the harm an action does from stress the scenario already contains, and it stops the shield from blocking an action that improves an already violated grid.",
          "**Enforced independence.** The shield imports nothing from the language-model, agent, simulation or grid packages, and a test fails if it ever does. The deterministic layer therefore cannot be influenced by the layer it supervises.",
          "**Explanations from structure.** Decisions are explained from the inputs, decision factors and safety result. Free-text model rationales are not reliable accounts of behaviour " + n(17) + ", so none is requested or stored.",
          "**A counterfactual evaluation.** Besides measuring what happened, every step also computes what the raw proposals would have done without the shield, so the benefit is measured and not assumed: 192 violations in 145 steps for the shielded arm's proposals."),
        H2("2.3 What Is Standard"),
        P("Most of the system is standard engineering, and the report does not claim otherwise: multi-agent decomposition of a power system " + n(8) + ", " + n(18) + "; AC power flow with pandapower " + n(11) + "; a closed action schema and sandboxing of model output; bisection for a monotone constraint; SHA-256 hash chaining " + n(20) + "; a REST and WebSocket API; and a React dashboard. "
          "The language-model interface follows the common pattern of a tool call returning structured arguments " + n(16) + ". Shielding as a concept comes from safe reinforcement learning " + n(12) + ", " + n(14) + ", and the concern that learning systems act unsafely goes back to the safety problems catalogued by Amodei et al. " + n(15) + "."),
        H2("2.4 Limits of the Novelty Claim"),
        P("The claim is bounded by the evidence: the shield was evaluated on a three-node simulated feeder with a mock language model, so it has not been shown to be better than the sandbox-and-rollback approach of Grid-Agent, which was evaluated on other networks and with real models. "
          "No numeric comparison with any of the three papers is possible, because the systems, benchmarks and metrics differ."),
    ]


def contribution_blocks():
    return [
        P("The contributions of the project, stated as things that now exist and were checked:"),
        N("**A neuro-symbolic architecture in running code.** A proposer, which may be a language model, and a deterministic validator separated by a closed `EnergyAction` schema and by enforced module independence, with a coordinator in between (Chapter 5, Chapter 6).",
          f"**A Symbolic Safety Shield with projection.** Ten ordered checks (structure, power limits, battery, node limits, power balance, power flow, voltage, line loading, transformer, grid limits), 25 violation codes and bisection projection with re-verification of the rounded action. In 21 shielded runs it handled {F.PROPOSALS:,} proposals and caused no violation in 504 steps.",
          "**A violation-attribution rule and an evaluation built on it.** Three arms (rule baseline, agents without shield, SafeGrid-AI), seven scenarios, three seeds, per-scenario tables and the counterfactual count of what raw proposals would have caused.",
          "**Explainability and audit by design.** A structured explanation for every decision, a hash-chained safety log verified in 21 of 21 runs, and a dry-run tool that lets an operator test any action against the shield without applying it.",
          "**An operator console.** A React application with live run control, single-line diagram, agent monitor, shield view, power-flow charts, scenario runner and explainability view, tested in a browser at three widths and two themes with no console errors.",
          "**An honest record.** The documents state what the measurements do not show: a mock model, no violation-resolution rate, three seeds, a model-relative guarantee, two failing tests and one hanging test, and no user study."),
        P(f"Reuse by others is straightforward: any controller that can return an `EnergyAction` can be placed behind the provider interface and measured on the same scenarios, with or without the shield; the 63-run result file is kept at `docs/results/experiment_3seeds_24steps.json`."),
    ]


def scope_blocks():
    return [
        H2("1.1 In Scope"),
        B("**Simulated network.** A three-node low-voltage feeder behind a 20/0.4 kV, 0.25 MVA transformer, solved with an AC power flow (pandapower " + n(11) + ") every 15 minutes of simulated time.",
          "**Agents.** Three agents (residential prosumer with 6 kWp PV and a 10 kWh battery; EV storage node with a 40 kWh battery, charge only, 7.4 kW; renewable prosumer with 20 kWp PV and a 30 kWh battery) that perceive a structured context and propose one action per step.",
          "**Actions.** Seven action types: charge, discharge, import, export, curtail generation, shift load and idle, under a closed schema.",
          "**Safety.** Ten ordered checks, three verdicts (approved, projected, rejected), configurable limits and a hash-chained audit log.",
          "**Scenarios.** Seven seeded scenarios: normal, high solar, peak demand, battery stress, line congestion, voltage violation and unsafe AI action.",
          "**Providers.** A deterministic mock, a rule-based baseline, a failing provider for tests, a fault-injecting provider and an API provider for a hosted model, any of which may fail into a labelled fallback.",
          "**Interfaces.** A REST and WebSocket API and a React console with seven screens, a landing page and a demo sign-in.",
          "**Evaluation.** An experiment runner for three strategies, and results stored in SQLite."),
        H2("1.2 Out of Scope"),
        B("Real hardware, field data or any connection to a real network.",
          "Protection, fast dynamics, frequency control, harmonics and three-phase unbalance.",
          "Forecasting, electricity markets and real tariffs (a time-of-use tariff of 3.8 to 9.0 INR per kWh is illustrative).",
          "Training or fine-tuning of a language model, and evaluation of a live hosted model.",
          "Authentication, authorisation and transport security of the API; the demo sign-in is a browser-side gate only.",
          "User studies and usability evaluation.",
          "Formal verification of the shield."),
        H2("1.3 Intended Users and Use"),
        P("The intended users are students, instructors and researchers who want to study how an autonomous proposer behaves under a safety layer. The intended use is simulation, teaching and comparison of controllers. "
          "The software is not intended to control, and must not be connected to, real distribution equipment."),
    ]


def assumption_blocks():
    return [
        P("The results depend on the following assumptions, all of which are built into the simulator or the experiment:"),
        B("**Quasi-static operation.** Each 15-minute step is solved as a steady state; dynamics inside the step are ignored.",
          "**Single-phase equivalent.** The feeder is balanced; load power factor is 0.95; line type NAYY 4x50 SE.",
          "**Perfect observation.** Agents receive exact node state, prices and a weather label; there is no measurement noise or communication delay.",
          "**The simulator is the truth.** The shield judges an action by what the simulated power flow says; if the model were wrong, the shield would protect the wrong limits.",
          "**Synthetic inputs.** Solar follows `sin^1.2` between 06:00 and 18:00 scaled by a seeded cloud factor of 0.45 to 1.0; household load has a morning and an evening bump with 5 % seeded noise; the tariff and the export credit (60 % of the import price) are illustrative.",
          "**Monotone safety.** Bisection assumes that scaling an action down never makes it less safe; the defensive re-verification of the final rounded action guards against small violations of this assumption.",
          "**Limits come from configuration.** 0.95 to 1.05 pu, 100 % line and transformer loading, 200 kW grid import and export; the voltage band is of the kind used in public-network standards " + n(19) + ".",
          "**A mock stands in for the language model.** The deterministic, seeded provider produces plausible proposals with occasional over-sizing; real models will behave differently."),
    ]


def limitation_blocks():
    cons = [
        "Language-model reasoning quality, robustness to prompts and real inference latency are all unmeasured. The measured benefit of the shield is the benefit against a mock that over-sizes requests on purpose, so it is likely an indication, not an estimate, of the benefit against a real model.",
        "The project cannot say how often unsafe proposals are repaired when the grid is already outside its limits. It can say only that actions do not make things worse. The `peak_demand` result shows that, there, the rule baseline leaves fewer violation steps than the shielded agents.",
        "The 0.17 ms mean decision latency in the tables must not be read as the latency of an AI planner; with a hosted model it would be orders of magnitude larger and would dominate the step time.",
        "Three seeds give means but not meaningful confidence intervals; the feeder has three nodes, so effects such as congestion are exaggerated compared with real networks and phenomena such as unbalance are absent. Absolute costs in INR are illustrative.",
        "The shield's guarantee is that executed actions create or worsen no violation of the configured limits in the simulated model. It is neither a formal proof nor a promise of a violation-free grid. The wording of the abstract (\"mathematically guaranteeing zero physical constraint violations\") is stronger than what was built or tested.",
        "No number from this project can be compared with the base paper's. Statements about advantages over it are statements about design, not about measured performance.",
        "Test code defects reduce confidence in the regression suite: the two grid tests fail on numeric tolerances with pandapower 3.5.6, and the WebSocket test hangs. They do not affect the experiment results, which come from the engine, but a green suite would be better evidence.",
        "Whether operators find the explanations clear, and whether they trust or over-trust the shield, is unknown.",
    ]
    out = [P(f"{len(GAPS)} limitations affect how the results may be read. Each is stated with its consequence.")]
    for i, (g, c) in enumerate(zip(GAPS, cons), 1):
        out.append(H2(f"3.{i} " + ["No live language model", "No violation-resolution rate", "Decision latency is not representative", "Small synthetic experiment", "Model-relative guarantee", "Qualitative comparison with the base paper", "Failing and hanging tests", "No user study"][i - 1]))
        out.append(P("**Limitation.** " + g))
        out.append(P("**Consequence.** " + c))
    return out


def not_measured_blocks():
    return [
        P("Honest reporting means listing what was not measured. The table gives each item, the reason, and what would be needed."),
        TAB("Quantities not measured", ["Quantity", "Why it was not measured", "What would be needed"],
            [["Accuracy, F1, precision, recall, confusion matrix", "Not applicable: there is no dataset, no trained model and no classification task; inputs are generated from a seed", "Nothing; these metrics do not apply to this project"],
              ["Real language-model latency and cost", "No API key was configured; the provider was run only in its unconfigured and mocked paths", "A hosted model, a key and a repeat of the experiment"],
              ["Violation resolution rate", "The evaluation measures violations prevented and steps with any violation, not repair of pre-existing violations", "A resolution metric and a planner that is rewarded for resolving"],
              ["Quality of language-model reasoning", "The mock is a transparent heuristic with seeded over-sizing", "Evaluation with real models"],
              ["Performance on standard test networks", "Only the three-node feeder was modelled", "IEEE and CIGRE feeders in pandapower"],
              ["Formal proof of the shield", "Evidence is by testing and simulation", "A stated model and a verifier"],
              ["User acceptance, usability and trust", "No users were recruited", "A task-based study with a questionnaire"],
              ["Load and soak behaviour", "One local user, short runs", "Concurrent clients and long runs"],
              ["Confidence intervals", "Three seeds only", "More seeds (for example 20 or more)"]],
            widths=[1.8, 2.5, 2.2], size=9.5),
    ]


def walkthrough_blocks():
    return [
        P("This section walks through the five pieces of code that carry the design. Excerpts are copied from `backend/app` and shortened only by removing blank lines and comments of no importance."),
        H2("3.1 The shield's decision procedure (`safety/shield.py`)"),
        P("`SymbolicSafetyShield.evaluate` has four stages. It first applies structural checks, then approves an idle action at once, then evaluates the request exactly as proposed with local checks and a trial power flow, and finally, only if that finds a violation, projects the request."),
        CODE("""# 1. structural / sanity checks -> reject
sv = validator.structural_violations(action, node, lim, cfg, known_agents, known_nodes)
if sv:
    return self._decision(ShieldStatus.REJECTED, action, None, sv, [], Setpoint(), 0.0, current, current, False)

# 3. evaluate the request exactly as proposed
v_local = local_new(sp_req)
v_grid = []
trial_req = None
if not v_local:
    trial_req = trial(sp_req)
    v_grid = grid_new(trial_req)
violations = v_local + v_grid
if not violations:
    ...  # APPROVED, with the duration aligned to the step""", 8.5),
        P("The cheap local checks (battery, node limits, balance) run first, and the expensive trial power flow runs only when they pass. This ordering is why a rejected absurd request costs a median of 36.6 ms while a projected one costs 230.0 ms in the latency table."),
        H2("3.2 Projection by bisection (`safety/projector.py`)"),
        CODE("""def bisect_max(is_safe, hi=1.0, iters=30):
    \"\"\"Largest lam <= hi with is_safe(lam), assuming safety is monotone in lam. Returns 0.0 if none.\"\"\"
    if is_safe(hi):
        return hi
    if not is_safe(0.0):
        return 0.0
    lo, up = 0.0, hi
    for _ in range(iters):
        mid = 0.5 * (lo + up)
        if is_safe(mid):
            lo = mid
        else:
            up = mid
    return lo""", 8.5),
        P("`is_safe(lam)` scales the physical effect of the action by lam and asks whether the scaled action creates any new or worse violation. The shield first bisects over the cheap local limits (40 iterations) and then over the power-flow limits (14 iterations). "
          "The monotonicity assumption in the docstring is the honest weak point of the method: if a smaller action could be less safe, the bisection could return an unsafe value, which is why the shield then re-verifies the exact rounded action up to four times, multiplying lam by 0.999 each time, and rejects any result below 0.05 kW."),
        H2("3.3 Attribution of violations (`safety/validator.py`)"),
        CODE("""def new_violations(after, before, tol=1e-4):
    \"\"\"Violations attributable to the action: new, or pre-existing but made worse.\"\"\"
    prior = {v.key(): v.excess for v in before}
    return [v for v in after if v.key() not in prior or v.excess > prior[v.key()] + tol]""", 8.5),
        P("`before` is the violation list of the grid with every agent idle (`base_grid`) and `after` is the list after the trial. A violation that existed before survives only if its excess has grown by more than the tolerance. "
          "The same function defines the metric `violations_caused_by_actions` in the engine, so the shield and the evaluation use one definition."),
        H2("3.4 Ordering of proposals (`simulation/coordinator.py`)"),
        CODE("""RELIEF = {"idle", "curtail_generation", "shift_load"}

def order_decisions(decisions, step):
    \"\"\"Relief actions first (they can only help), then rotate the rest for fairness.\"\"\"
    ds = list(decisions)
    if ds:
        k = step % len(ds)
        ds = ds[k:] + ds[:k]
    return sorted(ds, key=lambda d: 0 if d.action.action_type in RELIEF else 1)""", 8.5),
        P("The coordinator never edits an action. It rotates the starting agent each step so that no agent always sees the grid first, and then moves relief actions to the front, because sorting is stable and relief actions can only help. "
          "The shield validates the proposals in this order against the cumulative state, so a later proposal sees the effect of earlier ones. `detect_conflicts` reports `PEER_MISMATCH`, `TARGET_CONTENTION` and `SHARED_FEEDER` for the log and the dashboard; 241 conflicts were reported across the 21 shielded runs."),
        H2("3.5 The tamper-evident log (`safety/events.py`)"),
        CODE("""@staticmethod
def create(event_id, run_id, step, sim_time, wall_time, payload, prev_hash):
    body = _canonical(payload)
    digest = hashlib.sha256((prev_hash + _canonical([event_id, run_id, step, sim_time]) + body).encode()).hexdigest()
    return SafetyEvent(event_id, run_id, step, sim_time, wall_time, body, prev_hash, digest)

def verify_chain(events):
    prev = GENESIS
    for e in events:
        expect = hashlib.sha256((prev + _canonical([e.event_id, e.run_id, e.step, e.sim_time]) + e.payload_json).encode()).hexdigest()
        if e.prev_hash != prev or e.hash != expect:
            return False
        prev = e.hash
    return True""", 8.5),
        P("Each event stores the hash of the one before it, and its own hash covers that value, the event identity and a canonical (sorted-key, compact) JSON payload. The wall-clock time is stored but left out of the hash so that two runs with the same seed produce the same chain. "
          "Editing the payload of one event, removing one or reordering them changes a hash and breaks every later link; `verify_chain` recomputes them all. The log is tamper-evident, not tamper-proof: anyone who can rewrite the whole chain can also recompute it, so the head hash would have to be stored elsewhere to detect that."),
    ]


def decision_blocks():
    return [
        TAB("Implementation decisions and their reasons", ["Decision", "Reason", "Cost accepted"],
            [["Separate proposer and validator behind a closed schema", "The model may be wrong or hostile; the layer that stops it must not depend on it. The schema forbids extra fields and non-finite numbers, and a test enforces the import isolation.", "Every proposal must be expressible as one of seven action types"],
             ["Project instead of veto", "The agent's intent is usually sensible at a smaller size; 237 of 1,512 proposals were kept this way.", "Bisection needs several trial power flows; assumes monotone safety"],
             ["Full AC power flow in the loop (pandapower)", "Voltage and line limits depend on the whole network; a lumped approximation would miss the effects the shield exists to catch " + n(11) + ".", "About 0.1 s of compute per step; the shielded step time is 347.8 ms"],
             ["Attribute violations against the idle baseline", "Separates what an action causes from stress the scenario creates, and lets the shield accept actions that relieve a violated grid.", "A violation that was already present is not removed by design"],
             ["Relief-first, rotating order", "Relief actions cannot harm, and rotation avoids a fixed favourite among the agents.", "Order still matters: later proposals may be projected harder"],
             ["Structured explanations, no chain-of-thought", "Model-written rationales are not faithful accounts of behaviour " + n(17) + "; structured inputs and factors can be checked.", "Explanations are less fluent than free text"],
             ["Deterministic, seeded mock provider", "Reproducible experiments and tests without an API key; the same seed gives the same totals.", "Results measure the shield and coordination, not language-model quality"],
             ["Labelled fallback decision", "Any provider failure, time-out or invalid output becomes a deterministic decision tagged `fallback` and is still shielded, so a model outage cannot stop or endanger the grid.", "Fallback quality is that of a simple cost-aware heuristic"],
             ["SQLite with a hash-chained log", "No server to install; the chain makes edits detectable " + n(20) + ".", "Single-writer database; the head hash is not stored elsewhere"],
             ["FastAPI with REST and one WebSocket", "Typed requests (pydantic), automatic validation (422 for unknown fields), and a single stream for live events.", "No authentication in the prototype"],
             ["React console with a demo sign-in", "Gives a reviewable operator view; the sign-in only gates the demonstration.", "The gate is browser-side and not a security boundary"],
             ["15-minute step", "Matches typical metering and tariff intervals and keeps a quasi-static model reasonable.", "Fast dynamics are not represented"]],
            widths=[1.7, 3.1, 1.7], size=9),
        P("Two decisions are worth stating in more detail because they are easy to get wrong. First, import and export are treated as net exchange targets and not as battery commands: asking to export 5 kW means that the node's connection point should carry 5 kW outward, and the battery covers the difference between that target and the node's own load and solar balance. "
          "That is why a request to export 3 kW from a node that can only import is rejected as `DIRECTION_UNATTAINABLE`; no amount of scaling turns an import into an export. "
          "Second, the shield never trusts the arithmetic of the proposal. It does not read the agent's stated confidence or reason codes when deciding; they are stored for the audit trail only."),
    ]


# ------------------------------------------------------------------------------------------------ extensions
def _after(blocks, heading, extra):
    """Insert `extra` at the end of the section that starts with `heading` (just before the next H1/H2, or at the end)."""
    idx = next(k for k, b in enumerate(blocks) if b[0] in ("h2", "h3") and b[1].startswith(heading))
    j = next((k for k in range(idx + 1, len(blocks)) if blocks[k][0] in ("h1", "h2")), len(blocks))
    return blocks[:j] + extra + blocks[j:]


_chapter10 = chapter10_blocks


def chapter10_blocks():  # noqa: F811
    b = _chapter10()
    b = _after(b, "10.1", [
        P("Two smaller improvements follow from the experiment. A randomised scenario library, with faults, weather, loads and starting states drawn from distributions, would test the safety claim on hundreds of situations and support confidence intervals instead of means over three seeds. "
          "The strict counters for voltage and line loading (Section 8.3) should use the shield's own tolerance, so that a quantity placed exactly on its limit by projection is not counted by one counter and accepted by another.")])
    b = _after(b, "10.2", [
        P("A fifth feature is a replay mode: because every run has a seed, a configuration and a hash-chained log, a past run can be replayed in the dashboard and a changed constraint "
          "(for example a 0.97 pu lower voltage limit) applied to the same proposals to see which decisions would change, which turns the audit trail into a tool for tuning limits and post-incident review.")])
    b = _after(b, "10.3", [
        P("The shield is the part that must be most reliable, so it should be versioned separately from the agents, deployed with its constraint file under change control and tested against a fixed library of proposals on every release. "
          "At hundreds of agents the cost of trial power flows would need sensitivity screening or a distributed validator.")])
    b = _after(b, "10.4", [
        P("A final direction is the relationship between shield and planner: today the shield is a veto with repair and the planner sees its corrections only in the next context. "
          "A bounded propose, validate, revise loop within one step is the closest analogue to the validation agent of Grid-Agent " + n(2) + " and would allow a like-for-like comparison.")])
    return b


_conclusion = conclusion_blocks


def conclusion_blocks():  # noqa: F811
    b = _conclusion()
    b = _after(b, "What the Measurements Show", [
        TAB("Headline measurements (mean per 24-step run, 21 runs per strategy)", ["Metric", "Rule baseline", "Agents, no shield", "SafeGrid-AI"],
            [["Steps with violations caused by actions", _o("baseline_rule", "violation_steps_caused_by_actions"), _o("agents_unshielded", "violation_steps_caused_by_actions"), _o("safegrid_shielded", "violation_steps_caused_by_actions")],
             ["Steps with any violation after execution", _o("baseline_rule", "violation_steps_executed"), _o("agents_unshielded", "violation_steps_executed"), _o("safegrid_shielded", "violation_steps_executed")],
             ["Energy cost (INR, illustrative)", _o("baseline_rule", "total_cost", 1), _o("agents_unshielded", "total_cost", 1), _o("safegrid_shielded", "total_cost", 1)],
             ["Renewable utilisation", _o("baseline_rule", "renewable_utilization", 3), _o("agents_unshielded", "renewable_utilization", 3), _o("safegrid_shielded", "renewable_utilization", 3)],
             ["Mean step time (ms)", _o("baseline_rule", "avg_step_time_ms", 1), _o("agents_unshielded", "avg_step_time_ms", 1), _o("safegrid_shielded", "avg_step_time_ms", 1)]],
            widths=[2.7, 1.2, 1.4, 1.2], size=10, align=["l", "r", "r", "r"]),
        P("Beyond the averages, the system behaved as designed in the situations built to test it: a 1,000 kW export was rejected, a 900 kW import was rejected, a malformed output became a labelled fallback decision, a congested feeder never exceeded its rating, and the dashboard displayed each of these decisions with its reasons.")])
    return b


_future = future_blocks


def future_blocks():  # noqa: F811
    b = _future()
    b = _after(b, "Evaluate with a Real Language Model", [
        P("The experiment design is ready for this: the provider interface, the schema validation of model output, the time-out and the labelled fallback already exist, and the experiment runner accepts a provider name. "
          "What is missing is an API key, a budget and a decision about which models to compare. A reasonable protocol is the same seven scenarios and three arms with at least ten seeds, with the model's temperature fixed, so that variation between seeds reflects the scenario and not sampling noise; "
          "wall-clock time per step would then be dominated by model latency, and the shield's 0.35 s per step would no longer be the bottleneck.")])
    b = _after(b, "Stronger Guarantees", [
        P("A formal statement needs three ingredients: the model (the quasi-static AC power flow and the battery model), the property (no executed action creates or worsens a violation of the configured limits) and the assumptions (monotone safety under scaling, the tolerance of the attribution rule). "
          "The first two can be written down directly; the third is where a verifier or an exhaustive test over a fine grid of actions would provide real evidence, because it is the assumption the bisection relies on.")])
    b = _after(b, "Realism and Scale", [
        P("Measured profiles would also change the picture. Solar output on a real day, a metered household load shape and a real tariff would move the numbers for cost and renewable utilisation, and might change which scenarios are hard; "
          "the present synthetic profiles were chosen to be transparent and reproducible, not to be representative.")])
    b = _after(b, "Operator-Facing Features", [
        P("The order in which these should be done is: approval workflow first, because it changes the role of the shield from automatic to supervised; the tool interface second, because it lets other agents use the system; the user study third, because it needs the first two to be meaningful; authentication last, because it matters only once a deployment target exists.")])
    return b


_contrib = contribution_blocks


def contribution_blocks():  # noqa: F811
    b = _contrib()
    return b + [
        TAB("Contributions and how each was checked", ["Contribution", "Where it lives", "How it was checked"],
            [["Proposer / validator separation", "`models/actions.py`, `safety/shield.py`", "`test_malformed_actions_fail_schema_validation`; `test_shield_does_not_import_llm_or_agents`"],
             ["Shield with projection", "`safety/validator.py`, `projector.py`, `shield.py`", "22 shield tests; 504 shielded steps with 0 violations caused"],
             ["Violation attribution", "`validator.new_violations`, `engine.step`", "`test_preexisting_violation_does_not_block_a_relieving_action`; experiment metrics"],
             ["Coordinator", "`simulation/coordinator.py`", "`test_coordinator_detects_peer_mismatch`; 241 conflicts reported in 21 runs"],
             ["Explanations", "`agents/explain.py`", "`test_explanation_is_structured_and_has_no_chain_of_thought`"],
             ["Hash-chained log", "`safety/events.py`", "`test_event_chain_is_tamper_evident`; chain valid in 21 of 21 runs"],
             ["Three-arm experiment", "`simulation/experiment.py`", "`test_experiment_runs_real_simulations`; 63 runs saved to JSON"],
             ["Operator console", "`frontend/src`", "Browser walk at 360, 768 and 1440 px, light and dark; smoke test 20 of 20"]],
            widths=[1.6, 2.3, 2.6], size=9.5),
        P("What is **not** claimed as a contribution: a new learning algorithm, a new power-flow method, an evaluation of any real language model, or a safety proof. "
          "The contribution is a design, an implementation of it, and a measurement of what the design does inside the limits stated in the limitations document."),
    ]


_scope = scope_blocks


def scope_blocks():  # noqa: F811
    b = _scope()
    b = _after(b, "1.1 In Scope", [
        TAB("Scope by dimension", ["Dimension", "Included", "Excluded"],
            [["Network", "3 nodes, 4 buses, 3 lines, 1 transformer; single-phase equivalent", "Meshed, three-phase or larger networks"],
             ["Time", "15-minute quasi-static steps; runs of 12 to 32 native steps (24 in the experiment)", "Seconds-scale dynamics, protection"],
             ["Control", "One action per agent per step, seven action types", "Multi-step plans executed without re-validation"],
             ["Safety", "Voltage, line, transformer, battery, node and grid import/export limits", "Frequency, harmonics, short-circuit levels"],
             ["Data", "Seeded synthetic profiles", "Measured profiles, forecasts"],
             ["Models", "Deterministic mock; API provider implemented", "Evaluated hosted models; training or fine-tuning"],
             ["People", "Developer browser walk-through", "User studies"]],
            widths=[1.1, 3.0, 2.4], size=9.5)])
    return b + [
        H2("1.4 Deliverables"),
        P(f"The deliverables are the source code ({F.LOC['backend']:,} lines of backend, {F.LOC['tests']} lines of tests and {F.LOC['frontend']:,} lines of frontend), the run scripts, the documentation set, the 63-run result file and the screenshots and diagrams used in the reports. "
          "Everything runs on one ordinary computer without a graphics processor, and the backend and frontend start with one script (`run.bat`)."),
    ]


_assume = assumption_blocks


def assumption_blocks():  # noqa: F811
    b = _assume()
    return b + [
        TAB("Numerical assumptions and what changes if they are wrong", ["Assumption", "Value used", "If it were different"],
            [["Voltage band", "0.95 to 1.05 pu", "A tighter band raises the intervention rate and the cost of safety"],
             ["Line and transformer limit", "100 % of rating", "A lower operating limit needs only a new constraint file"],
             ["Grid import and export limit", "200 kW", "Not reached on this small feeder in the reported scenarios; a much lower value would bind"],
             ["Smallest useful action", "0.05 kW", "Larger values turn more projections into rejections"],
             ["Implausible-request factor", "5 x node rating", "Smaller values reject large but possibly valid requests"],
             ["Power-balance tolerance", "0.05 kW", "Looser values hide errors in the power flow"],
             ["Control step", "15 minutes", "Longer steps make the quasi-static model less accurate"],
             ["Mock over-sizing", "Seeded, scenario-dependent rates of unsafe proposals", "A different rate changes the size of the unshielded harm, not the shielded result"]],
            widths=[1.7, 1.9, 2.9], size=9.5),
        P("Each of these is a configuration value, not a constant buried in a check, so a different assumption can be tested by editing the constraint file or the run configuration. "
          "The experiment used the defaults shown."),
    ]


_limit = limitation_blocks


def limitation_blocks():  # noqa: F811
    b = _limit()
    return b + [
        H2("3.9 What Would Change the Conclusions"),
        P(f"Four findings would change the conclusions if they came out differently. First, a real language model that routinely produces schema-valid but plainly unreasonable proposals would push the intervention rate far above the measured {F.pct(F.mean('safegrid_shielded', 'intervention_rate'))} and would make the cost of safety (compute and renewable utilisation) the main question. "
          "Second, a trial power flow that disagrees with a more detailed network model would show that the shield enforces the wrong limits. Third, a user study in which operators over-trust the shield's \"approved\" label would show that the interface, not the algorithm, creates the risk. "
          "Fourth, a test of the bisection on non-monotone cases that returns an unsafe value would show that the defensive re-verification is not enough."),
        P("None of these has been observed, and none has been tested, which is why the guarantee is stated as model-relative and why the report prefers the wording \"no new or worse violation in the simulated model\" to \"zero violations\"."),
    ]


_notmeas = not_measured_blocks


def not_measured_blocks():  # noqa: F811
    b = _notmeas()
    return b + [
        P("Two of these deserve a sentence on why they are not simply an oversight. Classification metrics are absent because the project has no classifier: it generates inputs from a seed and asks what the shield does with proposals, so reporting an accuracy or an F1 score would be inventing a task. "
          "Real-model latency is absent because the measured provider is a deterministic mock; presenting its 0.1-0.2 ms as a result about artificial intelligence would be misleading. "
          "The table is kept in the report so that a reader looking for these numbers finds an explicit statement instead of a gap."),
    ]


_walk = walkthrough_blocks


def walkthrough_blocks():  # noqa: F811
    b = _walk()
    return b + [
        H2("3.6 One step of the engine (`simulation/engine.py`)"),
        P("`SimulationEngine.step` is the place where the pieces meet. It applies the seeded inputs to the simulator, takes a no-action baseline with a trial power flow, builds an observation, lets the agent manager perceive and decide concurrently, asks the coordinator for conflicts and an order, and then hands the validation and commit to a worker thread because it is CPU-bound."),
        CODE("""contexts = await self.manager.perceive_all(obs)
decisions = await self.manager.decide_all(contexts)
conflicts = coordinator.detect_conflicts(decisions)
ordered = coordinator.order_decisions(decisions, i)

results, raw_viol, final_trial, stats = await asyncio.to_thread(
    self._validate_and_commit, decisions, ordered, current)""", 8.5),
        P("Inside `_validate_and_commit` the engine first computes the counterfactual: it resolves every raw proposal to a set-point, runs one trial power flow with all of them applied, and records the violations (`raw_viol`). "
          "This is the number reported as violations the raw proposals would cause. It then validates the ordered proposals one by one, each against the cumulative set-points accepted so far, and finally commits the accepted set-points once. "
          "In the ablation arm the same function applies the proposals as requested without the shield, so the two arms differ in one branch."),
        H2("3.7 Provider failure becomes a labelled fallback (`agents/base_agent.py`)"),
        CODE("""try:
    action, source = await asyncio.wait_for(self.provider.generate(ctx), timeout=self.timeout_s)
except Exception as e:  # any provider failure -> labelled deterministic fallback (still shielded)
    reason = f"{type(e).__name__}: {str(e)[:160]}"
    action, source = self.fallback_policy(ctx), "fallback"
""", 8.5),
        P("Time-outs, unreachable services, unconfigured keys and schema-invalid outputs all end in the same place: a deterministic cost-aware decision tagged `fallback`, with the reason kept for the log. The fallback decision is passed to the shield like any other proposal, "
          "so a model outage can neither stop the grid agents nor bypass validation. In the experiment the fallback rate is 0.2 %, which is the one deliberately malformed output injected by the `unsafe_ai_action` scenario."),
    ]


_decide = decision_blocks


def decision_blocks():  # noqa: F811
    b = _decide()
    return b + [
        H3("Alternatives considered"),
        B("**A validation agent instead of a rule layer.** A second language model that checks the first was not chosen, because a safety layer built from the same kind of component shares its failure modes and cannot be tested to a fixed expectation. A deterministic checker can be unit-tested with hand-written cases.",
          "**A linearised power-flow check.** A DC or sensitivity-based approximation is faster, but voltage limits at the end of a weak feeder are exactly where the approximation is poorest; the exact AC trial was kept and its cost accepted.",
          f"**Rejecting every unsafe proposal.** This is the simplest rule and would have rejected {F.PROJECTED + F.REJECTED} proposals, {F.PROJECTED} of which were only too large. Projection kept most of their value.",
          "**Storing model rationales for explanation.** Rejected on grounds of faithfulness and of cost; structured factors were enough to explain each decision and are checkable.")
    ]


_conclusion2 = conclusion_blocks


def conclusion_blocks():  # noqa: F811
    b = _conclusion2()
    return _after(b, "Contributions", [
        H2("Lessons Learned"),
        B("**Measure the counterfactual.** Reporting only what happened with the shield on would have made the result a statement about the scenarios. Computing, in the same step, what the raw proposals would have done turned it into a statement about the shield.",
          "**Separate harm from stress.** A metric that simply counts violations per step would charge the shield with stress that no action caused. The attribution rule avoids that, and it also exposes the cases (peak demand) where the shield leaves more stress than a simple controller.",
          "**Say what a number is.** A decision latency of 0.17 ms, a classification metric that does not exist, or a 'guarantee' stronger than the tests all look like results; writing down what each one is not kept the report honest.",
          "**Keep the checker small and dull.** The whole safety package is 621 lines of ordinary deterministic code (of 3,117 backend lines) with 22 dedicated unit tests, a deliberate contrast with the component it supervises.")])


_future2 = future_blocks


def future_blocks():  # noqa: F811
    b = _future2()
    return b + [
        H2("Suggested Order of Work"),
        TAB("Roadmap", ["Step", "Work", "Result expected"],
            [["1", "Repair the two grid tests and the WebSocket test", "A green regression suite"],
             ["2", "Run the 63-run experiment with a hosted model and at least ten seeds", "Real latency, cost, fallback rate; the shield's benefit against a real proposer"],
             ["3", "Add a resolution metric and a revise-after-veto loop", "Evidence on whether the planner can clear pre-existing violations"],
             ["4", "Move to benchmark feeders and a three-phase model", "Scaling behaviour of trial power flows; relevance beyond three nodes"],
             ["5", "Human approval workflow and a user study", "Usability and trust data"],
             ["6", "Formal statement and verification of the shield's guarantee", "A stronger, model-relative guarantee with stated assumptions"]],
            widths=[0.5, 3.2, 2.8], size=10, align=["c", "l", "l"]),
        P("The first two steps are cheap and answer the questions a reader will ask first; the others each open a new line of work and can proceed in parallel once a real model is available."),
    ]


_limit2 = limitation_blocks


def limitation_blocks():  # noqa: F811
    b = _limit2()
    return b + [
        H2("3.10 How to Read the Numbers"),
        P("The numbers in the report are measurements of a specific simulator. Three habits keep them in proportion. First, read the per-scenario tables before the overall means: the overall mean mixes a scenario in which nothing happens with one in which most proposals are changed. "
          "Second, read the attribution metric and the counterfactual together: 0 violations caused is meaningful because the raw proposals would have caused 192 violations in 145 steps. "
          "Third, treat the cost, renewable-utilisation and latency figures as indications of direction and order of magnitude, not as predictions for a real feeder or a real model."),
    ]
