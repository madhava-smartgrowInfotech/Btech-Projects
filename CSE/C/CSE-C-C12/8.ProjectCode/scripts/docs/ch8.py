"""Chapter 8: Results and output screens. Every number is read from facts.py (docs/metrics/*.json)."""

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, PAIR, TAB
from .refs import CITE as R

SH = F.shot
SETN = {
    "S1_shipped_protocol_30": "S1, shipped protocol (held-out record still indexed)",
    "S1_leave_one_out_30": "S1, leave-one-out",
    "S2_verbatim_leave_one_out_176": "S2, every record verbatim, leave-one-out",
    "S3_two_symptoms_leave_one_out_176": "S3, two random symptoms, leave-one-out",
    "S4_lay_language_60": "S4, lay-language probes",
}
S1P, S1L, S2, S3, S4 = F.SETS


def S(name, caption, base=5.6, max_h=3.9):
    """Screenshot figure with a width that keeps the picture on one page."""
    return FIG(SH(name), caption, F.shot_w(SH(name), base, max_h))


def _cap(name, text):
    return (SH(name), text)


def _ms(v):
    return f"{v / 1000:.2f} s" if v >= 1000 else f"{v:.0f} ms"


def _r(cfg, s, key="top1"):
    return F.RET[cfg][s][key]


def _setup():
    e = F.ENV
    k = F.KB
    n = F.M["probe_sizes"]
    return [
        H2("8.1 Experimental set-up"),
        P(f"All measurements were made on one machine: {e['cpu']}, {e['ram_gb']} GB of memory, Windows, Python {e['python']}, PyTorch {e['torch']}, transformers {e['transformers']}, "
          f"sentence-transformers {e['sentence_transformers']}, FAISS {e['faiss']}, scikit-learn {e['scikit_learn']}, FastAPI {e['fastapi']}. No GPU was used. The three models are "
          f"`{e['embedding_model']}`, `{e['reranker_model']}` and `{e['generator_model']}`; retrieval takes a candidate pool of {e['candidate_k']} records, fuses semantic and lexical scores with weights "
          f"{e['weights'][0]} and {e['weights'][1]}, and keeps the top {e['top_k']} after reranking."),
        P(f"**Data.** The knowledge base holds {k['records']} records for {k['conditions']} conditions ({k['mean_symptoms_per_record']} symptoms per record, a vocabulary of {k['symptom_vocabulary']} symptom phrases). "
          f"It is synthetic: `scripts/prepare_data.py` writes {k['conditions']} hand-typed condition entries with up to six random symptom subsets each, and all records of a condition share one description and one guidance text "
          f"(only {k['distinct_description_guidance_pairs']} distinct description-guidance pairs exist). No public dataset and no clinical review were involved, so every accuracy below measures how well the pipeline "
          f"finds the right entry in this small table, not how well it recognises disease."),
        FIG(F.fig("f07_kb_composition.png"), "Composition of the knowledge base: records per condition and severity labels (synthetic data).", 5.6),
        P("**Query sets.** Five query sets were used, because the choice of set changes the picture a great deal."),
        TAB("Query sets used in the evaluation", ["Set", "Queries", "How they were made", "Held-out handling"],
            [["S1 shipped protocol", "30", "`I have ` + the symptom list of one random record per condition (the protocol of `scripts/evaluate.py`, seed 7)", "Held-out record remains in the index"],
             ["S1 leave-one-out", "30", "The same 30 queries", "Held-out record removed from both retrievers"],
             ["S2", "176", "Every record's own symptom list", "Leave-one-out"],
             ["S3", "176", "Two random symptoms of each record (`I have a and b`)", "Leave-one-out"],
             ["S4", f"{n['lay']}", "Two everyday-language descriptions per condition written by the authors (not copied from the knowledge base)", "Not needed"]],
            widths=[1.2, 0.7, 3.1, 1.5], align=["l", "c", "l", "l"], size=9.5),
        P(f"The S4 queries, {n['out_of_kb']} out-of-knowledge-base complaints, {n['safety_pos']} emergency descriptions and {n['safety_neg']} non-emergency texts were written by the project team, not by clinicians; "
          f"they are small probe sets that exercise the pipeline and should be read as such. Accuracy is the share of queries whose first retrieved record belongs to the right condition (top-1); "
          f"intervals are 95% Wilson intervals [{R['wilson']}]. Top-3 and Top-5 count the first three or five retrieved records; MRR@5 is the mean reciprocal rank of the first correct record."),
    ]


