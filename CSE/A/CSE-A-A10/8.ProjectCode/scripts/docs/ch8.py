"""Chapter 8: Results and output screens. Every number is read from facts.py (experiments/**/metrics.json) or typed exactly as in docs/REPORT_FACTS.md."""
import json
import os

from . import facts as F
from .blocks import CODE, FIG, H1, H2, H3, N, B, P, PAIR, TAB
from .refs import CITE as R

SH = F.shot
CK = F.CTRL_KEYS


def S(name, caption, base=5.6, max_h=3.9):
    """Screenshot figure with a width that keeps the picture on one page."""
    return FIG(SH(name), caption, F.shot_w(SH(name), base, max_h))


def SP(a, b):
    """Two screenshots side by side: a, b are (file, caption)."""
    return PAIR([(SH(a[0]), a[1]), (SH(b[0]), b[1])], 2.95)


def M(grid, c, key):
    d = (F.C2 if grid == "2x2" else F.C3)["results"][c]["metrics"][key]
    return d["mean"], d["std"]


def ms_(grid, c, key, nd=1):
    m, s = M(grid, c, key)
    return f"{m:.{nd}f} ± {s:.{nd}f}"


def _ctrl_table(grid, caption):
    rows = []
    for c in CK:
        r = (F.C2 if grid == "2x2" else F.C3)["results"][c]
        rows.append([F.CTRL_LABEL[c], ms_(grid, c, "Avg delay / vehicle (s)"), ms_(grid, c, "Avg queue (veh)"),
                     f"{M(grid, c, 'Max approach queue')[0]:.0f}", f"{M(grid, c, 'Throughput (veh)')[0]:.0f}",
                     ms_(grid, c, "Emergency delay (s)"), f"{M(grid, c, 'Fuel wasted idling (L)')[0]:.1f}"])
    return TAB(caption, ["Controller", "Avg delay (s)", "Avg queue (veh)", "Max queue", "Throughput", "Ambulance delay (s)", "Idle fuel (L)"], rows,
               widths=[1.75, 0.95, 0.95, 0.55, 0.75, 0.9, 0.55], align=["l", "c", "c", "c", "c", "c", "c"], size=9.5)


def _setup():
    a = F.VR["ambulance_classification"]
    out = [
        H2("8.1 Experimental set-up"),
        P("All measurements in this chapter were made on one machine: an Intel Core i5-12500 (6 cores, 12 threads) with 15.7 GB of memory, no CUDA GPU (Intel UHD 770 only), Windows 11, "
          "Python 3.11.9, PyTorch 2.14.1 (CPU build), Ultralytics 8.4.186 with the COCO-trained `yolov8n.pt` weights, scikit-learn 1.5.0, NumPy 1.26.4, OpenCV 4.11.0, pandas 2.2.1 and FastAPI 0.143.3. "
          "The machine was shared with other programs, so absolute timings are indicative; the simulation results do not depend on load because the simulator is seeded and deterministic. "
          "Every table and figure was produced from stored JSON by `scripts/run_experiments.py`, `scripts/eval_real_vision.py`, `scripts/measure_api.py` and `scripts/docs/make_figures.py`; no result was typed in by hand."),
        TAB("Data used in the evaluation", ["Item", "Content", "Source and status"],
            [["Simulated traffic (control experiments)", "2x2 or 3x3 junction grid, Poisson demand, seeds 40-44, 1800 s per run, start 08:00",
              "FlowSense simulator (`smart_traffic/sim.py`); identical demand for all four controllers; not SUMO"],
             ["Forecaster training set", f"{F.PR['n_samples']:,} samples x {F.PR['n_features']} features; target = queue 30 s ahead",
              "Six simulated 1800 s runs under the adaptive controller (alternating 2x2 / 3x3, demand 0.7-1.6, start 07:00-17:00)"],
             ["Synthetic overhead scenes", "300 scenes, 2,754 vehicles, half with an ambulance", "`vision.render_scene`; the same author wrote the renderer and the detector"],
             ["Real mixed-traffic frames", "293 dashcam frames (640x480), 1,467 vehicle boxes without pedestrians; 2-, 3- and 4-wheelers",
              f"Visaitech mixed-traffic dataset v0.1, CC BY 4.0 [{R['ds_traffic']}]; no model is trained on it, so all 293 frames are test data"],
             ["Real ambulance photos", f"{a['ambulance_images']} ambulance and {a['no_ambulance_images']} non-ambulance images (first 300 files of each folder)",
              f"Ambulance classification dataset, CC BY 4.0 [{R['ds_ambulance']}]; positives include photos where the lights are off or not visible"],
             ["Bundled sample photo", "`bus.jpg`, 1080 x 810", "Ultralytics sample used by the Vision page"]],
            widths=[1.5, 2.3, 2.8], align=["l", "l", "l"], size=9.5),
        P("Test conditions for the control experiments: demand multiplier 1.2 (times the time-of-day profile, which peaks at 08:30), duration 1800 s, five seeds, and the mean and sample standard deviation over seeds are reported. "
          "Fuel and CO2 are derived from queued vehicle-seconds at 0.6 L/h per idling vehicle and 2.31 kg per litre, which are assumptions of the simulator. "
          "No threshold of the vision layer was tuned on the real images: the confidence threshold 0.3 and the light-bar colour limits are the application's own defaults. "
          "No significance test was run; the five-seed spread is the only statement of uncertainty."),
    ]
    if F.REPORT:
        out[1] = P("All measurements were made on one machine: Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB memory, no CUDA GPU, Windows 11, Python 3.11.9, PyTorch 2.14.1 (CPU), Ultralytics 8.4.186 with COCO-trained `yolov8n.pt`, scikit-learn 1.5.0. "
                   "The machine was shared with other programs, so timings are indicative; simulation results are seeded and deterministic. Every table and figure was produced from stored JSON by the scripts in `scripts/`; no result was typed in by hand.")
        out[3] = P("Control experiments: demand multiplier 1.2 (times the time-of-day profile), 1800 s, five seeds, mean and sample standard deviation over seeds. Fuel and CO2 follow from 0.6 L/h per idling vehicle and 2.31 kg per litre (simulator assumptions). "
                   "No vision threshold was tuned on the real images (confidence 0.3 and the light-bar colour limits are the application's defaults), and no significance test was run.")
    return out


def _screens_report():
    """Compact walkthrough for the full report: ten of the nineteen screens in five pairs (the rest are in Appendix C / document 14)."""
    return [H2("8.2 Output screens"),
            P("The captures are real screens of the running console (Chrome, 1440 by 900, dark theme), made by `scripts/capture_screens.py` with the backend and console running and the simulator advanced so that every view holds live data; nothing is a mock-up. "
              "The sign-in page (demo account `operator@flowsense.app` / `Flow@1234`, printed on the page), the landing page and the About page are in Appendix C and in the separate results document."),
            SP(("05_live_control.png", "Output screen: Live control centre - advanced controller, demand x1.6, 2x2 grid, emergency banner active, KPI strip updating."),
               ("06_live_map_and_status.png", "Output screen: road map, queue chart and junction status table with the 30 s forecast column.")),
            P("The live control centre is the main operating screen. The scenario bar selects the controller, the demand multiplier (0.4 to 2.0), the emergency toggle and the buttons *Run live*, *Skip 5 min*, *Send ambulance* and *Reset*. "
              "In the capture the advanced controller ran at demand x1.6: 156 vehicles in the network, 139 queued, 55 s average delay, 5.3 s ambulance delay, and a banner announcing pre-emption along the route (green wave). "
              "The map shows vehicles by class, signal heads (green, clearing, red), the ambulance star and a lightning mark on a pre-empted junction; the table lists each junction's phase, timer, four queues and the 30 s forecast."),
            SP(("07_benchmark.png", "Output screen: Benchmark - settings and the four headline tiles (-38 % delay vs fixed-time, -73 % ambulance delay)."),
               ("08_benchmark_charts.png", "Output screen: Benchmark charts - delay with error bars, ambulance delay, queue over time, ambulance-delay distribution.")),
            P("The benchmark screen runs the four controllers on identical traffic with the interface defaults (30 min, demand x1.2, three seeds, 08:00). The tiles read -38 % delay against fixed-time, -11 % against the emergency-aware controller, -73 % ambulance delay (5.1 against 18.7 s) and 12.4 L of idle fuel saved; "
              "the charts show fixed-time 73.0, adaptive 48.5, emergency-aware 51.2 and advanced 45.4 s. These are the first three of the five seeds in Section 8.3 (the five-seed fixed-time mean is 67.8 s), not a different experiment; the screen also shows that plain adaptive control has the worst ambulance delay in that run (22.6 s) because it ignores ambulances."),
            SP(("10_vision_synthetic.png", "Output screen: Vision, synthetic scene - detections with a magenta ring on the light-bar cluster."),
               ("12_vision_yolo.png", "Output screen: Vision, YOLOv8n on the bundled sample photograph - one bus at confidence 0.87.")),
            P("The Vision page analyses a rendered overhead scene (9 vehicles and an ambulance; 10 detected of 10) with the classical detector, where the magenta ring is the red-plus-blue cluster that relabels the white vehicle *ambulance* (13.0 PCU, HIGH, recommended green 12 s), and the bundled street photograph with YOLOv8n (one bus, no light bar). "
              "These screens show the mechanism working; Section 8.7 measures it on real photographs, where the synthetic success does not carry over."),
            SP(("13_prediction.png", "Output screen: Prediction - 26,988 samples, MAE 1.64, R2 0.961, 35 % below persistence, scatter and importance."),
               ("14_prediction_forecast.png", "Output screen: Prediction - model comparison and the live 30 s forecast per approach.")),
            P("The prediction page reports the forecaster as the application trains it at start-up and the live forecast bars for the 16 approaches. It presents the favourable random-split numbers; the held-out-simulation result that qualifies them is in Section 8.6."),
            SP(("15_violations.png", "Output screen: Violations - totals, per-junction and per-minute charts."),
               ("16_violations_log.png", "Output screen: Violations - evidence log (time, junction, approach, violation, plate, vehicle, confidence).")),
            P("The violations page shows 11 events after 16 simulated minutes (8 red-light jumping, 3 wrong-way driving, mean confidence 0.94). The events, the plates and the confidences (drawn between 0.86 and 0.99) are generated by the simulator; the page title says *detection*, but no model detects anything (Section 8.7 and Chapter 10).")]


