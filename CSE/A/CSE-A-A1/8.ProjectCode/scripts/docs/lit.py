"""Shared text used by the decks, the chapter documents, the report and (in condensed form) the paper: objectives, problem statement,
base-paper summary, research gap and the literature table. Reference numbers [n] follow refs.py."""

# from 6.OBJECTIVES&PROBLEM STATEMENT.docx, verbatim
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
    "General purpose chatbots answer from public internet data rather than the student's own prescribed syllabus.",
    "Students have no single view of what has been studied, what remains, and how well each topic is understood.",
]

NEED = ("a platform that ingests a student's own academic documents, answers strictly from them with citations, and adapts the study plan to "
        "measured topic mastery.")

PROBLEM_STATEMENT = ("Given a student's own academic documents (syllabi, lecture notes, question banks), extract the subjects, units and topics they contain, "
                     "answer the student's questions strictly from that material and show the source passage, test the student on it, and turn the quiz results "
                     "into a topic-wise priority list and dashboard - through a web application that a student can run on an ordinary laptop with no GPU and "
                     "no paid service, with its retrieval and answer quality reported honestly on the data actually available.")

# ---------------------------------------------------------------------------------------------------------------- base paper
BASE_PAPER_SUMMARY = [
    "SAC-RAG [1] (IEEE Access 2026) joins question-type-adaptive retrieval and context compression in one RAG framework; an LLM classifier labels each query Fact, "
    "Definition or Reasoning (92.0% agreement with manual labels on 300 questions).",
    "Retrieval depends on the type: Fact uses BM25 plus dense vectors with a BGE cross-encoder rerank (top 10); Definition uses dense vectors only (top 8); "
    "Reasoning decomposes the question into sub-questions, retrieves in parallel, merges and reranks.",
    "A unified LLM compression step extracts evidence snippets from the retrieved passages before the answer is generated.",
    "Evaluation: HotpotQA, 2WikiMultiHopQA and MuSiQue, 1,000 questions each, gpt-5-mini at temperature 0, four settings (Naive, Compress, Adaptive, SAC-RAG), "
    "measured by Exact Match, F1, Recall@10 and tokens.",
    "Headline results: adaptive retrieval raises HotpotQA EM from 0.560 to 0.611 and Recall@10 from 0.787 to 0.880; compression cuts tokens by 38-58% for a 1-2 point EM drop; "
    "reasoning-question EM rises from 0.455 to 0.577 after compression on HotpotQA.",
    "Cost: about 27.8 s per instance against 9.6 s for naive RAG on HotpotQA, because of the extra LLM calls for classification, decomposition and compression.",
    "What the base paper does not cover: a student's own documents, quizzes or any learning analytics; it evaluates open-domain multi-hop QA only.",
]

# ---------------------------------------------------------------------------------------------------------------- gap
GAP_BATCH = ("Existing work applies RAG to general question answering and context compression. None of the surveyed systems combines document ingestion, "
             "syllabus-grounded tutoring and progress analytics for a student's own curriculum.")

GAP = (GAP_BATCH + " This project fills that gap with a working platform, but only in part: it ingests PDF, DOCX and TXT notes and recognises subject and unit headings "
       "written in a few common forms; it retrieves with TF-IDF (lexical vectors) and not with learned embeddings; it answers by extracting key sentences (a simple form of "
       "compression), or through Claude when an API key is set; it cites the source file and passage for every answer; it generates fill-in-the-blank quizzes and ranks topics "
       "by quiz accuracy. It does not implement question-type routing, LLM compression, revision schedules, knowledge tracing or curriculum-coverage tracking, and it has no "
       "relevance threshold, so an off-topic question can still receive an extracted answer.")

