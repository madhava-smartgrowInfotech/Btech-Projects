"""Chapter 8 content (and 14.RESULTS.docx): output screens, measured results, comparison, samples, success and failure, limits, objectives.

Every number is read from experiments/*/metrics.json or docs/sample_io/samples.json (captured from a live server by scripts/capture_samples.py).
Every screenshot description was written after looking at the PNG."""
from __future__ import annotations

import json

from doc_common import CHARTS, ROOT, SHOTS, metrics

_base = metrics("baseline")
_seeds = metrics("seeds")
_sweep = metrics("noise_sweep")
_gold = metrics("gold_retrain")
_nf = metrics("noise_free_leakage")
_seq = metrics("sequential")
_dp = metrics("dp_accounting")
_sc = metrics("scaling")
_syn = metrics("synthetic_corpus")
_nn = metrics("neural_adapter")
_sp = metrics("security_probe")
_samples = json.loads((ROOT / "docs" / "sample_io" / "samples.json").read_text(encoding="utf-8"))


def pc(x, n=1):
    return f"{100 * x:.{n}f} %"


def _rep(d):
    return bool(getattr(d, "report", False))


# ----------------------------------------------------------------------------------------------------------------- screens
MAIN = ["01", "04", "05", "06", "07", "09", "10", "13"]
EXTRA = ["02", "03", "04b", "08", "09b", "11", "12", "14", "15", "16", "17"]

SCREENS = {
    "01": ("01_landing.png", "Landing page with the live lab status",
           "The landing page carries the ForgetSafe name and the tag line \"Certified right to be forgotten\", a navigation bar (How it works, Screens, Live), a dark-mode "
           "toggle and an *Open the lab* button. The headline reads \"Forget a client, prove it, keep the model useful.\" On the right, a *Live lab status* card is filled "
           "from `GET /api/state`: the badge says Connected, the session is \"Not trained yet\", there are \"5 registered\" active clients in the domains Finance, "
           "Healthcare, Education, Retail and Travel, and the audit ledger shows \"1 record(s), chain valid\" (the ledger already held one training event from an "
           "earlier session of the capture run). Two floating chips name the guarantees the product claims, \"ε · δ DP guarantee\" and \"SHA-256 hash-chained ledger\"; "
           "three tags below the buttons read Differential privacy, Membership-inference check and Audit trail."),
    "04": ("04_training_trained.png", "Federated training screen after training",
           "After pressing *Train federated model* a toast reads \"Federated training complete, 5 clients aggregated, ε 1.6149\". The four tiles show 5 of 5 active clients, "
           "DP epsilon 1.6149 with δ = 0.00001, perplexity 130.22 and next-character accuracy 5.1 % (utility 0.093). The *Clients* table lists Client 01 to Client 05 with their "
           "domains, 5 records each, original L2 norms of 26.589, 28.231, 26.401, 25.219 and 26.552, and a clipped L2 of 25.000 for every client. The *Clipped update norm* "
           "chart beside it shows five bars of equal height under an axis that runs to 28, which is the visual form of the clipping: every update leaves the client at the same length."),
    "05": ("05_dashboard_trained.png", "Dashboard after training",
           "The dashboard headline reads \"Right-to-be-forgotten, certified\". The *Workflow* card is a three-step stepper: Train is ticked and marked Done, Unlearn "
           "(\"Remove a client\") is highlighted as the current step and Verify shows \"Audit chain valid\". The summary tiles repeat the training figures (5 of 5 clients, ε 1.6149, "
           "perplexity 130.22, accuracy 5.1 %, both labelled with the public evaluation set). Below, *Client updates* draws the clipped norm of each client as a horizontal bar and "
           "*Latest certificate* still shows \"No certificate yet\" with a *Request unlearning* button, because no removal has been made."),
    "06": ("06_explorer_before_unlearning.png", "Model explorer before any removal",
           "The explorer offers a *Seed text* field (here \"privacy\"), a *Generate sample* button and a *Method notes* card that summarises clipping, Gaussian noise, subtraction "
           "and the membership attack. The *Samples* list, newest first, tags the generated text with the seed, the model state (\"5 active clients\") and the first characters of the "
           "model hash (fe4d958335…). The text is \"privacybsov btrppsvyklrcxrvymej,..!qgnlgpynl\": a string of characters with no words, which is what a bigram model dominated by "
           "noise produces."),
    "07": ("07_unlearning_request.png", "Certified unlearning screen before a request",
           "The *Right-to-be-forgotten request* card shows a drop-down labelled *Client to remove* set to \"Client 01 — Finance\", the note \"5 active clients\" and the "
           "*Execute & certify* button. The area underneath is an empty state: \"No certificate yet. A verification certificate with the residual-influence check, membership-inference "
           "AUC and retained utility appears here after an unlearning request.\""),
    "09": ("09_unlearning_certificate.png", "Verification certificate after removing Client 01",
           "A toast confirms \"Client removed and certified, Client 01 (Finance) · certified\". The drop-down now offers the four remaining clients (Client 02 — Healthcare is selected, "
           "\"4 active clients\"). The *Verification certificate* card shows the badge Certified, the identifier CERT-C5427F948A72, the client and the UTC time (2026-10-26 14:16:03) and a "
           "*Download JSON* button, followed by the measured fields: privacy guarantee ε 1.6149 · δ 0.00001, utility retained 93.65 %, residual influence (L2) 2.790e-14, reference retrain (L2) "
           "2.790e-14, membership AUC 0.200 → 0.160, perplexity 130.221 → 146.472 and next-character accuracy 5.1 % → 4.4 %. The *Before vs after* chart on the right draws the membership AUC and "
           "the accuracy as paired bars."),
    "10": ("10_explorer_after_unlearning.png", "Model explorer after removing Client 01",
           "The same seed \"privacy\" now produces a sample tagged \"4 active clients\" and model hash d0f7b70df5…, and the text is again \"privacybsov btrppsvyklrcxrvymej,..!qgnlgpynl\", "
           "character for character the same as before the removal. The generator uses a fixed random seed and the noisy probabilities changed too little to alter any draw, so the "
           "explorer cannot show, by eye, that a client was removed (Section on sample inputs and outputs)."),
    "13": ("13_audit_ledger.png", "Compliance audit screen with a verified hash chain",
           "After pressing *Verify hash chain* a toast reads \"Hash chain verified, Verified 4 audit record(s)\" and the *Chain status* card shows the badge Valid and the note that "
           "the ledger \"survives new sessions and server restarts\". The *Ledger* table lists the four records, newest first, with sequence number, event type (Unlearning or Training), UTC "
           "time, client, status and the first characters of the record hash: #4 Unlearning, Client 02 (Healthcare), Certified, 5c20d6e7d1ee282ef5…; #3 Unlearning, Client 01 (Finance), "
           "Certified, 208f652b947ede288f…; #2 and #1 Training. A search box and a *View* action on each row open the full record."),
    "02": ("02_landing_how_it_works.png", "Landing page, how-it-works section",
           "Scrolled down, the landing page lists five numbered stages: 01 Federated training (isolated clients, each update L2-clipped before the coordinator sees it), 02 Noisy aggregation "
           "(a Gaussian noise gives a one-shot (ε, δ) bound), 03 Parameter-level unlearning (a client's tracked update is subtracted, retained clients renormalised, no full retraining), "
           "04 Independent verification (comparison with a clean retained-only recomputation, then a membership-inference attack) and 05 Tamper-evident audit (every event hash-chained with SHA-256). "
           "A heading \"Four screens, one workflow\" starts the next section."),
    "03": ("03_training_before.png", "Federated training screen before the first training run",
           "In the untrained state all four tiles show a dash with the foot-note \"Not trained yet\", and an empty-state card reads \"The global model has not been trained. Run federated training "
           "to aggregate the five clients' clipped updates into one noisy global model\" with a *Train federated model* button. The header buttons *New session* and *Train federated model* are "
           "available and the status chip reads API online."),
    "04b": ("04b_training_full.png", "Federated training screen, full page",
            "The full-page capture adds the *Global model fingerprint* card below the clients table: the SHA-256 of the current parameter vector, fe4d958335a7a158acdf8d5d441073a39f9d1bb70fc95141ae3dd49d5869bbba, "
            "and the start of the session identifier."),
    "08": ("08_unlearning_confirm.png", "Confirmation dialog before a removal",
           "Pressing *Execute & certify* opens a modal dialog titled \"Remove this client?\" with the text \"Client 01 (Finance) will be erased from the global model. This cannot be undone in this session.\" "
           "and two buttons, Cancel and Remove & certify. The page behind it is blurred. The dialog guards against an accidental click on an action that changes the model."),
    "09b": ("09b_certificate_full.png", "Verification certificate, full page",
            "The full certificate adds the lower rows: Clients 5 → 4, clip norm · noise 25 · 3, the method \"Tracked clipped-update subtraction with retained-client renormalization\", the model "
            "hash before (fe4d958335a7a158…) and after (d0f7b70df52c5d17…) and the audit record hash 208f652b947ede288f0291ceb321ab92bd9cf7911af5ad74bb3dc6f96e864ca8, which is the value that links the "
            "certificate to ledger record 3. A second chart, *Perplexity*, shows the before bar (130.221) lower than the after bar (146.472)."),
    "11": ("11_second_certificate.png", "Certificate for the second removal (Client 02)",
           "After the second request the certificate is CERT-30F21BF8C9A3 for Client 02 (Healthcare), issued 2026-10-26 14:16:17 UTC: ε 1.6149 · δ 0.00001, utility retained 98.30 %, residual influence "
           "and reference retrain both 3.633e-14, membership AUC 0.480 → 0.440, and perplexity 146.472 → 171.275 (the bottom row is partly cut off in the capture). The drop-down now offers "
           "Client 03 — Education with \"3 active clients\"."),
    "12": ("12_dashboard_after_unlearning.png", "Dashboard after two removals",
           "All three workflow steps are ticked; Unlearn reads \"2 client(s) removed\" and Verify \"Audit chain valid\". The tiles show 3 of 5 active clients, ε 1.6149 (unchanged), perplexity 171.28 and "
           "accuracy 4.4 %. The *Client updates* bars for Finance and Healthcare are drawn in a different colour from the others, and *Latest certificate* now shows CERT-30F21BF8C9A3 for "
           "Client 02 (Healthcare) with ε 1.6149 · δ 0.00001 and utility retained 98.30 %."),
    "14": ("14_training_after_unlearning.png", "Training screen after two removals",
           "The training screen keeps the per-client table (original and clipped norms are unchanged, because the stored updates are not modified by unlearning) while the tiles show 3 of 5 active clients, "
           "perplexity 171.28, accuracy 4.4 % and utility 0.085. The button now reads *Retrain model* and the bars of the two removed clients are drawn in a different (light blue) colour."),
    "15": ("15_dashboard_dark.png", "Dashboard in dark mode",
           "The same dashboard in the dark theme: the page, cards and tiles switch to dark surfaces with light text, the toggle in the top bar now shows a sun icon, and the accent colours remain "
           "legible. The numbers are the same as in the light theme (3 of 5 clients, 171.28, 4.4 %, certificate CERT-30F21BF8C9A3)."),
    "16": ("16_unlearning_mobile.png", "Certified unlearning screen on a 390-pixel-wide viewport",
           "On a phone-width viewport the sidebar is replaced by a top bar (menu button, logo, status dot, theme toggle) and a bottom navigation with Home, Train, Forget, Explore and Audit, with Forget "
           "highlighted. The request card stacks vertically (Client 03 — Education, \"3 active clients\", *Execute & certify*) and the certificate card for CERT-30F21BF8C9A3 begins below it."),
    "17": ("17_legacy_ui.png", "Original single-page interface served by the API",
           "The original interface, served at `/` by the Python server, shows the title \"Certified Federated Unlearning Lab\", four tabs (Federated Training, Certified Unlearning, Model Explorer, Compliance Audit) "
           "and the same session state as the React interface: 3 active clients, ε 1.615, perplexity 171.28, accuracy 4.4 %. The client table lists clipped L2 25.000 and clip scales 0.940, 0.886, 0.947, "
           "0.991 and 0.942, with Client 01 and Client 02 marked Removed and the other three Active."),
}


