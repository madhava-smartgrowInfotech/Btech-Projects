"""Literature and framing data for the decks (Review 1, Review 2, final) and the IEEE paper.

Every literature fact traces to the base-paper PDF, the archived arXiv PDFs in this batch, or the entry notes in refs.py (REF_NOTES).
Reference numbers match scripts/docs/refs.py (CITE keys).  Items quoted from the base paper's own related-work section are marked
"(as reported in the base paper)".  The four batch-survey items [2]-[5] could not be verified beyond their titles and are never quoted for numbers.
"""
from . import facts as F
from .refs import CITE as R

BASE_PAPER_TITLE = "Emergency-Aware Adaptive Traffic Signal Control Using YOLO-Based Light-Bar Detection and SUMO System-Level Validation"
BASE_PAPER_VENUE = "M. Lamrabet, M. Alami Chentoufi, R. Ellaia - IEEE Access, vol. 14, 2026"

# [work, year, approach, finding / limitation]   (each cell <= 90 characters)
LIT_TABLE = [
    [f"Lamrabet et al. [{R['base']}] (base paper)", "2026", "YOLO26m roof light-bar detector as priority layer over a GA-SGD controller; SUMO",
     "P 0.73, R 0.69, mAP50 0.73 on 3,130 images; ambulance travel 56 s vs 70 s; one roundabout"],
    [f"Goenawan (ASTM) [{R['astm']}]", "2024", "YOLOv5 vehicle detection + RNN-LSTM count forecast sets cycle length; CARLA",
     "MSE 4.521, RMSE 2.232 (12 h); 21 vs ~15 veh/min; simulation only"],
    [f"Gupta et al. (NeCDM) [{R['necdm']}]", "2026", "Neighbour-embedded GNN predicts traffic flow for crowd-delivery stations",
     "Up to 4.03 % lower L1, 16.66 % lower L2 loss; routes deliveries, not signals"],
    [f"Lamrabet et al. [{R['gasgd']}]", "2025", "Simulation-based GA-SGD optimisation of signal timing, Morocco case study",
     "Efficient for ordinary traffic; no emergency detection (as stated in the base paper)"],
    [f"Sasikala et al. [{R['sasikala']}]", "2025", "GPS + RFID + IoT signal control with dynamic ambulance routing",
     "35 % shorter response time (as reported in the base paper); needs roadside infrastructure"],
    [f"Zlatkovic et al. [{R['zlatkovic']}]", "2023", "Pre-emption concepts for connected vehicles, VISSIM",
     "Up to 36 % emergency delay cut (as reported in the base paper); needs connected vehicles"],
    [f"Giordano et al. [{R['giordano']}]", "2025", "Efficient CNN siren recognition on Raspberry Pi audio",
     "Embedded real time; audio gives no position and suffers urban noise (base paper's view)"],
    [f"Khalili, Smyth [{R['khalili']}]", "2024", "SOD-YOLOv8: multi-path fusion and PIoU loss for small objects",
     "Better small-object mAP (as reported in the base paper); vehicle detection only"],
    [f"Suhana; Satyanarayana; Sharma [{R['suhana']}], [{R['satyanarayana']}], [{R['sharma']}]", "2025",
     "YOLOv5 / YOLOv8 classify ambulance, fire truck, police car from CCTV",
     "Vehicle appearance as cue; weak for unmarked or regionally different fleets (base paper)"],
    [f"Batch survey items [{R['s_signaliq']}]-[{R['s_incip']}]", "2024-26", "YOLOv8 / density / dynamic-signal systems (titles only)",
     "Authors and results not verified; not quoted for numbers"],
]

# [work, approach, data, reported result, limitation]  - short cells for the IEEE paper's TABLE I
PAPER_TABLE = [
    [f"Base paper [{R['base']}]", "YOLO26m light-bar detector over GA-SGD, SUMO", "3,130 images; Souissi roundabout", "mAP50 0.73; ambulance 56 vs 70 s", "One roundabout; simulation"],
    [f"ASTM [{R['astm']}]", "YOLOv5 + RNN-LSTM cycle length", "CARLA simulation", "RMSE 2.232; 21 vs ~15 veh/min", "No emergency logic"],
    [f"NeCDM [{R['necdm']}]", "Neighbour-embedded GNN", "Delivery-station traffic", "L2 loss -16.66 %", "Not signal control"],
    [f"Sasikala et al. [{R['sasikala']}]", "GPS, RFID, IoT pre-emption", "Not stated in base paper", "35 % faster response", "Needs infrastructure"],
    [f"Zlatkovic et al. [{R['zlatkovic']}]", "Connected-vehicle pre-emption", "VISSIM", "Up to 36 % less delay", "Needs connected vehicles"],
    [f"Giordano et al. [{R['giordano']}]", "CNN siren detection", "Audio clips", "Real time on Raspberry Pi", "No position; noise"],
    [f"Jayakumar et al. [{R['jayakumar']}]", "Audio features + SVM / ensembles", "Siren audio", "99.5 % accuracy", "Acoustic only"],
    [f"Khalili, Smyth [{R['khalili']}]", "SOD-YOLOv8", "Traffic scenes", "mAP gain (no figure here)", "Vehicles, not sirens"],
    [f"Suhana et al. [{R['suhana']}]-[{R['sharma']}]", "YOLO ambulance classes", "CCTV frames", "Not compared here", "Appearance-dependent"],
    [f"Survey [{R['s_signaliq']}]-[{R['s_incip']}]", "YOLOv8 / density / signals", "Not verified", "Not verified", "Details unverified"],
]

