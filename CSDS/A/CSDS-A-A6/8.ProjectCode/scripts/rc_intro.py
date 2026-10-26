"""Chapter 1 content: domain, motivation, problem, need, objectives, scope, contributions, limitations, organisation (ClauseGuard).

Every figure comes from docs/REPORT_FACTS.md and experiments/**/metrics.json. References are numbered as in doc_common.REFERENCES:
[1] base paper; [2]-[4] papers read in full; [5]-[7] batch-survey items that could not be retrieved; [8] CUAD; [9]-[19] method and software
references; [20]-[23] Indian statutes.
"""
from __future__ import annotations

from doc_common import PRODUCT


def sec_domain(d):
    d.h2("Introduction to the Project Domain")
    d.paras(
        "A contract is the instrument through which most economic relationships are fixed: a freelancer agrees to deliver software for a "
        "fee, an employee accepts a bond and a notice period, a small business takes a supply or subscription agreement. Such documents "
        "are drafted by the party with more bargaining power and are usually signed without legal advice. They contain terms that can "
        "shift risk heavily to the weaker party: a right for one side to terminate at will, a penalty for delay that bears no relation "
        "to the loss, a promise not to work for any competitor for years, unlimited liability, a clause that assigns all of a "
        "freelancer's intellectual property, an arbitration clause in which one party appoints the arbitrator, or a subscription that "
        "renews itself. Individually each of these is common. A signatory who cannot tell which clauses matter, or who does not see how "
        "several clauses combine, signs with less information than the counterparty has.",
        "The domain of this project is therefore **automated contract review for non-lawyers under Indian contract law**. It lies between "
        "several established areas. Legal natural language processing supplies datasets and benchmarks such as the Contract Understanding "
        "Atticus Dataset (CUAD) [8] and domain models such as LEGAL-BERT [9]. Text embeddings [10], [12], [13] turn a clause into a vector "
        "that can be compared with other clauses, and retrieval-augmented generation (RAG) [11] grounds a language model's answer in "
        "retrieved text. Keyword weighting [14] and readability formulas [15] give simple, auditable measures of text. Graph structures "
        "[16] can represent relationships between items. The base paper of this project, SmartLaw Advisor by Almutairy et al. [1], "
        "combines a large language model, a RAG pipeline over a Saudi legal corpus and a contract-analysis module for Arabic documents.",
        f"**{PRODUCT}**, the system built in this project, accepts a contract as a PDF or DOCX file, splits it into clauses with page "
        "numbers, assigns each clause one of twenty CUAD-style clause types, applies eight curated rules drawn from Indian statutes "
        "[20]-[23] to flag predatory terms, checks whether flagged clauses form one of three risky combinations, computes a complexity "
        "score with an A to F grade, and asks a language model to explain each flag in plain language and to propose safer wording. The "
        "results are shown clause by clause in a web application.",
        "One point of wording must be made at the outset. The batch abstract describes a RAG architecture that combines the Claude API "
        "with pgvector semantic search and a Neo4j knowledge graph. What was built and measured differs in three respects. The language "
        "model and the embedding model are **Google Gemini**, not Claude. Clause vectors are stored as binary columns in **SQLite** and "
        "compared with NumPy, not stored in pgvector. The clause graph is an **in-memory NetworkX graph** with three fixed combination "
        "patterns, not a Neo4j database of clause types, legal concepts and precedents. There is also no retrieval over a legal corpus: "
        "the only retrieval step is the nearest-centroid match of a clause against twenty CUAD categories. These differences, and their "
        "consequences, are discussed in Chapters 6 and 8.")


