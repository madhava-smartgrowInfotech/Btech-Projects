"""Chapter 2 content: literature survey, base paper analysis, related work, datasets and algorithms, strengths and limitations, gap (ClauseGuard).

References are numbered as in doc_common.REFERENCES: [1] base paper (read in full); [2] ContractEval, [3] A Few Good Clauses, [4] LDAS (read in
full from the PDFs in the batch folder); [5]-[7] items of the batch literature survey that could not be retrieved (title only, no result is
quoted); [8] CUAD; [9]-[19] method and software references; [20]-[23] Indian statutes.
All figures attributed to papers were read from their PDFs (see docs/REPORT_FACTS.md section 9).
"""
from __future__ import annotations

from doc_common import BASE_PAPER

LIT_TABLE = [["Work", "Approach", "Data", "Reported result", "Limitation for this project"],
             ["Almutairy et al. 2026 [1] (base)", "Gemini 1.5 Flash with RAG over a Saudi corpus; contract analysis by checklist and clause-level LLM analysis", "150 legal questions, 50 real contract drafts, Arabic", "98.67% (148/150) on questions; contract analysis judged by inspecting sample outputs", "Arabic, Saudi law; no clause combinations; no complexity score; contract results qualitative"],
             ["Liu et al. 2025 [2] (ContractEval)", "Benchmark of 19 LLMs asked to extract risk clauses from whole contracts", "CUAD test data, 41 categories", "Best F1 0.644 (GPT-4.1 mini); best open-source F1 0.540", "Extraction of spans, not Indian law; no explanation or combination analysis"],
             ["Lincoln et al. 2026 [3]", "Domain-trained small model against five frontier LLMs, full-document extraction", "24 held-out contracts, 508 labelled field instances, 26 fields", "Macro F1 0.812, micro F1 0.842; cost down 78%-97%", "Extraction of fields, not risk; closed domain model"],
             ["Dhaksha Charan R et al. 2026 [4] (LDAS)", "Serverless pipeline; generative model extracts ten clause types; template comparison; weighted risk score", "20 synthetic contracts, 30 sample contracts, one primary test document", "94.2% extraction accuracy; risk score correlation r = 0.87; 100% on the primary document", "Detects missing clauses against a template, not predatory wording; small, partly synthetic data"],
             ["ClauseMiner 2026 [5]", "Prompt-engineered LLM clause extraction (from the title)", "Not retrieved", "Not retrieved", "Not retrieved"],
             ["Legal-BERT contract risk 2025 [6]", "Legal-BERT clause risk detection (from the title)", "Not retrieved", "Not retrieved", "Not retrieved"],
             ["Construction contract risk 2024 [7]", "LLM-based risk detection (from the title)", "Not retrieved", "Not retrieved", "Not retrieved"]]


