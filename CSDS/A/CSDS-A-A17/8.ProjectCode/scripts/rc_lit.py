"""Chapter 2 content: literature survey, base paper analysis, related work, datasets and algorithms, strengths and limitations, gap.

References are numbered as in doc_common.REFERENCES: [1] base paper; [2]-[5] batch-survey papers (not retrievable, no results quoted);
[6], [7] papers read from archived_base_papers/; [8], [9] real-photograph datasets; [10]-[23] method and software references.
"""
from __future__ import annotations

from doc_common import BASE_PAPER


def sec_lit_overview(d):
    d.h2("Overview of the Literature Survey")
    d.paras(
        "The survey covers five groups of work. The first is the base paper [1], an integrated smart-agriculture system for the "
        "pre-harvest stage. The second is work on image-based assessment of crops and agricultural products [2], [3], [7]. The third is "
        "work on crop-price prediction [4], [5] and on forecasting agricultural commodity prices with modern models [6]. The fourth is "
        "the learning, image-analysis and explanation techniques from which CropSight is built [10]-[22]. The fifth is the data on "
        "which grading can be checked against real photographs [8], [9].",
        "The batch literature survey lists five papers [1]-[5]. The base paper [1] was read in full from its PDF. Papers [2]-[5] could "
        "not be retrieved independently during this work: searches by title and venue did not find them, so they are described here "
        "by title, year and venue as listed in the batch survey, and **no result is attributed to them**. To avoid resting the review "
        "on titles alone, two further papers whose full text is in the project's archive of candidate base papers were read and are "
        "reported: a study of time-series foundation models for commodity prices [6] and a study of large-scale crop image recognition [7].")
    d.table([["No.", "Paper (as listed)", "Year", "Venue", "Status in this survey"],
             ["1", "AI-driven smart agriculture: an integrated approach for soil analysis, irrigation, and crop-fertilizer recommendations [1] (base paper)", "2025", "IEEE Access", "Read in full"],
             ["2", "Cross-task consistent multi-task learning for fine-grained crop leaf disease diagnosis and severity grading [2]", "2026", "CVIDL 2026", "Listed; not retrieved"],
             ["3", "Design of agricultural product quality inspection and e-commerce grading system based on image recognition [3]", "2026", "AIDLNN 2025", "Listed; not retrieved"],
             ["4", "Crop and market price prediction system using machine learning [4]", "2023", "IRJMETS", "Listed; not retrieved"],
             ["5", "Crop price prediction using machine learning [5]", "2024", "Journal of Electrical Systems", "Listed; not retrieved"],
             ["6", "Time-series foundation models for agricultural forecasting [6]", "2026", "arXiv:2601.06371", "Added; read"],
             ["7", "Large-scale crop image recognition, ConvLSTM and LCMST-Net [7]", "2026", "IEEE Access", "Added; read"]],
            "Papers in the batch literature survey and the two papers added", widths=[0.06, 0.46, 0.08, 0.2, 0.2], font=9.5)


