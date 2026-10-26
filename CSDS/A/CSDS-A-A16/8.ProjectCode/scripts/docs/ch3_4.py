"""Chapters 3 (Feasibility Study) and 4 (System Requirements and Analysis) for Mosaic (CSDS-A-A16)."""

from . import facts as F
from . import lit
from .blocks import B, H1, H2, H3, N, P, TAB
from .refs import CITE as R


def _lat(label_start):
    for l in (F.APIM or {}).get("latency", []):
        if l["label"].startswith(label_start):
            return l
    return None


def _p50(label_start, default="n/a"):
    l = _lat(label_start)
    return f"{l['p50_ms']:.1f}" if l else default


def _minutes():
    m = [v["config"]["minutes"] for v in F.ABL.values()]
    return f"{min(m):.0f} to {max(m):.0f}" if m else "several"


def feasibility_blocks():
    n_tests = F.TESTS["tests"] if F.TESTS else "n/a"
    fin, base = F.FIN, F.BASE
    return [
        H1("3. FEASIBILITY STUDY"),
        H2("3.1 Introduction"),
        P(f"Before the design was fixed, the project was examined for technical, economic, operational and schedule feasibility. This chapter records that examination with the evidence gathered while building and measuring {F.PRODUCT}: "
          "what was available, what it cost, who would run it and how the work was organised. The idea under test is the one taken from the base paper "
          f"[{R['base']}]: generate faces that show two emotions at once, then train a multi-label classifier on them."),
        H2("3.2 Technical Feasibility"),
        P("The product needs six capabilities: a face dataset, a face detector, a convolutional classifier, a conditional generator, a web service with storage, and a browser interface. Each is available in free, widely used libraries, "
          "and each was shown to run on the development machine (an Intel Core i5-12500 class desktop with 6 cores and 12 threads, 15.7 GB of memory, Windows 11 Pro, **no GPU**). "
          "All training in this project therefore ran on the CPU."),
        TAB("Technology choices and the evidence that they are feasible", ["Capability", "Choice (pinned version)", "Evidence"],
            [["Dataset", f"FER2013 pickles from a Hugging Face mirror [{R['fer2013']}]", f"{F.DATA['n_train']:,} training and {F.DATA['n_test']:,} test faces (48 x 48, grayscale) load in about a minute."],
             ["Face detection", f"OpenCV 4.10 headless, Haar cascade [{R['viola']}][{R['opencv']}]", "Bundled cascade file; no model download, no GPU. Finds 0 % of raw 48-pixel faces and about half of upscaled ones (Chapter 8)."],
             ["Classifier and generator", f"PyTorch 2.4.1, torchvision 0.19.1 [{R['pytorch']}], CPU only", f"EmotionCNN with {fin['parameters']:,} parameters trains five epochs in roughly 2 minutes per epoch on a shared CPU."],
             ["Web service", f"FastAPI 0.115.0 [{R['fastapi']}], uvicorn 0.30.6, SQLAlchemy 2.0.35, pydantic 2.9.2", f"Eight JSON endpoints plus a static thumbnail mount; median analyse request {_p50('POST /api/analyze anonymous')} ms over HTTP on 127.0.0.1."],
             ["Accounts", "python-jose 3.3.0 (HS256), passlib 1.7.4 with bcrypt 4.0.1", f"Login median {_p50('POST /api/auth/login')} ms, dominated by the bcrypt work factor."],
             ["Storage", "SQLite through SQLAlchemy", "Two tables; no database server to install."],
             ["Interface", f"Next.js 16.3.6, React 19.2.8, TypeScript 5, Tailwind CSS 4 [{R['nextjs']}], Recharts 3, zustand 5", "Seven routes built (landing, login, register, analyze, history, history detail, not-found); 19 screens captured with data."],
             ["Tests", "pytest with FastAPI TestClient", f"{n_tests} automated tests pass in about {F.TESTS['seconds']:.0f} seconds." if F.TESTS else "pytest suite present."]],
            widths=[1.2, 2.3, 3.0], align=["l", "l", "l"], size=9.5),
        P("Capacity was judged against the smallest and largest jobs the product performs. A single analysis is one face crop through a network of "
          f"{fin['parameters']:,} parameters, which the measurements put at a median of {_p50('POST /api/analyze anonymous')} ms end to end. Training is the heavy part: the final classifier took 10 minutes 37 seconds for five epochs on 30,909 images "
          "while other jobs were running on the same machine, and each seeded re-training in Chapter 8 took " + _minutes() + " minutes. A GPU would shorten this but is not required."),
        P("Three technical risks were identified and examined. The first is **data**: FER2013 has no compound-emotion labels, so the compound half of the system can be trained only on synthetic faces and cannot be validated on real ones. "
          "The second is **generator quality**: the conditional GAN is small (about 1.1 million parameters) and was trained for ten epochs on 2,800 faces, which is far less than the base paper's setting. "
          f"The third is **recognition accuracy on real faces**: the single-label baseline reaches {base['accuracy'] * 100:.1f} % and the final model {fin['accuracy'] * 100:.1f} % on the 7,178 test faces, "
          f"in line with the {51.6:.1f} % that a lightweight CNN is reported to reach on FER-2013 in a recent study [{R['galkaduwa']}], but well below what laboratory datasets allow. "
          "These are feasibility results in the sense that the pipeline runs end to end and is measurable; Chapter 8 reports honestly where the compound objective was not met."),
        H2("3.3 Economic Feasibility"),
        P("The project was carried out with no expenditure on licences, cloud services or special hardware. Every library used is open source under a permissive licence (FastAPI, React, Next.js and Tailwind under MIT, PyTorch under a BSD-style licence, "
          "OpenCV under Apache 2.0 or BSD depending on version). The computer was an ordinary desktop; no GPU, database server, message broker or paid API is needed, and no calls leave the machine at run time."),
        P("The dataset is the one external asset. The Hugging Face mirror used here tags FER2013 as apache-2.0; the original competition terms are less clear, so the data is not redistributed in the documents "
          "and the code reads it from `backend/data/`, which the repository ignores. No cost was incurred for data, software or hosting."),
        TAB("Cost summary", ["Item", "Cost incurred", "Remark"],
            [["Software licences", "None", "All components open source"],
             ["Cloud or hosting", "None", "Runs on one local machine; the API binds to localhost"],
             ["GPU or special hardware", "None", "CPU-only training and inference"],
             ["Dataset", "None", "Public FER2013 mirror; licence caveat above"],
             ["Staff time", "Team effort only", "Four students, one guide; no cost is estimated here"]],
            widths=[1.9, 1.5, 3.1], align=["l", "l", "l"]),
        P("For a real deployment the main recurring costs would be hosting a CPU server and, more importantly, obtaining a licensed, consented dataset with genuine compound labels; neither was needed for this project and neither is priced here."),
        H2("3.4 Operational Feasibility"),
        P("A user needs only a browser. Registration takes a name, an e-mail address and a password of at least six characters; analysing a face is a drag-and-drop or one webcam click; the result appears in well under a second on the test machine "
          "and is stored in a history list. An operator needs Python 3.11, Node.js and two commands per tier (`uvicorn app.main:app` and `npm run start`), plus a one-off training run if the checkpoint is absent. "
          "The last point mattered in practice: the batch was received without `classifier_final.pt`, so the API answered `model_loaded: false` until the final training stage was run. "
          "A start-up message or a bundled checkpoint would remove this hurdle; the repository ignores `checkpoints/` for size reasons."),
        P("The system keeps no photographs: only the cropped grayscale face of a signed-in user's analysis is written to `media/thumbs/`, and the user can delete any history entry. "
          "Passwords are stored as bcrypt hashes. Facial-expression analysis is nevertheless sensitive, and the base paper itself notes that informed consent and data protection must be respected when such methods are used at scale [" + f"{R['base']}" + "]."),
        H2("3.5 Schedule Feasibility"),
        P("The work was planned in phases of one to three weeks. The table gives the relative order and duration of each phase; calendar dates are not recorded here because they are not part of the repository history."),
        TAB("Work plan", ["Phase", "Weeks", "Main outputs"],
            [["1. Study and planning", "1 - 2", "Base paper read, objectives and taxonomy fixed, API contract written"],
             ["2. Data and backbone", "3 - 4", "FER2013 loader, 7-class backbone CNN, first accuracy figure"],
             ["3. Generator and synthesis", "5 - 7", "Conditional GAN, compound-face synthesis, 18-label classifier"],
             ["4. Service", "6 - 8", "FastAPI routers, JWT accounts, SQLite history, Haar face detection"],
             ["5. Interface", "7 - 10", "Next.js landing, auth, analyse and history screens, charts"],
             ["6. Testing and measurement", "10 - 12", "pytest suite, seeded ablation, GAN fidelity and API measurements"],
             ["7. Documentation", "11 - 13", "Diagrams, decks, chapter documents, report and IEEE paper"]],
            widths=[2.1, 0.8, 3.6], align=["l", "c", "l"]),
        P("Schedule risk came mostly from CPU training time and from a shared machine: one training run is minutes, but a seeded study of eight runs is more than an hour. The risk was handled by running the studies unattended in a single chained script."),
        H2("3.6 Advantages and Constraints"),
        B("**Advantages.** Everything is local, free and reproducible; the code base is small (about 1,000 lines of backend Python); the same 64 x 64 network serves seven basic and eleven compound outputs; "
          "the evaluation includes a no-synthesis control, so the effect of the generated faces can be isolated.",
          "**Constraints.** FER2013 is small, low-resolution (48 x 48) and noisily labelled, and has no compound labels. Training and serving frames differ (aligned dataset crops versus Haar crops of arbitrary photographs). "
          "The generator is small and under-trained. There is no real compound test set, so the compound objective can be examined only on synthetic faces."),
    ]


