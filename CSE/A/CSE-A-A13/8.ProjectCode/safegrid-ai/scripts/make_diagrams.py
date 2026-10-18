"""
Draws every design diagram used in the project documents (matplotlib only, 150 dpi).

    python scripts/make_diagrams.py            # -> docs/diagrams/*.png

Each diagram mirrors what the code does: backend/app/{api,services,simulation,agents,llm,safety,grid,database}.
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyBboxPatch, Polygon, Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "diagrams")
os.makedirs(OUT, exist_ok=True)

NAVY, INK, SLATE = "#1B2A41", "#0F172A", "#475569"
ORANGE, BLUE, GREEN, PURPLE, GOLD, RED = "#EB6834", "#2A78D6", "#1BAF7A", "#6B52D6", "#E8A317", "#D6453A"
PAPER, LINE = "#F6F8FB", "#9AA8BD"
plt.rcParams["font.family"] = "DejaVu Sans"


def canvas(w, h, title=None, ty=99):
    """Work in a 100 x ty coordinate space; the figure is cropped to its content when saved."""
    top = ty + 2
    fig, ax = plt.subplots(figsize=(w, w * top / 100))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, top)
    ax.axis("off")
    ax.set_aspect("equal")
    if title:
        ax.text(1, ty, title, fontsize=13, fontweight="bold", color=NAVY, va="top")
    return fig, ax


def box(ax, x, y, w, h, text, fc=PAPER, ec=LINE, tc=INK, fs=9.5, bold=False, lw=1.3, rounding=1.2, ls="-", ha="center"):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={rounding}", fc=fc, ec=ec, lw=lw, ls=ls)
    ax.add_patch(p)
    tx = x + w / 2 if ha == "center" else x + 1.2
    ax.text(tx, y + h / 2, text, ha=ha, va="center", fontsize=fs, color=tc, fontweight="bold" if bold else "normal", linespacing=1.25)
    return (x, y, w, h)


def arrow(ax, p, q, label=None, color=SLATE, lw=1.4, ls="-", fs=8, off=(0, 1.2), rad=0.0, head="-|>", lab_ha="center", lp=None):
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle=head, color=color, lw=lw, ls=ls,
                                                    connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0))
    if label:
        lx, ly = lp if lp else ((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1])
        ax.text(lx, ly, label, fontsize=fs, color=color, ha=lab_ha, va="center", bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", path)


def mid(b, side):
    x, y, w, h = b
    return {"l": (x, y + h / 2), "r": (x + w, y + h / 2), "t": (x + w / 2, y + h), "b": (x + w / 2, y)}[side]


# ---------------------------------------------------------------- 01 architecture
def architecture():
    fig, ax = canvas(11, 7.4, "System architecture", ty=78)
    for x, w, label in ((1, 20, "Presentation tier"), (24, 22, "Application tier"), (49, 29, "Simulation and safety core"), (81, 18, "Data tier")):
        ax.add_patch(Rectangle((x, 6), w, 66, fc="#FBFCFE", ec="#D5DCE6", lw=1))
        ax.text(x + w / 2, 69.4, label, ha="center", fontsize=9.5, color=SLATE, fontweight="bold")
    ui = box(ax, 2.5, 36, 17, 26, "React 18 dashboard\nVite, port 5313\n\nDashboard, Grid view,\nAgent monitor,\nSafety shield,\nPower flow, Scenarios,\nExplainability", fc="#E8F0FC", ec=BLUE, fs=7.8)
    land = box(ax, 2.5, 10, 17, 18, "Landing page\n(three.js hero)\n\nDemo sign-in\n(browser-side gate)", fc="#E8F0FC", ec=BLUE, fs=7.8)
    api = box(ax, 25, 44, 20, 18, "FastAPI service\nport 8313\n\nREST routers: health, grid,\nsimulation, scenarios,\nagents, safety, metrics", fc="#E6F6EF", ec=GREEN, fs=7.8)
    ws = box(ax, 25, 29, 20, 11, "WebSocket\n/ws/simulation\nConnectionHub", fc="#E6F6EF", ec=GREEN, fs=7.8)
    svc = box(ax, 25, 10, 20, 15, "SimulationService\nstart, stop, step,\nscenario run, dry run,\nexperiment jobs", fc="#EFEBFC", ec=PURPLE, fs=7.8)
    eng = box(ax, 50, 59, 27, 8, "SimulationEngine (one per run)", fc="#EFEBFC", ec=PURPLE, fs=8, bold=True)
    agt = box(ax, 50, 46, 27, 10, "AgentManager: 3 agents\nprosumer, EV, renewable", fc=PAPER, ec=NAVY, fs=7.8)
    llm = box(ax, 50, 36, 27, 7, "LLM provider: mock / api / baseline / failing", fc="#FFF1EA", ec=ORANGE, fs=7.4)
    crd = box(ax, 50, 27, 27, 6.5, "Coordinator: conflicts, relief-first order", fc=PAPER, ec=NAVY, fs=7.6)
    sh = box(ax, 50, 15.5, 27, 9.5, "Symbolic Safety Shield\napprove / project / reject", fc="#FDE9E7", ec=RED, fs=8.2, bold=True, lw=2)
    grid = box(ax, 50, 7.5, 27, 6, "GridSimulator (pandapower AC power flow)", fc="#E6F6EF", ec=GREEN, fs=7.4)
    db = box(ax, 82, 44, 16, 18, "SQLite\nsafegrid.db\n\nruns, events,\nsafety_events,\nsteps, experiments", fc="#FFF8E5", ec=GOLD, fs=7.8)
    chain = box(ax, 82, 27, 16, 12, "Hash-chained\nsafety log\n(SHA-256)", fc="#FFF8E5", ec=GOLD, fs=7.8)
    prof = box(ax, 82, 10, 16, 12, "Seeded profiles\nPV, load, price,\nscenario faults", fc="#FFF8E5", ec=GOLD, fs=7.8)
    arrow(ax, mid(ui, "r"), (25, 53), "REST", color=BLUE, off=(0, 2.0), fs=7.4)
    arrow(ax, (25, 33.5), (19.5, 41), "events", color=GREEN, fs=7.2, off=(1.5, -2.2))
    arrow(ax, (35, 44), (35, 40))
    arrow(ax, (35, 29), (35, 25))
    arrow(ax, (45, 17.5), (50, 62), None, rad=-0.22, color=PURPLE)
    arrow(ax, (63.5, 59), (63.5, 56))
    arrow(ax, (63.5, 46), (63.5, 43))
    arrow(ax, (63.5, 36), (63.5, 33.5), "proposals", off=(6.5, 0), fs=7.2)
    arrow(ax, (63.5, 27), (63.5, 25), None)
    arrow(ax, (63.5, 15.5), (63.5, 13.5), "trial / commit", off=(7.5, 0), fs=7.2)
    arrow(ax, (77, 20), (82, 33), "append", fs=7.2, off=(0.5, -2), color=RED)
    arrow(ax, (77, 63), (82, 56), "persist", fs=7.2, off=(1.5, 2.5))
    arrow(ax, (82, 16), (77, 61), None, ls="--", rad=0.15)
    ax.text(50, 2.6, "Trust boundary: the LLM provider is an untrusted proposer; the coordinator, shield and simulator are trusted deterministic code.",
            ha="center", fontsize=8, color=SLATE, style="italic")
    save(fig, "01_system_architecture.png")


# ---------------------------------------------------------------- 02 workflow
def workflow():
    fig, ax = canvas(11, 4.6, "High-level workflow of one simulation step (15 simulated minutes)", ty=50)
    steps = [
        ("1  Inputs", "seeded PV, load,\nprice, faults", NAVY),
        ("2  Baseline", "no-action power\nflow of the grid", BLUE),
        ("3  Perceive", "structured context\nper agent", ORANGE),
        ("4  Propose", "agent / LLM returns\none EnergyAction", PURPLE),
        ("5  Coordinate", "detect conflicts,\nrelief actions first", GOLD),
        ("6  Validate", "Safety Shield:\napprove, project, reject", RED),
        ("7  Commit", "power flow, battery\nstate of charge", GREEN),
        ("8  Log, explain", "hash-chained event,\nWebSocket to dashboard", NAVY),
    ]
    w, gap = 22.9, 2.2
    for i, (t, s, c) in enumerate(steps):
        row_y = 28 if i < 4 else 7
        xx = 1.5 + (i % 4) * (w + gap)
        box(ax, xx, row_y, w, 14, "", fc="white", ec=c, lw=2)
        ax.add_patch(Rectangle((xx, row_y + 9.6), w, 4.4, fc=c, ec=c))
        ax.text(xx + w / 2, row_y + 11.8, t, ha="center", va="center", color="white", fontsize=10, fontweight="bold")
        ax.text(xx + w / 2, row_y + 4.6, s, ha="center", va="center", color=INK, fontsize=9, linespacing=1.3)
        if i % 4 != 3:
            arrow(ax, (xx + w, row_y + 6), (xx + w + gap, row_y + 6))
    x_last = 1.5 + 3 * (w + gap) + w / 2
    ax.plot([x_last, x_last], [28, 24], color=SLATE, lw=1.4)
    ax.plot([x_last, 1.5 + w / 2], [24, 24], color=SLATE, lw=1.4)
    arrow(ax, (1.5 + w / 2, 24), (1.5 + w / 2, 21.2))
    ax.text(50, 44.6, "The shield sees only the structured action; it never reads prompts or model text. Every non-approved action is written to the safety log.",
            ha="center", fontsize=8.3, color=SLATE, style="italic")
    save(fig, "02_high_level_workflow.png")


# ---------------------------------------------------------------- DFD helpers
def process(ax, cx, cy, r, text, num, fs=8):
    ax.add_patch(Circle((cx, cy), r, fc="#E8F0FC", ec=BLUE, lw=1.6))
    ax.text(cx, cy + r * 0.45, num, ha="center", va="center", fontsize=8.5, fontweight="bold", color=BLUE)
    ax.text(cx, cy - r * 0.12, text, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.2)
    return (cx, cy, r)


def entity(ax, x, y, w, h, text):
    ax.add_patch(Rectangle((x, y), w, h, fc="#FFF1EA", ec=ORANGE, lw=1.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9, color=INK, fontweight="bold", linespacing=1.2)
    return (x, y, w, h)


def store(ax, x, y, w, h, text, tag):
    ax.add_patch(Rectangle((x, y), w, h, fc="#FFF8E5", ec="none"))
    ax.plot([x, x + w], [y + h, y + h], color=GOLD, lw=1.8)
    ax.plot([x, x + w], [y, y], color=GOLD, lw=1.8)
    ax.plot([x, x], [y, y + h], color=GOLD, lw=1.8)
    ax.text(x + 1.3, y + h / 2, tag, ha="left", va="center", fontsize=8.5, fontweight="bold", color=GOLD)
    ax.text(x + w / 2 + 2.5, y + h / 2, text, ha="center", va="center", fontsize=8.3, color=INK, linespacing=1.2)
    return (x, y, w, h)


# ---------------------------------------------------------------- 03-06 DFDs and UML
def uml_class(ax, x, y, w, name, attrs, methods, fc="#FFFFFF", ec=NAVY, stereotype=None, fs=7.0):
    line = 2.1
    h_head = 5.2 if stereotype else 3.6
    h_attr = max(len(attrs), 1) * line + 1.0
    h_met = max(len(methods), 1) * line + 1.0
    h = h_head + h_attr + h_met
    ax.add_patch(Rectangle((x, y - h), w, h, fc=fc, ec=ec, lw=1.4))
    ax.add_patch(Rectangle((x, y - h_head), w, h_head, fc="#E8F0FC", ec=ec, lw=1.4))
    if stereotype:
        ax.text(x + w / 2, y - 1.3, f"<<{stereotype}>>", ha="center", va="center", fontsize=6.3, color=SLATE)
        ax.text(x + w / 2, y - 3.5, name, ha="center", va="center", fontsize=8, fontweight="bold", color=INK)
    else:
        ax.text(x + w / 2, y - h_head / 2, name, ha="center", va="center", fontsize=8, fontweight="bold", color=INK)
    ax.plot([x, x + w], [y - h_head - h_attr, y - h_head - h_attr], color=ec, lw=1.0)
    for i, a in enumerate(attrs):
        ax.text(x + 0.8, y - h_head - 0.5 - (i + 0.5) * line, a, ha="left", va="center", fontsize=fs, color=INK, family="DejaVu Sans Mono")
    for i, m in enumerate(methods):
        ax.text(x + 0.8, y - h_head - h_attr - 0.5 - (i + 0.5) * line, m, ha="left", va="center", fontsize=fs, color=INK, family="DejaVu Sans Mono")
    return (x, y - h, w, h)


def poly(ax, pts, label=None, color=SLATE, lw=1.4, fs=7.2, lp=None, ls="-"):
    xs, ys = zip(*pts[:-1])
    ax.plot(list(xs) + [pts[-2][0]], list(ys) + [pts[-2][1]], color=color, lw=lw, ls=ls, solid_capstyle="butt")
    arrow(ax, pts[-2], pts[-1], None, color=color, lw=lw, ls=ls)
    if label:
        ax.text(lp[0], lp[1], label, fontsize=fs, color=color, ha="center", va="center", bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85))


def dfd0():
    fig, ax = canvas(11, 5.2, "Data flow diagram, level 0 (context)", ty=58)
    entity(ax, 2, 40, 17, 14, "Operator\n(dashboard user)")
    entity(ax, 2, 4, 17, 14, "LLM provider\n(optional, external)")
    process(ax, 50, 38, 15, "SafeGrid-AI\nsystem", "0", fs=10)
    store(ax, 74, 44, 24, 8, "runs, steps, events", "D1")
    store(ax, 74, 28, 24, 8, "hash-chained safety log", "D2")
    store(ax, 74, 12, 24, 8, "scenarios, limits", "D3")
    arrow(ax, (19, 50), (36.5, 43), "scenario, seed, provider,\nstart / stop / step,\ndry-run action", lp=(27.5, 52.8), fs=7.8)
    arrow(ax, (36.5, 33), (19, 42), "grid state, decisions, explanations,\nshield events, metrics (live)", lp=(27, 32.5), fs=7.8)
    arrow(ax, (39.5, 27.5), (19, 15), "structured context\n(per agent, per step)", lp=(21, 23.5), fs=7.8)
    arrow(ax, (19, 8), (45, 23.3), "proposed EnergyAction", lp=(36, 11.5), fs=7.8)
    arrow(ax, (63, 44), (74, 48), "run records", off=(0, 2.6), fs=7.8)
    arrow(ax, (64.8, 37), (74, 33), "safety events", off=(1.5, 3.2), fs=7.8)
    arrow(ax, (74, 17), (60, 28), "limits, scenarios", lp=(75, 23.5), fs=7.8)
    save(fig, "03_dfd_level0.png")


def dfd1():
    fig, ax = canvas(11, 6.6, "Data flow diagram, level 1", ty=78)
    entity(ax, 1.5, 58, 13, 12, "Operator")
    entity(ax, 1.5, 36, 13, 12, "LLM provider")
    entity(ax, 1.5, 11, 13, 12, "Operator")
    process(ax, 28, 64, 8.5, "Configure\nand control\nrun", "1.0", fs=7.4)
    process(ax, 50, 64, 8.5, "Generate\nscenario\ninputs", "2.0", fs=7.4)
    process(ax, 50, 42, 8.5, "Agents\nperceive and\npropose", "3.0", fs=7.4)
    process(ax, 72, 42, 8.5, "Coordinate\nand validate\n(shield)", "4.0", fs=7.4)
    process(ax, 72, 17, 8.5, "Execute:\npower flow,\nbattery state", "5.0", fs=7.4)
    process(ax, 34, 17, 8.5, "Log, explain,\npublish", "6.0", fs=7.4)
    store(ax, 70, 60, 29, 7, "scenarios, limits", "D3")
    store(ax, 22, 0, 24, 5, "run store (runs, steps)", "D1")
    store(ax, 82, 22, 17, 7, "safety log", "D2")
    arrow(ax, (14.5, 64), (19.5, 64), "commands", off=(0, 2.4), fs=7.2)
    arrow(ax, (36.5, 64), (41.5, 64), "config", off=(0, 2.4), fs=7.2)
    arrow(ax, (70, 63.5), (58.5, 64), "faults", off=(0, 2.4), fs=7.2)
    arrow(ax, (50, 55.5), (50, 50.5), "profiles", off=(4.5, 0), fs=7.2)
    arrow(ax, (41.5, 44), (14.5, 44), "context", off=(0, 1.8), fs=7.2, color=ORANGE)
    arrow(ax, (14.5, 40), (41.5, 40), "proposed action", off=(0, -1.9), fs=7.2, color=ORANGE)
    arrow(ax, (58.5, 42), (63.5, 42), None)
    ax.text(61, 44.2, "proposals", fontsize=7.2, color=SLATE, ha="center")
    arrow(ax, (83, 60), (76, 50.3), "limits", off=(4.0, 0), fs=7.2)
    arrow(ax, (72, 33.5), (72, 25.5), "validated\nactions", off=(5.2, 0), fs=7.2)
    arrow(ax, (63.5, 17), (42.5, 17), "grid result", off=(0, 2.4), fs=7.2)
    arrow(ax, (45.5, 35), (39, 25), "decisions", off=(-3.8, 0), fs=7.2)
    arrow(ax, (78, 35), (89, 29), "safety\nevents", off=(5, 1.5), fs=7.2, color=RED)
    arrow(ax, (25.5, 17), (14.5, 17), "live state,\nexplanations", off=(0, 4.4), fs=7.2)
    arrow(ax, (34, 8.5), (34, 5), "records", off=(4, 0), fs=7.2)
    save(fig, "04_dfd_level1.png")


def dfd2():
    fig, ax = canvas(11, 6.8, "Data flow diagram, level 2: process 4.0 (coordinate and validate)", ty=76)
    pts = [
        (16, 62, "4.1", "Order\nproposals\n(relief first)"),
        (40, 62, "4.2", "Structural\nchecks"),
        (64, 62, "4.3", "Trial power\nflow of the\nrequest"),
        (88, 62, "4.4", "Keep only new\nor worse\nviolations"),
        (88, 36, "4.5", "Any\nviolation?"),
        (64, 36, "4.6", "Bisection:\nlargest safe\nscale"),
        (40, 36, "4.7", "Re-verify the\nrounded\naction"),
        (16, 36, "4.8", "Approve,\nproject or\nreject"),
        (16, 10, "4.9", "Append\nhash-chained\nevent"),
    ]
    for cx, cy, num, t in pts:
        process(ax, cx, cy, 8.3, t, num, fs=7.2)
    for a, b in ((0, 1), (1, 2), (2, 3)):
        arrow(ax, (pts[a][0] + 8.3, pts[a][1]), (pts[b][0] - 8.3, pts[b][1]))
    arrow(ax, (88, 53.7), (88, 44.3))
    arrow(ax, (79.7, 36), (72.3, 36), "yes", off=(0, 2.0), fs=7.5)
    arrow(ax, (55.7, 36), (48.3, 36))
    arrow(ax, (31.7, 36), (24.3, 36))
    arrow(ax, (16, 27.7), (16, 18.3))
    poly(ax, [(82.1, 41.9), (82.1, 48.5), (21.9, 48.5), (21.9, 41.9)], "no violation: approve as requested", color=GREEN, fs=7.5, lp=(52, 48.5))
    store(ax, 40, 6.5, 26, 7, "D2 safety log", "")
    arrow(ax, (24.3, 10), (40, 10), "event", off=(0, 2.0), fs=7.5, color=RED)
    store(ax, 78, 8, 21, 7, "D3 limits", "")
    arrow(ax, (88, 15), (88, 27.7), None, ls="--")
    ax.text(50, 71.5, "Inputs: EnergyAction proposals from process 3.0 and the no-action grid state; outputs: validated actions to process 5.0.",
            ha="center", fontsize=8, color=SLATE, style="italic")
    save(fig, "05_dfd_level2.png")


def uml():
    fig, ax = canvas(12, 8.6, "UML class diagram (backend/app)", ty=106)
    svc = uml_class(ax, 1, 100, 22, "SimulationService", ["- engine", "- hub: ConnectionHub", "- store: Store"], ["+ start(config)", "+ stop()", "+ step_once()", "+ run_scenario(id)", "+ start_experiment()"])
    eng = uml_class(ax, 28, 100, 24, "SimulationEngine", ["- config: RunConfig", "- cfg: ConstraintConfig", "- sim: GridSimulator", "- shield, manager", "- safety_events[]"], ["+ step()", "+ preview()  (dry run)", "+ finish(status)", "- _validate_and_commit()", "- _record_safety()"])
    mgr = uml_class(ax, 57, 100, 21, "AgentManager", ["- agents: dict", "- provider"], ["+ perceive_all(obs)", "+ decide_all(ctx)", "+ by_node(id)"])
    agent = uml_class(ax, 82, 100, 17, "BaseAgent", ["+ agent_id, node_id", "+ provider", "+ last"], ["+ perceive(obs)", "+ decide(ctx)", "+ fallback_policy()", "+ remember(entry)", "(Prosumer, Storage,", " Renewable subclass)"])
    store_ = uml_class(ax, 1, 68, 22, "SQLiteStore", ["- _db", "- _lock"], ["+ create_run()", "+ add_safety_event()", "+ add_step()", "+ save_experiment()"], stereotype="Store")
    sim = uml_class(ax, 28, 68, 24, "GridSimulator", ["- net (pandapower)", "- nodes: NodeState"], ["+ apply_exogenous()", "+ trial(setpoints)", "+ commit(setpoints)", "+ snapshot()"], fc="#F3FBF7", ec=GREEN)
    shield = uml_class(ax, 57, 68, 21, "SymbolicSafetyShield", ["- cfg: ConstraintConfig"], ["+ evaluate(action, node,", "    trial, current, ...)", "- _decision(...)"], fc="#FFF7F6", ec=RED)
    prov = uml_class(ax, 82, 68, 17, "LLMProvider", ["+ name, source"], ["+ generate_action(ctx)", "+ describe()"], stereotype="abstract")
    cfg = uml_class(ax, 28, 44, 24, "ConstraintConfig", ["+ v_min, v_max", "+ line_max_loading_pct", "+ trafo_max_loading_pct", "+ node_limits: dict"], ["+ to_dict()"])
    dec = uml_class(ax, 57, 44, 21, "ShieldDecision", ["+ status", "+ requested_action", "+ validated_action", "+ violations, checks"], ["+ to_dict()"], stereotype="record")
    provs = uml_class(ax, 82, 44, 17, "Mock / Api / RuleBased\nFailing / FaultInjecting", ["+ name"], ["+ generate_action(ctx)"])
    ev = uml_class(ax, 57, 21, 21, "SafetyEvent", ["+ event_id, run_id, step", "+ prev_hash, hash"], ["+ create(...)", "+ payload", "(frozen dataclass)"], stereotype="record")
    act = uml_class(ax, 82, 22, 17, "EnergyAction", ["+ agent_id", "+ action_type", "+ power_kw", "+ duration_minutes", "+ reason_codes"], ["(pydantic, extra=forbid)"], stereotype="model")
    arrow(ax, (23, 96), (28, 96), "creates", off=(0, 1.5), fs=6.5)
    arrow(ax, (52, 96), (57, 96), "owns", off=(0, 1.5), fs=6.5)
    arrow(ax, (78, 96), (82, 96), "1..3", off=(0, 1.5), fs=6.5)
    arrow(ax, (12, 100 - 22.2), (12, 68), "uses", off=(2, 0), fs=6.5)
    arrow(ax, (40, 100 - 26.6), (40, 68), "owns", off=(2.2, 0), fs=6.5)
    arrow(ax, (50, 100 - 26.6), (60, 68), "owns", off=(-1.5, 1.2), fs=6.5)
    arrow(ax, (57, 61), (52, 61), "trial()", off=(0, 1.6), fs=6.5)
    arrow(ax, (90.5, 100 - 25), (90.5, 68), "has a", off=(2.2, 0), fs=6.5)
    arrow(ax, (90.5, 44), (90.5, 68 - 13.5), "implements", off=(3.5, 0), fs=6.5, ls="--")
    arrow(ax, (67.5, 68 - 14.4), (67.5, 44), "returns", off=(2.4, 0), fs=6.5)
    arrow(ax, (59, 68 - 14.4), (48, 44), "reads", off=(-1.5, -1.2), fs=6.5)
    arrow(ax, (67.5, 44 - 17.7), (67.5, 21), "logged as", off=(2.8, 0), fs=6.5)
    arrow(ax, (90.5, 44 - 11.9), (90.5, 22), "returns", off=(2.4, 0), fs=6.5)
    save(fig, "06_uml_class_diagram.png")


# ---------------------------------------------------------------- 07 sequence diagram
def sequence():
    fig, ax = canvas(12, 8.0, "Sequence diagram: one simulation step", ty=80)
    names = ["Dashboard", "FastAPI", "Simulation\nEngine", "Agent +\nLLM provider", "Coordinator", "Safety\nShield", "Grid\nSimulator", "SQLite +\nWebSocket"]
    xs = [6, 18, 30, 43, 55, 67, 79, 92]
    for x, n in zip(xs, names):
        box(ax, x - 5, 70, 10, 6, n, fc="#E8F0FC", ec=NAVY, fs=7.4, bold=True)
        ax.plot([x, x], [70, 12], color=LINE, lw=1.0, ls=(0, (4, 3)))
    msgs = [
        (0, 1, 66, "POST /simulation/step"),
        (1, 2, 63, "step()"),
        (2, 6, 60, "apply_exogenous(); trial({})  (no-action baseline)"),
        (2, 3, 56.5, "perceive_all(obs); decide_all(ctx)"),
        (3, 2, 53.5, "EnergyAction x 3 (or labelled fallback)"),
        (2, 4, 50, "detect_conflicts(); order_decisions()"),
        (2, 5, 46.5, "evaluate(action, node, trial_fn)"),
        (5, 6, 43, "trial(setpoints)   (several power flows)"),
        (6, 5, 40, "GridTrial: voltages, loadings"),
        (5, 2, 36.5, "ShieldDecision: approved / projected / rejected"),
        (2, 6, 32.5, "commit(validated setpoints)"),
        (2, 7, 28.5, "add_safety_event(); add_step()"),
        (2, 7, 25, "publish agent_action, safety_intervention, grid_update"),
        (2, 1, 20, "step record"),
        (1, 0, 16.5, "200 {step, summary}"),
    ]
    for a, b, y, t in msgs:
        xa, xb = xs[a], xs[b]
        arrow(ax, (xa, y), (xb, y), None, color=INK if a < b else SLATE, ls="-" if a < b else "--", lw=1.2)
        ax.text((xa + xb) / 2, y + 1.3, t, ha="center", va="bottom", fontsize=6.9, color=INK)
    ax.add_patch(Rectangle((64, 31), 33, 17.2, fc="none", ec=RED, lw=1.0, ls=(0, (3, 2))))
    ax.text(97.5, 47.3, "loop over\nagents", fontsize=6.5, color=RED, ha="right", va="top")
    save(fig, "07_sequence_diagram.png")


# ---------------------------------------------------------------- 08 use-case diagram
def usecase():
    fig, ax = canvas(10, 7.4, "Use-case diagram", ty=78)
    ax.add_patch(Rectangle((24, 4), 52, 70, fc="#FBFCFE", ec="#D5DCE6", lw=1.2))
    ax.text(50, 71.2, "SafeGrid-AI", ha="center", fontsize=10, fontweight="bold", color=SLATE)
    cases = [
        (50, 64, "Sign in (demo account)"),
        (50, 56.5, "Choose scenario, seed and agent brain"),
        (50, 49, "Start, step, stop or reset a run"),
        (50, 41.5, "Watch grid, agents and shield live"),
        (50, 34, "Inspect an agent decision and its explanation"),
        (50, 26.5, "Dry-run a custom action against the shield"),
        (50, 19, "Run a scenario to completion"),
        (50, 11.5, "Compare strategies over several seeds"),
    ]
    for cx, cy, t in cases:
        ax.add_patch(Ellipse((cx, cy), 42, 5.8, fc="#E8F0FC", ec=BLUE, lw=1.4))
        ax.text(cx, cy, t, ha="center", va="center", fontsize=7.8, color=INK)

    def actor(x, y, label):
        ax.add_patch(Circle((x, y + 8), 1.6, fc="white", ec=NAVY, lw=1.6))
        ax.plot([x, x], [y + 6.4, y + 2.5], color=NAVY, lw=1.6)
        ax.plot([x - 2.5, x + 2.5], [y + 5, y + 5], color=NAVY, lw=1.6)
        ax.plot([x, x - 2.2], [y + 2.5, y], color=NAVY, lw=1.6)
        ax.plot([x, x + 2.2], [y + 2.5, y], color=NAVY, lw=1.6)
        ax.text(x, y - 5.2, label, ha="center", fontsize=8.5, fontweight="bold", color=INK)

    actor(10, 38, "Operator")
    actor(91, 56, "LLM provider\n(optional)")
    actor(91, 20, "Scheduler\n(experiment job)")
    for cx, cy, t in cases[:8]:
        arrow(ax, (13, 44), (cx - 21, cy), None, head="-", lw=0.9, color=LINE)
    arrow(ax, (88.5, 62), (71, 49), None, head="-", lw=0.9, color=LINE)
    arrow(ax, (88.5, 28), (71, 11.5), None, head="-", lw=0.9, color=LINE)
    save(fig, "08_use_case_diagram.png")


# ---------------------------------------------------------------- 09 ER diagram
def er():
    fig, ax = canvas(11, 6.0, "Entity-relationship diagram (SQLite)", ty=62)

    def ent(x, y, w, name, cols):
        h = 4.2 + len(cols) * 2.8
        ax.add_patch(Rectangle((x, y - h), w, h, fc="white", ec=NAVY, lw=1.5))
        ax.add_patch(Rectangle((x, y - 4.2), w, 4.2, fc=NAVY, ec=NAVY))
        ax.text(x + w / 2, y - 2.1, name, ha="center", va="center", color="white", fontsize=9.5, fontweight="bold")
        for i, (c, t, k) in enumerate(cols):
            yy = y - 4.2 - (i + 0.5) * 2.8
            ax.text(x + 1.0, yy, (k + " " if k else "   ") + c, ha="left", va="center", fontsize=7.8, color=INK, fontweight="bold" if k == "PK" else "normal")
            ax.text(x + w - 1.0, yy, t, ha="right", va="center", fontsize=7.4, color=SLATE)
        return (x, y - h, w, h)

    runs = ent(36, 58, 28, "runs", [("run_id", "TEXT", "PK"), ("created_at", "TEXT", ""), ("finished_at", "TEXT", ""), ("status", "TEXT", ""), ("config", "JSON text", ""), ("resolved", "JSON text", ""), ("summary", "JSON text", ""), ("fingerprint", "TEXT", "")])
    ev = ent(1, 30, 28, "events", [("id", "INTEGER", "PK"), ("run_id", "TEXT", "FK"), ("step", "INTEGER", ""), ("event_type", "TEXT", ""), ("payload", "JSON text", "")])
    se = ent(36, 26, 28, "safety_events", [("id", "INTEGER", "PK"), ("run_id", "TEXT", "FK"), ("step", "INTEGER", ""), ("status", "TEXT", ""), ("payload", "JSON text (hash chain)", "")])
    st = ent(71, 30, 28, "steps", [("run_id", "TEXT", "PK,FK"), ("step", "INTEGER", "PK"), ("payload", "JSON text", "")])
    ex = ent(71, 58, 28, "experiments", [("exp_id", "TEXT", "PK"), ("created_at", "TEXT", ""), ("spec", "JSON text", ""), ("results", "JSON text", "")])
    arrow(ax, (36, 38), (29, 26), "1 : N", head="-", off=(-1, 3.2), fs=8, color=NAVY)
    arrow(ax, (50, 58 - 4.2 - 8 * 2.8), (50, 26), "1 : N", head="-", off=(3.5, 0), fs=8, color=NAVY)
    arrow(ax, (64, 38), (71, 26), "1 : N", head="-", off=(2.5, 3.2), fs=8, color=NAVY)
    ax.text(71, 13, "Indexes: ix_events_run(run_id, event_type),\nix_safety_run(run_id, status)", fontsize=7, color=SLATE, ha="left", va="top")
    ax.text(71, 4.5, "FK = logical reference to runs.run_id (no FOREIGN KEY\nconstraint is declared). experiments is independent: it\nstores the specification and results of a comparison job.", fontsize=7.2, color=SLATE, ha="left", va="top")
    save(fig, "09_er_diagram.png")


# ---------------------------------------------------------------- 10 core algorithm flowchart
def flowchart():
    fig, ax = canvas(8.6, 11.5, "Core algorithm: Symbolic Safety Shield evaluate()", ty=108)
    ax.set_ylim(-8, 110)

    def proc(cx, cy, w, h, t, fc="#E8F0FC", ec=BLUE, fs=8, tc=INK):
        box(ax, cx - w / 2, cy - h / 2, w, h, t, fc=fc, ec=ec, fs=fs, tc=tc)

    def dec(cx, cy, w, h, t, fs=7.6):
        ax.add_patch(Polygon([(cx - w / 2, cy), (cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2)], fc="#FFF8E5", ec=GOLD, lw=1.4))
        ax.text(cx, cy, t, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.15)

    X = 36
    proc(X, 102, 46, 5, "Start: EnergyAction + node + grid state", fc=NAVY, ec=NAVY, fs=8, tc="white")
    dec(X, 91, 40, 9.5, "Structural violations?\n(unknown agent / node, limits,\nreason codes, magnitude)")
    proc(X + 38, 91, 20, 5, "REJECT", fc="#FDE9E7", ec=RED, fs=8.5)
    dec(X, 78, 28, 7, "Idle or ~0 kW?")
    proc(X + 38, 78, 20, 5, "APPROVE", fc="#E6F6EF", ec=GREEN, fs=8.5)
    proc(X, 67.5, 46, 6, "Resolve setpoint; local checks (battery, SOC,\nnode limits, balance) vs no-action baseline")
    proc(X, 58.5, 46, 6, "Trial AC power flow of the request;\nkeep only NEW or WORSE violations")
    dec(X, 48, 28, 7, "Any violation?")
    proc(X + 38, 48, 20, 5, "APPROVE", fc="#E6F6EF", ec=GREEN, fs=8.5)
    proc(X, 37, 46, 6, "Bisection: largest scale lambda in [0, 1]\n(40 iterations local, 14 iterations power flow)")
    proc(X, 28, 46, 6, "Round down; re-verify the exact action\n(up to 4 attempts, lambda x 0.999)")
    dec(X, 17.5, 38, 9.5, "Safe and >= 0.05 kW and\ncorrect direction?")
    proc(X + 38, 17.5, 20, 5, "REJECT", fc="#FDE9E7", ec=RED, fs=8.5)
    proc(X, 6.5, 34, 5, "PROJECT: execute scaled action", fc="#FFF1EA", ec=ORANGE, fs=8.5)
    proc(X, -3, 50, 5, "Append hash-chained safety event; return ShieldDecision", fc=NAVY, ec=NAVY, fs=7.6, tc="white")
    arrow(ax, (X, 99.5), (X, 95.8))
    arrow(ax, (X, 86.2), (X, 81.5), "no", off=(2, 0), fs=7.5)
    arrow(ax, (X + 20, 91), (X + 28, 91), "yes", off=(0, 1.8), fs=7.5)
    arrow(ax, (X, 74.5), (X, 70.6), "no", off=(2, 0), fs=7.5)
    arrow(ax, (X + 14, 78), (X + 28, 78), "yes", off=(0, 1.8), fs=7.5)
    arrow(ax, (X, 64.5), (X, 61.6))
    arrow(ax, (X, 55.5), (X, 51.5))
    arrow(ax, (X + 14, 48), (X + 28, 48), "no", off=(0, 1.8), fs=7.5)
    arrow(ax, (X, 44.5), (X, 40.1), "yes", off=(2, 0), fs=7.5)
    arrow(ax, (X, 34), (X, 31.1))
    arrow(ax, (X, 25), (X, 22.3))
    arrow(ax, (X + 19, 17.5), (X + 28, 17.5), "no", off=(0, 1.8), fs=7.5)
    arrow(ax, (X, 12.7), (X, 9.1), "yes", off=(2, 0), fs=7.5)
    arrow(ax, (X, 4), (X, -0.5))
    xr = X + 50
    for yy in (91, 78, 48, 17.5):
        ax.plot([X + 48, xr], [yy, yy], color=SLATE, lw=1.0, ls=":")
    ax.plot([xr, xr], [91, -3], color=SLATE, lw=1.0, ls=":")
    arrow(ax, (xr, -3), (X + 25, -3), None, color=SLATE, lw=1.0, ls=":")
    save(fig, "10_core_algorithm_flowchart.png")


# ---------------------------------------------------------------- 11 feeder topology
def feeder():
    fig, ax = canvas(11, 5.0, "Simulated low-voltage feeder (pandapower network)", ty=50)
    hv = box(ax, 2, 33, 12, 8, "HV grid\n20 kV\n(external grid)", fc="#EFEBFC", ec=PURPLE, fs=8)
    t0 = box(ax, 20, 33, 13, 8, "Transformer T0\n0.25 MVA\n20 / 0.4 kV", fc="#FFF1EA", ec=ORANGE, fs=8)
    for x, y, nm in ((38, 37, "B0"), (56, 37, "B1"), (82, 37, "B3"), (56, 14, "B2")):
        ax.add_patch(Circle((x, y), 2.2, fc=NAVY, ec=NAVY))
        ax.text(x, y - 4.6, nm, ha="center", fontsize=9, fontweight="bold", color=INK)
    arrow(ax, (14, 37), (20, 37), head="-")
    arrow(ax, (33, 37), (35.8, 37), head="-")
    ax.plot([40.2, 53.8], [37, 37], color=SLATE, lw=2.2)
    ax.text(47, 39.2, "L0_1  0.30 km", ha="center", fontsize=8, color=SLATE)
    ax.plot([58.2, 79.8], [37, 37], color=SLATE, lw=2.2)
    ax.text(69, 39.2, "L1_3  0.45 km", ha="center", fontsize=8, color=SLATE)
    ax.plot([38, 38, 53.8], [34.8, 14, 14], color=SLATE, lw=2.2)
    ax.text(45, 16.2, "L0_2  0.25 km", ha="center", fontsize=8, color=SLATE)
    box(ax, 47, 24, 18, 7.5, "node_1: prosumer_01\n6 kWp PV, 10 kWh battery,\nhousehold load", fc="#E8F0FC", ec=BLUE, fs=7.2)
    ax.plot([56, 56], [31.5, 34.8], color=BLUE, lw=1.6)
    box(ax, 66, 6, 22, 9, "node_2: ev_01 (at B2)\n40 kWh EV battery,\n7.4 kW, charge only", fc="#E8F0FC", ec=BLUE, fs=7.2)
    ax.plot([58.2, 66], [14, 10.5], color=BLUE, lw=1.6)
    box(ax, 72, 24, 26, 8.5, "node_3: renewable_01 (at B3)\n20 kWp PV, 30 kWh battery", fc="#E8F0FC", ec=BLUE, fs=7.2)
    ax.plot([82, 82], [32.5, 34.8], color=BLUE, lw=1.6)
    ax.text(50, 3.2, "Line type NAYY 4x50 SE; load power factor 0.95; limits: 0.95-1.05 pu, 100 % line and transformer loading, 200 kW import/export.",
            ha="center", fontsize=8, color=SLATE, style="italic")
    save(fig, "11_feeder_topology.png")


# ---------------------------------------------------------------- 12 hash chain
def hashchain():
    fig, ax = canvas(11, 3.4, "Hash-chained safety log", ty=33)
    for i in range(4):
        x = 2 + i * 24.5
        box(ax, x, 8, 21, 17, "", fc="white", ec=NAVY, lw=1.5)
        ax.add_patch(Rectangle((x, 21), 21, 4, fc=NAVY, ec=NAVY))
        ax.text(x + 10.5, 23, f"event {i + 1}" if i < 3 else "event n", ha="center", va="center", color="white", fontsize=8.5, fontweight="bold")
        ax.text(x + 1, 17, "prev_hash = hash of the\nprevious event" if i else "prev_hash = 000...0\n(genesis)", fontsize=6.8, va="center", color=INK)
        ax.text(x + 1, 11.2, "hash = SHA-256(prev_hash +\n[id, run, step, time] + payload)", fontsize=6.4, va="center", color=INK)
        if i < 3:
            arrow(ax, (x + 21, 14), (x + 24.5, 14), color=RED)
    ax.text(50, 3, "verify_chain() recomputes every hash; changing, removing or reordering any event breaks all later links.", ha="center", fontsize=8, color=SLATE, style="italic")
    save(fig, "12_hash_chain.png")


if __name__ == "__main__":
    for fn in (architecture, workflow, dfd0, dfd1, dfd2, uml, sequence, usecase, er, flowchart, feeder, hashchain):
        fn()
