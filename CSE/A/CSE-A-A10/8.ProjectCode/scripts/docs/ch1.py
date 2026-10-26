"""Chapter 1: Introduction."""

from . import facts as F
from .blocks import B, FIG, H1, H2, N, P, TAB
from . import lit
from .refs import CITE as R


def trim(blocks, drop=(), drop_sections=(), replace=None, table_rows=None):
    """Report-mode trimming helper (kept for the other chapter modules). drop: block-text prefixes to remove; drop_sections: heading
    prefixes whose whole section is removed; replace: {prefix: block}; table_rows: {caption prefix: keep(row)}."""
    replace = replace or {}
    table_rows = table_rows or {}
    out, skip_level = [], None
    for b in blocks:
        if b[0] in ("h1", "h2", "h3"):
            lvl = int(b[0][1])
            if skip_level is not None and lvl <= skip_level:
                skip_level = None
            if skip_level is None and any(b[1].startswith(x) for x in drop_sections):
                skip_level = lvl
        if skip_level is not None:
            continue
        v = b[1]
        k = v[0] if isinstance(v, list) and v else (v if isinstance(v, str) else "")
        if any(k.startswith(x) for x in drop):
            continue
        hit = next((x for x in replace if k.startswith(x)), None)
        if hit:
            if replace[hit] is not None:
                out.append(replace[hit])
            continue
        if b[0] == "tab":
            cap = next((x for x in table_rows if b[1].startswith(x)), None)
            if cap:
                b = ("tab", b[1], b[2], [r for r in b[3] if table_rows[cap](r)], b[4], b[5], b[6])
        out.append(b)
    return out


