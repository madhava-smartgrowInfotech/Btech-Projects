"""Chapter 1: Introduction (SentinelFlow, CSE-C-C15)."""

from . import facts as F
from . import lit
from .blocks import B, FIG, H1, H2, N, P, TAB
from .refs import CITE as R


def K():
    return F.K()


def blocks():
    k = K()
    W = F.WIN
    risk07 = [W[w]["distributed_risk_ge_0.7_only"]["recall"] for w in ("window_2s", "window_5s", "window_10s")]
    return [
        H1("1. INTRODUCTION"),
        H2("1.1 Domain and Background"),
        P("A distributed denial-of-service (DDoS) attack makes a network service unavailable by flooding it with traffic from many sources at once. Because the traffic comes from many "
          f"compromised or rented machines, it cannot be stopped by blocking a single address, and the taxonomy of Mirkovic and Reiher [{R['mirkovic']}] already distinguished the many ways in which "
          "such floods can be built and defended against. The base paper of this project describes DDoS as one of the most prevalent and destructive threats to network operators and points to "
          f"incidents with multi-terabit floods and low-rate, stealthy patterns that evade conventional detection [{R['base']}]."),
        P("Two developments make the problem harder for the owner of a small network. First, a growing number of connected devices gives attackers more machines to recruit. Second, newer attack styles do not "
          f"aim at one victim: a *carpet-bombing* attack spreads traffic over many destinations in the same network, so that each individual flow looks small and legitimate while the sum degrades the whole network [{R['carpet']}]. "
          "A detector that only watches the busiest flow or the busiest destination can miss it."),
        P("The usual defence has two halves. Detection decides that traffic is hostile; mitigation then acts on that decision, for example by rate limiting or blocking the offending sources. This project "
          f"builds both halves in one working product, **{F.PRODUCT}**, that runs on an ordinary computer: a classifier trained on labelled flow data decides, window by window, whether traffic is benign or an attack, "
          "an explainable rule layer assesses how distributed the traffic is and how severe the situation is, and a mitigation manager quarantines the worst sources for a limited time and lets them recover."),
        FIG(F.diag("01_system_architecture.png"), "System architecture of SentinelFlow: browser tier, Flask API, pipeline modules and local files.", 5.6),
        P("The figure above gives the overall picture. The browser tier is a React console; the Flask application owns the shared inference function; the pipeline modules capture or simulate packets, classify, assess and act; "
          "SQLite and a few files hold the state. Chapter 5 explains each tier."),
        H2("1.2 Motivation"),
        P("The motivation comes from three observations in the batch survey and the base paper."),
        B("**Signature-based defences miss new or modified patterns.** A classifier that learns from flow features can generalise to variants that no signature describes, provided the training data is representative.",
          "**Detection without action leaves the service down.** The batch survey names the gap as closing the loop from real-time detection to automatic, adaptive mitigation with measured response latency. "
          f"The base paper itself lists sidecar operation, throttling or blackholing of suspicious flows and live testbeds as future work [{R['base']}].",
          "**A false positive is itself a denial of service.** Quarantining a legitimate source because the detector was wrong harms exactly the users the system is supposed to protect, so the false-positive rate has to be measured at the point where an action is taken, not only at the classifier."),
        P("A fourth, practical motivation emerged while documenting the work: reported accuracies of 99 to 100 % are common in the literature [" + f"{R['base']}], [{R['alduailij']}], [{R['becerra']}" + "], "
          f"but they come from offline evaluations on one dataset at a time, and the audit of CICIDS2017 by Engelen et al. [{R['engelen']}] and the critique of Sommer and Paxson [{R['sommer']}] both warn that such numbers "
          "do not guarantee real-world performance. A student project that reports its own numbers has to show where its model stands on real data, and that is done in Chapter 8."),
        H2("1.3 Problem Statement"),
        P("The batch problem statement lists four weaknesses of current practice:"),
        B(*lit.PROBLEM_STATEMENT),
        P(f"The need that follows is stated in the batch document as: *{lit.NEED[0].lower() + lit.NEED[1:]}*"),
        H2("1.4 Need for the Proposed System"),
        P("Existing open-source intrusion detection tools are built for network engineers: they need a dedicated sensor, rule sets and expertise. Research prototypes, including the base paper, evaluate a classifier on a "
          "stored dataset and stop there. A small organisation, a laboratory or a student team needs something between the two: a self-contained program that watches a network interface, tells an administrator in plain "
          "words why a window of traffic is considered an attack, takes a limited and reversible action, and keeps a history that can be inspected afterwards. Such a program also has to be safe to demonstrate, which is why "
          "SentinelFlow includes a Simulation Mode that exercises the whole pipeline without sending or capturing a single real packet."),
        H2("1.5 Overview of the Proposed Solution"),
        P("SentinelFlow treats time as a sequence of monitoring windows (ten seconds by default, two to 120 seconds allowed). For every finished window the system performs the same six steps, whether the packets "
          "came from the network card or from the simulator:"),
        N("**Aggregate.** Packets are reduced to ten features (packet and byte counts, per-second rates and average packet sizes, each for the received and the sent direction) plus context that the classifier does not see: the number of distinct sources and destinations, the protocol mix and the busiest addresses.",
          "**Classify.** A 200-tree Random Forest returns Benign or Attack and a confidence.",
          "**Assess distribution.** A weighted rule score between 0 and 1 expresses how widely the traffic is spread over sources and destinations, how high the packet rate is and how far it deviates from the average of the last twelve windows.",
          "**Grade severity.** A transparent score combines the label, the confidence, the packet rate, the distribution score, the spread and the number of consecutive suspicious windows into Low, Medium, High or Critical, and records every factor that contributed.",
          "**Act.** High and Critical windows quarantine the three busiest sources that are not protected local addresses for 40 seconds (80 for Critical); Medium recommends rate limiting; Low only keeps monitoring. Quarantines expire by themselves and are then marked as recovered.",
          "**Record and show.** The detection, with its full explanation, and each quarantine are stored in SQLite and appear on the console, which polls the API every two seconds."),
        P("The same ten-feature schema is used for training: columns of a CICIDS2017 flow record are mapped to it (forward packets and bytes become *sent*, backward become *received*, rates are counts divided by the flow duration). "
          "That sharing is what allows a classifier trained on flow rows to be applied to live windows, and it is also the source of the flow-to-window scale problem measured in Chapter 8."),
        H2("1.6 Objectives"),
        P("The six objectives of the batch are reproduced in Table 1.1 together with the chapter that reports how far each was reached."),
        TAB("Project objectives and where they are addressed", ["No.", "Objective", "Addressed in"],
            [["1", lit.OBJECTIVES[0], "Chapters 6 and 8"], ["2", lit.OBJECTIVES[1], "Chapters 6 and 7"],
             ["3", lit.OBJECTIVES[2], "Chapters 6 and 8"], ["4", lit.OBJECTIVES[3], "Chapters 5, 6 and 8"],
             ["5", lit.OBJECTIVES[4], "Chapters 5 and 8"], ["6", lit.OBJECTIVES[5], "Chapters 7 and 8"]],
            widths=[0.5, 4.2, 1.7], align=["c", "l", "l"], size=10.5),
        H2("1.7 Scope"),
        P("**In scope.** Binary classification of traffic windows as benign or attack with a Random Forest on ten flow features; capture with Scapy and a safe software simulator; "
          "an explainable distributed-risk and severity layer; temporary application-level quarantine with automatic recovery; a SQLite history of detections, mitigations and host health; a REST API with twelve endpoints; "
          "a nine-page React console; offline training from CICIDS2017 CSV files; automated tests; and a measured evaluation on synthetic and real data."),
        P("**Out of scope.** Changing the operating-system firewall or any router or switch; software-defined-network controller integration; multi-class attack identification; encrypted-traffic payload analysis; "
          "user registration, password reset, role-based access and report export (listed as user stories US-101 to US-103 and US-119 in the batch backlog but not built); and any claim about performance under a real production attack."),
        H2("1.8 Contributions"),
        N(f"A working closed loop from traffic window to stored detection to temporary quarantine to automatic recovery, on a commodity host, with the decision latency measured (Chapter 8).",
          "A transparent distributed-risk score (source diversity, destination diversity, packet-rate pressure and deviation from a rolling baseline) aimed at carpet-bombing patterns. "
          f"Measured on its own it is a precise but weak detector (recall {min(risk07) * 100:.0f} to {max(risk07) * 100:.0f} % at the 0.7 threshold, no false positives), so it is used as one input of the severity score.",
          f"An explainable severity engine that lists its contributing factors. At 5-second windows it reduces the false-positive rate on benign windows from {k['w5_fpr_ml'] * 100:.1f} % (Random Forest label alone) to {k['w5_fpr_act'] * 100:.2f} % (High or Critical severity).",
          "A Simulation Mode that drives the identical inference pipeline without network access, always labelled as simulated in the interface.",
          f"A shared ten-feature schema for flow rows and monitoring windows, and a measured finding about it: the forest shipped with the product was trained on synthetic data and scores {k['shipreal_acc'] * 100:.1f} % accuracy on {k['real_rows']:,} real CICIDS2017 DDoS-day flows, "
          f"while the same forest retrained on those flows reaches {k['rr_acc'][0] * 100:.2f} % (five seeds)."),
        H2("1.9 Limitations and Assumptions"),
        P("The limitations are stated here once and measured in detail in Chapters 7 and 8."),
        B(f"The shipped model was trained on a labelled synthetic fallback because CICIDS2017 could not be downloaded when the product was built; its {k['ship_acc'] * 100:.2f} % accuracy is measured on a held-out split of that synthetic data.",
          "Mitigation is an application-level denylist. `apply_os_firewall_block()` is a stub that returns `applied: false`; no packet is dropped by the operating system, and rate limiting is only recommended.",
          "Live capture needs Npcap and Administrator rights. Npcap is not installed on the machine used for this report, so only the error path of live capture was exercised; Simulation Mode drives the same pipeline.",
          f"The model was calibrated on 10-second windows. At shorter windows the Random Forest label alone raises many false alarms ({k['w2_fpr_ml'] * 100:.1f} % at 2 s and {k['w5_fpr_ml'] * 100:.1f} % at 5 s on benign windows).",
          "The REST API has no authentication; the console login is a browser-side demonstration gate. Both servers bind to 127.0.0.1."),
        P("The work rests on four assumptions: the forward direction of a CICIDS2017 flow corresponds to *sent* traffic and the backward direction to *received* traffic; local interface addresses define inbound and outbound orientation for live windows; "
          "a quarantine of 40 seconds (doubled for Critical) is long enough to demonstrate recovery; and a ten-second window is long enough to aggregate meaningful rates yet short enough to react."),
        H2("1.10 Organisation of the Report"),
        P("Chapter 2 surveys the base paper and related work and states the research gap. Chapter 3 studies the technical, economic, operational and schedule feasibility. Chapter 4 analyses the existing and proposed systems and lists the requirements. "
          "Chapter 5 presents the design: architecture, workflow, data flow diagrams, UML diagrams, database and user interface. Chapter 6 describes the methodology and implementation: data, preprocessing, algorithm, formulation, API, security and installation. "
          "Chapter 7 reports testing and its limits, and Chapter 8 the results with every output screen, the comparison with the base paper and objectives against outcomes. Chapter 9 concludes, Chapter 10 gives the future scope, "
          "and the report ends with the references and three appendices (important code, installation and user guide, additional screens)."),
    ]
