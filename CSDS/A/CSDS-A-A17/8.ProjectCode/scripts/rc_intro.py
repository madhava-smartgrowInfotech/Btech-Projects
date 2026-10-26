"""Chapter 1 content: domain, motivation, problem, need, objectives, scope, contributions, limitations, organisation.

Every figure comes from docs/REPORT_FACTS.md and experiments/*/metrics.json. References are numbered as in doc_common.REFERENCES.
"""
from __future__ import annotations

from doc_common import PRODUCT


def sec_domain(d):
    d.h2("Introduction to the Project Domain")
    d.paras(
        "Agriculture supports millions of farmers, but a farmer's income depends on events that begin only after the crop has been "
        "harvested: how the produce is judged, what price the market offers on the day, who buys it, and whether it reaches the buyer in "
        "good condition. Most research in smart agriculture addresses the period before harvest. The base paper of this project, by "
        "Khaliq et al. [1], is a typical and recent example: it combines Internet-of-Things (IoT) soil sensors, deep learning and "
        "explainable artificial intelligence (XAI) to advise on soil health, irrigation, crop choice and fertiliser. The period after "
        "harvest, in which quality is graded, a price is agreed and the produce is stored and transported, receives much less attention "
        "in the same integrated, explainable form.",
        "The domain of this project is therefore **post-harvest decision support for farmers**: the grading of crop quality from "
        "photographs, the prediction of market prices, the planning of delivery, the monitoring of storage and transport conditions, and "
        "the marketplace that connects farmers, distributors and buyers. It sits between several established areas of computer science. "
        "Image analysis supplies colour, texture, edge and blemish measures from a photograph [15], [16], [17], [19], [20]. "
        "Supervised learning supplies classifiers and regressors such as random forests [10] and gradient boosting [11], and quantile "
        "regression [12] supplies prediction bands. Explainable AI supplies methods such as SHAP [13], [14] that attribute a prediction to "
        "its input features. IoT sensing supplies the stream of storage and transport conditions that the base paper [1] uses on the farm.",
        f"**{PRODUCT}**, the system built in this project, combines these ideas into one web application with four roles. A farmer uploads "
        "a photograph of the harvested crop and receives a quality grade (A, B, C or Reject) with a probability for each class and the "
        "features that drove the decision; asks for a 30-day price forecast with a confidence band and a best day to sell; and obtains a "
        "ranked list of buyers with a suggested route before publishing the lot to a marketplace. Buyers browse and order, distributors "
        "carry the order and watch a live sensor stream, and an administrator sees platform figures and the transparency card of each "
        "model. The title of the project, *CropSight: Smart Crop Delivery with AI-Based Price and Quality Intelligence*, is read in this "
        "sense: the intelligence is limited to grading, pricing and delivery decisions after harvest, and each decision is explained.",
        "One point of wording must be made at the outset. The batch abstract speaks of deep learning for image grading. What was built "
        "and measured is **classical machine learning on hand-crafted computer-vision features**: eleven colour, texture, edge, blemish "
        "and size measures computed from the pixels of the uploaded photograph and classified by a random forest. This choice, and "
        "its consequences, are explained in Chapters 6 and 8.")