def _screen(d, key, width=5.4, max_h=3.4):
    fn, cap, desc = SCREENS[key]
    d.figure(SHOTS / fn, cap, width=width, max_h=(2.9 if _rep(d) else max_h))
    d.p(desc)


def sec_screens(d, all_screens=False):
    d.h2("Output Screens")
    d.p("The screens below were captured from the running application (Python API on port 8109, React interface on port 5109) at 1440 x 900 pixels by a scripted Chrome session. "
        "The interface was driven by clicks, so every value shown was produced by the application: one session with the default configuration (seed 2026, clip norm 25, noise multiplier 3, δ = 1e-5), "
        "training through the interface, then removal of Client 01 (Finance) and of Client 02 (Healthcare). Each caption describes only what is visible in the picture.")
    keys = MAIN + (EXTRA if all_screens else [])
    if all_screens:
        keys = ["01", "02", "03", "04", "04b", "05", "06", "07", "08", "09", "09b", "10", "11", "12", "13", "14", "15", "16", "17"]
    if _rep(d) and not all_screens:
        # report: screens in pairs (two per row) to keep the chapter within the page budget; each description follows its pair
        for a, b in (("01", "04"), ("05", "06"), ("07", "09"), ("10", "13")):
            d.figure_pair([(SHOTS / SCREENS[a][0], SCREENS[a][1]), (SHOTS / SCREENS[b][0], SCREENS[b][1])], width=3.05, max_h=2.15)
            d.p(SCREENS[a][2])
            d.p(SCREENS[b][2])
    else:
        for k in keys:
            _screen(d, k)
    if not all_screens:
        d.p("The remaining screens (untrained state, confirmation dialog, full-page certificate, second certificate, dashboard after two removals, dark mode, mobile layout and the legacy "
            "interface) are reproduced in Appendix C.")


