"""ER (data model), UML class, use-case and sequence diagrams for ForgetSafe (drawn from certified_unlearning/ and the web API)."""
from __future__ import annotations

from matplotlib.patches import Circle

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, INK, LINE, ROSE_L, Canvas, anchor

LH = 1.22  # line height (canvas units) for 6.2 pt text


def ent_h(n_attrs, subtitle=True):
    return 4.6 + (3.2 if subtitle else 0.6) + n_attrs * LH + 1.4


def entity(c, x, y_top, w, title, attrs, fc, hfc, subtitle=None, fs=6.2):
    h = ent_h(len(attrs), bool(subtitle))
    y = y_top - h
    c.box(x, y, w, h, "", fc=fc, r=1.2)
    c.rect(x, y + h - 4.6, w, 4.6, fc=hfc, ec=INK, lw=1.0, z=2)
    c.text(x + w / 2, y + h - 2.3, title, fs=7.4, bold=True)
    start = y + h - 5.8
    if subtitle:
        c.ax.text(x + w / 2, y + h - 5.4, subtitle, ha="center", va="top", fontsize=5.6, style="italic", color="#44506b")
        start = y + h - 8.4
    for i, t in enumerate(attrs):
        c.ax.text(x + 1.2, start - i * LH, t, ha="left", va="top", fontsize=fs, color=INK)
    return {"x": x, "y": y, "w": w, "h": h}


def card(c, x, y, text):
    c.text(x, y, text, fs=6.8, bold=True, color=INDIGO)


def er(out):
    c = Canvas(10.4, 7.8)
    cd = entity(c, 2, 70, 26, "CLIENT_DATASET", ["PK client_id", "display_name", "domain", "records  (5 sentences)"], "white", "#d9f2e4", subtitle="built-in corpus, dataset.py")
    se = entity(c, 40, 71, 25, "SESSION", ["PK session_id  (uuid4)", "random_seed", "clip_norm  (25.0)", "noise_multiplier  (3.0)", "delta  (1e-5)"], "white", "#dbe8fb",
                subtitle="FederatedUnlearningEngine")
    cu = entity(c, 2, 48, 26, "CLIENT_UPDATE", ["PK,FK session_id", "PK,FK client_id", "update[1089]  (clipped)", "original_norm", "clip_scale", "active"], "white", "#dbe8fb",
                subtitle="engine.updates + update_metadata")
    gm = entity(c, 40, 48, 25, "GLOBAL_MODEL", ["PK,FK session_id", "noise[1089]", "noisy_sum[1089]", "parameters[1089]", "smoothing  (0.15)", "model_hash"], "white", "#dbe8fb",
                subtitle="in memory")
    ce = entity(c, 76, 70, 27, "UNLEARNING_CERTIFICATE",
                ["PK certificate_id", "FK session_id", "FK client_id", "client_name, issued_at_utc", "status, method", "epsilon, delta", "clip_norm, noise_multiplier",
                 "residual_influence_l2", "reference_retrain_l2", "membership_auc_before / _after", "perplexity_before / _after", "accuracy_before / _after",
                 "utility_retention_percent", "clients_before / _after", "model_hash_before / _after", "FK audit_record_hash"],
                "white", "#dbe8fb", subtitle="in memory (certificates list)", fs=5.9)
    au = entity(c, 32, 19, 38, "AUDIT_RECORD", ["PK sequence", "event_type  (FEDERATED_TRAINING | CLIENT_UNLEARNING)", "timestamp_utc, session_id, event fields",
                                                "previous_hash", "record_hash  = sha256(previous_hash | canonical record)"], "white", "#fbebc8",
                subtitle="persisted: data/audit_log.jsonl", fs=5.9)
    # relationships
    c.line((15, cd["y"]), (15, cu["y"] + cu["h"]))
    card(c, 13.2, cd["y"] - 1.6, "1"); card(c, 13.2, cu["y"] + cu["h"] + 1.6, "N")
    c.text(21.5, (cd["y"] + cu["y"] + cu["h"]) / 2, "produces\n(one per session)", fs=6.0, italic=True)
    c.path([(40, 64), (34, 64), (34, 42), (28, 42)], head=False)
    card(c, 38.0, 65.5, "1"); card(c, 30.0, 43.6, "N")
    c.text(36.2, 53, "has", fs=6.2, italic=True)
    c.line((52, se["y"]), (52, gm["y"] + gm["h"]))
    card(c, 50.2, se["y"] - 1.6, "1"); card(c, 50.2, gm["y"] + gm["h"] + 1.6, "1")
    c.text(57, (se["y"] + gm["y"] + gm["h"]) / 2, "owns", fs=6.2, italic=True)
    c.line((65, 60), (76, 60))
    card(c, 67, 61.5, "1"); card(c, 74.4, 61.5, "N")
    c.text(70.5, 57.6, "issues", fs=6.2, italic=True)
    c.path([(15, 70), (15, 74.2), (89, 74.2), (89, 70)], head=False)
    card(c, 16.8, 72.4, "1"); card(c, 87.2, 72.4, "N")
    c.text(52, 75.4, "is the removed client of", fs=6.2, italic=True)
    c.path([(80, ce["y"]), (80, 11.5), (70, 11.5)], head=False)
    card(c, 78.2, ce["y"] - 1.6, "1"); card(c, 71.8, 13.0, "1")
    c.text(88, 30, "audit_record_hash\nlinks the two", fs=6.0, italic=True)
    c.path([(65, 55), (68, 55), (68, au["y"] + au["h"])], head=False, ls="--")
    card(c, 66.4, 56.5, "1"); card(c, 69.8, au["y"] + au["h"] + 1.6, "N")
    c.text(70.5, 40, "session_id inside\neach event\n(no foreign key)", fs=5.8, italic=True, ha="left")
    c.path([(32, 15), (28, 15), (28, 8), (32, 8)], head=True)
    c.text(14.5, 11.5, "previous_hash = record_hash of\nthe record before (sequence - 1);\nthe first record uses 64 zeros", fs=6.0, italic=True)
    # legend
    c.box(84, 3, 19, 22, "", fc="white", ec="#9aa5ba", ls="--")
    c.text(93.5, 22.5, "No SQL database", fs=7.0, bold=True)
    c.text(93.5, 12, "Blue entities live in the\nengine's memory and vanish\nwith the process; green is\nthe built-in corpus. Only\nAUDIT_RECORD is written to\ndisk (one JSON line each).", fs=5.9)
    c.save(out)


