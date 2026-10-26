"""Chapter 5: System Design (also the 'Design' part of document 12 and the diagram texts of document 11)."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, PAIR, TAB
from .refs import cite

# (key, title, file, caption, text) - used by document 11 and by the blocks below
DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png",
     "Three-tier architecture of AgriVision: browser, FastAPI service, original Flask modules, and the data stores.",
     "The browser tier is a React single-page application (twelve page components, axios client, TanStack Query hooks, English, Hindi and Marathi interface strings) served by Vite on port 5416, "
     "which proxies every /api request to the application tier. The application tier is `backend/main.py`: sixteen FastAPI routes grouped into account, diagnosis, history and reports, and "
     "insight (dashboard and analytics), plus public routes for health, the disease guide and uploaded images. The domain tier is the unchanged Flask product in `agrivision/`: `inference.py` "
     "(the diagnosis engine), `disease_db.py` (the 38-class knowledge base) and `app.py`/`config.py` (table creation, limits). Below them sit the SQLite file with the `users` and `results` tables, "
     "the folder of uploaded images, and the offline `models/` and `datasets/` folders. The `models/` folder is empty in the shipped product."),
    ("flow", "High-level workflow", "02_high_level_workflow.png",
     "High-level workflow: the diagnosis path used on every scan, and the offline learning path used to measure accuracy.",
     "The upper row is what happens when a farmer scans a leaf: the photograph and crop are uploaded, the service checks the sign-in, the file extension, size and emptiness, the engine decodes and "
     "resizes the image to 256 pixels and measures colour and texture shares, the candidate classes of the chosen crop are selected, the classes are scored and ranked, the top three are returned with a "
     "confidence, the knowledge card of the top class supplies symptoms and three treatments, and the scan is stored and shown. The lower row is the offline path that produced the accuracy figures "
     "in this report: PlantDoc folders are resized to 224 pixels, a stratified 10 % validation split is taken, models are trained with three seeds and evaluated on the 236 test photographs. "
     "The trained network is not copied into the application."),
    ("dfd0", "DFD level 0 (context diagram)", "03_dfd_level0.png",
     "Context diagram (DFD level 0) of AgriVision.",
     "The whole system is one process, 0 AgriVision. The farmer sends sign-up and sign-in details and a leaf photograph with a crop choice, and receives the diagnosis with the top three predictions, severity, "
     "treatments and prevention advice, and the history, analytics and exported CSV or PDF reports. The model owner and the PlantDoc dataset are drawn as external entities because they work outside the "
     "web application: the dataset supplies labelled leaf photographs to the training and measurement scripts, and the model owner may return trained weights that `inference.py` would load if they were "
     "placed in `agrivision/models/`."),
    ("dfd1", "DFD level 1", "04_dfd_level1.png",
     "DFD level 1: six processes and four data stores.",
     "Level 1 splits the system into six processes: 1.0 Authenticate and register (reads and writes D1 users and returns a token), 2.0 Manage profile (language, region, crops), 3.0 Diagnose leaf photo "
     "(writes the image file to D3 uploads and a scan row to D2 results, reads a card from D4), 4.0 Browse the disease guide (reads D4), 5.0 History, delete and export (reads and deletes D2 rows and D3 "
     "files, produces CSV and PDF), and 6.0 Dashboard and analytics (counts and groups D2 rows). D4, the knowledge base of 38 cards, is Python data in `disease_db.py` and not a database table. Every "
     "process except 4.0 requires the bearer token; process 4.0 and the card lookup are public."),
    ("dfd2", "DFD level 2 (process 3.0)", "05_dfd_level2.png",
     "DFD level 2: process 3.0 'Diagnose leaf photo' decomposed into seven sub-processes.",
     "Process 3.0 is decomposed into 3.1 Validate upload (extension, 10 MB limit, empty file), 3.2 Decode and resize to 256 x 256 RGB, 3.3 Colour and texture features (green, brown, yellow, dark and white "
     "pixel shares and the global standard deviation), 3.4 Select candidate classes by crop, 3.5 Score and rank the classes, 3.6 Calibrate the top-three confidence, and 3.7 Attach the knowledge card and "
     "save the scan. Errors leave from 3.1 (HTTP 400 or 413) and from 3.4, where a crop with fewer than three candidate classes raises an exception that the API reports as HTTP 400 (defect D1). Process 3.5 "
     "and 3.6 are replaced by a single network forward pass when a trained model file is installed."),
    ("uml", "UML class diagram", "06_uml_class_diagram.png",
     "UML class diagram: modules of the application and the two table-backed entities.",
     "The product is written with functions and modules rather than classes, so the diagram shows modules with the stereotype module and the two persistent entities User and Result with the stereotype entity. "
     "`backend.main` imports `inference` (the engine, with the optional model, its labels and the PlantDoc label map) and `disease_db` (the 38 class labels, 26 curated overrides and five generic treatment "
     "kinds). `app` and `config` hold the limits and `init_db()`, which creates the tables and the demo user. `train` is an offline script that writes the weights `inference.try_load_model()` would load. "
     "One User has many Results through `user_id`; the code reads and writes them with `sqlite3` directly, without an object-relational mapper."),
    ("seq", "Sequence diagram of the main flow", "07_sequence_diagram.png",
     "Sequence diagram: uploading a leaf photograph and opening the result.",
     "The sequence follows one diagnosis. The farmer chooses a photograph and crop in the Detect page; the SPA posts the multipart form to `/api/v1/detect/upload` with the bearer token. The service verifies "
     "the HMAC signature and expiry, reads the user row, checks the extension, size and emptiness, and calls `predict()`. The engine returns the top three classes, the confidence and the latency; the service "
     "asks `disease_db` for the card of the top class, writes the image under a random name, inserts the result row and answers with the result id, the top three, the severity and the treatments. The SPA then "
     "requests `/api/v1/history/{id}`, the service checks that the scan belongs to the user, and the Result page is drawn. The bottom box lists the alternative outcomes: 400, 413 and 401."),
    ("uc", "Use case diagram", "08_use_case_diagram.png",
     "Use case diagram: visitor, registered farmer and the offline model owner.",
     "A visitor can browse the public disease guide, register or sign in and change the theme or interface language. A registered farmer can additionally upload a leaf photograph and choose a crop, view the "
     "diagnosis with top three, severity and treatments, search and filter the scan history, export one scan as CSV or PDF, delete a scan, open the dashboard and analytics, and edit the profile (language and "
     "crops). Export and delete are limited to the owner of the scan: any other user receives 404. The model owner is drawn with a dashed outline because the actor works outside the web application, running "
     "`train.py` and `run_experiments.py` and, if wished, installing trained weights."),
    ("er", "Entity-relationship diagram", "09_er_diagram.png",
     "Entity-relationship diagram of the SQLite database (tables users and results).",
     "The database has two tables created by `init_db()`. `users` holds the account (id, unique email, phone, name, password hash, role, region, language, a JSON text list of crops, creation time and an active "
     "flag). `results` holds one row per scan (id, `user_id`, image path and size, the predicted class label, confidence, a JSON text copy of the top three, severity, the crop hint, latency and time, and a "
     "bookmark flag). The relation is one user to many results. The disease knowledge base and the image files are drawn as dashed boxes because they are not tables: `results.predicted` stores one of "
     "the 38 class labels and `results.image_path` points to a file in `static/uploads`."),
    ("algo", "Flowchart of the core algorithm", "10_core_algorithm_flowchart.png",
     "Flowchart of `predict()` in `agrivision/inference.py` (the shipped heuristic engine).",
     "The flowchart follows `predict()`. If a Keras or ONNX model file is present the image is resized to the model input, scaled to [0, 1], passed through the network and the three largest outputs are "
     "mapped to the 38 classes. Otherwise, as shipped, the image is converted to RGB and resized to 256 x 256, six features are measured, the candidate classes of the chosen crop are selected, and a hand-written "
     "score is computed for each candidate. The three highest scores are kept, the first confidence is the clamped value 0.62 + 0.22 min(1.6, s), and the other two are fractions of it taken from the image hash. "
     "If fewer than three candidates exist the ranking raises an IndexError, which the API reports as HTTP 400 UNREADABLE_IMAGE."),
    ("protocol", "Experiment protocol", "11_experiment_protocol.png",
     "Offline experiment protocol used for every accuracy figure in this report.",
     "Every accuracy in this report comes from `scripts/run_experiments.py`. The PlantDoc train folder (2,342 photographs, 28 classes) and test folder (236 photographs, 27 classes) are resized to 224 x 224 "
     "and cached. A stratified 10 % validation split is taken from the train folder for each seed and used only for early stopping; the compact CNN and MobileNetV2 are trained with seeds 42, 43 and 44. The test "
     "photographs are never used to fit or select a model. The shipped heuristic engine is evaluated on the same test photographs with five hash seeds. The shipped `train.py` instead validates on the test "
     "folder, which this protocol avoids."),
    ("deploy", "Deployment view", "12_deployment.png",
     "Local deployment of AgriVision started by `run.bat`.",
     "`run.bat` creates a Python virtual environment, installs the backend requirements and the frontend packages, and starts two processes on one PC: uvicorn serving the FastAPI application on port 8416 "
     "with `PYTHONHASHSEED=0` (so the heuristic's hash jitter is the same in every run) and the Vite server on port 5416 that proxies `/api` to it. The browser opens `http://localhost:5416`. The SQLite "
     "file and the upload folder are local to the machine. The original Flask application can be started on port 5000 and shares the same database and uploads. Nothing in this setup is "
     "suitable for several simultaneous users without a production web server and a different database."),
]
D = {k: (t, f, c, x) for k, t, f, c, x in DIAGRAMS}


def dg(key, width=5.6):
    t, f, c, x = D[key]
    return FIG(F.diag(f), c, width)


def screen(name, caption, base=5.2, max_h=3.3):
    p = F.shot(name)
    return FIG(p, caption, F.shot_w(p, base, max_h))


def blocks():
    return [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        H2("5.1 Design goals and constraints"),
        P("AgriVision has to let a farmer with a phone or a laptop send one leaf photograph and read, in a few seconds, what the system thinks the disease is, how urgent it is and what to do about it. "
          "The design therefore starts from five goals taken from the objectives (Chapter 1): a single deployable stack that runs on one ordinary PC; a diagnosis step that can be replaced when a better model "
          "is available without touching the rest of the application; advice that comes from a curated knowledge base rather than from the model; an interface that is usable in English, Hindi and "
          "Marathi on a phone-sized screen; and honest reporting, so that the application states which engine produced a result."),
        B("**One stack, one command.** Python 3.10 or newer and Node.js 20 or newer; `run.bat` creates the environment and starts both servers. No GPU, no cloud service and no paid API are needed.",
          "**Replaceable engine.** `inference.predict()` is the only function that looks at pixels. It returns the same dictionary whether the answer comes from the heuristic or from a Keras or ONNX network.",
          "**Reuse, not rewrite.** The original Flask product (`agrivision/`) already held the knowledge base, the detection function and the tables. The FastAPI layer imports these modules unchanged and adds only a JSON login, serialisers and a few reports, so a scan made through either interface appears in the other.",
          "**Privacy by ownership.** Every scan belongs to one user; reading, exporting or deleting it requires that user's token and returns 404 to anybody else.",
          "**Visible limits.** The sidebar, the landing page and every result show the engine name and a note that the score is not a calibrated probability."),
        H2("5.2 System architecture"),
        dg("arch", 4.9),
        P(D["arch"][3]),
        TAB("Tiers and their modules", ["Tier", "Module", "Responsibility", "Size"],
            [["Presentation", "`frontend/src` (React 18, Vite 8, TypeScript 5.9, Tailwind 4)", "12 page components, axios client, TanStack Query hooks, theme and language providers, UI kit", f"{F.LOC['frontend']:,} lines"],
             ["Application", "`backend/main.py` (FastAPI)", "16 routes, HMAC bearer token, serialisers, CSV and PDF export, error format", f"{F.LOC['backend']} lines"],
             ["Domain", "`agrivision/inference.py`", "Diagnosis engine: heuristic or Keras/ONNX model, crop candidates, label map", "177 lines"],
             ["Domain", "`agrivision/disease_db.py`", "38 class labels, 26 curated cards, generic treatments by disease kind", "221 lines"],
             ["Domain", "`agrivision/app.py`, `config.py`", "Table creation, demo user, limits (10 MB; jpg, jpeg, png, webp); original Flask pages", "404 lines"],
             ["Data", "`agrivision.db`, `static/uploads/`", "Tables `users` and `results`; uploaded images under random names", "-"],
             ["Offline", "`agrivision/train.py`, `scripts/run_experiments.py`", "CNN training script of the original product; seeded measurements", "103 + 430 lines"]],
            widths=[1.0, 2.1, 2.7, 0.9], align=["l", "l", "l", "l"], size=9),
        H2("5.3 High-level workflow"),
        dg("flow", 5.0),
        P(D["flow"][3]),
        P("The diagnosis path contains no learning in the shipped product: the engine is a fixed formula, which is why its accuracy is measured separately in Chapter 8. The offline path is the only "
          "place where data are used to fit anything, and its protocol is kept away from the test photographs on purpose."),
        H2("5.4 Data flow diagrams"),
        H3("5.4.1 Level 0: context"),
        dg("dfd0", 4.6),
        P(D["dfd0"][3]),
        H3("5.4.2 Level 1: processes and stores"),
        dg("dfd1", 4.4),
        P(D["dfd1"][3]),
        TAB("DFD level 1 processes and the routes that implement them", ["Process", "Name", "Routes (backend/main.py)", "Stores touched"],
            [["1.0", "Authenticate and register", "POST /auth/register, POST /auth/login, GET /auth/me", "D1 read and write"],
             ["2.0", "Manage profile", "PUT /profile", "D1 read and write"],
             ["3.0", "Diagnose leaf photo", "POST /detect/upload", "D2 write, D3 write, D4 read"],
             ["4.0", "Browse the disease guide", "GET /diseases, GET /diseases/{name}", "D4 read"],
             ["5.0", "History, delete and export", "GET /history, GET /history/{id}, DELETE /history/{id}, GET /history/export, GET /history/{id}/export", "D2 read and delete, D3 delete, D4 read"],
             ["6.0", "Dashboard and analytics", "GET /dashboard, GET /analytics/dashboard", "D2 read, D4 read"]],
            widths=[0.7, 1.7, 3.0, 1.3], align=["c", "l", "l", "l"], size=9),
        H3("5.4.3 Level 2: process 3.0"),
        dg("dfd2", 4.6),
        P(D["dfd2"][3]),
        H2("5.5 UML diagrams"),
        H3("5.5.1 Class (module) diagram"),
        dg("uml", 4.4),
        P(D["uml"][3]),
        H3("5.5.2 Sequence diagram"),
        dg("seq", 4.1),
        P(D["seq"][3]),
        H3("5.5.3 Use case diagram"),
        dg("uc", 4.2),
        P(D["uc"][3]),
        TAB("Use cases and the screens that realise them", ["Use case", "Actor", "Screen", "Route"],
            [["Browse the disease guide", "Visitor, farmer", "Disease guide, Disease detail", "GET /diseases"],
             ["Register or sign in", "Visitor", "Register, Login", "POST /auth/register, /auth/login"],
             ["Upload a leaf photo and choose the crop", "Farmer", "Detect", "POST /detect/upload"],
             ["View diagnosis, top three, treatments", "Farmer", "Result", "GET /history/{id}"],
             ["Search and filter history", "Farmer", "History", "GET /history?q=&crop=&disease="],
             ["Export one scan (CSV, PDF) or all (CSV)", "Farmer", "Result, History", "GET /history/{id}/export, /history/export"],
             ["Delete a scan", "Farmer", "History, Result", "DELETE /history/{id}"],
             ["Dashboard and analytics", "Farmer", "Dashboard, Analytics", "GET /dashboard, /analytics/dashboard"],
             ["Edit profile (language, crops)", "Farmer", "Profile", "PUT /profile"],
             ["Train and measure models", "Model owner", "(command line)", "train.py, run_experiments.py"]],
            widths=[2.4, 1.0, 1.5, 1.8], align=["l", "l", "l", "l"], size=9),
        H2("5.6 Database design"),
        dg("er", 4.8),
        P(D["er"][3]),
        TAB("Table users", ["Column", "Type", "Constraint or default", "Meaning"],
            [["id", "TEXT", "PRIMARY KEY (UUID)", "Account identifier, also the `uid` inside the token"],
             ["email", "TEXT", "UNIQUE NOT NULL", "Login name; stored lower-case"],
             ["phone, full_name", "TEXT", "-", "Optional contact and display name"],
             ["password_hash", "TEXT", "NOT NULL", "Salted hash made by `werkzeug.security.generate_password_hash`"],
             ["role", "TEXT", "'farmer'", "Only the value farmer is used"],
             ["region, language", "TEXT", "'' and 'en'", "Language is en, hi or mr"],
             ["crops", "TEXT", "'[]'", "JSON list of monitored crops; tomato is stored when none is chosen"],
             ["created_at", "TEXT", "-", "ISO time (UTC)"],
             ["is_active", "INTEGER", "1", "Sign-in and token checks require 1"]],
            widths=[1.3, 0.8, 1.6, 3.2], align=["l", "l", "l", "l"], size=9),
        TAB("Table results", ["Column", "Type", "Constraint or default", "Meaning"],
            [["id", "TEXT", "PRIMARY KEY (UUID)", "Scan identifier used in /result/{id}"],
             ["user_id", "TEXT", "NOT NULL, FOREIGN KEY users(id)", "Owner of the scan"],
             ["image_path, image_size", "TEXT, INTEGER", "-", "`static/uploads/<uuid>.<ext>` and size in bytes"],
             ["predicted", "TEXT", "-", "One of the 38 canonical class labels"],
             ["confidence", "REAL", "-", "Score of the top class (not a calibrated probability for the heuristic)"],
             ["top3", "TEXT", "-", "JSON list of [class, score] pairs"],
             ["severity", "TEXT", "-", "high, medium or none (copied from the card)"],
             ["crop_hint, latency_ms", "TEXT, INTEGER", "-", "Crop chosen by the user; engine time reported by `predict()`"],
             ["created_at, bookmarked", "TEXT, INTEGER", "0", "ISO time; bookmark flag (not used by the React screens)"]],
            widths=[1.5, 1.0, 1.7, 2.7], align=["l", "l", "l", "l"], size=9),
        P("Design notes. The foreign key is declared but SQLite enforces it only when `PRAGMA foreign_keys=ON` is set per connection, which neither `app.py` nor `backend/main.py` does; the ownership rule is "
          "enforced in the queries (`WHERE id=? AND user_id=?`). The `INSERT INTO results VALUES(...)` statement is positional, so a column added to the table would break both front ends; this is why the "
          "database was left untouched during the rebuild. Arrays are stored as JSON text because the lists are short and always read together with their row."),
        H2("5.7 Module design"),
        H3("5.7.1 Backend modules"),
        TAB("Backend functions and their roles", ["Function (backend/main.py)", "Role"],
            [["`make_token`, `read_token`, `current_user`", "Create and check the HMAC-SHA256 bearer token (7 days); load the active user or answer 401"],
             ["`get_db`, `init_db` (from app.py)", "One SQLite connection per request with `row_factory = Row`; create tables and the demo user at start-up"],
             ["`register`, `login`, `me`, `update_profile`", "Create account (validates e-mail and 6-character password), check password hash, return profile, save language and crops"],
             ["`detect`", "Validate the file, call `predict`, look up the card, store the image and the row, return the result summary"],
             ["`history`, `history_one`, `history_delete`", "List with search, crop and healthy/diseased filters and paging; one scan with top three and card; delete row and file"],
             ["`export_one`, `export_all`, `pdf_bytes`", "CSV for one scan or for all scans; one-scan PDF drawn with reportlab"],
             ["`dashboard`, `analytics`", "Totals, healthy and urgent counts, disease rate, six recent scans; distribution by disease, severity split and scans per day"],
             ["`diseases`, `disease_one`, `upload_file`, `health`", "Public: knowledge cards, stored images (random file name is the capability), engine and database status"]],
            widths=[2.4, 4.3], align=["l", "l"], size=9),
        H3("5.7.2 Domain modules"),
        P("`inference.py` exposes `predict(img_bytes, crop_hint)` and the helpers `_features`, `_candidates`, `_heuristic_predict` and `try_load_model`. At import time `try_load_model()` looks for "
          "`models/pd36c.h5`, `plantdoc_cnn.h5`, `pd36c.keras`, `pd36c.onnx` or `pd36c.pt` next to the module; a Keras or ONNX file is loaded, otherwise the heuristic is used. `PLANTDOC_MAP` translates the 28 "
          "PlantDoc folder names written by `train.py` into the 38 canonical labels so that history, severity and treatments keep working with a trained model. `disease_db.py` builds a card from "
          "`_OVERRIDES` (26 curated diseases) and `_GENERIC_TREATMENTS` (five kinds: healthy, fungal, bacterial, viral, pest), so every class returns symptoms, lifecycle, severity, three treatments with "
          "cost text, prevention and an urgent flag."),
        H3("5.7.3 Frontend modules"),
        TAB("Frontend structure (frontend/src)", ["Folder or file", "Content"],
            [["`pages/` (12 files)", "Landing, Login, Register, Dashboard, Detect, Result, History, Analytics, Profile, Encyclopedia, DiseaseDetail, NotFound"],
             ["`lib/api.ts`, `queries.ts`, `auth.tsx`", "axios instance with token interceptor and 401 handling; query hooks (health, diseases, dashboard, analytics, history, result); sign-in context"],
             ["`lib/i18n.tsx`, `theme.tsx`", "44 interface keys in English, Hindi and Marathi with stored choice; light and dark theme"],
             ["`components/ui/`", "AppShell with sidebar and bottom navigation, Button, Card, Field, FileDrop, Select, Table, Toast, Overlay and further kit parts"],
             ["`components/charts`, `agri`, `landing`, `motion`", "Recharts wrapper, disease badges, landing sections, entrance animations"]],
            widths=[2.2, 4.5], align=["l", "l"], size=9),
        H2("5.8 API design"),
        P("All routes live under `/api` and return JSON. Protected routes need the header `Authorization: Bearer <token>`. Errors share one shape, `{error, message, detail}`, so the React client can show "
          "`message` directly; validation errors raised by FastAPI itself (for example `limit=0`) answer 422."),
        TAB("API summary", ["Method", "Path", "Auth", "Purpose"],
            [["GET", "/api/health", "no", "Status, class count, engine name, trained_model flag"],
             ["GET", "/api/v1/diseases, /diseases/{name}", "no", "38 cards; one card by class or display name"],
             ["GET", "/api/v1/uploads/{name}", "no", "Stored leaf image"],
             ["POST", "/api/v1/auth/register, /auth/login", "no", "Create account; sign in. Both return a token"],
             ["GET", "/api/v1/auth/me", "yes", "Profile of the token's user"],
             ["PUT", "/api/v1/profile", "yes", "Name, region, language (en, hi, mr), crops"],
             ["GET", "/api/v1/dashboard, /analytics/dashboard", "yes", "Counts and six recent scans; distribution, severity, timeline"],
             ["POST", "/api/v1/detect/upload", "yes", "Multipart image and crop_type; returns top three, severity, treatments"],
             ["GET", "/api/v1/history, /history/{id}", "yes", "Paged list with filters; one scan with card"],
             ["DELETE", "/api/v1/history/{id}", "yes", "Delete row and image"],
             ["GET", "/api/v1/history/export, /history/{id}/export?format=csv|pdf", "yes", "Downloads"]],
            widths=[0.8, 2.6, 0.6, 2.7], align=["c", "l", "c", "l"], size=9),
        TAB("Error codes returned by the API", ["HTTP", "error", "When"],
            [["400", "NO_IMAGE, INVALID_IMAGE_FORMAT, UNREADABLE_IMAGE, INVALID_REQUEST", "No or empty file; extension not jpg, jpeg, png or webp; engine raised an exception (including defect D1); bad e-mail, short password, unsupported language"],
             ["401", "AUTHENTICATION_REQUIRED, INVALID_CREDENTIALS", "Missing, forged, expired or unknown token; wrong password"],
             ["404", "NOT_FOUND", "Unknown disease, or a scan that does not exist or belongs to another user"],
             ["409", "EMAIL_EXISTS", "E-mail already registered"],
             ["413", "IMAGE_TOO_LARGE", "File larger than 10 MB"],
             ["422", "(FastAPI validation)", "Paging parameters out of range"]],
            widths=[0.6, 2.7, 3.4], align=["c", "l", "l"], size=9),
        H2("5.9 Core algorithm design"),
        dg("algo", 4.0),
        P(D["algo"][3]),
        P("The design deliberately keeps the engine behind one function. The formulas in the flowchart are written out in Section 6.6; the measured behaviour is in Chapter 8, and the consequences of the "
          "fewer-than-three-candidates branch are discussed under defect D1 in Chapter 7."),
        H2("5.10 Deployment design"),
        dg("deploy", 4.8),
        P(D["deploy"][3]),
        H2("5.11 User interface design"),
        P("The interface follows the Aurora Glass design kit: translucent cards on a dark or light gradient background, an emerald, teal and lime accent palette (remapped from the kit's violet) and "
          "a sidebar that collapses to a bottom navigation bar on phone-sized screens. Every screen has the same shell: sidebar, a breadcrumb bar with the API status, language menu, theme toggle and "
          "user menu. The design rules were: one primary action per screen, large touch targets, plain words, the engine note always visible, and no information carried by colour alone (severity badges "
          "carry a text label)."),
        TAB("Screen map", ["Screen", "Route", "Purpose", "Needs sign-in"],
            [["Landing", "/", "Product story, live disease-guide teaser, how it works", "no"],
             ["Login, Register", "/login, /register", "Sign in (demo account hint) or create an account with crop and language", "no"],
             ["Dashboard", "/dashboard", "Totals, quick scan buttons, field tips, recent scans", "yes"],
             ["Detect", "/detect", "Choose crop, drop or capture a photo, diagnose", "yes"],
             ["Result", "/result/{id}", "Diagnosis, top three, symptoms, treatments, exports", "yes"],
             ["History", "/history", "Search, crop and healthy/diseased filters, delete, export", "yes"],
             ["Analytics", "/analytics", "Disease distribution, severity split, scans per day", "yes"],
             ["Profile", "/profile", "Name, region, language, monitored crops", "yes"],
             ["Disease guide, Detail", "/encyclopedia, /disease/{class}", "38 searchable cards and a full treatment page", "no"]],
            widths=[1.4, 1.7, 2.9, 0.7], align=["l", "l", "l", "c"], size=9),
        PAIR([(F.shot("01_landing_dark.png"), "Landing page (dark theme)."), (F.shot("07_detect_ready.png"), "Detect screen with a photograph chosen and the crop selected.")], 3.0),
        P("Only the 44 interface keys are translated into Hindi and Marathi, so field tips, treatments and symptom text remain in English (see Chapter 10). Every other screen, including the "
          "Hindi and phone-width captures, is shown in Chapter 8 and Appendix C."),
    ]
