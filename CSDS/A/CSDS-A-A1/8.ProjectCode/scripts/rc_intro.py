"""Chapter 1 content: domain, motivation, problem, need, objectives, scope, contributions, limitations, organisation."""
from __future__ import annotations

from doc_common import PRODUCT


def sec_domain(d):
    d.h2("Introduction to the Project Domain")
    d.paras(
        "Health insurance is the main financial protection most families have against the cost of hospital treatment. In India it is sold "
        "through dozens of products from many insurers, and each product is defined by a policy wording: a document of twenty to sixty "
        "pages that sets out what is covered, what is excluded, how long a policyholder must wait before certain treatments are covered, "
        "what share of each bill the policyholder pays, and how a claim must be made. The policyholder is expected to read and understand "
        "this document, but it is written in dense legal and technical language and is rarely read in full.",
        "The domain of this project is therefore **document understanding for insurance**, and more precisely **question answering and "
        "claim guidance over a single long, clause-structured legal document**. It sits between several established areas of computer "
        "science. Retrieval-augmented generation (RAG) [7] grounds a large language model (LLM) in text retrieved from a trusted source. "
        "Classical information retrieval supplies keyword ranking such as BM25 [8] and rank fusion [9]. Dense sentence embeddings [10], "
        "[11] and cross-encoder re-ranking [12] supply semantic matching. Natural-language inference [14] can check whether a statement "
        "is supported by a text.",
        f"**{PRODUCT}**, the system built in this project, combines these ideas into one application. A person uploads their policy wording "
        "(or opens one of four sample wordings); PolicyLens parses it into numbered clauses with page positions, builds a **Policy Card** "
        "that lists the key terms with the clause and page that support each value, answers questions in plain language with citations, "
        "flags the fine print that tends to cost money at claim time, checks a planned claim, and compares two policies. The title of the "
        "project, *AI Health Insurance Assistance Using LLM + RAG*, should be read in exactly that sense: a large language model does the "
        "writing, but retrieval decides what it is allowed to say, and independent checks measure how well each answer is supported.")


def sec_motivation(d):
    d.h2("Background and Motivation")
    d.paras(
        "Three observations motivated the project. First, policy wordings are long and technical, so the details that matter most are "
        "easy to miss. A cataract operation, a knee replacement or a delivery may be covered only after a waiting period of one to four "
        "years; a room that costs more than the stated limit can reduce the whole claim proportionately; a co-payment may apply "
        "from a given age. Policyholders usually discover these conditions when a claim is rejected or reduced, not when they buy the policy.",
        "Second, the usual sources of help are slow and generic. Agents, helplines and FAQ pages answer in general terms and depend on "
        "human availability, and comparison websites compare premiums and headline benefits rather than exclusions and claim conditions. "
        "General-purpose chatbots answer fluently but from broad training data, not from the user's own wording, so they can state "
        "coverage details that the policy does not contain. The research literature calls such statements hallucinations [16]. For a "
        "legally binding document a confident wrong answer is worse than no answer: the study of Quebec automobile-insurance questions "
        "by Beauchemin et al. found that between 5% and 13% of the answers given by a retrieval-augmented GPT-4o contained a false "
        "statement that could mislead a customer [2].",
        "Third, claim filing has no guided pre-check. A policyholder planning an operation has no simple way to learn whether the "
        "waiting period is complete, which documents the insurer will ask for, or how much of the bill is likely to be theirs. This "
        "makes a claim-guidance feature a natural companion to question answering. The base paper [1] addresses a different task, the "
        "summarisation of long Turkish court rulings, but it shows how long, domain-specific legal text can be handled by selecting the "
        "important passages first and generating from them. That extract-then-generate idea is the starting point of this project, "
        "applied to health-insurance wordings and extended from summaries to cited answers and claim guidance.")


def sec_problem(d):
    d.h2("Problem Statement")
    d.paras(
        "Health insurance policies are long and technical, so users cannot easily find coverage, exclusions and conditions. Users "
        "depend on agents and helplines that give slow, generic and inconsistent answers. General chatbots may produce answers that are "
        "not supported by the user's actual policy. Claim filing lacks guidance on eligibility and required documents, which leads to "
        "delays and rejections.",
        "**Formal statement.** Given the text of a health-insurance policy wording (a PDF with a selectable text layer), produce (i) a "
        "structured Policy Card in which every extracted value is tied to the clause and page that state it; (ii) for any question about "
        "the policy, an answer in English, Hindi or Telugu that uses only that wording, cites the clauses it relies on, and says "
        "plainly when the wording does not cover the question; (iii) for a planned treatment, a verdict (covered, partly covered, not "
        "covered, or needs more information) with eligibility pre-checks, a document checklist, claim steps and a cost estimate; and "
        "(iv) a side-by-side comparison of two policies. The system must measure, not assume, how accurate and how well supported its "
        "answers are.",
        "**Need.** A conversational assistant that answers strictly from the user's own policy document, cites the supporting clauses "
        "and guides claims step by step.")