def _screens():
    return [
        H2("8.2 Output screens"),
        P("The screens below were captured from the running application (Chrome, 1440 by 900 pixels, backend on port 8412 and React frontend on port 5412) using the demo account, with real queries sent through the real pipeline. "
          "The application is called CareLens AI on screen. Screens 07, 08, 09 to 12, 18, 19 and 20 were captured with the evidence-based fallback generator active, because the default local generator returns its own prompt in this software environment "
          "(Section 8.6); screen 21 was captured with the default generator and shows that defect. History rows are from the capture run only."),
        PAIR([_cap("01_landing_light.png", "Landing page, light theme: product pitch and entry buttons."),
              _cap("02_landing_dark.png", "Landing page, dark theme.")], 2.8),
        PAIR([_cap("03_landing_bottom_dark.png", "Bottom of the landing page (dark theme)."),
              _cap("17_not_found.png", "Unknown route: the 404 screen.")], 2.8),
        PAIR([_cap("04_register.png", "Create-account form (email and a password of 6 to 128 characters)."),
              _cap("05_login.png", "Sign-in form; the demo account is created automatically at start-up.")], 2.8),
        S("06_assistant_empty.png", "Symptom assistant before the first question: example chips, the consultation box and the permanent not-a-diagnosis line."),
        S("07_assistant_answer.png", "Answer to \"I have high fever, headache and body pain since yesterday\" (fallback generator): top condition Influenza, text assembled from the matched records. Note that the guidance sentence is repeated because several near-identical records matched."),
        S("20_assistant_evidence.png", "The same answer scrolled to the evidence cards: typical symptoms, description, guidance, severity badge, match bar and red flags per record. The fifth card is Dengue with a displayed match of 75%."),
        S("18_assistant_lay_query.png", "An everyday-language query (\"Burning when I pee, going to the toilet every few minutes and the urine looks cloudy\") retrieving Urinary Tract Infection."),
        S("19_assistant_caution.png", "Caution banner (amber) for \"I am pregnant and have mild nausea in the mornings\": the word `pregnant` is a caution keyword; the top record is Gastritis."),
        S("08_assistant_emergency.png", "Emergency banner (red) for \"I have severe chest pain and difficulty breathing\": the rule layer prepends an urgent-care notice and the top record is Heart Attack."),
        S("21_assistant_generator_echo.png", "Failure case: with the default Flan-T5 generator the answer text is the prompt itself (instruction lines, `User symptoms:` and the retrieved records), labelled `local-generator:google/flan-t5-small`."),
        S("09_history.png", "Consultation history: query, top condition, safety badge, displayed relevance (always 100% for the top record), date and view/delete actions."),
        S("10_history_search.png", "History filtered by the search term \"fever\"."),
        S("11_consultation_detail.png", "Saved consultation: summary table (symptoms, safety flag, top relevance, id) and the stored assistant answer, with back and delete buttons."),
        S("12_delete_confirm.png", "Confirmation dialog before a consultation is deleted."),
        S("13_about_metrics.png", "About page: the seven pipeline stages and the figures served from `results/metrics.json` (Top-1 100, Top-3 100, 245 ms, 176 records). These are the shipped evaluation's values; Section 8.3 explains why they are an upper bound, and the page itself adds that caveat further down."),
        S("14_about_dark.png", "About page, dark theme."),
        PAIR([_cap("15_mobile_assistant.png", "Assistant at phone width (390 pixels)."),
              _cap("16_mobile_history.png", "History as cards at phone width.")], 2.4),
    ]


def _per_condition_sentence():
    pc = F.M["lay_per_condition_correct"]
    full = [k for k, (a, b) in pc.items() if a == b]
    part = [(k, a, b) for k, (a, b) in pc.items() if a < b]
    s = (f"Per condition, the shipped pipeline answered both lay-language probes correctly for {len(full)} of the {len(pc)} conditions"
         + (", and missed at least one for " + ", ".join(f"{k} ({a} of {b})" for k, a, b in part) if part else "") + ". "
         "Conditions with a distinctive symptom (a rash with blisters, loss of smell and taste, face droop with slurred speech) are found reliably; conditions that overlap with a close neighbour, such as a common cold and allergic rhinitis, "
         "or a prolonged fever and appendicitis, are where the first record can be wrong.")
    return s


