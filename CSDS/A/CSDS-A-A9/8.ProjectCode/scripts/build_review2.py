"""Build 13.Review_2_PPT.pptx from D:\\abstracts\\Templates\\Review_2_PPT.pptx (20 slides).

Every number comes from experiments/*/metrics.json via doc_common.metrics (the same numbers as docs/REPORT_FACTS.md).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_review1 import MISSING, drop_orphan_images, footers, pic, scrub_zip, title_slide  # noqa: E402
from deckkit import fill, replace_chart, set_notes, set_paras, set_table, shape, style_chart, table_size  # noqa: E402
from doc_common import BATCH, CHARTS, DIAG, PRODUCT, SHOTS, TITLE, metrics  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.util import Emu  # noqa: E402

SRC = r"D:\abstracts\Templates\Review_2_PPT.pptx"
OUT = BATCH / "13.Review_2_PPT.pptx"


def px(v):
    return Emu(int(v * 9525))


def cards(s, items, size=15, min_pt=10):
    for tid, bid, ttl, body in items:
        set_paras(shape(s, tid), ttl)
        fill(s, bid, body, size, min_pt=min_pt)


def fit(s, sid, paras, size):
    """Set text at an explicit size (the template's own size is smaller than the boxes need)."""
    set_paras(shape(s, sid), paras, size)


def frame_to(pic_, frame):
    if pic_ is not None:
        frame.left, frame.top, frame.width, frame.height = pic_.left, pic_.top, pic_.width, pic_.height


def build():
    b = metrics("baseline")
    seeds = metrics("seeds")
    sweep = metrics("noise_sweep")["rows"]
    gold = metrics("gold_retrain")["results"]
    nf = metrics("noise_free_leakage")
    sc = metrics("scaling")
    api = metrics("api")
    au = metrics("audit_tamper")
    dp = metrics("dp_accounting")
    nnm = metrics("neural_adapter")
    nn0 = nnm["summary"]["by_sigma"][0]
    nn_b = nnm["base"]
    syn = metrics("synthetic_corpus")
    load = metrics("load_test")
    sec = metrics("security_probe")
    acc = metrics("acceptance")
    n_need = syn["n_sweep"]["smallest_n_within_1_2x"]["4.85"]
    sec_c = sec["classification_counts"]
    race_one = load["races"]["32 simultaneous unlearn requests for the same client"]["status_counts"]
    st = {x["concurrency"]: x for x in load["scenarios"]["GET /api/state"]["levels"]}
    t = b["training"]
    contrib = b["contributions"]
    lat = api["latency"]
    g3 = next(r for r in gold if r["noise_multiplier"] == 3.0)
    detected = sum(c["detected"] for c in au["cases"][1:])
    n_attacks = len(au["cases"]) - 1
    n_bad = sum(1 for e in api["edge_cases"] if e["status"] in (-1, 501))
    s_hi = next(r for r in sweep if r["noise_multiplier"] == 0.1)

    prs = Presentation(SRC)
    S = list(prs.slides)
    footers(prs, f"{PRODUCT}  \u00b7  Review 2  \u00b7  Batch A9")
    cp = prs.core_properties
    cp.title, cp.subject, cp.author = f"{PRODUCT}: Review 2", TITLE, "Batch A9"
    cp.keywords = "federated unlearning, differential privacy, membership inference, audit ledger"
    cp.category = cp.comments = cp.content_status = ""
    cp.last_modified_by = "Batch A9"

    # 1 title
    title_slide(S[0], "Review 2 covers the design, methodology and progress of ForgetSafe.")

    # 2 contents (template labels are generic and fit)
    set_notes(S[1], "Twelve parts: recap, architecture, methodology, dataset, preprocessing, model and training, decision logic, data flow and database, technology, progress, results and screens, testing, challenges and next steps.")

    # 3 recap
    s = S[2]
    fill(s, 8, "A client's influence stays in the federated model's parameters; retraining for every deletion request is impractical and heuristic unlearning gives no proof.", 16)
    fill(s, 13, "Subtract the client's tracked update, bound the release with differential privacy, verify, and record the request in a SHA-256 ledger: Python API plus React UI.", 16)
    for sid, tx in zip((15, 18, 21, 24, 27), ["Training: 5 clients", "Clip + noise + aggregate", "Subtract client update", "Verify: attack, utility", "Certificate + ledger"]):
        fill(s, sid, tx, 15)
    set_notes(s, "Recap of Review 1. The base paper recorded in the batch files is a sign-language survey whose review method is adopted; the technical neighbours are [2] to [4].")

    # 4 architecture
    s = S[3]
    pic(s, DIAG / "01_system_architecture.png", (57, 124, 720, 518), remove_ids=(4,), name="System architecture diagram")
    fit(s, 5, ["Client: React 19 + Vite 8 (port 5109); the dev server proxies /api to the API.",
                "API: Python standard-library http.server (port 8109), 9 routes (8 JSON endpoints and the legacy page); one shared engine behind a lock.",
                "Engine: FederatedUnlearningEngine with train(), unlearn(), metrics() and generate().",
                f"Model: character-bigram LM (1,089 parameters) in the product; a {nn_b['base_parameters']:,}-parameter GRU with LoRA-style adapters in the neural study.",
                "Record: membership AUC, perplexity, reference recomputation and a SHA-256 hash-chained ledger (data/audit_log.jsonl)."], 14)
    set_notes(s, "Everything runs on one machine with no third-party Python package. There is no SQL database: state is in memory plus the JSONL ledger.")

    # 5 methodology
    s = S[4]
    for sid, tx in zip((5, 8, 11, 14, 17, 20, 23), ["Load 5 client corpora", "Bigram update per client", "L2-clip to C = 25", "Sum + Gaussian noise", "Unlearn: subtract update", "Verify: AUC, utility", "Certificate + ledger"]):
        fill(s, sid, tx, 14, min_pt=9)
    set_paras(shape(s, 25), "Tracked updates")
    fill(s, 26, "Clipped client updates are stored, so one can be subtracted later without touching raw records.", 15)
    set_paras(shape(s, 28), "Verification stack")
    fill(s, 29, "Membership AUC, public-set perplexity and accuracy, a retention floor of 70 %, and a retained-only recomputation.", 15)
    set_paras(shape(s, 31), "Reproducible")
    fill(s, 32, "Fixed seeds; four run_*.py scripts regenerate every experiments/*/metrics.json (product, synthetic corpus, neural, testing).", 15)
    set_notes(s, "Seven steps from the client corpora to the certificate. The recomputation re-uses the same stored noise, so it is exact by construction; an independent fresh-noise retrain comparison was added to the evaluation.")

    # 6 dataset
    s = S[5]
    set_paras(shape(s, 2), "Dataset and input sources")
    names = [c["domain"] for c in contrib]
    ch = replace_chart(s, 4, names, [("Raw update L2 norm", [round(c["original_norm"], 2) for c in contrib])], number_format="0.0")
    style_chart(ch, "Raw update norm of each client (clip norm C = 25)", ["5B5BD6"], number_format="0.0", legend=False, label_pt=11, axis_title="L2 norm before clipping")
    ch.value_axis.minimum_scale = 0
    ch.value_axis.maximum_scale = 32
    sc_d, nn_c = syn["design"], nnm["config"]
    rows = [["Source (all synthetic)", "Size", "Use"],
            ["Product corpus", "5 clients x 5 sentences (25 records); 5 public + 5 non-member", "The app: training and removal"],
            ["Synthetic-corpus study", f"20 domains x {sc_d['per_client_train_sentences']} train / {sc_d['per_client_held_out_sentences']} held-out; {sc_d['public_evaluation_sentences']} public", "Real engine at realistic size"],
            ["Neural-study corpus", f"{nn_c['n_clients']} domains x {nn_c['train_per_client']} train / {nn_c['heldout_per_client']} held-out; {nn_c['public_train']:,} public", "GRU + LoRA-style adapters"],
            ["Bigram parameters", "33 symbols; 33 x 33 = 1,089", "Bigram count vector"],
            ["External data", "None: seeded grammars, offline", "No licence issue"]]
    sz = table_size(rows, 530, 400, [0.26, 0.46, 0.28], 12, 10)
    set_table(shape(s, 7), rows, sz, widths=[0.26, 0.46, 0.28], header_size=sz)
    set_notes(s, "Three synthetic data sources: the product's built-in corpus (certified_unlearning/dataset.py), a seeded 20-domain grammar corpus for the real engine, and a seeded 8-domain corpus for the neural study. In the product every raw update norm (25.2 to 28.2) exceeds C, so all five updates are clipped.")

    # 7 preprocessing
    s = S[6]
    set_paras(shape(s, 2), "Data preparation and features")
    set_paras(shape(s, 7), "Text normalisation")
    fill(s, 8, "normalize_text(): lower-case; characters outside the 33-symbol alphabet become spaces; whitespace collapsed; ^ and $ mark the start and end of each record.", 15)
    set_paras(shape(s, 12), "Update vector")
    fill(s, 13, f"Counts of adjacent symbol pairs form a 1,089-dimensional vector per client. Raw L2 norms range {min(c['original_norm'] for c in contrib):.1f} to {max(c['original_norm'] for c in contrib):.1f}.", 15)
    set_paras(shape(s, 17), "Clipping and noise")
    fill(s, 18, f"Each vector is scaled to norm at most C. Product: C = 25 (scales {min(c['clip_scale'] for c in contrib):.3f} to {max(c['clip_scale'] for c in contrib):.3f}). At realistic size raw norms are about {syn['raw_norms']['median']:,.0f}, so C = 25 would shrink updates {syn['raw_norms']['ratio_median_norm_to_C25']:.0f}x: the studies use C = median raw norm. Noise std = sigma x C per coordinate.", 14)
    set_notes(s, "Preparation turns each client's sentences into one clipped update. In the product the noise standard deviation is 75 per coordinate while a clipped update has norm 25, so the noise dominates at the default setting. On 200-sentence clients the raw update norm is about 1,239 and the product's C = 25 scales every update by 0.02; the synthetic-corpus and neural studies therefore set C to the median raw norm.")

    # 8 model
    s = S[7]
    set_paras(shape(s, 2), "Model and aggregation")
    pic(s, DIAG / "02_high_level_workflow.png", (75, 124, 693, 518), remove_ids=(4,), name="High-level workflow")
    rows = [["Component", "Detail"], ["Product model", "Character-bigram LM, 1,089 parameters (33 x 33), pure Python"],
            ["Neural study", f"GRU {nn_b['base_parameters']:,} parameters, frozen"], ["Adapter per client", f"rank {nn_b['adapter_rank']}, {nn_b['adapter_dimension']:,} parameters"],
            ["Release", "(sum + noise) / n, same for both"]]
    set_table(shape(s, 9), rows, 11, header_size=11)
    set_paras(shape(s, 6), "Product: bigram parameter vector as the adapter update. Neural study: PyTorch GRU with LoRA-style adapters on synthetic text, CPU only.", 11)
    set_notes(s, "The product's model is a bigram language model whose parameter vector stands in for an adapter update. The neural study applies the same clip, noisy-sum and subtraction steps to the adapter parameters of a small GRU (137,151 parameters, rank-64 adapters of 14,272 parameters) trained on synthetic text; it ran in about four minutes on the CPU.")

    # 9 training configuration
    s = S[8]
    set_paras(shape(s, 2), "Training configuration")
    rows = [["Setting", "Value"], ["Clients", "5 in the product; 5-20 and 8 in the studies"], ["Clip norm C", "25 in the product; median raw norm in the studies"],
            ["Noise multiplier sigma", "3 (std 75 per coordinate); sweeps 0 to 10"], ["delta", "1e-5"], ["Reported epsilon", f"{dp['default_epsilon']:.4f} at sigma 3"],
            ["Seeds", "2026 (product); 5 to 50 seeds per study"], ["Certified if", "L2 <= 1e-10 and retention >= 70 %"]]
    set_table(shape(s, 10), rows, 13, header_size=13)
    p = pic(s, CHARTS / "s03_clients_needed_for_epsilon_below_1.png", (672, 180, 550, 340), remove_ids=(5,), name="Federation-size chart")
    frame_to(p, shape(s, 6))
    set_paras(shape(s, 7), f"Synthetic corpus: perplexity relative to the noise-free model against federation size; sigma 4.85 (epsilon 1.00) needs about {n_need:,} clients to come within 1.2x", 11)
    if p is not None:
        shape(s, 7).top = Emu(p.top + p.height + px(10))
    set_notes(s, f"Epsilon = sqrt(2 ln(1.25/delta)) / sigma. The classical Gaussian bound is valid only for epsilon < 1, which needs sigma above {dp['sigma_needed_for_epsilon_below_1']:.3f}; the product's default sigma = 3 is outside that range. Because the noise is added once to the sum and divided by n, a larger federation dilutes it: on the synthetic corpus (100 sentences per client, C = median norm) the perplexity falls to within 1.2x of the noise-free model from about {n_need:,} clients at sigma 4.85.")

    # 10 decision logic
    s = S[9]
    pic(s, DIAG / "10_algorithm_flowchart.png", (45, 124, 620, 520), remove_ids=(4,), name="Decision flowchart")
    items = [(5, 6, 7, "Certified or review", f"CERTIFIED if reference L2 is at most 1e-10 and retention is at least 70 %, else REVIEW_REQUIRED. In {seeds['n_unlearning_requests']} requests all were CERTIFIED."),
             (8, 9, 10, "Refused requests", "Before training, unknown client, repeat removal and removing the last client return HTTP 400 with a message."),
             (11, 12, 13, "Utility score", "0.65 x accuracy + 0.35 / (1 + ln(1 + perplexity)); retention = after / before x 100, capped at 100.")]
    for card, tid, bid, ttl, body in items:
        c = shape(s, card)
        tt, bb = shape(s, tid), shape(s, bid)
        c.left, c.width = px(690), px(531)
        tt.left, tt.width = px(714), px(490)
        bb.left, bb.width = px(714), px(490)
        set_paras(tt, ttl)
        tt.top, tt.height = c.top + px(10), px(40)
        bb.top, bb.height = c.top + px(50), px(92)
        fill(s, bid, body, 15, min_pt=10)
    set_notes(s, "The flowchart follows FederatedUnlearningEngine.unlearn(). The retention threshold is a demonstration floor, not a legal criterion.")

    # 11 data flow
    s = S[10]
    set_paras(shape(s, 2), "Data flow and modules")
    pic(s, DIAG / "04_dfd_level1.png", (57, 112, 640, 440), remove_ids=(4,), name="DFD level 1")
    set_paras(shape(s, 5), "DFD level 1: six processes, five stores", 11)
    shape(s, 5).left, shape(s, 5).top = px(57), px(560)
    rows = [["Module", "Responsibility"],
            ["engine.py", "train(), unlearn(), certificate, metrics, reference recomputation"],
            ["model.py, dataset.py", "bigram update and clipping, perplexity, accuracy, membership AUC; corpora"],
            ["audit.py, web.py", "hash-chained ledger and verify(); JSON API and legacy page"]]
    set_table(shape(s, 12), rows, 12, widths=[0.30, 0.70], header_size=12, row_h=60, total_px=500)
    tb = shape(s, 12)
    tb.left, tb.top, tb.width = px(721), px(190), px(500)
    set_notes(s, "Data flow of the training and unlearning requests and the modules that implement them.")

    # 12 database and UML
    s = S[11]
    set_paras(shape(s, 2), "Data model and UML (no SQL database)")
    pic(s, DIAG / "06_er_diagram.png", (670, 112, 551, 420), remove_ids=(5,), name="ER diagram")
    pic(s, DIAG / "07_uml_class_diagram.png", (57, 112, 600, 420), name="UML class diagram")
    set_paras(shape(s, 6), "UML class diagram (left) and ER view of the data model (right); only the audit record is persisted", 11)
    shape(s, 6).left, shape(s, 6).top, shape(s, 6).width = px(57), px(548), px(1164)
    shape(s, 13)._element.getparent().remove(shape(s, 13)._element)
    set_notes(s, "ForgetSafe has no SQL database. Engine state lives in memory; certificates and training events are appended to data/audit_log.jsonl, which survives restarts and new sessions.")

    # 13 technology
    s = S[12]
    cards(s, [(7, 8, "Language", "Python 3.11 (standard library only), JavaScript"),
              (12, 13, "Engine and maths", "dataclasses, hashlib, json, math, random.gauss; no NumPy"),
              (17, 18, "Backend", "http.server ThreadingHTTPServer, JSON API, RLock-guarded engine"),
              (22, 23, "Frontend", "React 19, Vite 8, react-router 7, Recharts 3, Framer Motion, GSAP"),
              (27, 28, "Desktop and CLI", "Tkinter GUI (--desktop) and terminal demo (--demo)"),
              (32, 33, "Storage and tests", "JSONL ledger; unittest (5 tests), smoke test (14 checks), Playwright captures")], 15)
    set_notes(s, "Versions are the ones in frontend/package.json. There is no third-party Python dependency and no external AI service.")

    # 14 progress
    s = S[13]
    rows = [["Component", "Status"], ["Federated training with clipping and noise", "Completed"], ["Tracked-update unlearning and certificate", "Completed"],
            ["Membership attack and utility metrics", "Completed"], ["SHA-256 ledger with verification", "Completed"],
            ["React UI (landing + 5 screens), legacy UI, Tkinter, CLI", "Completed"],
            ["Product measurements: 11 experiments, 12 charts", "Completed"],
            ["Synthetic-corpus and neural-adapter studies", "Completed"],
            ["Load, security-probe and acceptance studies", "Completed"],
            ["Privacy accountant, signed ledger, authentication", "Planned"]]
    set_table(shape(s, 15), rows, 12, widths=[0.72, 0.28], header_size=12)
    for vid, lid, v, lab in [(6, 7, "9", "API routes (8 JSON + legacy page)"), (9, 10, "5", "unit tests pass"), (12, 13, "14/14", "smoke-test checks pass")]:
        set_paras(shape(s, vid), v)
        set_paras(shape(s, lid), lab)
    set_notes(s, "All planned features and studies are done. The engineering items for the next stage are a privacy accountant, a signed ledger and authentication.")

    # 15 preliminary results
    s = S[14]
    set_paras(shape(s, 2), "Preliminary results: attack AUC against noise")
    pick = [r for r in sweep if r["noise_multiplier"] in (0.01, 0.1, 0.5, 1.0, 3.0, 10.0)]
    ch = replace_chart(s, 4, [f"sigma {r['noise_multiplier']:g}" for r in pick],
                       [("Before removal", [round(r["membership_auc_before"]["mean"], 3) for r in pick]),
                        ("After removal", [round(r["membership_auc_after"]["mean"], 3) for r in pick])], number_format="0.00")
    style_chart(ch, "Membership AUC before and after removal (20 seeds x 5 clients per sigma)", ["5B5BD6", "2F9E77"], number_format="0.00", legend=True, label_pt=10, axis_title="AUC (0.5 = chance)")
    ch.value_axis.maximum_scale = 1.1
    for vid, lid, v, lab in [(6, 7, f"{nf['mean_auc_before']:.2f} \u2192 {nf['mean_auc_after']:.2f}", "bigram attack AUC with no noise, before \u2192 after removal"),
                             (9, 10, f"{nn0['client_auc_before']['mean']:.2f} \u2192 {nn0['client_auc_after']['mean']:.2f}", f"neural adapters, client-level AUC (fresh retrain {nn0['client_auc_retrain']['mean']:.2f})"),
                             (12, 13, f"{n_need:,}", "clients for epsilon < 1 with a useful model (synthetic corpus)")]:
        set_paras(shape(s, vid), v)
        set_paras(shape(s, lid), lab)
    set_notes(s, f"At sigma 3 the attack is already near chance before removal ({seeds['membership_auc_before']['mean']:.2f} +/- {seeds['membership_auc_before']['sd']:.2f}), so there is little to remove. Without noise the attack is near-perfect and removal brings it to about 0.54. A fresh-noise retrain is as far from the unlearned model as two retrains are from each other: {g3['l2_unlearned_vs_fresh_retrain']['mean']:.0f} versus {g3['l2_fresh_retrain_vs_fresh_retrain']['mean']:.0f} at sigma 3. At sigma 0.1 the useful model has AUC {s_hi['membership_auc_before']['mean']:.2f} before and {s_hi['membership_auc_after']['mean']:.2f} after. The neural adapter study (8 synthetic clients, GRU with {nn_b['adapter_dimension']:,}-parameter adapters) shows the same: client-level AUC {nn0['client_auc_before']['mean']:.2f} before, {nn0['client_auc_after']['mean']:.2f} after removal, {nn0['client_auc_retrain']['mean']:.2f} for a fresh retrain; sigma 4.85 with 100-sentence clients needs about {n_need:,} clients for a useful model.")

    # 16 output screens
    s = S[15]
    p1 = pic(s, SHOTS / "09_unlearning_certificate.png", (45, 128, 590, 476), remove_ids=(4,), name="Certificate screenshot")
    p2 = pic(s, SHOTS / "13_audit_ledger.png", (645, 128, 590, 476), remove_ids=(7,), name="Audit ledger screenshot")
    frame_to(p1, shape(s, 5))
    frame_to(p2, shape(s, 8))
    set_paras(shape(s, 6), "Certificate for Client 01 (Finance): certified, 93.65 % utility retained, AUC 0.200 \u2192 0.160", 11)
    set_paras(shape(s, 9), "Compliance audit: 4 ledger records, hash chain verified valid", 11)
    for cap_id, p in ((6, p1), (9, p2)):
        if p is not None:
            shape(s, cap_id).top = Emu(max(p.top + p.height + px(12), px(500)))
    set_notes(s, "Real captures of the running application (seed 2026, trained through the UI, Finance removed, then Healthcare). The ledger also holds two training events from earlier capture sessions.")

    # 17 testing
    s = S[16]
    set_paras(shape(s, 2), "Testing and observations")
    err_levels = [(x["concurrency"], x["errors_5xx_or_connection"]) for sc_ in load["scenarios"].values() for x in sc_["levels"] if x["errors_5xx_or_connection"]]
    first_err = min(c for c, _ in err_levels)
    rows = [["Test group", "Count", "Result"], ["Unit tests (unittest)", "5", "5 passed"], ["Smoke test on the live API", "14", "14 passed"],
            ["Load, 1 to 64 concurrent clients", f"{len(load['scenarios'])} scenarios", f"errors only from {first_err} clients up"],
            ["Security probes", f"{sec['n_probes']}", f"{sec_c['handled']} handled, {sec_c['noteworthy']} noted, {sec_c['defect']} defects"],
            ["Scripted synthetic-user acceptance", f"{acc['journeys']} journeys", f"{acc['journeys_passed_all_steps']} passed all steps"],
            ["Audit tamper attacks", f"{n_attacks}", f"{detected} detected, {n_attacks - detected} not"]]
    set_table(shape(s, 18), rows, 14, widths=[0.42, 0.2, 0.38], header_size=14)
    fit(s, 5, [f"Audit chain catches edits, deletions and re-ordering ({detected} of {n_attacks} attacks); tail truncation, a full re-hash forgery and an appended forged record pass, and an emptied ledger verifies as valid.",
                f"Races: 32 simultaneous removals of one client gave {race_one['200']} success and {race_one['400']} refusals; 16 simultaneous trainings left a valid 16-record chain; a 2,000-request soak had 0 errors.",
                f"/api/state saturates near {max(x['requests_per_s'] for x in st.values()):.0f} requests/s because it re-reads the ledger; medians: train {lat['POST /api/train']['p50_ms']:.0f} ms, unlearn {lat['POST /api/unlearn']['p50_ms']:.0f} ms.",
                f"{sec_c['defect']} security defects (no read timeout, POST open to cross-site requests, Host unchecked, connection bursts refused, no authentication) are listed with their fixes under next steps.",
                f"Acceptance is scripted ({acc['total_certificates_checked']} certificates checked, {acc['console_error_journeys']} console errors), not a human study."], 14)
    set_notes(s, "Load: 1, 2, 4, 8, 16, 32 and 64 concurrent clients on 127.0.0.1 against health, state, generate and a mixed train/unlearn workload. Security: 58 synthetic malicious or malformed requests, classified as handled, noteworthy or defect. Acceptance: 20 randomised Playwright journeys (desktop and 390 px phone, light and dark, some cancelling the first dialog). Latency measured on an i5-12500; the numbers shift between runs.")

    # 18 challenges
    s = S[17]
    cards(s, [(7, 8, "Noise swamps the model", f"At sigma 3 perplexity is {seeds['pre_unlearning_perplexity']['mean']:.0f} +/- {seeds['pre_unlearning_perplexity']['sd']:.0f} against 32 for a uniform model; accuracy about 4 %."),
              (12, 13, "Certificate is an identity", f"The reference re-uses the stored noise (L2 about 1e-14). A fresh-noise retrain study: {g3['l2_unlearned_vs_fresh_retrain']['mean']:.0f} versus {g3['l2_fresh_retrain_vs_fresh_retrain']['mean']:.0f}."),
              (17, 18, "Epsilon outside classical range", f"Reported epsilon {dp['default_epsilon']:.2f} exceeds 1; the bound needs sigma above {dp['sigma_needed_for_epsilon_below_1']:.3f}. With 5 clients a useful model needs sigma 0.1 or less; with about {n_need:,} clients sigma 4.85 works."),
              (22, 23, "Clip norm C = 25 is 50x too small", f"At 200 sentences per client raw norms are about {syn['raw_norms']['median']:,.0f}; C = 25 scales them by {syn['raw_norms']['scale_applied_by_product_C25']['mean']:.2f}. The studies set C to the median raw norm."),
              (27, 28, "Ledger is tamper-evident only", f"{detected} of {n_attacks} attacks detected; truncation, re-hash forgery and forged append are not; an emptied ledger verifies; one garbage line makes /api/state return 500."),
              (32, 33, "API hardening", f"{sec_c['defect']} defects in {sec['n_probes']} probes: no read timeout, cross-site POST accepted, Host unchecked, connection bursts refused, no authentication.")], 14)
    set_notes(s, "Six findings from the measurement suite and the testing studies, each backed by experiments/*/metrics.json and docs/REPORT_FACTS.md. The positive result that goes with them: epsilon below 1 and a useful model coexist once the federation is large (about 1,000 clients on the synthetic corpus).")
    for n, sid in enumerate((4, 9, 14, 19, 24, 29), 1):
        shape(S[17], sid).name = f"Challenge card {n}"
    for sh in S[17].shapes:
        if sh.shape_type == 13:
            sh._element.nvPicPr.cNvPr.set("descr", "icon")

    # 19 next steps
    s = S[18]
    for sid, tx in zip((5, 8, 11, 14), ["Honest certificate", "Privacy accounting", "Harden ledger and API", "Report and demo"]):
        fill(s, sid, tx, 16)
    fill(s, 15, ["Put the fresh-noise retrain comparison in the certificate next to the same-noise recomputation, and re-draw the noise per release.",
                 "Add a privacy accountant and the exact analytic Gaussian bound [19] (it gives epsilon 1.27 at sigma 3, not 1.61); plan federations of about 1,000 clients for epsilon below 1.",
                 "Harden: sign or anchor ledger records, authenticate and CSRF-protect the API, add read timeouts, reject an emptied ledger and return a clean 400 for oversized bodies.",
                 "Complete the final report and demonstration; extend the adapter study to LoRA on a small pretrained language model with Flower."], 15, bullet=True)
    set_notes(s, "Engineering items for the final stage; each follows from a measured finding in the challenges slide. The exact analytic Gaussian value was computed for the report with the Balle and Wang calibration.")

    set_notes(S[19], "Thank you. Questions are welcome.")
    drop_orphan_images(prs)
    prs.save(OUT)
    scrub_zip(OUT)
    print("saved", OUT, len(prs.slides._sldIdLst), "slides; missing pictures:", sorted(set(MISSING)))


if __name__ == "__main__":
    build()
