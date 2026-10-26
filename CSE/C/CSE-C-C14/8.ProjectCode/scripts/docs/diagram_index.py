"""Index of the VeriVision AI design diagrams: (key, title, file, caption, explanatory paragraph).

The files are written by scripts/docs_build/make_diagrams.py into docs/diagrams/ and mirror the code in app/ and scripts/.
Used by the block-diagram document and the full report.
"""

DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png",
     "Four-tier architecture of VeriVision AI: React web app, Flask application, PyTorch inference and local file storage.",
     "The browser tier is a React and Vite application on port 5414 that talks to the Flask server on port 8414 through JSON and one multipart image upload; the Vite dev server proxies /api, /health and /artifacts. "
     "The Flask tier holds the status routes, the demo sign-in with a signed 12-hour token, the three analysis routes and the upload guards. "
     "Behind it the inference tier loads four PyTorch models once, runs them, fuses their logits and produces the Grad-CAM overlays and the robustness re-checks. "
     "Everything persisted is a file: the four checkpoints, the model metadata, the evaluation artifacts and the dataset folders. There is no relational database, and images are never sent to an external service."),
    ("flow", "High-level workflow", "02_high_level_workflow.png",
     "High-level workflow of VeriVision AI for one POST /api/analyze request.",
     "A request passes through ten stages. The image is validated (extension, size, non-empty, decodable), converted to RGB and resized for each route, and the four routes return logit pairs. "
     "The pairs are fused with the two gates into a verdict and a confidence word, Grad-CAM overlays are produced for three routes on the predicted class, and the image is re-tested under JPEG, resize and blur variants. "
     "The result is assembled as one JSON object and shown as a verdict card with tabs. If a checkpoint is missing the endpoint answers 503 and the Status page names the missing files."),
    ("dfd0", "Data flow diagram, level 0", "03_dfd_level0.png",
     "Context diagram (DFD level 0) of VeriVision AI with its two actors and two external stores.",
     "At level 0 the whole system is one process. The user sends an image and a demo login and receives the verdict, confidence, per-route votes, Grad-CAM overlays and robustness result. "
     "The developer supplies training and evaluation commands and receives checkpoints and metrics. The system reads and writes the model files and metric artifacts and reads the image dataset folders when training. "
     "No external web service takes part."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png",
     "DFD level 1 of VeriVision AI: seven processes and three data stores.",
     "Level 1 splits the system into validation and authentication (1.0), preprocessing and route logits (2.0), fusion and gating (3.0), Grad-CAM explanation (4.0), the robustness re-check (5.0), reporting of insights (6.0) and training and evaluation (7.0). "
     "Process 2.0 loads the model files and metadata once and passes four logit pairs to 3.0. The predicted class drives 4.0, and 5.0 re-runs the pipeline on degraded variants; both return to the report that goes to the user. "
     "Process 7.0 writes the checkpoints, the metadata and the metric artifacts that process 6.0 later reads."),
    ("dfd2", "Data flow diagram, level 2", "05_dfd_level2.png",
     "DFD level 2 of VeriVision AI: processes 2.0 and 3.0 expanded into eleven sub-processes.",
     "Level 2 follows app/inference.py and app/ensemble.py. The image is decoded and resized (2.1) and normalised with ImageNet statistics (2.2); four route models, one of them with horizontal-flip test-time augmentation, produce logit pairs (2.3a to 2.3d). "
     "Gate 1 decides whether route B is an outlier (3.1), the remaining logits are combined by the configured weights (3.2), Gate 2 checks the B and C consensus (3.3) and the softmax and confidence wording are applied (3.4)."),
    ("uml", "UML class diagram", "06_uml_class.png",
     "UML class diagram of VeriVision AI showing the application factory, the two blueprints and the service modules.",
     "FlaskApp registers the Routes blueprint (HTML pages, health and the original JSON predict) and the Api blueprint (sign-in, config, insights and analyze), which reuses the analysis routine of Routes. "
     "Both call Inference, which uses Preprocessing for validation and decoding, Models for the four architectures and checkpoints, Ensemble for fusion and gating, Explainability for Grad-CAM and Robustness for the degraded variants. "
     "Config holds every tunable setting. The Training scripts reuse the model builders. The service modules are Python files of functions; they are drawn as classes to show their responsibilities."),
    ("seq", "Sequence diagram of an analysis", "07_sequence_analyze.png",
     "Sequence diagram of one image analysis, from the browser upload to the JSON response.",
     "The browser posts the image with its bearer token. api.py verifies the token, makes sure the models are loaded, validates and decodes the upload and calls predict_image. "
     "Inference runs the four forward passes and asks Ensemble for the fused result. api.py then asks the explanation and robustness modules for the Grad-CAM overlays and the consistency check, assembles one dictionary and returns it as JSON, or an error code for a bad token, upload or missing model. "
     "The browser renders the verdict, the tabs and the heat-map selector."),
    ("uc", "Use-case diagram", "08_use_case.png",
     "Use-case diagram of VeriVision AI with the user and the developer.",
     "The user signs in with the demo account, uploads an image, reads the verdict and confidence, inspects the per-route votes, opens the Grad-CAM heat map, checks the robustness consistency, reads the model insights and checks the system status. "
     "The verdict, votes, heat map and robustness all depend on an uploaded image. The developer reads the insights and status and prepares data, trains and evaluates the models with the scripts."),
    ("er", "Entity-relationship diagram (file-based data model)", "09_er_diagram.png",
     "Persisted data model of VeriVision AI: model checkpoints, model metadata and metric artifacts, plus the runtime-only session token and upload buffer.",
     "VeriVision has no relational database. The persisted entities are the four ModelCheckpoint files, one ModelMetadata record per model that points at its checkpoint, and the MetricsArtifact JSON files written by the evaluation script from ImageSample test folders. "
     "The SessionToken and the UploadBuffer exist only inside a request: the token is a signed value that is not stored and the uploaded bytes are decoded in memory and discarded after the reply."),
    ("flowchart", "Flowchart of the core algorithm", "10_flowchart_ensemble.png",
     "Flowchart of the logit fusion with the two gating rules implemented in app/ensemble.py.",
     "The four logit pairs enter with weights 0.35, 0.15, 0.25 and 0.25. Gate 1 removes route B when its margin is at least 2.5 and all three other routes point the other way; the weights are then renormalised. "
     "The weighted sum of the remaining logits is formed. Gate 2 nudges the fused logits by 0.75 toward the B and C class when B and C agree with margins of at least 2.5 and the fused direction differs. "
     "A softmax gives the probabilities, the larger one is the confidence, and the agreement count is the number of routes whose own label equals the final label."),
    ("train", "Training and evaluation pipeline", "11_training_pipeline.png",
     "Training and evaluation pipeline of VeriVision AI (scripts/).",
     "The dataset script builds class-balanced train, validation and test folders. Each route is fine-tuned from ImageNet weights with its own augmentation, AdamW with cosine decay and either cross-entropy or focal loss, and early stopping on the validation F1. "
     "The checkpoints are saved to models, and the evaluation script measures every route and the ensemble on the held-out test folder and on degraded variants, writing the JSON artifacts that the insights page reads."),
]