def _retrieval():
    sh = F.SHIP
    rows = []
    for s in F.SETS:
        x = sh[s]
        rows.append([SETN[s], str(x["n"]), F.pct(x["top1"], 1), F.ci("hybrid_rerank", s), F.pct(x["top3"], 1), F.pct(x["top5"], 1), F.f3(x["mrr5"]), str(x["n_misses"])])
    return [
        H2("8.3 Retrieval accuracy of the shipped pipeline"),
        P("The shipped configuration is hybrid fusion followed by the cross-encoder, with the HyDE-style expansion on. Table 8.2 gives its accuracy on the five query sets."),
        TAB("Accuracy of the shipped pipeline (hybrid + cross-encoder) on the five query sets", ["Query set", "n", "Top-1", "95% CI", "Top-3", "Top-5", "MRR@5", "Misses"],
            rows, widths=[2.3, 0.4, 0.6, 0.9, 0.6, 0.6, 0.6, 0.5], align=["l", "c", "c", "c", "c", "c", "c", "c"], size=9),
        H3("8.3.1 The shipped 100% is an upper bound"),
        P(f"`scripts/evaluate.py` holds one record per condition out of the test set but leaves it in the index, and its query is that record's own symptom list. Retrieval then finds the record itself, and "
          f"the About page reports {F.pct(F.SHIPPED_EVAL.get('top1_accuracy', 1.0), 0)} for Top-1, Top-3, precision, recall, F1 and MRR on {F.SHIPPED_EVAL.get('n_test', 30)} queries. Reproducing that protocol gives {F.pct(_r('hybrid_rerank', S1P), 1)}; "
          f"removing the held-out record gives {F.pct(_r('hybrid_rerank', S1L), 1)} on the same queries and {F.pct(_r('hybrid_rerank', S2), 1)} on all {F.SHIP[S2]['n']} records. The sibling records of the same condition remain in the index, "
          f"so even leave-one-out is generous; the figure shows how the same pipeline falls as queries become less like the stored text."),
        FIG(F.fig("f03_protocol_comparison.png"), "The shipped pipeline under four conditions: shipped protocol, leave-one-out, two-symptom queries and lay-language probes.", 5.2),
        H3("8.3.2 Failure patterns"),
        P(f"On the lay-language probes the pipeline fails {F.SHIP[S4]['n_misses']} times in {F.SHIP[S4]['n']}: "
          + "; ".join(f"\"{m['query']}\" (true {m['truth']}, first record {m['predicted']})" for m in F.SHIP[S4]["misses"])
          + f". Both are confusions between conditions that share most symptoms. On two-symptom queries it fails {F.SHIP[S3]['n_misses']} times in {F.SHIP[S3]['n']}; the logged examples are "
          + "; ".join(f"\"{m['query']}\" ({m['truth']} read as {m['predicted']})" for m in F.SHIP[S3]["misses"][:4])
          + ". Two symptoms such as headache and fatigue are shared by many conditions, so these misses reflect real ambiguity, and a single ranked answer hides it."),
        P(_per_condition_sentence()),
        FIG(F.fig("f01_lay_confusion.png"), "Confusion matrix of the shipped pipeline on the 60 lay-language probes (rows: true condition, columns: first retrieved condition).", 5.4),
        P(f"The five evidence cards are not five different conditions: the mean number of distinct conditions among the five retrieved records is {F.SHIP[S4]['mean_distinct_conditions_in_top5']} on the lay probes and "
          f"{F.SHIP[S3]['mean_distinct_conditions_in_top5']} on the two-symptom queries, because each condition owns four to six near-identical records. The \"possible conditions\" list is therefore not a differential diagnosis."),
    ]