def sec_lit_overview(d):
    d.h2("Overview of the Literature Survey")
    d.paras(
        "The survey covers four groups of work. The first is the base paper [1], a legal assistant and contract analyser for Arabic "
        "documents under Saudi law. The second is work that evaluates language models on clause-level risk identification and extraction "
        "in English commercial contracts [2], [3] and that builds clause-extraction and risk-scoring systems [4]. The third is the "
        "learning, retrieval and text-analysis techniques from which ClauseGuard is built [8]-[19]. The fourth is the Indian statutes "
        "that define what is predatory in this project [20]-[23].",
        "The batch literature survey lists five papers. The base paper [1] was read in full from its PDF, and so was the ContractEval "
        "benchmark [2], whose PDF is in the project's archive. Three listed papers (ClauseMiner [5], the Legal-BERT contract risk paper "
        "[6] and the construction-contract risk study [7]) could not be retrieved during this work, so they are named by title, year and "
        "venue as listed and **no result is attributed to them**. To avoid resting the review on titles alone, two further papers whose "
        "full text is in the project's archive were read and are reported: a comparison of a domain-trained small model with frontier "
        "language models on contract extraction [3] and an AWS-based clause extraction and risk-scoring system [4].")
    d.table([["No.", "Paper (as listed or added)", "Year", "Venue", "Status in this survey"],
             ["1", "SmartLaw Advisor: AI-powered legal consultation and contract analysis for Saudi Arabia [1] (base paper)", "2026", "IEEE Access", "Read in full"],
             ["2", "ContractEval: benchmarking LLMs for clause-level legal risk identification in commercial contracts [2]", "2025", "arXiv:2508.03080 (listed for NLLP 2025)", "Read in full"],
             ["3", "ClauseMiner: prompt-engineered LLM for accurate, scalable legal clause extraction [5]", "2026", "Eng. Appl. of Artificial Intelligence", "Listed; not retrieved"],
             ["4", "Autonomous contract analysis and clause risk detection using Legal-BERT [6]", "2025", "ICSCN 2025", "Listed; not retrieved"],
             ["5", "A study on LLM-based approach for construction contract risk detection [7]", "2024", "Int. Conf. Big Data and Digital Management", "Listed; not retrieved"],
             ["6", "A few good clauses: LLMs vs domain-trained small language models on structured contract extraction [3]", "2026", "arXiv:2605.05532", "Added; read in full"],
             ["7", "Automated legal clause extraction and risk scoring using NLP and generative AI [4]", "2026", "IJRASET vol. 14 issue IV", "Added; read in full"]],
            "Papers in the batch literature survey and the two papers added", widths=[0.06, 0.46, 0.08, 0.2, 0.2], font=9.5)


