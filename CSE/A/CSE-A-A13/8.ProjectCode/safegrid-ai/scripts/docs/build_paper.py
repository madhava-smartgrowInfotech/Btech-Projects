"""Builds 19.IEEE_Paper.docx (two-column, 6 pages) and 19.IEEE_Paper.pdf for SafeGrid-AI.

Content comes only from facts.py (docs/results/experiment_3seeds_24steps.json and the measurements in docs/REPORT_FACTS.md),
content_shared.py and refs.py. The five paper figures are drawn here at column width so that their text stays legible.

    python -m scripts.docs.build_paper            # from 8.ProjectCode/safegrid-ai
    python -m scripts.docs.build_paper --no-pdf
"""

import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, Polygon

from . import facts as F
from .paper import Paper
from .refs import PAPER_REFS

FIG_DIR = F.FIGS
NAVY, GREY, ORANGE, BLUE, GREEN, RED, GOLD = "#1B2A41", "#8A97AB", "#EB6834", "#2A78D6", "#1BAF7A", "#D6453A", "#E8A317"
COL = {"baseline_rule": GREY, "agents_unshielded": ORANGE, "safegrid_shielded": GREEN}
plt.rcParams.update({"font.family": ["Times New Roman", "DejaVu Serif"], "font.size": 7, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#6b7280", "axes.linewidth": 0.6, "axes.grid": True, "grid.color": "#E3E8EF", "grid.linewidth": 0.5, "axes.axisbelow": True,
                     "xtick.major.width": 0.5, "ytick.major.width": 0.5})
W = 3.4  # column width, inches
SHORT_SC = {"normal": "normal", "high_solar": "high\nsolar", "peak_demand": "peak\ndemand", "battery_stress": "battery\nstress",
            "line_congestion": "line\ncongest.", "voltage_violation": "voltage\nviolation", "unsafe_ai_action": "unsafe\nAI action"}


def _save(fig, name):
    os.makedirs(FIG_DIR, exist_ok=True)
    p = os.path.join(FIG_DIR, name)
    fig.savefig(p, dpi=300, bbox_inches="tight", pad_inches=0.02, facecolor="white")
    plt.close(fig)
    return p


# ------------------------------------------------------------------ drawn figures
def _box(ax, x, y, w, h, text, fc="#F6F8FB", ec="#9AA8BD", fs=6, bold=False, lw=0.8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2", fc=fc, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", color="#0F172A", linespacing=1.15)


def _arrow(ax, p, q, color="#475569", lw=0.8, ls="-"):
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, ls=ls, shrinkA=0, shrinkB=0, mutation_scale=6))


def fig_architecture():
    fig, ax = plt.subplots(figsize=(W, 2.7))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 70)
    ax.axis("off")
    for x, w, t in ((1, 17, "Presentation"), (22, 21, "Application"), (47, 31, "Simulation and safety core"), (82, 17, "Data")):
        ax.add_patch(plt.Rectangle((x, 2), w, 62, fc="#FBFCFE", ec="#D5DCE6", lw=0.6))
        ax.text(x + w / 2, 66, t, ha="center", fontsize=6, color="#475569", fontweight="bold")
    _box(ax, 2.5, 26, 14, 24, "React\ndashboard\n(Vite)\n\nlive grid,\nagents, shield,\nexplanations", fc="#E8F0FC", ec=BLUE, fs=5.4)
    _box(ax, 23.5, 38, 18, 18, "FastAPI\nREST routers", fc="#E6F6EF", ec=GREEN, fs=5.8)
    _box(ax, 23.5, 22, 18, 12, "WebSocket\nhub", fc="#E6F6EF", ec=GREEN, fs=5.8)
    _box(ax, 23.5, 6, 18, 12, "Simulation\nService", fc="#EFEBFC", ec="#6B52D6", fs=5.8)
    _box(ax, 48.5, 52, 28, 8, "SimulationEngine", fc="#EFEBFC", ec="#6B52D6", fs=5.8, bold=True)
    _box(ax, 48.5, 41, 28, 8, "3 agents + LLM provider\n(untrusted proposer)", fc="#FFF1EA", ec=ORANGE, fs=5.4)
    _box(ax, 48.5, 31, 28, 7, "Coordinator", fc="#F6F8FB", ec=NAVY, fs=5.8)
    _box(ax, 48.5, 19, 28, 9, "Symbolic Safety Shield", fc="#FDE9E7", ec=RED, fs=6, bold=True, lw=1.2)
    _box(ax, 48.5, 6, 28, 9, "pandapower\nAC power flow", fc="#E6F6EF", ec=GREEN, fs=5.6)
    _box(ax, 83, 38, 15, 18, "SQLite\nruns, events,\nsteps,\nexperiments", fc="#FFF8E5", ec=GOLD, fs=5.4)
    _box(ax, 83, 14, 15, 18, "hash-chained\nsafety log\n(SHA-256)", fc="#FFF8E5", ec=GOLD, fs=5.4)
    _arrow(ax, (16.5, 42), (23.5, 47))
    _arrow(ax, (23.5, 28), (16.5, 34))
    _arrow(ax, (32.5, 38), (32.5, 34))
    _arrow(ax, (32.5, 22), (32.5, 18))
    _arrow(ax, (41.5, 12), (48.5, 55))
    for y0, y1 in ((52, 49), (41, 38), (31, 28), (19, 15)):
        _arrow(ax, (62.5, y0), (62.5, y1))
    _arrow(ax, (76.5, 24), (83, 24), color=RED)
    _arrow(ax, (76.5, 56), (83, 50))
    return _save(fig, "paper_fig1_architecture.png")


