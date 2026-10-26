"""Chapter 2: Literature survey."""

from . import facts as F
from . import lit
from .blocks import B, H1, H2, H3, N, P, TAB
from .refs import N as C


def blocks():
    nr = lambda s: F.pop(100, s, "no_reservation")           # noqa: E731
    return [
        H1("CHAPTER 2: LITERATURE SURVEY"),
        H2("2.1 Overview"),
        P("The survey has three threads, because the project joins three bodies of work. The first is allocation and optimisation of parking inside managed facilities, which is the subject of the registered base paper. "
          "The second is reservation-based parking and the reliability of a reservation, which is the subject of the technical base paper whose rules the code implements. "
          "The third is the family of systems that surround a reservation: mobile and web access, payment deposits, pricing, auctions and sensing. "
          f"The registered base paper {C('base')} and the technical base paper {C('cabri')} are analysed in depth in Section 2.2; every claim about them in this report was checked against the PDFs in the batch folder. "
          "Claims about the other works are limited to what the two base papers say about them, and where those papers give no result the tables below say so instead of supplying one."),
        P("The batch literature survey (5.LITERATURE SURVEY.docx) lists five works: the registered base paper and four papers from 2024 and 2026 on web-based and digital parking reservation. "
          "A web search on 26 October 2026 for the title of each of the four found no matching record, so they are listed in the reference list and in the table in Section 2.8 as the batch gave them, without authors, and nothing in this report depends on their content."),
        H2("2.2 Base Paper Analysis"),
        H3("2.2.1 Registered base paper: Jemmali et al., IEEE Open Journal of the Computer Society, 2026"),
        P(f"**Reference.** M. Jemmali, L. K. B. Melhim, A. Ammar, T. R. Gadekallu and W. Boulila, \"Smart parking for medical cities via passenger-aware allocation and fast grouping-permutation heuristics,\" "
          f"IEEE Open Journal of the Computer Society, vol. 7, pp. 1106-1118, 2026, doi 10.1109/OJCS.2026.3693801 {C('base')}."),
        P("**Problem.** Medical cities attract large and heterogeneous visitor flows. Allocating spaces by vehicle count ignores how many people each vehicle carries, which leads to uneven loads across parking zones, congestion near critical services and longer search times. "
          "The paper assigns vehicles to parking spaces by the total number of passengers, with the aim of minimising the disparity between the loads of the spaces, and states the problem as a small integer programme: "
          "each vehicle is assigned to exactly one space, the load of a space is the sum of the passenger counts assigned to it, and the objective is the sum over all spaces of the load minus the smallest load."),
        P("**Method.** A visitor registers a parking request through a web or mobile application, giving the number of passengers, the transport mode and the vehicle and booking identifiers. "
          "The system issues a QR code that carries the booking, the declared passengers and the allocated space; gate sensors scan it, compare the declared passengers with the occupancy detected by cameras and sensors, print a guidance card and update a scheduler, "
          "which keeps the status of every space from gate cameras, in-space sensors, mobile apps and the hospital information systems. "
          "A four-stage grouping procedure (prioritisation, dataset segmentation, group reordering, scheduling evaluation) and six grouping-permutation algorithms are proposed to compute the allocation."),
        P("**Evaluation and findings.** The algorithms are compared on nine instance classes and 2,790 generated test cases. The best of the six reaches the highest best-solution percentage (68.2 %) and the lowest average gap; "
          "the variant GVb matches or beats the baseline MR of the authors' earlier work on 1,547 of 2,790 instances (55.4 %), outperforming it on 57 (2.0 %) and matching it on 1,490 (53.4 %), while MR is better on 1,243 (44.6 %), and GVb needs substantially less execution time (sub-millisecond for the proposed heuristics)."),
        P("**Strengths and limits.** The paper offers a clear objective, a fast algorithm family and a reference architecture that includes a booking interface. Its limits, for the purpose of this project, are that it optimises allocation inside one managed facility with sensing hardware, "
          "needs passenger counts, evaluates generated instances rather than a running service, and does not deal with payment, with overstays or with operator analytics. Its own related-work section observes that earlier reservation platforms often treated availability guarantees on arrival as unenforced."),
        H3("2.2.2 Technical base paper: Cabri et al., arXiv:2605.17650, 2026"),
        P(f"**Reference.** G. Cabri, M. Montangero, F. Muzzini and R. Wang, \"Reservation based smart parking management,\" arXiv:2605.17650 [cs.MA], May 2026 {C('cabri')}. This paper is in the project folder as the base paper of the code, and the buffer and star mechanisms of the engine come from it."),
        P("**Problem.** A reservation-based system fails a driver when the reserved space is still occupied by a previous driver who overstayed. The authors call this a \"No Park\" situation and distinguish it from \"No Reservation\", in which a request is refused in advance. "
          "They argue that a refusal in advance is better for the driver than arriving and finding no space."),
        P("**Method.** Two mechanisms. The Reservation Module keeps a buffer of free parking slots in each area that new requests may not reserve but that can be given to an arriving driver whose own slot is still occupied. "
          "A request is accepted if the user has a good reputation and credit. If an arriving driver finds the area full, the system suggests one alternate nearby area and books it automatically; if that is full too, the system has failed. "
          "The buffer may be static or dynamic. In the dynamic policy the buffer starts at a fixed constant, grows by one each time a vehicle leaves after the end of its reservation, up to a fixed maximum, and is reset to its lowest value periodically. "
          "The Reward System keeps a rating of 0 to 5 stars per user: B consecutive on-time departures (Benefits) add a star, W overstays (Warnings) remove one, the rating changes the parking fee, and a rating below a threshold together with a recent violation bars the user from the system-managed areas for one subsequent session."),
        P(f"**Evaluation and findings.** The SUMO simulator {C('sumo')} models 80 reservable spots in 8 areas of equal size. Good vehicles leave on time and bad vehicles stay one hour longer; every vehicle makes 10 parks of 1 to 3 hours, "
          "with two further stops of 8 to 16 hours outside the system; users start with 3 stars. Experiment 1 raises the population from 80 to 110 vehicles in steps of 10; experiment 2 varies the share of bad vehicles from 25 % to 50 % with the population drawn from 80 to 110. "
          "Each configuration is run 5 times, and the dynamic buffer is compared with a static 0-spot, 1-spot and 3-spot buffer. The paper reports that any buffer beats none, that smaller static buffers cause more No Park events and fewer No Reservation events and larger ones the reverse, "
          "and that the dynamic buffer gives the better trade-off. The results are shown as figures; the paper gives no numeric table. The authors describe the work as preliminary."),
        P("**Strengths and limits.** The mechanism is simple, explicit and easy to implement, and the experimental scenario is fully described. The limits are that it is a simulation, that the user-behaviour model is two fixed types, "
          "that it assumes barrier-controlled areas and fully equipped vehicles, that only one alternate is ever suggested, and that no implementation, payment or user interface is described."),
        H3("2.2.3 What ParkSure takes from each paper, and what it does not"),
        TAB("Relation of ParkSure to the two base papers", ["Aspect", "Jemmali et al. [1]", "Cabri et al. [2]", "ParkSure"],
            [["Problem", "Balance the number of people per parking space", "Keep reserved spaces available despite overstays", "Run a reservation platform that stays reliable despite overstays"],
             ["Core technique", "Grouping-permutation heuristics", "Buffer of non-reservable slots plus star rating", "Admission rule k + b < c, buffer, haversine alternate, Trust Score"],
             ["Evidence", "2,790 generated instances", "SUMO, 80 spots, 5 runs, figures only", f"{F.PYTEST_PASSED} tests, own simulator (30 runs per cell), measured response times"],
             ["Delivered as", "Framework and algorithms", "Algorithm description and simulation", "Running web application with 22 routes and 24 screens"],
             ["Not covered", "Payment, overstays, analytics", "Implementation, payment, interface", "Passenger-aware allocation, sensors, SUMO, real data"]],
            widths=[1.0, 1.7, 1.8, 1.9], align=["l", "l", "l", "l"], size=9),
        P("ParkSure does not implement the grouping heuristics of the registered base paper and does not claim to match or beat them: they solve a different problem on different data. "
          "What it takes from that paper is the architecture of a booking interface in front of a central allocation engine, and the observation that availability on arrival must be enforced. "
          "From the technical base paper it takes the buffer, the dynamic reset, the single alternate and the star rating. It differs in two places that the experiments examine: the buffer in the code grows on on-time checkouts, whereas the paper grows it on late departures, "
          "and the lockout of a suspended driver lasts at least fourteen days after the last warning, whereas the paper bars one subsequent session."),
        H2("2.3 Reservation Systems and the Reliability of a Reservation"),
        P(f"Reservation is the central idea. Doulamis et al. model parking requests as time intervals and let a scheduler decide whether to accept a request and which space to assign {C('doulamis')}. "
          f"Yan et al. describe an off-street system in which spaces are reserved on the fly and drivers see real-time availability {C('yan')}. "
          f"Safitri et al. present a mobile reservation system that displays the occupancy rate and uses a heuristic with the haversine formula {C('safitri')}, and Somani et al. a cross-platform system in which the driver pays part of the fee to confirm a booking, to prevent false bookings {C('somani')}. "
          f"A further line limits access to drivers who hold a reservation, so that availability can be guaranteed {C('cabri')}."),
        P("These works concentrate on making a reservation possible. The technical base paper points out what they leave open: when the previous occupant does not leave on time, a reservation does not guarantee a place. "
          "ParkSure's admission rule is the interval-overlap rule of the scheduling line of work, with the buffer added to it as the base paper proposes."),
        H2("2.4 Allocation, Optimisation and Pricing"),
        P(f"Mejri et al. formulate slot assignment as a multi-objective integer linear programme that weighs walking distance to the destination, vehicle proximity and parking congestion {C('mejri')}. "
          f"Kotb et al. propose iParker, which offers flexible reservation times and dynamic revenue and pricing models {C('kotb')}. "
          f"Chen et al. analyse efficiency and equity in parking reservation {C('chen')}, and an earlier work of the registered base paper's lead author studies smart-parking management algorithms for smart cities {C('jemmali22')}. "
          f"The registered base paper places itself in this optimisation stream and notes that hospital-focused models of this kind emphasise profit rather than equitable access {C('base')}."),
        P("ParkSure takes a deliberately simpler position. Its price is the location's hourly rate multiplied by a factor that depends on the driver's Trust Score; there is no demand-based price and no optimisation of which bay is given. "
          "The simplicity keeps every decision inspectable, and the cost is that none of the gains of an optimiser are claimed."),
        H2("2.5 Auction and Agent-Based Parking"),
        P(f"Auction mechanisms allocate scarce spaces by bids. Rizvi et al. introduced ASAP, an agent-assisted auction-based parking system over Internet of Things sensors, which reduced search time and improved utilisation as summarised by the technical base paper {C('asap')}, "
          f"and followed it with MaPark, a multi-agent auction framework in which distributed agents negotiate assignments {C('mapark')}. Kokolaki et al. describe a centralised auction in which drivers bid for public spaces and a central authority coordinates assignment and payment {C('kokolaki')}."),
        P("Auctions suit competitive allocation of a scarce resource. A fixed-price booking service, which is what the batch asks for, has no bids, and the interesting question is reliability rather than price discovery. "
          "This body of work is therefore context for ParkSure rather than a source of mechanisms."),
        H2("2.6 Surveys, Sensing and Recent Reservation Services"),
        P(f"Aljohani et al. survey parking solutions for smart cities {C('aljohani')}, Xiao et al. survey parking prediction {C('xiao')} and Fahim et al. review smart parking systems from several aspects {C('fahim')}. Muzzini et al. show how optimised parking allocation can reduce congestion and improve urban viability {C('muzzini')}. "
          f"Geng and Cassandras describe an early smart-parking infrastructure and its implementation {C('geng')}, and Elfaki et al. a real-time control and monitoring system built on sensors {C('elfaki')}. "
          f"The registered base paper groups several of these early systems as infrastructure- and reservation-centric: they emphasise occupancy detection, reservation platforms and guidance interfaces, report limited quantitative optimisation of allocation, "
          f"and do not always enforce an availability guarantee on arrival {C('base')}. Among recent services it cites CRPark, a smart parking system with competition and reservation services {C('crpark')}."),
        P("These surveys and systems rely on sensing to know the true occupancy. ParkSure has no sensors; it knows physical occupancy only from check-ins, which is the weakest part of its availability claim and is stated as a limitation in Section 1.8."),
        H2("2.7 Datasets and Algorithms Used in Related Work and in This Project"),
        P(f"The related work uses three kinds of evidence. The registered base paper uses generated instances (nine instance classes, 2,790 cases) and measures the gap to the best solution and the execution time. "
          f"The technical base paper uses a SUMO simulation of 80 spots, counting No Park and No Reservation events over five runs per configuration. Most of the other works describe a system without a reported quantitative evaluation in the sources available here."),
        P(f"ParkSure uses no external dataset. It has the product's own seeded history for the operator analytics and a purpose-built simulator for the buffer comparison. The algorithms it uses are listed below, with the source of each idea."),
        TAB("Algorithms used in ParkSure and where each comes from", ["Algorithm", "Used for", "Source of the idea"],
            [["Interval overlap with a buffer: k + b < c", "Admission of a reservation request", f"Interval scheduling of requests {C('doulamis')}, textbook interval scheduling {C('kt')}, buffer from {C('cabri')}"],
             ["Dynamic buffer: init 1, +1 per on-time checkout, cap 5, daily reset", "Hold-back of bays per location", f"Dynamic buffer of {C('cabri')} (which grows it on late departures instead)"],
             ["Haversine great-circle distance", "Choosing the one nearest alternate location", f"Haversine formula {C('sinnott')}, used for parking by {C('safitri')}"],
             ["Trust Score: 3 benefits give +1, 2 warnings give -1, fee multiplier 0.90 to 1.75, suspension below 1.5", "Fees and access control", f"Star reward system of {C('cabri')}"],
             ["Deterministic replay of booking history", "Strategy Insights for operators", "Developed in this project"],
             ["Discrete-event simulation", "Comparing five buffer policies", f"Scenario of {C('cabri')} (SUMO {C('sumo')}); simulator developed in this project"]],
            widths=[2.4, 1.8, 2.2], align=["l", "l", "l"], size=9.5),
        H2("2.8 Strengths and Limitations of Existing Research"),
        TAB("Comparison of the surveyed work", ["Work", "Approach", "Data", "Reported result", "Limitation"], lit.rows(),
            widths=[0.9, 1.7, 0.95, 1.5, 1.35], align=["l", "l", "l", "l", "l"], size=8),
        P("**Strengths.** The literature establishes that reservation reduces search, that interval scheduling is a sound admission rule, that a buffer of non-reservable bays protects arriving drivers, "
          "that a reputation mechanism can discourage overstays, and that fast heuristics can allocate spaces in sub-millisecond time inside a managed facility."),
        P("**Limitations.** Most sources describe a mechanism without a reported evaluation in the available text; the two that evaluate do so on generated instances or in a simulator, with simple two-type user behaviour; "
          "none reports the response time, the failure modes or the security of an operating web service; and none combines booking, payment and operator analytics in one measured platform."),
        TAB("Batch survey titles that could not be verified", ["No.", "Title as listed in the batch survey", "Year", "Source as listed"],
            [[str(i), t, y, s] for i, (t, y, s) in enumerate(lit.SURVEY_UNVERIFIED, 1)],
            widths=[0.45, 3.3, 0.55, 2.1], align=["c", "l", "c", "l"], size=9.5),
        P(f"These four entries are kept in the reference list {C('s2', 's3', 's4', 's5')} because the batch survey names them. A web search found no record of any of them under the listed title and source, so their authors, content and results are unknown to us and none is used in this report."),
        H2("2.9 Research Gap"),
        P(lit.GAP),
        P("The project's answer has three parts. It builds the platform, so that search, booking, payment, check-in and check-out are one measured system. "
          "It implements the buffer and reputation rules of the technical base paper in running code and tests them in a simulator that agrees with the code. "
          f"And it reports where the implemented rule departs from the paper, since in the simulator the shipped rule refuses {nr('dynamic_parksure'):.0f} of 1,000 requests at 100 vehicles against {nr('dynamic_paper'):.0f} for the paper's rule, a difference a reader could not see from the papers alone."),
    ]