def sec_base_paper(d):
    d.h2("Base Paper Analysis")
    d.p(f"**Base paper.** {BASE_PAPER}")
    d.paras(
        "**Problem and scope.** Almutairy et al. start from the complexity of local laws and the scarcity of affordable legal support in "
        "Saudi Arabia, and from the absence of Arabic digital assistants aligned with Saudi legislation. They propose a virtual legal "
        "advisory platform with two functions: a legal chatbot that answers questions from a Saudi legal corpus, and a contract analysis "
        "system that extracts and classifies clauses of Arabic documents and checks them against national law. The paper was received on "
        "24 December 2025 and published on 17 February 2026.",
        "**Retrieval pipeline.** The chatbot uses retrieval-augmented generation. Legal documents are cut into coherent chunks by a "
        "semantic chunking step with a window of at most 1,024 tokens, embedded with GATE-AraBERT-v1 (an Arabic embedding model "
        "fine-tuned on legal terms), and indexed in the Chroma vector database (the paper also mentions a FAISS index of about 18,400 "
        "vectors and 152 MB). A query is embedded by the same model, the nearest chunks are retrieved (the paper states that the "
        "retriever returns a small number of candidates, k = 1), re-ranked by a cross-encoder (ARA-Reranker-V1), compressed to the "
        "essential passage and passed to Gemini 1.5 Flash. The generation settings are a temperature of 0.2, a maximum of 1,024 tokens, "
        "top-p 0.95 and top-k 40, so that the answer is nearly deterministic and tied to the supplied context.",
        "**Contract analysis.** A user uploads a PDF, which is read by an OCR step that uses the multimodal ability of Gemini and is "
        "validated for errors in dates, figures and clause numbers. Each contract is compared with a checklist of essential clauses "
        "(payment terms, governing law, dispute resolution, termination, liability allocation, confidentiality and force majeure) that "
        "Saudi legal practitioners validated, and every clause is analysed by the language model for prohibited terms, ambiguous "
        "obligations and legally incomplete formulations. The paper describes the combination as hybrid rule-based and LLM-guided. "
        "The output is structured JSON with recommendations in Arabic, and a further step lists contradictory clause pairs.",
        "**Data and experiments.** The evaluation set has 150 legal questions over ten legal domains and 50 real contract drafts; the "
        "authors justify the small size by the lack of public machine-readable Saudi legal data and by privacy rules, and note that "
        "the sets were built under expert supervision. All experiments ran in a cloud environment (Intel Xeon Platinum 8272CL, 32 GB, "
        "Ubuntu 20.04, API round-trip of 280 to 350 ms) and timings were averaged over three runs.",
        "**Reported results.** Without retrieval, Gemini 1.5 Flash answered 148 of 150 questions correctly (98.67%) with an average "
        "response time of 1.63 s, ahead of GPT-3.5 (98.00%, 147 correct), GPT-4 (97.33%, 146, 2.56 s) and ALLaM (96.00%, 144, 4.51 s). "
        "With RAG the average similarity to the reference answer was 96.57% for Gemini at 143.52 s per query, which the authors explain "
        "as the cost of a full evaluation pipeline without caching, not the latency of the deployed system. For contract analysis the "
        "paper reports no numeric score; it compares sample outputs. In the sample shown, Gemini returned seven flagged clauses, six of "
        "which were judged accurate and the first erroneous, ALLaM nine (the first incorrect, with repetition), Command A five (the "
        "first incorrect) and GPT-4 six (the first wrong, and one clause that merged three issues).",
        "**Failure cases and limitations stated by the authors.** Three kinds of error are described: incomplete retrieval when a "
        "relevant clause spans several chunks, misclassification of multi-purpose clauses that cover payment, liability and "
        "confidentiality together (the model assigns only one category), and, in a few answers, a statutory citation that was not in "
        "the retrieved context. They also note that performance on very ambiguous texts may vary, that a limited legal database restricts "
        "adaptation to changing regulation, that language models carry bias, and that legal data are unstructured and must be cleaned.",
        "**What ClauseGuard adopts and what it changes.** ClauseGuard keeps the jurisdiction-aware, language-model-based design: contract "
        "text is turned into clauses, clause-level analysis uses a hosted Gemini model, and the result is written in plain language. It "
        "changes the following: the jurisdiction (Indian law, English text), the detection method (curated rules tied to statutes "
        "instead of a checklist and free-form LLM judgement), the unit of risk (combinations of clauses, which the base paper's own "
        "failure analysis does not address), the addition of a complexity grade, and the evaluation (clause classification and predatory "
        "detection scored separately on stated data). It drops the pieces it did not build: the legal-corpus retrieval with re-ranking, "
        "OCR and the chatbot.")
    d.table([["Aspect", "Base paper [1]", "ClauseGuard"],
             ["Jurisdiction and language", "Saudi law, Arabic", "Indian contract law, English"],
             ["Language model", "Gemini 1.5 Flash", "Gemini (embeddings; text model gemini-flash-latest by default, gemini-3.1-flash-lite in the measured run)"],
             ["Retrieval", "Semantic chunks, GATE-AraBERT-v1, Chroma, cross-encoder re-ranking", "No legal-corpus retrieval; nearest centroid over 20 CUAD categories (NumPy cosine, SQLite vectors)"],
             ["Contract analysis", "Checklist of essential clauses plus clause-level LLM analysis; contradiction pairs", "Eight statute-tagged regex rules, three clause combinations, LLM explanation and safer wording"],
             ["Complexity measure", "None", "Flesch, legalese density, cross-references, sentence length, A-F grade"],
             ["Input", "PDF through an OCR step", "PDF (text layer) and DOCX; no OCR"],
             ["Data", "150 questions, 50 contract drafts (Arabic)", "CUAD for classification (240 held-out spans), 40 curated clauses and 40 probe clauses for rules, 510 CUAD contracts for scale"],
             ["Evidence of contract analysis", "Qualitative comparison of sample outputs", "Measured: precision 1.000 / recall 0.941 (authored set), 0.786 / 0.458 (probe set); top-1 0.792 (classification)"],
             ["Comparability", "Different language, law, task and data", "No numeric head-to-head is claimed"]],
            "Base paper compared with ClauseGuard", widths=[0.2, 0.38, 0.42], font=9.5)


