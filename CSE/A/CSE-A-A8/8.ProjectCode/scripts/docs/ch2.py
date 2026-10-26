"""Chapter 2: Literature survey.

Figures quoted here come from the base paper's PDF, the two archived arXiv PDFs, or the publisher / arXiv record of the cited work.
Where a work could only be checked at abstract level the text says so.
"""

from .blocks import B, FIG, H1, H2, H3, N, P, TAB
from .refs import n
from . import facts as F

LIT_TABLE = [
    ["Karhade et al., 2025 [1] (base paper)", "RAG on LLaMA-3 8B; ChromaDB; chunks 1,024 / overlap 100; top-3 retrieval", "20 medical books, 383 YouTube transcripts, a 33-parameter range document", "20 responses scored 1-100 by GPT-4: correctness 92.4, clarity 89.7, helpfulness 91.1, completeness 88.9 (as stated)", "Metabolic syndrome only; no extraction accuracy, latency or trend tracking"],
    ["Ren et al., 2025 [2]", "Serialisation of image-based lab reports into structured data (abstract-level reading)", "Phone-photographed lab reports for teleconsultation", "Not read beyond the abstract", "Full text not reviewed"],
    ["Xiang et al., 2026 [3] (Checkup2Action)", "Constrained LLM workflow producing structured Action Cards", "2,000 de-identified real check-up reports", "Experts judged 84% of outputs fully reasonable; removing safety constraints raised recall 0.527 to 0.825 with more diagnostic overstatement", "Needs multimodal reports; actions, not value tracking"],
    ["Bakhsheshi and Beigy, 2025 [4]", "Qwen-VL-Max, Gemini 2.5 Pro, Llama 4 Maverick prompted with report images", "100 blood-report images chosen from 426 in a public Kaggle set", "Mean pairwise Sentence-BERT similarity 0.803 between the models' answers", "Measures agreement between models, not correctness; small set"],
    ["Nguyen et al., 2025 [5] (Medalyze)", "Three fine-tuned FLAN-T5-Large models behind a web and a mobile application", "Medical report and conversation text", "Not read beyond the abstract", "Summarises text; no value extraction from files"],
    ["Lewis et al., 2020 [6]", "Retrieval-augmented generation", "Knowledge-intensive NLP benchmarks", "Foundation of the RAG approach used in [1]", "General-domain; not specific to lab values"],
    ["Hsu et al., 2025 [10] (MEDPLAN)", "Two-stage RAG: assessment, then personalised plan", "Electronic health records", "As summarised in [1]", "Needs clinical notes; not report files"],
    ["Du et al., 2020 [12] (PP-OCR)", "Ultra-lightweight OCR system", "General text images", "Practical, small models (abstract level)", "Needs the PaddlePaddle runtime; not adopted here"],
    ["Smith, 2007 [13] (Tesseract)", "Open-source OCR engine", "General documents", "Widely deployed baseline engine", "Sensitive to scan quality; adopted here for images"],
]