def _screens():
    if F.REPORT:
        return _screens_report()
    out = [H2("8.2 Output screens"),
           P("The captures below are real screens of the running console (Chrome, 1440 by 900 pixels, dark theme unless stated), made by `scripts/capture_screens.py` with the FastAPI backend and the React console running and the simulator advanced so that every view holds live data. "
             "Nothing is a mock-up. The live, benchmark, vision, prediction and violation screens are the working surfaces of the product; the landing page in both themes and the light-theme live screen appear in Appendix C when this text is part of the full report."),
           ]
    cap = {
        "04": "Output screen: sign-in page with the demo operator account shown and a one-click *Use demo account* button.",
        "05": "Output screen: Live control centre - advanced controller, demand x1.6, 2x2 grid, with the emergency banner active and the KPI strip updating.",
        "06": "Output screen: live road map (signal heads, queued vehicles by class, junction labels) beside the queue chart and the junction status table with the 30 s forecast column.",
        "07": "Output screen: Benchmark - settings and the four headline tiles (-38 % delay vs fixed-time, -11 % vs emergency-aware, -73 % ambulance delay, 12.4 L fuel).",
        "08": "Output screen: Benchmark charts - average delay with error bars, ambulance delay, queue over time and the ambulance-delay distribution for the four controllers.",
        "09": "Output screen: Benchmark - full results table and the demand sweep from x0.6 to x1.8.",
        "10": "Output screen: Vision, synthetic scene - the camera frame and the detections with a magenta ring on the light-bar cluster.",
        "11": "Output screen: Vision - density report (10 vehicles, 13 PCU, HIGH, emergency YES, recommended green 12 s) and the detection table.",
        "12": "Output screen: Vision, YOLOv8n on the bundled sample photo - one bus detected at confidence 0.87.",
        "13": "Output screen: Prediction - 26,988 training samples, MAE 1.64 vehicles, R2 0.961, 35 % lower error than persistence, scatter and feature importance.",
        "14": "Output screen: Prediction - model comparison table and the live 30 s forecast per approach, with the highest predicted build-up called out.",
        "15": "Output screen: Violations - totals, per-junction and per-minute charts and the head of the evidence log.",
        "16": "Output screen: Violations - the evidence log (time, junction, approach, violation, plate, vehicle, confidence) and the per-controller violation table.",
        "17": "Output screen: About page - the base paper, and what is adopted from it versus what this project adds.",
        "18": "Output screen: About page - the system pipeline diagram, the four controllers and the run commands.",
    }
    nm = {"04": "04_login.png", "05": "05_live_control.png", "06": "06_live_map_and_status.png", "07": "07_benchmark.png", "08": "08_benchmark_charts.png",
          "09": "09_benchmark_sweep.png", "10": "10_vision_synthetic.png", "11": "11_vision_density.png", "12": "12_vision_yolo.png", "13": "13_prediction.png",
          "14": "14_prediction_forecast.png", "15": "15_violations.png", "16": "16_violations_log.png", "17": "17_about.png", "18": "18_about_pipeline.png"}

    def item(k):
        return (nm[k], cap[k])

    if True:
        out += [S("01_landing_dark.png", "Output screen: landing page (dark theme) with a live preview simulation of the advanced controller and a terminal log of signal changes.", 5.0, 3.5),
                P("The landing page is public. It runs a separate preview simulation (`GET /api/public/pulse`) so that visitors see junctions changing in real time, with counters for vehicles in the network, queued vehicles, average delay and completed trips. "
                  "It is the only page that does not require sign-in."),
                S("02_landing_features_dark.png", "Output screen: landing page capability cards - detect, prioritise, predict, coordinate, enforce, validate.", 5.0, 3.5),
                P("The six cards restate the six capabilities of the batch abstract as the product presents them. The text is marketing-style wording of the implemented modules; the measured status of each module is in Sections 8.5 to 8.8, and the violation card in particular describes simulated events (Section 8.7)."),
                S("03_landing_light.png", "Output screen: landing page in the light theme; the theme choice is remembered in the browser.", 5.0, 3.5)]
    out += [S(*item("04"), 4.6, 3.2),
            P("The sign-in page prints the demo operator account (`operator@flowsense.app` / `Flow@1234`) so that the demonstration is self-explanatory; the button *Use demo account* fills both fields. "
              "A wrong password returns HTTP 401 with a message and a hint, shown as a toast; there is no registration, password reset or role model, which is stated as a limitation in Chapter 4."),
            ]
    out += [S(*item("05")), S(*item("06"))]
    out += [P("The live control centre is the main operating screen. The scenario bar selects the signal controller (four choices), the traffic demand multiplier (0.4 to 2.0), the emergency-vehicle toggle and the buttons *Run live* (30 ticks of 2 simulated seconds), *Skip 5 min*, *Send ambulance* and *Reset*; "
              "the grid size and the ML forecast toggle sit in the sidebar. The KPI strip shows the simulated clock, vehicles in the network, average delay per vehicle, ambulance delay and violations. "
              "In the capture the advanced controller was running at demand x1.6: 156 vehicles in the network, 139 queued, 55 s average delay, 5.3 s ambulance delay with 3 ambulances served and 1 active, and the red banner announcing pre-emption along the route (green wave)."),
            P("The second screen shows the road map. Squares are vehicles coloured by class (car, bike, bus, truck), the star is an ambulance, signal heads show green, clearing or red, and the lightning mark appears on a junction that is currently pre-empted. "
              "The junction table lists the current green phase, the phase timer, the four approach queues (N/E/S/W) and the 30-second forecast for the same four approaches; switching the controller while the simulation runs changes the behaviour on the same traffic.")]
    out += [S(*item("07")), S(*item("08"))]
    out += [P("The benchmark screen runs the four controllers on identical traffic (same seeds, so the same vehicles and the same ambulances). It was run with the interface defaults: 30 minutes, demand x1.2, three seeds, start 08:00, ML forecast on. "
              "The tiles read -38 % delay against fixed-time, -11 % against the emergency-aware controller, -73 % ambulance delay (5.1 s against 18.7 s) and 12.4 L of idle fuel (28.6 kg CO2) saved. "
              "The charts show mean ± standard deviation over the three seeds (fixed-time 73.0, adaptive 48.5, emergency-aware 51.2, advanced 45.4 s), the queue growth over the half hour, and the ambulance-delay distribution as box plots. "
              "These three-seed figures are the first three of the five seeds in Section 8.3 (fixed 73.0 s is the mean of seeds 40-42, whereas the five-seed mean is 67.8 s); the screen is not a different experiment. "
              "The screen also shows an effect that the tables confirm: the plain adaptive controller has the worst ambulance delay in the three-seed run (22.6 s), because it does not recognise ambulances at all.")]
    out += [S(*item("09")), S(*item("10"))]
    out += [P("The lower half of the benchmark page lists the full results table (average delay, queue, maximum approach queue, throughput, ambulance delay, ambulance maximum, ambulances served and red-light violations per controller) and runs the demand sweep on request; "
              "the sweep chart shows the four controllers separating as demand grows, with the advanced controller lowest from x1.2 upward and slightly above the adaptive controller at x0.6 (Section 8.4)."),
          P("The Vision page has three modes. In the synthetic mode shown here, a rendered overhead scene (9 vehicles and an ambulance, flash frame A, seed 3) is analysed by the classical contour detector; the right image shows boxes with class and confidence, and the magenta ring is the red-plus-blue light-bar cluster that relabels the white vehicle as *ambulance*. "
            "Ground truth was 10 vehicles and 10 were detected.")]
    out += [S(*item("11")), S(*item("12"))]
    out += [P("Below the images the page reports the density: 7 cars, 1 bus, 1 truck and 1 ambulance give 13.0 passenger-car units, 93 % of an assumed road capacity of 14 PCU, level HIGH, emergency YES, and a recommended green time of 12 s (pre-empt). "
              "The detection table lists every box with class, confidence and corners. The third screen runs YOLOv8n on the bundled street photograph: one bus is found at confidence 0.87 and no light-bar cluster, as expected for a photograph without an emergency vehicle. "
              "These screens show the mechanism working; Section 8.7 measures it on real photographs, where the synthetic-scene success does not carry over.")]
    out += [S(*item("13")), S(*item("14"))]
    out += [P("The prediction page reports the shipped forecaster as the application trains it at start-up: 26,988 samples, MAE 1.64 vehicles, R2 0.961 and 35 % lower error than the persistence rule *the queue stays the same*; the scatter shows 1,500 random held-out points close to the diagonal and the importance chart shows that the current queue (0.692) and the queue 30 s ago (0.133) dominate. "
              "The comparison table lists persistence (MAE 2.535), Random Forest (1.605) and Gradient Boosting (1.644, used). The live forecast bars compare the queue now with the 30 s forecast for each of the 16 approaches and name the approach with the largest predicted build-up (here J2, S approach, 0 to 3 vehicles). "
              "The screen therefore presents the favourable random-split numbers; the held-out-simulation result that qualifies them is in Section 8.6.")]
    out += [S(*item("15")), S(*item("16"))]
    out += [P("The violations page shows the log of the live simulation after 16 simulated minutes: 11 events (8 red-light jumping, 3 wrong-way driving) with an average confidence of 0.94, charts by junction and by minute, and an evidence log with a plate, a vehicle class and a confidence per event. "
              "The lower table lists the average red-light and wrong-way events per controller from the last benchmark. These events are generated by the simulator from ground-truth red-light runners and wrong-way drivers, and the plate and the confidence (drawn between 0.86 and 0.99) are generated too; the page title says *detection*, but no model detects anything, as Section 8.7 and Chapter 10 state.")]
    out += [S(*item("17")), S(*item("18"))]
    out += [P("The About page lists the base paper with its DOI and a table of what is adopted from it and what is added: YOLO detection, emergency-aware control (the base paper pre-empts at one junction; FlowSense looks 15 s upstream for a route-wide green wave), validation (SUMO in the base paper, a built-in simulator here) and the extensions named in the batch abstract. "
              "The pipeline diagram and the controller list repeat the design of Chapter 5 inside the product. The About page's wording *violation detector* is the interface's label for the simulated violation log."),
          ]
    if True:
        out += [S("19_live_control_light.png", "Output screen: Live control centre in the light theme.", 5.0, 3.5),
                P("Every page of the console is available in a light and a dark theme; the choice is stored in the browser and follows the operating-system setting on first visit.")]
    return out


