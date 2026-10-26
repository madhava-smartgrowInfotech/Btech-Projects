"""Implementation decisions, conclusion, future scope, references and appendices (ForgetSafe).

Numbers come from experiments/*/metrics.json; code listings are extracted from the source files when the document is built, so they match the code that
produced the results."""
from __future__ import annotations

import re

from docx.shared import Inches

from doc_common import CHARTS, REFERENCES, ROOT, SHOTS, UNVERIFIED, metrics

_base = metrics("baseline")
_seeds = metrics("seeds")
_nf = metrics("noise_free_leakage")
_gold = metrics("gold_retrain")
_sc = metrics("scaling")
_dp = metrics("dp_accounting")


# ----------------------------------------------------------------------------------------------------------------- decisions
def sec_decisions(d):
    d.h2("Implementation Decisions and Their Reasoning")
    d.p("A small system is made of a small number of decisions, and each of them fixes something that the evidence of Chapters 7 and 8 later measures. The table lists the main decisions, the reason for each and what it cost; "
        "the paragraphs that follow explain the three decisions that shape the results most.")
    d.table([["Decision", "Reason", "Cost"],
             ["Python standard library only for the engine and the API", "runs offline on a classroom computer with no installation; every line is inspectable; reproducible by `python app.py`", "hand-written HTTP handler: no authentication, HTML 501 for unsupported methods, aborted connection on oversized bodies"],
             ["Character-bigram model as a stand-in for an LLM adapter", "a 1,089-value parameter vector lets subtraction, verification and the attack run in milliseconds; the orchestration is separate from the model, so a LoRA tensor could replace it", "no claim about real LLMs can be made; the model is useless at the default noise"],
             ["Additive aggregation with stored per-client updates", "makes removal an exact vector subtraction without access to raw records", "the server must keep every client's clipped update, which is itself sensitive; only linear aggregation is supported"],
             ["L2 clipping at C = 25 before aggregation", "bounds each client's contribution (the sensitivity of the sum) so that Gaussian noise can be calibrated", "all five raw norms (25.2 to 28.2) exceed C, so all updates are scaled to the same length"],
             ["Noise drawn once per training session and kept", "the retained-only recomputation can reproduce the unlearned model exactly; the model is a deterministic function of its inputs", "the reference check is an identity; the privacy accounting of a second release is not addressed"],
             ["Classical Gaussian formula ε = sqrt(2 ln(1.25/δ)) / σ", "standard, easy to state and to verify in a test", "valid only for ε < 1; the default σ = 3 gives ε = 1.6149, outside that range"],
             ["Loss-based membership attack on ten sentences", "cheap, deterministic, needs no shadow models", "AUC resolution 0.04; uninformative at the default noise"],
             ["CERTIFIED if reference L2 <= 1e-10 and retention >= 70 %", "two explicit, documented thresholds for a demonstration", "the first can never fail and the second never binds (minimum observed retention 79.9 %)"],
             ["Append-only JSONL ledger with SHA-256 chaining", "human-readable, trivial to append and to verify, no database", "append re-reads the whole file; no signatures or external anchor"],
             ["React frontend over the unchanged API (ports 5109 and 8109)", "the working engine and the original interface stay untouched; Vite proxies `/api`, so no CORS change", "two processes to start; the legacy page is kept in parallel"],
             ["One shared engine guarded by a lock", "simple and correct under concurrency: 32 simultaneous removals of one client gave exactly one success", "no multi-user separation; throughput of the state call saturates near 80 requests per second"],
             ["Fixed random seed 2026 in the default engine", "reproducible demonstrations and tests", "a single noise draw unless seeds are varied (the experiments vary them)"]],
            "Main implementation decisions", widths=[0.26, 0.38, 0.36], font=8.5)
    d.h3("Why subtraction instead of an approximate algorithm")
    d.p("The literature offers many ways to unlearn: retraining, sharded retraining [12], influence-function updates with a certified bound [13][14], client-level calibration [17] and, more recently, pruning of memorising parameters [2] "
        "and primal-dual optimisation [4]. ForgetSafe takes the simplest exact route that its own aggregation allows. Because the released model is `theta = (sum of clipped updates + noise) / n`, a client's contribution is a known additive term, "
        "and removing it needs no optimisation and no access to the client's data. The price of exactness is the storage of every client's clipped update on the coordinator and the restriction to one-shot linear aggregation. "
        "Neither restriction would survive in a real LLM pipeline with several rounds of non-linear local training, which is why the report presents the result as a verified *workflow* rather than as an algorithm that scales.")
    d.h3("Why the noise is kept")
    d.p("The unlearned model is `(noisy_sum - u_j) / (n - 1)` and the reference is `(noise + sum of retained updates) / (n - 1)`. Keeping the same noise vector makes the two identical, which is what lets the engine state its certificate as an "
        "equality with a tolerance. The alternative, drawing fresh noise at every release, gives a more honest comparison with retraining (as the added experiment shows) but then the equality is only distributional, "
        "and the cumulative privacy loss over several releases has to be accounted for. The project chose the first option for the demonstration and measured the second separately; the report treats this as the most important design "
        "limitation of the certificate.")
    d.h3("Why a frontend rebuild left the backend alone")
    d.p("The backend already exposed a complete JSON API for the original single-page interface. A modern React interface was added on top of it without changing `certified_unlearning/` or `app.py`; the Vite development server "
        "proxies `/api` to port 8109, and ports are read from `.env` by `run.bat` and `vite.config.js`. This kept the tested engine stable (the five unit tests and the smoke test never needed to change) and kept the original interface, the "
        "Tkinter desktop window and the command-line demonstration working. The cost is that API weaknesses such as the missing authentication remain visible in the new interface.")


