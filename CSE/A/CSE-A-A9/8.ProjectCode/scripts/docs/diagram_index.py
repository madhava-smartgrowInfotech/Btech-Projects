"""Index of the BotGraph design diagrams: (key, title, file, caption, explanatory paragraph).

The files are written by scripts/docs_build/make_diagrams.py, diagrams_dfd.py and diagrams_more.py into docs/diagrams/.
Used by the block-diagram document (11) and the full report.
"""

DIAGRAMS = [
    ("arch", "System architecture", "01_system_architecture.png",
     "Four-tier architecture of BotGraph: React web app, FastAPI application, core modules with in-memory state, and the SQLite database plus files.",
     "The presentation tier is the React 18 and Vite 5 web app on port 5309; its pages are loaded on demand and a Vite proxy forwards every /api call to the API. "
     "The FastAPI application on 127.0.0.1:8309 groups the routes (core, accounts, clusters, queue, models) and auth.py, which checks bcrypt password hashes and issues HS256 tokens valid for 12 hours. "
     "Below it, services/store.py loads the graph, scores, clusters and metrics once at start-up, and the ml package holds the graph builder, the three GNN layers, training, clustering and evaluation, "
     "all written in plain PyTorch sparse operations. Retraining runs in a background thread, one run at a time. The data tier is one SQLite file for users, moderator decisions and training runs, "
     "plus the processed graph, the trained weights and scores, and the experiment JSON files."),
    ("flow", "High-level workflow", "02_high_level_workflow.png",
     "Two lanes: the offline pipeline that builds and trains, and the running application where moderators review and retrain.",
     "Lane A takes the public datasets, builds the graph with the seeded botnets, assembles the 23 node features, trains the baseline and the three GNNs for three seeds on a 60/20/20 split, "
     "keeps the best graph model by validation F1, clusters its embeddings with Louvain and writes the artefacts. Lane B loads those artefacts once, signs the user in, lets them review ranked accounts "
     "and clusters, records confirm or dismiss decisions, retrains on the decisions and reloads the new scores. The retrain step calls the same training code as Lane A, which is how the moderator "
     "feedback loop closes."),
    ("dfd0", "Data flow diagram, level 0", "03_dfd_level0.png",
     "Context diagram (DFD level 0) with the analyst, the moderator and the public datasets.",
     "At level 0 the whole product is one process. The analyst or researcher sends sign-in details and queries and receives scores, reasons, clusters, the graph summary and the model metrics. "
     "The moderator also sends confirm or dismiss decisions and the retrain command, and receives the decision log, the new scores and the F1 before and after retraining. "
     "The public datasets enter only through the graph builder, which reads files from data/raw; no external service is called at run time."),
    ("dfd1", "Data flow diagram, level 1", "04_dfd_level1.png",
     "DFD level 1: seven processes and four data stores.",
     "Level 1 splits the product into seven processes. Process 1.0 authenticates the user and checks the role against the users table (D1). Process 5.0 serves scores, accounts, clusters and metrics from the artefacts (D4) "
     "and joins the moderator decisions from D1; process 6.0 records those decisions. Process 2.0 builds the graph and features from the raw files (D2) into the processed graph (D3), 3.0 trains and evaluates the four models "
     "from D3 and writes weights, scores and metrics to D4, and 4.0 detects botnet clusters and writes clusters.json. Process 7.0 reads the logged decisions from D1 as labels, reuses the training and clustering code and writes new artefacts."),
    ("dfd2", "Data flow diagram, level 2", "05_dfd_level2.png",
     "DFD level 2: the serving process 5.0 expanded into six sub-processes.",
     "Level 2 follows the account and cluster routes. Sub-process 5.1 decodes the bearer token and checks the role. Sub-process 5.2 ranks, filters and pages the accounts by score, status, cluster and search text, "
     "using the stored scores and the served threshold. Sub-process 5.3 joins the latest moderator decision to each account from the reviews table. For one account, 5.4 computes the gradient-times-input explanation through "
     "the loaded GraphSAGE weights and 5.5 builds the neighbourhood from the highest-scoring ties and the links between them. Sub-process 5.6 returns a cluster with its members, shared behaviour and graph from clusters.json."),
    ("uml", "UML class diagram", "06_uml_class.png",
     "UML class diagram: the three database models, the in-memory Store, the routers, and the graph and network classes of the ml package.",
     "User, Review and TrainingRun are the SQLAlchemy models; a user makes many reviews and starts many training runs, and a review records the training run that used it in used_in_run, which is a logical link without a foreign key. "
     "The Store singleton holds the graph, scores, clusters and metrics in memory and offers neighbour lookup, the neighbourhood edges and the gradient-times-input explanation. The routers read the Store and write Review "
     "and TrainingRun rows; the retrain route starts train.fit_all in a thread and then reloads the Store. Net is the two-layer network built from GCN, GraphSAGE or GAT layers over a sparse Graph object."),
    ("seq", "Sequence diagram of the main flow", "07_sequence_flow.png",
     "Sequence diagram: sign in, score and explain an account, record a moderator decision, retrain on the decisions.",
     "The login request is checked against the users table with bcrypt and answered with a signed token. Every later call carries the token, which auth.py decodes before the route reads the Store; "
     "the account detail returns the score, the reasons from the gradient-times-input explanation, the neighbourhood and the decision history. A moderator decision passes require_moderator, which returns 403 for an analyst, "
     "and is stored as a Review row. The retrain request collects the labels from the reviews, records a running TrainingRun, answers 202, and a background thread trains, writes the artefacts, reloads the Store "
     "and finally stores F1 after retraining and marks the used decisions."),
    ("uc", "Use-case diagram", "08_use_case.png",
     "Use-case diagram with the analyst, the moderator (who inherits the analyst's use cases) and the researcher.",
     "Everyone signs in with one of the two demo logins. The analyst can view the overview and the graph and features, browse and search ranked accounts, inspect an account with its reasons and neighbourhood, "
     "explore botnet clusters and compare the models and the scalability results. The moderator can do all of that and also confirm or dismiss an account or a whole cluster, undo a decision that no training run has used, "
     "and start a retraining run. The researcher is a way of using the analyst login for the model comparison, not a separate role in the code."),
    ("er", "ER diagram", "09_er_diagram.png",
     "Entity-relationship diagram: the three SQLite tables and the file-based graph artefacts treated as logical entities.",
     "Only users, reviews and training_runs are database tables. Both reviews and training_runs carry a foreign key user_id to users, and reviews.used_in_run holds the id of the training run that used the decision, "
     "without a database constraint. The graph itself is stored in files: the accounts with their 23 features and labels, the ties (each with an edge_kind of real or injected), the clusters in clusters.json and "
     "the scores of every model in scores.npz. A review points into those files through target_id and the list of member account ids, so a decision on a cluster fans out to every member."),
    ("flowp", "Flowchart of the core pipeline", "10_flowchart_pipeline.png",
     "Flowchart of the core algorithm: build the graph, train four models for three seeds, tune the threshold on validation, serve the best.",
     "The builder keeps the 3,963 real accounts and 88,156 ties, adds eight botnets and 150 lone spammers with a fixed seed, gives each account its profile, posting, timing and interaction features and camouflages "
     "part of the bots, which gives 4,533 accounts and 94,456 ties. Features are standardised and the stratified split is 2,719, 906 and 908 accounts. Each of the four models is trained for seeds 0, 1 and 2 with a "
     "class-weighted loss, early stopping on validation F1 and a threshold tuned on the validation set; test metrics are averaged over the seeds. The graph model with the best validation F1 is served, and its embeddings feed cluster detection."),
    ("flowc", "Flowchart of botnet cluster detection", "11_flowchart_clustering.png",
     "Flowchart of cluster detection: candidates, similarity graph plus real ties, Louvain, size filter, description and the coordinated or diffuse label.",
     "Accounts with a fake-probability of at least 0.30 become candidates. Each candidate is linked to its five most cosine-similar candidates in the 64-dimensional embedding space, and every real tie between two candidates adds "
     "a weight of 1.0. Louvain community detection groups this weighted graph, groups with fewer than five accounts are dropped, and each remaining group is described by its size, mean score, tie density and shared behaviour. "
     "A group with a tie density of at least 5% is labelled coordinated, otherwise diffuse; on the served model this gives nine groups, the eight injected botnets and one loose group of 160 accounts."),
    ("model", "Model architecture", "12_model_architecture.png",
     "Architecture of the node classifiers: two message-passing layers, a linear head, and the layer formulas for the baseline, GCN, GraphSAGE and GAT.",
     "All four models share one shape. The standardised 23 features pass through dropout 0.3, a first layer from 23 to 64 units with ELU, dropout, a second layer from 64 to 64 units with ELU, dropout and a linear layer to two outputs, "
     "followed by a softmax that gives the fake-probability. The output of the second layer is the 64-dimensional embedding used for botnet clustering. The baseline replaces the layers with dense ones that ignore neighbours; "
     "GCN multiplies by the symmetrically normalised adjacency with self-loops; GraphSAGE keeps separate weights for the account itself and the mean of its neighbours; GAT weighs each neighbour with a learned attention."),
]