def requirements_blocks():
    t = F.TESTS
    return [
        H1("4. SYSTEM REQUIREMENTS AND ANALYSIS"),
        H2("4.1 Introduction"),
        P("This chapter states what was built and why. It describes the existing approaches and their limits, the proposed system, the requirements it was held to, the hardware and software needed to run it, the user roles and the constraints. "
          "Requirement identifiers (FR for functional, NFR for non-functional) are used again in the testing and results chapters."),
        H2("4.2 Existing System and Its Limitations"),
        P(f"Facial emotion recognition is normally framed as single-label classification of the six basic emotions of Ekman and Friesen [{R['ekman']}] plus neutral. Public datasets such as FER2013 [{R['fer2013']}], CK+ [{R['ckplus']}] and AffectNet [{R['affectnet']}] follow that framing, "
          f"and CNN classifiers trained on them are the standard baseline [{R['lideng']}]; a recent comparison reports 51.6 % accuracy for a lightweight CNN on FER-2013 against 44.0 % for HOG with an SVM [{R['galkaduwa']}]. "
          f"Real expressions mix emotions, a fact studied by Du, Tao and Martinez [{R['du2014']}] and addressed by compound-expression challenges built on RAF-DB [{R['rafdb']}], where an ensemble of ViT, PosterV2 and ResNet reaches 60.4 to 64.3 % accuracy on seven compound classes [{R['abaw7']}]. "
          "Those systems need real compound labels, which are scarce. Expression-editing GANs such as StarGAN and GANimation [" + f"{R['stargan']}][{R['ganimation']}" + "] can create new expressions but may distort identity."),
        TAB("Limitations of the existing approaches", ["Approach", "What it does", "Limitation addressed by this project"],
            [["Single-label CNN on FER2013", "One of seven labels per image", "Cannot express two emotions in one face"],
             ["Classical features (HOG, LBP) with SVM or regression", "Hand-made descriptors", "Weak on unconstrained images; far below CNNs on FER-2013"],
             ["Compound recognition on RAF-DB or C-EXPR-DB", "Supervised on real compound labels", "Depends on scarce, licensed data"],
             ["Generic expression-editing GANs", "Transfer or edit an expression", "No multi-label training target; identity may drift"],
             ["Research code without an application", "Offline scores on a split", "No service, accounts or history for an end user"]],
            widths=[2.2, 1.9, 2.4], align=["l", "l", "l"], size=9.5),
        H2("4.3 Proposed System"),
        P(f"Mosaic follows the analysis-by-synthesis idea of the base paper [{R['base']}] at a much smaller scale. A conditional GAN, trained on real faces with a seven-dimensional emotion condition, is asked for faces whose condition has two active components at 0.5 each; "
          "those faces, labelled with both basic emotions and the matching compound emotion, are added to the real training faces. A compact CNN with 18 sigmoid outputs (seven basic and eleven compound labels) is trained on the union with binary cross-entropy, "
          "so that one image can carry several positive labels. A FastAPI service wraps the detector and the network, adds accounts and history, and a Next.js console lets a user upload a photo or take a webcam frame and read the result."),
        B("**Multi-label output.** Every analysis returns 18 independent confidences instead of one forced class.",
          "**Synthetic enlargement.** The compound classes are populated with generated faces, because no real compound faces were available.",
          "**Single pipeline.** The same inference function serves anonymous and signed-in calls; only signed-in calls are stored.",
          "**Local and private.** No call leaves the machine; only the cropped grayscale face is kept, and only for signed-in users.",
          "**Measurable.** The repository includes the training log, a test suite and scripts that produced every number in this report."),
        P("The advantages are architectural and practical; whether the synthetic faces actually teach the classifier compound emotions is an empirical question answered in Chapter 8, where the result is negative for this implementation."),
        H2("4.4 Functional Requirements"),
        TAB("Functional requirements", ["ID", "Requirement", "Where implemented"],
            [["FR1", "A visitor can register with name, e-mail and a password of at least six characters; duplicate e-mails are rejected (HTTP 409)", "`routers/auth.py`, `schemas.RegisterRequest`"],
             ["FR2", "A registered user can log in and receives a signed token valid for seven days; wrong credentials give HTTP 401", "`routers/auth.py`, `security.py`"],
             ["FR3", "The client can retrieve the current user from a token", "`GET /api/auth/me`"],
             ["FR4", "A user can submit a JPEG or PNG by upload, drag and drop, or webcam capture", "`CaptureWidget.tsx`, `POST /api/analyze`"],
             ["FR5", "The system detects the largest face in the image and rejects images with no face", "`ml/face.py`, `ml/inference.py`"],
             ["FR6", "The system returns the seven basic and eleven compound confidences, each list sorted, plus the dominant emotion and its kind", "`ml/inference.py`"],
             ["FR7", "The result is displayed as a dominant-emotion card, a basic-emotion bar chart and the six highest compound scores", "`ResultsView.tsx`"],
             ["FR8", "A signed-in user's analyses are stored with a cropped-face thumbnail", "`routers/analyze.py`, `models.Analysis`"],
             ["FR9", "A user can list their history, newest first, with limit and offset", "`GET /api/history`"],
             ["FR10", "A user can open and delete one of their own history entries; others' entries answer 404", "`/api/history/{id}`"],
             ["FR11", "Anyone can check whether the model is loaded", "`GET /api/health`"],
             ["FR12", "The classifier is trained from FER2013 and synthetic compound faces by one command, which logs its results", "`ml/run_pipeline.py`"],
             ["FR13", "The generator synthesises faces for the eleven compound classes by blending two basic conditions", "`ml/synthesize_compound.py`"],
             ["FR14", "Users can log out; the token is cleared in the browser", "`DashboardShell.tsx`, `lib/store.ts`"]],
            widths=[0.5, 4.0, 2.0], align=["c", "l", "l"], size=9.5),
        H2("4.5 Non-Functional Requirements"),
        TAB("Non-functional requirements", ["ID", "Requirement", "How it is met or measured"],
            [["NFR1", "Responsiveness: an analysis should finish in well under a second on a CPU", f"Measured median {_p50('POST /api/analyze anonymous')} ms (anonymous) and {_p50('POST /api/analyze authenticated')} ms (stored) over 127.0.0.1"],
             ["NFR2", "Passwords are never stored in clear text", "bcrypt hash; the response never contains the hash"],
             ["NFR3", "Protected routes reject missing or forged tokens", "HTTP 401 for no, tampered or expired tokens; tested"],
             ["NFR4", "One user cannot read or delete another's history", "Queries filter on `user_id`; tested (HTTP 404)"],
             ["NFR5", "Browser access is restricted to the known front-end origin", "CORS allows `localhost:3000` and `127.0.0.1:3000` only"],
             ["NFR6", "The system runs without a GPU or cloud service", "PyTorch CPU build; no outbound calls"],
             ["NFR7", "The code is covered by automated tests", f"{t['tests']} tests, {t['failures']} failures" if t else "pytest suite"],
             ["NFR8", "Invalid input should produce a clean error, not a crash", "Validation errors give HTTP 422; **undecodable uploads currently give HTTP 500** (documented defect)"],
             ["NFR9", "Recognition accuracy comparable to published lightweight CNNs on FER2013", f"{F.FIN['accuracy'] * 100:.1f} % on the 7,178 test faces (Chapter 8)"],
             ["NFR10", "Reproducibility", "Scripts and JSON metrics for every reported number; seeds fixed in the ablation study"]],
            widths=[0.6, 3.0, 2.9], align=["c", "l", "l"], size=9.5),
        H2("4.6 Hardware Requirements"),
        TAB("Hardware", ["Item", "Minimum", "Used in this project"],
            [["Processor", "x86-64, 4 cores", "Intel Core i5-12500 class, 6 cores / 12 threads"],
             ["Memory", "8 GB", "15.7 GB"],
             ["Disk", "2 GB free (dependencies, data, checkpoints)", "Local SSD"],
             ["GPU", "Not required", "None"],
             ["Camera", "Optional (webcam tab)", "Not used for the screenshots; real FER2013 faces were uploaded"],
             ["Display", "1280 x 720", "1440 x 900 for screenshots"]],
            widths=[1.4, 2.4, 2.7], align=["l", "l", "l"]),
        H2("4.7 Software Requirements"),
        TAB("Software (pinned in `backend/requirements.txt` and `frontend/package.json`)", ["Layer", "Package", "Version"],
            [["Runtime", "Python / Node.js", "3.11 (used 3.11.9) / 24.x (used 24.19.0)"],
             ["Web service", "fastapi, uvicorn[standard], pydantic, pydantic-settings", "0.115.0, 0.30.6, 2.9.2, 2.5.2"],
             ["Data layer", "sqlalchemy, python-multipart", "2.0.35, 0.0.9"],
             ["Security", "python-jose[cryptography], passlib[bcrypt], bcrypt", "3.3.0, 1.7.4, 4.0.1"],
             ["ML", "torch, torchvision, opencv-python-headless, numpy, pandas, pillow, requests", "2.4.1, 0.19.1, 4.10.0.84, 1.26.4, 2.2.2, 10.4.0, 2.32.3"],
             ["Front end", "next, react, react-dom, typescript", "16.3.6, 19.2.8, 19.2.8, ^5"],
             ["Front-end libraries", "tailwindcss, framer-motion, gsap, lenis, three, @react-three/fiber, @react-three/drei, recharts, zustand, react-webcam, lucide-react", "^4, ^13.4.1, ^3.15.0, ^1.3.26, ^0.186.0, ^9.8.0, ^10.7.8, ^3.10.1, ^5.0.15, ^7.2.0, ^1.47.0"],
             ["Testing", "pytest, FastAPI TestClient (httpx)", "8.2.0 (used), 0.28.1 (used)"],
             ["Browser", "Chrome-class browser", "Chrome via Playwright for screenshots"]],
            widths=[1.2, 3.3, 2.0], align=["l", "l", "l"], size=9),
        P("The documentation run used newer installed versions of several packages than the pins (for example FastAPI 0.143.3, torch 2.14.1 and uvicorn 0.54.0 in the system interpreter), with `bcrypt` pinned back to 4.0.1 because bcrypt 5 breaks passlib hashing. "
          "The pinned `backend/.venv` shipped in the batch was a Python 3.10 environment from another machine and could not be used."),
        H2("4.8 User Roles"),
        TAB("User roles", ["Role", "Access", "Can do"],
            [["Anonymous caller (API only)", "No token", "Call `POST /api/analyze` and `GET /api/health`; the result is returned but not stored. The web UI does not offer this path: `/app` redirects to login."],
             ["Registered user", "Bearer token, seven days", "Analyse faces, view and delete own history, read own profile"],
             ["Developer / operator", "Command line", "Run the training pipeline, start the servers, run the tests and measurement scripts"]],
            widths=[1.8, 1.6, 3.1], align=["l", "l", "l"]),
        P("There is no administrator role and no moderation interface; every user is equal and sees only their own data."),
        H2("4.9 Constraints and Assumptions"),
        B("The compound taxonomy has eleven categories taken as a subset of the compound categories described by Du, Tao and Martinez [" + f"{R['du2014']}" + "]; it is fixed in code and mirrored in the front end and API contract.",
          "The classifier input is a 64 x 64 grayscale face; colour, pose and occlusion are not modelled.",
          "FER2013 labels are single basic emotions; the classifier's compound outputs rest entirely on generated faces.",
          "Face detection relies on the OpenCV Haar cascade and assumes a roughly frontal face of at least 40 x 40 pixels.",
          "The service is designed for a single machine; there is no rate limiting, e-mail verification or password reset.",
          "Ports used in code are 8000 (API) and 3000 (UI); during this documentation run port 8000 was occupied by another program, so the API ran on 8116."),
    ]


def blocks():
    return feasibility_blocks() + requirements_blocks()