def class_h(attrs, methods, stereo):
    return 4.4 + (1.0 if stereo else 0) + 0.6 + len(attrs) * 1.16 + 1.2 + len(methods) * 1.16 + 0.8


def class_box(c, x, y_top, w, name, attrs, methods, stereo=None, fs=5.9, hfc="#dbe8fb"):
    lh = 1.16
    h = class_h(attrs, methods, stereo)
    y = y_top - h
    c.box(x, y, w, h, "", fc="white", r=0.8)
    hh = 4.4 + (1.0 if stereo else 0)
    c.rect(x, y_top - hh, w, hh, fc=hfc, ec=INK, lw=1.0, z=2)
    if stereo:
        c.text(x + w / 2, y_top - 1.3, stereo, fs=5.4, italic=True)
        c.text(x + w / 2, y_top - 3.4, name, fs=7.0, bold=True)
    else:
        c.text(x + w / 2, y_top - 2.2, name, fs=7.0, bold=True)
    ty = y_top - hh - 0.6
    for i, t in enumerate(attrs):
        c.ax.text(x + 0.9, ty - i * lh, t, ha="left", va="top", fontsize=fs, color=INK)
    sep = ty - len(attrs) * lh - 0.1
    c.line((x, sep), (x + w, sep), lw=0.8)
    for i, t in enumerate(methods):
        c.ax.text(x + 0.9, sep - 0.5 - i * lh, t, ha="left", va="top", fontsize=fs, color=INK)
    return {"x": x, "y": y, "w": w, "h": h, "top": y_top}