def sec_motivation(d):
    d.h2("Background and Motivation")
    d.paras(
        "Five observations motivated the project, and they follow the batch introduction. First, individuals, freelancers, gig workers "
        "and small businesses increasingly sign digital contracts without legal support. Second, such contracts can contain unfair "
        "termination terms, hidden liabilities or one-sided arbitration clauses. Third, non-experts struggle to recognise these clauses, "
        "which creates an information asymmetry against the weaker party. Fourth, professional legal review is expensive and not "
        "always accessible: one of the surveyed papers puts the check of a 10-page commercial contract for clause completeness alone at "
        "45 to 90 minutes of a legal professional's time [4], and the benchmark literature on automated review begins from that cost [2]. Fifth, language models with retrieval can read a contract "
        "and explain risks in plain language [1], which makes an affordable first-pass reviewer technically possible.",
        "Recent work shows both the promise and the limits of that possibility. The ContractEval benchmark [2] evaluated 19 language "
        "models on the CUAD test data over 41 clause categories and found that the best proprietary models reached an F1 of about 0.64, "
        "so that even strong models miss or mis-extract a considerable share of risk clauses. A study of a domain-trained small model [3] "
        "reported a macro F1 of 0.812 on 26 extraction fields over 24 contracts, at a much lower cost than frontier models. A "
        "cloud-based clause extraction and risk-scoring system [4] reported 94.2% average extraction accuracy on 20 synthetic contracts. "
        "The base paper [1] reported high accuracy for a Saudi legal assistant, but for Arabic text and Saudi law.",
        "Almost all of this work concerns US or European commercial contracts, or Saudi regulation, and it analyses clauses one at a "
        "time. Indian contract law has its own provisions on the questions that matter most to a signatory: agreements in restraint of "
        "trade are void under section 27 of the Indian Contract Act, 1872, and compensation for breach is limited by section 74 [20]; the "
        "Arbitration and Conciliation Act, 1996 [21] governs arbitration clauses; the Consumer Protection Act, 2019 [22] addresses unfair "
        "contract terms for consumers; and the Copyright Act, 1957 [23] governs the assignment of authors' rights. A tool for Indian "
        "signatories has to reflect these provisions.",
        "Taken together, the observations point to a gap: an affordable, jurisdiction-aware tool that flags predatory clauses, notices "
        "when clauses combine into something worse than each alone, and explains the result in plain language. The project asks how far "
        "a student team can go towards such a tool with open data (CUAD), a hosted language model and curated rules, and how honestly "
        "the result can be evaluated when no labelled corpus of Indian contracts is available.")


def sec_problem(d):
    d.h2("Problem Statement")
    d.paras(
        "Non-experts cannot easily identify predatory or ambiguous clauses in contracts. Legal review is expensive and inaccessible for "
        "freelancers and small businesses. Existing tools ignore Indian contract law and analyse clauses in isolation. Users sign "
        "contracts without understanding hidden liabilities or unfair terms.",
        "**Formal statement.** Given a contract file in PDF or DOCX format, produce (i) a segmentation of the text into clauses, each with "
        "its page number; (ii) a clause type for each clause drawn from a fixed set of twenty CUAD categories, with a confidence value; "
        "(iii) for each clause, the set of predatory-clause rules, from a curated set tied to Indian statutes, that the clause "
        "triggers, together with a plain-language reason, the quoted triggering words and a safer rewording; (iv) the risky combinations "
        "of rules that occur anywhere in the contract; (v) a complexity score from 0 to 100 and a grade from A to F; and (vi) a "
        "plain-language summary with the key obligations of the signatory. Clause classification and predatory-clause detection must be "
        "evaluated separately.")
    d.p("The problem is a systems problem as much as a modelling problem: six outputs have to be produced consistently from one "
        "document, kept for later viewing by the user who uploaded it, and explained in a way that a non-lawyer can follow.")


def sec_need(d):
    d.h2("Need for the Proposed System")
    d.bullets([
        "**Cost and access.** Professional review is slow and costly for the people most exposed to one-sided terms. A tool that gives a clause-level first reading in about a minute (15.5 s to 113.6 s in the three uploads of this project, almost all of it waiting for the language model) can help a signatory decide which clauses to ask a lawyer about.",
        "**Jurisdiction.** The surveyed systems and benchmarks work on US, EU or Saudi texts [1]-[4], [8]. A reviewer for Indian signatories has to encode the provisions of Indian statutes [20]-[23].",
        "**Combinations of clauses.** A termination-at-will clause, a no-refund clause and a penalty clause are each common, but together they let one side end the contract, keep the payment and still charge a penalty. Clause-by-clause tools do not report this.",
        "**Explanations that a non-lawyer can use.** A label such as *Liquidated Damages* does not tell a freelancer what to do. A flag has to say why the clause is risky, quote the words that triggered it and offer a fairer wording.",
        "**Honest evaluation.** Clause classification and predatory-clause detection are different tasks and are often conflated. The need is for a tool whose two scores are measured separately, on data that is described, with the weaknesses stated.",
    ])


def sec_objectives(d):
    d.h2("Objectives")
    d.p("The project has six objectives, taken from the batch objectives document. For each, the note in brackets states what was delivered.")
    d.numbered([
        "Segment uploaded contracts into clauses and classify clause types. [Delivered: a heading-based segmenter with a paragraph fallback, and a nearest-centroid classifier over twenty CUAD categories using Gemini embeddings.]",
        "Build a RAG pipeline using the Claude API and pgvector semantic search. [Delivered in a different form: Gemini for embeddings and generation, vectors in SQLite and NumPy; there is no retrieval over a legal corpus, so the pipeline is retrieval-assisted classification plus prompted generation, not a full RAG system.]",
        "Model clause relationships and legal concepts in a Neo4j knowledge graph. [Delivered in part: an in-memory NetworkX graph with one node per clause and edges drawn from three fixed combination patterns; no legal-concept or precedent nodes and no graph database.]",
        "Flag predatory clauses and clause combinations using Indian contract law criteria. [Delivered: eight curated regular-expression rules tied to Indian statutes and three combination patterns.]",
        "Compute an overall contract complexity score and a plain-language risk summary. [Delivered: a 0 to 100 score from four text measures, an A to F grade, and a Gemini-written summary and list of obligations.]",
        "Evaluate clause classification and predatory detection separately using CUAD and curated criteria. [Delivered: separate measurements on 240 held-out CUAD spans and on a 40-clause curated set, extended in this work by an independent probe set and a 510-contract corpus run.]",
    ])
    d.p("Chapter 8 measures each objective against the results and states where an objective was met only in part.")


