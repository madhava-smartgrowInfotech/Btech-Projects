"""Literature and framing data for the decks (Review 1, Review 2 and the final deck).

Every literature fact traces to docs/REPORT_FACTS.md or scripts/docs/refs.py (REF_NOTES); reference numbers match refs.CITE.
Items 2-4 of the batch survey could not be verified and are never used for a claim.
"""

from .refs import CITE as R

BASE_PAPER_TITLE = "A Hybrid Retrieval-Augmented Generation Framework for Intelligent Symptom Monitoring and Disease Guidance"
BASE_PAPER_VENUE = "U. S. Madhury and M. Ramesh - Int. J. Eng. Res. Sci. Technol., vol. 22, no. 3, 2026"

# [work, year, approach, finding / limitation]   (each cell <= 90 characters)
LIT_TABLE = [
    [f"Madhury & Ramesh [{R['base']}] (base paper)", "2026", "Sequence-NQ embeddings + FAISS + RAG over a symptom-disease base; login, history",
     "No numbers reported; one Typhoid example; no ablation or latency"],
    [f"Divya et al. [{R['divya']}]", "2018", "AI self-diagnosis chatbot for symptom conversations",
     "Described in [1] as effective; no figures read"],
    [f"Hsu & Yu [{R['hsu']}]", "2022", "Machine learning + natural-language understanding medical chatbot",
     "Better than rule-based chatbots per [1]; no figures read"],
    [f"Babu & Boddu [{R['babu']}]", "2024", "BERT-based medical chatbot for query understanding",
     "Ungrounded generation; no retrieval of sources"],
    [f"Peri et al. [{R['peri']}]", "2024", "RAG chatbot that chats with medical books",
     "Grounds answers in retrieved text; no symptom log or safety layer reported"],
    [f"Son et al. [{R['emr']}]", "2025", "RAG chatbot over hospital EMR manuals, fine-tuned BGE-M3 / E5 embeddings",
     "5,931 pairs; 97.6% / 89.7% retrieval accuracy; <10 ms; admin, not symptoms"],
    [f"Nananukul & Kejriwal [{R['clinicbot']}]", "2026", "ClinicBot: guideline extraction, evidence priority, citations (diabetes)",
     "System demonstration; no accuracy table; one disease"],
    [f"Gao et al. HyDE [{R['hyde']}]", "2023", "LLM writes a hypothetical answer that is embedded for retrieval",
     "Needs an LLM; here replaced by a fixed template"],
]

OBJECTIVES = [
    "Build a curated medical knowledge base and index it for semantic retrieval",
    "Accept symptoms in natural language and expand the query to improve recall",
    "Implement hybrid retrieval combining dense vector search with neural reranking",
    "Generate grounded responses that cite the retrieved source for every statement",
    "Track reported symptoms over time to reveal progression and trends",
    "Evaluate retrieval relevance, answer groundedness and response time",
]

PROBLEM_STATEMENT = [
    "Self-diagnosis through general web search yields inaccurate and frightening results",
    "General chatbots answer from public data with no medical grounding or citation",
    "Symptoms are recorded as isolated events, so progression over time is never visible",
    "An ungrounded health answer can cause real harm if acted upon",
    "Need: an assistant that answers only from a curated knowledge base, cites it and keeps a history",
]

GAPS = [
    "The base paper reports no accuracy, recall or latency, so its retrieval quality is unverified",
    "It uses dense search only: exact symptom words are not matched lexically and nothing is reranked",
    "General medical chatbots rarely show which retrieved record supports each answer",
    "Emergency wording needs a safety layer that a retrieval-only chatbot does not provide",
    "Consultations are stored, but progression and trends over time are not analysed",
    "No student-deployable tool joins hybrid retrieval, safety escalation and a private history",
]

EXISTING_SYSTEM = [
    "People search the web and read pages that are not tied to their own symptoms",
    "General chatbots answer from model memory without a medical source",
    "Symptom checkers return fixed lists with no explanation of why a condition matched",
    "Dense-only retrieval chatbots miss exact symptom words and rank without a reranker",
    "Consultations are not kept, so a person cannot look back at earlier episodes",
]

LIMITATIONS_EXISTING = [
    "Web search gives generic and alarming results that ignore the symptom description",
    "Ungrounded language models can hallucinate, which is unacceptable for health advice",
    "Retrieval chatbots rarely report measured accuracy, latency or failure cases",
    "Emergency symptoms get the same calm answer as a mild cold unless a rule layer exists",
    "Cloud chatbots send private health text to external servers",
]

PROPOSED_APPROACH = [
    "Normalise the symptom text and expand it with a local HyDE-style template",
    "Retrieve candidates twice: MiniLM semantic search in FAISS and BM25 lexical search",
    "Fuse the min-max normalised scores 0.65 semantic + 0.35 lexical, then rerank with a cross-encoder",
    "Build the answer only from the retrieved records, with evidence cards and a safety filter",
    "Flag emergencies with rules and store every consultation privately per user",
]

EXPECTED_OUTCOMES = [
    "A working web app from symptom text to evidence-backed answer and stored history",
    "Hybrid retrieval measured against single retrievers and the offline fallback",
    "Rule-based emergency escalation with a permanent non-diagnosis disclaimer",
    "Measured latency and honest limits: synthetic knowledge base, no clinical review",
    "Information only: the assistant never replaces a clinician",
]

BASE_PAPER_POINTS = [
    "Sequence-NQ transformer embeddings with FAISS similarity search",
    "RAG over a symptom-disease knowledge base with disease guidance",
    "Secure registration, login, chatbot analysis and a consultation log",
    "Reports no accuracy, recall, latency or ablation figures",
    "Single worked example: constipation, stomach ache, high fever, swollen lymph nodes -> Typhoid",
    "No safety layer, reranker or lexical retrieval described",
]

SUPPORT_EVIDENCE = [
    f"RAG answers from retrieved documents rather than model memory [{R['rag']}]",
    f"Fine-tuned BGE-M3 reached 97.6% and Multilingual-E5 89.7% retrieval accuracy on 5,931 hospital question-document pairs, under 10 ms per query [{R['emr']}]",
    f"ClinicBot ranks guideline evidence by clinical significance and shows verifiable citations, because equal-weight RAG gives noisy context [{R['clinicbot']}]",
    f"Hallucination in generated text is a documented risk that grounding aims to reduce [{R['halluc']}]",
    f"The base paper itself reports no quantitative results [{R['base']}]",
]
