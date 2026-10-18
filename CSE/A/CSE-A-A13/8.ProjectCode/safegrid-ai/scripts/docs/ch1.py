"""Chapter 1: Introduction."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .content_shared import GAPS, OBJECTIVES, PROBLEM_POINTS, PROBLEM_STATEMENT
from .refs import n

OBJECTIVES = OBJECTIVES  # re-exported for the decks

APP = F.pct(F.APPROVED / F.PROPOSALS)
PRJ = F.pct(F.PROJECTED / F.PROPOSALS)
REJ = F.pct(F.REJECTED / F.PROPOSALS)
INTERV = F.PROJECTED + F.REJECTED


def blocks():
    return [
        H1("CHAPTER 1: INTRODUCTION"),
        H2("1.1 Introduction to the Project Domain"),
        P("An electricity distribution network has to match generation and demand at every instant while keeping voltages, cable currents and transformer loading "
          "inside the limits that the equipment and the supply standards allow. For most of the twentieth century a few large generators fed passive consumers "
          "and fixed operating rules were enough. Rooftop solar, community batteries and electric vehicles now turn many consumers into prosumers who both draw "
          "and inject power, the injections depend on weather, and the direction of flow on a street-level feeder can reverse within minutes " + n(10) + ". A small "
          "cluster of generation, storage and load operated as one controllable unit is usually called a microgrid " + n(9) + "."),
        P("Two ideas from computer science meet this problem. The first is the multi-agent system: instead of one central controller, autonomous software agents "
          "each perceive part of the system, decide for their own device or node, and coordinate with the others " + n(18) + "; it is a natural fit for distributed "
          "energy resources and has long been studied in power engineering " + n(8) + ". The second is the large language model (LLM) used as an agent: given the "
          "state of a system as structured text, it can propose an action, choose a tool and justify the choice " + n(16) + ", which fixed rules and classical "
          "optimisers do not do naturally."),
        P("This project, SafeGrid-AI, combines the two and adds a third element: every action proposed by an agent passes through a deterministic Symbolic "
          "Safety Shield before it can touch the grid. The shield is ordinary code, independent of any language model, that checks the proposal against the "
          "physical and operational limits, executes it as requested if it is safe, scales it down to the largest safe value if it is not, and rejects it if no "
          "safe value exists. Because the agent is only a proposer, the same architecture works with a scripted agent, a mock model or a real LLM, and the safety "
          "argument does not depend on how well the model behaves. The environment is a simulated three-node low-voltage feeder solved with the pandapower AC "
          "power-flow library " + n(11) + "."),
        H2("1.2 Background and Motivation"),
        P("Recent work shows how far LLM-driven agents can go in power systems. Grid-Agent couples a planning agent that uses power-flow solvers with a "
          "validation agent that executes actions in a sandbox with rollback, and reports success rates of up to 100 % for the best model configurations on IEEE "
          "69-bus, CIGRE medium-voltage and IEEE 30-bus networks, although weaker configurations reach only 63 % and 44 % " + n(2) + ". "
          "A position paper from a transmission operator proposes exposing a grid simulator to AI agents through the Model Context Protocol, with traceability "
          "and human oversight " + n(3) + ". The base paper of this batch designs a multi-agent energy management system for a DC microgrid with four rule-based "
          "agents and shows in simulation that the bus voltage stays at 800 V in eight operating scenarios " + n(1) + "."),
        P("Together these papers leave a gap. The rule-based system is safe by construction of its rules but cannot adapt or explain a decision in operator "
          "language. The LLM-based systems adapt, but their safety rests on trial execution and rollback rather than on a rule layer independent of the model, and "
          "a probabilistic model that emits a tool call to physical equipment can, in principle, emit a wrong or unauthorised one. Avoiding unintended side "
          "effects and unsafe exploration are listed among the concrete open problems of AI safety " + n(15) + ". In reinforcement learning, shielding corrects "
          "actions that would violate a specification " + n(12) + ", and a safety layer can project an action onto the set of safe actions " + n(13) + "; surveys "
          "describe both families " + n(14) + ". We transfer the same idea to an agentic grid controller, with the shield operating on a physical network model."),
        P("Explainability is the second motivation. An operator who cannot ask why a battery was discharged will not trust the controller. Narrations produced "
          "by a language model can misrepresent the real reasons for an answer " + n(17) + ", so SafeGrid-AI builds its explanations from structured facts the "
          "system itself knows: the inputs the agent saw, the factors that drove the choice, the action, and the shield's verdict with the violated limits. No "
          "chain-of-thought text is requested or stored."),
        H2("1.3 Problem Statement"),
        P(PROBLEM_STATEMENT),
        P("The batch problem statement lists four weaknesses of current practice that this formulation addresses; the need is an explainable multi-agent "
          "controller that routes power dynamically while a safety layer blocks any unsafe action:"),
        B(*PROBLEM_POINTS),
        H2("1.4 Need for the Proposed System"),
        B("**Adaptivity.** Fixed rules do not follow cloud cover, price changes or an unusual load pattern; agents that read the current context can.",
          "**Containment of unsafe actions.** An agent can propose an action that overloads a line or pushes a voltage out of band; the shield makes that "
          "impossible to execute rather than unlikely.",
          "**Distributed decisions.** Each agent decides for its own node, so the loss of one agent degrades only that node; a failed or malformed proposal "
          "is replaced by a labelled deterministic fallback and is still shielded.",
          "**Auditability.** Every intervention is written to a hash-chained log, so what was proposed and what was executed can be checked for tampering " + n(20) + ".",
          "**Evidence before deployment.** An AI controller has to be measured on seeded, repeatable scenarios, including deliberately unsafe proposals, "
          "before anyone considers connecting it to equipment."),
        FIG(F.diag("11_feeder_topology.png"), "The simulated three-node low-voltage feeder used throughout the project", 6.0),
        H2("1.5 Project Objectives"),
        P("The objectives are those recorded in the batch objectives document:"),
        N(*OBJECTIVES),
        P("Section 8.10 compares each objective with what was delivered: objectives 1 to 5 were achieved (objective 2 with a mock model in place of a live LLM), "
          "and objective 6 in part, since unsafe actions blocked and decision latency were measured but a violation-resolution rate was not."),
        H2("1.6 Scope of the Project"),
        H3("In scope"),
        B("A software-only simulation of a three-node 0.4 kV feeder with a household prosumer, an electric-vehicle charger and a renewable prosumer, solved with "
          "AC power flow in 15-minute steps.",
          "Three agents with a pluggable provider interface (mock, API-based LLM, rule-based, failing) and a deterministic fallback policy.",
          "A coordinator for conflicting proposals, and the Symbolic Safety Shield with ten ordered checks and bisection projection.",
          "Seven seeded scenarios, including injected unsafe and malformed proposals, and a three-strategy comparison.",
          "A FastAPI service (REST and WebSocket), SQLite persistence, a hash-chained safety log and a React dashboard."),
        H3("Out of scope"),
        B("Connection to real equipment, real measurements or a real network operator; protection, dynamics and three-phase unbalance.",
          "Training or fine-tuning of any model; no dataset is used, since the inputs are generated from a seed.",
          "Evaluation with a live language model, and a user study with operators.",
          "A formal proof of safety; the guarantee we claim is relative to the simulated model."),
        H2("1.7 Project Contributions"),
        B("**A model-independent safety path for agentic power control.** The shield reads only the structured action and the grid model, never prompts or model "
          "text, and a test enforces that it imports nothing from the language-model, agent, simulation or grid packages.",
          "**Approve, project or reject.** The shield scales unsafe actions to the largest safe value by bisection on trial power flows, so the agent's intent "
          "is kept as far as safety allows.",
          "**Attribution of violations.** Only violations that are new or worse than the grid state with every agent idle are blamed on an action.",
          "**Conflict-aware coordination.** Peer mismatch, target contention and shared-feeder conflicts are detected, and relief actions are validated first.",
          "**Structured, auditable explanations.** Each decision carries its inputs, factors, action and safety result, and every non-approved action is chained "
          "into a tamper-evident log.",
          "**A measured evaluation.** Across " + str(F.N_RUNS) + " runs the shield approved " + str(F.APPROVED) + " of " + f"{F.PROPOSALS:,}" + " proposals (" + APP + "), projected "
          + str(F.PROJECTED) + " (" + PRJ + ") and rejected " + str(F.REJECTED) + " (" + REJ + "); executed actions caused no limit violation in any of the 504 shielded steps, against "
          + str(F.UNSHIELDED_CAUSED_STEPS) + " steps without the shield."),
        H2("1.8 Limitations and Assumptions"),
        P("The results of this report have to be read with the following limitations in mind; Chapter 8 and the Scope and Limitations document discuss them in detail."),
        B(*GAPS),
        P("We assume that the three-node feeder, the seeded profiles and the illustrative time-of-use tariff are representative enough to exercise the "
          "controller, that the pandapower AC power flow is an acceptable network model for 15-minute steps, and that the limits (0.95 to 1.05 per unit, 100 % "
          "loading of lines and transformer, 200 kW import and export) are the limits the operator wants enforced. Costs are in rupees at an illustrative "
          "tariff and are used only to compare strategies."),
        H2("1.9 Organization of the Report"),
        B("**Chapter 2** surveys the base paper and related work and states the research gap; **Chapter 3** assesses feasibility; **Chapter 4** describes the "
          "existing and proposed systems and lists the requirements.",
          "**Chapter 5** presents the design (architecture, workflow, data flow and UML diagrams, database, core algorithm); **Chapter 6** explains the methodology "
          "and implementation.",
          "**Chapter 7** describes the testing, including the failing tests; **Chapter 8** presents the output screens and measured results, and compares "
          "objectives with outcomes.",
          "**Chapter 9** concludes and **Chapter 10** lists future work. The references and three appendices (important code, installation and user guide, "
          "additional screens) follow."),
    ]