def _benchmark():
    d2, d3 = F.derived("2x2"), F.derived("3x3")
    if F.REPORT:
        return _benchmark_report(d2, d3)
    out = [H2("8.3 Controller benchmark"),
           P("Four controllers were run on identical traffic: fixed-time (30 s split), queue-actuated adaptive control, an emergency-aware adaptive controller that emulates the idea of the base paper (pre-emption at the junction a light-bar is seen at, 5 s look-ahead), and the advanced controller of this project. "
             "The first table below gives the 2x2 grid and the second the 3x3 grid; each cell is the mean ± sample standard deviation over five seeds of 1800 simulated seconds at demand x1.2."),
           _ctrl_table("2x2", "Controller benchmark on the 2x2 grid (5 seeds, 1800 s, demand x1.2, mean ± std)"),
           P(f"**Network delay.** The advanced controller reduces average delay per vehicle from 67.8 to 44.2 s against fixed-time (-{d2['delay_cut_advanced_vs_fixed_pct']:.1f} %), but only from 46.2 to 44.2 s against the plain queue-actuated controller (-{d2['delay_cut_advanced_vs_adaptive_pct']:.1f} %), "
             "a difference smaller than one standard deviation of the adaptive controller (4.2 s). Most of the gain over fixed-time therefore comes from being adaptive at all, not from the additional ingredients of the advanced controller. "
             f"Against the base-paper-style controller the reduction is {d2['delay_cut_advanced_vs_basepaper_pct']:.1f} %; that controller is itself {-d2['delay_cut_basepaper_vs_adaptive_pct']:.1f} % *worse* than plain adaptive control on mean delay (49.2 against 46.2 s), which is the price of pre-empting a junction for every ambulance."),
           P(f"**Ambulances.** Ambulance delay falls from 20.1 s (fixed-time) and 20.6 s (adaptive, which ignores ambulances) to 6.0 s for the base-paper-style controller and 5.7 s for the advanced controller, a reduction of {d2['emergency_cut_advanced_vs_fixed_pct']:.1f} % against fixed-time and {d2['emergency_cut_advanced_vs_basepaper_pct']:.1f} % against the base-paper style. "
             "Over five runs 54 ambulances entered the network under every controller (the demand is controller-independent), and the controllers pre-empted 58 times (base-paper style) and 64 times (advanced). "
             f"Idle fuel falls by {d2['fuel_saved_L_advanced_vs_fixed_per_run']:.1f} L per 30-minute run against fixed-time, from 28.9 to 18.4 L under the simulator's idling assumption."),
           _ctrl_table("3x3", "Controller benchmark on the 3x3 grid (5 seeds, 1800 s, demand x1.2, mean ± std)"),
           P(f"On the larger grid the advanced controller reduces delay by {d3['delay_cut_advanced_vs_fixed_pct']:.1f} % against fixed-time, {d3['delay_cut_advanced_vs_adaptive_pct']:.1f} % against adaptive and {d3['delay_cut_advanced_vs_basepaper_pct']:.1f} % against the base-paper style. "
             f"Ambulance delay is {d3['emergency_cut_advanced_vs_fixed_pct']:.1f} % lower than fixed-time (5.6 against 42.4 s) and {d3['emergency_cut_advanced_vs_basepaper_pct']:.1f} % lower than the base-paper style (5.6 against 7.5 s); with nine junctions the ambulance crosses several signals, so pre-empting one junction at a time helps less than a route-wide green wave. "
             f"The base-paper-style controller is {-d3['delay_cut_basepaper_vs_adaptive_pct']:.1f} % worse than adaptive on mean delay and produces more red-light events per run (59.2) than the other controllers (46.8 to 47.8), a side effect of holding red for runners while other approaches are forced green."),
           FIG(F.fig("f01_delay_by_controller.png"), "Average delay per vehicle by controller on the 2x2 and 3x3 grids (mean ± std over 5 seeds).", 5.8),
           FIG(F.fig("f02_emergency_delay.png"), "Ambulance delay by controller on the 2x2 and 3x3 grids (mean ± std over 5 seeds).", 5.8)]
    if not F.REPORT:
        out += [FIG(F.fig("f11_queue_timeseries.png"), "Total queued vehicles over time for the four controllers (2x2 grid, seed 40).", 5.6)]
    out += [P("The per-seed spread is large for fixed-time (average delay 86.1, 69.3, 63.5, 61.6 and 58.3 s over seeds 40-44), because a fixed split cannot absorb the demand fluctuations of a given seed, and small for the advanced controller (49.0, 43.3, 44.0, 42.0 and 42.8 s). "
              "The advanced controller had the lowest delay on four of the five seeds (on seed 43 the adaptive controller was marginally lower, 41.8 against 42.0 s), and its lead over the adaptive controller is below 4 s on every seed, so the claim that is supported is *adaptive control is much better than fixed-time; the advanced additions help a little*.")]
    return out


