"""Chapter 8: Results and Output Screens (also document 14)."""

import os
import sys

from . import facts as F
from .blocks import B, FIG, H1, H2, H3, N, P, TAB

sys.path.insert(0, os.path.join(F.CODE, "scripts"))

OBJECTIVES = [
    "Build a document ingestion module that parses syllabi, lecture notes and question banks and extracts subjects, units and topics.",
    "Store the extracted content as vector embeddings so the material can be searched semantically rather than by keyword.",
    "Implement a RAG question-answering engine that answers strictly from the uploaded material and cites the source.",
    "Apply semantic context compression so retrieval stays accurate without exceeding the model context window.",
    "Generate personalised study roadmaps and revision schedules from topic coverage and performance.",
    "Present curriculum coverage, study velocity and engagement metrics on an interactive dashboard.",
]

SHIPPED = F.SHIPPED
BM = "bm25"
HY = "hybrid_bm25_dense"
DN = "dense_bge_small"
TYPES = ["fact", "definition", "reasoning"]


def screen(name, caption, base=5.4, max_h=3.4):
    p = F.shot(name)
    return FIG(p, caption, F.shot_w(p, base, max_h))


def pair(a, ca, b_, cb, w=3.1):
    return ("pair", [(F.shot(a), ca), (F.shot(b_), cb)], w)


def pairf(a, ca, b_, cb, w=3.1):
    return ("pair", [(F.fig(a), ca), (F.fig(b_), cb)], w)


def objective_rows():
    status = [
        ("Partly met", "PDF, DOCX and TXT are parsed; subjects and units are recognised from \"Subject:\", \"Course:\", \"Unit n:\" and \"Chapter n:\" headings "
                       "(36 of 36 units on the corpus) but not from \"UNIT-I\", \"Module 1\" or numbered lists (0 of 5 each); DOCX tables and scanned pages are not read."),
        ("Not met", f"The shipped retriever is TF-IDF with cosine similarity, which is lexical. A dense model was measured only as a reference (Hit@4 {F.hit(DN, 4):.3f}, "
                    f"hybrid with BM25 {F.hit(HY, 4):.3f}) and is not part of the product."),
        ("Met in extractive mode", "Every answer word comes from the retrieved chunks (100 %) and each answer lists source file, passage and match score. "
                                   "Without a relevance threshold, 9 of 12 off-topic questions still received an answer. The Claude mode was not measured."),
        ("Partly met", f"Extractive sentence selection removes {F.CMP['4']['token_reduction_pct']:.1f} % of the words of four retrieved chunks, but answer-key recall falls from "
                       f"{F.CMP['4']['key_in_ctx']:.3f} to {F.CMP['4']['key_in_ans']:.3f}. There is no question-type routing and no learned compression as in [1]."),
        ("Partly met", "A priority roadmap (High below 50 %, Medium below 80 %, Low otherwise) is built from quiz accuracy per topic. There is no revision schedule, no spaced repetition and no coverage model; "
                       "topics are single TF-IDF keywords."),
        ("Partly met", "The dashboard shows documents, questions asked, quiz questions attempted, subject-wise accuracy and recent documents. Curriculum coverage and study velocity over time are not computed."),
    ]
    return [[str(i), o, s, why] for i, (o, (s, why)) in enumerate(zip(OBJECTIVES, status), 1)]


