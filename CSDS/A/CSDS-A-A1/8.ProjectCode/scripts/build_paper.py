"""Build 19.IEEE_Paper.docx: a six-page, two-column IEEE conference paper on PolicyLens.

    python scripts/build_paper.py        then   python scripts/paper_finish.py   (page count + PDF through Word)

Every number comes from docs/REPORT_FACTS.md (via doc_common.py) and the evaluation run eval-20260922-0027.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paper_kit as K  # noqa: E402
from doc_common import BATCH, ROOT  # noqa: E402

OUT = BATCH / "19.IEEE_Paper.docx"
PAPER = ROOT / "docs" / "paper"
CHARTS = ROOT / "docs" / "charts"

K.TITLE = "PolicyLens: Clause-Grounded Health-Insurance Question Answering and Claim Guidance with Hybrid Retrieval and an LLM"
K.ABSTRACT = (
    "Health-insurance policy wordings are long and technical, so policyholders often learn what is excluded only when a claim is "
    "reduced. General chatbots answer from training data rather than from the user's own policy and can state coverage that the "
    "wording does not contain. This paper presents PolicyLens, an assistant that answers strictly from an uploaded wording. The "
    "wording is parsed into numbered clauses with page positions; a hybrid retriever that combines BM25, MiniLM embeddings, "
    "Reciprocal Rank Fusion and a cross-encoder selects the relevant clauses; a large language model writes a cited answer in "
    "English, Hindi or Telugu; and an independent natural-language-inference model scores how well each answer is supported. A "
    "two-score rule makes the assistant decline when the wording is silent, and calculated rules guide claims. On a hand-built set "
    "from four real wordings the relevant clause was in the top five for 51 of 51 questions, all 51 answers were correct and cited, "
    "six of six out-of-scope questions were declined, and the mean faithfulness score was 87.0. The set is small and partly tuned, "
    "and no user study was carried out."
)
K.KEYWORDS = ("claim guidance, faithfulness, health insurance, hybrid retrieval, large language model, question answering, "
              "retrieval-augmented generation")


def build():
    P = K.Paper()
    P.front()
    P.abstract()

    # ---------------------------------------------------------------- I
    P.h1("I. Introduction")
    P.para("Health insurance is the main protection most families have against hospital costs, and each product is defined by a policy "
           "wording: a document of twenty to sixty pages that states what is covered, what is excluded, how long a policyholder must wait "
           "before certain treatments are covered, what share of a bill the policyholder pays and how a claim is made. The wording is "
           "legally binding but written in dense technical language, so the conditions that matter most, such as waiting periods, "
           "sub-limits and co-payments, are easily missed until a claim is reduced or rejected.")
    P.para("Today a policyholder reads the wording alone, asks an agent or a helpline, or uses a comparison site that compares premiums "
           "and headline benefits. Agents are slow and inconsistent, and comparison sites do not explain exclusions or claim "
           "conditions. A general-purpose chatbot is fluent but answers from broad training data, not from the user's policy, and large "
           "language models are known to produce plausible statements that the source does not support [16]. The cost is real: in a study "
           "of retrieval-augmented GPT-4o answering Quebec car-insurance questions, between 5% and 13% of the answers contained a false "
           "statement that could mislead a customer [2]. The base paper [1] shows how long legal text can be handled by selecting the "
           "important passages first and generating from them, but it summarises Turkish court rulings; it does not answer questions, "
           "cite passages or guide claims.")
    P.para("This paper presents PolicyLens, an assistant that answers questions strictly from the user's own policy wording, shows the "
           "clause and page behind every statement, measures how well each answer is supported, and guides claims. Its contributions are:", after=2)
    P.numbered([
        "clause-aware parsing and segmentation of insurance wordings, so that every citation can be highlighted on the original page, and a Policy Card whose values are verified against their quotes;",
        "a measured hybrid retriever (BM25, dense embeddings, Reciprocal Rank Fusion, cross-encoder) and grounded generation in which citations to unretrieved clauses are removed;",
        "an independent natural-language-inference faithfulness score and a two-score abstention rule that declines questions the wording does not cover;",
        "Claim Copilot, whose waiting-period, co-payment and estimate rules are calculated and cannot be overruled by the model, and an offline evaluation on four real wordings.",
    ])
    P.para("Section II reviews related work, Section III describes the method, Section IV reports the results and Section V concludes.", before=2)
    P.h2("A. System Hardware")
    P.para("All measurements were taken on one desktop with a 12th-generation Intel Core i5-12500 (6 cores, 12 threads), 15.7 GB of "
           "memory and no discrete graphics card, running Windows 11 and Python 3.11.9. The three local models run on the CPU. Language "
           "generation uses the Google Gemini API on its free tier.")
    P.h2("B. Software Requirements")
    P.para("The back end is FastAPI with Pydantic 2, SQLAlchemy 2 over SQLite, PyJWT and bcrypt; PDFs are read with PyMuPDF; keyword search "
           "uses rank-bm25 and vectors are stored in ChromaDB. The local models are all-MiniLM-L6-v2, ms-marco-MiniLM-L6-v2 and "
           "nli-deberta-v3-xsmall, run through sentence-transformers and PyTorch. The front end is React 18 with TypeScript, Vite, "
           "Tailwind CSS, TanStack Query and Recharts. Tests use pytest.")

    # ---------------------------------------------------------------- II
    P.h1("II. Literature Survey")
    P.para("**Base paper.** Albayati and Findik [1] address the lack of tools for summarising Turkish legal documents. They collected "
           "2,000 Turkish consumer-rights court rulings from a public site and cleaned them to keep the decisions and arguments. Their "
           "hybrid pipeline first selects important sentences with TF-IDF and TextRank, then generates abstractive summaries with LED, "
           "Long-T5, BART-large and GPT-3.5 Turbo from the extractive output. The extractive stage is scored with cosine similarity and "
           "content precision, recall and F1 (0.47 for TF-IDF with keywords) and the generators with ROUGE [19]; GPT-3.5 Turbo was best "
           "with ROUGE-1 55%, ROUGE-2 35%, ROUGE-L 42% and ROUGE-Sum 44%. The idea that carries over is select-then-generate. What does "
           "not carry over is the task and the evaluation: overlap with a reference summary does not show whether a statement is "
           "supported by the source, and there are no citations back to passages.")
    P.para("**Question answering over insurance and policy text.** Beauchemin et al. [2] built a Quebec car-insurance corpus and 82 "
           "expert answers, and found that retrieval improved GPT-4o on average but left 5-13% of answers with a false statement. "
           "Maharjan and Yadav [6] compared a plain LLM, basic RAG and RAG with cross-encoder re-ranking on public-health policy documents "
           "with Mistral-7B and the same MiniLM embeddings as ours: faithfulness rose from 0.347 to 0.621 and 0.797, and document "
           "segmentation remained a bottleneck. A multi-strategy RAG system for medical-insurance questions [3] and a chatbot for the "
           "Iran Health Insurance Organization [4] are listed in our batch survey; we could not retrieve their text and so state no "
           "result for them. Knollmeyer et al. [5] study knowledge-graph-enhanced RAG for manufacturing documents.")
    P.para("**Retrieval, ranking and checking.** Retrieval-augmented generation [7] conditions a generator on retrieved passages. BM25 [8] "
           "is the standard keyword ranking; dense retrieval [18] with Sentence-BERT [10] and the distilled MiniLM [11] captures "
           "paraphrase; Reciprocal Rank Fusion [9] combines rankings without calibrating scores; cross-encoders [12] trained on MS MARCO "
           "[15] rank more accurately at higher cost. Natural-language-inference models trained on MultiNLI [14], such as the DeBERTa "
           "family [13], predict whether a text entails a statement and so can score support. We use Gemini [17] for generation.")
    P.table([["Work", "Approach", "Data", "Reported result", "Limitation"],
             ["[1] base paper", "TF-IDF/TextRank, then LED, Long-T5, BART, GPT-3.5", "2,000 Turkish rulings", "ROUGE-1 55%, -2 35%, -L 42%", "Summaries; no citations or QA"],
             ["[2] 2024", "RAG with GPT-4o", "Quebec auto insurance; 82 answers", "Better on average; 5-13% false", "Auto insurance; one model"],
             ["[6] 2026", "LLM vs RAG vs RAG + re-rank", "Public-health policies", "Faithfulness .347/.621/.797", "Not insurance wordings"],
             ["[5] 2025", "Knowledge-graph RAG", "Manufacturing documents", "Not read", "Other domain"],
             ["[3] 2026, [4] 2023", "Multi-strategy RAG; service chatbot", "Not retrieved", "Not retrieved", "Titles only"]],
            "Related work", widths=[0.15, 0.25, 0.2, 0.22, 0.18], size=6.5)
    P.para("**Gap.** The reviewed work summarises rulings, answers questions in another insurance line or domain, or is available only "
           "by title. We found no system that joins clause-level structure with page citations, a per-answer support score, a rule "
           "for declining unanswerable questions, claim guidance and a repeatable evaluation on several real health-insurance wordings. "
           "PolicyLens addresses this combination.")

    # ---------------------------------------------------------------- III
    P.h1("III. Methodology")
    P.h2("A. Pipeline and Architecture")
    P.para("PolicyLens has two phases. Preparation runs once per wording in a background worker: validate the PDF (signature, size, "
           "encryption, SHA-256), parse, segment, index, extract the Policy Card and compute risks. Use runs on demand: retrieve, "
           "generate, check. Fig. 1 shows the architecture: a React web app, a FastAPI back end with eight services, SQLite and "
           "ChromaDB storage, three CPU models, and the Gemini API as the only external service.")
    P.figure(PAPER / "fig1_architecture.png", "System architecture of PolicyLens.", width=3.4)
    P.h2("B. Parsing and Segmentation")
    P.para("Wordings are laid out for print. The parser reads each line with its page, box and font, removes running headers and "
           "footers by their repetition, restores the reading order of two-column pages, joins letter-spaced headings and reads tables by "
           "row; a page without a text layer is rejected. The segmenter starts a clause at a printed number (4.2.1), a definition "
           "(Def. 5), an IRDAI exclusion code (Excl03) or a heading, makes each coded list item its own clause, keeps the heading path "
           "and the highlight rectangles, and splits chunks longer than 380 words. The four sample wordings (166 pages, 73,001 words) "
           "gave 801 clauses. Fixed-size windows were not used because a citation must point at one rule and be highlighted on its page.")
    P.h2("C. Hybrid Retrieval")
    P.para("For each question BM25 Okapi (k1 = 1.4, b = 0.7, with an insurance synonym list) and cosine search over 384-dimensional "
           "MiniLM vectors each return 30 clauses. Reciprocal Rank Fusion scores a clause d over the rankings r as")
    P.eq("RRF(d) = Σ_{r} 1 / (60 + rank_{r}(d))", 1)
    P.para("The fused top 20 plus each retriever's own top 8 form the pool, so that a clause found by only one method still reaches the "
           "re-ranker. The cross-encoder score CE(q, d) decides the order and the fused rank breaks ties:", indent=False)
    P.eq("s(d) = CE(q, d) + 0.06 · RRF(d)", 2)
    P.para("The best seven clauses are passed on, together with the rule that a retrieved table belongs to and the tables that a rule "
           "governs (up to four more), because lists and sub-limit tables are separate clauses from the rule that gives them meaning.", indent=False)
    P.h2("D. Grounded Generation and the Abstention Rule")
    P.para("Gemini receives the tagged clauses, the question and a JSON schema, and returns a status, the answer in the requested "
           "language, an English version, claims tagged with clauses, and follow-up questions. Any tag that does not belong to a "
           "retrieved clause is removed. Before the call, let S be the best final score and B the best BM25 score of the retrieved "
           "clauses; the assistant answers \"not covered in this policy\" without calling the model if")
    P.eq("S < 0.004  and  B < 9.0", 3)
    P.para("Neither score separates answerable from unanswerable questions alone, but the pair does (Section IV). Hindi and Telugu "
           "questions are translated into an English search query and searched together with the original.", indent=False)
    P.para("**Languages.** A question whose script is Devanagari or Telugu is detected without a model call and translated into an English "
           "search query by the lighter Gemini model; the original and the translation are both searched and the cross-encoder keeps the "
           "better view of each clause. The answer is written in the requested language and also in English, which is the text that the "
           "faithfulness scorer reads, so the score does not depend on the translation. Cards and risk lists are translated on request and "
           "cached; clause quotes always stay in the policy's original English.", indent=True)
    P.figure(PAPER / "fig2_flow.png", "Main flow of answer_question().", width=3.4)
    P.h2("E. Faithfulness Score")
    P.para("An independent NLI model scores each claim. The cited clause text is cut into sentence and two-sentence windows w; the "
           "eight windows most similar to the claim c are kept and the entailment probability e(w, c) is taken from the softmax of the "
           "model's logits. With o(c) the token overlap of the claim and its evidence, the support of a claim is")
    P.eq("sup(c) = max( max_{w} e(w, c), 0.75 · o(c) [o(c) ≥ 0.8] ) · κ", 4)
    P.para("where κ = 0.5 if a number in the claim (dates and years excluded) does not occur in the cited text, and 1 otherwise. The score "
           "of an answer with n claims is F = (100 / n) Σ sup(c), labelled well supported (F ≥ 80), partly supported (50 ≤ F < 80) or "
           "weakly supported (F < 50). The scorer is independent of the writing model, runs offline and costs no quota.", indent=False)
    P.h2("F. Policy Card, Claim Copilot and Comparison")
    P.para("One Gemini call with a JSON schema extracts the Policy Card: sum insured, deductible, co-payment, room-rent rule, initial, "
           "pre-existing, specific-disease and maternity waiting periods, sub-limits, key exclusions and claim timelines, each as a value "
           "with a verbatim quote and a clause tag. The quote is then located in the clauses with fuzzy matching to confirm its clause "
           "and page, and values whose quote is not found are shown as unverified; the share of verified values was 0.91 to 1.00 across "
           "the four wordings. A risk engine applies rules to the extracted numbers (for example a co-payment above a threshold, a long "
           "waiting period, a room-rent cap, a short claim deadline) and merges them with model-found risks, removing duplicates and "
           "assigning a severity. Claim Copilot gathers 16 clauses with "
           "seven to nine targeted searches. Rules calculate from the card the months of cover against each waiting period, the "
           "co-payment that applies at the insured's age and claim mode, sub-limits that name the treatment, and the split of the bill: "
           "with a bill C, deductible dd, sub-limit L and co-payment p percent, P = min(max(0, C − dd), L) and the insurer pays "
           "P − P·p/100. A failed waiting-period check can never be shown as \"covered\". A comparator builds a field-by-field table with "
           "trade-offs that cite both policies.")
    P.h2("G. Implementation")
    P.para("The API has 42 route handlers under /api with JWT authentication (HS256, 24 h), bcrypt password hashes and owner-only "
           "access to every record. Uploads are validated and processed by a background thread that resumes after a restart. The Gemini "
           "client requests JSON-schema output, falls back through three models, pauses an overloaded model for ten minutes, paces requests "
           "and caches identical requests on disk. No model is trained; the three local models are pre-trained. Twenty-five automated "
           "tests cover authentication, parsing, rules, faithfulness and the full policy flow with a stand-in for the language model.")

    # ---------------------------------------------------------------- IV
    P.h1("IV. Results")
    P.h2("A. Test Conditions")
    P.para("The evaluation set was written by hand from the four wordings (Star Health, HDFC ERGO, Niva Bupa, Care Health): 57 questions "
           "(51 answerable, 6 out of scope), 5 Hindi or Telugu questions, 14 claim scenarios and 52 Policy Card values. Evidence snippets "
           "are copied verbatim from the PDFs. No model is trained, so the whole set is held-out test data. A clause is relevant if it "
           "contains an evidence snippet; a question is answered correctly if the answer contains every key fact. The figures are from "
           "run eval-20260922-0027 on the machine of Section I-A. During the run the free-tier quota of the two larger Gemini models was "
           "used up, so every answer came from the smallest model, gemini-3.5-flash-lite. Retrieval is scored by hit@k (a relevant clause in the "
           "top k), mean reciprocal rank MRR@10 and evidence recall@5; answers by accuracy, citation accuracy (the cited clause contains "
           "the evidence or lies on an expected page), faithfulness and abstention accuracy; claims by verdict accuracy and per-verdict "
           "precision, recall and F1; and the card by the share of 52 hand-checked values that are correct after unit conversion.")
    P.h2("B. Retrieval, Answers and Faithfulness")
    P.table([["Measure", "Result"],
             ["Hybrid + re-rank: hit@1 / hit@5 / MRR@10", "0.804 / 1.000 / 0.897"],
             ["BM25 only: hit@1 / hit@5", "0.647 / 1.000"],
             ["Dense only: hit@1 / hit@5", "0.490 / 0.804"],
             ["Hybrid (RRF): hit@1 / hit@5", "0.686 / 0.961"],
             ["Answer accuracy / citation accuracy", "51/51 / 51/51"],
             ["Faithfulness, mean / median", "87.0 / 91.7"],
             ["Well / partly / weakly supported", "45 / 8 / 3 (of 56)"],
             ["Out-of-scope declined / false abstentions", "6/6 / 0"],
             ["Hindi or Telugu answers correct", "5/5"],
             ["Claim verdicts correct", "14/14"],
             ["Policy Card values correct", "51/52 (98.1%)"],
             ["Answer time, median / 95th percentile", "4.3 s / 18.2 s"],
             ["Automated tests", "25 passed"]],
            "Measured results, run eval-20260922-0027", widths=[0.64, 0.36], size=7)
    P.para("Keywords matter in policy text: BM25 alone put a relevant clause in the top five for every question, while dense search "
           "alone missed one question in five (Fig. 3a). The cross-encoder decides the top of the list: it lifted hit@1 from 0.686 "
           "(fusion) to 0.804 and MRR@10 from 0.795 to 0.897, at a median cost of 0.88 s on the CPU. All 51 answers contained every key "
           "fact and cited a clause that contains the evidence. Of 56 scored answers, 45 were well supported, 8 partly and 3 weakly; "
           "all three weak ones were still correct. They show the limits of a small NLI model: an exclusion-list item that does not "
           "itself say \"excluded\" (its heading does), a rule stated as the inverse of an exclusion, and a defined term replaced by "
           "its abbreviation. Adding the heading to the evidence fixed the first kind but also confirmed a wrong statement about an "
           "exception, so it was not adopted. The same co-payment question scored 99.0 in one run and 37.9 in another, so the score "
           "is shown as a prompt to open the cited clause, not as a verdict. Accuracy was complete in every category: waiting periods 14 of 14, "
           "benefits 15 of 15, claim process 8 of 8, exclusions 5 of 5, policy terms 4 of 4, room rent 3 of 3 and sub-limits 2 of 2. Parsing "
           "and indexing a wording took 3.2 to 4.2 s (24 to 53 pages), and the median retrieval stage took 0.86 s, Gemini 2.5 s and the "
           "faithfulness scorer 0.83 s, which together give the 4.3 s median answer time.")
    P.figure(CHARTS / "paper_results.png", "Retrieval methods (a) and answer time by stage (b).", width=3.4)
    P.h2("C. Abstention, Claims and Policy Card")
    P.para("Measured through the running API for all 57 questions, the best re-rank score was at most 0.0029 and the best BM25 score at "
           "most 7.3 for the six out-of-scope questions, while answerable questions reached scores as low as 0.0020 and 7.1. Neither "
           "alone separates them, but the pair of Eq. (3) declined 6 of 6 out-of-scope questions and none of the 51 answerable ones. "
           "All 14 claim verdicts were correct (five covered, one partly covered, seven not covered, one needs information); precision, "
           "recall and F1 were 1.0 for every verdict, and the reasons had a mean faithfulness of 82.7. The one wrong Policy Card value "
           "is an ambiguity of the document: the HDFC ERGO wording covers seven plan variants with different cumulative bonuses, and "
           "the card reports the Optima Secure figure (50%) while the reference takes the general clause (10%).")
    P.h2("D. Improvement Across Three Runs")
    P.para("Three runs are kept, each fixing what the previous one exposed. The baseline run reached hit@5 of 98.0%, answer accuracy of "
           "88.2% and citation accuracy of 92.2%, with five false abstentions: answerable questions that the assistant declined. "
           "Requiring both a low re-rank score and a low keyword score before declining, and sending a rule together with the tables it "
           "governs, raised answer accuracy to 98.0% and citation accuracy to 96.1% and left one false abstention. The last remaining "
           "errors came from list items that carry an exclusion code, which the segmenter had merged into a single clause. Making each "
           "such item its own clause, telling the model that an exclusion is an answer, and no longer applying a non-network "
           "co-payment to cashless claims gave 100% on retrieval, answers and citations with no false abstention. The gains came from "
           "structure and context, not from a better model. They were also made by studying failures on the evaluation set itself, which is "
           "why the final figures should be read as optimistic.")
    P.h2("E. Output Screens")
    P.figure(PAPER / "fig4_answer.png", "Cited answer: 24-month wait, two sources, faithfulness 88.", width=3.4)
    P.figure(PAPER / "fig5_claim.png", "Claim Copilot: knee replacement partly covered (20% co-payment).", width=3.4)
    P.para("Fig. 4 shows a real answer to \"Is cataract surgery covered and after how long?\": covered after a 24-month waiting period, "
           "with two source chips that open the original page. An out-of-scope question (a house fire) was declined in 1.7 s without "
           "a model call; the Hindi room-rent answer scored 92. Fig. 5 shows the claim check for a knee replacement with 36 months of "
           "cover at age 64: partly covered because the waiting periods are complete but a 20% co-payment applies from age 61.")
    P.h2("F. Comparison with the Base Paper and Observed Limits")
    P.para("The datasets, tasks, languages and metrics differ from the base paper [1] (summarisation of Turkish rulings, ROUGE), so no "
           "numeric comparison is possible and none is claimed; the comparison is of approach. The closest figure is the policy-document "
           "study [6], whose faithfulness values (0.347, 0.621, 0.797) use another model, corpus and measure and are not comparable "
           "with our 87.0, but agree that two-stage retrieval with re-ranking is what makes grounded answers reliable. The limits are "
           "these: 51 answerable questions over four policies, with the abstention thresholds and parser fixes tuned on the same set, "
           "so the figures are optimistic; only the smallest Gemini model was measured; the Telugu translation of one card line mixes "
           "Bengali and Gurmukhi script; a slow tail of answers (95th percentile 18.2 s, maximum 24.8 s) comes from the model fallback chain; "
           "and no load, security or user-acceptance test was carried out.")

    # ---------------------------------------------------------------- V
    P.h1("V. Conclusion")
    P.para("PolicyLens answers health-insurance questions from the user's own wording, with a clause and page behind every statement, "
           "an independent support score, and a rule for declining what the wording does not cover. Against the objectives, key "
           "attributes are extracted into a verified Policy Card (51 of 52 values), relevant clauses are retrieved (top five for 51 of "
           "51 questions), answers are plain-language, grounded and cited (51 of 51), claims are guided (14 of 14 verdicts), and accuracy, "
           "faithfulness (mean 87.0) and speed (median 4.3 s) were measured. The main finding is that structure and re-ranking, not a "
           "larger model, drove the gains across three runs, from 88.2% to 100% answer accuracy. The honest limits are a small set "
           "partly tuned on itself, the smallest model, a heuristic faithfulness score and no user study.")
    P.para("Future work: a fresh evaluation on unseen wordings with the larger Gemini models; plan-variant selection and OCR for scanned "
           "policies; better faithfulness scoring and automatic checks of translation quality; and a hosted deployment with HTTPS, load "
           "testing and a study with real policyholders.")

    P.references()
    K.Paper  # keep import used
    P.d.core_properties.title = K.TITLE
    P.d.core_properties.author = "Batch A1"
    P.d.save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    build()
