"""Chapters 3 (Feasibility Study) and 4 (System Requirements and Analysis). Numbers come from facts.py."""

from . import facts as F
from .blocks import B, H1, H2, H3, N, P, TAB
from .refs import cite

HC, C, MB, LAT = F.HC, F.C, F.MB, F.LAT


def chapter3():
    return [
        H1("CHAPTER 3: FEASIBILITY STUDY"),
        P("A feasibility study asks whether the proposed system can be built with the available means, at an acceptable cost, and used by the people it is meant for. "
          "The answers below are given for the system as it was actually built and measured, not only as planned."),
        H2("3.1 Technical Feasibility"),
        P("Every component of AgriVision is an open-source package that runs on one ordinary Windows computer. The measurement machine was " + F.HARDWARE +
          ". The tool chain was " + F.SOFTWARE + ". The question that matters is whether each technical risk was retired."),
        TAB("Technical risks and how they turned out", ["Risk", "Evidence", "Outcome"],
            [["A web stack with an image upload can run on a laptop", f"Backend start-up {LAT['startup_s']:.1f} s; detect call median {LAT['detect_client_ms']['median']:.0f} ms (p95 {LAT['detect_client_ms']['p95']:.0f} ms) on 127.0.0.1", "Feasible"],
             ["Two front ends can share one database", "FastAPI layer imports the Flask product's `init_db`, `inference` and `disease_db`; 39 smoke checks pass", "Feasible"],
             ["A CNN can be trained on a CPU in reasonable time", f"Compact CNN: about {F.C['train_seconds']['mean']:.0f} s per seed; MobileNetV2: about {MB['train_seconds']['mean']:.0f} s per seed (CPU only)", "Feasible"],
             ["A small CNN trained from scratch is accurate on field photographs", f"{F.pm(C)} test accuracy on PlantDoc ({F.NTRAIN:,} training photographs)", "Not feasible with this data and recipe"],
             ["Transfer learning reaches a useful level on the same data", f"MobileNetV2: {F.pm(MB)} accuracy, top-3 {F.pm(MB, 'top3_accuracy')}", "Partly: better, still about half of photographs correct"],
             ["A heuristic on colour and texture can replace a network", f"{F.pct(HC['accuracy']['mean'])} top-1 with the crop chosen; chance is {F.pct(F.H['chance_with_crop_hint'])}", "Not feasible"],
             ["A knowledge base can give advice for every recognised class", "38 classes, 26 curated cards and 5 generic kinds, three treatments each", "Feasible; agronomic validation outstanding"]],
            widths=[2.3, 3.1, 1.3], align=["l", "l", "l"], size=9.5),
        P("The technical conclusion is mixed and is carried through the rest of the report: the application is technically easy to build and run; the accuracy of the diagnosis "
          "is the technical risk that was not retired within the data and time available."),
        H2("3.2 Economic Feasibility"),
        P("No paid software, cloud service or data licence was used. All libraries are open source, PlantDoc is released under CC-BY-4.0, the pre-trained MobileNetV2 weights are "
          "downloaded free of charge, and the whole project was developed and measured on the student team's own computer. The table lists the cost heads and what each cost. "
          "No monetary figure is quoted because none was recorded; the point is that no cost head needs funding."),
        TAB("Cost heads", ["Item", "What was used", "Cost to the project"],
            [["Development hardware", F.HARDWARE, "Existing computer; no purchase"],
             ["Operating system and tools", "Windows 11, Python, Node.js, Git", "Free"],
             ["Libraries and frameworks", "TensorFlow, scikit-learn, OpenCV, Pillow, FastAPI, Flask, React, Vite, Tailwind CSS, Recharts", "Free, open source"],
             ["Dataset", "PlantDoc (CC-BY-4.0)", "Free"],
             ["Pre-trained weights", "MobileNetV2, ImageNet weights", "Free download"],
             ["GPU or cloud training", "Not used (everything ran on the CPU)", "None"],
             ["Hosting", "Not deployed; runs locally with `run.bat`", "None so far; a small virtual server would be the first recurring cost (not estimated)"],
             ["Expert validation of advice", "Not done", "Not incurred; would need an agronomist's time"]],
            widths=[1.8, 3.2, 1.7], align=["l", "l", "l"], size=9.5),
        P("For a farmer, the running cost is the cost of a smartphone and a data connection. The advice text itself quotes costs in rupees per acre for each treatment "
          "(for example \"250 to 600 rupees per acre per spray\" for chemical treatments); these are generic figures held in the knowledge base and have not been checked against "
          "local prices. Economic feasibility for the farmer therefore depends on a diagnosis accurate enough that a spray is not wasted, which the present engine does not provide."),
        H2("3.3 Operational Feasibility"),
        B("**Ease of use.** The farmer needs three actions: choose a crop, add a photograph (from files or the camera button), press \"Diagnose now\". The result page shows the disease, "
          "severity, top-3 list, an engine notice and treatments. The interface works at phone width (screenshot in Appendix C) and passed 55 browser checks at 360, 768 and 1,440 px "
          "in the frontend session.",
          "**Language.** The menus, headings and key labels are available in English, Hindi and Marathi; the disease and treatment text is English only, so operational feasibility "
          "for a farmer who reads only Hindi or Marathi is only partly met.",
          "**Operation by the institution.** Installation is one batch file; data are one SQLite file and one image folder that can be copied for backup.",
          "**Risk in use.** A wrong diagnosis with a high displayed confidence is the main operational hazard. The result page therefore states that the heuristic score is not a "
          "calibrated probability and asks the user to confirm with an agricultural officer before spraying."),
        H2("3.4 Schedule Feasibility"),
        P("The project was planned in phases over one academic project period. The table gives the phases in relative weeks; actual calendar dates are not recorded in the batch "
          "documents and are left blank on purpose."),
        TAB("Project phases (indicative, relative weeks)", ["Weeks", "Phase", "Outcome"],
            [["1-2", "Problem study and literature survey", "Batch documents 2 to 6; base paper read"],
             ["3-4", "Requirements and design", "PRD, class list, knowledge-base design, architecture"],
             ["5-8", "Original Flask product", "Detection page, history, disease guide, SQLite, heuristic engine"],
             ["9-10", "API layer and React front end", "FastAPI service, 12 pages, three-language interface, light and dark themes"],
             ["11-12", "Training script and measurements", "PlantDoc experiments, transfer-learning reference, latency measurement"],
             ["13-14", "Testing", "39 smoke checks, 51 edge checks, 55 browser checks; seven defects recorded"],
             ["15-16", "Documentation and presentation", "Decks, chapter documents, report, paper"]],
            widths=[0.9, 2.6, 3.2], align=["c", "l", "l"], size=9.5),
        P("The schedule was feasible for a working application and a measurement study. It was not long enough to collect a field dataset, to train and install a network "
          "that is accurate enough, or to validate the advice with an agronomist."),
        H2("3.5 Advantages and Constraints"),
        B("**Advantages.** Zero licence cost; one-command start; fast responses (a diagnosis returns in well under a second); a documented API; modular code that can take a trained "
          "model by dropping two files into `agrivision/models/`; honest self-reporting in the interface.",
          "**Constraints.** Small and noisy training data (2,342 photographs, 2 to 180 per class); CPU-only hardware; the 38-class label set; no expert panel; no field trial; "
          "an interface language that covers only part of the text; one machine used for both development and measurement."),
    ]