# ---------------------------------------------------------------- 8.2 screens
def screens_main():
    return [
        H2("8.2 Output screens"),
        P("All screens are real captures (1440 x 900 pixels) of the React application running against the FastAPI backend, taken by `scripts/capture_screens.py --rich` on a scratch database. "
          "The user has five uploaded documents (the bundled sample notes and four corpus files), four questions asked and eight quizzes taken. The quiz answers were scripted: the capture script picks the option that restores "
          "the sentence from the notes for a chosen number of questions out of five, which simulates a student with different mastery in each subject. The scores on the dashboard and the roadmap therefore illustrate the screens "
          "and are not results of a user study. The landing, login, registration, picker and dark-theme screens are in Appendix C."),
        H3("8.2.1 Upload, documents, dashboard and roadmap"),
        pair("06_upload-done.png", "Upload after processing the sample notes: \"12 topics detected, 4 chunks indexed\" and the topic chips.",
             "08_documents.png", "Documents: five documents with subject, detected topics, chunk counts (114, 104, 112, 101, 4), quiz and delete buttons.", 3.15),
        P("The first six chips are the subject and unit headings found by the heading rules; the last six are TF-IDF keywords that fill the list up to twelve. The generic words \"data\", \"unit\" and \"structures\" "
          "show why keyword topics are a weak basis for a roadmap (Section 8.12)."),
        pair("07_dashboard.png", "Dashboard: 5 documents, 4 questions, 40 quiz questions; accuracy per subject (Data Structures 85 %, Algorithms 80 %, Operating Systems 60 %, Database Systems 30 %).",
             "13_roadmap.png", "Roadmap: 30 topics (High 9, Medium 2, Low 19); the first rows are generic keywords such as \"elements\", \"used\" and \"using\".", 3.15),
        P("The bars use the same thresholds as the roadmap, so the red bar for Database Systems (30 %) and the amber bar for Operating Systems (60 %) mark the subjects to revise first. The scores come from the scripted answers."),
        H3("8.2.2 Asking questions and taking a quiz"),
        screen("09_ask.png", "Ask screen: \"What is a deadlock?\" answered from 02_Operating_Systems.txt (passage 8, match 0.46), with the badge \"Offline mode: key sentences from your notes\", recent questions and expandable sources.", 4.6, 3.3),
        P("The answer is made of sentences of the notes, so nothing is invented and the source passage is named. The sentences chosen, however, describe deadlock avoidance and recovery and not the definition, "
          "which lies in the first passage of the document (Section 8.12)."),
        pair("11_quiz-taking.png", "Quiz in progress: fill-in-the-blank questions with four options.",
             "12_quiz-result.png", "Quiz result: 80 % (4 of 5) with the correct term and topic per question.", 3.15),
        P("Question 3 of this quiz (\"____ 2: Stacks and Queues A stack is\") is built from a heading line and illustrates the poor questions counted in Section 8.7. "
          "The correct answers stay on the server until the quiz is graded."),
    ]