# ----------------------------------------------------------------------------------------------------------------- conclusion
def sec_conclusion_summary(d):
    d.h2("Summary of the Work")
    d.paras(
        "Machine unlearning promises that a participant's influence can be removed from a trained model on request, and the General Data Protection Regulation's right to erasure [20] is the usual motivation. For federated "
        "language models the difficulty is double: the data never leaves the clients, yet each client's influence stays in the shared parameters, and retraining a large model for every request is impractical. The project asked what a "
        "*certified and auditable* removal workflow for such a setting would look like, and answered it with ForgetSafe, a working demonstrator.",
        "ForgetSafe simulates five federated clients, clips each client's update, aggregates the updates with calibrated Gaussian noise into a global character-level language model that stands in for an LLM adapter, and removes a client by subtracting "
        "its stored update. Each removal is verified against a retained-only recomputation, evaluated with a loss-based membership-inference attack, measured for retained utility, and written as a certificate and as a SHA-256 hash-chained ledger record. "
        "The system is a standard-library Python engine and API, a React web interface, the original single-page interface, a Tkinter window and a command-line demonstration, with 5 unit tests and 14 smoke checks. "
        "Four measurement studies on synthetic data produced the evidence of this report: the 50-seed and noise-sweep experiments on the product, a synthetic-corpus study with up to 4,000 clients, a neural study in which eight synthetic "
        "clients fine-tune LoRA-style adapters of a 137,151-parameter GRU, and load, security and scripted-acceptance tests of the running system.")


def sec_conclusion_objectives(d):
    d.h2("Objectives Achieved")
    d.table([["Objective", "Verdict", "Basis"],
             ["1. Federated fine-tuning of an LLM across clients", "Met at small scale", "5 bigram clients; 8 synthetic clients fine-tuning LoRA-style adapters of a 137,151-parameter GRU; pretrained billion-parameter LLMs are outside the scope"],
             ["2. Parameter-level unlearning without full retraining", "Met", "exact subtraction in both models; 250/250 bigram requests; neural removal 24 µs against 5.9 s of retraining"],
             ["3. Certification with differential-privacy guarantees", "Met as reported, with conditions", "ε and δ reported; outside the classical range at σ = 3; ε < 1 with a useful model from about 1,000 clients; noise reused, no accountant"],
             ["4. Verification by membership inference and comparison with retraining", "Met", "run on every request; fresh-noise retraining comparison agrees on three models; the attack is informative where leakage exists"],
             ["5. Utility preserved on the remaining data", "Met, with the measured noise limits", f"mean retention {_seeds['utility_retention_percent']['mean']:.1f} % (bigram), 99.9 % at σ ≤ 0.01 and 59 % at σ = 0.1 (neural)"],
             ["6. Auditable compliance record per request", "Met with measured defects", "every event hash-chained and linked to its certificate; truncation, re-hash forgery and an emptied file undetected"]],
            "Objectives and verdicts", widths=[0.36, 0.2, 0.44], font=9.5)
    d.p("All six objectives are met within the stated scale. Two carry measured conditions that the report turns into engineering items: the privacy guarantee (objective 3) holds in the useful regime only for large "
        "federations, and the audit record (objective 6) needs signatures and an external anchor.")


