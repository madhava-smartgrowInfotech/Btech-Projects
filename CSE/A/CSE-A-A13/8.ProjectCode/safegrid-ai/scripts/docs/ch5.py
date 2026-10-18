"""Chapter 5: System design. The diagram explanations are shared with '11. BLOCK DIAGRAMS ALL.docx'."""

import os

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import n

# (key, section title, file, caption, explanation)
DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png", "System architecture of SafeGrid-AI",
     "The system has four tiers. The presentation tier is the React 18 console served by Vite on port 5313: a landing page with a three.js hero, a demo sign-in, and seven "
     "console screens. The application tier is a FastAPI service on port 8313: REST routers, a WebSocket route (`/ws/simulation`) that streams events through the "
     "`ConnectionHub`, and `SimulationService`, which owns the current run, runs scenarios, answers dry-run requests and manages experiment jobs. The simulation and safety "
     "core holds one `SimulationEngine` per run. The engine drives an `AgentManager` with three agents, whose proposals come from an LLM provider (mock, api, baseline or "
     "failing); the coordinator orders the proposals; the Symbolic Safety Shield validates each one; and the `GridSimulator` runs the pandapower AC power flow for trial and "
     "committed states. The data tier is a SQLite file with five tables, the hash-chained safety log, and the seeded profiles and scenario faults. The footnote in the figure "
     "states the trust boundary: the LLM provider is an untrusted proposer; the coordinator, shield and simulator are trusted deterministic code."),
    ("flow", "High-level workflow", "02_high_level_workflow.png", "High-level workflow of one simulation step (15 simulated minutes)",
     "One control step has eight stages. (1) Seeded profiles give solar output, household load, price and any scenario fault. (2) A no-action power flow records the grid "
     "state if every agent stayed idle; it is the baseline against which later violations are attributed. (3) Each agent perceives a structured context built from its node, "
     "its neighbours and the grid limits. (4) Each agent returns one `EnergyAction`; a provider failure or invalid answer becomes a labelled deterministic fallback. (5) The "
     "coordinator detects conflicts and puts relief actions first. (6) The Safety Shield validates the proposals one after another against the cumulative grid state and "
     "approves, projects or rejects each. (7) Only the validated set-points are committed: the power flow is run again and battery states of charge are updated. (8) "
     "Non-approved decisions are appended to the hash-chained safety log, the step is stored, and events are streamed to the dashboard."),
    ("dfd0", "Data flow diagram, level 0", "03_dfd_level0.png", "Data flow diagram, level 0 (context diagram)",
     "The context diagram shows SafeGrid-AI as a single process with two external entities. The operator sends the scenario, seed, provider choice, start, stop and step "
     "commands and dry-run actions, and receives live grid state, decisions, explanations, shield events and metrics. The optional LLM provider receives the structured "
     "context of each agent and returns a proposed `EnergyAction`. Internally the system writes the run store (runs, steps, events; D1) and the hash-chained safety log (D2), "
     "and reads the scenario and constraint configuration (D3)."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png", "Data flow diagram, level 1",
     "Level 1 splits the system into six processes. Configure and control run (1.0) accepts the operator's commands. Generate scenario inputs (2.0) combines the run "
     "configuration with the faults and limits in D3 and produces the seeded profiles. Agents perceive and propose (3.0) exchanges context and proposed actions with the LLM "
     "provider. Coordinate and validate (4.0) is the shield: it reads the limits, appends safety events to D2 and passes validated actions on. Execute (5.0) runs the power "
     "flow and updates battery states. Log, explain and publish (6.0) writes the run store (D1) and returns live state and explanations to the operator."),
    ("dfd2", "Data flow diagram, level 2", "05_dfd_level2.png", "Data flow diagram, level 2: process 4.0 expanded",
     "Level 2 expands the shield process into the steps that `SymbolicSafetyShield.evaluate` performs. Proposals are first ordered with relief actions first (4.1) and "
     "checked structurally (4.2). A trial power flow of the request as proposed (4.3) is compared with the no-action baseline so that only new or worse violations are "
     "kept (4.4); the limits come from D3. If there is none (4.5) the action is approved as requested. Otherwise a bisection finds the largest safe scale of the action "
     "(4.6), the rounded action is verified again (4.7), the decision is formed as approve, project or reject (4.8), and a hash-chained event is appended to D2 (4.9)."),
    ("uml", "UML class diagram", "06_uml_class_diagram.png", "UML class diagram of the backend (backend/app)",
     "`SimulationService` creates and controls the `SimulationEngine` and uses the `SQLiteStore`. The engine owns the `AgentManager`, the `GridSimulator` and the "
     "`SymbolicSafetyShield`. The manager holds the agents derived from `BaseAgent` (the prosumer, storage and renewable subclasses differ only in the extra context they "
     "add); each agent has an abstract `LLMProvider`, implemented by the mock, api, rule-based, failing and fault-injecting providers, which returns an `EnergyAction`. "
     "The shield reads a `ConstraintConfig`, calls `GridSimulator.trial` and returns a `ShieldDecision`; non-approved decisions are logged as `SafetyEvent` records "
     "whose `prev_hash` and `hash` fields form the chain."),
    ("seq", "Sequence diagram", "07_sequence_diagram.png", "Sequence diagram: one simulation step",
     "The dashboard posts to `/api/simulation/step` (a live run repeats the sequence in a background task). FastAPI calls `step()` on the engine, which applies the "
     "exogenous inputs, runs the no-action power flow, and calls `perceive_all` and `decide_all` on the agents; they return three actions. The engine detects conflicts, "
     "orders the proposals and calls `evaluate` on the shield for each in turn (the dashed frame); the shield calls `trial` on the grid simulator several times and returns "
     "a `ShieldDecision`. The engine commits the validated set-points, stores the safety events and the step, publishes `agent_action`, `safety_intervention` and "
     "`grid_update` events to the WebSocket clients, and returns the step record."),
    ("uc", "Use-case diagram", "08_use_case_diagram.png", "Use-case diagram",
     "The operator can sign in with the demo account, choose a scenario, seed and agent brain, start, step, stop or reset a run, watch the grid, agents and shield live, "
     "inspect an agent decision and its explanation, dry-run a custom action against the shield, run a scenario to completion and compare strategies over several seeds. "
     "The optional LLM provider takes part in the run use cases by answering each agent's context; the experiment scheduler (a background job inside the service) takes part "
     "in the strategy comparison."),
    ("er", "Entity-relationship diagram", "09_er_diagram.png", "Entity-relationship diagram of the SQLite store",
     "`runs` holds one row per simulation run, with its configuration, resolved settings, summary and the final hash of the safety chain. `events` (stream events), "
     "`safety_events` (non-approved decisions with their hash chain) and `steps` (one row per step) each reference a run by `run_id`, one run to many rows. `experiments` "
     "is independent: it stores the specification and aggregate results of a strategy comparison. Two indexes speed up the lookups of events and safety events by run."),
    ("flowchart", "Core algorithm flowchart", "10_core_algorithm_flowchart.png", "Core algorithm: Symbolic Safety Shield evaluate()",
     "The flowchart follows the code in `safety/shield.py`. A structural violation (unknown agent or node, an agent acting on a node it does not own, a non-finite, negative "
     "or implausible power) rejects the action at once; an idle or zero-power action is approved. Otherwise the action becomes a physical set-point, the local checks "
     "(battery, state of charge, node limits, balance) and one trial power flow are run, and only violations that are new or worse than the no-action state count. With "
     "none, the action is approved. With some, a bisection (40 iterations for local limits, 14 for power-flow limits) finds the largest safe scale; the rounded action is "
     "re-verified up to four times; and the action is rejected if nothing safe remains, if the safe part is below 0.05 kW, or if an import or export target would change "
     "direction. Otherwise the scaled action is executed as a projection. Every outcome other than approval is appended to the safety log."),
    ("feeder", "Simulated feeder topology", "11_feeder_topology.png", "Simulated low-voltage feeder (pandapower network)",
     "The simulated grid is a 20 kV external grid feeding a 0.25 MVA 20/0.4 kV transformer (T0) at bus B0. Line L0_1 (0.30 km) connects B0 to B1, where node_1, the "
     "residential prosumer (6 kWp PV, 10 kWh battery), is attached; line L1_3 (0.45 km) continues to B3, node_3, the renewable prosumer (20 kWp PV, 30 kWh battery); line L0_2 "
     "(0.25 km) connects B0 to B2, node_2, the EV (40 kWh battery, 7.4 kW, charge only). All lines are NAYY 4x50 SE cable and the load power factor is 0.95."),
    ("chain", "Hash-chained safety log", "12_hash_chain.png", "Hash-chained safety log",
     "Each safety event stores the hash of the previous event (a string of zeros for the first) and its own SHA-256 hash over the previous hash, the identifiers "
     "[event id, run, step, simulated time] and the canonical payload. `verify_chain` recomputes every hash, so changing, removing or reordering any event breaks all later links. "
     "The wall-clock time is stored but excluded from the hash so that reruns are comparable."),
]

