"""Chapters 3 and 4: Feasibility study; System requirements and analysis."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import n


def _lat(name):
    for call, cnt, med, p95 in F.API_LAT:
        if call.startswith(name):
            return med, p95
    raise KeyError(name)


def feasibility_blocks():
    health = _lat("GET /api/health")
    state = _lat("GET /api/grid/state")
    step = _lat("POST /api/simulation/step")
    return [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        P("Before building the system we asked four questions: can it be built with the tools at hand, what does it cost, will the intended users be able to "
          "operate it, and does it fit the project calendar. This chapter answers them with what actually happened during the project."),
        H2("3.1 Technical Feasibility"),
        P("Every component of SafeGrid-AI is free, mature, open-source software and runs on one ordinary desktop computer. The network is modelled and solved "
          "with pandapower " + n(11) + "; the service layer is FastAPI with pydantic models and uvicorn; the dashboard is React 18 built with Vite, with three.js "
          "only on the landing page; persistence is SQLite from the Python standard library. The language-model side sits behind one small interface, so the "
          "project depends on no particular provider and was built and tested without an API key."),
        P("Feasibility was confirmed by measurement. The whole stack ran on a " + F.MACHINE + ". A read request such as the grid state returns in a median of "
          + str(state[0]) + " ms and a full simulation step, including three agent decisions and the shield's trial power flows, in a median of " + str(step[0]) + " ms, so a "
          "32-step scenario completes in about ten seconds. The main technical risks and how they were handled are summarised below."),
        TAB("Technical risks and mitigations", ["Risk", "Mitigation in the project"],
            [["A language model emits an unsafe or malformed action", "The proposal is a schema-validated EnergyAction; the Symbolic Safety Shield validates it; a failure becomes a labelled, shielded deterministic fallback"],
             ["No API key or no network during development and demonstration", "A deterministic, seeded mock provider produces repeatable proposals, including deliberately unsafe ones"],
             ["Power flow is slower than the control step", "Trial power flows run in a worker thread; measured mean step time is " + str(round(F.mean('safegrid_shielded', 'avg_step_time_ms'))) + " ms against a 15-minute simulated step"],
             ["Results cannot be reproduced", "All profiles and faults come from a seed; all 63 runs are recorded in one JSON file"],
             ["Safety log could be altered after the fact", "Each event carries the SHA-256 of the previous one; the chain was valid in 21 of 21 shielded runs"]],
            widths=[2.4, 3.8], size=9.5),
        P("Two design choices keep the technical risk low. The service is asynchronous: the agents decide concurrently and the CPU-bound part of a step (the "
          "shield and the power flows) runs in a worker thread, so a slow step never blocks the WebSocket stream or the read endpoints. And the language-model "
          "provider is replaceable at run time, with four implementations: a seeded mock, an API-based provider (Anthropic or OpenAI wire format, with the returned "
          "tool call validated against the action schema), a rule-based provider and a provider that always fails, used to test the fallback. Because the shield "
          "does not depend on the provider, switching changes how good the proposals are, not whether the executed actions are safe."),
        H2("3.2 Economic Feasibility"),
        P("The project was built without any purchase. The development machine already existed, all software is open source, and the measured results use the "
          "mock provider, so no paid language-model service was used. The table below lists the resources and what each cost the project. It is an account of "
          "what was incurred, not a budget estimate for a deployment, and team effort is not priced."),
        TAB("Development resources and cost incurred (INR)", ["Resource", "Source", "Cost incurred (INR)", "Note"],
            [["Development and test computer", "Existing desktop PC", "0", "No purchase; " + F.MACHINE],
             ["Python libraries (pandapower, FastAPI, pydantic, numpy, pandas, scipy)", "Open source", "0", "Installed from the public package index"],
             ["Front-end libraries (React, Vite, three.js, charting)", "Open source", "0", "Installed with npm"],
             ["Database", "SQLite, Python standard library", "0", "No server to run"],
             ["Test and capture tools (pytest, Playwright, Chromium)", "Open source", "0", "Used for tests and screenshots"],
             ["Language-model API", "Not used for measurements", "0", "A paid API would be needed to run the optional real-LLM provider; its cost depends on the provider and was not estimated"],
             ["Hosting", "Local machine only", "0", "No cloud deployment was made"]],
            widths=[2.2, 1.4, 0.9, 1.7], size=9.0, align=["l", "l", "c", "l"]),
        P("A real deployment would be dominated by other costs: measurement and communication equipment, integration with the operator's systems, a live "
          "language-model service with its per-request cost and latency, and verification of the safety layer. We do not estimate them, because no such "
          "deployment is within the scope of this work."),
        H2("3.3 Operational Feasibility"),
        P("The intended user is a grid operator, a researcher or a student who wants to see how an AI controller behaves on a small network. The dashboard "
          "has a landing page, a sign-in page and seven working views (dashboard, grid, agents, safety shield, power flow, scenarios and explainability), with "
          "run controls, a scenario choice and an agent-brain choice in the top bar of every screen, and a demo sign-in for reviewers. The interface works at "
          "widths from 360 to 1440 pixels in light and dark themes, and a browser walk through every screen produced no console errors and no horizontal "
          "overflow. Starting the system takes one script on Windows (run.bat); Appendix B gives the manual steps."),
        P("Use by actual operators was not tested. No user study was carried out, so operational feasibility rests on the working software and the browser "
          "checks, not on user feedback."),
        H2("3.4 Schedule Feasibility"),
        P("The work followed the three review phases of the course. No calendar dates are given because the project record does not hold them."),
        TAB("Project schedule by review phase", ["Phase", "Planned content", "Delivered"],
            [["Review 1", "Problem identification, literature survey, objectives, proposed architecture", "Batch abstract, base paper record, literature survey of five papers, objectives and problem statement"],
             ["Review 2", "Design and core implementation: network, agents, shield, API", "Pandapower network, three agents with provider interface, coordinator, Symbolic Safety Shield, FastAPI REST and WebSocket, SQLite store, first scenarios"],
             ["Final review", "Complete system, evaluation, user interface, documentation", "Seven scenarios and three-strategy experiment (63 runs), React dashboard, tests, screenshots, this report, decks and paper"]],
            widths=[1.0, 2.5, 2.7], size=9.5),
        H2("3.5 Advantages and Constraints"),
        H3("Advantages"),
        B("No cost, no special hardware, and no dependence on any single model provider.",
          "A repeatable experiment: the same seed gives the same profiles and the same mock decisions, so results can be regenerated.",
          "A modular design in which the provider, the agents, the shield and the simulator can each be replaced or tested alone."),
        H3("Constraints"),
        B("The network is a three-node synthetic feeder, so the findings do not transfer to real networks without further work.",
          "Real-LLM behaviour and latency are unknown; the mock provider is the only one measured.",
          "The shield's guarantee is only as good as the network model and the configured limits.",
          "Two unit tests fail on numeric tolerances and one WebSocket test hangs (Chapter 7); none of these affects the experiment results, but they are open defects."),
    ]


def requirements_blocks():
    health = _lat("GET /api/health")
    state = _lat("GET /api/grid/state")
    dry = _lat("POST /api/agents/{id}/decision")
    step = _lat("POST /api/simulation/step")
    t = F.TESTS
    return [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        H2("4.1 Existing System"),
        P("Today a low-voltage feeder with distributed generation is operated by fixed rules: inverter settings that limit voltage rise, time-of-use tariffs that "
          "nudge consumers, and protection that trips when a limit is breached. The base paper's multi-agent system " + n(1) + " is a better organised version of "
          "the same idea, with four rule-based agents that divide the control of a DC microgrid among themselves. Recent research systems add a language model "
          "that plans actions " + n(2) + n(3) + ", but they are prototypes whose safety checks are performed by trial execution, and they give an operator no "
          "structured explanation of each decision."),
        P("An operator sees the outcome, not the reasoning: a voltage alarm, a tripped breaker, a monthly bill. There is no way to ask why a battery was "
          "charged at a particular time, and with a language-model controller the answer is usually generated text whose faithfulness to the real cause cannot "
          "be checked " + n(17) + ". The needs that follow are for a controller that adapts, that is checked by something other than itself, and that leaves a record."),
        H2("4.2 Limitations of the Existing System"),
        B("Fixed rules cannot adapt to renewable variability, price changes or a changed topology.",
          "A central controller is a single point of failure; local rules alone do not coordinate neighbouring nodes that share a feeder.",
          "An unconstrained AI agent can propose an unsafe action, and a check that is itself performed by a language-model agent depends on the model.",
          "Decisions are not accompanied by explanations that an operator can audit, and there is no tamper-evident record of what was proposed and what was executed."),
        H2("4.3 Proposed System"),
        P("SafeGrid-AI is a neuro-symbolic multi-agent controller. Each of three agents, for a household prosumer, an electric-vehicle charger and a renewable "
          "prosumer, perceives a structured context (its own load, solar output, battery state, the price, its neighbours' exchange and the grid limits) and asks a "
          "provider for one EnergyAction: charge or discharge the battery, import or export power, curtail generation, shift load, or stay idle. "
          "A coordinator detects conflicting proposals and orders them with relief actions first. The Symbolic Safety Shield then validates each proposal "
          "against the cumulative grid state and approves it, projects it to the largest safe value by bisection, or rejects it; only validated set-points are "
          "committed to the power-flow model. Each decision is explained, stored, streamed to the dashboard and, if not a plain approval, appended to the "
          "hash-chained safety log."),
        P("The three agents differ in what they own. The prosumer agent (node 1, a household with 6 kWp of solar and a 10 kWh battery) trades off its own load, "
          "the tariff and its battery. The EV agent (node 2, a 40 kWh vehicle battery that can only be charged, at up to 7.4 kW) decides when to charge. The "
          "renewable agent (node 3, 20 kWp of solar and a 30 kWh battery) decides how much to store, export or curtail. The tariff is an illustrative five-band "
          "time-of-use schedule of 3.8, 5.2, 4.6, 9.0 and 5.0 rupees per kWh, with exported energy credited at 60 % of the import price. Seven scenarios (normal, "
          "high solar, peak demand, battery stress, line congestion, voltage violation and unsafe AI action) stress different limits; the last injects "
          "deliberately unsafe and malformed proposals so that the shield's behaviour can be seen."),
        P("When a provider fails, times out or returns something that does not match the action schema, the agent substitutes a deterministic cost-aware fallback "
          "decision, labelled as such and shielded like any other. When two proposals conflict, the coordinator records the conflict and validates the relief "
          "actions first, so that a curtailment is evaluated before a competing charge request on the same feeder."),
        FIG(F.diag("02_high_level_workflow.png"), "Workflow of one simulation step in the proposed system", 6.0),
        H2("4.4 Advantages of the Proposed System"),
        B("**Safety independent of the model:** executed actions caused no limit violation in any of 504 shielded steps, while the same agents without the shield did so in "
          + str(F.UNSHIELDED_CAUSED_STEPS) + " steps.",
          "**Intent preserved:** " + str(F.PROJECTED) + " of " + f"{F.PROPOSALS:,}" + " proposals were scaled down instead of being discarded, and only " + str(F.REJECTED) + " were rejected.",
          "**Explainable:** every decision shows its inputs, factors, action and safety verdict, without any chain-of-thought text.",
          "**Auditable:** a hash-chained log whose chain was valid in 21 of 21 runs.",
          "**Testable:** seeded scenarios, an experiment runner, a dry-run endpoint that validates a hand-made action without applying it, and an automated test suite."),
        H2("4.5 Functional Requirements"),
        TAB("Functional requirements", ["ID", "Requirement", "Where implemented"],
            [["FR-1", "Configure a run: scenario, seed, provider, steps, constraint overrides, initial state of charge, shield on or off", "RunConfig, POST /api/simulation/start|reset"],
             ["FR-2", "Start, stop, reset and single-step a run, and report its status", "SimulationService, /api/simulation/*"],
             ["FR-3", "Generate seeded solar, load and price profiles and inject scenario faults", "simulation/scenarios.py"],
             ["FR-4", "Give each agent a structured context of its node, neighbours, price and limits", "agents/base_agent.py (perceive)"],
             ["FR-5", "Obtain one schema-validated EnergyAction per agent per step, with a labelled deterministic fallback on any provider failure", "llm/*, agents/base_agent.py (decide)"],
             ["FR-6", "Detect peer mismatch, target contention and shared-feeder conflicts and order proposals relief-first", "simulation/coordinator.py"],
             ["FR-7", "Validate every action with the Symbolic Safety Shield: approve, project or reject, with the violated checks", "safety/shield.py"],
             ["FR-8", "Commit only validated set-points and solve the AC power flow", "grid/simulator.py"],
             ["FR-9", "Record non-approved actions in a SHA-256 hash-chained log and verify the chain", "safety/events.py, /api/safety/events"],
             ["FR-10", "Build a structured explanation for every decision (inputs, factors, action, safety result)", "agents/explain.py"],
             ["FR-11", "Validate a custom action as a dry run without changing the grid", "POST /api/agents/{id}/decision"],
             ["FR-12", "Stream events to connected dashboards over a WebSocket", "/ws/simulation, services/hub.py"],
             ["FR-13", "Persist runs, steps, events and safety events and serve them back", "database/store.py, /api/runs, /api/events"],
             ["FR-14", "Run a scenario to completion and return its summary", "POST /api/scenarios/{id}/run"],
             ["FR-15", "Compare a rule baseline, agents without the shield and SafeGrid-AI over several seeds", "simulation/experiment.py, /api/experiments"],
             ["FR-16", "Show grid, agents, shield, power flow, scenarios and explanations in a responsive dashboard", "frontend/src/pages/*"]],
            widths=[0.5, 3.7, 2.0], size=9.0, align=["c", "l", "l"]),
        P("The sixteen requirements fall into four groups: FR-1 to FR-3 set up and drive a run; FR-4 to FR-8 are the decision pipeline of one step; FR-9 to FR-13 "
          "are the accountability functions (log, explanation, dry run, stream, persistence); FR-14 to FR-16 are evaluation and presentation. Each pipeline "
          "requirement maps to one module, so the shield can be tested without a model, the coordinator without a power flow, and the explanation builder without either."),
        H2("4.6 Non-Functional Requirements"),
        TAB("Non-functional requirements and the evidence for each", ["Quality", "Requirement", "Evidence from this project"],
            [["Safety", "No executed action may create or worsen a limit violation (in the simulated model)", "0 violations caused in 504 shielded steps; " + str(F.UNSHIELDED_CAUSED) + " violations in " + str(F.UNSHIELDED_CAUSED_STEPS) + " steps without the shield"],
             ["Responsiveness", "Read requests should feel immediate; a control step should be much shorter than the simulated step", "Median " + str(health[0]) + " ms (health), " + str(state[0]) + " ms (grid state); step median " + str(step[0]) + " ms, p95 " + str(step[1]) + " ms"],
             ["Determinism", "The same seed gives the same run", "Seeded profiles, faults and mock decisions; results stored in one JSON file"],
             ["Auditability", "Interventions must be tamper-evident", "Chain valid in 21 of 21 shielded runs; " + str(F.SAFETY_EVENTS) + " safety events recorded"],
             ["Reliability", "A provider failure must not stop the run", "Failing and malformed outputs become a labelled fallback (fallback rate " + F.f3(F.mean('safegrid_shielded', 'fallback_rate')) + ")"],
             ["Testability", "Core logic is covered by automated tests", str(t['passed']) + " of " + str(t['total']) + " tests pass; 2 fail on numeric tolerances, 1 hangs (Chapter 7)"],
             ["Security", "Model output is data, never code", "The shield reads only EnergyAction fields; output is never run as code, SQL or shell; the API has no authentication (research prototype)"],
             ["Usability", "Works on phones and desktops, in light and dark themes", "Browser walk at 360, 768 and 1440 px: no console errors, no horizontal overflow"],
             ["Portability", "Runs on one ordinary computer without a GPU", "Measured on " + F.MACHINE]],
            widths=[1.0, 2.3, 2.9], size=9.0),
        P("Two of these requirements pull against each other, and the trade-off is reported. Safety costs time and some renewable energy: the shield's trial power "
          "flows raise the mean step time from about " + f"{F.mean('baseline_rule', 'avg_step_time_ms'):.0f}" + " ms to "
          + f"{F.mean('safegrid_shielded', 'avg_step_time_ms'):.0f}" + " ms, and renewable utilisation is " + F.f2(F.mean('safegrid_shielded', 'renewable_utilization'))
          + " instead of 1.00 for the rule baseline because the shield limits some solar output in the high-solar and voltage-violation scenarios. The agent-proposal "
          "dry run takes a median of " + str(dry[0]) + " ms. These figures are for a mock provider; a real language model would add its own latency, which was not measured."),
        H2("4.7 Hardware Requirements"),
        P("No minimum configuration was determined by experiment; the table gives the machine on which every result in this report was measured, and we state it "
          "as the minimum we can vouch for. Smaller machines were not tried."),
        TAB("Hardware requirements (measured machine)", ["Item", "Specification"],
            [["Processor", "Intel Core i5-12500, 6 cores, 12 threads"], ["Memory", "15.7 GB RAM"], ["Accelerator", "None; no GPU is used"],
             ["Storage", "Space for the repository, the Python environment and node modules (a few hundred megabytes); runs are stored in a local SQLite file"],
             ["Display", "Any screen; the dashboard is responsive from 360 pixels"], ["Network", "Local loopback only; internet is needed only to install packages or to call a real LLM"]],
            widths=[1.5, 4.7], size=10),
        H2("4.8 Software Requirements"),
        TAB("Software requirements (versions used)", ["Component", "Version used", "Role"],
            [["Windows", "11 Pro", "Operating system of the measurement machine"], ["Python", "3.11.9", "Back end and scripts"],
             ["pandapower", "3.5.6", "AC power-flow model of the feeder"], ["FastAPI", "0.143.3", "REST and WebSocket service"],
             ["pydantic", "2.14.1", "Schema validation of actions and configuration"], ["numpy / pandas / scipy", "2.4.6 / 2.3.3 / 1.17.1", "Numerics used by pandapower and the profiles"],
             ["uvicorn", "0.54.0", "ASGI server"], ["httpx", "0.28.1", "HTTP client (API provider, tests)"], ["pytest", "9.1.1", "Automated tests"],
             ["SQLite", "Python standard library", "Persistence"], ["Node.js", "24.19.0", "Front-end build and development server"],
             ["React / Vite", "18 / 5", "Dashboard"], ["three.js", "bundled with the front end", "Landing-page hero only"],
             ["Playwright with Chromium", "1.44.0", "Browser walk-through and screenshots"]],
            widths=[1.7, 1.9, 2.6], size=9.5),
        H2("4.9 User Roles and System Constraints"),
        P("There is one role, the operator, who may run and inspect everything. The demo sign-in is a browser-side gate meant for demonstrations; the API has no "
          "accounts or authentication, so the system must not be exposed to an untrusted network. Cross-origin access is limited by a configurable list of "
          "allowed origins, and the environment file that holds any real API key is never committed to the repository."),
        P("The principal constraints are the following. The agents control only the three nodes of the simulated feeder. The limits enforced are 0.95 to 1.05 per "
          "unit for voltage (tighter than the plus or minus 10 % band that the European supply standard " + n(19) + " allows at low voltage for most of the time), "
          "100 % loading of lines and of the transformer, and 200 kW import or export at the connection to the external grid. Actions are limited to seven types "
          "with power between 0 and 1,000,000 kW as a sanity limit and a duration of 1 to 1,440 minutes, and reason codes must be upper-case identifiers of at "
          "most 48 characters. A proposal that breaks any of these structural rules is rejected before any power flow is run."),
    ]


def blocks():
    return feasibility_blocks() + requirements_blocks()