# ----------------------------------------------------------------------------------------------------------------- engine results
def _studies_synthetic_neural(d):
    """Synthetic-corpus study (real engine, larger federations) and neural adapter study; numbers from experiments/synthetic_corpus and neural_adapter."""
    rep = _rep(d)
    s, nn = _syn, _nn
    rn = s["raw_norms"]
    clip = {(r["clip_mode"], r["sigma"]): r for r in s["clip"]["rows"]}
    c25 = lambda sg: clip[("C = 25 (product default)", sg)]  # noqa: E731
    cmed = lambda sg: clip[("C = median raw norm", sg)]  # noqa: E731
    d.h3("Synthetic-corpus study: more data, larger federations")
    d.p(("`scripts/run_synthetic_corpus.py` generates a seeded synthetic corpus (template grammar, 20 domains; 200 training, 200 held-out and a 300-sentence public set per client) and runs the real engine on it, with a *sentence-level* attack (a client's training sentences against its own held-out sentences) and a *domain-level* attack (against other clients' held-out sentences).") if rep else ("The 25-sentence corpus is too small for the bigram model to learn and gives the membership attack only five members. `scripts/run_synthetic_corpus.py` therefore generates a seeded "
        "synthetic corpus (a template grammar with per-domain vocabularies, 20 domains) with 200 training sentences and 200 held-out sentences per client plus a 300-sentence public set, "
        "and runs the real engine classes on it. Two attacks are used: *sentence-level* (a client's training sentences against its own held-out sentences, which measures memorisation) "
        "and *domain-level* (its training sentences against other clients' held-out sentences, which measures leakage of what the client's data is about); their resolution is 5e-5."))
    d.p((f"The raw norm of a 200-sentence update has median {rn['median']:,.0f}, so the product's C = 25 scales it by {rn['scale_applied_by_product_C25']['mean']:.3f} (about {rn['ratio_median_norm_to_C25']:.0f} times); noise-free perplexity is {c25(1e-09)['ppl_before']['mean']:.1f} at C = 25 against {cmed(1e-09)['ppl_before']['mean']:.1f} at the median norm, so the study uses C = median norm.") if rep else (f"**Clip norm.** The raw update norm of a 200-sentence client has median {rn['median']:,.0f} (range {rn['min']:,.0f} to {rn['max']:,.0f}), so the product's C = 25 scales every update by "
        f"{rn['scale_applied_by_product_C25']['mean']:.3f}, about {rn['ratio_median_norm_to_C25']:.0f} times down. Without noise this costs utility (perplexity {c25(1e-09)['ppl_before']['mean']:.1f} at C = 25 against "
        f"{cmed(1e-09)['ppl_before']['mean']:.1f} at the median norm, because the fixed smoothing constant then dominates the shrunken counts); with noise the small C seems to help "
        f"(perplexity {c25(1.0)['ppl_before']['mean']:.1f} against {cmed(1.0)['ppl_before']['mean']:.1f} at σ = 1) only because it flattens the predictions: accuracy is identical "
        f"({100 * c25(1.0)['acc_before']['mean']:.1f} %). The study therefore uses C = median norm, the setting that preserves the signal."))
    rows = []
    for r in s["sweep"]["rows"]:
        if r["n_clients"] != 10 or r["sigma"] not in (1e-09, 0.1, 1.0, 3.0):
            continue
        eps = "no noise" if r["sigma"] < 1e-6 else f"{r['epsilon']:.3g}"
        sg = "1e-9" if r["sigma"] < 1e-6 else f"{r['sigma']:g}"
        rows.append([sg, eps, f"{r['ppl_before']['mean']:.1f}", f"{r['auc_other_before']['mean']:.3f} → {r['auc_other_after']['mean']:.3f}",
                     f"{r['auc_same_before']['mean']:.3f} → {r['auc_same_after']['mean']:.3f}", pc(r["certified_fraction"], 0)])
    d.table([["σ", "ε", "Perplexity", "Domain-level AUC", "Sentence-level AUC", "Certified"]] + rows,
            "Synthetic-corpus study, 10 clients, 200 sentences each (50 requests per row)", widths=[0.1, 0.12, 0.16, 0.24, 0.26, 0.12], font=9, align=["c"] * 6)
    g = {x["sigma"]: x for x in s["gold"]["results"]}
    g01, g1 = g[0.1], g[1.0]
    d.p((f"The sentence-level AUC stays at 0.50 at every σ: a bigram model does not memorise sentences. The domain-level AUC is 0.474 with the client in the model and falls to 0.220 without noise (0.324 at σ = 0.1) once it is removed; the noise hides this at σ ≥ 1. Fresh-noise retraining gives the same picture (L2 {g01['l2_unlearned_vs_fresh_retrain']['mean']:.0f} against {g01['l2_fresh_retrain_vs_fresh_retrain']['mean']:.0f} at σ = 0.1).") if rep else (f"A bigram model does not memorise sentences: the sentence-level AUC stays at 0.50 before and after removal at every σ, even with no noise. What it does carry is the *domain*: the domain-level "
        f"attack is at chance with the client in the model (0.474) and falls to 0.220 without noise (0.472 to 0.324 at σ = 0.1) once the client is removed, because its now-unseen text is less likely under "
        f"the model than the other clients' text: the fall is the size of the footprint that subtraction removes. At σ ≥ 1 the noise hides the effect (0.490 → 0.463). The fresh-noise comparison above repeats at this scale: the unlearned model is {g01['l2_unlearned_vs_fresh_retrain']['mean']:.0f} from a "
        f"fresh retrain and two retrains are {g01['l2_fresh_retrain_vs_fresh_retrain']['mean']:.0f} apart at σ = 0.1 ({g1['l2_unlearned_vs_fresh_retrain']['mean']:.0f} against "
        f"{g1['l2_fresh_retrain_vs_fresh_retrain']['mean']:.0f} at σ = 1), with equal perplexity ({g1['perplexity_unlearned']['mean']:.1f} and {g1['perplexity_fresh_retrain']['mean']:.1f})."))
    if not rep:
        d.figure(CHARTS / "s02_clip_norm_choice.png", "Perplexity for three choices of the clip norm, with noise (left) and without (right)", width=5.4)
        d.figure(CHARTS / "s04_synthetic_fresh_retrain.png", "Distance between the unlearned model and a fresh retrain, against two fresh retrains (synthetic corpus, 10 clients)", width=4.8)
    d.figure(CHARTS / "s01_synthetic_noise_sweep.png", "Synthetic corpus: perplexity against σ for 5, 10 and 20 clients (left) and the two membership attacks for 10 clients (right)", width=5.7)
    d.p(("**Large federations make ε < 1 useful.** The noise is added once to the sum, which is divided by the number of clients n, so the relative noise shrinks with n. The table gives the perplexity relative to the noise-free model (100 sentences per client, five seeds; * = within 1.2 times).") if rep else ("**Large federations make ε < 1 useful.** The noise is added once to the sum and the sum is divided by the number of clients n, so the relative noise shrinks as n grows. The table gives the "
        "perplexity of the released model relative to the noise-free model (100 synthetic sentences per client, C = median norm, five seeds); a value of 1.2 or less is marked with an asterisk."))
    nrows = {(r["n_clients"], r["sigma"]): r for r in s["n_sweep"]["rows"]}
    rows = []
    for n in (5, 20, 100, 500, 1000, 4000):
        row = [f"{n:,}"]
        for sg in (1.0, 3.0, 4.85, 10.0):
            r = nrows[(n, sg)]
            row.append(f"{r['ratio_to_noise_free']:.2f}" + ("*" if r["within_1_2x"] else ""))
        rows.append(row)
    d.table([["Clients n", "σ = 1 (ε 4.84)", "σ = 3 (ε 1.61)", "σ = 4.85 (ε 1.00)", "σ = 10 (ε 0.48)"]] + rows,
            "Perplexity relative to the noise-free model against federation size (* = within 1.2x)", widths=[0.16, 0.21, 0.21, 0.21, 0.21], font=9.5, align=["c"] * 5)
    sm = s["n_sweep"]["smallest_n_within_1_2x"]
    u = s["n_sweep"]["unlearning_at_smallest_n"]
    ret = min(x["retention_percent"] for x in u["sequential_removals"])
    d.figure(CHARTS / "s03_clients_needed_for_epsilon_below_1.png", "Perplexity relative to the noise-free model against the number of federated clients, for four noise levels", width=4.9)
    d.p((f"With ε < 1 (σ = 4.85) the model is within 1.2 times the noise-free perplexity from {sm['4.85']:,} clients ({sm['3.0']:,} at σ = 3, {sm['1.0']} at σ = 1); at n = {u['n_clients']:,} (ε = {u['epsilon']:.3f}) five removals were all {u['sequential_removals'][0]['status']} with retention ≥ {ret:.3f} %. The five-client demonstration is far too small a federation for the Gaussian mechanism: the proxy is private and useful only in the regime a real federated service lives in.") if rep else (f"With ε below 1 (σ = 4.85) the model is within 1.2 times the noise-free perplexity from about {sm['4.85']:,} clients, and within 1.2 times at the default σ = 3 from {sm['3.0']:,}; at σ = 1 "
        f"{sm['1.0']} clients suffice. At n = {u['n_clients']:,}, σ = {u['sigma']} (ε = {u['epsilon']:.3f}) five successive removals were all {u['sequential_removals'][0]['status']} with retention of at least {ret:.3f} %. "
        "The conclusion for the privacy-utility trade-off is therefore not that the Gaussian mechanism is unusable but that the five-client demonstration is far too small a federation for it: "
        f"the proxy is private and useful only in the regime a real federated service lives in. Timing at 20 clients of 200 sentences: training {s['timing']['train_ms_median']:.0f} ms, `unlearn()` "
        f"{s['timing']['unlearn_ms_median']:.0f} ms, retraining on the 19 retained clients {s['timing']['retrain_retained_ms_median']:.0f} ms; the fixed cost of the metrics and the two attacks again exceeds the proxy's retraining time."))

    d.h3("Neural adapter study: the same method on a small neural model")
    base, cfg = nn["base"], nn["config"]
    ao = nn["summary"]["adapter_only"]
    d.p((f"`scripts/run_neural_experiment.py` applies the release and removal unchanged to a small neural model: a frozen character-level GRU ({base['base_parameters']:,} parameters) pre-trained on synthetic public text, and {cfg['n_clients']} synthetic client domains that each train a LoRA-style adapter ({base['adapter_dimension']:,} parameters, rank {base['adapter_rank']}) on {cfg['train_per_client']} sentences; five seeds, {nn['runtime_seconds']:.0f} s on the CPU. Adapting cuts a client's own-domain perplexity from {ao['base_own_heldout_ppl']['mean']:.0f} to {ao['own_heldout_ppl']['mean']:.2f}.") if rep else (f"To check that the method is not an artefact of a count-based model, `scripts/run_neural_experiment.py` applies ForgetSafe's release and removal unchanged to the parameters of a small neural "
        f"language model. A character-level GRU with {base['base_parameters']:,} parameters is pre-trained on a synthetic public pool and frozen; {cfg['n_clients']} synthetic client domains "
        f"(own vocabulary and sentence templates, {cfg['train_per_client']} training and {cfg['heldout_per_client']} held-out sentences each) each train a LoRA-style low-rank adapter "
        f"({base['adapter_dimension']:,} parameters, rank {base['adapter_rank']}); the flattened adapters are clipped to the median norm, summed, noised with σ·C and divided by n, and a client is removed by subtracting its stored "
        f"adapter. Five seeds, {nn['runtime_seconds']:.0f} s on the CPU. Adapting helps a client's own domain a great deal (held-out perplexity {ao['base_own_heldout_ppl']['mean']:.0f} for the base model, "
        f"{ao['own_heldout_ppl']['mean']:.2f} with its adapter) and a single adapter already leaks (sample-level AUC {ao['sample_auc']['mean']:.2f}, client-level AUC {ao['client_auc']['mean']:.2f})."))
    by = {r["sigma"]: r for r in nn["summary"]["by_sigma"]}

    def cap(x):
        return "≥ 1e8 (destroyed)" if x >= 1e8 else f"{x:.3g}"

    rows = []
    for sg in ((0.0, 0.05, 0.1, 0.3, 3.0) if rep else (0.0, 0.01, 0.05, 0.1, 0.3, 1.0, 3.0)):
        r = by[sg]
        rv = r["retention_retained_ppl_percent"]
        rv = rv["mean"] if isinstance(rv, dict) else rv
        rows.append([f"{sg:g}", "no noise" if r["epsilon"] is None else f"{r['epsilon']:.3g}",
                     f"{cap(r['retained_ppl_before']['mean'])} → {cap(r['retained_ppl_after']['mean'])}",
                     f"{r['client_auc_before']['mean']:.3f} → {r['client_auc_after']['mean']:.3f} ({r['client_auc_retrain']['mean']:.3f})",
                     f"{r['l2_unl_vs_retrain']['mean']:.4g} / {r['l2_retrain_vs_retrain']['mean']:.4g}", "-" if rv is None else f"{rv:.1f}"])
    d.table([["σ", "ε", "Retained-client perplexity", "Client-level AUC before → after (fresh retrain)", "L2 unlearned / retrain vs retrain / retrain", "Retention %"]] + rows,
            "Neural adapter study: removal of one of eight clients (40 requests per row)", widths=[0.07, 0.1, 0.22, 0.27, 0.22, 0.12], font=8.5, align=["c"] * 6)
    d.figure(CHARTS / "n02_neural_membership_auc.png", "Client-level (left) and sample-level (right) membership AUC before removal, after removal and after a fresh retrain", width=5.6)
    if not rep:
        d.figure(CHARTS / "n01_neural_noise_vs_quality.png", "Neural adapter study: perplexity against σ (left) and utility retention after removal (right)", width=5.4)
    tm = nn["summary"]["timing"]
    sq = nn["summary"]["sequential"]
    d.p((f"Removal is real (client-level AUC {by[0.0]['client_auc_before']['mean']:.2f} → {by[0.0]['client_auc_after']['mean']:.2f}, where a fresh retrain sits, {by[0.0]['client_auc_retrain']['mean']:.2f}), and the unlearned model is as far from a fresh retrain as two retrains are from each other at every σ ({by[0.1]['l2_unl_vs_retrain']['mean']:.1f} and {by[0.1]['l2_retrain_vs_retrain']['mean']:.1f} at σ = 0.1). Utility holds to σ = 0.03 (retention {by[0.03]['retention_retained_ppl_percent']['mean']:.1f} %), falls to {by[0.1]['retention_retained_ppl_percent']['mean']:.1f} % at σ = 0.1, below the 70 % floor, and the model is destroyed from σ = 0.3, while ε < 1 needs σ > 4.85. Subtracting an adapter takes {tm['subtract_us_median']:.0f} microseconds against {tm['retrain_seven_adapters_s_median']:.1f} s for retraining the seven retained adapters.") if rep else (f"The three findings of the bigram product recur on a neural model. *Removal is real*: without noise the client-level attack falls from {by[0.0]['client_auc_before']['mean']:.2f} to {by[0.0]['client_auc_after']['mean']:.2f}, "
        f"exactly where a fresh retrain without the client sits ({by[0.0]['client_auc_retrain']['mean']:.2f}); the sample-level AUC of the released average stays at 0.50 because averaging eight adapters hides what a single adapter memorises. "
        f"*The unlearned model is distributed like a retrained one*: its distance to a fresh retrain equals the distance between two fresh retrains at every σ (for example {by[0.1]['l2_unl_vs_retrain']['mean']:.1f} and "
        f"{by[0.1]['l2_retrain_vs_retrain']['mean']:.1f} at σ = 0.1), and the same-noise identity check agrees to float32 rounding ({by[0.0]['identity_max_abs']['mean']:.0e} to {by[3.0]['identity_max_abs']['mean']:.0e}). "
        f"*Privacy and utility compete*: retention of the retained clients' perplexity is {by[0.01]['retention_retained_ppl_percent']['mean']:.1f} % at σ = 0.01, {by[0.05]['retention_retained_ppl_percent']['mean']:.1f} % at σ = 0.05 and "
        f"{by[0.1]['retention_retained_ppl_percent']['mean']:.1f} % at σ = 0.1, below the 70 % floor, and the model is destroyed from σ = 0.3, while ε < 1 would need σ > 4.85; with eight clients the neural study sits in the same "
        "small-federation regime as the bigram product with ten. Removing three clients one after another at σ = 0 raises the public perplexity from "
        f"{sq['sigma=0|step=0']['public_ppl']['mean']:.2f} to {sq['sigma=0|step=3']['public_ppl']['mean']:.2f}. The cost is the clearest gain: subtraction takes {tm['subtract_us_median']:.0f} microseconds, "
        f"the full request with metrics and attack {tm['unlearn_with_metrics_ms_median']:.0f} ms, and retraining the seven retained adapters {tm['retrain_seven_adapters_s_median']:.1f} s, which is "
        f"{tm['speedup_retrain_over_unlearn_with_metrics']:.0f} times slower than the whole request."))
    if not rep:
        d.figure(CHARTS / "n03_neural_retrain_and_cost.png", "Distance to a fresh retrain against distance between fresh retrains (left) and the cost of removing one client (right)", width=5.4)


