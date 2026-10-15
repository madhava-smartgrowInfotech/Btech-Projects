"""Chapter 5 (System Design) sections and the diagram helper used by the block-diagram document."""
from __future__ import annotations

from doc_common import DIAG, SHOTS

ORDER = ["architecture", "workflow", "dfd0", "dfd1", "dfd2", "usecase", "sequence", "er", "uml", "flowchart"]

FILES = {"architecture": "01_system_architecture.png", "workflow": "02_high_level_workflow.png", "dfd0": "03_dfd_level0.png",
         "dfd1": "04_dfd_level1.png", "dfd2": "05_dfd_level2.png", "er": "06_er_diagram.png", "uml": "07_uml_class_diagram.png",
         "usecase": "08_use_case_diagram.png", "sequence": "09_sequence_diagram.png", "flowchart": "10_algorithm_flowchart.png"}

CAPTION = {
    "architecture": "System architecture of PhishGuard",
    "workflow": "High-level workflow: from dataset to a self-refining detector",
    "dfd0": "Data-flow diagram, level 0 (context)",
    "dfd1": "Data-flow diagram, level 1",
    "dfd2": "Data-flow diagram, level 2 (the check path)",
    "usecase": "Use-case diagram",
    "sequence": "Sequence diagram: check a URL, report it, refine the model",
    "er": "Entity-relationship diagram",
    "uml": "UML class diagram of the Python modules",
    "flowchart": "Flowchart of the core algorithm (decision order of detector.check)",
}

WIDTH = {"architecture": 5.6, "workflow": 5.6, "dfd0": 5.4, "dfd1": 5.8, "dfd2": 5.8, "usecase": 4.6, "sequence": 5.6, "er": 5.6, "uml": 5.7, "flowchart": 4.6}

