"""Chapter 1: Introduction."""

from . import facts as F
from .blocks import B, H1, H2, N, P, TAB

# Batch objectives (6.OBJECTIVES&PROBLEM STATEMENT.docx), kept here so the chapter does not depend on lit.py being ready.
OBJECTIVES = [
    "Build a document ingestion module that parses syllabi, lecture notes and question banks and extracts subjects, units and topics.",
    "Store the extracted content as vector embeddings so the material can be searched semantically rather than by keyword.",
    "Implement a RAG question-answering engine that answers strictly from the uploaded material and cites the source.",
    "Apply semantic context compression so retrieval stays accurate without exceeding the model context window.",
    "Generate personalised study roadmaps and revision schedules from topic coverage and performance.",
    "Present curriculum coverage, study velocity and engagement metrics on an interactive dashboard.",
]

PROBLEM_POINTS = [
    "Learning platforms store academic files but never extract the units, topics or learning objectives inside them.",
    "Recommendations are identical for every learner and ignore prior performance and study behaviour.",
    "General-purpose chatbots answer from public internet data rather than the student's own prescribed syllabus.",
    "Students have no single view of what has been studied, what remains, and how well each topic is understood.",
]

NEED = ("A platform that ingests a student's own academic documents, answers strictly from them with citations, and adapts the study plan to "
        "measured topic mastery.")