def sec_conclusion_findings(d):
    d.h2("Key Findings")
    s = _seeds
    syn = metrics("synthetic_corpus")
    nn = metrics("neural_adapter")
    ld = metrics("load_test")
    sp = metrics("security_probe")
    ac = metrics("acceptance")
    g = _gold["results"][0]
    by0 = nn["summary"]["by_sigma"][0]
    d.numbered([
        f"**At five clients and the default noise the model is dominated by noise and there is nothing to remove.** Perplexity is {s['pre_unlearning_perplexity']['mean']:.0f} ± {s['pre_unlearning_perplexity']['sd']:.0f} over 50 seeds against 32 for a uniform model, and the membership attack is at chance before removal (AUC {s['membership_auc_before']['mean']:.2f}) and after ({s['membership_auc_after']['mean']:.2f}).",
        f"**The removal itself is real.** With the noise switched off the attack falls from {_nf['mean_auc_before']:.3f} to {_nf['mean_auc_after']:.3f} (bigram), from 0.474 to 0.220 at domain level on the synthetic corpus, and from {by0['client_auc_before']['mean']:.2f} to {by0['client_auc_after']['mean']:.2f} on neural adapters, where a fresh retrain gives {by0['client_auc_retrain']['mean']:.2f}.",
        f"**The shipped certificate is an identity, not an independent proof; the independent check agrees.** The reference reuses the stored noise and updates, so its distance (about 1e-14) cannot fail. Compared with retraining on fresh noise, the unlearned model is as far from a retrain as two retrains are from each other: {g['l2_unlearned_vs_fresh_retrain']['mean']:.0f} against {g['l2_fresh_retrain_vs_fresh_retrain']['mean']:.0f} (bigram), 645 against 650 (synthetic corpus), 31.8 against 31.8 (neural).",
        f"**Privacy and utility meet only in large federations.** With five or eight clients ε < 1 needs σ > {_dp['sigma_needed_for_epsilon_below_1']:.2f} and the model is destroyed; on the synthetic corpus the released model is within 1.2 times the noise-free perplexity at ε = 0.999 from about {syn['n_sweep']['smallest_n_within_1_2x']['4.85']:,} clients. The product's clip norm C = 25 is about 50 times too small for 200-sentence clients.",
        "**Reusing the noise has a measurable consequence.** With the same noise in both releases, n·θ − (n−1)·θ′ recovers the removed client's clipped update to 1.3e-13, and the printed ε is a training-time figure; the exact analytic Gaussian calibration gives ε = 1.271 at σ = 3 (reported 1.615) but 9.997 at σ = 0.5 (reported 9.690).",
        f"**The audit ledger catches careless tampering only.** Edits, deletions and swaps are detected; tail truncation, a full re-hash forgery, an appended forged record and an emptied file are not, and one corrupt line stops the interface from loading.",
        f"**The server is correct under concurrency and weak at its edges.** 32 simultaneous removals of one client gave exactly one HTTP 200; 16 simultaneous trainings gave 16 valid ledger records; a 2,000-request soak had 0 errors. Of {sp['n_probes']} security probes {sp['classification_counts']['defect']} found defects (no authentication, cross-site POST, missing read timeout, bursts of connections refused), each with a fix in Chapter 10.",
        f"**Removal is cheap where retraining is not.** Subtracting a neural adapter takes {nn['summary']['timing']['subtract_us_median']:.0f} microseconds against {nn['summary']['timing']['retrain_seven_adapters_s_median']:.1f} s to retrain seven adapters; on the bigram proxy unlearning is {_sc['rows'][-1]['speedup_retrain_over_unlearn']:.1f} times faster than retraining at 500 clients and slower below about 100, because of its fixed metric and ledger cost.",
        f"**The interface is stable.** {ac['journeys_passed_all_steps']} of {ac['journeys']} scripted synthetic-user journeys passed every step ({ac['total_certificates_checked']} certificates, no console errors) across desktop and phone layouts and both themes."])


def sec_conclusion_applications(d):
    d.h2("Practical Applications")
    d.p("ForgetSafe is not a compliance product and does not claim that any real model has been formally erased. Within that boundary it has three practical uses.")
    d.bullets(["**A teaching and demonstration tool** for federated learning, differential privacy, membership inference and tamper-evident logging, with every step visible in a browser and reproducible offline.",
               "**A reference workflow and certificate schema.** The order of operations (train, track, subtract, verify, certify, record) and the 25 fields of the certificate can be reused when the proxy model is replaced by a real adapter.",
               "**A harness for checking unlearning claims.** The fresh-noise comparison and the noise-free attack are small, general checks that expose a certificate which cannot fail; they can be pointed at other unlearning implementations."])


