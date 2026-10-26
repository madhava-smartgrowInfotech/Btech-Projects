"""Build 16.Final_PPT.pptx from D:\\abstracts\\Templates\\Final_PPT.pptx (28 slides) for ForgetSafe.

    python scripts/build_final.py
Every number comes from experiments/*/metrics.json (via doc_common.metrics) and docs/REPORT_FACTS.md.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deckkit import drop_slide_notes_text, fill, put_picture, set_notes, set_paras, set_table, shape, table_size  # noqa: E402
from doc_common import BATCH, CHARTS, DIAG, GUIDE, GUIDE_DESIG, PRODUCT, REFERENCES, SHOTS, STUDENTS, TITLE, YEAR, metrics  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.dml.color import RGBColor  # noqa: E402
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN  # noqa: E402
from pptx.util import Emu  # noqa: E402

DIAG = Path(os.environ.get("FS_DIAG", str(DIAG)))  # test override only
SRC = r"D:\abstracts\Templates\Final_PPT.pptx"
OUT = BATCH / "16.Final_PPT.pptx"
FOOT = "Dept. of CSE  |  Batch A9  |  Final Review"

# ------------------------------------------------------------------ measured numbers
BASE = metrics("baseline")
SEEDS = metrics("seeds")
SWEEP = {r["noise_multiplier"]: r for r in metrics("noise_sweep")["rows"]}
GOLD = {r["noise_multiplier"]: r for r in metrics("gold_retrain")["results"]}
NOFREE = metrics("noise_free_leakage")
TAMPER = metrics("audit_tamper")
SCALE = metrics("scaling")
API = metrics("api")["latency"]
DP = metrics("dp_accounting")
NN = metrics("neural_adapter")
NN0 = NN["summary"]["by_sigma"][0]
NN_S = {r["sigma"]: r for r in NN["summary"]["by_sigma"]}
NN_B = NN["base"]
NN_T = NN["summary"]["timing"]
SYN = metrics("synthetic_corpus")
SYN_G = {r["sigma"]: r for r in SYN["gold"]["results"]}
N_NEED = SYN["n_sweep"]["smallest_n_within_1_2x"]["4.85"]
SYN_R5 = next(r for r in SYN["n_sweep"]["rows"] if r["n_clients"] == 5 and abs(r["sigma"] - 4.85) < 1e-9)
LOAD = metrics("load_test")
SEC = metrics("security_probe")
SEC_C = SEC["classification_counts"]
ACC = metrics("acceptance")
LOAD_STATE = {x["concurrency"]: x for x in LOAD["scenarios"]["GET /api/state"]["levels"]}
RACE1 = LOAD["races"]["32 simultaneous unlearn requests for the same client"]["status_counts"]
T = BASE["training"]
S_PPL, S_AUCB, S_AUCA = SEEDS["pre_unlearning_perplexity"], SEEDS["membership_auc_before"], SEEDS["membership_auc_after"]
S_RET = SEEDS["utility_retention_percent"]
S_PPL_AFTER = SEEDS["perplexity_after_unlearning"]

COMPACT_REFS = [
    "[1] A. Khan et al., “Deep learning approaches for continuous sign language recognition: A comprehensive review,” IEEE Access, vol. 13, pp. 55524-55544, 2025 (base paper).",
    "[2] J. Wei et al., “Rethinking federated unlearning via the lens of memorization,” KDD ’26, 2026, arXiv:2605.24545.",
    "[3] F. Zhang et al., “Oblivionis: A lightweight learning and unlearning framework for federated large language models,” arXiv:2508.08875, 2025.",
    "[4] Y. Jiang et al., “Certifying the right to be forgotten: Primal-dual optimization ... in vertical federated learning,” arXiv:2512.23171, 2025.",
    "[5] “Federated illusion: Multi-level geometric privacy audit for federated graph unlearning,” Information, 2026 (batch survey; not verified).",
    "[6] “Computationally efficient federated unlearning,” Proc. 26th Int. Middleware Conf., 2025 (batch survey; not verified).",
    "[7] W. Zhang, “A comprehensive investigation of federated unlearning ...,” Proc. DAML, SciTePress, 2024, pp. 569-573.",
    "[8] “Unlearning under siege: Robustness risks of certified machine unlearning,” Neurocomputing, 2026 (batch survey; not verified).",
    "[9] H. B. McMahan et al., “Communication-efficient learning of deep networks from decentralized data,” AISTATS, 2017.",
    "[10] C. Dwork and A. Roth, “The algorithmic foundations of differential privacy,” Found. Trends Theor. Comput. Sci., 2014.",
    "[11] M. Abadi et al., “Deep learning with differential privacy,” ACM CCS, 2016.",
    "[12] L. Bourtoule et al., “Machine unlearning,” IEEE S&P, 2021.",
    "[13] C. Guo et al., “Certified data removal from machine learning models,” ICML, 2020.",
    "[14] A. Sekhari et al., “Remember what you want to forget: Algorithms for machine unlearning,” NeurIPS, 2021.",
    "[15] R. Shokri et al., “Membership inference attacks against machine learning models,” IEEE S&P, 2017.",
    "[16] S. Yeom et al., “Privacy risk in machine learning: Analyzing the connection to overfitting,” IEEE CSF, 2018.",
    "[17] G. Liu et al., “FedEraser: Enabling efficient client-level data removal from federated learning models,” IWQoS, 2021.",
    "[18] Y. Cao and J. Yang, “Towards making systems forget with machine unlearning,” IEEE S&P, 2015.",
    "[19] B. Balle and Y.-X. Wang, “Improving the Gaussian mechanism for differential privacy,” ICML, 2018.",
    "[20] European Parliament and Council, Regulation (EU) 2016/679 (GDPR), OJ L 119, 2016, Art. 17.",
    "[21] N. Carlini et al., “Extracting training data from large language models,” USENIX Security, 2021.",
    "[22] E. J. Hu et al., “LoRA: Low-rank adaptation of large language models,” ICLR, 2022.",
]


def panel(src, side, name):
    """Crop one half of a two-panel chart so it stays legible in a half-slide picture box (derived file next to the chart)."""
    from PIL import Image

    out = Path(src).with_name(name)
    with Image.open(src) as im:
        w, h = im.size
        box = (0, 0, w // 2 + 4, h) if side == "left" else (w // 2 - 4, 0, w, h)
        im.crop(box).save(out)
    return out


def pcent(x, d=1):
    return f"{100 * x:.{d}f} %"


def lat(key):
    v = API[key]
    return f"{v['p50_ms']:.1f} / {v['p95_ms']:.1f}"


def px(v):
    return Emu(int(v * 9525))


def table(s, rows, widths, max_pt=16, h=430, w=1180):
    sz = table_size(rows, w, h, widths, max_pt, 8)
    tshape = [sh for sh in s.shapes if sh.has_table][0]
    set_table(tshape, rows, sz, widths=widths, header_size=sz)


def title(s, text):
    set_paras(shape(s, 4), text)


def two_pics(s, left, right, cap_l, cap_r, box_h=352, top=182, cap_top=546):
    put_picture(s, left, (43, top, 576, box_h), remove_ids=(7,), name=cap_l)
    put_picture(s, right, (657, top, 576, box_h), remove_ids=(9,), name=cap_r)
    set_paras(shape(s, 8), cap_l, 13)
    set_paras(shape(s, 10), cap_r, 13)
    for cid in (8, 10):
        c = shape(s, cid)
        c.top = px(cap_top)
        c.height = px(100)


def diagram_with_panel(s, img, points, pic_box, panel_box, size=16):
    """Large diagram on the left, key points (the template's caption shape, moved and left-aligned) on the right."""
    put_picture(s, img, pic_box, remove_ids=(7,), name=Path(img).stem)
    cap = shape(s, 8)
    cap.left, cap.top, cap.width, cap.height = (px(v) for v in panel_box)
    fill(s, 8, ["\u2022  " + p for p in points], size, min_pt=11, gap_pt=6)
    for p in cap.text_frame.paragraphs:
        p.alignment = PP_ALIGN.LEFT
        for r in p.runs:
            r.font.italic = False
            r.font.color.rgb = RGBColor(0x26, 0x26, 0x26)
    cap.text_frame.vertical_anchor = MSO_ANCHOR.TOP


def purge_unused_images(prs):
    """Drop picture relationships whose shapes were removed, so template images do not stay inside the package."""
    from pptx.opc.constants import RELATIONSHIP_TYPE as RT

    for slide in prs.slides:
        xml = slide._element.xml
        for rid, rel in list(slide.part.rels.items()):
            if rel.reltype == RT.IMAGE and f'"{rid}"' not in xml:
                slide.part.drop_rel(rid)


def build():
    prs = Presentation(SRC)
    S = list(prs.slides)
    drop_slide_notes_text(prs)
    cp = prs.core_properties
    cp.title, cp.subject, cp.author = f"{PRODUCT}: Final Review", TITLE, "Batch A9"
    cp.keywords = "machine unlearning, federated learning, differential privacy, right to be forgotten, audit"
    cp.category = cp.comments = cp.content_status = ""
    cp.last_modified_by = "Batch A9"
    for s in S[1:]:
        for sh in s.shapes:
            if sh.has_text_frame and sh.text_frame.text.startswith("Dept. of CSE"):
                set_paras(sh, FOOT)

    # 1 title
    s = S[0]
    set_paras(shape(s, 4), TITLE)
    set_paras(shape(s, 5), "Final Review")
    set_paras(shape(s, 6), "Team Details : Batch A9")
    set_paras(shape(s, 7), [f"{r}   {n}" for n, r in STUDENTS], 16)
    set_paras(shape(s, 8), ["Under the Esteemed Guidance of", GUIDE, f"{GUIDE_DESIG}, Department of CSE (Data Science)"])
    set_paras(shape(s, 9), f"DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING (DATA SCIENCE)  \u00b7  Academic Year {YEAR}", 12)
    set_notes(s, "Final review of ForgetSafe: a certified federated-unlearning demonstrator with a tamper-evident compliance ledger.")

    # 2 contents
    s = S[1]
    fill(s, 7, ["Abstract", "Base Paper & Literature Survey", "Research Gap & Problem Statement", "Objectives", "Proposed System & Architecture", "Methodology & Algorithm",
                "Design & Implementation", "Results, Parameter Analysis, Testing & Comparison", "Output Screens", "Conclusion & Future Scope", "References"], 20, bullet=True)

    # 3 abstract
    s = S[2]
    fill(s, 7, ["Federated LLMs keep each client's data local, yet every client's influence stays in the shared parameters; GDPR Article 17 lets a user demand removal.",
                f"ForgetSafe is a runnable demonstrator: five simulated clients train a character-bigram model (1,089 parameters); a neural study applies the same method to LoRA-style adapters of a {NN_B['base_parameters']:,}-parameter GRU (8 synthetic clients). All data is synthetic.",
                "A client is removed by subtracting its tracked clipped update, with no retraining; each request gets a certificate, a membership-inference check, a utility check and a SHA-256 hash-chained audit record.",
                f"Measured: 250 bigram requests all CERTIFIED (retention {S_RET['mean']:.1f} % \u00b1 {S_RET['sd']:.1f}); neural client-level attack {NN0['client_auc_before']['mean']:.2f} \u2192 {NN0['client_auc_after']['mean']:.2f}, equal to a fresh retrain ({NN0['client_auc_retrain']['mean']:.2f}); subtraction {NN_T['speedup_retrain_over_unlearn_with_metrics']:.0f}x faster than retraining; 5 unit tests, 14 smoke checks, {SEC['n_probes']} security probes, {ACC['journeys_passed_all_steps']}/{ACC['journeys']} acceptance journeys.",
                f"Findings: at the default noise the product's model is worse than a uniform guess (perplexity {S_PPL['mean']:.0f} vs 32) and the attack is at chance; epsilon < 1 and a useful model coexist only for large federations (about {N_NEED:,} clients); the certificate check is an identity.",
                "Keywords: machine unlearning, federated learning, differential privacy, right to be forgotten, audit."], 16, bullet=True)
    set_notes(s, "Abstract: problem, approach, headline measurements and findings. Everything is measured on synthetic data.")

    # 4 base paper
    s = S[3]
    fill(s, 7, [REFERENCES[0],
                "What it is: a survey of deep-learning continuous sign language recognition; it organises the field into a taxonomy (spatial, temporal and alignment approaches), compares strengths and drawbacks and lists open gaps.",
                "Relevance: its subject is unrelated to unlearning. The batch records adopt only its review method: taxonomy, comparison of strengths and limitations, research-gap identification. No numeric comparison with it is possible and none is made.",
                "Technical anchor: Wei et al., KDD 2026 [2] - Grouped Memorization Evaluation and FedMemPrune, a pruning-based federated unlearning that closely matches retraining baselines on CIFAR-10, CIFAR-100 and EMNIST.",
                "Companion: Oblivionis [3], a federated LLM learning-and-unlearning framework motivated by GDPR."], 16, bullet=True)
    set_notes(s, "[1] is the base paper recorded in the batch files; [2] and [3] are the closest technical works, read from the PDFs in archived_base_papers.")

    # 5 literature survey
    s = S[4]
    rows = [["Author / Year", "Methodology", "Dataset", "Key Results", "Limitations"],
            ["Khan et al., 2025 (base) [1]", "Survey; taxonomy of sign-language recognition models", "Sign-language video datasets (surveyed)", "Taxonomy, challenges and gaps", "Unrelated subject; review method only"],
            ["Wei et al., KDD 2026 [2]", "Grouped Memorization Evaluation; FedMemPrune (prune memorising parameters)", "CIFAR-10, CIFAR-100, EMNIST; ResNet, VGG-9", "Closely matches retraining; removes memorisation better than federated-unlearning baselines", "Image classifiers, not LLM pipelines"],
            ["Zhang et al., 2025 (Oblivionis) [3]", "Unified FL + unlearning; 6 FL and 5 unlearning algorithms", "TOFU, MUSE; Llama-2-7B, Llama-3.1/3.2", "Beats local training; balances forgetting and utility", "Empirical comparison of algorithms; certification not its focus"],
            ["Jiang et al., 2025 (FedORA) [4]", "Primal-dual optimisation for sample/label unlearning", "Income, MedMNIST, CIFAR-10/100, Tiny-ImageNet", "Comparable to retraining at lower cost; bounded gap to train-from-scratch", "Vertical FL; not LLMs"],
            ["Zhang, 2024 [7]", "Short review of FedEraser, FedCIO, FedRecovery, F2UL", "Review (no data)", "Precision vs cost vs privacy-risk trade-offs", "5-page review"],
            ["Items [5], [6], [8]", "Titles in the batch survey", "Not retrieved", "Not retrieved", "Not independently verified; no claims made"]]
    table(s, rows, [0.18, 0.25, 0.19, 0.22, 0.16], 14, 500)
    set_notes(s, "[1]-[4] and [7] were read or verified; [5], [6] and [8] could not be found online, so nothing beyond their titles is claimed.")

    # 6 research gap
    s = S[5]
    rows = [["Source", "Research Gap"],
            ["Base paper [1]", "Reviews an unrelated field; it supplies a method of organising work, not an unlearning technique"],
            ["Memorization pruning, primal-dual [2], [4]", "Empirical or vertical-FL unlearning on image and tabular benchmarks; not designed for federated LLM pipelines; no per-request compliance record"],
            ["Federated LLM unlearning [3]", "Compares unlearning algorithms on TOFU and MUSE; evaluation is empirical (ROUGE, truth ratio); the abstract describes no certificate or regulator-facing audit record"],
            ["Reviews and audits [5]-[8]", "List challenges (efficiency, metrics, non-IID data) and robustness risks of certified unlearning (titles only for [5], [6], [8])"],
            ["Existing practice (batch survey)", "Full retraining is too costly; heuristic weight edits give no proof; SISA needs a sharded design; DP training limits influence but does not remove it"],
            ["Open problem", "Certified, auditable client-level unlearning for federated LLM pipelines. ForgetSafe builds the workflow and measures it on a bigram model and on neural LoRA-style adapters (synthetic data)"]]
    table(s, rows, [0.28, 0.72], 16, 500)
    set_notes(s, "The gap is the certified, auditable workflow. The prototype implements it and measures it at small scale on synthetic data; billion-parameter LLMs are outside its scope.")

    # 7 problem statement
    s = S[6]
    fill(s, 7, ["A client's influence remains embedded in the shared parameters of a federated LLM after training.",
                "Retraining a large federated model for every deletion request is impractical.",
                "Heuristic unlearning gives no formal proof that data was forgotten.",
                "Without verifiable unlearning a model cannot demonstrate compliance with the Right to Be Forgotten.",
                "Need: a certified unlearning framework that removes a client's influence efficiently and proves it to regulators and users - with an auditable record of every request."], 20, bullet=True)

    # 8 objectives
    s = S[7]
    fill(s, 7, [f"O1 Federated fine-tuning across clients - met at small scale: 5 bigram clients and 8 neural-adapter clients ({NN_B['base_parameters']:,}-parameter GRU); billion-parameter LLMs are outside the project's scope and hardware.",
                f"O2 Parameter-level unlearning without retraining - met: exact subtraction; {NN_T['subtract_us_median']:.0f} microseconds against {NN_T['retrain_seven_adapters_s_median']:.1f} s to retrain 7 adapters.",
                f"O3 Certify forgetting with DP guarantees - met as reported: epsilon {DP['default_epsilon']:.2f} at sigma 3 is outside the classical range; epsilon < 1 with a useful model needs about {N_NEED:,} clients; noise is reused.",
                "O4 Verify by membership inference and retraining comparison - met on three models; the fresh-noise retrain comparison agrees everywhere; the attack is informative where leakage exists.",
                f"O5 Preserve utility - met: {S_RET['mean']:.1f} % retention (bigram default), {NN_S[0.0]['retention_retained_ppl_percent']['mean']:.1f} % (neural, no noise), {NN_S[0.03]['retention_retained_ppl_percent']['mean']:.1f} % at sigma 0.03; {NN_S[0.1]['retention_retained_ppl_percent']['mean']:.0f} % at sigma 0.1 would be REVIEW_REQUIRED.",
                f"O6 Auditable record per request - met, with {SEC_C['defect']} measured defects: forgeable chain, empty ledger verifies, one bad line breaks the UI."], 16, bullet=True)

    # 9 proposed system
    s = S[8]
    fill(s, 7, ["Train - each client's bigram update is L2-clipped (C = 25); the coordinator adds Gaussian noise (sigma = 3) to the sum and averages.",
                "Track - the clipped update of every client is stored so it can be removed later.",
                "Request - an operator selects a client for removal (POST /api/unlearn).",
                "Unlearn - subtract the stored update, divide by n - 1: no retraining.",
                "Verify - retained-only recomputation (L2 <= 1e-10), loss-based membership attack, perplexity, accuracy and a 70 % retention floor.",
                "Certify - a certificate with epsilon, delta, hashes and metrics is issued and downloadable as JSON.",
                "Record - training and unlearning events are appended to a SHA-256 hash-chained ledger that anyone can re-verify."], 18, bullet=False)

    # 10 architecture
    s = S[9]
    diagram_with_panel(s, DIAG / "01_system_architecture.png",
                       ["React 19 + Vite UI on port 5109: dashboard, training, unlearning, explorer, audit; proxies /api",
                        "Python standard-library HTTP API on port 8109: 9 routes, JSON errors",
                        "Engine: clipping, noisy aggregation, unlearning, certification; bigram model; membership attack",
                        "Audit ledger: append-only JSONL, SHA-256 chain",
                        "No SQL database and no login: state lives in memory and the ledger file"],
                       (43, 178, 640, 494), (700, 200, 540, 440), 17)

    # 11 methodology
    s = S[10]
    put_picture(s, DIAG / "02_high_level_workflow.png", (57, 178, 1161, 424), remove_ids=(7,), name="High-level workflow")
    set_paras(shape(s, 8), "End-to-end workflow: train, track updates, request, subtract, verify, certify, record", 14)

    # 12 data, model, parameters
    s = S[11]
    title(s, "Data, Model & Parameters")
    fill(s, 7, [f"Data (all synthetic): the product's built-in corpus (5 clients x 5 sentences); a seeded 20-domain grammar corpus (200 train / 200 held-out sentences per client, 300 public); an 8-domain corpus for the neural study ({NN['config']['train_per_client']} train / {NN['config']['heldout_per_client']} held-out per client).",
                f"Models: character-bigram LM (33 x 33 = 1,089 parameters, add-0.15 smoothing); neural GRU ({NN_B['base_parameters']:,} parameters, frozen) with rank-{NN_B['adapter_rank']} LoRA-style adapters ({NN_B['adapter_dimension']:,} parameters per client).",
                f"Clipping: the product's C = 25 clips all five raw norms (25.2-28.2); at 200 sentences per client raw norms are about {SYN['raw_norms']['median']:,.0f} (C = 25 would scale them by {SYN['raw_norms']['scale_applied_by_product_C25']['mean']:.2f}), so the studies use C = median raw norm.",
                f"Noise: Gaussian, std sigma x C per coordinate; in the product 75 per coordinate, expected noise L2 = {DP['expected_noise_l2']:.0f} against a clipped client norm of 25.",
                f"Privacy: epsilon = sqrt(2 ln(1.25/delta)) / sigma = {DP['default_epsilon']:.4f} at sigma 3, delta = 1e-5; the classical bound needs epsilon < 1, i.e. sigma > {DP['sigma_needed_for_epsilon_below_1']:.3f}.",
                "Thresholds: reference tolerance 1e-10; retention floor 70 %; utility = 0.65 x accuracy + 0.35 / (1 + ln(1 + perplexity))."], 15, bullet=True)
    set_notes(s, "Three synthetic data sources and two models. The findings describe the algorithm and the demonstrator at small scale; billion-parameter LLMs are outside the project's scope and hardware.")

    # 13 decision workflow
    s = S[12]
    diagram_with_panel(s, DIAG / "10_algorithm_flowchart.png",
                       ["Guards: trained, client exists, not already removed, at least one client remains",
                        "Subtract the stored clipped update from the noisy sum; rebuild the model over n - 1 clients",
                        "Recompute the retained-only aggregate from stored updates and the same noise; L2 <= 1e-10 and retention >= 70 % gives CERTIFIED, otherwise REVIEW_REQUIRED",
                        "Append the certificate to the hash-chained ledger"],
                       (43, 178, 560, 494), (630, 210, 610, 420), 17)

    # 14 user-system interaction
    s = S[13]
    title(s, "User\u2013System Interaction")
    diagram_with_panel(s, DIAG / "09_sequence_diagram.png",
                       ["The UI calls POST /api/train; the engine clips, aggregates and logs a FEDERATED_TRAINING event",
                        "POST /api/unlearn runs unlearn(): subtract, rebuild, verify, issue the certificate and append the ledger record",
                        "GET /api/certificate/latest downloads the JSON; POST /api/audit/verify re-walks the hash chain"],
                       (43, 178, 560, 494), (630, 210, 610, 420), 17)

    # 15 data model
    s = S[14]
    title(s, "Data Model (no SQL database)")
    diagram_with_panel(s, DIAG / "06_er_diagram.png",
                       ["Session / engine: seed, clip norm, noise multiplier, delta",
                        "ClientDataset and ClientUpdate: records, clipped vector, original norm, clip scale",
                        "GlobalModel: 1,089 parameters and a SHA-256 model hash",
                        "UnlearningCertificate: 25 fields incl. metrics and hashes; one AuditRecord per event, chained by previous_hash"],
                       (43, 178, 560, 494), (630, 210, 610, 420), 17)

    # 16 implementation highlights
    s = S[15]
    rows = [["Module", "Implementation"],
            ["model.py", "Bigram counts, L2 clipping, perplexity, next-character accuracy, loss-based membership AUC, sampling"],
            ["engine.py", "train(): clip, sum, add noise; unlearn(): subtract, rebuild, verify, certificate; epsilon formula; guards for repeat and last client"],
            ["audit.py", "Append-only JSONL; record_hash = SHA-256(previous_hash | canonical JSON); verify() re-walks the chain"],
            ["web.py + app.py", "Standard-library threaded HTTP server; 9 routes; 1 MB body limit; JSON errors; also --demo and --desktop modes"],
            ["frontend/", "React 19, Vite 8, Recharts; five pages plus landing; toasts, confirm dialogs, dark mode"],
            ["tests/ + scripts/", "5 unit tests, 14-check smoke test, and four measurement scripts: run_experiments.py, run_synthetic_corpus.py, run_neural_experiment.py, run_testing_experiments.py"]]
    table(s, rows, [0.18, 0.82], 18, 500)

    # 17 results
    s = S[16]
    title(s, "Results \u2013 Measured Performance")
    rows = [["Measure", "Result", "Note"],
            ["Default run (seed 2026), 5 removals", "5 / 5 CERTIFIED", f"reference L2 <= {BASE['max_reference_l2']:.1e}; retention {BASE['min_retention_percent']:.1f}-98.8 %"],
            ["Seed study, 250 requests", f"250 / 250 CERTIFIED", f"retention {S_RET['mean']:.1f} \u00b1 {S_RET['sd']:.1f} % (min {S_RET['min']:.1f})"],
            ["Perplexity at sigma = 3", f"{T['perplexity']:.1f} (seed 2026); {S_PPL['mean']:.0f} \u00b1 {S_PPL['sd']:.0f}", "uniform model = 32; accuracy about 4-5 %"],
            ["Membership AUC before / after", f"{S_AUCB['mean']:.3f} / {S_AUCA['mean']:.3f}", f"chance = 0.5; sd {S_AUCB['sd']:.2f}; change {SEEDS['membership_auc_change']['mean']:+.3f}"],
            ["Unlearned vs fresh retrain (L2)", f"bigram {GOLD[3.0]['l2_unlearned_vs_fresh_retrain']['mean']:.0f} vs {GOLD[3.0]['l2_fresh_retrain_vs_fresh_retrain']['mean']:.0f}; synthetic corpus {SYN_G[0.1]['l2_unlearned_vs_fresh_retrain']['mean']:.0f} vs {SYN_G[0.1]['l2_fresh_retrain_vs_fresh_retrain']['mean']:.0f}; neural {NN_S[0.1]['l2_unl_vs_retrain']['mean']:.1f} vs {NN_S[0.1]['l2_retrain_vs_retrain']['mean']:.1f}", "unlearned vs retrain equals retrain vs retrain; both are just the noise"],
            ["Noise-free attack AUC", f"bigram {NOFREE['mean_auc_before']:.2f} \u2192 {NOFREE['mean_auc_after']:.2f}; neural client-level {NN0['client_auc_before']['mean']:.2f} \u2192 {NN0['client_auc_after']['mean']:.2f}", f"fresh retrain {NN0['client_auc_retrain']['mean']:.2f}: the removal itself works"],
            ["Neural adapters, retention", f"{NN_S[0.0]['retention_retained_ppl_percent']['mean']:.1f} % (no noise); {NN_S[0.05]['retention_retained_ppl_percent']['mean']:.0f} % (sigma 0.05)", f"useful only for sigma <= 0.05; destroyed from sigma 0.3"],
            ["Clients for epsilon < 1 (synthetic corpus)", f"about {N_NEED:,}", "perplexity within 1.2x of noise-free at sigma 4.85"],
            ["Audit tamper cases detected", "4 of 7 attacks", "edit, flip, delete, swap caught; truncation and re-hash forgery not"]]
    table(s, rows, [0.30, 0.38, 0.32], 15, 500)
    set_paras(shape(s, 8), "All data synthetic: 25-sentence bigram product, 20-domain corpus, 137k-parameter neural GRU. Results describe the method at this scale, not a billion-parameter LLM.", 13)
    set_notes(s, "The headline certificate result is an identity; the fresh-noise retrain comparison and the noise-free attack supply the real evidence, on three models. Automated checks (5 unit tests, 14 smoke checks, load, security probes, acceptance journeys) are on the performance and testing slide.")

    # 18 per-client table and tamper matrix (equivalent of a confusion matrix)
    s = S[17]
    title(s, "Attack Outcomes & Tamper-Detection Matrix")
    two_pics(s, panel(CHARTS / "n02_neural_membership_auc.png", "left", "n02a_neural_client_level_auc.png"), CHARTS / "c10_audit_tamper.png",
             f"Neural adapters: client-level attack AUC {NN0['client_auc_before']['mean']:.2f} → {NN0['client_auc_after']['mean']:.2f} after removal = fresh retrain ({NN0['client_auc_retrain']['mean']:.2f}); the sample-level AUC stays near 0.5 at every sigma",
             "Ledger tamper matrix: 4 of 7 attacks detected; truncation, re-hash forgery and forged append pass")
    set_notes(s, "There is no classifier here, so the equivalent of a confusion matrix is the before / after / fresh-retrain attack outcome (here for the neural study; the bigram per-client table is in the report) and the detected / not-detected matrix of tamper attacks.")

    # 19 parameter analysis
    s = S[18]
    title(s, "Parameter Analysis: Federation Size and Noise")
    two_pics(s, CHARTS / "s03_clients_needed_for_epsilon_below_1.png", panel(CHARTS / "n01_neural_noise_vs_quality.png", "right", "n01b_neural_retention.png"),
             f"Synthetic corpus: epsilon < 1 (sigma 4.85) needs about {N_NEED:,} clients to come within 1.2x of the noise-free perplexity; with 5 clients the ratio is {SYN_R5['ratio_to_noise_free']:.0f}x",
             f"Neural adapters: useful only for sigma <= 0.05 (epsilon >= {NN_S[0.05]['epsilon']:.0f}); retention {NN_S[0.03]['retention_retained_ppl_percent']['mean']:.1f} % at 0.03, {NN_S[0.1]['retention_retained_ppl_percent']['mean']:.0f} % at 0.1; destroyed from 0.3",
             box_h=330)
    set_notes(s, f"Left: synthetic corpus, 100 sentences per client, C = median norm, 5 seeds per point. Right: neural study, 8 clients, 5 seeds. Product sweep (5 clients, 20 seeds x 5 clients per sigma): useful only at sigma <= 0.1 (epsilon >= {SWEEP[0.1]['epsilon']:.0f}); at sigma 3 perplexity is {SWEEP[3.0]['perplexity']['mean']:.0f}; epsilon < 1 needs sigma > 4.85, where perplexity is 198-305.")

    # 20 performance & testing
    s = S[19]
    ledger = SCALE["ledger_append_ms_at_length"]
    r500 = SCALE["rows"][-1]
    rows = [["Measurement", "Result"],
            ["API response, median / p95 (ms, 127.0.0.1)", f"health {lat('GET /api/health')}; train {lat('POST /api/train')}; unlearn {lat('POST /api/unlearn')}; generate {lat('POST /api/generate')}; audit verify {lat('POST /api/audit/verify')}"],
            ["Unlearn vs retrain (proxy)", f"5 clients: {SCALE['rows'][0]['unlearn_ms_median']:.0f} vs {SCALE['rows'][0]['full_retrain_ms_median']:.0f} ms (unlearn slower); 100 clients 1.4x faster; {r500['clients']} clients ({r500['total_records']:,} records) {r500['speedup_retrain_over_unlearn']:.1f}x faster"],
            ["Neural adapters: unlearn vs retrain", f"subtraction {NN_T['subtract_us_median']:.0f} microseconds; with metrics and attack {NN_T['unlearn_with_metrics_ms_median']:.0f} ms; retraining the 7 retained adapters {NN_T['retrain_seven_adapters_s_median']:.1f} s ({NN_T['speedup_retrain_over_unlearn_with_metrics']:.0f}x)"],
            ["Load and concurrency (1-64 clients)", f"/api/state saturates near {max(x['requests_per_s'] for x in LOAD_STATE.values()):.0f} req/s (ledger re-read per call); 32 simultaneous removals of one client: {RACE1['200']} success, {RACE1['400']} refused; 16 simultaneous trainings: valid chain; 2,000-request soak: 0 errors"],
            ["Ledger cost", f"append re-reads the file: {ledger['1']:.2f} ms at 1 record, {ledger['2000']:.1f} ms at 2,000; verify 2,000 records {SCALE['ledger_verify_2000_ms']:.0f} ms"],
            ["Automated tests", f"5 unit tests and 14 smoke checks pass; {ACC['journeys_passed_all_steps']}/{ACC['journeys']} scripted synthetic-user journeys pass ({ACC['total_certificates_checked']} certificates, 0 console errors)"],
            ["Security probes", f"{SEC['n_probes']} probes: {SEC_C['handled']} handled, {SEC_C['noteworthy']} noteworthy, {SEC_C['defect']} defects (no read timeout, cross-site POST accepted, Host unchecked, connection bursts refused, empty ledger verifies, bad ledger line breaks the UI, no authentication)"]]
    table(s, rows, [0.22, 0.78], 15, 500)
    set_notes(s, "Machine: Intel Core i5-12500, 15.7 GB RAM, no GPU. Latencies are single-client medians; proxy retraining is itself cheap, so the bigram numbers say nothing about larger models; the neural row is the measured cost for 7 adapters of 14,272 parameters.")

    # 21 comparison
    s = S[20]
    title(s, "Comparison with Base Paper and Closest Work (context only)")
    rows = [["System", "Task and data", "Method", "Reported / measured", "Guarantee and audit", "Comparable?"],
            ["Base paper [1]", "Review of continuous sign language recognition", "Taxonomy of spatial, temporal, alignment models", "No unlearning results", "-", "No: unrelated subject"],
            ["Wei et al. [2] (KDD 2026)", "Federated unlearning on CIFAR-10/100, EMNIST", "FedMemPrune: prune memorising parameters", "Closely matches retraining baselines", "Empirical memorisation metric", "No: images, not LLMs"],
            ["Oblivionis [3]", "Federated LLM unlearning on TOFU, MUSE (Llama models)", "6 FL x 5 unlearning algorithms", "Beats local training; forgetting/utility balance", "Empirical metrics (ROUGE, truth ratio)", "No: real LLMs"],
            ["ForgetSafe (ours)", "Bigram product (5 clients) and neural LoRA-style adapters (8 clients), synthetic text", "Tracked-update subtraction, DP release bound, verification, hash ledger", f"250/250 certified; neural client AUC {NN0['client_auc_before']['mean']:.2f} → {NN0['client_auc_after']['mean']:.2f} = fresh retrain", "Certificate + hash-chained ledger (forgeable)", "-"]]
    table(s, rows, [0.12, 0.2, 0.2, 0.18, 0.17, 0.13], 15, 500)
    set_paras(shape(s, 8), "Different tasks, data and metrics: no numeric head-to-head is possible. The comparison is of scope and approach, and ForgetSafe is a small demonstrator.", 13)
    set_notes(s, "State plainly: no claim that ForgetSafe beats any of these works.")

    # 22-24 outputs
    s = S[21]
    title(s, "Output \u2013 Training and Dashboard")
    two_pics(s, SHOTS / "04_training_trained.png", SHOTS / "12_dashboard_after_unlearning.png",
             "Federated training: 5 clients, epsilon 1.6149, perplexity 130.22, accuracy 5.1 %, clipped norms 25.000",
             "Dashboard after two removals: 3 of 5 clients active, latest certificate shown")
    s = S[22]
    title(s, "Output \u2013 Certified Unlearning")
    two_pics(s, SHOTS / "08_unlearning_confirm.png", SHOTS / "09_unlearning_certificate.png",
             "Confirmation dialog before removing Client 01 (Finance)",
             "Certificate CERT-C5427F948A72: epsilon 1.6149, retention 93.65 %, AUC 0.200 \u2192 0.160")
    s = S[23]
    title(s, "Output \u2013 Model Explorer and Audit Ledger")
    two_pics(s, SHOTS / "10_explorer_after_unlearning.png", SHOTS / "13_audit_ledger.png",
             "Sample text from the 4-client model: seed \u201cprivacy\u201d continues as noise-like characters",
             "Ledger of 4 events (2 training, 2 unlearning); hash chain verified")

    # 25 conclusion
    s = S[24]
    fill(s, 7, ["Built ForgetSafe: federated training, tracked-update subtraction, DP release bound, membership and utility checks, certificates and a hash-chained ledger, with a React UI and a JSON API.",
                f"Measured on synthetic data: 250 of 250 bigram requests certified; neural adapters: client-level attack {NN0['client_auc_before']['mean']:.2f} → {NN0['client_auc_after']['mean']:.2f} = fresh retrain, removal {NN_T['speedup_retrain_over_unlearn_with_metrics']:.0f}x faster than retraining; 5 unit tests, 14 smoke checks, {ACC['journeys_passed_all_steps']}/{ACC['journeys']} acceptance journeys.",
                f"Key findings: at the product's sigma = 3 the model is worse than uniform (perplexity {S_PPL['mean']:.0f} vs 32); the certificate check is an identity, so the fresh-noise retrain comparison is the real evidence; with no noise the attack falls from {NOFREE['mean_auc_before']:.2f} to {NOFREE['mean_auc_after']:.2f}; epsilon < 1 with a useful model needs about {N_NEED:,} clients.",
                f"Measured defects to fix: forgeable ledger, empty ledger verifies, no read timeout, cross-site POST accepted, no authentication ({SEC_C['defect']} of {SEC['n_probes']} probes).",
                "All six objectives are met at the scale of the demonstrator (bigram product, 8-client neural adapter study); the batch's billion-parameter setting is outside the project's scope."], 18, bullet=True)

    # 26 future scope
    s = S[25]
    fill(s, 7, ["Extend the adapter study to LoRA on a small pretrained Hugging Face language model with Flower for transport.",
                "Add a privacy accountant, the exact analytic Gaussian bound [19] (epsilon 1.27 at sigma 3) and fresh noise per release; target federations of about 1,000 clients for epsilon < 1.",
                "Sign ledger records and anchor the head hash externally; add authentication, CSRF protection, read timeouts and a check that rejects an emptied ledger.",
                "Stronger attacks (shadow models, extraction tests [21]) and a fresh-noise retrain reference inside every certificate.",
                "Batched ledger append and a ledger index so state reads stay fast as the history grows."], 20, bullet=True)

    # 27 references
    s = S[26]
    fill(s, 7, COMPACT_REFS, 11, min_pt=9, bullet=True, gap_pt=2)

    set_notes(S[27], "Thank you. Questions are welcome.")
    purge_unused_images(prs)
    prs.save(OUT)
    print("saved", OUT, len(prs.slides._sldIdLst), "slides")


if __name__ == "__main__":
    build()