def blocks():
    sh = F.SHIPPED
    cmp4 = F.CMP["4"]
    ab = F.ABS
    return [
        H1("CHAPTER 1: INTRODUCTION"),
        P("This chapter introduces the domain, the motivation, the problem, the objectives, the scope that was actually delivered, the contributions and the limitations that govern every "
          "result reported later. It closes with a map of the report."),

        H2("1.1 Domain and Background"),
        P("The project belongs to learning analytics and AI-assisted tutoring. A student of an engineering programme handles, in every semester, scattered PDFs, syllabi, lecture notes and question banks "
          "for six to eight subjects. Conventional e-learning portals store these files but do not look inside them: the units, topics and learning objectives stay locked in the documents, "
          "and the portal can neither answer a question from them nor say which topics deserve revision."),
        P("Large Language Models (LLMs) explain concepts well but hallucinate when they are not grounded in a trusted source, and a general chatbot answers from public data rather than from the "
          "syllabus the student is studying. Retrieval-Augmented Generation (RAG) retrieves the relevant passage first and generates the answer only from it [4]. "
          "Retrieval can be lexical, using term statistics such as TF-IDF [7] or BM25 [6], or dense, using learned embeddings [5], [9]. A second line of work compresses the retrieved "
          "context so that an answer stays within the model's context window and is not distracted by redundant text [10], [12]."),
        P("The base paper, SAC-RAG by Zhang et al. [1], combines both ideas for open-domain question answering: an LLM classifies each question as factual, definitional or reasoning, "
          "a different retrieval strategy is applied to each type, and an LLM compresses the retrieved passages into evidence snippets before the answer is generated. On three multi-hop "
          "datasets the authors report that compression cuts token consumption by 38-58% at the cost of one to two points of exact match. The paper does not "
          "treat document ingestion, quizzes or learner analytics. The Adaptive Learning Intelligence Platform (ALIP) takes the retrieve-then-answer idea of [1] and builds around it the "
          "parts a student needs: ingestion of the student's own files, source-cited answers, quizzes and a study roadmap. SAC-RAG's question classifier, type-specific retrieval and LLM compression "
          "are not implemented here, and the retriever is lexical, not semantic; Chapters 2 and 8 return to this difference."),

        H2("1.2 Motivation"),
        P("Four observations motivate the work. They come from the batch problem statement and from the literature on AI in education [2], [3]."),
        B("**Study material is stored but not understood.** Nothing extracts the units and topics that PDFs and notes contain, so there is no structured view of the syllabus.",
          "**Answers are not grounded in the student's syllabus.** An examination candidate needs answers that come from the prescribed notes and point back to the passage used.",
          "**Recommendations ignore performance.** Knowledge-tracing work such as TutorLLM [2] combines a learning state with retrieval, but needs interaction logs and a trained model that a single student does not have.",
          "**No single view of progress.** A student cannot see what has been studied, what remains and how well each topic is understood."),
        P("A system that answers from the student's own files and records performance per topic addresses all four with data the student already has: the documents, the questions asked and the quizzes taken. "
          "The retrieval and answering parts run on an ordinary laptop with no paid service."),

        H2("1.3 Problem Statement"),
        P("The batch problem statement lists four weaknesses of current learning platforms:"),
        B(*PROBLEM_POINTS),
        P("Written as a task for software, the problem addressed by this project is:"),
        P("*Given the documents a student uploads (syllabi, notes, question banks, timetables), extract their subjects, units and topics into a searchable knowledge repository; answer the student's "
          "questions using only that repository and show the passage each answer came from; generate practice questions from the same material; and turn the quiz results into a "
          "priority-ranked study roadmap and a dashboard, through a web application that runs on an ordinary PC.*"),
        P("**Research gap.** The surveyed RAG work in education (Chapter 2) applies RAG to question answering, to assessment, to tutoring in one subject, or studies context compression on benchmarks. "
          "None of the surveyed systems combines document ingestion, syllabus-grounded tutoring and progress analytics for a student's own curriculum."),

        H2("1.4 Need for the Proposed System"),
        P("The batch documents summarise the need in one sentence: " + NEED[0].lower() + NEED[1:] + " Three properties follow. Answers must be traceable: each lists the file, the passage "
          "number and a match score. The system must work offline and at no cost: the default answerer is extractive and needs no network. "
          f"And it must feel interactive: a question is answered in about {F.API['ask']['median_ms']:.0f} ms (median over "
          f"{F.API['ask']['n']} calls with {F.CORPUS['chunks']} chunks indexed) and a quiz is generated in about {F.API['quiz_generate']['median_ms']:.0f} ms (Chapter 8)."),

        H2("1.5 Objectives"),
        P("The six objectives are those of the batch document 6.OBJECTIVES&PROBLEM STATEMENT. The table states how each was addressed and whether it was met; "
          "\"Partly\" and \"Not met\" are used where the work fell short, and Chapter 8 gives the evidence."),
        TAB("Objectives and their status", ["No.", "Objective", "How it was addressed", "Status"],
            [["O1", OBJECTIVES[0],
              f"PDF, DOCX and TXT are parsed and chunked. Headings of the form \"Subject:\", \"Course:\", \"Unit N:\" and \"Chapter N:\" are found "
              f"({F.DOCAN['unit_recall'] * 100:.0f}% of the 36 unit headings of the test corpus), plus up to 12 TF-IDF topics. \"UNIT-I\", \"Module 1\" and Word tables are not handled.", "Partly"],
             ["O2", OBJECTIVES[1],
              "Chunks are indexed with TF-IDF (unigrams and bigrams), a sparse lexical representation, not a learned embedding. "
              f"A dense model was measured only as an experiment (Hit@4 {F.hit('dense_bge_small', 4):.3f} against {F.hit(sh, 4):.3f} for the shipped retriever).", "Not met"],
             ["O3", OBJECTIVES[2],
              f"Every answer word occurs in the retrieved chunks, and each answer lists file, passage and score. Hit@4 is {F.hit(sh, 4):.3f}. "
              f"There is no relevance threshold: {ab['off_topic_answered_by_shipped']} of {ab['n_off_topic']} off-topic questions still received an answer. "
              "The optional Claude mode was not measured.", "Met for extractive mode"],
             ["O4", OBJECTIVES[3],
              f"Extractive sentence selection removes {cmp4['token_reduction_pct']:.1f}% of the words, but answer-key recall falls from {cmp4['key_in_ctx']:.3f} to {cmp4['key_in_ans']:.3f}. "
              "SAC-RAG's classifier-driven retrieval and LLM compression are not implemented.", "Partly"],
             ["O5", OBJECTIVES[4],
              "Quiz accuracy per topic is bucketed High (below 50), Medium (below 80) and Low. There is no revision schedule or coverage model; topics are single TF-IDF keywords.", "Partly"],
             ["O6", OBJECTIVES[5],
              "The dashboard shows documents, questions, quiz attempts, a subject-wise accuracy chart and recent documents. Coverage and study velocity over time are absent.", "Partly"]],
            widths=[0.45, 2.0, 3.45, 0.9], align=["c", "l", "l", "c"], size=9.5),

        H2("1.6 Scope of the Project"),
        P("**In scope.** (i) Upload of PDF, DOCX and TXT material up to 16 MB; (ii) text extraction, chunking, subject and topic detection and a per-user knowledge repository; "
          "(iii) retrieval and cited extractive answering, with an optional LLM mode; (iv) generated fill-in-the-blank quizzes with server-side grading; (v) a priority-ranked roadmap and a "
          "dashboard; (vi) registration and login with hashed passwords; (vii) two interfaces over one Python core, a React application on a FastAPI service and the original Flask "
          "application; (viii) tests, measurements and documentation."),
        P("**Out of scope.** Learned embeddings and a vector database, question-type classification, LLM-based compression, revision scheduling, knowledge-tracing models, "
          "coverage and study-velocity analytics, optical character recognition for scanned PDFs, teacher or administrator roles, and any study with real students."),

        H2("1.7 Contributions"),
        N("**An end-to-end, offline-capable study platform** that joins document ingestion, source-cited answering, quizzes and a priority roadmap in one application with a React front end, "
          "a 14-endpoint FastAPI service and the original Flask interface.",
          "**A document-to-knowledge-repository pipeline** that extracts text from three formats, chunks it with overlap, detects subject and unit headings and ranks topics by TF-IDF.",
          "**A grounded answering path** whose extractive answers contain only words of the retrieved chunks and name the source file, passage and match score.",
          f"**A measured evaluation of the retrieval and compression steps.** A six-subject corpus of {F.CORPUS['words']:,} words and {F.CORPUS['questions']} hand-written questions compares the shipped TF-IDF retriever with "
          f"BM25 and a dense reference, measures what extractive compression costs ({cmp4['token_reduction_pct']:.1f}% fewer words for a drop of {(cmp4['key_in_ctx'] - cmp4['key_in_ans']) * 100:.1f} points of answer-key recall) and shows where the system fails.",
          f"**Reproducible tooling.** A pytest suite of {F.TESTS['tests']} tests, a {F.SMOKE_TOTAL}-check API smoke test, and scripts that rebuild the corpus, experiments, figures, diagrams and screenshots."),

        H2("1.8 Limitations and Assumptions"),
        B(f"**Retrieval is lexical.** The shipped retriever reaches Hit@1 {F.hit(sh, 1):.3f} and Hit@4 {F.hit(sh, 4):.3f}; BM25 reaches {F.hit('bm25', 1):.3f} and {F.hit('bm25', 4):.3f}, and BM25 with a dense model {F.hit('hybrid_bm25_dense', 1):.3f} and {F.hit('hybrid_bm25_dense', 4):.3f}.",
          "**No relevance threshold.** The engine refuses only when no query term occurs in any chunk, so off-topic questions can receive an irrelevant extract.",
          f"**Quizzes are cloze questions on keywords.** The answer term stays visible in the stem in {F.QUIZ['answer_repeated_in_stem_rate'] * 100:.1f}% of generated questions, and only {F.AUDIT['summary']['acceptable']} of {F.AUDIT['summary']['n']} questions in a manual review were acceptable.",
          "**Narrow heading detection, local-demo security.** Only Arabic-numeral headings are recognised; the session cookie is not Secure; two uploads with the same file name share one file on disk.",
          "**Evaluation data is not student data.** The measurements use Wikipedia articles arranged as course notes and 72 questions written for this work; no real syllabi, no study with students and no measurement of the Claude mode were possible."),
        P("Assumptions: each student uploads text-based English documents; subject names are typed at upload; a quiz answer is correct only when the chosen option equals the blanked term; "
          "topic accuracy is computed over all quiz questions sharing a topic keyword; and the measurement machine was shared with other work, so timings are medians of repeated runs."),

        H2("1.9 Organisation of the Report"),
        P("Chapter 2 surveys the base paper and related work. Chapter 3 assesses feasibility and Chapter 4 states the requirements. Chapter 5 gives the design (architecture, data flow diagrams, UML, database, "
          "modules, interface) and Chapter 6 the methodology and implementation (data, algorithms, formulation, API, security, installation). Chapter 7 reports testing. Chapter 8 presents the output screens, "
          "the retrieval and compression results, the comparison with the base paper and the failure analysis. Chapters 9 and 10 give the conclusion and the future scope. The references and three appendices "
          "(important code, installation and user guide, additional screens) follow."),
    ]
