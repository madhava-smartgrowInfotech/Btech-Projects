"""Chapter 2: Literature survey."""

from . import facts as F
from .blocks import EQ, H1, H2, H3, N, P, TAB
from .refs import CITE as R


def c(*keys):
    """Citation string such as [1], [10] from CITE keys."""
    return ", ".join(f"[{R[k]}]" for k in keys)


def blocks():
    base = c("base")
    return [
        H1("CHAPTER 2: LITERATURE SURVEY"),

        H2("2.1 Overview"),
        P(f"This chapter reviews the work on which {F.PRODUCT} builds and against which it must be judged. It starts with the base paper assigned to the batch {base}, analyses it in detail, "
          "and then groups related work by theme: symptom chatbots, retrieval-augmented generation in healthcare, the retrieval and reranking components, and generation and safety. It then "
          "describes the data and algorithms that the project itself uses, tabulates the works, lists the sources named in the project's literature survey with an honest note on what could be verified, "
          "and ends with the research gap. Numerical results are quoted only where they were read in the paper itself or in a bibliographic record."),

        H2("2.2 Analysis of the Base Paper"),
        P(f"The base paper is \"A Hybrid Retrieval-Augmented Generation Framework for Intelligent Symptom Monitoring and Disease Guidance\", by U. S. Madhury and M. Ramesh of the Department of "
          f"Computer Science and Engineering, Ellenki College of Engineering and Technology, Hyderabad, published in the International Journal of Engineering Research and Science and Technology, "
          f"vol. 22, no. 3, 2026, pp. 702-707 {base}. It presents a framework also named SymptoTrackAI."),
        P("**Method.** A symptom-disease knowledge base - symptom descriptions, disease names and health advice - is organised, de-duplicated and indexed. A transformer the paper calls the "
          "\"Sequence-NQ transformer\" turns both the records and the user's query into embeddings, and FAISS similarity search retrieves the most relevant records. The retrieved text is passed to a "
          "retrieval-augmented generation (RAG) step that writes a context-aware reply. A web application adds registration, authentication, a chatbot for symptom analysis and a health log in which "
          "queries, predicted advice and timestamps are stored for later review."),
        P("**Claims.** The paper states that \"experimental observations\" show the hybrid retrieval framework consistently delivers accurate and context-sensitive responses and efficient response time, "
          "and that the health log supports continuous monitoring. Its single worked example is a conversation in which constipation and stomach ache, followed by high fever and swollen lymph nodes, "
          "lead the chatbot to suggest typhoid. Its conclusion lists future work: a larger knowledge base, multilingual support, multimodal inputs such as clinical reports and images, and cloud deployment."),
        P("**Strengths.** The paper gives a clear, implementable architecture; it chooses retrieval over free generation, which is the right instinct in a medical setting; and it treats persistence of "
          "consultations as part of the system, not an afterthought."),
        P("**Limitations.** The paper reports no accuracy figure, no response-time figure, no size or source for the knowledge base, no baseline and no test set, so none of its claims can be "
          "reproduced or compared. \"Hybrid\" in its title refers to combining retrieval with generation; it does not use lexical retrieval, reranking or query expansion. It has no safety "
          "mechanism for emergencies, and although it speaks of long-term tracking, it describes storage of past consultations, not analysis of change over time."),
        TAB("Base paper compared with this project", ["Aspect", "Base paper", F.PRODUCT], [
            ["Retrieval", "Embeddings (\"Sequence-NQ\") + FAISS", "MiniLM embeddings + FAISS, BM25, weighted fusion, cross-encoder rerank"],
            ["Query handling", "Query embedded as typed", "Normalisation and a rule-based HyDE-style template"],
            ["Generation", "RAG reply", "Flan-T5 or deterministic evidence-based answer, plus filter"],
            ["Safety", "Not described", "Ten emergency rules, caution list, disclaimer, answer filter"],
            ["Accounts and history", "Registration, login, health log", "bcrypt + signed cookie; per-user history with search, detail, delete"],
            ["Evaluation", "Qualitative observations; one example", f"Ablation on five query sets; {F.SAF['n_pos']}+{F.SAF['n_neg']} safety probes; latency; tests"],
            ["Knowledge base", "Symptom-disease dataset, size not stated", f"{F.KB['records']} synthetic records, {F.KB['conditions']} conditions"],
        ], widths=[1.3, 2.3, 2.7], size=9.5, align=["l", "l", "l"]),

        H2("2.3 Related Work by Theme"),
        H3("2.3.1 Symptom and medical chatbots without retrieval"),
        P(f"The base paper's own related-work section covers earlier chatbots, and its descriptions are repeated here with their numbers, of which there are none. Divya et al. {c('divya')} built an "
          f"AI chatbot that suggests conditions from described symptoms. Kumar et al. {c('kumar')} used machine learning and language processing for primary clinical guidance. Hsu and Yu {c('hsu')} "
          f"combined machine learning with natural-language understanding and, according to the base paper, understood health conversations better than rule-based chatbots. Babu and Boddu {c('babu')} "
          f"built a BERT-based chatbot for medical queries. Alqaidi et al. {c('alqaidi')} integrated a medical chatbot into a network service, and Prathwini and Prathyakshini {c('prescience')} used "
          "text classification to predict diseases from symptoms. These systems predict or classify from learned parameters, so their answers are only as good as the training data and carry no pointer "
          "to a source - the weakness that retrieval is meant to repair."),
        H3("2.3.2 Retrieval-augmented generation in healthcare"),
        P(f"Lewis et al. {c('rag')} introduced RAG as a way to give a generator access to an external, updatable memory. In medicine, Peri et al. {c('peri')} built a chatbot that retrieves from medical books before "
          f"generating, in order to reduce fabricated answers. Natarajan et al. {c('natarajan')} studied language-model support for medical information retrieval. Son et al. {c('emr')} built a RAG "
          f"chatbot over electronic-medical-record manuals; with 5,931 question-document pairs they fine-tuned two multilingual embedding models and reported retrieval accuracy of 97.6% for BGE-M3 and 89.7% for "
          f"Multilingual-E5-Large, with query latency under 10 ms. ClinicBot {c('clinicbot')} grounds answers in the American Diabetes Association guideline, extracts it into units with provenance, ranks "
          f"evidence by clinical significance, not text similarity, and shows citations; it is a system demonstration without an accuracy table. Xiong et al. {c('medrag')} benchmarked "
          "RAG components - corpora, retrievers and language models - for medical question answering. Three further RAG chatbots appear in the batch literature survey "
          f"({c('survey2', 'survey3', 'survey4')}); their full texts could not be located, so nothing beyond their titles is claimed here."),
        H3("2.3.3 Retrieval and reranking components"),
        P(f"Dense retrieval [{R['dpr']}] represents query and passage as vectors and compares them; Sentence-BERT {c('sbert')} made such embeddings practical for sentences, and MiniLM {c('minilm')} "
          f"distilled a small, fast model that gives the all-MiniLM-L6-v2 embeddings used here. FAISS {c('faiss')} provides exact and approximate nearest-neighbour search. BM25 {c('bm25')} remains a strong "
          f"lexical baseline and is covered in standard texts {c('irbook')}. Fusion of several rankings is well established; reciprocal rank fusion {c('rrf')} is one rank-based scheme, and weighted "
          f"combination of normalised scores, used here, is another. Cross-encoders such as monoBERT {c('monobert')} read query and candidate together and, trained on MS MARCO {c('msmarco')}, give "
          f"better ordering than the first-stage scores at a higher cost. HyDE {c('hyde')} asks a language model to write a hypothetical answer document and retrieves with that; this project's "
          "version is a fixed text template, not a language-model call, so it borrows the idea but not the mechanism."),
        H3("2.3.4 Generation and safety"),
        P(f"Instruction-tuned models such as Flan-T5 {c('flan')} follow prompts at small sizes and are available through the Hugging Face library {c('hf')}. Hallucination remains an "
          f"open problem {c('halluc')}, and while large models encode clinical knowledge {c('medpalm')}, the same work stresses the need for human evaluation. This is why the project keeps the answer "
          "tied to retrieved records and adds explicit emergency rules rather than trusting a model to recognise danger."),

        H2("2.4 Data and Algorithms Used in This Project"),
        P(f"**Data.** The base paper's data set is not available or described in enough detail to reuse, and no public symptom-disease base was used. The project's knowledge base is built by "
          f"`scripts/prepare_data.py` from a hand-written table: {F.KB['conditions']} conditions, each with a description, guidance, severity and red flags, and several symptom-subset variants, giving "
          f"{F.KB['records']} records. Each record has retrieval text of the form \"Disease: ... Symptoms: ... Description: ... Guidance: ...\". It is labelled synthetic."),
        P("**Algorithms.** The query is lower-cased and tidied, split on commas and conjunctions, and wrapped in a template sentence. The combined text is embedded (384 dimensions, normalised) and searched in a "
          f"FAISS inner-product index; the same text is tokenised and scored by BM25. Each list is min-max normalised over the union of candidates and fused:"),
        EQ(f"score(d) = {F.FUSION_WEIGHTS[0]} · norm(sem(d)) + {F.FUSION_WEIGHTS[1]} · norm(lex(d))"),
        P(f"The {F.CANDIDATE_K} best fused candidates are scored by the cross-encoder ms-marco-MiniLM-L-6-v2 and the top {F.TOP_K} are kept. The displayed relevance is the reranker score "
          "scaled by min-max over the candidates, which is why its maximum is always 1.00 (Chapter 8)."),

        H2("2.5 Summary of the Surveyed Works"),
        TAB("Surveyed works: approach, data, reported result, limitation", ["Work", "Approach", "Data", "Reported result", "Limitation"], [
            [f"Base paper {c('base')}", "Embeddings + FAISS + RAG; web app with history", "Symptom-disease base, size not stated", "Qualitative only", "No numbers; no safety or reranking"],
            [f"Divya et al. {c('divya')}", "AI self-diagnosis chatbot", "Not stated in base paper", "Qualitative", "No grounding in a source"],
            [f"Hsu, Yu {c('hsu')}", "ML + language understanding chatbot", "Not stated in base paper", "Better than rule-based (as summarised)", "Learned, ungrounded"],
            [f"Peri et al. {c('peri')}", "RAG over medical books", "Medical books", "Qualitative in base paper", "Chat over text, not symptom triage"],
            [f"Son et al. {c('emr')}", "RAG over EMR manuals, tuned embeddings", "5,931 question-document pairs", "97.6% / 89.7% retrieval accuracy; < 10 ms", "Hospital manuals, not symptoms"],
            [f"ClinicBot {c('clinicbot')}", "Guideline extraction, evidence priority, citations", "ADA Standards of Care 2025", "Demonstration", "One disease area; no accuracy table"],
            [f"Xiong et al. {c('medrag')}", "RAG benchmark for medical QA", "Medical QA sets", "Benchmark and toolkit", "Question answering, not symptom entry"],
            [f"Gao et al. {c('hyde')}", "Hypothetical-document query expansion", "Retrieval benchmarks", "Gains over unsupervised dense retrieval", "Needs a language-model call"],
        ], widths=[1.2, 1.5, 1.2, 1.25, 1.25], size=8.5, align=["l", "l", "l", "l", "l"]),

        H2("2.6 The Batch Literature Survey"),
        P("The project's own literature survey lists five sources. They are reproduced with the extent to which each could be verified."),
        TAB("Sources in the batch literature survey", ["No.", "Source", "Verification"], [
            ["1", f"Base paper, IJERST 2026 {c('base')}", "Read in full (PDF); no numbers reported"],
            ["2", f"RAG framework for medical question answering, Iconic Research and Engineering Journals, 2026 {c('survey2')}", "Not found online; title and source only"],
            ["3", f"Book-verified RAG medical chatbot, ICICV 2026 {c('survey3')}", "Not found online; title and source only"],
            ["4", f"Healthcare chatbot with RAG, Int. J. Pharmacy with Medical Sciences, 2026 {c('survey4')}", "Not found online; title and source only"],
            ["5", f"RAG-based EMR chatbot, Healthcare Informatics Research, 2025 {c('emr')}", "Verified on the journal page: 5,931 pairs, 97.6% / 89.7%, < 10 ms"],
        ], widths=[0.5, 4.0, 1.8], size=9.5, align=["c", "l", "l"]),
        P("Strengths of the literature as a whole: retrieval-grounded answering is well motivated and increasingly benchmarked, and the retrieval building blocks are mature and openly available. "
          "Its limitations: symptom-oriented RAG work reports little quantitative evidence, often on private or unspecified data; safety escalation is rarely evaluated; and the cost of running these "
          "systems on ordinary hardware is seldom measured."),

        H2("2.7 Research Gap"),
        P("The base paper establishes a hybrid RAG framework for symptom monitoring. The gap addressed here is adding longitudinal symptom tracking and personalised health insight on top of that retrieval "
          "pipeline. The survey shows four concrete gaps around it:"),
        N("**Evidence.** The base paper's claims are untested; there is no baseline, test set or latency figure to compare against.",
          "**Retrieval quality.** Combining dense and lexical retrieval with a neural reranker is standard elsewhere but is absent from the symptom-monitoring framework, and nobody had measured what each stage adds.",
          "**Safety.** Emergency recognition and medication-instruction filtering are not described, although the domain demands them.",
          "**Tracking.** Longitudinal tracking is promised but not realised: the base paper stores consultations and stops there."),
        P("This project closes the first three gaps in part - by building the stages, measuring them and reporting what failed - and delivers only the storage half of the fourth, which is stated "
          "as an unmet objective in Chapters 1, 8 and 9."),
    ]
