"""Chapter 2 content: literature survey, base paper analysis, related work, algorithms, strengths and limitations, gap."""
from __future__ import annotations

from doc_common import BASE_PAPER


def sec_lit_overview(d):
    d.h2("Overview of the Literature Survey")
    d.paras(
        "The survey covers four groups of work. The first is the base paper [1], on summarising long legal documents. The second is "
        "recent work on question answering over insurance and policy documents with retrieval-augmented generation [2]-[6]. The third "
        "is the retrieval and language-model techniques that PolicyLens is built from: retrieval-augmented generation [7], BM25 [8], "
        "dense retrieval and sentence embeddings [10], [11], [18], rank fusion [9], cross-encoder re-ranking [12], [15] and "
        "natural-language inference [13], [14]. The fourth is work on the reliability of language-model output [16].",
        "Of the sources, the base paper [1], the Quebec insurance study [2] and the policy-document RAG evaluation [6] were read in "
        "detail (abstract, method and results). The sources [3] and [4] are listed in the batch literature survey, but their text could "
        "not be retrieved independently, so they are described here by title and venue only and no result is attributed to them. For "
        "[5] the bibliographic details were confirmed but the results were not read, so only its topic is stated.")


def sec_base_paper(d):
    d.h2("Base Paper Analysis")
    d.p(f"**Base paper.** {BASE_PAPER}")
    d.paras(
        "**Problem and data.** Albayati and Findik address the lack of automated summarisation tools for Turkish legal documents, "
        "where the agglutinative morphology and specialised vocabulary make the task harder. They collected 2,000 Turkish court rulings "
        "(consumer-rights cases) from a public website with a scraping tool and cleaned them to keep the decisions and legal arguments.",
        "**Method.** A hybrid pipeline. Extractive methods, TF-IDF and TextRank, first select the important sentences of each ruling. "
        "Transformer models for long inputs, LED and Long-T5, together with BART-large and GPT-3.5 Turbo, then generate an abstractive "
        "summary from the extractive output. The paper evaluates the extractive methods with cosine similarity and content precision, "
        "recall and F1, and the abstractive models with ROUGE [19].",
        "**Reported results.** TF-IDF with keyword guidance reached a content F1 of 0.47. GPT-3.5 Turbo gave the best ROUGE scores: "
        "ROUGE-1 55%, ROUGE-2 35%, ROUGE-L 42% and ROUGE-Sum 44%. BART-large was the weakest model.",
        "**Claimed contributions.** The first Turkish legal summarisation framework, a validated dataset of Turkish civil cases, evidence "
        "that a hybrid extractive-plus-abstractive approach works for legal text, and preprocessing adapted to Turkish.",
        "**What PolicyLens adopts.** The base paper's central idea is that a long, domain-specific legal document is best handled by "
        "first selecting the important passages and then generating text from them. PolicyLens applies the same idea to health-insurance "
        "wordings: retrieval selects the relevant clauses, and the language model generates from those clauses only.",
        "**What PolicyLens changes.** The task (cited question answering, claim guidance and comparison instead of summarisation), the "
        "domain (health-insurance wordings instead of court rulings), the language (English wordings with Hindi and Telugu "
        "interaction instead of Turkish), the selection step (a measured hybrid retriever with a cross-encoder instead of TF-IDF and "
        "TextRank), the generation model (Gemini with a JSON schema instead of fine-tuned summarisers) and the evaluation (retrieval, "
        "citation, faithfulness and verdict measures instead of ROUGE).",
        "**Limitations of the base paper, as we read them.** It evaluates summaries by overlap with reference summaries, which does not "
        "show whether a statement is supported by the source; it has no citations back to passages; and it does not address "
        "question answering or guidance. These are not criticisms of its purpose, only the reasons it cannot be used unchanged here.")