def sec_motivation(d):
    d.h2("Background and Motivation")
    d.paras(
        "Four observations motivated the project, and they follow the batch introduction. First, a farmer's income depends on "
        "unpredictable market prices, and a farmer who sells on the first available day has little information about whether the price "
        "is likely to rise or fall. Price-prediction systems that use machine learning on market, weather and demand data have been "
        "proposed [4], [5], and recent work shows that modern forecasting models can improve markedly on conventional benchmarks "
        "for agricultural commodity prices [6], but these systems seldom reach the farmer at the point of sale.",
        "Second, crop quality is usually judged by eye by a trader at the market. Such judgement is quick but subjective, and the same "
        "lot can receive different grades from different people, which in turn affects the price. Image-based grading and "
        "inspection systems have been proposed for agricultural products [3], computer vision has been applied to leaf-disease "
        "diagnosis and severity grading [2], and a recent crop-image recognition model reports an accuracy of 0.982 on its own "
        "benchmark [7]; but a farmer needs the grade together with a price and a buyer, not as an isolated classification.",
        "Third, produce is lost after harvest when storage and transport conditions are not monitored. A cold-chain breach, a humidity "
        "excursion or rough handling can spoil a lot, and without readings nobody can tell where or when it happened. Fourth, farmers "
        "have limited access to buyers and to real-time decision support, and the existing channel passes through middlemen who keep a "
        "share of the final price. Government portals publish prices without forecasts, and decisions about grade and price are "
        "rarely explained to the seller.",
        "Taken together, these observations show a gap between what pre-harvest smart-agriculture systems provide and what a farmer "
        "needs once the crop is in the shed. The base paper [1] demonstrates that IoT, learning models and XAI can be combined into an "
        "end-to-end advisory system with a farmer-friendly interface. This project asks whether the same combination can be carried "
        "over to the post-harvest stage, and how honestly it can be built and evaluated by a student team without access to a "
        "labelled crop-image set, a real market feed or sensor hardware.")


def sec_problem(d):
    d.h2("Problem Statement")
    d.paras(
        "Crop quality is graded manually and inconsistently. Farmers cannot predict prices or choose the best time to sell. Storage and "
        "transport conditions cause unmonitored post-harvest losses. Middlemen and limited market access reduce farmer income.",
        "**Formal statement.** Given a photograph of a harvested crop lot, its type, quantity and region, produce (i) a quality grade in "
        "{A, B, C, Reject} with class probabilities and a ranked list of the image features that drove the decision; (ii) a current price, "
        "a confidence band and a 30-day forecast for that crop, region and grade, with the drivers of the price and the best day to "
        "sell within a spoilage window; (iii) a ranked list of buyers with a match score and a suggested route; and then (iv) carry the "
        "lot through a marketplace order whose stages are enforced for each role, and (v) monitor temperature, humidity and shock while "
        "the lot is in transit and raise an alert when a reading leaves its safe range.")
    d.p("The problem is a systems problem as much as a modelling problem: five decisions have to be made consistently, explained to "
        "different users, and linked to the same record of the lot.")


def sec_need(d):
    d.h2("Need for the Proposed System")
    d.paras(
        "An integrated platform is needed that grades quality, forecasts prices, monitors the supply chain and connects farmers to "
        "buyers. Separate tools for each task leave the farmer to combine their outputs, and a tool that gives a grade or a price "
        "without a reason is difficult to trust or to dispute. The need can be stated as four requirements.",
    )
    d.bullets([
        "**Consistency.** The same photograph should receive the same grade each time, and the grade should be stored with the lot so that buyer and seller see one value.",
        "**Foresight.** A price with an uncertainty band and a recommended selling day lets the farmer weigh waiting against spoilage.",
        "**Transparency.** Grading and pricing decisions must be accompanied by the features that produced them, in plain language, so that they can be questioned.",
        "**Traceability.** An order must move through defined stages, each permitted to one role, and a shipment must leave a record of its conditions.",
    ])
    d.p("CropSight is proposed to meet these four requirements in one application, and the evaluation in Chapter 8 states how far each is met.")


def sec_objectives(d):
    d.h2("Objectives")
    d.p("The project has six objectives, taken from the batch objectives document:")
    d.numbered([
        "Grade crop quality automatically from images (the batch text says \"using deep learning\"; the delivered grader uses a random forest on eleven image features).",
        "Forecast crop prices from market, weather and demand data.",
        "Monitor storage and transport conditions using IoT sensors (delivered as a simulated sensor stream, because no hardware was available).",
        "Explain grading and pricing decisions with XAI (delivered with SHAP).",
        "Recommend buyers, delivery routes and the best time to sell.",
        "Connect farmers, distributors and buyers through a digital marketplace.",
    ])
    d.p("Chapter 8 measures each of these objectives against the results, and states where an objective was met only in part.")