def sec_conclusion_limits(d):
    d.h2("Known Limitations")
    d.p("The weaknesses below were measured, not assumed; each has an engineering item in Chapter 10.")
    d.bullets(["The certificate's reference shares noise and updates with the unlearned model and cannot fail; ε is the training-time value, outside its proven range at σ = 3, with no accountant.",
               "At the default five-client configuration the model is noise-dominated and the membership attack is uninformative; the useful, private regime needs about 1,000 clients.",
               "The audit ledger has no signature or external anchor, verifies when emptied, re-reads the whole file on every append and on every state call, and stops the interface when one line is corrupt.",
               "The API has no authentication and one shared engine; the 58 security probes found eight defects (Content-Length handling, read timeouts, cross-site POST, Host check, connection bursts, two ledger-file cases, no authentication).",
               "**Boundaries of the evidence:** the neural study is a 137,151-parameter GRU with 8 synthetic clients and one aggregation round, not a billion-parameter LLM; every corpus is synthetic; interface acceptance is scripted, not human; timings come from one CPU workstation.",
               "Three of the five papers in the batch literature survey could not be retrieved; they are listed without claims about their contents."])


# ----------------------------------------------------------------------------------------------------------------- future scope


# ----------------------------------------------------------------------------------------------------------------- future scope
def sec_future_improvements(d):
    d.h2("Improvements to the Existing System")
    d.numbered(["**Fresh noise at every release and a privacy accountant.** Draw new noise per release, track Rényi or zero-concentrated DP across training and removals, and use the analytic Gaussian calibration [19] (ε = 1.271 instead of 1.615 at σ = 3). The same-noise identity then disappears, so the certificate must adopt the check below.",
                "**Make the certificate able to fail, with a sensible clip norm.** Compare the unlearned model with retraining on fresh noise and run the noise-free attack, with a stated statistical test, and choose C from the median raw update norm (the default C = 25 shrinks 200-sentence updates about 50 times).",
                "**Sign and anchor the ledger.** Sign each record, publish the head hash and the record count to an external witness, quarantine corrupt lines instead of failing, read only the tail on append and cache the chain verification (`/api/state` saturates near 80 requests per second).",
                "**Harden the HTTP layer.** Reject negative Content-Length, set socket read timeouts, return JSON 413 and 405, require a JSON content type, check Origin and Host and add a request token, add security headers, and run behind a production server with a larger accept queue.",
                "**Authentication and roles** with an approval step before a removal.",
                "**Strengthen the attack.** Many more member and non-member records, calibrated thresholds, shadow-model or likelihood-ratio attacks [15][16], and AUC with confidence intervals."])


def sec_future_features(d):
    d.h2("Additional Features")
    d.bullets(["A request queue and batch removal of several clients, with the ledger recording request, approval and completion times.",
               "Printable or signed certificates (PDF or JSON-LD) and a public verification page that re-checks a certificate against the ledger.",
               "Sample-level and label-level unlearning in addition to client-level removal, as treated in [4].",
               "Multiple training rounds with per-round update storage, so that removal can be studied for iterative FedAvg [9].",
               "A built-in run of the fresh-noise comparison and the noise-free attack, so that the interface shows the independent evidence next to each certificate."])


def sec_future_deploy(d):
    d.h2("Scalability and Deployment")
    d.bullets(["Run the API under an ASGI or WSGI server behind a reverse proxy with TLS, in a container image with `.env`-based configuration.",
               "Replace the in-memory engine by per-tenant sessions backed by a database, and the JSONL file by an append-only store with signed batches.",
               "Encrypt the stored clipped updates at rest, restrict their access and define a retention policy; they are the artefact that makes removal possible and are sensitive.",
               "Add secure aggregation so that the coordinator never sees an individual update in the clear, and study how per-client subtraction can be supported with it; federations of thousands of clients, the regime in which ε < 1 and a useful model coexist, need it.",
               "Index ledger reads and add monitoring of request latency and ledger length, so that the service scales beyond the measured 80 state reads per second."])


