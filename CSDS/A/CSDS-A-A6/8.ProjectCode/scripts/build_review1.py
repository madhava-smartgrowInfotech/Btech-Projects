"""Build 7.Review_1_PPT.pptx from D:\\abstracts\\Templates\\Review_1_PPT.pptx (16 slides) for ClauseGuard.

    python scripts/build_review1.py
Every number comes from docs/REPORT_FACTS.md (section 9 for the literature) and the batch documents 2-6.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deckkit import fill, put_picture, replace_chart, set_notes, set_paras, set_table, shape, style_chart, table_size  # noqa: E402
from doc_common import BATCH, BATCH_NAME, COLLEGE, DEPT, DIAG, GUIDE, GUIDE_DESIG, PRODUCT, REFERENCES, STUDENTS, SUBTITLE, YEAR  # noqa: E402
from pptx import Presentation  # noqa: E402

SRC = r"D:\abstracts\Templates\Review_1_PPT.pptx"
OUT = BATCH / "7.Review_1_PPT.pptx"
FOOTER = f"{PRODUCT}  \u00b7  Review 1  \u00b7  Batch A6"


def scrub_theme(path):
    """The template's theme is named after another project: rename it."""
    import shutil
    import zipfile
    tmp = Path(str(path) + ".tmp")
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.startswith("ppt/theme/") and item.filename.endswith(".xml"):
                data = data.decode("utf-8").replace("Hidden Risk", PRODUCT).encode("utf-8")
            zout.writestr(item, data)
    shutil.move(tmp, path)