def sec_base_paper(d):
    d.h2("Base Paper Analysis")
    d.p(f"**Base paper.** {BASE_PAPER}")
    d.paras(
        "**Problem and scope.** Khaliq et al. address water shortage, inefficient resource use and declining soil health, and argue that "
        "traditional farming based on observation and generalised practice lacks the precision these problems need. They propose an "
        "AI-powered smart-agriculture system that integrates deep learning, IoT sensing and explainable AI for four tasks: soil "
        "analysis, irrigation advice, crop recommendation and fertiliser recommendation. All four tasks concern the period before and "
        "during cultivation.",
        "**Data and preprocessing.** The framework draws on soil nutrient profiles, real-time environmental sensor readings, "
        "historical weather data and crop records, arranged as tabular datasets for each task. Preprocessing consists of missing-value "
        "imputation by mean or median, normalisation of numeric features to the range 0 to 1, outlier removal by standard-deviation "
        "thresholds, and label or one-hot encoding of categorical fields such as crop names. As we read the text, the number of records "
        "of each dataset is not stated.",
        "**Method.** Four models are used. A Transformer-based Tabular Learning (TTL) model gives irrigation advice; a TabNet regressor "
        "analyses soil health; a Sparse Weighted Fusion Transformer (SwiFT) recommends crops; and a TabNet classifier recommends "
        "fertiliser [22]. The data are split 80% to 20% for training and testing, and the transformer models are trained with the Adam "
        "optimiser at a learning rate of 0.001, a batch size of 32 and 30 epochs. Explanations of the TabNet predictions are produced "
        "with LIME [21]. A weather API supplies forecasts for the irrigation decision, and a chatbot interface is added for farmers. "
        "The models were developed in Python on a Windows 10 computer with an Intel Core i5 processor and 8 GB of memory.",
        "**Reported results.** TTL reaches 99.13% accuracy for irrigation advice; the TabNet regressor reaches a root mean square error "
        "of 1.51 and an R² of 98.7% for soil analysis; SwiFT reaches 98.75% for crop recommendation; and the TabNet classifier "
        "reaches 99.3% for fertiliser recommendation. A feature study on crop recommendation shows the value of combining soil and "
        "climate inputs: accuracy falls to 97% and 82% when soil nutrients or climate features are removed, and to 67% and 51% when only "
        "nutrients, or only pH and rainfall, are used.",
        "**Strengths.** The paper covers four decisions in one framework, adds explanations and a farmer-facing interface, reports an "
        "ablation, and uses a modest computer, which supports the claim that such systems are affordable.",
        "**Limitations, as we read them.** The framework works on tabular data only and does not use images; it stops at the farm gate "
        "and does not address grading, price, storage or delivery; the numbers of records are not stated in the text; and the authors "
        "themselves list real-time adaptive control and generalisation across geographical regions as future work.",
        "**What CropSight adopts.** The architectural idea of the base paper: IoT sensing, learning models and explanation combined in "
        "one system with a farmer-facing interface. CropSight applies it **after harvest**, to quality grading, price prediction and "
        "delivery, and keeps the explanation component, using SHAP [13], [14] where the base paper uses LIME [21].",
        "**What differs.** The input (photographs, prices and shipments instead of soil and weather tables); the models (a random forest [10] "
        "and gradient boosting [11] instead of transformers and TabNet); the explanation method (SHAP instead of LIME); the sensing "
        "(a simulated stream instead of soil sensors); the addition of a delivery planner and a role-gated marketplace; and the "
        "absence of a chatbot. The training data also differ: CropSight is trained on synthetic data, and this is stated wherever "
        "results are given. Because tasks and datasets differ, the accuracies of the base paper and of CropSight are not comparable.")
    d.table([["Aspect", "Base paper [1]", "CropSight"],
             ["Stage of the farming cycle", "Before and during cultivation", "After harvest"],
             ["Decisions", "Soil health, irrigation, crop, fertiliser", "Quality grade, price and best day, buyer and route, shipment alerts"],
             ["Input data", "Tabular soil, weather, fertiliser and crop records", "Crop photograph, market context features, order and sensor records"],
             ["Models", "TTL, TabNet, SwiFT (deep, transformer-based)", "Random forest, gradient boosting with quantile bands (classical)"],
             ["Explanation", "LIME", "SHAP (TreeExplainer)"],
             ["Sensing", "IoT soil and environment sensors", "Simulated storage and transport stream"],
             ["User interface", "Chatbot and weather API", "Role-based web application and marketplace"],
             ["Reported evidence", "Accuracy 98.75% to 99.3%; RMSE 1.51; R² 98.7%", "Accuracy 92.3% and R² 0.992 on synthetic test sets; chance-level transfer to real photographs"]],
            "Base paper and CropSight compared", widths=[0.24, 0.38, 0.38], font=9.5)