def _ablation():
    cfgs = F.CFG_ORDER
    rows = []
    for c in cfgs:
        rows.append([F.RET[c]["label"]] + [F.pct(_r(c, s), 1) for s in (S2, S3, S4)] + [F.f3(_r(c, S4, "mrr5"))])
    nh, sh = "hybrid_rerank_nohyde", "hybrid_rerank"
    return [
        H2("8.4 Ablation: what each stage contributes"),
        P("The same query sets were run through seven configurations. The BM25 and dense paths use the same expanded query as the pipeline, so the table isolates retrieval and ranking rather than the interface."),
        TAB("Top-1 accuracy by configuration (leave-one-out for S2 and S3)", ["Configuration", "S2 (176)", "S3 (176)", "S4 (60)", "S4 MRR@5"], rows,
            widths=[2.7, 0.9, 0.9, 0.9, 0.9], align=["l", "c", "c", "c", "c"], size=9.5),
        FIG(F.fig("f02_ablation.png"), "Top-1 accuracy of the seven retrieval configurations on the verbatim, two-symptom and lay-language query sets.", 5.4),
        B(f"**Lexical matching is already strong on this data.** BM25 alone reaches {F.pct(_r('bm25', S2), 1)} on S2 and {F.pct(_r('bm25', S4), 1)} on S4. The knowledge base was generated from short symptom phrases, so word overlap is a very good signal.",
          f"**Dense embeddings alone are weaker on verbatim text** ({F.pct(_r('dense', S2), 1)} on S2) but slightly better on lay language ({F.pct(_r('dense', S4), 1)} on S4); fusion gives {F.pct(_r('hybrid', S2), 1)} and {F.pct(_r('hybrid', S4), 1)}.",
          f"**The cross-encoder helps on lay language** ({F.pct(_r('hybrid', S4), 1)} to {F.pct(_r(sh, S4), 1)}, a change of about {abs(F.SHIP[S4]['n_misses'] - F.RET['hybrid'][S4]['n_misses'])} queries out of {F.SHIP[S4]['n']}) and on two-symptom queries ({F.pct(_r('hybrid', S3), 1)} to {F.pct(_r(sh, S3), 1)}), at a cost of several hundred milliseconds (Section 8.8).",
          f"**The HyDE-style expansion did not help.** Without it the shipped pipeline scores {F.pct(_r(nh, S2), 1)} on S2, {F.pct(_r(nh, S3), 1)} on S3 and {F.pct(_r(nh, S4), 1)} on S4, against {F.pct(_r(sh, S2), 1)}, {F.pct(_r(sh, S3), 1)} and {F.pct(_r(sh, S4), 1)} with it. "
            "The expansion is a fixed template that wraps the user's words in generic medical phrasing; it adds no information, and the extra words dilute the query. The differences are small (a few queries) and the intervals overlap, so the honest reading is no measurable benefit rather than proven harm."),
        FIG(F.fig("f09_hyde_effect.png"), "Effect of the HyDE-style expansion: the shipped pipeline with and without it on each query set.", 5.0),
        P(f"**Offline mode.** When the sentence-embedding model cannot be downloaded the application falls back to TF-IDF vectors and skips reranking. That mode scores {F.pct(_r('hybrid_tfidf', S4), 1)} on S4 and {F.pct(_r('hybrid_tfidf', S3), 1)} on S3 "
          f"(and {F.pct(_r('hybrid_tfidf', S2), 1)} on verbatim S2): usable, and weaker than the full pipeline on paraphrased input ({F.pct(_r(sh, S4), 1)}). The interface does not tell the user which mode is running."),
    ]


def _relevance():
    r = F.REL
    ex = r["out_kb_examples"][:6]
    return [
        H2("8.5 The displayed relevance score"),
        P(f"The match bar and the labels Strong, Moderate and Weak are computed by min-max normalising the cross-encoder scores of the {F.CANDIDATE_K} candidates, so the best candidate always receives 1.00 and a Strong label. "
          f"The measurement confirms it: the top record had displayed relevance 1.00 in all {r['in_kb_n']} in-knowledge-base queries and in all {r['out_kb_n']} out-of-knowledge-base complaints, and all {r['out_kb_n']} of the latter were labelled Strong match "
          f"(also through `pipeline.answer`: {r['out_kb_labels_via_pipeline_answer']}). The history screen shows 100% in every row for the same reason."),
        TAB("Complaints with no matching condition in the knowledge base", ["Query", "First record shown", "Displayed", "Raw rerank score"],
            [[x["query"], x["top_condition"], "100% Strong", F.f2(x["raw_rerank"])] for x in ex], widths=[3.0, 1.4, 0.9, 1.0], align=["l", "l", "c", "c"], size=9.5),
        P(f"The information needed to do better is present. The raw cross-encoder score of the top record averages {r['raw_rerank_in_kb']['mean']} for in-knowledge-base queries (range {r['raw_rerank_in_kb']['min']} to {r['raw_rerank_in_kb']['max']}) and "
          f"{r['raw_rerank_out_kb']['mean']} for out-of-knowledge-base ones (range {r['raw_rerank_out_kb']['min']} to {r['raw_rerank_out_kb']['max']}); the area under the ROC curve for telling them apart is {r['auroc_in_vs_out_by_raw_rerank_score']} with the raw rerank score and "
          f"{r['auroc_in_vs_out_by_raw_hybrid_score']} with the raw hybrid score. The normalisation throws it away. On this small set a threshold on the raw score would separate the groups perfectly; with only {r['out_kb_n']} out-of-knowledge-base queries that is encouraging but not a guarantee."),
        FIG(F.fig("f05_relevance_display.png"), "Raw cross-encoder score of the top record for in-knowledge-base and out-of-knowledge-base queries, against the constant displayed value of 100%.", 5.2),
    ]