SCHEMA = {
    "runs": [("run_id", "TEXT", "PRIMARY KEY", "Identifier of the run"),
             ("created_at", "TEXT", "", "UTC creation time"),
             ("finished_at", "TEXT", "", "UTC finish time (null while running)"),
             ("status", "TEXT", "", "idle, running, paused, stopped, completed or failed"),
             ("config", "TEXT (JSON)", "", "RunConfig as submitted"),
             ("resolved", "TEXT (JSON)", "", "Scenario, steps, time step, seed, provider, constraints used"),
             ("summary", "TEXT (JSON)", "", "Final metrics of the run"),
             ("fingerprint", "TEXT", "", "Hash of the last safety event (chain head)")],
    "events": [("id", "INTEGER", "PRIMARY KEY AUTOINCREMENT", "Row number"),
               ("run_id", "TEXT", "indexed with event_type", "Run the event belongs to"),
               ("step", "INTEGER", "", "Simulation step"),
               ("event_type", "TEXT", "", "agent_action, safety_intervention, grid_update, ..."),
               ("payload", "TEXT (JSON)", "", "The event as streamed")],
    "safety_events": [("id", "INTEGER", "PRIMARY KEY AUTOINCREMENT", "Row number"),
                      ("run_id", "TEXT", "indexed with status", "Run the event belongs to"),
                      ("step", "INTEGER", "", "Simulation step"),
                      ("status", "TEXT", "", "projected, rejected (or approved for an anomaly record)"),
                      ("payload", "TEXT (JSON)", "", "Requested and validated action, violations, corrections, checks, grid before/after, prev_hash, hash")],
    "steps": [("run_id", "TEXT", "PRIMARY KEY (with step)", "Run"),
              ("step", "INTEGER", "PRIMARY KEY (with run_id)", "Simulation step"),
              ("payload", "TEXT (JSON)", "", "Full step record: grid snapshot, agent rows, conflicts, counts")],
    "experiments": [("exp_id", "TEXT", "PRIMARY KEY", "Identifier of a strategy comparison"),
                    ("created_at", "TEXT", "", "UTC creation time"),
                    ("spec", "TEXT (JSON)", "", "Scenarios, seeds, steps, arms, time step"),
                    ("results", "TEXT (JSON)", "", "Per-run summaries and aggregates")],
}

