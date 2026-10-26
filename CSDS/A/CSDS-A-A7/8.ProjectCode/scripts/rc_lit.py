"""Chapter 2 content: literature survey, base paper analysis, related work, datasets and algorithms, strengths and limitations, gap (SHEGUARD).

References are numbered as in doc_common.REFERENCES: [1] base paper (read in full); [2] IoT review (read in full); [3]-[5] batch-survey papers
(not retrievable, no results quoted); [6]-[8] papers read from archived_base_papers/; [9]-[15] clustering methods; [16]-[30] software, services,
datasets and specifications.
"""
from __future__ import annotations

from doc_common import BASE_PAPER


def sec_lit_overview(d):
    d.h2("Overview of the Literature Survey")
    d.paras(
        "The survey covers five groups of work. The first is the base paper [1], a clustering and GPS-integration approach to safe "
        "routes for women. The second is the systematic review of IoT devices for women's safety [2]. The third is work on "
        "smartphone and wearable safety applications with alerts and location tracking [3]-[7]. The fourth is a recent benchmark "
        "for camera-based detection of crimes against women [8]. The fifth is the clustering, routing and software techniques "
        "from which SHEGUARD is built [9]-[30].",
        "The batch literature survey lists five papers [1]-[5]. The base paper [1] and the IoT review [2] were read in full from "
        "their PDFs. Papers [3]-[5] could not be retrieved independently during this work, so they are described here by "
        "title, year and venue as listed in the batch survey, and **no result is attributed to them**. To avoid resting the "
        "review on titles alone, three further papers whose full text is in the project's archive of candidate base papers were "
        "read and are reported: an Android application with an ESP32 camera and crime-zone classification [6], a safe-route "
        "recommendation system [7] and a video-anomaly benchmark for women's safety [8].")
    d.table([["No.", "Paper (as listed)", "Year", "Venue", "Status in this survey"],
             ["1", "SafeRoutes: charting a secure path, a holistic approach to women's safety through advanced clustering and GPS integration [1] (base paper)", "2024", "IEEE Access", "Read in full"],
             ["2", "The role of IoT in woman's safety: a systematic literature review [2]", "2023", "IEEE Access", "Read in full"],
             ["3", "A mobile-based women safety application with real-time emergency alert and location tracking [3]", "2026", "Int. Scientific J. of Engineering and Management", "Listed; not retrieved"],
             ["4", "Shake-to-Alert: an automated mobile safety application for women with emergency notification via motion detection [4]", "2025", "ITIKD conference", "Listed; not retrieved"],
             ["5", "Cross-platform women safety mobile application with real-time alert system and GPS tracking [5]", "2026", "ICESIC conference", "Listed; not retrieved"],
             ["6", "Women safety mobile application using ESP32 camera and real-time crime data analysis [6]", "2025", "Int. J. of Electrical, Electronics and Computer Systems", "Added; read"],
             ["7", "SafeGuard: safe route recommendation system [7]", "2025", "IRJMETS", "Added; read"],
             ["8", "ExtrAnom: a VAD benchmark emphasizing the need for women's safety in society [8]", "2026", "arXiv:2605.25806", "Added; read"]],
            "Papers in the batch literature survey and the three papers added", widths=[0.06, 0.44, 0.08, 0.24, 0.18], font=9.5)


