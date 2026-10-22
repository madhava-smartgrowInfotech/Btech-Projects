"""Literature and framing data for the decks (Review 1, Review 2 and the final deck).

Every literature fact traces to docs/LITERATURE_FACTS.md; reference numbers match scripts/docs/refs.py.
"""

from .refs import CITE as R

BASE_PAPER_TITLE = "LLM-Assisted Reviewer Assignment via Auditable Expertise Matching"
BASE_PAPER_VENUE = "F. Bagheri, D. Buscaldi, D. Reforgiato Recupero - IEEE Access, vol. 14, 2026"

# [work, year, approach, finding / limitation]   (each cell <= 90 characters)
LIT_TABLE = [
    [f"Bagheri et al. [{R['base']}] (base paper)", "2026", "LLM ensemble induces keywords; judge LLM picks; SBERT / KG matchers",
     "663 papers, 524 reviewers; best MRR@3 0.7843; no paper assessment"],
    [f"Charlin et al. [{R['tpms']}]", "2012", "Learned paper-reviewer suitability scores + integer-program assignment",
     "Learns from few provided scores; two conference datasets"],
    [f"Mimno & McCallum [{R['mimno']}]", "2007", "Author-Persona-Topic expertise model vs language-model baselines",
     "Judged on human relevance labels; APT beat the language-model baselines"],
    [f"Kang et al. PeerRead [{R['peerread']}]", "2018", "Accept/reject prediction from 14.7K drafts and 10.7K reviews",
     "Up to 21% error reduction over majority; decision only, no matching"],
    [f"Liang et al. [{R['liang_llm_feedback']}]", "2024", "GPT-4 feedback on full PDFs vs human reviewers",
     "Overlap 30.85% / 39.23% (humans 28.58% / 35.25%); no reviewer matching"],
    [f"Li et al. ReViewGraph [{R['reviewgraph']}]", "2025", "LLM reviewer-author debates + graph network for accept/reject",
     "ICLR accuracy 66-72%; costly agents; decisions only"],
    [f"Torrielli et al. [{R['inject_aro']}]", "2026", "Hidden instructions in manuscripts steer chatbot reviewers",
     "Followed in 78% (ChatGPT) and 86% (Gemini) of cases"],
    [f"Reimers & Gurevych SBERT [{R['sbert']}]", "2019", "Siamese BERT sentence embeddings compared by cosine",
     "Pair search over 10,000 sentences: ~65 h (BERT) to ~5 s"],
]

OBJECTIVES = [
    "Build a corpus of submitted papers and reviewer publication profiles",
    "Extract topics, methods and keywords from paper text with NLP",
    "Represent reviewer expertise as comparable vectors",
    "Rank candidate reviewers by semantic similarity for each paper",
    "Give a preliminary assessment: structure, novelty signals, completeness",
    "Evaluate assignment quality and conflict-of-interest handling",
]

PROBLEM_STATEMENT = [
    "Reviewer assignment is manual and depends on the editor's personal knowledge",
    "Keyword matching picks reviewers who share vocabulary, not expertise",
    "Slow reviews delay the publication of valid research",
    "Review quality varies between reviewers with no consistency check",
    "Need: assess submissions automatically and assign the most expert reviewer",
]

GAPS = [
    "Base paper scores reviewer affinity only; it never assesses the paper itself",
    "Automated-review work predicts decisions or writes reviews but does not match reviewers",
    "Conflict of interest and workload were left out of the base paper's experiments",
    "LLM reviewers can be steered by hidden text (78-86% compliance), so human oversight is needed",
    "Embedding matchers are hard to audit; per-score breakdowns are rare",
    "No student-deployable tool joins PDF intake, assessment and auditable matching",
]

EXISTING_SYSTEM = [
    "Editor or chair picks reviewers by memory, bidding or keyword search",
    "Dense-embedding matchers rank reviewers but give no readable reasons",
    "Separate tools screen submissions; none is linked to reviewer choice",
    "LLM review writers read the whole paper with no audit trail",
    "Conflict and workload are checked by hand or left to a later step",
]

LIMITATIONS_EXISTING = [
    "Mismatched reviewers lower review quality and delay decisions",
    "Embeddings are opaque: editors cannot see why a reviewer ranks first",
    "Historical assignments used as labels are an imperfect proxy for expertise",
    "Decision predictors need real review corpora that are rarely open",
    "Uploading manuscripts to cloud AI conflicts with confidentiality rules",
]

PROPOSED_APPROACH = [
    "Read the PDF locally: text, sections, references, structural signals",
    "Add a trained decision signal and a local AI critique with a visible fallback",
    "Ground the paper with related works from OpenAlex",
    "Rank reviewers: 0.55 similarity + 0.20 keyword + 0.15 method + 0.10 availability",
    "Subtract a conflict penalty and show every term of the score",
]

EXPECTED_OUTCOMES = [
    "A working web app from PDF upload to reviewer ranking and export",
    "Transparent, reproducible score breakdown for each recommended reviewer",
    "Preliminary assessment that screens submissions before human review",
    "Measured results for the decision model and the matcher, gaps stated",
    "Decision support only: the final judgement stays with a human editor",
]

BASE_PAPER_POINTS = [
    "LLMs only induce keywords; they never rank reviewers",
    "Ensemble of producer LLMs, a judge LLM and deterministic normalisation",
    "663 papers from 85 conferences, 1,989 assignments, 524 reviewers",
    "Metrics MRR@3, P@3, MAP@3; best MRR@3 0.7778 (titles), 0.7843 (abstracts)",
    "Most text-encoder differences are not statistically significant",
    "COI and capacity not benchmarked; no assessment of the paper itself",
]

SUPPORT_EVIDENCE = [
    f"NeurIPS 2021 committees disagreed on about 23% of accept/reject outcomes [{R['neurips_consistency']}]",
    f"Hidden instructions steered chatbot reviewers in 78% (ChatGPT) and 86% (Gemini) of cases [{R['inject_aro']}]",
    f"Simple prompt injections reached up to 100% acceptance scores in LLM reviews [{R['keuper']}]",
    f"GPT-4 feedback overlapped human reviewers 30.85% vs 28.58% between two humans [{R['liang_llm_feedback']}]",
    f"Reviewer assignment studied for about thirty years; a recent systematic synthesis was missing [{R['rap_scoping']}]",
]