BACKEND = os.path.join(F.CODE, "backend", "app")
FRONT = os.path.join(F.CODE, "frontend", "src")

MODULES = [
    ("api/, services/", "REST routers, run lifecycle, experiment jobs, WebSocket hub", ["api", "services"]),
    ("simulation/engine.py", "One run: step loop, validation, metrics, events", ["simulation/engine.py"]),
    ("simulation/ (other)", "Coordinator, scenarios, seeded profiles, strategy comparison, runners", ["simulation/coordinator.py", "simulation/scenarios.py", "simulation/timestep.py", "simulation/experiment.py", "simulation/run_experiment.py", "simulation/run_scenario.py"]),
    ("agents/, llm/", "Agents, manager, policies, explanations; provider contract and providers", ["agents", "llm"]),
    ("safety/", "Constraints, validator, projector, shield, hash-chained events", ["safety"]),
    ("grid/", "pandapower network, power-flow wrappers, GridSimulator", ["grid"]),
    ("database/, models/, config.py, main.py", "SQLite store, EnergyAction and run schemas, settings, entry point", ["database", "models", "config.py", "main.py"]),
]


def _lines(rel_list, base):
    total = 0
    for rel in rel_list:
        p = os.path.join(base, rel)
        files = []
        if os.path.isdir(p):
            for root, _d, fs in os.walk(p):
                files += [os.path.join(root, f) for f in fs if f.endswith((".py", ".jsx", ".js", ".css"))]
        elif os.path.exists(p):
            files = [p]
        for f in files:
            with open(f, encoding="utf-8", errors="ignore") as fh:
                total += sum(1 for _ in fh)
    return total