def fig_shield():
    fig, ax = plt.subplots(figsize=(W, 3.15))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 112)
    ax.axis("off")
    X, BW = 3, 58
    steps = [
        (100, "Proposed EnergyAction (agent / LLM)", NAVY, "white", None),
        (86, "1 Structural checks: agent, node, limits,\nreason codes, magnitude", "#E8F0FC", "#0F172A", ("REJECT", RED)),
        (72, "2 Idle or about 0 kW?", "#FFF8E5", "#0F172A", ("APPROVE", GREEN)),
        (58, "3 Trial AC power flow of the request;\nkeep violations that are NEW or WORSE\nthan the all-idle grid state", "#E8F0FC", "#0F172A", ("none: APPROVE", GREEN)),
        (41, "4 Bisection: largest scale lambda in [0, 1]\n(40 local + 14 power-flow iterations),\nround down, re-verify the exact action", "#E8F0FC", "#0F172A", None),
        (25, "5 Safe, at least 0.05 kW, right direction?", "#FFF8E5", "#0F172A", ("no: REJECT", RED)),
        (11, "PROJECT: execute the scaled action", "#FFF1EA", "#0F172A", None),
        (-1, "Log hash-chained event; return decision", NAVY, "white", None),
    ]
    heights = [8, 11, 8, 14, 15, 8, 8, 8]
    for (y, t, fc, tc, out), h in zip(steps, heights):
        yb = y - h / 2
        ax.add_patch(FancyBboxPatch((X, yb), BW, h, boxstyle="round,pad=0,rounding_size=1.2", fc=fc, ec="#6b7280" if fc not in (NAVY,) else NAVY, lw=0.7))
        ax.text(X + BW / 2, y, t, ha="center", va="center", fontsize=5.7, color=tc, linespacing=1.15)
        if out:
            _arrow(ax, (X + BW, y), (X + BW + 8, y), color=out[1])
            ax.text(X + BW + 9.5, y, out[0], ha="left", va="center", fontsize=6, color=out[1], fontweight="bold")
    for (y0, h0), (y1, h1) in zip(zip([s[0] for s in steps], heights), zip([s[0] for s in steps][1:], heights[1:])):
        _arrow(ax, (X + BW / 2, y0 - h0 / 2), (X + BW / 2, y1 + h1 / 2))
    ax.set_ylim(-7, 106)
    return _save(fig, "paper_fig2_shield.png")


def _grouped(ax, key, ylabel, fmt="{:.1f}", labels=True):
    x = np.arange(len(F.SCENARIOS))
    w = 0.27
    for i, arm in enumerate(F.ARMS):
        vals = [F.sc_mean(sc, arm, key) for sc in F.SCENARIOS]
        bars = ax.bar(x + (i - 1) * w, vals, w, color=COL[arm], label=F.ARM_LABEL[arm], linewidth=0)
        if labels:
            for b, v in zip(bars, vals):
                if v > 0:
                    ax.text(b.get_x() + b.get_width() / 2, v + 0.15, fmt.format(v), ha="center", va="bottom", fontsize=4.6, color="#334155", rotation=90)
    ax.set_xticks(x)
    ax.set_xticklabels([SHORT_SC[s] for s in F.SCENARIOS], fontsize=5.4)
    ax.set_ylabel(ylabel, fontsize=6.2)
    ax.tick_params(axis="y", labelsize=6)


def fig_violations():
    fig, ax = plt.subplots(figsize=(W, 2.45))
    _grouped(ax, "violation_steps_caused_by_actions", "steps (of 24) with violations\ncaused by actions")
    ax.set_ylim(0, 16)
    ax.legend(frameon=False, fontsize=5.8, loc="upper left", handlelength=1.2)
    return _save(fig, "paper_fig3_violations.png")


def fig_decisions():
    fig, ax = plt.subplots(figsize=(W, 2.35))
    x = np.arange(len(F.SCENARIOS))
    ap = np.array([F.sc_mean(s, "safegrid_shielded", "approved") for s in F.SCENARIOS])
    pr = np.array([F.sc_mean(s, "safegrid_shielded", "projected") for s in F.SCENARIOS])
    rj = np.array([F.sc_mean(s, "safegrid_shielded", "rejected") for s in F.SCENARIOS])
    ax.bar(x, ap, color=GREEN, label="approved", linewidth=0)
    ax.bar(x, pr, bottom=ap, color=GOLD, label="projected", linewidth=0)
    ax.bar(x, rj, bottom=ap + pr, color=RED, label="rejected", linewidth=0)
    for i in range(len(x)):
        ax.text(x[i], ap[i] / 2, f"{ap[i]:.0f}", ha="center", va="center", fontsize=5.2, color="white")
        ax.text(x[i], ap[i] + pr[i] / 2, f"{pr[i]:.0f}", ha="center", va="center", fontsize=5.2, color=NAVY)
        ax.text(x[i], ap[i] + pr[i] + rj[i] / 2, f"{rj[i]:.0f}", ha="center", va="center", fontsize=5.2, color="white")
    ax.set_xticks(x)
    ax.set_xticklabels([SHORT_SC[s] for s in F.SCENARIOS], fontsize=5.4)
    ax.set_ylabel("proposals per run (of 72)", fontsize=6.2)
    ax.set_ylim(0, 90)
    ax.tick_params(axis="y", labelsize=6)
    ax.legend(frameon=False, fontsize=5.8, ncol=3, loc="upper center", handlelength=1.2)
    return _save(fig, "paper_fig4_decisions.png")