def sec_engine_results(d):
    rep = _rep(d)
    t = _base["training"]
    d.h2("Model and Verification Results")
    d.p("The results in this section were produced by `scripts/run_experiments.py`, `scripts/run_synthetic_corpus.py` and `scripts/run_neural_experiment.py` on the development machine and are stored in `experiments/*/metrics.json`. Throughout, "
        "*perplexity* and *next-character accuracy* are measured on the five public evaluation sentences, *membership AUC* is the loss-based attack of Chapter 6 (a client's five "
        "records against five fixed non-member sentences, so its resolution is 0.04), and *utility retention* is the utility score after removal divided by the score before, capped at 100 %. The last two subsections extend the study with synthetic data: a larger corpus on the real engine, and a small neural model.")
    d.h3("Baseline run with the default configuration")
    d.p(f"With seed 2026, clip norm 25, noise multiplier 3 and δ = 1e-5 the trained model has ε = {t['epsilon']:.4f}, perplexity {t['perplexity']:.2f} and next-character accuracy "
        f"{pc(t['next_character_accuracy'], 2)} (utility {t['utility_score']:.4f}; training took {t['train_ms']:.1f} ms). A model that spread probability evenly over the 32 symbols it can emit "
        f"would have perplexity {_base['uniform_perplexity_reference']:.0f}, so the trained model is *worse than uniform*. The table gives the result of removing each client in turn from a freshly trained model.")
    rows = []
    for c in _base["unlearning_per_client"]:
        rows.append([c["client_name"], c["status"].title(), f"{c['reference_retrain_l2']:.2e}", f"{c['membership_auc_before']:.2f} → {c['membership_auc_after']:.2f}",
                     f"{c['perplexity_before']:.1f} → {c['perplexity_after']:.1f}", f"{pc(c['accuracy_before'], 2)} → {pc(c['accuracy_after'], 2)}", f"{c['utility_retention_percent']:.2f}"])
    d.table([["Client removed", "Status", "Reference L2", "Membership AUC", "Perplexity", "Accuracy", "Retention %"]] + rows,
            "Removing each client from the default model (seed 2026)", widths=[0.18, 0.11, 0.12, 0.15, 0.17, 0.17, 0.10], font=8.5)
    if not rep:
        d.figure(CHARTS / "c04_baseline_clients.png", "Membership AUC before and after removal, and utility retained, for each client (default run)", width=5.8)
    d.p(("All five requests are CERTIFIED, the reference distance is about 1e-14 and retention lies between 93.6 % and 98.8 %; the lowest values (Finance, Travel) rest on one correct character out of 275. The AUC values scatter around 0.5: ten sentences carry no membership signal at this noise.") if rep else (f"All five requests are CERTIFIED and the reference distance is of the order of 1e-14 (largest {_base['max_reference_l2']:.2e}). Utility retention is between "
        f"{_base['min_retention_percent']:.2f} % and {max(c['utility_retention_percent'] for c in _base['unlearning_per_client']):.2f} % (mean {_base['mean_retention_percent']:.2f} %). The two lowest values, "
        "Finance and Travel, are the two cases in which next-character accuracy fell from 5.09 % to 4.36 %, that is by two correct predictions out of 275 characters; the retention figure is therefore "
        "dominated by a tiny accuracy count. The membership AUC values (0.04 to 0.48 before removal) scatter on both sides of 0.5: with ten sentences and a noisy model they carry no signal about membership."))
    d.h3("Fifty seeds: how stable is the default result?")
    s = _seeds
    d.p(f"To separate the behaviour of the method from the luck of one noise draw, the procedure was repeated for 50 noise seeds and for all five clients, giving {s['n_unlearning_requests']} unlearning requests.")
    d.table([["Quantity", "Mean", "Std. dev.", "Min", "Max"],
             ["Perplexity before removal (50 models)", f"{s['pre_unlearning_perplexity']['mean']:.1f}", f"{s['pre_unlearning_perplexity']['sd']:.1f}", f"{s['pre_unlearning_perplexity']['min']:.1f}", f"{s['pre_unlearning_perplexity']['max']:.1f}"],
             ["Accuracy before removal (50 models)", pc(s['pre_unlearning_accuracy']['mean'], 2), pc(s['pre_unlearning_accuracy']['sd'], 2), pc(s['pre_unlearning_accuracy']['min'], 2), pc(s['pre_unlearning_accuracy']['max'], 2)],
             ["Perplexity after removal (250 requests)", f"{s['perplexity_after_unlearning']['mean']:.1f}", f"{s['perplexity_after_unlearning']['sd']:.1f}", f"{s['perplexity_after_unlearning']['min']:.1f}", f"{s['perplexity_after_unlearning']['max']:.1f}"],
             ["Membership AUC before removal", f"{s['membership_auc_before']['mean']:.3f}", f"{s['membership_auc_before']['sd']:.3f}", f"{s['membership_auc_before']['min']:.2f}", f"{s['membership_auc_before']['max']:.2f}"],
             ["Membership AUC after removal", f"{s['membership_auc_after']['mean']:.3f}", f"{s['membership_auc_after']['sd']:.3f}", f"{s['membership_auc_after']['min']:.2f}", f"{s['membership_auc_after']['max']:.2f}"],
             ["Change in AUC (after - before)", f"{s['membership_auc_change']['mean']:+.3f}", f"{s['membership_auc_change']['sd']:.3f}", f"{s['membership_auc_change']['min']:+.2f}", f"{s['membership_auc_change']['max']:+.2f}"],
             ["Utility retention (%)", f"{s['utility_retention_percent']['mean']:.2f}", f"{s['utility_retention_percent']['sd']:.2f}", f"{s['utility_retention_percent']['min']:.2f}", f"{s['utility_retention_percent']['max']:.2f}"]],
            "Fifty-seed study with the default configuration", widths=[0.40, 0.15, 0.15, 0.15, 0.15], font=9.5, align=["l", "c", "c", "c", "c"])
    if not rep:
        d.figure(CHARTS / "c11_seed_study.png", "Membership AUC and public-set perplexity before and after removal over 250 requests (mean +/- standard deviation)", width=5.2)
    d.p((f"{s['status_counts']['CERTIFIED']} of {s['n_unlearning_requests']} requests are CERTIFIED and none falls below the 70 % floor, but this stabilises only the bookkeeping: the membership AUC is {s['membership_auc_before']['mean']:.3f} before removal (chance) and {s['membership_auc_after']['mean']:.3f} after, and perplexity of about 142 shows a noise-dominated aggregate (expected noise norm {_dp['expected_noise_l2']:.0f} against a clipped client update of 25).") if rep else (f"{s['status_counts']['CERTIFIED']} of {s['n_unlearning_requests']} requests are CERTIFIED, none falls below the 70 % retention floor (the minimum is {s['utility_retention_percent']['min']:.1f} %) "
        f"and the largest reference distance is {s['reference_l2']['max']:.2e}. These numbers are stable, but what they stabilise is the *bookkeeping*. The informative result is the membership AUC: "
        f"{s['membership_auc_before']['mean']:.3f} before removal, which is chance, and {s['membership_auc_after']['mean']:.3f} after, a mean change of only {s['membership_auc_change']['mean']:+.3f}. At the default "
        "noise the attacker learns nothing about a client either before or after the removal, so the experiment has no leakage to show disappearing. The perplexity of about 142 (range "
        f"{s['pre_unlearning_perplexity']['min']:.0f} to {s['pre_unlearning_perplexity']['max']:.0f}) confirms that the aggregate is noise-dominated: the expected noise vector has an L2 norm of "
        f"{_dp['expected_noise_l2']:.0f}, while a clipped client update has norm 25 (about 1 % of the noise)."))
    d.h3("Noise sweep: the privacy-utility trade-off")
    d.p("The noise multiplier σ was varied from 0.001 to 10 (20 seeds, five clients each, 100 requests per value). The reported ε follows the engine's formula ε = sqrt(2 ln(1.25/δ)) / σ with δ = 1e-5, "
        "so ε = 4.8448 / σ.")
    rows = []
    for r in _sweep["rows"]:
        if rep and r["noise_multiplier"] not in (0.001, 0.1, 0.5, 1.0, 3.0, 4.85, 10.0):
            continue
        rows.append([f"{r['noise_multiplier']:g}", f"{r['epsilon']:.3f}", f"{r['perplexity']['mean']:.1f}", pc(r['accuracy']['mean']), f"{r['membership_auc_before']['mean']:.3f}",
                     f"{r['membership_auc_after']['mean']:.3f}", f"{r['retention_percent']['mean']:.1f}"])
    d.table([["σ", "ε", "Perplexity", "Accuracy", "AUC before", "AUC after", "Retention %"]] + rows, "Noise sweep (mean over 100 requests per row)",
            widths=[0.1, 0.14, 0.15, 0.15, 0.16, 0.16, 0.14], font=9, align=["c"] * 7)
    if not rep:
        d.figure(CHARTS / "c01_noise_vs_quality.png", "Perplexity and next-character accuracy against the noise multiplier (dotted lines: default σ = 3 and the ε < 1 boundary at σ = 4.85)", width=5.9)
    d.p(("Three regimes appear: for σ ≤ 0.1 (ε ≥ 48) the model is useful (perplexity 12.5 to 16.3, accuracy about 24 %); for 0.3 ≤ σ ≤ 1 quality degrades quickly; from σ = 2 it is no better than noise (perplexity 145 at σ = 3 against 32 for a uniform model).") if rep else ("Three regimes are visible. For σ <= 0.1 (ε >= 48) the model is a useful bigram model: perplexity 12.5 to 16.3, accuracy about 24 %, and the membership attack works (AUC 0.86 to 0.99 before removal). "
        "For 0.3 <= σ <= 1 quality degrades quickly (perplexity 27 to 66, accuracy 15 % to 5 %). From σ = 2 upward the model is no better than noise; at the default σ = 3 perplexity is 145 against "
        "32 for a uniform model, and at σ = 10 it is 305."))
    if not rep:
        d.figure(CHARTS / "c02_noise_vs_auc.png", "Membership AUC before and after removal against the noise multiplier (error bars: standard error)", width=4.8)
    d.p(("Where there is something to find (small σ) removal works (AUC 0.992 → 0.542 at σ = 0.001, 0.856 → 0.550 at σ = 0.1); where the noise is large the attack is already at 0.52 to 0.55, so the noise that hides the leakage also hides the removal.") if rep else ("The attack gives the second half of the story. Where there is something to find (small σ) the removal clearly works: the mean AUC drops from 0.992 to 0.542 at σ = 0.001 and from 0.856 to 0.550 at σ = 0.1. "
        "Where the noise is large the attack is already at 0.52 to 0.55 before removal, so unlearning has nothing to remove. A privacy-preserving noise level and a measurable forgetting effect "
        "are therefore mutually exclusive in this configuration: the noise that makes the leakage invisible also makes the removal invisible."))
    if not rep:
        d.figure(CHARTS / "c03_privacy_utility.png", "Reported ε against perplexity: the classical bound is valid only to the left of ε = 1", width=4.6)
    d.p((f"The classical bound needs σ > {_dp['sigma_needed_for_epsilon_below_1']:.2f}; at σ = 4.85 perplexity is 198 and accuracy 3.4 %, and the default ε = {_dp['default_epsilon']:.4f} lies outside the proven range: at five clients no point is both proven and useful.") if rep else (f"The classical one-shot Gaussian bound is valid for ε < 1, which needs σ > {_dp['sigma_needed_for_epsilon_below_1']:.2f}. At σ = 4.85 the model has perplexity 198 and accuracy 3.4 %. At the default σ = 3, the "
        f"reported ε = {_dp['default_epsilon']:.4f} lies outside the range for which that bound is proved. There is no point on the curve that is both inside the proven range and useful."))
    d.h3("What unlearning removes when there is no noise")
    nf = _nf
    rows = [[r["client_id"].replace("client_", "").title(), f"{r['member_nll_before']:.3f} → {r['member_nll_after']:.3f}", f"{r['auc_before']:.2f} → {r['auc_after']:.2f}", f"{r['retention_percent']:.2f}"] for r in nf["rows"]]
    d.table([["Client", "Member NLL (before → after)", "Membership AUC (before → after)", "Retention %"]] + rows, "Removal with σ = 1e-6 (essentially no noise)",
            widths=[0.22, 0.30, 0.32, 0.16], font=9.5, align=["l", "c", "c", "c"])
    if not rep:
        d.figure(CHARTS / "c06_noise_free_auc.png", "Membership AUC before and after removal with almost no noise", width=4.5)
    d.p((f"With the noise effectively off, the attack separates members almost perfectly (mean AUC {nf['mean_auc_before']:.3f}) and subtraction brings it to {nf['mean_auc_after']:.3f}; the member loss rises from {nf['mean_member_nll_before']:.3f} to {nf['mean_member_nll_after']:.3f}. This is the evidence that removal works, which the default noise hides.") if rep else (f"To check that removal itself works, the noise was effectively switched off. The attack then separates a client's records from non-members almost perfectly (mean AUC {nf['mean_auc_before']:.3f}), and "
        f"after subtraction it falls to {nf['mean_auc_after']:.3f}, close to chance; the mean per-character loss on the removed client's own sentences rises from {nf['mean_member_nll_before']:.3f} to "
        f"{nf['mean_member_nll_after']:.3f}. Individual AUCs after removal range from 0.20 to 0.88 because the attack uses only ten sentences. This is the evidence that subtracting the stored update really removes "
        "the client's statistical footprint from the model, and it is the experiment that the default configuration cannot provide."))
    d.h3("An independent check: comparison with retraining on fresh noise")
    d.p(("The shipped certificate compares the unlearned model with a reference that shares the stored noise and updates, so its distance is zero by construction. The experiment `gold_retrain` compares it with models retrained on the retained clients with independent noise (200 pairs per σ), with two independent retrains as the yardstick.") if rep else ("The shipped certificate compares the unlearned model with a \"reference\" built from the retained clients' stored updates *and the same stored noise*; the two sides share every input, so their distance "
        "is zero up to rounding by construction. A real retraining would draw new noise. The experiment `gold_retrain` therefore compares each unlearned model with models retrained on the retained clients with "
        "independent noise (200 pairs for each σ), and compares two independent retrainings with each other as the yardstick for how far two honest runs differ."))
    rows = []
    for r in _gold["results"]:
        rows.append([f"{r['noise_multiplier']:g}", f"{r['l2_unlearned_vs_fresh_retrain']['mean']:.1f} ± {r['l2_unlearned_vs_fresh_retrain']['sd']:.1f}",
                     f"{r['l2_fresh_retrain_vs_fresh_retrain']['mean']:.1f} ± {r['l2_fresh_retrain_vs_fresh_retrain']['sd']:.1f}",
                     f"{r['membership_auc_unlearned']['mean']:.3f} / {r['membership_auc_fresh_retrain']['mean']:.3f}",
                     f"{r['perplexity_unlearned']['mean']:.1f} / {r['perplexity_fresh_retrain']['mean']:.1f}",
                     f"{pc(r['accuracy_unlearned']['mean'], 2)} / {pc(r['accuracy_fresh_retrain']['mean'], 2)}"])
    d.table([["σ", "L2: unlearned vs fresh retrain", "L2: fresh retrain vs fresh retrain", "AUC (unlearned / retrain)", "Perplexity", "Accuracy"]] + rows,
            "Unlearned model against retraining with independent noise (200 pairs per σ)", widths=[0.07, 0.21, 0.21, 0.19, 0.16, 0.16], font=8.5, align=["c"] * 6)
    if not rep:
        d.figure(CHARTS / "c05_gold_retrain.png", "Distance between the unlearned model and a fresh retrain, compared with the distance between two fresh retrains", width=5.0)
    g3, g05 = _gold["results"]
    d.p((f"The unlearned model is as far from a fresh retrain as two retrains are from each other ({g3['l2_unlearned_vs_fresh_retrain']['mean']:.1f} against {g3['l2_fresh_retrain_vs_fresh_retrain']['mean']:.1f} at σ = 3): the distance is the injected noise, and perplexity, accuracy and AUC agree within it.") if rep else (f"At σ = 3 the unlearned model is {g3['l2_unlearned_vs_fresh_retrain']['mean']:.1f} away from a fresh retrain and two fresh retrains are {g3['l2_fresh_retrain_vs_fresh_retrain']['mean']:.1f} apart; at σ = 0.5 the figures are "
        f"{g05['l2_unlearned_vs_fresh_retrain']['mean']:.1f} and {g05['l2_fresh_retrain_vs_fresh_retrain']['mean']:.1f}. The unlearned model is therefore exactly as far from a retrained model as retrained models are from each other: "
        "the distance is the injected noise, and the unlearned model behaves like one more retrained model. Perplexity and accuracy agree to within the noise (167 against 153 at σ = 3, 46.0 against 44.6 at σ = 0.5), "
        "and the membership AUC of the unlearned model is, if anything, closer to chance than that of the retrained model (0.481 against 0.552 at σ = 3). This is the evidence that the unlearned model is "
        "distributed like a retrained one, which the 1e-14 reference distance does not demonstrate on its own."))
    if not rep:
        d.h3("Sequential removal")
        rows = []
        for st in _seq["steps"]:
            rows.append([str(st["step"]), st.get("removed", "-").replace("client_", "").title() if st.get("removed") else "-", str(st["active_clients"]), f"{st['perplexity']:.1f}", pc(st["next_character_accuracy"], 2),
                         f"{st['retention_percent']:.2f}" if "retention_percent" in st else "-", st.get("status", "-").title() if st.get("status") else "-"])
        d.table([["Step", "Removed", "Active clients", "Perplexity", "Accuracy", "Retention %", "Status"]] + rows, "Removing four of the five clients in turn (seed 2026)",
                widths=[0.08, 0.17, 0.15, 0.15, 0.15, 0.16, 0.14], font=9.5, align=["c"] * 7)
        if not rep:
            d.figure(CHARTS / "c07_sequential_removal.png", "Perplexity and accuracy as clients are removed one after another", width=5.2)
        d.p(f"All four removals are CERTIFIED and the ledger verifies afterwards (\"{_seq['audit_detail']}\"). Perplexity rises from {_seq['steps'][0]['perplexity']:.0f} to {_seq['steps'][-1]['perplexity']:.0f} as the five clients are reduced to one: "
            "the noise vector is unchanged while the aggregate is divided by a smaller client count, so the relative weight of the noise grows. Removing the fifth client is refused with \"At least one client must remain in the model\". "
            "Retention values remain above 93 % at every step because each is measured against the previous model, which is already poor.")
    else:
        d.p("Removing four of the five clients in turn (seed 2026) kept every request CERTIFIED and the ledger valid; perplexity rose from 130 to 303 because the unchanged noise is divided by a smaller client count, and the fifth removal is refused (\"At least one client must remain in the model\").")
    _studies_synthetic_neural(d)


