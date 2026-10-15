"""Chapter 2 sections (literature survey) and the base-paper analysis."""
from __future__ import annotations

# Work / approach / data / reported result / limitation.  Everything here is taken from the work's own abstract or from the base paper's
# description of it; nothing is quoted from a full text that was not read.
LIT_ROWS = [
    ["Danach et al., 2025 [1] (base paper)", "Random Forest demand forecast + matheuristic (MILP start, VNS) for e-commerce hub location",
     "Proprietary data of a global transport company; two years of demand", "Delivery-time compliance 92.3%, fulfilment 97.6%, robustness 0.87; +7.8% / +9.4% / +16% over traditional methods",
     "Data not public; sector-specific; scalability not extensively tested; the RF gain over statistics is left as 'X %'"],
    ["Zheng et al., 2024 [2]", "Diversity-based hybrid PSO (Gaussian random walk, bubble-net, Archimedes spiral) for drone logistics hub location",
     "Rural village delivery scenario", "Abstract reports a 42.58% improvement in scheme efficiency over other intelligent algorithms", "Metaheuristic only; no demand forecasting; no optimality bound"],
    ["Yang et al., 2023 [3]", "Maximal-detour liner shipping p-hub centre; three MILP models and an improved Benders decomposition",
     "Liner shipping networks (not detailed in the abstract)", "Models detour limits explicitly; decomposition strategies speed up the exact solve", "Fixed demand; liner-shipping specific"],
    ["Dehghan Chenary et al., 2024 [4]", "Bi-objective mobile hub location with congestion; Pareto-based clustering hybrid metaheuristic",
     "Australian Post dataset", "Better Pareto sets than MOPSO and NSGA-II (as reported in the abstract)", "Metaheuristic; demand treated as given"],
    ["Zhang et al., 2025 [5]", "Two-stage adaptive robust hub location under budgeted demand uncertainty; column-and-constraint generation with Benders",
     "Not stated in the abstract", "More reliable out-of-sample solutions than a two-stage stochastic model (as reported in the abstract)", "Uncertainty set is assumed, not learned from data"],
    ["Danach et al., 2019 [9]", "Capacitated single-allocation p-hub location-routing; Lagrangian relaxation and hyper-heuristic",
     "Not reviewed in detail", "Described in [1] as a Lagrangian-relaxation and hyper-heuristic approach for large instances", "No demand forecasting"],
    ["Ernst and Krishnamoorthy, 1996 [8]", "Efficient algorithms for the uncapacitated single-allocation p-hub median problem", "Not reviewed in detail", "Efficient algorithms for the uncapacitated problem (title)", "Uncapacitated; fixed demand"],
]


def sec_overview(d):
    d.h2("Overview of the Survey")
    d.paras(
        "The literature relevant to this project falls into five groups: the foundations of hub location, heuristic and metaheuristic search "
        "for hub and facility location, exact and decomposition methods, optimisation under demand uncertainty, and the use of machine "
        "learning to forecast the demand that drives the location decision. Matheuristics, the methodological family of the base paper, "
        "sit between the exact and the heuristic groups.",
        "The batch's literature-survey list names five works: the base paper [1] and four recent related studies [2]-[5]. Their bibliographic "
        "details were confirmed from the publishers' pages; their methods are summarised below from their abstracts and from the base paper's "
        "own description. This chapter does not claim to have read more than that. Classical references [6]-[10] are those the base paper "
        "itself cites for hub location, and references [11]-[20] are the methodological sources of the tools used in this project.")


