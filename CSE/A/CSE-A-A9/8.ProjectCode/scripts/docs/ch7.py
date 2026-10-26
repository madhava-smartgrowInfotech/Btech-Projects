"""Chapter 7: System Testing. Counts come from facts.py and docs/REPORT_FACTS.md; the checks listed are the ones in scripts/smoke_test.py."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, TAB

# the 36 checks of scripts/smoke_test.py, grouped by feature (name as printed by the script)
CHECKS = [
    ("Health and sign-in", [
        "health reports the graph size", "protected routes reject anonymous requests", "wrong password is rejected",
        "demo moderator and analyst can sign in"]),
    ("F1 / F2 graph and features", [
        "node and edge counts add up", "feature summary lists every feature", "labels are imbalanced"]),
    ("F3 / F7 model comparison and scalability", [
        "GCN beats the no-graph baseline", "GAT beats the no-graph baseline", "GraphSAGE beats the no-graph baseline",
        "best architecture is flagged", "scalability sweep covers a growing graph", "training time grows with the graph"]),
    ("F4 account scoring", [
        "accounts are ranked by fake-probability", "account detail lists its top contributing features",
        "account detail summarises the neighbourhood", "neighbourhood graph has nodes and links",
        "search finds an account by handle", "unknown account id returns 404"]),
    ("F5 botnet clusters", [
        "coordinated botnets were found", "injected botnets are recovered as single communities",
        "cluster detail has members and an interactive graph"]),
    ("F6 moderator queue", [
        "analyst cannot record decisions", "decisions are counted", "a cluster decision clears its member accounts from the queue",
        "decisions are logged with who made them", "account status reflects the decision",
        "a decision can be undone before it is used in training"]),
    ("Retraining on decisions", [
        "analyst cannot retrain", "retraining finished", "run recorded with the number of labels used",
        "before and after F1 recorded for every model", "retrained model is now served",
        "decisions are marked as used in that run", "a used decision cannot be undone",
        "API still serves the full graph after retraining"]),
]


SHORT_CHECKS = {
    "Health and sign-in": "graph size reported; anonymous and wrong-password requests rejected; both demo users sign in",
    "F1 / F2 graph and features": "node and edge counts add up; all features listed; labels imbalanced",
    "F3 / F7 model comparison and scalability": "each graph model beats the baseline; best model flagged; scalability covers a growing graph and training time grows with it",
    "F4 account scoring": "ranking, top contributing features, neighbourhood summary and graph, search, 404 for an unknown account",
    "F5 botnet clusters": "coordinated botnets found; injected botnets recovered; cluster detail has members and graph",
    "F6 moderator queue": "analyst refused; decisions counted, logged with their author and reflected in the status; cluster decision clears its members; undo",
    "Retraining on decisions": "analyst refused; run finishes and is recorded with labels used and F1 before and after; retrained model served; decisions marked used and not undoable; full graph still served",
}


def _check_rows():
    rows, n = [], 0
    for grp, items in CHECKS:
        n += len(items)
        rows.append([grp, str(len(items)), SHORT_CHECKS[grp] if F.REPORT else "; ".join(items)])
    assert n == F.SMOKE_TOTAL, n
    return rows


def _lat_rows():
    return [[k, f"{m:.1f}", f"{p:.1f}"] for k, (m, p) in F.LATENCY.items()] + [["POST /api/auth/login (5 requests, bcrypt)", f"{F.LOGIN_MS}", "-"]]


def _scal_rows():
    rows = []
    for r in F.SC["rows"]:
        m = r["models"]
        rows.append([f"{r['nodes']:,}", f"{r['edges']:,}"] + [f"{m[k]['train_seconds_per_epoch']:.3f} / {m[k]['inference_seconds']:.3f}" for k in ("baseline", "gcn", "gat", "sage")])
    return rows


def _trim(blocks):
    """Full report only: drop or shorten text that restates a table (the chapter is the same in the stand-alone documents)."""
    out = []
    for b in blocks:
        k = b[0]
        if k == "b" and b[1] and b[1][0].startswith("**Graph builder.**"):
            continue
        if k == "p":
            t = b[1]
            if t.startswith("There is no pytest or unit-test suite"):
                b = ("p", "There is no pytest or unit-test suite in the repository. Unit behaviour is checked only indirectly: a failure in the graph builder, the layers of `ml/gnn.py`, the clustering code or the store would surface as a wrong count, ordering or comparison in the smoke test, but would not be pinpointed to its function.")
            elif t.startswith("Two parts of the flow deserve a remark"):
                b = ("p", "The retraining step is not a stub: the test starts a real run, polls it until it reports `done`, and checks the run record, the stored F1 for all four models, the served model and the used decisions; a final check confirms that the API still serves all 4,533 accounts after the swap.")
            elif t.startswith("One practical observation from running the suite"):
                continue
            elif t.startswith("Medians lie between 3 and 16 ms"):
                b = ("p", "Medians lie between 3 and 16 ms and no 95th percentile exceeds 29 ms, because the store loads the graph, scores and clusters once at start-up and each request slices arrays held in memory. Sign-in takes about 233 ms because of bcrypt. "
                          "The measurements were taken while another program was using the processor, so they are upper bounds, and with 20 repetitions the 95th percentile is the second-largest value.")
            elif t.startswith("These figures are limited in three ways"):
                b = ("p", "These figures have three limits: the largest graph (36 thousand accounts) is far below platform scale, disjoint copies understate the cost of a real, well-mixed graph, and the whole graph is processed in one pass, so neighbourhood sampling would be needed at scale and was not implemented.")
            elif t.startswith("`scripts/ui_checks.py` drives the web application"):
                b = ("p", "`scripts/ui_checks.py` drives the web application at 360, 768 and 1440 px in both themes and tests dark mode, keyboard focus, Escape on dialogs and reduced motion; `scripts/capture_screens.py` walks every screen and reports console errors. "
                          "`docs/FRONTEND_PLAN.md` records both as passing when the interface was built; they were not re-run on 2026-10-26.")
            elif t.startswith("On the measurement machine's system Python"):
                b = ("p", "On the measurement machine's system Python, `import torch` failed with `WinError 1114` whenever `fastapi` or numpy had been imported first. Preloading `torch` avoids it; the 2026-10-26 runs did this through a throw-away `sitecustomize.py` outside the project, and the product code was not changed. "
                          "The project's own `.venv` (made by `setup.bat`) does not show the problem but is not part of the delivered tree, so the system interpreter (PyTorch 2.14.1, CPU build) was used.")
            elif t.startswith("The product has three layers, and each was tested"):
                b = ("p", "The product has three layers, tested where a failure would show: the model pipeline by the measured evaluation of Chapter 8, the API and its database by an end-to-end smoke test over HTTP, and the web application by scripted browser captures and a manual tour.")
        out.append(b)
    return out


def blocks():
    sm = F.scal_row(1)["models"]["sage"]
    big = F.scal_row(8)["models"]["sage"]
    gat1, gat8 = F.scal_row(1)["models"]["gat"], F.scal_row(8)["models"]["gat"]
    out = [
        H1("CHAPTER 7: SYSTEM TESTING"),
        P("This chapter describes how BotGraph was tested, what each kind of test covered, what passed and what was left untested. The testing is deliberately described at the size it really had: "
          f"one automated end-to-end suite of {F.SMOKE_TOTAL} checks, a set of measured response times, a scalability sweep, and a manual walk-through of the web application. "
          "There is no unit-test suite in the repository, and the chapter says so rather than presenting the smoke test as more than it is."),

        H2("7.1 Testing strategy"),
        P("The product has three layers, and each was tested at the level where a failure would show: the model pipeline (`ml/`) by the measured evaluation of Chapter 8, "
          "the API and its database (`backend/app/`) by an end-to-end smoke test that drives the real HTTP interface, and the web application (`frontend/`) by scripted browser captures and a manual tour."),
        TAB("Test levels used and what they cover", ["Level", "Method", "Where it lives", "Status"],
            [["Model evaluation", "Held-out test split, three seeds, six metrics; ablation and threshold sweep", "`ml/train.py`, `ml/eval.py`, `scripts/run_extra_experiments.py`", "Done (Chapter 8)"],
             ["Unit", "No separate unit tests; units are exercised through the API by the smoke test", "-", "Not present"],
             ["Integration", f"{F.SMOKE_TOTAL}-check end-to-end run against a live API with a scratch database", "`scripts/smoke_test.py`", f"{F.SMOKE_PASSED}/{F.SMOKE_TOTAL} pass"],
             ["Functional", "Each feature F1-F7 checked through its API responses and, manually, its screen", "smoke test; `docs/03_HOW_TO_RUN.md` tour", "Done"],
             ["Security", "Anonymous, wrong-password and wrong-role requests", "smoke test", "Basic checks pass; see 7.6"],
             ["Performance", "Latency of ten GET endpoints; training and inference time up to 36 k accounts", "measured 2026-10-26; `experiments/scalability.json`", "Done, single machine"],
             ["User interface", "Responsive widths, dark mode, keyboard, reduced motion, console errors", "`scripts/ui_checks.py`, `scripts/capture_screens.py`", "Run when the UI was built; not re-run on 2026-10-26"],
             ["Acceptance", "Five-minute guided tour by a person", "`docs/03_HOW_TO_RUN.md`, section 3a", "Walk-through only; no formal user study"]],
            widths=[1.0, 2.4, 1.9, 1.2], align=["l", "l", "l", "l"], size=9.5),
        P("The smoke test never touches the shipped data. It copies the trained models and experiment files to a temporary directory, creates a scratch SQLite database, starts its own API on port 13091 "
          "through the environment variables `DATABASE_URL`, `BOTGRAPH_MODELS_DIR` and `BOTGRAPH_EXPERIMENTS_DIR`, and deletes everything afterwards. Retraining inside the test therefore rewrites only the copies."),

        H2("7.2 Unit-level testing"),
        P("There is no pytest or unit-test suite in the repository. Unit behaviour is checked indirectly: a failure in the graph builder, the layers in `ml/gnn.py`, the clustering code or the store would surface as a wrong count, a wrong ordering or a "
          "failed comparison in the smoke test, but a unit-level failure would not be pinpointed to its function. The following behaviours are the ones the smoke test pins down at unit granularity:"),
        B("**Graph builder.** Node and edge counts add up (real plus injected equals total), the feature table lists every feature, and the fake share is between 5 % and 25 %.",
          "**Models.** Each of GCN, GAT and GraphSAGE reaches a higher mean F1 than the feature-only baseline in the stored results, and exactly one model is flagged best.",
          "**Scoring.** Accounts are returned in descending order of fake-probability, and the top account scores above 0.9.",
          "**Explanations.** An account's detail lists at least five contributing features.",
          "**Clustering.** At least six coordinated clusters exist and at least six injected botnets are recovered as single communities."),
        P("A proper unit suite would add tests for the sparse message-passing layers against a dense reference, for `class_weights`, `best_threshold` and `metrics` on hand-computed inputs, and for `clustering.recovery`. These are listed as future work in Chapter 10."),

        H2("7.3 Integration testing: the smoke test"),
        P(f"`scripts/smoke_test.py` runs {F.SMOKE_TOTAL} checks in one pass against a freshly started API: it signs in as both demo users, reads the graph, compares the models, scores accounts, opens clusters, records decisions as the moderator, "
          "retrains on those decisions and reads the results back. It stops at the first failed check. The run on 2026-10-26 passed all checks."),
        TAB(f"The {F.SMOKE_TOTAL} smoke-test checks by feature", ["Feature", "Checks", "What is checked"], _check_rows(), widths=[1.6, 0.6, 4.3], align=["l", "c", "l"], size=9.5),
        P("Two parts of the flow deserve a remark. First, the retraining step is not a stub: the test starts a real run, polls its status until it reports `done`, and then checks that the run was recorded with the number of labels it used, "
          "that F1 before and after was stored for all four models, that the retrained model is now the one served, and that the decisions are marked as used. "
          "Second, the final check confirms that the API still serves all 4,533 accounts after the swap, which would catch a retrain that replaced the artefacts with a truncated set."),
        P(f"One practical observation from running the suite: with a shared CPU the retraining step dominates the run time (four models with one seed each, GAT being the slowest). The suite as a whole took several minutes on the machine used, "
          "so it is a pre-release check rather than something to run on every edit."),

        H2("7.4 Functional testing"),
        P("Each of the seven features is reached through an API response that the smoke test inspects and through a screen that was captured with real data (Chapter 8). The table lists what was verified for each."),
        TAB("Functional coverage of features F1-F7", ["Feature", "Verified through the API", "Verified on screen"],
            [["F1 Graph builder", "Counts and schema in `/api/graph/summary`", "Graph & features"],
             ["F2 Node features", "23 features listed with genuine and fake means", "Graph & features"],
             ["F3 Three architectures", "Metrics for four models, best flagged, lift over baseline", "Models & scale, Comparison tab"],
             ["F4 Account scoring", "Ranking, detail, per-model scores, reasons, neighbourhood, search, 404", "Accounts, Account detail"],
             ["F5 Botnet clusters", "Cluster list and detail with members and graph", "Botnet clusters, Cluster detail"],
             ["F6 Moderator queue", "Roles, decisions, undo, log, retraining bookkeeping", "Moderator queue, Decision log"],
             ["F7 Evaluation", "Metrics and scalability rows via `/api/models` and `/api/models/scalability`", "Models & scale, Scalability tab"]],
            widths=[1.5, 3.1, 1.9], align=["l", "l", "l"], size=9.5),
        P("The moderator rules were tested as behaviour, not just as responses: a decision on a cluster applies to every member (the pending-account count falls by more than the three decisions recorded), the account status in the detail view changes to *confirmed*, "
          "the decision log names the moderator who made it, and an undo removes the decision. These are the rules that make the queue usable by more than one person."),

        H2("7.5 Validation and edge cases"),
        TAB("Edge cases and how the system behaved", ["Case", "Expected", "Observed"],
            [["Account id that does not exist (`/api/accounts/99999999`)", "404 with a plain message", "404 (smoke test)"],
             ["Negative account id (`/api/accounts/-1`)", "404", "404 (probe, 2026-10-26)"],
             ["Cluster id that does not exist when deciding", "404 mentioning that clusters can change after retraining", "404 \"No cluster BN-99999. It may have changed after the model was retrained.\" (probe)"],
             ["Non-numeric account id in a decision", "422", "422 \"Account ids are numbers.\" (probe)"],
             ["Decision value other than confirm or dismiss", "422 from schema validation", "422 \"Input should be 'confirm' or 'dismiss'\" (probe)"],
             ["Page size 500 (maximum is 100)", "422 from query validation", "422 (probe)"],
             ["Retraining with no decisions recorded", "409 with advice", "409 \"There are no moderator decisions yet...\" (probe)"],
             ["Malformed bearer token", "401", "401, but the message reads \"Your session has expired\" for any invalid token (probe)"],
             ["Undo of a decision already used in a training run", "409", "409 (smoke test and probe)"],
             ["Undo of a decision before any training run", "Decision removed", "Removed (smoke test)"],
             ["Analyst records a decision or starts retraining", "403", "403 (smoke test and probe)"],
             ["Request without a token", "401", "401 (smoke test)"],
             ["Test split during retraining", "Never receives a moderator label", "By code reading (`fit_all` skips split 2 in the feedback); of 129 labels in one run only 99 were used, the rest fell in the test split"]],
            widths=[2.4, 1.9, 2.2], align=["l", "l", "l"], size=9.5),
        P("The rows marked *probe* were run on 2026-10-26 by a throw-away script against a scratch copy of the application; they were not added to the smoke test, which is a gap. "
          "Two small defects came out of them: every invalid token is reported as an expired session, and the retraining step can change the served architecture (see 7.11)."),

        H2("7.6 Security testing"),
        P("Security was tested at the level a demonstration application needs, and no further. The table separates what was checked from what was only reviewed."),
        TAB("Security measures and their evidence", ["Measure", "How it works", "Evidence"],
            [["Authentication", "Email and password; passwords stored as bcrypt hashes, truncated to 72 bytes as bcrypt requires", "Wrong password returns 401; demo users sign in (smoke test)"],
             ["Session token", "JWT signed with HS256, 12-hour expiry, carries user id and role; the user is re-read from the database on every request", "Anonymous requests return 401 (smoke test); expiry not exercised"],
             ["Role enforcement", "`require_moderator` guards decisions, undo and retraining", "Analyst receives 403 on a decision and on retraining (smoke test)"],
             ["Cross-origin access", "CORS allows only the web app's origins (`localhost` and `127.0.0.1` on port 5309)", "By code reading (`main.py`); not tested from a foreign origin"],
             ["Injection", "SQLAlchemy parameterised queries; account search uses plain substring matching with `regex=False`", "By code reading"],
             ["Secrets", "`.env` is git-ignored; the JWT secret comes from `.env`", "See the weakness below"]],
            widths=[1.3, 3.0, 2.2], align=["l", "l", "l"], size=9.5),
        P("**A weakness found while preparing this chapter.** `.env.example` ships the placeholder `generate-a-random-64-char-string` as the JWT secret, and `settings.py` replaces any empty value or any value starting with `generate-a-random` by a fixed development secret written in the source. "
          "A copy of the project that is started without editing `.env` therefore signs its tokens with a secret that is public. This is acceptable for the local demonstration the project targets, and the README tells the reader to replace the placeholder for anything beyond a demo, "
          "but it would be a serious fault in a deployed service. There is also no rate limiting or lockout on the sign-in route (a request takes about 233 ms because of bcrypt, which slows guessing but does not prevent it), no password change or reset, no multi-factor sign-in and only two seeded accounts. "
          "No penetration test, dependency audit or fuzzing was carried out."),

        H2("7.7 Performance testing"),
        H3("7.7.1 API response time"),
        P(f"The ten read endpoints were each called 20 times against a warm server on `127.0.0.1`, with a scratch database, after login. The API took {F.STARTUP_S} s to load the graph, scores and clusters and answer its first health request. "
          "The address `127.0.0.1` is used instead of `localhost` because, on the test machine, name resolution of `localhost` added about two seconds per call, which would have swamped the figures."),
        TAB("API response times (20 requests per endpoint, milliseconds)", ["Endpoint", "Median", "95th percentile"], _lat_rows(), widths=[3.6, 1.2, 1.5], align=["l", "r", "r"], size=10),
        P("Medians lie between 3 and 16 ms and no 95th percentile exceeds 29 ms. The responses are fast because the store loads the graph, the scores and the clusters once at start-up and each request only slices arrays held in memory. "
          "The one slow call is sign-in at about 233 ms, which is bcrypt's deliberate cost. The measurements were taken while another program was using the processor, so they are upper bounds, and with 20 repetitions the 95th percentile is the second-largest value rather than a stable estimate."),
        FIG(F.fig("f10_api_latency.png"), "Median and 95th-percentile response time of ten API endpoints (20 requests each, 127.0.0.1).", 5.4),
        H3("7.7.2 Scalability of training and inference"),
        P("The account graph was copied one, two, four and eight times as disjoint components, so that nodes and ties grow in step while the structure of each component stays the same. "
          "For each size, every model was trained for 10 epochs (the table gives seconds per epoch) and a forward pass over the whole graph was timed (the median of three)."),
        TAB("Training seconds per epoch / inference seconds, by graph size (CPU)", ["Accounts", "Ties", "Baseline MLP", "GCN", "GAT", "GraphSAGE"], _scal_rows(),
            widths=[0.9, 0.9, 1.2, 1.2, 1.2, 1.2], align=["r", "r", "c", "c", "c", "c"], size=9.5),
        P(f"From 4,533 to 36,264 accounts (8 times) and from 94,456 to 755,648 ties, a GraphSAGE epoch grew from {sm['train_seconds_per_epoch']:.3f} s to {big['train_seconds_per_epoch']:.3f} s "
          f"({big['train_seconds_per_epoch'] / sm['train_seconds_per_epoch']:.1f} times) and a forward pass from {sm['inference_seconds']:.3f} s to {big['inference_seconds']:.3f} s; "
          f"GAT grew from {gat1['train_seconds_per_epoch']:.3f} s to {gat8['train_seconds_per_epoch']:.3f} s per epoch. Growth is close to proportional to the number of ties, as expected from sparse message passing, and GAT is the most expensive because it computes attention on every tie. "
          "The first baseline timing is higher than its second (0.073 s against 0.022 s) because of start-up warm-up, so single entries should not be over-read."),
        P("These figures are limited in three ways. The largest graph has 36 thousand accounts, three orders of magnitude below a platform with tens of millions of users. Disjoint copies understate the cost of a real, well-mixed graph, whose neighbourhoods overlap and whose degree distribution has a heavier tail. "
          "And the whole graph is processed in one pass, which would not fit in memory at platform scale; neighbourhood sampling or mini-batching would be needed and was not implemented."),

        H2("7.8 User interface checks"),
        P("`scripts/ui_checks.py` drives the web application in a headless browser at 360, 768 and 1440 px in light and dark themes, toggles dark mode, tests keyboard focus and the Escape key on dialogs, and runs with reduced motion; "
          "`scripts/capture_screens.py` walks every screen, saves the screenshots and reports any console error. `docs/FRONTEND_PLAN.md` records both as passing when the interface was built. "
          "They were not re-run on 2026-10-26: the screenshots used in this report are the captures from that earlier run, taken from the application with the shipped model and data."),

        H2("7.9 User acceptance"),
        P("No formal acceptance test or user study was carried out. The nearest thing is the five-minute guided tour in `docs/03_HOW_TO_RUN.md`, which the project team used as an acceptance walk-through:"),
        N("**Graph & features** - read the node and edge counts, which parts are real data, and the 23 features.",
          "**Models & scale** - compare the three architectures against the no-graph baseline and open the Scalability tab.",
          "**Accounts** - open the top-ranked account and read its probability, the traits behind it and its neighbourhood graph.",
          "**Botnet clusters** - open a coordinated cluster and see that the injected botnets come back as single communities.",
          "**Moderator queue** - dismiss one member, confirm another, see both in the decision log, and press *Retrain with decisions*."),
        P("Each step can be completed on the shipped data, which is what acceptance of the seven features means here. Whether a trust-and-safety moderator would find the explanations and the queue useful was not measured."),

        H2("7.10 Environment note"),
        P("On the measurement machine's system Python, `import torch` failed with `WinError 1114` (a DLL initialisation error) whenever `fastapi` or numpy had been imported first, so the API and the smoke test did not start. "
          "Preloading `torch` before anything else avoids it; the runs on 2026-10-26 did this through a throw-away `sitecustomize.py` kept outside the project, and the product code was not changed. "
          "The project's own `.venv`, created by `setup.bat` with the pinned `torch>=2.2,<2.6`, does not show the problem, but that folder is not part of the delivered tree, so the system interpreter (PyTorch 2.14.1, CPU build) was used for all 2026-10-26 runs. "
          "A reader who runs `scripts/smoke_test.py` with a plain system Python on a similar machine may meet the same error."),

        H2("7.11 Limits of the testing done"),
        B("**No unit tests** and no coverage measurement; the smoke test is the only automated suite.",
          "**Retraining side effects found, not fixed.** In one run on correct decisions the served architecture changed from GraphSAGE to GAT, because the best architecture is chosen on the validation F1 of a single seed after the reviewed accounts have left the validation set; "
          "GraphSAGE had the higher test F1 (0.947 against 0.892) in that run. After such a switch `/api/health` reports the full-run F1 of the new architecture (0.900) rather than its retrained value. "
          "In another run two deliberately wrong moderator decisions lowered F1 for every model (Chapter 8). None of this is covered by the smoke test, which only checks that the run completes and is recorded.",
          "**One run of the suite** on one machine; no repeated runs to look for flaky checks. GAT results can drift by about 0.01 between runs because its edge softmax sums in a non-deterministic order, so the check that GAT beats the baseline has a margin (0.900 against 0.827) but no guarantee.",
          "**No load or concurrency test:** latency was measured with a single client; the behaviour with many moderators deciding at once, and SQLite's locking under that load, was not tested.",
          "**No adversarial testing:** nothing tests whether an attacker who knows the model can shape a bot's profile and ties to evade it; the camouflage built into the data is a first, mild stand-in.",
          "**No test on data the model has not seen the kind of:** all evaluation is on one synthetic-plus-real benchmark with one split; there is no second dataset and no cross-validation.",
          "**Security only at the demonstration level** (7.6).",
          "**Interface checks not repeated** after the last change, and no assistive-technology test beyond keyboard focus.",
          "**Timings** come from a shared i5-12500 without a GPU; they show the shape of the cost, not production numbers."),
    ]
    return _trim(out) if F.REPORT else out
