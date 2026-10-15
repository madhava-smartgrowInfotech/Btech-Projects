"""Report text, part G: chapter 8 (results and output screens), chapter 9 (conclusion), objectives-versus-outcomes.
Numbers are read from the experiment files at build time and match docs/REPORT_FACTS.md."""
import json
import os

from common import *

EV = json.load(open(os.path.join(ROOT, "experiments", "eval", "metrics.json")))
SS_ = json.load(open(os.path.join(ROOT, "experiments", "seed_study.json")))
ERR = json.load(open(os.path.join(ROOT, "experiments", "error_analysis.json")))
SMP = json.load(open(os.path.join(ROOT, "experiments", "samples.json"), encoding="utf-8"))
DET = EV["detection"]
TP = DET["taxpayer"]


def _hu(x, nd):
    from decimal import ROUND_HALF_UP, Decimal
    return str(Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP))


def f2(x):
    return _hu(x, 2)


def f3(x):
    return _hu(x, 3)


SEEDS = SS_["seeds"]
MEAN, STD, MIN, MAX = SS_["mean"], SS_["std"], SS_["min"], SS_["max"]
SWEEP = {r["threshold"]: r for r in SS_["threshold_sweep_seed42"]}
FP, FN = ERR["false_positives"], ERR["false_negatives"]

# screens used in the body of chapter 8 (the rest go to Appendix C)
BODY_SCREENS = ["ov_run", "ov_done", "tp_list", "tp_sig", "tp_ev", "tp_net", "tp_spike", "graph", "chain_c", "chain_s", "case1", "perf", "runs"]


def prange(role):
    v = [SEEDS[k]["per_pattern"][role] for k in SEEDS]
    return f"{min(v):.2f} to {max(v):.2f}"


def pct(x):
    return f"{100 * x:.1f} %"


