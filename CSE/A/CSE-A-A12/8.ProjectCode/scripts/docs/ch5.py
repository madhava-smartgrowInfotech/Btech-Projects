"""Chapter 5: System design. The diagram explanations are shared with '11. BLOCK DIAGRAMS ALL.docx'."""

from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import n
from . import facts as F

# (key, section title, file, caption, explanation)
DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png", "System architecture of the pneumonia detection system",
     "The system has four tiers. In the presentation tier the React single-page application (served by the Vite development server on port 5312) and the "
     "original Flask interface (port 5000) are the two ways a user reaches the system. The application tier is the FastAPI service in `backend/main.py` "
     "(port 8312), which authenticates the session cookie, validates uploads and exposes the REST and file routes; it imports `app.py` for the model loader and "
     "folder settings, so the model is loaded once and shared. The inference tier is the three modules that do the actual work: `preprocess.py` turns an upload "
     "into a 224 x 224 tensor, `model_builder.py` defines the CNN and `gradcam.py` produces the heat map. The data tier holds the SQLite database "
     "(`pneumonia_app.db`, table `predictions`), the saved original and overlay images, and the trained weights. When `saved_models/` holds no weights the "
     "loader builds an untrained network and flags Demo Mode."),
    ("flow", "High-level workflow", "02_high_level_workflow.png", "High-level workflow of one scan, from sign-in to review",
     "A scan passes through eight steps. The user signs in, uploads a PNG or JPEG of at most 8 MB, and the server validates the name, type, size and "
     "that the file can be decoded. The image is preprocessed (224 x 224, CLAHE, light blur, scaling to [0, 1]) and classified by the CNN, whose softmax output "
     "gives the three class probabilities. Grad-CAM then explains the predicted class, and the record plus the two image files are stored. Finally the user "
     "reviews the result, the history and the dashboard. A failure at the validation or decoding step ends the flow with a JSON error and stores nothing."),
    ("dfd0", "Data flow diagram, level 0", "03_dfd_level0.png", "Data flow diagram, level 0 (context diagram)",
     "The context diagram shows the system as a single process with one external entity, the user. The user sends credentials, X-ray images and history or delete "
     "requests; the system returns the classification result with its heat map, the history and the statistics. Internally the system reads and writes three "
     "data stores: the predictions table (D1), the uploaded and heat-map image files (D2) and the trained model weights (D3), which are only read."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png", "Data flow diagram, level 1",
     "Level 1 splits the system into five processes. Authenticate (1.0) checks the credentials and sets a signed cookie (D0). Validate upload (2.0) accepts the "
     "image only if the cookie is valid, the extension is allowed, the size is within 8 MB and the file decodes. Preprocess, classify and explain (3.0) reads the "
     "model weights (D3) and returns the label, probabilities and overlay. Store result (4.0) writes one row to the predictions table (D1) and the two images to "
     "the file store (D2). Manage history (5.0) serves the list, the statistics and deletions, and removes the image files when a scan is deleted."),
    ("dfd2", "Data flow diagram, level 2", "05_dfd_level2.png", "Data flow diagram, level 2: process 3.0 expanded",
     "Level 2 expands the inference process into its nine steps, in the order the code executes them. The upload is decoded to grayscale (3.1), resized to "
     "224 x 224 (3.2), enhanced with CLAHE (clip limit 2.5, 8 x 8 tiles; 3.3), smoothed with a 3 x 3 Gaussian (3.4) and converted to three channels scaled to "
     "[0, 1] (3.5). The network produces three probabilities (3.6); the arg-max and its probability become the label and confidence (3.7). The class index "
     "drives Grad-CAM on the last convolutional layer (3.8), whose 14 x 14 map is blended at alpha 0.4 over the display image (3.9). The result record carries "
     "the label, confidence, probabilities and the overlay image."),
    ("uml", "UML class diagram", "06_uml_class_diagram.png", "UML class diagram (modules drawn as classes)",
     "The code base is function-oriented, so the diagram draws each Python module as a class stereotyped as a module, listing its constants and public "
     "functions. `ApiService` (`backend/main.py`) uses `FlaskApp` (`app.py`) for the model loader and imports `Preprocess`; `FlaskApp` builds or loads the "
     "network through `ModelBuilder`, which creates Keras models, and `GradCAM` receives the name of the last convolutional layer from `ModelBuilder`. "
     "`Database` persists `Prediction` rows. `Login` is the only real class in the API layer (a Pydantic model that validates the sign-in body)."),
    ("seq", "Sequence diagram", "07_sequence_diagram.png", "Sequence diagram: analysing one X-ray",
     "The sequence follows one analysis. The React page checks the file type and size, then posts it as multipart data with the session cookie. The API verifies "
     "the cookie and validates the upload, calls the preprocessing function, and, under a lock that allows one TensorFlow inference at a time, runs the "
     "network and Grad-CAM. It writes the overlay image and the database row and returns HTTP 201 with the full record. The page then navigates to the result "
     "route, which fetches the record and the two images and renders the badge, confidence, bars and side-by-side view."),
    ("uc", "Use-case diagram", "08_use_case_diagram.png", "Use-case diagram",
     "The user can sign in, upload an X-ray, view the class, confidence and probabilities, inspect the Grad-CAM overlay (side by side or blended), browse and "
     "filter the history, export it as CSV, view dashboard statistics, print the report or download the heat map, and delete a scan. Every case except signing in "
     "requires a valid session. The developer is a second actor who trains and exports a model with the scripts, outside the web interface."),
    ("er", "Entity-relationship diagram", "09_er_diagram.png", "Entity-relationship diagram of the stored data",
     "All persistent data are in one table, `predictions`, with ten columns. Each row owns exactly one original image in `static/uploads/` and one overlay "
     "in `static/heatmaps/`, referenced by relative path, so the relationship between a row and its files is one to one to one. The demo user and the class label set "
     "are logical entities: the user is configured through the environment and carried only in a signed cookie, and the label set is the fixed list of three "
     "class names."),
    ("flowchart", "Flowchart of the core algorithm", "10_core_algorithm_flowchart.png", "Flowchart of the core algorithm (POST /api/predict)",
     "The flowchart gives the decisions of the prediction route in order: valid session (401 otherwise), a named file with an allowed extension (400), size "
     "within 8 MB (413), save under a random 12-character name, decodable image (400, and the saved file is deleted). It then preprocesses, predicts, takes the "
     "arg-max, runs Grad-CAM, writes the overlay, inserts the row and returns 201 with the record. The order matches `backend/main.py` and the Flask route."),
]