def feasibility_extra():
    return [
        H2("3.6 Risk Analysis"),
        TAB("Project risks and mitigation", ["Risk", "Effect", "Mitigation and status"],
            [["Training data too small for a network trained from scratch", "Low accuracy", f"Measured: {F.pct(C['accuracy']['mean'], 0)}; transfer learning raises it to {F.pct(MB['accuracy']['mean'], 0)}; larger or own data is future work"],
             ["Field photographs differ from laboratory images", "Large drop against published scores", "Evaluated on PlantDoc, not PlantVillage"],
             ["Wrong diagnosis shown with high confidence", "Wasted or wrong spray", "Engine notice on every result; recommendation to confirm with an officer; fix of the saturating score is future work"],
             ["Advice not validated by an agronomist", "Unsafe dosage or product", "Disclaimer in the interface; expert review listed as the first future task"],
             ["Public default signing secret", "Forged sessions on a shared server", "Set `AGRIVISION_SECRET`; recorded as defect D3"],
             ["Shared CPU with other jobs during training", "Longer and noisier timing figures", "Accuracy figures were stable across seeds; timings are indicative"]],
            widths=[2.3, 1.6, 2.8], align=["l", "l", "l"], size=9.5),
        H2("3.7 Legal and Ethical Considerations"),
        P("PlantDoc is released under CC-BY-4.0 and is credited. Photographs uploaded by users are personal data of the farmer's holding and are stored until deleted; the interface "
          "allows deletion of each scan and its image file. No data leave the machine on which the application runs. The advice text names chemical products and doses, "
          "so a responsible deployment needs expert review and local regulation checks before use; the application does not claim to replace an expert."),
    ]