def _benchmark_report(d2, d3):
    return [H2("8.3 Controller benchmark"),
            P("Four controllers ran on identical traffic: fixed-time (30 s split), queue-actuated adaptive control, an emergency-aware controller that emulates the idea of the base paper (pre-emption at the junction where a light-bar is seen, 5 s look-ahead), and the advanced controller of this project. "
              "Each cell is the mean ± sample standard deviation over five seeds of 1800 simulated seconds at demand x1.2."),
            _ctrl_table("2x2", "Controller benchmark on the 2x2 grid (5 seeds, 1800 s, demand x1.2, mean ± std)"),
            _ctrl_table("3x3", "Controller benchmark on the 3x3 grid (5 seeds, 1800 s, demand x1.2, mean ± std)"),
            P(f"**Network delay.** On the 2x2 grid the advanced controller cuts average delay from 67.8 to 44.2 s against fixed-time (-{d2['delay_cut_advanced_vs_fixed_pct']:.1f} %; -{d3['delay_cut_advanced_vs_fixed_pct']:.1f} % on 3x3) but only from 46.2 to 44.2 s against plain adaptive control (-{d2['delay_cut_advanced_vs_adaptive_pct']:.1f} %; -{d3['delay_cut_advanced_vs_adaptive_pct']:.1f} % on 3x3), "
              "less than one standard deviation of the adaptive controller (4.2 s). Most of the gain over fixed-time comes from being adaptive at all. "
              f"Against the base-paper-style controller the reduction is {d2['delay_cut_advanced_vs_basepaper_pct']:.1f} % (2x2) and {d3['delay_cut_advanced_vs_basepaper_pct']:.1f} % (3x3); that controller is itself {-d2['delay_cut_basepaper_vs_adaptive_pct']:.1f} % and {-d3['delay_cut_basepaper_vs_adaptive_pct']:.1f} % *worse* than plain adaptive control on mean delay, the price of pre-empting a junction for every ambulance, and on 3x3 it also produces more red-light events per run (59.2 against 46.8 to 47.8)."),
            P(f"**Ambulances.** Ambulance delay falls from 20.1 s (fixed-time) and 20.6 s (adaptive, which ignores ambulances) to 6.0 s (base-paper style) and 5.7 s (advanced) on 2x2: {d2['emergency_cut_advanced_vs_fixed_pct']:.1f} % below fixed-time and {d2['emergency_cut_advanced_vs_basepaper_pct']:.1f} % below the base-paper style. "
              f"On 3x3 it is 5.6 s against 42.4 s (fixed, -{d3['emergency_cut_advanced_vs_fixed_pct']:.1f} %) and 7.5 s (base-paper style, -{d3['emergency_cut_advanced_vs_basepaper_pct']:.1f} %): with nine junctions an ambulance crosses several signals, so a route-wide green wave helps more than pre-empting one junction at a time. "
              f"Over five runs 54 ambulances entered the 2x2 network under every controller (demand is controller-independent), pre-empted 58 times (base-paper style) and 64 times (advanced); idle fuel falls by {d2['fuel_saved_L_advanced_vs_fixed_per_run']:.1f} L per run against fixed-time."),
            PAIR([(F.fig("f01_delay_by_controller.png"), "Average delay per vehicle by controller, 2x2 and 3x3 (mean ± std, 5 seeds)."),
                  (F.fig("f02_emergency_delay.png"), "Ambulance delay by controller, 2x2 and 3x3 (mean ± std, 5 seeds).")], 3.0),
            P("The per-seed spread is large for fixed-time (86.1, 69.3, 63.5, 61.6, 58.3 s over seeds 40-44) and small for the advanced controller (49.0, 43.3, 44.0, 42.0, 42.8 s); its lead over adaptive control is below 4 s on every seed, so the supported claim is that *adaptive control is much better than fixed-time and the advanced additions help a little*.")]


def _sweep_emergency():
    rows = []
    for i, lv in enumerate(F.SW["levels"]):
        rows.append([f"x{lv}"] + [f"{F.SW['series'][c][i]['delay_mean']:.1f}" for c in CK])
    erows = []
    for c in CK:
        r = F.EM["results"][c]
        erows.append([F.CTRL_LABEL[c], str(r["n"]), f"{r['mean']:.1f}", f"{r['median']:.0f}", f"{r['p90']:.0f}", f"{r['max']:.0f}", f"{r['network_delay']:.1f}"])
    return [H2("8.4 Demand sweep and emergency-heavy traffic"),
            P("To see where each controller helps, the demand multiplier was swept from x0.6 to x1.8 on the 2x2 grid (three seeds, 1200 s per run). The table gives the average delay per vehicle."),
            TAB("Average delay per vehicle (s) against demand, 2x2 grid, 3 seeds, 1200 s", ["Demand", "Fixed-time", "Adaptive", "Emergency-aware", "Advanced AI"], rows,
                widths=[1.0, 1.3, 1.3, 1.5, 1.3], align=["c", "c", "c", "c", "c"], size=10),
            FIG(F.fig("f03_demand_sweep.png"), "Average delay per vehicle against demand for the four controllers (2x2 grid, 3 seeds).", 4.6),
            P("The ordering is stable from x0.9 to x1.8, with fixed-time worst; the advanced controller is lowest from x1.2 (41.1 s against 42.2 s for adaptive) to x1.8 (127.6 against 135.3 s). "
              "At light demand it is **worse** than plain adaptive control (26.4 against 20.6 s at x0.6, 30.2 against 27.2 s at x0.9): its forecast and inbound-platoon terms hold green for traffic that has not yet arrived, which is waste on near-empty roads. "
              "A deployment would need a demand-dependent switch back to the plain adaptive rule; the project does not implement one."),
            P("A second test raised the ambulance rate to one per minute on average (3600 s, five seeds, demand x1.2): roughly 285 ambulances per controller instead of 54."),
            TAB("Ambulance delay and network delay under emergency-heavy traffic (2x2 grid, 3600 s, 5 seeds)", ["Controller", "Ambulances", "Mean (s)", "Median (s)", "p90 (s)", "Max (s)", "Network delay (s)"], erows,
                widths=[2.0, 0.8, 0.7, 0.8, 0.7, 0.7, 0.9], align=["l", "c", "c", "c", "c", "c", "c"], size=9.5),
            P("Both pre-empting controllers cut the mean ambulance delay by about three quarters (6.4 and 5.3 s against 20.7 s for fixed-time and 23.4 s for adaptive) and the worst case from 42 s (fixed) and 80 s (adaptive) to 26 and 24 s. "
              "Pre-emption has a price for everybody else: network delay is 50.1 s for adaptive control, 57.7 s for the base-paper style and 50.9 s for the advanced controller, which recovers most of the cost through its queue-aware pressure and green wave. "
              "The median ambulance delay is 7 s for both; the advanced controller's advantage is in the mean (5.3 against 6.4 s), clearing " + f"{100 * F.EM['results']['advanced']['zero_delay_share']:.0f} % of ambulances with no delay at all.")]


def _ablation():
    rows = []
    for k, m in F.AB["results"].items():
        rows.append([k, f"{m['Avg delay / vehicle (s)']['mean']:.1f} ± {m['Avg delay / vehicle (s)']['std']:.1f}", f"{m['Avg queue (veh)']['mean']:.1f}", f"{m['Emergency delay (s)']['mean']:.1f}"])
    return [H2("8.5 Ablation of the advanced controller"),
            P("To find out which ingredient of the advanced controller matters, each was removed in turn (2x2 grid, demand x1.2, 1800 s, five seeds) by subclassing the simulator in the experiment script, without changing the product code."),
            TAB("Ablation of the advanced controller", ["Variant", "Avg delay (s)", "Avg queue (veh)", "Ambulance delay (s)"], rows, widths=[2.6, 1.4, 1.3, 1.4], align=["l", "c", "c", "c"], size=10),
            *([] if F.REPORT else [FIG(F.fig("f04_ablation.png"), "Average delay and ambulance delay for each ablation of the advanced controller (2x2 grid, 5 seeds).", 5.6)]),
            B("**ML forecast:** removing it raises mean delay from 44.2 to 47.4 s (+3.2 s), about one standard deviation, and is the largest effect on network delay among the three efficiency features.",
              "**Platoon look-ahead:** removing it changes mean delay by only +0.7 s (44.9 against 44.2 s), inside the noise.",
              "**Emergency green wave** (15 s look-ahead): removing it leaves network delay unchanged (44.5 s) but raises ambulance delay from 5.7 to 9.0 s.",
              "**Emergency pre-emption altogether:** network delay is the lowest of all variants (42.4 s) but ambulance delay is 27.3 s, nearly five times higher: the efficiency against safety trade-off in one row."),
            P("With five seeds and standard deviations of 2.2 to 3.9 s, only the ambulance effects and the pre-emption trade-off are clearly separated from noise.")]


