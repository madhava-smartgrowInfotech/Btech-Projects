# C8 / PeerScope - content brief shared by every documentation builder

Read this before writing any text. Numbers come from `scripts/docs/facts.py` (`F.*`, which reads `docs/metrics/metrics.json`,
`docs/metrics/latency.json`, `docs/metrics/tests.json`) - never type a measured number by hand. Other facts: `docs/REPORT_FACTS.md`,
`docs/LITERATURE_FACTS.md`, `scripts/docs/refs.py` (`REFS`, `CITE`), `scripts/docs/diagram_index.py` (`DIAGRAMS`), `docs/figures/f*.png`,
`docs/diagrams/*.png`, `docs/screenshots/*.png`.

## What PeerScope is (verified from the code)
A local web app (FastAPI 8408 + React/Vite 5408, SQLite, no login). User uploads a research-paper PDF (<= 20 MB, %PDF header check).
Pipeline (`app/services/pipeline.py::run_analysis`): PyMuPDF extraction -> normalisation, title heuristic, section detection (9 sections by
regex), reference parsing -> features (frequency keywords, 21-term method lexicon, 18 topic hints, four structural signals combined as
0.35 structure + 0.25 evidence + 0.25 method clarity + 0.15 presentation) -> trained decision signal (TF-IDF word 1-2 + char 3-5,
LogisticRegression balanced, three classes accept/borderline/reject) -> review (deterministic rules always; 3-step local Qwen2.5-1.5B-Instruct
analyse/critique/synthesise when it loads, else a visible "unavailable" notice) -> literature grounding (OpenAlex, 6 works, 8 s timeout, ranked by
embedding similarity) -> reviewer matching -> stored analysis (SQLite `analyses`, JSON blob) -> JSON/PDF export.
Matching score: `0.55*expertise cosine + 0.20*keyword overlap + 0.15*method/topic overlap + 0.10*availability - 0.60*conflict penalty`, x100 clipped to 0-100;
bands Strong >= 65, Good >= 45, Possible >= 25, else Weak. Embeddings: sentence-transformers all-MiniLM-L6-v2 (same checkpoint family the base paper uses for its
SBERT baseline), TF-IDF fallback when it cannot load. Conflict check: literal conflict terms, full reviewer name, or affiliation string found in the first
3,000 characters of the paper text. Reviewer directory: 6 clearly-labelled demo profiles (Reviewer Alpha ... Zeta; Epsilon inactive), CRUD + CSV import/export.
Endpoints: GET /api/health, GET /api/model/metrics, GET/POST /api/reviewers, PUT/DELETE /api/reviewers/{id}, GET /api/reviewers/export/csv,
POST /api/reviewers/import, POST /api/analyze, GET /api/analyses, GET /api/analyses/{id}, GET /api/analyses/{id}/export?format=json|pdf.
Frontend pages: Landing, Dashboard, Analyze, Reviewers, Model performance, History, Saved analysis, About.
Product is called PeerScope; the project title is "Paper Evaluation Using Artificial Intelligence (Hybrid AI Framework for Research Paper Evaluation and
Reviewer Recommendation)". Base paper = Bagheri, Buscaldi, Reforgiato Recupero, IEEE Access 2026 (ref [1]); supporting [6], [7].

## Honest limitations - state them plainly wherever relevant (do not soften, do not hide)
1. **Decision model = synthetic data.** `data/processed_dataset.csv` is the 1,400-row synthetic fallback (the public PeerRead probe in `prepare_dataset.py` did not return data).
   Labels are built from the same strength/weakness phrases that appear in the text, and `borderline` is generated from both phrase groups, so it cannot be
   told apart from text: the best accuracy any text classifier can reach is ~0.56 (`F.GEN["best_possible_accuracy_from_phrases"]`). Reported accuracy 0.55 is therefore
   near that ceiling, borderline recall is 0.07, but accept-vs-reject is 93% correct. It shows the pipeline works; it is NOT evidence of predicting real peer-review decisions.
   On the four real papers run through the pipeline the model said "borderline" (confidence 0.55-0.66) for every one.
2. **Reviewer pool = 6 demo profiles**; no real publication histories, no h-index, no scraping of publication databases (the abstract mentions h-index and publication history; only
   the free-text `publication_titles` field exists).
3. **Matching evaluation = 40 probe abstracts written by the project team** with the team's own reviewer labels (not independent experts, not real submissions). Probe results
   are optimistic and not comparable with the base paper's MRR@3 on 663 real papers / 524 reviewers.
4. **TF-IDF fallback embedder** is fitted once on the first request's texts and then frozen (`_FALLBACK_VEC`), so offline quality is lower (top-1 0.75 vs 0.95).
5. **Novelty is not assessed.** The review "coverage" chart has a fixed Novelty value (55) and the novelty text says "inconclusive ... requires verification"; OpenAlex results are context, not a novelty test.
6. **Structural weights** (0.35/0.25/0.25/0.15) and thresholds are heuristics, not fitted or validated against human judgements. Section detection is regex based and misses roman-numeral
   headings such as "I. INTRODUCTION" (the IEEE base paper PDF: introduction not detected, title heuristic returned "Digital Object Identifier ...").