def chapter4():
    st = {"I": "Implemented", "P": "Partly", "N": "Not implemented"}
    fr = [
        ["FR1", "Register with email, password (6 characters or more), name, region, language and crop", st["I"], "POST /auth/register; duplicate email 409"],
        ["FR2", "Sign in and out; a session token valid for 7 days", st["I"], "HMAC-signed bearer token (defects D3, D4)"],
        ["FR3", "Upload a leaf photograph (JPG, PNG, JPEG, WEBP, up to 10 MB) and choose the crop; camera capture", st["I"], "413 above 10 MB, 400 for other formats"],
        ["FR4", "Return the most likely class, top-3 list, confidence and severity", st["P"], f"Returned, but accuracy is {F.pct(HC['accuracy']['mean'])} (D1, D2)"],
        ["FR5", "Show symptoms, lifecycle, chemical, organic and cultural treatments and prevention for each class", st["I"], "38 classes; 26 curated cards"],
        ["FR6", "Recommend fertiliser", st["N"], "Only treatment text exists"],
        ["FR7", "Predict crop yield from environmental data", st["N"], "No model, no data source"],
        ["FR8", "Give weather-based farming recommendations", st["N"], "The dashboard season alert is a fixed sentence"],
        ["FR9", "Keep a history of scans with search, crop and healthy/diseased filters, and delete", st["I"], "GET /history, DELETE /history/{id}"],
        ["FR10", "Export one scan or all scans as CSV, one scan as PDF", st["I"], "reportlab PDF"],
        ["FR11", "Dashboard of totals and recent scans; analytics charts", st["I"], "Distribution, severity, timeline"],
        ["FR12", "Edit profile: name, region, language, crops", st["I"], "PUT /profile"],
        ["FR13", "Interface in English, Hindi and Marathi", st["P"], "44 interface keys; disease and treatment text English only"],
        ["FR14", "Browse the disease guide without signing in", st["I"], "38 cards, detail page"],
        ["FR15", "Use a trained CNN for diagnosis", st["P"], "train.py and experiments exist; no weights installed in the application"],
        ["FR16", "Administrative dashboard", st["N"], "Not built"],
        ["FR17", "Voice interface in regional languages", st["N"], "Not built"],
    ]
    nfr = [
        ["NFR1 Performance", "A diagnosis should return within a second", f"Median {LAT['detect_client_ms']['median']:.0f} ms, p95 {LAT['detect_client_ms']['p95']:.0f} ms client round trip (100 photographs, 127.0.0.1)", "Met"],
        ["NFR2 Accuracy", "Correct class for most field photographs", f"Best measured {F.pm(MB)} (MobileNetV2, not installed); shipped engine {F.pct(HC['accuracy']['mean'])}", "Not met"],
        ["NFR3 Usability", "Usable by a non-expert on a phone", "Three-step flow; 55 browser checks at 360, 768, 1,440 px passed (previous session)", "Met for the interface"],
        ["NFR4 Security", "Authenticated access, hashed passwords, ownership checks", "Salted scrypt hashes, forged and expired tokens refused, other users' scans return 404; defects D3, D4", "Partly met"],
        ["NFR5 Reliability", "Errors are reported cleanly", "One JSON error shape for 400, 401, 404, 409, 413; defect D1 makes a valid photograph look unreadable", "Partly met"],
        ["NFR6 Portability", "Runs on a normal Windows PC", "`run.bat` creates the environment; Python 3.10+ and Node 20+", "Met"],
        ["NFR7 Maintainability", "Modular, documented code", f"{F.LOC['agrivision']} lines of legacy Python, {F.LOC['backend']} lines API, {F.LOC['frontend']:,} lines TypeScript; tests in `scripts/`", "Met"],
        ["NFR8 Honesty", "The interface must not overstate certainty", "Engine notice on every result and in the sidebar; but the displayed score still saturates near 97 % (D2)", "Partly met"],
        ["NFR9 Privacy", "Photographs belong to the user", "Stored on the server in a folder; served by random file name without a token", "Partly met"],
    ]
    return [
        H1("CHAPTER 4: SYSTEM REQUIREMENTS AND ANALYSIS"),
        H2("4.1 Existing System and Its Limitations"),
        P("Farmers today identify disease in one of four ways: their own experience, advice from a neighbour or a seed-shop owner, a visit by an agricultural officer, or a laboratory test. "
          "The literature adds machine-learning tools " + cite("mohanty", "ferentinos", "pd36c") + " and a mobile detector built on PlantDoc " + cite("plantdoc") + "."),
        TAB("Existing approaches and their limits", ["Approach", "Strength", "Limitation for a smallholder"],
            [["Own experience, neighbours", "Immediate, free", "Fails on a new disease; no record; advice may be wrong or outdated"],
             ["Agricultural officer or expert", "Authoritative", "Few experts, long distances, delay while the disease spreads"],
             ["Laboratory diagnosis", "Accurate", "Slow, costly, needs sample transport"],
             ["Published CNN classifiers " + cite("pd36c", "lstm"), "99 % on curated data", "Evaluated on laboratory images; stop at a class label; no advice, no language support"],
             ["Generic agricultural apps", "Broad content", "Fragmented, often English only, not tied to the photograph (batch abstract)"]],
            widths=[2.0, 1.7, 3.0], align=["l", "l", "l"], size=9.5),
        H2("4.2 Proposed System and Its Advantages"),
        P("AgriVision is a web application in which a signed-in farmer uploads a leaf photograph and the crop, and receives a diagnosis with severity, the top three candidates, "
          "treatments (chemical, organic, cultural) with cost text, and prevention advice; the scan is saved in a history that can be filtered, exported and analysed. The "
          "interface can be switched between English, Hindi and Marathi. The diagnosis engine is a module with one function, `predict(image_bytes, crop)`, behind which either the "
          "built-in heuristic or a trained network can sit."),
        B("One place for the photograph, the diagnosis, the advice and the record of what was found, instead of four separate steps.",
          "The advice is attached to each class in a knowledge base that can be reviewed and edited by an expert without touching the image code.",
          "A modest computer is enough; there is no cloud dependency.",
          "A documented REST API (`/docs`) lets other tools, such as a phone application, use the same service.",
          "The system reports its own engine and warns about its limits on every result."),
        H2("4.3 Functional Requirements"),
        P("The functional requirements are taken from the batch abstract and the product requirements document and are listed with the status they reached. \"Partly\" means the "
          "item exists but does not meet its intention."),
        TAB("Functional requirements and implementation status", ["ID", "Requirement", "Status", "Note"], fr, widths=[0.5, 3.2, 1.0, 2.0], align=["c", "l", "l", "l"], size=9),
        P(f"Of the seventeen requirements, {sum(1 for r in fr if r[2] == st['I'])} are implemented, {sum(1 for r in fr if r[2] == st['P'])} are partly implemented and "
          f"{sum(1 for r in fr if r[2] == st['N'])} are not implemented. The five missing items (fertiliser, yield, weather, administration, voice) are the parts of the batch abstract "
          "that go beyond diagnosis and advice."),
        H2("4.4 Non-Functional Requirements"),
        TAB("Non-functional requirements and the evidence for them", ["Requirement", "Target", "Evidence", "Status"], nfr, widths=[1.2, 1.7, 2.9, 0.9], align=["l", "l", "l", "l"], size=9),
        H2("4.5 Hardware Requirements"),
        TAB("Hardware", ["Role", "Used and measured", "Remark"],
            [["Server and development PC", F.HARDWARE, "All measurements in this report were made on this machine; training ran on the CPU"],
             ["Minimum for running the application", "Not measured separately", "The backend starts in about 2 s and uses no GPU; any PC that runs Python 3.10 and a browser should do"],
             ["Training the CNNs", "The same PC; 15.7 GB RAM; about 6 to 13 minutes per run", "A GPU is not required for this data size, but would shorten transfer-learning runs"],
             ["Farmer's device", "Any current phone or PC browser with a camera and a network connection", "The interface was checked at 360, 390, 768 and 1,440 px widths"]],
            widths=[1.8, 2.5, 2.4], align=["l", "l", "l"], size=9.5),
        H2("4.6 Software Requirements"),
        TAB("Software", ["Layer", "Software", "Purpose"],
            [["Operating system", "Windows 11 Pro (measured); the stack is cross-platform", "Host"],
             ["Language runtimes", "Python 3.11.9, Node 24.19 (Python 3.10+ and Node 20+ required by `run.bat`)", "Backend, front-end build"],
             ["Backend", "FastAPI, uvicorn, python-multipart, Flask 3.1 (original product), Pillow, NumPy, reportlab, SQLite (standard library)", "API, image handling, PDF export, storage"],
             ["Front end", "React 18.3, Vite 8, TypeScript 5.9, Tailwind CSS 4, TanStack Query, Recharts, GSAP, react-router 7", "Single-page application"],
             ["Machine learning (offline)", "TensorFlow 2.21 (Keras 3), scikit-learn 1.5, OpenCV 4.11", "Training and measurement; not required to run the application"],
             ["Testing and capture", "Python scripts in `scripts/`, Playwright with Chrome", "API checks, browser checks, screenshots"],
             ["Browser", "Chrome or Edge, current version", "Client"]],
            widths=[1.5, 3.4, 1.8], align=["l", "l", "l"], size=9.5),
        H2("4.7 User Roles"),
        TAB("User roles", ["Role", "Can do", "Cannot do"],
            [["Visitor (guest)", "See the landing page, browse the disease guide, register, sign in", "Diagnose, see history"],
             ["Farmer (registered)", "Upload and diagnose, view and filter history, export, delete own scans, view dashboard and analytics, edit profile, change language", "See another user's scans (404)"],
             ["Model owner (offline)", "Run `train.py` and `run_experiments.py`, install weights in `agrivision/models/`, edit the knowledge base", "Not a role of the web application"],
             ["Administrator", "Planned in the batch abstract", "Not implemented; the `role` column of `users` exists and holds 'farmer'"]],
            widths=[1.5, 3.3, 1.9], align=["l", "l", "l"], size=9.5),
        H2("4.8 Use-Case Descriptions"),
        TAB("Main use cases", ["Use case", "Actor and precondition", "Main flow", "Alternative flows"],
            [["UC1 Diagnose a leaf", "Farmer, signed in", "Choose crop; add photo; press Diagnose now; result page shows class, severity, top-3, treatments", "Bad file: 400 message; over 10 MB: 413; crop with fewer than 3 classes: 400 (D1); token expired: back to sign-in"],
             ["UC2 Review history", "Farmer, at least one scan", "Open History; search, filter by crop or healthy/diseased; open a scan; export CSV or PDF", "No match: empty state; scan of another user: 404"],
             ["UC3 Delete a scan", "Farmer, owner of the scan", "Press delete, confirm; row and image file are removed", "Not owner: 404"],
             ["UC4 Browse the guide", "Anyone", "Open Disease guide; search; open a disease card", "Unknown name: 404"],
             ["UC5 Change language or profile", "Farmer, signed in", "Open the language menu or Profile; choose English, Hindi or Marathi; save", "Unsupported language: 400"],
             ["UC6 Measure an engine", "Model owner, dataset present", "Run `run_experiments.py`; read `experiments/plantdoc/metrics.json`", "Missing TensorFlow: only heuristic and baseline commands run"]],
            widths=[1.3, 1.4, 2.4, 1.6], align=["l", "l", "l", "l"], size=8.5),
        H2("4.9 Data Requirements"),
        TAB("Data held by the system", ["Data", "Fields", "Kept in", "Retention"],
            [["User", "id, email (unique), phone, full name, password hash, role, region, language, crops, created, active flag", "SQLite table `users`", "Until the database is removed"],
             ["Scan result", "id, user id, image path and size, predicted class, confidence, top-3 JSON, severity, crop hint, latency, time, bookmark flag", "SQLite table `results`", "Until the user deletes the scan"],
             ["Leaf image", "JPG, PNG, JPEG or WEBP up to 10 MB, stored under a random file name", "`agrivision/static/uploads/`", "Deleted together with the scan"],
             ["Knowledge base", "38 class cards: symptoms, lifecycle, severity, three treatments, prevention, urgent flag", "`disease_db.py` (code)", "Part of the source"],
             ["Training data", f"PlantDoc folders ({F.NTRAIN:,} train, {F.NTEST} test)", "`datasets/` (git-ignored, 445 MB)", "Developer machine only"]],
            widths=[1.2, 2.9, 1.4, 1.2], align=["l", "l", "l", "l"], size=9),
        H2("4.10 Traceability from Objectives to Requirements"),
        TAB("Objectives and the requirements that serve them", ["Objective (batch)", "Requirements", "Status"],
            [["1 Assemble a labelled dataset", "Data requirements, FR15", "Delivered with PlantDoc (not self-collected)"],
             ["2 Preprocess and augment", "FR15", "In the training script and experiments only"],
             ["3 Train a CNN", "FR15", "Trained and measured; not installed in the application"],
             ["4 Map disease to treatment and fertiliser advice", "FR5, FR6", "Treatment yes, fertiliser no"],
             ["5 Web interface with multilingual support", "FR1 to FR3, FR9 to FR14", "Interface yes; advice text English only"],
             ["6 Per-class accuracy; validate recommendations", "NFR2, NFR8", "Per-class accuracy measured; recommendations not validated"]],
            widths=[2.6, 1.6, 2.5], align=["l", "l", "l"], size=9.5),
        H2("4.11 Constraints and Assumptions"),
        B("**Data.** Only PlantDoc was used; no photographs were collected by the team; the knowledge base covers 38 classes of 14 crops.",
          "**Accuracy.** The shipped engine is a heuristic; the trained networks are offline experiments.",
          "**Advice.** Treatments and costs are generic and were not validated by an agronomist; they must be confirmed locally before spraying.",
          "**Network and device.** The application assumes a connection to the server; there is no offline mode.",
          "**Security.** The default signing secret must be replaced through `AGRIVISION_SECRET` before any deployment beyond a classroom; login attempts are not limited.",
          "**Privacy.** Uploaded photographs are retained until the user deletes the scan."),
    ]


def blocks():
    return chapter3() + feasibility_extra() + chapter4()
