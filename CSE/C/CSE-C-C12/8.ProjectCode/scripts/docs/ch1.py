"""Chapter 1: Introduction."""

from . import facts as F
from .blocks import B, H1, H2, N, P, TAB
from .refs import CITE as R

OBJECTIVES = [
    "Build a curated medical knowledge base and index it for semantic retrieval.",
    "Accept symptoms described in natural language and expand the query to improve recall.",
    "Implement hybrid retrieval combining dense vector search with neural reranking.",
    "Generate grounded responses that cite the retrieved source for every statement.",
    "Track reported symptoms over time to reveal progression and trends.",
    "Evaluate retrieval relevance, answer groundedness and response time.",
]


def blocks():
    s2, s3, s4 = (F.SHIP[k] for k in ("S2_verbatim_leave_one_out_176", "S3_two_symptoms_leave_one_out_176", "S4_lay_language_60"))
    k = F.KB
    base = R["base"]
    return [
        H1("CHAPTER 1: INTRODUCTION"),
        P(f"This chapter introduces the domain of the project, the motivation for building {F.PRODUCT}, the problem it addresses, the objectives set for it, the scope that was actually delivered, "
          "the contributions, and the limitations and assumptions that govern every result reported later. It ends with a map of the rest of the report. The project title is SymptoTrackAI; "
          f"the web application that implements it carries the name {F.APP_NAME} in the code and on screen, and the report uses the two names accordingly."),

        H2("1.1 Domain and Background"),
        P("Healthcare informatics is the use of computing to collect, organise and present health information. One of its most visible applications is the symptom checker: a person describes "
          "what they feel and receives information about what it might mean and how urgent it is. The idea is attractive because the first step in most illnesses is a question asked at home "
          "- is this serious, should I wait, should I see someone - and because access to a clinician is not always quick or convenient."),
        P(f"Conversational language models have made it possible to ask that question in ordinary words. Studies of their medical ability show that large models encode a good deal of clinical "
          f"knowledge [{R['medpalm']}], but they also produce fluent text that is wrong, a failure known as hallucination [{R['halluc']}], and in health a confident wrong answer can do harm. "
          f"Retrieval-augmented generation (RAG) [{R['rag']}] addresses this by retrieving passages from a curated source and letting the answer draw only on them. The base paper assigned to the batch "
          f"[{base}] applies this idea to symptom monitoring: it retrieves symptom-disease records with FAISS similarity search [{R['faiss']}], and it stores each consultation so that a user can review their history."),
        P("Retrieval itself has two classic forms. Dense retrieval compares embeddings of the query and the records, so that \"stuffy nose\" can match \"nasal congestion\" "
          f"[{R['dpr']}], [{R['sbert']}]. Lexical retrieval such as BM25 [{R['bm25']}] matches the words themselves and is exact and fast but blind to synonyms. A cross-encoder reranker "
          f"[{R['monobert']}] reads the query and a candidate together and scores them more carefully than either retriever can. {F.PRODUCT} combines all three."),

        H2("1.2 Motivation"),
        B("Patients often delay consultation because early symptoms seem minor or access is inconvenient.",
          "Self-diagnosis through web search produces alarming and frequently wrong conclusions.",
          "Language models can interpret symptoms described in ordinary language, but ungrounded models hallucinate, which is unacceptable in a health context.",
          "A health application that must run on an ordinary computer, keep the person's records on that computer and need no paid service is useful to a student team, a small clinic or a classroom."),
        P("A further motivation is methodological. The base paper reports its results only as \"experimental observations\" and shows one example conversation, so its claims cannot be checked. "
          "This project therefore treats measurement as part of the work: every number in this report was produced by a script that can be re-run (Chapter 8)."),

        H2("1.3 Problem Statement"),
        B("Self-diagnosis through general web search yields inaccurate and frightening results.",
          "General chatbots answer from public data with no medical grounding or citation.",
          "Symptoms are recorded as isolated events, so progression over time is never visible.",
          "An ungrounded health answer can cause real harm if acted upon."),
        P("The problem can be stated as follows: given a free-text description of symptoms, return the most relevant medical information from a curated knowledge base, show the records the answer rests on, "
          "escalate clearly when the text describes a possible emergency, and keep a private history of consultations - all on a machine without a GPU and without sending the person's text to a third party."),

        H2("1.4 Need for the System"),
        P("The need, as the project's problem statement puts it, is a symptom assistant that answers only from a curated medical knowledge base, cites its sources and tracks symptoms over time. "
          "Three needs follow. The answer must be grounded, because the cost of an unsupported statement is high. The system must be explicit about what it does not know, because a symptom list "
          "cannot establish a diagnosis. And the person's data must stay under their control, because symptom text is sensitive."),

        H2("1.5 Objectives"),
        P("Six objectives were set at the start of the project. the table below repeats them and gives the final status; the evidence for each status is in Chapters 7 and 8."),
        TAB("Objectives and their final status", ["No.", "Objective", "Status", "What was delivered"], [
            ["1", OBJECTIVES[0], "Achieved, with a synthetic base", f"{k['records']} records, {k['conditions']} conditions, FAISS and BM25 indexes; written by the team, not clinically validated"],
            ["2", OBJECTIVES[1], "Achieved", "Normalisation and a rule-based HyDE-style template; its measured effect is neutral to negative"],
            ["3", OBJECTIVES[2], "Achieved and measured", f"Fusion and cross-encoder; top-1 {F.pct(s4['top1'])} on {s4['n']} everyday-language probes"],
            ["4", OBJECTIVES[3], "Partly", "Answers are built from retrieved records and shown with evidence cards; no per-statement citation"],
            ["5", OBJECTIVES[4], "Not achieved beyond storage", "Consultations are saved, searchable and deletable; no trend or progression analysis"],
            ["6", OBJECTIVES[5], "Partly", "Retrieval relevance and response time measured; groundedness checked only structurally"],
        ], widths=[0.4, 2.0, 1.2, 2.7], size=9.5, align=["c", "l", "l", "l"]),

        H2("1.6 Scope of the Work"),
        P("In scope: registration and sign-in; symptom entry in free text; query normalisation and expansion; dense and lexical retrieval over the knowledge base, fusion and reranking; an evidence-based "
          "answer with a safety layer; storage, search, review and deletion of consultations per user; a React web interface with light and dark themes; and the scripts that measure the pipeline. "
          "Out of scope: diagnosis, prescription or dosage advice, images, voice, clinical validation, multi-language support, and any integration with hospital systems. Chapter 4 gives the requirements "
          "and the full scope and limitations appear in Chapter 9."),

        H2("1.7 Contributions"),
        N(f"A working implementation of a hybrid RAG symptom assistant that runs on a CPU-only PC: MiniLM embeddings with FAISS, BM25, weighted fusion, a cross-encoder reranker and an evidence-based answer, behind a FastAPI service and a React interface.",
          "A fall-back design in which each model-dependent stage has an offline alternative (TF-IDF vectors, hybrid order without reranking, template answer), so the system still answers without model downloads.",
          "A rule-based safety layer with ten emergency patterns, a caution list, a permanent disclaimer and an answer filter for medication instructions.",
          f"A reproducible evaluation (Chapter 8): an ablation of seven retrieval configurations on five query sets, leave-one-out testing, a probe set in everyday language, and measurements of the safety layer and of latency.",
          "An honest account of what the evaluation exposed: an inflated shipped metric, a generator that echoes its prompt, a relevance display that hides the model's own signal, and gaps in the safety rules."),

        H2("1.8 Limitations and Assumptions"),
        P(f"The knowledge base is synthetic: it was generated by script from a hand-written table of {k['conditions']} conditions, so there is only one description and one piece of guidance per condition, "
          f"shared by all of its records. Accuracy on it says how well the pipeline finds a condition whose wording it has seen, not how well it would help a patient. Probe queries and safety "
          f"test sentences were written by the authors, who are not clinicians, so they test the software, not clinical accuracy. The assumptions are that users write in English, that the "
          f"machine has about {F.ENV['ram_gb']} GB of memory for the three models, and that a person who receives an emergency notice will act on it. {F.PRODUCT} is information, not medical advice."),
        P(f"For orientation: with the full pipeline the correct condition is first for {F.pct(s2['top1'])} of {s2['n']} leave-one-out verbatim queries, {F.pct(s3['top1'])} of {s3['n']} queries "
          f"giving two symptoms, and {F.pct(s4['top1'])} of {s4['n']} everyday-language probes (95% interval {F.ci('hybrid_rerank', 'S4_lay_language_60')}). These are measured on the synthetic base."),

        H2("1.9 Organisation of the Report"),
        TAB("Chapters of this report", ["Chapter", "Title", "Content"], [
            ["1", "Introduction", "Domain, motivation, problem, objectives, scope, contributions"],
            ["2", "Literature Survey", "Base paper analysis, related work, gap"],
            ["3", "Feasibility Study", "Technical, economic, operational and schedule feasibility"],
            ["4", "System Requirements and Analysis", "Existing and proposed system, requirements, users"],
            ["5", "System Design", "Architecture, DFDs, UML, database, modules, interface"],
            ["6", "Methodology and Software Implementation", "Pipeline, algorithms, API, security, installation"],
            ["7", "System Testing", "Strategy, unit, integration, security, performance"],
            ["8", "Results and Output Screens", "Measurements, screens, comparison, objectives versus outcomes"],
            ["9", "Conclusion", "Summary, findings, known limitations"],
            ["10", "Future Scope", "Improvements and further research"],
        ], widths=[0.7, 2.4, 3.2], align=["c", "l", "l"], size=10),
        P("The references and three appendices (important code, installation and user guide, additional screens) follow Chapter 10."),
    ]