def sec_scope(d):
    d.h2("Scope of the Project")
    d.h3("In scope")
    d.bullets([
        "Photographs of harvested produce (JPEG, PNG or WEBP, up to 8 MB) and eight crops: tomato, onion, potato, wheat, rice, mango, cotton and maize.",
        "Computer-vision feature extraction (eleven features) and a four-class grade with probabilities and a SHAP explanation of the top six features.",
        "A price model with a point estimate, a 15%-85% quantile band, a 30-day forecast, a best day to sell within a 14-day window and a grouped SHAP explanation.",
        "A transparent delivery-scoring engine that ranks buyers by price, distance, quality fit, reliability and spoilage risk and proposes a route.",
        "A role-gated marketplace (farmer, buyer, distributor, administrator) with a placed, confirmed, in-transit, delivered order lifecycle.",
        "A live sensor stream over WebSocket with threshold alerts, stored in a history table (the source is a simulator).",
        "A web application with sign-up and log-in, role dashboards, charts and an administrator page that discloses how each model was trained.",
        "An evaluation of both models, of the delivery scoring and of the simulator, a real-photograph transfer check, and an automated test suite.",
    ])
    d.h3("Out of scope")
    d.bullets([
        "Pre-harvest tasks: soil analysis, irrigation, crop and fertiliser recommendation, which are the subject of the base paper [1].",
        "Training on a real labelled crop-image set or a real market-price feed; none was available, so both models are trained on synthetic data.",
        "Real sensor hardware, cold-chain devices and GPS tracking; the stream is simulated.",
        "Payments, invoicing, contracts and integration with government market portals.",
        "A language-model assistant or chatbot; the base paper includes a chatbot, this project does not.",
        "Grading of crops that are not in the list of eight, and of photographs with several lots or a cluttered background.",
        "Production hardening such as HTTPS termination, rate limiting, a hosted database and load testing.",
    ])
    d.h3("Assumptions")
    d.bullets([
        "A photograph shows one lot of one crop, against a plain, bright background, in reasonable light.",
        "Quantities and asking prices are entered honestly by the user; they are not validated against market norms.",
        "Prices are in rupees per quintal (100 kg) and regions are the eight named regions of the demonstration data.",
        "The application runs on one machine with a single SQLite database for one demonstration deployment.",
    ])


def sec_contrib(d):
    d.h2("Key Contributions")
    d.numbered([
        "**An integrated post-harvest platform.** One application that links image-based quality grading, price forecasting, delivery planning, a role-gated marketplace and a live sensor stream, with 21 API endpoints (20 REST and one WebSocket) and nine database tables, applying the IoT, learning and XAI idea of the base paper [1] after harvest instead of before it.",
        "**Real computer-vision feature extraction with an explained grade.** Eleven features are computed from the pixels of the uploaded photograph (foreground mask, colour statistics, grey-level co-occurrence texture, edge density, blemish ratio, size score); a random forest grades the lot and SHAP lists the six features that drove the grade. On its own synthetic test set the grader scored 92.3% accuracy (five seeds: 92.9% ± 0.3%), and every error was between neighbouring grades.",
        "**A price estimate with an uncertainty band and a selling-day rule.** A gradient-boosted model gives the point price (test MAE 164.6 INR per quintal, R² 0.992, MAPE 5.1% against a noise floor of 2.8%), two quantile models give a 15%-85% band (empirical coverage 69.3% against 70% nominal), and the best day to sell is the maximum of the forecast over a 14-day spoilage window.",
        "**Transparent delivery scoring with measured stability.** A five-term weighted score ranks buyers and suggests a route; perturbing every weight by a factor between 0.5 and 1.5 left the top buyer unchanged in 97.7% of 25,600 trials.",
        "**A role-gated order lifecycle.** Order stages are enforced by a state machine in which each transition is open to one role, and a shipment record and sensor history are created when transit starts.",
        "**An honest, reproducible evaluation that includes a negative result.** Both models are evaluated against baselines and over several seeds; a check on 3,200 real fruit photographs shows that the synthetic-trained grader does not transfer (accuracy 50.4%, AUC 0.571, chance level), while the same eleven features retrained on real freshness labels reach 90.6% in five-fold cross-validation. The result locates the weakness in the training data, not in the feature extractor.",
        "**A tested and documented code base.** A suite of 39 automated tests (36 pass, 3 expected failures that document real gaps), measured API latencies, and defects found by testing are reported instead of hidden.",
    ])
    d.p("Contributions 1, 4 and 5 are engineering contributions; contributions 2, 3 and 6 are those whose quality was measured. Compared "
        "with the base paper [1], which works on tabular soil, weather and crop data from the farm and reports accuracies of 98.75% to 99.3% "
        "on its own datasets, this project works on photographs, prices and shipments after harvest, uses classical models rather than "
        "transformer models, and is trained on synthetic data. The datasets and tasks differ, so no numeric head-to-head is claimed.")