# ----------------------------------------------------------------------------------------------------------------- product results
def sec_product_results(d):
    d.h2("Certificate, Ledger and API Results")
    d.p("The product's visible output is the certificate and the ledger record behind it. The first removal of the default session (Client 01, Finance) produced the following values; the field names are those of "
        "the JSON that `GET /api/certificate/latest` returns.")
    c = _base["unlearning_per_client"][0]
    rows = [["certificate_id / status", f"{c['certificate_id']} / {c['status']}"],
            ["client", c["client_name"]],
            ["method", c["method"]],
            ["epsilon, delta", f"{c['epsilon']:.4f}, {c['delta']}"],
            ["clip_norm, noise_multiplier", f"{c['clip_norm']:g}, {c['noise_multiplier']:g}"],
            ["residual_influence_l2 = reference_retrain_l2", f"{c['residual_influence_l2']:.3e}"],
            ["membership_auc_before → after", f"{c['membership_auc_before']:.2f} → {c['membership_auc_after']:.2f}"],
            ["perplexity_before → after", f"{c['perplexity_before']:.3f} → {c['perplexity_after']:.3f}"],
            ["accuracy_before → after", f"{pc(c['accuracy_before'], 2)} → {pc(c['accuracy_after'], 2)}"],
            ["utility_retention_percent", f"{c['utility_retention_percent']:.2f}"],
            ["clients_before → after", f"{c['clients_before']} → {c['clients_after']}"],
            ["model_hash_before", c["model_hash_before"][:32] + "…"],
            ["model_hash_after", c["model_hash_after"][:32] + "…"],
            ["audit_record_hash", c["audit_record_hash"][:32] + "…"]]
    d.table([["Field", "Value (default session, seed 2026)"]] + rows, "Fields of the unlearning certificate", widths=[0.38, 0.62], font=9)
    d.p("Two fields deserve a remark. `residual_influence_l2` and `reference_retrain_l2` are always equal: the engine assigns one to the other (the comment in `engine.py` explains that the stored update is subtracted "
        "algebraically, so its coefficient in the retained aggregate is zero within floating-point error). And `epsilon` is the training-time value; the certificate does not recompute any privacy figure after the removal.")
    d.p("Every training and every unlearning event becomes one line of `data/audit_log.jsonl`. A record keeps its event fields and adds `sequence`, `previous_hash` and `record_hash`, where the hash is the SHA-256 of "
        "the predecessor's hash, a vertical bar and the canonical (sorted, compact) JSON of the record. The first record's predecessor is 64 zeros. The certificate's `audit_record_hash` equals the hash of its own ledger record, "
        "which is how a certificate is tied to the ledger: in the capture session certificate CERT-C5427F948A72 carries 208f652b947ede28…, the hash shown in row 3 of the ledger screen.")
    d.p("The API returned the expected status codes for all 14 smoke checks and for 18 of the 20 edge-case probes (Chapter 7). It kept a correct ledger under 32 simultaneous removals and 16 simultaneous trainings, and 20 scripted synthetic-user journeys passed every step. Typical latencies on the local loop-back were 36 ms for training and 58 ms for a complete unlearning request, and a certificate is available for download as JSON with the audit verdict attached.")


