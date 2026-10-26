"""Build 7.Review_1_PPT.pptx from D:\\abstracts\\Templates\\Review_1_PPT.pptx (16 slides).

Every number comes from experiments/*/metrics.json via doc_common.metrics (the same numbers as docs/REPORT_FACTS.md).
"""
from __future__ import annotations

import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deckkit import fill, put_picture, remove, replace_chart, set_notes, set_paras, set_table, shape, style_chart, table_size  # noqa: E402
from doc_common import BATCH, COLLEGE, DEPT, DIAG, GUIDE, GUIDE_DESIG, PRODUCT, REFERENCES, STUDENTS, TITLE, YEAR, metrics  # noqa: E402
from pptx import Presentation  # noqa: E402

SRC = r"D:\abstracts\Templates\Review_1_PPT.pptx"
OUT = BATCH / "7.Review_1_PPT.pptx"
MISSING: list[str] = []


def scrub_zip(path, extra=None):
    """Rename template theme/brand strings inside the package (theme names are not reachable through python-pptx)."""
    tmp = Path(str(path) + ".tmp")
    repl = {"Hidden Risk": PRODUCT}
    repl.update(extra or {})
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.endswith(".xml") or item.filename.endswith(".rels"):
                text = data.decode("utf-8")
                for a, b in repl.items():
                    text = text.replace(a, b)
                data = text.encode("utf-8")
            zout.writestr(item, data)
    shutil.move(tmp, path)


def pic(slide, path, box, remove_ids=(), name=None):
    """put_picture that tolerates a diagram that is not generated yet (the template picture is still removed)."""
    path = Path(path)
    if not path.exists():
        MISSING.append(path.name)
        for sid in remove_ids:
            remove(slide, sid)
        return None
    return put_picture(slide, path, box, remove_ids=remove_ids, name=name)


def fit(s, sid, paras, size, **kw):
    """Set text at an explicit size (the template's own size is smaller than the boxes need)."""
    set_paras(shape(s, sid), paras, size)


def footers(prs, text):
    for lay in prs.slide_layouts:
        for sh in lay.shapes:
            if sh.has_text_frame and sh.text_frame.text.startswith("The Hidden Risk"):
                set_paras(sh, text)
    for m in prs.slide_masters:
        for sh in m.shapes:
            if sh.has_text_frame and sh.text_frame.text.startswith("The Hidden Risk"):
                set_paras(sh, text)
    for sl in prs.slides:
        for sh in sl.shapes:
            if sh.has_text_frame and sh.text_frame.text.startswith("The Hidden Risk"):
                set_paras(sh, text)


def drop_orphan_images(prs):
    """Removing a picture shape leaves its image part in the package: drop every unreferenced slide image relationship."""
    for sl in prs.slides:
        xml = sl._element.xml
        for rid, rel in list(sl.part.rels.items()):
            if rel.reltype.endswith("/image") and f'"{rid}"' not in xml:
                sl.part.drop_rel(rid)


def title_slide(s, label_note):
    set_paras(shape(s, 2), PRODUCT)
    set_paras(shape(s, 3), TITLE, 18)
    set_paras(shape(s, 6), [f"{n}  {r}" for n, r in STUDENTS], 15)
    set_paras(shape(s, 8), f"{GUIDE}, {GUIDE_DESIG}")
    set_paras(shape(s, 9), [DEPT, f"{COLLEGE}  \u00b7  Batch A9 (CSE-DS, Section A)  \u00b7  {YEAR}"], 13)
    set_notes(s, label_note)