# ---------------------------------------------------------------- blocks
def blocks():
    c = F.CORPUS
    ci = F.RET_CI
    sh = F.RET[SHIPPED]
    cm4 = F.CMP["4"]
    b = [H1("CHAPTER 8: RESULTS AND OUTPUT SCREENS")]

    # ---- 8.1
    b += [H2("8.1 Experimental setup and protocol"),
          P(f"The product has no trained model, so there is no accuracy to report in the usual sense. Its own code was therefore run on a purpose-built evaluation corpus: six subject files (Data Structures, Operating Systems, "
            f"Database Systems, Computer Networks, Machine Learning, Algorithms) assembled from 36 English Wikipedia articles [18] under CC BY-SA 4.0, {c['words']:,} words in all, laid out with a \"Subject:\" line and six \"Unit n:\" sections. "
            f"Chunked by the platform (180 words, 30 overlap) the corpus gives {c['chunks']} chunks of {c['mean_chunk_words']} words on average. Every article is pinned to a revision identifier in `experiments/corpus_manifest.json`, "
            f"so `scripts/fetch_corpus.py` rebuilds it exactly."),
          P(f"The evaluation set has {c['questions']} hand-written questions, 12 per subject and 24 each of the three question types of the base paper [1] (fact, definition, reasoning, typed by wording). "
            f"The gold answer of a question is a sentence fragment copied from the corpus; a retrieved chunk is a hit when it contains it. All {c['evidence_intact_in_a_chunk']} fragments lie wholly inside at least one chunk. "
            f"A further {c['off_topic_questions']} off-topic questions test whether the system refuses what its notes cannot answer. Measurements were made on {F.ENV['cpu']} with {F.ENV['ram']} of memory and no GPU "
            f"(Python {F.ENV['python']}, scikit-learn {F.ENV['sklearn']}) on 25 October 2026; the machine was shared, so timings are medians of repeated runs. The measures are Hit@k, mean reciprocal rank over ten chunks (MRR@10), "
            "answer-key recall (a short key string of the gold answer occurs in the text), words passed on, and milliseconds."),
          P("**What this protocol does not show.** The corpus is encyclopaedic text and not a student's scanned notes; the questions were written by the project team; with only 72 of them the 95 % interval of the shipped retriever's Hit@4 "
            f"is wide ({ci['hit4'][0]:.3f} to {ci['hit4'][1]:.3f}); and the generator under test is the offline extractive one, because no API key for the Claude mode was available. The numbers describe how the shipped components "
            "behave on this corpus, not real classroom use.")]
    b += screens_main()

    # ---- 8.3 retrieval
    ks = (1, 3, 4, 10)
    rows = [F.ret_row(n, ks) for n in ["tfidf_shipped (1-2gram)", "tfidf_unigram", "bm25", "tfidf_lsa200", "hybrid_bm25_lsa", "dense_bge_small", "hybrid_bm25_dense"]]
    b += [H2("8.3 Retrieval quality"),
          P(f"Seven retrievers were run on the same {c['chunks']} chunks and 72 questions: the shipped TF-IDF retriever (unigrams and bigrams), a unigram variant, BM25 [6] (k1 = 1.5, b = 0.75), latent semantic analysis [8] with 200 dimensions, "
            "a weighted sum of BM25 and LSA, the dense BGE-small model [9] (quantised ONNX through `fastembed`, 384 dimensions) and a weighted sum of BM25 and the dense scores. The last four are reference points outside the product."),
          TAB("Retrieval quality, 72 questions, 672 chunks (the shipped retriever is the first row)", ["Retriever", "Hit@1", "Hit@3", "Hit@4", "Hit@10", "MRR@10"], rows,
              widths=[2.3, 0.7, 0.7, 0.7, 0.7, 0.8], align=["l", "c", "c", "c", "c", "c"], size=10),
          FIG(F.fig("fig_retrieval_methods.png"), "Hit@1, Hit@4 and MRR@10 of the seven retrievers on the same chunks and questions.", 5.0),
          P(f"The shipped retriever puts the evidence in the top four chunks for {F.pct(F.hit(SHIPPED, 4))} of the questions and in the first chunk for {F.pct(F.hit(SHIPPED, 1))}. "
            f"Bootstrap intervals (2,000 resamples) are {ci['hit1'][0]:.3f} to {ci['hit1'][1]:.3f} for Hit@1, {ci['hit4'][0]:.3f} to {ci['hit4'][1]:.3f} for Hit@4 and {ci['mrr10'][0]:.3f} to {ci['mrr10'][1]:.3f} for MRR@10, "
            f"so differences of a few points between retrievers are within noise. Two signals are larger: BM25 ranks the evidence first more often than TF-IDF ({F.hit(BM, 1):.3f} against {F.hit(SHIPPED, 1):.3f}), "
            f"and the sum of BM25 and dense scores is best on every measure (Hit@1 {F.hit(HY, 1):.3f}, Hit@4 {F.hit(HY, 4):.3f}, MRR@10 {F.RET[HY]['mrr10']:.3f}). The dense model alone is no better than TF-IDF "
            f"(Hit@4 {F.hit(DN, 4):.3f} against {F.hit(SHIPPED, 4):.3f}); its value lies in being complementary to a lexical score, in line with the hybrid design of [1]. "
            f"Embedding the 672 chunks took {F.DENSE['embed_chunks_s']} s on the CPU and each query {F.DENSE['embed_query_ms_each']} ms."),
          H3("8.3.1 By question type, number of chunks and chunk size")]
    bt_ = F.RET
    b += [pairf("fig_by_type.png", "Hit@1 and Hit@4 by question type for the shipped retriever, BM25 and BM25 plus dense.",
                "fig_hit_at_k.png", "Hit@k for k = 1 to 10; the dotted line marks the default of four chunks.", 3.2),
          P(f"For the shipped retriever, fact and definition questions reach the same Hit@4 ({sh['by_type']['fact']['hit4']:.3f}) but definitions are rarely ranked first (Hit@1 {sh['by_type']['definition']['hit1']:.3f}, against {sh['by_type']['fact']['hit1']:.3f} for facts), "
            f"because a definition question such as \"What is routing?\" contains words that occur in dozens of chunks of the same subject. Reasoning questions are hardest at four chunks ({sh['by_type']['reasoning']['hit4']:.3f}) because their wording differs from the sentence that holds the answer. "
            f"BM25 gains most on facts (Hit@4 {bt_[BM]['by_type']['fact']['hit4']:.3f}); the hybrid is the only retriever strong on all three types (Hit@4 {bt_[HY]['by_type']['fact']['hit4']:.3f}, {bt_[HY]['by_type']['definition']['hit4']:.3f} and {bt_[HY]['by_type']['reasoning']['hit4']:.3f}). "
            f"The curve is steep up to four chunks and flat after ten: with TF-IDF, {F.hit(SHIPPED, 3):.3f} of the questions are covered by three chunks, {F.hit(SHIPPED, 4):.3f} by four and {F.hit(SHIPPED, 10):.3f} by ten.")]
    crow = []
    for k, v in F.CHUNKS.items():
        mark = " (shipped)" if k == "180/30" else ""
        crow.append([k + mark, f"{v['chunks']:,}", f"{v['mean_words']:.0f}", f"{v['evidence_intact']}/72", f"{v['hit1']:.3f}", f"{v['hit4']:.3f}", f"{v['hit10']:.3f}", f"{v['mrr10']:.3f}"])
    b += [TAB("Effect of the chunk size (words / overlap) on the shipped TF-IDF retriever", ["Size / overlap", "Chunks", "Mean words", "Evidence intact", "Hit@1", "Hit@4", "Hit@10", "MRR@10"], crow,
              widths=[1.3, 0.7, 0.7, 0.9, 0.6, 0.6, 0.7, 0.8], align=["l", "c", "c", "c", "c", "c", "c", "c"], size=9.5),
          P("Very small chunks (60 words) split 2 of the 72 evidence fragments across boundaries and score lowest (Hit@4 0.611). Larger chunks score higher, but not like for like: a 450-word chunk is more likely to contain the evidence by chance, "
            "and four such chunks pass on about 1,800 words. The shipped 180 words keep every fragment intact and the context short; the table does not show that it is the best.")]

    # ---- 8.4 compression
    crows = []
    for k in ("1", "2", "4", "6", "8"):
        v = F.CMP[k]
        crows.append([k + (" (default)" if k == "4" else ""), f"{v['mean_ctx_words']:.0f}", f"{v['mean_ans_words']:.1f}", f"{v['token_reduction_pct']:.1f} %", f"{v['key_in_ctx']:.3f}", f"{v['key_in_ans']:.3f}", f"{v['evidence_in_ans']:.3f}"])
    bt = F.CMP["by_type_k4"]
    gh = F.CMP["k4_given_retrieval_hit"]
    b += [H2("8.4 Context compression and answer quality"),
          P("Objective 4 asks for context compression. The only compression in the product is the extractive answer step: the retrieved chunks are split into sentences, ranked by TF-IDF similarity to the question, and the best four are joined. "
            "\"Answer key\" is a short string of the gold answer (for example \"coffman\"); a question counts as answered when the key occurs in the text. This is the kind of trade-off that [1] measures for its LLM compressor."),
          TAB("Words passed on and answer-key recall against the number of retrieved chunks (72 questions)", ["Chunks retrieved", "Words in chunks", "Words in answer", "Words removed", "Key in chunks", "Key in answer", "Evidence sentence in answer"], crows,
              widths=[1.0, 0.8, 0.8, 0.8, 0.8, 0.8, 1.2], align=["c", "c", "c", "c", "c", "c", "c"], size=9.5),
          FIG(F.fig("fig_compression.png"), "Answer-key recall in the full retrieved chunks and in the extractive answer, and the percentage of words removed, against the number of chunks retrieved.", 4.6),
          P(f"At the default of four chunks the answer keeps {cm4['mean_ans_words']:.1f} of {cm4['mean_ctx_words']:.0f} words ({cm4['token_reduction_pct']:.1f} % fewer) and answer-key recall falls from {cm4['key_in_ctx']:.3f} to {cm4['key_in_ans']:.3f}, "
            f"a loss of {100 * (cm4['key_in_ctx'] - cm4['key_in_ans']):.1f} percentage points. This is far more aggressive than [1], which reports 38 to 58 % fewer tokens for a drop of one to two points of exact match with a language model as compressor on different data. "
            f"The extractive step always returns about 85 to 95 words, so the share removed grows with k while the key recall of the answer rises only from {F.CMP['1']['key_in_ans']:.3f} to {F.CMP['8']['key_in_ans']:.3f}. "
            f"When retrieval has found the evidence (57 of 72 questions), the answer contains the key in {F.pct(gh['key_in_ans'], 1)} of the cases and the evidence sentence in {F.pct(gh['evidence_in_ans'], 1)}. "
            "Every word of every answer occurs in the retrieved chunks (1.000), so the answers are grounded in the notes by construction. "
            f"Definition questions suffer most: the key is in the retrieved chunks for {bt['definition']['key_in_ctx']:.3f} of them but in the answer for only {bt['definition']['key_in_ans']:.3f} "
            f"(facts {bt['fact']['key_in_ctx']:.3f} to {bt['fact']['key_in_ans']:.3f}, reasoning {bt['reasoning']['key_in_ctx']:.3f} to {bt['reasoning']['key_in_ans']:.3f}), "
            "because the answerer prefers sentences that repeat the words of the question and the defining sentence often does not.")]

    # ---- 8.5 abstention
    sw = F.ABS["sweep"]
    keep = [s for s in sw if s["tau"] in (0.0, 0.10, 0.12, 0.15, 0.20, 0.30)]
    b += [H2("8.5 Answering only from the notes: abstention"),
          P("Objective 3 requires answers strictly from the uploaded material. The engine abstains only when no query word occurs in any chunk. "
            f"Of the {F.ABS['n_off_topic']} off-topic questions, {F.ABS['off_topic_answered_by_shipped']} still received an answer and {F.ABS['off_topic_refused_by_shipped']} were refused ({F.pct(F.ABS['off_topic_refused_by_shipped'] / F.ABS['n_off_topic'], 0)} correct abstention). "
            "\"What is the capital city of Australia?\" returned a sentence about a phone book organised by city because the word \"city\" occurs in the notes (top-1 score 0.36), whereas \"Who painted the Mona Lisa?\" was refused."),
          FIG(F.fig("fig_abstention.png"), "Left: top-1 cosine score of the 72 in-scope and 12 off-topic questions. Right: effect of a refusal threshold on the top-1 score.", 5.0),
          P(f"In-scope top-1 scores have a mean of {F.ABS['top1_score_in_scope']['mean']:.3f} (10th percentile {F.ABS['top1_score_in_scope']['p10']:.3f}, minimum {F.ABS['top1_score_in_scope']['min']:.3f}); "
            f"off-topic scores a mean of {F.ABS['top1_score_off_topic']['mean']:.3f} (maximum {F.ABS['top1_score_off_topic']['max']:.3f}). The distributions overlap only a little. The product has no threshold; the table is a suggestion, not an implemented feature."),
          TAB("Effect of a refusal threshold on the top-1 score", ["Threshold", "In-scope questions answered", "Off-topic questions refused"],
              [[f"{s['tau']:.2f}" + (" (shipped behaviour)" if s["tau"] == 0.0 else ""), F.pct(s["in_scope_answered"]), F.pct(s["off_topic_refused"])] for s in keep],
              widths=[1.8, 2.2, 2.2], align=["l", "c", "c"], size=10),
          P("A threshold of 0.12 to 0.15 would refuse 75 to 83 % of the off-topic questions at a cost of 1.4 to 4.2 % of the in-scope questions. The 12 off-topic questions are few and clearly outside the notes, "
            "so the threshold would have to be re-checked on questions that are only partly covered.")]

    # ---- 8.6 document analysis
    hf = F.DOCAN["heading_formats"]
    b += [H2("8.6 Document analysis"),
          P(f"Objective 1 asks the platform to extract subjects, units and topics. On the six corpus files the heading rules found all {int(round(F.DOCAN['unit_recall'] * 36))} of 36 \"Unit n:\" headings and the \"Subject:\" line of every file. "
            "Each file yields the maximum of twelve topics: seven headings plus five TF-IDF keywords such as \"data\", \"node\" and \"unit\"; the headings are the useful topics, the keywords are often generic. "
            "A synthetic five-unit syllabus written in seven common styles shows that only an Arabic numeral followed by a colon or hyphen is recognised."),
          TAB("Units found in a five-unit syllabus, by heading style", ["Heading style", "Units found", "Of"], [[k, str(v["units_found"]), str(v["of"])] for k, v in hf.items()],
              widths=[2.4, 1.2, 0.8], align=["l", "c", "c"], size=10),
          P("Roman numerals (\"UNIT-I\", \"Unit I:\"), \"Module 1:\" and numbered lists (\"1. Title\"), which Indian university syllabi use widely, are not recognised, so such a syllabus yields keywords but no unit list. "
            "Tests confirmed that plain text, DOCX paragraphs and PDFs with a text layer are extracted; text inside DOCX tables is lost; a scanned PDF returns no text and the upload reports that nothing readable was found; "
            "a corrupt PDF returns a short error string without stopping the request.")]

    # ---- 8.7 quiz
    qz = F.QUIZ
    aud = F.AUDIT["summary"]
    items = F.AUDIT["items"]

    def qrow(i):
        it = items[i]
        stem = it["question"].replace("Fill in the blank: ", "")
        if len(stem) > 110:
            stem = stem[:107] + "..."
        return [stem, it["answer"], it["label"] + (": " + it["note"] if it["note"] else "")]
    b += [H2("8.7 Quiz generation and the roadmap"),
          P(f"Quizzes were generated from each corpus file with 30 random seeds (five questions requested each time), 900 questions in all. Every request produced five questions (yield {qz['yield']:.3f}) and every question was structurally valid "
            f"({qz['structurally_valid']:.3f}); generation takes a median of {qz['gen_ms_median']} ms. Structure is not quality: another option also occurs as a word inside the question in {F.pct(qz['ambiguous_rate'])} of the questions, "
            f"and the answer term itself is still visible in the question in {F.pct(qz['answer_repeated_in_stem_rate'])} (only its first occurrence is blanked). A manual review of 30 questions (seed 0, one reviewer) judged "
            f"{aud['acceptable']} acceptable ({F.pct(aud['acceptable'] / aud['n'])}), {aud['ambiguous']} ambiguous and {aud['poor']} poor."),
          TAB("Three of the 30 reviewed questions (the blank is shown as _____)", ["Question", "Answer", "Review"], [qrow(14), qrow(8), qrow(27)],
              widths=[3.3, 0.9, 2.5], align=["l", "c", "l"], size=9),
          FIG(F.fig("fig_quiz_quality.png"), "Left: manual review of 30 questions. Right: automatic checks over 900 questions.", 4.6),
          P("The poor questions share three causes: sentences that begin mid-thought or contain formulas and code, terms repeated in the question, and blanks on very general words. "
            "The roadmap inherits the weakness, because the topic of a question is the blanked term; \"using\", \"used\", \"normal\" and \"elements\" appear on the roadmap screen as items to revise. "
            "The roadmap rule was tested at its boundaries: 0 of 1 and 49 of 100 correct give High, 1 of 2 and 79 of 100 give Medium, 4 of 5 and 80 of 100 give Low.")]

    # ---- 8.8 performance
    sc = F.SCALE
    srows = [[f"{s['chunks']:,}", f"{s['words']:,}", f"{s['index_build_ms']:.0f}", f"{s['retrieve_ms_median']:.1f} / {s['retrieve_ms_p95']:.1f}", f"{s['answer_ms_median']:.1f} / {s['answer_ms_p95']:.1f}"] for s in sc]
    A = F.API
    arows = [[lab, f"{A[k]['median_ms']:.1f}", f"{A[k]['p95_ms']:.1f}"] for lab, k in [("health", "health"), ("login (password hashing)", "login"), ("dashboard", "dashboard"), ("documents list", "documents_list"),
                                                                                    ("roadmap", "roadmap"), ("ask history", "history"), ("ask (retrieve + extractive answer)", "ask"),
                                                                                    ("quiz generate", "quiz_generate"), ("quiz submit", "quiz_submit")]]
    up = A["uploads"]
    b += [H2("8.8 Performance"),
          P("Two sets of timings were taken: the retriever in process for four index sizes (the corpus repeated one, two, four and eight times), and the running HTTP API on 127.0.0.1 (one user, 672 chunks, 30 calls per endpoint). "
            "The address `127.0.0.1` matters: on this machine the name `localhost` added about two seconds to every Python request."),
          TAB("In-process retrieval time against index size (72 queries, milliseconds)", ["Chunks", "Words", "Index build", "Retrieve median / 95th", "Retrieve + answer median / 95th"], srows,
              widths=[0.9, 1.1, 1.0, 1.7, 2.0], align=["c", "c", "c", "c", "c"], size=10),
          TAB("HTTP API latency on 127.0.0.1, 30 calls each (milliseconds)", ["Endpoint", "Median", "95th percentile"], arows, widths=[3.4, 1.2, 1.5], align=["l", "c", "c"], size=10),
          pairf("fig_scaling.png", "Retrieval and index-rebuild time against the number of chunks (log scale).",
                "fig_api_latency.png", "Median (bars) and 95th percentile (dots) of the API endpoints.", 3.2),
          P(f"Retrieval time grows about linearly with the number of chunks: 2.5 ms at 672 chunks and 19.4 ms at 5,376 (about 963,000 words); rebuilding the index after an upload or delete takes 263 ms and 974 ms. "
            f"A student with a few dozen documents is well inside this range. All endpoints except login answer in under 40 ms at the median; login takes about {A['login']['median_ms']:.0f} ms because the password hash is computed on purpose. "
            "`quiz submit` showed a 95th percentile of 1.0 s and 2.2 s in two runs, caused by one or two slow database commits in 30 calls; the cause was not isolated and the median stayed at 24 ms. "
            f"Uploading one corpus file (88 to 110 KB) with re-indexing took {min(u['ms'] for u in up):.0f} to {max(u['ms'] for u in up):.0f} ms in the second run and 119 to 811 ms in the first, a spread that follows the load of the shared machine. "
            "The Claude mode would add the network latency of a model call, which was not measured.")]

    # ---- 8.9 tests
    T = F.TESTS
    b += [H2("8.9 Test results"),
          P(f"The automated suite in `tests/` has {T['tests']} tests in six files and all {T['tests'] - T['failures'] - T['errors']} passed in {T['seconds']:.1f} s ({T['failures']} failures, {T['errors']} errors, {T['skipped']} skipped): "
            f"test_api {F.TEST_FILES['test_api.py']}, test_text_extraction {F.TEST_FILES['test_text_extraction.py']}, test_security {F.TEST_FILES['test_security.py']}, "
            f"test_rag_engine {F.TEST_FILES['test_rag_engine.py']} and test_quiz_generator {F.TEST_FILES['test_quiz_generator.py']}, on a temporary database. "
            f"The smoke script `scripts/smoke_test.py` ran {F.SMOKE_TOTAL} checks against a live server and all passed. The frontend builds (`tsc --noEmit` and `vite build`, 8.7 s), and a Playwright walk through every screen at 1440, 768 and 360 pixels in both themes "
            "reported no console errors, page errors, failed requests or horizontal overflow. Four behaviours are recorded by the tests as known limitations: two uploads with the same file name share one file on disk; "
            "text in DOCX tables is not read; headings such as \"UNIT-I\" are not recognised; the session cookie is HttpOnly and SameSite=Lax but not Secure. Chapter 7 describes the tests in detail.")]

    # ---- 8.10 base paper
    b += [H2("8.10 Comparison with the base paper"),
          P("The base paper [1] evaluates a pipeline for multi-hop question answering. Its data, models and measures differ from those of this project, so its numbers cannot be compared with the numbers in this chapter; only the direction of effects can."),
          TAB("SAC-RAG [1] and this project", ["Aspect", "SAC-RAG [1]", "This project"],
              [["Data", "HotpotQA [13], 2WikiMultiHopQA and MuSiQue, 1,000 questions each", f"Six-subject notes corpus, {c['words']:,} words, {c['questions']} hand-written questions"],
               ["Retrieval", "Fact: BM25 + dense with BGE reranker; definition: dense; reasoning: sub-question decomposition", f"TF-IDF cosine (Hit@4 {F.hit(SHIPPED, 4):.3f}); BM25 + dense only as a reference (Hit@4 {F.hit(HY, 4):.3f})"],
               ["Question type", "LLM classifier, 92.0 % accuracy on 300 labelled questions", "Not implemented; typed by hand for analysis only"],
               ["Compression", "LLM extracts evidence; 38 to 58 % fewer tokens for 1 to 2 points of exact match", f"Extractive; {cm4['token_reduction_pct']:.1f} % fewer words, answer-key recall {cm4['key_in_ctx']:.3f} to {cm4['key_in_ans']:.3f}"],
               ["Generator, measures", "gpt-5-mini; exact match, F1, Recall@10, tokens", "None in the measured mode (Claude mode not measured); Hit@k, MRR@10, answer-key recall"],
               ["Latency", "About 27.8 s against 9.6 s per question (extra LLM calls)", f"{A['ask']['median_ms']:.0f} ms median per question, no model call"]],
              widths=[1.1, 2.8, 2.8], align=["l", "l", "l"], size=9),
          P(f"Three patterns agree in direction with [1]. Combining a lexical and a dense score beats either alone (Hit@4 {F.hit(HY, 4):.3f} against {F.hit(BM, 4):.3f} for BM25 and {F.hit(DN, 4):.3f} for dense). "
            "Compression trades answer quality for fewer words, and here the loss is larger because the compressor is extractive and unaware of the answer. And the paper reports a latency cost for its extra LLM calls, which the offline mode of this project does not have, "
            "and it has no quality gain from them either. The paper's Recall@10 (0.787 to 0.880 on HotpotQA) counts gold documents among ten retrieved, whereas Hit@10 here asks whether one fragment appears in ten chunks, so the two must not be read against each other. "
            "**What is not achieved.** The question classifier, the type-specific retrieval and the LLM compression module of [1] are not implemented; the project adopts the retrieve, compress and generate structure and the evaluation vocabulary, not the method. "
            "Chapter 9 states this as a finding and Chapter 10 describes how the gap could be closed.")]

    # ---- 8.11 samples
    b += [H2("8.11 Sample inputs and outputs"),
          P("Real outputs of the shipped engine (offline extractive mode) on the corpus, shortened to the first sentences. The score is the cosine similarity of the best chunk."),
          TAB("Sample questions and the engine's answers", ["Question", "Answer (start)", "Top source (score)", "Evidence in top 4?"],
              [["Which stack operation removes the most recently added element?", "\"Additionally, a peek operation can ... return the value of the last element added ... Push ... and Pop, which removes the mo...\"", "01_Data_Structures, passage 0 (0.33)", "Yes, rank 1"],
               ["Which layer of the TCP/IP suite does TCP belong to?", "\"Therefore, the entire suite is commonly referred to as TCP/IP. ... TCP, which is part of the transport layer of the TCP/IP suite.\"", "04_Computer_Networks, passage 0 (0.32)", "Yes, rank 1"],
               ["Why is regularization used to prevent overfitting?", "\"Regularization is a technique used to prevent overfitting by adding a penalty term to the loss function ...\"", "05_Machine_Learning, passage 14 (0.28)", "Yes, rank 1"],
               ["What is a binary search tree?", "\"The binary search tree and B-tree data structures are based on binary search. Balanced binary search trees ...\"", "01_Data_Structures, passage 57 (0.50)", "Yes, not rank 1"],
               ["Who painted the Mona Lisa?", "\"No relevant content was found in your uploaded documents for this question. ...\"", "none", "Correct refusal"]],
              widths=[1.7, 2.9, 1.3, 0.9], align=["l", "l", "l", "l"], size=9),
          P("The first three answers contain the key but are stitched from neighbouring sentences; the fourth starts with a sentence about binary search and reaches the definition only later. "
            "The answer length is nearly constant at about 90 words, more than a short factual question needs.")]

    # ---- 8.12 success and failure
    fr = F.RET[SHIPPED]["first_rank"]
    bmr = F.RET[BM]["first_rank"]
    hyr = F.RET[HY]["first_rank"]

    def rk(x):
        return "not in top 10" if not x else str(x)
    from eval_questions import QUESTIONS
    cases = [(9, "The question says \"slow\", the notes say \"degenerate\"; the top chunks share only the words \"binary search tree\" and \"linked list\"."),
             (41, "\"Routing\" occurs in many chunks and the lead sentence sits in passage 63, while passages 67 and 64 repeat the word more often. No retriever in the table finds it in the top ten."),
             (57, "The evidence is an analogy sentence (\"get stuck in some hole\"); the words \"gradient descent\" match the passages that define the method. No retriever in the table finds it in the top ten."),
             (16, "Passage 0 holds the definition of a deadlock; passages 7 and 4 about avoidance and recovery repeat \"deadlock\" more often (0.48 and 0.42), so the answer on the Ask screen describes avoidance.")]
    miss = [i for i, x in enumerate(fr) if not x or x > 4]
    frows = [[QUESTIONS[i][2], QUESTIONS[i][1], rk(fr[i]), rk(bmr[i]), rk(hyr[i]), why] for i, why in cases]
    b += [H2("8.12 Success and failure analysis"),
          P(f"**Where it works.** The shipped retriever finds the evidence in the top four chunks for {72 - len(miss)} of 72 questions. It is reliable when the question repeats distinctive words of the evidence, such as names, years and unusual terms "
            "(who coined the acronym ACID, write-ahead logging, the laboratory that developed the support vector machine and the year the OSI model was published all rank the evidence first). "
            f"**Where it fails.** {len(miss)} questions are missed at four chunks; four real misses show the typical causes."),
          TAB("Four real failures of the shipped retriever", ["Question", "Type", "Rank TF-IDF", "Rank BM25", "Rank BM25 + dense", "Cause"], frows,
              widths=[1.5, 0.7, 0.6, 0.6, 0.7, 2.6], align=["l", "c", "c", "c", "c", "l"], size=8.5),
          P("Lexical mismatch is the main limit of any keyword retriever and is the case dense embeddings are meant to repair; the hybrid repairs some cases (\"What does each node in a basic linked list contain?\" moves from rank 7 to rank 2) but not the first one in the table. "
            "Frequency effects hit definition questions, and chunk-level scoring gives no weight to the first sentence of a section, which usually defines the concept. "
            "A fourth failure lies in the answer step: even when the right chunk is retrieved, the answer omits the key for about one question in six. "
            "Other components fail too: a DOCX table is silently dropped, a syllabus with \"UNIT-I\" headings yields no unit list, a quiz may contain a fragment or a formula, a roadmap may list \"using\" as a topic, and an off-topic question that shares a word with the notes is answered.")]

    # ---- 8.13 limits
    b += [H2("8.13 Limitations of the evaluation"),
          B("**Corpus.** Wikipedia articles are well written and self-contained; lecture notes, scanned slides and mixed-language material are harder. The 36 articles are in English and cover six computer-science subjects.",
            "**Questions.** Seventy-two questions written by the project team after reading the articles are few and favour lexical overlap; the intervals in Section 8.3 are wide.",
            "**Measures.** Hit@k and answer-key recall are proxies for answer quality. No human judged the answers, and no exact match or F1 against reference answers was computed.",
            "**Claude mode.** No API key was available, so the generation mode that uses a language model was not measured.",
            "**Screens and load.** The quiz answers in the screenshots were scripted. One user was simulated; concurrent users and multi-process deployment were not tested, since the quiz state and the index cache live in the memory of one process.",
            "**Dense reference.** The dense and hybrid retrievers are experiments run outside the product with a quantised model; their numbers show potential, not delivered behaviour.")]

    # ---- 8.14 objectives
    b += [H2("8.14 Objectives against outcomes"),
          TAB("The six objectives of the batch against what was measured", ["No.", "Objective", "Status", "Evidence"], objective_rows(),
              widths=[0.4, 2.2, 0.9, 3.2], align=["c", "l", "c", "l"], size=9),
          P("One objective is met in the offline mode, four are met in part and one (semantic embeddings) is not met. The platform works end to end for a student on a laptop and each component was measured, "
            "but the semantic retrieval and the semantic compression of the title and of the base paper are the largest gap between what was planned and what was built.")]
    return b