def build():
    prs = Presentation(SRC)
    S = list(prs.slides)
    cp = prs.core_properties
    cp.title, cp.subject, cp.author = f"{PRODUCT}: Review 1", SUBTITLE, "Batch A6"
    cp.keywords = "legal NLP, contract analysis, predatory clauses, CUAD, Indian contract law"
    cp.category = cp.comments = cp.content_status = ""
    cp.last_modified_by = "Batch A6"
    for lay in prs.slide_layouts:
        for sh in lay.shapes:
            if sh.has_text_frame and sh.text_frame.text.startswith("The Hidden Risk"):
                set_paras(sh, FOOTER)
    for sl in S:
        for sh in sl.shapes:
            if sh.has_text_frame and sh.text_frame.text.startswith("The Hidden Risk"):
                set_paras(sh, FOOTER)

    # 1 title
    s = S[0]
    set_paras(shape(s, 2), PRODUCT)
    set_paras(shape(s, 3), SUBTITLE)
    set_paras(shape(s, 6), [f"{n}  {r}" for n, r in STUDENTS], 15)
    set_paras(shape(s, 8), f"{GUIDE}, {GUIDE_DESIG}")
    set_paras(shape(s, 9), [DEPT, f"{COLLEGE}  \u00b7  {BATCH_NAME}  \u00b7  {YEAR}"], 13)
    set_notes(s, "Review 1 covers problem identification and research for ClauseGuard, a tool that scores the complexity of a contract and flags predatory clauses, with a focus on Indian contract law.")

    # 2 contents
    set_notes(S[1], "Nine parts: the abstract, the base paper and related work, the existing systems and their limits, the research gap, our problem statement and objectives, the approach and architecture, expected outcomes and references.")

    # 3 abstract
    s = S[2]
    set_paras(shape(s, 2), "Abstract: reading a contract before signing it")
    fill(s, 8, "Freelancers, individuals and small businesses sign contracts with complex, ambiguous or predatory clauses and have no affordable legal review. The weaker party faces information asymmetry.", 16)
    fill(s, 13, "Split a contract into clauses, classify each clause type, flag predatory clauses against Indian contract-law criteria, find clause combinations that are risky together, and score overall complexity. A retrieval and LLM pipeline writes the plain-language explanation.", 15)
    fill(s, 18, "A web application: upload a PDF or DOCX, get a complexity grade, a clause-by-clause risk breakdown with the quoted provision and safer wording, and a clause graph. Classification and predatory detection are evaluated separately.", 15)
    set_notes(s, "The abstract in one slide: the problem for non-experts, the idea of jurisdiction-aware clause analysis, and the web application that is the deliverable.")

    # 4 base paper
    s = S[3]
    fill(s, 5, REFERENCES[0], 14)
    set_paras(shape(s, 7), "Method")
    fill(s, 8, "A legal chatbot and a contract-analysis module for Saudi law. Gemini 1.5 Flash with retrieval-augmented generation over an Arabic legal corpus (GATE-AraBERT-v1 embeddings, a Chroma vector store, cross-encoder reranking). Contracts are checked against a practitioner-validated clause checklist plus LLM semantic analysis.", 14)
    set_paras(shape(s, 10), "Data and reported results")
    fill(s, 11, "150 legal questions over ten domains and 50 real contract drafts. Gemini 1.5 Flash answered 148 of 150 questions correctly (98.67 %), ahead of GPT-3.5 (98.00 %), GPT-4 (97.33 %) and ALLaM (96.00 %). Contract-analysis results are shown clause by clause, not as a score.", 14)
    set_paras(shape(s, 13), "Limits and our adaptation")
    fill(s, 14, "Arabic and Saudi law only, a small expert-reviewed dataset, no clause-combination reasoning and no complexity score. We keep its retrieval-first, jurisdiction-aware design for Indian contracts and add combination detection and a complexity grade.", 14)
    set_notes(s, "The base paper is SmartLaw Advisor (IEEE Access, 2026). We adopt its jurisdiction-aware RAG design and its contract-analysis idea, and extend it to Indian contracts with clause combinations and a complexity score.")

    # 5 literature survey
    s = S[4]
    rows = [["Work", "Approach", "Data", "Reported result"],
            ["Almutairy et al., 2026 (base) [1]", "Gemini 1.5 Flash + RAG over a Saudi corpus; clause checklist + LLM analysis", "150 questions, 50 contract drafts (Arabic)", "98.67 % (148 of 150) on questions; contract analysis shown qualitatively"],
            ["Liu et al., ContractEval, 2025 [2]", "Benchmark of 19 LLMs on clause-level legal risk identification", "CUAD test data, 41 categories", "Proprietary models beat open-source; top two F2 = 0.672 and 0.678"],
            ["Lincoln et al., 2026 [3]", "Domain-trained small model vs five frontier LLMs for structured extraction", "24 held-out contracts, 508 field instances", "Macro F1 0.812, micro F1 0.842; cost down 78-97 %"],
            ["Charan R et al., 2026 [4]", "Serverless GenAI clause extraction with a weighted 0-100 risk score", "20 synthetic contracts; 30 rated contracts", "94.2 % extraction accuracy; r = 0.87 with expert ratings"],
            ["ClauseMiner, 2026 [5]", "Prompt-engineered LLM clause extraction (from the title)", "Listed in survey, not retrieved", "Not retrieved"],
            ["Legal-BERT clause risk detection, 2025 [6]", "Clause risk detection with Legal-BERT (from the title)", "Listed in survey, not retrieved", "Not retrieved"],
            ["LLM construction-contract risk detection, 2024 [7]", "LLM-based risk detection (from the title)", "Listed in survey, not retrieved", "Not retrieved"]]
    sz = table_size(rows, 1164, 520, [0.24, 0.31, 0.21, 0.24], 14, 9)
    set_table(shape(s, 6), rows, sz, header_size=sz)
    set_notes(s, "[1] to [4] were read in full. [5] to [7] are in the batch literature survey but could not be retrieved, so only their titles are used and no results are claimed for them.")

    # 6 supporting evidence
    s = S[5]
    set_paras(shape(s, 2), "Supporting evidence: LLMs on legal tasks")
    ch = replace_chart(s, 4, ["Gemini 1.5 Flash", "GPT-3.5", "GPT-4", "ALLaM"], [("Accuracy (%)", [98.67, 98.00, 97.33, 96.00])], number_format="0.00")
    style_chart(ch, "Accuracy on 150 Saudi legal questions, baseline models, from the base paper [1] (%)", ["3F3FBF"], number_format="0.00", legend=False, label_pt=12, axis_title="accuracy (%)")
    ch.value_axis.minimum_scale = 0
    ch.value_axis.maximum_scale = 100
    set_paras(shape(s, 8), "Takeaway")
    fill(s, 9, "LLMs answer legal questions accurately [1], but finding the risky clause is harder: on CUAD the best models reach an F2 of about 0.67 [2], and a small domain-trained model can match frontier models on extraction [3].", 14)
    set_paras(shape(s, 13), "Caveat")
    fill(s, 14, "These are published results on other tasks and data (Arabic law, US contracts). They motivate our design; they are not our results. Our own measurements come in the later reviews.", 14)
    set_notes(s, "The chart shows the base paper's baseline accuracy for four models on its own 150-question set. ContractEval and the Onit study are cited in words because their metrics differ.")

    # 7 existing system
    s = S[6]
    set_paras(shape(s, 2), "Existing system and current approaches")
    steps = ["Receive the contract", "Read alone, or pay a lawyer", "Review is slow and costly", "Clauses read one by one", "Sign without full understanding", "Hidden liability found late"]
    for sid, t in zip((5, 8, 11, 14, 17, 20), steps):
        fill(s, sid, t, 14)
    set_paras(shape(s, 24), "Manual and enterprise review")
    fill(s, 25, "Contracts are reviewed by lawyers or signed with no expert help. Commercial analysis tools target enterprises and US or EU law.", 16)
    set_paras(shape(s, 29), "Research systems and chatbots")
    fill(s, 30, "Research systems classify clause types on datasets such as CUAD. General chatbots can summarise a contract but are not grounded in legal context.", 16)
    set_notes(s, "How a freelancer or small business handles a contract today, and what tools exist.")

    # 8 limitations
    s = S[7]
    set_paras(shape(s, 2), "Limitations of existing methods")
    for tid, bid, ttl, body in [
        (7, 8, "Costly and slow", "Professional legal review is expensive and slow for individuals and small businesses."),
        (12, 13, "Indian law ignored", "Existing tools rarely consider Indian contract law."),
        (17, 18, "Clauses in isolation", "Risky combinations are missed, and classification and predatory detection are often mixed in one score."),
        (22, 23, "Ungrounded summaries", "General LLM summaries may be inaccurate and lack clause-level references.")]:
        set_paras(shape(s, tid), ttl)
        fill(s, bid, body, 16)
    set_notes(s, "Four limitations taken from the literature survey: cost, jurisdiction, isolated clauses and ungrounded summaries.")

    # 9 research gap
    s = S[8]
    gaps = [("Jurisdiction", "Analysis tools mostly target US and EU law; Indian contracts are under-represented. The base paper is Saudi-specific [1]."),
            ("Combinations", "Clauses are analysed one at a time; clause pairs that are harmless alone but dangerous together are missed."),
            ("Evaluation", "Clause classification and predatory-clause detection are often reported as one number."),
            ("Explanation", "Users need the quoted provision, the reason in plain language and a safer wording."),
            ("Access", "Freelancers and small businesses need an affordable first-pass review before signing.")]
    for (lid, tid), (lab, txt) in zip([(5, 6), (8, 9), (11, 12), (14, 15), (17, 18)], gaps):
        set_paras(shape(s, lid), lab)
        fill(s, tid, txt, 16)
    set_notes(s, "Jurisdiction-aware detection of predatory clause combinations in Indian contracts is under-represented in the literature we surveyed.")

    # 10 problem statement
    s = S[9]
    fill(s, 5, "Non-experts cannot easily spot predatory or ambiguous clauses, and legal review is out of reach for freelancers and small businesses. We need an affordable, jurisdiction-aware tool that flags predatory clauses and combinations in an Indian contract and explains the risk in plain language before signing.", 22)
    set_paras(shape(s, 8), "A contract file (PDF or DOCX)")
    set_paras(shape(s, 11), "Clause types, flagged clauses, risky combinations")
    set_paras(shape(s, 14), "Complexity grade + plain-language summary")
    set_notes(s, "Input is a contract file; outputs are clause types, flags with reasons, combinations and a complexity grade; the extra property is a plain-language explanation tied to each clause.")

    # 11 objectives
    s = S[10]
    fill(s, 4, ["Segment uploaded contracts into clauses and classify clause types.",
                "Build a retrieval-augmented pipeline: an LLM API plus semantic search over clause embeddings.",
                "Model clause relationships in a graph to find risky combinations.",
                "Flag predatory clauses and combinations using Indian contract-law criteria.",
                "Compute an overall complexity score and a plain-language risk summary.",
                "Evaluate clause classification and predatory detection separately (CUAD and curated criteria)."], 22, bullet=True)
    set_notes(s, "The six objectives of the project, from the batch objectives document.")

    # 12 proposed approach
    s = S[11]
    for tid, bid, ttl, body in [
        (7, 8, "Segment and classify", "PDF or DOCX split into clauses with page numbers; each clause matched to one of 20 CUAD categories by embedding similarity."),
        (12, 13, "Predatory-clause rules", "Eight Indian-law rules (restraint of trade, penalty, unilateral termination and more); the LLM writes the reason, quote and safer wording."),
        (17, 18, "Clause graph", "A graph of clauses flags three combinations that are risky together, such as termination + no refund + penalty."),
        (22, 23, "Complexity grade", "Readability, legal jargon, cross-references and sentence length combine into a score and an A-F grade, with a plain summary."),
        (27, 28, "Web app and evaluation", "React + FastAPI + SQLite. Classification is scored on CUAD and predatory detection on a curated Indian-law set, separately.")]:
        set_paras(shape(s, tid), ttl)
        fill(s, bid, body, 13)
    set_notes(s, "The approach as built: Gemini embeddings and text generation, a NumPy similarity search and a NetworkX graph in place of the planned Claude API, pgvector and Neo4j, to keep the prototype simple to run locally.")

    # 13 architecture
    s = S[12]
    put_picture(s, DIAG / "01_system_architecture.png", (150, 105, 980, 490), remove_ids=(4,), name="System architecture diagram")
    set_paras(shape(s, 5), "Proposed architecture: React web app, FastAPI backend with parsing, classification, rule, graph and complexity services, SQLite, and the Gemini API")
    set_notes(s, "Browser to React to FastAPI. The services run in the backend; embeddings and explanations come from the Gemini API; data stay in SQLite and local files.")

    # 14 expected outcomes
    s = S[13]
    for tid, bid, ttl, body in [
        (7, 8, "Clause map", "Every clause with its page, type and confidence."),
        (12, 13, "Predatory flags", "Flags with the quoted provision and the Indian-law reason."),
        (17, 18, "Safer wording", "A fairer rewrite for each flagged clause."),
        (22, 23, "Risky combinations", "A clause graph that links clauses risky together."),
        (27, 28, "Complexity grade", "An A-F grade and a plain-language summary."),
        (32, 33, "Honest evaluation", "Two separate scores, with limits stated plainly.")]:
        set_paras(shape(s, tid), ttl)
        fill(s, bid, body, 16)
    set_notes(s, "Expected outcomes are targets at this stage; they are measured and reported honestly in the later reviews.")

    # 15 references
    s = S[14]
    fill(s, 4, [f"[{i}] {r}" for i, r in enumerate(REFERENCES[:10], 1)], 14, min_pt=8.5, bullet=True, gap_pt=3)
    set_notes(s, "References [1] to [10]; [5] to [7] are listed in the batch survey but were not retrieved. The full list is in the report.")

    set_notes(S[15], "Thank you. Questions are welcome.")
    prs.save(OUT)
    scrub_theme(OUT)
    print("saved", OUT, len(prs.slides._sldIdLst), "slides")


if __name__ == "__main__":
    build()