def blocks():
    c = F.NAMES
    ex = F.EXTRACTION["overall"]
    return [
        H1("CHAPTER 2: LITERATURE SURVEY"),
        H2("2.1 Overview"),
        P(f"This chapter begins with a close reading of the base paper {n(1)}, then groups related work by theme: digitising report images, turning reports into "
          f"patient-facing guidance, retrieval and language models in healthcare, and the OCR and sequence-labelling techniques named in the project abstract. "
          "It ends with the research gap. Where a work was checked only at abstract level, or only through the base paper's own summary of it, the text says so. "
          "Five works were listed in the batch literature survey; only the first is the base paper. The other four are discussed in Section 2.4."),
        H2("2.2 Base paper analysis"),
        P(f"**Reference.** {F.BASE_PAPER}"),
        H3("2.2.1 Problem and approach"),
        P("The paper argues that blood test reports are hard for the general population to interpret, that minor changes are often mistaken for serious problems, "
          "and that metabolic syndrome, a cluster of raised glucose, blood pressure, triglycerides, glycated haemoglobin and insulin resistance with low HDL, is a case where "
          "understanding the report leads to lifestyle action. It proposes a generative AI system that explains a report and suggests diet and lifestyle changes, "
          "and alerts the user when a medical consultation may be needed."),
        H3("2.2.2 Knowledge base and parameters"),
        P("The knowledge base holds 20 medical books (text extracted with PyMuPDF and cleaned), 383 YouTube video transcripts (produced with the Whisper model and "
          "cleaned) and a parameter document. The parameter document lists 33 blood parameters in the groups complete blood count, glucose, insulin, "
          "lipid profile, apolipoproteins, liver, kidney and thyroid function, vitamins, homocysteine and inflammation markers, each with a normal, "
          "an optimal and a possible range, separately for men and women where they differ."),
        H3("2.2.3 Retrieval and generation"),
        P("Text is split with a recursive character splitter into chunks of 1,024 characters with an overlap of 100, embedded, and stored in the ChromaDB vector store. "
          "A user query is embedded in the same way, the top three chunks by cosine similarity are retrieved after a threshold filter, and the chunks are "
          "concatenated with the query into a prompt for the LLaMA-3 8-billion-parameter model. Sources are returned with the answer, and a generic answer is given "
          "if nothing relevant is retrieved. The authors chose LLaMA-3 over OpenAI and DeepSeek models for cost, open licence and local deployment. Users have "
          "accounts, and uploaded reports are stored encrypted and reused in later queries."),
        H3("2.2.4 Evaluation and what it shows"),
        P("Evaluation uses 20 responses, each scored from 1 to 100 by GPT-4 on correctness, clarity, helpfulness and completeness, with human monitoring. The "
          "conclusion states averages of 92.4, 89.7, 91.1 and 88.9. Recomputing the means from the paper's own Table 4 gives 94.0, 94.9, 90.1 and 88.65, so the stated and "
          "tabulated numbers disagree; this report quotes both and relies on neither as a benchmark."),
        TAB("Base paper compared with this project", ["Aspect", "Base paper [1]", "This project"], [
            ["Scope", "Metabolic syndrome; 33 parameters", "Any test that appears on a report line; 55-name dictionary for name matching"],
            ["Input", "Report supplied to the chat system (parsed with PyMuPDF)", "PDF, JPG, JPEG or PNG; text layer or OpenCV + Tesseract OCR"],
            ["Explanation", "RAG over books and transcripts with LLaMA-3 8B", "Rule-based text for 17 tests plus a generic fallback; optional LLM rewrite; no retrieval"],
            ["Evaluation", "20 responses scored by GPT-4", f"{c['n_dictionary_names']} names under noise; 1,680 labelled rows in 120 generated reports; latency; 36 tests"],
            ["Over time", "Listed as future scope", "Trends, report comparison and dashboard implemented"],
        ], widths=[1.1, 2.4, 2.8], size=10),
        H3("2.2.5 Strengths and weaknesses"),
        B("**Strengths:** grounding of advice in a curated knowledge base with source citations, a fall-back that avoids unsupported personalised answers, and a clear clinical focus.",
          "**Weaknesses:** single condition; no measurement of how accurately values are read from report files; the evaluator is itself an LLM, so the scores measure agreement with GPT-4's judgement; "
          "no latency, no comparison with a baseline and no trend analysis; the paper lists haemoglobin in mg/dL where g/dL is the clinical unit."),
        H2("2.3 Related work by theme"),
        H3("2.3.1 Digitising report images"),
        P(f"Ren et al. {n(2)} address a practical situation: in teleconsultation people photograph a laboratory report with a phone, and the content must be turned into "
          "structured data. We read this paper at abstract level only, but it confirms the first stage of this project, extraction before explanation, as a problem in its own right. "
          f"Bakhsheshi and Beigy {n(4)} take the opposite route and skip OCR: they send 100 blood-report images, selected from 426 in a public Kaggle collection, to three "
          "vision-language models (Qwen-VL-Max, Gemini 2.5 Pro and Llama 4 Maverick) with patient-style questions, and compare the answers with Sentence-BERT embeddings "
          f"{n(18)}. Their headline overall similarity is 0.803. This measures how much the models agree with each other, not whether they are right, and the authors "
          "themselves warn that the dataset is small. It does show that image-in, explanation-out is plausible, but without values stored in a structured form nothing can be trended."),
        H3("2.3.2 From reports to patient guidance"),
        P(f"Checkup2Action {n(3)} introduces a dataset of 2,000 de-identified real check-up reports and a constrained workflow that generates structured Action Cards, each with an "
          "issue, a priority, a recommended department, a follow-up window and a patient-facing explanation. Clinical experts judged 84% of evaluated outputs fully reasonable. "
          "Its most useful finding for this project concerns safety: removing the safety constraints raised problem recall from 0.527 to 0.825 but produced more diagnostic "
          "overstatement. That trade-off is why this project's explanations avoid diagnosis and always advise consulting a clinician. "
          f"Medalyze {n(5)} fine-tunes three FLAN-T5-Large models for report summarisation and related tasks and ships web and mobile front ends; we read its abstract only."),
        H3("2.3.3 Retrieval and language models in healthcare"),
        P(f"Retrieval-augmented generation {n(6)} combines a language model with an external knowledge store so that answers rest on retrieved passages. In healthcare, "
          f"Salvagno et al. {n(7)} assess the feasibility of ChatGPT for clinical and research scenarios and flag privacy and accuracy concerns; Liu et al. {n(8)} study AI-drafted replies in "
          f"electronic health records and report efficiency gains with personalisation and ethical concerns; Shokrollahi et al. {n(9)} review generative AI in healthcare; and "
          f"MEDPLAN {n(10)} uses a two-stage RAG design that first assesses and then plans treatment. These four are known to us through the base paper's summaries and their "
          f"bibliographic records. Kataria et al. {n(11)} review diet and lifestyle modification in metabolic syndrome, the clinical background of the base paper."),
        H3("2.3.4 OCR and sequence labelling"),
        P(f"The abstract names PP-OCR and a conditional random field (CRF). PP-OCR {n(12)} is a practical ultra-lightweight OCR system from the PaddlePaddle ecosystem. "
          f"Tesseract {n(13)} is the long-established open-source engine; it is the engine this project uses for images because it needs only one executable. "
          f"A linear-chain CRF {n(14)} labels each token of a sequence given its neighbours and would be trained on annotated report lines; no such annotated corpus exists for this "
          f"project, so a rule-based parser with a TF-IDF matcher {n(15, 16)} was used instead (Section 3.1)."),
        H2("2.4 Other works in the batch literature survey"),
        P(f"The batch survey lists four further titles: a 2025 digitisation method {n(2)}, and three items {n(25, 26, 27)} on laboratory health and safety, RT-PCR data from one "
          "hospital laboratory and inter-laboratory extraction testing of medical devices. The last three concern laboratory operation, not patient-facing report analysis. "
          "Their authors and content could not be verified from the information given, so they are listed in the references but are not used as evidence anywhere in this report."),
        H2("2.5 Datasets and algorithms used in the literature"),
        TAB("Summary of the literature", ["Work", "Approach", "Data", "Reported result", "Limitation"], LIT_TABLE,
            widths=[1.15, 1.35, 1.2, 1.5, 1.2], size=8.5),
        P("Across these works three kinds of data appear: curated text knowledge bases, images of reports, and full multimodal reports. None of them offers a publicly "
          "available, labelled set of lab-report rows with value, unit and range that could serve as ground truth for the extraction step. This project therefore generated one (Chapter 6), "
          "and says wherever it matters that the corpus is synthetic."),
        H2("2.6 Strengths and limitations of the existing approaches"),
        B("**Language-model approaches** produce fluent explanations quickly and need little engineering, but they are costly or need local hardware, can overstate findings [3], and "
          "give no structured record of the values for later comparison.",
          "**Retrieval-grounded approaches** [1] improve trust through citations, but depend on a curated corpus and, in the base paper, on one clinical condition.",
          "**Digitisation approaches** [2], [4] address input, but stop at extraction or at free-text answers.",
          "**Classical OCR and parsing** are cheap, transparent and fast, but brittle when a layout changes; Section 8 measures exactly how brittle."),
        H2("2.7 Research gap"),
        P("The survey shows plenty of work on explaining an already-digital report for one condition, and some on reading report images, but no open pipeline that does all of "
          "the following together: accepts a PDF or an image, extracts arbitrary test rows with unit and range, flags them, explains the abnormal ones with a safety disclaimer, "
          "and tracks each parameter across successive reports. The base paper itself places personalisation over several reports in future scope. This project addresses that "
          f"gap with a deliberately light design, and measures it: on a generated corpus the extraction stage reaches a row-level F1 of {F.f3(ex['row_f1'])}, with the failure modes "
          "reported in Chapter 8."),
    ]
