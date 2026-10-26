"""Text of 19.IEEE_Paper.docx (FlowSense). Every number is read from facts.py (experiments/**/metrics.json) or typed from docs/REPORT_FACTS.md.

Citations are written {r:N} with the global reference numbers of refs.py; Paper.expand renumbers them in order of first appearance.
"""
from . import facts as F
from . import paper_figs
from .paper import Paper
from .refs import CITE


def c(*keys):
    return "{r:" + ",".join(str(CITE[k]) for k in keys) + "}"


def build(path):
    figs = paper_figs.make()
    P = Paper()
    f1, f2, f3 = F.f1, F.f2, F.f3
    D = "Avg delay / vehicle (s)"
    E = "Emergency delay (s)"
    d2, d3 = F.derived("2x2"), F.derived("3x3")
    g = F.gm
    fx2, ad2, em2, av2 = (g("2x2", k, D) for k in F.CTRL_KEYS)
    fx3, ad3, em3, av3 = (g("3x3", k, D) for k in F.CTRL_KEYS)
    efx2, ead2, eem2, eav2 = (g("2x2", k, E) for k in F.CTRL_KEYS)
    efx3, ead3, eem3, eav3 = (g("3x3", k, E) for k in F.CTRL_KEYS)
    ab = F.AB["results"]
    abd = {k: v[D]["mean"] for k, v in ab.items()}
    abe = {k: v[E]["mean"] for k, v in ab.items()}
    sw = F.SW["series"]
    emh = F.EM["results"]
    pr = F.PR
    rs, lo = pr["random_split_5x"], pr["leave_one_simulation_out"]
    sh = pr["shipped_fit"]
    vs = F.VS["results"]
    vc, vn, vd, vb = vs["clean"], vs["gaussian_noise_sigma10"], vs["brightness_x0.6"], vs["gaussian_blur_7x7"]
    mt = F.VR["mixed_traffic"]
    pc = mt["per_class"]
    am = F.VR["ambulance_classification"]
    lb, yb = am["lightbar_cluster_any"], am["ambulance_flag_yolo_plus_lightbar"]
    api = {r["endpoint"].split(":")[0]: r for r in F.API["results"]}
    bp = F.BASE_PAPER_RESULTS
    gb_fold = lo["Gradient Boosting (used)"]["mae_per_fold"]
    pe_fold = lo["Persistence"]["mae_per_fold"]
    th = F.TH

    authors = [[n, f"Roll No. {r}", "Dept. of Computer Science and Engineering", F.COLLEGE_SHORT, "[CITY], India", "[EMAIL]"] for n, r in F.STUDENTS_UPPER]
    authors.append([F.GUIDE.upper(), f"{F.GUIDE_DESIGNATION} (project guide)", "Dept. of Computer Science and Engineering", F.COLLEGE_SHORT, "[CITY], India", "[EMAIL]"])
    P.title_block("FlowSense: AI-Based Smart Traffic Management with Adaptive, Emergency-Aware and Coordinated Signal Control", authors)
    P.begin_two_columns()

    P.abstract(
        "Fixed-time traffic signals cannot see queues or ambulances. This paper presents FlowSense, a working web platform that puts the whole chain in one pipeline: "
        "YOLOv8 vehicle detection with a light-bar rule, a gradient-boosting 30-second queue forecaster, an adaptive controller with inter-junction look-ahead and an emergency green wave, "
        "and a violation log. Four controllers were compared on identical seeded demand in an in-house simulator, not SUMO. "
        f"The adaptive family cut average delay by {d2['delay_cut_advanced_vs_fixed_pct']:.0f} % on a 2x2 grid and {d3['delay_cut_advanced_vs_fixed_pct']:.0f} % on 3x3 against fixed-time control, "
        f"and ambulance delay fell from {efx2[0]:.1f} s to {eav2[0]:.1f} s, but FlowSense beat plain queue-actuated control by only {d2['delay_cut_advanced_vs_adaptive_pct']:.0f}-{d3['delay_cut_advanced_vs_adaptive_pct']:.0f} %, within one standard deviation. "
        f"The forecaster reaches R2 {f3(rs['Gradient Boosting (used)']['r2_mean'])} on a random split but fails on an unseen congested run. "
        f"Vision scores {vc['recall'] * 100:.0f} % recall on synthetic scenes but the light-bar rule finds only {lb['tp']} of {am['ambulance_images']} real ambulance photos. No trained light-bar detector was built.",
        ["adaptive signal control", "emergency vehicle priority", "queue forecasting", "traffic simulation", "vehicle detection", "YOLOv8"])

    # ------------------------------------------------------------------ I
    P.heading("I", "Introduction")
    P.para("Many urban junctions still run fixed-time plans that were set for an average day {r:%d}. Such a plan keeps giving green to an empty approach while a queue grows on another, "
           "and it treats an ambulance like any other vehicle. Cameras are already installed at many junctions, and detectors such as YOLO count and classify vehicles from their video in real time %s, "
           "so the information needed to do better is available. The difficulty is joining the pieces: detection, demand estimation, signal timing, emergency priority and coordination "
           "between neighbouring junctions are usually studied one at a time, and the systems in our literature survey perform adaptive control or detection separately." % (CITE["webster"], c("yolo", "ultralytics")))
    P.para(f"The base paper {c('base')} adds a trained YOLO26m roof light-bar detector as a supervisory emergency layer on top of a GA-SGD optimised controller {c('gasgd')} and validates it in SUMO "
           f"{c('sumo')} on one roundabout in Rabat. Its detector reaches precision {bp['precision']}, recall {bp['recall']} and mAP50 {bp['map50']} on {3130:,} images. It leaves the other parts of a city-wide system open: "
           "queue forecasting, corridor coordination and a working operator console. This work builds those parts and, just as importantly, measures where they do and do not help.")
    P.para("The contributions are: (1) FlowSense, an end-to-end working product (simulator, forecaster, vision layer, FastAPI service, React console) with 38 automated tests; "
           "(2) an advanced controller combining passenger-car-equivalent (PCU) pressure, a 30-second queue forecast, platoon look-ahead, spill-back avoidance and an emergency green wave, "
           "compared fairly with fixed-time, queue-actuated and base-paper-style controllers on identical demand; "
           "(3) an honest evaluation including an ablation, a leave-one-simulation-out test of the forecaster and a test of the vision layer on 893 real images; and (4) a plain list of what is not achieved. "
           "Section II reviews the literature, Section III the method, Section IV the results, and Section V concludes.")
    P.sub("A", "System Hardware")
    P.para("All experiments ran on one CPU-only desktop PC: Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB RAM, Intel UHD 770 graphics (no CUDA GPU), Windows 11 Pro. "
           "A 1800 s simulation of four junctions takes %.2f s (%s times real time) and a 3x3 run %.2f s." % (th["2x2/advanced"]["wall_s"], f"{th['2x2/advanced']['speedup']:,.0f}", th["3x3/advanced"]["wall_s"]))
    P.sub("B", "Software Requirements")
    P.para("Python 3.11.9 with NumPy 1.26.4, pandas 2.2.1, scikit-learn 1.5.0 %s, OpenCV 4.11.0, PyTorch 2.14.1 (CPU) and Ultralytics 8.4.186 running yolov8n.pt %s; "
           "FastAPI 0.143.3 for the service; Node 24, React 19 and Vite 8 for the console; pytest 8.2 for tests." % (c("sklearn"), c("ultralytics")))

    # ------------------------------------------------------------------ II
    P.heading("II", "Literature Survey")
    P.para(f"**Base paper.** Lamrabet et al. {c('base')} observe that optimised controllers suffer from “emergency blindness” and that preemption schemes need costly hardware. "
           f"They train a single-class YOLO26m detector on the roof light-bar (3,130 manually curated images, 2,599/266/265 split, 100 epochs, 640 px, Colab T4) and reach a mean precision of 0.73, recall 0.69, "
           f"mAP50 0.73 and mAP50-95 0.34 over three runs, at 11-14 ms per frame. A priority arbitrator acts when confidence is at least 0.5 for three consecutive frames: it applies yellow clearance, forces green on the ambulance approach and "
           f"hands control back to GA-SGD afterwards. In a SUMO model of the Souissi roundabout the ambulance travel time was {bp['amb_travel_s']['proposed']} s against {bp['amb_travel_s']['ga_sgd']} s for GA-SGD and "
           f"{bp['amb_travel_s']['fixed']} s for fixed-time, and total waiting time was {bp['total_wait_s']['proposed']:,} s against {bp['total_wait_s']['ga_sgd']:,} s and {bp['total_wait_s']['fixed']:,} s. "
           "Its own limits are a moderate dataset, a single simulated roundabout, no flashing-state check and no real-road trial.")
    P.para(f"**Classical and learned signal control.** Fixed-time plans follow Webster's delay-minimising cycle {c('webster')}. Max-pressure control {c('varaiya')} balances upstream and downstream queues without a model of demand, "
           f"and reinforcement-learning controllers learn phase choices from traffic state {c('intellilight')}. Our advanced controller is pressure-style in spirit but is a hand-written rule set, not max-pressure or a learned policy.")
    P.para(f"**Emergency-vehicle priority.** Infrastructure-based schemes use GPS, RFID or IoT links; one reports a 35 % reduction in ambulance response time {c('sasikala')}. Acoustic detection runs a CNN on siren audio on embedded hardware {c('giordano')}. "
           f"Vision approaches detect vehicles with YOLO variants {c('phuong')} and emergency vehicles by their appearance {c('suhana')}, which depends on the vehicle's shape and livery; the base paper's light-bar cue avoids that dependence.")
    P.para(f"**End-to-end systems.** ASTM {c('astm')} detects vehicles with YOLOv5, forecasts vehicle counts for 12 hours with an LSTM (RMSE 2.232 vehicles) and, in the CARLA simulator, reports 21 against about 15 vehicles per minute and a 5 s against about 12 s pass delay. "
           f"The survey also lists Signal-IQ {c('s_signaliq')}, an integrated YOLOv8 hardware-validated system; we could not verify its authors or results, so it is listed without numbers.")
    P.table("Selected related work", ["Work", "Approach", "Data / test", "Reported result", "Limitation"],
            [[f"Base {c('base')}", "YOLO26m light-bar + GA-SGD", "3,130 images; SUMO roundabout", "amb. travel 56 s vs 70 s", "One roundabout; sim only"],
             [f"ASTM {c('astm')}", "YOLOv5 + LSTM cycle length", "CARLA", "5 s vs ~12 s pass delay", "Simulated; no emergency logic"],
             [f"Sasikala et al. {c('sasikala')}", "GPS / IoT preemption", "IoT scenario", "35 % faster response", "Needs infrastructure"],
             [f"Giordano et al. {c('giordano')}", "Siren audio CNN", "Embedded audio", "(not quoted here)", "No localisation"],
             [f"Phuong; Suhana {c('phuong', 'suhana')}", "YOLO vehicle / emergency", "Street images", "(not quoted here)", "Appearance-dependent"],
             [f"Signal-IQ {c('s_signaliq')}", "YOLOv8 + signal control", "Hardware (per title)", "not verified", "Authors not verified"],
             ["This work", "YOLOv8n, forecaster, 4 controllers", "In-house simulator; real photos", "see Section IV", "No trained light-bar model"]],
            [0.55, 0.78, 0.72, 0.72, 0.63], size=6.5)
    P.para("**Positioning.** Compared with the studies above, this work trades depth in one component for breadth across the chain: the base paper's detector and SUMO study are deeper in their parts, "
           "while FlowSense supplies a forecaster, coordination, a violation log and an operator console around a simpler detector, and checks its own claims against baselines.")
    P.para("**Research gap.** The surveyed systems perform adaptive control or vehicle detection separately. What is missing is one pipeline that detects, forecasts, adapts timing, gives emergency priority "
           "and coordinates junctions, built as a runnable product and evaluated against the simpler baselines it is supposed to beat. FlowSense addresses the pipeline and the evaluation; "
           "it does not reproduce the base paper's trained detector or its SUMO study.")

    # ------------------------------------------------------------------ III
    P.heading("III", "Methodology")
    P.sub("A", "Simulator, Workload and Data")
    P.para("The simulator is a pure-Python, one-second-tick model of a 2x2 or 3x3 grid of signalised junctions with four approaches (N, E, S, W) and a two-phase signal (north-south or east-west). "
           "Vehicles arrive by a Poisson process on entry roads (0.15 veh/s north-south, 0.10 east-west) scaled by a demand slider and a morning and evening rush-hour profile, "
           "queue at the stop line, discharge at 0.5 veh/s with 2 s start-up loss and 3 s clearance, travel 12 s to the next junction, and are blocked when an approach holds 30 vehicles. "
           "The mix is 68 %% cars, 13 %% bikes, 6 %% buses and 13 %% trucks, weighted 1, 0.5, 3 and 2 passenger-car units %s; 5 %% of cars are red-light runners and wrong-way drivers appear at random. "
           "Ambulances arrive at about one per 150 s. Demand is seeded and independent of the controller, so all controllers face identical vehicles and emergencies. "
           "No external data is used for control. The forecaster is trained on 26,988 samples from six simulated 1800 s runs of the adaptive controller; vision is tested on a public set of 293 real dashcam frames %s and "
           "600 ambulance and non-ambulance photos %s." % (c("hcm"), c("ds_traffic"), c("ds_ambulance")))
    P.sub("B", "Controllers")
    P.para("**Fixed-time** alternates phases every 30 s. **Adaptive** is queue-actuated (minimum green 15 s, maximum 60 s). **Emergency-aware** is adaptive plus pre-emption at one junction when an ambulance is queued or within 5 s; "
           "it emulates the base paper's idea but is not a re-implementation (no GA-SGD, no trained detector, the controller knows ambulances by ground truth). "
           "**Advanced (FlowSense)** scores each phase by")
    P.eq("P_phi = Σ γ_a ( W_a + 0.7 max(q_a − n_a, 0) + I_a + h_a/12 )")
    P.para("where, for each approach a of the phase, W is the PCU-weighted queue, q the forecast queue 30 s ahead and n the current length, I the PCU arriving within 8 s on the link (platoon look-ahead), h the waiting time of the head vehicle (fairness), "
           "and γ is 0.3 when the straight-ahead downstream queue is at least 26 (spill-back avoidance) and 1 otherwise. A junction switches phase when the current phase has no demand and the other has some, when")
    P.eq("P_other > 2 P_cur + 4")
    P.para("or at the 60 s limit, with a 13 s minimum green. Independently, an ambulance in a queue or inbound within 15 s forces its phase green after 2 s, which with the look-ahead gives a green wave along its route. "
           "Inter-junction communication is therefore simulated as look-ahead on the transit queue, not as a network protocol.")
    P.figure(figs["flow"], "Main flow: the one-second simulation loop and the advanced controller's decision at each junction.", 3.3)
    P.sub("C", "Queue Forecaster")
    P.para(f"For each approach, eleven features (queue, PCU queue, queue 10 s and 30 s ago, inflow over 30 s, inbound vehicles in 15 s, green flag, time in green, entry flag, sine and cosine of the hour) predict the queue 30 s ahead. "
           f"A gradient-boosting regressor {c('gbm')} (160 trees, depth 4, learning rate 0.08) from scikit-learn is the model; a random forest {c('rf')}, ridge regression and persistence are baselines. "
           f"It is evaluated on a random 75/25 split and, more strictly, by holding out each of the six simulated runs in turn. Outputs are clipped to 0-40 vehicles and used inside the advanced controller's pressure score.")
    P.sub("D", "Vision Layer")
    P.para("YOLOv8n with COCO weights, restricted to car, motorcycle, bus and truck classes, finds vehicles; it is not fine-tuned. A rule detects emergency light bars: red (H 0-8 or 172-180) and blue (H 100-130) pixels with S ≥ 120 and V ≥ 190 "
           "are dilated, and a red-blue cluster that sits on the upper part of a vehicle box relabels that vehicle as an ambulance. A classical contour detector handles the synthetic overhead scenes. "
           "Density and the recommended green time follow")
    P.eq("ρ = ΣPCU / 14,    g = 12 s if ambulance else min(60, max(15, 12 + 3.2 ΣPCU))")
    P.para("with LOW, MEDIUM, HIGH and JAMMED levels at ρ of 0.35, 0.7 and 1.0. Violations (red-light jumping, wrong-way driving) are generated by the simulator from ground-truth events and logged with a plate and a confidence between 0.86 and 0.99; "
           "there is no trained violation detector.")
    P.sub("E", "Architecture and Implementation")
    P.figure(figs["arch"], "FlowSense architecture: React console, FastAPI service and the three engine modules; state is in memory and there is no database.", 3.3)
    P.para("The FastAPI service exposes 20 endpoints with stateless HMAC-signed tokens for one demo operator, input validation that returns readable messages, a 12 MB upload limit and a cached benchmark. "
           "The forecaster trains in a background thread at start-up in about %.0f s. The React console has eight pages. Errors return a JSON message and a hint rather than a stack trace, and unknown controllers, grids or out-of-range demand are rejected with HTTP 422. The code is checked by 38 pytest tests (24 engine and vision, 14 API; all pass) and a 33-check end-to-end smoke test (all pass)." % sh["fit_seconds"])

    P.sub("F", "Evaluation Protocol")
    P.para("Average delay is the mean number of seconds a vehicle spends queued before it leaves the network; ambulance delay is the same quantity for ambulances only; throughput counts vehicles that finished their trip; "
           "idle fuel and CO2 follow from queued vehicle-seconds. Every controller is run on the same five seeds, so differences are paired by demand. Vision is scored by greedy IoU matching (0.3 on synthetic scenes, 0.5 on real frames) "
           "and by confusion counts on photos; no threshold was tuned on the real images, and the application's own defaults are used. "
           "All experiments are scripted (run_experiments.py, eval_real_vision.py, measure_api.py), write JSON files and can be re-run in about two minutes, plus one minute for the real-image test.")

    # ------------------------------------------------------------------ IV
    P.heading("IV", "Results")
    P.sub("A", "Test Conditions")
    P.para("Controller results use seeds 40-44, 1800 s, demand ×1.2 and an 08:00 start, reported as mean ± sample standard deviation over five runs. Each grid size was run separately. "
           "Fuel is idle queue time at 0.6 L/h per queued vehicle (a simulator assumption). All numbers come from experiments/**/metrics.json.")
    P.table("Controller comparison, five seeds (mean ± std)", ["Controller", "2x2 delay (s)", "2x2 amb. (s)", "3x3 delay (s)", "3x3 amb. (s)"],
            [[F.CTRL_SHORT[k], F.mstd(g("2x2", k, D)), F.mstd(g("2x2", k, E)), F.mstd(g("3x3", k, D)), F.mstd(g("3x3", k, E))] for k in F.CTRL_KEYS],
            [0.75, 0.62, 0.62, 0.62, 0.62], size=6.8, align=["l", "c", "c", "c", "c"])
    P.figure(figs["results"], "Average delay and ambulance delay by controller (mean ± std, five seeds) on 2x2 and 3x3 grids.", 3.4)
    P.sub("B", "Controller Performance")
    P.para(f"Table II shows that any adaptive controller beats fixed time: the advanced controller cuts average delay by {d2['delay_cut_advanced_vs_fixed_pct']:.1f} % on 2x2 ({fx2[0]:.1f} to {av2[0]:.1f} s) and "
           f"{d3['delay_cut_advanced_vs_fixed_pct']:.1f} % on 3x3, saving {d2['fuel_saved_L_advanced_vs_fixed_per_run']:.1f} L of idling fuel per half-hour run on 2x2. "
           f"Most of this gain comes from adaptivity itself. Against plain queue-actuated control the advanced controller is better by only {d2['delay_cut_advanced_vs_adaptive_pct']:.1f} % (2x2) and "
           f"{d3['delay_cut_advanced_vs_adaptive_pct']:.1f} % (3x3), which is within about one standard deviation of the adaptive controller ({ad2[1]:.1f} s on 2x2). "
           f"The base-paper-style controller has a higher mean delay than plain adaptive control ({em2[0]:.1f} against {ad2[0]:.1f} s on 2x2; {em3[0]:.1f} against {ad3[0]:.1f} s on 3x3): pre-emption has a price. "
           f"In the demand sweep (2x2, three seeds) fixed time rises from {sw['fixed'][0]['delay_mean']:.1f} s at ×0.6 to {sw['fixed'][-1]['delay_mean']:.1f} s at ×1.8, the advanced controller from {sw['advanced'][0]['delay_mean']:.1f} to {sw['advanced'][-1]['delay_mean']:.1f} s; "
           f"at ×0.6 it is worse than adaptive ({sw['adaptive'][0]['delay_mean']:.1f} s) because it holds green for forecast and inbound traffic that is light.")
    P.table("Average delay (s) versus demand, 2x2, three seeds", ["Demand", "Fixed", "Adaptive", "Emerg.", "FlowSense"],
            [[f"×{lv}"] + [f"{sw[k][i]['delay_mean']:.1f}" for k in F.CTRL_KEYS] for i, lv in enumerate(F.SW["levels"])],
            [0.6, 0.6, 0.6, 0.6, 0.7], size=6.8, align=["c", "c", "c", "c", "c"])
    P.sub("C", "Emergency Priority and Ablation")
    P.para(f"Ambulance delay falls from {efx2[0]:.1f} s (fixed) to {eav2[0]:.1f} s with the advanced controller on 2x2 ({d2['emergency_cut_advanced_vs_fixed_pct']:.1f} % lower) and from {efx3[0]:.1f} to {eav3[0]:.1f} s on 3x3 "
           f"({d3['emergency_cut_advanced_vs_fixed_pct']:.1f} % lower). Against the base-paper-style controller the gain is {d2['emergency_cut_advanced_vs_basepaper_pct']:.1f} % on 2x2 and {d3['emergency_cut_advanced_vs_basepaper_pct']:.1f} % on 3x3, "
           f"the larger gap coming from the green wave across more junctions. In an emergency-heavy test (one ambulance per 60 s, 3600 s) the mean ambulance delay is {emh['fixed']['mean']:.1f}, {emh['adaptive']['mean']:.1f}, {emh['emergency']['mean']:.1f} and {emh['advanced']['mean']:.1f} s "
           f"for fixed, adaptive, base-paper-style and advanced control, while the network delay is {emh['adaptive']['network_delay']:.1f}, {emh['emergency']['network_delay']:.1f} and {emh['advanced']['network_delay']:.1f} s for the last three. "
           f"The ablation (five seeds) shows {abd['advanced (full)']:.1f} s for the full controller, {abd['no ML forecast']:.1f} s without the forecast, {abd['no platoon look-ahead']:.1f} s without look-ahead and {abd['no emergency pre-emption']:.1f} s without any pre-emption; "
           f"removing the green wave raises ambulance delay from {abe['advanced (full)']:.1f} to {abe['no emergency green wave']:.1f} s and removing pre-emption to {abe['no emergency pre-emption']:.1f} s. "
           "Pre-emption therefore lowers network efficiency slightly in exchange for safety; the differences between the full controller and its ablations other than pre-emption are of the order of one standard deviation.")
    P.table("Ablation of the advanced controller, 2x2, five seeds", ["Variant", "Delay (s)", "Ambulance delay (s)"],
            [[k, F.mstd((v[D]["mean"], v[D]["std"])), f"{v[E]['mean']:.1f}"] for k, v in ab.items()],
            [1.6, 0.8, 0.8], size=6.8, align=["l", "c", "c"])
    P.sub("D", "Queue Forecaster")
    P.para(f"On a random 75/25 split the gradient-boosting model scores a mean absolute error (MAE) of {rs['Gradient Boosting (used)']['mae_mean']:.2f} vehicles and R2 {f3(rs['Gradient Boosting (used)']['r2_mean'])}, against "
           f"{rs['Persistence']['mae_mean']:.2f} and {f3(rs['Persistence']['r2_mean'])} for persistence; the random forest is as good ({rs['Random Forest']['mae_mean']:.2f}). "
           f"That test overstates generalisation, because snapshots of one run are near-duplicates. Holding out whole runs, the mean R2 falls to {lo['Gradient Boosting (used)']['r2_mean']:.2f}. "
           f"The model beats persistence in five of six held-out runs (for example {gb_fold[0]:.2f} against {pe_fold[0]:.2f} vehicles) but fails on the one congested run (3x3, demand ×1.6, 17:00): MAE {gb_fold[3]:.1f} against {pe_fold[3]:.1f}, "
           "because queues of up to 138 vehicles lie outside the training range, tree models cannot extrapolate and the output is clipped at 40. Removing the forecast from the controller costs about "
           f"{abd['no ML forecast'] - abd['advanced (full)']:.1f} s of delay.")
    P.table("Forecaster and vision measurements", ["Test", "Result"],
            [["Forecast MAE, random split (GB / persistence)", f"{rs['Gradient Boosting (used)']['mae_mean']:.2f} / {rs['Persistence']['mae_mean']:.2f}"],
             ["Forecast R2, leave-one-run-out (GB)", f"{lo['Gradient Boosting (used)']['r2_mean']:.2f} ± {lo['Gradient Boosting (used)']['r2_std']:.2f}"],
             ["Synthetic scenes: recall / precision", f"{vc['recall'] * 100:.1f} % / {vc['precision'] * 100:.1f} %"],
             ["Synthetic: noise σ=10 / dark ×0.6 recall", f"{vn['recall'] * 100:.0f} % / {vd['recall'] * 100:.0f} %"],
             ["Real frames: 4-wheeler P / R", f"{pc['4-wheeler']['precision'] * 100:.0f} % / {pc['4-wheeler']['recall'] * 100:.0f} %"],
             ["Real frames: 2-wheeler / 3-wheeler recall", f"{pc['2-wheeler']['recall'] * 100:.0f} % / {pc['3-wheeler']['recall'] * 100:.0f} %"],
             ["Real ambulance photos: light-bar recall", f"{lb['tp']} / {am['ambulance_images']} ({lb['recall'] * 100:.1f} %)"],
             ["Real non-ambulance: false alarms", f"{lb['fp']} / {am['no_ambulance_images']}"]],
            [1.95, 1.2], size=6.8, align=["l", "c"])
    P.sub("E", "Vision Layer")
    P.para(f"On {vc['scenes']} synthetic overhead scenes ({vc['objects']:,} vehicles) the contour detector reaches recall {vc['recall'] * 100:.1f} % and precision {vc['precision'] * 100:.1f} %, labels {vc['class_accuracy_of_matched'] * 100:.1f} % of matched vehicles correctly and finds the ambulance in every scene that has one "
           f"({vc['ambulance_false_alarm_rate'] * 100:.1f} % false alarms). This is an in-domain test: the same authors wrote the renderer and the detector, and the detector is brittle. Gaussian noise of σ=10 gives {vn['detections']} detections, "
           f"brightness ×0.6 removes every light bar (ambulance recall {vd['ambulance_recall'] * 100:.0f} %) and a 7×7 blur halves it to {vb['ambulance_recall'] * 100:.0f} %. "
           f"On {mt['images']} real mixed-traffic dashcam frames YOLOv8n at confidence 0.3 reaches precision {pc['4-wheeler']['precision'] * 100:.0f} % and recall {pc['4-wheeler']['recall'] * 100:.0f} % for four-wheelers, "
           f"only {pc['2-wheeler']['recall'] * 100:.0f} % recall for two-wheelers and {pc['3-wheeler']['recall'] * 100:.0f} % for auto-rickshaws (COCO has no such class), with {mt['latency_ms_mean']:.0f} ms per frame on the CPU. "
           f"The light-bar rule flags {lb['tp']} of {am['ambulance_images']} real ambulance photos (and {yb['tp']} when a YOLO box is required) with {lb['fp']} false alarm in {am['no_ambulance_images']} other photos: most photos show lights off, daylight or colours below the thresholds, and on inspection the few hits sit on red and blue livery, not on roof lights. "
           "The synthetic result does not transfer to real images.")
    P.sub("F", "Comparison with the Base Paper")
    P.para(f"The base paper reports an ambulance travel time of {bp['amb_travel_s']['proposed']} s against {bp['amb_travel_s']['fixed']} s for fixed-time (12.5 % lower), a waiting time of {bp['amb_wait_s']['proposed']} s against {bp['amb_wait_s']['fixed']} s (32 % lower) "
           f"and a total network waiting time 41 % below fixed-time, in one SUMO roundabout scenario. FlowSense measures ambulance delay (queue waiting) {d2['emergency_cut_advanced_vs_fixed_pct']:.0f} % and {d3['emergency_cut_advanced_vs_fixed_pct']:.0f} % below fixed-time on its two grids and network delay "
           f"{d2['delay_cut_advanced_vs_fixed_pct']:.0f} % and {d3['delay_cut_advanced_vs_fixed_pct']:.0f} % below. The numbers are not comparable in absolute terms: the testbed (in-house grid simulator against SUMO roundabout), the metric (waiting delay against travel time), "
           f"the demand and the emergency knowledge (ground truth against a detector with precision {bp['precision']}) all differ. The base paper's detector evidence (mAP50 {bp['map50']} on {3130:,} annotated images) has no counterpart here.")
    P.sub("G", "Output Screens and Performance")
    P.figure(figs["live"], "FlowSense live control centre: road map with signal states and queues, and the junction status table with 30-second forecasts.", 3.4)
    P.figure(figs["benchvis"], "FlowSense benchmark screen (three seeds) and vision screen: synthetic scene with detections, PCU density and recommended green.", 3.4)
    P.para(f"Measured on 127.0.0.1, a live step of 2 s takes {api['live step 2 s']['mean_ms']:.0f} ms, a 300 s step {api['live step 300 s']['mean_ms']:.0f} ms, the prediction page {api['prediction']['mean_ms']:.0f} ms and a synthetic vision frame {api['vision synthetic']['mean_ms']:.0f} ms; "
           f"a YOLOv8n frame takes {mt['latency_ms_mean']:.0f} ms and the first four-controller benchmark about {api['POST /api/benchmark (4 ctrl x 3 seeds x 1800 s, first call)']['mean_ms'] / 1000:.1f} s (cached repeats {api['POST /api/benchmark (cached)']['mean_ms']:.0f} ms).")

    P.sub("H", "Failure Cases and Observed Limits")
    P.para(f"Eight failure cases are worth stating. (1) At low demand (×0.6) the advanced controller is {sw['advanced'][0]['delay_mean'] - sw['adaptive'][0]['delay_mean']:.1f} s worse than plain adaptive control. "
           f"(2) The base-paper-style controller is slower than adaptive control on average and, on 3x3, runs {g('3x3', 'emergency', 'Red-light violations')[0]:.1f} simulated red-light violations per run against {g('3x3', 'advanced', 'Red-light violations')[0]:.1f} for FlowSense. "
           f"(3) Without any pre-emption the network delay is lowest ({abd['no emergency pre-emption']:.1f} s) but ambulance delay is {abe['no emergency pre-emption']:.1f} s. "
           f"(4) The forecaster collapses outside its training range. (5) The classical detector returns nothing under mild noise. (6) The light-bar rule misses {lb['fn']} of {am['ambulance_images']} real ambulance photos. "
           f"(7) YOLOv8n misses most two-wheelers and all auto-rickshaws in dense dashcam frames ({mt['gt_boxes_excluding_pedestrians']:,} vehicle boxes, overall recall {pc['any vehicle class']['recall'] * 100:.0f} % at precision {pc['any vehicle class']['precision'] * 100:.0f} %). "
           "(8) Fixed-time delay varies strongly between seeds (a standard deviation of "
           f"{fx2[1]:.1f} s on 2x2), so a three-seed screen differs from the five-seed table: the application's benchmark screen shows 73.0, 48.5, 51.2 and 45.4 s for the first three seeds. "
           "Other threats to validity are that the simulator's demand, saturation flow and link time are the authors' assumptions, that the datasets for vision are small public sets (the ambulance photos are the first 300 files of each class), "
           "and that there is no real-camera, hardware-in-the-loop or field test.")

    # ------------------------------------------------------------------ V
    P.heading("V", "Conclusion and Future Scope")
    P.para(f"FlowSense meets its engineering objectives: one tested product that detects vehicles, forecasts queues, adapts signal timing, gives ambulances priority and logs violations. "
           f"In simulation, adaptive control cuts delay by about a third against fixed time and pre-emption cuts ambulance delay by {d2['emergency_cut_advanced_vs_fixed_pct']:.0f}-{d3['emergency_cut_advanced_vs_fixed_pct']:.0f} %. "
           f"The key finding is that the advanced additions give only {d2['delay_cut_advanced_vs_adaptive_pct']:.0f}-{d3['delay_cut_advanced_vs_adaptive_pct']:.0f} % over plain queue-actuated control, and that safety priority costs other traffic a little.")
    P.para("The limits are plain. Validation is in an in-house simulator, not SUMO, and cannot be compared with the base paper in absolute terms. The controllers know ambulances by ground truth; the vision module is not in the control loop. "
           "No light-bar detector was trained, and the colour rule finds almost no real ambulances. Vehicle detection is stock YOLOv8n and misses most motorcycles and rickshaws in dense dashcam traffic. "
           "Violations are simulated events. The forecaster fails on congestion outside its training range, and the console has no database and one demo operator.")
    P.para("Future work: train a light-bar and emergency-vehicle detector on annotated data and put it in the loop with temporal confirmation; fine-tune the vehicle detector on local mixed-traffic images; "
           "retrain the forecaster on congested runs and add uncertainty; validate in SUMO and compare with max-pressure and learned controllers; add real violation detection with tracking; and test on a live camera with hardware-in-the-loop.")

    P.references()
    P.save(path)
    return path
