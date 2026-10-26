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
                "Model: character-bigram language model, 1,089 parameters, a proxy for an LLM adapter update.",
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
    fill(s, 32, "Fixed seed 2026; scripts/run_experiments.py regenerates experiments/*/metrics.json.", 15)
    set_notes(s, "Seven steps from the client corpora to the certificate. The recomputation re-uses the same stored noise, so it is exact by construction; an independent fresh-noise retrain comparison was added to the evaluation.")

    # 6 dataset
    s = S[5]
    set_paras(shape(s, 2), "Dataset and input sources")
    names = [c["domain"] for c in contrib]
    ch = replace_chart(s, 4, names, [("Raw update L2 norm", [round(c["original_norm"], 2) for c in contrib])], number_format="0.0")
    style_chart(ch, "Raw update norm of each client (clip norm C = 25)", ["5B5BD6"], number_format="0.0", legend=False, label_pt=11, axis_title="L2 norm before clipping")
    ch.value_axis.minimum_scale = 0
    ch.value_axis.maximum_scale = 32
    rows = [["Set", "Size", "Use"],
            ["Client corpora", "5 clients x 5 sentences (25 records)", "Federated training"],
            ["Public evaluation", "5 sentences", "Perplexity, accuracy, utility"],
            ["Non-member texts", "5 sentences", "Membership-attack baseline"],
            ["Alphabet and parameters", "33 symbols; 33 x 33 = 1,089", "Bigram count vector"],
            ["External data", "None; hand-written, offline", "No licence issue; no real corpus"]]
    sz = table_size(rows, 530, 400, [0.30, 0.42, 0.28], 12, 10)
    set_table(shape(s, 7), rows, sz, widths=[0.30, 0.42, 0.28], header_size=sz)
    set_notes(s, "All data is the built-in synthetic corpus in certified_unlearning/dataset.py. Every raw update norm (25.2 to 28.2) exceeds C, so all five updates are clipped.")

    # 7 preprocessing
    s = S[6]
    set_paras(shape(s, 2), "Data preparation and features")
    set_paras(shape(s, 7), "Text normalisation")
    fill(s, 8, "normalize_text(): lower-case; characters outside the 33-symbol alphabet become spaces; whitespace collapsed; ^ and $ mark the start and end of each record.", 15)
    set_paras(shape(s, 12), "Update vector")
    fill(s, 13, f"Counts of adjacent symbol pairs form a 1,089-dimensional vector per client. Raw L2 norms range {min(c['original_norm'] for c in contrib):.1f} to {max(c['original_norm'] for c in contrib):.1f}.", 15)
    set_paras(shape(s, 17), "Clipping and noise")
    fill(s, 18, f"Each vector is scaled to norm at most C = 25 (scales {min(c['clip_scale'] for c in contrib):.3f} to {max(c['clip_scale'] for c in contrib):.3f}). Gaussian noise with std sigma x C = {dp['noise_std_per_coordinate_default']:.0f} (sigma = 3) is added to every coordinate of the sum.", 15)
    set_notes(s, "Preparation turns each client's sentences into one clipped 1,089-number update. The noise standard deviation is 75 per coordinate while a clipped update has norm 25, so the noise dominates at the default setting.")

    # 8 model
    s = S[7]
    set_paras(shape(s, 2), "Model and aggregation")
    pic(s, DIAG / "02_high_level_workflow.png", (75, 124, 693, 518), remove_ids=(4,), name="High-level workflow")
    rows = [["Component", "Detail"], ["Model", "Character-bigram LM"], ["Parameters", "1,089 (33 x 33)"], ["Smoothing", "0.15 on non-negative values"], ["Release", "(sum + noise) / n"]]
    set_table(shape(s, 9), rows, 12, header_size=12)
    set_paras(shape(s, 6), "A proxy for an LLM adapter update; pure Python, no neural network, no GPU.", 11)
    set_notes(s, "The abstract speaks of federated LLMs; the implemented model is a bigram language model whose parameter vector stands in for an adapter update. Orchestration and verification are separated from the model so a real adapter can replace it later.")

    # 9 training configuration
    s = S[8]
    set_paras(shape(s, 2), "Training configuration")
    rows = [["Setting", "Value"], ["Clients", "5 (Finance, Healthcare, Education, Retail, Travel)"], ["Clip norm C", "25"],
            ["Noise multiplier sigma", "3 (std 75 per coordinate)"], ["delta", "1e-5"], ["Reported epsilon", f"{dp['default_epsilon']:.4f}"],
            ["Random seed", "2026"], ["Certified if", "L2 <= 1e-10 and retention >= 70 %"]]
    set_table(shape(s, 10), rows, 13, header_size=13)
    p = pic(s, CHARTS / "c03_privacy_utility.png", (672, 180, 550, 340), remove_ids=(5,), name="Privacy-utility chart")
    frame_to(p, shape(s, 6))
    set_paras(shape(s, 7), "Reported epsilon against perplexity for 12 noise settings (20 seeds each)", 11)
    if p is not None:
        shape(s, 7).top = Emu(p.top + p.height + px(10))
    set_notes(s, f"Epsilon = sqrt(2 ln(1.25/delta)) / sigma. The classical Gaussian bound is valid only for epsilon < 1, which needs sigma above {dp['sigma_needed_for_epsilon_below_1']:.3f}; the default sigma = 3 is outside that range.")

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
            ["React UI (landing + 5 screens), legacy UI, Tkinter, CLI", "Completed"], ["Measurement suite: 11 experiments, 12 charts", "Completed"],
            ["Real LLM adapter, real datasets, privacy accountant, signed ledger", "Not done"]]
    set_table(shape(s, 15), rows, 13, widths=[0.72, 0.28], header_size=13)
    for vid, lid, v, lab in [(6, 7, "9", "API routes (8 JSON + legacy page)"), (9, 10, "5", "unit tests pass"), (12, 13, "14/14", "smoke-test checks pass")]:
        set_paras(shape(s, vid), v)
        set_paras(shape(s, lid), lab)
    set_notes(s, "All planned features run. The open items are a real LLM, real data, a privacy accountant and a signed ledger.")

    # 15 preliminary results
    s = S[14]
    set_paras(shape(s, 2), "Preliminary results: attack AUC against noise")
    pick = [r for r in sweep if r["noise_multiplier"] in (0.01, 0.1, 0.5, 1.0, 3.0, 10.0)]
    ch = replace_chart(s, 4, [f"sigma {r['noise_multiplier']:g}" for r in pick],
                       [("Before removal", [round(r["membership_auc_before"]["mean"], 3) for r in pick]),
                        ("After removal", [round(r["membership_auc_after"]["mean"], 3) for r in pick])], number_format="0.00")
    style_chart(ch, "Membership AUC before and after removal (20 seeds x 5 clients per sigma)", ["5B5BD6", "2F9E77"], number_format="0.00", legend=True, label_pt=10, axis_title="AUC (0.5 = chance)")
    ch.value_axis.maximum_scale = 1.1
    for vid, lid, v, lab in [(6, 7, f"{nf['mean_auc_before']:.2f} \u2192 {nf['mean_auc_after']:.2f}", "attack AUC with no noise, before \u2192 after removal"),
                             (9, 10, f"{seeds['pre_unlearning_perplexity']['mean']:.0f}", "perplexity at sigma 3 (uniform model = 32)"),
                             (12, 13, f"{seeds['status_counts']['CERTIFIED']}/{seeds['n_unlearning_requests']}", "requests certified (50 seeds x 5 clients)")]:
        set_paras(shape(s, vid), v)
        set_paras(shape(s, lid), lab)
    set_notes(s, f"At sigma 3 the attack is already near chance before removal ({seeds['membership_auc_before']['mean']:.2f} +/- {seeds['membership_auc_before']['sd']:.2f}), so there is little to remove. Without noise the attack is near-perfect and removal brings it to about 0.54. A fresh-noise retrain is as far from the unlearned model as two retrains are from each other: {g3['l2_unlearned_vs_fresh_retrain']['mean']:.0f} versus {g3['l2_fresh_retrain_vs_fresh_retrain']['mean']:.0f} at sigma 3. At sigma 0.1 the useful model has AUC {s_hi['membership_auc_before']['mean']:.2f} before and {s_hi['membership_auc_after']['mean']:.2f} after.")

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
    rows = [["Test group", "Count", "Result"], ["Unit tests (unittest)", "5", "5 passed"], ["Smoke test on the live API", "14", "14 passed"],
            ["Seed study, unlearning requests", f"{seeds['n_unlearning_requests']}", f"{seeds['status_counts']['CERTIFIED']} certified"],
            ["Audit tamper attacks", f"{n_attacks}", f"{detected} detected, {n_attacks - detected} not"],
            ["API edge cases", f"{len(api['edge_cases'])}", f"{len(api['edge_cases']) - n_bad} as intended, {n_bad} not"]]
    set_table(shape(s, 18), rows, 12, widths=[0.5, 0.12, 0.38], header_size=12)
    fit(s, 5, [f"Audit chain catches edits, deletions and re-ordering ({detected} of {n_attacks} attacks); tail truncation, a full re-hash forgery and an appended forged record pass.",
                f"API medians on 127.0.0.1: train {lat['POST /api/train']['p50_ms']:.0f} ms, unlearn {lat['POST /api/unlearn']['p50_ms']:.0f} ms, state {lat['GET /api/state (trained)']['p50_ms']:.0f} ms.",
                "A 2 MB body aborts the connection instead of a clean 400; PUT returns the stdlib HTML 501 page.",
                "No authentication; one shared engine for all callers.",
                "Not done: load, security and user-acceptance testing."], 16)
    set_notes(s, "Edge cases that returned the intended 400/404: unlearn before training, unknown client, malformed JSON, repeat removal, last client. Latency measured on an i5-12500 with a single client; the numbers shift between runs.")

    # 18 challenges
    s = S[17]
    cards(s, [(7, 8, "Noise swamps the model", f"At sigma 3 perplexity is {seeds['pre_unlearning_perplexity']['mean']:.0f} +/- {seeds['pre_unlearning_perplexity']['sd']:.0f} against 32 for a uniform model; accuracy about 4 %."),
              (12, 13, "Certificate is an identity", f"The reference re-uses the stored noise (L2 about 1e-14). A fresh-noise retrain study: {g3['l2_unlearned_vs_fresh_retrain']['mean']:.0f} versus {g3['l2_fresh_retrain_vs_fresh_retrain']['mean']:.0f}."),
              (17, 18, "Epsilon outside classical range", f"Reported epsilon {dp['default_epsilon']:.2f} exceeds 1; the bound needs sigma above {dp['sigma_needed_for_epsilon_below_1']:.3f}. Useful models need sigma 0.1 or less (epsilon 48 or more)."),
              (22, 23, "Attack has no signal", f"AUC {seeds['membership_auc_before']['mean']:.2f} +/- {seeds['membership_auc_before']['sd']:.2f} before removal at the default noise; {nf['mean_auc_before']:.2f} to {nf['mean_auc_after']:.2f} without noise."),
              (27, 28, "Ledger is tamper-evident only", f"{detected} of {n_attacks} attacks detected; truncation, re-hash forgery and forged append are not (no signature)."),
              (32, 33, "API robustness", "Oversized body aborts the connection; PUT gives an HTML 501 page; no authentication on any route.")], 14)
    set_notes(s, "Six findings from the measurement suite, each backed by experiments/*/metrics.json and docs/REPORT_FACTS.md.")
    for n, sid in enumerate((4, 9, 14, 19, 24, 29), 1):
        shape(S[17], sid).name = f"Challenge card {n}"
    for sh in S[17].shapes:
        if sh.shape_type == 13:
            sh._element.nvPicPr.cNvPr.set("descr", "icon")

    # 19 next steps
    s = S[18]
    for sid, tx in zip((5, 8, 11, 14), ["Honest certificate", "Privacy accounting", "Harden ledger and API", "Report and demo"]):
        fill(s, sid, tx, 16)
    fill(s, 15, ["Report an independent fresh-noise retrain comparison in the certificate next to the same-noise recomputation.",
                 "Add a privacy accountant, account for or re-draw the noise after unlearning, and use a calibrated Gaussian bound that is valid for epsilon above 1 [19].",
                 "Sign or anchor ledger records, authenticate requests and return a clean 400 for oversized bodies.",
                 "Complete the final report and demonstration; a LoRA adapter on a small LLM remains future work."], 16, bullet=True)
    set_notes(s, "Planned work, not yet done.")

    set_notes(S[19], "Thank you. Questions are welcome.")
    drop_orphan_images(prs)
    prs.save(OUT)
    scrub_zip(OUT)
    print("saved", OUT, len(prs.slides._sldIdLst), "slides; missing pictures:", sorted(set(MISSING)))


if __name__ == "__main__":
    build()