7. **Conflict detection = literal string matching**: 12/12 literal injected links detected, 0/3 paraphrased ones (affiliation reworded, first name only); 0 false flags on 240 clean paper-reviewer pairs.
8. **Local LLM**: Qwen2.5-1.5B fp32 on CPU, ~3 tokens/s; one analysis with AI review takes minutes (see `F.LATENCY`); output is not fact-checked; no GPU used. Prompt-injection by text hidden in a PDF is
   possible in principle ([2], [27]); PeerScope's mitigation is local processing, deterministic fallback and a human-in-the-loop disclaimer, not a filter.
9. Matching re-embeds every reviewer profile on every request (no cache): 6 reviewers 86 ms, 500 reviewers 5.2 s with MiniLM. No authentication, CORS open, single user, SQLite.
10. Abstract items NOT implemented: deep-learning domain classifier, originality score from a corpus, readability indices beyond average sentence length, scope alignment with a target venue, h-index ranking.
11. Literature retrieval needs internet (OpenAlex); offline it degrades to `unavailable`.

## Objectives (from 6.OBJECTIVES&PROBLEM STATEMENT.docx) and honest status
1 Build a corpus of submitted papers and reviewer publication profiles - **partly**: analyses are stored; reviewer directory exists with 6 demo profiles + CSV import; no real publication corpus; decision dataset synthetic.
2 Extract topics, methods, keywords with NLP - **done (heuristic)**: frequency keywords, lexicons.
3 Represent reviewer expertise as comparable vectors - **done** from profile text + titles via MiniLM embeddings (no real publication history).
4 Compute semantic similarity to rank reviewers - **done**; measured on probe set.
5 Preliminary quality assessment (structure, novelty signals, completeness) - **done except novelty** (see 5 above).
6 Evaluate assignment quality against expert judgement and COI handling - **partly**: team-labelled probe set, not independent experts; COI measured by injection test.

## Style rules
Formal academic English, "the project", "the system", "the team" - no marketing, no emojis, no first-person singular. British or neutral spelling consistent with "organisation", "normalise".
Short paragraphs, concrete numbers from `F`, tables with captions. Do not claim "state of the art", "outperforms the base paper" or "validated on real peer review data".
When comparing with the base paper state plainly: different task scope, different data (663 papers / 524 reviewers vs a 40-abstract team-written probe and 6 demo reviewers), numbers not comparable.
Forbidden strings anywhere in any output (the verifier fails on them): Fakeddit, PHEME, Snopes, MCNN, bank transaction, social media manipulation, fraud detection, skincare, Dayananda, Sindhu, pneumonia, chest X-ray, **recommender system** (the base paper's index term is 'recommender systems' - do not copy it; write 'reviewer recommendation' or 'reviewer assignment' instead).
Student names and the guide only appear on title/certificate/declaration pages (they come from `F.STUDENTS`, `F.GUIDE`).

## Additions after the measurements (read docs/REPORT_FACTS.md for every number)
- Screenshots in docs/screenshots/01..17 were RE-CAPTURED from real runs: papers analysed = IEEE base paper (id 1), arXiv survey 2604.27924 (id 2, literature unavailable because its title contains '?'), ReViewGraph paper 2511.08317 (id 3, 17 pages, the one shown on screens 06-10 and 15). View each PNG before describing it. The analysis shown has: structural score 65.2, decision signal borderline 58% confidence, AI review generated by Qwen2.5-1.5B-Instruct, top reviewer Reviewer Gamma 28.4 (low absolute scores: the demo reviewers are not close to this paper's topic). The AI synthesis text visibly contains errors (e.g. wrong dataset description) - a good failure example.
- Latency (F.LATENCY): local LLM = ~97% of the time; stages in F.LATENCY['pipeline_stages']; HTTP with LLM off in F.LATENCY['http_api'] (health 2.4 ms median; analyze demo 1.29 s; survey 1.19 s); HTTP with LLM on 534 / 621 / 946 s (F.LATENCY['http_llm_on_s']). tests.json: pytest 7/7 in 34.09 s, smoke 24/24 (both with LLM disabled).
- Extra defects (all in REPORT_FACTS section 9): OpenAlex 400 on titles with '?', roman-numeral headings not detected, fixed Novelty 55, UTC timestamps shown without zone (appear ~5.5 h behind IST), corrupt-but-%PDF-headed file returns 200, CSV without names imports 0 rows silently, TF-IDF fallback frozen after first call.
- Colours/names: product PeerScope, reviewer demo names Reviewer Alpha..Zeta (Epsilon inactive).
- Office COM (Word/PowerPoint) is flaky and shared between forks: wrap every COM session in the file lock helper `scripts/docs/comlock.py` (`with com_lock(): ...`), use DispatchEx, retry on "Server execution failed", never taskkill WINWORD/POWERPNT, and keep sessions short.
