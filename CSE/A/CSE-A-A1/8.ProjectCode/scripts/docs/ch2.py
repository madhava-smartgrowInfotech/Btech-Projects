"""Chapter 2: Literature survey."""

from . import facts as F
from .blocks import B, H1, H2, H3, N, P, TAB

# (Work, Approach, Data, Reported result, Limitation). Only facts read in the papers themselves (the PDFs of [1]-[3]) or stated by [1]
# about the works it cites; nothing is quoted from the unverified batch-survey titles [19]-[22].
LIT_TABLE = [
    ["Zhang et al. 2026 [1] (base paper)", "LLM question classifier, type-specific retrieval (hybrid BM25 + dense with rerank, dense only, or sub-question decomposition), LLM context compression",
     "HotpotQA, 2WikiMultiHopQA, MuSiQue; 1,000 questions each; gpt-5-mini", "Tokens down 38-58% for 1-2 points of EM; HotpotQA EM 0.560 to 0.611 and Recall@10 0.787 to 0.880 with adaptive retrieval",
     "Benchmark QA, not student documents; extra LLM calls raise latency (27.8 s against 9.6 s per question on HotpotQA)"],
    ["Li et al. 2024 [2] (TutorLLM)", "Knowledge tracing (MLFBK) combined with a scraper and GPT-4 RAG; personalised recommendations in a browser plug-in",
     "Two-week crossover study, 30 undergraduates, online linear algebra course", "10% higher user satisfaction (SUS) and 5% higher quiz scores than a general LLM",
     "Small sample; needs interaction logs and a trained KT model; one course"],
    ["Vatankhah Barenji et al. 2026 [3]", "Agentic RAG grader that retrieves rubric criteria, exemplar essays and instructor feedback to grade and comment",
     "701 student essays; vector store (Supabase)", "94-99% agreement with human evaluators; Pearson r 0.89; mean absolute error 2.94 percentage points",
     "Assessment, not tutoring; needs an instructor-curated knowledge base"],
    ["Karpukhin et al. 2020 [5] (DPR)", "Dense dual-encoder passage retrieval trained on question-passage pairs", "Open-domain QA benchmarks",
     "Reported 9-19 points higher top-20 passage accuracy than a strong BM25 system", "Needs training data and embeddings; benchmark text, not personal notes"],
    ["Jeong et al. 2024 [11]; Jiang et al. 2023 [10]; Xu et al. 2024 [15]",
     "As described in [1]: route a question to no, single-step or multi-step retrieval; compress the prompt with a small model; treat compression as summarisation",
     "See the original papers", "Not quoted here (read only through [1])", "Each handles routing or compression alone; [1] unites them"],
]


