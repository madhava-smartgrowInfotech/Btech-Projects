# ClauseGuard - Overview

ClauseGuard is a contract-analysis tool for Indian agreements. Users upload a PDF or DOCX
contract and get back:

- The contract split into clauses with page numbers, each classified by CUAD-style type.
- Predatory-clause flags (restraint of trade, penalty vs liquidated damages, unilateral
  termination, unlimited liability, one-sided arbitration, auto-renewal, IP overreach, no-refund)
  with a plain-language reason, the exact triggering provision, and safer wording.
- Risky clause **combinations** - clause pairs that are harmless alone but dangerous together
  (e.g. unilateral termination + no-refund + penalty).
- An overall complexity grade (A-F) built from readability, legalese density, cross-references
  and sentence length.
- A plain-language summary and list of key obligations.
- Separate evaluation scores for clause classification (against CUAD) and predatory-clause
  detection (against a curated Indian-law test set).

## Who it's for

Freelancers and individuals signing contracts, startups/small businesses without in-house
counsel, and legal-ops teams doing first-pass review.

## Screens

Landing, Login/Register, Upload, Contract report (grade + summary + annotated clauses),
Clause detail (explanation + rule + safer wording), Clause graph, Evaluation.

## Scope

This build intentionally uses a local vector store (NumPy) instead of pgvector, and a NetworkX
in-memory graph instead of Neo4j, to keep the stack simple and fast to run locally without extra
infrastructure - see `docs/02_HOW_IT_WORKS.md` for the reasoning and `MASTER_PROMPT_FAST.md`
section "Deferred for speed" for what was intentionally left out.