def sec_base_paper(d):
    d.h2("Base Paper Analysis")
    d.p(f"**Base paper.** {BASE_PAPER}")
    d.paras(
        "**Problem and scope.** Agrawal et al. address the safety of women in urban environments, and argue that traditional "
        "safety initiatives anchored in law enforcement and infrastructure need to be complemented by data analytics, because "
        "conventional methods suffer from subjective labelling and from too little labelled data about women's safety. They "
        "propose SafeRoutes, a framework with three parts: a data-ingestion pipeline connected to public and government "
        "sources, unsupervised machine-learning models that cluster regions by safety, and an integration with map services "
        "and cab vendors that visualises rides, draws a safety radius around a recommended path and alerts a driver who "
        "drifts into an unsafe area.",
        "**Data and preprocessing.** All data are taken from the Open Government Data Platform India (data.gov.in): district-wise "
        "population for 2001 and 2011, crimes reported under the Indian Penal Code in 2013 with a focus on women, literacy, "
        "per-capita total expenditure, police-inspector strength for 2013, an additional district population table with "
        "demographic and social indicators, and forest cover. Preprocessing consists of missing-value imputation by mean, "
        "median or k-nearest-neighbour imputation, feature engineering such as population growth rate, scaling with a "
        "standard or min-max scaler, and feature selection through a correlation matrix and principal component analysis or "
        "model-based importance. The paper does not state how many districts the final table holds.",
        "**Method.** Parameters judged relevant to women's safety, such as rape and kidnapping cases, police presence and "
        "infrastructure, are chosen from domain knowledge and ranked with the Pearson and Spearman correlation indices. "
        "K-Means and Gaussian mixture models are then compared [9], [14], and three to four clusters are reported to fit the "
        "data. Because no cluster can be called safe without a label, the authors add dummy data for cities described as the "
        "safest in the world and give a score of 100 to the cluster that contains the most of them. For travel, the paper "
        "describes a flow chart in which a cab service requests a safe path, a 1.96 times safety buffer (a confidence interval) "
        "tolerates construction diversions, a deviation into a red zone raises alerts and rerouting, and persistent deviation "
        "escalates to authorities.",
        "**Reported results.** The results section is a description of the study. It offers correlation matrices (Pearson and "
        "Spearman), a label-encoded table, and an ablation of clustering choices: explained variance against the number of "
        "clusters, Gaussian-mixture Bayesian information criterion scores, a Ward dendrogram [15], and three validity indices. "
        "As printed in its tables, the silhouette values are 0.440 for two clusters and 0.416 for three, the "
        "Calinski-Harabasz index [13] is 264.7 for two clusters, 221.0 for three and 222.7 for four, and the "
        "Davies-Bouldin index [12] is 1.021, 0.970 and 1.011 for two, three and four clusters; three clusters give the lowest "
        "Davies-Bouldin value of the three. The abstract and conclusion describe the outcomes as **anticipated**: heatmaps, "
        "classified regions and a benchmark for future research. The paper gives no accuracy, precision or latency figure, and "
        "the cab integration is described but neither implemented nor evaluated. (The paper's silhouette plot shows values "
        "near 0.25 to 0.31, which differ from its Table 3; the tables are quoted here as printed.)",
        "**Strengths.** The paper uses several public sources, justifies its feature selection statistically, compares "
        "clustering algorithms with several validity indices, discusses bias in crime data and under-reporting, and links area "
        "risk to the act of travelling, which most clustering studies do not.",
        "**Limitations, as we read them.** The results are anticipated outcomes rather than measured system performance; "
        "the number of districts and the final feature set are not stated; the 'safest city' reference data are dummy values; "
        "the 2013 crime year is a single snapshot; and the cab integration, which is the part that touches the traveller, has "
        "no implementation or user evidence.",
        "**What SHEGUARD adopts.** The central idea: group districts by recorded crime into a small number of risk tiers "
        "without labels using K-Means, and use the tiers to guide travellers on a map. SHEGUARD also uses the Davies-Bouldin "
        "and silhouette indices [11], [12] to check the clustering.",
        "**What differs.** SHEGUARD uses one feature (average counted crimes per reporting year, 2001-2012) rather than a "
        "multi-source table; it fixes three tiers rather than choosing the number from the data; it has no population, "
        "literacy, expenditure or police data and no Gaussian mixture analysis in the product; and instead of a cab-vendor "
        "alert it implements a route scorer on routing alternatives, plus SafePhrase and one-tap activation, a live guardian "
        "link, hashed evidence, an assistant and an installable web app. Because data, features and tasks differ, the "
        "validity indices of the two works are not comparable and no claim of superiority is made.")
    d.table([["Aspect", "Base paper [1]", "SHEGUARD"],
             ["Data", "data.gov.in: population 2001 and 2011, IPC 2013, literacy, expenditure, police strength, forest cover", "Kaggle district-wise crimes against women, 2001-2012, one derived feature; coordinates from Nominatim"],
             ["Clustering", "K-Means and Gaussian mixture, 3-4 clusters chosen with indices", "K-Means, k = 3 fixed, on one feature; tiers are two cut-offs"],
             ["Cluster indices reported", "Silhouette, Calinski-Harabasz, Davies-Bouldin, BIC (tables)", "Silhouette 0.580, Davies-Bouldin 0.531, Calinski-Harabasz 1155.4 on 467 points"],
             ["Travel integration", "Cab-vendor safe path, 1.96 times buffer, deviation alerts (designed, not evaluated)", "OSRM alternatives scored by district tier and time of day (implemented, measured)"],
             ["Emergency functions", "None in the paper", "One-tap SOS, SafePhrase, live guardian link, hashed evidence"],
             ["Assistant, user interface", "None in the paper", "Gemini-backed assistant; installable React web application"],
             ["Reported evidence", "Anticipated outcomes; cluster-selection tables; no accuracy", "Measured clustering quality, route-scoring study, 57 tests, API latencies; assistant and alert delivery not demonstrated"]],
            "Base paper and SHEGUARD compared", widths=[0.2, 0.40, 0.40], font=9.5)