def blocks():
    sh = F.SHIPPED
    cmp4 = F.CMP["4"]
    ab = F.ABS
    hf = F.DOCAN["heading_formats"]
    return [
        H1("CHAPTER 2: LITERATURE SURVEY"),

        H2("2.1 Overview"),
        P("This chapter reviews the work on which the Adaptive Learning Intelligence Platform builds and against which it is judged. It analyses the batch base paper, "
          "SAC-RAG [1], in detail, then the two supporting papers kept in the batch folder: TutorLLM [2], which joins knowledge tracing with RAG, and an LLM-powered RAG assessment system for higher "
          "education [3]. Related work is grouped by theme, the datasets and algorithms of this project are described, and the chapter ends with the research gap. "
          "A number is quoted from a paper only when it was read in the paper itself; statements about works that [1] cites (Adaptive-RAG, LLMLingua, RECOMP, Self-RAG) "
          "repeat the description given in [1] and are marked as such, and for the four further titles of the batch survey only the title and venue are used."),

        H2("2.2 Analysis of the Base Paper: SAC-RAG"),
        P("The batch documents name as base paper \"SAC-RAG: Semantic Adaptive Context Compression for Retrieval-Augmented Generation\" by Zhang, Yu, Huo and Su of Shenyang Ligong University, "
          "published in IEEE Access, volume 14, 2026 [1]. It studies how to make RAG both more accurate and cheaper for multi-hop question answering."),
        H3("Problem addressed"),
        P("Standard RAG applies one retrieval strategy to every question and passes all retrieved passages to the generator. The authors identify two weaknesses: different question types need different "
          "retrieval, and redundant retrieved text raises token consumption and can lower answer quality, a \"lost-in-retrieval\" effect related to the observation that models use information in the "
          "middle of long contexts poorly [12]. Earlier work optimises either retrieval (Adaptive-RAG [11], Self-RAG [14]) or compression (LLMLingua [10], RECOMP [15]), but not both in one framework [1]."),
        H3("Method"),
        P("SAC-RAG has five stages: question classification, type-specific retrieval, context compression, answer generation and evaluation. An LLM with a few-shot prompt classifies each question as "
          "Fact, Definition or Reasoning. The retrieval strategy then depends on the type:"),
        B("**Fact** questions use hybrid retrieval. The score of a candidate document is S = lambda x BM25(q, d) + (1 - lambda) x cos(e_q, e_d), where BM25 uses k1 = 1.5 and b = 0.75 and the dense vectors come from "
          "the text-embedding-3-small model (1,536 dimensions, stored in Milvus). Candidates are merged, de-duplicated and re-ranked with the bge-reranker-base cross-encoder, keeping the top 10.",
          "**Definition** questions use dense retrieval only, taking the top 8 documents.",
          "**Reasoning** questions are decomposed by an LLM into sub-questions, each retrieved in parallel (top 10 each), then merged and re-ranked."),
        P("All retrieved sets then pass through one LLM compression module that extracts evidence snippets, and the generator answers from the compressed context. "
          "Compression uses one prompt for every type; the type-specific retrieval changes what the compressor receives, so its effect differs by type [1]."),
        H3("Evaluation and reported results"),
        P("Four settings are compared on HotpotQA, 2WikiMultiHopQA and MuSiQue, with 1,000 questions per dataset, gpt-5-mini at temperature 0 and four metrics (Exact Match, F1, Recall@10 and average tokens): "
          "Naive RAG, Compress RAG, Adaptive RAG and SAC-RAG (both). Compression against Naive raises EM by 1.2, 2.4 and 2.9 points and lowers tokens by 9-36% (H1). Adaptive retrieval against Naive raises EM by "
          "5.1, 3.3 and 4.2 points and Recall@10 by 2.5-9.3 points; on HotpotQA EM rises from 0.560 to 0.611 and Recall@10 from 0.787 to 0.880 (H2). SAC-RAG against Compress adds 2.3, 0.4 and 0.0 points of EM (H3). "
          "Against Adaptive RAG, SAC-RAG cuts token consumption by 38-58% at a cost of one to two points of EM; its average of 1,087-1,918 tokens compares with 2,407-3,111 [1]."),
        P("The classifier agrees with manual labels on 92.0% of 300 sampled questions; 21 of its 24 errors label a reasoning question as factual. On reasoning questions of HotpotQA compression raises EM from "
          "0.455 to 0.577, while on MuSiQue, where retrieval recall is low (0.42-0.48), it slightly lowers it. The system-level comparison with Vanilla RAG, IterDRAG, ReSearch and AirRAG uses different "
          "backbone models, which the authors acknowledge [1]."),
        H3("What the paper leaves open"),
        B("**Cost in latency.** The extra LLM calls raise the time per question from about 9.6 s (Naive RAG) to 27.8 s on HotpotQA [1].",
          "**Benchmarks, not learners.** The paper does not consider a student's own documents, document ingestion, or any learner-facing feature.",
          "**Dependence on LLMs and paid services.** Classification, decomposition and compression need an LLM, and retrieval needs a vector database and a reranker, none of which a student laptop offers."),
        TAB("SAC-RAG components and their status in the Adaptive Learning Intelligence Platform", ["SAC-RAG component [1]", "In ALIP", "Status"],
            [["LLM question classifier (Fact / Definition / Reasoning)", "None. All questions take the same path. Question type is used only to analyse results (Chapter 8).", "Not implemented"],
             ["Hybrid BM25 + dense retrieval with reranking; dense-only retrieval; sub-question decomposition", "TF-IDF with unigrams and bigrams, cosine similarity, top 4. BM25 and BGE-small were measured as experiments only.", "Not implemented; reference only"],
             ["LLM context compression and answer generation", "Extractive selection of the four best sentences; an optional Claude call restricted to the context (not measured).", "Partly (extractive)"],
             ["Evaluation with EM, F1, Recall@10 and tokens", "Hit@k, MRR, answer-key recall and words removed, on a 72-question notes corpus.", "Own protocol"]],
            widths=[2.3, 3.2, 1.2], align=["l", "l", "l"], size=9.5),
        P("This project adopts the retrieve-then-answer pipeline of [1] and its idea that retrieved context should be reduced before it reaches the "
          "answer, and measures the reduction. It does not reproduce the paper's adaptive retrieval or its learned compression."),

        H2("2.3 Analysis of the Supporting Papers"),
        H3("TutorLLM: knowledge tracing and RAG for personalised learning"),
        P("Li et al. [2] observe that LLMs hallucinate and lack personalisation, while educational recommenders based on knowledge tracing (KT) personalise but cannot "
          "answer free-form questions. TutorLLM combines a KT model (MLFBK) that tracks the student's learning state, a scraper that collects the text of the online course page being studied, and a GPT-4 RAG module "
          "that uses both to answer and to recommend study material. It was implemented as a Chrome plug-in and evaluated in a two-week crossover study with 30 undergraduates in an online linear algebra course; "
          "the paper reports a 10% improvement in user satisfaction (System Usability Scale) and a 5% increase in quiz scores compared with a general LLM alone [2]. Knowledge tracing models "
          "the acquisition of a skill from a student's sequence of answers [17]. TutorLLM is closest in aim to this project but differs in means: it relies on interaction logs and a trained KT network, whereas the present "
          "platform records only per-topic quiz outcomes and turns them into three priority bands."),
        H3("LLM-powered assessment RAG for higher education"),
        P("Vatankhah Barenji, Salimi and Khoshgoftar [3] build an agentic assessment system on RAG for large university courses. A language model retrieves rubric criteria, exemplar essays and instructor "
          "feedback from a vector store to produce grades and formative comments. On 701 student essays the authors report 94-99% agreement with human evaluators, a Pearson correlation of 0.89 "
          "with instructor scores and a mean absolute error of 2.94 percentage points [3]. It shows that grounding model output in curated course material is accepted practice, but it grades work "
          "against a rubric and does not tutor from a student's own notes."),

        H2("2.4 Related Work"),
        H3("2.4.1 Foundations: RAG and retrieval functions"),
        P("Retrieval-augmented generation was introduced by Lewis et al. to give a generator access to an external knowledge store and so reduce hallucination [4]. Karpukhin et al. train a dual-encoder "
          "for passage retrieval and report 9-19 points higher top-20 accuracy than a strong BM25 baseline on open-domain QA [5]. Lexical functions remain "
          "competitive and cheap: TF-IDF weights terms by their frequency in a text and rarity across the collection [7], and BM25 adds term-frequency saturation and length normalisation [6]. "
          "Latent semantic analysis projects TF-IDF vectors into a low-dimensional space with a singular value decomposition [8], and embedding "
          "models such as the BGE family give dense vectors without task-specific training [9]. These are the retrievers compared in Chapter 8. "
          "Longer context is not free: models use relevant information less well when it sits in the middle of a long input [12]."),
        H3("2.4.2 Adaptive retrieval and context compression"),
        P("As described in [1], Adaptive-RAG [11] chooses between no retrieval, single-step and multi-step retrieval according to question complexity; Self-RAG [14] has the model decide when to retrieve by "
          "self-reflection. LLMLingua [10] compresses the retrieved text with a small language model, and RECOMP [15] formulates compression as summarisation. "
          "SAC-RAG [1] combines the two lines. This project's extractive sentence selection is the simplest member of the compression family: it keeps "
          "whole sentences, adds no words and needs no model, at the cost shown in Chapter 8."),
        H3("2.4.3 RAG in education and evaluation data"),
        P("TutorLLM [2] personalises recommendations with knowledge tracing, and the system of [3] grades essays against retrieved rubrics. The batch "
          "survey adds four titles [19]-[22] (medical content for spaced repetition, a vision-language teaching platform, financial education, and Lean resources built with ChatGPT and RAG); "
          "only their titles and venues are known to this work, so their methods and results are not discussed (Section 2.6). "
          "Multi-hop benchmarks such as HotpotQA [13] are the evaluation ground of [1]. Educational notes are different: short, definition-heavy, with headings and lists, so this project builds "
          "its own evaluation corpus from encyclopedic articles arranged as course notes [18]."),
        TAB("Comparison of the surveyed work", ["Work", "Approach", "Data", "Reported result", "Limitation"], [list(r) for r in LIT_TABLE],
            widths=[1.0, 1.6, 1.15, 1.35, 1.2], align=["l", "l", "l", "l", "l"], size=8),
        P("The numbers in the table are those stated by each paper; they come from different data and are not a league table."),

        H2("2.5 Datasets and Algorithms Used in This Project"),
        P(f"A student's own notes are personal and no real syllabus was released for this "
          f"work, so the platform was measured on a six-subject corpus built from 36 English Wikipedia articles [18] (Data Structures, Operating Systems, Database Systems, Computer Networks, Machine Learning, Algorithms), "
          f"{F.CORPUS['words']:,} words in {F.CORPUS['chunks']} chunks of about {F.CORPUS['mean_chunk_words']:.0f} words. Each subject is one file with a \"Subject:\" line and six \"Unit n:\" sections. "
          f"{F.CORPUS['questions']} questions were written by hand, 24 each of fact, definition and reasoning type (the taxonomy of [1]), each with a gold evidence sentence copied from the "
          f"corpus; {F.CORPUS['off_topic_questions']} off-topic questions test abstention. The bundled sample notes of 619 words are used for the screens."),
        TAB("Algorithms used and measured", ["Algorithm", "Role in this project", "Source"], [
            ["TF-IDF (unigram and bigram, English stop words); cosine similarity", "Shipped retriever; also ranks sentences for extractive answers and ranks keywords as topics and quiz terms", "[7], [16]"],
            ["Word-window chunking (180 words, 30 overlap)", "Splits documents into retrievable units", "-"],
            ["BM25 (k1 = 1.5, b = 0.75); TF-IDF with LSA (200 dimensions)", "Experimental lexical and latent-semantic alternatives", "[6], [8]"],
            ["BGE-small-en-v1.5 (384-d, quantised ONNX) and BM25 + dense hybrid", "Experimental dense reference, not shipped", "[9], [1]"],
            ["Extractive sentence selection (top 4)", "Shipped context reduction and answer", "[1], [10]"],
            ["Cloze question generator; accuracy bands (below 50, below 80)", "Quiz from top-40 TF-IDF terms; roadmap priority", "-"],
        ], widths=[2.4, 3.3, 1.0], align=["l", "l", "c"], size=10),

        H2("2.6 Strengths and Limitations of the Surveyed Approaches"),
        TAB("Approach families compared", ["Family", "Strengths", "Limitations for this project's goals"], [
            ["Adaptive retrieval and LLM compression [1], [10], [11], [15]", "Large token savings for a small loss of accuracy; modular", "Several LLM calls, vector database and reranker; evaluated on benchmarks, not notes"],
            ["Dense retrieval [5], [9]", "Matches meaning beyond shared words", "Needs an embedding model and storage"],
            ["Lexical retrieval [6], [7]", "Cheap, offline, transparent, strong on exact terms", "Misses paraphrases; no notion of meaning"],
            ["RAG with learner modelling [2]", "Personalised recommendations; field study", "Needs interaction logs and a trained KT model; one course, 30 students"],
            ["RAG for assessment [3]", "High agreement with human graders at scale", "Grades against a rubric; needs an instructor-built knowledge base"],
        ], widths=[1.9, 2.1, 2.7], align=["l", "l", "l"], size=10),
        P("Grounding generation in retrieved text reduces hallucination and allows citation [4]. Across the field, evaluation relies on benchmarks or one course, with LLM judges or small samples, so results do not transfer "
          "to a particular student's syllabus, and personalisation and compression are studied apart. The four batch-survey titles [19]-[22] are recorded in the reference list with a note that their details are not verified; "
          "nothing is quoted from them and no claim in this report depends on them."),

        H2("2.7 Research Gap"),
        P("The base paper [1] improves the retrieve-and-compress step of RAG but is evaluated only on question-answering benchmarks. "
          "TutorLLM [2] personalises, but needs interaction logs and a trained knowledge-tracing model. The assessment system [3] works from instructor-supplied rubrics. None of the surveyed systems combines document "
          "ingestion, syllabus-grounded tutoring and progress analytics for a student's own curriculum, which is the gap stated in the batch survey. The points still open are:"),
        N("Ingestion of the student's own documents (PDF, DOCX, TXT) into a structured repository with subjects, units and topics.",
          "Answers that come only from that repository and name the passage they were taken from, at no cost and without a network.",
          "A measured account of what the cheap, offline versions of retrieval and context reduction achieve against the stronger methods of the literature, on notes rather than benchmark questions.",
          "Practice questions and a priority roadmap derived from the same documents and from per-topic results."),
        P("The Adaptive Learning Intelligence Platform addresses these points with simple, transparent components. It does not close the retrieval-quality gap to the base paper: "
          f"the shipped TF-IDF retriever reaches Hit@4 {F.hit(sh, 4):.3f} on the notes corpus, below BM25 ({F.hit('bm25', 4):.3f}) and below a BM25 plus dense hybrid ({F.hit('hybrid_bm25_dense', 4):.3f}); extractive "
          f"compression removes {cmp4['token_reduction_pct']:.1f}% of the words but lowers answer-key recall from {cmp4['key_in_ctx']:.3f} to {cmp4['key_in_ans']:.3f}; and {ab['off_topic_answered_by_shipped']} of "
          f"{ab['n_off_topic']} off-topic questions still receive an answer. Of {len(hf)} heading styles tested, {sum(1 for v in hf.values() if v['units_found'] == v['of'])} were fully recognised. "
          "Chapter 8 reports these results and Chapter 9 states them again as limitations."),
    ]