def sec_base_paper(d):
    d.h2("Analysis of the Base Paper")
    d.p("**Reference.** K. Danach, A. Rammal, I. Moukadem, H. Harb and A. Nasser, 'Advanced optimization in e-commerce logistics: Combining "
        "matheuristics with random forests for hub location efficiency,' IEEE Access, vol. 13, pp. 55915-55926, 2025 [1]. The paper was "
        "received on 3 February 2025 and accepted on 9 March 2025, and is open access.")
    d.h3("Problem and model")
    d.p("The paper studies the HLP for e-commerce distribution networks with centralised hubs, dynamic demand, capacity constraints, service-level "
        "requirements, cost minimisation and risk. The formulation minimises the fixed cost of opened hubs, the variable transport cost and a "
        "penalty on unmet demand; flows y_ij are continuous, hubs x_i and capacity levels z_ik are binary, capacity constraints bind the "
        "flow into each hub, demand constraints require every demand point to be served, and valid inequalities tighten the model (activation, "
        "single-allocation, demand-splitting limits).")
    d.h3("Solution approach")
    d.p("The paper combines a Random Forest and a matheuristic. A relaxed MILP provides an initial solution; Variable Neighbourhood Search improves it; "
        "a Random Forest trained on historical demand forecasts the future demand at each location; the forecasts are fed back so the hub "
        "locations and capacities are re-optimised; finally the solution is validated on test scenarios (peak demand, sudden spikes, "
        "route disruptions). The paper also says the Random Forest assists in tuning matheuristic parameters and in scenario analysis.")
    d.h3("Data and experiments")
    d.p("The experiments use a proprietary dataset of a global transport company with thousands of customer locations, several candidate hub sites, "
        "two years of demand history, transport costs and hub capacities. Scalability was tested on networks of 50 to 500 nodes.")
    d.h3("Reported results")
    d.table([["Indicator", "Value reported in [1]"],
             ["Delivery-time compliance", "92.3% on average (+7.8% over traditional methods in the abstract)"],
             ["Fulfilment rate", "97.6% on average (+9.4% in the abstract)"],
             ["Network robustness", "0.87 (+16% in the abstract)"],
             ["Operating-cost reduction", "15-20% against benchmarks"],
             ["Scalability", "networks up to 300 nodes within reasonable time; near-optimal for up to 500 nodes"]],
            "Results reported by the base paper", widths=[0.34, 0.66], font=10)
    d.h3("Strengths")
    d.bullets(["The idea of replacing the fixed-demand assumption by an explicit forecast is simple and practical.",
               "It states the limits of the study plainly (sector-specific data, offline evaluation, scalability not extensively tested).",
               "It points to clear extensions: other learners, real-time IoT data, explainable AI, sustainability objectives."])
    d.h3("Gaps that this project addresses")
    d.bullets(["The dataset, code and matheuristic parameters are not available, so the results cannot be reproduced; this project ships code, a seeded dataset and saved results.",
               "The sentence on the Random Forest's gain reads 'improves the predictive accuracy by X %'; this project measures the gain against two naive forecasters on a time-based hold-out.",
               "The paper does not show how forecast error affects the plan; this project scores each plan on realised demand and reports the overloaded hubs.",
               "No application is provided; this project adds a usable web interface."])


def sec_related(d):
    d.h2("Related Work by Theme")
    d.h3("Foundations of hub location")
    d.p("O'Kelly introduced the location of interacting hub facilities [6]. Campbell, Ernst and Krishnamoorthy surveyed hub location problems, "
        "separating median, centre and fixed-cost variants and single from multiple allocation [7]. Ernst and Krishnamoorthy developed efficient "
        "algorithms for the uncapacitated single-allocation p-hub median problem [8]. These works define the single-allocation structure on which "
        "this project's model is based, with the addition of capacities and a delivery-time term.")
    d.h3("Heuristics and metaheuristics")
    d.p("Zheng, Xu and Chen locate logistics hubs for drones with a diversity-based hybrid particle swarm optimiser that combines a Gaussian "
        "random walk, a bubble-net strategy and an Archimedes spiral; the abstract reports a 42.58% improvement in scheme efficiency over other "
        "intelligent algorithms [2]. Dehghan Chenary, Ferdowsi and Hartl treat a bi-objective mobile hub location problem with congestion by "
        "combining Pareto-based clustering with a metaheuristic and test it on the Australian Post dataset against MOPSO and NSGA-II [4]. "
        "Danach, Gelareh and Neamatian Monemi combine Lagrangian relaxation with a hyper-heuristic for a capacitated single-allocation "
        "location-routing problem [9]. All of these search the solution space by heuristic moves; none uses a demand forecast.")
    d.h3("Exact methods and decomposition")
    d.p("Yang, Zheng, Wang and Hu study a liner-shipping p-hub centre problem with a maximal-detour restriction; they give three MILP models and an "
        "improved Benders decomposition with inspection, heuristic and multi-cut strategies [3]. The result illustrates how far exact methods "
        "can be pushed by decomposition, and why the exact MIP remains the reference against which heuristics are judged.")
    d.h3("Uncertainty")
    d.p("Zhang, Wang and Gao formulate a two-stage adaptive robust hub location problem: capacitated hubs are located in the first stage "
        "against the worst case over a budgeted uncertainty set, and routing is decided in the second stage after demand is revealed. A "
        "column-and-constraint-generation method built on Benders decomposition solves large instances and gives better out-of-sample "
        "performance than a two-stage stochastic model [5]. Here the uncertainty set is assumed; the base paper and this project instead "
        "learn the demand from data.")
    d.h3("Forecasting and machine learning")
    d.p("The base paper's own survey discusses LSTM-based demand prediction for couriers, recurrent networks with metaheuristic tuning for "
        "e-commerce sales, a transformer for passenger flow between transport hubs, and federated graph neural networks for facility location [1]. "
        "The Random Forest of Breiman [11] was chosen in [1] for its robustness, interpretability and low sensitivity to tuning; Hyndman and "
        "Athanasopoulos [19] provide the forecasting-evaluation conventions (time-ordered splits, naive benchmarks) used in this project.")
    d.h3("Matheuristics")
    d.p("Maniezzo, Boschetti and Stuetzle define matheuristics as the interoperation of metaheuristics and mathematical programming [12]. "
        "Kernel search, in which a restricted MIP is solved over a small set of promising variables, was introduced by Angelelli, Mansini "
        "and Speranza [17], and Variable Neighbourhood Search by Hansen and Mladenovic [16]. This project's solver uses the kernel-search idea "
        "and a MIP-priced local search; VNS, named in the base paper, is not implemented.")


