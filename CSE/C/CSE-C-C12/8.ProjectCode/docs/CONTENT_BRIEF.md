# CONTENT BRIEF - SymptoTrackAI (CSE-C-C12) documentation build

Kit: `scripts/docs` (copied from CSE-C-C8; kit.py, blocks.py, pptkit.py, comlock.py, word_finalize.py, finalize_all.py, preview.py, build_docs.py are generic).
Facts: `docs/REPORT_FACTS.md` is the single source of truth; numbers in code come from `scripts/docs/facts.py` (reads `docs/metrics/*.json`). **Never type a measured number by hand - read it from `F`.**
References: `scripts/docs/refs.py` (`CITE['key']` gives the number; use `[n]` in text). Cite only what the source supports. Refs 2-4 are unverified: never cite them for a claim (list them in the survey table as "listed in the batch survey, details not verified").

## Naming
Project title SymptoTrackAI (all title pages, headings); the implemented web application is **CareLens AI** (name on screen and in code). Say so once early in each document ("SymptoTrackAI, implemented as the CareLens AI web application"). Students/roll numbers/guide from `F`; leave `[ACADEMIC YEAR]`, `[PLACE]`, `[DATE]`, `[DESIGNATION]`, `[HOD NAME]`, `[PRINCIPAL NAME]` placeholders.

## Honest story to tell (all facts are in REPORT_FACTS.md)
- Built: FastAPI + React app; hybrid retrieval (MiniLM+FAISS, BM25, fusion 0.65/0.35, cross-encoder rerank) over a **synthetic** 176-record / 30-condition knowledge base; HyDE-style **template** expansion; grounded answer (Flan-T5 or deterministic fallback); regex safety layer; bcrypt/JWT accounts; per-user SQLite consultation history with search/detail/delete.
- Real measurements: lay-language probes (60, author-written) top-1 0.967 shipped, 1.000 without HyDE; two-symptom queries 0.881; verbatim LOO 0.972; shipped metrics.json 1.0 is an upper bound (held-out record still indexed). BM25 alone is strong (0.883 S4, 1.0 verbatim). TF-IDF offline mode 0.817 on S4.
- Defects: generator echoes prompt (transformers 5), relevance always 100% (out-of-KB also "Strong match"; raw rerank AUROC 1.0 would fix), safety recall 27/40 (paraphrases 0/12) and 6/10 hard-negative false alarms, filter case-sensitive, near-duplicate evidence cards, no trend tracking, groundedness not judged, synthetic KB, no user study.
- Base paper reports **no numbers**: compare qualitatively (what each does), state plainly that no quantitative comparison is possible.
- Objectives table (REPORT_FACTS section 12) must be used verbatim in status: achieved / partly / not achieved.

## Diagram manifest (`docs/diagrams/`, PNG 150 dpi) - written by scripts/docs_build/make_diagrams.py + diagrams_more.py
01_system_architecture, 02_high_level_workflow, 03_dfd_level0, 04_dfd_level1, 05_dfd_level2, 06_uml_class, 07_sequence_chat, 08_use_case, 09_er_diagram, 10_flowchart_retrieval, 11_safety_decision_flow
Index with caption + explanation tuples: `scripts/docs/diagram_index.py` (`DIAGRAMS = [(key, title, file, caption, text), ...]`, keys arch, flow, dfd0, dfd1, dfd2, uml, seq, uc, er, flowchart, safety).

## Figure manifest (`docs/figures/`) - written by scripts/docs_build/make_figures.py from docs/metrics/metrics.json
f01_lay_confusion (30x30 confusion matrix, shipped config, S4), f02_ablation (top-1 per configuration, sets S2/S3/S4), f03_protocol_comparison (shipped config: shipped protocol vs LOO vs S3 vs S4),
f04_latency_stages (stage means + totals), f05_relevance_display (raw rerank score in-KB vs out-of-KB vs displayed 100%), f06_safety_rules (recall literal/paraphrase, false alarms ordinary/hard),
f07_kb_composition (records per condition + severity), f08_api_latency (HTTP /api/chat fallback vs Flan-T5), f09_hyde_effect (shipped vs no-HyDE per set).
Screens: `docs/screenshots/*.png` (inventory in REPORT_FACTS section 11). `college_banner.png` is extracted from the Final template by `front._banner()` on first use.

## Module interfaces (keep the C8 function names; `build_docs.py` calls them)
ch1.blocks(); ch2.blocks(); ch3_4.blocks()/chapter3()/chapter4(); ch5.blocks(); ch6.methodology_blocks()/application_blocks()/blocks(); ch7.blocks();
ch8.blocks(); ch9_10.novelty_blocks()/contribution_blocks()/scope_blocks()/assumption_blocks()/limitation_blocks()/not_measured_blocks()/walkthrough_blocks()/decision_blocks()/
conclusion_blocks()/future_blocks()/chapter9_blocks()/chapter10_blocks(); appendix.code_blocks()/guide_blocks()/screens_blocks(); front.cover/certificate/declaration/acknowledgement/abstract/abbreviations.
Blocks come from `blocks.py` (H1/H2/H3/P/B/N/FIG/TAB/PAIR/EQ/CODE). `F.REPORT` is True while building 17.Final Document - emit compact variants then. Headings: report chapters are H1 "1. INTRODUCTION" style (see C8).
Report size target: 80-95 Word pages (A4, 12 pt, 1.5 spacing, 1.25/1.0 in margins) - about 24-27k words with ~45 figures/screens; chapter documents 9, 10, 12, 14, 15 and 11 are reusable pieces of the same text (no second wording).

## Per-file ownership
- diagrams/figures: docs_build/*, docs/diagram_index.py
- ch1, ch2, front.py, ch3_4
- ch5, ch6, ch7
- ch8, ch8_report, ch9_10, appendix
- decks: lit.py, deck_review1/2/final.py, pptkit tweaks
- paper: paper.py, build_paper.py, paper_finish.py
- lead: facts.py, refs.py, build_docs.py, verify_docs.py, finalize

## Hard bans (verify_docs fails on these): leftovers of the templates (`[STUDENT NAME`, `[ROLL NO`, "Fakeddit", "PHEME", "Snopes", "MCNN", "bank transaction", "social media manipulation", "Hidden Risk") and of the IEEE reference paper ("skincare", "Dayananda", "Sindhu", "recommender system"). Also avoid C8 words (PeerScope, reviewer assignment, Qwen, OpenAlex).