def sec_scope(d):
    d.h2("Scope of the Project")
    d.h3("In scope")
    d.bullets([
        "Contracts in English as PDF (with real page numbers) or DOCX files, read for text; the file is removed from the server after analysis.",
        "Segmentation into clauses at numbered headings (`1.`, `2.1`, `Section 3`, `Article 4`), with a paragraph-merging fallback.",
        "Classification of each clause into one of twenty substantive CUAD categories by Gemini embedding and nearest centroid, with an optional language-model tie-break.",
        "Eight predatory-clause rules (restraint of trade, penalty versus liquidated damages, unilateral termination, unlimited liability, one-sided arbitration, automatic renewal, intellectual-property overreach, no-refund) and three risky combinations.",
        "A complexity grade from readability, legalese density, cross-references and sentence length, and a Gemini plain-language summary with key obligations.",
        "A web application with sign-up and log-in, upload, a contract list, a report, a clause detail page, a clause graph and an evaluation page, and a REST API with JWT authentication.",
        "Separate evaluation of classification and predatory detection, a probe set of independently written clauses, a run over all 510 CUAD contracts, API timings and an automated test suite.",
    ])
    d.h3("Out of scope")
    d.bullets([
        "Legal advice. The output is information to help a signatory prepare questions for a lawyer; no lawyer reviewed the explanations.",
        "Training or fine-tuning a model. Nothing is trained; the twenty centroids are means of cached example embeddings.",
        "Scanned or image-only documents (no OCR), languages other than English, and documents other than contracts.",
        "A corpus of Indian contracts, a case-law or statute retrieval index, precedent modelling, and a Neo4j or pgvector deployment.",
        "Negotiation, redlining and e-signature, multi-user organisations, and any payment feature.",
        "Production hardening such as HTTPS termination, rate limiting, a hosted database and load testing.",
    ])
    d.h3("Assumptions")
    d.bullets([
        "The uploaded file contains selectable text and numbered clause headings in the form the segmenter recognises.",
        "A Gemini API key with enough quota is available; the build was measured on a shared free-tier key.",
        "The eight rules and three combinations encode the author's reading of the cited statutes and are not a complete statement of Indian law.",
        "The application runs on one machine with a single SQLite database for one demonstration deployment.",
    ])


def sec_contrib(d):
    d.h2("Key Contributions")
    d.numbered([
        f"**An end-to-end contract reviewer for Indian agreements.** One application, {PRODUCT}, that parses PDF and DOCX files, segments them into clauses with page numbers, classifies each clause, flags predatory terms, finds risky combinations, grades complexity and explains each flag, with 9 API endpoints, 4 database tables and 7 screens. It adopts the jurisdiction-aware, language-model-based design of the base paper [1] for Indian contracts.",
        "**An Indian-law rule set with explanations.** Eight regular-expression rules, each tied to a named statute [20]-[23], and for every flag a reason, the quoted provision and a safer wording written by the language model from the rule's stated legal basis. On the 40-clause test set written with the rules they reach precision 1.000 and recall 0.941; on an independent probe set of 40 clauses they reach precision 0.786 and recall 0.458, which is the more honest figure.",
        "**Clause-combination logic.** Three combinations of rule identifiers (unilateral termination with no refund and penalty; restraint of trade with unlimited liability; automatic renewal with unilateral termination) are reported when all their rules occur anywhere in a contract. On the 510 CUAD contracts 11 show a combination; the invented one-sided contract shows all three.",
        "**A complexity grade.** A weighted score from the Flesch reading ease [15], legal-jargon density, cross-reference count and sentence length, graded A to F. Over the 510 CUAD contracts the grades are A 4, B 169, C 268, D 68 and F 1. The measure is lexical: the invented one-sided contract scored B and the fair one A.",
        "**Separate evaluation of classification and predatory detection.** Clause classification reaches top-1 accuracy 0.792 and top-3 accuracy 0.979 on 240 held-out CUAD spans in 20 categories, against 0.675 for a TF-IDF [14] plus logistic-regression baseline; predatory detection is scored on its own test sets. The two scores are never merged.",
        "**Measured findings about the build itself.** Parity between DOCX and PDF input (8 of 8 rules against 6 of 8 on identical text), thresholds that never act (the tie-break and the Unclassified floor), a split of the evaluation data that is not contract-disjoint, a 56 ms per contract processing time for the non-API pipeline, and upload times of 15.5 s to 113.6 s. These are reported rather than hidden.",
        "**A tested and documented code base.** A suite of 73 automated tests (68 pass, 5 expected failures that document known limits), API response times, and reproducible experiment scripts.",
    ])
    d.p("Contributions 1 to 4 are engineering contributions; contributions 5 and 6 are the evaluation contributions. Compared with the base "
        "paper [1], which works on Arabic text and Saudi law, retrieves from a legal corpus with a reranker and reports 98.67% accuracy on 150 "
        "legal questions, this project works on English contracts under Indian law, has no legal-corpus retrieval, adds combinations "
        "and a complexity grade, and reports its own metrics on its own data. The tasks and data differ, so no numeric head-to-head "
        "is claimed.")