def sec_need(d):
    d.h2("Need for the Proposed System")
    d.bullets([
        "**Understanding before buying and before claiming.** The decisive conditions (waiting periods, sub-limits, co-payments, exclusions) are scattered across the wording; a tool must surface them with their sources.",
        "**Trustworthy answers.** A policyholder can only rely on an answer if it names the clause and page it comes from and if the system admits when the wording is silent.",
        "**Measured reliability.** Because LLMs can state unsupported facts [16], the system needs an independent, quantitative check of how well each answer is supported, and an offline evaluation that can be repeated.",
        "**Guidance, not just explanation.** Claim pre-checks, a document checklist and an out-of-pocket estimate address the delays and rejections that follow from missing information.",
        "**Accessibility.** Many policyholders read more comfortably in Hindi or Telugu than in English, so questions and answers must work in those languages while the evidence stays in the original English wording.",
        "**Low cost and privacy.** The system should run on an ordinary laptop, keep documents on the user's machine, and use an external model only for the language generation step.",
    ])


def sec_objectives(d):
    d.h2("Objectives")
    d.numbered([
        "Extract key policy attributes automatically from uploaded health insurance documents.",
        "Build a RAG pipeline that retrieves the policy clauses relevant to each user question.",
        "Generate plain-language answers with an LLM, grounded in and citing the retrieved clauses.",
        "Provide guided claim support with eligibility pre-checks, evidence checklists and procedural steps.",
        "Summarise risks, exclusions and cost-coverage trade-offs to support plan comparison.",
        "Evaluate the assistant for answer accuracy, faithfulness and response time.",
    ])
    d.p("These are the six objectives of the project as defined at its start. Chapter 8 measures each of them against the results.")


def sec_scope(d):
    d.h2("Scope of the Project")
    d.h3("In scope")
    d.bullets([
        "Health-insurance policy wordings in PDF form with a selectable text layer, including two-column layouts, tables and IRDAI exclusion codes.",
        "Parsing into numbered clauses with page numbers and highlight positions, and a viewer that shows the original page with the cited clause highlighted.",
        "A Policy Card of key terms (sum insured, waiting periods, co-payment, room-rent rule, sub-limits, exclusions, claim deadlines) with source and verification status for every value.",
        "Hybrid retrieval (BM25, dense embeddings, rank fusion, cross-encoder re-ranking) and cited answers with an NLI-based faithfulness score.",
        "Claim Copilot: calculated eligibility pre-checks, a verdict, a document checklist, claim steps and a cost estimate.",
        "Side-by-side comparison of two policies; risk highlights by severity; English, Hindi and Telugu questions, answers and card translation.",
        "A web application with accounts, a dashboard, a Model performance page, light and dark themes and a phone-friendly layout.",
        "An offline evaluation harness and a hand-built evaluation set drawn from four real policy wordings.",
    ])
    d.h3("Out of scope")
    d.bullets([
        "Making or predicting the insurer's claim decision: PolicyLens explains the wording; the insurer decides.",
        "Scanned PDFs without a text layer (they are rejected with a clear message); optical character recognition is not included.",
        "Training or fine-tuning any model. Every model is pre-trained, and the evaluation set is used only to measure.",
        "Premium quotes, purchase, payment, claim submission to insurers or any integration with insurer systems.",
        "Medical advice, and policies other than health insurance.",
        "Uploads in languages other than English (questions and answers work in Hindi and Telugu, the wording must be English).",
        "Multi-user administration, roles beyond a single policyholder account, and production hardening such as HTTPS termination and rate limiting by IP.",
    ])
    d.h3("Assumptions")
    d.bullets([
        "The uploaded wording is the policy the user holds and has a readable text layer in English.",
        "The Google Gemini API is reachable and the free-tier quota is not exhausted; when it is, the application falls back through a chain of models.",
        "One user works on one machine; the data folder stays on that machine.",
    ])