def uml(out):
    c = Canvas(10.4, 8.0)
    T = 79
    cd = class_box(c, 2, T, 24, "ClientDataset", ["client_id: str", "display_name: str", "domain: str", "records: tuple[str, ...]"], [], stereo="frozen dataclass", hfc="#d9f2e4")
    tm = class_box(c, 29, T, 24, "TrainingMetrics", ["active_clients: int", "epsilon: float", "delta: float", "perplexity: float", "next_character_accuracy: float", "utility_score: float", "model_hash: str"], [],
                   stereo="frozen dataclass")
    cc = class_box(c, 56, T, 22, "ClientContribution", ["client_id, display_name, domain", "record_count: int", "original_norm: float", "clipped_norm: float", "clip_scale: float", "active: bool"], [],
                   stereo="frozen dataclass")
    cert = class_box(c, 80, T, 23, "UnlearningCertificate",
                     ["certificate_id: str", "session_id, client_id: str", "client_name: str", "issued_at_utc: str", "status: str", "method: str", "epsilon, delta: float", "clip_norm: float",
                      "noise_multiplier: float", "residual_influence_l2: float", "reference_retrain_l2: float", "membership_auc_before/after", "perplexity_before/after", "accuracy_before/after",
                      "utility_retention_percent", "clients_before/after: int", "model_hash_before/after: str", "audit_record_hash: str"], ["to_dict() -> dict"], stereo="frozen dataclass")
    eng_top = min(tm["y"], cc["y"]) - 8
    eng = class_box(c, 29, eng_top, 49, "FederatedUnlearningEngine",
                    ["clients: dict[str, ClientDataset]", "audit: AuditLedger", "clip_norm, noise_multiplier, delta: float", "random_seed: int;  session_id: str",
                     "updates: dict[str, list[float]]", "update_metadata: dict[str, (norm, scale)]", "active_client_ids: list[str]", "noise, noisy_sum: list[float]",
                     "model: CharacterLanguageModel | None", "certificates: list[UnlearningCertificate]"],
                    ["train() -> TrainingMetrics", "metrics() -> TrainingMetrics", "contributions() -> list[ClientContribution]", "unlearn(client_id) -> UnlearningCertificate",
                     "generate(seed_text, length) -> str", "export_certificate(certificate, path)", "epsilon, trained  (properties)", "_rebuild_model();  _reference_parameters(ids)"])
    lm = class_box(c, 2, eng_top - 4, 24, "CharacterLanguageModel", ["parameters: list[float]  (1,089)", "smoothing: float = 0.15"],
                   ["negative_log_likelihood(text)", "perplexity(records)", "next_character_accuracy(records)", "generate(seed, length, seed)", "_row_probabilities(char)"], stereo="model.py")
    c.text(14, lm["y"] - 3.2, "module functions in model.py:\nraw_update(), clipped_update(),\nmembership_auc()", fs=5.8, italic=True)
    row2 = eng["y"] - 8
    al = class_box(c, 56, row2, 22, "AuditLedger", ["path: Path"], ["read_all() -> list[dict]", "append(event) -> dict", "verify() -> (bool, str)"], stereo="audit.py")
    st = class_box(c, 29, row2, 23, "ApplicationState", ["audit_path: Path", "engine: FederatedUnlearningEngine", "lock: RLock"], ["snapshot() -> dict"], stereo="web.py")
    rh = class_box(c, 2, row2, 24, "RequestHandler", ["server_version: str"], ["do_GET()", "do_POST()", "_json(payload, status, headers)", "_body() -> dict", "log_message(format, *args)"],
                   stereo="BaseHTTPRequestHandler")
    note_top = row2
    c.box(81, row2 - 12, 22, 12, "UnlearningApp (gui.py, Tk)\nand run_demo() (app.py)\ncall the engine directly:\nno HTTP, no ApplicationState", fs=6.0, fc=GREY_L, ec="#9aa5ba", ls="--")
    # ---- relationships
    ye = eng["y"] + eng["h"] - 2.4
    c.path([(14, cd["y"]), (14, ye), (29, ye)], head=False)
    c.ax.text(28.2, ye, "◇", fontsize=9, ha="center", va="center", color=INK)
    c.text(17.5, cd["y"] - 2.2, "2..*", fs=6.2, bold=True, color=INDIGO)
    c.text(21.2, ye + 1.8, "clients", fs=6.0, italic=True)
    ym = lm["y"] + lm["h"] - 8
    c.line((26, ym), (29, ym))
    c.ax.text(28.6, ym, "◆", fontsize=8, ha="center", va="center", color=INK)
    c.text(27.6, ym + 1.7, "0..1", fs=6.0, bold=True, color=INDIGO)
    c.text(27.6, ym - 1.8, "model", fs=6.0, italic=True)
    c.line((66, eng["y"]), (66, al["top"]))
    c.ax.text(66, eng["y"] + 0.9, "◆", fontsize=8, ha="center", va="center", color=INK)
    c.text(68.6, eng["y"] - 1.9, "1", fs=6.2, bold=True, color=INDIGO)
    c.text(62.4, eng["y"] - 2.6, "audit", fs=6.0, italic=True)
    ya = eng["y"] + eng["h"] - 12
    c.path([(78, ya), (91.5, ya), (91.5, cert["y"])], head=True)
    c.text(94.2, cert["y"] - 1.8, "0..*", fs=6.2, bold=True, color=INDIGO)
    c.text(84, ya + 1.6, "certificates", fs=6.0, italic=True)
    c.arrow((40, eng["y"] + eng["h"]), (40, tm["y"]), ls="--", head=True)
    c.text(46.5, (eng["y"] + eng["h"] + tm["y"]) / 2, "<<creates>>", fs=5.8, italic=True)
    c.arrow((70, eng["y"] + eng["h"]), (70, cc["y"]), ls="--", head=True)
    c.text(75.6, (eng["y"] + eng["h"] + cc["y"]) / 2, "<<creates>>", fs=5.8, italic=True)
    c.arrow((40.5, st["top"]), (40.5, eng["y"]), head=True)
    c.text(44.5, (st["top"] + eng["y"]) / 2, "1  engine", fs=6.0, italic=True)
    c.arrow((26, st["top"] - 6), (29, st["top"] - 6), head=True)
    c.text(27.5, st["top"] - 4.2, "uses", fs=5.8, italic=True)
    c.save(out)