def sec_future_research(d):
    d.h2("Further Research")
    d.numbered(["**Real federated LLM adapters.** Repeat the neural study with LoRA adapters [22] on a pretrained small Hugging Face language model, with Flower for federation and Opacus for accounted DP-SGD; the GRU study of this project provides the protocol (sweep, fresh-noise comparison, attacks, cost).",
                "**Benchmarks with forget-quality metrics.** Evaluate on TOFU- and MUSE-style benchmarks and compare with the algorithms studied in [3] (gradient ascent, gradient difference, NPO, SimNPO and retraining).",
                "**Baselines from the literature.** Implement sharded retraining [12], FedEraser-style calibration [17], certified removal [13][14] and pruning-based unlearning [2] behind the same certificate interface and compare cost, utility and verification evidence.",
                "**Extraction and memorisation tests.** Test whether a removed client's text can still be extracted from the model [21], and measure memorisation at the example level as in [2].",
                "**Real, partitioned corpora and large federations.** Replace the synthetic corpora by public text partitioned across clients with realistic non-identical distributions, at the federation sizes (about 1,000 clients) at which the privacy-utility trade-off opens up.",
                "**A study with human users**, for example compliance officers and operators, to complement the scripted acceptance journeys.",
                "**A formal statement of what a certificate means** under the GDPR [20]: which guarantee (distributional closeness to retraining, bounded influence, or empirical non-membership) a regulator should accept, and how it composes over repeated requests."])


# ----------------------------------------------------------------------------------------------------------------- references
def sec_references(d, heading=True):
    if heading:
        d.h2("References")
    for i, ref in enumerate(REFERENCES, 1):
        p = d.p(f"[{i}]\t{ref}", align="left", size=11, line=1.2, space_after=4)
        p.paragraph_format.left_indent = Inches(0.45)
        p.paragraph_format.first_line_indent = Inches(-0.45)
    nums = ", ".join(f"[{n}]" for n in UNVERIFIED)
    d.p(f"Note: references [1] to [4] and [9] to [22] were checked against their sources or are standard published works; {nums} are titles taken from the batch literature survey that could not be located "
        "by independent search, so they are listed as given and no claim in this report depends on their content. Reference [1] is the base paper recorded in the batch files; only its review method is adopted. "
        "Reference [2] is the 2026 paper named in the project's base-paper archive.", size=10, line=1.15, italic=True)


# ----------------------------------------------------------------------------------------------------------------- appendices
def _func(rel: str, name: str) -> str:
    """Verbatim source of a function or method `name` from certified_unlearning/<rel>."""
    lines = (ROOT / "certified_unlearning" / rel).read_text(encoding="utf-8").splitlines()
    pat = re.compile(rf"^(\s*)def {re.escape(name)}\(")
    for i, line in enumerate(lines):
        m = pat.match(line)
        if m:
            indent = len(m.group(1))
            j = i + 1
            while j < len(lines):
                if lines[j].strip() and (len(lines[j]) - len(lines[j].lstrip())) <= indent and not lines[j].lstrip().startswith(")"):
                    break
                j += 1
            block = lines[i:j]
            while block and not block[-1].strip():
                block.pop()
            return "\n".join(block)
    raise KeyError(f"{name} not found in {rel}")


def appendix_a(d):
    d.p("The listings are extracted from the source files when this document is built, so they are exactly the code that produced the results. They show the five functions on which the certificate depends.")
    d.h2("Federated Training and Unlearning (engine.py)")
    d.code(_func("engine.py", "train"), "FederatedUnlearningEngine.train() in certified_unlearning/engine.py")
    d.code(_func("engine.py", "unlearn"), "FederatedUnlearningEngine.unlearn() in certified_unlearning/engine.py")
    d.h2("Hash-Chained Audit Ledger (audit.py)")
    d.code(_func("audit.py", "append") + "\n\n" + _func("audit.py", "verify"), "AuditLedger.append() and AuditLedger.verify() in certified_unlearning/audit.py")
    d.h2("Clipping and Membership Attack (model.py)")
    d.code(_func("model.py", "clipped_update") + "\n\n" + _func("model.py", "membership_auc"), "clipped_update() and membership_auc() in certified_unlearning/model.py")