def sec_related(d):
    d.h2("Related Work")
    d.h3("IoT devices and wearables for women's safety")
    d.paras(
        "Farooq et al. [2] carried out a systematic literature review of research studies on IoT devices for women's safety, "
        "examining articles published between 2016 and 2022 in well-regarded venues. They report that pulse-rate and pressure "
        "sensors are the most commonly used sensors, that alerts are transmitted over GPS, GSM and Raspberry Pi hardware, and "
        "that machine-learning methods such as logistic regression, hidden Markov models and decision trees are used to "
        "identify women under threat. They propose a taxonomy and an architectural model, and conclude that systems which "
        "generate alerts automatically, with less human interaction and better accuracy, still need to be developed. This "
        "conclusion matches the first gap noted in the batch survey: an alert that needs a deliberate action is hard to give "
        "in an emergency. SHEGUARD addresses it only in part, with a spoken phrase and a one-tap button, and not with "
        "automatic sensing.")
    d.h3("Mobile applications with emergency alert and tracking")
    d.paras(
        "The batch survey lists three recent application papers [3], [4], [5]: a mobile-based application with real-time "
        "emergency alert and location tracking, Shake-to-Alert, which from its title notifies contacts through motion "
        "detection, and a cross-platform application with a real-time alert system and GPS tracking. Their text could not be "
        "retrieved, so only their topics are stated and no result is quoted. They show the common pattern: an alert triggered "
        "by a button or by phone motion, plus GPS tracking of the user.",
        "Thawale et al. [6] describe an Android application with the Google Maps API, Firebase cloud storage and an ESP32-CAM "
        "module that captures time-stamped images during an emergency, together with an area-wise crime-intensity "
        "classification into low, medium and high zones. They report a crime-zone classification accuracy of 93% on pre-defined "
        "test locations, SOS delivery in 4 to 6 seconds, a location accuracy of 7 metres, an image upload under 8 seconds, a "
        "map render time of 2 seconds, and a battery use of 12% per hour, with a 100% success rate on stable networks that "
        "fell to 80% at first attempt on a poor network. These are the authors' own figures, on their own test locations. The "
        "system pairs a risk map with evidence capture, as SHEGUARD does, but depends on extra hardware.",
        "Shinde et al. [7] present SafeGuard, an Android navigation application that analyses crime reports, traffic congestion "
        "and crowd density to recommend safe routes, with a one-touch SOS, live location sharing, incident reporting with a "
        "heatmap, voice commands for location and messages, and interval safety checks. It is the closest functional "
        "relative of SHEGUARD, and it shows that route safety, voice activation and sharing belong together in one "
        "application. The paper describes the design; no performance figure is quoted here.")
    d.h3("Clustering for area risk")
    d.p("K-Means [9], [10] partitions points into k groups by minimising the within-cluster sum of squares, and the base paper "
        "uses it with Gaussian mixture models fitted by expectation maximisation [14]. The silhouette [11], Davies-Bouldin [12] "
        "and Calinski-Harabasz [13] indices measure how compact and separated the clusters are, and hierarchical clustering "
        "with Ward linkage [15] gives a dendrogram. These indices measure the geometry of a clustering; none of them shows that "
        "the clusters correspond to safety. SHEGUARD reports all three indices, compares Ward and Gaussian mixture tiers with "
        "K-Means, and states this limit.")
    d.h3("Camera-based detection of crimes against women")
    d.p("Sangeeta et al. [8] present ExtrAnom, a video-anomaly benchmark of 1001 videos in five crime categories with four "
        "textual annotations each, of which 50% are normal videos; the anomaly videos include harassment (18.9%), chain "
        "snatching (17.6%), kidnapping (7.3%), stalking (3.9%) and assassinations (2.3%), and the set contains low-light (8%), "
        "low-resolution (13%) and long-shot (15%) material. They find that existing datasets are insufficient for "
        "women-centric anomalies. This line of work detects an incident from a camera after it begins; it is complementary "
        "to a personal application, and SHEGUARD uses no video.")
    d.h3("Routing, mapping and real-time communication")
    d.p("OSRM [17] computes routes on OpenStreetMap data [18] and can return alternatives, which makes it a free source of "
        "candidate routes; its public demo server is rate limited and has no service guarantee. WebSocket [20] gives a "
        "persistent two-way channel suited to pushing a moving position. JSON Web Tokens [19] carry the identity of a logged-in "
        "user without server-side session storage, and bcrypt [21] stores passwords in a form that is slow to guess. SHA-256 "
        "[22] produces a fixed-length fingerprint of a file, so a later change to the file changes the fingerprint. The "
        "browser's speech-recognition interface [25] turns speech into text in Chrome and Edge, and the Gemini API [26] "
        "generates text from a prompt.")


