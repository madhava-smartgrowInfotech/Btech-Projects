"""System architecture, high-level workflow and DFD level 0 for ForgetSafe (drawn from certified_unlearning/ and frontend/)."""
from __future__ import annotations

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, ROSE_L, Canvas, anchor


def architecture(out):
    c = Canvas(10.4, 8.4)
    # ---- people
    c.zone(1.5, 73.5, 101, 9.5, "People", fc="#f4f5fb")
    c.box(5, 73.9, 44, 5.4, "Operator  (handles a deletion request: trains, removes a client, reads the certificate)", fs=7.0)
    c.box(54, 73.9, 45, 5.4, "Compliance auditor  (reads certificates, verifies the audit hash chain)", fs=7.0)
    # ---- front doors
    c.zone(1.5, 51.5, 101, 18, "Front doors  (all call the same engine)", fc="#eef4fe")
    c.box(4, 53.0, 31, 12.4, "React 19 + Vite UI  (port 5109)\nLanding, Dashboard, Training,\nUnlearning, Explorer, Audit\nfetch('/api/...') via Vite proxy", fs=6.9, fc="white")
    c.box(38, 53.0, 21, 12.4, "Legacy single-page\nUI  (GET /, inline\nHTML + JS in web.py)", fs=6.9, fc="white")
    c.box(62, 53.0, 19, 12.4, "Tkinter desktop\napp.py --desktop\n(gui.py, direct\nengine calls)", fs=6.9, fc="white")
    c.box(84, 53.0, 17, 12.4, "CLI demo\napp.py --demo\n(run_demo, temp\nledger)", fs=6.9, fc="white")
    c.arrow((20, 73.5), (20, 69.5), both=True)
    c.arrow((70, 73.5), (70, 69.5), both=True)
    # ---- API
    c.box(4, 41, 62, 8.5, "stdlib http.server API  (port 8109, JSON, no authentication)\nThreadingHTTPServer - RequestHandler - ApplicationState (RLock)\n"
          "GET /api/health /api/state /api/certificate/latest   POST /api/train /api/session /api/unlearn /api/generate /api/audit/verify",
          fc=INDIGO_L, ec=INDIGO, fs=6.2, bold=False)
    c.arrow((20, 53), (20, 49.5), both=True, label="HTTP + JSON", loff=(7, 0), fs=6.8)
    c.arrow((48, 53), (48, 49.5), both=True)
    c.arrow((71, 53), (71, 38.5), color="#8a93a8", ls="--")
    c.arrow((92.5, 53), (92.5, 38.5), color="#8a93a8", ls="--")
    c.text(81.5, 44.5, "direct calls\n(no HTTP)", fs=6.8, italic=True)
    # ---- engine zone
    c.zone(1.5, 11.5, 101, 27, "FederatedUnlearningEngine  (certified_unlearning/engine.py)  -  one engine per session", fc="#eef8f2")
    c.arrow((35, 41), (35, 38.5), both=True)
    c.box(4, 23.5, 27, 10.5, "Client datasets (dataset.py)\n5 clients x 5 records\nRaw records stay inside the\nclient object", fs=6.7, fc=GREEN_L)
    c.box(34, 23.5, 21, 10.5, "clipped_update()\nbigram counts -> L2 clip\nC = 25  (model.py)", fs=6.7, fc="white")
    c.box(58, 23.5, 21, 10.5, "Noisy aggregate\nsum + N(0, (sigma C)^2)\ndivide by n   (sigma = 3)", fs=6.7, fc="white")
    c.box(82, 23.5, 19, 10.5, "CharacterLanguageModel\n33 x 33 = 1,089 params\nperplexity, accuracy,\nmembership_auc()", fs=6.4, fc="white")
    c.arrow((31, 28.7), (34, 28.7))
    c.arrow((55, 28.7), (58, 28.7))
    c.arrow((79, 28.7), (82, 28.7))
    c.text(52, 21.3, "Only clipped updates cross from a client to the aggregator.", fs=6.9, italic=True)
    c.box(4, 13.3, 52, 5.6, "train() - unlearn() - metrics() - contributions() - generate() - export_certificate()", fs=6.8, fc=INDIGO_L, ec=INDIGO, bold=True)
    c.box(60, 13.3, 41, 5.6, "Tracked state: updates, noise, noisy_sum, certificates", fs=6.6, fc="white")
    # ---- storage
    c.zone(1.5, 0.3, 101, 10.2, "Storage", fc="#fff8e8")
    c.box(5, 1.3, 40, 5.0, "AuditLedger  ->  data/audit_log.jsonl  (SHA-256 chain)", fs=6.8, fc="white")
    c.box(49, 1.3, 24, 5.0, "In-memory engine state", fs=6.8, fc="white")
    c.box(77, 1.3, 22, 5.0, "No SQL database", fs=6.8, fc=ROSE_L, ec="#c98a8a")
    c.arrow((25, 13.3), (25, 6.3), both=True)
    c.arrow((70, 13.3), (62, 6.3), both=True)
    c.save(out)