def module_rows():
    rows = [[m, role, f"{_lines(rel, BACKEND):,}"] for m, role, rel in MODULES]
    rows.append(["**Backend total**", "", f"**{sum(int(r[2].replace(',', '')) for r in rows):,}**"])
    return rows


PAGES = [
    ("Landing", "pages/Landing.jsx", "Introduction and three.js hero; links to the console"),
    ("Login", "pages/Login.jsx", "Demo sign-in (browser-side gate)"),
    ("Dashboard", "pages/Dashboard.jsx", "KPI tiles, charts, latest intervention, event timeline"),
    ("Grid view", "pages/GridView.jsx", "Single-line diagram, voltage and loading colouring, line table"),
    ("Agent monitor", "pages/AgentMonitor.jsx", "Agent cards and the selected agent's decision history"),
    ("Safety shield", "pages/SafetyShield.jsx", "Counters, event table, dry run, active constraints"),
    ("Power flow", "pages/PowerFlow.jsx", "Eight charts of the AC power-flow results"),
    ("Scenarios", "pages/ScenarioRunner.jsx", "Scenario cards, run to completion, strategy comparison"),
    ("Explainability", "pages/Explainability.jsx", "Decision lane, factors, context and raw JSON"),
]


def page_rows():
    out = []
    for name, rel, role in PAGES:
        out.append([name, f"`{rel}`", role, f"{_lines([rel], FRONT):,}"])
    return out


def diagram_blocks(heading_level=2):
    out = []
    for key, title, file, caption, text in DIAGRAMS:
        out.append(("h3" if heading_level == 3 else "h2", f"{title}"))
        out.append(FIG(F.diag(file), caption, 6.0))
        out.append(P(text))
    return out


def schema_blocks():
    out = []
    for name, cols in SCHEMA.items():
        out.append(TAB(f"Table `{name}`", ["Column", "Type", "Constraint", "Meaning"], [list(c) for c in cols], widths=[1.2, 1.0, 1.6, 2.5], size=9.5))
    out.append(P("The tables are created by `CREATE TABLE IF NOT EXISTS`, so a fresh checkout needs no migration, and every statement uses bound parameters. "
                 "Structured values are stored as JSON text, which keeps the schema stable while the event payloads evolve. The store is a "
                 "single connection with a lock, adequate for one operator and listed as a limit in Chapter 9."))
    return out


