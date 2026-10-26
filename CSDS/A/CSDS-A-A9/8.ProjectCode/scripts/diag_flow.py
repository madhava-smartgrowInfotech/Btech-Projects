"""DFD level 1, DFD level 2 and the flowchart of unlearn() for ForgetSafe (drawn from certified_unlearning/engine.py and web.py)."""
from __future__ import annotations

from diagram_kit import AMBER_L, BLUE_L, GREEN_L, GREY_L, INDIGO, INDIGO_L, ROSE_L, Canvas, anchor


def store(c, cx, cy, w, h, text, fc=AMBER_L, fs=6.8):
    """Open-ended data-store symbol: two horizontal lines and a label."""
    c.rect(cx - w / 2, cy - h / 2, w, h, fc=fc, ec="none")
    c.line((cx - w / 2, cy + h / 2), (cx + w / 2, cy + h / 2), color="#1b2238", lw=1.3)
    c.line((cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), color="#1b2238", lw=1.3)
    c.line((cx - w / 2, cy + h / 2), (cx - w / 2, cy - h / 2), color="#1b2238", lw=1.3)
    c.text(cx, cy, text, fs=fs)


def bipath(c, pts, label=None, seg=0, loff=(0, 1.6), fs=6.5):
    """Poly-line with arrow heads at both ends."""
    c.path(pts, label=label, seg=seg, loff=loff, fs=fs)
    c.arrow(pts[1], pts[0])


def dfd1(out):
    """Planar layout: P2 (left) and P4 (right) are joined by four store routes D1, D2, D3, D5 (top to bottom);
    Operator, P1, P3, P5 sit in the face between the D2 and D3 routes; P6, D4 and the auditor sit below the D5 route."""
    c = Canvas(11.0, 9.8)
    # entities
    c.box(31, 48, 12, 8, "Operator", fc=GREEN_L, fs=7.6, bold=True)
    c.box(4, 1, 22, 8, "Compliance auditor", fc=GREEN_L, fs=7.2, bold=True)
    # processes
    c.ellipse(37, 67, 20, 11, "1\nManage\nsession", fc=INDIGO_L, fs=7.0)
    c.ellipse(13, 52, 22, 13, "2\nFederated\ntraining", fc=INDIGO_L, fs=7.2)
    c.ellipse(37, 36.5, 20, 11, "5\nGenerate\nsample text", fc=INDIGO_L, fs=7.0)
    c.ellipse(71, 52, 18, 13, "3\nUnlearn\nclient", fc=INDIGO_L, fs=7.2)
    c.ellipse(97, 52, 20, 13, "4\nVerify and\ncertify", fc=INDIGO_L, fs=7.2)
    c.ellipse(60, 5.5, 22, 9, "6  Audit ledger and\ncertificate export", fc=INDIGO_L, fs=6.5)
    # stores (one box each)
    store(c, 60, 92, 22, 6, "D1  Client datasets", fs=6.4)
    store(c, 60, 80, 22, 6, "D2  Clipped updates + noise", fs=6.0)
    store(c, 60, 27, 22, 6, "D3  Global model", fs=6.4)
    store(c, 60, 16, 22, 6, "D5  Audit ledger (JSONL)", fs=6.2)
    store(c, 101, 29.5, 10, 7, "D4\nCertificates", fs=5.8)
    # Operator <-> processes (short straight arrows)
    bipath(c, [(37, 56), (37, 61.5)], label="new session / id", loff=(9, 0), fs=6.0)
    bipath(c, [(31, 52), (24, 52)], label="train /\nmetrics", loff=(0, 3.4), fs=5.8)
    bipath(c, [(37, 48), (37, 42)], label="seed / sample", loff=(9, 0), fs=6.0)
    bipath(c, [(43, 52), (62, 52)], label="client_id / certificate", loff=(0, 1.8), fs=6.0)
    # process 2 (training): D1 -> P2, P2 -> D2, D3, D5
    c.path([(49, 92), (5, 92), (5, 56.5)], label="records", seg=0, loff=(0, 1.6), fs=6.0)
    c.path([(13, 58.5), (13, 80), (49, 80)], label="clipped updates + noise", seg=1, loff=(2, 1.6), fs=6.0)
    c.path([(13, 45.5), (13, 27), (49, 27)], label="global model", seg=1, loff=(2, 1.6), fs=6.0)
    c.path([(7, 46.5), (7, 16), (49, 16)], label="FEDERATED_TRAINING event", seg=1, loff=(2, -1.6), fs=6.0)
    # process 5 (sample text)
    c.arrow((51, 30), (45, 33.5), label="model", loff=(1.5, 2.3), fs=6.0)
    # process 3 (unlearn)
    bipath(c, [(68, 77), (70, 58.5)], label="tracked update", loff=(-7.5, 0), fs=6.0)
    c.arrow((70, 45.5), (68, 30), label="rebuilt model", loff=(8.5, 0), fs=6.0)
    c.arrow((80, 52), (87, 52))
    # process 4 (verify and certify): reads D1, D2, D3; writes D4, D5
    c.path([(71, 92), (102, 92), (102, 57.6)], label="records (membership attack)", seg=0, loff=(0, 1.6), fs=6.0)
    c.path([(71, 80), (91, 80), (91, 57.2)], label="retained updates + noise", seg=0, loff=(0, 1.6), fs=6.0)
    c.path([(71, 27), (90, 27), (90, 47.3)], label="model", seg=0, loff=(0, 1.6), fs=6.0)
    c.path([(101, 46.0), (101, 33)], label="certificate", seg=0, loff=(-6, 0), fs=6.0)
    c.path([(95, 45.5), (95, 16), (71, 16)], label="CLIENT_UNLEARNING record", seg=1, loff=(0, -1.6), fs=6.0)
    # process 6 (audit ledger and certificate export)
    bipath(c, [(60, 13), (60, 10)])
    c.text(66.5, 11.5, "ledger lines", fs=6.0, ha="left")
    c.path([(101, 26), (101, 5.5), (71, 5.5)], label="certificate", seg=1, loff=(0, 1.6), fs=6.0)
    bipath(c, [(26, 5), (49, 5)], label="verify / status,\ncertificate JSON", loff=(0, 3.4), fs=6.0)
    c.text(24, 12.4, "3 hands over to 4 inside one unlearn() call.\nStores are open boxes, one per store.", fs=6.2, italic=True)
    c.save(out)


