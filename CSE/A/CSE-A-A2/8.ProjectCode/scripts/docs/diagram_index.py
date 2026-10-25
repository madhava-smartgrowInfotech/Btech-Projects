"""Index of the ResQAI design diagrams: (key, title, file, caption, explanatory paragraph).

The files are written by scripts/docs_build/make_diagrams.py into docs/diagrams/ (matplotlib, 150 dpi) and mirror app.py, auth.py,
train_models.py, data/*.json and frontend/src. Used by the block-diagram document and the full report.
"""

DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png",
     "Four-tier architecture of ResQAI: React console, Flask API, machine-learning tier and file-based data tier.",
     "The presentation tier is a React 19 and Vite 8 single-page application on port 5302. Its pages (landing, login, register, live monitor, manual override, emergency response) share one state object, MonitorContext, "
     "which holds the sensor history, the event log, the 15-second countdown and the dispatch result, and reach the server only through lib/api.js; the Vite dev server proxies /api to port 8302. "
     "The application tier is a single Flask process: app.py serves the original dashboard, /api/simulate, /api/predict, /api/hospitals, /api/emergency and /api/health, and auth.py adds the account endpoints and an optional guard. "
     "The machine-learning tier is loaded once at start-up with joblib: a StandardScaler and two random forests, with a rule-based fallback that answers only if the model files are missing. "
     "There is no database. The data tier is two JSON files (users.json, hospitals.json) and four pickles; the only outside services are OpenStreetMap map tiles and the browser's own Geolocation API, both used on the client side."),
    ("flow", "High-level workflow", "02_high_level_workflow.png",
     "High-level workflow of one event, from the sensor reading to the dispatched alert.",
     "A reading of eleven features is produced (here by /api/simulate, in a deployment by the phone) and sent to /api/predict. The detector says whether the event is a crash and with what probability, and the severity model grades it None, Minor, Moderate or Severe. "
     "Only a Moderate or Severe result leaves the logging path: live monitoring pauses and a confirmation dialog counts down from 15 seconds. The occupant can cancel with a button or Escape, which is logged as a false alarm. "
     "If the countdown reaches zero, or the occupant presses Send alert now, the browser location is read (3 second timeout), the three nearest hospitals are ranked by great-circle distance, and a dispatch message with a map link, the severity, the confidence, the nearest hospital and its phone number is composed and shown. "
     "No message is transmitted in this build."),
    ("dfd0", "Data flow diagram, level 0", "03_dfd_level0.png",
     "Context diagram (DFD level 0) of ResQAI with its user and the two outside services.",
     "At level 0 the whole system is one process. The occupant sends registration details, credentials, a scenario choice or manual sensor values, and a cancel or send decision, and receives the detection result, the countdown, the dispatch message, the hospitals, the map and the event log. "
     "The browser Geolocation API supplies the device latitude and longitude, and the OpenStreetMap tile server supplies map tiles on request. "
     "The sensor readings are generated inside the system because no phone is attached; the dispatch message is displayed, not transmitted; and accounts and the hospital directory are local JSON files."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png",
     "DFD level 1 of ResQAI: six processes and three data stores.",
     "Level 1 divides the system into authentication (1.0), reading acquisition (2.0), detection and grading (3.0), alert confirmation (4.0), location and hospital ranking (5.0) and dispatch composition (6.0). "
     "Process 1.0 reads and writes the users file (D1) and issues the signed token that the other processes may require. Process 2.0 turns a scenario choice or typed values into the eleven-feature reading. "
     "Process 3.0 reads the model pickles (D3) and returns the accident flag, the probability and the severity, which process 4.0 turns into a countdown when the severity is Moderate or Severe. "
     "After confirmation, process 5.0 reads the hospital directory (D2) and ranks it from the device location, and process 6.0 assembles the message that goes back to the occupant."),
    ("dfd2", "Data flow diagram, level 2", "05_dfd_level2.png",
     "DFD level 2 of process 3.0: expansion of build_feature_vector and predict_from_features.",
     "Level 2 follows the code of app.py. The payload is completed with defaults and the derived magnitudes (3.1), scaled with the training mean and standard deviation (3.2), and passed to the detector (3.3) and to the severity model (3.4) in parallel. "
     "Process 3.5 applies the gate that forces the severity to None when the detector says no accident, and builds the JSON response. "
     "Process 3.6 is the rule-based fallback on acc_magnitude, used only when the model files cannot be loaded; its answers carry the model source rule_based_fallback."),
    ("uml", "UML class diagram", "06_uml_class.png",
     "Design-level class diagram of ResQAI: data classes, the two scikit-learn model objects, the hospital directory and the React state provider.",
     "The backend is written as functions in app.py and auth.py rather than as application classes, so the diagram shows the objects those functions work on. "
     "SensorReading is the eleven-feature record and Prediction the response of /api/predict; both are transient JSON. The same RandomForestClassifier class appears twice at run time, as the detector (200 trees, depth 10) and as the severity model (250 trees, depth 12), "
     "fed by one StandardScaler. HospitalDirectory wraps the ten-entry JSON file with the haversine distance and the nearest-k selection, and EmergencyAlert is the response of /api/emergency. "
     "On the client, MonitorProvider owns the state machine: it runs readings, starts and cancels the countdown, and sends the alert. AuthService and User describe auth.py and users.json."),
    ("seq", "Sequence diagram of the main flow", "07_sequence_main_flow.png",
     "Sequence of the main flow: scenario, detection, confirmation and dispatch.",
     "The occupant presses Severe crash. The React app fetches a simulated reading, posts it to /api/predict, and the Flask process scales it and calls the two forests. "
     "A Moderate or Severe answer opens the dialog and starts the countdown. In branch A the occupant cancels and the event is only logged. In branch B the countdown expires or the occupant sends the alert, the browser location is read, "
     "/api/emergency is called, the three nearest hospitals are computed, and the dispatch message, the alert id and the numbers 112 and 108 come back and are shown with the map."),
    ("uc", "Use-case diagram", "08_use_case.png",
     "Use cases of ResQAI for the vehicle occupant, the developer and the external services.",
     "The occupant registers or signs in, runs any of five scenarios, switches on live monitoring, types manual sensor values, confirms or cancels an alert, views the response map and hospitals, taps the 108, 112 or 103 numbers, and uses the theme switch and the event log. "
     "The developer retrains the models, sets REQUIRE_AUTH and runs the test scripts; these are command-line activities, not screens. The external services (map tiles and device location) support the map and the location steps."),
    ("er", "Entity diagram", "09_er_diagram.png",
     "Entities of ResQAI: two persisted records, the model files, and three transient run-time entities.",
     "ResQAI has no relational database. The persisted records are the accounts in users.json (keyed by lower-case e-mail, with a scrypt password hash) and the ten hospitals in hospitals.json, plus the four model pickles. "
     "SensorReading, Prediction and EmergencyAlert exist only as JSON in a request or as React state (a history of 40 points and an event log of 25 entries), so a page reload loses them, and alerts are not stored on the server. "
     "Each reading yields one prediction; a prediction may lead to at most one alert, which is built from the three nearest hospitals. An alert carries no user id, so alerts cannot yet be tied to an account."),
    ("flowc", "Flowchart of the core algorithm", "10_flowchart_core_algorithm.png",
     "Flowchart of predict_from_features and the client-side confirmation rule.",
     "The payload is completed and turned into a feature vector. If the models are loaded, the vector is scaled, the detector gives the class and the probability of an accident, and the severity model gives the grade; if the detector says no accident the grade is set to None. "
     "If the models are missing the three thresholds of the fallback give the grade instead. The response is returned to the browser, which opens the 15-second confirmation only when the grade is Moderate or Severe."),
    ("train", "Training pipeline", "11_training_pipeline.png",
     "Offline pipeline of train_models.py: generate, split, scale, train, evaluate, save.",
     "The training script generates 12,000 synthetic sensor events with seed 42 (60 percent normal driving, 20 percent harsh braking, 10 percent minor, 6 percent moderate and 4 percent severe crashes), splits them 80/20 stratified on the accident label, "
     "fits the scaler on the training part, trains the two forests with balanced class weights, prints the accuracy and classification report on the 2,400 held-out events, and writes the four pickles to models/."),
]