def appendix_b(d):
    d.h2("Installation Guide")
    d.p("ForgetSafe needs Python 3.10 or newer (the project was run on 3.11.9) and, for the React interface, Node.js 18 or newer with npm (run with Node 24.19 and npm 11.17). The Python engine and API use only the standard library, "
        "so there is nothing to install for them.")
    d.numbered(["Open the `8.ProjectCode` folder. If `.env` is missing, copy `.env.example` to `.env`; it holds `BACKEND_PORT=8109` and `FRONTEND_PORT=5109`.",
                "On Windows run `run.bat`. It starts the API with `python app.py --port 8109`, installs `frontend/node_modules` on first use, starts the interface with `npm run dev` and opens http://127.0.0.1:5109.",
                "To start the parts by hand: `python app.py --port 8109` in one terminal; `cd frontend`, `npm install`, `npm run dev` in another. The development server proxies `/api` to port 8109 and refuses to start if port 5109 is taken.",
                "For a production build run `npm run build` in `frontend` (output in `frontend/dist`) and `npm run preview`.",
                "The original interfaces are unchanged: `python app.py` serves the single-page interface on port 8000 (and at `/` on any chosen port), `python app.py --desktop` opens the Tkinter window and `python app.py --demo` prints one scripted run.",
                "Run the checks with `python -m unittest discover -s tests -v` (5 tests) and `python scripts/smoke_test.py` (14 checks on a temporary server).",
                "To reproduce the report's numbers run `python scripts/run_experiments.py` (all experiments, a few minutes; or name experiments, e.g. `baseline seeds`), then `python scripts/run_synthetic_corpus.py`, `python scripts/run_neural_experiment.py` (PyTorch; about 4 minutes after a one-time pre-training of about 6 minutes) and `python scripts/run_testing_experiments.py` (starts its own servers and a browser), and finally `python scripts/make_charts.py`."])
    d.p("The audit ledger is written to `data/audit_log.jsonl` relative to the directory from which the server is started; it is excluded from version control. Starting the server from another directory therefore starts a separate ledger.")
    d.h2("User Guide")
    d.p("The web interface has five areas, reached from the sidebar (or from the bottom bar on a phone). The steps below follow the order of the workflow.")
    d.numbered(["**Dashboard.** Shows where the session stands (Train, Unlearn, Verify), the summary tiles, the clipped norm of each client and the latest certificate.",
                "**Federated training.** Press *Train federated model*. The tiles show active clients, ε, perplexity and next-character accuracy, and the table lists each client's original and clipped norm. *New session* starts a fresh engine; the audit history is kept.",
                "**Model explorer.** Type a seed such as \"privacy\" and press *Generate sample*. Each sample is tagged with the model state that produced it.",
                "**Certified unlearning.** Choose a client, press *Execute & certify* and confirm. The certificate appears with its identifier, status, residual and reference distances, membership AUC, perplexity, accuracy, hashes and a *Download JSON* button.",
                "**Compliance audit.** Press *Verify hash chain*. The status card shows Valid or Invalid with the first failing record; the table lists every event and *View* opens its full record."])
    d.figure_pair([(SHOTS / "04_training_trained.png", "Training screen after the first run"), (SHOTS / "09_unlearning_certificate.png", "Certificate after a removal")], width=3.05, max_h=2.1)
    d.p("At most one client can be removed per request; at least one client must remain, and a client that was already removed cannot be removed again. The drop-down lists only active clients, the interface shows \"Only one client remains\" when no further removal is possible, and other refusals are reported as messages.")
    d.h2("Troubleshooting")
    d.bullets(["*Could not load the lab* in the browser: the API is not running or the port in `.env` differs from the one used to start it.",
               "*Port already in use*: change `BACKEND_PORT` or `FRONTEND_PORT` in `.env`; the Vite server uses a strict port and will not pick another.",
               "*Audit chain Invalid*: the ledger file was edited or truncated by hand; the message names the first record that fails. Delete the file only if a fresh ledger is acceptable.",
               "No certificates after restarting the server: certificates are held in memory; the ledger keeps the record of each removal, but a restarted server must train again before it can remove another client."])


def appendix_c(d):
    from rc_results import SCREENS
    d.p("The screens below complement Chapter 8. They come from the same capture session (1440 x 900, default configuration, Client 01 and Client 02 removed).")

    def pair(a, b):
        d.figure_pair([(SHOTS / SCREENS[a][0], SCREENS[a][1]), (SHOTS / SCREENS[b][0], SCREENS[b][1])], width=3.05, max_h=2.15)
        d.p(SCREENS[a][2])
        d.p(SCREENS[b][2])

    pair("03", "08")
    d.figure(SHOTS / SCREENS["09b"][0], SCREENS["09b"][1], width=4.2, max_h=4.0)
    d.p(SCREENS["09b"][2])
    pair("11", "12")
    pair("14", "15")
    pair("17", "16")
    d.figure(SHOTS / SCREENS["02"][0], SCREENS["02"][1], width=4.6, max_h=2.9)
    d.p(SCREENS["02"][2])