def sec_related(d):
    d.h2("Related Work")
    d.h3("Image-based assessment of crops and agricultural products")
    d.paras(
        "The batch survey lists two image-based papers. One is on cross-task consistent multi-task learning for fine-grained crop leaf "
        "disease diagnosis and severity grading [2], published at the 2026 International Conference on Computer Vision, Image and Deep "
        "Learning; the other is on the design of an agricultural-product quality-inspection and e-commerce grading system based on image "
        "recognition [3], published in the proceedings of AIDLNN 2025. Their titles show the two ideas that CropSight combines, severity "
        "grading from images and image-based grading tied to e-commerce, but their results could not be read and none is quoted.",
        "Feng and Zong [7] study large-scale crop image recognition. They improve a ConvLSTM network with a coordinate-attention mechanism "
        "and an atrous spatial pyramid pooling (ASPP) module, and classify the extracted spatiotemporal features with a model they call "
        "LCMST-Net. The improved ConvLSTM reaches an accuracy of 0.979 and a recall of 0.926, and the average classification accuracy of "
        "LCMST-Net is 0.982. The work shows what deep networks achieve on large labelled crop-image sets; it is also a reminder that "
        "CropSight did not have such a set.")
    d.h3("Crop-price prediction and agricultural forecasting")
    d.paras(
        "The batch survey lists two machine-learning papers on crop and market price prediction [4], [5], from 2023 and 2024. Their "
        "text could not be retrieved, so only their topic is stated: predicting crop prices with machine learning from market data.",
        "Wang and Zhang [6] evaluate 17 forecasting approaches from four classes (traditional time series, machine learning, deep "
        "learning and five time-series foundation models) on monthly commodity-price data of the United States Department of "
        "Agriculture Economic Research Service from 1997 to 2025. They report that zero-shot foundation models outperform the "
        "traditional, machine-learning and deep-learning models trained from scratch, and that on three of four major commodities "
        "they also beat the department's futures-based forecasts; Time-MoE improves on the benchmark by 54.9% for wheat and 18.5% for "
        "corn on 2017-2024 data excluding the COVID period. The paper is the strongest evidence that price forecasting from real "
        "history is a feasible and improving field; it also shows what CropSight does not do, since CropSight's price model is not a "
        "time-series model and was not trained on a real price history.")
    d.h3("IoT sensing and cold-chain monitoring")
    d.p("The base paper [1] uses IoT sensors for soil and environmental monitoring and treats the sensor stream as an input to learning "
        "models. CropSight transfers the sensing idea to storage and transport, with temperature, humidity and shock readings and a "
        "threshold alert. No physical sensors were available, so the stream is generated by a simulator whose behaviour is measured in "
        "Chapter 8.")
    d.h3("Explainable AI for tabular and image-feature models")
    d.p("Tree ensembles are accurate but not transparent. SHAP [13] assigns each feature a contribution to a prediction on the basis of "
        "Shapley values, and the TreeExplainer algorithm computes them exactly and quickly for tree models [14]. The base paper uses "
        "LIME [21], which fits a local linear model around a prediction. CropSight uses SHAP on both of its tree models because the "
        "computation is exact for trees and the contributions add up to the prediction.")
    d.h3("Classical and deep models for grading and pricing")
    d.p("Deep networks dominate recent image work [2], [7] and the base paper [1] uses transformer models for tabular data, and both "
        "report high accuracy on their own datasets. They need large labelled datasets and, usually, a graphics processor. Tree "
        "ensembles remain strong on small and medium tabular problems [10], [11], train in seconds on a central processor, "
        "and can be explained exactly [14]. For a project with no labelled crop images and no graphics processor, the second "
        "family was the practical choice; the cost of that choice, a feature extractor that must be designed by hand and a grader "
        "that depends entirely on how well the training distribution matches real photographs, is measured in Chapter 8.")
    d.h3("Marketplaces and delivery planning")
    d.p("The batch survey notes that farmers sell through middlemen at market prices and that government portals publish prices "
        "without forecasts. The reviewed papers do not combine grading, price and buyer matching with a delivery plan; CropSight "
        "does so with a transparent weighted score rather than a trained model, so that every ranking can be explained.")


def sec_lit_algorithms(d):
    d.h2("Datasets and Algorithms Used in the Literature and in CropSight")
    d.h3("Datasets")
    d.table([["Dataset", "Content", "Use in CropSight"],
             ["Fresh and Rotten Fruits [8]", "3,200 raw photographs of 8 fruits (apple, banana, grape, guava, jujube, orange, pomegranate, strawberry), 200 fresh and 200 rotten each; CC BY 4.0", "Real-photograph check of the grader and of the feature extractor"],
             ["Vegetable Classification, Bangladesh [9]", "4,319 photographs of 12 vegetables including tomato, onion and potato; CC BY 4.0", "Real tomato, onion and potato photographs for the demonstration and sample inputs"],
             ["Synthetic quality features", "6,000 rows, 11 features, 4 grades, 6% label noise (generated by the project)", "Training and test set of the shipped grader"],
             ["Synthetic market series", "23,360 rows, 8 crops, 8 regions, 2022-2024 (generated by the project)", "Training and test set of the shipped price model"]],
            "Datasets in the survey and in the project", widths=[0.24, 0.46, 0.30], font=9.5)
    d.h3("Algorithms and software")
    d.table([["Technique", "Reference", "Role in CropSight"],
             ["Otsu thresholding", "[17]", "Foreground mask on the saturation channel"],
             ["Grey-level co-occurrence texture", "[15]", "Texture contrast, homogeneity and energy"],
             ["Canny edge detector", "[16]", "Edge density inside the mask"],
             ["OpenCV, scikit-image", "[20], [19]", "Colour conversion, morphology, edges, texture"],
             ["Random forest", "[10]", "Four-class quality grader (250 trees)"],
             ["Gradient boosting", "[11]", "Point price model (300 trees)"],
             ["Quantile regression", "[12]", "15% and 85% price quantiles"],
             ["SHAP, TreeExplainer", "[13], [14]", "Feature contributions for grade and price"],
             ["scikit-learn", "[18]", "Training, evaluation, baselines"],
             ["LIME, TabNet (base paper)", "[21], [22]", "Explanation and tabular learning in the base paper, not used here"],
             ["JSON Web Token", "[23]", "Stateless authentication of API calls"]],
            "Techniques and the references behind them", widths=[0.32, 0.18, 0.50], font=9.5)
    d.p("The choice between a deep network and a random forest on hand-crafted features is discussed in Chapter 6. In short, the "
        "forest needs no large labelled image set, trains in seconds on a computer without a graphics processor, and gives exact "
        "SHAP explanations, which suits a project with no labelled crop images [10], [13], [14].")