# ----------------------------------------------------------------------------------------------------------------- comparison
def sec_comparison(d):
    d.h2("Comparison with the Base Paper and Related Work")
    d.p("The comparison has to begin with a plain statement of what can and cannot be compared. The base paper recorded in the batch files, Khan et al. [1], is a review of deep-learning approaches to continuous "
        "sign language recognition. Its subject is unrelated to federated unlearning, it reports no unlearning, privacy or language-model measurement, and this project adopts only its *review method*: a taxonomy of approaches, "
        "a comparison of strengths and limitations and the identification of open gaps. **No numerical comparison with [1] is possible, and none is made.**")
    d.p("The technically closest works are [2] (the paper named in the project's base-paper record as the 2026 base paper), [3] and [4]. They were read from the PDFs kept in the project's archive; the table "
        "lists what they evaluate. ForgetSafe's numbers are **not comparable** with theirs: those works train real neural networks on public benchmarks, while ForgetSafe measures a 1,089-parameter bigram model on 25 hand-written sentences, synthetic corpora with up to 4,000 clients, and a 137,151-parameter GRU with LoRA-style adapters on synthetic text.")
    d.table([["Work", "Setting and data", "Method", "What it reports", "Relation to ForgetSafe"],
             ["[1] Khan et al. (IEEE Access, 2025)", "Review of continuous sign language recognition", "Taxonomy of spatial, temporal and alignment approaches", "Survey of studies, datasets, challenges and gaps", "Review method only; subject unrelated; no results to compare"],
             ["[2] Wei et al. (KDD 2026)", "Federated unlearning on CIFAR-10, CIFAR-100 and EMNIST with ResNet-18, ResNet-34 and VGG-9; six baselines", "FedMemPrune: pruning of parameters that carry memorised information, guided by a grouped memorisation metric", "Abstract: closely matches retraining-based baselines while eliminating memorisation more effectively than existing methods", "Same goal (client-level removal in FL); ForgetSafe subtracts a stored update instead of pruning, and has no image or example-level evaluation"],
             ["[3] Zhang et al., Oblivionis (arXiv, 2025)", "Federated LLM fine-tuning and unlearning with Llama-2-7B and Llama-3.x models on the TOFU and MUSE benchmarks", "Framework combining 6 federated-learning and 5 unlearning algorithms", "Forget quality and model utility across algorithm pairs; motivated by GDPR erasure", "Same problem at LLM scale; ForgetSafe is a bigram stand-in without any LLM"],
             ["[4] Jiang et al., FedORA (arXiv, 2025)", "Vertical federated learning on Income (48,842 samples), MedMNIST, CIFAR-10, CIFAR-100 and Tiny-ImageNet", "Primal-dual optimisation with a theoretical bound to training from scratch", "Unlearning effectiveness comparable to retraining at lower computation and communication", "Provides a formal bound where ForgetSafe provides an identity check; different FL setting (vertical)"]],
            "What the closest works evaluate, and why the numbers are not comparable", widths=[0.15, 0.22, 0.21, 0.21, 0.21], font=8.5)
    rep = bool(getattr(d, "report", False))
    d.p(("Three qualitative observations follow. First, [2] and [4] state their evidence against *retraining*, and ForgetSafe adopts that yardstick on all three of its models (L2 875 against 881, 645 against 650, 31.8 against 31.8); what those works have and it lacks is a benchmark with real pretrained models. Second, [3] needs forget-quality and utility metrics on real text, of which bigram and GRU perplexity are the crudest. Third, ForgetSafe adds an inspectable end-to-end workflow with measured weaknesses, the federation size at which ε < 1 and a useful model coexist (about 1,000 clients) and the cost of removal against retraining (24 microseconds against 5.9 s for adapters).") if rep else ("Three qualitative observations follow. First, [2] and [4] state their guarantee or their evidence against *retraining*, and ForgetSafe adopts the same yardstick on all three of its models (fresh-noise retraining: 875 against 881, 645 against 650 and 31.8 against 31.8 in L2 distance, each equal to the distance between two retrains); what those works have and ForgetSafe lacks is a benchmark with real pretrained models. Second, [3] shows that the federated-LLM setting needs forget-quality and utility metrics on real text; the perplexities here, bigram and GRU, are the crudest members of that family, but the GRU study shows the method working on adapter parameters of the kind [3] uses. Third, what ForgetSafe adds is an end-to-end, inspectable workflow in which the guarantee, the attack, the utility check and the audit record are produced together for every request, with the weaknesses of each step measured and reported, and two quantitative results the other works do not give: the federation size at which ε < 1 and a useful model coexist (about 1,000 clients) and the cost of removal against retraining (24 microseconds against 5.9 s for adapters)."))