def sec_lit_algorithms(d):
    d.h2("Datasets and Algorithms Used in the Literature and in SHEGUARD")
    d.h3("Datasets")
    d.table([["Dataset", "Content", "Use in SHEGUARD"],
             ["Crime in India, district-wise crimes against women [23]", "9,017 rows (8,597 after removing total rows), 35 states and union territories, 2001-2012, 827 district entries, 7 crime columns; CC0", "Source of the risk feature (average counted crimes per reporting year)"],
             ["Crimes against women in India 2001-2021 [24]", "736 state-year rows, 2001-2021; CC0", "Not used by any feature; available for a trend view"],
             ["District coordinates from Nominatim [29]", "467 of 827 district entries geocoded (56.5%), the rest dropped", "Location of each district for nearest-district lookup"],
             ["Routing alternatives from OSRM [17]", "Live responses, cached for the study in 16 city pairs", "Candidate routes to score"],
             ["Base-paper data (data.gov.in) [1]", "District population, IPC 2013, literacy, expenditure, police strength, forest cover", "Not used; listed to show what SHEGUARD lacks"]],
            "Datasets in the survey and in the project", widths=[0.28, 0.44, 0.28], font=9.5)
    d.h3("Algorithms and software")
    d.table([["Technique", "Reference", "Role in SHEGUARD"],
             ["K-Means clustering", "[9], [10]", "Groups 467 districts into three risk tiers"],
             ["Silhouette, Davies-Bouldin, Calinski-Harabasz", "[11], [12], [13]", "Cluster-quality indices"],
             ["Gaussian mixture, Ward linkage", "[14], [15]", "Alternative tierings used in the study only"],
             ["scikit-learn", "[16]", "K-Means, scaling, indices"],
             ["OSRM and OpenStreetMap", "[17], [18]", "Route alternatives and map tiles"],
             ["JSON Web Token", "[19]", "Stateless authentication of API calls"],
             ["WebSocket", "[20]", "Live location push to guardians"],
             ["bcrypt", "[21]", "Password hashing"],
             ["SHA-256", "[22]", "Evidence fingerprint"],
             ["Web Speech API", "[25]", "SafePhrase speech recognition in the browser"],
             ["Gemini API", "[26]", "Safety assistant"],
             ["FastAPI, Leaflet, Nominatim, Telegram Bot API", "[27], [28], [29], [30]", "Back end, map view, place search and geocoding, guardian alerts"]],
            "Techniques and the references behind them", widths=[0.36, 0.20, 0.44], font=9.5)
    d.p("The choice between a multi-feature clustering and a single-feature tiering is discussed in Chapter 6. In short, "
        "the single count was the only feature available in the district file that could be mapped to a place, and the "
        "result is two cut-offs on that count [9], [10].")