def _forecaster():
    rs, lo = F.PR["random_split_5x"], F.PR["leave_one_simulation_out"]
    rows = []
    for m in rs:
        rows.append([m, f"{rs[m]['mae_mean']:.3f} ± {rs[m]['mae_std']:.3f}", f"{rs[m]['r2_mean']:.3f}", f"{lo[m]['mae_mean']:.2f} ± {lo[m]['mae_std']:.2f}", f"{lo[m]['r2_mean']:.2f}"])
    g = lo["Gradient Boosting (used)"]["mae_per_fold"]
    p = lo["Persistence"]["mae_per_fold"]
    frows = [[f"Run {i + 1}", "2x2" if i % 2 == 0 else "3x3", f"{a:.2f}", f"{b:.2f}", "yes" if a < b else "**no**"] for i, (a, b) in enumerate(zip(g, p))]
    out = [H2("8.6 Queue forecaster"),
           P(f"The forecaster predicts each approach's queue 30 s ahead from {F.PR['n_features']} features. It was evaluated twice: with the random 75/25 split used by the application (five different splits), and by leaving one whole simulation run out at a time (six folds), which is the fair test because snapshots from the same run are near-duplicates of each other."),
           TAB("Forecast error by validation scheme (30 s horizon, 26,988 samples)", ["Model", "Random split MAE", "Random split R2", "Leave-one-run-out MAE", "Leave-one-run-out R2"], rows,
               widths=[1.8, 1.3, 0.9, 1.4, 1.0], align=["l", "c", "c", "c", "c"], size=9.5),
           P("On the random split the gradient-boosting model in the product reaches MAE 1.642 ± 0.011 and R2 0.959 against 2.565 and 0.896 for persistence (-36 % MAE); the Random Forest is as good (1.609) and ridge regression is barely better than persistence (2.446). "
             "As the application trains it (one split) the figures are MAE 1.644 and R2 0.961, as on the Prediction screen. The current queue (importance 0.692) and the queue 30 s earlier (0.133) dominate, so the model mostly extrapolates the recent trend."),
           FIG(F.fig("f05_forecaster_validation.png"), "Forecast MAE by model for the random split and for leave-one-simulation-out validation, with the per-run comparison of gradient boosting against persistence.", 5.8),
           *([] if F.REPORT else [TAB("Leave-one-simulation-out MAE, gradient boosting against persistence", ["Held-out run", "Grid", "Gradient boosting MAE", "Persistence MAE", "Boosting better?"], frows,
               widths=[1.2, 0.8, 1.6, 1.4, 1.3], align=["c", "c", "c", "c", "c"], size=10)]),
           P("Held out by run, the picture changes. Gradient boosting beats persistence in five of the six runs (for example 0.68 against 0.87 and 1.47 against 2.08), but in run 4 - the 3x3 grid at demand x1.6 starting at 17:00, the only heavily congested run, with queues up to 138 vehicles while the other five runs peak at 16 or fewer - its error is 14.66 against 5.49, and the mean R2 over folds is only 0.04. "
             "A tree ensemble cannot predict outside the range it was trained on, and `predict` also clips to 40 vehicles. The forecaster is useful inside the congestion range it has seen and unreliable outside it, and the random-split R2 of 0.96 overstates what a deployment would experience; in closed loop it is worth about 3 s of mean delay (Section 8.5)."),
           ]
    if not F.REPORT:
        out += [FIG(F.fig("f06_forecast_scatter_importance.png"), "Predicted against actual 30 s queue for the shipped model on held-out random rows, and the gradient-boosting feature importance.", 5.8)]
    return out


def _vision():
    vs = F.VS["results"]
    vrows = []
    names = {"clean": "Clean", "gaussian_noise_sigma10": "Gaussian noise, sigma 10", "gaussian_noise_sigma25": "Gaussian noise, sigma 25", "brightness_x0.6": "Brightness x0.6", "gaussian_blur_7x7": "Gaussian blur 7x7"}
    for k, v in vs.items():
        vrows.append([names[k], f"{v['recall']:.3f}", f"{v['precision']:.3f}", f"{v['class_accuracy_of_matched']:.3f}", f"{v['ambulance_recall']:.3f}", f"{v['ambulance_false_alarm_rate']:.3f}"])
    m = F.VR["mixed_traffic"]
    mrows = []
    for k, v in m["per_class"].items():
        mrows.append([k, str(v["n_gt"]), str(v["tp"]), str(v["fp"]), str(v["fn"]), f"{v['precision']:.3f}", f"{v['recall']:.3f}", f"{v['f1']:.3f}"])
    a = F.VR["ambulance_classification"]
    arows = []
    for k, lab in (("lightbar_cluster_any", "Any red+blue light-bar cluster in the frame"), ("ambulance_flag_yolo_plus_lightbar", "YOLOv8n box with a light bar on it (the application's *ambulance* class)")):
        v = a[k]
        arows.append([lab, str(v["tp"]), str(v["fp"]), str(v["fn"]), str(v["tn"]), f"{v['precision']:.3f}", f"{v['recall']:.3f}", f"{v['f1']:.3f}", f"{v['false_alarm_rate']:.3f}"])
    y = F.VY["sample_photo"]
    out = [H2("8.7 Vision layer and violation log"),
           H3("8.7.1 Synthetic overhead scenes"),
           P("The classical contour detector and the light-bar rule were run on 300 rendered scenes (3 to 14 vehicles, ambulance in about 44 % of them, both flash frames), matching boxes with intersection-over-union of at least 0.3. This test is in-domain by construction: the same author wrote the renderer and the detector."),
           TAB("Synthetic-scene detection under image degradations (300 scenes, 2,754 vehicles)", ["Condition", "Recall", "Precision", "Class accuracy", "Ambulance recall", "Ambulance false alarms"], vrows,
               widths=[1.9, 0.8, 0.9, 1.0, 1.1, 1.2], align=["l", "c", "c", "c", "c", "c"], size=9.5),
           *([] if F.REPORT else [FIG(F.fig("f07_vision_synthetic_robustness.png"), "Vehicle recall and ambulance recall of the classical detector on synthetic scenes under noise, darkening and blur.", 5.4)]),
           P("On clean scenes recall is 0.976, precision 1.000, class accuracy 0.961 and the ambulance is found in every scene that contains one (recall 1.000, 0.6 % false alarms); the vehicle count is exact in 80 % of scenes with a mean absolute error of 0.22. "
             "The detector is brittle, though: Gaussian noise with sigma 10 already produces **no detections at all** because the road-segmentation thresholds fail, darkening to 60 % keeps vehicle recall at 0.874 but loses **every** light bar, and a 7x7 blur halves ambulance recall (0.508). "
             "YOLOv8n finds nothing in these synthetic scenes (a domain gap), so the two detectors are not interchangeable."),
           H3("8.7.2 YOLOv8n on real mixed-traffic frames"),
           P(f"YOLOv8n with the application's default confidence 0.3 was run on the 293 real dashcam frames of the Visaitech dataset [{R['ds_traffic']}] (no tuning, IoU 0.5 matching, predicted classes mapped to the dataset's taxonomy: bike to 2-wheeler, car/bus/truck to 4-wheeler)."),
           TAB("YOLOv8n on 293 real mixed-traffic frames (confidence 0.3, IoU 0.5)", ["Class", "Boxes", "TP", "FP", "FN", "Precision", "Recall", "F1"], mrows,
               widths=[1.6, 0.7, 0.6, 0.6, 0.7, 0.8, 0.8, 0.7], align=["l", "c", "c", "c", "c", "c", "c", "c"], size=10),
           *([] if F.REPORT else [FIG(F.fig("f12_real_vision_per_class.png"), "Precision and recall of YOLOv8n per class on the 293 real mixed-traffic frames.", 5.2)]),
           P(f"For cars, buses and trucks (4-wheelers) precision is 0.609 and recall 0.586. Two-wheelers, which are 859 of the 1,467 boxes, are mostly missed (recall 0.083, precision 0.441), and auto-rickshaws (3-wheelers) are never matched because COCO has no such class. "
             f"Across all vehicle classes recall is {m['per_class']['any vehicle class']['recall']:.3f} and precision {m['per_class']['any vehicle class']['precision']:.3f}; the per-image count error is {m['count_mae_per_image']:.2f} vehicles and inference takes {m['latency_ms_mean']:.1f} ms on the CPU (median {m['latency_ms_median']:.1f} ms), i.e. about 31 frames per second at 640x480. "
             "A stock COCO detector is a poor counter for South Asian mixed traffic: objective 1 is met for speed but not for accuracy, and fine-tuning on a dataset such as this one is the next step."),
           H3("8.7.3 The light-bar rule on real ambulance photographs"),
           TAB("Emergency-vehicle rules on 300 real ambulance and 300 real non-ambulance photographs", ["Rule", "TP", "FP", "FN", "TN", "Precision", "Recall", "F1", "False-alarm rate"], arows,
               widths=[2.1, 0.4, 0.4, 0.5, 0.5, 0.7, 0.6, 0.5, 0.8], align=["l", "c", "c", "c", "c", "c", "c", "c", "c"], size=9),
           *([PAIR([(F.fig("f12_real_vision_per_class.png"), "Precision and recall of YOLOv8n per class on the 293 real frames."),
                    (F.fig("f08_ambulance_real_confusion.png"), "Confusion matrix of the light-bar rule on 600 real photographs.")], 3.0)]
             if F.REPORT else [FIG(F.fig("f08_ambulance_real_confusion.png"), "Confusion matrix of the light-bar rule on 600 real photographs (300 ambulance, 300 non-ambulance).", 4.6)]),
           P("On real photographs the rule almost never fires: 4 of 300 ambulance photos contain a red-and-blue cluster that passes the thresholds (recall 0.013) and only 2 of 300 produce an *ambulance* box (recall 0.007), with 1 and 0 false alarms in the 300 non-ambulance photos. "
             "Most of the photographs show daylight scenes with the lights off or in colours that miss the saturation and brightness limits (S at least 120, V at least 190). YOLOv8n did find at least one vehicle in 93.3 % of the ambulance photographs, so the first stage works and the second stage is the failure. "
             "Looking at the images shows that even the few hits are not what they seem: the four ambulance photographs that triggered a cluster were flagged on red-and-blue livery stripes, a flag graphic or a star-of-life rather than on roof lights, and the one non-ambulance photograph that triggered it showed a blue car, so the rule responds to red-and-blue colour, not to emergency lights, and a recall of 0.013 overstates it. "
             "The 100 % ambulance recall on synthetic scenes does **not** transfer to real images. The base paper's trained single-class YOLO26m light-bar detector reports precision 0.73, recall 0.69 and mAP50 0.73 on a 3,130-image set; this project did not train a detector and does not reach that standard."),
           H3("8.7.4 Sample photograph and violation log"),
           P(f"On the bundled sample photograph YOLOv8n finds one bus (confidence 0.873) and no light-bar cluster; latency over 20 runs after warm-up is {y['latency_ms_mean']:.1f} ms mean, {y['latency_ms_median']:.1f} ms median and {y['latency_ms_p95']:.1f} ms 95th percentile on the CPU. "
             "The violation log has no accuracy to report: red-light jumping (5 % of cars, released after waiting 25 s on red) and wrong-way driving (probability 0.0003 per entry second) are produced by the simulator, and the plate and confidence of each row are random draws. "
             "In the benchmark, red-light events are a property of the traffic (about 19 to 20 per run on 2x2 for every controller) and wrong-way events are identical (5.0) for all controllers.")]
    return out


