"""Literature rows shared by the report (Chapter 2), the decks and the paper:
(key, work, approach, data, reported result, limitation).

Only facts stated in the two base papers (which describe the related works they cite) are used. Where the base papers
do not state a result, the cell says so; nothing is filled in from memory.
"""

ROWS = [
    ("base", "Jemmali et al. (base paper)", "Passenger-count-based allocation: four-stage grouping procedure and six grouping-permutation heuristics balance the number of people per parking space",
     "Nine instance classes, 2,790 generated test cases", "Best algorithm reaches the highest best-solution share (68.2 %); GVb matches or beats baseline MR on 1,547 of 2,790 instances (55.4 %), in sub-millisecond time",
     "Allocation inside one managed medical-city facility; relies on passenger counts and IoT sensing; no payment, overstay handling or operator analytics"),
    ("cabri", "Cabri et al.", "Reservation module with a buffer of non-reservable slots (dynamic: grows when vehicles leave late) plus a 0-5 star reward system; one alternate area is suggested",
     "SUMO simulation, 80 spots in 8 areas, 80-110 vehicles, 25-50 % overstaying by 1 h, 5 runs", "Any buffer beats none; the dynamic buffer gives the best trade-off between failed parks and rejected reservations (shown as figures, no numeric table)",
     "Preliminary, simulation only; assumes barrier-controlled areas and fully equipped vehicles; no implementation, payment or user interface"),
    ("doulamis", "Doulamis et al.", "Interval scheduling: requests are time intervals that the scheduler accepts or rejects", "Not stated in the base paper's summary", "Not stated in the base paper's summary",
     "No overstay handling is described in the base paper's summary"),
    ("safitri", "Safitri et al.", "Mobile reservation system that shows occupancy rate, using a heuristic and the haversine formula", "Not stated in the base paper's summary", "Not stated in the base paper's summary",
     "Mobile client only, per its title; no buffer or reputation mechanism described"),
    ("somani", "Somani et al.", "Cross-platform reservation: the driver pays part of the fee to confirm a booking and prevent false bookings", "Not stated in the base paper's summary", "Not stated in the base paper's summary",
     "Deposit discourages false bookings but does not address overstays"),
    ("mejri", "Mejri et al.", "Slot assignment as a multi-objective integer linear programme (walking distance, vehicle proximity, congestion impact)", "Not stated in the base paper's summary", "Not stated in the base paper's summary",
     "Optimisation model; no operating web platform is described"),
    ("kotb", "Kotb et al. (iParker)", "Flexible reservation times with dynamic resource allocation, revenue and pricing models", "Not stated in the base paper's summary", "Not stated in the base paper's summary",
     "Pricing is dynamic by demand, not by the driver's past punctuality"),
    ("auction", "Rizvi et al. (ASAP, MaPark); Kokolaki et al.", "Auction-based parking: agent-assisted and multi-agent auctions over IoT sensors; centralised bidding for public spaces", "Not stated in the base paper's summary", "ASAP reported better utilisation and shorter search time (as summarised in the base paper)",
     "Auctions suit competitive allocation, not a fixed-price booking service"),
    ("yan", "Yan et al. (SmartParking)", "Off-street parking with on-the-fly spot reservation and real-time availability for drivers", "Not stated in the base paper's summary", "Not stated in the base paper's summary",
     "Security-focused architecture; no overstay mitigation described"),
    ("chen", "Chen et al.", "Efficiency and equity analysis of parking reservation (as cited in the base paper)", "Not stated in the base paper", "Not stated in the base paper",
     "Analytical study; not a deployable service"),
    ("crpark", "Hu et al. (CRPark)", "Smart parking system with competition and reservation services (as cited in the base paper)", "Not stated in the base paper", "Not stated in the base paper",
     "Detail not given in the base paper"),
]
SURVEY_UNVERIFIED = [
    ("Design and implementation of a web-based smart vehicle parking reservation and management system with real-time slot allocation", "2026", "American Journal of AI Cyber Computing Management"),
    ("Digital parking slot reservation system for vehicles", "2026", "International Journal of Engineering Science and Advanced Technology"),
    ("Parking slot prediction and face recognition based parked vehicle theft prevention in smart parking system", "2024", "International Research Journal of Modernization in Engineering Technology and Science"),
    ("Smart vehicle parking reservation system using web and mobile technologies", "2026", "Research Digest on Engineering Management and Social Innovations"),
]
GAP = ("The surveyed work either optimises allocation inside a large managed facility (the registered base paper), proposes a buffer and reputation mechanism that is evaluated only in simulation, "
       "or describes reservation components one at a time (booking, payment, mobile access, pricing). A general reservation platform that combines search, booking, payment, an overstay-aware availability "
       "engine and operator analytics for ordinary urban parking, and measures its own behaviour, is not reported.")


def rows():
    return [[w, a, d, r, l] for _, w, a, d, r, l in ROWS]