def dfd2(out):
    c = Canvas(11.0, 7.8)
    c.box(0.5, 50, 9, 12, "Operator", fc=GREEN_L, fs=6.8, bold=True)
    c.box(0.2, 20, 8.8, 12, "Operator\n(gets\ncertificate)", fc=GREEN_L, fs=5.8, bold=True)
    # row 1: process 3 (unlearn)
    r1 = [(27, "3.1\nCheck guards\n(trained, known,\nnot removed, >1 left)"), (59, "3.2\nSubtract tracked\nupdate from the\nnoisy sum"),
          (91, "3.3\nRenormalise and\nrebuild model\n(divide by n - 1)")]
    for x, t in r1:
        c.ellipse(x, 56, 24, 14, t, fc=INDIGO_L, fs=6.9)
    store(c, 27, 73.5, 26, 6, "D3  Global model", fs=6.3)
    store(c, 59, 73.5, 26, 6, "D2  Clipped updates + noise", fs=6.3)
    store(c, 91, 73.5, 26, 6, "D3  Global model", fs=6.3)
    c.arrow((9.5, 56), (15, 56), label="client_id", loff=(0.5, 2.3), fs=6.2)
    c.arrow((27, 70.5), (27, 63), label="state + active clients", loff=(11, 0), fs=6.3)
    c.arrow((39, 56), (47, 56), label="accepted", loff=(0, 2.2), fs=6.2)
    bipath(c, [(59, 70.5), (59, 63)], label="update", loff=(4.5, 0), fs=6.3)
    c.arrow((71, 56), (79, 56), label="new sum", loff=(0, 2.2), fs=6.2)
    bipath(c, [(91, 70.5), (91, 63)], label="model", loff=(4, 0), fs=6.3)
    # row 2: process 4 (verify and certify), right to left
    xs = [100, 80, 60, 40, 20]
    r2 = ["4.1\nReference:\nretained updates\n+ same noise", "4.2\nMembership\nAUC before\nand after", "4.3\nUtility\nretention", "4.4\nStatus:\nL2 <= 1e-10\nand >= 70 %",
          "4.5\nBuild certificate,\nappend ledger\nrecord"]
    for x, t in zip(xs, r2):
        c.ellipse(x, 26, 16, 14.5, t, fc=BLUE_L, fs=6.1)
    c.path([(91, 49), (91, 42), (100, 42), (100, 33.3)])
    c.text(83, 39.8, "model, noise, retained updates", fs=6.2)
    for a, b, t in zip(xs[:-1], xs[1:], ["reference|L2", "AUC|pair", "retention|%", "status"]):
        c.arrow((a - 8, 26), (b + 8.0, 26))
        c.text((a + b) / 2, 31.0, t.replace("|", chr(10)), fs=5.9)
    c.arrow((12, 26), (8.5, 26))
    # bottom stores
    for x, t in zip(xs, ["D2  Updates\n+ noise", "D1  Client\ndatasets", "D3  Global\nmodel", "D4  Certificates", "D5  Audit\nledger"]):
        store(c, x, 6, 17, 6.5, t, fs=6.1)
    c.arrow((100, 9.3), (100, 18.7))
    c.text(104.6, 13.5, "updates", fs=6.0)
    c.arrow((80, 9.3), (80, 18.7))
    c.text(83.8, 13.5, "records", fs=6.0)
    c.arrow((60, 9.3), (60, 18.7))
    c.text(63.5, 13.5, "model", fs=6.0)
    c.arrow((24, 19.5), (37, 9.3), label="certificate", loff=(5.5, 2.3), fs=6.0)
    c.arrow((20, 18.7), (20, 9.3), label="record", loff=(-4, 0), fs=6.0)
    c.text(55, 43.5, "Process 4 runs inside the same unlearn() call, right to left; each hand-over is an in-memory value", fs=6.8, italic=True)
    c.text(55, 0.8, "Level 2 expansion of processes 3 (unlearn client) and 4 (verify and certify)", fs=6.8, italic=True)
    c.save(out)