def workflow(out):
    c = Canvas(10.4, 6.8)
    rows = [
        ("A  Federated training  (POST /api/train)", 49.0, BLUE_L, [
            ("1  Clip", "each client's bigram-\ncount vector, L2\nclip C = 25"),
            ("2  Aggregate", "sum clipped updates,\nadd Gaussian noise\nN(0, (sigma C)^2)"),
            ("3  Normalise", "divide by client count\n-> global model\n(1,089 parameters)"),
            ("4  Record", "metrics: epsilon,\nperplexity, accuracy;\nledger event TRAINING")]),
        ("B  Unlearning request  (POST /api/unlearn)", 27.0, INDIGO_L, [
            ("5  Guard", "trained? known client?\nnot yet removed?\nat least 2 active?"),
            ("6  Subtract", "noisy_sum minus the\nclient's stored\nclipped update"),
            ("7  Rebuild", "drop client from active\nlist; divide by n - 1;\nnew model + hash"),
            ("8  Reference", "retained updates +\nsame noise,\nL2 distance to model")]),
        ("C  Verification, certificate and audit", 5.0, GREEN_L, [
            ("9  Attack", "membership AUC of the\nclient's records,\nbefore and after"),
            ("10  Utility", "perplexity, accuracy,\nretention % of the\nutility score"),
            ("11  Decide", "L2 <= 1e-10 and\nretention >= 70 %\n-> CERTIFIED, else\nREVIEW_REQUIRED"),
            ("12  Certificate", "certificate + ledger\nrecord (hash chain);\nPOST /api/audit/verify\nre-walks the chain")]),
    ]
    xs = [3, 29, 55, 81]
    w, h = 20.5, 15.5
    for title, y, fc, items in rows:
        c.text(101, y + h + 2.3, title, fs=8.4, bold=True, ha="right")
        boxes = []
        for (hd, t), x in zip(items, xs):
            c.box(x, y, w, h, t, fc=fc, fs=7.0)
            c.text(x + w / 2, y + h - 2.1, hd, fs=7.8, bold=True)
            boxes.append({"x": x, "y": y, "w": w, "h": h})
        for a_, b_ in zip(boxes[:-1], boxes[1:]):
            c.arrow(anchor(a_, "r"), anchor(b_, "l"))
    c.path([(91.2, 49.0), (91.2, 47.2), (13.2, 47.2), (13.2, 42.7)], head=True)
    c.path([(91.2, 27.0), (91.2, 25.2), (13.2, 25.2), (13.2, 20.7)], head=True)
    c.save(out)


def dfd0(out):
    c = Canvas(10.4, 5.6)
    c.ellipse(52, 26, 30, 20, "0\nForgetSafe\ncertified federated\nunlearning lab", fc=INDIGO_L, ec=INDIGO, fs=9)
    c.box(1, 14, 20, 24, "Operator\n(UI, desktop or\nCLI user)", fs=8.4, fc=GREEN_L, bold=True)
    c.box(83, 14, 20, 24, "Compliance\nauditor", fs=8.4, fc=GREEN_L, bold=True)
    c.box(41, 45, 22, 7.2, "Built-in client corpus\n(dataset.py)", fs=7.6, fc=AMBER_L)
    c.arrow((52, 45), (52, 36.2), label="client records\n(5 x 5 sentences)", loff=(10.5, 0), fs=7.2)
    c.arrow((21, 31), (39.6, 31), label="session, train, unlearn\n(client_id), generate (seed)", loff=(0, 3.6), fs=7.0)
    c.arrow((39.6, 21), (21, 21), label="session id, metrics,\ncertificate, sample text,\nerrors", loff=(0, -5.2), fs=7.0)
    c.arrow((83, 31), (64.4, 31), label="verify request,\ncertificate request", loff=(0, 3.6), fs=7.0)
    c.arrow((64.4, 21), (83, 21), label="chain status, ledger\nrecords, certificate JSON", loff=(0, -4.6), fs=7.0)
    c.text(52, 4, "Every request is an HTTP call to port 8109 (or a direct engine call from the desktop and CLI front doors).", fs=7.2, italic=True)
    c.save(out)
