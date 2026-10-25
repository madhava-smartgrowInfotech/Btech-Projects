"""Index of the SecurePay AI design diagrams: (key, title, file, caption, explanatory paragraph).

The files are written by scripts/docs_build/make_diagrams.py into docs/diagrams/ (PNG, 150 dpi) and mirror the code in
backend/ and frontend/src/pages. Used by the block-diagram document and the full report.
"""

DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png",
     "Four-tier architecture of SecurePay AI: React web app, Flask application, Python model modules and local data files.",
     "The browser tier is a React and Vite single-page application served on port 5304; it reaches the API only through the fetch wrapper in lib/api.js, and the Vite dev server proxies /api to port 8304. "
     "The Flask tier exposes the routes in app.py and the read-only blueprint in api_extra.py, and keeps the dataset, the fitted pipeline, the three models and their histories in one in-memory store. "
     "Behind it the model tier holds preprocessing, the GRBMC classifier, the two samplers, the training loop and the evaluation helper. "
     "The data tier is plain files: the 39,000-row CSV, pipeline.pkl, three model pickles, three history files and the last batch-prediction CSV. There is no SQL database."),
    ("flow", "High-level workflow", "02_high_level_workflow.png",
     "High-level workflow: the build path that produces the models and the score path that uses them.",
     "The upper row is the build path, run from the Model lab page or from seed_models.py. A synthetic dataset is generated, preprocessed, reduced to the most important columns, split 80/20, "
     "and three models are trained by the classical, simulated-annealing and quantum-inspired samplers; the models and their per-epoch histories are saved. "
     "The lower row is the score path used by the Verify and Bulk pages. Input values are turned into the feature vector, the scaling step is attempted, the three models each give a fraud probability, "
     "their mean is compared with 0.5, and the probability is mapped to a LOW, MEDIUM or HIGH risk band. The scaling box is marked because, on the bulk-upload path, that step is skipped in the current code (the single-transaction path scales correctly)."),
    ("dfd0", "Data flow diagram, level 0", "03_dfd_level0.png",
     "Context diagram (DFD level 0) of SecurePay AI with its two users and the local file store.",
     "At level 0 the whole application is one process. The merchant or analyst sends transaction fields or a CSV file and receives a fraud score, a risk level and a decision. "
     "The risk-operations team sends retrain and view requests and receives analytics, model metrics and the predictions CSV. "
     "The application has no login, so the two actors are roles of use rather than accounts. "
     "The only other thing it talks to is its own set of local files, read and written through pandas and joblib. No external web service and no quantum hardware is involved at any point."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png",
     "DFD level 1 of SecurePay AI: six processes and four data stores.",
     "Level 1 splits the system into six processes. Process 1.0 generates and preprocesses the dataset, 2.0 trains the three models from the split held in the pipeline, "
     "3.0 scores one transaction, 4.0 scores an uploaded CSV batch, 5.0 produces analytics and model reports from the dataset, the history files and the feature importances, and 6.0 exports the predictions. "
     "Four data stores appear: the dataset CSV (D1), the fitted pipeline (D2), the models with their histories (D3) and the batch-predictions CSV (D4). "
     "Processes 3.0 and 4.0 read the scaler and the column list from D2 and the three models from D3; process 4.0 writes D4, which process 6.0 serves as a download."),
    ("dfd2", "Data flow diagram, level 2", "05_dfd_level2.png",
     "DFD level 2 of SecurePay AI: the single-transaction scoring process split into five sub-processes.",
     "Level 2 expands process 3.0, POST /api/predict_single. Sub-process 3.1 validates the JSON, fills any missing field with the dataset mean or mode and one-hot encodes the categorical fields. "
     "Sub-process 3.2 aligns the columns with the training columns and attempts to scale the numeric ones with the stored scaler. "
     "Sub-process 3.3 asks the three models for a fraud probability, 3.4 averages them and applies the 0.5 threshold, and 3.5 assigns the risk band at 0.4 and 0.7. "
     "The note under the diagram records that this single-transaction path scales all 24 numeric columns before selecting the 18 model columns and is therefore correct; the bulk-upload route selects first, which is where the defect described in the next diagrams occurs."),
    ("uml", "UML class diagram", "06_uml_class.png",
     "Class and module diagram of the SecurePay AI backend: the GRBMC class, the helper modules and the Flask application with its store.",
     "GRBMC is the only real class. It holds the weight matrices W and U, the biases b, c and d, the persistent chain used by contrastive divergence, and the methods for one Gibbs step, one training epoch, probability prediction and the QUBO matrix. "
     "The samplers module supplies the simulated-annealing and quantum-inspired gradient functions that train_model passes to GRBMC. "
     "The preprocessing, evaluation and synthetic_data modules are collections of functions. The Flask application owns a store dictionary with up to three GRBMC instances, "
     "and the api_extra blueprint reads that store to answer the analytics, history and feature-importance requests."),
    ("seq", "Sequence diagram: verify a transaction", "07_sequence_prediction.png",
     "Sequence of one Verify request from the React page to the three models and back.",
     "The user presses Run fraud check on the Verify page. The browser posts the form values to /api/predict_single, the Vite dev proxy forwards the call to Flask on port 8304, "
     "and the handler asks ensure_pipeline for the stored columns and scaler. It then fills defaults, one-hot encodes, aligns the columns and attempts the scaling step. "
     "predict_proba is called on each of the three models, the returned probabilities are averaged, and the handler answers with a JSON object holding the prediction, the fraud probability, the label, "
     "the risk level and the per-model probabilities. The page then draws the risk meter and the per-model bars."),
    ("uc", "Use-case diagram", "08_use_case.png",
     "Use cases offered by the SecurePay AI screens, grouped by the role that typically needs them.",
     "The application has seven functions, each backed by a real page or endpoint. The merchant or analyst verifies a single transaction, bulk-verifies a CSV file, downloads the predictions CSV and downloads the sample CSV. "
     "The risk-operations team views analytics by place, time, amount and card signals, compares the three models and their training curves, and retrains the models in the Model lab. "
     "There is no login, so the split into two roles is a way of describing typical use rather than an access-control rule; either role can open every screen. "
     "The diagram is therefore a use-case view of the interface, not of a permission model."),
    ("er", "Entity-relationship diagram of the persisted data", "09_er_diagram.png",
     "Entity-relationship view of the files SecurePay AI persists; the project has no SQL database.",
     "Because the project stores everything in files, the entity-relationship view shows the file formats and the code paths that relate them. "
     "creditcard_synthetic.csv holds the 39,000 raw transactions. Preprocessing turns it into pipeline.pkl, which stores the split, the fitted scaler, the 18 selected columns and the feature importances. "
     "Training turns the pipeline into three model pickles and, for each of them, one history file of per-epoch metrics. "
     "The batch-prediction route reads the pipeline and the models and writes batch_predictions.csv with three extra columns. sample_batch.csv is a 20-row extract of the dataset used by the Bulk page demonstration."),
    ("train", "Flowchart: building the models", "10_flowchart_training.png",
     "Flowchart of the build path: preprocessing steps, the choice of training mode and the per-epoch loop.",
     "The chart follows preprocessing.full_pipeline and train.train_model. The dataset is one-hot encoded, the 24 numeric columns are z-scored, columns correlated above 0.95 are dropped, "
     "the data are balanced by manual undersampling, a random forest ranks the features and the top 18 are kept, and a stratified 80/20 split is made. "
     "The mode then selects the trainer. Classical uses 200 hidden units, a batch of 512 and persistent contrastive divergence. The simulated-annealing and quantum-inspired modes use 65 hidden units, a batch of 32 and a 3,000-row subsample per epoch. "
     "After every epoch the model is scored on the test split; after the last epoch the model and its history are saved."),
    ("decision", "Flowchart: scoring in the bulk route", "11_flowchart_decision.png",
     "Flowchart of the bulk-upload scoring path, with the scaling step that fails silently drawn as a dashed box.",
     "The chart follows the bulk route, predict_batch (predict_single scales before it selects columns, so it does not have this fault). Missing fields are filled from the dataset, the categorical fields are one-hot encoded, and columns the model expects are added with the value zero. "
     "The dashed box is the scaler call: the scaler was fitted on 24 numeric columns, only 13 are present after the selection, scikit-learn raises an error and a bare except clause discards it, "
     "so the model receives unscaled values. The 18 model columns are then selected, the three models are asked for a probability, and the mean is compared with 0.5 for the label. "
     "The risk band is LOW below 0.4, MEDIUM from 0.4 to 0.7 and HIGH above 0.7."),
    ("grbmc", "Structure of the GRBMC and its samplers", "12_grbmc_structure.png",
     "Layers and weights of the Gaussian-Bernoulli RBM classifier, and the three ways its negative phase is sampled.",
     "The model has 18 Gaussian visible units for the selected features, a layer of binary hidden units, and two label units that hold the one-hot class. "
     "Weights W connect visible and hidden units, weights U connect label and hidden units, and the vectors c, b and d are the biases. The hidden layer has 200 units for the classical trainer and 65 for the other two. "
     "Training moves W and the other parameters by the difference between a data average and a model average. The three trainers differ only in how the model average is obtained: "
     "a persistent Gibbs chain, simulated-annealing sweeps with a rising inverse temperature, or the same sweeps with random tunnelling flips that decay as the schedule advances."),
]