def sec_contrib(d):
    d.h2("Key Contributions")
    d.numbered([
        "**Clause-aware parsing and segmentation of insurance wordings.** A parser that handles two-column layouts, running headers, letter-spaced headings and tables, and a segmenter that turns the text into numbered clauses (including IRDAI exclusion codes) with page numbers and highlight boxes, so that every citation can be shown on the original page.",
        "**Verified Policy Card.** One schema-constrained Gemini call extracts the key terms; every value's quote is then located in the clauses to confirm its clause and page, and values whose quote cannot be found are shown as unverified. 51 of 52 hand-checked values were correct.",
        "**Measured hybrid retrieval for policy text.** BM25, dense retrieval, rank fusion and cross-encoder re-ranking were compared on 51 questions; the combination found the right clause in the top five for all 51 and ranked it first for 80.4%.",
        "**Grounded, cited answers that can decline.** Answers are limited to retrieved clauses, citations to clauses that were not retrieved are removed, and a two-score rule (re-rank below 0.004 and best BM25 below 9.0) makes the assistant answer \"not covered in this policy\" without calling the model: 6 of 6 out-of-scope questions were declined and none of 51 answerable questions was.",
        "**Independent faithfulness score.** A local natural-language-inference model scores how well each answer's statements are supported by the clauses cited for them, with a number check; the mean score was 87.0 and the score is shown with every answer.",
        "**Claim Copilot with rules that cannot be overruled.** Waiting-period checks, age and network co-payment, sub-limits and the cost estimate are calculated from the Policy Card, and the model's verdict cannot contradict a failed waiting-period check: 14 of 14 scenario verdicts were correct.",
        "**Multilingual use and plan comparison.** English, Hindi and Telugu questions and answers, translated cards and risk lists, and a field-by-field comparison with trade-offs that cite both policies.",
        "**A repeatable evaluation.** An offline harness, a 57-question evaluation set, 14 claim scenarios and 52 card checks, three kept runs that show how each fix improved the results, and a public Model performance page.",
    ])
    d.p("Contributions 1 and 6 to 8 are engineering contributions; contributions 2 to 5 are the elements whose quality was measured. Compared "
        "with the base paper [1], which summarises Turkish court rulings and reports ROUGE scores, this project changes the task from "
        "summarisation to grounded question answering and claim guidance, changes the domain from court rulings to health-insurance "
        "wordings, and replaces ROUGE with retrieval, citation, faithfulness and verdict measures.")


def sec_limits(d):
    d.h2("Limitations and Assumptions")
    d.bullets([
        "**Small evaluation.** 51 answerable questions over four policies and 14 claim scenarios. A result of 100% means no error was found on this set, not that errors cannot occur.",
        "**Partly tuned on the evaluation set.** The abstention thresholds and parser fixes were made after studying failures on the same set, so the final figures are optimistic; a fresh unseen set is future work.",
        "**Smallest model in the chain.** During the evaluation the free-tier quota of the two larger Gemini models was exhausted, so every result comes from `gemini-3.5-flash-lite`.",
        "**Faithfulness is a heuristic.** A small NLI model and a number check; three of 56 correct answers scored below 50, and one identical question scored 99.0 in one run and 37.9 in another.",
        "**Translation quality.** A Telugu Policy Card line contains Bengali and Gurmukhi script mixed into the Telugu text, and bracketed English terms are left untranslated.",
        "**Plan variants.** A wording that covers several plan variants (HDFC ERGO covers seven) can make a card value ambiguous; selecting the variant is not yet implemented.",
        "**Text-layer PDFs only,** English wordings only; no OCR.",
        "**Single machine and single user.** No load, concurrency or security testing was carried out, and no user study with real policyholders.",
        "**No comparison on the base paper's metric.** The base paper reports ROUGE for summarisation; PolicyLens does not summarise, so no numeric comparison is possible.",
    ])


def sec_organisation(d):
    d.h2("Organisation of the Report")
    d.table([["Chapter", "Title", "Content"],
             ["1", "Introduction", "Domain, motivation, problem statement, objectives, scope, contributions, limitations"],
             ["2", "Literature Survey", "Base paper, related work by theme, algorithms, strengths and limitations, research gap"],
             ["3", "Feasibility Study", "Technical, economic, operational and schedule feasibility"],
             ["4", "System Requirements and Analysis", "Existing and proposed system, requirements, platform, user role"],
             ["5", "System Design", "Architecture, workflow, DFDs, UML, database, modules, user interface"],
             ["6", "Methodology and Software Implementation", "Pipeline, dataset, preprocessing, algorithms, mathematics, application, API, security, installation"],
             ["7", "System Testing", "Strategy, unit, integration, functional, security, validation, performance, acceptance, limits"],
             ["8", "Results and Output Screens", "Output screens, measured results, comparison, failure analysis, objectives against outcomes"],
             ["9", "Conclusion", "Summary, objectives achieved, findings, applications, limitations"],
             ["10", "Future Scope", "Improvements, features, deployment, research"]],
            "Organisation of the report", widths=[0.1, 0.3, 0.6], font=10)
    d.p("The report ends with the references, Appendix A (important code), Appendix B (installation and user guide) and Appendix C (additional screens).")
