"""Chapter 1: Introduction."""

from . import facts as F
from . import lit
from .blocks import B, FIG, H1, H2, N, P, TAB
from .refs import CITE as R


def _full_blocks():
    hy = F.MINILM["full_hybrid_shipped_weights"]
    tf = F.TFIDF["full_hybrid_shipped_weights"]
    acc = F.pct(F.SHIPPED["accuracy"], 0)
    dec = F.pct(F.DM["decisive_only"]["accuracy"], 0)
    ceil = F.f2(F.GEN["best_possible_accuracy_from_phrases"])
    conf = F.MINILM["conflict"]["detected_by_kind"]
    lit_n = sum(conf[k]["detected"] for k in ("conflict term", "affiliation", "full name"))
    lit_t = sum(conf[k]["n"] for k in ("conflict term", "affiliation", "full name"))
    base, survey, rgraph = R["base"], R["survey_wu"], R["reviewgraph"]
    return [
        H1("CHAPTER 1: INTRODUCTION"),
        P(f"This chapter introduces the domain of the project, the motivation for building {F.PRODUCT}, the problem it addresses, the objectives set for it, the scope that "
          "was actually delivered, the contributions, and the limitations and assumptions that govern every result reported later. It closes with a map of the rest of the report."),

        H2("1.1 Domain and Background"),
        P("Scholarly publishing rests on peer review: before a journal or conference accepts a manuscript, one or more independent experts read it and advise the editor "
          "or programme chair. Two decisions precede every review. The editor must first judge whether a submission is complete and sound enough to deserve reviewers' time, "
          "and must then choose, from a pool of qualified people, the reviewers whose knowledge fits the paper. The second decision is known in the literature as the reviewer "
          f"assignment problem, and it has been studied for about thirty years [{R['rap_scoping']}], [{R['rap_survey']}]."),
        P("The volume of work has grown faster than the pool of reviewers. A large study of the NeurIPS 2021 process, in which two independent committees reviewed a tenth of "
          f"the submissions, found that the committees disagreed on about 23 % of the accept or reject outcomes [{R['neurips_consistency']}]. Such disagreement does not mean that "
          "reviewers are careless; it shows how much depends on which reviewers a paper happens to meet. Choosing the right reviewers is therefore an important lever, and it is "
          "mostly done by hand."),
        P("Natural language processing (NLP) offers a way to support both decisions. A paper and a reviewer can each be represented as a vector of numbers computed from their text, "
          f"so that texts on similar topics lie close together; sentence embeddings such as Sentence-BERT [{R['sbert']}] and document embeddings such as SPECTER [{R['specter']}] "
          "are widely used for this purpose. Large language models (LLMs) can in addition read a paper and write a critique. These capabilities are attractive, but they bring "
          f"new risks: an LLM that reads a manuscript can be steered by instructions hidden in it [{R['inject_aro']}], [{R['keuper']}], and many publishers restrict uploading "
          f"manuscripts to external AI services, a concern the base paper itself raises [{base}]."),
        P(f"A recent survey of LLM-assisted peer review [{survey}] organises the field into review generation, tasks after the review such as rebuttal and meta-review, and the "
          "evaluation of automated reviewers. It catalogues data sets and discusses the ethical limits of automation. Reviewer assignment itself is covered only in passing, "
          "which is one reason the batch combines the two themes: the assessment of a submission and the choice of the people who will judge it."),
        P("Three terms are used throughout the report. An *assessment* is the set of readable signals computed from the paper itself (structure, evidence, method clarity, "
          "presentation, a decision signal and a critique). A *match score* is the number between 0 and 100 that expresses how well a reviewer fits a paper. A *conflict of interest* "
          "is a relation, such as shared affiliation or collaboration, that should keep a reviewer from judging a paper."),
        P(f"This project, {F.PRODUCT}, works in that setting. It is a local web application that turns a research-paper PDF into a preliminary assessment and a ranked, explainable "
          "list of suggested reviewers, and it keeps the final judgement with a human editor."),

        H2("1.2 Motivation"),
        P("Three observations motivate the project. First, the assignment of reviewers is slow and depends on an editor's personal knowledge of the field. A mismatched reviewer "
          "produces a weak review and delays the decision, while a good match shortens both."),
        P(f"Second, the work published on the two halves of the editorial workload is separate. The base paper chosen for this batch, \"{lit.BASE_PAPER_TITLE}\" [{base}], "
          "improves and audits the scoring of reviewer expertise but does not look at the submission itself. Work on automated review, in contrast, predicts decisions or writes "
          f"review text [{R['peerread']}], [{R['reviewadvisor']}], [{R['liang_llm_feedback']}], [{rgraph}] but does not recommend reviewers. A system that joins the two - "
          "a first-pass assessment of the paper and a ranking of suitable reviewers in one tool - is the gap the batch literature survey identifies."),
        P("Third, the strongest recent systems depend on cloud services or on expensive multi-model pipelines, and they give scores that an editor cannot easily inspect. "
          "An editor who must justify an assignment needs to see why a reviewer was ranked first. The team therefore decided to build a tool that runs on one ordinary computer, "
          "processes the PDF locally, and shows the arithmetic behind every recommendation."),

        P("A fourth, practical motivation is confidentiality. Review is a confidential process, and a manuscript that is uploaded to an external service has left the control of the "
          "editor. Running the extraction, the classifier, the embeddings and the language model on the editor's own machine removes that concern for everything except a short title-based "
          "query sent to the literature service; this design choice is described in Chapter 6."),

        H2("1.3 Problem Statement"),
        P("The problem statement recorded for the batch is reproduced here in the words of the project documents."),
        B("Reviewer assignment is manual and depends on an editor's personal knowledge of the field.",
          "Keyword matching assigns reviewers who share vocabulary with the paper but not genuine expertise.",
          "Review turnaround is slow, delaying the publication of valid research.",
          "Evaluation quality varies widely between reviewers, with no consistency check."),
        P("**Need.** A framework that assesses submissions automatically and assigns each to the most topically expert reviewer, while remaining transparent enough for the "
          "editor to audit and override its suggestions. In this report the problem is stated more precisely as follows: given a PDF and a directory of reviewer profiles, "
          "produce (a) a preliminary assessment of the paper made of readable signals and (b) a ranking of the reviewers in which every score can be decomposed into its parts."),

        H2("1.4 Need for the Project"),
        P("The need follows from the gaps described above. An editor receiving a submission wants a quick, honest first view of it and a short list of candidate reviewers, "
          "and wants to be able to explain the list. Existing options either rank reviewers with opaque dense embeddings, or screen papers with tools that know nothing about the "
          "reviewer pool, or hand the whole manuscript to an external chatbot. None of the works surveyed in Chapter 2 delivers PDF intake, a preliminary assessment and an "
          "auditable ranking in one application that a small editorial office can run locally."),
        P("The need for care is equally clear. Automated reviews can be wrong, biased towards acceptance and open to manipulation [" + f"{R['keuper']}" + "], so the project is framed as "
          "decision support: every screen carries a disclaimer, an unavailable component is reported as unavailable rather than faked, and the assessment never replaces a "
          "reviewer."),

        H2("1.5 Objectives"),
        P("Six objectives were set at the start of the project. the table below repeats them and gives the status reached at the end of the work, which Chapters 8 and 9 substantiate "
          "with measurements."),
        TAB("Objectives of the project and the status reached",
            ["No.", "Objective", "Status at the end of the project"],
            [["1", "Build a corpus of submitted papers and reviewer publication profiles",
              f"Partly met: every analysis is stored; the reviewer directory holds {F.REVIEWER_POOL} demo profiles with CSV import; no real publication corpus was assembled and the decision data set is synthetic"],
             ["2", "Extract topics, methods and keywords from paper text using NLP",
              "Met with simple methods: frequency keywords and fixed lists of method terms and topic hints"],
             ["3", "Represent reviewer expertise as comparable vectors",
              "Met: profile text and publication titles are embedded with a sentence-embedding model; real publication histories were not used"],
             ["4", "Compute semantic similarity to rank candidate reviewers",
              f"Met: cosine similarity inside an auditable score; top-1 {F.pct(hy['top1'], 1)} on the project's 40-paper probe set"],
             ["5", "Provide a preliminary assessment of structure, novelty signals and completeness",
              "Met for structure, evidence, method clarity and presentation; novelty is not measured and is reported as inconclusive"],
             ["6", "Evaluate assignment quality against expert judgement and conflict handling",
              f"Partly met: labels come from the team, not independent experts; {lit_n} of {lit_t} literal conflict links were detected"]],
            widths=[0.45, 2.55, 3.3], align=["c", "l", "l"], size=10),

        P("Two points about the table deserve emphasis. The abstract of the batch also mentions deep-learning models for classifying research areas, an originality score drawn from a corpus, "
          "and ranking by h-index and publication history. The delivered system does not implement these: research areas are inferred from term lists, originality is not scored, and "
          "reviewers carry a free-text list of publication titles instead of a harvested record. The report states these differences wherever the abstract's wording would otherwise suggest "
          "more than was built."),

        H2("1.6 Scope of the Work"),
        P(f"{F.PRODUCT} is a complete, runnable application, and the scope reflects that. Within scope are: PDF intake with validation (PDF files up to {F.UPLOAD_LIMIT_MB} MB); "
          "local extraction of text, sections and references; structural signals; a trained three-class decision signal; a review made of deterministic rules and, when the "
          "model can be loaded, a three-step critique written by a local language model; literature grounding through the OpenAlex service; reviewer matching with an itemised score "
          "and a conflict check; a reviewer directory with create, update, delete, activate and CSV import and export; stored analyses with JSON and PDF export; and a web "
          "interface with a landing page, dashboard, analysis page, directory, model-performance page, history and a page on responsible use."),
        P("Outside the scope are: a global assignment optimiser that balances the load across a whole conference, reviewer bidding, harvesting of real publication records, "
          "a user-account system, multi-user deployment, languages other than English, scanned documents without a text layer, and any claim that the assessment predicts "
          "the real outcome of a peer review. Chapter 10 returns to several of these as future work."),
        TAB("Scope at a glance", ["Area", "In scope", "Out of scope"], [
            ["Input", "English-language research-paper PDFs with a text layer, up to 20 MB", "Scanned images without text, other file types, non-English text"],
            ["Assessment", "Structure, evidence, method clarity, presentation, decision signal, local critique", "Novelty measurement, checking of scientific correctness"],
            ["Matching", "Similarity, keyword, method and availability terms, conflict penalty, filters", "Global load balancing, bidding, real publication harvesting"],
            ["Data", "SQLite storage of reviewers and analyses, JSON and PDF export", "Multi-user accounts, cloud deployment"],
            ["Interface", "Eight-page web application with light and dark themes", "Mobile application, plug-ins for submission systems"],
        ], widths=[1.0, 2.7, 2.6], align=["l", "l", "l"], size=10),
        FIG(F.diag("02_high_level_workflow.png"), f"High-level workflow of {F.PRODUCT} from the uploaded PDF to the ranked reviewers.", 5.6),

        H2("1.7 Contributions"),
        P("The contributions of the project, stated at the level the evidence supports, are the following."),
        N("**An end-to-end local application.** One tool takes a research-paper PDF through extraction, assessment, literature context and reviewer matching and stores and "
          "exports the result, which the surveyed systems treat as separate problems.",
          "**An auditable matching score.** Following the auditable principle of the base paper, every recommendation shows its weighted terms "
          f"(0.55 expertise similarity, 0.20 keyword overlap, 0.15 method and topic overlap, 0.10 availability, minus a 0.60 conflict penalty), the matched terms and a plain-language explanation; "
          "availability and conflict of interest are part of the score instead of being left to a later step.",
          "**A hybrid assessment with honest fall-backs.** Structural signals, a trained decision signal and a local-LLM critique are combined, and each component reports its own status; "
          "when the language model or the literature service is unavailable the interface says so.",
          f"**A measured evaluation that states its limits.** The decision model scores {acc} accuracy on a synthetic data set whose labelling caps accuracy near {ceil}; "
          f"the matcher reaches top-1 {F.pct(hy['top1'], 1)} with sentence embeddings and {F.pct(tf['top1'], 1)} with the offline fallback on a team-written probe set; "
          "both results are reported with the reasons they cannot be compared directly with the base paper."),
        P("The expected benefit for an editorial office is a shorter first pass: the assessment tells the editor within moments whether the paper has the sections, references and "
          "method detail that a review needs, and the ranking supplies a short list of reviewers with reasons. The benefit for the research community is a worked, open example of how "
          "the auditable principle of the base paper can be applied inside a complete application, with its weaknesses measured and reported."),
        P("What is not claimed is as important. The project does not show that the decision signal predicts real review outcomes, does not compare against independent expert "
          "assignments, and does not assess novelty."),

        H2("1.8 Limitations and Assumptions"),
        P("The principal limitations are summarised here and treated in full in Chapter 8 and the scope-and-limitations document."),
        B(f"The decision model was trained on a synthetic, template-generated set of {F.DM['rows']:,} labelled texts because no public review corpus was obtained. The label "
          f"\"borderline\" cannot be told from the text, so the best accuracy any text classifier can reach on this data is about {ceil}. The measured accuracy ({acc}) is close to that "
          f"ceiling; accept versus reject is separated correctly {dec} of the time, and the borderline class is almost never predicted.",
          f"The reviewer pool contains {F.REVIEWER_POOL} demo profiles, and the matching probe set of 40 abstracts was written by the team, so the matching results are optimistic.",
          "Conflict detection compares literal strings; reworded affiliations and partial names are not recognised.",
          "Novelty is not measured. The assessment reports structure and evidence, not originality.",
          "The local language model runs on a processor only, at roughly three tokens per second, so a full analysis with the critique takes several minutes."),
        P("The assumptions are that uploaded files are English-language research papers with a text layer; that the reviewer directory is maintained by the editorial office and its "
          "conflict terms are filled in; that the application runs on a trusted local machine used by one person at a time; and that an editor reads the output as advice."),

        H2("1.9 Organisation of the Report"),
        P("The remaining chapters are organised as shown in the table below."),
        TAB("Organisation of the report", ["Chapter", "Title", "Content"], [
            ["1", "Introduction", "Domain, motivation, problem, objectives, scope, contributions, limitations"],
            ["2", "Literature Survey", "Base paper, related work by theme, algorithms, research gap"],
            ["3", "Feasibility Study", "Technical, economic, operational and schedule feasibility"],
            ["4", "System Requirements and Analysis", "Existing and proposed system, requirements, hardware, software, users"],
            ["5", "System Design", "Architecture, workflow, data-flow and UML diagrams, database, modules, interface"],
            ["6", "Methodology and Software Implementation", "Pipeline, data, algorithms, formulation, API, security, installation"],
            ["7", "System Testing", "Strategy, unit, integration, functional, security, performance, limits"],
            ["8", "Results and Output Screens", "Measurements, output screens, comparison with the base paper, objectives"],
            ["9", "Conclusion", "Summary, findings, applications, known limitations"],
            ["10", "Future Scope", "Improvements, features, scalability, further research"],
        ], widths=[0.7, 2.2, 3.4], align=["c", "l", "l"], size=10.5),
        P("The references and three appendices (important code, installation and user guide, additional screens) follow Chapter 10."),
    ]


# paragraphs / tables left out of the compact report variant (page budget); the chapter document keeps them
_DROP = ("A recent survey of LLM-assisted peer review", "Three terms are used throughout", "A fourth, practical motivation",
         "Scope at a glance", "The expected benefit for an editorial office", "The references and three appendices",
         "The principal limitations are summarised")


def blocks():
    full = _full_blocks()
    if not F.REPORT:
        return full
    out = []
    for b in full:
        key = b[1] if b[0] == "p" else (b[1] if b[0] == "tab" else "")
        if isinstance(key, str) and key.startswith(_DROP):
            continue
        out.append(b)
    return out
