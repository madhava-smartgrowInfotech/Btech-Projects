"""Chapter 5: System Design for Mosaic.

build_docs.doc12 renders blocks()[1:], so the first element must be the chapter H1.
The diagram explanations in diagram_index.DIAGRAMS also appear in the Block Diagrams document; here they are adapted, not repeated.
"""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .diagram_index import DIAGRAMS
from .refs import CITE as R

_IDX = {d[0]: d for d in DIAGRAMS}


def dg(key, width=5.4, extra=None):
    """Figure for one diagram plus the paragraphs written for this chapter."""
    _, _title, fname, caption, _text = _IDX[key]
    out = [FIG(F.diag(fname), caption, width)]
    for e in extra or []:
        out.append(P(e))
    return out


def sh(name, caption, base=5.4, max_h=3.6):
    p = F.shot(name)
    return FIG(p, caption, F.shot_w(p, base, max_h))


def blocks():
    a, w = F.API_PORT, F.WEB_PORT
    fin = F.FIN
    gp = F.GAN["generator_parameters"]
    out = [
        H1("5. SYSTEM DESIGN"),
        P("This chapter describes how Mosaic is built: the architecture and workflow, the data flow, the class, sequence and use-case design, the data design, the core algorithms, "
          "the module and API design and the user interface. Every diagram was drawn from the code in `backend/app` (`main.py`, `routers/`, `ml/`, `models.py`, `security.py`) and `frontend/src`; the complete set, each with a longer explanation, "
          "is also collected in the Block Diagrams document."),
        P("Three facts about the design are stated at the outset because they shape everything below. Mosaic is a **single Python process** with a browser front end: there is no queue, no worker and no external service, and the network, the face detector and the SQLite file are all used inside the request that needs them. "
          "Its **recognition is multi-label**: the final network has 18 independent sigmoid outputs (seven basic and eleven compound), so one face can carry several positive labels, and the rule that picks the single dominant emotion is just an argmax over those 18. "
          f"And its **compound half is trained on synthetic faces only**, because the real dataset has no compound labels. The design follows the two-stage analysis-by-synthesis scheme of the base paper [{R['base']}] (generate, then recognise) at a much smaller scale and omits its identity-preserving encoder."),

        H2("5.1 Design Goals and Architecture"),
        P("Five goals shaped the design. First, **one model for basic and compound emotions**, so that the service stays a single forward pass. Second, **make the generator's contribution testable**: the final network is initialised from a separately trained 7-class backbone, so that the effect of the synthetic faces can be compared with a no-synthesis control. "
          "Third, **be private by default**: uploaded photographs are never written to disk, only the cropped grayscale face of a signed-in user is kept, and a user can delete it. Fourth, **run on a laptop without special hardware**: everything is CPU-only PyTorch. "
          "Fifth, **keep the API contract small and stable**, so that the front end and back end could be built independently from `API_CONTRACT.md`."),
    ] + dg("arch", 5.4, extra=[
        f"The architecture has four tiers. The browser tier is a Next.js 16 application (React 19, TypeScript) served on port {w}; it keeps the session token in a persisted zustand store named `mosaic-auth` and calls the API with `fetch`. "
        f"The FastAPI application (uvicorn) listens on port {F.API_DEFAULT_PORT} by default (port {a} during this documentation run, because another program held 8000) and mounts the thumbnail folder as static files under `/api/media/thumbs`. "
        "CORS admits only `http://localhost:3000` and `http://127.0.0.1:3000`. The ML tier is a set of plain Python modules: `face.py` (Haar detector), `inference.py` (preprocessing, forward pass, ranking), `classifier_model.py` (the CNN), "
        "`gan_model.py` and the training scripts. State lives in `mosaic.db`, in the three checkpoint files under `checkpoints/`, and in `media/thumbs/`. At start-up `main.py` creates the tables and tries to load `classifier_final.pt`; if the file is absent the server still starts "
        "and `/api/health` reports `model_loaded: false`."]) + [

        H2("5.2 High-Level Workflow"),
    ] + dg("flow", 5.4, extra=[
        "The workflow has two time scales. Training is a command-line program, `python -m app.ml.run_pipeline`, which runs three stages in order and appends one line per stage to `checkpoints/training_log.txt`: the 7-class backbone (five epochs), the conditional GAN (ten epochs on 2,800 faces) "
        "and the final 18-output classifier (five epochs on 28,709 real and 2,200 synthetic faces). Serving is a request-driven path: each upload is decoded, a face is located, the face is classified and the answer is returned and, for a signed-in user, stored. "
        "There is no batching and no queue; the measured median for the whole path is about 19 ms on the development machine."]) + [

        H2("5.3 Data Flow Diagrams"),
        H3("5.3.1 Level 0: context"),
    ] + dg("dfd0", 4.8, extra=[
        "At level 0 the system has four neighbours. The end user supplies photographs and credentials and receives tokens, scores and history; the developer starts the training pipeline; the OpenCV package supplies the Haar cascade file; "
        "the FER2013 pickles supply labelled faces at training time only. A single store, D1, stands for the SQLite database, the checkpoints and the thumbnail folder."]) + [
        H3("5.3.2 Level 1: seven processes"),
    ] + dg("dfd1", 5.4, extra=[
        "Level 1 separates seven processes. Process 1.0 handles registration and login against the users store D1. Processes 2.0 (face detection), 3.0 (classification) and 4.0 (ranking and response) run once per upload. "
        "Process 5.0 stores the analysis row in D2 and the face thumbnail in D3, and 6.0 lists, reads and deletes history rows. Process 7.0, the offline training pipeline, produces the checkpoint files of D4 from the FER2013 pickles; process 3.0 loads them once when the server starts. "
        "Process 5.0 runs for every signed-in call, including calls where no face was found (the row then has empty emotion lists and no thumbnail)."]) + [
        H3("5.3.3 Level 2: classification and ranking"),
    ] + dg("dfd2", 5.4, extra=[
        "Process 3.0 is expanded into resizing the crop to 64 x 64 pixels, scaling intensities to the range minus one to one (x/255, then (x - 0.5)/0.5), the forward pass through the four convolutional blocks and two fully connected layers, and a sigmoid on the 18 logits. "
        "Process 4.0 splits the 18 probabilities into the seven basic and eleven compound scores, sorts each list by confidence in descending order, and takes the index of the largest of all 18 as the dominant emotion, labelled `basic` if the index is below seven and `compound` otherwise."]) + [

        H2("5.4 UML Class Design"),
    ] + dg("uml", 5.4, extra=[
        "The class diagram contains only what exists in the code. `User` and `Analysis` are SQLAlchemy models joined by a one-to-many relationship with cascading delete. `EmotionCNN` is one class used with two output sizes: seven for the backbone and 18 for the final model. "
        f"`ConditionalGenerator` ({gp:,} parameters) maps 100 noise values plus a seven-element condition to a 64 x 64 image through five transposed convolutions and a tanh; `ConditionalDiscriminator` scores an image together with its condition. "
        "The remaining boxes are function modules (security, dependencies, inference, face detection plus taxonomy, routers) drawn with the stereotype <<module>>. The generator and discriminator are used only by the training scripts."]) + [
        TAB("The EmotionCNN layers (`ml/classifier_model.py`)", ["Stage", "Layers", "Output shape"],
            [["Input", "1-channel 64 x 64 face, scaled to [-1, 1]", "1 x 64 x 64"],
             ["Block 1", "Conv 3x3 (32), BatchNorm, ReLU, MaxPool 2", "32 x 32 x 32"],
             ["Block 2", "Conv 3x3 (64), BatchNorm, ReLU, MaxPool 2", "64 x 16 x 16"],
             ["Block 3", "Conv 3x3 (128), BatchNorm, ReLU, MaxPool 2", "128 x 8 x 8"],
             ["Block 4", "Conv 3x3 (128), BatchNorm, ReLU, MaxPool 2", "128 x 4 x 4"],
             ["Classifier", "Flatten (2,048), Linear 256, ReLU, Dropout 0.4, Linear `out_dim`", f"7 (backbone) or 18 (final); {fin['parameters']:,} parameters at 18"]],
            widths=[1.0, 3.8, 1.7], align=["l", "l", "l"], size=9.5),
        P(f"The architecture combines standard components: batch normalisation [{R['bn']}], dropout [{R['dropout']}] and, for the final model, sigmoid outputs with binary cross-entropy, the usual formulation of multi-label learning [{R['multilabel']}]. "
          "It is deliberately close to the 'simple CNN' of the base paper, which also ends in a sigmoid layer, but it is a different, smaller network trained on different data."),

        H2("5.5 Sequence Design of the Main Flow"),
    ] + dg("seq", 5.4, extra=[
        "The main flow is the analysis of one photo by a signed-in user. The router asks `deps.get_current_user_optional()` for the user: if the Bearer token is absent or invalid the user is `None` and the flow continues anonymously. "
        "`analyze_image_bytes()` then runs the detector and the network and returns the lists. For a signed-in user the router inserts an `Analysis` row, commits, writes the cropped face to `media/thumbs/<id>.jpg` and updates `thumbnail_path`, so a successful analysis costs two commits. "
        "The alternative flows at the foot of the diagram record behaviour that was verified by the tests: anonymous calls are not stored, images without a face give `face_detected: false`, and another user's history id gives 404."]) + [

        H2("5.6 Use-Case Design"),
    ] + dg("uc", 4.6, extra=[
        "The end user's use cases are registration, login and logout, analysing a photo (upload or webcam), reading the three views of the result, browsing the history and deleting an entry. An opened history entry has its own route, `/app/history/[id]`, but no element in the history page links to it; "
        "the route can be reached only by typing the address. Other API clients can analyse without an account, in which case nothing is stored. The developer's single use case is running the training pipeline. "
        "No use case needs an administrator, which is why the design has no such role."]) + [

        H2("5.7 Database Design"),
    ] + dg("er", 5.2, extra=[
        "The database has two tables. User identifiers and analysis identifiers are random UUID strings. The 18 scores of an analysis are not spread across 18 columns: `basic_emotions`, `compound_emotions` and `dominant` are JSON columns holding the same objects the API returns "
        "(`key`, `label`, `confidence`, and `kind` for the dominant emotion). This keeps a history read to one query and lets the label set change without a migration, at the price that scores cannot be filtered or aggregated in SQL. The only declared foreign key is `analyses.user_id`."]) + [
        TAB("Table `users`", ["Column", "Type", "Constraint", "Meaning"],
            [["id", "VARCHAR", "Primary key (uuid4)", "User identifier, also the JWT `sub` claim"],
             ["name", "VARCHAR", "NOT NULL", "Display name"],
             ["email", "VARCHAR", "UNIQUE, INDEX, NOT NULL", "Login name; format is not validated (any string is accepted)"],
             ["password_hash", "VARCHAR", "NOT NULL", "bcrypt hash through passlib"],
             ["created_at", "DATETIME", "default UTC now", "Registration time"]],
            widths=[1.3, 0.9, 1.9, 2.4], align=["l", "l", "l", "l"], size=9.5),
        TAB("Table `analyses`", ["Column", "Type", "Constraint", "Meaning"],
            [["id", "VARCHAR", "Primary key (uuid4)", "Analysis identifier, also the thumbnail file name"],
             ["user_id", "VARCHAR", "FOREIGN KEY users.id, INDEX, NOT NULL", "Owner"],
             ["created_at", "DATETIME", "default UTC now", "Time of analysis"],
             ["face_detected", "BOOLEAN", "default false", "Whether the Haar detector found a face"],
             ["basic_emotions", "JSON", "default []", "Seven objects {key, label, confidence}, sorted by confidence"],
             ["compound_emotions", "JSON", "default []", "Eleven objects, sorted by confidence"],
             ["dominant", "JSON", "nullable", "{key, label, confidence, kind} for the argmax of all 18; null when no face"],
             ["thumbnail_path", "VARCHAR", "nullable", "Path of the cropped grayscale face under `media/thumbs/`"]],
            widths=[1.3, 0.9, 2.2, 2.1], align=["l", "l", "l", "l"], size=9.5),

        H2("5.8 Core Algorithms"),
        H3("5.8.1 Inference: analyze_image_bytes()"),
    ] + dg("flowchart", 4.5, extra=[
        "The decoding step uses Pillow and converts to RGB, then to BGR for OpenCV. The Haar cascade `haarcascade_frontalface_default.xml` is run on the grayscale image with scale factor 1.1, five minimum neighbours and a minimum face size of 40 x 40 pixels "
        f"[{R['viola']}]; the face with the largest width times height is kept. The crop is resized to 64 x 64, scaled, passed through the network and a sigmoid. The function has a `threshold` argument that is never used; "
        "the decision rule is simply the argmax. This rule has an important consequence: because a compound output must exceed every basic output to be chosen, and the compound outputs are tiny after training (Chapter 8), the dominant emotion is in practice always basic."]) + [
        H3("5.8.2 Training: three stages"),
    ] + dg("train", 5.0, extra=[
        f"Stage 1 trains the backbone with class-weighted cross-entropy and Adam [{R['adam']}] at a learning rate of 1e-3. Stage 2 trains the conditional GAN [{R['cgan']}][{R['gan']}] with Adam at 2e-4 (beta 0.5), batch size 64 and a real-label target of 0.9 (one-sided label smoothing), on 400 faces per class. "
        "The generator input is 100 Gaussian noise values concatenated with the seven-element condition; a one-hot condition was used in training. Stage 3a builds the compound training faces by feeding the generator a condition with 0.5 on each of the two component emotions "
        "(a blend never seen in training), 200 faces per class. Stage 3b copies the convolutional weights of the backbone into the 18-output network and trains it for five epochs with binary cross-entropy and Adam at 5e-4 on the union of real and synthetic faces. "
        "The target of a real face has one basic bit set; the target of a synthetic face has the two component bits and the compound bit set."]) + [

        H2("5.9 Module Design"),
        TAB("Backend modules (`backend/app`)", ["Module", "Responsibility", "Key interfaces"],
            [["`main.py`", "Create tables, CORS, mount thumbnails, include routers, load the model at start-up", "`app`"],
             ["`config.py`", "Paths, secret key (environment variable `MOSAIC_SECRET_KEY`, with a development default), token lifetime (7 days), database URL, CORS origins", "constants"],
             ["`db.py`, `models.py`", "SQLAlchemy engine/session, `User` and `Analysis` models", "`get_db()`"],
             ["`security.py`, `deps.py`", "bcrypt hashing, HS256 tokens, required and optional current user", "`create_access_token()`, `get_current_user()`"],
             ["`schemas.py`", "Pydantic request and response models (password minimum 6 characters)", "`RegisterRequest`, `AnalysisResponse`"],
             ["`routers/auth.py`", "Register, login, current user", "`/api/auth/*`"],
             ["`routers/analyze.py`", "Run inference, persist analysis and thumbnail", "`POST /api/analyze`"],
             ["`routers/history.py`", "List, read and delete a user's analyses", "`/api/history`"],
             ["`routers/health.py`", "Report model loading state", "`GET /api/health`"],
             ["`ml/taxonomy.py`", "The 7 + 11 labels, compound components, display labels", "`ALL_LABELS`, `COMPOUND_COMPONENTS`"],
             ["`ml/face.py`", "Largest-face Haar detection", "`detect_largest_face()`"],
             ["`ml/inference.py`", "Preprocess, forward pass, ranking, dominant emotion", "`analyze_image_bytes()`, `load_model()`"],
             ["`ml/classifier_model.py`, `ml/gan_model.py`", "Network definitions", "`EmotionCNN`, `ConditionalGenerator`, `ConditionalDiscriminator`"],
             ["`ml/dataset.py`", "Load FER2013 pickles, decode and resize, class weights", "`load_split()`, `class_weights()`"],
             ["`ml/train_*.py`, `synthesize_compound.py`, `run_pipeline.py`", "The three training stages and the synthesis step", "`main()`"]],
            widths=[1.9, 3.2, 1.4], align=["l", "l", "l"], size=9),
        TAB("Front-end modules (`frontend/src`)", ["Module", "Responsibility"],
            [["`app/page.tsx` and `components/landing/*`", "Landing page: navigation, hero with Three.js particle canvas, feature cards (GSAP), how-it-works, call to action"],
             ["`app/login`, `app/register`, `components/auth/*`", "Authentication pages and form; on success the token and user are stored and the router goes to `/app`"],
             ["`app/app/layout.tsx`, `DashboardShell.tsx`, `hooks/useAuthGuard.ts`", "Authenticated shell with sidebar (Analyze, History, user, log out); redirects to `/login` when no token is present"],
             ["`app/app/page.tsx`, `CaptureWidget.tsx`", "Analyse page: upload (drag and drop or file chooser) or webcam capture, loading, error and empty states"],
             ["`ResultsView.tsx`", "Dominant card, Recharts bar chart of the seven basic scores, top six compound bars; a message when no face was found"],
             ["`app/app/history`, `HistoryList.tsx`", "History grid with colour dot, dominant label, time and delete button; detail route for one analysis"],
             ["`lib/api.ts`, `store.ts`, `taxonomy.ts`, `emotionColors.ts`", "Typed API client, persisted auth store, compound components, colours"]],
            widths=[2.6, 3.9], align=["l", "l"], size=9),

        H2("5.10 API Design"),
        P("The API follows `API_CONTRACT.md`. All endpoints live under `/api`; bodies are JSON except the analyse call, which is `multipart/form-data` with one field named `image`. Errors use FastAPI's `{\"detail\": ...}` shape."),
        TAB("Endpoints", ["Method and path", "Auth", "Success", "Errors"],
            [["POST /api/auth/register", "None", "201 `{token, user}`", "409 duplicate e-mail; 422 invalid body or password shorter than 6"],
             ["POST /api/auth/login", "None", "200 `{token, user}`", "401 invalid credentials; 422"],
             ["GET /api/auth/me", "Required", "200 user", "401"],
             ["POST /api/analyze", "Optional", "200 analysis (`id` is null when not stored)", "422 no file; **500 on an undecodable file**; 200 with `face_detected: false` when no face"],
             ["GET /api/history?limit&offset", "Required", "200 `{items, total}`, newest first", "401; 422 non-numeric limit"],
             ["GET /api/history/{id}", "Required", "200 analysis", "401; 404 missing or owned by another user"],
             ["DELETE /api/history/{id}", "Required", "204", "401; 404"],
             ["GET /api/health", "None", "200 `{status, model_loaded}`", "-"],
             ["GET /api/media/thumbs/{id}.jpg", "None (static)", "200 JPEG", "404"]],
            widths=[2.1, 0.9, 1.7, 1.8], align=["l", "l", "l", "l"], size=9),
        P("Two differences between the contract and the implementation were found while testing and are kept as they are. The contract says a photograph without a face returns HTTP 422; the implementation returns 200 with `face_detected: false` and empty lists, "
          "and the UI handles it. The thumbnail URL is returned as a path relative to the API (`/api/media/thumbs/<id>.jpg`); the contract does not say who resolves it."),

        H2("5.11 User Interface Design"),
        P("The interface is a dark, single-theme design with a violet-to-orange accent, a display font for headings and one colour per basic emotion (angry red, disgust green, fear purple, happy amber, sad blue, surprise pink, neutral grey). "
          "A compound emotion takes the colour of its first component. The design intentionally avoids academic wording, as the API contract requires. The screens below were captured with the production build of the real front end against the real model."),
        sh("01_landing_hero.png", "Landing page: hero with the animated particle canvas and the call to action."),
        sh("07_analyze_empty.png", "Analyse page before an upload: Upload and Webcam tabs, drop zone and an empty results panel."),
        sh("08_result_happy.png", "Analyse page after uploading a real FER2013 face: dominant card, basic-emotion chart and compound bars."),
        sh("17_history.png", "History page: one card per stored analysis with its dominant label, confidence and time."),
        P("The analyse page keeps the capture on the left and the results on the right on wide screens (two columns from 1024 px), and stacks them on narrow ones; the sidebar is hidden below 640 px and replaced by a header with a log-out link. "
          "The results panel animates in with Framer Motion; compound bars show only the six highest of the eleven scores. Loading, error and empty states each have their own panel."),
        H3("5.11.1 Interface defects found during design review"),
        B("**Thumbnail not shown.** `ResultsView` renders `result.thumbnail_url` directly, a relative path that resolves against the front-end origin instead of the API origin, so the face thumbnail appears as a broken image in every result card. "
          "The helper `thumbnailUrl()` in `lib/api.ts` would fix it but is not applied there.",
          "**History detail unreachable.** `/app/history/[id]` renders a saved result, but the history cards do not link to it.",
          "**Reload in development mode.** In the Next.js development server a hard reload of `/app` redirected to `/login` even with a stored token, because the guard runs before the persisted store is read; the production build kept the session in the probe that was run. "
          "The screenshots were therefore taken with the production build and in-app navigation."),

        H2("5.12 Design Decisions and Their Reasons"),
        TAB("Principal design decisions", ["Decision", "Reason", "Cost"],
            [["One multi-label network with 18 sigmoid outputs", "A face can carry several emotions; sigmoid outputs do not compete", "No single normalised distribution; thresholds must be chosen"],
             ["Initialise the final network from a softmax backbone", "Faster convergence, and a separately measurable single-label baseline", "The comparison with the baseline mixes extra epochs with multi-label training; a real-only control was added in Chapter 8"],
             ["Condition the generator with a seven-element soft vector", "Allows blended conditions such as 0.5 happy + 0.5 surprise without retraining", "The generator was trained only on one-hot conditions, so blends are out of distribution"],
             ["64 x 64 grayscale input", "Fits CPU training and the 48 x 48 source data", "Loses colour and fine detail"],
             ["JSON columns for scores", "One query per history read; flexible labels", "No SQL filtering by score"],
             ["Optional authentication on `/api/analyze`", "Lets clients try the model without an account", "Anonymous calls are not stored; the web UI does not use this path"],
             ["Haar cascade for detection", "Ships with OpenCV; no extra model", "Misses non-frontal and very small faces; crops differ from training frames"]],
            widths=[2.1, 2.3, 2.1], align=["l", "l", "l"], size=9),
    ]
    return out
