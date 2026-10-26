# NARRATIVE - the story every QuantPulse document tells (CSE-C-C4)

Numbers: only from `docs/REPORT_FACTS.md` / `scripts/docs/facts.py` (F.SUM, F.FWD, F.RR, F.MIL, F.API, F.SHIP). Never type a metric by hand when F has it; read it.

## One-paragraph story
The batch title and objectives ask for stock-direction prediction from **three sources (prices, news, social media) with Multiple Instance Learning (a day = a bag of news instances)**, evaluated with accuracy/precision/recall/F1 against a price-only baseline. The base paper named in the batch papers (Nejatbakhsh & Aliasgari, IEEE Access 2026) is a hybrid LSTM + attention + FinBERT sentiment + simulated FedAvg **price-level** forecaster on ten tech stocks. **QuantPulse implements that paper end to end as a working product** (FastAPI + React, ten tickers, five classical baselines, four deep tiers, 5- and 30-day forecasts with bands, six screens). It does **not** contain MIL, social-media text, or precision/recall/F1. To close that gap honestly an **offline MIL study** was run on real FNSPID headlines (not part of the application). Results are mostly negative and are reported as such.

## What was achieved (say this plainly)
- A complete, tested, running forecasting product: 7 API endpoints, 6 screens, 56 pytest tests + 26 smoke checks pass, ~10-20 ms warm API latency for stored results, ~140 ms for history (live Yahoo download), ~4.6 s median for sentiment.
- Ten-ticker x nine-model comparison reproducible with `python -m backend.train`; plus the added reproducible experiment suite (`scripts/run_experiments.py`, `mil_study.py`).
- An honest evaluation: the shipped deep tiers do not beat "tomorrow = today" on real closes; the base paper's R2 0.91 was not reproduced; the 5-day forecasts were wrong in direction for 6 of 10 tickers and the stored forecasts predicted a -14.8 % average fall against an actual -0.4 %.
- MIL study: real headlines, bag formulation, gated-attention MIL, 5 seeds, 3 expanding folds: **no model beat the always-up rate (53.6 %); all MIL variants within about +-2 points of the price-only LSTM with bootstrap intervals spanning zero; the shuffled-bag placebo scores the same.** News carried no measurable next-day directional signal at this sample size (1,309 test samples, seven tickers, 2022-2023, mostly day-level time stamps).

## Defects found (documented as limitations, product code left unchanged)
Clipped test targets inflate direction metrics (shipped 67-68 % vs true 53 %); sentiment channel is exactly zero in training and synthetic template headlines in test; FedAvg across differently scaled clients; stale artefacts vs refreshed CSVs; multi-step forecast rolls OHLC to the predicted close; non-reproducible synthetic headlines (hash seed); mixed baseline protocols; API never loads the saved .keras models (it serves stored JSON); the stored 5-day forecast comes from the federated model, the 30-day from the local attention+sentiment model.

## Wording rules
- Title = "Stock Market Prediction Using Multi-Source Multiple Instance Learning"; product = QuantPulse. Say "the product forecasts price level and a trend flag; MIL was studied offline" - never claim the product does MIL.
- Social-media text: no data source was available; not implemented, say so. Objective 1 and 2 are only partly met (prices yes; news only as NewsAPI-or-synthetic headlines; no social media).
- Base paper comparison: always "datasets and protocols differ" - the paper uses a 30-day NewsAPI window and scaled units; this project 2 years of data, dollar units, 97 test windows/ticker. Never say we beat or matched it.
- Sentiment in the product is synthetic template headlines unless a NEWSAPI_KEY is set (it was not). Never present synthetic sentiment as a finding about real news.
- Use "no evidence of improvement", not "news does not matter". Quote the sample size and intervals.
- Disclaimer: research/education tool, not financial advice.
- No login exists; no database exists (ER diagram is logical); do not invent roles beyond "trader/analyst", "evaluator/developer".
- College, HOD, principal, academic year, guide designation: keep the template placeholders.

## Figures (docs/figures/, written by scripts/docs/make_figures.py) - use exactly these names
| file | what |
|---|---|
| f01_shipped_mae_by_model.png | mean MAE per model, shipped artefact (10 tickers) |
| f02_true_mae_vs_persistence.png | per ticker: true-target MAE of LSTM+attention (5 seeds) vs persistence |
| f03_clipping_and_direction.png | % of test closes above training max per ticker; shipped vs true directional accuracy |
| f04_forward_test_30day.png | 10 panels: actual closes vs the shipped 30-day forecast |
| f05_forecast_vs_actual_change.png | 5-day predicted vs actual % change per ticker |
| f06_sentiment_channel.png | non-zero sentiment rows in train vs test part; TSLA channel over time |
| f07_seed_variation.png | true MAE per tier across the 5 seeds (strip/box) with persistence line |
| f08_mil_accuracy.png | MIL study: accuracy +- std per model with always-up line |
| f09_mil_prf.png | MIL study: precision/recall/F1 per model |
| f10_mil_paired_ci.png | MIL study: accuracy difference to price-only LSTM with 95 % interval |
| f11_api_latency.png | API median/p95 latency per endpoint |
| f12_base_paper_comparison.png | base paper reported figures vs measured (R2, trend accuracy) with a "datasets differ" note |
| f13_forward_tiers.png | retrained tiers: 5-/30-day forward MAE vs persistence |
| f14_mil_attention_examples.png | one gated-attention example: headlines with weights vs uniform weight |

## Diagrams (docs/diagrams/, index in scripts/docs/diagram_index.py)
arch, flow, dfd0, dfd1, dfd2, uml, seq, uc, er, flow_core (recursive forecast), flow_sent (sentiment path), model (architecture). Files 01_..12_.

## Screenshots (docs/screenshots/, see REPORT_FACTS section 8)
Use these for output screens: 01,02 landing; 03,15,10 dashboard; 16,04,14,05,11 forecast; 06,12,07 models; 08,13 sentiment; 09 about.

## Module interface (keep these function names so scripts/docs/build_docs.py works)
ch1.blocks, ch2.blocks, ch3_4.blocks, ch5.blocks (first block is the H1), ch6.methodology_blocks / application_blocks / blocks, ch7.blocks, ch8.blocks, ch9_10: novelty_blocks, contribution_blocks, scope_blocks, assumption_blocks, limitation_blocks, not_measured_blocks, walkthrough_blocks, decision_blocks, conclusion_blocks, future_blocks, chapter9_blocks, chapter10_blocks; appendix: code_blocks, guide_blocks, screens_blocks; front: cover, certificate, declaration, acknowledgement, abstract, abbreviations. Block constructors in scripts/docs/blocks.py (P, B, N, H1/H2/H3, FIG, TAB, PAIR, EQ, CODE). Chapter numbering: H1 "1. INTRODUCTION" ... H2 "1.1 ..." etc.