def sec_lit_strengths(d):
    d.h2("Strengths and Limitations of Existing Work")
    d.table([["Work", "Strengths", "Limitations for this project"],
             ["Base paper [1]", "Four decisions in one framework; XAI; weather API; chatbot; ablation; high reported accuracy", "Tabular, pre-harvest only; no images, grading, price or delivery; record counts not stated in the text read"],
             ["Leaf-disease multi-task learning [2]", "Joint diagnosis and severity grading (from the title)", "Not retrieved; leaves, not harvested produce; no result quoted"],
             ["Quality inspection and e-commerce grading [3]", "Image-based grading linked to e-commerce (from the title)", "Not retrieved; no result quoted"],
             ["Crop and market price prediction [4], [5]", "Machine-learning price prediction (from the titles)", "Not retrieved; no result quoted"],
             ["Foundation models for commodity prices [6]", "17 approaches, 28 years of real data, comparison with USDA forecasts", "Monthly national series; not a farm-gate, grade-specific price"],
             ["Crop image recognition [7]", "Accuracy 0.982 with ConvLSTM and LCMST-Net", "Needs large labelled data and a deep network; no price or delivery"],
             ["Fruit and vegetable photograph sets [8], [9]", "Real photographs, open licence", "Freshness labels, not A/B/C/Reject grades; fruit and vegetable types differ from the crop list"]],
            "Strengths and limitations of the surveyed work", widths=[0.26, 0.37, 0.37], font=9.5)
    d.p("Two general lessons follow. High reported accuracies on one dataset do not show that a model works elsewhere, and the "
        "transfer check in Chapter 8 is a direct example of this for CropSight itself. Systems that explain their decisions are rare "
        "in the post-harvest literature reviewed, which is why explanation was kept as a design requirement.")


def sec_gap(d):
    d.h2("Research Gap")
    d.p("Smart-agriculture systems focus on pre-harvest decisions; few support post-harvest quality grading, price forecasting and "
        "delivery planning for farmers. The reviewed work leaves four gaps, summarised below.")
    d.table([["Gap", "Evidence in the surveyed work", "How CropSight responds"],
             ["Post-harvest decisions are not covered together", "The base paper [1] stops at soil, irrigation, crop and fertiliser; [2]-[7] each treat one task", "One platform for grading, price, delivery, monitoring and marketplace"],
             ["Grading is not linked to price and buyer", "Image work [2], [3], [7] ends at a class label", "The grade feeds the price model and the buyer ranking"],
             ["Decisions are not always explained to the seller", "Many models are opaque; the base paper explains soil and fertiliser only", "SHAP explanation shown with every grade and price"],
             ["Claims rest on a single dataset", "Reported accuracies are on the papers' own data", "A real-photograph transfer check, baselines and several seeds, with a negative result reported"]],
            "Research gap and the project response", widths=[0.28, 0.38, 0.34], font=9.5)
    d.p("The project therefore asks a practical question: can grading, price intelligence, delivery planning and monitoring be "
        "joined in one explainable application for the post-harvest stage, and how far can such an application be trusted when "
        "it must be trained without real labelled data? Chapters 6 to 8 answer both parts.")