def actor(c, x, y, label):
    c.ax.add_patch(Circle((x, y + 8.5), 1.6, fc="white", ec=INK, lw=1.2))
    c.line((x, y + 6.9), (x, y + 2.6))
    c.line((x - 3, y + 5.3), (x + 3, y + 5.3))
    c.line((x, y + 2.6), (x - 2.4, y - 0.4))
    c.line((x, y + 2.6), (x + 2.4, y - 0.4))
    c.text(x, y - 3.4, label, fs=7.4, bold=True)


def usecase(out):
    c = Canvas(10.4, 7.6)
    c.rect(14, 1.5, 78, 70, fc="#fbfcff", ec="#9aa5ba", lw=1.2, ls="--")
    c.text(53, 69, "ForgetSafe  (React UI, legacy UI, desktop and CLI front doors)", fs=8.0, bold=True)
    actor(c, 7, 36, "Operator")
    actor(c, 98, 36, "Compliance\nauditor")
    uc = {"start": (28, 60, "Start new session"), "train": (28, 50, "Train federated model"), "gen": (28, 25, "Generate sample text"),
          "dash": (28, 15, "View dashboard and\nclient contributions"),
          "unl": (54, 27, "Request client\nunlearning"), "cert": (54, 46, "View verification\ncertificate"), "down": (54, 37, "Download certificate\nJSON"),
          "ledger": (79, 60, "Browse audit ledger"), "verify": (79, 50, "Verify audit hash chain"),
          "check": (40, 6.5, "Run verification checks\n(attack, reference, utility)"), "append": (69, 6.5, "Append audit record\n(training and unlearning)")}
    for key, (x, y, t) in uc.items():
        fc = INDIGO_L if key in ("unl", "train", "start", "gen", "dash") else (GREEN_L if key in ("cert", "down", "ledger", "verify") else AMBER_L)
        c.ellipse(x, y, 24, 7.4, t, fc=fc, fs=6.6)
    for k in ("start", "train", "gen", "dash", "unl", "cert", "down"):
        x, y, _ = uc[k]
        c.line((11, 40), (x - 12, y), color="#6a7490", lw=1.0)
    for k in ("ledger", "verify", "cert", "down"):
        x, y, _ = uc[k]
        c.line((94.5, 40), (x + 12, y), color="#6a7490", lw=1.0)
    c.arrow((50, 23.3), (43.5, 10.2), ls="--")
    c.text(42.5, 18.0, "<<include>>", fs=6.0, italic=True)
    c.arrow((58, 23.3), (65.5, 10.2), ls="--")
    c.text(67.2, 18.0, "<<include>>", fs=6.0, italic=True)
    c.box(68, 14, 23.5, 17, "The desktop (Tkinter) and CLI demo give the\nOperator the same use cases. The auditor\nneeds only read access:\nGET /api/certificate/latest,\nPOST /api/audit/verify, ledger in /api/state.\nTraining also appends an audit record.",
          fs=5.9, fc="white", ec="#c8cfe0", ls="--")
    c.save(out)