SCHEMA = [
    ["id", "INTEGER", "Primary key, auto-increment", "Scan number shown in the interface"],
    ["filename", "TEXT", "NOT NULL", "Original file name as uploaded"],
    ["original_path", "TEXT", "NOT NULL", "Relative path of the saved original, e.g. uploads/ab12cd34ef56.jpg"],
    ["heatmap_path", "TEXT", "NOT NULL", "Relative path of the Grad-CAM overlay, e.g. heatmaps/ab12cd34ef56_heatmap.png"],
    ["prediction", "TEXT", "NOT NULL", "Predicted class name"],
    ["confidence", "REAL", "NOT NULL", "Probability of the predicted class, 0 to 1"],
    ["prob_normal", "REAL", "", "Softmax probability of Normal"],
    ["prob_bacterial", "REAL", "", "Softmax probability of Bacterial Pneumonia"],
    ["prob_viral", "REAL", "", "Softmax probability of Viral Pneumonia"],
    ["created_at", "TEXT", "NOT NULL", "UTC timestamp in ISO-8601 form"],
]

MODULES = [
    ["`model/preprocess.py`", "Image preparation", "`load_and_preprocess_image`, `apply_clahe`, `preprocess_for_display`, augmentors"],
    ["`model/model_builder.py`", "Network definition", "`build_custom_cnn`, `build_transfer_model`, `find_last_conv_layer`, `CLASS_NAMES`"],
    ["`model/gradcam.py`", "Explanation", "`make_gradcam_heatmap`, `overlay_heatmap`"],
    ["`model/train.py`", "Original training script (unchanged)", "Keras generators, checkpoint, report"],
    ["`scripts/train_experiment.py`", "Reproducible experiment runner", "patient-level split, class weights, metrics.json, figures"],
    ["`database/db.py`", "Persistence", "`init_db`, `insert_prediction`, `get_prediction`, `get_all_predictions`"],
    ["`app.py`", "Original Flask app and model loader", "`get_model`, `allowed_file`, routes `/`, `/predict`, `/result/<id>`, `/history`, `/about`"],
    ["`backend/main.py`", "FastAPI layer", "auth routes, `/api/predict`, `/api/predictions`, `/api/stats`, `/api/files`, `/api/health`"],
    ["`frontend/src/pages/*`", "React screens", "Landing, Login, Dashboard, Detect, Result, History, About, NotFound"],
    ["`frontend/src/lib/*`", "Client logic", "`api.js` (fetch and upload progress), `auth.jsx`, `theme.jsx`, `format.js`, `hooks.js`"],
    ["`tests/`, `scripts/*.py`", "Verification", "73 pytest tests, smoke test, UI verification, screenshot capture"],
]