def sec_related(d):
    d.h2("Related Work")
    d.h3("Question answering over insurance and policy documents")
    d.paras(
        "Beauchemin, Khoury and Gagnon [2] test retrieval-augmented generation for Quebec automobile-insurance questions. They build a "
        "reference corpus of insurance expertise and a set of 82 expert answers to lay questions, and evaluate GPT-4o with and without "
        "the corpus, with automatic and manual assessment. Retrieval improved the answers on average, but between 5% and 13% of answers "
        "still contained a false statement that could mislead a customer, and the authors conclude that LLM answering is not reliable "
        "enough for mass use in critical areas. This is the strongest argument for the two safeguards in PolicyLens: citations that the "
        "user can check, and an independent faithfulness score.",
        "Maharjan and Yadav [6] compare a plain LLM, a basic RAG pipeline and an advanced RAG pipeline with cross-encoder re-ranking on "
        "public-health policy documents, using Mistral-7B-Instruct-v0.2 and the same all-MiniLM-L6-v2 embedding model that PolicyLens "
        "uses. Faithfulness rose from 0.347 (plain LLM) to 0.621 (basic RAG) and 0.797 (advanced RAG), and they report that document "
        "segmentation remains a bottleneck for multi-step reasoning. Their two findings, that two-stage retrieval matters and that "
        "segmentation limits quality, correspond to PolicyLens's re-ranker and to its clause-aware segmenter.",
        "A multi-strategy RAG system for medical-insurance question answering is described in [3], and an AI chatbot for the Iran Health "
        "Insurance Organization in [4]. Both are listed in the batch survey; only their titles and venues are used here. Knollmeyer et "
        "al. [5] study knowledge-graph-enhanced RAG for document question answering in manufacturing, which indicates that structure "
        "beyond flat text chunks is an active direction; PolicyLens keeps the document's own clause structure instead of building a graph.")
    d.h3("Retrieval and ranking")
    d.paras(
        "Retrieval-augmented generation [7] conditions a generator on passages retrieved from an external store, which reduces reliance "
        "on the model's memory. BM25 [8] is the standard probabilistic keyword ranking and remains strong when queries and documents "
        "share exact terms. Dense retrieval [18] embeds queries and passages into a vector space; Sentence-BERT [10] and the distilled "
        "MiniLM [11] provide compact general-purpose embeddings. Reciprocal Rank Fusion [9] combines ranked lists without calibrating "
        "their scores. Cross-encoders [12] read the query and passage together and rank more accurately than either retriever alone, at "
        "higher cost; MS MARCO [15] is the usual training data for such rankers.")
    d.h3("Checking model output")
    d.paras(
        "Hallucination in natural language generation is surveyed in [16]. Natural-language inference, trained on corpora such as "
        "MultiNLI [14] and used with strong encoders such as DeBERTaV3 [13], predicts whether a premise entails a hypothesis, and so "
        "can score whether an answer's statements are supported by the text it cites. PolicyLens uses a small NLI cross-encoder for "
        "this purpose, independent of the model that wrote the answer. The large language model itself is accessed through the Gemini "
        "API [17].")
    rows = [["Ref.", "Work", "Task / approach", "Data", "Reported result", "Limitation for this project"],
            ["[1]", "Albayati and Findik, 2025 (base paper)", "Hybrid extractive + abstractive summarisation of rulings", "2,000 Turkish court rulings", "GPT-3.5 Turbo ROUGE-1 55%, ROUGE-2 35%, ROUGE-L 42%", "Summarisation, not QA; no citations; Turkish court rulings"],
            ["[2]", "Beauchemin et al., 2024", "RAG over an insurance corpus with GPT-4o", "Quebec auto-insurance corpus; 82 expert answers", "Better on average; 5-13% of answers had a false statement", "Auto insurance; one model; small answer set"],
            ["[6]", "Maharjan and Yadav, 2026", "Plain LLM vs basic vs advanced RAG (cross-encoder)", "Public-health policy documents", "Faithfulness 0.347 / 0.621 / 0.797", "Public-health guidance, not insurance wordings"],
            ["[3]", "Multi-strategy RAG for medical-insurance QA, 2026", "Multi-strategy RAG", "Not retrieved", "Not retrieved", "Listed in batch survey only"],
            ["[4]", "AI chatbot, Iran Health Insurance Organization, 2023", "Service chatbot", "Not retrieved", "Not retrieved", "Listed in batch survey only"],
            ["[5]", "Knollmeyer et al., 2025", "Knowledge-graph-enhanced RAG for documents", "Manufacturing documents", "Not read", "Different domain; results not read"]]
    d.table(rows, "Related work reviewed", widths=[0.07, 0.19, 0.2, 0.17, 0.19, 0.18], font=8.5)


