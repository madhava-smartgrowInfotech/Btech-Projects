"""Chapter 2: Literature survey."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .content_shared import BASE_COMPARE, GAPS, LIT_TABLE
from .refs import n

LIT_TABLE = LIT_TABLE  # re-exported for the decks


def blocks():
    return [
        H1("CHAPTER 2: LITERATURE SURVEY"),
        H2("2.1 Overview"),
        P("The survey covers four strands of work: multi-agent energy management in microgrids, large language models as grid-control agents, safe learning "
          "and action shielding, and the open-source tools used to simulate distribution networks. The batch literature survey lists five papers, the first "
          "being the base paper " + n(1) + ". We read the base paper in full, and two supporting papers kept in the batch folder: Grid-Agent " + n(2) + " and a position "
          "paper on agentic grid studies with the Model Context Protocol " + n(3) + ". The other four papers of the batch survey " + n(4) + "-" + n(7) + " are known by title, "
          "year and venue only; we classified them from those and did not read them in full, so nothing is claimed about their method or results beyond what "
          "the title states. Four classic references " + n(8) + n(9) + n(10) + n(18) + " give the background."),
        TAB("Literature survey comparison", ["Work", "Approach", "Setting", "Reported result or stated limit"],
            [list(r) for r in LIT_TABLE], widths=[1.15, 1.6, 1.5, 1.95], size=8.5),
        H2("2.2 Base Paper Analysis"),
        P("The base paper, Eyimaya and Altin, 'Design of multi-agent-based energy management system for DC microgrids' " + n(1) + ", designs an energy management "
          "system for a DC microgrid with photovoltaic and wind generation, a synchronous generator, a battery energy storage system, a grid connection and "
          "critical and non-critical loads. Four rule-based agents, for the distributed energy resources, the storage, the loads and the grid connection, decide "
          "on their own part of the system and together keep the bus voltage regulated. The system is simulated in MATLAB/Simulink with a 20 microsecond "
          "sampling time and an 800 V DC bus, over eight operating scenarios. The reported result is that the bus voltage is regulated at 800 V in all "
          "scenarios and that the critical loads are supplied without interruption."),
        P("The authors name the open issues: scalability, integration with real software, cybersecurity, and the lack of experimental validation. The paper "
          "contains no language model, no safety layer independent of the control logic, and no interface that explains a decision. We adopt from it the "
          "division of responsibility among agents by role and the testing of a controller against several operating scenarios. We differ in four ways, "
          "summarised in the table below: an AC low-voltage feeder solved with pandapower, agents driven by a pluggable language-model provider, an independent "
          "shield that validates every action, and decisions that are explained and logged."),
        TAB("Base paper compared with SafeGrid-AI (qualitative)", ["Aspect", "Base paper [1]", "SafeGrid-AI"], [list(r) for r in BASE_COMPARE],
            widths=[1.2, 2.5, 2.5], size=9.5),
        P("The comparison is qualitative on purpose. The systems differ in physics (DC against AC), in tooling, in decision makers and in what was "
          "measured, and the two studies share no benchmark, so no like-for-like number exists and we do not construct one."),
        H2("2.3 LLM-Based and Agentic Grid Control"),
        P("Grid-Agent " + n(2) + " is the closest published system to ours in intent. A planning agent proposes coordinated action sequences with the help of "
          "power-flow solvers, and a validation agent checks them through sandboxed execution with rollback; violations are resolved by changing switch "
          "configurations, deploying batteries and curtailing load. It is evaluated on the IEEE 69-bus, CIGRE medium-voltage and IEEE 30-bus systems, where the "
          "best language-model configurations report a 100 % success rate and weaker ones 63 % and 44 %. Two observations shape our work. First, the spread "
          "between model configurations shows that the outcome depends on the model, which argues for a safety layer whose behaviour does not. Second, its safety "
          "mechanism is trial execution and rollback by another agent; SafeGrid-AI instead uses a deterministic rule layer that is not an agent, and projects an "
          "unsafe action to a safe one instead of discarding it."),
        P("The position paper by Picault and Goubet " + n(3) + " examines how agentic AI and the Model Context Protocol can support power-grid studies at a "
          "transmission operator. It describes an MCP server, pypowsybl-mcp, that exposes a grid simulator to AI agents through standardised tool calls, "
          "and lists requirements: interoperability, stateful execution, traceability, role-aware access control and human oversight. It outlines an evaluation "
          "strategy but reports no quantitative results. Its relevance to us is the requirement list: traceability and human oversight are what our hash-chained "
          "log and explainability view provide, at the scale of a small feeder. It also notes that integrations with the open-source pandapower library show "
          "that connecting language models to power-system solvers is feasible, which is the route we take."),
        P("Both papers evaluate real language-model agents. Ours does not, and we state this plainly: the provider that produced every measured result is a "
          "deterministic mock, and a live model was never exercised. The comparison supports the architecture, not any claim about language-model quality."),
        H2("2.4 Multi-Agent and Reinforcement-Learning Energy Management"),
        P("Multi-agent systems have a long history in power engineering. McArthur and colleagues " + n(8) + " set out the concepts, approaches and technical "
          "challenges, and Wooldridge's textbook " + n(18) + " gives the agent vocabulary of perception, action and coordination that we use. The microgrid concept "
          "goes back to Lasseter " + n(9) + ", and Farhangi " + n(10) + " places such local intelligence in the wider smart-grid picture."),
        P("The batch survey adds four more recent items that we know by title and venue: a 2025 conference paper on multi-agent deep reinforcement learning for "
          "energy-efficient smart grid management " + n(4) + "; a 2024 paper on an energy-system fault reconstruction control strategy based on multi-agent deep "
          "reinforcement learning " + n(5) + "; a 2025 paper on distributed optimal scheduling that treats electric vehicles, charging stations and the grid as "
          "separate agents " + n(6) + "; and a 2025 review chapter on multi-agent energy management in the power grid " + n(7) + ". From the titles alone we can say "
          "that learning-based multi-agent control and agent-based vehicle scheduling are active topics and that a review exists. We cannot say how these works "
          "handle safety, and we do not guess; none of the titles mentions a language model, a safety shield or an explanation interface."),
        H2("2.5 Safe Learning, Shielding and Auditability"),
        P("The common ground of the safe-learning literature is that a learning or generative component should not have the last word on a physical action. "
          "Amodei and colleagues " + n(15) + " list avoiding negative side effects and safe exploration among the concrete open problems of AI safety. García and "
          "Fernández " + n(14) + " survey safe reinforcement learning and distinguish approaches that change the learning objective from those that change how "
          "actions are chosen or filtered. Shielding, introduced by Alshiekh and colleagues " + n(12) + ", places a monitor between the agent and the environment "
          "that corrects actions which would violate a specification. Dalal and colleagues " + n(13) + " add a safety layer that adjusts the action so that "
          "constraints hold at every step. Our shield belongs to this family, with two differences: it is built for an agent that is not being trained, and its "
          "model of the world is a full AC power flow, so a candidate action is judged by actually solving the network."),
        P("Two further ideas complete the picture. The first is the explanation problem. The ReAct pattern " + n(16) + " has language models interleave reasoning "
          "text and actions, which makes behaviour readable, but Turpin and colleagues " + n(17) + " show that such text can be systematically unfaithful to the "
          "real cause of an answer. For explanations meant to be audited, we assemble them from facts the system controls. The second is tamper evidence: a log "
          "in which every record includes the SHA-256 hash " + n(20) + " of the previous one lets an auditor detect any later change, removal or reordering, at "
          "the cost of one hash per event."),
        H2("2.6 Simulation Tools and Algorithms Used in Related Work"),
        P("The base paper simulates in MATLAB/Simulink, a commercial environment suited to fast electrical transients, with a sampling time of 20 microseconds. "
          "Grid-Agent works with standard benchmark networks and power-flow solvers, and the position paper builds on pypowsybl and mentions pandapower " + n(11) + ". "
          "We chose pandapower: it is open source, written in Python like our back end, and solves balanced AC power flow with a Newton-Raphson method. A "
          "simulation step that needs several trial power flows finishes in about a third of a second on average (" + str(round(F.mean('safegrid_shielded', 'avg_step_time_ms'))) + " ms, Chapter 8)."),
        P("The algorithms we use are deliberately plain (a cost-aware heuristic policy for the mock provider, relief-first ordering, bisection for the projection, "
          "SHA-256 chaining for the log) so that the safety path is easy to read, test and, in future work, verify."),
        H2("2.7 Strengths and Limitations of Existing Research"),
        H3("Strengths"),
        B("Rule-based multi-agent control is predictable and, in the base paper, regulates the bus voltage in all eight scenarios examined " + n(1) + ".",
          "LLM-based agents handle varied situations, tool use and violation types without hand-written rules, and the best configurations are reported to "
          "succeed in every case examined " + n(2) + ".",
          "Protocol-based integration through MCP promises interoperability and auditable tool use " + n(3) + ".",
          "Safe-learning methods provide a precise way to keep an agent inside a specified safe set " + n(12) + n(13) + "."),
        H3("Limitations"),
        B("The base paper has no language model, no independent safety layer and no explanation interface, and it names scalability, integration, cybersecurity and "
          "missing experimental validation as open issues.",
          "In the LLM-based work the quality of the outcome depends strongly on the model (100 %, 63 % and 44 % in the same study), and the safety check is performed "
          "by sandboxed trial and rollback rather than by an independent rule layer.",
          "The position paper reports no quantitative results.",
          "Shielding and safety-layer methods were developed for reinforcement-learning agents in generic environments, not for language-model agents on a power network."),
        H3("Limitations of this project, stated for balance"),
        P("The same honesty applies to our own work. The limits listed in Section 1.8 bound every conclusion of this report; the four that matter most when "
          "comparing with the surveyed work are that every agent result comes from a deterministic mock provider, that no live language model was evaluated, "
          "that the guarantee is relative to the simulated model and not a formal proof, and that the comparison with the base paper is qualitative only."),
        H2("2.8 Research Gap"),
        P("The surveyed work builds multi-agent energy management without a language-model planning layer, or builds a language-model planning layer whose "
          "safety depends on the model and on trial and rollback. What is missing is the combination, in one controller, of agentic planning, a deterministic "
          "safety shield independent of the model that projects an unsafe action to a safe one, and explanations and an audit trail an operator can inspect. "
          "SafeGrid-AI is a first, simulation-level attempt to fill that gap and to measure it on repeatable scenarios; it does not close the gap for real "
          "equipment, live language models or larger networks."),
        FIG(F.diag("01_system_architecture.png"), "SafeGrid-AI places a deterministic shield between the agents and the grid (overview, detailed in Chapter 5)", 6.0),
    ]