ENDPOINTS = [
    ["GET", "/api/health", "No", "Status, model readiness, Demo Mode flag, class names, upload limits"],
    ["POST", "/api/auth/login", "No", "Demo sign-in; sets the signed HttpOnly cookie"],
    ["POST", "/api/auth/logout", "No", "Clears the cookie"],
    ["GET", "/api/auth/me", "No", "Signed-in user, or `null` when signed out"],
    ["POST", "/api/predict", "Yes", "Multipart `xray_image`; returns the stored record (201)"],
    ["GET", "/api/predictions?limit=", "Yes", "History, newest first (limit clamped to 1-1000)"],
    ["GET", "/api/predictions/{id}", "Yes", "One record; 404 JSON if missing"],
    ["DELETE", "/api/predictions/{id}", "Yes", "Removes the row and both image files"],
    ["GET", "/api/stats", "Yes", "Totals, per-class counts, average confidence, 7-day series"],
    ["GET", "/api/files/{uploads|heatmaps}/{name}", "Yes", "Stored images; basename check blocks traversal"],
]

SCREENS = [
    ["Landing `/`", "Public introduction: hero, how it works, the three classes, key figures, disclaimer, call to action"],
    ["Sign in `/login`", "Demo credentials with a one-click fill button and a show-password option"],
    ["Dashboard `/app`", "Stat cards, class-distribution and scans-per-day charts, recent scans"],
    ["Detect `/app/detect`", "File drop area, preview, analyse button with progress, validation messages, Demo Mode alert"],
    ["Result `/app/result/:id`", "Side-by-side and blended views, class badge, probability bars, scan details, print, download, delete"],
    ["History `/app/history`", "Search, class filter, sortable paginated table with thumbnails, CSV export, empty state"],
    ["About `/app/about`", "Abstract, five-step pipeline, technology, disclaimer"],
    ["Not found `*`", "Friendly 404 with a way back"],
]


def diagram_blocks(heading_level=3):
    out = []
    for i, (key, title, file, caption, text) in enumerate(DIAGRAMS, 1):
        out.append(("h3" if heading_level == 3 else "h2", f"{title}"))
        out.append(FIG(F.diag(file), caption, 6.0))
        out.append(P(text))
    return out


def schema_blocks():
    return [
        TAB("Table `predictions`", ["Column", "Type", "Constraint", "Meaning"], SCHEMA, widths=[1.2, 0.8, 1.6, 2.7], size=9.5),
        P("The table is created by `init_db()` with `CREATE TABLE IF NOT EXISTS`, so a fresh checkout needs no migration. All statements use bound parameters "
          "(`?`), never string formatting, which removes SQL injection through file names or ids."),
    ]