def sec_lit_algorithms(d):
    d.h2("Datasets and Algorithms Used in the Literature")
    d.table([["Technique", "Used in", "Role in PolicyLens"],
             ["TF-IDF, TextRank (extractive selection)", "[1]", "Counterpart of retrieval: selects passages before generation. PolicyLens uses BM25 [8] instead"],
             ["LED, Long-T5, BART-large, GPT-3.5 Turbo", "[1]", "Abstractive generators; PolicyLens uses Gemini [17] with a JSON schema"],
             ["ROUGE-1/2/L", "[1], [19]", "Summary overlap; not applicable to cited QA"],
             ["RAG with GPT-4o", "[2]", "Same principle; PolicyLens adds a faithfulness score and abstention"],
             ["all-MiniLM-L6-v2 embeddings", "[6], [10], [11]", "Dense retrieval in PolicyLens"],
             ["Cross-encoder re-ranking", "[6], [12], [15]", "Final ranking of fused candidates"],
             ["Reciprocal Rank Fusion", "[9]", "Combines BM25 and dense rankings"],
             ["NLI (DeBERTa family)", "[13], [14]", "Faithfulness scoring of each answer"]],
            "Techniques in the literature and their role in PolicyLens", widths=[0.34, 0.16, 0.5], font=9.5)


def sec_lit_strengths(d):
    d.h2("Strengths and Limitations of Existing Approaches")
    d.table([["Approach", "Strengths", "Limitations"],
             ["Reading the wording / agents and helplines", "Authoritative; human judgement", "Slow, inconsistent, generic; the wording is long and technical"],
             ["Comparison websites", "Easy premium and benefit comparison", "Do not explain exclusions, waiting periods or claim conditions"],
             ["General-purpose chatbots", "Fluent, available at any time", "Answer from training data, not the user's policy; may hallucinate [16]; no citations"],
             ["RAG over insurance text [2]", "Grounded in a corpus; better on average than the plain model", "5-13% false statements remain; one model; no per-answer support score"],
             ["Advanced RAG with re-ranking [6]", "Faithfulness 0.797 vs 0.347 for the plain model", "Different domain; segmentation named as a bottleneck"],
             ["Summarisation framework [1]", "Handles very long legal texts; strong ROUGE with GPT-3.5 Turbo", "Summaries only; no question answering, citations or guidance"]],
            "Strengths and limitations of existing approaches", widths=[0.28, 0.34, 0.38], font=9.5)


def sec_gap(d):
    d.h2("Research Gap")
    d.p("Existing work summarises or answers questions over legal and general documents, but few systems combine policy attribute "
        "extraction, clause-grounded question answering and claim guidance for health insurance. The survey leaves five specific gaps "
        "that this project addresses:")
    d.numbered([
        "**Structure.** Retrieval over flat chunks loses the clause numbers and pages on which a policyholder relies; segmentation is named as a bottleneck in [6]. A clause-aware parser that preserves numbering, pages and positions is needed.",
        "**Per-answer evidence of support.** [2] shows that retrieval alone leaves false statements; no reviewed system gives the user a score of how well each answer is supported by the cited text.",
        "**Knowing when not to answer.** A policy question may simply not be covered by the wording; the assistant must decline without calling the model rather than invent an answer.",
        "**Guidance as well as explanation.** None of the reviewed work combines question answering with calculated claim pre-checks, document checklists and a cost estimate.",
        "**Measured, repeatable evidence on real wordings.** The reviewed studies work on one insurance line or on other domains; a repeatable evaluation on several real health-insurance wordings, with retrieval, citation, faithfulness, abstention and verdict measures, was not found in the work reviewed.",
    ])