def sec_lit_strengths(d):
    d.h2("Strengths and Limitations of Existing Work")
    d.table([["Work", "Strengths", "Limitations for this project"],
             ["Base paper [1]", "Multi-source data; statistical feature selection; several clustering methods and indices; bias discussion; link to travel", "Anticipated results only; record counts not stated; cab integration not implemented or evaluated; no emergency functions"],
             ["IoT review [2]", "Systematic coverage of 2016-2022; taxonomy and architecture; identifies the need for automatic activation", "A review, no system; hardware-centred"],
             ["Mobile alert applications [3], [4], [5]", "Alert and tracking on a phone; one adds motion detection (from its title)", "Not retrieved; no result quoted"],
             ["ESP32 camera application [6]", "Evidence camera plus crime-zone classification; reported 93% zone accuracy and 4-6 s SOS", "Extra hardware; accuracy on pre-defined test locations; authors' own figures"],
             ["SafeGuard route recommendation [7]", "Route safety, SOS, voice and sharing in one application", "Design description; no result quoted here"],
             ["ExtrAnom benchmark [8]", "1001 videos for women-centric anomalies; shows data gap", "Camera-based; not a personal application"],
             ["Kaggle district data [23], [24]", "Open licence; district granularity", "Counts, not rates; 2001-2012 only; no coordinates"]],
            "Strengths and limitations of the surveyed work", widths=[0.26, 0.38, 0.36], font=9.5)
    d.p("Two general lessons follow. A risk map based on historical crime counts is a statement about reporting as much as "
        "about danger, which both the base paper and this project must acknowledge; and an alert application is only as "
        "useful as the channel that delivers its message, which is why delivery was treated as something to verify and not to assume.")


def sec_gap(d):
    d.h2("Research Gap")
    d.p("Women's safety applications and IoT devices mainly focus on sending an SOS alert; few combine safe-route prevention, "
        "hands-free activation and evidence preservation in one platform. The reviewed work leaves four gaps, summarised below.")
    d.table([["Gap", "Evidence in the surveyed work", "How SHEGUARD responds"],
             ["Alerts are triggered by a deliberate action", "The IoT review [2] calls for less human interaction and automatic activation", "One-tap SOS and a spoken SafePhrase (no automatic sensing)"],
             ["Prevention and emergency are separate systems", "The base paper [1] covers area risk and travel; applications [3]-[7] cover alerts", "One platform: route scoring, SOS, live link, evidence"],
             ["Guardians receive one-time alerts", "Many applications send a single message with a position", "A private link with a position that updates over a WebSocket, no login"],
             ["Evidence is rarely preserved securely", "Evidence capture appears only with extra hardware [6]", "Photograph and audio with time, place and SHA-256 hash"]],
            "Research gap and the project response", widths=[0.26, 0.40, 0.34], font=9.5)
    d.p("The project therefore asks a practical question: can route risk, hands-free activation, live guardian tracking and "
        "tamper-evident evidence be joined in one application, and how far can that application be trusted when its risk "
        "table rests on old, coarse data and its delivery channels cannot be verified? Chapters 6 to 8 answer both parts.")