def sec_limits(d):
    d.h2("Limitations and Assumptions")
    d.bullets([
        "**The rules are regular expressions.** On the independent probe set they miss 13 of 24 predatory clauses (recall 0.458) because they need the keyword, and they flag three of 16 benign look-alikes. The 40-clause test set was written by the author of the rules, so its scores (1.000 precision, 0.941 recall) are an upper bound, and the Evaluation screen's wording \"held-out\" overstates it.",
        "**Classification is measured on annotation spans.** The 240 test items are CUAD answer spans of about 290 characters, whereas the product classifies whole clauses of about 1,158 characters. In 19 whole clauses from two uploaded contracts about half of the labels were plausible (author's reading, indicative only). The split is by text and not by contract (192 of 240 items share a contract with training examples), although the contract-disjoint score is similar (0.800).",
        "**Two thresholds never act.** On the 240 spans the top similarity ranges from 0.657 to 0.849, so the tie-break (which needs a value below 0.60) and the Unclassified floor (below 0.35) are never reached, and every clause receives one of the twenty labels even if it belongs to none.",
        "**Input format matters.** PDF line breaks defeat rules that use a bounded gap between key phrases (6 of 8 rules found in the PDF form of a contract for which the DOCX form gives 8 of 8); text before the first numbered heading is discarded; 84 of 510 CUAD contracts produce fewer than five clauses; scanned PDFs cannot be read.",
        "**The complexity grade is lexical.** It does not measure fairness, and its weights and cut-offs were chosen by the author and are not validated against human ratings.",
        "**Language-model output is unverified.** Explanations, safer wording and summaries come from Gemini, were not checked by a lawyer, and were not measured for errors.",
        "**No Indian contract data.** CUAD consists of US filings; no corpus of Indian contracts was available, so nothing was evaluated on Indian documents.",
        "**Dependence on a hosted model.** The free tier of the default text model allowed 20 requests per day; a call takes about 12 s; the user interface times out after 180 s, so a contract with many flags could fail in the browser although the server would finish.",
        "**Single machine, single database,** no load, concurrency or penetration testing, and no user study.",
    ])


def sec_organisation(d):
    d.h2("Organisation of the Report")
    d.table([["Chapter", "Title", "Content"],
             ["1", "Introduction", "Domain, motivation, problem statement, objectives, scope, contributions, limitations"],
             ["2", "Literature Survey", "Base paper, related work by theme, datasets and algorithms, strengths and limitations, research gap"],
             ["3", "Feasibility Study", "Technical, economic, operational and schedule feasibility"],
             ["4", "System Requirements and Analysis", "Existing and proposed system, requirements, platform, user roles"],
             ["5", "System Design", "Architecture, workflow, DFDs, UML, database, modules, user interface"],
             ["6", "Methodology and Software Implementation", "Pipeline, datasets, preprocessing, algorithms, mathematics, application, API, security, installation"],
             ["7", "System Testing", "Strategy, unit, integration, functional, security, validation, performance, acceptance, limits"],
             ["8", "Results and Output Screens", "Output screens, measured results, comparison, failure analysis, objectives against outcomes"],
             ["9", "Conclusion", "Summary, objectives achieved, findings, applications, limitations"],
             ["10", "Future Scope", "Improvements, features, deployment, research"]],
            "Organisation of the report", widths=[0.1, 0.3, 0.6], font=10)
    (d.p if not getattr(d, "report", False) else (lambda *a, **k: None))("The report ends with the references, Appendix A (important code), Appendix B (installation and user guide) and Appendix C (additional screens).")
