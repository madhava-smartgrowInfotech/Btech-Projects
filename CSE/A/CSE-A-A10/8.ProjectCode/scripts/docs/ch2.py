"""Chapter 2: Literature survey."""

from . import facts as F
from . import lit
from .blocks import B, H1, H2, H3, N, P, TAB
from .refs import CITE as R


def blocks():
    bp = F.BASE_PAPER_RESULTS
    base = R["base"]

    def c(*keys):
        return ", ".join(f"[{R[k]}]" for k in keys)

    tw, tr, aw, atr = bp["total_wait_s"], bp["amb_travel_s"], bp["amb_wait_s"], bp["avg_wait_s"]
    out = [
        H1("CHAPTER 2: LITERATURE SURVEY"),
        H2("2.1 Overview"),
        P("The survey has four purposes: to understand the base paper in depth, to place it among the work on emergency-vehicle priority, vehicle detection, forecasting and signal control, "
          "to identify datasets and algorithms worth reusing, and to find the gap FlowSense fills. The base paper and the papers it cites were read from its text and reference list; two papers archived with this batch (a CNN-LSTM "
          "traffic-management system and a graph-neural-network traffic paper) were read from their PDFs. The batch survey names four more systems (references [" + str(R["s_signaliq"]) + "] to [" + str(R["s_incip"]) + "]); "
          "searches did not find their records, so they are described from their titles only and nothing is claimed for them beyond that."),
        H2("2.2 Base Paper Analysis"),
        P(f"**Title.** {lit.BASE_PAPER_TITLE}. **Authors and venue.** {lit.BASE_PAPER_VENUE} (pp. 104922-104933, doi 10.1109/ACCESS.2026.3710015) [{base}]."),
        H3("2.2.1 Aim and approach"),
        P("The paper starts from a limitation it calls \"emergency blindness\": a traffic controller that has been optimised for ordinary traffic, in this case a hybrid genetic-algorithm and "
          f"stochastic-gradient-descent (GA-SGD) controller from the authors' earlier study [{R['gasgd']}], treats an ambulance like any other vehicle. Conventional pre-emption fixes this "
          "with hardware on vehicles and junctions, which is hard to scale. The authors instead detect the roof-mounted siren or light-bar with a camera and a YOLO detector, independent of whether "
          "the lights are flashing and independent of the vehicle's body shape, on the argument that the light-bar is the one visual cue common to ambulances, fire engines and police vehicles. "
          "The detector is not a replacement for the optimiser: it is a supervisory layer that overrides the optimised plan only while an emergency vehicle is present."),
        H3("2.2.2 Architecture and priority logic"),
        P("The architecture has a steady-state optimisation layer (GA-SGD), a priority override layer (the YOLO26m light-bar module) and a priority arbitrator between them. "
          "The arbitrator counts consecutive frames with a light-bar detected at confidence 0.5 or more; after three (N = 3) and with the vehicle inside the detection zone, it stores the current phase, applies a yellow clearance and forces or extends green on the "
          "emergency approach, then returns control to the optimiser when the vehicle leaves the controlled area."),
        H3("2.2.3 Dataset and detector training"),
        P(f"The detector data are {bp['detector']}. Images come from three open Roboflow Universe sets plus public-domain images, were reviewed by hand, and label only "
          "the light-bar region, lit and unlit, so that the model learns the object rather than the flashing. Training used pretrained Ultralytics weights, SGD (initial learning rate 0.01, momentum 0.937), "
          "early stopping with patience 25 and mosaic and MixUp augmentation; the three runs (default seed, 42 and 123) differ only in the seed."),
        H3("2.2.4 System-level validation"),
        P("To go beyond detector accuracy the authors modelled the Souissi roundabout in Rabat, Morocco, in SUMO and compared three controllers: fixed-time, GA-SGD and GA-SGD with the "
          "vision-triggered override. The paper reports a selected stress scenario (demand scale 12, ambulance departing at 330 s) chosen from a calibrated sweep over demand and departure "
          "time, and notes that the benefit of pre-emption depends on how the ambulance's arrival meets the queue and the signal state."),
        H3("2.2.5 Reported results"),
        P(f"The detector reached a mean precision of {bp['precision']}, recall {bp['recall']}, mAP50 {bp['map50']} and mAP50-95 {bp['map5095']} over the three runs (best run precision "
          f"{bp['best_precision']}, mAP50 {bp['best_map50']}), at {bp['latency_ms'][0]} to {bp['latency_ms'][1]} ms per frame on an NVIDIA T4 GPU (about 72 to 87 frames per second). "
          "The table below gives the system-level results in the selected scenario."),
        TAB("System-level results reported by the base paper in its selected SUMO scenario (one pre-emption event)",
            ["Metric", "Proposed (vision override)", "GA-SGD", "Fixed-time"],
            [["Ambulance travel time (s)", tr["proposed"], tr["ga_sgd"], tr["fixed"]],
             ["Ambulance waiting time (s)", aw["proposed"], aw["ga_sgd"], aw["fixed"]],
             ["Total waiting time, all vehicles (s)", f"{tw['proposed']:,}", f"{tw['ga_sgd']:,}", f"{tw['fixed']:,}"],
             ["Average waiting time per vehicle (s)", atr["proposed"], atr["ga_sgd"], atr["fixed"]],
             ["Average travel time per vehicle (s)", bp["avg_travel_s"]["proposed"], bp["avg_travel_s"]["ga_sgd"], bp["avg_travel_s"]["fixed"]]],
            widths=[2.6, 1.4, 1.1, 1.1], align=["l", "c", "c", "c"], size=10),
        P("The authors read these as a 20.0 % cut in ambulance travel time against GA-SGD and 12.5 % against fixed-time control, and 12.9 % and 41.0 % cuts in total network waiting time. "
          "Under identical training settings YOLO26m also outperformed YOLOv8m for this small-object task."),
        H3("2.2.6 Limitations stated by the authors"),
        B("A moderate dataset and a small, hard object (rooftop light-bars); simulation-only validation with a simplified loop; one modelled roundabout; light-bar presence only, not flashing state, so a visual cue and not a deployment-ready authorisation."),
        H3("2.2.7 What FlowSense adopts and what it changes"),
        P("FlowSense adopts the paper's central idea (the light-bar as the emergency cue and priority as an override that returns control afterwards) and its habit of validating the control layer across controllers on identical demand. "
          "It adds a machine-learning queue forecast, coordination between neighbouring junctions and a violation log; it replaces the trained YOLO26m detector with stock YOLOv8n plus a colour-based light-bar rule, which is weaker (Chapter 8); "
          "and it replaces SUMO and GA-SGD with an in-house simulator and a queue-actuated, pressure-style controller, so its numbers cannot be compared with the paper's in absolute terms. "
          "The \"emergency-aware adaptive\" controller in the benchmark is an emulation of the paper's idea inside the FlowSense simulator, not a re-implementation of its software."),
        H3("2.2.8 Critical assessment"),
        P("The paper's strengths are a real problem (an optimised controller blind to ambulances), a cue argued to be common across fleets and detectable in 11 to 14 ms per frame, three training runs reported with "
          "standard deviations, and simulation-based validation of the control layer. Its weaknesses are those its authors list, plus two: the system-level result is one selected scenario with one pre-emption event, which says little about "
          "the average gain, and the detector (precision 0.73, recall 0.69, mAP50-95 0.34) and the SUMO controller are validated separately (the emergency vehicle's position is read from the simulator), as in FlowSense. "
          "FlowSense therefore replaces single scenarios by five-seed means, evaluates detector and controller separately and says so, and reports false-alarm rates."),
        H2("2.3 Related Work by Theme"),
        P("The related work is grouped by the capability it supplies, mirroring the modules of FlowSense: emergency pre-emption by infrastructure, by sound and by vision, then forecasting and learned control, then classical control."),
        H3("2.3.1 Infrastructure-based emergency pre-emption"),
        P(f"Sasikala et al. [{R['sasikala']}] combine GPS tracking, RFID identification and adaptive signal control and report, as quoted in the base paper, a 35 % cut in ambulance response time. "
          f"Zlatkovic et al. [{R['zlatkovic']}] study pre-emption in connected-vehicle environments in VISSIM, with reported reductions of up to 36 % in emergency-vehicle delay. Prajwal et al. [{R['prajwal']}] "
          f"use IoT devices at intersections, and Chowdhury et al. [{R['chowdhury']}] add UAV-assisted monitoring. These approaches work but depend on equipment on vehicles and junctions."),
        H3("2.3.2 Acoustic siren detection"),
        P(f"Giordano et al. [{R['giordano']}] run an efficient CNN on a Raspberry Pi to recognise sirens in real time; Jayakumar et al. [{R['jayakumar']}] combine temporal and spectral audio features with classical learners (the base paper quotes 99.5 % accuracy). "
          "As the base paper observes, acoustic methods suffer urban noise and say nothing about where the vehicle is."),
        H3("2.3.3 Vision-based vehicle and emergency-vehicle detection"),
        P(f"Phuong et al. [{R['phuong']}] evaluate YOLOv5 to YOLOv10 in Vietnamese surveillance scenes and highlight small objects and occlusion. Khalili and Smyth [{R['khalili']}] propose SOD-YOLOv8 for small traffic objects "
          f"with multi-path feature fusion and a PIoU loss. Fahim [{R['fahim']}] fine-tunes YOLOv9 for Dhaka traffic. For emergency vehicles specifically, {c('suhana', 'satyanarayana', 'sharma')} train YOLO models to classify ambulances, "
          "fire trucks and police cars from CCTV streams. The base paper's criticism, which FlowSense's real-image results echo, is that classifying the vehicle depends on regional appearance, "
          "while the roof light-bar is a more common cue."),
        P(f"The foundation for all of these is the YOLO family [{R['yolo']}], whose ready-trained versions are distributed by Ultralytics [{R['ultralytics']}] on COCO [{R['coco']}]. "
          "COCO has classes for car, motorcycle, bus and truck but not for an auto-rickshaw, a limitation that shows up in the real-image evaluation of Chapter 8."),
        H3("2.3.4 Forecasting and learning-based control"),
        P(f"Goenawan's ASTM system [{R['astm']}] is the closest companion paper. It detects vehicles with YOLOv5, forecasts vehicle counts for the next 12 hours with an RNN-LSTM "
          f"(reported MSE {4.521}, RMSE {2.232} vehicles) and sets the signal cycle length from the forecast, around Webster's formula. In CARLA it reports a flow rate of 21 vehicles per minute against about 15 without it and a pass delay of 5 s against about 12 s; "
          f"it does not mention emergency vehicles or coordination. Gupta et al. [{R['necdm']}] propose a neighbour-embedded graph neural network for congestion prediction at delivery stations (reductions up to 4.03 % in L1 loss, 16.66 % in L2 loss, 7.64 % in computation time), "
          f"but its task is choosing delivery vehicles, not signal control. Wei et al. [{R['intellilight']}] show that reinforcement learning can learn phase selection; FlowSense uses a simpler, inspectable rule. "
          f"The GA-SGD controller of the base paper's authors [{R['gasgd']}] is, per the base paper, strong for ordinary traffic but blind to emergency vehicles."),
        H3("2.3.5 Classical signal control"),
        P(f"Fixed-time plans follow Webster's method [{R['webster']}], which chooses cycle length and splits from average flows and then repeats them. Max-pressure control [{R['varaiya']}] "
          "gives green to the phase with the greatest queue difference between an approach and its downstream links and has attractive stability properties. Both are strong baselines: "
          "FlowSense's own \"adaptive\" controller is a queue-actuated rule of this family, and its \"advanced\" controller adds a pressure-style score. It is not max-pressure and is not claimed to inherit its proofs."),
        H3("2.3.6 The batch survey items"),
        P(f"The batch survey lists four further systems whose titles indicate a YOLOv8-based adaptive and emergency-aware controller validated on hardware [{R['s_signaliq']}], a density-estimation controller [{R['s_cisct']}], "
          f"accelerated emergency-vehicle detection with signal control [{R['s_i2itcon']}] and a client-server detection and signal system [{R['s_incip']}]. Their records could not be located, so their authors and results are unverified and they are not used for any comparison."),
        H3("2.3.7 Synthesis"),
        P("Three observations follow. First, emergency priority trades infrastructure against robustness: connected equipment is precise but costly, audio is cheap but ambiguous, and vision is position-aware "
          "but sensitive to appearance and lighting. Second, forecasting and control are studied in different papers, so no surveyed work shows a forecast used inside an emergency-aware controller. Third, results come from different "
          "simulators (SUMO, VISSIM, CARLA) and metrics, so numbers are not interchangeable between papers; the only fair comparison is between controllers inside one simulator, which is what FlowSense does."),
        TAB("Related work compared", ["Work", "Year", "Approach", "Finding / limitation"], lit.LIT_TABLE[:8], widths=[1.6, 0.5, 2.1, 2.2], align=["l", "c", "l", "l"], size=9),
        H2("2.4 Datasets and Algorithms Used"),
        H3("2.4.1 Data"),
        P(f"FlowSense does not train on a traffic dataset; its demand is generated by a seeded Poisson process shaped by a morning and an evening peak. Two public sets were used only to test the "
          f"vision layer. The Visaitech mixed-traffic set [{R['ds_traffic']}] has 293 dashcam frames with 1,506 boxes in four classes (pedestrian, two-wheeler, three-wheeler, four-wheeler) from South Asian mixed traffic, "
          f"under CC BY 4.0. The ambulance photo set [{R['ds_ambulance']}] holds 2,121 ambulance and 2,628 non-ambulance images, also CC BY 4.0; the first 300 of each folder by file name were used. "
          f"Passenger-car-equivalent weights follow the practice of the Highway Capacity Manual [{R['hcm']}]."),
        H3("2.4.2 Algorithms"),
        B(f"**YOLOv8n** [{R['ultralytics']}]: smallest YOLOv8 model, COCO-pretrained, used without fine-tuning for car, motorcycle, bus and truck.",
          "**HSV light-bar rule:** red and blue masks, dilated and intersected, relabel a vehicle box as an ambulance when a red-blue cluster sits on its roof region.",
          f"**Gradient boosting** [{R['gbm']}] (scikit-learn [{R['sklearn']}]) for the 30-second queue forecast, with a random forest [{R['rf']}] and a persistence baseline.",
          "**Pressure-style control with look-ahead** and a **seeded one-second simulation** in the spirit of SUMO [" + str(R['sumo']) + "], so that every controller sees the same random demand."),
        H3("2.4.3 Evaluation measures"),
        P("**Average delay** is the mean seconds a vehicle spent queued before leaving the network; **average queue** the mean number of queued vehicles over all approaches; **throughput** the vehicles that completed their trip; "
          "**emergency delay** the queueing time of ambulances only. The forecaster is scored by **MAE** (mean absolute error in vehicles) and **R2** against a persistence baseline. Detection uses **precision**, **recall** and **F1** "
          "with a match at intersection-over-union of at least 0.5 (0.3 on the loose synthetic boxes); the light-bar rule's **false-alarm rate** is the share of non-ambulance photos flagged."),
        H2("2.5 Strengths and Limitations of Existing Work"),
        TAB("Strengths and limitations of the main approaches", ["Approach", "Strengths", "Limitations"],
            [["Infrastructure pre-emption (GPS, RFID, connected vehicles)", "Direct, precise vehicle identity; large reported reductions in emergency delay", "Needs equipment on vehicles and junctions; hard to scale"],
             ["Acoustic siren detection", "Cheap sensors; embedded real time", "Urban noise; no position information"],
             ["Vision, vehicle-class detection", "Position known; uses existing cameras", "Appearance depends on region and fleet; unmarked vehicles missed"],
             ["Vision, light-bar detection (base paper)", "Common cue; independent of livery; 11-14 ms per frame", "Small object; moderate dataset; simulation only; one roundabout"],
             ["Learned forecasting (LSTM, GNN)", "Anticipates demand", "Studied apart from the controller; no emergency handling"]],
            widths=[2.0, 2.2, 2.3], align=["l", "l", "l"], size=9.5),
        H2("2.6 Research Gap"),
        P("The surveyed systems perform adaptive signal control or vehicle detection separately. The gap is one pipeline that detects, adapts timing, prioritises emergency vehicles and "
          "coordinates between junctions, evaluated on identical traffic. Beyond that headline gap, five narrower gaps follow from the survey:"),
        N(*lit.GAPS),
        P("FlowSense addresses the first gap by building the pipeline, the second and third by comparing four controllers on identical seeds, the fourth by testing the vision layer on real photographs and the fifth by validating the forecaster on held-out runs."),
        H2("2.7 Summary"),
        P("The base paper supplies the cue (the light-bar), the override logic and the discipline of simulation-based validation; the companion papers supply forecasting ideas but not emergency handling. "
          "What is missing, and what FlowSense attempts, is one working pipeline whose parts are measured against each other on identical traffic, and an honest account of how much of each part's benefit survives outside the generator that produced the test data."),
    ]
    return out