# ----------------------------------------------------------------------------------------------------------------- samples
def sec_samples(d):
    d.h2("Sample Inputs and Outputs")
    d.p("The following requests and responses were captured from a live server started for this purpose (`scripts/capture_samples.py`, port 8197, a temporary working directory), using the default configuration; "
        "they are stored in `docs/sample_io/samples.json`. Certificate identifiers and timestamps differ from run to run, the numerical fields do not.")
    tr = _samples["train"]
    d.code(f"{tr['request']}   ->   HTTP {tr['status']}\n" + json.dumps(tr["response"], indent=2), "Training request and response")
    gb, ga = _samples["generate_before"], _samples["generate_after"]
    d.code(f"{gb['request']}   ->   HTTP {gb['status']}\n" + json.dumps(gb["response"], indent=2), "Text generated before the removal")
    un = _samples["unlearn"]
    resp = dict(un["response"])
    d.code(f"{un['request']}   ->   HTTP {un['status']}\n" + json.dumps(resp, indent=2), "Unlearning request and the certificate it returns")
    d.code(f"{ga['request']}   ->   HTTP {ga['status']}\n" + json.dumps(ga["response"], indent=2), "Text generated after the removal")
    av, ru = _samples["audit_verify"], _samples["repeat_unlearn"]
    d.code(f"{av['request']}   ->   HTTP {av['status']}\n" + json.dumps(av["response"], indent=2) + f"\n\n{ru['request']}   ->   HTTP {ru['status']}\n" + json.dumps(ru["response"], indent=2),
           "Audit verification and a repeated request")
    same = gb["response"]["text"] == ga["response"]["text"]
    d.p(f"Reading the samples: the training response carries the privacy and quality figures and the SHA-256 fingerprint of the parameter vector; the unlearning response carries every field of the certificate, "
        "including the model hash before and after (they differ, so the parameters changed) and the audit record hash. The two generated texts are " + ("**identical**" if same else "different") +
        ": the generator draws from a fixed random seed and the noisy probabilities changed too little to alter a draw. The text therefore cannot be used to see the removal, and the evidence for it has to come from the attack and "
        "the retraining comparison above. The repeated request is refused with a clear JSON error and leaves the model and the ledger unchanged.")
    recs = _samples["state_audit_records"]
    d.table([["Seq.", "Event", "previous_hash (first 16)", "record_hash (first 16)"]] +
            [[str(r["sequence"]), r["event_type"], r["previous_hash"][:16] + "…", r["record_hash"][:16] + "…"] for r in recs],
            "The two ledger records written by this sequence of requests", widths=[0.08, 0.32, 0.30, 0.30], font=9)