def _generation():
    g = F.GEN
    return [
        H2("8.6 Generated answer text"),
        P(f"With the default configuration the generator returned the prompt, not an answer: {g['echo_answers']} of {g['n']} test queries ({F.pct(g['echo_rate'], 0)}) produced text beginning with the instruction lines followed by the user's symptoms and the retrieved records. "
          f"The cause is the installed library version: transformers {g['transformers_version']} no longer provides the `text2text-generation` task ({g['text2text_task_in_installed_transformers']}), so the code falls back to the `text-generation` task, "
          f"which for a T5 model returns its input. The answer is still labelled `{g['generator_label']}`. Generation took {g['mean_generate_ms']:.0f} ms on average. The requirement file asks only for `transformers>=4.38`, so an older version would not show this behaviour; it was not tested here."),
        P(f"The evidence-based fallback, used when no generator can be loaded, builds the answer from the retrieved records in {g['mean_fallback_ms']} ms. Every condition it names is one of the retrieved records ({g['fallback_names_only_retrieved_conditions']} of {g['n']} answers; true by construction). "
          "This gives structural grounding, since nothing outside the retrieved text can appear. It is not a synthesis: it lists the matched records and repeats their guidance sentence once per matching record (screens 07 and 11), it has no per-statement citation, "
          "and no human or model judgement of groundedness was carried out, so objective 4 is only partly met."),
    ]


def _safety():
    s = F.SAF
    gp, gn = s["by_group_pos"], s["by_group_neg"]
    f = s["filter"]
    return [
        H2("8.7 Safety layer"),
        P(f"The rule layer has {s['n_rules']} emergency patterns and {s['n_caution_keywords']} caution keywords. It was tested with {s['n_pos']} emergency descriptions and {s['n_neg']} other texts written by the team."),
        TAB("Emergency detection on the probe sets", ["Probe group", "Texts", "Result"],
            [["Emergencies worded like the rules", str(gp["literal"]["n"]), f"{gp['literal']['detected']} flagged emergency"],
             ["Emergencies in everyday wording", str(gp["paraphrase"]["n"]), f"{gp['paraphrase']['detected']} flagged emergency; {gp['paraphrase']['flagged_caution_instead']} flagged caution; the rest passed as routine"],
             ["Ordinary non-emergency texts", str(gn["ordinary"]["n"]), f"{len(gn['ordinary']['false_emergency'])} false emergencies; {gn['ordinary']['routine']} routine"],
             ["Hard negatives (negation, history)", str(gn["hard"]["n"]), f"{len(gn['hard']['false_emergency'])} false emergencies, {len(gn['hard']['caution'])} caution flags"]],
            widths=[2.3, 0.7, 3.2], align=["l", "c", "l"], size=9.5),
        FIG(F.fig("f06_safety_rules.png"), "Emergency detection: recall on literal and paraphrased wording, and false alarms on ordinary and hard-negative texts.", 5.2),
        P(f"Overall recall is {F.pct(s['emergency_recall'], 1)} (95% CI {s['recall_ci'][0] * 100:.1f}-{s['recall_ci'][1] * 100:.1f}%) and precision {F.pct(s['emergency_precision'], 1)}. The rules catch the wording they were written for and nothing else: "
          f"\"{gp['paraphrase']['missed'][0]}\", \"{gp['paraphrase']['missed'][2]}\" and \"{gp['paraphrase']['missed'][9]}\" all passed as routine. In the other direction a sentence that merely mentions a trigger "
          f"(\"{gn['hard']['false_emergency'][0]}\") raised an emergency alarm because negation and history are not understood. For a health tool, the missed paraphrases are the serious failure."),
        P(f"The answer filter removed a banned phrase in {f['removed']} of {f['n']} test sentences, and in {f['listed_removed']} of the {f['n_listed_phrases']} cases that use one of its five listed phrases: the replacement is case-sensitive, so \"Take ibuprofen\", \"Dosage:\" and \"Prescribe\" at the start of a sentence are detected but not replaced. "
          "Drug names outside the list (paracetamol, amoxicillin) pass through. The retrieved guidance texts contain no dosages, so the filter is a second line of defence that was never needed in the captured sessions."),
    ]


