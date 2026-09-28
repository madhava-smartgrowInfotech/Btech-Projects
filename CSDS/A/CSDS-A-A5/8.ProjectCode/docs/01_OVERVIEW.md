# TaxSentinel - Overview

## The problem
Input-tax-credit (ITC) fraud under GST runs through fake invoices, circular trading and networks of
shell companies, and it costs large amounts of revenue. Manual audits and rule-based checks are slow
and react after the fact. Confirmed fraud labels are scarce, which limits supervised learning, and
existing systems rarely explain why a claim was flagged.

## What TaxSentinel does
TaxSentinel learns what normal GST behaviour looks like from unlabelled data. It then ranks taxpayers
and invoice chains by how far they deviate and writes a plain-language case note for each flag.

| Capability | What you get |
|---|---|
| GST ecosystem generator | A seeded generator for taxpayers, B2B invoices and monthly GSTR-1/2B/3B returns, with injected fraud and ground-truth labels |
| Feature layers | Invoice-level, return-behaviour and buyer-seller network features for every taxpayer-month |
| JEPA behaviour encoder | A small self-supervised model, trained on CPU in seconds, whose prediction error is the anomaly score |
| Fraud-ring detection | Circular-trading loops and shared-identity (shell) clusters found with NetworkX, shown as an interactive graph |
| Risk ranking | One combined score per taxpayer and per invoice chain, with drill-down to invoices, returns and partners |
| Written explanations | Gemini writes an investigator-style case note in which every claim cites an evidence ID |
| Evaluation | Precision@k, recall and F1 against the injected labels, compared with a rule-based baseline |

## Who it is for
- Tax-administration analysts and investigators
- Forensic accountants
- Compliance teams at large businesses auditing their supplier networks

## Fraud patterns covered
- **Fake invoices**: an established business claims ITC on invoices bought from a shell cluster, with no goods moving.
- **Circular trading**: 3-5 firms pass the same value around a loop (A → B → C → A) to inflate turnover and credit.
- **Shell entities**: young registrations that share an address or contact number, trade mostly with each other, pay almost no tax in cash and then stop filing.
- **ITC spikes**: a month's claim far above both the taxpayer's history and the credit available in GSTR-2B.

## Screens
1. **Landing**: what the product does.
2. **Login / register**: JWT sign-in, plus a seeded demo account.
3. **Overview**: counts, flagged taxpayers, patterns, top invoice chains, and a *Generate & analyse* control that builds a new ecosystem.
4. **Taxpayers**: the risk ranking with search and filters, plus each taxpayer's profile (layer scores, monthly ITC chart, evidence, partners, anomalous invoices).
5. **Fraud rings**: the interactive graph of loops, shell clusters and flagged taxpayers, and the ranked invoice chains.
6. **Case detail**: the evidence list next to the Gemini case note; clicking a citation jumps to its evidence.
7. **Model performance**: precision@k, recall@k, F1, ablations, per-pattern recall, ring recovery and JEPA training.

## Results (bundled ecosystem, seed 42)
| | TaxSentinel | Rule baseline |
|---|---|---|
| Precision@79 (79 = number of fraud taxpayers) | **0.949** | 0.620 |
| F1 at flag threshold | **0.955** | 0.432 |
| ROC-AUC | **0.997** | 0.876 |

All 5 injected circular-trading rings are recovered. Full numbers are in the [README](../README.md).