def sec_related(d):
    d.h2("Related Work")
    d.h3("Benchmarks of language models on clause-level risk")
    d.paras(
        "ContractEval [2] asks whether open-source models can match proprietary ones at identifying clause-level legal risk. It builds "
        "on the CUAD test data [8] (41 clause categories annotated by lawyers) and evaluates 19 models (four proprietary and fifteen "
        "open-source) by F1 and F2, by the Jaccard similarity of the extracted span to the labelled span, and by a \"laziness\" rate, "
        "the share of answers that wrongly say that no related clause exists. GPT-4.1 reached F1 0.641 and F2 0.672, and GPT-4.1 mini F1 "
        "0.644 and F2 0.678; Gemini 2.5 Pro Preview reached F1 0.497 and Claude Sonnet 4 F1 0.523, although Gemini 2.5 Pro had the lowest "
        "laziness rate (0.011) and the highest Jaccard score (0.506) among the proprietary models. The best open-source result was F1 0.540 "
        "(Qwen3 8B in thinking mode). The authors conclude that proprietary models are more correct, that larger open models do better "
        "with diminishing returns, that thinking mode raises output effectiveness but lowers correctness, and that most models perform "
        "at the level of a junior legal assistant. For this project the paper shows that even strong models miss many CUAD risk clauses, "
        "which supports pairing a language model with auditable rules instead of trusting it alone.")
    d.h3("Domain-trained and frontier models for contract extraction")
    d.paras(
        "Lincoln et al. [3] compare a domain-trained Mixture-of-Experts model, Olava Extract, with five frontier systems (Claude Opus 4.6, "
        "Claude Sonnet 4.6, Gemini 2.5 Pro, Gemini 3.1 Pro Preview and GPT-5.4) on 24 held-out public contracts with 508 labelled field "
        "instances over 26 fields. Each contract was given whole to the model in one call, without chunking or retrieval, and the "
        "train and test contracts were separated by document identifier. The domain model reached a macro F1 of 0.812 and a micro F1 of "
        "0.842, the highest precision (fewer unsupported answers) and a cost of $0.018 per contract under batching, but it trailed the "
        "leader by more than 0.05 F1 on 7 of the 26 fields, mostly currency, date and option-list fields. The lesson for ClauseGuard is "
        "methodological: separating training and test contracts by document is the stricter protocol, and the CUAD split used by the "
        "project's evaluation script does not do this (Chapter 8).")
    d.h3("Clause extraction and risk-scoring systems")
    d.paras(
        "The LDAS system of Dhaksha Charan R and colleagues [4] is a serverless pipeline on AWS (Lambda, S3 and a generative model "
        "reached through Bedrock) that extracts ten clause types from PDF and DOCX files, marks clauses that are missing against a "
        "configurable template, and computes a weighted risk score from 0 to 100 in which high-risk clause types weigh 10 and medium "
        "types 5. On its primary test document, a software-services invoice, it reported eight deviations (six high, two medium), a score "
        "of 87 and no false positives; on 20 synthetic contracts a 94.2% average extraction accuracy; a Pearson correlation of 0.87 between "
        "its risk score and expert ratings over 30 sample contracts; and 14 of 15 contract pairs compared correctly. An end-to-end run "
        "took 62 s on average over 50 submissions. The system detects *missing* clauses, not predatory wording, and its evidence rests on "
        "one primary document and synthetic contracts. It is nevertheless the closest published example of the score-and-explain design "
        "used here, and it reports the one validation of a risk score against human ratings that this project lacks.",
        "Three further papers appear in the batch survey: ClauseMiner, a prompt-engineered language model for scalable legal clause "
        "extraction [5]; a study of contract risk detection with Legal-BERT [6]; and a study of language-model-based risk detection in "
        "construction contracts [7]. They could not be retrieved, so only their titles are used: they indicate that prompt-based extraction, "
        "a legal-domain encoder and a vertical (construction) application are active directions, but nothing about their data or results "
        "is claimed here.")
    d.h3("Legal-domain language models and text embeddings")
    d.paras(
        "BERT [10] introduced pre-trained bidirectional transformers for language understanding, and LEGAL-BERT [9] showed that "
        "pre-training or further pre-training on legal text helps legal tasks. Sentence-BERT [12] made sentence embeddings practical "
        "for similarity search, and Gemini Embedding [13] is the family to which the embedding model of this project belongs. ClauseGuard "
        "does not train or fine-tune any of them: it uses a hosted embedding model and measures how well the clause vectors separate the "
        "twenty CUAD categories.")
    d.h3("Retrieval-augmented generation")
    d.paras(
        "Retrieval-augmented generation [11] combines a retriever with a generator so that an answer can rest on retrieved passages. The "
        "base paper [1] applies it to a Saudi legal corpus. ClauseGuard does not retrieve from a corpus of laws: it embeds the clause, "
        "finds the nearest category centroid and, for each rule hit, places the rule's hand-written statement of its legal basis in the "
        "prompt. This is grounding by prompt, not retrieval, and the report says so wherever the architecture is described.")
    d.h3("Readability, complexity and graph reasoning")
    d.paras(
        "The Flesch reading ease [15] is a long-standing measure of how difficult a text is to read, computed from sentence and word "
        "length. None of the surveyed contract tools reports a document-level complexity grade, which is the contribution of this project's "
        "scoring module; its weights are the author's own and are not validated. Graph libraries such as NetworkX [16] make it easy to "
        "represent clauses as nodes and relations as edges. No surveyed work reasons over combinations of risky clauses, and the "
        "ClauseGuard graph is limited to three patterns written by hand.")
    d.table(LIT_TABLE, "Comparison of the surveyed works", widths=[0.16, 0.24, 0.17, 0.2, 0.23], font=8.5)