def build():
    nf = metrics("noise_free_leakage")
    seeds = metrics("seeds")
    nn0 = metrics("neural_adapter")["summary"]["by_sigma"][0]
    nn_b = metrics("neural_adapter")["base"]
    prs = Presentation(SRC)
    S = list(prs.slides)
    cp = prs.core_properties
    cp.title, cp.subject, cp.author = f"{PRODUCT}: Review 1", TITLE, "Batch A9"
    cp.keywords = "federated unlearning, differential privacy, right to be forgotten, membership inference, audit ledger"
    cp.category = cp.comments = cp.content_status = ""
    cp.last_modified_by = "Batch A9"
    footers(prs, f"{PRODUCT}  \u00b7  Review 1  \u00b7  Batch A9")

    # 1 title
    title_slide(S[0], "Review 1 covers problem identification and research for ForgetSafe, a demonstrator of certified client-level unlearning for federated language models.")

    # 2 contents (template labels are generic and fit)
    set_notes(S[1], "Nine parts: abstract, base paper, literature survey, existing approaches and limitations, research gap, problem statement and objectives, proposed approach and architecture, expected outcomes and references.")

    # 3 abstract
    s = S[2]
    set_paras(shape(s, 2), "Abstract: removing a client without retraining")
    fit(s, 8, "A federated LLM keeps every client's influence in its shared parameters. The GDPR lets a user demand erasure, but retraining a large model for each request is impractical and heuristic unlearning gives no proof of forgetting.", 15)
    fit(s, 13, "Track each client's clipped update, subtract it on request, bound the noisy release with differential privacy, verify with a membership-inference test and a retained-only recomputation, and chain every request in a SHA-256 audit ledger.", 15)
    fit(s, 18, "ForgetSafe: a Python API (port 8109) and React UI (port 5109) that issue a certificate per request. The engine runs on a character-bigram model and, in a second study, on a neural GRU with LoRA-style adapters, both on synthetic data.", 15)
    set_notes(s, "The problem, the idea and the deliverable. The prototype is a demonstrator on small models and synthetic data; the later reviews report what it proves and what it measures.")

    # 4 base paper
    s = S[3]
    fill(s, 5, REFERENCES[0], 14)
    set_paras(shape(s, 7), "Method")
    fit(s, 8, "A review of deep-learning approaches to continuous sign-language recognition. It builds a taxonomy (sign language, data collection, input method, gesture signals, identification methods, datasets) and groups models by spatial, temporal and alignment approach.", 15)
    set_paras(shape(s, 10), "Scope")
    fit(s, 11, "Compares the strengths and drawbacks of the approaches and names open gaps: real-time processing, diverse datasets and signer variability. It is a literature review; its subject differs from this project, so no result is compared with ours.", 15)
    set_paras(shape(s, 13), "What this project adopts")
    fit(s, 14, "Only its review method: organise approaches into a taxonomy, compare strengths and limitations, state the gap. It is applied here to federated unlearning. Closest technical works: Wei et al., KDD 2026 [2] and Oblivionis [3].", 15)
    set_notes(s, "The base paper recorded in the batch files is a sign-language survey. Its subject is unrelated, so only its review method is adopted. The technical comparison in the later reviews is qualitative against [2] to [4].")

    # 5 literature survey
    s = S[4]
    rows = [["Work", "Approach", "Data", "Reported result"],
            ["Khan et al., 2025 (base paper) [1]", "Survey and taxonomy of deep-learning CSLR models", "Sign-language literature", "Review; no unlearning content"],
            ["Wei et al., KDD 2026 [2]", "FedMemPrune: prune parameters responsible for memorised data (Grouped Memorization Evaluation)", "Federated benchmarks (see paper)", "Closely matches retraining baselines; removes memorisation better than other FU methods (abstract)"],
            ["Zhang et al., Oblivionis, 2025 [3]", "Federated LLM learning and unlearning framework; 6 FL and 5 unlearning algorithms", "LLM fine-tuning tasks (see paper)", "Balances forgetting and utility; outperforms local training (abstract)"],
            ["Jiang et al., FedORA, 2025 [4]", "Primal-dual unlearning for vertical FL with a bound to train-from-scratch", "Tabular and image datasets", "Effectiveness and utility comparable to retraining with less computation (abstract)"],
            ["W. Zhang, DAML 2024 [7]", "Review of FedEraser, FedCIO, FedRecovery, F2UL", "None (review)", "Precision versus cost trade-off; future work: metrics, efficiency, Non-IID"],
            ["Items [5], [6], [8] in the batch survey", "Federated graph audit; efficient FU; robustness of certified unlearning (titles only)", "Not retrieved", "Not independently verified; no claim made"]]
    sz = table_size(rows, 1164, 500, [0.20, 0.34, 0.18, 0.28], 12, 11)
    set_table(shape(s, 6), rows, sz, header_size=sz)
    set_notes(s, "Entries [1] to [4] and [7] were read or verified online. Entries [5], [6] and [8] come from the batch literature survey and could not be found, so only their titles are used. The results shown for [2] to [4] are taken from their abstracts and are on other tasks, so they are not comparable with ours.")

    # 6 supporting evidence
    s = S[5]
    set_paras(shape(s, 2), "Supporting evidence: influence stays in the parameters")
    rows_nf = nf
    ch = replace_chart(s, 4, ["No noise, before removal", "No noise, after removal", "Default noise, before removal", "Default noise, after removal"],
                       [("Membership AUC", [round(rows_nf["mean_auc_before"], 3), round(rows_nf["mean_auc_after"], 3),
                                            round(seeds["membership_auc_before"]["mean"], 3), round(seeds["membership_auc_after"]["mean"], 3)])], number_format="0.000")
    style_chart(ch, "Loss-based membership attack AUC on a client's own sentences (0.5 = chance)", ["5B5BD6"], number_format="0.000", legend=False, label_pt=12, axis_title="AUC")
    ch.value_axis.maximum_scale = 1.1
    set_paras(shape(s, 8), "Takeaway")
    fill(s, 9, f"With no DP noise, an attacker recognises a client's own sentences almost perfectly (AUC {nf['mean_auc_before']:.2f}). Subtracting the tracked update brings it to {nf['mean_auc_after']:.2f}. At the default noise the attack is already near chance ({seeds['membership_auc_before']['mean']:.2f}).", 14)
    set_paras(shape(s, 13), "Caveat")
    fill(s, 14, f"Synthetic-data measurements: the 25-sentence bigram model above, and a {nn_b['base_parameters']:,}-parameter neural GRU with LoRA-style adapters (8 clients), where the client-level attack falls from {nn0['client_auc_before']['mean']:.2f} to {nn0['client_auc_after']['mean']:.2f}, the same as a fresh retrain ({nn0['client_auc_retrain']['mean']:.2f}). Literature [2]-[4], [7] motivates the problem.", 14)
    set_notes(s, "No-noise = noise multiplier 1e-6, five clients, one removal each. Default noise = sigma 3, mean over 50 seeds x 5 clients (250 requests). Both come from experiments/noise_free_leakage and experiments/seeds. The neural figures come from experiments/neural_adapter (sigma 0, 5 seeds x 8 clients).")

    # 7 existing system
    s = S[6]
    set_paras(shape(s, 2), "Existing system and current approaches")
    steps = ["Client data joins federated training", "Deletion request arrives", "Retrain without the client", "Or edit weights heuristically", "Or retrain only a shard (SISA)", "No proof for the regulator"]
    for sid, t in zip((5, 8, 11, 14, 17, 20), steps):
        fill(s, sid, t, 14)
    set_paras(shape(s, 24), "Retraining and approximate unlearning")
    fill(s, 25, "Full retraining without the deleted client, or approximate unlearning by gradient ascent or heuristic weight adjustment.", 16)
    set_paras(shape(s, 29), "Shards and training-time DP")
    fill(s, 30, "SISA-style sharded training retrains only the affected shards; differential privacy during training limits any one person's influence.", 16)
    set_notes(s, "The four existing approaches listed in the batch literature survey.")

    # 8 limitations
    s = S[7]
    set_paras(shape(s, 2), "Limitations of existing methods")
    for tid, bid, ttl, body in [
        (7, 8, "Too expensive", "Full retraining is too costly for large federated LLMs."),
        (12, 13, "No formal guarantee", "Heuristic methods give no formal guarantee that data is forgotten."),
        (17, 18, "Not auditable", "Unlearning is not verifiable or auditable for regulators."),
        (22, 23, "Utility and scope", "Aggressive unlearning degrades utility; most methods target centralised models, not federated LLM pipelines.")]:
        set_paras(shape(s, tid), ttl)
        fill(s, bid, body, 16)
    set_notes(s, "Limitations as stated in the batch literature survey.")

    # 9 research gap
    s = S[8]
    gaps = [("Guarantee", "Federated unlearning mostly removes client influence heuristically; certified unlearning for federated LLM pipelines is open."),
            ("Verification", "Membership-inference tests and comparison with retraining are not built into one removal workflow."),
            ("Audit", "The survey finds unlearning neither verifiable nor auditable for regulators; each request needs its own record."),
            ("Utility", "Aggressive unlearning degrades utility, so retained quality must be checked after every removal."),
            ("Setting", "Most methods target centralised models rather than federated LLMs [3].")]
    for (lid, tid), (lab, txt) in zip([(5, 6), (8, 9), (11, 12), (14, 15), (17, 18)], gaps):
        set_paras(shape(s, lid), lab)
        fit(s, tid, txt, 16)
    set_notes(s, "The gap is the one stated in the batch survey: certified, auditable unlearning designed for federated LLM pipelines remains an open problem. The audit and utility rows restate the survey's limitation list.")

    # 10 problem statement
    s = S[9]
    fill(s, 5, "Given a trained federated model and a client's deletion request, remove that client's influence without retraining from scratch, bound the privacy of the released model, verify the removal with a membership-inference test and a retained-only recomputation, keep the model useful for the remaining clients, and leave an auditable record that can be shown to a regulator.", 21)
    set_paras(shape(s, 8), "Trained federated model + a client's deletion request")
    set_paras(shape(s, 11), "Updated model + certificate (DP bound, attack, utility)")
    set_paras(shape(s, 14), "Hash-chained audit record")
    set_notes(s, "Inputs, outputs and the extra property: every request is recorded in a tamper-evident ledger.")

    # 11 objectives
    s = S[10]
    fit(s, 4, ["Set up federated fine-tuning of an LLM across multiple clients.",
                "Remove a client's influence by parameter-level unlearning without full retraining.",
                "Certify forgetting with differential-privacy based guarantees.",
                "Verify unlearning with membership-inference tests and comparison with retraining.",
                "Preserve model utility on the remaining data.",
                "Provide auditable compliance records for each unlearning request."], 26)
    set_notes(s, "The six objectives of the batch file. Each is measured against the outcome in the later reviews and the final report.")

    # 12 proposed approach
    s = S[11]
    for tid, bid, ttl, body in [
        (7, 8, "Federated training", "Five simulated clients; each update is L2-clipped (C = 25) and stored; Gaussian noise is added to the sum."),
        (12, 13, "Parameter-level unlearning", "Subtract the tracked update, renormalise over the retained clients; no retraining and no raw data."),
        (17, 18, "DP certificate", "Epsilon and delta from the Gaussian-mechanism bound, plus a recomputation from the retained updates."),
        (22, 23, "Verification", "Loss-based membership AUC, perplexity, next-character accuracy and utility retention per request."),
        (27, 28, "Audit and application", "SHA-256 hash-chained ledger; Python API and React UI. Shown on a bigram model and on neural LoRA-style adapters (synthetic data).")]:
        set_paras(shape(s, tid), ttl)
        fit(s, bid, body, 12)
    set_notes(s, "The approach in five blocks. The same clip, noisy-sum, subtraction, verification and audit workflow runs on the bigram model and on LoRA-style adapters of a small GRU (neural study, synthetic data).")

    # 13 architecture
    s = S[12]
    pic(s, DIAG / "01_system_architecture.png", (215, 118, 790, 482), remove_ids=(4,), name="System architecture diagram")
    set_paras(shape(s, 5), "Proposed architecture: React UI, Python API, federated unlearning engine, bigram model and hash-chained ledger")
    set_notes(s, "Browser to React to the Python API; the engine trains, unlearns and verifies; every event is appended to the JSONL ledger.")

    # 14 expected outcomes
    s = S[13]
    for tid, bid, ttl, body in [
        (7, 8, "Removal without retraining", "A client's update is subtracted from the global model in one step."),
        (12, 13, "A certificate per request", "Epsilon, delta, clipping norm, noise and model hashes in one JSON record."),
        (17, 18, "Attack evidence", "Membership AUC before and after each removal."),
        (22, 23, "Utility check", "Perplexity, accuracy and a retention score for the retained model."),
        (27, 28, "Tamper-evident record", "Every training and unlearning event chained with SHA-256."),
        (32, 33, "Working demonstrator", "Python API and React UI that run offline on one PC, plus the same method on a small neural adapter model.")]:
        set_paras(shape(s, tid), ttl)
        fill(s, bid, body, 16)
    set_notes(s, "Expected outcomes are targets at this stage; what was actually achieved, including the shortfalls, is reported in the later reviews.")

    # 15 references
    s = S[14]
    short = ["[1] A. Khan et al., Deep learning approaches for continuous sign language recognition: a comprehensive review, IEEE Access 13, 2025.",
             "[2] J. Wei et al., Rethinking federated unlearning via the lens of memorization, KDD 2026.",
             "[3] F. Zhang et al., Oblivionis: a lightweight learning and unlearning framework for federated LLMs, arXiv:2508.08875, 2025.",
             "[4] Y. Jiang et al., Certifying the right to be forgotten: primal-dual optimization (VFL), arXiv:2512.23171, 2025.",
             "[5] Federated illusion: multi-level geometric privacy audit for federated graph unlearning, Information, 2026 (not verified).",
             "[6] Computationally efficient federated unlearning, Middleware 2025 (not verified).",
             "[7] W. Zhang, A comprehensive investigation of federated unlearning, DAML 2024, pp. 569-573.",
             "[8] Unlearning under siege: robustness risks of certified machine unlearning, Neurocomputing, 2026 (not verified).",
             "[9] B. McMahan et al., Communication-efficient learning of deep networks from decentralized data, AISTATS 2017.",
             "[10] C. Dwork and A. Roth, The algorithmic foundations of differential privacy, 2014."]
    fit(s, 4, short, 14)
    set_notes(s, "References [1] to [10] in short form; the full IEEE list is in the report. [5], [6] and [8] are listed in the batch survey but could not be retrieved independently.")

    set_notes(S[15], "Thank you. Questions are welcome.")
    drop_orphan_images(prs)
    prs.save(OUT)
    scrub_zip(OUT)
    print("saved", OUT, len(prs.slides._sldIdLst), "slides; missing pictures:", sorted(set(MISSING)))


if __name__ == "__main__":
    build()