TEXT = {
    "architecture": [
        "The architecture has four layers. Users reach the system through the React interface on port 5103 or the command line. The Vite dev server "
        "serves the seven pages and proxies every /api call to the Flask application on port 8103, so the browser talks to one origin. "
        "backend/server.py wraps the original Flask application (phishguard.webapp) without changing it and adds five read-only JSON endpoints and "
        "the CORS header.",
        "Behind the API are six modules. Features turns a URL into 47 numbers; Detector applies the decision order; ThreatIntel stores reports and "
        "computes consensus; Train fits and compares the models; Retrain merges confirmed URLs into the training data; and the original pages module "
        "keeps the first Flask interface alive. Storage is local: the SQLite file threat_intel.db, the model files and metrics.json, and the dataset CSV. "
        "The two public feeds are the only external systems, and they are optional."],
    "workflow": [
        "The workflow has two halves. In the upper row the system is prepared once: the 40,000-URL dataset is loaded, 47 features are extracted, the "
        "three classifiers are trained and compared on the same split, and the best by F1 is saved and loaded by the detector. In the lower row the "
        "system is used and improved: a URL is checked, the community reports it, confirmed URLs retrain the models, and the detector hot-reloads the new "
        "model. The dashed arrow shows that the refined model serves the next check, so the cycle repeats.",
        "The note at the top records a design choice that makes the loop practical: all features are computed offline from the URL string, so the code "
        "that extracts features for training is identical to the code that runs at check time."],
    "dfd0": [
        "The context diagram shows PhishGuard as one process and four external entities. The analyst sends URLs and receives verdicts, probabilities, red "
        "flags and the activity log. The community reporter sends reports (URL, phishing or safe, reporter, note) and receives the vote tally and status. "
        "The maintainer sends retrain and sync commands and receives metrics and retrain status. The public threat feeds supply newly listed phishing URLs. "
        "The analyst and the reporter are often the same person; they are drawn separately because they use different pages."],
    "dfd1": [
        "Level 1 splits the system into seven processes and five data stores. Processes 1.0 to 3.0 form the check path: the URL is normalised and turned "
        "into features, scored by the model loaded from D4, and combined with the community status from D1 to give the verdict, which is logged in D2. "
        "Process 4.0 records a report and computes consensus in D1. Process 5.0 imports feed URLs as trusted reports. Process 6.0 reads confirmed URLs "
        "from D1 and the base data from D3, retrains, and writes new models to D4 and metrics to D5. Process 7.0 presents the metrics, activity and "
        "statistics to the maintainer. D4 is drawn twice only to keep the lines short."],
    "dfd2": [
        "Level 2 opens the check path. 1.1 normalises the URL (scheme, lower-case host, no www.). 1.2 extracts the 47 features. 2.1 scores them with the "
        "best model. 3.1 looks up the community store for the URL and for its host. 3.2 applies the reputation discount (x0.4 for well-known registered "
        "domains) and the pending-vote adjustment (+/-0.15 per net vote). 3.3 applies the thresholds 0.35 and 0.60. 3.4 builds the red flags and the "
        "reason text from the features. 3.5 writes a row to the checks log. A confirmed community verdict skips 2.1 to 3.3, as the flowchart shows."],
    "usecase": [
        "The use-case diagram has four actors. The analyst checks a URL or a batch, reads the red flags and the reason, and reviews the activity log. "
        "The community reporter reports a URL and views the threat-intelligence board; reporting includes confirmation by consensus. Checking a URL "
        "includes applying a confirmed verdict over the model. The maintainer compares the models, retrains them and synchronises the public feeds, "
        "and the feeds themselves act on the confirmation use case. The note records that there is no sign-in, so any user can act in any role."],
    "sequence": [
        "The sequence diagram has three parts. In part A the user presses Check; the React page calls GET /api/check; Flask asks the Detector, which "
        "extracts features, queries ThreatIntel for the URL and its host, asks the model for a probability, applies the decision rules, logs the check "
        "and returns the result. In part B a report is posted, ThreatIntel inserts it, updates the vote counts and recomputes consensus, and the API may "
        "start an automatic retrain after 25 new confirmations. In part C a retrain fits the three models, bumps the version and tells the Detector to "
        "reload the best model."],
    "er": [
        "The database has three tables in threat_intel.db. reports stores every individual report (URL, verdict, reporter, source, note, time) and is "
        "indexed on the normalised URL. intel holds one row per normalised URL with its phishing and safe vote counts, its status (pending, "
        "confirmed_phishing or confirmed_safe), its source, first-seen and last-updated times and a flag showing whether it has been used in training. "
        "checks is an append-only log of every verdict. reports and intel are linked logically by the normalised URL; the schema declares no SQL foreign "
        "key. The lower panel shows the three file-based stores that the pipeline reads and writes."],
    "uml": [
        "The class diagram shows the Python structure. ThreatIntel is the only real class with state (the database path). Detector holds a ThreatIntel, "
        "the loaded model, its name and version, and a lock that protects the model while it is swapped. features, train, retrain, data and config are "
        "modules of functions and constants, drawn as <<module>> classes. webapp and backend.server create the Flask application and call "
        "Detector.check. retrain calls train_all and load_dataset, and uses ThreatIntel's training_examples and mark_trained."],
    "flowchart": [
        "The flowchart is the decision procedure of Detector.check. An empty URL is rejected with HTTP 400. Otherwise the URL is normalised, 47 features "
        "and the red flags are extracted, and the community store is queried for the URL and for its host. A confirmed community entry decides at once: "
        "confirmed phishing gives probability max(0.97, model) and confirmed safe gives min(0.03, model). Otherwise the model produces p; a well-known "
        "registered domain multiplies p by 0.4; pending votes add 0.15 per net vote; and p is compared with 0.60 (phishing) and 0.35 (suspicious). "
        "Every outcome is logged and returned with its reason."],
}


def diagram(d, key, width=None):
    d.figure(DIAG / FILES[key], CAPTION[key], width=width or WIDTH[key], max_h=6.4 if key in ("sequence", "uml", "flowchart", "usecase") else 5.0)
    for t in TEXT[key]:
        d.p(t)


# ---------------------------------------------------------------- Chapter 5 sections
def sec_arch(d):
    d.h2("System Architecture")
    d.p("PhishGuard is a three-tier local application: a React interface, a Flask API with the detection modules, and local storage. The "
        "detection modules are ordinary Python code, so the same pipeline is reachable from the web interface, the original Flask pages and the command line.")
    diagram(d, "architecture")


def sec_workflow(d):
    d.h2("High-Level Workflow")
    diagram(d, "workflow")


def sec_dfd(d):
    d.h2("Data-Flow Diagrams")
    d.p("The data-flow diagrams follow the usual levelling: a context diagram, a level-1 decomposition and a level-2 expansion of the check path.")
    diagram(d, "dfd0")
    diagram(d, "dfd1")
    diagram(d, "dfd2")


def sec_uml(d):
    d.h2("UML Diagrams")
    d.p("Four behavioural and structural diagrams describe the system: use cases, a sequence of the main flow, the class structure and the "
        "flowchart of the core algorithm.")
    diagram(d, "usecase")
    diagram(d, "sequence")
    diagram(d, "uml")
    diagram(d, "flowchart")