def _speed():
    st = F.LAT["stages_ms"]
    a = F.LAT["pipeline_answer_with_local_generator_ms"]
    b = F.LAT["pipeline_answer_fallback_only_ms"]
    rows = [[k, f"{st[k]['mean']:.2f}", f"{st[k]['median']:.2f}", f"{st[k]['p95']:.2f}"] for k in ("expand", "embed", "faiss", "bm25", "fuse", "rerank", "safety")]
    names = {"expand": "query expansion", "embed": "query embedding", "faiss": "FAISS search", "bm25": "BM25 search", "fuse": "score fusion", "rerank": "cross-encoder rerank (15 pairs)", "safety": "safety rules"}
    for r in rows:
        r[0] = names[r[0]]
    t5, fb = F.LAT_T5, F.LAT_FB
    return [
        H2("8.8 Speed"),
        P(f"Per-stage times for {F.LAT['n']} queries with warm models are in Table 8.5. The cross-encoder dominates ({st['rerank']['mean']:.0f} ms on average for 15 pairs on the CPU); everything else except the query embedding ({st['embed']['mean']:.0f} ms mean, with a few slow outliers) takes a few milliseconds. "
          f"The stages were timed in separate passes, so they do not add up exactly to the totals. A whole `pipeline.answer` call takes {a['mean']:.0f} ms on average with the local generator (p95 {a['p95']:.0f} ms) and {b['mean']:.0f} ms with the fallback (p95 {b['p95']:.0f} ms)."),
        TAB("Time per pipeline stage (milliseconds, 30 queries, warm models)", ["Stage", "Mean", "Median", "95th percentile"], rows, widths=[2.6, 1.0, 1.0, 1.3], align=["l", "c", "c", "c"], size=9.5),
        FIG(F.fig("f04_latency_stages.png"), "Mean time per pipeline stage and totals for the two generator modes.", 5.2),
        P(f"Over HTTP on 127.0.0.1, `POST /api/chat` took {fb['chat_ms']['mean']:.0f} ms on average with the fallback generator (median {fb['chat_ms']['median']:.0f}, p95 {fb['chat_ms']['p95']:.0f}) and {t5['chat_ms']['mean']:.0f} ms with the Flan-T5 generator "
          f"(median {t5['chat_ms']['median']:.0f}, p95 {t5['chat_ms']['p95']:.0f}); sign-in takes about {fb['login_ms']['mean']:.0f} ms because of bcrypt, listing the history about {fb['history_list_ms']['mean']:.0f} ms and the health check about {fb['health_ms']['mean']:.0f} ms. "
          "The first request after start-up must load the models, which took about a minute in the measurement script, so the application is best started once and kept running. A reply in well under two seconds is comfortable for a chat; no load or concurrency test was made."),
        FIG(F.fig("f08_api_latency.png"), "HTTP latency of POST /api/chat with the fallback generator and with the default Flan-T5 generator.", 4.8),
    ]


def _tests():
    return [
        H2("8.9 Functional tests"),
        P(f"The nine pytest tests passed ({F.PYTEST_PASSED} of {F.PYTEST_TOTAL}, {F.PYTEST_SECONDS} s): query normalisation, emergency detection, the dosage filter, password hashing, fusion, the generator fallback, authentication with history isolation between users, "
          f"request validation and a retrieval round trip. The end-to-end smoke test, which goes through the Vite proxy as a browser would, passed {F.SMOKE_PASSED} of {F.SMOKE_TOTAL} checks (health, sign-in, session cookie, chat, evidence fields, emergency escalation, validation, history list, search, detail, delete, "
          "registration, duplicate-email rejection, private history of a new account, sign-out). The tests show that the wiring works; they do not measure clinical correctness."),
    ]


