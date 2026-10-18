"""
Content shared by the chapters, the decks and the paper, so that every document states the same thing.
Reference numbers are indexes into refs.REFS (1-based).
"""

from . import facts as F

# ---------------------------------------------------------------- objectives (batch document 6) with what was delivered
OBJECTIVES = [
    "Model the grid as a multi-agent system with agents responsible for generation, storage and load.",
    "Implement an LLM-driven planning agent that proposes routing actions from observed grid state.",
    "Add a safety shielding layer that validates each action against physical and operational constraints.",
    "Provide explanations for every routing decision so operators can audit the reasoning.",
    "Simulate fault and overload scenarios to test dynamic rerouting behaviour.",
    "Evaluate violation resolution rate, decision latency and the number of unsafe actions blocked.",
]

# (objective, status, evidence) - the honest outcome of each objective
OUTCOMES = [
    ("1. Multi-agent grid model", "Achieved",
     "Three agents (prosumer, EV storage, renewable prosumer) on a 3-node pandapower feeder; a coordinator detects peer mismatch, target contention and shared-feeder conflicts."),
    ("2. LLM planning agent", "Achieved with a mock model",
     "Agents build a structured context and obtain a schema-validated EnergyAction from a provider. A real-LLM provider (Anthropic / OpenAI wire format) is implemented but was not run against a live model; all measured results use the deterministic mock provider."),
    ("3. Safety shielding", "Achieved",
     "Symbolic Safety Shield with ten ordered checks and bisection projection: 0 violations caused by executed actions in all 504 shielded steps (1,512 proposals)."),
    ("4. Explanations", "Achieved",
     "Every decision carries inputs, decision factors, the action, the safety result and a reason code list; no chain-of-thought is requested or stored (tested)."),
    ("5. Fault and overload scenarios", "Achieved",
     "Seven seeded scenarios, including injected unsafe and malformed proposals; the shield rejected or scaled down 350 of 1,512 proposals."),
    ("6. Evaluation metrics", "Partly achieved",
     "Unsafe actions blocked (113 rejected, 237 projected) and decision latency were measured. A violation-resolution rate for pre-existing violations was not measured: the project measures violations prevented, not violations repaired."),
]

PROBLEM_POINTS = [
    "Fixed-rule grid control cannot adapt to renewable variability or changing topology.",
    "Centralised control creates a single point of failure for the whole network.",
    "Autonomous agents acting on physical infrastructure can take unsafe actions if unconstrained.",
    "Operators will not accept control decisions they cannot interrogate.",
]

PROBLEM_STATEMENT = (
    "Given the observed state of a low-voltage feeder with distributed solar, batteries and an electric vehicle, let several autonomous agents propose "
    "power set-points at every control step, and execute only set-points that cannot create or worsen a violation of voltage, line, transformer, battery "
    "or import/export limits, while recording a reviewable explanation and an audit trail for every decision."
)

# ---------------------------------------------------------------- literature table: (work, approach, setting, reported result / stated limit)
LIT_TABLE = [
    ("Eyimaya and Altin, 2026 [1] (base paper)",
     "Four rule-based agents (DER, energy storage, load, grid) coordinate a DC microgrid",
     "MATLAB/Simulink, 800 V DC bus, PV, wind, generator, battery, critical and non-critical loads; 20 microsecond sampling",
     "Bus voltage held at 800 V and critical loads supplied in all eight operating scenarios; authors name scalability, software integration, cybersecurity and missing experimental validation as open issues"),
    ("Zhang et al., 2025 [2]",
     "LLM planning agent proposes actions with power-flow solvers; validation agent executes in a sandbox with rollback",
     "IEEE 69-bus, CIGRE MV and IEEE 30-bus networks; violations resolved by switching, batteries and load curtailment",
     "Best LLM configurations report a 100 % success rate; weaker configurations 63 % and 44 %. Safety relies on sandboxed trial and rollback, not on a formal rule layer; no operator-facing explanation interface"),
    ("Picault and Goubet, 2026 [3]",
     "Position paper: Model Context Protocol server exposes a grid simulator (pypowsybl) to AI agents under human oversight",
     "Transmission-system-operator studies; first implementation step (pypowsybl-mcp) and an evaluation strategy",
     "No quantitative results; sets requirements (traceability, stateful execution, role-aware access, human validation) that motivate an auditable action path"),
    ("Multi-agent deep RL for smart grid management, 2025 [4]",
     "Multi-agent deep reinforcement learning (classified from the title and venue)",
     "Smart-grid energy management",
     "Full text was not reviewed for this report; listed in the batch literature survey"),
    ("Fault reconstruction control with multi-agent deep RL, 2024 [5]",
     "Multi-agent deep reinforcement learning for energy-system fault handling (title and venue)",
     "Energy system fault reconstruction",
     "Full text was not reviewed for this report; listed in the batch literature survey"),
    ("Distributed EV scheduling, 2025 [6]",
     "Distributed optimal scheduling that treats vehicles, charging stations and the grid as separate agents (title and venue)",
     "Electric-vehicle charging",
     "Full text was not reviewed for this report; listed in the batch literature survey"),
    ("Multi-agent systems in power systems: a review, 2025 [7]",
     "Review of multi-agent energy management in the power grid (title and venue)",
     "Power-grid energy management",
     "Full text was not reviewed for this report; listed in the batch literature survey"),
    ("McArthur et al., 2007 [8]",
     "Concepts, approaches and technical challenges of multi-agent systems for power engineering",
     "Survey, Part I of two",
     "Establishes agents as a natural fit for distributed power systems; open challenges include verification and trust"),
]