def sec_database(d):
    d.h2("Database Design")
    diagram(d, "er")
    d.table([["Table", "Column", "Type", "Notes"],
             ["reports", "id", "INTEGER", "primary key, autoincrement"],
             ["", "url_norm, url", "TEXT", "normalised and original URL; index idx_reports_url on url_norm"],
             ["", "verdict", "TEXT", "CHECK in ('phishing', 'safe')"],
             ["", "reporter, source, note", "TEXT", "defaults: 'anonymous', 'community'"],
             ["", "created_at", "TEXT", "UTC ISO time"],
             ["intel", "url_norm", "TEXT", "primary key"],
             ["", "url", "TEXT", "first original form"],
             ["", "phishing_votes, safe_votes", "INTEGER", "default 0"],
             ["", "status", "TEXT", "pending | confirmed_phishing | confirmed_safe"],
             ["", "source, first_seen, last_updated", "TEXT", "source is community or the feed name"],
             ["", "used_in_training", "INTEGER", "1 after a retrain has consumed the entry"],
             ["checks", "id, url, verdict, probability, decided_by, created_at", "INTEGER, TEXT, REAL", "append-only activity log"]],
            "Schema of the SQLite database (phishguard/threat_intel.py)", widths=[0.12, 0.36, 0.17, 0.35], font=9)
    d.p("Each connection is opened per operation with a 30-second timeout and committed on exit, so the Flask worker threads and the background retrain thread "
        "do not share a connection. All statements use bound parameters.")


def sec_modules(d):
    d.h2("Module Design")
    d.table([["Module", "File", "Responsibility", "Main functions"],
             ["Features", "phishguard/features.py", "URL normalisation, 47 features, red flags", "normalize_url, extract_features, featurize_urls, explain_features"],
             ["Data", "phishguard/data.py", "Load, clean and split the dataset", "load_dataset, build_matrices, dataset_summary"],
             ["Train", "phishguard/train.py", "Fit, evaluate and save three models; metrics.json", "build_models, evaluate, train_all, load_metrics"],
             ["ThreatIntel", "phishguard/threat_intel.py", "Reports, votes, consensus, feed sync, check log", "report, lookup, lookup_host, sync_feeds, stats"],
             ["Detector", "phishguard/detector.py", "Decision order and hot reload", "check, ml_probability, reload"],
             ["Retrain", "phishguard/retrain.py", "Merge confirmed URLs and retrain", "retrain, maybe_auto_retrain"],
             ["Web app", "phishguard/webapp.py", "Original Flask pages and the JSON API", "create_app"],
             ["API layer", "backend/server.py", "Adds five read-only endpoints and CORS; port 8103", "build_app"],
             ["CLI", "run.py", "train, check, report, sync, retrain, serve, download", "cmd_*"],
             ["Frontend", "frontend/src", "Seven pages, components, API client", "pages/*.jsx, lib/api.js"]],
            "Module breakdown", widths=[0.13, 0.22, 0.34, 0.31], font=9)


def sec_ui(d):
    d.h2("User Interface Design")
    d.p("The interface is a React single-page application with a landing page and a six-item side navigation (Check URL, Report, Threat "
        "intelligence, Models, Activity, Landing page). Colour carries meaning consistently: red for phishing, amber for suspicious, green for safe. "
        "Every result shows a probability gauge and a risk scale with the two thresholds marked, so the user sees how close a verdict is to the "
        "boundary. A light and a dark theme are available.")
    d.figure(SHOTS / "03_check_phishing.png", "Check URL screen: verdict, probability gauge and risk scale", width=5.3)
    d.figure(SHOTS / "12_models_full.png", "Models screen: comparison, confusion matrix and feature importances", width=3.6, max_h=6.2)
    d.bullets(["**Check URL.** Single and batch tabs; example URLs; verdict card; red flags; community status; the 47 extracted features; recent checks.",
               "**Report.** URL, phishing or safe, reporter name and note, with the consensus rule explained beside the form.",
               "**Threat intelligence.** Counters, a searchable table with status and vote columns, a detail drawer and a feed-sync dialog.",
               "**Models.** Metric cards, bar and radar charts, comparison table, confusion matrix, top-10 feature importances and the retrain control.",
               "**Activity.** Check log with a probability trend, verdict mix and search.",
               "**States.** Loading skeletons, empty states and a clear message when the backend is unreachable."])