def sec_datasets_algorithms(d):
    d.h2("Datasets and Algorithms Used in the Literature")
    d.table([["Work", "Dataset", "Algorithm family", "Evaluation measure"],
             ["[1]", "Proprietary logistics data, 2 years", "Random Forest + MILP + VNS", "Delivery-time compliance, fulfilment, robustness, cost"],
             ["[2]", "Drone-delivery scenario for villages", "Diversity-based hybrid PSO", "Scheme efficiency vs other algorithms"],
             ["[3]", "Liner-shipping networks", "MILP + improved Benders decomposition", "Solve time, detour constraints"],
             ["[4]", "Australian Post dataset", "Pareto clustering + metaheuristic", "Pareto set quality vs MOPSO, NSGA-II"],
             ["[5]", "Not stated in the abstract", "Column-and-constraint generation + Benders", "Out-of-sample performance vs stochastic model"],
             ["This project", "Synthetic, 90 regions x 36 months", "Random Forest + matheuristic (greedy, local search, kernel) + exact MIP baseline", "MAPE/R2; cost, delivery time, simulated fulfilment, SLA reliability; solve time"]],
            "Datasets, algorithms and measures in the surveyed work", widths=[0.1, 0.27, 0.33, 0.3], font=9.5)


def sec_strengths_limits(d):
    d.h2("Strengths and Limitations of the Surveyed Work")
    d.table([["Work", "Strength", "Limitation for this project's purpose"]] +
            [[r[0], r[3], r[4]] for r in LIT_ROWS],
            "Strengths and limitations of the surveyed work", widths=[0.22, 0.39, 0.39], font=9)


def sec_gap(d):
    d.h2("Research Gap")
    d.p("Classical hub location models use fixed demand and cannot adapt to fluctuating e-commerce orders; combining machine-learning demand "
        "forecasting with optimisation is still limited in practice. From the survey, four specific gaps follow, and each corresponds to a "
        "part of this project.")
    d.table([["Gap in the literature", "How this project responds"],
             ["Hub location studies assume known or assumed demand [2]-[5], [8], [9]", "Demand is forecast from history by a Random Forest and fed into the model"],
             ["The base paper's data, code and matheuristic parameters are unavailable [1]", "Open code, a seeded dataset, saved models and results, tests"],
             ["Effects of forecast error on the plan are not shown", "Plans are made on the forecast and scored on realised demand; overloaded hubs are reported"],
             ["No evidence on how much re-planning is worth", "A rolling-horizon simulation against a static plan over six months"],
             ["Exact versus matheuristic behaviour is described but not measured on growing instances", "Scalability benchmark at 90, 180 and 270 nodes with an exact-MIP time limit"]],
            "Research gaps and responses", widths=[0.5, 0.5], font=10)