OBJECTIVES = [
    "Ingest camera frames and detect and count vehicles with a YOLO-based model",
    "Estimate traffic density per approach in passenger-car units",
    "Compute adaptive signal timing that allocates green in proportion to measured demand",
    "Detect emergency vehicles and give them priority passage through the junction",
    "Coordinate adjacent junctions so queues are smoothed along a corridor",
    "Evaluate detection accuracy, average waiting time and emergency-vehicle clearance time",
]

# the eight objectives in the batch documentary (Documentary/Batch_10_AI_Smart_Traffic_Management_System.docx)
OBJECTIVES_DOC = [
    "Detect and classify vehicles in real time using YOLOv8 and computer vision",
    "Control signal timings dynamically from vehicle density",
    "Give emergency vehicles priority passage by optimising signal operation",
    "Predict future congestion with machine learning and manage traffic proactively",
    "Enable communication and coordination between neighbouring intersections",
    "Detect traffic violations such as red-light jumping and wrong-way driving",
    "Reduce waiting time, congestion and fuel consumption",
    "Improve road safety and management efficiency through intelligent decisions",
]

PROBLEM_STATEMENT = [
    "Fixed signal timings waste green time on empty approaches while queues build on others",
    "Manual traffic control cannot scale to the number of junctions in a modern city",
    "Emergency vehicles lose critical minutes at signals that have no priority mechanism",
    "Junctions operate independently, so clearing one only moves the queue to the next",
    "Need: a controller that measures real traffic, adapts timing, clears the way for ambulances and coordinates junctions",
]

EXISTING_SYSTEM = [
    "Fixed-time plans (Webster-style splits) repeat the same cycle whatever the traffic [" + str(R["webster"]) + "]",
    "Queue-actuated and max-pressure controllers react to demand but see neither emergency vehicles nor the next junction [" + str(R["varaiya"]) + "]",
    "Emergency pre-emption relies on GPS/RFID/connected-vehicle infrastructure [" + str(R["sasikala"]) + "], [" + str(R["zlatkovic"]) + "] or on audio sirens [" + str(R["giordano"]) + "]",
    "Vision systems detect vehicles or ambulance bodies with YOLO but are validated apart from the signal controller [" + str(R["suhana"]) + "], [" + str(R["sharma"]) + "]",
    "Forecasting models (LSTM, GNN) are studied separately from the controller that would use them [" + str(R["astm"]) + "], [" + str(R["necdm"]) + "]",
]

LIMITATIONS_OF_EXISTING = [
    "Fixed-time signals cannot react: in our simulator they give the longest delay (67.8 s on a 2x2 grid at demand x1.2)",
    "Infrastructure-based pre-emption is expensive to roll out across a city",
    "Audio siren detection has no position and suffers urban noise (as noted in the base paper [" + str(R["base"]) + "])",
    "Detectors that classify the whole emergency vehicle depend on regional livery and fail on unmarked vehicles (base paper)",
    "The base paper's own validation covers one modelled roundabout and a trained single-class detector (P 0.73, R 0.69) [" + str(R["base"]) + "]",
    "Several surveyed systems are only described by title in the batch survey; their results could not be verified [" + str(R["s_signaliq"]) + "]-[" + str(R["s_incip"]) + "]",
]

GAPS = [
    "The surveyed systems perform adaptive signal control or vehicle detection separately: no single pipeline detects, adapts timing, prioritises emergency vehicles and coordinates junctions",
    "Forecasting, emergency priority and corridor coordination are rarely compared on identical traffic with the same seeds",
    "Pre-emption is usually reported as a gain for the ambulance, not as a price for the other traffic [" + str(R["base"]) + "]",
    "Synthetic-scene accuracy is seldom tested on real photographs, where a colour-based light-bar rule may not transfer",
    "Forecast quality is usually shown on a random split; held-out simulation runs show how far it generalises",
]
