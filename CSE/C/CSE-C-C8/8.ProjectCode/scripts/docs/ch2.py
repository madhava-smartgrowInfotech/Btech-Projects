"""Chapter 2: Literature survey."""

from . import facts as F
from .blocks import B, EQ, H1, H2, H3, N, P, TAB
from .refs import CITE as R


def c(*keys):
    """Citation string such as [1], [10] from CITE keys."""
    return ", ".join(f"[{R[k]}]" for k in keys)


def _full_blocks():
    base = c("base")
    hy = F.MINILM["full_hybrid_shipped_weights"]
    tf = F.TFIDF["full_hybrid_shipped_weights"]
    return [
        H1("CHAPTER 2: LITERATURE SURVEY"),

        H2("2.1 Overview"),
        P(f"This chapter reviews the work on which {F.PRODUCT} builds and against which it must be judged. It starts with the base paper assigned to the batch {base}, analyses it in "
          "detail, and then groups related work by theme: reviewer assignment, text representation, automated review and decision prediction, the integrity of LLM-based review, "
          "and the tools used in the implementation. It then describes the data and algorithms that the project itself uses, summarises strengths and limitations, "
          "lists the additional sources named in the project's literature survey, and ends with the research gap."),
        P("Two remarks on method. Numerical results are quoted only where they were read in the paper itself or in a bibliographic record, and the text says when a source could be "
          "verified only in part. Three of the five entries in the batch literature survey could not be read in full; they are listed in Section 2.6 with that caveat and no claim is "
          "attributed to them beyond what the record shows."),

        H2("2.2 Analysis of the Base Paper"),
        P(f"The base paper is \"LLM-Assisted Reviewer Assignment via Auditable Expertise Matching\" by Bagheri, Buscaldi and Reforgiato Recupero of the University of Cagliari and "
          f"Sorbonne Paris Nord, published in IEEE Access, volume 14, pages 127834-127863, in 2026 {base}. It runs to 30 pages. Its subject is the reviewer assignment problem (RAP): "
          "match submissions to qualified reviewers under constraints of expertise coverage, reviewer capacity and conflict of interest."),
        H3("Problem and central idea"),
        P("The authors argue that the central difficulty of RAP is the construction of the affinity score between a paper and a reviewer, and that dense embeddings, although effective, "
          "are hard to audit. Their idea is to confine the language models to a narrow, checkable task. LLMs never rank reviewers and never decide; they only induce keywords, and every "
          "later step is deterministic or stored so that it can be inspected. This is what the title means by *auditable expertise matching*."),
        H3("Method"),
        N("**Producer ensemble.** Several heterogeneous LLMs each return 6 to 12 keyphrases of one to three words, as a strict JSON array, for a view of the paper (title, abstract "
          "summary or full abstract) or for each prior publication of a reviewer. The models named in the text include Qwen 3, Grok 4 and LLaMA 4.",
          "**Judge.** A stronger LLM chooses the single best candidate list for faithfulness, coverage, specificity and non-redundancy; it may choose but not rewrite.",
          "**Deterministic normalisation.** Lower-casing, trimming, lemmatisation with WordNet and de-duplication.",
          "**Audit trail.** Prompts, model identifiers, raw candidates, the winning index, final keywords, score matrices and top-3 lists are stored at every stage.",
          "**Matchers.** The paper compares TF-IDF cosine, keyword-set Jaccard and their mean; an SBERT bi-encoder with the all-MiniLM-L6-v2 checkpoint (a reviewer is represented by "
          "the mean-pooled embeddings of publications); a two-stage bi-encoder plus cross-encoder re-ranker (cross-encoder/ms-marco-MiniLM-L-6-v2); keyword-aware SBERT variants; and "
          "keyword knowledge-graph matchers built with Node2Vec."),
        P("The re-ranking stage mixes the cross-encoder score with the first-stage text score through a convex combination of normalised scores:"),
        EQ("s_hybrid = λ · norm(s_ce) + (1 − λ) · norm(s_text)"),
        H3("Data and protocol"),
        P("The authors' own data set contains 663 papers from 85 computer-science conferences, with 1,989 assignments (about three reviewers per paper), and 524 unique reviewer profiles "
          "of up to 20 most-cited publications each, taken from Semantic Scholar. Historical assignments are the relevance labels. The metrics are MRR@3, P@3 and MAP@3, "
          "macro-averaged over papers, with paired two-sided t-tests, 95 % confidence intervals and a bootstrap fallback of 10,000 resamples; the Gini coefficient of reviewer load is "
          "reported as a workload diagnostic. The data are stated to be available on reasonable request."),
        H3("Reported results"),
        TAB("Results of the base paper as stated in the paper", ["Item", "Reported value"], [
            ["Best MRR@3 on titles", "0.7778 (keyword-aware two-stage re-ranking)"],
            ["Best MRR@3 and MAP@3 on abstracts", "0.7843 and 0.2991 (knowledge-graph edge Jaccard)"],
            ["Best P@3 on summaries", "0.4545 (keyword-aware SBERT)"],
            ["Best MAP@3 on summaries", "0.3232 (keyword-aware SBERT)"],
            ["TF-IDF cosine on titles (MRR@3 / P@3 / MAP@3)", "0.7078 / 0.3882 / 0.2941"],
            ["SBERT cosine on titles (MRR@3 / P@3 / MAP@3)", "0.6571 / 0.3873 / 0.2636"],
            ["Cross-encoder re-ranking on titles", "MRR@3 +0.1173 (+17.76 %), P@3 -0.0133 against the keyword-aware bi-encoder"],
            ["Gini coefficient of load, SBERT baseline", "0.375 (titles), 0.376 (summaries), 0.373 (abstracts)"],
        ], widths=[2.9, 3.4], align=["l", "l"], size=10.5),
        P("Most differences among the text encoders are not statistically significant; for example, on titles the keyword-aware bi-encoder against the SBERT baseline gives a P@3 "
          "difference of +0.0030 with a 95 % interval of [-0.0022, 0.0082] (p = 0.257). The local knowledge-graph matcher on titles is significantly worse (MAP@3 difference -0.0414). "
          "The paper also cites two facts about the task: the NeurIPS 2021 repeat committees disagreed on about 23 % of submissions, and 91 % of the top-100 medical journals prohibit "
          "uploading manuscripts to AI tools."),
        H3("Limitations stated by the authors and our reading"),
        B("Historical assignments are an imperfect proxy for expertise, because availability, bidding, conflicts and workload also shaped them; no human expert judgements are used.",
          "No capacity- or conflict-aware end-to-end allocation was benchmarked, because the metadata were not available.",
          "LLM keywords may hallucinate, drift between model versions and carry bias; the stored artefacts do not allow a producer-by-producer ablation, so the advantage of the "
          "ensemble over a single LLM is not established.",
          "The system only matches reviewers. It makes no assessment of the submission itself, and it has no user interface; its scoring runs offline over a fixed data set, and "
          "availability and conflict are left to a downstream solver."),
        P("For this project the base paper supplies three things: the principle that a recommendation must be auditable, the observation that the all-MiniLM-L6-v2 bi-encoder is a "
          "strong and simple baseline, and a clear statement of what remains untested - conflict and capacity inside the score. Section 2.9 states how PeerScope differs."),

        H2("2.3 Related Work by Theme"),
        H3("2.3.1 Reviewer assignment"),
        P(f"A scoping review of the reviewer assignment problem retained 26 studies from Scopus, Google Scholar and DBLP and notes that the problem has been studied for about thirty "
          f"years and that a recent systematic synthesis was missing {c('rap_scoping')}. A survey of algorithms from 1992 to 2022 organises them into three parts: a database of "
          f"candidate reviewers, the computation of a matching degree, and the optimisation of the assignment {c('rap_survey')}."),
        P(f"Early work learned the match from text. Mimno and McCallum compared two language-model approaches with a new Author-Persona-Topic model against human relevance judgements on "
          f"documents from the Rexa database, and the new model performed best {c('mimno')}. Charlin, Zemel and Boutilier learned suitability scores from a few provided scores and then "
          f"solved an integer program for the assignment, testing on two conference data sets {c('tpms')}. Stelmakh, Shah and Singh's PeerReview4All maximises the quality for the "
          f"most disadvantaged paper through an incremental max-flow algorithm and proposes an experiment design for comparing algorithms without ground truth {c('peerreview4all')}."),
        P(f"Other work addresses fairness and integrity. FairColor is an algorithm for balanced and fair assignment {c('faircolor')}; only its bibliographic record was verified for this "
          f"report. Jecmen and co-authors use randomised assignment to limit malicious reviewers, quid-pro-quo arrangements and de-anonymisation; the general problem is NP-hard and "
          f"they give an efficient practical case {c('jecmen')}. The Chain-of-Factors method chains semantic, topic and citation factors in one instruction-tuned language model for coarse-to-fine "
          f"reviewer search, with experiments on four data sets {c('chain_of_factors')}. The NeurIPS 2021 consistency experiment, which found disagreement on about 23 % of outcomes, "
          f"shows why the assignment matters {c('neurips_consistency')}."),
        H3("2.3.2 Text representation and similarity"),
        P(f"TF-IDF weights a term by its frequency in a document and by the inverse of the number of documents that contain it. Salton and Buckley survey the term-weighting family "
          f"{c('tfidf')}, and Sparck Jones gave the statistical interpretation of inverse document frequency {c('idf')}. TF-IDF vectors compared by cosine are the classical baseline for "
          f"matching papers to reviewers, and they appear in the base paper."),
        P(f"Sentence-BERT uses siamese BERT networks to produce sentence embeddings that can be compared by cosine; it reduces the search for the most similar pair among 10,000 sentences "
          f"from about 65 hours with BERT to about 5 seconds {c('sbert')}. MiniLM compresses large transformers by deep self-attention distillation {c('minilm')}; the checkpoint "
          f"all-MiniLM-L6-v2 that PeerScope uses belongs to this family, and the base paper names the same checkpoint for its SBERT baseline. SPECTER trains document-level embeddings "
          f"for scientific papers with citation information and is evaluated on the SciDocs benchmark of seven tasks {c('specter')}."),
        H3("2.3.3 Automated review and decision prediction"),
        P(f"PeerRead provides 14.7 thousand paper drafts with accept or reject decisions from ACL, NIPS and ICLR, and 10.7 thousand textual reviews; simple models predict acceptance with "
          f"up to 21 % error reduction over the majority baseline {c('peerread')}. Yuan, Liu and Neubig use summarisation models to generate first-pass reviews; the generated reviews "
          f"cover more aspects than human ones but are less constructive {c('reviewadvisor')}."),
        P(f"Large language models changed the scale. Liang and co-authors gave GPT-4 the full PDF of 3,096 papers from Nature journals and 1,709 ICLR papers; the overlap between the model's "
          f"points and a human reviewer was 30.85 % and 39.23 %, against 28.58 % and 35.25 % between two human reviewers, and in a study with 308 researchers 57.4 % found the feedback "
          f"helpful or very helpful {c('liang_llm_feedback')}. DeepReview adds multi-stage reasoning, literature retrieval and evidence-based argumentation; its 14-billion-parameter reviewer "
          f"reports win rates of 88.21 % against GPT-o1 and 80.20 % against DeepSeek-R1 {c('deepreview')}. ReViewGraph simulates reviewer-author debates with LLM agents, builds a "
          f"heterogeneous graph of opinion edges and predicts accept or reject with a graph network; on ICLR 2023, 2024 and 2025 submissions its accuracy is 70.29, 66.10 and 71.65 % and its "
          f"macro-F1 is 69.89, 65.54 and 71.65 % {c('reviewgraph')}. A survey from Yale, NYU and TCS Research catalogues this field {c('survey_wu')}, and a second survey covers LLMs for "
          f"automated scholarly review {c('llm_review_survey')} (only its record was verified)."),
        H3("2.3.4 Integrity and risks of LLM-based review"),
        P(f"The preprint of Torrielli and co-authors studies indirect prompt injection in peer review, in which hidden instructions in a manuscript try to steer an AI reviewer. In 5,600 "
          f"controlled experiments on NeurIPS and ICLR manuscripts with two general-purpose chatbots the hidden instructions were followed in 78 % of cases for ChatGPT and 86 % for Gemini, "
          f"and instructions placed early in the text were the most influential; the journal version reports positive steering, refusal or redirection above 98 % success on 100 OpenReview papers "
          f"{c('inject_aro')}. Keuper generated reviews of 1,000 ICLR 2024 papers with several LLMs and found that very simple prompt injections reach up to 100 % acceptance scores and that "
          f"the reviews are biased towards acceptance, above 95 % for many models {c('keuper')}. These findings argue for local processing, a deterministic fall-back and a human in the loop, "
          "which are the choices made in PeerScope."),
        H3("2.3.5 Tools used in the implementation"),
        P(f"Qwen2.5 is a family of open-weight language models pre-trained on up to 18 trillion tokens {c('qwen25')}; PeerScope loads the 1.5-billion-parameter instruction model, with "
          f"the 0.5-billion-parameter model as fall-back, through the Hugging Face transformers library {c('hf_transformers')}. The transformer architecture is that of Vaswani et al. "
          f"{c('transformer')}. Scikit-learn provides the vectorisers, the logistic regression and the metrics {c('sklearn')}. OpenAlex is a fully open index of scholarly works with a free "
          f"programming interface, which PeerScope queries for related literature {c('openalex')}."),

        H3("2.3.6 Evaluation measures used in the literature"),
        P("Assignment work evaluates a ranking of reviewers for each paper against a set of relevant reviewers. Three measures recur, and the base paper uses all of them at rank 3. "
          "Let Q be the set of papers, rank_q the position of the first relevant reviewer for paper q, and rel_q(i) equal to 1 when the reviewer at position i is relevant."),
        EQ("MRR@k = (1/|Q|) Σ_q 1/rank_q  (counted only when rank_q ≤ k, otherwise 0)"),
        EQ("P@k = (1/k) Σ (i = 1..k) rel_q(i),   AP@k = (1/min(k, R_q)) Σ (i = 1..k) P@i · rel_q(i)"),
        P("MRR rewards placing one relevant reviewer high, precision at k measures how many of the top k are relevant, and MAP averages the precision over the ranks at which relevant "
          "reviewers appear. Because the metrics depend on the relevance labels, results on different data sets cannot be compared directly; the base paper's labels are historical "
          "assignments, whereas PeerScope's probe labels are written by the team. Decision predictors, in contrast, are scored with accuracy and macro-averaged F1 over the decision classes, "
          "which is how PeerRead and ReViewGraph report their results and how Chapter 8 reports the decision signal."),
        P("Two cautions from the literature bear on how results should be read. First, a ranking metric computed against historical assignments rewards agreement with past editors, "
          "including their habits and constraints; it does not measure whether the review that followed was good. Second, the base paper's significance tests show that many apparently "
          "different encoders cannot be separated statistically, so small differences in a table should not be over-interpreted. The evaluation in Chapter 8 is built with both cautions in mind: "
          "it reports the size of the probe set, the labelling procedure and the number of cases behind every percentage."),

        H2("2.4 Data and Algorithms Used in This Project"),
        P(f"**Decision data.** No public review corpus could be obtained during the project, so the decision model is trained on a synthetic set of {F.DM['rows']:,} labelled texts generated "
          "from templates of strength and weakness phrases. Section 6.2 and Chapter 8 describe the generator and show why it limits what the model can learn. PeerRead "
          f"{c('peerread')} is the natural real replacement and is listed as future work."),
        P(f"**Reviewer profiles.** Six demonstration profiles, each with an expertise description, topic, method and keyword lists, publication titles, load and conflict terms. "
          f"Matching quality is measured on 40 abstracts written by the team (Chapter 8)."),
        P("**Algorithms.** The choices follow the literature above and are justified in Chapter 6."),
        TAB("Algorithms used in PeerScope and their sources", ["Step", "Algorithm", "Source"], [
            ["Decision signal", "Word (1-2 gram) and character (3-5 gram) TF-IDF features with balanced logistic regression", f"{c('tfidf', 'idf', 'sklearn')}"],
            ["Expertise similarity", "all-MiniLM-L6-v2 sentence embeddings compared by cosine; offline TF-IDF fall-back", f"{c('sbert', 'minilm', 'base')}"],
            ["Keyword and method overlap", "Set overlap with partial substring matches over extracted terms", "this project"],
            ["Audit score", "Weighted sum of similarity, overlap and availability minus a conflict penalty", f"audit principle of {c('base')}"],
            ["Critique", "Three-step prompt (analyse, critique, synthesise) with Qwen2.5-1.5B-Instruct on CPU", f"{c('qwen25', 'hf_transformers')}"],
            ["Literature context", "OpenAlex works search ranked by embedding similarity", f"{c('openalex')}"],
        ], widths=[1.5, 3.4, 1.4], align=["l", "l", "l"], size=10.5),
        P("The cosine similarity between a paper vector p and a reviewer vector r, used for the expertise term, is"),
        EQ("sim(p, r) = (p · r) / (‖p‖ · ‖r‖),  clipped below at 0"),

        H2("2.5 Strengths and Limitations of Existing Approaches"),
        TAB("Approach families compared", ["Family", "Strengths", "Limitations for an editorial desk"], [
            ["Learned suitability and optimisation " + c("tpms", "peerreview4all", "faircolor"), "Principled assignment under load and fairness constraints", "Need scores or labels; no reading of the paper itself; little explanation per recommendation"],
            ["Embedding matchers " + c("sbert", "specter", "base"), "Capture topical fit beyond shared words; cheap at inference", "Opaque; many encoder differences are statistically indistinguishable " + c("base")],
            ["LLM keyword induction " + c("base"), "Readable keywords; full audit trail", "Several LLM calls per paper and reviewer; possible hallucination; no conflict or capacity benchmark"],
            ["Decision predictors " + c("peerread", "reviewgraph"), "Show that text carries some signal about outcomes", "Need real review corpora; give a verdict, not a reviewer"],
            ["LLM review writers " + c("liang_llm_feedback", "deepreview"), "Broad feedback, useful to many authors", "Can be steered by hidden text " + c("inject_aro", "keuper") + "; no reviewer matching"],
        ], widths=[1.8, 2.1, 2.4], align=["l", "l", "l"], size=10),
        P("The evidence behind these families is uneven. The assignment algorithms are mostly validated on conference data of the authors' own or on human relevance judgements for a "
          "single venue; the decision predictors are validated on held-out papers from the same review platform; and the LLM review studies measure overlap with human reviewers, which "
          "is itself noisy, as the 23 % disagreement between two committees shows. None of these evaluations can be reproduced on a small local installation without the same data, "
          "which is why this project reports its own measurements together with the conditions under which they were made."),
        P("In short, the literature is strong on each half of the workload separately. Auditable matching is well developed in the base paper, and automated assessment is developing quickly, "
          "but the two are rarely joined, and the integrity risks of LLM reading argue for keeping the human editor in charge."),

        H2("2.6 Additional Sources Named in the Project Literature Survey"),
        P("The literature survey recorded for the batch lists five entries. The first is the base paper. The others were checked for this report as follows."),
        TAB("Sources named in the batch literature survey", ["Title as recorded", "Year", "Reference", "Verification"], [
            ["LLM-Assisted Reviewer Assignment via Auditable Expertise Matching", "2026", c("base"), "Read in full from the PDF"],
            ["How to get your paper accepted by an AI reviewer: indirect prompt injection in peer review", "2026", c("inject_aro"), "Abstract and bibliographic record verified (preprint; journal version in Scientometrics)"],
            ["Unveiling the Reviewer Mindset: Evidence-Based Insights into Scholarly Peer Review", "2025", c("reviewer_mindset"), "Title, authors and date verified; content not read"],
            ["Review of: Performance evaluation of adaptive introgression classification methods, Round 1, Reviewer 2", "2024", c("pci_r1"), "Record exists; an anonymous review report from another field, not research literature; text not read"],
            ["Review of: Performance evaluation of adaptive introgression classification methods, Round 2, Reviewer 2", "2024", c("pci_r2"), "As above"],
        ], widths=[2.6, 0.5, 0.7, 2.5], align=["l", "c", "c", "l"], size=10),
        P("The two review reports are examples of real, open reviewer text. No claim in this report depends on them."),

        H2("2.7 Summary Comparison"),
        TAB("Comparison of the surveyed work", ["Work", "Approach", "Data", "Reported result", "Limitation"], [
            [f"Bagheri et al. {c('base')}", "LLM keyword ensemble + judge; TF-IDF, SBERT, graph matchers", "663 papers, 524 reviewers", "MRR@3 up to 0.7843", "No paper assessment; COI and capacity not benchmarked"],
            [f"Charlin et al. {c('tpms')}", "Learned suitability + integer program", "Two conference sets", "Not quoted", "Needs provided scores"],
            [f"Mimno & McCallum {c('mimno')}", "Author-Persona-Topic model", "Rexa documents", "Best of three models", "Human labels needed"],
            [f"Kang et al. {c('peerread')}", "Accept/reject prediction", "14.7K drafts, 10.7K reviews", "Up to 21 % error reduction", "Decision only"],
            [f"Liang et al. {c('liang_llm_feedback')}", "GPT-4 feedback on PDFs", "3,096 + 1,709 papers", "30.85 % / 39.23 % overlap", "No reviewer matching"],
            [f"Li et al. {c('reviewgraph')}", "Debate simulation + graph network", "ICLR 2023-2025", "Accuracy 66.10-71.65 %", "Decision only; costly"],
            [f"Torrielli et al. {c('inject_aro')}", "Hidden-instruction attack", "NeurIPS, ICLR papers", "78 % / 86 % compliance", "Describes the risk, not a remedy"],
            [f"This project (PeerScope)", "Local assessment + auditable matching", f"Synthetic decision set; {F.REVIEWER_POOL} demo reviewers; 40-paper probe", f"Top-1 {F.pct(hy['top1'], 1)} (probe)", "Optimistic evaluation; novelty not measured"],
        ], widths=[1.15, 1.3, 1.2, 1.1, 1.55], align=["l", "l", "l", "l", "l"], size=9),

        H2("2.8 Research Gap"),
        N(f"The base paper improves and audits the affinity matrix only: it scores 663 papers against 524 reviewers but performs no assessment of the paper, so an editor still needs a "
          f"separate tool for first-pass screening {c('base', 'survey_wu')}.",
          f"Automated review work predicts decisions or writes reviews but does not recommend reviewers {c('peerread', 'reviewadvisor', 'liang_llm_feedback', 'deepreview', 'reviewgraph')}; "
          "the two halves of the workload are served by separate lines of research.",
          f"The base paper's evaluation uses historical assignments as labels and leaves conflict of interest and capacity out of the experiments {c('base')}; how availability and "
          f"conflict should enter an auditable score is untested, and randomisation {c('jecmen')} is not a transparent per-reviewer score.",
          f"LLM-based reviewing is vulnerable to hidden instructions (78-86 % compliance {c('inject_aro')}; up to 100 % acceptance scores {c('keuper')}) and tends towards acceptance, "
          "which argues for local processing, a deterministic fall-back and a human in the loop.",
          f"Dense-embedding matchers are hard to audit {c('base')}; per-recommendation score breakdowns with matched terms and explicit availability and conflict terms are rare, and none "
          f"of the assignment works {c('tpms', 'mimno', 'peerreview4all', 'faircolor', 'jecmen', 'chain_of_factors')} is an end-to-end local application with PDF intake.",
          f"Published decision-prediction results depend on real review corpora {c('peerread', 'reviewgraph')}; a project without such data must say plainly that a classifier trained on "
          "synthetic labels demonstrates the pipeline and not real-world predictive power."),

        H2("2.9 How PeerScope Differs"),
        P(f"PeerScope adopts the auditable principle of the base paper {base} but changes the design in four ways. First, it does not use an LLM ensemble to induce keywords: keywords and method "
          "terms come from deterministic frequency and lexicon extraction, and the local Qwen model writes review text only; it never ranks. Second, expertise similarity is a single "
          "bi-encoder cosine with all-MiniLM-L6-v2, the encoder the base paper uses for its SBERT baseline, with a TF-IDF fall-back. Third, availability and a conflict penalty are inside the "
          "score, and no global optimiser is run. Fourth, it adds what the base paper lacks: PDF intake, a preliminary assessment (structural signals, a decision signal and a "
          "critique), literature grounding, a reviewer directory, history and export."),
        P(f"The price of these choices is a much smaller evaluation. PeerScope was measured on {F.REVIEWER_POOL} demonstration reviewers and 40 abstracts written by the team: top-1 "
          f"{F.pct(hy['top1'], 1)} with sentence embeddings and {F.pct(tf['top1'], 1)} with the offline fall-back. These figures are not comparable with the base paper's MRR@3 and MAP@3 "
          "on 663 real papers, and Chapter 8 says so wherever the two are mentioned."),
    ]


# blocks left out of the compact report variant (page budget); the chapter document keeps them
_DROP = ("Two remarks on method", "The re-ranking stage mixes", "s_hybrid =", "2.3.6 Evaluation measures", "Assignment work evaluates a ranking",
         "MRR@k =", "P@k =", "MRR rewards placing", "Two cautions from the literature", "The cosine similarity between a paper vector",
         "sim(p, r) =", "Approach families compared", "The evidence behind these families", "In short, the literature is strong",
         "The two review reports are examples", "Other work addresses fairness", "TF-IDF weights a term", "Qwen2.5 is a family", "2.3.5 Tools used", "The literature survey recorded for the batch lists")


def blocks():
    full = _full_blocks()
    if not F.REPORT:
        return full
    return [b for b in full if not (isinstance(b[1], str) and b[0] in ("p", "h3", "eq", "tab") and b[1].startswith(_DROP))]