def flowchart(out):
    c = Canvas(10.4, 9.4)
    c.terminal(6.5, 70, 11, 6.5, "Start\nunlearn(\nclient_id)", fs=6.4)
    xs = [25, 47, 69, 91]
    labels = ["model is\nNone?", "client_id not\nin clients?", "client_id not\nin active ids?", "only one\nactive client?"]
    errs = ["RuntimeError\nTrain the federated\nmodel first", "KeyError\nUnknown client:\n<id>", "ValueError\n<id> has already\nbeen unlearned", "ValueError\nAt least one client\nmust remain"]
    for x, t, e in zip(xs, labels, errs):
        c.diamond(x, 70, 20, 12, t, fs=6.6)
        c.box(x - 10, 82, 20, 7, e, fc=ROSE_L, ec="#c98a8a", fs=6.1)
        c.arrow((x, 76), (x, 82), label="yes", loff=(2.6, 0), fs=6.5)
    c.arrow((12, 70), (15, 70))
    for a, b in zip(xs[:-1], xs[1:]):
        c.arrow((a + 10, 70), (b - 10, 70), label="no", loff=(0, 1.9), fs=6.5)
    c.text(52, 92.2, "every guard raises; web.py maps ValueError / KeyError / RuntimeError to HTTP 400 {\"error\": message}", fs=6.8, italic=True)
    # right column: the computation
    c.arrow((91, 64), (91, 62), label="no", loff=(2.6, 0), fs=6.5)
    steps = [(58, "before = metrics();  auc_before = membership_auc(\nmodel, client records, 5 non-member texts)"),
             (47, "noisy_sum = noisy_sum - updates[client_id];\nactive_client_ids.remove(client_id)"),
             (36, "_rebuild_model(): parameters = noisy_sum / n_active\nafter = metrics();  auc_after = membership_auc(...)"),
             (25, "reference = (noise + retained updates) / n_active;\ndistance = L2(model - reference)"),
             (14, "retention = min(100, 100 x utility_after / utility_before)")]
    prev = None
    for y, t in steps:
        b = c.box(58, y - 4, 44, 8, t, fc=BLUE_L, fs=6.3)
        if prev is not None:
            c.arrow((80, prev["y"]), (80, y + 4))
        prev = b
    # left column: decision and outcome
    c.path([(58, 14), (52, 14), (52, 60), (24, 60), (24, 56)])
    c.diamond(24, 50, 32, 12, "L2 <= 1e-10\nand retention\n>= 70 % ?", fs=6.3)
    c.path([(8, 50), (8, 44)], label="yes", loff=(-2.4, 0), fs=6.5)
    c.path([(40, 50), (40, 44)], label="no", loff=(2.4, 0), fs=6.5)
    c.box(0.5, 37, 15, 7, "status =\nCERTIFIED", fc=GREEN_L, fs=6.3, bold=True)
    c.box(32.5, 37, 15, 7, "status =\nREVIEW_\nREQUIRED", fc=AMBER_L, fs=6.0, bold=True)
    c.path([(8, 37), (8, 33), (24, 33), (24, 30)])
    c.path([(40, 37), (40, 33), (24, 33), (24, 30)])
    c.box(4, 22, 40, 8, "build UnlearningCertificate: epsilon, delta,\nclip norm, noise multiplier, L2, AUC, perplexity,\nmodel hashes before and after", fc=BLUE_L, fs=6.0)
    c.arrow((24, 22), (24, 18))
    c.box(4, 10, 40, 8, "audit.append(CLIENT_UNLEARNING + certificate):\nsequence, previous_hash, record_hash;\nattach audit_record_hash, store certificate", fc=INDIGO_L, fs=6.0)
    c.arrow((24, 10), (24, 6.5))
    c.terminal(24, 3.5, 30, 5.5, "return certificate (HTTP 200)", fs=6.6)
    c.save(out)