def sequence(out):
    c = Canvas(10.4, 8.6)
    xs = {"op": 8, "ui": 25, "api": 43, "eng": 62, "mod": 80, "led": 97}
    names = {"op": "Operator", "ui": "React UI\n(port 5109)", "api": "API\nweb.py (8109)", "eng": "Federated-\nUnlearningEngine", "mod": "Character-\nLanguageModel", "led": "AuditLedger\n(JSONL file)"}
    for k, x in xs.items():
        c.box(x - 7, 79, 14, 6.4, names[k], fs=6.3, fc=GREEN_L if k == "op" else (INDIGO_L if k in ("ui", "api") else BLUE_L), bold=True)
        c.line((x, 79), (x, 1.5), color="#9aa5ba", lw=1.0, ls="--")
    steps = [("Train", [
        ("op", "ui", "click Train federated model", False), ("ui", "api", "POST /api/train", False), ("api", "eng", "train()", False),
        ("eng", "eng", "clip, sum, noise, divide by n", False), ("eng", "mod", "build model; perplexity, accuracy", False),
        ("eng", "led", "append(FEDERATED_TRAINING)", False), ("api", "ui", "TrainingMetrics JSON", True)]),
        ("Unlearn", [
            ("op", "ui", "pick client, confirm", False), ("ui", "api", "POST /api/unlearn {client_id}", False), ("api", "eng", "unlearn(client_id)", False),
            ("eng", "mod", "metrics + membership_auc (before)", False), ("eng", "eng", "subtract update, rebuild, reference L2", False),
            ("eng", "mod", "metrics + membership_auc (after)", False), ("eng", "led", "append(CLIENT_UNLEARNING)", False), ("api", "ui", "UnlearningCertificate JSON", True)]),
        ("Verify", [
            ("op", "ui", "click Verify hash chain", False), ("ui", "api", "POST /api/audit/verify", False), ("api", "led", "verify()", False),
            ("led", "api", "(valid, detail)", True), ("api", "ui", "{valid, detail}", True)])]
    y = 76.0
    step = 3.2
    bands = []
    for title, msgs in steps:
        top = y + 1.9
        for (a, b, t, ret) in msgs:
            xa, xb = xs[a], xs[b]
            if a == b:
                y -= 0.4
                c.path([(xa, y), (xa + 5, y), (xa + 5, y - 1.9), (xa, y - 1.9)], head=True)
                c.text(xa + 6.2, y - 0.95, t, fs=6.3, ha="left")
                y -= 1.5
            else:
                c.arrow((xa, y), (xb, y), ls="--" if ret else "-", lw=1.1, label=t, loff=(0, 1.5), fs=6.3)
            y -= step
        bands.append((title, top, y + step - 1.1))
        y -= 1.6
    for title, top, bottom in bands:
        c.text(103, top - 0.8, title, fs=7.4, bold=True, ha="right", color=INDIGO)
        c.line((1, bottom - 0.3), (103, bottom - 0.3), color="#c8cfe0", lw=0.8, ls=":")
    c.save(out)