def sec_limits(d):
    d.h2("Limitations and Assumptions")
    d.bullets([
        "**Synthetic training data.** No real labelled crop-image set and no real market series were available. The grader is trained on feature vectors drawn from per-grade normal distributions, and the price model on a series produced by a formula with 3.5% noise. The high scores measure how well each model recovers its generator, not performance on farms or markets, and the administrator page says so.",
        "**The grader does not transfer to real photographs.** On 3,200 real fruit photographs it assigned grade B to about 99% of both fresh and rotten fruit; 99.8% of the real photographs lie outside the three-standard-deviation envelope of every synthetic grade profile.",
        "**Classical machine learning, not deep learning.** The grader is a random forest on eleven hand-crafted features. A convolutional network would need a real labelled image set that the project did not have.",
        "**The price forecast is not a time-series forecast.** The 30-day curve is the point model evaluated on 31 successive hash-generated market contexts; rainfall and temperature carry almost no importance (0.00009 and 0.00005), and the apparent gain from waiting to the best day (mean 14.6%) is an artefact of that context.",
        "**Simulated sensors.** The stream is a seeded random walk with injected events, without mean reversion: in 50 simulated shipments 91.6% of steps were in alarm, and a reconnection replays the same trajectory.",
        "**Simulated buyer offers.** The offered price of a buyer is the model price times a hash-derived factor between 0.90 and 1.18, so differences between buyers are not market information.",
        "**Defects found by testing.** The administrator volume figure multiplies a price per quintal by kilograms and overstates volume 100 times; a corrupt image with an image content type returns a server error and leaves a draft listing without a grade; crop, region, quantity and price are not validated; the WebSocket endpoint is not authenticated; and a default signing key ships in the configuration.",
        "**Single machine, single database,** no load, concurrency or penetration testing, and no user study with real farmers.",
        "**No numeric comparison with the base paper.** The base paper reports accuracies on tabular farm data; CropSight works on different data and tasks.",
    ])


def sec_organisation(d):
    d.h2("Organisation of the Report")
    d.table([["Chapter", "Title", "Content"],
             ["1", "Introduction", "Domain, motivation, problem statement, objectives, scope, contributions, limitations"],
             ["2", "Literature Survey", "Base paper, related work by theme, datasets and algorithms, strengths and limitations, research gap"],
             ["3", "Feasibility Study", "Technical, economic, operational and schedule feasibility"],
             ["4", "System Requirements and Analysis", "Existing and proposed system, requirements, platform, user roles"],
             ["5", "System Design", "Architecture, workflow, DFDs, UML, database, modules, user interface"],
             ["6", "Methodology and Software Implementation", "Pipeline, datasets, preprocessing, algorithms, mathematics, application, API, security, installation"],
             ["7", "System Testing", "Strategy, unit, integration, functional, security, validation, performance, acceptance, limits"],
             ["8", "Results and Output Screens", "Output screens, measured results, real-photograph check, comparison, failure analysis, objectives against outcomes"],
             ["9", "Conclusion", "Summary, objectives achieved, findings, applications, limitations"],
             ["10", "Future Scope", "Improvements, features, deployment, research"]],
            "Organisation of the report", widths=[0.1, 0.3, 0.6], font=10)
    (d.p if not getattr(d, "report", False) else (lambda *a, **k: None))("The report ends with the references, Appendix A (important code), Appendix B (installation and user guide) and Appendix C (additional screens).")