def blocks():
    a2 = F.gm("2x2", "advanced", "Avg delay / vehicle (s)")
    f2 = F.gm("2x2", "fixed", "Avg delay / vehicle (s)")
    e2a, e2f = F.gm("2x2", "advanced", "Emergency delay (s)"), F.gm("2x2", "fixed", "Emergency delay (s)")
    d2, d3 = F.derived("2x2"), F.derived("3x3")
    base = R["base"]
    out = [
        H1("CHAPTER 1: INTRODUCTION"),
        H2("1.1 Domain Overview"),
        P("Road traffic is a network problem. Vehicles travel along links, wait in queues at junctions, and are released by traffic signals that decide, second by second, which "
          "approach may move. The field that studies how to make that decision well is called intelligent transportation systems, and its tools have changed in step with "
          "computing: electromechanical timers gave way to fixed-time plans computed from survey counts [" + str(R["webster"]) + "], these gave way to actuated and pressure-based "
          "controllers that react to detected queues [" + str(R["varaiya"]) + "], and in the last decade to learned controllers and camera-based sensing [" + str(R["intellilight"]) + "], "
          "[" + str(R["yolo"]) + "]. This project sits in the last group. It is an artificial-intelligence application in which computer vision measures the traffic, "
          "machine learning anticipates it, and a control rule turns both into signal timing."),
        P("Three pieces of technology make such a system practical today. Single-stage object detectors of the YOLO family [" + str(R["yolo"]) + "], [" + str(R["ultralytics"]) + "] count "
          "and classify vehicles in one pass over an image, fast enough to run on an ordinary computer. Gradient-boosted trees [" + str(R["gbm"]) + "] learn non-linear relations in "
          "tabular features such as queue lengths and arrival counts with little tuning. And simulation allows a controller to be tried on thousands of simulated minutes of "
          "traffic before a single signal is touched [" + str(R["sumo"]) + "]. FlowSense uses all three."),
        P("Terms used throughout: a **phase** is a set of movements that may go together (FlowSense uses two, north-south and east-west); **saturation flow** is the discharge rate of a queue on green "
          "(0.5 vehicles per second per lane); a **passenger-car unit (PCU)** expresses a bus or truck as a number of cars of road space (bus 3, truck 2, bike 0.5); **delay** is time spent waiting in a queue; "
          "and **pre-emption** is the temporary override of a signal plan for an emergency vehicle."),
    H2("1.2 Background and Motivation"),
        P("Congestion costs time, fuel and air quality in every growing city. A fixed-time signal repeats the same cycle all day: it gives green to an approach that is empty "
          "and red to one with a queue, because the plan was computed for an average that no particular minute resembles. Cameras are already installed at many major junctions, "
          "but their footage is rarely used to drive the signals. When a camera can count the vehicles on each approach, the green time can follow the demand, and when it can "
          "recognise an emergency vehicle, that approach can be cleared before the vehicle arrives."),
        P("Emergency vehicles make the case sharper. An ambulance in a queue at a red signal has no way to ask for green unless the junction is equipped for pre-emption. "
          "Published schemes rely on GPS, RFID or connected-vehicle links [" + str(R["sasikala"]) + "], [" + str(R["zlatkovic"]) + "], which need equipment on every vehicle and every "
          "junction, or on audio siren recognition [" + str(R["giordano"]) + "], [" + str(R["jayakumar"]) + "], which suffers urban noise and cannot say where the siren is. "
          f"The base paper of this project [{base}] takes a third route: detect the roof light-bar itself with a YOLO detector and let that detection trigger a priority override "
          "on top of an optimised signal controller, validated in the SUMO simulator on one roundabout."),
        P("A single junction is also not the whole problem. If one junction discharges a long queue quickly, the vehicles arrive at the next junction as a platoon; if that junction "
          "is already full the platoon spills back and blocks the first. The batch's abstract therefore asks for four capabilities in one system: dynamic signal control from "
          "measured density, emergency-vehicle priority, congestion prediction, and coordination between neighbouring junctions, plus detection of violations such as red-light jumping. "
          "The surveyed literature (Chapter 2) addresses these separately; building them into one working product, and measuring each honestly, is the motivation for FlowSense."),
        P("Control logic for a signalised network cannot be trialled on a live road, so the route is simulation: running every controller on exactly the same seeded traffic is the only fair way to compare them. "
          "FlowSense therefore builds the simulator first and treats every claim as a measurement on that shared traffic."),
        H2("1.3 Problem Statement"),
        P("Fixed signal timings waste green time on empty approaches while queues build on others. Manual traffic control cannot scale to the number of junctions in a modern city. "
          "Emergency vehicles lose critical minutes waiting at signals with no priority mechanism. Junctions operate independently, so clearing one simply moves the queue to the next."),
        P("**The problem addressed in this report** is to design, build and evaluate a vision-based controller that measures real traffic density, adapts signal timing, gives emergency "
          "vehicles priority and coordinates adjacent junctions, and to state how much of each claimed benefit survives a measurement made on identical traffic and on real photographs."),
        P("The problem is broken into five research questions that the later chapters answer with measurements:"),
        N("How much of the improvement over fixed-time signals comes from adaptivity alone, and how much from forecasting, junction coordination and emergency priority?",
          "What does emergency pre-emption cost the rest of the traffic?",
          "Does a 30-second machine-learning queue forecast help when it is used inside the controller, and does it generalise beyond the simulation runs it was trained on?",
          "Does a vision rule that works on generated scenes also work on real photographs of traffic and of ambulances?",
          "Can the whole pipeline run interactively on an ordinary CPU-only PC?"),
        H2("1.4 Need for the Project"),
        B("**Adaptive timing is the largest single gain.** A controller that follows the queue instead of a clock is the baseline any smart-traffic claim has to beat; the project "
          "measures that baseline rather than assuming it.",
          "**Emergency priority has a price.** Pre-emption helps the ambulance and can hurt other traffic; the size of that price has to be measured on the same demand for every controller.",
          "**Components are rarely evaluated together.** Detection, forecasting, priority and coordination are usually published as separate studies; a combined product exposes how they interact.",
          "**Synthetic success is not real success.** A detector tested only on scenes the authors generated can look near-perfect; the same rule must also be tried on real photographs.",
          "**Operators need a console, not a script.** A control room needs to see the map, the queues, the forecast and the alerts in one place, which is why the project ships a web application."),
        H2("1.5 Objectives"),
        P("The objectives come from two batch documents: the six objectives of the batch objectives sheet and the eight in the project documentary. The table below lists the six and records "
          "where each stands at the end of the project; the eight documentary objectives are met as noted in the paragraph below the table."),
        TAB("Objectives of the batch objectives sheet and their status", ["No.", "Objective", "Status at the end of the project"],
            [["1", lit.OBJECTIVES[0], "Partly met: YOLOv8n (COCO weights, not fine-tuned) runs on still frames and uploads; no live video stream"],
             ["2", lit.OBJECTIVES[1], "Met: density in passenger-car units from detections (vision page) and from queues (simulator)"],
             ["3", lit.OBJECTIVES[2], f"Met in the simulator: delay {d2['delay_cut_advanced_vs_fixed_pct']:.1f} % below fixed-time on a 2x2 grid"],
             ["4", lit.OBJECTIVES[3], f"Met in the simulator (ambulance delay {e2a[0]:.1f} s vs {e2f[0]:.1f} s); the light-bar rule failed on real ambulance photos"],
             ["5", lit.OBJECTIVES[4], f"Met as look-ahead and spill-back avoidance; gain over plain adaptive control only {d2['delay_cut_advanced_vs_adaptive_pct']:.1f} %"],
             ["6", lit.OBJECTIVES[5], "Met with stated limits: five-seed simulator study, real-image tests, 38 unit and API tests"]],
            widths=[0.5, 2.7, 3.1], align=["c", "l", "l"], size=10),
        P("Of the eight documentary objectives, the first (YOLOv8 detection), second (dynamic timing), third (emergency priority), fourth (congestion prediction with machine learning), "
          "fifth (coordination between junctions) and seventh (less waiting time, congestion and fuel) are implemented and measured in the simulator. The sixth (red-light and "
          "wrong-way detection) is implemented as a logged event stream generated by the simulator, not as a trained detector. The eighth (road safety and efficiency) is addressed "
          "only through the measured delay and ambulance-delay results; no safety outcome such as collisions is measured."),
        H2("1.6 Scope"),
        P("The system covers a signalised network of two-phase junctions (north-south and east-west green) in a 2x2 or 3x3 grid, with cars, bikes, buses and trucks, one ambulance "
          "class, red-light runners and wrong-way drivers. Four controllers run on identical seeded demand. A vision page applies YOLOv8n to uploaded images and a classical detector to "
          "synthetic overhead scenes; a prediction page shows a queue forecaster; a violations page shows the event log; a FastAPI service and a React console tie them together. "
          "Chapters 5 and 6 give the design and implementation."),
        P("Out of scope are real camera streams, hardware signal controllers, SUMO or CARLA validation, a trained light-bar detector, a trained violation detector, number-plate reading, "
          "turn-phase (protected left-turn) signal plans, pedestrians, and any database. Section 1.8 and Chapter 9 return to these."),
        H2("1.7 Contributions"),
        N("A working end-to-end product that joins vehicle detection, density estimation, queue forecasting, adaptive control, emergency pre-emption, inter-junction look-ahead and a violation log behind one API and one web console.",
          "A seeded simulator that runs four controllers on identical demand, so every comparison is like-for-like, together with a reproducible experiment script that writes every reported number to a JSON file.",
          f"An advanced controller that combines PCU-weighted pressure, a 30-second machine-learning queue forecast, platoon look-ahead, spill-back damping and an emergency green wave; it lowers average delay by {d2['delay_cut_advanced_vs_fixed_pct']:.1f} % against fixed-time signals on a 2x2 grid.",
          "A measured trade-off of emergency pre-emption: an ablation showing that removing pre-emption gives the lowest network delay but a much longer ambulance delay.",
          "A validity check of the forecaster and the vision layer beyond the default split: leave-one-simulation-out validation of the forecaster, and evaluation of YOLOv8n and the light-bar rule on two public real-image sets.",
          "An honest account of what does not work, including the failure of the colour-based light-bar rule on real ambulance photographs and the simulator's reliance on ground-truth emergency knowledge."),
        P(f"The headline measurements are these. On a 2x2 grid over five seeds the advanced controller averages {a2[0]:.1f} s of delay per vehicle against {f2[0]:.1f} s for fixed-time signals. "
          f"Its advantage over plain queue-actuated control is only {d2['delay_cut_advanced_vs_adaptive_pct']:.1f} %, within one standard deviation, and the base-paper-style controller "
          f"has a higher mean delay than plain adaptive control ({-d2['delay_cut_basepaper_vs_adaptive_pct']:.1f} % higher on 2x2, {-d3['delay_cut_basepaper_vs_adaptive_pct']:.1f} % on 3x3). "
          "These figures are examined in Chapter 8."),
        P(f"Against the base paper [{base}] the contribution is breadth (forecasting, coordination, violations and a working console) and a candid measurement of each part, not a better emergency detector: "
          "the paper's trained detector (precision 0.73, recall 0.69) is the stronger evidence for that."),
        H2("1.8 Limitations and Assumptions"),
        B("**The simulator is not SUMO.** Demand, saturation flow (0.5 vehicles per second per lane), link time (12 s) and capacity (30 vehicles per approach) are the project's own assumptions, "
          "so absolute delays cannot be compared with the base paper's roundabout results.",
          "**Emergency vehicles are known by ground truth to the simulated controllers.** The vision module is not in the control loop, and inter-junction \"communication\" is look-ahead on the transit queue, not a network protocol.",
          "**Violations are simulated events.** A plate string and a confidence between 0.86 and 0.99 are attached to each event by the simulator; no model detects them.",
          "**No light-bar detector was trained.** The emergency rule is a colour threshold in HSV space and failed on real ambulance photographs.",
          "**The forecaster is trained on six simulated runs** and does not extrapolate to heavier congestion than it has seen.",
          "**Single demo operator, no database, CPU only.** The console has one demo login; state is held in memory; everything was measured on an Intel Core i5-12500 with no GPU.",
          "**Assumed:** two-phase signals, Poisson arrivals shaped by a morning and an evening peak, a fixed vehicle mix (68 % cars, 13 % bikes, 6 % buses, 13 % trucks), and an idling fuel rate of 0.6 litres per hour per queued vehicle."),
        H2("1.9 Organisation of the Report"),
        P("**Chapter 2** surveys the literature, analyses the base paper in depth and states the research gap. **Chapter 3** studies the technical, economic, operational and schedule feasibility. "
          "**Chapter 4** sets out the existing and proposed systems and the requirements. **Chapter 5** presents the design: architecture, workflow, data-flow diagrams, UML, the logical data model, "
          "modules and screens. **Chapter 6** describes the methodology and implementation, including the algorithms, the equations, the API and installation. **Chapter 7** reports the testing. "
          "**Chapter 8** presents the results and output screens, the comparison with the base paper and the objectives against outcomes. **Chapter 9** concludes and **Chapter 10** gives the future scope. "
          "The references and three appendices (important code, installation and user guide, additional screens) follow."),
    ]
    return out