def fig_traces():
    p = os.path.join(F.DOCS, "results", "timeseries_seed42.json")
    d = json.load(open(p, encoding="utf-8"))
    specs = [("line_congestion", "max_line_loading_pct", "worst line loading (%)", 100.0, "Line congestion"),
             ("voltage_violation", "max_voltage_pu", "highest bus voltage (pu)", 1.05, "Voltage violation")]
    fig, axes = plt.subplots(1, 2, figsize=(W, 2.05))
    fig.subplots_adjust(wspace=0.42)
    for ax, (sc, key, yl, lim, title) in zip(axes, specs):
        for tag, col, lab in (("noshield", ORANGE, "agents, no shield"), ("shield", GREEN, "SafeGrid-AI")):
            ys = [s.get(key) for s in d[f"{sc}_{tag}"]["series"]]
            ax.plot(range(len(ys)), ys, color=col, lw=1.0, label=lab)
        ax.axhline(lim, color=RED, lw=0.6, ls="--")
        ax.set_title(title, fontsize=6.4, pad=2)
        ax.set_xlabel("step (15 min)", fontsize=6)
        ax.set_ylabel(yl, fontsize=6)
        ax.tick_params(labelsize=5.6)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, frameon=False, fontsize=5.8, loc="lower center", ncol=2, handlelength=1.4, bbox_to_anchor=(0.5, -0.2))
    return _save(fig, "paper_fig5_traces.png")