# ----------------------------------------------------------------------------------------------------------------- success / failure
def sec_success_failure(d):
    d.h2("Success and Failure Analysis")
    d.h3("What worked")
    sp = _sp["classification_counts"]
    d.table([["Success", "Evidence"],
             ["The unlearning workflow is complete and repeatable", "train → request → subtract → verify → certificate → ledger; 250/250 certified over 50 seeds; 5 unit tests, 14 smoke checks and 20/20 scripted acceptance journeys pass"],
             ["Removal is real when there is something to remove", "bigram, no noise: AUC 0.992 → 0.544; synthetic corpus, domain level 0.474 → 0.220; neural adapters, client level 0.78 → 0.53 (a fresh retrain gives 0.53)"],
             ["The unlearned model behaves like a retrained one", "L2 to a fresh retrain 875 against 881 between two fresh retrains (bigram, σ = 3); 645 against 650 (synthetic corpus, σ = 0.1); 31.8 against 31.8 (neural, σ = 0.1)"],
             ["ε < 1 and a useful model coexist in a large federation", "σ = 4.85 (ε = 0.999) and perplexity within 1.17 times noise-free at 1,000 synthetic clients; five removals CERTIFIED, retention ≥ 99.998 %"],
             ["Removal is cheap where retraining is not", "neural adapters: 24 µs to subtract against 5.9 s to retrain seven adapters; bigram proxy: 6.8 times faster than retraining at 500 clients"],
             ["Concurrency is correct", "32 simultaneous removals of one client: one 200, 31 × 400; 16 simultaneous trainings: 16 valid ledger records; 2,000-request soak without errors"],
             ["The guards and the interface hold up", "untrained, unknown, repeat and last-client requests refused with JSON errors; 20 journeys × 7 steps, 49 certificates, 0 console errors; light, dark and 390-px layouts"]],
            "Cases in which the system succeeds", widths=[0.30, 0.70], font=9)
    d.h3("Weak points and defects, as measured")
    d.table([["Weak point or defect", "Evidence", "Consequence"],
             ["The default model is noise-dominated", "perplexity 142 ± 28 against 32 for a uniform model; accuracy 3.7 %; noise norm about 100 times a client's signal", "retained \"utility\" of 97 % is measured against an almost useless model"],
             ["Nothing is visible to remove at the default setting", "membership AUC 0.524 before and 0.495 after (chance); sentence-level AUC 0.50 even without noise", "at five clients and σ = 3 the attack neither supports nor refutes forgetting"],
             ["The certificate cannot fail", "reference distance 1e-14 on 250/250 requests; the reference shares the stored noise and updates", "CERTIFIED states that the arithmetic was done correctly; the fresh-noise comparison supplies the independent evidence"],
             ["ε is outside its proven range, noise is reused, no accountant", "ε = 1.6149 > 1 at σ = 3; with the noise reused, n·θ − (n−1)·θ′ recovers the removed update to 1.3e-13", "the certificate's ε is a one-release figure; the released models must not both be published"],
             ["Small federations are not both private and useful", "five clients: ε < 1 gives perplexity 198 and accuracy 3.4 %; eight neural clients: destroyed from σ = 0.3, 59 % retention at σ = 0.1", "the demonstration size is the cause; 1,000 clients are needed (previous section)"],
             ["The explorer cannot show the effect", "the 44-character samples before and after a removal are identical", "the screen is illustrative only"],
             ["The ledger is not tamper-proof and can break the UI", "tail truncation, re-hash forgery, a forged appended record and an emptied file all verify; one garbage line makes `/api/state` return 500", "signatures, an external anchor and tolerant reading are needed (Chapter 10)"],
             ["Defects in the HTTP layer", f"{sp['defect']} defects in {_sp['n_probes']} probes, six of them in the HTTP layer: negative and short Content-Length block a thread, a cross-site POST removes a client, Host is not checked, a 64-connection burst has 30 refused, no authentication; the other two are the ledger-file defects above", "acceptable for a local demonstrator, not for a service (Chapter 7 lists the fixes)"],
             ["Unlearning is not faster on the small demo", "45.3 ms against 13.4 ms for retraining the proxy; break-even near 100 clients", "the efficiency claim holds at scale (500 clients, neural adapters)"]],
            "Weak points and defects found", widths=[0.26, 0.40, 0.34], font=8.5)


def sec_results_limits(d):
    d.h2("Boundaries of the Results")
    d.p("Four boundaries define what the results of this chapter cover; each is stated with the evidence that sets it.")
    d.bullets([
        "**Scale.** The product is a 1,089-parameter bigram model; the neural adapter study uses a 137,151-parameter GRU with 8 synthetic clients and one aggregation round, and the synthetic-corpus study up to 4,000 synthetic clients. No pretrained billion-parameter language model is used, and no claim is made about one.",
        "**Data.** The product's 25 sentences and every other corpus are synthetic (seeded generators); membership AUC has a resolution of 0.04 at five sentences and 5e-5 at 200, with a standard deviation of 0.22 over the 250 default requests.",
        "**Acceptance.** Interface acceptance is established by 20 scripted synthetic-user journeys, not by human participants.",
        "**Machine and baselines.** All timings are medians from one CPU workstation (i5-12500, 15.7 GB, no GPU); the only comparison algorithm is retraining. Gradient ascent, SISA sharding, pruning [2] and primal-dual methods [4] are compared with in the literature table, not implemented."])


def sec_objectives(d):
    d.h2("Objectives Against Outcomes")
    d.p("The six objectives come from the project's objectives and problem statement. The verdicts use the evidence of this chapter and of Chapter 7.")
    d.table([["No.", "Objective", "Outcome", "Verdict"],
             ["1", "Set up federated fine-tuning of an LLM across multiple clients", "Federated aggregation of clipped, noised updates across 5 simulated clients on the bigram proxy, and across 8 synthetic clients fine-tuning LoRA-style adapters of a 137,151-parameter GRU; pretrained billion-parameter LLMs are outside the project's scope and hardware", "Met at small scale"],
             ["2", "Remove a client's influence by parameter-level unlearning without full retraining", "Exact subtraction of the tracked update in both models; 250/250 bigram requests; neural removal 24 µs against 5.9 s retraining; behaves like a fresh retrain", "Met"],
             ["3", "Certify forgetting with differential-privacy based guarantees", "ε and δ reported with the classical formula; outside its range at σ = 3 (ε = 1.6149); ε < 1 and a useful model coexist from about 1,000 clients (ε = 0.999); noise reused, no accountant", "Met as reported, with measured conditions"],
             ["4", "Verify with membership-inference tests and comparison with retraining", "Attack and reference check on every request; fresh-noise retraining comparison agrees on three models (L2 875 vs 881; 645 vs 650; 31.8 vs 31.8); the attack is informative where leakage exists (noise-free, small σ, domain level)", "Met"],
             ["5", "Preserve model utility on the remaining data", "Retention 97.1 % ± 3.5 over 250 bigram requests; neural 99.9 % at σ ≤ 0.01 and 98.5 % at σ = 0.03; 59 % at σ = 0.1 would be REVIEW_REQUIRED", "Met, with the measured noise limits"],
             ["6", "Provide auditable compliance records for each request", "Every training and removal is a hash-chained record linked to its certificate; edits, deletions and swaps detected; truncation, re-hash forgery and an emptied file are not (findings with fixes in Chapter 10)", "Met with measured defects"]],
            "Objectives measured against outcomes", widths=[0.06, 0.26, 0.50, 0.18], font=9)


