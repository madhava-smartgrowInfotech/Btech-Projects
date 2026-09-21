# PolicyLens - Overview

PolicyLens is an AI assistant that reads **your own health-insurance policy wording**, answers questions with the **exact clause and page** it relies on, flags the fine print that costs money at claim time, and guides you through a claim.

---

## The problem

- Health-insurance policy wordings run to 25-60 dense pages. Coverage, exclusions, waiting periods and limits are scattered across definitions, benefit sections, exclusion codes and annexures.
- People depend on agents and helplines for answers that are slow, generic and sometimes inconsistent.
- General-purpose chatbots answer from what "most policies" do - not from the policy the person actually holds - and can invent coverage.
- Claims get delayed or rejected because people miss a waiting period, a sub-limit, a co-payment rule, a deadline or a required document.

## What PolicyLens does

PolicyLens answers **strictly from the uploaded policy**. Every statement cites the clause it comes from; one click shows that clause highlighted on the PDF page. When the policy does not cover a topic, it says so instead of guessing, and an independent model scores how well each answer is supported by the cited text.

## Who it is for

| User | How they use PolicyLens |
|---|---|
| Policyholders and families | Understand their cover before they need it; check a planned treatment; prepare a claim |
| Insurance advisors | Explain policies to many customers quickly and accurately, with clause references |
| HR / benefits teams | Answer employees' questions about a group health policy and compare plan options |

---

## Features

| # | Feature | What you get |
|---|---|---|
| F1 | **Policy upload and parsing** | Upload a PDF; PolicyLens splits it into sections and clauses (numbering, exclusion codes, two-column layouts, tables) with page positions. The original PDF stays viewable. |
| F2 | **Policy Card** | An automatic summary: sum insured, deductible, co-payment, room rent, ICU, waiting periods, sub-limits, key exclusions, claim deadlines, free-look and grace periods - every value linked to its clause and page and checked against a quote from the text. |
| F3 | **Clause-grounded chat** | Ask in plain words; answers cite clause and page, and say "not covered in this policy" when the wording is silent. |
| F4 | **Hybrid retrieval** | Keyword search (BM25) and semantic embeddings (ChromaDB) are fused and re-ranked by a cross-encoder to find the right clauses. |
| F5 | **Claim Copilot** | Describe a treatment: get *covered / partly covered / not covered / needs information* with reasons, calculated eligibility checks (waiting periods, co-payment), a cost estimate, a document checklist and step-by-step claim procedure. |
| F6 | **Plan comparison** | Two policies side by side - limits, waiting periods, exclusions - with trade-offs and "choose A if / choose B if". |
| F7 | **Risk highlights** | Long waiting periods, sub-limits, co-pay traps, room-rent proportionate deductions and strict deadlines flagged by severity. |
| F8 | **Multilingual answers** | English, Hindi (हिन्दी) and Telugu (తెలుగు) for answers, Claim Copilot, comparisons, Policy Cards and risk highlights. |
| F9 | **Faithfulness score** | Each answer shows a 0-100 score of how well the cited clauses support it, with a per-statement breakdown. |

Also included: a dashboard of your activity, a **Model performance** page with measured accuracy, light and dark themes, and a layout that works from a 360-pixel phone screen up.

---

## How it works in one paragraph

When a policy is uploaded, PyMuPDF reads every line with its font and position; a segmenter rebuilds the clause structure and splits it into retrievable chunks with highlight boxes. The chunks are embedded locally (MiniLM) into ChromaDB and indexed for keyword search (BM25). Gemini reads the whole wording once to build the Policy Card as schema-checked JSON, and every extracted value is verified against the text. For each question, hybrid retrieval finds the most relevant clauses, Gemini writes an answer that may use only those clauses and must cite them, citations to anything else are removed, and a local natural-language-inference model scores each statement against its cited clause. See [02_ARCHITECTURE.md](02_ARCHITECTURE.md).

## What is measured

On a hand-built evaluation set drawn from four real Indian policy wordings, PolicyLens reports retrieval accuracy for each search method, answer accuracy, citation accuracy, abstention on unanswerable questions, faithfulness, response time, Claim Copilot verdict accuracy and Policy Card extraction accuracy. The latest results are in [05_MODELS_AND_TRAINING.md](05_MODELS_AND_TRAINING.md) and in the app.

## Limits

- Answers are guidance based on the policy wording; the insurer makes the final claim decision.
- Scanned (image-only) PDFs are detected and rejected - OCR is not included.
- The policy **schedule** (your personal sum insured, premium and options) is a separate document; PolicyLens reads the **wording**, so answers mention where the schedule decides.
- AI features need an internet connection and a Gemini key; search, the document viewer and the faithfulness checker run offline.