def sec_lit_algorithms(d):
    d.h2("Datasets and Algorithms Used in the Literature and in ClauseGuard")
    d.h3("Datasets")
    d.table([["Dataset", "Content", "Use in ClauseGuard"],
             ["CUAD v1 [8]", "510 commercial contracts, 41 categories of clause annotated by lawyers, CC BY 4.0; mostly US filings", "Twenty substantive categories: 500 training spans (25 per category) for the centroids, 240 held-out spans (12 per category) for classification; all 510 contracts for the scale run"],
             ["Curated Indian-law test set", "40 clauses labelled with the rules they should trigger, written with the rules", "Predatory-detection score of the shipped evaluation (precision 1.000, recall 0.941)"],
             ["Independent probe set", "24 predatory paraphrases and 16 benign look-alikes written during the documentation run", "Second predatory-detection score (precision 0.786, recall 0.458)"],
             ["Invented and public sample contracts", "Two invented contracts (one-sided freelance, fair consulting) and one real CUAD contract typeset as PDF", "End-to-end uploads and screenshots"],
             ["Saudi corpus and contract drafts [1]", "150 questions and 50 Arabic drafts of the base paper", "Not available; cited only"]],
            "Datasets in the literature and in this project", widths=[0.22, 0.38, 0.4], font=9.5)
    d.h3("Algorithms and software")
    d.table([["Technique", "Reference", "Role in ClauseGuard"],
             ["Text embeddings (gemini-embedding-001, 3,072 dimensions)", "[10], [12], [13]", "Clause vectors for nearest-centroid classification"],
             ["Nearest centroid, cosine similarity", "[12]", "Assign one of 20 CUAD categories; baselines were k-NN, logistic regression and TF-IDF"],
             ["TF-IDF term weighting and logistic regression", "[14], [17]", "Baselines in the classification experiment (top-1 0.621 and 0.675)"],
             ["Retrieval-augmented generation", "[11], [1]", "Compared with; ClauseGuard grounds explanations through the rule's legal basis in the prompt"],
             ["Regular-expression rules tied to statutes", "[20]-[23]", "Eight predatory-clause detectors"],
             ["Language-model explanation", "[1]", "Reason, quoted provision, safer wording, summary and key obligations"],
             ["Flesch reading ease", "[15]", "Readability component of the complexity score"],
             ["Graph of clauses (NetworkX)", "[16]", "Nodes for clauses, edges for the three risky combinations"],
             ["bcrypt password hashing, JSON Web Tokens", "[18], [19]", "Authentication of users and API calls"],
             ["scikit-learn", "[17]", "Baseline classifiers and metrics in the experiment scripts"]],
            "Techniques and their role", widths=[0.36, 0.16, 0.48], font=9.5)