def results_blocks():
    R = {}
    # ---------------- 8.1 screens
    scr = [("h2", "8.1 Output Screens"),
           ("p", "All screens below were captured from the running application at 1440 x 900 with the bundled ecosystem (seed 42, 600 taxpayers) generated through the interface. None is a mock-up. They are described in the order of the analyst's workflow; the remaining screens are in Appendix C.")]
    text = {
        "ov_run": "The Overview during a run. Pressing *Generate & analyse* starts the background generation; the stepper marks generate and features as done and JEPA training as active, with the epoch and loss (epoch 10 of 100, loss 0.2571, 25 %), and the activity log streams every pipeline message. This is the screen that makes the long-running stage visible instead of leaving the user with a spinner.",
        "ov_done": "The Overview after the run. The headline cards show 600 taxpayers with 6,977 monthly returns, 64,474 invoices of which 581 are anomalous, 78 flagged taxpayers (13.0 % of the ecosystem) and Rs 25.62 Cr of ITC attached to flagged taxpayers out of Rs 187.59 Cr claimed. The detection card shows precision@79 of 95 % for the model against 62 % for the rule baseline.",
        "tp_list": "The ranked list. The first rows are circular-trading and shell-entity taxpayers with risks of 0.91 to 0.97 and the layer scores in separate columns. Search, pattern, sector and flag filters and the sort order are kept in the URL so that a view can be shared.",
        "tp_sig": "The profile of the top-ranked taxpayer, Lotus Manufacturing Pvt Ltd (risk 0.97, rank 1, circular trading). The Signals tab shows the four layer scores (JEPA 0.93, behaviour 0.61, network 0.78, invoice 1.00), the rule triggered (R4) and the monthly chart of ITC available in GSTR-2B against ITC claimed in GSTR-3B, with the JEPA deviation line peaking at 25.0 times a typical taxpayer-month in March 2026.",
        "tp_ev": "The Evidence tab. Five numbered items, ordered by severity, each with layer, severity and the concrete figures: JEPA deviation, suspicious purchase invoices (11 invoices worth Rs 8.94 Cr carrying Rs 1.61 Cr of ITC), suspicious sales invoices issued (12 worth Rs 9.15 Cr), membership of ring R01 with the loop path, and almost no tax paid in cash (16.6 % of Rs 2.03 Cr).",
        "tp_net": "The Network tab. The local trading network of the taxpayer is drawn with the circular-trading loop in red and a table of the main trading partners with the value bought from and sold to each and their own risk; the partners in the loop have risks of 0.86 to 0.94.",
        "tp_spike": "A different pattern: Ganga Wholesale, flagged as a shell entity with an ITC spike. The monthly chart shows the GSTR-3B claim rising far above the credit available in GSTR-2B in two months while the JEPA deviation line peaks, which is how the spike is seen.",
        "graph": "The whole fraud network. Loop edges are red, high-risk taxpayers red, watch-list taxpayers amber, shared-identity members are ringed. The cluster of connected red nodes in the middle is the set of five injected rings and their neighbours.",
        "chain_c": "Invoice chain CH-R01, the top-ranked chain: a five-party loop (Maa Industries LLP to Surya Enterprises to Lotus Manufacturing to Krishna Traders to Royal Textiles and back) with 98 invoices worth Rs 44.65 Cr passing Rs 9.78 Cr of ITC; 63 % of its invoices are injected fraud in the sample labels.",
        "chain_s": "Invoice chain CH-S37, a shell-supply chain: three linked registrations that bill several buyers, with 100 % of the chain's invoice value anomalous.",
        "case1": "The case page with the Gemini note. The summary names the taxpayer, its risk and the main pattern; each bullet of *Why it was flagged* ends in citation chips such as E2 or E4 that scroll to and highlight the evidence item; the evidence list sits beside the note.",
        "perf": "Model performance for the loaded ecosystem: precision@79 94.9 %, recall@79 94.9 %, F1 at the flag threshold 0.955 against 0.432 for the rule baseline, and the JEPA final loss 0.1115 with the loss curve. Below are the precision@k and recall@k charts for the model and the baseline and the taxpayer-level table with the ablations.",
        "runs": "Run history. The last ten generations with status, seed, taxpayer count, flagged taxpayers and duration, and the ecosystem currently loaded. Every row is a real run made while building and testing this report.",
    }
    for k in BODY_SCREENS:
        scr.append(("p", text[k]))
        scr.append(SCR(k, 4.7))
    R["screens"] = scr

    # ---------------- 8.2 performance
    m, b = TP["model"], TP["rule_baseline"]
    ab = TP["ablation"]
    perf = [("h2", "8.2 Model Performance"),
            ("p", "All figures below are on the bundled ecosystem (seed 42): 600 taxpayers, 79 of them injected fraud, 64,474 invoices, of which 530 are fraud. The scores are computed without labels and then compared with the injected labels. **Because the weights and threshold were chosen on this ecosity, these are best-case figures**; the cross-seed study in Section 8.2.6 shows how they change on other generated ecosystems.".replace("ecosity", "ecosystem")),
            ("h3", "8.2.1 Taxpayer-level detection and ablations"),
            ("tbl", "main", "Taxpayer-level results (seed 42)", ["Method", "P@10", "P@25", "P@50", "P@79", "Prec.", "Recall", "F1", "ROC-AUC"], [
                ["**TaxSentinel (all layers)**", f2(m["precision_at_k"]["10"]), f2(m["precision_at_k"]["25"]), f2(m["precision_at_k"]["50"]), f3(m["precision_at_k"]["79"]), f3(m["at_threshold"]["precision"]), f3(m["at_threshold"]["recall"]), f3(m["at_threshold"]["f1"]), f3(m["roc_auc"])],
                ["Rule baseline R1-R5", f2(b["precision_at_k"]["10"]), f2(b["precision_at_k"]["25"]), f2(b["precision_at_k"]["50"]), f3(b["precision_at_k"]["79"]), f3(b["at_threshold"]["precision"]), f3(b["at_threshold"]["recall"]), f3(b["at_threshold"]["f1"]), f3(b["roc_auc"])],
                ["JEPA + behaviour only", f2(ab["jepa_only"]["precision_at_k"]["10"]), f2(ab["jepa_only"]["precision_at_k"]["25"]), f2(ab["jepa_only"]["precision_at_k"]["50"]), f3(ab["jepa_only"]["precision_at_k"]["79"]), f3(ab["jepa_only"]["at_threshold"]["precision"]), f3(ab["jepa_only"]["at_threshold"]["recall"]), f3(ab["jepa_only"]["at_threshold"]["f1"]), f3(ab["jepa_only"]["roc_auc"])],
                ["Graph + invoice only", f2(ab["graph_and_invoice_only"]["precision_at_k"]["10"]), f2(ab["graph_and_invoice_only"]["precision_at_k"]["25"]), f2(ab["graph_and_invoice_only"]["precision_at_k"]["50"]), f3(ab["graph_and_invoice_only"]["precision_at_k"]["79"]), f3(ab["graph_and_invoice_only"]["at_threshold"]["precision"]), f3(ab["graph_and_invoice_only"]["at_threshold"]["recall"]), f3(ab["graph_and_invoice_only"]["at_threshold"]["f1"]), f3(ab["graph_and_invoice_only"]["roc_auc"])],
                ["Without invoice layer", f2(ab["without_invoice_layer"]["precision_at_k"]["10"]), f2(ab["without_invoice_layer"]["precision_at_k"]["25"]), f2(ab["without_invoice_layer"]["precision_at_k"]["50"]), f3(ab["without_invoice_layer"]["precision_at_k"]["79"]), "-", "-", "-", f3(ab["without_invoice_layer"]["roc_auc"])],
            ], [1.3, 0.58, 0.58, 0.58, 0.62, 0.68, 0.58, 0.5, 0.66]),
            ("p", "TaxSentinel flags 78 taxpayers: 75 are injected fraud and 3 are false alarms, and 4 of the 79 are missed (F1 0.955). The rule baseline flags 236, of which 68 are fraud and 168 are false alarms (F1 0.432). Ranking by risk is clean at the top: the first 50 taxpayers contain no false alarms. {fig:p_at_k} and {fig:methods} show the same comparison graphically."),
            ("fig", "p_at_k", C("c01_precision_at_k.png"), "Precision@k for the full model, the ablations and the rule baseline (seed 42)", 5.6),
            ("fig", "methods", C("c02_method_comparison.png"), "F1, ROC-AUC and average precision by method (seed 42)", 5.6),
            ("p", "The ablations are the most informative result. The JEPA with the behaviour variant alone reaches an F1 of only 0.327 (precision 0.842 but recall 0.203): when it flags a taxpayer it is usually right, but it finds one fraud taxpayer in five at the 0.5 threshold. Graph plus invoice evidence alone gives F1 0.887 and precision 1.00, with 16 misses. Combining all layers improves recall to 0.949 at precision 0.962. Removing the invoice layer barely changes P@79 (0.949) and slightly lowers ROC-AUC (0.996 against 0.997): the invoice layer mainly sharpens the middle of the ranking, and the layers overlap. The honest reading is that the JEPA is a useful component but not the whole answer; most of the detection power comes from the network and invoice layers, and the JEPA adds recall on top of them."),
            ("h3", "8.2.2 Confusion matrices and recall by pattern"),
            ("fig", "cm", C("c08_confusion_matrices.png"), "Taxpayer-level confusion matrices at the flag threshold (seed 42)", 5.8),
            ("tbl", "pat", "Recall by injected pattern at the flag threshold (seed 42)", ["Pattern", "Count", "TaxSentinel", "Rule baseline", "Pattern correctly named"], [
                [{"circular_trading": "Circular trading", "shell_entity": "Shell entity", "fake_invoice_buyer": "Fake-invoice buyer", "itc_spike": "ITC spike"}[k], str(v["count"]), f2(v["model_recall"]), f2(v["baseline_recall"]), f2(v["pattern_named"])]
                for k, v in DET["per_pattern"].items()], [1.8, 0.8, 1.2, 1.3, 1.9]),
            ("p", "Recall is 1.00 for circular trading (baseline 0.86) and for shell entities (baseline 1.00), 0.89 for fake-invoice buyers (baseline 0.58) and 0.83 for ITC spikes, where the **rule baseline is better** (1.00): a one-month claim above 3 times the previous month is exactly what rule R4 tests, while the model's score for a single month is diluted by the taxpayer's other months. In every case where a flagged taxpayer was one of these patterns, the pattern was named correctly."),
            ("fig", "pat", C("c03_recall_by_pattern.png"), "Recall by injected fraud pattern, model against rule baseline (seed 42)", 5.2),
            ("h3", "8.2.3 Invoice-level detection, rings and chains"),
            ("tbl", "inv", "Invoice-level, ring and chain results (seed 42)", ["Measure", "Value"], [
                ["Anomalous-invoice flags (score >= 0.5)", f"{DET['invoice']['model']['at_threshold']['flagged']} flagged; precision {f3(DET['invoice']['model']['at_threshold']['precision'])}, recall {f3(DET['invoice']['model']['at_threshold']['recall'])}, F1 {f3(DET['invoice']['model']['at_threshold']['f1'])}"],
                ["Invoice ranking", f"ROC-AUC {f3(DET['invoice']['model']['roc_auc'])}; precision@100 {f2(DET['invoice']['model']['precision_at_k']['100'])}, @500 {f3(DET['invoice']['model']['precision_at_k']['500'])}, @530 {f3(DET['invoice']['model']['precision_at_k']['530'])}"],
                ["Baseline: not reported in supplier's GSTR-1", f"{DET['invoice']['rule_baseline']['at_threshold']['flagged']} flagged; precision {f3(DET['invoice']['rule_baseline']['at_threshold']['precision'])}, recall {f3(DET['invoice']['rule_baseline']['at_threshold']['recall'])}, F1 {f3(DET['invoice']['rule_baseline']['at_threshold']['f1'])}"],
                ["Injected circular-trading rings recovered", f"{DET['rings']['recovered']} of {DET['rings']['injected']} (at least 80 % of members in one detected ring)"],
                ["Rings detected", f"{DET['rings']['detected']} ({DET['rings']['detected_with_fraud_members']} with injected-fraud members, {DET['rings']['detected_without_fraud_members']} without)"],
                ["Invoice chains", f"{DET['chains']['total']} chains; share of the top 10 that are fraud: {f2(DET['chains']['precision_top10'])}"],
            ], [2.8, 4.2]),
            ("fig", "invc", C("c07_invoice_level.png"), "Invoice-level precision, recall and F1: invoice score against the GSTR-1 mismatch check (seed 42)", 5.2),
            ("p", "The invoice score has F1 0.924 against 0.160 for the classic mismatch check, which flags 1,071 invoices and finds only 24 % of the fraud. Every injected ring was recovered, but two of the nine detected rings contain no injected-fraud taxpayer: these are legitimate reciprocal trade loops that look like circular trading, and they are discussed in Section 8.5."),
            ("h3", "8.2.4 Threshold analysis"),
            ("p", "The flag threshold was fixed at 0.5. {tab:sweep} and {fig:sweep} show what other thresholds would have done on the same scores. F1 is highest between 0.4 and 0.6 and falls on either side: a lower threshold adds false alarms (at 0.2 there are " + str(SWEEP[0.2]["fp"]) + "), a higher one misses fraud (at 0.8 only " + str(SWEEP[0.8]["tp"]) + " of 79 are found). The distribution of the scores ({fig:hist}) explains the stability near 0.5: legitimate taxpayers pile up at low risk and injected fraud at high risk, with a thin overlap."),
            ("tbl", "sweep", "Flag threshold sweep on the seed-42 scores", ["Threshold", "Flagged", "TP", "FP", "FN", "Precision", "Recall", "F1"], [
                [f"{t:.1f}", str(r["flagged"]), str(r["tp"]), str(r["fp"]), str(r["fn"]), f3(r["precision"]), f3(r["recall"]), f3(r["f1"])] for t, r in SWEEP.items()], [1.0, 0.9, 0.7, 0.7, 0.7, 1.0, 0.9, 0.9]),
            ("fig", "sweep", C("c09_threshold_sweep.png"), "Precision, recall and F1 against the risk threshold (seed 42)", 5.4),
            ("fig", "hist", C("c10_risk_distribution.png"), "Distribution of the combined risk score for legitimate and injected-fraud taxpayers (log scale)", 5.4),
            ("h3", "8.2.5 Which layer carries which signal"),
            ("fig", "layers", C("c12_layer_scores.png"), "Mean layer scores of injected-fraud and legitimate taxpayers (seed 42)", 5.2),
            ("p", "Averaged over taxpayers, " + ", ".join(f"the {l} layer scores {SS_['layer_means_seed42'][l]['fraud']:.2f} for fraud against {SS_['layer_means_seed42'][l]['legit']:.2f} for legitimate" for l in ("jepa", "behaviour", "network", "invoice")) + ". The separation is largest in the network and invoice layers, which agrees with the ablation."),
            ("h3", "8.2.6 Cross-seed study"),
            ("p", "To test how far the seed-42 figures generalise, the whole pipeline (generation, JEPA training, scoring, evaluation) was re-run on five other ecosystems of 600 taxpayers, seeds 1, 2, 3, 7 and 11, with the same weights and threshold ({tab:seeds}, {fig:seeds}). Over these five ecosystems the taxpayer-level F1 has a mean of " + f3(MEAN["f1"]) + " (standard deviation " + f3(STD["f1"]) + ", range " + f3(MIN["f1"]) + " to " + f3(MAX["f1"]) + "), ROC-AUC " + f3(MEAN["roc_auc"]) + " (range " + f3(MIN["roc_auc"]) + " to " + f3(MAX["roc_auc"]) + ") and precision@k " + f3(MEAN["p_at_k"]) + ", against a rule-baseline F1 of " + f3(MEAN["base_f1"]) + " and precision@k of " + f3(MEAN["base_p_at_k"]) + ". Ranking quality is stable (ROC-AUC " + f3(MIN["roc_auc"]) + " to " + f3(MAX["roc_auc"]) + ") and the advantage over the rule baseline holds on every seed (the model's F1 is higher on all five). What changes is how many of the weaker-signal taxpayers cross the fixed 0.5 line: circular-trading recall is 1.00 and all injected rings are recovered on every seed, shell-entity recall is " + prange("shell_entity") + ", but fake-invoice-buyer recall ranges from " + prange("fake_invoice_buyer") + " and ITC-spike recall from " + prange("itc_spike") + " on the other seeds (0.89 and 0.83 on seed 42). The seed-42 figures are therefore a best case, because the weights and threshold were set on that ecosystem."),
            ("tbl", "seeds", "Cross-seed study (600 taxpayers each; same weights and threshold)", ["Seed", "Fraud", "Flagged", "P@k", "Precision", "Recall", "F1", "ROC-AUC", "Baseline F1", "Rings found"], [
                [str(k), str(v["n_fraud"]), str(v["flagged"]), f3(v["p_at_k"]), f3(v["precision"]), f3(v["recall"]), f3(v["f1"]), f3(v["roc_auc"]), f3(v["base_f1"]), f"{v['rings_recovered']}/{v['rings_injected']}"] for k, v in SEEDS.items()] +
            [["**mean**", "", "", f3(MEAN["p_at_k"]), f3(MEAN["precision"]), f3(MEAN["recall"]), f3(MEAN["f1"]), f3(MEAN["roc_auc"]), f3(MEAN["base_f1"]), ""],
             ["**std**", "", "", f3(STD["p_at_k"]), f3(STD["precision"]), f3(STD["recall"]), f3(STD["f1"]), f3(STD["roc_auc"]), f3(STD["base_f1"]), ""]], [0.6, 0.6, 0.7, 0.6, 0.8, 0.7, 0.6, 0.8, 0.8, 0.8]),
            ("fig", "seeds", C("c11_seed_study.png"), "F1 at the flag threshold on five other generated ecosystems, model against rule baseline", 5.4),
            ("h3", "8.2.7 Transfer check on PaySim"),
            ("p", "To check that the JEPA module is not tied to the GST generator, the same module (window 0, three feature blocks) was trained without labels on 100,000 PaySim transactions for 15 epochs (6.2 s) and scored by prediction error. Its ROC-AUC is 0.935 against 0.790 for ranking by transaction amount, and its precision@100 is 0.31 against 0.02 ({fig:paysim}). Average precision is low for both (0.090 and 0.013) because only 134 of 100,000 transactions are fraud. This is an out-of-domain sanity check, not a claim about GST."),
            ("fig", "paysim", C("c06_paysim_transfer.png"), "PaySim transfer check: unlabelled JEPA against ranking by amount", 5.4),
    ]
    R["perf"] = perf

    # ---------------- 8.3 explanation quality
    es = EV["explanations"]["summary"]
    cases = SMP["eval_cases"]
    exp = [("h2", "8.3 Explanation Quality"),
           ("p", "Gemini notes were generated for the top-ranked flagged cases and checked automatically. Six of the intended ten completed; for the other four the free-tier service returned 503 (overloaded), 429 (quota exhausted) or 504 (timeout) from every model in the fallback chain, and these failures are recorded in the evaluation file. {tab:expl} summarises the six notes."),
           ("tbl", "expl", "Automatic quality checks over six Gemini case notes", ["Check", "Result"], [
               ["Notes evaluated / attempted", "6 / 10"],
               ["Invalid citations", pct(es["invalid_citation_rate"])],
               ["Citations per note (mean)", f"{es['mean_citations']:.1f}"],
               ["Evidence items cited", pct(es["evidence_coverage"])],
               ["High-severity items cited", pct(es["high_severity_coverage"])],
               ["Numbers in the text found in the evidence", pct(es["numeric_grounding"])],
               ["All three sections present", pct(es["all_sections_present"])],
               ["Suspected pattern named", pct(es["pattern_named"])],
               ["Words per note (mean)", f"{es['mean_words']:.0f}"],
           ], [4.0, 3.0]),
           ("p", "Citation discipline is perfect on these six notes: no citation points to a non-existent item and every evidence item is cited. The weaker figure is numeric grounding: 84.3 % of the numbers in the text appear in the evidence. The remainder are plausibly derived figures (for example a total of two evidence amounts, a rounded percentage or a month count) that a simple string match cannot confirm; the notes were not audited number by number, so these are unverified rather than known to be wrong. The same case written several times gives different notes (temperature 0.2 is not zero): the stored notes for Lotus Manufacturing across four separate generations during this project had numeric grounding between " + f"{min(q['quality']['numeric_grounding'] for q in SMP['stored_note_quality'] if q['gstin'] == SMP['taxpayer']['gstin']):.2f} and {max(q['quality']['numeric_grounding'] for q in SMP['stored_note_quality'] if q['gstin'] == SMP['taxpayer']['gstin']):.2f}" + " with 13 to 14 citations each. The checks measure grounding, not correctness of the investigative advice; no human judged the notes."),
           ]
    R["expl"] = exp

    # ---------------- 8.4 sample IO
    ev_rows = [[e["id"], e["layer"], e["severity"], e["title"]] for e in SMP["evidence"]]
    note = SMP["note"]["text"]
    sample = [("h2", "8.4 Sample Inputs and Outputs"),
              ("p", "**Input.** A generation request `POST /api/pipeline/run` with `{\"seed\": 42, \"taxpayers\": 600}`, then `GET /api/taxpayers/36ROJCS8039W1ZU` for the top-ranked taxpayer."),
              ("code", "{ \"gstin\": \"36ROJCS8039W1ZU\", \"legal_name\": \"Lotus Manufacturing Pvt Ltd\", \"sector\": \"manufacturer\", \"state\": \"Telangana\",\n"
                       "  \"risk\": 0.9651, \"rank\": 1, \"flagged\": true, \"patterns\": [\"circular_trading\"],\n"
                       "  \"jepa\": 0.9283, \"behaviour\": 0.6051, \"network\": 0.784, \"invoice\": 1.0,\n"
                       "  \"itc_at_risk\": 16083140, \"rules\": [\"R4\"], \"rings\": [\"R01\"] }"),
              ("p", "**Output 1: the evidence list** built by the pipeline for this taxpayer ({tab:sev}); the full detail text of each item carries the figures quoted in the case note."),
              ("tbl", "sev", "Evidence list for Lotus Manufacturing Pvt Ltd", ["ID", "Layer", "Severity", "Title"], ev_rows, [0.5, 1.2, 1.0, 4.3]),
              ("p", "**Output 2: the case note** written by Gemini from that evidence (model " + SMP["note"]["model"] + "), with its automatic quality check: " + f"{SMP['note']['quality']['citations']} citations, {SMP['note']['quality']['invalid_citations']} invalid, evidence coverage {SMP['note']['quality']['evidence_coverage']:.0%}, high-severity coverage {SMP['note']['quality']['high_severity_coverage']:.0%}, numeric grounding {SMP['note']['quality']['numeric_grounding']:.1%} ({SMP['note']['quality']['numbers_grounded']} of {SMP['note']['quality']['numbers']} numbers), {SMP['note']['quality']['words']} words."),
              ("code", note.replace("₹", "Rs ")),
              ]
    R["sample"] = sample

    # ---------------- 8.5 success / failure
    def fp_row(t):
        return [t["legal_name"], t["sector"].replace("_", " "), f"{t['risk']:.2f}", ", ".join(t["patterns"]) or "-", f"{t['jepa']:.2f} / {t['behaviour']:.2f} / {t['network']:.2f} / {t['invoice']:.2f}", ", ".join(t["rings"]) or "-"]

    def fn_row(t):
        return [t["legal_name"], ", ".join(t["roles"]), f"{t['risk']:.2f}", str(t["rank"]), f"{t['jepa']:.2f} / {t['behaviour']:.2f} / {t['network']:.2f} / {t['invoice']:.2f}"]

    ring_wo = [r for r in ERR["rings"] if not r["with_fraud"]]
    inv_fp = ERR["invoice_false_positive_flags"]
    inv_fn = ERR["invoice_false_negative_flags"]
    sf = [("h2", "8.5 Success and Failure Analysis"),
          ("h3", "Where the system succeeds"),
          ("bul", [
              "**The top of the ranking is clean.** The first 50 taxpayers contain no false alarm; the top 10 chains are all majority-fraud (precision 1.00).",
              "**Circular trading is found completely:** recall 1.00 and all 5 injected rings recovered, against 0.86 for the rule baseline. The loop is drawn and cited, so the finding is checkable.",
              "**Shell clusters are found with the help of the network layer:** shell-entity recall 1.00, although the JEPA alone finds only about one in five of the flagged shell firms.",
              "**Evidence and notes are grounded:** no invalid citations and full evidence coverage over the evaluated notes.",
              "**Far fewer false alarms than rules:** 3 against 168.",
          ]),
          ("h3", "Where it fails: the " + str(len(FP)) + " false positives (seed 42)"),
          ("tbl", "fp", "Legitimate taxpayers flagged at the 0.5 threshold", ["Taxpayer", "Sector", "Risk", "Patterns", "Layers J / B / N / I", "Ring"], [fp_row(t) for t in FP], [1.6, 0.9, 0.5, 1.4, 1.8, 0.8]),
          ("p", "All three false alarms are driven by the JEPA and behaviour layers, not by network or invoice evidence: two of them (Apex Distributors and Vertex Enterprises LLP) have a network score and an invoice score of exactly 0 and are flagged as *unusual behaviour* on a JEPA deviation score of 0.68 and 0.80; the third (Orbit Industries) combines a JEPA score of 0.37 with a behaviour score of 0.51. They are legitimate firms whose month-to-month behaviour was unusual (the generator includes seasonality, one-off capital purchases and credit catch-ups on purpose). The structural detectors did not produce a single false alarm at taxpayer level. At ring level, two of the nine detected rings contain no injected-fraud taxpayer; they are loops of legitimate reciprocal trade with the lowest ring scores (0.30 and 0.27), and they do not push their members over the flag threshold. For a user the consequence is that an *unusual behaviour* flag with no network or invoice evidence deserves the lowest priority, which the evidence list makes visible."),
          ("h3", "Where it fails: the " + str(len(FN)) + " false negatives (seed 42)"),
          ("tbl", "fn", "Injected-fraud taxpayers missed at the 0.5 threshold", ["Taxpayer", "Injected role", "Risk", "Rank", "Layers J / B / N / I"], [fn_row(t) for t in FN], [1.9, 1.7, 0.6, 0.6, 2.2]),
          ("p", "The four missed taxpayers are two ITC-spike cases and two fake-invoice buyers whose signals are modest. Their risks are 0.29 to 0.47 and they rank 80th to 122nd of 600, so they sit just below the flag line and well above most legitimate firms, but not among the 79 who would be found by an exact-count cutoff. The spike cases (Eastern Enterprises, Global Logistics) have a JEPA score of about 0.4 and no network or invoice evidence; the fake-invoice buyers (Metro Manufacturing, Zenith Enterprises) have almost no JEPA signal (0.02 to 0.03) and a network score of 0.31, because their purchases from shell clusters are a small share of their total purchases. This is the cost of a single fixed threshold and of weights tuned on one ecosystem; the sweep in Section 8.2.4 shows that a threshold of 0.4 would recover two of the four at the price of five more false alarms (8 instead of 3)."),
          ("h3", "Invoice-level failures"),
          ("p", "At invoice level there are " + str(DET["invoice"]["model"]["at_threshold"]["fp"]) + " false positives and " + str(DET["invoice"]["model"]["at_threshold"]["fn"]) + " missed fraud invoices. The most common flag combinations among the false positives are " + "; ".join(f"[{k}] ({v})" for k, v in inv_fp[:3]) + ": invoices that carry the ring-edge flag or that combine a missing supplier report with a missing e-way bill, which also occur on legitimate reciprocal trade. The most common combinations among the missed fraud invoices are " + "; ".join(f"[{k}] ({v})" for k, v in inv_fn[:3]) + ". The first of these is instructive: a shell-cluster flag (weight 0.35) together with a vanished supplier (0.20) gives a noisy-OR of 1 - 0.65 x 0.80 = 0.48, just under the 0.50 invoice threshold, so these invoices are missed by 0.02. A fake invoice that is reported by its (shell) supplier, has an e-way bill and a plausible value leaves nothing for an invoice-level rule to flag and is caught only through the taxpayer or the network."),
          ("h3", "Failure of the explanation component"),
          ("p", "Four of ten requested notes could not be produced because the free Gemini tier was overloaded or out of quota. The product reports the failure and tries fallback models, but the dependence on an external service is a real operational weakness."),
          ]
    R["sf"] = sf

    # ---------------- 8.6 comparison with base paper
    cmp = [("h2", "8.6 Comparison with the Base Paper"),
           ("p", "The base paper [1] is a qualitative study and reports no detection model, accuracy or other measured performance, so there is **no like-for-like numerical comparison** between its results and this project's. The comparison below is therefore on what the paper recommends and on the project's own baseline."),
           ("tbl", "base", "Base paper recommendations and this project", ["Base paper [1] position", "This project", "Status"], [
               ["Fake invoicing, circular trading and shell companies are the main ITC fraud patterns", "All three (and ITC spikes) are injected, detected and measured", "Implemented"],
               ["Use data analytics and network analysis for detection", "Feature layers, JEPA deviation, trade-graph cycles and identity clusters", "Implemented"],
               ["Dynamic AI-based risk modelling, ideally at registration", "Risk scoring of existing taxpayers; registration-time scoring of new applicants was not built (registration age and cluster membership are inputs)", "Partly"],
               ["Quantitative AI-supported fraud detection as future research", "Evaluated with precision@k, F1, ROC-AUC, ablations and cross-seed study on synthetic data", "Done on synthetic data only"],
               ["Unified economic intelligence grid across agencies", "Single-state, single-source prototype", "Not addressed"],
               ["Forensic capacity of officers", "Evidence-backed case notes intended to reduce the effort of reading a case", "Supports, not measured"],
               ["Faster prosecution and recovery", "Out of scope", "Not addressed"],
           ], [2.7, 3.0, 1.3]),
           ("p", "Against the rule-based checks that the paper's setting implies, the quantitative comparison on the same data is: F1 0.955 against 0.432 and P@79 0.949 against 0.620 on seed 42; and a mean F1 of " + f3(MEAN["f1"]) + " against " + f3(MEAN["base_f1"]) + " over five other seeds."),
           ("p", "For context only, TED [7], a supervised heterogeneous-graph model, reports F1 between 76.35 % and 94.96 % on two *real* tax datasets depending on the share of positive training samples, and Mehta et al. [6] report no accuracy metric for their circular-trading communities. These numbers are **not comparable** with this project's: the data are real and different, TED is trained with labels and TaxSentinel is not, and the tasks are defined differently. What can be said is that an unlabelled method reaching F1 around 0.8 to 0.95 on a synthetic ecosystem with injected hard negatives is in the range where it is worth validating on real data; it does not show that it would match TED there."),
           ]
    R["cmp"] = cmp

    R["limits"] = [("h2", "8.7 Limitations of the Results"),
                   ("bul", [
                       "Synthetic data: the labels are the generator's, and the detectors partly mirror the generator's fraud logic (loops, shared addresses, young registrations). Real fraud may be messier, which would lower the figures.",
                       "The weights and threshold were tuned on seed 42; the cross-seed F1 is lower (mean " + f3(MEAN["f1"]) + ", minimum " + f3(MIN["f1"]) + ").",
                       "No held-out split for the encoder; the cross-seed study is the closest substitute.",
                       "The comparison is with a rule baseline built by the project team from standard scrutiny rules; it is not an official tool.",
                       "Explanation checks measure grounding, not correctness; six notes were evaluated.",
                       "Measurements were taken on one machine under varying load.",
                   ])]

    # ---------------- 8.8 objectives vs outcomes
    obj = [("h2", "8.8 Objectives versus Outcomes"),
           ("tbl", "obj", "Objectives and measured outcomes", ["#", "Objective", "Outcome", "Status"], [
               ["1", "Build a multi-layer GST dataset (invoices, behaviour, network)", "Generator with 600 taxpayers, 64,474 invoices, 6,977 returns, 4 fraud patterns, 7 hard-negative kinds; 19 features in 3 layers", "Achieved (synthetic)"],
               ["2", "Learn normal behaviour with a self-supervised JEPA", "53,420-value JEPA trained without labels in 11.7 s; final loss 0.1115", "Achieved"],
               ["3", "Detect fake invoices, circular trading and shell entities", "Recall 0.89, 1.00 and 1.00 at the threshold; 5 of 5 rings; ITC spikes 0.83", "Achieved on seed 42; lower F1 on other seeds"],
               ["4", "Rank suspicious taxpayers and invoice chains", "P@50 = 1.00, P@79 = 0.949, ROC-AUC 0.997; top-10 chains 1.00", "Achieved"],
               ["5", "Natural-language explanations with a tuned LLM", "Cited Gemini notes with checks; prompt-tuned, not fine-tuned", "Achieved with a deviation: prompting, not fine-tuning"],
               ["6", "Evaluate detection accuracy and explanation quality", "Full harness, ablations, cross-seed study, PaySim check; 6 of 10 notes evaluated", "Achieved, with the gaps listed in Section 8.7"],
           ], [0.4, 2.2, 3.0, 1.4]),
           ]
    R["obj"] = obj
    return R


