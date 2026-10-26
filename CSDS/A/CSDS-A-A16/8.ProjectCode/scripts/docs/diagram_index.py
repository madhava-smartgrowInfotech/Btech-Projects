"""Index of the eleven design diagrams: (key, title, file, caption, explanatory paragraph). Used by document 11 and by the report."""

DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png",
     "System architecture of Mosaic: browser tier, FastAPI service, ML modules and local files.",
     "Mosaic is one Python process with a browser front end. The Next.js console (port 3000) talks to the FastAPI application (port 8000 by default) over JSON and multipart HTTP; "
     "CORS admits only `localhost:3000` and `127.0.0.1:3000`. The routers handle accounts, analysis and history; `deps.py` and `security.py` turn a Bearer token into a user "
     "(optionally, for `/api/analyze`), hash passwords with bcrypt and sign seven-day HS256 tokens. Underneath, `app/ml` holds the face detector (OpenCV Haar cascade), the inference module, "
     "the 18-output `EmotionCNN` and, for training only, the conditional generator and discriminator. State lives in SQLite (`mosaic.db`), in the checkpoint files and in a folder of "
     "cropped-face thumbnails. Nothing calls an external service at run time."),
    ("flow", "High-level workflow", "02_high_level_workflow.png",
     "High-level workflow: three offline training stages, then one online pass per uploaded image.",
     "The workflow has two stages. Offline, `python -m app.ml.run_pipeline` loads the FER2013 pickles, trains a 7-class backbone, trains the conditional GAN on 400 faces per class, "
     "synthesises 200 faces for each of the eleven compound classes by conditioning on two emotions at 0.5 each, and trains the final 18-output classifier on 28,709 real plus 2,200 synthetic images. "
     "Online, every request to `/api/analyze` passes through five steps: upload, Haar face detection, preprocessing and CNN forward pass, ranking of the 18 sigmoid outputs, and storage plus display. "
     "When no face is found the API still answers 200, with `face_detected` false and empty lists."),
    ("dfd0", "Data flow diagram, level 0", "03_dfd_level0.png",
     "Level 0 data flow diagram: Mosaic and its four external entities.",
     "The context diagram treats Mosaic as one process. The end user sends a photo, credentials or history requests and receives a token, the basic and compound scores, the dominant emotion and the saved history. "
     "The developer starts the training pipeline; the OpenCV Haar cascade file supplies the face detector; the FER2013 pickles supply labelled faces at training time only. "
     "One data store, D1, stands for the SQLite database, the checkpoint files and the thumbnail folder."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png",
     "Level 1 data flow diagram: seven processes and four data stores.",
     "Level 1 splits the system into seven processes. 1.0 registers users and issues tokens (store D1, users); 2.0 detects the largest face; 3.0 classifies the face crop with the CNN; "
     "4.0 ranks the scores and builds the response; 5.0 stores the analysis (D2) and the face thumbnail (D3); 6.0 lists, reads and deletes history; and 7.0 is the offline training pipeline that "
     "produces the checkpoint files in D4, which process 3.0 loads once at start-up."),
    ("dfd2", "Data flow diagram, level 2", "05_dfd_level2.png",
     "Level 2 data flow diagram: processes 3.0 (classify) and 4.0 (rank and respond) expanded.",
     "Process 3.0 becomes four steps: resize the crop to 64 by 64 pixels, scale it to the range minus one to one, run the four-block CNN, and apply a sigmoid to the 18 logits. "
     "Process 4.0 splits the 18 probabilities into the seven basic and eleven compound scores, sorts each list by confidence, and takes the argmax over all 18 as the dominant emotion. "
     "The classifier weights come from D4 and are loaded when the server starts."),
    ("uml", "UML class diagram", "06_uml_class.png",
     "UML class diagram of the classes and module-level interfaces present in the code.",
     "The code has two ORM classes (`User`, `Analysis`, joined one-to-many), three neural-network classes (`EmotionCNN`, `ConditionalGenerator`, `ConditionalDiscriminator`) and several function modules, "
     "which are drawn with the stereotype <<module>>. `inference.analyze_image_bytes()` uses the face detector, the taxonomy and `EmotionCNN` with 18 outputs; the routers use `security`, `deps`, "
     "the models and `inference`. The generator and discriminator are used only by the training scripts and are never loaded by the API."),
    ("seq", "Sequence diagram of the main flow", "07_sequence_main_flow.png",
     "Sequence diagram: a signed-in user uploads a photo and receives a result.",
     "The main flow starts when the user chooses or drops an image. The Next.js page posts it to `/api/analyze` with the Bearer token; the router resolves the optional user, calls "
     "`analyze_image_bytes()`, which runs the Haar detector and the CNN, then inserts an `Analysis` row, writes the cropped-face thumbnail, updates its path and returns the 200 response. "
     "The alternative flows at the bottom cover anonymous calls, a photo without a face, a missing model file, an undecodable upload (HTTP 500, no handler) and history access control."),
    ("uc", "Use-case diagram", "08_use_case.png",
     "Use-case diagram: what the end user, an API client and the developer can do.",
     "The end user can register, log in and out, upload a photo or capture a webcam frame, read the basic-emotion chart, the compound scores and the dominant emotion, and browse or delete history. "
     "An opened history entry has a route (`/app/history/[id]`) but no link in the UI points to it. Another API client may analyse without an account (the result is then not stored); "
     "the developer runs the training pipeline from the command line."),
    ("er", "Entity-relationship diagram", "09_er_diagram.png",
     "Entity-relationship diagram of the SQLite database: two tables joined one-to-many.",
     "`models.py` defines two tables. `users` holds a UUID, name, unique indexed e-mail, bcrypt hash and creation time. `analyses` holds a UUID, an indexed foreign key to the user, the creation time, "
     "whether a face was detected, the 7 basic and 11 compound scores as JSON documents, the dominant emotion as JSON and the thumbnail path. The ORM relationship cascades deletes from a user to their analyses. "
     "Uploaded photos are never stored; only the cropped grayscale face is written to disk."),
    ("flowchart", "Flowchart of the core algorithm", "10_flowchart_core_algorithm.png",
     "Flowchart of analyze_image_bytes(), the algorithm every request passes through.",
     "`analyze_image_bytes()` decodes the upload with Pillow, converts it to BGR for OpenCV and runs the Haar cascade (scale factor 1.1, five neighbours, minimum size 40 by 40). If nothing is found it returns "
     "`face_detected` false. Otherwise it crops the largest box in grayscale, resizes to 64 by 64, scales to [-1, 1], runs the 18-output CNN, applies a sigmoid, sorts the basic and compound lists, "
     "and takes the argmax over all 18 as the dominant emotion, marked basic when its index is below seven."),
    ("train", "Flowchart of the training pipeline", "11_flowchart_training.png",
     "Flowchart of the training pipeline: backbone, cEmoGAN, synthesis and the final multi-label classifier.",
     "Stage 1 trains a 7-class softmax CNN (five epochs, Adam 1e-3, class-weighted cross-entropy). Stage 2 trains the conditional GAN on 400 faces per class for ten epochs. Stage 3a synthesises 2,200 compound faces "
     "(200 per class) and Stage 3b trains the 18-output classifier with binary cross-entropy for five epochs from the backbone's convolutional weights, on the 28,709 real faces (one basic bit each) plus the synthetic faces "
     "(two basic bits and one compound bit each). The FER2013 test set has no compound labels, so compound outputs cannot be validated on real data."),
]