def sec_lit_strengths(d):
    d.h2("Strengths and Limitations of Existing Work")
    d.table([["Work", "Strengths", "Limitations for this project"],
             ["SmartLaw Advisor [1]", "Complete pipeline with retrieval, re-ranking, OCR and contract analysis; expert-validated checklist; model comparison; honest failure analysis", "Arabic and Saudi law; contract-analysis results are qualitative; no combinations of clauses; no complexity measure; small data"],
             ["ContractEval [2]", "Expert-annotated CUAD test data; 19 models; correctness, span quality and laziness measured separately", "Measures extraction of spans, not explanation or jurisdiction; US contracts; no combination logic"],
             ["A Few Good Clauses [3]", "Full-document protocol; contracts separated by identifier; cost and latency reported", "Field extraction, not risk; domain model is closed; 24 contracts"],
             ["LDAS [4]", "Score and explanation in one product; end-to-end timing; correlation of the score with expert ratings", "Detects absent clauses rather than predatory wording; one primary document, synthetic and sample contracts"],
             ["ClauseMiner, Legal-BERT contract risk, construction risk [5]-[7]", "Indicate prompt-based extraction, a legal encoder and a vertical application", "Not retrieved; nothing about their data or results is claimed"],
             ["Commercial contract tools (general knowledge, not surveyed)", "Enterprise integration and large clause libraries", "Aimed at companies, US or EU law; not assessed in this work"]],
            "Strengths and limitations of the surveyed works", widths=[0.22, 0.38, 0.4], font=9.5)
    d.p("None of the surveyed systems analyses combinations of clauses, reports a document-level complexity grade, or covers Indian "
        "contract law. These three facts define the gap that ClauseGuard addresses. The last row of the table is general background and "
        "was not examined in detail in this work.")


def sec_gap(d):
    d.h2("Research Gap")
    d.p("Contract analysis tools mostly target US and EU law and single clauses; jurisdiction-aware detection of predatory clause "
        "combinations in Indian contracts remains underrepresented. The table lists the specific gaps, the evidence in the surveyed work "
        "and how far this project closes each one.")
    d.table([["Gap", "Evidence in the surveyed work", "How ClauseGuard responds, and how far"],
             ["Indian contract law is not covered", "The base paper is Saudi [1]; the benchmark and extraction studies use US contracts [2], [3], [8]", "Eight rules tied to the Indian Contract Act, the Arbitration and Conciliation Act, the Consumer Protection Act and the Copyright Act [20]-[23]. Partly closed: the rules are keyword patterns (recall 0.458 on independent clauses) and no Indian contract corpus was available"],
             ["Clauses are analysed one at a time", "No surveyed work reports a risk that arises from a combination of clauses", "Three fixed combinations of rule identifiers. Partly closed: 3 patterns, matched anywhere in the contract; no data to say how common or harmful they are beyond 11 of 510 CUAD contracts"],
             ["Classification and risk detection are conflated", "ContractEval scores extraction by category; LDAS reports one risk score; the base paper reports question accuracy [1], [2], [4]", "Two separate scores: top-1 0.792 for classification and precision/recall for rules. Closed for this build; both scores have caveats stated in Chapter 8"],
             ["Reviews are not written for non-lawyers", "Outputs of the surveyed work are labels, spans or scores", "Plain-language reason, quoted provision, safer wording and summary per contract. Not verified by a lawyer"],
             ["No complexity grade for the whole document", "None of [1]-[4] reports one", "A to F grade from four text measures. Lexical only; unvalidated against human ratings"],
             ["Grounded retrieval over Indian law", "The base paper retrieves from a Saudi corpus [1]", "**Not closed**: ClauseGuard has no retrieval over a legal corpus and no knowledge graph of concepts and precedents"]],
            "Research gaps and the response of this project", widths=[0.22, 0.34, 0.44], font=9.5)
