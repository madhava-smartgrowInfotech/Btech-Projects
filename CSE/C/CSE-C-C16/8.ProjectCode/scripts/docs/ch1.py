"""Chapter 1: Introduction. Every measured number comes from facts.py (experiments/plantdoc/*.json)."""

from . import facts as F
from . import lit
from .blocks import B, H1, H2, H3, N, P, TAB
from .refs import cite

HC, C, MB = F.HC, F.C, F.MB


def blocks():
    return [
        H1("CHAPTER 1: INTRODUCTION"),
        H2("1.1 Domain"),
        P("This project sits where agriculture, computer vision and web development meet. Its subject is the recognition of crop disease from a photograph of a leaf, and the delivery of "
          "advice about what to do next to a farmer who may not read English and may not be able to reach an agricultural officer. The batch domain statement names "
          "artificial intelligence, computer vision, agriculture technology and web development; the product built in this project, AgriVision, uses all four: an image-analysis "
          "engine, a disease knowledge base, a React web application and a FastAPI service."),
        P("The visual symptoms of most foliar diseases - spots, rings, mould, rust pustules, yellowing, mosaic patterns - appear on the leaf before the disease spreads through "
          "the field. A leaf is also the easiest part of a plant to photograph with an ordinary phone. This is why leaf-image classification has been the main entry point of machine "
          "learning into plant protection " + cite("mohanty", "ferentinos") + "."),
        H3("1.1.1 Relevance to sustainable development"),
        P("The title of the project links disease detection to sustainable development. The link is practical rather than rhetorical. A disease identified early can be treated "
          "with a single targeted spray instead of repeated blanket spraying, which lowers the farmer's cost and the amount of pesticide that reaches soil and water; a correctly "
          "identified healthy leaf avoids a spray that was never needed; and treatment advice that includes organic and cultural measures next to chemical ones, as the knowledge base "
          "of AgriVision does for every class, keeps lower-impact options in front of the farmer. These benefits depend entirely on the diagnosis being right, which is why the "
          "measured accuracy is a central result of this report and not a side note."),
        H2("1.2 Background and Motivation"),
        P("Crop disease is a leading cause of yield loss. The introductions of the base paper " + cite("base") + " and of the compact-CNN paper " + cite("pd36c") +
          " both quote the figure of about USD 220 billion lost to crop diseases every year, and the base paper adds that soybean disease alone costs up to USD 3.9 billion in the "
          "United States. For a smallholder the loss is direct: a field of tomato or potato hit by blight within a fortnight cannot be replanted in time."),
        P("Diagnosis is normally made by an agricultural expert, by a laboratory test, or by the farmer's own experience. Experts are few and far from most fields; laboratory work is "
          "slow and expensive; experience does not transfer to a new disease or a new crop. Delayed diagnosis means delayed spraying, and wrongly chosen spraying means wasted money "
          "and avoidable chemical use. The batch abstract adds that farmers also lack timely guidance on fertilisers, pesticides and crop management, and that existing agricultural "
          "tools are fragmented, costly or inaccessible to small-scale farmers."),
        P("Deep learning has made image-based diagnosis technically possible. Convolutional networks reach more than 99 % on curated leaf collections " +
          cite("mohanty", "ferentinos", "pd36c") + ". The same literature warns that these scores fall sharply on photographs taken in real fields " + cite("barbedo", "plantdoc") +
          ": in the PlantDoc benchmark, built from web-scraped field photographs, accuracy of well-known networks is between 13.7 % and 70.5 % depending on whether leaves are cropped "
          "and how the network is pre-trained " + cite("plantdoc") + ". The motivation of this project is therefore twofold: to build the farmer-facing application that "
          "turns a classification into advice, and to measure honestly how good the classification part is on field photographs."),
        H3("1.2.1 Why leaf photographs and why PlantDoc"),
        P("A leaf photograph needs no equipment beyond a phone, and the symptoms that matter for most foliar diseases are visible on it. For measurement the project needs photographs "
          "taken the way a farmer would take them. PlantDoc " + cite("plantdoc") + " is such a set: its images were collected from the web, show leaves in fields and gardens with "
          "natural backgrounds, and cover 13 crops that overlap strongly with the 38-class label set of the knowledge base. Its small size and noise are not a flaw of the choice; "
          "they are the conditions under which the application would be used. The cost is that results on it are far lower than the 99 % that curated collections give, and "
          "this report reports the lower numbers."),
        H2("1.3 Problem Statement"),
        P(lit.PROBLEM_STATEMENT),
        P("The batch problem statement lists four underlying problems:"),
        B(*lit.PROBLEM_POINTS),
        P("**Need.** The batch documents summarise the need as " + lit.NEED),
        H2("1.4 Objectives"),
        P("The six objectives set in the batch documents are reproduced below. Chapter 8 (Section 8.9) measures each of them against what was achieved; the short version is that "
          "the dataset, the web interface and the treatment mapping were delivered, the network was trained but is not accurate enough, and the validation of advice and the "
          "fertiliser recommendation were not done."),
        N(*lit.OBJECTIVES),
        H2("1.5 Scope of the Work"),
        P("**In scope.** (a) An image-upload web application with registration, sign-in, a dashboard, a detection screen, a result screen, a history with search and filters, "
          "CSV and PDF exports, an analytics page, a profile and a disease guide; (b) a knowledge base of 38 classes (14 crops, 12 of them healthy classes) with symptoms, severity, "
          "chemical, organic and cultural treatments and prevention; (c) an interface in English, Hindi and Marathi; (d) a REST API with token authentication; (e) an experiment "
          "script that measures the diagnosis engines on the PlantDoc test split; (f) automated API and edge-case tests."),
        P("**Out of scope or not delivered.** Yield prediction, weather-based recommendations, fertiliser-dose advice, a voice interface, an administrative dashboard, a trained "
          "neural network inside the application, foliage-level (whole-plant) images, offline use on a phone, and any validation of the advice by an agronomist. The batch "
          "abstract proposes several of these; they are listed as future work in Chapter 10."),
        TAB("What the batch abstract promises and what was delivered", ["Promised in the abstract", "Status", "Where in this report"],
            [["Detect crop disease from an uploaded leaf image", "Delivered as an application; diagnosis accuracy low (heuristic engine)", "Chapters 5, 6, 8"],
             ["Recommend fertilisers, pesticides and crop management practices", "Pesticide and cultural measures per disease class delivered; fertiliser dose not delivered", "Chapters 4, 6"],
             ["Predict crop yield from environmental data", "Not delivered", "Chapters 4, 10"],
             ["Weather-based farming recommendations", "Not delivered (a fixed seasonal alert only)", "Chapters 4, 10"],
             ["Multi-language support", "Interface in English, Hindi and Marathi; advice text English only", "Chapters 4, 6, 8"],
             ["Farmer profile management and crop history tracking", "Delivered", "Chapters 5, 6"],
             ["Administrative dashboard", "Not delivered", "Chapters 4, 10"]],
            widths=[2.6, 2.7, 1.4], align=["l", "l", "l"], size=9.5),
        H2("1.6 Contributions"),
        N("AgriVision, a deployable web application that joins leaf-photograph diagnosis to a 38-class treatment knowledge base, history, exports, analytics and a three-language interface, started with one command (`run.bat`) on a CPU-only laptop.",
          "A clean contract between a FastAPI layer and the original Flask product: the same detection and knowledge modules, database and image store are shared and nothing is reimplemented.",
          f"A reproducible, seeded benchmark on PlantDoc ({F.NTRAIN:,} training and {F.NTEST} test photographs) that measures the shipped heuristic engine, the compact CNN of the training script, a MobileNetV2 transfer-learning reference and classical baselines under one protocol.",
          f"Findings that a reader can act on: the engine shipped in the application reaches {F.pct(HC['accuracy']['mean'])} top-1 accuracy when the crop is chosen, the compact CNN {F.pct(C['accuracy']['mean'])}, and a transfer-learning reference {F.pct(MB['accuracy']['mean'])}; seven defects were found and documented (Chapter 7)."),
        H2("1.7 Limitations and Assumptions"),
        P("The honest summary of the limits of this work is short. The application ships without a trained network, so its diagnosis is a colour-and-texture heuristic that is "
          f"no better than chance on PlantDoc photographs (top-1 {F.pct(HC['accuracy']['mean'])}, against {F.pct(F.H['chance_with_crop_hint'])} expected by chance when the crop is known). "
          f"It also fails outright for {F.pct(HC['failed_share']['mean'])} of the test photographs because ten of the nineteen crop keys of the engine (nine of the 18 offered in the web form) leave it with fewer than three candidate "
          "classes (defect D1). The best network measured, MobileNetV2, is not part of the application and still reaches only about half of the test photographs correctly."),
        P("The work assumes that the farmer photographs one leaf at a time, in daylight, and chooses the crop correctly; that the 38-class label set of the knowledge base "
          "covers the disease being photographed (ten of its classes have no PlantDoc images, and many real diseases are not in it); that PlantDoc is a fair stand-in for field photographs "
          "(it is a small, noisy, web-scraped set); and that the treatment text is a first guide to be confirmed by an agricultural officer, as the application says on every result."),
        H2("1.8 Organisation of the Report"),
        TAB("Organisation of the report", ["Chapter", "Content"],
            [["1 Introduction", "Domain, motivation, problem, objectives, scope, contributions, limits"],
             ["2 Literature Survey", "Base paper analysis, related work by theme, datasets and algorithms, research gap"],
             ["3 Feasibility Study", "Technical, economic, operational and schedule feasibility"],
             ["4 System Requirements and Analysis", "Existing and proposed system, requirements with implementation status, hardware, software, users"],
             ["5 System Design", "Architecture, workflow, data flow diagrams, UML, database, modules, user interface"],
             ["6 Methodology and Software Implementation", "Dataset, preprocessing, engines, training, API, security, installation"],
             ["7 System Testing", "Strategy, unit, integration, security, edge cases, performance, defects found"],
             ["8 Results and Output Screens", "Measured accuracy of every engine, output screens, failure analysis, objectives against outcomes"],
             ["9 Conclusion", "Summary, findings, practical use, known limits"],
             ["10 Future Scope", "What would make the system usable in a field"],
             ["References and Appendices", "IEEE reference list; important code; installation and user guide; additional screens"]],
            widths=[2.4, 4.3], align=["l", "l"], size=10.5),
    ]