def _perf():
    if F.REPORT:
        th = F.TH
        return [H2("8.8 Performance and testing"),
                P("API response times were measured at 127.0.0.1 (using `localhost` adds about 2 s per call here); Chapter 7 gives the full table. Everyday calls complete in 3 to 30 ms; a 300 s simulation skip takes about 100 ms; the YOLOv8 sample-photo route averaged 503 ms because the first call loads the weights (95th percentile 3.7 s), while the detector alone takes about 51 ms. "
                  "The first benchmark of four controllers by three seeds of 1800 s takes 4.8 s, a repeat is served from the cache in 12 ms, and the demand sweep takes 4.0 s. "
                  f"The simulator runs 1800 simulated seconds in {th['2x2/fixed']['wall_s']:.2f} s (2x2 fixed) to {th['3x3/advanced']['wall_s']:.2f} s (3x3 advanced), 3,500 to 10,900 times real time, and a forecast of 16 rows takes {th['predictor_batch16_ms']:.2f} ms. "
                  f"The pytest suite has {F.PYTEST_TOTAL} tests ({F.PYTEST_ENGINE} engine, {F.PYTEST_API} API) and all {F.PYTEST_PASSED} passed in about {F.PYTEST_SECONDS} s; `scripts/smoke_test.py` passed {F.SMOKE_PASSED} of {F.SMOKE_TOTAL} end-to-end checks. Concurrent users, load, penetration testing and real camera or signal hardware were not tested.")]
    rows = []
    for r in F.API["results"]:
        rows.append([r["endpoint"].split(":")[0] if ":" in r["endpoint"] else r["endpoint"], f"{r['mean_ms']:.1f}", f"{r['p95_ms']:.1f}" if "p95_ms" in r else "-"])
    th = F.TH
    out = [H2("8.8 Performance and testing"),
           P("API response times were measured against the running backend at 127.0.0.1 (using `localhost` adds about 2 s per call on this machine through an IPv6 fall-back and would distort the figures); 20 calls per endpoint unless noted."),
           TAB("API latency (ms)", ["Endpoint", "Mean", "95th percentile"], rows, widths=[3.8, 1.0, 1.4], align=["l", "c", "c"], size=9.5)]
    if not F.REPORT:
        out += [FIG(F.fig("f10_api_latency.png"), "Mean API response time per endpoint (log scale), 127.0.0.1.", 5.4)]
    out += [P("Everyday calls complete in 3 to 30 ms; a 300 s simulation skip takes about 100 ms; the YOLOv8 sample-photo route averaged 503 ms over ten calls because the first call loads the weights (95th percentile 3.7 s), while the detector alone takes about 51 ms on that photograph. "
              "The first benchmark of four controllers by three seeds of 1800 s takes 4.8 s, a repeat is served from the cache in 12 ms, and the demand sweep takes 4.0 s. "
              f"The simulator itself runs 1800 simulated seconds in {th['2x2/fixed']['wall_s']:.2f} s (2x2 fixed) to {th['3x3/advanced']['wall_s']:.2f} s (3x3 advanced), i.e. 3,500 to 10,900 times faster than real time, and a forecast of 16 rows takes {th['predictor_batch16_ms']:.2f} ms. "
              "The predictor trains once at start-up in about 6 s."),
          P(f"Testing: the pytest suite has {F.PYTEST_TOTAL} tests and all {F.PYTEST_PASSED} passed in about {F.PYTEST_SECONDS} s ({F.PYTEST_ENGINE} for the engine, predictor and vision rules and {F.PYTEST_API} for the API through FastAPI's test client), and `scripts/smoke_test.py` passed {F.SMOKE_PASSED} of {F.SMOKE_TOTAL} end-to-end checks against the running server. "
            "Chapter 7 describes them. Concurrent users, load, penetration testing and any real camera or signal hardware were not tested.")]
    return out