# qualitative comparison with the base paper (no numeric comparison exists: different system, no shared benchmark)
BASE_COMPARE = [
    ("System modelled", "DC microgrid, 800 V bus, MATLAB/Simulink", "Three-node AC low-voltage feeder, pandapower AC power flow"),
    ("Decision makers", "Four rule-based agents", "Three agents driven by a pluggable LLM provider (mock in all measurements), with a deterministic fallback"),
    ("Safety mechanism", "Control logic keeps the bus voltage regulated; no separate validation layer", "Independent Symbolic Safety Shield: approve, project or reject every action before it is executed"),
    ("Explanation", "None reported", "Structured explanation per decision, hash-chained audit log, dashboard views"),
    ("Evidence", "Eight Simulink scenarios, bus voltage regulated at 800 V", "Seven scenarios x 3 strategies x 3 seeds (63 runs): 0 violations caused by executed actions in 504 shielded steps"),
    ("Validation reached", "Simulation only; authors note the lack of experimental validation", "Simulation only; synthetic profiles; mock LLM; no field data"),
]

# the headline sentences, reused word for word wherever a short statement is needed
HEADLINE = (
    f"Across 21 shielded runs ({F.PROPOSALS:,} agent proposals) the shield approved {F.APPROVED:,} ({F.APPROVED / F.PROPOSALS * 100:.1f} %), "
    f"projected {F.PROJECTED} ({F.PROJECTED / F.PROPOSALS * 100:.1f} %) and rejected {F.REJECTED} ({F.REJECTED / F.PROPOSALS * 100:.1f} %), and no executed action "
    f"created or worsened a limit violation (0 of 504 steps), whereas the same agents without the shield did so in {F.UNSHIELDED_CAUSED_STEPS} steps "
    f"({F.UNSHIELDED_CAUSED} violations)."
)

GAPS = [
    "Every agent result comes from the deterministic mock provider; no live language model was evaluated, so language-model reasoning quality and real inference latency are unmeasured.",
    "The batch objective 'violation resolution rate' was not measured; the project measures violations prevented (caused by actions = 0) and steps with any violation, not repair of a grid that is already outside its limits.",
    "Mean decision latency is 0.1-0.2 ms for the mock provider and says nothing about a real model.",
    "Three seeds, a three-node synthetic feeder, an illustrative tariff, no protection, no dynamics and no three-phase unbalance.",
    "The guarantee is model-relative (no new or worse violations in the simulated model), not a formal proof; the abstract's 'mathematically guaranteeing zero physical constraint violations' is stronger than what was built and tested.",
    "The comparison with the base paper is qualitative: different system, no shared benchmark, no like-for-like numbers.",
    "Two unit tests fail on numeric tolerances with pandapower 3.5.6 and one WebSocket test hangs under the installed Starlette test client.",
    "No user study was carried out, so usability and operator trust are not measured.",
]

KEYWORDS = "agentic AI, large language models, multi-agent systems, smart grid, neuro-symbolic safety, safety shielding, explainability, power flow"