# ------------------------------------------------------------------ content
def build(path):
    O = F.OVERALL
    m = F.mean
    P = Paper()
    n_steps = 21 * 24
    authors = [[n.title(), f"Roll No. {r}", "Dept. of Computer Science and Engineering", "TKR College of Engineering and Technology", F.CITY] for n, r in F.STUDENTS]
    authors.append([F.GUIDE.title() + " (Guide)", F.GUIDE_DESIGNATION, "Dept. of Computer Science and Engineering", "TKR College of Engineering and Technology", F.CITY])
    P.title_block("SafeGrid-AI: An Explainable Multi-Agent System for Dynamic Power Routing", authors)
    P.begin_two_columns()

    P.abstract(
        "Language-model agents can plan energy dispatch from a structured view of the grid, but a non-deterministic proposer that acts on physical infrastructure can "
        "request set-points that break voltage, line or battery limits. SafeGrid-AI is a neuro-symbolic multi-agent system for a low-voltage feeder with solar, batteries "
        "and an electric vehicle. Three agents propose one structured action per step; a coordinator orders them; a deterministic Symbolic Safety Shield validates every action "
        "against ten ordered checks, executing it unchanged, scaled down by bisection to the largest safe value, or not at all, and writes each decision to a hash-chained log with a "
        "structured explanation. On a pandapower AC model, 7 scenarios, 3 strategies and 3 seeds (63 runs), the shield approved "
        f"{F.APPROVED:,}, projected {F.PROJECTED} and rejected {F.REJECTED} of {F.PROPOSALS:,} proposals and no executed action created or worsened a limit violation in "
        f"{n_steps} steps, whereas the same agents without it did so in {F.UNSHIELDED_CAUSED_STEPS} steps. Safety costs time (mean step {m('safegrid_shielded', 'avg_step_time_ms'):.0f} ms against "
        f"{m('agents_unshielded', 'avg_step_time_ms'):.0f} ms) and some solar energy. Every agent result uses a deterministic mock model, the guarantee is relative to the simulated model, "
        "and grid stress that exists with all agents idle is not repaired.",
        ["agentic AI", "explainability", "large language models", "multi-agent systems", "neuro-symbolic safety", "safety shielding", "smart grid"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para("Distributed solar, home batteries and electric vehicles turn the last kilometre of the distribution grid into a place where supply and demand must be balanced "
           "every few minutes and where a badly chosen set-point can push a voltage or a cable past its limit {r:10,9}. Multi-agent systems are a natural fit, because each "
           "prosumer or device can own its decisions {r:8,18}. Recent work lets large language models act as such agents: Grid-Agent plans remedial actions with power-flow "
           "solvers {r:2}, and a Model Context Protocol server exposes a grid simulator to agents under human oversight {r:3}. Language models can reason over messy context and "
           "use tools {r:16}, but their output is probabilistic. A hallucinated or over-sized command is harmless in text and unacceptable on a feeder.")
    P.para("Three properties are wanted at once: adaptability, so that decisions follow weather, price and demand; auditability, so that an operator can ask why a set-point was chosen; and a "
           "hard stop, so that no proposal can leave the permitted operating region. Fixed rules give the third property only if they are right for every case, and Section IV shows a rule "
           "controller that is not. Language-model agents give the first two but not the third. A design that keeps all three has to treat the proposer as untrusted.")
    P.para("The safe-learning literature offers a remedy: a shield that monitors every action and corrects it before it reaches the environment {r:12}, or a safety layer that projects "
           "an action onto the feasible set {r:13,14}. This paper brings that idea to language-model energy agents. We keep the agents free to propose, and put an independent, "
           "deterministic Symbolic Safety Shield between every proposal and the grid, so that safety does not depend on the model behaving well {r:15}.")
    P.para("The contributions are: (1) a neuro-symbolic architecture in which an untrusted proposer, a coordinator, a shield and an AC power-flow simulator are separate components; "
           "(2) a shield that validates ten ordered checks, attributes only new or worse violations to an action, and projects an unsafe action onto the largest safe fraction by "
           "bisection; (3) a hash-chained audit log and structured, per-decision explanations; and (4) a reproducible comparison of three strategies over seven scenarios and three "
           "seeds, with the cost of safety and the limits of the evidence stated. Section II reviews related work, Section III describes the system, Section IV reports the measurements "
           "and Section V concludes.")

    # ------------------------------------------------------------------ II
    P.heading("II", "Related Work")
    P.para("**Base paper.** Eyimaya and Altin {r:1} design four rule-based agents (distributed energy resources, energy storage, load and grid) for a DC microgrid with PV, wind, a "
           "synchronous generator, a battery and critical and non-critical loads. In MATLAB/Simulink with a 20 microsecond sampling time and an 800 V bus, the bus voltage stays regulated "
           "and critical loads stay supplied in all eight operating scenarios. The authors name scalability, software integration, cybersecurity and the lack of experimental validation "
           "as open issues. The agents contain no language model, no formal safety layer and no explanation interface; those are the three things this work adds.")
    P.para("**LLM agents for grids.** Grid-Agent {r:2} pairs a planning agent with a validation agent that executes in a sandbox with rollback; on IEEE 69-bus, CIGRE MV and IEEE 30-bus "
           "networks its best language-model configurations report a 100 % success rate, weaker ones 63 % and 44 %. Safety there comes from sandboxed trial and rollback "
           "rather than from a separate rule layer. Picault and Goubet {r:3} argue for traceable, stateful, human-supervised agent workflows and present a first MCP interface, "
           "without quantitative results. McArthur et al. {r:8} and Wooldridge {r:18} give the general case for agents in power engineering; Lasseter {r:9} and Farhangi {r:10} frame the "
           "microgrid and smart-grid setting.")
    P.para("**Optimisation baselines.** Classical optimal power flow is mathematically robust but, for modern grids with renewable generation and many discrete assets, becomes a mixed-integer, "
           "non-convex, unbalanced AC problem that is hard to solve {r:2}. The shield does not optimise anything: it only filters what an agent proposes, which keeps its cost to a few trial power "
           "flows per action and leaves the choice of objective, cost, self-consumption or something else, to the agent.")
    P.para("**Safe learning and explanation.** Shielding {r:12}, safety layers {r:13} and safe reinforcement learning {r:14} constrain a learner's actions; Amodei et al. {r:15} list safe "
           "exploration and robustness among the basic problems of AI safety. For explanations, written reasoning from a language model can be unfaithful to what actually drove its "
           "answer {r:17}, so our explanations are built from the recorded inputs, the chosen action and the shield's checks, not from model-written reasoning. Table I summarises the comparison.")
    P.table("Comparison with the closest work", ["Work", "Decision layer", "Safety mechanism", "Evidence"], [
        ["{r:1}", "Four rule-based agents", "Control logic regulates the bus; no validation layer", "8 Simulink scenarios, DC microgrid"],
        ["{r:2}", "LLM planner + validator agent", "Sandboxed trial with rollback", "3 IEEE/CIGRE networks; 100 % best, 63 % and 44 % weaker"],
        ["{r:3}", "LLM agents via MCP, human in the loop", "Human validation, traceability", "Position paper, no results"],
        ["This work", "3 agents, pluggable LLM provider", "Deterministic shield: approve, project, reject; audit chain", "63 runs, 504 shielded steps, mock LLM"],
    ], widths=[0.4, 0.85, 1.1, 1.05], size=6.5, align=["c", "l", "l", "l"])
    P.para("**Positioning.** Compared with {r:1}, this work moves from a DC microgrid in Simulink to an AC feeder solved with pandapower, replaces fixed rules by a pluggable proposer, and "
           "adds a validation layer and an audit trail. Compared with {r:2}, it validates an action before it is committed, deterministically and without a language model, and it attributes "
           "violations to actions rather than to the grid. Compared with {r:3}, it supplies the auditable action path that paper calls for, but it does not address transmission-system studies. "
           "The comparison with {r:1} is qualitative: the two systems share no benchmark, so no like-for-like number exists.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Proposed System and Method")
    P.sub("A", "Architecture")
    P.para("The system (Fig. 1) is a React dashboard over a FastAPI service with REST routes and a WebSocket stream. A simulation service owns one engine per run. At each 15-minute step the "
           "engine takes seeded solar, load and price profiles, computes the no-action power flow with pandapower {r:11}, lets each agent perceive a structured context, collects one "
           "proposal per agent, has the coordinator order them, validates them one by one against the cumulative grid state, commits only the validated set-points, and "
           "stores and streams the result. The agents and the language model are untrusted; the coordinator, shield and simulator are trusted, and a test enforces that the "
           "shield imports nothing from the language-model, agent, simulation or grid packages.")
    P.figure(fig_architecture(), "System architecture. The proposer is untrusted; the coordinator, shield and power-flow simulator are deterministic trusted code.")
    P.sub("B", "Feeder, agents and proposals")
    P.para("The simulated feeder is a 20 kV source behind a 0.25 MVA 20/0.4 kV transformer with three low-voltage buses (NAYY 4x50 cables of 0.30, 0.45 and 0.25 km) and power factor 0.95. "
           "Three agents sit on it: a residential prosumer (6 kWp PV, 10 kWh battery), an electric vehicle (40 kWh, 7.4 kW, charge only) and a renewable prosumer (20 kWp PV, 30 kWh battery). "
           "An agent's context holds its load, solar output, battery state, price, its neighbours' exchange and voltage, and the grid limits. Its reply must be one EnergyAction: one of seven "
           "types (charge, discharge, import, export, curtail, shift load, idle), a finite power, a duration, a target and reason codes; unknown fields are rejected. A provider "
           "failure, timeout or malformed output becomes a labelled deterministic fallback decision that is shielded like any other. All measurements use a deterministic, seeded mock "
           "provider built on a cost-aware heuristic with seeded over-sizing; an API provider for Anthropic and OpenAI wire formats exists but was not run against a live model.")
    P.sub("C", "Coordinator")
    P.para("The coordinator flags three conflict types: peer mismatch, target contention and shared feeder. It orders proposals relief-first (idle, curtail and shift-load actions "
           "before charging and exporting), then in a rotating order, so that actions that lower stress are validated before actions that add it.")
    P.sub("D", "Symbolic Safety Shield")
    P.para("The shield (Fig. 2) reads only the structured action. Its ten ordered checks are structure, power limits, battery, node limits, power balance, power-flow convergence, bus voltage "
           "(0.95 to 1.05 pu, tighter than the 10 % band of EN 50160 {r:19}), line loading (100 %), transformer loading (100 %) and import/export limits (200 kW). A violation is blamed on an "
           "action only if it is new or worse than in the all-idle grid state, so pre-existing stress does not cause good actions to be rejected. An action with no such violation is "
           "approved unchanged. Otherwise the shield projects it: with a the requested set-point and N(·) the set of new or worse violations,")
    P.para("λ* = max {λ : 0 ≤ λ ≤ 1, N(λa) = ∅},          (1)", align="c", indent=0, italic=True, before=2, after=3)
    P.para("found by bisection (40 iterations on local limits, 14 on power-flow limits). The rounded action is re-verified up to four times with a shrinking factor; a result below 0.05 kW, or one that "
           "flips an import into an export, is rejected. The shield never extends or enlarges a proposal.")
    P.figure(fig_shield(), "Decision flow of the Symbolic Safety Shield for one proposed action.")
    P.sub("E", "Audit trail and explanation")
    P.para("Every non-approved action and every fallback is written as a safety event whose SHA-256 hash {r:20} covers the previous hash, the event identity and the payload, so removing or "
           "editing an event breaks the chain; verification passed in 21 of 21 shielded runs. Each decision also carries a structured explanation (inputs, decision factors, "
           "chosen action, shield result). No chain-of-thought is requested or stored, and a test checks this.")
    P.sub("F", "Implementation")
    P.para(f"The backend is {F.LOC['backend']:,} lines of Python (FastAPI 0.143, pydantic 2, pandapower 3.5.6) with a SQLite store of five tables (runs, events, safety events, steps, experiments); "
           f"the tests add {F.LOC['tests']} lines and the dashboard {F.LOC['frontend']:,} lines of JavaScript and CSS. REST routes start, stop, step and reset a run, run a scenario to completion, list "
           "agents and their decisions, read safety events and constraints, and launch comparison jobs; a dry-run route validates an operator-supplied action against the shield without applying it. "
           "The WebSocket stream carries agent actions, safety interventions, conflicts and grid updates, and the dashboard shows the live grid, each agent's decision with its explanation, the "
           "safety log and the power-flow charts. The API has no authentication because it is a single-user research prototype, the dashboard sign-in is a browser-side gate only, and model output "
           "is never executed as code, SQL or a shell command.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Experimental Results and Discussion")
    P.sub("A", "Setup")
    P.para(f"Seven seeded scenarios (normal, high solar, peak demand, battery stress, line congestion, voltage violation and unsafe AI action, which injects over-sized and malformed proposals) "
           f"were run for 24 steps of 15 minutes under three strategies and seeds 0, 1 and 2, giving {F.N_RUNS} runs. The strategies are a non-LLM time-of-use rule controller with no shield, "
           "the three agents with no shield (proposals applied as requested) and SafeGrid-AI (agents plus shield). The main metric counts the steps whose executed actions caused a violation "
           "that was new or worse than the all-idle grid state. All data are synthetic, generated from the seed, and the tariff is illustrative. The runs took about ten minutes on "
           f"{F.MACHINE}, with Python 3.11, pandapower 3.5.6 and FastAPI 0.143.")
    P.para("**Metrics.** Violations caused by actions counts limit violations that are new or worse than in the all-idle grid state, which is what the shield is designed to prevent. Steps with any "
           "violation after execution also include stress that no action caused. Raw-proposal violations are a counterfactual: the violations the unvalidated proposals of the same step would have caused. "
           "Renewable utilisation is one minus the curtailed share of the available PV energy (undefined in line congestion, where no PV energy is available), battery throughput is charged plus discharged "
           "energy divided by installed capacity, and step time is the wall-clock time of one step including agent decisions, validation and the power flow.")
    rows = [
        ["Steps with violations caused by actions (of 24)"] + [f"{m(a, 'violation_steps_caused_by_actions'):.2f}" for a in F.ARMS],
        ["Violations caused by actions"] + [f"{m(a, 'violations_caused_by_actions'):.2f}" for a in F.ARMS],
        ["Steps with any violation after execution"] + [f"{m(a, 'violation_steps_executed'):.2f}" for a in F.ARMS],
        ["Voltage-violation steps"] + [f"{m(a, 'voltage_violation_steps'):.2f}" for a in F.ARMS],
        ["Line-overload events"] + [f"{m(a, 'line_overload_events'):.2f}" for a in F.ARMS],
        ["Energy cost (INR, illustrative tariff)"] + [f"{m(a, 'total_cost'):.1f}" for a in F.ARMS],
        ["Renewable utilisation"] + [f"{m(a, 'renewable_utilization'):.3f}" for a in F.ARMS],
        ["Battery throughput / capacity"] + [f"{m(a, 'battery_utilization'):.3f}" for a in F.ARMS],
        ["Mean step time (ms)"] + [f"{m(a, 'avg_step_time_ms'):.1f}" for a in F.ARMS],
    ]
    P.table("Measured results, mean per run over 7 scenarios and 3 seeds (21 runs per strategy, 24 steps)", ["Metric", "Rule baseline", "Agents, no shield", "SafeGrid-AI"], rows,
            widths=[1.6, 0.55, 0.65, 0.6], size=6.5, align=["l", "c", "c", "c"])
    P.sub("B", "Safety outcome")
    P.para(f"Table II and Fig. 3 give the main result. With the shield, executed actions caused no violation in any of the {n_steps} steps (0.00 in every scenario). The same agents without it "
           f"caused violations in {F.UNSHIELDED_CAUSED_STEPS} steps ({F.UNSHIELDED_CAUSED} violations in total), and the rule controller, although not a language model, caused them in "
           f"{F.BASELINE_CAUSED_STEPS} steps, all in line congestion (12.0 of 24 steps per run) and peak demand (3.3); so a conventional controller needs a shield as well. Without the shield, the "
           f"raw proposals of the shielded arm would have caused {F.RAW_WOULD} violations in {F.RAW_WOULD_STEPS} steps.")
    P.figure(fig_violations(), "Steps (of 24) with violations caused by executed actions, mean of three seeds, by scenario and strategy.")
    P.para("Per scenario (Fig. 3), the unshielded agents cause violations in all seven: 1.67 steps in normal, 0.67 in high solar, 4.00 in peak demand, 4.67 in battery stress, 11.33 in line "
           "congestion, 6.33 in voltage violation and 4.33 in unsafe AI action. The rule controller is safe in five scenarios but causes 12.00 steps in line congestion and 3.33 in peak "
           "demand, because it follows time-of-use rules and has no network check.")
    P.sub("C", "Shield behaviour")
    P.para(f"Of {F.PROPOSALS:,} proposals the shield approved {F.APPROVED:,} ({F.APPROVED / F.PROPOSALS * 100:.1f} %), projected {F.PROJECTED} ({F.PROJECTED / F.PROPOSALS * 100:.1f} %) and rejected "
           f"{F.REJECTED} ({F.REJECTED / F.PROPOSALS * 100:.1f} %), logging {F.SAFETY_EVENTS} safety events and {F.CONFLICTS} coordinator conflicts. Fig. 4 shows that line congestion needs the most "
           f"projections (23.0 of 72 proposals per run) and that voltage violation, battery stress and unsafe AI action need the most rejections (8.3, 8.0 and 8.0), as expected from their design. The coordinator flagged about 11.5 conflicts per run ({F.CONFLICTS} in 21 runs), and the fallback rate was 0.2 %, caused by the malformed-output "
           "fault injected in unsafe AI action; a fallback decision is still validated like any other.")
    P.figure(fig_decisions(), "Shield decisions per run (72 proposals), mean of three seeds, by scenario.")
    rows3 = []
    for sc in F.SCENARIOS:
        g = lambda k: F.sc_mean(sc, "safegrid_shielded", k)
        rows3.append([sc.replace("_", " "), f"{g('approved'):.1f} / {g('projected'):.1f} / {g('rejected'):.1f}", f"{g('violations_without_shield'):.1f}",
                      f"{g('violation_steps_no_action'):.1f}", f"{g('violation_steps_executed'):.1f}"])
    P.table("SafeGrid-AI per scenario, mean of 3 seeds (72 proposals and 24 steps per run)", ["Scenario", "Approved / projected / rejected", "Raw-proposal violations", "Idle-grid stress steps", "Violation steps after execution"],
            rows3, widths=[0.8, 0.9, 0.55, 0.55, 0.6], size=6.3, align=["l", "c", "c", "c", "c"])
    P.para("Table III separates what the shield prevents from what it cannot. Raw-proposal violations are the violations the unvalidated proposals would have caused; they are largest in line "
           "congestion (16.0) and peak demand (14.0) and the shield removes all of them. Idle-grid stress is violation that exists when every agent does nothing: 20.0 of 24 steps in high solar and 12.0 "
           "in peak demand, and no proposal causes it. The shield does not repair it by design. The relief-first order and the projections nevertheless reduce it in some scenarios (high solar falls from 20.0 "
           "to 1.7 violation steps), but not in all: 8.7 of the 12.0 peak-demand steps remain in violation. Relief is a by-product, not a guarantee.")
    P.sub("D", "Single-run traces")
    P.para("Fig. 5 shows seed-42 runs. In line congestion the unshielded agents drive the worst line to 137.7 % loading, while the shield projects the same agents' actions to exactly 100.0 %. In voltage "
           "violation the highest bus voltage is 1.117 pu without the shield and 1.056 pu with it: slightly above 1.05 pu because stress that exists with every agent idle is not repaired. In "
           "peak demand the lowest voltage is 0.861 pu without and 0.932 pu with the shield, still below 0.95 pu for the same reason.")
    P.figure(fig_traces(), "Seed-42 traces, shield off and on; dashed lines are the limits.")
    P.sub("E", "Cost of safety and run-time behaviour")
    P.para(f"The shield is not free. Mean step time rises from {m('agents_unshielded', 'avg_step_time_ms'):.0f} to {m('safegrid_shielded', 'avg_step_time_ms'):.0f} ms because each validation runs trial power flows. "
           f"Renewable utilisation falls from {m('agents_unshielded', 'renewable_utilization'):.3f} to {m('safegrid_shielded', 'renewable_utilization'):.3f} (0.607 in high solar and 0.787 in voltage violation, where PV is curtailed), "
           f"while mean energy cost is {m('safegrid_shielded', 'total_cost'):.1f} INR against {m('agents_unshielded', 'total_cost'):.1f} unshielded and {m('baseline_rule', 'total_cost'):.1f} for the rules, "
           "about 4 % above the rule baseline. Through the live API, a dry-run validation has a median of 62.8 ms (36.6 ms for an unsafe request that is rejected, "
           "230.0 ms when bisection is needed) and a full step 440.7 ms (95th percentile 522.2 ms). The mock provider answers in 0.17 ms on average, so these figures say nothing about the latency of a real model. Table IV lists the timings.")
    P.table("Live API latency on localhost (scenario unsafe AI action, seed 42)", ["Call", "n", "Median (ms)", "95th pct. (ms)"],
            [[c.replace("(agent proposal, dry run)", "(dry run)"), str(n), f"{a:.1f}", f"{b:.1f}"] for c, n, a, b in F.API_LAT],
            widths=[2.0, 0.3, 0.55, 0.55], size=6.3, align=["l", "c", "c", "c"])
    P.sub("F", "Explanations and audit trail in use")
    P.para("Every decision, approved or not, is stored with a structured explanation: the context the agent saw, the decision factors, the proposed action with its reason codes, and the shield's "
           "result. For a projected action the result lists the ten checks with their outcome (passed, failed, or not evaluated because an earlier check had already rejected the action), the "
           "violations with the quantity, the limit and the unit, and the correction from the requested power to the executed power. The dashboard presents the same record next to the live grid "
           "and the safety log lists the events with their hashes. This is a record of what was proposed, checked and changed; it is not a statement of why a language model chose an action, "
           "which is exactly what cannot be trusted to be faithful {r:17}.")
    P.para(f"A side effect of unchecked proposals is visible in the battery. Battery throughput per run is {m('agents_unshielded', 'battery_utilization'):.2f} times the installed capacity for the "
           f"unshielded agents, against {m('baseline_rule', 'battery_utilization'):.2f} for the rules and {m('safegrid_shielded', 'battery_utilization'):.2f} with the shield: over-sized charge and "
           "discharge requests cycle the batteries hard, the shield's checks cap them, and throughput returns to the level of the rule controller. This is consistent with the lower cost in Table II, "
           "although the experiment does not isolate the cause.")
    P.sub("G", "Discussion and limits")
    P.para("The result is narrower than the claim that motivated the project. The guarantee is that, in the simulated model, executed actions never create or worsen a violation of the configured limits; "
           "it is not a formal proof, and it does not make the grid violation-free: with every agent idle the feeder is already outside its limits in 6.3 steps per run on average, and after "
           f"execution {m('safegrid_shielded', 'violation_steps_executed'):.2f} steps per run still contain a violation, against {m('baseline_rule', 'violation_steps_executed'):.2f} for the rules. "
           "A violation-resolution rate for such pre-existing stress was not measured. All agent results use the mock provider, so language-model quality and real inference latency are unmeasured; "
           "there are only three seeds, a synthetic three-node feeder, no protection, dynamics or phase unbalance, and no user study. The comparison with the base paper is qualitative: its "
           "DC microgrid, Simulink model and rule agents share no benchmark with this work. 52 of 55 unit tests pass; two grid tests fail on numeric tolerances under pandapower 3.5.6 and one "
           "WebSocket test hangs under the installed test client, while a live smoke test passes 20 of 20 checks.")
    P.para("**Threats to validity.** The mock provider is a transparent cost-aware heuristic with seeded over-sizing, so the unshielded arm's violations measure how often an over-sized or "
           "ill-timed proposal hurts, not how often a real model errs; a real model may be more or less hazardous. The scenarios were written by the authors and include faults designed to "
           "stress the shield, so the unsafe-AI-action scenario shows the shield working, not how often unsafe proposals occur in practice. With three seeds the means carry little statistical "
           "weight, and the experiment output reports the spread of each metric rather than a significance test. The 0.95 to 1.05 pu band and the 100 % loading limits are configured "
           "values, and a change of limits changes the counts.")
    P.para("**Reproducibility.** The 63-run record, the seed-42 traces and the live-API timings are stored with the code, the experiment is a single command with fixed seeds, and every number in "
           "this paper is read from those files. Wall-clock figures depend on the machine and shift between runs; the violation counts do not, because the profiles, the mock provider and the "
           "shield are deterministic for a given seed.")
    P.para("**Operational use.** Because validation takes tens to a few hundred milliseconds, the shield fits a control step of minutes. In an operator's hands the dry-run route lets a proposed set-point "
           "be checked before it is applied, the safety log shows which check failed and by how much, and the explanation attached to each decision lists the inputs and factors that led to it. "
           "None of this was evaluated with users. Before any use beyond simulation the model would have to be replaced by measured network data, protection and dynamics would have to be "
           "modelled, and the API would need authentication.")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion and Future Work")
    P.para(f"SafeGrid-AI separates proposing from permitting: agents propose, and a deterministic shield approves, scales down or rejects each action before the simulated feeder sees it. Over "
           f"{F.N_RUNS} runs and {n_steps} shielded steps no executed action created or worsened a limit violation, at the price of about {m('safegrid_shielded', 'avg_step_time_ms') / m('agents_unshielded', 'avg_step_time_ms'):.1f} "
           "times the step time and some curtailed solar energy, and every decision left an explanation and a tamper-evident record. The evidence is simulated, uses a mock model and three seeds, and "
           "supports a model-relative guarantee only.")
    P.para(f"Three lessons stand out. First, a conventional rule controller was not safe either ({F.BASELINE_CAUSED_STEPS} violating steps), so a shield is useful whatever the proposer is. Second, the "
           "guarantee comes from checking actions, not from the model, so a stronger or weaker language model is expected to change cost and utilisation but not the safety counts; this expectation "
           "has not been tested with a live model. Third, safety has a measurable price: about "
           f"{m('safegrid_shielded', 'avg_step_time_ms') / m('agents_unshielded', 'avg_step_time_ms'):.1f} times the step time and {(m('agents_unshielded', 'renewable_utilization') - m('safegrid_shielded', 'renewable_utilization')) * 100:.1f} points "
           f"of renewable utilisation ({m('agents_unshielded', 'renewable_utilization'):.3f} to {m('safegrid_shielded', 'renewable_utilization'):.3f}) relative to unshielded agents.")
    P.para("Future work is to evaluate live language models and their latency, to measure a violation-resolution rate for pre-existing stress, to repair the two failing tolerance tests, to test larger and "
           "three-phase networks and real measurement data, to add many more seeds, and to study operator trust with a user study.")

    P.references()
    P.save(path)
    return path, len(P.order)


def export_pdf(docx_path, pdf_path, tries=5):
    """Word COM is flaky right after another Office run: retry a few times."""
    import time

    last = None
    for _ in range(tries):
        try:
            return _export_pdf(docx_path, pdf_path)
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(8)
    raise last


def _export_pdf(docx_path, pdf_path):
    import win32com.client

    from .render_deck import ComLock

    with ComLock():
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        try:
            doc = word.Documents.Open(os.path.abspath(docx_path), ReadOnly=True, AddToRecentFiles=False)
            doc.Repaginate()
            doc.ExportAsFixedFormat(os.path.abspath(pdf_path), 17)
            pages = doc.ComputeStatistics(2)
            doc.Close(False)
            return pages
        finally:
            word.Quit()


if __name__ == "__main__":
    out = os.path.join(F.BATCH, "19.IEEE_Paper.docx")
    print(build(out))
    if "--no-pdf" not in sys.argv:
        pdf = os.path.join(F.BATCH, "19.IEEE_Paper.pdf")
        print("pages (Word):", export_pdf(out, pdf))
