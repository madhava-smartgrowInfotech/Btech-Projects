"""IEEE-style reference list. Order = citation number in the report. Use N('key') to get the number for a key.

Entries 1-2 are the two base papers (read in full from the PDFs in Documentary/ and archived_base_papers/).
Related-work entries are copied from the reference lists of those two papers; what the text says about them is only what those papers say.
The four batch-survey titles (keys s2..s5) could not be located on the web (searches on 2026-10-26 found no record);
they are listed as given in 5.LITERATURE SURVEY.docx and are never quoted for any result.
"""

_R = [
    ("base", "M. Jemmali, L. K. B. Melhim, A. Ammar, T. R. Gadekallu and W. Boulila, \"Smart parking for medical cities via passenger-aware allocation and fast grouping-permutation heuristics,\" IEEE Open Journal of the Computer Society, vol. 7, pp. 1106-1118, 2026, doi: 10.1109/OJCS.2026.3693801."),
    ("cabri", "G. Cabri, M. Montangero, F. Muzzini and R. Wang, \"Reservation based smart parking management,\" arXiv:2605.17650 [cs.MA], May 2026."),
    ("aljohani", "M. Aljohani, S. Olariu, A. Alali and S. Jain, \"A survey of parking solutions for smart cities,\" IEEE Transactions on Intelligent Transportation Systems, vol. 23, no. 8, pp. 10012-10029, 2021."),
    ("xiao", "X. Xiao, Z. Peng, Y. Lin, Z. Jin, W. Shao, R. Chen, N. Cheng and G. Mao, \"Parking prediction in smart cities: A survey,\" IEEE Transactions on Intelligent Transportation Systems, vol. 24, no. 10, pp. 10302-10326, 2023."),
    ("asap", "S. R. Rizvi, S. Zehra, R. Mukkamala and S. Olariu, \"ASAP: An agent-assisted smart auction-based parking system in Internet of Things,\" in Proc. 9th ACM Symp. on Design and Analysis of Intelligent Vehicular Networks and Applications, 2019, pp. 1-8."),
    ("mapark", "S. R. Rizvi, S. Zehra and S. Olariu, \"MaPark: A multi-agent auction-based parking system in Internet of Things,\" IEEE Intelligent Transportation Systems Magazine, vol. 13, no. 4, pp. 104-115, 2020."),
    ("doulamis", "N. Doulamis, E. Protopapadakis and L. Lambrinos, \"Improving service quality for parking lot users using intelligent parking reservation policies,\" in Proc. 27th Int. Conf. on Advanced Information Networking and Applications Workshops, IEEE, 2013, pp. 1392-1397."),
    ("kokolaki", "E. Kokolaki, M. Karaliopoulos and I. Stavrakakis, \"Trading public parking space,\" in Proc. IEEE Int. Symp. on a World of Wireless, Mobile and Multimedia Networks, 2014, pp. 1-6."),
    ("yan", "G. Yan, W. Yang, D. B. Rawat and S. Olariu, \"SmartParking: A secure and intelligent parking system,\" IEEE Intelligent Transportation Systems Magazine, vol. 3, no. 1, pp. 18-30, 2011."),
    ("safitri", "R. R. Safitri, A. Pratiarso and A. Zainudin, \"Mobile-based smart parking reservation system with rate display occupancy using heuristic algorithm and haversine formula,\" in Proc. 2020 Int. Electronics Symp. (IES), IEEE, 2020, pp. 332-339."),
    ("somani", "A. Somani, S. Periwal, K. Patel and P. Gaikwad, \"Cross platform smart reservation based parking system,\" in Proc. 2018 Int. Conf. on Smart City and Emerging Technology (ICSCET), IEEE, 2018, pp. 1-5."),
    ("mejri", "N. Mejri, M. Ayari, R. Langar and L. Saidane, \"Reservation-based multi-objective smart parking approach for smart cities,\" in Proc. 2016 IEEE Int. Smart Cities Conf. (ISC2), 2016, pp. 1-6."),
    ("kotb", "A. O. Kotb, Y.-C. Shen, X. Zhu and Y. Huang, \"iParker - a new smart car-parking system based on dynamic resource allocation and pricing,\" IEEE Transactions on Intelligent Transportation Systems, vol. 17, no. 9, pp. 2637-2647, 2016."),
    ("muzzini", "F. Muzzini, N. Capodieci and M. Montangero, \"Improving urban viability through smart parking,\" International Journal of Parallel, Emergent and Distributed Systems, vol. 38, no. 6, pp. 522-540, 2023."),
    ("chen", "R. Chen, G. Gao, L.-J. Kang and L.-Y. Zhang, \"Efficiency and equity analysis on parking reservation,\" Transportation Research Part E: Logistics and Transportation Review, vol. 187, art. no. 103606, 2024."),
    ("jemmali22", "M. Jemmali, L. K. B. Melhim, M. T. Alharbi, A. Bajahzar and M. N. Omri, \"Smart-parking management algorithms in smart city,\" Scientific Reports, vol. 12, no. 1, pp. 1-15, 2022."),
    ("geng", "Y. Geng and C. G. Cassandras, \"A new 'smart parking' system infrastructure and implementation,\" Procedia - Social and Behavioral Sciences, vol. 54, pp. 1278-1287, 2012."),
    ("crpark", "Z. Hu, Y. Cao, J. Huang, L. Wu, L. Xu and R. Zhang, \"CRPark: A smart parking system with competition and reservation services,\" IEEE Transactions on Vehicular Technology, vol. 74, no. 8, pp. 12981-12996, Aug. 2025."),
    ("fahim", "A. Fahim, M. Hasan and M. A. Chowdhury, \"Smart parking systems: Comprehensive review based on various aspects,\" Heliyon, vol. 7, no. 5, art. no. e07050, 2021."),
    ("elfaki", "A. O. Elfaki, W. Messoudi, A. Bushnag, S. Abuzneid and T. Alhmiedat, \"A smart real-time parking control and monitoring system,\" Sensors, vol. 23, no. 24, art. no. 9741, 2023."),
    ("sumo", "P. A. Lopez, M. Behrisch, L. Bieker-Walz, J. Erdmann, Y.-P. Flotterod, R. Hilbrich, L. Lucken, J. Rummel, P. Wagner and E. Wiessner, \"Microscopic traffic simulation using SUMO,\" in Proc. 21st IEEE Int. Conf. on Intelligent Transportation Systems (ITSC), 2018, pp. 2575-2582."),
    ("kt", "J. Kleinberg and E. Tardos, Algorithm Design. Boston, MA, USA: Addison-Wesley, 2006."),
    ("sinnott", "R. W. Sinnott, \"Virtues of the haversine,\" Sky and Telescope, vol. 68, no. 2, p. 159, 1984."),
    ("rest", "R. T. Fielding, \"Architectural styles and the design of network-based software architectures,\" Ph.D. dissertation, Dept. Inf. Comput. Sci., Univ. California, Irvine, CA, USA, 2000."),
    ("jwt", "M. Jones, J. Bradley and N. Sakimura, \"JSON Web Token (JWT),\" IETF RFC 7519, May 2015."),
    ("bcrypt", "N. Provos and D. Mazieres, \"A future-adaptable password scheme,\" in Proc. USENIX Annual Technical Conf., FREENIX Track, 1999, pp. 81-91."),
    ("sqla", "M. Bayer, \"SQLAlchemy,\" in The Architecture of Open Source Applications, Volume II, A. Brown and G. Wilson, Eds., 2012."),
    ("fastapi", "S. Ramirez, \"FastAPI documentation,\" [Online]. Available: https://fastapi.tiangolo.com (accessed Oct. 2026)."),
    ("stripe", "Stripe, Inc., \"Stripe Checkout and webhooks documentation,\" [Online]. Available: https://docs.stripe.com (accessed Oct. 2026)."),
    ("react", "Meta Platforms, Inc., \"React documentation,\" [Online]. Available: https://react.dev (accessed Oct. 2026)."),
    ("s2", "\"Design and implementation of a web-based smart vehicle parking reservation and management system with real-time slot allocation,\" American Journal of AI Cyber Computing Management, 2026 (title and source as listed in the batch literature survey; not located online and not quoted)."),
    ("s3", "\"Digital parking slot reservation system for vehicles,\" International Journal of Engineering Science and Advanced Technology, 2026 (title and source as listed in the batch literature survey; not located online and not quoted)."),
    ("s4", "\"Parking slot prediction and face recognition based parked vehicle theft prevention in smart parking system,\" International Research Journal of Modernization in Engineering Technology and Science, 2024 (title and source as listed in the batch literature survey; not located online and not quoted)."),
    ("s5", "\"Smart vehicle parking reservation system using web and mobile technologies,\" Research Digest on Engineering Management and Social Innovations, 2026 (title and source as listed in the batch literature survey; not located online and not quoted)."),
]
REFS = [t for _, t in _R]
_IDX = {k: i + 1 for i, (k, _) in enumerate(_R)}


def N(*keys):
    """Citation text like [3] or [3], [7] for one or more keys."""
    return ", ".join(f"[{_IDX[k]}]" for k in keys)