def _compare():
    return [
        H2("8.10 Comparison with the base paper"),
        P(f"The base paper {F.BASE_SHORT} [{R['base']}] reports no figures: its results section describes \"experimental observations\" that the hybrid retrieval \"consistently\" returns relevant records and shows one chat example "
          "(constipation, stomach ache, high fever and swollen lymph nodes giving Typhoid). There is no accuracy, no recall, no latency and no stated dataset size, and its \"Sequence-NQ transformer\" is not specified further. "
          "A numerical comparison is therefore impossible, and the datasets differ in any case: the base paper's symptom-disease knowledge base is not described in measurable terms, and this project's is a synthetic 176-record table. What can be compared is what each system does."),
        TAB("Qualitative comparison with the base paper", ["Aspect", "Base paper [1]", "This project (CareLens AI)"],
            [["Retrieval", "Sequence-NQ embeddings + FAISS", "MiniLM embeddings + FAISS and BM25, fused 0.65/0.35"],
             ["Reranking", "Not described", "Cross-encoder (MS MARCO MiniLM) on 15 candidates"],
             ["Query expansion", "Not described", "Rule-based HyDE-style template (no measured benefit)"],
             ["Generation", "RAG answer generation", "Flan-T5-small or deterministic evidence-based fallback"],
             ["Safety", "Not described", "Emergency regex rules, caution keywords, answer filter, disclaimer"],
             ["Application", "Registration, login, chatbot, history", "FastAPI + React app, bcrypt/JWT, private history with search, detail and delete"],
             ["Longitudinal tracking", "Stores history \"to support future analysis\"", "Stores and lists consultations; no trend analysis"],
             ["Evaluation", "Qualitative observations, no figures", "Five query sets, ablation, probes, latency, tests, with intervals"],
             ["Data", "Symptom-disease knowledge base (not quantified)", f"Synthetic, {F.KB['records']} records, {F.KB['conditions']} conditions"]],
            widths=[1.3, 2.3, 2.7], align=["l", "l", "l"], size=9.5),
        P("The honest summary is that this work adds components and a measurement the base paper does not describe, while neither work has been validated on real clinical data."),
    ]


def _samples():
    s3 = F.SHIP[S3]["misses"]
    return [
        H2("8.11 Sample inputs and outputs, success and failure analysis"),
        TAB("Sample queries and what the pipeline did (captured sessions and logged probes)", ["Input", "Output", "Verdict"],
            [["I have high fever, headache and body pain since yesterday", "Top record Influenza; fifth card Dengue (75%); routine", "Correct; plausible differential"],
             ["Burning when I pee, going to the toilet every few minutes and the urine looks cloudy", "Urinary Tract Infection", "Correct on everyday wording"],
             ["I have severe chest pain and difficulty breathing", "Emergency banner; top record Heart Attack", "Correct and safe"],
             ["I am pregnant and have mild nausea in the mornings", "Caution banner; top record Gastritis", "Caution correct; condition is a weak guess"],
             [f"{s3[0]['query']}" if s3 else "-", f"{s3[0]['predicted']} (true {s3[0]['truth']})" if s3 else "-", "Failure: shared symptoms"],
             [f"{s3[2]['query']}" if len(s3) > 2 else "-", f"{s3[2]['predicted']} (true {s3[2]['truth']})" if len(s3) > 2 else "-", "Failure: shared symptoms"],
             [F.REL["out_kb_examples"][1]["query"] + " (out-of-knowledge-base)", f"{F.REL['out_kb_examples'][1]['top_condition']}, shown as 100% Strong match", "Failure: no abstention"]],
            widths=[2.8, 2.2, 1.3], align=["l", "l", "l"], size=9.5),
        H3("8.11.1 What works"),
        B(f"Condition retrieval on symptom text is accurate on this knowledge base: {F.pct(_r('hybrid_rerank', S2), 1)} on verbatim leave-one-out and {F.pct(_r('hybrid_rerank', S4), 1)} on lay language.",
          "Emergency wording that matches the rules is escalated prominently, and the permanent disclaimer is always present.",
          f"The application is responsive on a CPU-only PC, keeps data private per user, runs offline with fallbacks, and passed {F.PYTEST_PASSED} of {F.PYTEST_TOTAL} unit tests and {F.SMOKE_PASSED} of {F.SMOKE_TOTAL} end-to-end checks."),
        H3("8.11.2 What fails"),
        B("The local generator echoes its prompt in the tested environment, so the generative half of \"RAG\" is not working; answers come from a template.",
          "The relevance display cannot express uncertainty: everything is a Strong match, including complaints outside the knowledge base.",
          f"Emergency rules miss all {F.SAF['by_group_pos']['paraphrase']['n']} paraphrased emergencies in the probe set and raise false alarms on negations.",
          "Evidence cards repeat near-identical records, so the user sees one condition five times instead of alternatives.",
          "Reported symptoms are not tracked over time: the history is a list, not a trend."),
    ]


