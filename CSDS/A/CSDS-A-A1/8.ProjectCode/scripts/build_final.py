"""Build 16.Final_PPT.pptx from D:\\abstracts\\Templates\\Final_PPT.pptx (28 slides)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deckkit import fill, put_picture, set_notes, set_paras, set_table, shape, table_size  # noqa: E402
from doc_common import BATCH, CHARTS, COLLEGE, DIAG, EXP, GUIDE, GUIDE_DESIG, PRODUCT, REFERENCES, SHOTS, STUDENTS, TITLE, YEAR  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.util import Emu  # noqa: E402

SRC = r"D:\abstracts\Templates\Final_PPT.pptx"
OUT = BATCH / "16.Final_PPT.pptx"
FOOT = "Dept. of CSE (Data Science)  |  Batch A1  |  Final Review"


def px(v):
    return Emu(int(v * 9525))


def table(s, sid, rows, widths, max_pt=16, h=430, w=1180):
    sz = table_size(rows, w, h, widths, max_pt, 9)
    tshape = [sh for sh in s.shapes if sh.has_table][0]
    set_table(tshape, rows, sz, widths=widths, header_size=sz)


def two_pics(s, left, right, cap_l, cap_r, ids_remove=(7, 9), cap_ids=(8, 10), box_h=352, top=182):
    put_picture(s, left, (43, top, 576, box_h), remove_ids=(ids_remove[0],), name=cap_l)
    put_picture(s, right, (657, top, 576, box_h), remove_ids=(ids_remove[1],), name=cap_r)
    set_paras(shape(s, cap_ids[0]), cap_l)
    set_paras(shape(s, cap_ids[1]), cap_r)
    for cid in cap_ids:
        shape(s, cid).top = px(554)


def build():
    prs = Presentation(SRC)
    S = list(prs.slides)
    cp = prs.core_properties
    cp.title, cp.subject, cp.author, cp.keywords = f"{PRODUCT}: Final Review", TITLE, "Batch A1", "health insurance, RAG, LLM, question answering"
    cp.category = cp.comments = cp.content_status = ""
    cp.last_modified_by = "Batch A1"
    for s in S[1:]:
        for sh in s.shapes:
            if sh.has_text_frame and sh.text_frame.text.startswith("Dept. of CSE"):
                set_paras(sh, FOOT)

    # 1 title
    s = S[0]
    set_paras(shape(s, 4), f"{PRODUCT}: {TITLE}")
    set_paras(shape(s, 5), "Final Review")
    set_paras(shape(s, 6), "Team Details : Batch A1")
    set_paras(shape(s, 7), [f"{r}   {n}" for n, r in STUDENTS], 16)
    set_paras(shape(s, 8), ["Under the Esteemed Guidance of", GUIDE, f"{GUIDE_DESIG}, Department of CSE (Data Science)"])
    set_paras(shape(s, 9), f"DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING (DATA SCIENCE)  \u00b7  Academic Year {YEAR}", 12)
    set_notes(s, "Final review of PolicyLens: an AI health-insurance assistant using retrieval-augmented generation and a large language model.")

    # 2 contents
    s = S[1]
    fill(s, 7, ["Abstract", "Base Paper & Literature Survey", "Research Gap & Problem Statement", "Objectives", "Proposed System & Architecture", "Methodology & Pipeline",
                "Design & Implementation", "Results, Testing & Comparison", "Output Screens", "Conclusion & Future Scope", "References"], 20, bullet=True)

    # 3 abstract
    s = S[2]
    fill(s, 7, ["Health insurance policies are long and technical, so users struggle to find coverage, exclusions, waiting periods and claim steps; agents are slow and general chatbots are not grounded in the user's own policy.",
                "PolicyLens combines retrieval-augmented generation with Google Gemini: the policy is parsed into numbered clauses; a hybrid retriever finds the relevant ones; the model answers from those clauses only, with citations.",
                "A Policy Card lists key terms with their clause and page; an independent NLI model scores each answer's support; the assistant says \"not covered in this policy\" when the wording is silent.",
                "Claim Copilot adds calculated eligibility pre-checks, a verdict, a document checklist and a cost estimate; plans can be compared; English, Hindi and Telugu are supported.",
                "Evaluation on 4 real wordings: relevant clause in the top 5 for 51/51 questions, 51/51 answers correct and cited, 6/6 out-of-scope declined, 14/14 claim verdicts, mean faithfulness 87.0, median answer 4.3 s.",
                "Keywords: health insurance, RAG, LLM, question answering, faithfulness, claim guidance."], 18, bullet=True)
    set_notes(s, "Abstract: problem, approach, application, and the headline measurements.")

    # 4 base paper
    s = S[3]
    fill(s, 7, [REFERENCES[0],
                "Task: multi-document summarisation of Turkish court rulings; 2,000 consumer-rights rulings scraped from a public site.",
                "Method: TF-IDF and TextRank select important sentences; LED, Long-T5, BART-large and GPT-3.5 Turbo generate abstractive summaries from them.",
                "Reported results: TF-IDF content F1 0.47; GPT-3.5 Turbo ROUGE-1 55%, ROUGE-2 35%, ROUGE-L 42%, ROUGE-Sum 44%.",
                "Our reading: overlap with reference summaries does not show whether statements are supported; no citations; no question answering or guidance. We adopt select-then-generate and change task, domain and evaluation."], 18, bullet=True)
    set_notes(s, "The base paper summarises legal rulings; PolicyLens applies its select-then-generate idea to cited question answering over insurance wordings.")

    # 5 literature survey
    s = S[4]
    rows = [["Author / Year", "Methodology", "Dataset", "Key Results", "Limitations"],
            ["Albayati and Findik, 2025 (base) [1]", "TF-IDF/TextRank, then LED, Long-T5, BART, GPT-3.5 Turbo", "2,000 Turkish court rulings", "GPT-3.5 Turbo ROUGE-1 55%, ROUGE-2 35%, ROUGE-L 42%", "Summaries only; no citations or QA"],
            ["Beauchemin et al., 2024 [2]", "RAG with GPT-4o", "Quebec auto-insurance corpus; 82 expert answers", "Better on average; 5-13% false statements", "Auto insurance; one model"],
            ["Maharjan and Yadav, 2026 [6]", "Plain LLM vs basic RAG vs RAG + cross-encoder", "Public-health policy documents", "Faithfulness 0.347 / 0.621 / 0.797", "Not insurance wordings"],
            ["Knollmeyer et al., 2025 [5]", "Knowledge-graph-enhanced RAG", "Manufacturing documents", "Not read", "Different domain"],
            ["Multi-strategy RAG, 2026 [3]; Iran chatbot, 2023 [4]", "RAG for medical-insurance QA; service chatbot", "Not retrieved", "Not retrieved", "Listed in batch survey only"]]
    table(s, 6, rows, [0.2, 0.25, 0.17, 0.22, 0.16], 14, 440)
    set_notes(s, "[1], [2] and [6] were read in detail. [3] and [4] could not be retrieved and [5]'s results were not read, so no results are claimed for them.")

    # 6 research gap
    s = S[5]
    rows = [["Author / Paper", "Research Gap"],
            ["Base paper [1]", "Summarisation of rulings: no question answering, no citations, no per-statement support, no guidance"],
            ["Beauchemin et al. [2]", "RAG still produced 5-13% false statements; no per-answer support score; one insurance line"],
            ["Maharjan and Yadav [6]", "Shows re-ranking helps and segmentation is a bottleneck; other domain, no claim guidance"],
            ["General chatbots and websites", "Answer from training data or compare premiums; not grounded in the user's policy; no claim pre-check"],
            ["All reviewed work", "No system joins attribute extraction, clause-grounded cited answers, abstention, claim guidance and a repeatable evaluation on several real wordings"]]
    table(s, 7, rows, [0.26, 0.74], 17, 440)
    set_notes(s, "The gap is grounded, cited, scored answers plus claim guidance, with measured evidence on real wordings.")

    # 7 problem statement
    s = S[6]
    fill(s, 7, ["Health insurance policies are long and technical, so users cannot easily find coverage, exclusions and conditions.",
                "Users depend on agents and helplines that give slow, generic and inconsistent answers.",
                "General chatbots may produce answers that are not supported by the user's actual policy.",
                "Claim filing lacks guidance on eligibility and required documents, leading to delays and rejections.",
                "Need: an assistant that answers strictly from the user's own policy, cites the supporting clauses and guides claims step by step."], 20, bullet=True)

    # 8 objectives
    s = S[7]
    fill(s, 7, ["Extract key policy attributes automatically from uploaded health insurance documents.",
                "Build a RAG pipeline that retrieves the policy clauses relevant to each user question.",
                "Generate plain-language answers with an LLM, grounded in and citing the retrieved clauses.",
                "Provide guided claim support with eligibility pre-checks, evidence checklists and procedural steps.",
                "Summarise risks, exclusions and cost-coverage trade-offs to support plan comparison.",
                "Evaluate the assistant for answer accuracy, faithfulness and response time."], 20, bullet=True)

    # 9 proposed system
    s = S[8]
    fill(s, 7, ["1. Upload - a policy wording PDF (or one of four samples); scans, encrypted and oversize files are refused.",
                "2. Parse and segment - numbered clauses with pages and highlight boxes; exclusion codes become clauses.",
                "3. Index - BM25 and MiniLM embeddings in ChromaDB.",
                "4. Policy Card and risks - one Gemini call, every value verified against its quote; rule and AI risks.",
                "5. Ask - hybrid retrieval, cited answer, faithfulness score; \"not covered in this policy\" when silent.",
                "6. Claim Copilot - calculated pre-checks, verdict, checklist, steps, estimate.",
                "7. Compare, translate, review - two plans side by side; English, Hindi, Telugu; dashboard."], 19, bullet=False)

    # 10 architecture
    s = S[9]
    put_picture(s, DIAG / "01_system_architecture.png", (240, 178, 800, 424), remove_ids=(7,), name="System architecture")
    set_paras(shape(s, 8), "Layered architecture: browser, React web app, FastAPI backend with retrieval and answering services, local models, storage, Gemini API")

    # 11 methodology
    s = S[10]
    put_picture(s, DIAG / "02_high_level_workflow.png", (57, 178, 1161, 424), remove_ids=(7,), name="High-level workflow")
    set_paras(shape(s, 8), "End-to-end workflow: upload, parse, segment, index, Policy Card, risks, ask, Claim Copilot, compare, review")

    # 12 dataset, features, model
    s = S[11]
    set_paras(shape(s, 4), "Dataset, Features & Models")
    fill(s, 7, ["Data: four public policy wordings (Star Health, HDFC ERGO, Niva Bupa, Care Health): 166 pages, 73,001 words, 801 clauses; no personal data.",
                "Evaluation set (hand-written): 57 questions (51 answerable, 6 out-of-scope), 5 Hindi/Telugu, 14 claim scenarios, 52 Policy Card values. All of it is test data; nothing is trained.",
                "Features: clause text with heading path; BM25 terms with insurance synonyms; 384-d MiniLM embeddings.",
                "Models (pre-trained, not fine-tuned): Gemini for generation; all-MiniLM-L6-v2; ms-marco-MiniLM-L6-v2 cross-encoder; nli-deberta-v3-xsmall.",
                "Settings: 30 candidates per retriever, RRF k 60, re-rank pool 20 + 8, top 7 clauses, abstain if re-rank < 0.004 and BM25 < 9.0, temperature 0.2.",
                "Why no training: the task is reading, not predicting; no labelled public set; wordings change every year."], 18, bullet=True)
    set_notes(s, "There is no train/validation/test split because no model is trained; the whole evaluation set is test data.")

    # 13 decision workflow
    s = S[12]
    put_picture(s, DIAG / "10_algorithm_flowchart.png", (300, 178, 680, 424), remove_ids=(7,), name="Algorithm flowchart")
    set_paras(shape(s, 8), "Core algorithm answer_question(): translate, retrieve, fuse, re-rank, abstain or generate, filter citations, score faithfulness")

    # 14 user-system interaction
    s = S[13]
    set_paras(shape(s, 4), "User\u2013System Interaction")
    put_picture(s, DIAG / "09_sequence_diagram.png", (270, 178, 740, 424), remove_ids=(7,), name="Sequence diagram")
    set_paras(shape(s, 8), "Sequence: ask a question, receive a cited answer with a faithfulness score, open the source page")

    # 15 database
    s = S[14]
    put_picture(s, DIAG / "06_er_diagram.png", (250, 178, 780, 424), remove_ids=(7,), name="ER diagram")
    set_paras(shape(s, 8), "Entity\u2013relationship diagram (12 SQLite tables)")

    # 16 implementation highlights
    s = S[15]
    rows = [["Module", "Implementation"],
            ["Parser + segmenter", "PyMuPDF lines; header/footer removal; column order; clause starts and IRDAI exclusion codes; 12-380 word chunks with highlight boxes"],
            ["Retrieval", "BM25 Okapi (k1 1.4, b 0.7) + MiniLM/ChromaDB; Reciprocal Rank Fusion (k 60); cross-encoder re-rank; top 7"],
            ["Answerer + faithfulness", "Tagged clauses to Gemini with a JSON schema; uncited tags dropped; NLI entailment + number check -> score 0-100"],
            ["Claim Copilot", "Calculated waiting-period, co-payment, sub-limit checks and estimate; Gemini plan; a failed waiting period is never \"covered\""],
            ["Gemini client", "JSON schema, three-model fallback chain, 10-minute cool-down, pacing, disk cache, usage log"],
            ["Web app + security", "React 18 + FastAPI; bcrypt, JWT 24 h, owner-only data, upload validation; 42 routes; 25 backend tests"]]
    table(s, 17, rows, [0.2, 0.8], 17, 440)

    # 17 results
    s = S[16]
    set_paras(shape(s, 4), "Results \u2013 Evaluation (run eval-20260922-0027)")
    rows = [["Measure", "PolicyLens", "Note"],
            ["Relevant clause in top 5", "100% (51/51)", "BM25 alone 100%, dense alone 80.4%"],
            ["Relevant clause ranked first", "80.4%", "BM25 64.7%, hybrid 68.6%"],
            ["Answer accuracy / citation accuracy", "100% / 100% (51/51)", "all key facts; right clause or page"],
            ["Faithfulness mean / median", "87.0 / 91.7", "45 well, 8 partly, 3 weakly supported"],
            ["Out-of-scope declined", "6/6, 0 false", "51 answerable never declined"],
            ["Claim verdicts / card values", "14/14 / 51/52", "98.1% card accuracy"],
            ["Answer time median / p95", "4.3 s / 18.2 s", "live Gemini, smallest model"]]
    table(s, 18, rows, [0.4, 0.25, 0.35], 18, 420)
    set_paras(shape(s, 8), "4 real wordings, 57 questions, 14 claim scenarios, 52 card values; held-out test only; small set partly tuned on itself; model: gemini-3.5-flash-lite.")
    set_notes(s, "Nothing is trained, so there is no accuracy of a trained model; these are measured retrieval, answer, citation, faithfulness and verdict results.")

    # 18 confusion matrix + faithfulness
    s = S[17]
    set_paras(shape(s, 4), "Claim Verdicts & Faithfulness")
    two_pics(s, CHARTS / "claims_confusion.png", EXP / "faithfulness_distribution.png", "Claim Copilot confusion matrix: 14 of 14 verdicts correct", "Faithfulness of 56 answers: 45 well, 8 partly, 3 weakly supported")
    set_notes(s, "The confusion matrix of the four claim verdicts and the distribution of the faithfulness score.")

    # 19 threshold and parameter analysis
    s = S[18]
    set_paras(shape(s, 4), "Threshold & Parameter Analysis")
    two_pics(s, CHARTS / "abstention_scatter.png", EXP / "retrieval_ablation.png", "Abstention rule: only the pair of scores separates the 6 out-of-scope questions", "Retrieval ablation: re-ranking lifts hit@1 from 0.686 to 0.804")
    set_notes(s, "Scores measured through the live API for all 57 questions: no answerable question is below both floors, all six out-of-scope questions are.")

    # 20 performance & testing
    s = S[19]
    rows = [["Measurement", "Result"],
            ["Retrieval time (median)", "BM25 1.1 ms; dense 10.7 ms; hybrid 11.0 ms; hybrid + re-rank 879 ms"],
            ["Answer time", "median 4.3 s, p95 18.2 s; stages: retrieval 0.86 s, Gemini 2.5 s, faithfulness 0.83 s"],
            ["Claim check", "mean 13.8 s on four live calls; policy parsing 3.2-4.2 s"],
            ["Automated tests", "25 passed, 0 failed (auth 6, faithfulness 3, parser 3, policy flow 7, units 6)"],
            ["Web build", "strict TypeScript + Vite production build succeed"],
            ["Live demo (15 Oct 2026)", "cited answer 6.2 s; abstained question 1.7 s; Hindi answer 10.0 s; claim check 14.2 s"]]
    table(s, 21, rows, [0.22, 0.78], 18, 430)
    set_notes(s, "Not measured: concurrent-user load, memory use, other hardware; user-acceptance testing was not performed.")

    # 21 comparison
    s = S[20]
    rows = [["System", "Data", "Method", "Support for statements", "Reported / measured", "Extras"],
            ["Base paper [1]", "2,000 Turkish court rulings", "TF-IDF/TextRank + LED, Long-T5, BART, GPT-3.5 Turbo", "Not measured; no citations", "ROUGE-1 55%, ROUGE-2 35%, ROUGE-L 42%", "-"],
            ["RAG study [6]", "Public-health policy documents", "Mistral-7B + MiniLM + cross-encoder re-rank", "Faithfulness measure", "Faithfulness 0.347 / 0.621 / 0.797", "-"],
            ["PolicyLens", "4 English health-insurance wordings (801 clauses)", "BM25 + dense + RRF + cross-encoder; Gemini JSON schema", "Clause + page citations; NLI score 0-100; abstention", "hit@5 100%, answers 51/51, citations 100%, faithfulness 87.0", "Policy Card, Claim Copilot, compare, 3 languages"]]
    table(s, 22, rows, [0.12, 0.17, 0.2, 0.2, 0.18, 0.13], 13, 400)
    set_paras(shape(s, 8), "Different tasks, data, languages and metrics: no numeric head-to-head is possible, so the comparison is of approach. Faithfulness values are on different scales.")

    # 22-24 outputs
    s = S[21]
    set_paras(shape(s, 4), "Output \u2013 Cited Answer and Source Page")
    two_pics(s, SHOTS / "11_chat_answer.png", SHOTS / "12_chat_citation.png", "Answer with two sources, faithfulness 88 and follow-ups", "A source chip opens the original page with the clause outlined")
    s = S[22]
    set_paras(shape(s, 4), "Output \u2013 Claim Copilot")
    two_pics(s, SHOTS / "16_claim_result_partly.png", SHOTS / "17_claim_result_not_covered.png", "Knee replacement, 36 months of cover: partly covered (20% co-payment)", "Cover from April 2026: not covered, waiting period incomplete")
    s = S[23]
    set_paras(shape(s, 4), "Output \u2013 Policy Card and Plan Comparison")
    two_pics(s, SHOTS / "06_policy_card.png", SHOTS / "19_compare_result.png", "Policy Card with values linked to clause and page", "Star Health against HDFC ERGO: overview and choose-A / choose-B")

    # 25 conclusion
    s = S[24]
    fill(s, 7, ["Built PolicyLens: grounded, cited, scored health-insurance answers, a verified Policy Card, claim guidance and plan comparison.",
                "Relevant clause in the top 5 for 51/51 questions; 51/51 answers correct and cited; 6/6 out-of-scope declined with no false abstentions; 14/14 claim verdicts; 51/52 card values.",
                "Mean faithfulness 87.0; median answer time 4.3 s; hybrid + re-rank beats BM25 alone and dense alone at the top of the list.",
                "25 backend tests pass; the web build succeeds; every screen was captured from the running application.",
                "Limits: small set partly tuned on itself; smallest Gemini model; heuristic faithfulness; mixed-script Telugu line; no user study; no numeric comparison with the base paper."], 19, bullet=True)

    # 26 future scope
    s = S[25]
    fill(s, 7, ["Evaluate on a fresh, larger question set from unseen wordings and with the larger Gemini models.",
                "Plan-variant selection on the Policy Card; OCR for scanned policies.",
                "Better faithfulness scoring and automatic checks of translation quality.",
                "Claim document upload with checklist verification and deadline reminders; renewal comparison.",
                "Server deployment: hosted database and vector store, HTTPS, rate limiting, load testing and a user study."], 20, bullet=True)

    # 27 references
    s = S[26]
    fill(s, 7, [f"[{i}] {r}" for i, r in enumerate(REFERENCES, 1)], 14, min_pt=7.5, bullet=True, gap_pt=2)

    set_notes(S[27], "Thank you. Questions are welcome.")
    prs.save(OUT)
    print("saved", OUT, len(prs.slides._sldIdLst), "slides")


if __name__ == "__main__":
    build()