def conclusion_blocks():
    C9 = {}
    C9["all"] = [
        ("h2", "9.1 Summary"),
        ("p", "TaxSentinel is a working prototype of a self-supervised, explainable framework for ITC-fraud detection in GST. It generates a labelled synthetic ecosystem, learns normal behaviour with a 53,420-value JEPA in 11.7 s on a CPU, combines that signal with circular-trading and shell-cluster detection and invoice-level scoring in a noisy-OR risk, ranks taxpayers and invoice chains, and explains each flag with a cited, automatically checked note, all behind a secured web application that was tested end to end."),
        ("h2", "9.2 Objectives Achieved"),
        ("p", "All six objectives were met on synthetic data, with one deviation: the LLM is prompted and checked, not fine-tuned (Section 8.8). The system ranks the 600-taxpayer ecosystem with precision@79 of 0.949 and ROC-AUC 0.997, recovers all five injected rings, finds anomalous invoices with F1 0.924, and produces notes with no invalid citations."),
        ("h2", "9.3 Key Findings"),
        ("num", [
            "**Several layers beat one.** JEPA plus behaviour alone has F1 0.327; graph plus invoice 0.887; all layers 0.955. Self-supervised deviation is a useful but partial signal, strongest as a complement to network and invoice evidence.",
            "**Structure matters more than amounts for circular trading and shells.** Balance, recurrence and concentration of a loop, and shared identity of a cluster, find what a per-taxpayer score cannot.",
            "**Rules are good at what they were written for.** The rule baseline beats the model on one-month ITC spikes (recall 1.00 against 0.83) but flags 236 taxpayers with 168 false alarms.",
            "**Headline accuracy does not fully generalise.** On five other generated ecosystems the mean F1 is " + f3(MEAN["f1"]) + " (range " + f3(MIN["f1"]) + " to " + f3(MAX["f1"]) + "), lower than 0.955, while the ranking quality (ROC-AUC mean " + f3(MEAN["roc_auc"]) + ") and the advantage over rules hold. The fixed weights and threshold are the weak point.",
            "**Citation-constrained generation works, and can be measured.** No invalid citations and full evidence coverage in six notes; 84 % numeric grounding shows where the remaining risk lies.",
        ]),
        ("h2", "9.4 Practical Applications"),
        ("bul", [
            "Prioritising audit and enquiry lists in a state tax-administration analytics unit.",
            "Preparing the starting file for an investigation: ranked evidence, loops and a first-draft note.",
            "Supplier-network audits by large businesses (a buyer can check whether its suppliers sit in a shell cluster).",
            "Teaching and evaluation: the seeded generator provides labelled ecosystems for comparing detection methods.",
        ]),
        ("h2", "9.5 Known Limitations"),
        ("p", "The data is synthetic; thresholds and weights need recalibration on real returns; the headline F1 is a best case; the LLM is prompted and depends on an external quota; and testing has no unit, UI or user-acceptance layer (Section 1.8 and Chapter 7). The output is a risk indication for review, never a finding of fraud."),
    ]
    return R_unused() if False else C9


def R_unused():
    return None