def _limits():
    return [
        H2("8.12 Limitations of the evaluation"),
        B("The knowledge base is synthetic and tiny; high scores reflect how it was built (short phrases, one text per condition), not medical competence.",
          "The lay-language, out-of-knowledge-base and safety probes were written by the authors, are small, and were not reviewed by clinicians.",
          "Leave-one-out leaves sibling records in the index; a stricter test would hold out whole record families or use an independent source.",
          "No human judgement of answer quality or groundedness, no user study, no load test, no accessibility audit.",
          "One machine and one library set; the generator behaviour depends on the installed transformers version.",
          "Latency stages were timed in separate passes on warm models; cold-start cost was measured once."),
    ]


OBJECTIVES = [
    ("1", "Build a curated medical knowledge base and index it for semantic retrieval", "Achieved (synthetic data)",
     f"{F.KB['records']} records, {F.KB['conditions']} conditions, FAISS flat index and BM25 index; written by the team, not clinically curated."),
    ("2", "Accept natural-language symptoms and expand the query", "Achieved",
     "Free text accepted (3 to 2000 characters); expansion is a rule-based template and showed no measurable benefit."),
    ("3", "Hybrid retrieval with neural reranking", "Achieved, measured",
     f"Hybrid + cross-encoder: top-1 {F.pct(_r('hybrid_rerank', S4), 1)} on lay probes and {F.pct(_r('hybrid_rerank', S3), 1)} on two-symptom queries."),
    ("4", "Grounded responses that cite the retrieved source for every statement", "Partly",
     "Answers are built from retrieved records and shown with evidence cards (record id, symptoms, guidance), but there is no per-statement citation and the local generator echoes its prompt."),
    ("5", "Track reported symptoms over time to reveal progression and trends", "Not achieved beyond storage",
     "Consultations are saved, searchable, viewable and deletable; there is no trend, timeline or progression analysis."),
    ("6", "Evaluate retrieval relevance, groundedness and response time", "Partly",
     "Retrieval and response time measured; groundedness checked structurally only (no judge)."),
]


def _objectives():
    return [
        H2("8.13 Objectives against outcomes"),
        TAB("Objectives of the project against what was measured", ["No.", "Objective", "Status", "Evidence"], [list(o) for o in OBJECTIVES],
            widths=[0.4, 2.0, 1.1, 2.8], align=["c", "l", "c", "l"], size=9.5),
        P("In short, the retrieval half of the system works and has been measured honestly; the generative half, the uncertainty display, the safety rules on paraphrased input and the longitudinal tracking promised by the base paper's gap statement are the parts that still need work before the tool could be used by real patients."),
    ]


def blocks():
    out = [H1("CHAPTER 8: RESULTS AND OUTPUT SCREENS"),
           P("This chapter reports what was measured and what the running application shows. Section 8.1 describes the set-up, Section 8.2 presents every output screen, Sections 8.3 to 8.9 give the quantitative results "
             "(retrieval accuracy, ablation, the relevance display, generated text, the safety layer, speed and tests), Section 8.10 compares the work with the base paper, and Sections 8.11 to 8.13 give sample output, "
             "success and failure analysis, the limits of the evaluation and the outcome against each objective. Where a result is weak it is reported as weak.")]
    parts = [_setup, _retrieval, _ablation, _relevance, _generation, _safety, _speed, _tests, _compare, _samples, _limits, _objectives]
    out += _setup()
    if F.REPORT:
        from . import ch8_report

        out += ch8_report.screens()
    else:
        out += _screens()
    for p in parts[1:]:
        out += p()
    return out