def _compare():
    bp = F.BASE_PAPER_RESULTS
    d2 = F.derived("2x2")
    amb_adapt = 100 * (1 - F.gm("2x2", "advanced", "Emergency delay (s)")[0] / F.gm("2x2", "adaptive", "Emergency delay (s)")[0])
    rows = [
        ["Test bed", "SUMO model of the Souissi roundabout, Rabat; one scenario (demand scale 12, ambulance at 330 s)", "In-house simulator; 2x2 and 3x3 junction grids; 5 seeds; ambulances at random entry roads"],
        ["Comparators", "Fixed-time, GA-SGD optimised control, GA-SGD + vision override", "Fixed-time, queue-actuated adaptive, base-paper-style emergency-aware, advanced"],
        ["Ambulance metric", "Travel time 56 s (proposed) vs 70 s (GA-SGD) vs 64 s (fixed): -20.0 % and -12.5 %", f"Ambulance delay 5.7 s vs 20.6 s (adaptive) vs 20.1 s (fixed): -{amb_adapt:.1f} % and -{d2['emergency_cut_advanced_vs_fixed_pct']:.1f} %"],
        ["Ambulance waiting", "15 s vs 21 s (GA-SGD) vs 22 s (fixed): -28.6 % and -31.8 %", "Same quantity as the delay row above (queue wait; no separate travel time)"],
        ["Network metric", "Total waiting 19,887 s vs 22,827 s (GA-SGD) vs 33,719 s (fixed): -12.9 % and -41.0 %; mean wait 14.154 s vs 16.247 s vs 23.999 s", f"Mean delay 44.2 s vs 46.2 s (adaptive) vs 67.8 s (fixed): -{d2['delay_cut_advanced_vs_adaptive_pct']:.1f} % and -{d2['delay_cut_advanced_vs_fixed_pct']:.1f} %"],
        ["Detector", "YOLO26m, one class (light-bar), 3,130 images (2,599 / 266 / 265), 100 epochs, T4 GPU; P 0.73, R 0.69, mAP50 0.73, mAP50-95 0.34 (3-run means)", "No trained detector: stock YOLOv8n (COCO) + HSV light-bar rule; real photos: light-bar recall 0.013, 4-wheeler recall 0.586"],
        ["Detector speed", "11.45-13.89 ms per frame on an NVIDIA T4 GPU", f"{F.VR['mixed_traffic']['latency_ms_mean']:.1f} ms per 640x480 frame on a CPU (YOLOv8n)"],
        ["Pre-emption events", "One pre-emption in the selected scenario", "54 ambulances per 5 runs (2x2); 58 and 64 pre-emptions (base-paper style, advanced)"],
        ["Extensions beyond the base paper", "None (single junction)", "30 s queue forecast, inter-junction look-ahead, spill-back avoidance, violation log, web console"],
    ]
    if F.REPORT:
        rows = [r for r in rows if r[0] not in ("Ambulance waiting", "Pre-emption events", "Comparators")]
    return [H2("8.9 Comparison with the base paper"),
            P(f"The base paper [{R['base']}] reports a trained detector and a SUMO study; FlowSense reports a simulator study and an untrained detector. **The two sets of numbers are not comparable in absolute terms**: the data are different (3,130 annotated light-bar images against public real photographs and rendered scenes), the test beds are different (one SUMO roundabout against four-junction and nine-junction grids of a purpose-built simulator), the traffic demand is different, and the quantities are not defined in the same way (ambulance *travel time* against ambulance *queue delay*). "
              "The table sets them side by side only to show what each study measured; the percentages are relative reductions inside each study."),
            TAB("Base paper against FlowSense: what was measured (different test beds)", ["Aspect", "Base paper [1]", "FlowSense (this project)"], rows, widths=[1.2, 2.7, 2.7], align=["l", "l", "l"], size=9),
            *([] if F.REPORT else [FIG(F.fig("f09_base_paper_comparison.png"), "Relative reductions reported by the base paper in SUMO and measured by FlowSense in its own simulator (different test beds; indicative only).", 5.6)]),
            P("What can be said: both studies find that giving an emergency vehicle priority cuts its delay by a clear margin without much harm to the network (the base paper lowers total waiting by 12.9 % against GA-SGD; here the advanced controller keeps network delay within 0.8 s of adaptive control under heavy ambulance traffic, 50.9 against 50.1 s). "
              "What cannot be said: that FlowSense detects emergency vehicles as well as the base paper's detector (it does not, Section 8.7), that its percentages would reproduce in SUMO, or that it beats the base paper. "
              "The project goes beyond the base paper in the breadth of the pipeline (forecasting, coordination, a working console) and in the ablation and held-out evaluations.")]


def _samples():
    rep_ = F.REPORT
    sio = json.load(open(os.path.join(F.DOCS, "metrics", "sample_io.json"), encoding="utf-8"))
    v, lv, vr = sio["vision"], sio["live"], sio["viol_row"]
    lk = lv["kpis"]
    login = ('POST /api/auth/login\n{"email": "operator@flowsense.app", "password": "Flow@1234"}\n\n'
             '200 {"token": "eyJhbGciOiAiSFMyNTYi...", "user": {"name": "Control Room Operator", "email": "operator@flowsense.app"}}\n\n'
             'POST /api/auth/login  {"email": "x@y.io", "password": "bad"}\n'
             '401 {"detail": {"message": "Email or password is incorrect.", "hint": "Use the demo operator account shown on the sign-in page."}}')
    live = ('PUT /api/live/config  {"controller": "advanced", "demand": 1.4, "emergencies": true, "use_ml": false}\n'
            'POST /api/live/step    {"seconds": 120}\n\n'
            f'200 {{"t": {lv["t"]}, "clock": "{lv["clock"]}", "config": {json.dumps(lv["config"])},\n'
            f'     "kpis": {json.dumps({k: lk[k] for k in ("demand_mult", "in_network", "queued", "avg_delay", "throughput", "violations", "preemptions")})},\n'
            f'     "banner": null, "junctions": [{{"junction": "J1", "green": "North-South (clearing)", "timer": 21, "queue": "7/6/1/12", "forecast": "0/0/0/0", "preempt": false}}, ...],\n'
            '     "map": {"roads": [...], "signals": [16 items], "vehicles": [...], "labels": [...]}, "queue_series": [...]}  (abridged)')
    bench = ('POST /api/benchmark  {"grid": "2x2", "seconds": 1800, "demand": 1.2, "seeds": 3, "start_hour": 8, "use_ml": true}\n\n'
             '200 {"settings": {...}, "kpis": {"d_fixed": 38, "d_paper": 11, "e_fixed": 73, "emg_ours": 5.1, "emg_base": 18.7, "fuel": 12.4, "co2": 28.6},\n'
             '     "controllers": {"fixed": {"delay_mean": 72.95, ...}, "adaptive": {...}, "emergency": {...}, "advanced": {"delay_mean": 45.42, "emg_mean": 5.1, ...}},\n'
             '     "table": [4 rows], "columns": [...]}  (abridged; the same run as the Benchmark screens)\n\n'
             'POST /api/benchmark  {"seconds": 10}\n'
             '422 {"detail": {"message": "Benchmark settings are out of range.", "hint": "Duration 5-60 min, demand 0.5-1.8, 1-5 seeds, start hour 0-23."}}\n'
             'PUT /api/live/config  {"demand": 9}\n'
             '422 {"detail": {"message": "Invalid input for demand: Input should be less than or equal to 2", "hint": "Check the value and try again."}}')
    vis = ('GET /api/vision/synthetic?vehicles=9&ambulance=true&flash=A&seed=3\n\n'
           f'200 {{"source": "synthetic", "width": {v["width"]}, "height": {v["height"]}, "truth_count": {v["truth_count"]}, "lightbars": {v["lightbars"]},\n'
           f'     "report": {json.dumps(v["report"])},\n'
           f'     "detections": [{json.dumps(v["detections"][0])}, ...] ({v["n_detections"]} in all), "frame": "data:image/jpeg;base64,...", "annotated": "data:image/jpeg;base64,..."}}')
    pred = ('GET /api/prediction\n\n'
            '200 {"kpis": {"samples": 26988, "mae": 1.64, "r2": 0.961, "vs_persistence": 35, "fit_seconds": ...},\n'
            '     "metrics": [{"model": "Persistence baseline", "mae": 2.535, "r2": 0.904}, {"model": "Random Forest", "mae": 1.605, "r2": 0.962},\n'
            '                 {"model": "Gradient Boosting (used)", "mae": 1.644, "r2": 0.961}], "scatter": [1,500 points], "importance": [11 features]}  (abridged)')
    viol = ('GET /api/violations   (one row of the log; plate and confidence are simulator draws)\n\n'
            f'     {{"time": "08:00:28", "junction": "J{vr["junction"]}", "approach": "{vr["approach"]}", "kind": "{vr["kind"]}", "plate": "{vr["plate"]}", "vehicle": "{vr["vehicle"]}", "confidence": {vr["confidence"]}}}')
    return [H2("8.10 Sample inputs and outputs"),
            P("The snippets below are real request and response shapes of the running API (abridged where marked); values come from the experiments or from a short real run of the same code. Every call except health, login, the demo account and the public pulse needs the header `Authorization: Bearer <token>`."),
            *([H3("Live control, benchmark errors and vision"), CODE(live, 7.6), CODE(bench.split("\n\n")[-1].replace("POST /api/benchmark", "POST /api/benchmark"), 7.6), CODE(vis, 7.6)] if rep_ else
              [H3("Sign-in"), CODE(login, 8), H3("Live control"), CODE(live, 8), H3("Benchmark and validation errors"), CODE(bench, 8),
               H3("Vision, prediction and violations"), CODE(vis, 8), CODE(pred, 8), CODE(viol, 8)])]