def blocks():
    D = {k: (t, f, c, x) for k, t, f, c, x in DIAGRAMS}

    def fig(key, w=6.0):
        return FIG(F.diag(D[key][1]), D[key][2], w)

    return [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        H2("5.1 Overall System Architecture"),
        P("The design follows three rules. The model that proposes and the code that decides must be separate. Everything that decides must be deterministic and testable "
          f"without a language model. And every decision must leave a record that can be checked afterwards. They follow the "
          f"shielding idea of safe reinforcement learning {n(12)}, in which a verified layer sits between a learner and its environment, and the multi-agent view of power "
          f"systems {n(8)}. The layers are shown below."),
        fig("arch"),
        P(D["arch"][3]),
        P("Two properties of this layout matter. First, the shield package imports nothing from the language-model, agent, simulation or grid packages; a test "
          "(`test_shield_does_not_import_llm_or_agents`) checks this, so model text cannot influence the shield even by accident. Second, the API has no user accounts: it is a "
          "single-user research prototype, and the demo sign-in is only a browser gate."),
        H2("5.2 High-Level Workflow"),
        fig("flow"),
        P(D["flow"][3]),
        P("The same stages run for Start (repeated on a timer, streaming events), Step (one pass) and a scenario run to completion. A dry run, "
          "`POST /api/agents/{id}/decision`, validates the agent's current proposal (or an action written by the operator) against the current state with trial power flows; "
          "nothing is committed and the run does not advance."),
        H2("5.3 Data Flow Diagrams"),
        H3("Level 0: context"),
        fig("dfd0", 5.8),
        P(D["dfd0"][3]),
        H3("Level 1"),
        fig("dfd1", 5.8),
        P(D["dfd1"][3]),
        H3("Level 2: the shield process"),
        fig("dfd2", 5.8),
        P(D["dfd2"][3]),
        H2("5.4 UML Diagrams"),
        H3("Class diagram"),
        fig("uml", 6.0),
        P(D["uml"][3]),
        H3("Sequence diagram"),
        fig("seq", 6.0),
        P(D["seq"][3]),
        H3("Use-case diagram"),
        fig("uc", 5.2),
        P(D["uc"][3]),
        H2("5.5 Entity-Relationship Diagram"),
        fig("er", 5.8),
        P(D["er"][3]),
        H2("5.6 Database Schema and Table Descriptions"),
        P("The store keeps five tables: run configuration and results, the event stream, the safety log, per-step records and strategy comparisons, which is everything "
          "the dashboard shows after a reload. Nothing else is persisted: the grid state is rebuilt from the seed and the scenario."),
    ] + schema_blocks() + [
        H2("5.7 Module Architecture"),
        P("The backend is organised by responsibility. The table below lists the modules with their measured sizes (lines of Python, counted from the source files when "
          f"this report is built). The backend has {F.LOC['backend']:,} lines in `app/` and {F.LOC['tests']} lines of tests; the frontend has "
          f"{F.LOC['frontend']:,} lines of JavaScript, JSX and CSS."),
        TAB("Backend modules and their size", ["Module", "Role", "Lines"], module_rows(), widths=[2.2, 3.4, 0.7], size=9.5, align=["l", "l", "r"]),
        P("The frontend is a single-page application with one lazy-loaded chunk per page (landing, login, dashboard, grid view, agent monitor, safety shield, power flow, "
          "scenarios, explainability), so three.js is fetched only for the landing page. State is kept in a `SimulationProvider` that wraps the REST and WebSocket clients; "
          "the pages are views of that state."),
        H2("5.8 Shield Decision Workflow"),
        P("The next three figures show the core algorithm, the grid it protects and the audit mechanism, the parts of the design that Chapter 8 tests directly."),
        fig("flowchart", 4.7),
        P(D["flowchart"][3]),
        fig("feeder", 6.0),
        P(D["feeder"][3]),
        fig("chain", 6.0),
        P(D["chain"][3]),
        P("**Design limits.** The feeder is small by choice: one step still costs several trial power flows, and the experiment of "
          f"Chapter 8 needed about ten minutes for {F.N_RUNS} runs. The shield checks actions against the model it is given; if the simulated network "
          f"differs from a real one, the guarantee does not carry over. Grid-Agent {n(2)} also validates plans by sandboxed execution, which likewise "
          f"depends on the model that is executed. This limitation is stated again in Chapters 8 and 9."),
    ]