def blocks():
    return [
        H1("CHAPTER 5: SYSTEM DESIGN"),
        H2("5.1 Architecture"),
        P("The design follows two rules: do not rewrite what already works, and keep each layer replaceable. The model, Grad-CAM and database modules of the "
          "original Flask project are reused as they are; the FastAPI layer and the React interface sit on top of them."),
        FIG(F.diag("01_system_architecture.png"), "System architecture of the pneumonia detection system", 6.0),
        P(DIAGRAMS[0][4]),
        H2("5.2 High-level workflow"),
        FIG(F.diag("02_high_level_workflow.png"), "High-level workflow of one scan, from sign-in to review", 6.0),
        P(DIAGRAMS[1][4]),
        H2("5.3 Data flow diagrams"),
        H3("Level 0"),
        FIG(F.diag("03_dfd_level0.png"), "Data flow diagram, level 0 (context diagram)", 5.6),
        P(DIAGRAMS[2][4]),
        H3("Level 1"),
        FIG(F.diag("04_dfd_level1.png"), "Data flow diagram, level 1", 5.8),
        P(DIAGRAMS[3][4]),
        H3("Level 2"),
        FIG(F.diag("05_dfd_level2.png"), "Data flow diagram, level 2: process 3.0 expanded", 5.8),
        P(DIAGRAMS[4][4]),
        H2("5.4 UML diagrams"),
        H3("Class diagram"),
        FIG(F.diag("06_uml_class_diagram.png"), "UML class diagram (modules drawn as classes)", 6.0),
        P(DIAGRAMS[5][4]),
        H3("Sequence diagram"),
        FIG(F.diag("07_sequence_diagram.png"), "Sequence diagram: analysing one X-ray", 5.8),
        P(DIAGRAMS[6][4]),
        H3("Use-case diagram"),
        FIG(F.diag("08_use_case_diagram.png"), "Use-case diagram", 5.4),
        P(DIAGRAMS[7][4]),
        H3("Core algorithm flowchart"),
        FIG(F.diag("10_core_algorithm_flowchart.png"), "Flowchart of the core algorithm (POST /api/predict)", 4.6),
        P(DIAGRAMS[9][4]),
        H2("5.5 Database design"),
        FIG(F.diag("09_er_diagram.png"), "Entity-relationship diagram of the stored data", 5.4),
        P(DIAGRAMS[8][4]),
        *schema_blocks(),
        H2("5.6 Module design"),
        TAB("Modules and responsibilities", ["Module", "Responsibility", "Key functions"], MODULES, widths=[1.9, 1.6, 2.8], size=9.5),
        H2("5.7 API design"),
        P("The API is JSON over HTTP. Errors use the standard FastAPI body `{\"detail\": \"message\"}` with 400 for bad input, 401 for a missing or invalid session, "
          "404 for unknown ids or files and 413 for oversize uploads. The validation order of `/api/predict` matches the original Flask route, so the same "
          "mistake produces the same message in both interfaces."),
        TAB("REST endpoints", ["Method", "Path", "Session", "Purpose"], ENDPOINTS, widths=[0.7, 2.2, 0.7, 2.7], size=9.5, align=["c", "l", "c", "l"]),
        H2("5.8 User interface design"),
        P("The interface uses the Neo Brutal Grid design kit: thick black outlines, hard offset shadows, a visible grid, an uppercase display typeface for headings and a monospace face for numbers. "
          "Colour carries meaning: green for Normal, coral for Bacterial Pneumonia and amber for Viral Pneumonia, and every colour is paired with a label and an icon so the "
          "meaning never depends on colour alone. The application shell has a sidebar that becomes a drawer on small screens, a theme toggle that remembers its setting, "
          "toast messages, skeleton placeholders and a 404 route."),
        TAB("Screens", ["Screen", "Content"], SCREENS, widths=[1.7, 4.6], size=10),
        FIG(F.shot_view("06_result.png"), "The result screen: side-by-side original and Grad-CAM overlay, class badge and probabilities", F.shot_w(F.shot_view("06_result.png"), 6.0)),
        P("Accessibility was designed in rather than added later: visible focus rings, a focus trap in dialogs, the Escape key closing the mobile drawer and the "
          "delete dialog, announced loading states, and a reduced-motion mode that keeps all content visible. Chapter 7 reports the automated checks of these properties."),
    ]