def _cases():
    out = [H2("8.11 Success and failure analysis"),
           P("The four photographs below are real images from the two public datasets, processed by the application's own vision code, chosen to show what works and what does not (the selection is illustrative, not a sample for statistics)."),
           FIG(F.fig("f13_real_examples.png"), "Real photographs processed by the vision layer: a detection result, a miss, a light-bar hit and a light-bar miss (images from CC BY 4.0 datasets).", 5.8),
           P("The top-left frame is the best case of the 293 (4 of 8 vehicles found), the top-right frame the worst (0 of 8: motorcycles and a rickshaw that COCO does not describe). In the bottom-left photograph the rule fires and YOLOv8n labels the vehicle *ambulance*, but the three magenta clusters sit on the red-and-blue livery stripes of the vehicle body rather than on a lit light bar, so even this *hit* shows that the rule responds to colour, not to a flashing light. "
             "In the bottom-right photograph a clearly visible ambulance is labelled *bus* by the stock detector and no light bar is found, the typical failure of the 296 misses."),
           H3("What worked"),
           B("**Adaptive control.** Queue-actuated and advanced control cut mean delay by about a third against fixed-time on both grids, with a stable advantage from demand x1.2 upward (Sections 8.3 and 8.4).",
             "**Emergency priority in simulation.** Pre-emption cuts ambulance delay by about 70-87 % against fixed-time, the worst-case ambulance delay from 42 s and 80 s to 24-26 s, and the green wave helps most on the 3x3 grid (Sections 8.3 and 8.4).",
             "**Like-for-like comparison.** The controllers face identical demand and ambulances (verified by a test), so differences are attributable to control.",
             "**Cars, buses and trucks in real frames, and the product itself.** Four-wheelers are found with precision 0.61 and recall 0.59 by a stock model at about 31 frames per second on a CPU; almost every API call answers in about 100 ms or less, and all 38 tests and 33 smoke checks pass."),
           H3("What failed or was weak"),
           B("**Emergency detection on real photographs:** the light-bar rule found 4 of 300 ambulance photos (recall 0.013), so the closed loop *camera sees ambulance, signal pre-empts* is demonstrated only in simulation, where ambulances are known by ground truth.",
             "**Two-wheelers and three-wheelers:** recall 0.083 and 0.000 on real South Asian frames; the density estimate would undercount exactly the vehicles that dominate such traffic.",
             "**Degraded images:** the classical detector returns nothing under mild noise; the light-bar rule is lost under 40 % darkening.",
             "**Forecaster outside its training range:** error 14.66 against 5.49 for persistence on the one heavily congested held-out run; **low demand:** the advanced controller is worse than plain adaptive control at x0.6 and x0.9.",
             "**Pre-emption cost and violations:** the base-paper-style controller raises mean delay above plain adaptive control on both grids, and without pre-emption ambulances wait 27.3 s; violations are simulated, not detected."),
           ]
    return out


def _limits():
    if F.REPORT:
        return [H2("8.12 Limitations of these results"),
                B("The simulator's parameters (saturation flow 0.5 veh/s, link time 12 s, spill-back at 30 vehicles, two-phase signals, 5 % red-light runners) are the authors' assumptions, not calibrated on field data; fuel and CO2 follow from an idling-rate assumption.",
                  "Five seeds (three for the sweep) give wide intervals; differences below about one standard deviation, notably advanced against adaptive, are not established, and the forecaster's random-split scores overstate generalisation.",
                  "The synthetic vision results are in-domain; the real-image tests use two small public sets (293 frames; 600 photographs from the first 300 files of each folder), not a traffic-camera feed. Nothing was tested with real cameras, signal controllers, concurrent users or at city scale.")]
    return [H2("8.12 Limitations of these results"),
            B("The simulator is mesoscopic and its parameters (saturation flow 0.5 veh/s, link time 12 s, spill-back at 30 vehicles, two-phase signals, 5 % red-light runners) are the authors' assumptions; no calibration against field data was done.",
              "Five seeds (three for the sweep) give wide intervals; differences below about one standard deviation, notably advanced against adaptive, are not established.",
              "The synthetic vision results are in-domain; the real-image tests use two small public sets (293 frames; 600 photographs from the first 300 files of each folder), not a traffic-camera feed, and not the base paper's data.",
              "Fuel and CO2 figures follow from an idling-rate assumption and are not measurements.",
              "The forecaster's random-split scores overstate generalisation; its closed-loop value is about 3 s of delay on this simulator.",
              "Nothing was tested with real cameras, signal controllers, concurrent users or at city scale.")]


def _objectives():
    rows = [
        ["1. Detect and classify vehicles in real time with YOLOv8", "**Partly achieved**", "Stock YOLOv8n runs at 32 ms per frame on a CPU; real-frame recall is 0.586 for 4-wheelers, 0.083 for 2-wheelers and 0 for 3-wheelers; no video stream or tracking."],
        ["2. Control signal timing dynamically from density", "**Achieved in simulation**", "Adaptive and advanced control cut delay by 34.8 % (2x2) and 30.5 % (3x3) against fixed-time; the vision density estimate (PCU) exists but is not wired into the simulator."],
        ["3. Priority passage for emergency vehicles", "**Achieved in simulation; detection not achieved**", "Ambulance delay 5.7 s against 20.1 s (2x2) and 5.6 s against 42.4 s (3x3); in simulation ambulances are known by ground truth, and the light-bar rule recalls 1.3 % of real ambulance photos."],
        ["4. Predict congestion with ML and act proactively", "**Partly achieved**", "MAE 1.64 and R2 0.96 on a random split, 35 % better than persistence; fails on an unseen heavily congested run; closed-loop gain about 3 s of delay."],
        ["5. Coordinate neighbouring junctions", "**Partly achieved**", "Platoon look-ahead, spill-back damping and an emergency green wave are implemented in simulation; measured effects are small (+0.7 s delay without look-ahead; ambulance delay 5.7 to 9.0 s without the green wave); no network protocol."],
        ["6. Detect violations (red-light, wrong-way)", "**Partly achieved**", "A violation log with plate and confidence exists, but the events are produced by the simulator; no detector, tracker or number-plate recognition."],
        ["7. Reduce waiting time, congestion and fuel", "**Achieved in simulation**", "Average queue 96.3 to 61.3 vehicles, delay 67.8 to 44.2 s, idle fuel 28.9 to 18.4 L per 30 minutes (2x2, against fixed-time); not measured on real roads."],
        ["8. Improve road safety and management efficiency", "**Not measured**", "Efficiency gains are simulated only; no safety metric (collisions, conflicts) exists in the simulator or in any experiment."],
    ]
    return [H2("8.13 Objectives against outcomes"),
            TAB("The eight project objectives against what was measured", ["Objective", "Status", "Evidence"], rows, widths=[1.8, 1.3, 3.5], align=["l", "l", "l"], size=9),
            P("Taken together, the objectives on control (2, 3, 7) are met in the simulator, the objectives on perception and enforcement (1, 3-detection, 6) are only partly met, and the objective on safety (8) was not evaluated. The summary of key findings is in Chapter 9.")]


def blocks():
    out = [H1("CHAPTER 8: RESULTS AND OUTPUT SCREENS"),
           P("This chapter reports what was measured. It begins with the set-up, shows every screen of the working product, then gives the controller benchmark, the demand sweep, the ablation, the forecaster and the vision evaluation, the performance and test results, the comparison with the base paper, sample inputs and outputs, a success and failure analysis and the objectives against outcomes. "
             "Where a result is weaker than the product's own screens suggest, the text says so."),
           ]
    if F.REPORT:
        out[1] = P("This chapter reports what was measured: the set-up, the main screens of the working product, the controller benchmark, demand sweep, ablation, forecaster and vision evaluation, performance and tests, the comparison with the base paper, sample inputs and outputs, a success and failure analysis and the objectives against outcomes. "
                   "Where a result is weaker than the product's own screens suggest, the text says so.")
    for fn in (_setup, _screens, _benchmark, _sweep_emergency, _ablation, _forecaster, _vision, _perf, _compare, _samples, _cases, _limits, _objectives):
        out += fn()
    return out