# ---------------------------------------------------------------------------------------------------------------- literature table
# (Work, Approach, Data, Reported result, Limitation). Only facts read in the PDFs or verified on the web (see refs.py).
LIT_TABLE = [
    ["Zhang et al. 2026 [1] (base paper)", "Question-type classifier; type-specific retrieval (BM25 + dense + rerank, dense only, sub-question decomposition); unified LLM context compression",
     "HotpotQA, 2WikiMultiHopQA, MuSiQue; 1,000 questions each; gpt-5-mini",
     "EM 0.560 -> 0.611 and Recall@10 0.787 -> 0.880 (HotpotQA, adaptive vs naive); tokens down 38-58% for a 1-2 point EM drop",
     "Open-domain multi-hop QA only; 27.8 s vs 9.6 s per instance; no student documents or analytics"],
    ["Li et al. 2024 [2] (TutorLLM)", "Knowledge tracing (MLFBK, BERT-based) predicts the learner state; RAG over a knowledge base scraped from online course material; LLM writes recommendations",
     "Online linear-algebra course; two-week crossover study with 30 undergraduates",
     "10% higher user satisfaction (SUS) and 5% higher quiz scores than a general LLM alone",
     "Knowledge base comes from course websites, not the student's own files; small sample; short study"],
    ["Vatankhah Barenji et al. 2026 [3]", "Agentic LLM assessment over a RAG store of rubric criteria, exemplar essays and instructor feedback",
     "701 student essays; human assessors agree at Cohen's kappa 0.63",
     "94-99% agreement with human evaluators; rubric-aligned formative feedback at scale",
     "Grades essays, does not tutor from a student's notes; pedagogical limits on originality and dialogue noted by the authors"],
    ["Kaczmarek et al. 2025 [19]", "RAG pipeline with query rephraser, improved retrieval and reranker for medical explanations, combined with spaced repetition",
     "Questions of the Polish State Specialization Examination; medical annotators and specialists check output",
     "Relevant documents among the top 10 rose from 4.59 to 6.83 on average",
     "Single exam domain; spaced repetition applied to a fixed exam, not to a student's own documents"],
    ["Gokhman et al. 2025 [20] (VL-RAG)", "Vision-language RAG retrieves tailored answers and images for text and image questions; web teaching platform",
     "Course content for machine learning, neural networks and deep learning",
     "Abstract reports no numeric result", "No quantitative evaluation in the abstract; instructor-prepared content, not student uploads"],
    ["Eleuterio et al. 2025 [21]", "Web scraper builds a knowledge base from a national financial-education portal; RAG chatbot behind an API for LMS and mobile embedding",
     "Public financial-education portal content", "Abstract states grounding reduces hallucination; no numeric result read",
     "Fixed public source; no personalisation or progress tracking"],
    ["Jeong et al. 2024 [11] (Adaptive-RAG)", "Routes each question to no retrieval, single-step or multi-step retrieval by predicted complexity",
     "Not read directly (described in [1])", "Results not quoted here", "No context compression (as noted in [1])"],
    ["Jiang et al. 2023 [10] (LLMLingua)", "Small language model drops low-information tokens to compress the prompt", "Not read directly (described in [1])",
     "Results not quoted here", "Works on top of a fixed retrieval strategy (as noted in [1])"],
    ["Liu et al. 2024 [12] (Lost in the middle)", "Studies how language models use information placed at different positions of a long context",
     "Not read directly (described in [1])", "Relevant evidence inside long retrieved contexts can be overlooked (as cited in [1])",
     "Motivates compression; does not propose a tutoring system"],
    ["Batch item 5 [22] (ZDM Mathematics Education, 2026)", "Student-built educational resources for the Lean theorem prover with ChatGPT and RAG",
     "Resources made by five university students (from the abstract excerpt found)", "Details not verified", "Authors, pages and results could not be confirmed"],
]

# Theme grouping used by chapter 2 and the paper: reference numbers per theme
THEMES = {
    "retrieval-augmented generation": [4, 27, 30, 24, 23, 14],
    "retrieval methods": [5, 6, 7, 8, 9],
    "context compression and adaptive retrieval": [1, 10, 11, 12, 15, 25, 26],
    "RAG in education and tutoring": [2, 3, 19, 20, 21, 22],
    "learning analytics and knowledge tracing": [2, 17],
    "benchmarks and tools": [13, 28, 29, 16, 18],
}

# Batch-survey items whose details stay unverified (the batch file gives title, year and venue only)
SURVEY_UNVERIFIED = [
    "Student-designed educational resources for Lean: exploring ChatGPT and Retrieval-Augmented Generation (ZDM - Mathematics Education, 2026): "
    "Springer lists a 2026 article of this title but two listings disagree on the authors; no authors, pages or results are quoted.",
]
